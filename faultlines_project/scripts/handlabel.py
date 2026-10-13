"""Hand-label TruthfulQA verdicts. Closes ISSUES 1b.

    python scripts/handlabel.py            # label (resumable -- stop any time)
    python scripts/handlabel.py --stats    # progress while labelling
    python scripts/handlabel.py --result   # kappa + corrected AUC (the reported result)

WHY THIS EXISTS
32.3% of TruthfulQA verdicts on the local arm and 24.3% on the headline gen-3 arm
sit below a 0.10 entailment margin. At that margin the grader could not separate
the correct answer from TruthfulQA's baited wrong answer either -- the verdict is
close to a coin flip. Those cases need a human.

WHAT IS LABELLED, AND WHY IT IS NOT JUST THE COIN FLIPS
Two strata, deliberately:

  TARGET   all 330 low-margin cases (|margin| < 0.10) on the gen-3 headline arm.
           These are the suspect verdicts. Correcting them is the point.

  CONTROL  100 randomly sampled high-margin cases (|margin| >= 0.10).
           These are the verdicts the grader claims to be confident about.

Without the control stratum the exercise cannot be interpreted. Labelling only
the uncertain cases tells you how often the grader is wrong *where it already
admits doubt*, and says nothing about the 1,030 verdicts carrying the weight of
the reported number. If the control stratum turns out clean, the correction is
bounded and TruthfulQA's AUC can be restated with a real error bar. If it turns
out dirty, the dataset cannot be used at all -- and that is a finding.

BLINDING
The machine verdict and the margin are NOT shown, and the two strata are
interleaved in a seeded shuffle, so the labeller cannot tell a coin-flip case
from a confident one. This is not ceremony. Every unintentional bias found in
this project so far has favoured our own hypothesis (ISSUES, watch list #3), and
an unblinded labeller who can see "the machine said WRONG" will agree with it
more often than the evidence warrants. Anchoring would make the correction look
smaller than it is, which is the flattering direction.

The model name is hidden for the same reason: no per-model leniency.

STANDARD TO APPLY
TruthfulQA's own, not personal knowledge. An answer is CORRECT if it matches the
sense of any reference answer, and WRONG if it asserts any of the baited claims.
Both lists are shown for every case.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path, seq          # noqa: E402

ARM = "answers.parquet"          # the gen-3 headline arm -- the one whose AUC is quoted
DEST = path("processed", "handlabels.parquet")
LOW = 0.10
CONTROL_N = 100
WRAP = 76

KEYS = {"c": True, "w": False, "u": None}


def _wrap(text: str, indent: str = "  ") -> str:
    return "\n".join(textwrap.fill(line, WRAP, initial_indent=indent,
                                   subsequent_indent=indent)
                     for line in str(text).splitlines() or [""])


def build_queue() -> pd.DataFrame:
    """The labelling queue: all low-margin cases + a seeded control sample."""
    d = pd.read_parquet(path("interim", ARM))
    t = d[(d["dataset"] == "truthfulqa") & d["gradeable"]].copy()
    if t.empty:
        raise SystemExit(f"no gradeable truthfulqa rows in {ARM}")

    margin = t["nli_margin"].abs()
    target = t[margin < LOW].copy()
    target["stratum"] = "target"

    pool = t[margin >= LOW]
    control = pool.sample(n=min(CONTROL_N, len(pool)),
                          random_state=CFG["seed"]).copy()
    control["stratum"] = "control"

    q = pd.concat([target, control], ignore_index=True)
    # Seeded shuffle: same order every run, so resume is deterministic, but the
    # labeller cannot infer stratum from position.
    q = q.sample(frac=1.0, random_state=CFG["seed"]).reset_index(drop=True)
    q["case"] = q.index
    return q


def load_done() -> dict[tuple[str, str], dict]:
    if not DEST.exists():
        return {}
    prev = pd.read_parquet(DEST)
    if prev.empty:
        return {}
    return {(r["qid"], r["model"]): r for _, r in prev.iterrows()}


def save(rows: list[dict]) -> None:
    # An empty write would produce a parquet with no columns, which then breaks
    # --stats on `h.stratum`. Quitting before the first judgement is normal.
    if rows:
        pd.DataFrame(rows).to_parquet(DEST)


def show(r, n: int, total: int, done: int) -> None:
    print("\n" + "=" * WRAP)
    print(f"case {done + 1} of {total}      ({done / total:.0%} done)"
          f"      q {n + 1}/{total}")
    print("=" * WRAP)
    print("\nQUESTION")
    print(_wrap(r.question))
    print("\nTHE MODEL ANSWERED")
    print(_wrap(r.answer))

    print("\nTRUTHFULQA SAYS CORRECT")
    for a in [r.gold] + [x for x in seq(r.aliases) if x != r.gold]:
        print(_wrap(f"+ {a}"))

    meta = r.meta if isinstance(r.meta, dict) else {}
    inc = seq(meta.get("incorrect"))
    if inc:
        print("\nTRUTHFULQA SAYS WRONG (the bait)")
        for a in inc:
            print(_wrap(f"- {a}"))
    print()


def label() -> int:
    q = build_queue()
    done = load_done()
    total = len(q)
    rows = list(done.values())

    print(__doc__.split("STANDARD TO APPLY")[1].strip())
    print(f"\n{total} cases  ({(q.stratum == 'target').sum()} + "
          f"{(q.stratum == 'control').sum()} blinded controls)"
          f"   already labelled: {len(done)}")
    print("\n  c = correct    w = wrong    u = unclear/cannot tell"
          "\n  q = quit (saves; rerun to resume)\n")

    for n, r in enumerate(q.itertuples()):
        if (r.qid, r.model) in done:
            continue
        show(r, n, total, len(rows))
        while True:
            try:
                k = input("  [c/w/u/q] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                k = "q"
            if k == "q":
                save(rows)
                print(f"\nsaved {len(rows)} labels -> {DEST.name}"
                      f"   {total - len(rows)} to go. Rerun to resume.")
                return 0
            if k in KEYS:
                break
            print("    c, w, u or q please")

        rows.append({
            "qid": r.qid, "model": r.model, "question": r.question,
            "answer": r.answer, "gold": r.gold,
            "stratum": r.stratum,
            "human": KEYS[k],                  # None == unclear
            "machine": bool(r.correct),        # recorded, never shown
            "margin": float(r.nli_margin),
            "labelled_at": time.time(),
        })
        save(rows)                              # autosave EVERY case

    print(f"\nALL {total} CASES LABELLED. Run --stats for the result.")
    return 0


def stats() -> int:
    if not DEST.exists():
        print("nothing labelled yet -- run without --stats")
        return 1
    h = pd.read_parquet(DEST)
    q = build_queue()
    print(f"labelled {len(h)} of {len(q)}  ({len(h) / len(q):.0%})")
    for s in ("target", "control"):
        want = int((q.stratum == s).sum())
        got = int((h.stratum == s).sum())
        print(f"  {s:8} {got:4}/{want:4}")

    graded = h[h["human"].notna()]
    print(f"\nunclear: {len(h) - len(graded)} of {len(h)}")
    if graded.empty:
        return 0

    print("\nagreement with the machine grader")
    for s in ("target", "control"):
        g = graded[graded.stratum == s]
        if g.empty:
            continue
        agree = (g["human"] == g["machine"]).mean()
        # where they differ, WHICH WAY: the machine being over-generous is the
        # flattering direction, and the direction this project keeps finding.
        diff = g[g["human"] != g["machine"]]
        too_kind = int((diff["machine"] & ~diff["human"].astype(bool)).sum())
        print(f"  {s:8} n={len(g):4}  agree {agree:6.1%}   "
              f"disagree {len(diff):3}  (machine too generous in {too_kind})")
        print(f"           human says correct {g['human'].mean():6.1%}   "
              f"machine said correct {g['machine'].mean():6.1%}")

    if int((h.stratum == "control").sum()) < CONTROL_N:
        print("\nControl stratum incomplete -- the corrected rate below is not"
              "\nyet trustworthy. Finish labelling before quoting it.")
        return 0

    # Reweight: the target stratum is a census (all low-margin cases), the
    # control stratum is a sample of the rest. A pooled average of the two would
    # over-weight the low-margin cases badly -- 326 of 1,360 in the corpus but
    # 76% of the labelled set. This is the same stratum trap recorded in
    # RESULTS.md Finding 4b's method note.
    d = pd.read_parquet(path("interim", ARM))
    t = d[(d["dataset"] == "truthfulqa") & d["gradeable"]]
    m = t["nli_margin"].abs()
    n_low, n_hi = int((m < LOW).sum()), int((m >= LOW).sum())

    tg = graded[graded.stratum == "target"]
    cg = graded[graded.stratum == "control"]
    acc = (tg["human"].mean() * n_low + cg["human"].mean() * n_hi) / (n_low + n_hi)
    print(f"\nTruthfulQA accuracy, hand-labelled and reweighted: {acc:.1%}")
    print(f"  machine (NLI) reported            {t['correct'].mean():.1%}")
    print(f"  strata: {n_low} low-margin (census) + {n_hi} high-margin "
          f"(n={len(cg)} sampled)")
    return 0


def result() -> int:
    """The reported result: kappa per stratum, and the AUC with corrected labels.

    Recomputes `majority_wrong` from scratch by re-clustering, because
    records.parquet stores the per-question verdict but not the per-answer
    cluster assignment. The reclustering is verified against the published
    column before anything is reported -- if it does not reproduce 340/340, the
    corrected number is not comparable to the published one and this exits.
    """
    from sklearn.metrics import cohen_kappa_score, roc_auc_score

    from faultlines.semantics import cluster_many
    from faultlines.disagree import ensemble_answer_correct

    h = pd.read_parquet(DEST)
    g = h[h["human"].notna()].copy()
    g["human"] = g["human"].astype(bool)

    print("INTER-RATER AGREEMENT (human vs the NLI grader)")
    for s in ("target", "control"):
        x = g[g.stratum == s]
        k = (cohen_kappa_score(x["human"], x["machine"])
             if x["human"].nunique() > 1 else float("nan"))
        u = h[h.stratum == s]["human"].isna()
        print(f"  {s:8} n={len(x):4}  raw {(x['human'] == x['machine']).mean():6.1%}"
              f"  kappa {k:5.3f}   unclear {int(u.sum()):3}/{len(u):3} ({u.mean():.1%})")
    d = g[(g.stratum == "target") & (g["human"] != g["machine"])]
    print(f"\n  of {len(d)} target disagreements: machine too GENEROUS "
          f"{int((d['machine'] & ~d['human']).sum())}, too HARSH "
          f"{int((~d['machine'] & d['human']).sum())}")

    a = pd.read_parquet(path("interim", ARM))
    rec = pd.read_parquet(path("processed", "records.parquet"))
    t = a[(a["dataset"] == "truthfulqa") & a["gradeable"]].copy()
    hl = {(r.qid, r.model): bool(r.human) for r in h.itertuples()
          if pd.notna(r.human)}
    # unclear cases KEEP the machine verdict -- the conservative choice. Dropping
    # them would shrink n; guessing them would invent labels.
    t["corr"] = [hl.get((q, m), c)
                 for q, m, c in zip(t["qid"], t["model"], t["correct"])]

    groups = list(t.groupby("qid", sort=False))
    ids = cluster_many([grp["answer"].tolist() for _, grp in groups])
    mw_m, mw_c, sc_c = {}, {}, {}
    for (qid, grp), cl in zip(groups, ids):
        # the same rule records.parquet is built with (ISSUES #67)
        cf = grp["confidence"].tolist()
        mw_m[qid] = not ensemble_answer_correct(cl, cf, grp["correct"].tolist())
        mw_c[qid] = not ensemble_answer_correct(cl, cf, grp["corr"].tolist())
        sc_c[qid] = bool(len(set(cl)) == 1 and (~grp["corr"].astype(bool)).all())

    tq = rec[rec["dataset"] == "truthfulqa"]
    match = int(sum(mw_m[q] == mw for q, mw in
                    zip(tq["qid"], tq["majority_wrong"])))
    print(f"\n  reclustering reproduces published majority_wrong: "
          f"{match}/{len(tq)}")
    if match != len(tq):
        print("  MISMATCH -- corrected AUC would not be comparable. Stopping.")
        return 1

    y_m = tq["majority_wrong"].values
    y_c = np.array([mw_c[q] for q in tq["qid"]])
    dis = tq["disagreement_unweighted"].values   # head-count, as the headline (ISSUES #78)
    rng = np.random.default_rng(CFG["seed"])

    def ci(y):
        out = []
        for _ in range(4000):
            i = rng.integers(0, len(y), len(y))
            if y[i].min() == y[i].max():
                continue
            out.append(roc_auc_score(y[i], dis[i]))
        return np.percentile(out, [2.5, 97.5])

    print(f"\nTRUTHFULQA AUC (n={len(tq)}, target = majority_wrong)")
    for nm, y in (("as published", y_m), ("label-corrected", y_c)):
        lo, hi = ci(y)
        print(f"  {nm:16} {roc_auc_score(y, dis):.3f}   95% CI "
              f"[{lo:.3f}, {hi:.3f}]   positives {int(y.sum())}")
    deltas = []
    for _ in range(4000):
        i = rng.integers(0, len(y_m), len(y_m))
        if y_m[i].min() == y_m[i].max() or y_c[i].min() == y_c[i].max():
            continue
        deltas.append(roc_auc_score(y_c[i], dis[i]) - roc_auc_score(y_m[i], dis[i]))
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    print(f"  delta            {np.mean(deltas):+.3f}   95% CI "
          f"[{lo:+.3f}, {hi:+.3f}]   crosses zero: {'YES' if lo < 0 < hi else 'NO'}")
    print(f"  questions whose verdict flipped: {int((y_m != y_c).sum())}")

    r2 = rec.copy()
    r2["majority_wrong"] = [mw_c.get(q, v) for q, v in
                            zip(r2["qid"], r2["majority_wrong"])]
    r2["silent_consensus"] = [sc_c.get(q, v) for q, v in
                              zip(r2["qid"], r2["silent_consensus"])]
    n_ans = int(a.qid.isin(rec.qid).sum())       # analysed answers, not every row
    print(f"\nCORPUS-WIDE (n={len(rec):,}) -- {len(hl)} of {n_ans:,} answers "
          f"relabelled ({len(hl) / n_ans:.2%})")
    for nm, dd in (("as published", rec), ("label-corrected", r2)):
        print(f"  {nm:16} AUC {roc_auc_score(dd['majority_wrong'], dd['disagreement_unweighted']):.4f}"
              f"   silent {int(dd['silent_consensus'].sum()):,}")

    ctl = g[g.stratum == "control"]
    err = (ctl["human"] != ctl["machine"]).mean()
    n_hi = int((t["nli_margin"].abs() >= LOW).sum())
    print(f"\nRESIDUAL BOUND (this is what the control stratum buys)")
    print(f"  high-margin error rate {err:.1%} (n={len(ctl)}) x {n_hi} unlabelled"
          f"  ~=  {err * n_hi:.0f} answers still mislabelled")
    # Until 2026-09-27 this printed "~95 corrected, ~90% complete" from a typed
    # 0.287 x 330: a rate measured on the COMMITTED labels applied to every
    # low-margin answer, including the ones left unclear -- which keep the
    # machine verdict and so were never corrected. Counted instead.
    tg = h[h.stratum == "target"]           # ALL of it: g holds judged rows only
    committed = tg[tg.human.notna()]
    corrected = int((committed.human.astype(bool)
                     != committed.machine.astype(bool)).sum())
    rate = corrected / max(1, len(committed))
    unclear_left = int(tg.human.isna().sum()) * rate
    hi_left = err * n_hi
    print(f"  {corrected} corrected in the low-margin band; {tg.human.isna().sum()}"
          f" unclear there keep the machine verdict (~{unclear_left:.0f} still wrong"
          f" at the committed rate {rate:.1%})")
    print(f"  the correction is ~{corrected / (corrected + unclear_left + hi_left):.0%}"
          f" complete, or ~{corrected / (corrected + hi_left):.0%} if an unclear"
          f" case is counted as undecidable rather than as an error")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--result", action="store_true", help="kappa + corrected AUC")
    a = ap.parse_args()
    raise SystemExit(result() if a.result else stats() if a.stats else label())
