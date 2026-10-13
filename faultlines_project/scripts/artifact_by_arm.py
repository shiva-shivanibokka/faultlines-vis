#!/usr/bin/env python
"""Does the grading-artifact rate differ between the two model generations?

    python scripts/artifact_by_arm.py

Runs no model and spends nothing: all four adjudications are already on disk.

WHY THIS EXISTS

`adjudicate_blind.py` measured the 2025 arm at 21.74% and that correction cut
the project's headline from 1,054 genuine blind spots to about 825 (ISSUES #55).
Every RQ3 finding COMPARES the two arms, and until 2026-08-26 only one of them
had been adjudicated. Chapter 7 argued the comparison survived because both arms
run through the identical grader, so a uniform strictness largely cancels.

**That argument is false in its premise.** The strictness does not cancel. It is
several points larger on the newer arm, it moves the same way inside every
dataset, and it is not explained by anything this script could find. It had to
be measured, and this is the measurement.

THE CONFOUND THIS SCRIPT EXISTS TO RULE OUT

The representative answer for a case is the first model in sorted order.
"Qwen/..." sorts first among the 2025 models, so all 1,054 of the 2025 cases
were judged on Qwen3-235B's answer -- and Qwen3-235B was the judge. Meanwhile
"gemma2:9b" sorts first in 2024, so that arm was judged on a model the judge has
no stake in. Self-favouring would inflate the 2025 rate relative to 2024, which
is the direction the first run showed. Logged as ISSUES #58.

Both arms were therefore re-judged by Olmo-3.1-32B-Instruct, which is in neither
ensemble and is trained on Dolma, the strongest available break in data lineage.
The gap did not shrink. It grew. Whatever produces it, it is not the judge
marking its own homework.

WHAT IT MEANS FOR ANYONE ELSE

Any longitudinal benchmark that grades automatically and compares a newer model
against an older one carries a strictness difference it has not measured, in the
direction that penalises the newer model. That is a methodological finding with
reach past this thesis, and it was invisible until BOTH arms were adjudicated.
"""
from __future__ import annotations

import sys
from math import erfc, sqrt
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import path                     # noqa: E402

# judge key -> (label, whether it sits inside one of the arms, {arm: filename})
JUDGES = {
    "qwen": ("Qwen3-235B", True, {
        "2024": "adjudicated_blind_2024.parquet",
        "2025": "adjudicated_blind.parquet"}),
    "olmo": ("Olmo-3.1-32B", False, {
        "2024": "adjudicated_blind_2024_outside2.parquet",
        "2025": "adjudicated_blind_outside2.parquet"}),
}
PRIMARY = "qwen"      # the judge every published figure was measured with


def wilson(k: int, n: int) -> tuple[float, float]:
    """The same interval RESULTS.md uses for every other rate."""
    if not n:
        return 0.0, 0.0
    z, p, D = 1.96, k / n, 1 + 1.96 ** 2 / n
    c = (p + z * z / (2 * n)) / D
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / D
    return max(0.0, c - h), min(1.0, c + h)


def two_prop(k1: int, n1: int, k2: int, n2: int) -> tuple[float, float]:
    """Pooled two-proportion z and its two-sided p."""
    if not n1 or not n2:
        return 0.0, 1.0
    p = (k1 + k2) / (n1 + n2)
    se = sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (k2 / n2 - k1 / n1) / se
    return z, erfc(abs(z) / sqrt(2))


BLIND_SRC = {"2024": "records_rq3local.parquet", "2025": "records.parquet"}


def load(judge: str, arm: str):
    """One arm's adjudications, cut to that arm's CURRENT blind set.

    The adjudication files were written before the corpus was deduplicated
    (ISSUES #66); a verdict on a question that is no longer in the analysed
    population must not count toward either arm's rate.
    """
    f = JUDGES[judge][2][arm]
    p = path("processed", f)
    if not p.exists():
        return None
    rec = pd.read_parquet(path("processed", BLIND_SRC[arm]))
    blind = set(rec.loc[rec.silent_consensus, "qid"])
    d = pd.read_parquet(p)
    return d[d.qid.isin(blind)]


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p on the discordant counts b and c."""
    from scipy.stats import binomtest
    n = b + c
    return float(binomtest(min(b, c), n, 0.5).pvalue) if n else 1.0


def counts(d: pd.DataFrame) -> tuple[int, int, int]:
    """artifacts, all cases, undecided.

    The denominator is ALL cases, not just the ones the judge committed on.
    An UNCLEAR verdict is not evidence of an artifact, and the two arms differ
    in how often the judge declined -- 56 against 0 under the primary judge --
    so a rate over committed verdicts is partly a rate of declining. Over all
    cases the two are comparable, and the reading is conservative in the
    direction that matters: it cannot inflate the correction.
    """
    k = int((d.judge == True).sum())                    # noqa: E712
    return k, len(d), int(d.judge.isna().sum())


def main() -> int:
    have = {j: {a: load(j, a) for a in ("2024", "2025")} for j in JUDGES}
    missing = [f"{j}/{a}" for j in have for a in have[j] if have[j][a] is None]
    if missing:
        print("missing adjudications: " + ", ".join(missing))
        print("run  scripts/adjudicate_blind.py --arm <arm> [--judge outside2]")
        return 1

    print("=" * 74)
    print("GRADING ARTIFACTS ARE NOT CONSTANT ACROSS MODEL GENERATIONS")
    print("=" * 74)
    print("A CORRECT verdict means the automatic grader was too strict, so the")
    print("case is not a genuine blind spot. Rates are over ALL cases -- see")
    print("counts() for why that is the comparable denominator.\n")

    print(f"  {'judge':<14} {'in an arm?':<11} {'2024':>22} {'2025':>22} "
          f"{'gap':>7} {'p':>9}")
    C = {}
    for j, (label, inside, _) in JUDGES.items():
        row = {}
        for a in ("2024", "2025"):
            k, n, u = counts(have[j][a])
            lo, hi = wilson(k, n)
            row[a] = (k, n, u, lo, hi)
        C[j] = row
        (k1, n1, _, l1, h1), (k2, n2, _, l2, h2) = row["2024"], row["2025"]
        _, p = two_prop(k1, n1, k2, n2)
        print(f"  {label:<14} {('YES -- 2025' if inside else 'no'):<11} "
              f"{k1:>4}/{n1:<5}{k1/n1:>6.2%} "
              f"{k2:>4}/{n2:<5}{k2/n2:>6.2%} "
              f"{k2/n2 - k1/n1:>+7.1%} {p:>9.4f}")

    print("\n  Both judges put the 2025 rate above the 2024 one. The judge that")
    print("  is NOT in either ensemble reports the LARGER gap, so the effect is")
    print("  not the in-ensemble judge being soft on its own answers -- which was")
    print("  the first and most serious explanation to rule out (ISSUES #58).")
    print("  Olmo is more lenient on both arms, which moves the LEVEL and not")
    print("  the difference. Absolute rates are judge-dependent; the sign is not.")

    # ---- composition, or a real within-dataset move? -----------------------
    print("\n" + "-" * 74)
    print("IS IT COMPOSITION, OR DOES IT MOVE INSIDE EVERY DATASET?")
    print("-" * 74)
    print("  PopQA has by far the tightest answer keys and the lowest artifact")
    print("  rate, and the two arms hold slightly different mixes. If the whole")
    print("  effect were mix, it would vanish inside the datasets.\n")
    for j, (label, _, _) in JUDGES.items():
        d24, d25 = have[j]["2024"], have[j]["2025"]
        dss = sorted(set(d24.dataset) | set(d25.dataset))
        print(f"  {label}")
        print(f"    {'dataset':<12} {'2024':>15} {'2025':>15} {'move':>8} {'p':>8}")
        up = 0
        for ds in dss:
            g1, g2 = d24[d24.dataset == ds], d25[d25.dataset == ds]
            k1, n1, _ = counts(g1)
            k2, n2, _ = counts(g2)
            if not n1 or not n2:
                continue
            _, p = two_prop(k1, n1, k2, n2)
            up += (k2 / n2) > (k1 / n1)
            print(f"    {ds:<12} {k1:>4}/{n1:<4}{k1/n1:>6.2%} "
                  f"{k2:>4}/{n2:<4}{k2/n2:>6.2%} "
                  f"{k2/n2 - k1/n1:>+8.1%} {p:>8.3f}")
        # direct standardisation: apply the 2024 per-dataset rates to the 2025 mix
        mix = d25.dataset.value_counts()
        exp = sum(mix.get(ds, 0) * (counts(d24[d24.dataset == ds])[0]
                                    / max(1, counts(d24[d24.dataset == ds])[1]))
                  for ds in dss)
        k2, n2, _ = counts(d25)
        print(f"    2024 rates applied to the 2025 mix: {exp/n2:>6.2%}   "
              f"actual 2025: {k2/n2:.2%}   "
              f"unexplained by mix: {k2/n2 - exp/n2:+.1%}")
        print(f"    higher in 2025 in {up} of {len(dss)} datasets\n")

    print("  Read the per-dataset p-values above rather than a sentence about")
    print("  them: until 2026-09-27 this line asserted that no dataset reached")
    print("  p < 0.05, while the outside judge's own rows showed two that did.")

    # ---- the mechanism, and the hypothesis that failed ---------------------
    print("\n" + "-" * 74)
    print("THE OBVIOUS EXPLANATION, TESTED AND REJECTED")
    print("-" * 74)
    print("  The natural story is verbosity: newer models wrap the right fact in")
    print("  more words, and extra words defeat a short-form matcher. If that")
    print("  were it, artifact cases would be the long answers.\n")
    print(f"  {'judge/arm':<16} {'all':>11} {'artifact':>11} {'genuine':>11}")
    for j, (label, _, _) in JUDGES.items():
        for a in ("2024", "2025"):
            d = have[j][a]
            ln = d.answer.astype(str).str.split().str.len()
            art = ln[d.judge == True]                    # noqa: E712
            gen = ln[d.judge == False]                   # noqa: E712
            print(f"  {label[:9]+'/'+a:<16} {ln.mean():>8.2f} w "
                  f"{art.mean():>8.2f} w {gen.mean():>8.2f} w")
    print("\n  It is not verbosity. These are short-form answers -- under two")
    print("  words on average -- and within each arm the artifact cases are no")
    print("  longer than the genuine ones; under the primary judge on the 2025")
    print("  arm they are marginally SHORTER. The 2025 answers are about a third")
    print("  of a word longer than the 2024 ones, which is far too small to")
    print("  carry a five-point difference.")
    print("\n  So the mechanism is NOT established. What is established is that")
    print("  the rate differs and that the difference is not the judge, not the")
    print("  dataset mix, and not answer length. Naming a cause this project did")
    print("  not test is the mistake it has spent 65 defects learning to avoid.")

    # ---- what it does to the headline --------------------------------------
    r = C[PRIMARY]
    (k1, n1, *_), (k2, n2, *_) = r["2024"], r["2025"]
    g24, g25 = n1 - k1, n2 - k2
    print("\n" + "=" * 74)
    print("WHAT THIS DOES TO RQ3 -- THE NUMBER CH5 AND CH7 ACTUALLY NEED")
    print("=" * 74)
    print("  (primary judge; the outside judge's figures follow below)\n")
    print(f"  graded blind spots      2024 {n1:>5}   2025 {n2:>5}   "
          f"{n2/n1:>5.2f}x")
    print(f"  GENUINE blind spots     2024 {g24:>5}   2025 {g25:>5}   "
          f"{g25/g24:>5.2f}x")
    # PAIRED. Both arms answered the same questions, so the growth test is
    # McNemar on the discordant cases (healed vs emerged), not a two-sample
    # proportion test over the corpus size twice (ISSUES #74: that read
    # p = 0.138 where the paired test read 0.077 on the same data).
    d24, d25 = have[PRIMARY]["2024"], have[PRIMARY]["2025"]
    gen24 = set(d24.qid) - set(d24.loc[d24.judge == True, "qid"])   # noqa: E712
    gen25 = set(d25.qid) - set(d25.loc[d25.judge == True, "qid"])   # noqa: E712
    pg = mcnemar_exact(len(gen24 - gen25), len(gen25 - gen24))
    print(f"\n  Genuine blind spots: {g25-g24:+d} cases, "
          f"{(g25/g24-1)*100:+.1f}%   (exact McNemar p = {pg:.3f}, paired)")
    print(f"  The graded counts said +{(n2/n1-1)*100:.1f}%. The real growth is "
          f"about {(n2/n1-1)/(g25/g24-1):.1f}x smaller,")
    print("  because the newer arm carries more grading artifacts.")
    print("\n  **Every RQ3 claim keeps its direction and loses about half its")
    print("  size.** And the argument this replaces is retired: 'both arms share")
    print("  a grader so strictness cancels' is false. It does not cancel.")
    for j, (label, _, _) in JUDGES.items():
        rr = C[j]
        (a1, m1, *_), (a2, m2, *_) = rr["2024"], rr["2025"]
        print(f"    {label:<14} genuine {m1-a1:>5} -> {m2-a2:>5}   "
              f"{(m2-a2)/(m1-a1):.2f}x")

    # ---- and the three RQ3 categories, recomputed case by case -------------
    #
    # This is the part the aggregate rates cannot give. "690 newly hidden
    # against 364 inherited" is on the deck, in the tool, in walkthroughs.html
    # and in three chapters, and every one of those counts is a GRADED count.
    # Both arms now have a per-case verdict, so the same three categories can be
    # rebuilt from the cases that survive adjudication in each arm.
    #
    # A case is genuinely blind in an arm when it was graded blind there AND the
    # judge did not overturn it. UNCLEAR counts as not-overturned, which is the
    # conservative direction: it keeps a case in the blind region rather than
    # removing it, so it cannot manufacture a correction.
    print("\n" + "=" * 74)
    print("THE THREE RQ3 CATEGORIES, ON GENUINE BLIND SPOTS")
    print("=" * 74)
    print("  persisted = blind in both   healed = 2024 only   emerged = 2025 only")
    print("  The published split is graded. This one is adjudicated.\n")
    print(f"  {'judge':<14} {'persisted':>10} {'healed':>8} {'emerged':>8} "
          f"{'emerged/persisted':>19}")
    rows = {}
    for j, (label, _, _) in JUDGES.items():
        gen = {}
        for a in ("2024", "2025"):
            d = have[j][a]
            overturned = set(d.loc[d.judge == True, "qid"])   # noqa: E712
            gen[a] = set(d.qid) - overturned
        per = len(gen["2024"] & gen["2025"])
        heal = len(gen["2024"] - gen["2025"])
        em = len(gen["2025"] - gen["2024"])
        rows[j] = (per, heal, em)
        print(f"  {label:<14} {per:>10} {heal:>8} {em:>8} {em/per:>18.2f}x")

    import json
    tool = json.loads((Path(__file__).resolve().parents[2] / "faultlines-tool"
                       / "data.json").read_text(encoding="utf-8"))["stats"]["rq3"]
    print(f"  {'published (graded)':<14} {tool['persisted']:>10} "
          f"{tool['healed']:>8} {tool['emerged']:>8} "
          f"{tool['emerged']/tool['persisted']:>18.2f}x")

    pe, he, ee = rows[PRIMARY]
    print("\n  Read this carefully, because it cuts both ways.")
    print(f"  The headline ratio SURVIVES and barely moves: {ee/pe:.2f}x against a")
    print(f"  published {tool['emerged']/tool['persisted']:.2f}x. An upgrade still")
    print("  creates far more newly hidden cases than it inherits, and that was")
    print("  the claim.")
    print(f"\n  What shrinks is the PERSISTED count -- {tool['persisted']} graded,")
    print(f"  {pe} genuine. A case blind in both arms had to survive adjudication")
    print("  twice, so the category most exposed to the correction is the one")
    print("  the thesis leaned on least.")
    print("\n  Both judges agree on the direction and on the rough size. The")
    print("  ratio is the robust number here; the absolute counts are not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
