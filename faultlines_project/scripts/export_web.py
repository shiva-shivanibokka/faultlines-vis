"""Export the parquet layer to JSON for the two web artifacts.

    python scripts/export_web.py

Writes:
    ../faultlines-tool/data.json    the tool: map + audit cases + generation diff
    ../faultlines-web/summary.json  the deck: headline numbers only

TWO SEPARATE VERCEL PROJECTS
Each directory is its own deploy root. The tool gets a URL that can be cited in
the thesis, and editing a slide does not redeploy 3 MB of data. The cost is that
the deck cannot reach the tool with a relative path in production -- see TOOL_URL
in faultlines-web/index.html, which resolves relatively on localhost and
absolutely once deployed.

WHY A SCRIPT AND NOT A HAND-EDIT
The deployed pages carried 300-question pilot numbers for days after the corpus
run superseded them (ISSUES #37). Hand-maintained numbers in HTML drift silently
because nothing recomputes them. Every figure either comes from here or is not
shown. Re-run this after any pipeline change and both pages are current.

PAYLOAD BUDGET
34,062 map points and 1,453 audit cases have to reach a browser over a static
host. Points go out as PARALLEL ARRAYS of rounded numbers, not objects: a
{"x":..,"y":..} per point costs ~4x the bytes for identical information. Text is
truncated -- the inspector shows enough to judge an answer, and the parquet
remains the source of record for anything longer.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import path, seq  # noqa: E402
from faultlines.datasets import duplicate_qids  # noqa: E402
from faultlines.grade import normalise, _SHORT_FORM_RATIO  # noqa: E402


def key_too_strict(rows, gold, aliases) -> bool:
    """True when EVERY model answer sits inside the gold but was rejected only
    by the short-form ratio guard.

    grade.contains_either_way accepts a short answer only at >=40% of the gold's
    length, because "York" must not count as "New York City". The same guard
    rejects "Bangladesh" for "People's Republic of Bangladesh" (0.33) and "China"
    for "People's Republic of China" (0.20), where the model is plainly right.

    It is not decidable lexically -- that is why this is a FLAG for the human in
    the inspector, not an automatic re-grade. Measured: 54 of the 950 blind
    spots, 5.7% (59 of 1,054 before the dedup). This flag catches only the
    containment artifact; adjudication puts all artifacts at 21.05%.
    """
    cands = [gold] + seq(aliases)
    for a in rows:
        A = normalise(a)
        hit = False
        for c in cands:
            C = normalise(c)
            if len(C) >= 4 and f" {A} " in f" {C} " and len(A) / len(C) < _SHORT_FORM_RATIO:
                hit = True
                break
        if not hit:
            return False
    return True

# set in main() from records.parquet; every stored per-question result is cut
# to it, because those parquets were written before duplicates were removed
ANALYSED: set = set()
# The CURRENT 2025 blind spots. RQ5 ran on the pre-dedup 1,054; the tie rule
# (ISSUES #67) made ~100 of those ordinary majority errors, and "rescued by
# search" is only a statement about a question that is still a blind spot.
BLIND: set = set()


def analysed(d: pd.DataFrame) -> pd.DataFrame:
    return d[d["qid"].isin(ANALYSED)] if ANALYSED else d


def blind_only(d: pd.DataFrame) -> pd.DataFrame:
    return d[d["qid"].isin(BLIND)] if BLIND else analysed(d)


OUT_TOOL = Path(__file__).resolve().parents[2] / "faultlines-tool" / "data.json"
OUT_WEB = Path(__file__).resolve().parents[2] / "faultlines-web" / "summary.json"
ISSUES = Path(__file__).resolve().parents[1] / "ISSUES.md"


def defect_count() -> int:
    """The defect total, read from ISSUES.md instead of typed into a slide.

    Slide 15 said "42 defects found, 42 fixed" for four days after ISSUES.md
    said 44 -- the same drift as #43, on the same kind of number: a count that
    only ever grows, hand-copied into a page that nobody re-reads. ISSUES.md's
    header line is the one authoritative statement of the total, so read it.

    Deliberately raises on a miss rather than returning a default. A wrong
    number that renders is worse than an export that fails loudly.
    """
    m = re.search(r"^##\s*(\d+)\s+defects found", ISSUES.read_text(encoding="utf-8"),
                  re.M)
    if not m:
        raise SystemExit(f"defect_count: no '## N defects found' line in {ISSUES}")
    return int(m.group(1))

Q_CHARS = 260          # question text shown in the inspector
A_CHARS = 200          # each model answer
DATASETS = ["popqa", "triviaqa", "halueval", "truthfulqa"]

# Short display names. The full provider IDs are 40+ chars and would dominate
# every row of the inspector; the mapping is recorded here so the page never has
# to guess and the real ID stays one lookup away.
SHORT = {
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": "Llama-4-Maverick",
    "Qwen/Qwen3-235B-A22B-Instruct-2507": "Qwen3-235B",
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506": "Mistral-Small-3.2",
    "google/gemma-3-27b-it": "Gemma-3-27B",
    "llama3.1:8b": "Llama-3.1-8B",
    "qwen2.5:7b": "Qwen2.5-7B",
    "mistral:7b": "Mistral-7B",
    "gemma2:9b": "Gemma-2-9B",
}


def short(m: str) -> str:
    return SHORT.get(m, m.split("/")[-1][:24])


def _trunc(s: str, n: int) -> str:
    s = str(s).strip().replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


NEW_MODELS = {"Qwen3-235B-A22B-Instruct-2507", "gemma-3-27b-it",
               "Llama-4-Maverick-17B-128E-Instruct-FP8",
               "Mistral-Small-3.2-24B-Instruct-2506"}


def ablation_stats() -> dict:
    """The ensemble-size curve and what drives the blind region.

    From `scripts/ensemble_ablation.py`, which scores every subset of the eight
    models that have answered the identical corpus. Exported because the size
    curve must travel WITH the 2.79% headline -- a reviewer's first question is
    what the rate would have been on three models, and the answer is 4.01%.

    `phi_silent` is the finding: within each ensemble size the blind region
    tracks how CORRELATED the models are (+0.92 across the 70 four-model
    ensembles; the r values are per size k, never pooled over all 154) and
    barely tracks how ACCURATE they are (-0.34). `phi_auc` is the tension that goes the other way, and it
    is exported alongside so no page can quote one without the other.
    """
    src = path("processed", "ensemble_ablation.parquet")
    if not src.exists():
        return {}
    d = pd.read_parquet(src)
    d["arm"] = d.models.map(
        lambda m: "2025" if set(m.split(" + ")) <= NEW_MODELS
        else ("2024" if not (set(m.split(" + ")) & NEW_MODELS) else "mixed"))
    cur = d[d.arm == "2025"]

    # HEAD-COUNT AUC throughout (auc_unweighted), since 2026-09-27. The headline
    # detector is the head-count score (DECISIONS 2026-08-03), but the ablation
    # scored every ensemble on the confidence-weighted one, so one chapter
    # compared two different detectors under one name. At k=2 it mattered:
    # corr(phi, AUC) +0.78 weighted, +0.93 head-count. ISSUES #78.
    def by_k(frame):
        # 6dp, not 5. At 5dp the k=2 mean 0.0662460 stores as 0.06625, which a
        # two-decimal percentage formatter renders as 6.63% instead of 6.62% --
        # the page and the write-up then disagree about a number neither of them
        # computed. Round once, at the point of display.
        return [{"k": int(k),
                 "n": int(len(g)),
                 "silent": round(float(g.silent_rate.mean()), 6),
                 "lo": round(float(g.silent_rate.min()), 6),
                 "hi": round(float(g.silent_rate.max()), 6),
                 "auc": round(float(g.auc_unweighted.mean()), 4)}
                for k, g in frame.groupby("k")]

    return {
        "n_ensembles": int(len(d)),
        "by_size_2025": by_k(cur),
        "by_size_all": by_k(d),
        "phi_silent": [{"k": int(k),
                        "r": round(float(g.phi_mean.corr(g.silent_rate)), 3)}
                       for k, g in d.groupby("k")],
        "err_silent": [{"k": int(k),
                        "r": round(float(g.err_mean.corr(g.silent_rate)), 3)}
                       for k, g in d.groupby("k")],
        "phi_auc": [{"k": int(k), "r": round(float(g.phi_mean.corr(g.auc_unweighted)), 3)}
                    for k, g in d.groupby("k")],
        # Is phi just capability in disguise? D. Kim (2026) finds diversity
        # metrics are ~1 - mean accuracy (rho ~0.99) in majority-vote ensembles.
        # Here the partial correlation holding mean error fixed answers it
        # directly, and phi-vs-error is exported so the answer can be checked.
        "phi_err": [{"k": int(k), "r": round(float(g.phi_mean.corr(g.err_mean)), 3)}
                    for k, g in d.groupby("k")],
        "phi_silent_partial": [{"k": int(k),
                                "r": round(partial(g, "phi_mean", "silent_rate",
                                                   "err_mean"), 3)}
                               for k, g in d.groupby("k")],
        "phi_auc_partial": [{"k": int(k),
                             "r": round(partial(g, "phi_mean", "auc_unweighted",
                                                "err_mean"), 3)}
                            for k, g in d.groupby("k")],
    }


def partial(g: pd.DataFrame, x: str, y: str, z: str) -> float:
    """First-order partial correlation of x and y holding z fixed."""
    r = g[[x, y, z]].corr()
    rxy, rxz, ryz = r.loc[x, y], r.loc[x, z], r.loc[y, z]
    return float((rxy - rxz * ryz) / np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2)))


def rq1b_stats() -> dict:
    """Does the whole record beat confidence alone where the vote is blind?

    From `scripts/rq1_multifeature.py`. Two rows are enough for a page: the
    floor (confidence on its own, the number RQ1 stopped at) and the ceiling
    (every feature the record holds). Both are out-of-fold and both survived a
    leak audit -- see RESULTS.md Finding 8, which describes the two leaks that
    were caught before the table was believed.
    """
    src = path("processed", "rq1_multifeature.parquet")
    if not src.exists():
        return {}
    d = pd.read_parquet(src)
    lo = d.loc[d[d.features == "confidence mean only"].auc.idxmax()]
    hi = d.loc[d.auc.idxmax()]
    # No n here: the region size is already exported as rq1.agree_n, and two
    # fields for one quantity is how they drift apart.
    return {
        "base": round(float(hi.base), 4),
        "conf_auc": round(float(lo.auc), 4),
        "best_auc": round(float(hi.auc), 4),
        "best_features": str(hi.features),
        "conf_risk50": round(float(lo.risk_at_50), 4),
        "best_risk50": round(float(hi.risk_at_50), 4),
        "best_risk25": round(float(hi.risk_at_25), 4),
    }


def irr_stats() -> dict:
    """Inter-rater reliability, stratum-weighted. The figure the thesis lacked.

    Derived, never typed: this is the number an examiner asks for by name, and
    the one most likely to be quoted from memory into a slide.
    """
    import glob
    files = glob.glob(str(path("processed", "handlabels2_*.parquet")))
    if not files:
        return {}
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "hl2", Path(__file__).resolve().parent / "handlabel2.py")
    hl2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hl2)

    first = pd.read_parquet(path("processed", "handlabels.parquet"))         .set_index(["qid", "model"])["human"]
    sizes = hl2.strata_sizes()      # ISSUES #69: 385 + 45, from the frozen frame
    out = []
    for f in sorted(files):
        d = pd.read_parquet(f)
        d["first"] = [first.get((q, mo)) for q, mo in zip(d.qid, d.model)]
        k, po, n = hl2.weighted_kappa(d, first, sizes)
        rng = np.random.default_rng(hl2.SEED)   # the project seed, via the module that owns it
        boots = [hl2.weighted_kappa(d, first, sizes, rng)[0]
                 for _ in range(hl2.BOOTSTRAP_N)]
        lo, hi = np.nanpercentile(boots, [2.5, 97.5])
        out.append({
            "annotator": str(d.annotator.iloc[0]), "labelled": int(len(d)),
            "kappa": round(float(k), 3), "lo": round(float(lo), 3),
            "hi": round(float(hi), 3), "agreement": round(float(po), 4),
            "n_compared": int(n), "population": int(sum(sizes.values())),
            "unclear": round(float(d["second"].isna().mean()), 3),
        })
    return {"annotators": out, "kappa": out[0]["kappa"] if out else None,
            "strata": sizes}


def artifact_stats() -> dict:
    """How much of the blind region is an answer-key artifact, measured.

    Until 2026-08-25 this was 5.6%, an exact count of the CONTAINMENT artifact
    reported as though it bounded every artifact. Adjudicating all 1,054 blind
    spots directly puts it at 21.7%, and the judge's own calibration against the
    human says that is closer to a floor than a ceiling.

    Exported because "1,054" appears on every page in this project and must
    never appear again without this beside it.
    """
    src = path("processed", "adjudicated_blind.parquet")
    if not src.exists():
        return {}
    d = analysed(pd.read_parquet(src))
    m = d.judge.notna()
    k, n = int((d.loc[m, "judge"] == True).sum()), int(m.sum())   # noqa: E712

    def wilson(k_, n_):
        from math import sqrt
        if not n_:
            return 0.0, 0.0
        z, p_, D = 1.96, k_ / n_, 1 + 1.96 ** 2 / n_
        c = (p_ + z * z / (2 * n_)) / D
        h = z * sqrt(p_ * (1 - p_) / n_ + z * z / (4 * n_ * n_)) / D
        return round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)

    lo, hi = wilson(k, n)
    total = int(len(d))
    return {
        "n_judged": n, "n_total": total, "undecided": int((~m).sum()),
        "rate": round(k / n, 4), "lo": lo, "hi": hi,
        "genuine": int(round(total * (1 - k / n))),
        "by_dataset": [
            {"dataset": ds,
             "n": int(g.judge.notna().sum()),
             "rate": round(float((g.loc[g.judge.notna(), "judge"] == True).mean()), 4)}  # noqa: E712
            for ds, g in d.groupby("dataset") if g.judge.notna().any()],
        # Measured on the 430 where a human saw the same answers. Typed as
        # 0.968 / 0.161 (the alias-free run) until the 27 Sep re-run; derived
        # now, from the run the chapters cite.
        **judge_calibration(),
    }


def judge_calibration() -> dict:
    """Where the adjudicator says the grader was too strict, how often the
    human agrees; where it sides with the grader, how often the human still
    calls the answer correct. Both over the 430 hand-labelled cases."""
    p = path("processed", "adjudicated.parquet")
    if not p.exists():
        return {}
    d = pd.read_parquet(p)
    d = d[d.human.notna() & d.judge.notna() & (d.machine == False)]  # noqa: E712
    fl, sd = d[d.judge == True], d[d.judge == False]                  # noqa: E712
    return {"judge_precision": round(float((fl.human == True).mean()), 4),  # noqa: E712
            "judge_precision_k": int((fl.human == True).sum()),           # noqa: E712
            "judge_precision_n": int(len(fl)),
            "judge_misses": round(float((sd.human == True).mean()), 4),   # noqa: E712
            "judge_misses_k": int((sd.human == True).sum()),              # noqa: E712
            "judge_misses_n": int(len(sd))}


def _wilson(k: int, n: int) -> tuple[float, float]:
    from math import sqrt
    z, p, D = 1.96, k / n, 1 + 1.96 ** 2 / n
    c = (p + z * z / (2 * n)) / D
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / D
    return max(0.0, c - h), min(1.0, c + h)


def _wilson_hi(k: int, n: int) -> float:
    return _wilson(k, n)[1]


def belief_stats() -> dict:
    """Do the models HOLD the belief, or did they fail to find the fact?

    From `scripts/belief_arms.py`. Both arms carry a control, and the control is
    exported alongside every repair rate on purpose: a page that shows "repaired
    0.8%" without "broke 3.0%" is telling half a story, and the half it leaves
    out is the half that matters.
    """
    src = path("processed", "belief_arms.parquet")
    if not src.exists():
        return {}
    d = analysed(pd.read_parquet(src))
    g = (d.groupby(["arm", "stratum", "qid"])
           .agg(right=("correct", "sum"), abst=("abstained", "sum"),
                n=("correct", "size")).reset_index())
    g["repaired"] = g.right > g.n / 2
    out = {}
    for arm in sorted(g.arm.unique()):
        b = g[(g.arm == arm) & (g.stratum == "blind")]
        c = g[(g.arm == arm) & (g.stratum == "control")]
        out[arm] = {
            "n_blind": int(len(b)), "n_control": int(len(c)),
            "repaired": round(float(b.repaired.mean()), 4),
            "repaired_n": int(b.repaired.sum()),
            "broke": round(float((~c.repaired).mean()), 4),
            "broke_n": int((~c.repaired).sum()),
            # A 2-2 split counts as NOT right above, so a control question
            # that splits "broke" and a blind spot that splits was "not
            # repaired". Most of the control breakage is exactly those ties,
            # so the ratio of the two rates is exported beside the version
            # that needs a MAJORITY wrong to call a control broken.
            "broke_strict": round(float((c.right < c.n / 2).mean()), 4),
            "broke_strict_n": int((c.right < c.n / 2).sum()),
            "ties_blind": int((b.right == b.n / 2).sum()),
            "ties_control": int((c.right == c.n / 2).sum()),
            # Wilson upper bound on the repair rate: "repaired 0" needs its
            # bound beside it, and it was typed (0.36%) until 2026-09-27.
            "repaired_hi": round(_wilson_hi(int(b.repaired.sum()), len(b)), 4),
            "abstain_blind": round(float((b.abst > 0).mean()), 6),   # 6dp: 523/950 stored at 4dp read 55.0% for a 55.05% rate (double rounding)
            "abstain_control": round(float((c.abst > 0).mean()), 6),
        }
        kb, kc = int((b.abst > 0).sum()), int((c.abst > 0).sum())
        if kb or kc:
            from scipy.stats import fisher_exact
            out[arm].update({
                "abstain_blind_ci": [round(x, 4) for x in _wilson(kb, len(b))],
                "abstain_control_ci": [round(x, 4) for x in _wilson(kc, len(c))],
                "abstain_fisher_p": float(fisher_exact(
                    [[kb, len(b) - kb], [kc, len(c) - kc]])[1]),
                "abstain_ratio": round((kb / len(b)) / (kc / len(c)), 2) if kc else None,
            })
    return out


def adjudicator_stats() -> dict:
    """A third rater on the 430 hand labels. Supplementary, never a substitute.

    `self_own` / `self_other` are exported together because the adjudicator is
    an ensemble member, and the only honest way to publish that is beside the
    measurement of whether it mattered.
    """
    src = path("processed", "adjudicated.parquet")
    if not src.exists():
        return {}
    d = pd.read_parquet(src)

    def k(a, b):
        m = a.notna() & b.notna()
        x, y = a[m].astype(bool), b[m].astype(bool)
        if not len(x):
            return None
        po = float((x == y).mean())
        pe = float(x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean()))
        return round((po - pe) / (1 - pe), 3) if pe < 1 else None

    own = d.model.str.contains("Qwen", case=False)
    dis = d[d.human.notna() & d.judge.notna() &
            (d.human.astype(bool) != d.judge.astype(bool))]
    return {
        "n": int(len(d)),
        "human_judge": k(d.human, d.judge),
        "human_machine": k(d.human, d.machine),
        "judge_machine": k(d.judge, d.machine),
        "self_own": k(d[own].human, d[own].judge),
        "self_other": k(d[~own].human, d[~own].judge),
        "disagreements": int(len(dis)),
    }


WRITEUP = Path(__file__).resolve().parents[2] / "writeup"

# The eight chapters, in thesis order, with the target length each was planned
# at. `people` marks the one that cannot be written without participants.
CHAPTERS = [
    ("1", "Introduction", "ch1-introduction.md", 2500, False),
    ("2", "Related work", "ch2-related-work.md", 5000, False),
    ("3", "Design", "ch3-design.md", 6000, False),
    ("4", "Method", "ch4-method.md", 5000, False),
    ("5", "Results", "ch5-results.md", 8000, False),
    # No longer people-blocked: Chapter 6 is an ANALYTICAL evaluation --
    # cognitive walkthrough, discovery provenance, measured performance --
    # and it says at the top that the six-task study was not run.
    ("6", "Evaluation", "ch6-evaluation.md", 4000, False),
    ("7", "Limitations", "ch7-limitations.md", 3500, False),
    ("8", "Conclusion", "ch8-conclusion.md", 1500, False),
]


def writeup_stats() -> dict:
    """Thesis progress, counted rather than claimed.

    The deck reports where the project stands, and "the write-up" was a single
    row reading "not started" that somebody would have to remember to update.
    That is the shape of every stale number in ISSUES: a fact with no source.
    This counts the files.
    """
    rows, words, target = [], 0, 0
    for num, title, fname, plan, people in CHAPTERS:
        f = WRITEUP / fname
        w = len(f.read_text(encoding="utf-8").split()) if f.exists() else 0
        words += w
        target += plan
        rows.append({"n": num, "title": title, "words": w,
                     "target": plan, "people": people,
                     "state": "drafted" if w else ("blocked" if people else "todo")})
    return {"chapters": rows, "words": words, "target": target,
            "drafted": sum(1 for r in rows if r["state"] == "drafted"),
            "total": len(rows)}


def panel_data() -> dict:
    """Row-level data for the tool's three D3 panels.

    Deliberately NOT in summary.json: the deck needs the summaries only, and a
    5 KB payload nothing on that page reads is how files quietly become
    unexplainable. data.json already carries megabytes; this is noise there.
    """
    out: dict = {}
    src = path("processed", "ensemble_ablation.parquet")
    if src.exists():
        d = pd.read_parquet(src)
        d = d.assign(arm=d.models.map(
            lambda m: "2025" if set(m.split(" + ")) <= NEW_MODELS
            else ("2024" if not (set(m.split(" + ")) & NEW_MODELS) else "mixed")))
        out["frontier"] = [
            {"m": r.models, "k": int(r.k), "arm": r.arm,
             "phi": round(float(r.phi_mean), 4),
             "auc": round(float(r.auc_unweighted), 4),
             "silent": round(float(r.silent_rate), 5),
             "err": round(float(r.err_mean), 4)}
            for r in d.itertuples()]

    src = path("processed", "rq1_multifeature.parquet")
    if src.exists():
        d = pd.read_parquet(src)
        # One curve per feature set, boosted only -- the logistic rows say the
        # same thing less well and doubling the payload to show it is not worth
        # the panel's complexity.
        d = d[d.model == "boosted"] if "boosted" in set(d.model) else d
        out["riskcov"] = [
            {"features": r.features, "auc": round(float(r.auc), 4),
             "x": list(r.curve_x), "y": list(r.curve_y),
             "base": round(float(r.base), 5)}
            for r in d.itertuples()]
    return out


def independence_stats(ans: pd.DataFrame, rec: pd.DataFrame) -> dict:
    """The premise the whole disagreement heuristic rests on, measured.

    Every framing of this project asserted that four makers means four
    independent brains with independent mistakes, and `pipeline.html` L2 even
    carried a note saying the pairwise error correlation was worth measuring
    before committing. It was never measured, so the claim that leads the paper
    lived nowhere but in prose -- exactly the shape of ISSUES #54, a figure with
    no source.

    It is exported here so it CANNOT be typed. Everything below is derived from
    answers.parquet on every run:

      phi   pairwise error correlation. For two binary variables the phi
            coefficient IS Pearson's r, so np.corrcoef is the whole computation.
            Independence would be 0.
      ratio observed P(all four wrong) over the product of the four individual
            error rates. That product is what independence predicts; the ratio
            is how far the premise is off.

    Measured 2026-08-25: phi = 0.667, ratio = 9.0x. See DECISIONS.md that date.

    STRATIFIED, since 2026-09-27 (ISSUES #68). The pooled ratio multiplies
    error rates averaged over four datasets whose difficulty differs six-fold
    (TriviaQA ~7% wrong, PopQA ~45%). Pooling alone manufactures co-failure: a
    hard question is hard for everyone, and a hard DATASET is a large block of
    hard questions. Independence is therefore tested WITHIN each dataset, and
    the headline is the stratified ratio -- observed all-wrong questions summed
    over datasets, against the sum of what within-dataset independence
    predicts. The pooled figures stay exported so the difference is visible
    rather than silently replaced.
    """
    w = (ans.assign(wrong=~ans["correct"].astype(bool))
            .pivot_table(index="qid", columns="model", values="wrong",
                         aggfunc="first"))
    # A question missing any model cannot enter either side of the comparison.
    # There are none today; dropping rather than filling means a future gap
    # shrinks n visibly instead of silently biasing the product downward.
    w = w.dropna().astype(bool)
    models = sorted(w.columns)

    raw_phi = [float(np.corrcoef(w[a], w[b])[0, 1])
               for i, a in enumerate(models) for b in models[i + 1:]]
    pairs = [{"a": short(a), "b": short(b), "phi": round(f, 4)}
             for (a, b), f in zip(((a, b) for i, a in enumerate(models)
                                   for b in models[i + 1:]), raw_phi)]

    observed = float(w.all(axis=1).mean())
    predicted = float(np.prod([float(w[m].mean()) for m in models]))

    dsof = rec.set_index("qid").dataset
    per, obs_sum, exp_sum = [], 0.0, 0.0
    for ds in DATASETS:
        wd = w[w.index.map(dsof) == ds]
        if len(wd) < 2:
            continue
        o = int(wd.all(axis=1).sum())
        e = float(np.prod([float(wd[m].mean()) for m in models])) * len(wd)
        ph = [float(np.corrcoef(wd[a], wd[b])[0, 1])
              for i, a in enumerate(models) for b in models[i + 1:]]
        obs_sum += o
        exp_sum += e
        per.append({"dataset": ds, "n": int(len(wd)),
                    "all_wrong": round(o / len(wd), 5),
                    "all_wrong_if_independent": round(e / len(wd), 5),
                    "ratio": round(o / e, 2) if e else None,
                    "phi_mean": round(sum(ph) / len(ph), 4)})

    return {
        "n": int(len(w)),
        "stratified": {"observed": int(obs_sum), "expected": round(exp_sum, 1),
                       "ratio": round(obs_sum / exp_sum, 2),
                       "phi_min": min(x["phi_mean"] for x in per),
                       "phi_max": max(x["phi_mean"] for x in per),
                       "by_dataset": per},
        "models": [short(m) for m in models],
        "error_rates": {short(m): round(float(w[m].mean()), 5) for m in models},
        "pairs": pairs,
        # from the unrounded pairs, 5 dp: the mean of 4-dp pairs re-rounded
        # to 0.6535 for a true 0.653516 and printed as 0.653 (2026-09-30)
        "phi_mean": round(sum(raw_phi) / len(raw_phi), 5),
        "all_wrong": round(observed, 5),
        "all_wrong_if_independent": round(predicted, 5),
        "ratio": round(observed / predicted, 2),
    }


def signal_stats(rec: pd.DataFrame) -> dict:
    """Per-dataset AUC + base rates. The 'how much should I trust the signal
    HERE' panel: 0.840 overall hides 0.683 on one dataset and 0.861 on another, and
    a user who filters to one dataset needs the local number.

    RESULTS.md quotes the UNWEIGHTED per-dataset figures (0.793 / 0.861 / 0.810 /
    0.683). Both are exported and labelled: the first draft of this function
    computed `auc` and `auc_weighted` from the same column, so the page would have
    shown two identical numbers under different names AND disagreed with
    RESULTS.md by 0.005 with no way to see why.
    """
    def pair(d: pd.DataFrame) -> dict:
        return {
            "auc": round(float(roc_auc_score(
                d.majority_wrong, d.disagreement_unweighted)), 3),
            "auc_weighted": round(float(roc_auc_score(
                d.majority_wrong, d.disagreement)), 3),
            "base": round(float(d.majority_wrong.mean()), 4),
            "silent": int(d.silent_consensus.sum()),
            "n": len(d),
        }

    out = {"overall": pair(rec), "by_dataset": []}
    for ds in DATASETS:
        d = rec[rec.dataset == ds]
        if d.empty or d.majority_wrong.nunique() < 2:
            continue
        out["by_dataset"].append({"dataset": ds, **pair(d)})
    return out


def baseline_stats(rec: pd.DataFrame) -> dict:
    """The competitor: single-model Semantic Entropy on the same questions.

    Scored on the 8,000-question stratified subset both arms share, so
    composition cannot bias it (RESULTS.md Finding 3).
    """
    b = pd.read_parquet(path("interim", "baseline.parquet"))
    r = rec.set_index("qid")
    rows = []
    for m, g in b.groupby("model"):
        g = g[g.qid.isin(r.index)]
        y = r.loc[g.qid, "majority_wrong"].values
        if len(set(y)) < 2:
            continue
        rows.append({"model": short(m),
                     "auc": round(float(roc_auc_score(y, g.semantic_entropy)), 3)})
    rows.sort(key=lambda x: -x["auc"])
    sub = r.loc[r.index.intersection(b.qid.unique())]
    return {
        "single_model": rows,
        # UNWEIGHTED, deliberately. This is the head-to-head against a competing
        # method, and it used to run on the confidence-weighted score (0.864)
        # while the headline AUC on the same page ran on the head-count (0.862).
        # Two numbers for one measurement, with the flattering one placed next to
        # the competitor -- the least defensible arrangement available. Weighting
        # is worth +0.003 at full corpus and it HURT at 7-9B (0.776 vs 0.788), so
        # there is nothing to buy with it and something to lose. Head-count
        # everywhere. See DECISIONS 2026-08-03.
        "cross_model_same_qids": round(float(roc_auc_score(
            sub.majority_wrong, sub.disagreement_unweighted)), 3),
        "n": int(len(sub)),
    }


def rq4_frame() -> pd.DataFrame:
    """RQ4 rows that are results. An empty answer is a failed call, not a wrong
    answer (standing rule 1); 15 of them sat in the parquet as wrong answers
    until 2026-09-27 because the loop appended them and only a resume filtered
    them (ISSUES #70). Dropped here as well as re-run, so a future failure
    shrinks n visibly instead of reading as retrieval failing."""
    q = analysed(pd.read_parquet(path("processed", "rq4_retrieval.parquet")))
    ok = pd.Series(True, index=q.index)
    for c in ("answer_cb", "answer_rag"):
        if c in q.columns:
            ok &= q[c].fillna("").astype(str).str.strip().ne("")
    return q[ok]


def rq4_stats() -> dict:
    q = rq4_frame()
    # Definition must MATCH RESULTS.md Finding 5: rates over the WHOLE stratum,
    # lift = retrieval - closed-book. The first draft computed "fraction of
    # closed-book failures that retrieval fixed" instead, which is also a valid
    # quantity but gave 71.7%/31.4% against the recorded +68%/+16% -- two
    # different numbers for one finding, one of them on a public page.
    out = []
    for cause, g in q.groupby("cause"):
        cb, rag = float(g.closedbook_ok.mean()), float(g.retrieved_ok.mean())
        out.append({"cause": cause, "n": int(len(g)),
                    "closedbook": round(cb, 3), "retrieved": round(rag, 3),
                    "lift": round(rag - cb, 3)})
    return {"by_cause": sorted(out, key=lambda x: -x["lift"])}


def rq5_stats() -> dict:
    """The matched Wikipedia-vs-open-web comparison, recomputed here.

    MATCHED is the whole point. The wiki arm covers 977 complete questions and
    the web arm 148; quoting 24.7% against 29.1% would compare different
    question sets and the difference would be composition, not the tool. Both
    arms are restricted to the questions that completed with ALL FOUR models in
    BOTH arms -- 131 of them.

    'Rescued' = at least one of the four models got it right once it could
    search. These are silent-consensus questions, so all four were wrong
    closed-book by construction; one model recovering is already the weakest
    bar that counts as the tool helping.
    """
    def complete(p):
        g = blind_only(pd.read_parquet(path("processed", p))).groupby("qid")
        d = g.agg(n=("model", "nunique"), rescued=("correct", "any"))
        return d[d.n == 4]

    wiki, web = complete("rq5_agentic.parquet"), complete("rq5_agentic_web.parquet")
    m = sorted(set(wiki.index) & set(web.index))
    w, b = wiki.loc[m, "rescued"], web.loc[m, "rescued"]
    return {"matched": len(m),
            "wiki": int(w.sum()), "web": int(b.sum()),
            "wiki_rate": round(float(w.mean()), 3),
            "web_rate": round(float(b.mean()), 3),
            "neither": int((~w & ~b).sum()),
            "neither_rate": round(float((~w & ~b).mean()), 3),
            "both": int((w & b).sum()),
            "web_only": int((b & ~w).sum()), "wiki_only": int((w & ~b).sum()),
            # the full wiki arm, for "and this is not a sampling artefact"
            "wiki_arm_n": int(len(wiki)), "web_arm_n": int(len(web))}


def intervals_stats(rec: pd.DataFrame, loc: pd.DataFrame,
                    ans: pd.DataFrame) -> dict:
    """Every claim's interval and test, DERIVED. ISSUES #77.

    Until 2026-09-27 the "Every claim, with its interval" table in RESULTS.md
    was "computed read-only from the stored parquet records" -- by hand, once,
    on 2026-08-25. No script could recompute it, so when the corpus changed
    every interval in the thesis went stale at once and nothing noticed. Now
    they are computed here on every export and check_writeup asserts them.
    """
    from math import sqrt
    from scipy.stats import binomtest, mannwhitneyu
    from faultlines.config import CFG
    rng = np.random.default_rng(CFG["seed"])
    B = 4000

    def wilson(k, n):
        z, p, D = 1.96, k / n, 1 + 1.96 ** 2 / n
        c = (p + z * z / (2 * n)) / D
        h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / D
        return round(max(0.0, c - h), 5), round(min(1.0, c + h), 5)

    def hanley(y, s):
        a = float(roc_auc_score(y, s))
        n1, n0 = int(np.sum(y)), int(len(y) - np.sum(y))
        q1, q2 = a / (2 - a), 2 * a * a / (1 + a)
        se = sqrt((a * (1 - a) + (n1 - 1) * (q1 - a * a)
                   + (n0 - 1) * (q2 - a * a)) / (n1 * n0))
        return a, se

    def paired_diff(b, c, n):
        """McNemar exact p and a Wald interval for a paired difference of
        proportions, (c - b) / n, from the discordant counts."""
        d = (c - b) / n
        se = sqrt(max(b + c - (c - b) ** 2 / n, 0)) / n
        p = float(binomtest(min(b, c), b + c, 0.5).pvalue) if b + c else 1.0
        return round(d, 5), round(d - 1.96 * se, 5), round(d + 1.96 * se, 5), p

    out: dict = {}
    y = rec.majority_wrong.astype(int).to_numpy()

    # 1 - headline AUC
    a, se = hanley(y, rec.disagreement_unweighted.to_numpy())
    out["auc"] = {"auc": round(a, 4), "lo": round(a - 1.96 * se, 4),
                  "hi": round(a + 1.96 * se, 4), "test": "Hanley-McNeil"}
    out["auc_by_dataset"] = []
    for ds in DATASETS:
        d = rec[rec.dataset == ds]
        yd = d.majority_wrong.astype(int).to_numpy()
        if yd.min() == yd.max():
            continue
        a, se = hanley(yd, d.disagreement_unweighted.to_numpy())
        out["auc_by_dataset"].append({
            "dataset": ds, "n": int(len(d)), "auc": round(a, 3),
            "lo": round(a - 1.96 * se, 3), "hi": round(a + 1.96 * se, 3),
            "width": round(2 * 1.96 * se, 3)})

    # 2 - cross-model vs the best single-model Semantic Entropy, paired
    b = pd.read_parquet(path("interim", "baseline.parquet"))
    b = b[b.qid.isin(rec.qid)]
    r = rec.set_index("qid")
    best, best_auc = None, -1.0
    for m, g in b.groupby("model"):
        yy = r.loc[g.qid, "majority_wrong"].astype(int).to_numpy()
        aa = roc_auc_score(yy, g.semantic_entropy)
        if aa > best_auc:
            best, best_auc = m, aa
    g = b[b.model == best].set_index("qid")
    qs = g.index.to_numpy()
    yy = r.loc[qs, "majority_wrong"].astype(int).to_numpy()
    cm = r.loc[qs, "disagreement_unweighted"].to_numpy()
    se_ = g.loc[qs, "semantic_entropy"].to_numpy()
    delta = roc_auc_score(yy, cm) - roc_auc_score(yy, se_)
    boots = []
    for _ in range(B):
        i = rng.integers(0, len(qs), len(qs))
        if yy[i].min() == yy[i].max():
            continue
        boots.append(roc_auc_score(yy[i], cm[i]) - roc_auc_score(yy[i], se_[i]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    out["vs_semantic_entropy"] = {
        "model": short(best), "n": int(len(qs)), "delta": round(float(delta), 4),
        "lo": round(float(lo), 4), "hi": round(float(hi), 4),
        "p_le_0": round(float(np.mean(np.array(boots) <= 0)), 5),
        "test": f"paired bootstrap, {B} resamples"}

    # 3 - blind-spot rate
    k, n = int(rec.silent_consensus.sum()), len(rec)
    lo, hi = wilson(k, n)
    out["blind_rate"] = {"k": k, "n": n, "rate": round(k / n, 5),
                         "lo": lo, "hi": hi, "test": "Wilson"}

    # 5 - share of errors that are shared, 2024 -> 2025, paired over questions
    li = loc.set_index("qid").loc[rec.qid]
    s25, m25 = rec.silent_consensus.to_numpy(bool), rec.majority_wrong.to_numpy(bool)
    s24, m24 = li.silent_consensus.to_numpy(bool), li.majority_wrong.to_numpy(bool)
    ratio = (s25.sum() / m25.sum()) / (s24.sum() / m24.sum())
    rb = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        rb.append((s25[i].sum() / m25[i].sum()) / (s24[i].sum() / m24[i].sum()))
    rb = np.array(rb)
    out["share_ratio"] = {
        "share_2024": round(float(s24.sum() / m24.sum()), 5),
        "share_2025": round(float(s25.sum() / m25.sum()), 5),
        "ratio": round(float(ratio), 4),
        "lo": round(float(np.percentile(rb, 2.5)), 4),
        "hi": round(float(np.percentile(rb, 97.5)), 4),
        "p_le_1": round(float(np.mean(rb <= 1)), 5),
        "test": f"paired bootstrap, {B} resamples"}

    # 5b - the blind-spot rate itself rises, paired
    healed, emerged = int((s24 & ~s25).sum()), int((s25 & ~s24).sum())
    d, lo, hi, p = paired_diff(healed, emerged, n)
    out["blind_rise"] = {"from": round(float(s24.mean()), 5),
                         "to": round(float(s25.mean()), 5),
                         "delta": d, "lo": lo, "hi": hi, "p": p,
                         "healed": healed, "emerged": emerged,
                         "test": "McNemar exact"}

    # 8 - RQ4, each arm paired, and the dissociation
    q = rq4_frame()
    rq4 = {}
    arms = {}
    for cause, g in q.groupby("cause"):
        cb, rt = g.closedbook_ok.astype(bool).to_numpy(), g.retrieved_ok.astype(bool).to_numpy()
        d, lo, hi, p = paired_diff(int((cb & ~rt).sum()), int((rt & ~cb).sum()), len(g))
        rq4[cause] = {"n": int(len(g)), "lift": d, "lo": lo, "hi": hi, "p": p}
        arms[cause] = (cb, rt)
    if {"obscurity", "misconception"} <= set(arms):
        (c1, r1), (c2, r2) = arms["obscurity"], arms["misconception"]
        dis = (r1.mean() - c1.mean()) - (r2.mean() - c2.mean())
        db = []
        rng10 = np.random.default_rng(CFG["seed"])
        for _ in range(10000):
            i = rng10.integers(0, len(c1), len(c1))
            j = rng10.integers(0, len(c2), len(c2))
            db.append((r1[i].mean() - c1[i].mean()) - (r2[j].mean() - c2[j].mean()))
        db = np.array(db)
        rq4["dissociation"] = {"delta": round(float(dis), 5),
                               "lo": round(float(np.percentile(db, 2.5)), 5),
                               "hi": round(float(np.percentile(db, 97.5)), 5),
                               "p_le_0": round(float(np.mean(db <= 0)), 5),
                               "test": "10,000 bootstrap"}
    out["rq4"] = rq4

    # 13 - RQ5 ceiling, and the wiki-vs-web difference that is noise
    s = rq5_stats()
    lo, hi = wilson(s["neither"], s["matched"])
    d, dlo, dhi, p = paired_diff(s["wiki_only"], s["web_only"], s["matched"])
    out["rq5"] = {"neither": s["neither"], "matched": s["matched"],
                  "rate": round(s["neither"] / s["matched"], 4), "lo": lo, "hi": hi,
                  "web_minus_wiki": d, "wd_lo": dlo, "wd_hi": dhi, "wd_p": p}

    # RQ1 - confidence inside the agreement region
    conf = ans.groupby("qid").confidence.mean()
    u = rec.set_index("qid").assign(conf=conf)
    u = u[u.n_clusters == 1]
    yu = u.majority_wrong.astype(int).to_numpy()
    a, se = hanley(yu, -u.conf.to_numpy())
    w_, r_ = u.conf[yu == 1], u.conf[yu == 0]
    pooled = sqrt(((len(w_) - 1) * w_.var() + (len(r_) - 1) * r_.var())
                  / (len(w_) + len(r_) - 2))
    out["rq1"] = {"auc": round(a, 4), "lo": round(a - 1.96 * se, 3),
                  "hi": round(a + 1.96 * se, 3), "z": round((a - 0.5) / se, 1),
                  "mw_p": float(mannwhitneyu(r_, w_, alternative="greater").pvalue),
                  "cohen_d": round(float((r_.mean() - w_.mean()) / pooled), 2)}
    base = float(yu.mean())
    rows = []
    for t in (0.900, 0.941, 0.970):
        ab = (u.conf < t).to_numpy()
        caught, lost = int((ab & (yu == 1)).sum()), int((ab & (yu == 0)).sum())
        prec = caught / max(1, ab.sum())
        rows.append({"t": t, "abstains": int(ab.sum()),
                     "caught": caught, "caught_pct": round(caught / yu.sum(), 3),
                     "lost": lost, "lost_pct": round(lost / (yu == 0).sum(), 3),
                     "precision": round(prec, 3), "lift": round(prec / base, 2)})
    out["abstain_table"] = {"base": round(base, 4), "rows": rows}

    # 12 - the stratified concordance ratio, bootstrapped within each dataset
    W = (ans.assign(w=~ans.correct.astype(bool))
            .pivot_table(index="qid", columns="model", values="w", aggfunc="first")
            .dropna().astype(bool))
    dsof = rec.set_index("qid").dataset
    blocks = [W[W.index.map(dsof) == ds].to_numpy() for ds in DATASETS]
    blocks = [x for x in blocks if len(x)]

    def strat_ratio(bs):
        o = sum(x.all(1).sum() for x in bs)
        e = sum(np.prod(x.mean(0)) * len(x) for x in bs)
        return o / e
    sb = [strat_ratio([x[rng.integers(0, len(x), len(x))] for x in blocks])
          for _ in range(2000)]
    # 4dp: a 3dp 3.405 formats to "3.40" for a bound that rounds to 3.41 --
    # the double-rounding defect of the deck's 6.63%/6.62%. Round at display.
    out["concordance"] = {"ratio": round(float(strat_ratio(blocks)), 4),
                          "lo": round(float(np.percentile(sb, 2.5)), 4),
                          "hi": round(float(np.percentile(sb, 97.5)), 4),
                          "test": "2,000 bootstrap, resampled within dataset"}
    return out


def funnel_stats(rec: pd.DataFrame) -> dict:
    """How 34,062 questions narrow to the 950 the tool is built for.

    Note what this is NOT: nothing is discarded. Every question stays in the
    corpus, in the map and in the AUC. This is the DEFINITION of the audit
    population, and stating it as a funnel is the only honest way to show that
    the headline 950 is 2.8% of the corpus and 6.8% of the questions the
    ensemble answers wrong.
    """
    n = len(rec)
    return {"total": n,
            "any_wrong": int(rec.any_wrong.sum()),
            "majority_wrong": int(rec.majority_wrong.sum()),
            "all_wrong": int(rec.all_wrong.sum()),
            "unanimous": int((rec.n_clusters == 1).sum()),
            "silent": int(rec.silent_consensus.sum())}


def abstain_stats(rec: pd.DataFrame, ans: pd.DataFrame) -> dict:
    """"Just make it say 'I don't know' when confidence is low" -- measured.

    The single most common suggestion this project receives, and the one RQ1's
    AUC 0.600 answers only obliquely. A ranking AUC does not tell a reader what
    an actual abstention policy would cost, so this computes the policy directly:
    refuse every answer below a confidence threshold, and report both sides of
    the trade -- errors caught AND correct answers destroyed.

    Restricted to the agreement region on purpose. That is where the proposal is
    the only one available (vote-counting is 0.00 there by construction), so it
    is where it deserves its fairest hearing. It still fails.

    Everything here is DERIVED. Nothing about this table may be typed into a
    slide as a literal -- see ISSUES #43, which was exactly that mistake in this
    same file.
    """
    conf = ans.groupby("qid").confidence.mean()
    u = rec.set_index("qid").assign(conf=conf)
    u = u[u.n_clusters == 1]
    wrong, right = u.majority_wrong, ~u.majority_wrong
    n_w, n_r = int(wrong.sum()), int(right.sum())

    def at(t):
        ab = u.conf < t
        return {"t": round(float(t), 3),
                "caught": round(float((ab & wrong).sum() / n_w), 3),
                "lost": round(float((ab & right).sum() / n_r), 3)}

    # the inverse question -- "to catch HALF the errors, what does it cost?"
    def cost_to_catch(target):
        for t in np.linspace(0.5, 1.0, 2001):
            if (u.conf < t)[wrong].mean() >= target:
                return {"target": target,
                        "t": round(float(t), 3),
                        "lost": round(float((u.conf < t)[right].mean()), 3)}
        return {"target": target, "t": None, "lost": None}

    return {"n": int(len(u)), "n_wrong": n_w, "n_right": n_r,
            "conf_right": round(float(u.loc[right, "conf"].mean()), 3),
            "conf_wrong": round(float(u.loc[wrong, "conf"].mean()), 3),
            "curve": [at(t) for t in (0.80, 0.90, 0.95, 0.97, 0.99)],
            "targets": [cost_to_catch(x) for x in (0.5, 0.8)]}


def count_tests() -> int:
    """How many tests the suite has, counted from the files.

    Only valid while every test is a plain `def test_*` with no parametrisation
    -- true today (70 functions, 70 collected). The moment someone adds
    @pytest.mark.parametrize the two diverge, so this refuses to guess: it
    raises, and the export fails loudly rather than shipping a smaller number
    than pytest would print.
    """
    d = Path(__file__).resolve().parents[1] / "tests"
    src = "\n".join(f.read_text(encoding="utf-8") for f in d.glob("test_*.py"))
    if "parametrize" in src:
        raise SystemExit("count_tests: parametrised tests present -- "
                         "a `def test_` count no longer equals the collected count")
    return len(re.findall(r"^\s*def test_", src, re.M))


def walkthrough_stats(rec: pd.DataFrame, loc: pd.DataFrame) -> dict:
    """Figures the walkthrough page states, derived rather than typed.

    The page is a narrative document, which is exactly the kind of artifact that
    accumulated #43/#45/#46/#47/#49 -- prose nobody re-reads, holding numbers
    with a live source. Building it with literals would have been the same
    mistake in a sixth file, so every statistic it shows comes from here.

    Case transcripts on the page ARE literal: they are quotations of four fixed
    model answers, not measurements, and a quotation that silently changed would
    be worse than one that went stale.
    """
    base = float(rec.silent_consensus.mean())

    def pattern(rx: str) -> dict:
        g = rec[rec.question.str.contains(rx, regex=True, na=False)]
        return {"n": int(len(g)),
                "blind": int(g.silent_consensus.sum()),
                "rate": round(float(g.silent_consensus.mean()), 4),
                "wrong": round(float(g.majority_wrong.mean()), 4),
                "unanimous": round(float((g.n_clusters == 1).mean()), 4)}

    pats = [("director of X", r"^Who was the director of"),
            ("genre of X", r"^What genre is"),
            ("author of X", r"^Who is the author of"),
            ("crew role of X", r"^Who was the (?:screenwriter|producer|composer)"),
            ("birthplace of X", r"^In what city was .* born"),
            ("capital of X", r"^What is the capital of")]

    # the within-template split: same question form, one variable
    tit = pd.read_parquet(path("interim", "popqa_wiki_titles.parquet"))
    tm = {q: (str(t), str(s)) for q, t, s
          in zip(tit.question, tit.s_wiki_title, tit.subj)}

    def is_shared(q: str) -> bool:
        got = tm.get(q)
        if not got or got[0] in ("", "nan") or got[1] in ("", "nan"):
            return False
        t, s = got
        return t != s and (t.startswith(s + ",") or t.startswith(s + " ("))

    d = rec[rec.question.str.startswith("Who was the director of", na=False)].copy()
    d = d[d.dataset == "popqa"]
    sh = np.array([is_shared(q) for q in d.question], dtype=bool)

    # W2: what the "newly hidden" were doing in 2024
    s3 = set(rec.loc[rec.silent_consensus, "qid"])
    s2 = set(loc.loc[loc.silent_consensus, "qid"])
    emerged = sorted(s3 - s2)
    li = loc.set_index("qid")
    return {
        "base": round(base, 4),
        "patterns": [{"name": n, **pattern(rx)} for n, rx in pats],
        "director": {
            "unique": {"n": int((~sh).sum()),
                       "rate": round(float(d.silent_consensus[~sh].mean()), 4)},
            "shared": {"n": int(sh.sum()),
                       "rate": round(float(d.silent_consensus[sh].mean()), 4)},
        },
        "emerged": {
            "n": len(emerged),
            "already_allwrong": int(li.loc[emerged, "all_wrong"].sum()),
            "had_correct": int((~li.loc[emerged, "majority_wrong"]).sum()),
        },
    }


def artifact_arms(blind: dict | None = None) -> dict | None:
    """The grading-artifact rate in BOTH arms, and RQ3 rebuilt on genuine cases.

    Added 2026-08-26 with the 2024 adjudication. Until then only the 2025 arm
    had been judged, and ch7 argued the RQ3 comparison survived the artifact
    correction because both arms share a grader so strictness cancels. It does
    not cancel: it is 4.9 points larger on the newer arm under the primary judge
    and 7.3 under an outside one.

    Two judges are exported, not one, and the outside judge is the point.
    Qwen3-235B is IN the 2025 ensemble and -- because the representative answer
    is the first model in sorted order -- judged its own answer in all 1,054
    2025 cases while judging gemma2:9b's in 2024 (ISSUES #58). Olmo-3.1-32B is
    in neither arm. If self-favouring drove the gap the outside judge would
    shrink it; it widens it, so the gap is not that.

    Everything here derives. `scripts/artifact_by_arm.py` prints the same
    figures with the reasoning attached, and check_writeup asserts the chapters
    against this block.
    """
    files = {
        "qwen": {"label": "Qwen3-235B", "inside": True,
                 "2024": "adjudicated_blind_2024.parquet",
                 "2025": "adjudicated_blind.parquet"},
        "olmo": {"label": "Olmo-3.1-32B", "inside": False,
                 "2024": "adjudicated_blind_2024_outside2.parquet",
                 "2025": "adjudicated_blind_outside2.parquet"},
    }
    def wilson(k_, n_):
        # export_web's other Wilson lives inside another function; rather than
        # hoist it and touch a working call site, this is the same four lines.
        from math import sqrt
        if not n_:
            return 0.0, 0.0
        z, ph, D = 1.96, k_ / n_, 1 + 1.96 ** 2 / n_
        c = (ph + z * z / (2 * n_)) / D
        h = z * sqrt(ph * (1 - ph) / n_ + z * z / (4 * n_ * n_)) / D
        return max(0.0, c - h), min(1.0, c + h)

    out = {"judges": [], "primary": "qwen"}
    for key, f in files.items():
        arms, gen = {}, {}
        for a in ("2024", "2025"):
            fp = path("processed", f[a])
            if not fp.exists():
                return None
            d = pd.read_parquet(fp)
            if blind is not None:
                d = d[d.qid.isin(blind[a])]
            k = int((d.judge == True).sum())              # noqa: E712
            lo, hi = wilson(k, len(d))
            arms[a] = {"n": int(len(d)), "artifacts": k,
                       "rate": round(k / len(d), 4),
                       "lo": round(lo, 4), "hi": round(hi, 4),
                       "genuine": int(len(d) - k),
                       "unclear": int(d.judge.isna().sum())}
            # UNCLEAR stays IN the blind region: not-overturned is the
            # conservative direction and cannot manufacture a correction.
            gen[a] = set(d.qid) - set(d.loc[d.judge == True, "qid"])  # noqa: E712
        per = len(gen["2024"] & gen["2025"])
        # The gap's test, and the same test inside each dataset. These were
        # read off artifact_by_arm.py's printout and typed into ch4/ch5/ch7
        # (p = 0.007, "not significant in any single dataset") and went stale
        # with the 27 Sep re-run -- ISSUES #77's shape. Now they derive.
        from math import erfc, sqrt as _sqrt

        def two_prop_p(k1, n1, k2, n2):
            if not n1 or not n2:
                return 1.0
            pp = (k1 + k2) / (n1 + n2)
            se = _sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
            return 1.0 if se == 0 else erfc(abs((k2 / n2 - k1 / n1) / se) / _sqrt(2))

        raw = {}
        for a in ("2024", "2025"):
            d = pd.read_parquet(path("processed", f[a]))
            raw[a] = d[d.qid.isin(blind[a])] if blind is not None else d
        by_ds = {}
        for ds in sorted(set(raw["2024"].dataset) | set(raw["2025"].dataset)):
            g1 = raw["2024"][raw["2024"].dataset == ds]
            g2 = raw["2025"][raw["2025"].dataset == ds]
            k1, k2 = int((g1.judge == True).sum()), int((g2.judge == True).sum())  # noqa: E712
            by_ds[ds] = {"n_2024": len(g1), "n_2025": len(g2),
                         "rate_2024": round(k1 / len(g1), 4) if len(g1) else None,
                         "rate_2025": round(k2 / len(g2), 4) if len(g2) else None,
                         "p": round(two_prop_p(k1, len(g1), k2, len(g2)), 4)}
        out["judges"].append({
            "key": key, "label": f["label"], "in_ensemble": f["inside"],
            "arm": arms,
            "gap": round(arms["2025"]["rate"] - arms["2024"]["rate"], 4),
            "p_gap": round(two_prop_p(arms["2024"]["artifacts"], arms["2024"]["n"],
                                      arms["2025"]["artifacts"], arms["2025"]["n"]), 5),
            "by_dataset": by_ds,
            "rq3": {"persisted": per,
                    "healed": len(gen["2024"] - gen["2025"]),
                    "emerged": len(gen["2025"] - gen["2024"]),
                    "ratio": round(len(gen["2025"] - gen["2024"]) / per, 5),
                    # exact McNemar on healed vs emerged: is the genuine blind
                    # region larger in 2025? Paired, because both arms answered
                    # the same questions (ISSUES #74).
                    "p_growth": round(float(__import__("scipy.stats", fromlist=["x"])
                                            .binomtest(min(len(gen["2024"] - gen["2025"]),
                                                           len(gen["2025"] - gen["2024"])),
                                                       len(gen["2024"] ^ gen["2025"]),
                                                       0.5).pvalue), 5)},
            "genuine": {a: len(gen[a]) for a in ("2024", "2025")},
            # 5dp, not 3: at 3dp Olmo's 2.03474 stores as 2.035 and any
            # consumer formatting to 2dp gets 2.04 for a value that rounds
            # to 2.03. Double-rounding, the same defect as the deck's
            # 6.63%-for-6.62%. Round ONCE, at the point of display.
        })
    return out


def grader_check() -> dict:
    """Did the automatic grader lean generous or harsh? The hand-labels answer.

    Scoped to the TARGET stratum, which is what RESULTS' "31 generous vs 39
    harsh" means and what the deck quotes. Corpus-wide it is 31 vs 40 -- the
    control stratum contributes exactly one disagreement -- so the conclusion is
    identical either way, but the scope has to travel with the pair or the two
    documents look like they disagree. Exported 2026-08-08 because the deck had
    the numbers typed and unscoped.

    `.astype(bool)` after `dropna` is not decoration: `human` is an object
    column holding None for unjudged cases, and `~` on object dtype returns
    integers (-1, -2) instead of raising -- the hazard behind ISSUES #36 and one
    this audit hit again while checking this very figure.
    """
    hl = pd.read_parquet(path("processed", "handlabels.parquet"))
    j = hl.dropna(subset=["human"]).copy()
    j["human"] = j.human.astype(bool)
    j["machine"] = j.machine.astype(bool)
    assert j.human.dtype == bool and j.machine.dtype == bool
    t = j[j.stratum == "target"]
    return {"stratum": "target", "judged": int(len(t)),
            "generous": int((t.machine & ~t.human).sum()),
            "harsh": int((~t.machine & t.human).sum())}


def rq1_rq2_stats(rec: pd.DataFrame, ans: pd.DataFrame) -> dict:
    """RQ1's agreement-region AUC and RQ2's popularity control.

    Added 2026-08-08 so `pipeline.html` can stop typing them. Both were quoted
    on that page at their 300-question pilot values -- 0.653 and -0.639/-0.353 --
    which is ISSUES #47: the page had no exporter behind it, so nothing could
    notice when the full run moved them.

    RQ2's two correlations are computed on the popularity subset, which is PopQA
    and only PopQA -- the other three benchmarks have no pageview count, so a
    corpus-wide correlation against `popularity` is NaN. Restricting is what
    makes -0.309 reproduce; stating why is what stops someone "fixing" it later
    by dropping the subset.
    """
    conf = ans.groupby("qid").confidence.mean()
    u = rec.set_index("qid").assign(conf=conf)
    u = u[u.n_clusters == 1]
    agree_auc = roc_auc_score(u.majority_wrong.astype(int), -u.conf)

    loc = pd.read_parquet(path("processed", "rq2_localize.parquet"))
    s = loc.dropna(subset=["popularity"])
    y = s.majority_wrong.astype(int)
    # The popularity control's AUCs. rq2_localize printed them and nothing
    # stored them, so the chapters quoted a lift no check could reach.
    from faultlines.rq2_localize import popularity_control
    ctrl = popularity_control(rec)
    return {
        "rq1": {"agree_auc": round(float(agree_auc), 3), "agree_n": int(len(u))},
        # Two densities, on purpose. `density` is computed over the shared map
        # and is what the tool draws; `density_within_dataset` recomputes
        # neighbours inside PopQA and is what the popularity control rests on.
        # 28.1% of a PopQA question's map-neighbours are from another dataset,
        # so these are genuinely different quantities -- AUDIT n1, closed
        # 2026-08-25. Exporting both stops a page quoting one as the other.
        "rq2": {"corr_pop": round(float(np.corrcoef(s.popularity, y)[0, 1]), 3),
                "corr_density": round(float(np.corrcoef(s.density, y)[0, 1]), 3),
                "corr_density_within":
                    round(float(np.corrcoef(s.density_within_dataset, y)[0, 1]), 3),
                "n": int(len(s)), "subset": "popqa",
                "auc_pop": round(float(ctrl["auc_popularity_only"]), 3),
                "auc_pop_density": round(float(ctrl["auc_pop_plus_density"]), 3),
                "auc_pop_density_within":
                    round(float(ctrl["auc_pop_plus_density_within"]), 3),
                "auc_density_within": round(float(ctrl["auc_density_within_only"]), 3),
                "neighbour_mix": round(float(ctrl["neighbour_mix"]), 3),
                # corpus-wide: does map-neighbourhood density predict error at all?
                "auc_density_map_all": round(float(roc_auc_score(
                    loc.majority_wrong.astype(int), loc.density)), 3)},
    }


def retrieval_outcomes() -> dict[str, dict]:
    """Per blind spot: did documents fix it, did Wikipedia search, did the web?

    Three arms, three DIFFERENT coverages, and the coverage is the whole reason
    this is a dict of nullable values rather than three booleans:

        RQ4  documents pasted in   570 questions   (obscurity 500 + misconception 70)
        RQ5  Wikipedia agent     1,054 questions   (977 complete with all four models)
        RQ5  open-web agent        151 questions   (148 complete) -- SAMPLED, because
                                                    free search tiers are ~1,000 credits
                                                    and the full arm needs ~6,000-8,000

    `None` means "this arm never ran here", and it must stay distinguishable from
    False. Collapsing them would make the map's biggest band "not fixed by the
    open web" -- which for ~900 questions would be encoding *our sampling budget*
    as if it were a finding about retrieval.
    """
    def rescued(fname: str) -> dict[str, bool]:
        g = blind_only(pd.read_parquet(path("processed", fname))).groupby("qid")
        d = g.agg(n=("model", "nunique"), ok=("correct", "any"))
        return d.loc[d.n == 4, "ok"].astype(bool).to_dict()   # complete arms only

    wiki, web = rescued("rq5_agentic.parquet"), rescued("rq5_agentic_web.parquet")
    r4 = rq4_frame()
    docs = dict(zip(r4.qid, r4.retrieved_ok.astype(bool)))

    out: dict[str, dict] = {}
    for q in set(wiki) | set(web) | set(docs):
        out[q] = {"docs": docs.get(q), "wiki": wiki.get(q), "web": web.get(q)}
    return out


def main() -> int:
    rec = pd.read_parquet(path("processed", "records.parquet"))
    loc = pd.read_parquet(path("processed", "records_rq3local.parquet"))
    ans = pd.read_parquet(path("interim", "answers.parquet"),
                          columns=["qid", "model", "answer", "correct", "confidence",
                                   "gold", "aliases"])
    lans = pd.read_parquet(path("interim", "answers_rq3local.parquet"),
                           columns=["qid", "model", "answer", "correct", "confidence"])
    # records.parquet IS the analysed population: gradeable, and each question
    # once (ISSUES #66). The answer tables still hold every row that was ever
    # asked, so they are cut to it here, once, before anything reads them.
    # Independence ran on the raw answers until 2026-09-27 and so counted the
    # 40 ungradeable questions its own chapter said were dropped.
    global ANALYSED, BLIND
    ANALYSED = set(rec.qid)
    BLIND = set(rec.qid[rec.silent_consensus])
    n_asked = int(ans.qid.nunique())
    ans = ans[ans.qid.isin(ANALYSED)]
    lans = lans[lans.qid.isin(set(loc.qid))]

    # ---------- map: parallel arrays ----------
    rec = rec.sort_values("qid").reset_index(drop=True)
    ds_idx = {d: i for i, d in enumerate(DATASETS)}
    silent_g3 = set(rec.loc[rec.silent_consensus, "qid"])
    silent_g2 = set(loc.loc[loc.silent_consensus, "qid"])

    # flags packed into one small int, so the map costs one array not five:
    #   bit0 majority_wrong  bit1 all_wrong  bit2 silent(gen-3)
    #   bit3 silent(gen-2)   bit4 any_wrong
    # any_wrong is here ONLY to split the map's correctness bands. It must never
    # be a prediction target -- it is mechanically implied by the disagreement
    # score (see disagree.py) and scoring against it gave a meaningless 0.911.
    # But "all four right" vs "the majority was right and one model was not" is
    # a real distinction on the map, and it costs one bit of an existing int.
    # numpy, not Series: pandas nullable/boolean Series do not support `<<`.
    def bits(col) -> np.ndarray:
        return np.asarray(col).astype(bool).astype(np.int32)

    # bits 5-7  how many of the four models were CORRECT      (0-4)
    # bits 8-10 how many gave the ENSEMBLE'S answer, i.e. the
    #           largest cluster's size                        (1-4)
    # Both are what a reader asks the moment they see "majority wrong": wrong by
    # how much, and did anyone get it right? Neither existed as a column.
    # n_correct comes from the answer rows; the majority size is recoverable
    # exactly from disagreement_unweighted, which is 1 - max(count)/n by
    # construction in disagree.py -- so no recomputation and no chance of the
    # two disagreeing. Three bits each, into the int that already ships.
    n_correct = (rec.qid.map(ans.groupby("qid").correct.sum())
                 .fillna(0).astype(int).clip(0, 4))
    n_major = ((1 - rec.disagreement_unweighted) * 4).round().astype(int).clip(1, 4)

    # bits 11-12  search: was this blind spot SEARCHED, and did search FIX it?
    #
    # RQ5 ONLY -- the two agentic arms -- and deliberately not RQ4. They look
    # like the same experiment and are not:
    #
    #   RQ5  population = the 1,054 blind spots      protocol = agent searches
    #   RQ4  population = majority_wrong ERRORS      protocol = we paste the article
    #
    # Only 33 of RQ4's 570 questions are blind spots at all. Folding the two into
    # one "retrieval fixed it" colour would put two populations and two protocols
    # under one legend entry, and a reader brushing a clump could not tell whether
    # a green dot means "an agent found the answer" or "we handed it over".
    # RQ4 keeps its own table in the signal panel; its per-case result still ships
    # below, where the inspector can name the arm instead of blending it.
    #
    # Two bits, not six: the map's question is about POSITION -- do the blind
    # spots that survive search sit somewhere different from the ones it repairs?
    # Which arm won is a per-case fact, and the arms have very different coverage
    # (Wikipedia 977, open web 148 by sampling), so an arm-split colour would
    # encode our search budget as if it were a property of the questions.
    # bits 13-14  is this question's subject sharing its name with something
    # better known? Wikipedia's own convention answers it with no judgement:
    # the bare name stays the title unless something else already owns it, so a
    # qualified title IS the collision. Only PopQA has linkable titles, hence a
    # separate "linkable" bit -- the other three datasets must not be silently
    # binned as "unique", which would put 28,270 questions into a band that
    # claims to have checked something it never could.
    #
    # Exported 2026-08-10 so the map can show the mechanism that Walkthrough 1
    # had to leave the tool to confirm: 4.6% blind on shared names against 1.6%
    # on unique ones, 2.8x, reproducing the 2026-08-03 enrichment table.
    tit = pd.read_parquet(path("interim", "popqa_wiki_titles.parquet"))
    tmap = {q: (str(t), str(s)) for q, t, s
            in zip(tit.question, tit.s_wiki_title, tit.subj)}

    def name_bits(question: str) -> tuple[bool, bool]:
        got = tmap.get(question)
        if not got or got[0] in ("", "nan") or got[1] in ("", "nan"):
            return False, False
        title, subj = got
        return True, title != subj and (title.startswith(subj + ",")
                                        or title.startswith(subj + " ("))

    nb = [name_bits(q) for q in rec.question]
    linkable = np.array([a for a, _ in nb], dtype=bool)
    shared = np.array([b for _, b in nb], dtype=bool)

    retr = retrieval_outcomes()
    arms = ("wiki", "web")
    ran = rec.qid.map(lambda q: any(retr.get(q, {}).get(a) is not None
                                    for a in arms))
    fixed = rec.qid.map(lambda q: any(retr.get(q, {}).get(a) for a in arms))

    flags = (bits(rec.majority_wrong)
             | (bits(rec.all_wrong) << 1)
             | (bits(rec.silent_consensus) << 2)
             | (bits(rec.qid.isin(silent_g2)) << 3)
             | (bits(rec.any_wrong) << 4)
             | (np.asarray(n_correct, dtype=np.int32) << 5)
             | (np.asarray(n_major, dtype=np.int32) << 8)
             | (bits(ran) << 11)
             | (bits(fixed) << 12)
             | (bits(linkable) << 13)
             | (bits(shared) << 14))

    # NOT exported: `disagreement` and the per-question mean confidence.
    # Both were shipped for map colourings that no longer exist. The
    # disagreement score is Spearman 0.981 against n_clusters -- it IS the
    # cluster count, weighted by confidence -- so colouring by both put one
    # measurement on screen twice. `k` is the legible half and it filters into
    # four clean bands; the weighted half is worth +0.003 AUC, i.e. RESULTS
    # claim 9's "wash at scale". Two arrays x 34,062 rounded floats removed
    # from every page load. Re-add here if a view ever needs the continuous
    # score -- it is still in records.parquet, which stays the source of record.
    m = {
        "qid": rec.qid.tolist(),
        "x": [round(float(v), 2) for v in rec.x],
        "y": [round(float(v), 2) for v in rec.y],
        "ds": [ds_idx.get(v, 0) for v in rec.dataset],
        "f": flags.tolist(),
        "k": rec.n_clusters.astype(int).tolist(),
    }

    # ---------- audit cases: the UNION of both arms' blind spots ----------
    # Union, not just gen-3's 950: the generation-diff panel must be able to
    # show EMERGED (gen-3 only) and HEALED (gen-2 only) cases, and a case that is
    # only ever a blind spot in the old arm is exactly a "healed" one.
    keep = sorted(silent_g3 | silent_g2)
    a_by = {q: g for q, g in ans[ans.qid.isin(keep)].groupby("qid")}
    l_by = {q: g for q, g in lans[lans.qid.isin(keep)].groupby("qid")}
    meta = rec.set_index("qid")
    lmeta = loc.set_index("qid")
    gold_al = ans.drop_duplicates("qid").set_index("qid")[["gold", "aliases"]]

    cases = []
    for q in keep:
        r = meta.loc[q]
        in3, in2 = q in silent_g3, q in silent_g2
        cases.append({
            "qid": q,
            "dataset": r.dataset,
            "q": _trunc(r.question, Q_CHARS),
            "gold": _trunc(r.gold, 120),
            # persisted / emerged / healed -- the RQ3 categories, per case
            "diff": "persisted" if (in3 and in2) else ("emerged" if in3 else "healed"),
            # Head-count here too. The tool only asks `dis < 0.02` -> "they all
            # said the same thing", and on the weighted score that sentence could
            # be printed for a case where they did NOT: three confident models
            # plus one hesitant dissenter scores 0.09 unweighted but can fall
            # under 0.02 when the dissenter is unsure enough. Unweighted, 0.00
            # means exactly one meaning cluster, which is what the words claim.
            "dis": round(float(r.disagreement_unweighted), 3),
            "new": [{"m": short(x.model), "a": _trunc(x.answer, A_CHARS),
                     "ok": bool(x.correct), "c": round(float(x.confidence), 3)}
                    for x in a_by[q].itertuples()] if q in a_by else [],
            "old": [{"m": short(x.model), "a": _trunc(x.answer, A_CHARS),
                     "ok": bool(x.correct), "c": round(float(x.confidence), 3)}
                    for x in l_by[q].itertuples()] if q in l_by else [],
            "dis_old": (round(float(lmeta.loc[q].disagreement_unweighted), 3)
                        if q in lmeta.index else None),
            # {docs, wiki, web} -> true / false / null. Null is "not run here",
            # and the inspector prints it as "not run" rather than as a failure.
            "rq": retr.get(q, {"docs": None, "wiki": None, "web": None}),
            # flag, not a verdict -- see key_too_strict()
            "keyflag": bool(q in a_by and key_too_strict(
                a_by[q]["answer"].tolist(), r.gold,
                gold_al.loc[q, "aliases"] if q in gold_al.index else [])),
        })

    persisted = len(silent_g3 & silent_g2)
    # Computed BEFORE `stats` is built. Until 2026-08-03 this field was the
    # literal `0` and the real count was derived 20 lines later, after the dict,
    # purely to print it -- so summary.json published "0 answer-key flags" while
    # lookup_keyflags.parquet held 60. Nothing read the field yet, which is the
    # only reason it never surfaced as a wrong number on a slide. A published
    # constant that no longer tracks its source is a wrong number waiting for a
    # reader.
    nflag = sum(1 for c in cases if c["keyflag"])
    stats = {
        "signal": signal_stats(rec),
        "baseline": baseline_stats(rec),
        "rq4": rq4_stats(),
        "rq5": rq5_stats(),
        "funnel": funnel_stats(rec),
        "intervals": intervals_stats(rec, loc, ans),
        "abstain": abstain_stats(rec, ans),
        **rq1_rq2_stats(rec, ans),
        "rq3": {
            # The six numbers of "result 3, the uncomfortable one". They were
            # typed into the slide until 2026-08-07 -- correct, verified exact
            # against these same two frames, and still the #43/#45 pattern: a
            # published figure with a live source and no link back to it. The
            # third column is the second divided by the first, and deriving it
            # means the slide cannot ever show a share that its own two rows
            # contradict.
            "rates": [{"gen": g,
                       "wrong": round(float(d.majority_wrong.mean()), 4),
                       "blind": round(float(d.silent_consensus.mean()), 4),
                       "share": round(float(d.silent_consensus.mean()
                                            / d.majority_wrong.mean()), 4)}
                      for g, d in (("2024", loc), ("2025", rec))],
            "gen2_silent": len(silent_g2), "gen3_silent": len(silent_g3),
            "persisted": persisted,
            "healed": len(silent_g2 - silent_g3),
            "emerged": len(silent_g3 - silent_g2),
            # The three figures the interface uses to say "these became
            # DETECTABLE, not correct". Exported 2026-08-08 because they were
            # typed (78% / 52%) and because one of them was ambiguous -- see
            # ISSUES #48. Both wrongness measures are published for the healed
            # set so the prose can name the one it means instead of leaving the
            # reader to assume; they differ by 26 points.
            "emerged_was_allwrong": int(loc.set_index("qid")
                                        .loc[sorted(silent_g3 - silent_g2),
                                             "all_wrong"].sum()),
            "healed_allwrong": int(rec.set_index("qid")
                                   .loc[sorted(silent_g2 - silent_g3),
                                        "all_wrong"].sum()),
            "healed_ens_wrong": int(rec.set_index("qid")
                                    .loc[sorted(silent_g2 - silent_g3),
                                         "majority_wrong"].sum()),
            "persistence": round(persisted / len(silent_g2), 3),
            "inherited": round(persisted / len(silent_g3), 3),
        },
        # Claim 12 -- the one that leads the paper. Derived, never typed.
        "independence": independence_stats(ans, rec),
        # Claims 14 and 15. Empty dicts if the scripts have not been run, so a
        # fresh clone exports rather than crashing; the pages check before use.
        "ablation": ablation_stats(),
        "rq1b": rq1b_stats(),
        "belief": belief_stats(),
        "artifact": artifact_stats(),
        "irr": irr_stats(),
        "writeup": writeup_stats(),
        "adjudicator": adjudicator_stats(),
        "corpus": {
            "asked": n_asked, "analysed": len(rec),
            "duplicates": len(duplicate_qids()),
            "generations": int(len(ans)),
            "models_new": [short(x) for x in sorted(ans.model.unique())],
            "models_old": [short(x) for x in sorted(lans.model.unique())],
        },
        "datasets": DATASETS,
        "keyflags": nflag,
        "defects": defect_count(),
        # "430 verdicts hand-labelled" appears on the closing slide. It grows
        # every time anyone labels a case, which is exactly the kind of number
        # that goes stale in a page nobody re-reads.
        "handlabels": int(len(pd.read_parquet(path("processed",
                                                   "handlabels.parquet")))),
        "grader_check": grader_check(),
        "walk": walkthrough_stats(rec, loc),
        "arms": artifact_arms({"2024": silent_g2, "2025": silent_g3}),
        # "62 tests passing" was typed on the closing slide beside "42 defects",
        # and the 42 had been stale for a week (ISSUES #49). Counting `def test_`
        # is exact here -- 70 functions, 70 collected, nothing parametrised -- and
        # if that ever stops being true the assert below fails the export rather
        # than publishing a number that quietly drifts from what pytest reports.
        "tests": count_tests(),
    }

    OUT_TOOL.parent.mkdir(parents=True, exist_ok=True)
    OUT_TOOL.write_text(json.dumps({"map": m, "cases": cases, "stats": stats,
                                    "panels": panel_data()},
                                   separators=(",", ":")), encoding="utf-8")
    OUT_WEB.parent.mkdir(parents=True, exist_ok=True)
    OUT_WEB.write_text(json.dumps(stats, indent=1), encoding="utf-8")

    print(f"-> {OUT_TOOL}   {OUT_TOOL.stat().st_size / 1e6:.2f} MB")
    print(f"   map {len(m['qid']):,} points   cases {len(cases):,}"
          f"   (persisted {stats['rq3']['persisted']}"
          f" / healed {stats['rq3']['healed']}"
          f" / emerged {stats['rq3']['emerged']})")
    print(f"-> {OUT_WEB}   {OUT_WEB.stat().st_size / 1e3:.1f} KB")
    # The deck and the walkthroughs draw their whole body from summary.json in
    # the browser, so anything that does not run JavaScript -- a crawler, a link
    # preview, an agent fetching the URL -- used to receive a <title> and an
    # empty shell. prerender.mjs bakes the rendered markup back into those two
    # files. It runs HERE, on every export, for the same reason nothing in this
    # project is typed by hand: a baked page that is not re-baked is last week's
    # numbers, published. Missing node is a warning and not a failure -- the
    # export above is already correct and the live pages still render for
    # anyone with a browser.
    pre = OUT_WEB.parent / "prerender.mjs"
    try:
        subprocess.run(["node", str(pre)], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"   !! prerender skipped ({exc}) -- {OUT_WEB.parent.name} pages are"
              f" now empty to anything that does not run JavaScript."
              f" Install Node and run: node {pre}")

    print(f"   overall AUC {stats['signal']['overall']['auc']}"
          f"   silent {stats['signal']['overall']['silent']}")
    for d in stats["signal"]["by_dataset"]:
        print(f"     {d['dataset']:11} n={d['n']:6,} auc {d['auc']:.3f}"
              f"  base {d['base']:.1%}  silent {d['silent']}")
    print(f"   baseline best single {stats['baseline']['single_model'][0]}"
          f"  vs cross {stats['baseline']['cross_model_same_qids']}"
          f"  (n={stats['baseline']['n']:,})")
    print(f"   rq4 {stats['rq4']['by_cause']}")
    print(f"   answer-key-too-strict flags: {nflag} of {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
