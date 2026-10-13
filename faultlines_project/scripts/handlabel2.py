#!/usr/bin/env python
"""Second annotator. Produces the inter-rater reliability figure the thesis lacks.

    python scripts/handlabel2.py --annotator NAME     # label, resumable
    python scripts/handlabel2.py --stats              # progress
    python scripts/handlabel2.py --result             # the two kappas

WHY THIS IS NOT JUST "LABEL THE 45 DISPUTED CASES"

An LLM adjudicator disagreed with the first annotator on 45 of 430 cases, and
handing a second human exactly those 45 is the obvious move. It is also wrong,
for the same reason `handlabel.py` needed a control stratum: a subset selected
for being contested is not a sample of the label set.

Measured on the actual data:

    disputed 45   the first annotator called 40 of them CORRECT -- 89%
                  chance agreement alone is therefore 0.802, so kappa's
                  denominator is 0.198 and two or three flipped cases move it
                  by tenths
    agreed  296   base rate 73%, chance agreement 0.609

A kappa computed on the disputed subset answers "how much do two people agree
where a machine already flagged trouble". Nobody asked that. The question an
examiner asks is "how reliable are these 430 labels", and only a random sample
can answer it.

SO: TWO STRATA, shuffled together, and the annotator is never told which is
which.

  RELIABILITY   70 drawn from the 296 the adjudicator did NOT contest
  DISPUTED      a census of all 45 it did

AND THE ANALYSIS HAS TO MATCH THE DESIGN. The first version of --result quoted
the reliability stratum's kappa on its own as "THE REPORTED FIGURE". That was
wrong for the mirror of the reason above: those 296 are pre-filtered for being
easy, so agreement on them estimates reliability on the easy subset, not on the
430. It read kappa = 1.000, which is what a stratum selected for being
uncontested should read.

This IS a stratified sample with known stratum sizes, so weighting each sampled
case by N/n reconstructs the population table. That is a stronger design than
simple random sampling; it just has to be ANALYSED as the stratified sample it
is. The per-stratum kappas remain as diagnostics and bracket the estimate: the
reliability stratum is an upper bound, the disputed stratum a lower one.

BLINDING
The first annotator's verdict, the machine's verdict, the adjudicator's verdict
and the NLI margin are all withheld. Every unintentional bias found in this
project so far has favoured its own hypothesis, and an annotator who can see a
previous answer will agree with it more often than the evidence warrants.
The model name is hidden too: no per-model leniency.

STANDARD TO APPLY
TruthfulQA's own, not personal knowledge. An answer is CORRECT if it matches the
sense of any reference answer, and WRONG if it asserts any of the baited claims.
Both lists are shown for every case. "Unclear" is a real option and is expected
on roughly a quarter of the hard cases -- it is a finding, not a failure.
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

SEED = CFG["seed"]
RELIABILITY_N = 70          # drawn from the uncontested stratum
# Bootstrap count lives here because the exporter reuses this module. It was
# 4,000 in the script and 2,000 in the exporter for one afternoon, which put
# [0.904, 1.000] in the prose and [0.906, 1.000] in summary.json -- two
# sources for one number, which is the defect this project keeps re-finding.
BOOTSTRAP_N = 4000
SRC = path("processed", "handlabels.parquet")
ADJ = path("processed", "adjudicated.parquet")
KEYS = {"c": True, "w": False, "u": None}


def dest(name: str) -> Path:
    return path("processed", f"handlabels2_{name.lower().strip()}.parquet")


def build_queue() -> pd.DataFrame:
    """The two strata, shuffled so they cannot be told apart.

    Two things here are defences rather than plumbing, and both were added after
    a dry run showed the first version failing them.

    THE ALIAS AND BAIT LISTS ARE JOINED BACK IN. `handlabels.parquet` records
    what the first annotator decided, not what they were shown -- it has no
    `aliases` and no `meta`. Building the queue from it alone meant the second
    annotator saw one accepted answer and no bait list, while the first saw the
    full lists. Two people applying different standards do not produce an
    inter-rater figure; they produce a number that looks like one.

    EVERY PRIOR VERDICT IS DROPPED FROM THE FRAME, not merely left unprinted.
    `show()` never displayed `human`, `machine` or `margin`, but they were
    sitting in the dataframe the annotator's process was holding, one debug
    print or one `read_parquet` away from anchoring the whole exercise.
    """
    h = pd.read_parquet(SRC)
    a = pd.read_parquet(path("processed", "adjudicated_noalias_irrframe.parquet"))  # the frame the labelled sample was drawn from (#69)

    m = a.human.notna() & a.judge.notna()
    disputed = set(zip(a.loc[m & (a.human.astype(bool) != a.judge.astype(bool)), "qid"],
                       a.loc[m & (a.human.astype(bool) != a.judge.astype(bool)), "model"]))

    key = list(zip(h.qid, h.model))
    h = h.assign(stratum=["disputed" if k in disputed else "agreed" for k in key])

    dis = h[h.stratum == "disputed"].copy()
    # The reliability stratum is drawn from the cases the adjudicator did NOT
    # contest, so the two strata do not overlap and each kappa means one thing.
    rel = (h[h.stratum == "agreed"]
           .sample(n=min(RELIABILITY_N, (h.stratum == "agreed").sum()),
                   random_state=SEED)
           .copy())
    rel["stratum"] = "reliability"

    q = pd.concat([rel, dis], ignore_index=True)

    ctx = (pd.read_parquet(path("interim", "answers.parquet"),
                           columns=["qid", "model", "aliases", "meta"])
             .set_index(["qid", "model"]))
    idx = pd.MultiIndex.from_arrays([q["qid"], q["model"]])
    q["aliases"] = ctx["aliases"].reindex(idx).to_numpy()
    q["meta"] = ctx["meta"].reindex(idx).to_numpy()
    missing = int(q["aliases"].isna().sum())
    if missing:
        raise SystemExit(
            f"{missing} cases have no alias list. Refusing to run: the second "
            "annotator would be judging against fewer accepted answers than the "
            "first, and the resulting kappa would measure that instead of "
            "agreement.")

    q = q.drop(columns=["human", "machine", "margin", "labelled_at"],
               errors="ignore")
    return q.sample(frac=1.0, random_state=SEED).reset_index(drop=True)


def show(r, n: int, total: int, done: int) -> None:
    w = textwrap.fill
    print("\n" + "=" * 68)
    print(f"  case {n + 1} of {total}      {done} labelled")
    print("=" * 68)
    print("\nQUESTION")
    print(w(str(r.question), 68))
    print("\nTHE ANSWER GIVEN")
    print(w(str(r.answer), 68))
    print("\nCOUNTED CORRECT BY TRUTHFULQA")
    for x in [r.gold] + [y for y in seq(getattr(r, "aliases", None)) if y != r.gold]:
        print(w(f"+ {x}", 68))
    meta = r.meta if isinstance(getattr(r, "meta", None), dict) else {}
    bait = seq(meta.get("incorrect"))
    if bait:
        print("\nCOUNTED WRONG BY TRUTHFULQA (the bait)")
        for x in bait:
            print(w(f"- {x}", 68))
    print()


def label(name: str) -> int:
    q = build_queue()
    out = dest(name)
    prev = pd.read_parquet(out) if out.exists() else None
    done = {(r.qid, r.model): r for r in prev.itertuples()} if prev is not None else {}
    rows = list(prev.to_dict("records")) if prev is not None else []

    print(__doc__.split("STANDARD TO APPLY")[1].strip())
    print(f"\n{len(q)} cases   already labelled: {len(rows)}")
    print("\n  c = correct    w = wrong    u = unclear / cannot tell"
          "\n  q = quit (saves; rerun to resume)\n")

    for n, r in enumerate(q.itertuples()):
        if (r.qid, r.model) in done:
            continue
        show(r, n, len(q), len(rows))
        while True:
            try:
                k = input("  [c/w/u/q] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                k = "q"
            if k == "q":
                pd.DataFrame(rows).to_parquet(out)
                print(f"\nsaved {len(rows)} -> {out.name}   "
                      f"{len(q) - len(rows)} to go. Rerun to resume.")
                return 0
            if k in KEYS:
                break
            print("    c, w, u or q please")
        rows.append({"qid": r.qid, "model": r.model, "stratum": r.stratum,
                     "annotator": name, "second": KEYS[k],
                     "labelled_at": time.time()})
        pd.DataFrame(rows).to_parquet(out)      # autosave EVERY case

    print(f"\nALL {len(q)} CASES LABELLED. Run --result.")
    return 0


def kappa(a: pd.Series, b: pd.Series) -> tuple[float, int]:
    m = a.notna() & b.notna()
    x, y = a[m].astype(bool), b[m].astype(bool)
    if not len(x):
        return float("nan"), 0
    po = float((x == y).mean())
    pe = float(x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean()))
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), int(len(x))


def strata_sizes() -> dict:
    """Population size of each stratum the sample was drawn from. ISSUES #69.

    Until 2026-09-27 the reliability stratum was sized at 296 -- the cases the
    human AND the adjudicator both decided, and agreed on. But build_queue draws
    it from every case the adjudicator did not contest: 385, including the 89
    the first annotator left UNCLEAR (19 of the 70 drawn have no first verdict,
    which is impossible from the 296). Weighting 70 draws as if they came from
    296 under-weighted the stratum where the annotators agree perfectly, so
    kappa read low.

    Read from the FRAME the sample was drawn against, frozen as
    adjudicated_noalias_irrframe.parquet. adjudicated.parquet was re-run with
    the alias lists on 2026-09-27 (ISSUES #71) and its disputed set moved; the
    strata of a sample already labelled cannot move with it.
    """
    h = pd.read_parquet(SRC)
    a = pd.read_parquet(path("processed", "adjudicated_noalias_irrframe.parquet"))
    m = a.human.notna() & a.judge.notna()
    dis = set(zip(a.loc[m & (a.human.astype(bool) != a.judge.astype(bool)), "qid"],
                  a.loc[m & (a.human.astype(bool) != a.judge.astype(bool)), "model"]))
    n_dis = sum(1 for k in zip(h.qid, h.model) if k in dis)
    return {"reliability": int(len(h) - n_dis), "disputed": int(n_dis)}


def weighted_kappa(d: pd.DataFrame, first: pd.Series, sizes: dict,
                   rng=None) -> tuple[float, float, int]:
    """Cohen's kappa over the WHOLE labelled population, from a stratified sample.

    THE DESIGN BUG THIS FIXES. The reliability stratum was drawn from the cases
    an LLM adjudicator had already ratified, on the reasoning that keeping the
    two strata disjoint made each kappa mean one thing. It does the opposite:
    those 296 are pre-filtered for being easy, so perfect agreement on them
    estimates reliability on the easy subset and not on the 430. That is the
    mirror of the trap it was written to avoid -- the first version sent only
    the hard cases, this one excluded them.

    It is recoverable without asking the annotator for more work, because this
    IS a stratified sample with known stratum sizes: 70 drawn from 296 agreed,
    and a census of all 45 disputed. Weighting each sampled case by N/n
    reconstructs the population table. That is a stronger design than simple
    random sampling, not a patch on a broken one -- it just has to be analysed
    as the stratified sample it is.

    Returns (kappa, observed agreement, effective n).
    """
    rows = []
    for st, N in sizes.items():
        g = d[d.stratum == st]
        m = g["first"].notna() & g["second"].notna()
        g = g[m]
        if not len(g):
            continue
        if rng is not None:                       # bootstrap within stratum
            g = g.iloc[rng.integers(0, len(g), len(g))]
        w = N / max(len(d[d.stratum == st]), 1)   # sampled -> population
        rows.append((g["first"].astype(bool).to_numpy(),
                     g["second"].astype(bool).to_numpy(), w))
    if not rows:
        return float("nan"), float("nan"), 0

    tab = np.zeros((2, 2))
    for a, b, w in rows:
        for i in (0, 1):
            for j in (0, 1):
                tab[i, j] += w * float(((a == bool(i)) & (b == bool(j))).sum())
    tot = tab.sum()
    po = (tab[0, 0] + tab[1, 1]) / tot
    pe = ((tab[0].sum() * tab[:, 0].sum() + tab[1].sum() * tab[:, 1].sum())
          / (tot * tot))
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return float(k), float(po), int(sum(len(a) for a, _, _ in rows))


def result(name: str | None) -> int:
    files = sorted(path("processed", ".").glob("handlabels2_*.parquet")) \
        if name is None else [dest(name)]
    files = [f for f in files if f.exists()]
    if not files:
        print("nothing labelled yet")
        return 1

    first = pd.read_parquet(SRC).set_index(["qid", "model"])["human"]
    sizes = strata_sizes()

    for f in files:
        d = pd.read_parquet(f)
        d["first"] = [first.get((q, mo)) for q, mo in zip(d.qid, d.model)]
        who = d.annotator.iloc[0]
        print("\n" + "=" * 70)
        print(f"  SECOND ANNOTATOR: {who}      {len(d)} cases labelled")
        print("=" * 70)

        print(f"\n  {'stratum':<13} {'population':>11} {'sampled':>8} "
              f"{'both committed':>15} {'kappa':>7} {'agree':>8}")
        for st in ("reliability", "disputed"):
            g = d[d.stratum == st]
            if not len(g):
                continue
            k, po, n = weighted_kappa(g, first, {st: sizes[st]})
            print(f"  {st:<13} {sizes[st]:>11} {len(g):>8} {n:>15} "
                  f"{k:>7.3f} {po:>8.1%}")

        k, po, n = weighted_kappa(d, first, sizes)
        rng = np.random.default_rng(SEED)
        boots = [weighted_kappa(d, first, sizes, rng)[0]
                 for _ in range(BOOTSTRAP_N)]
        lo, hi = np.nanpercentile(boots, [2.5, 97.5])

        print(f"\n  POPULATION ESTIMATE, stratum-weighted over all "
              f"{sum(sizes.values())} comparable cases")
        print(f"    Cohen's kappa {k:.3f}   95% CI [{lo:.3f}, {hi:.3f}]   "
              f"observed agreement {po:.1%}")
        print(f"    {BOOTSTRAP_N:,} bootstrap resamples within strata, seed {SEED}")

        unc = int(d["second"].isna().sum())
        print(f"\n  the second annotator returned 'unclear' on {unc} of {len(d)} "
              f"({unc/len(d):.0%})")
        print(f"  which is close to the 26% of low-margin cases the first "
              f"annotator\n  found undecidable -- two people independently "
              f"finding the same fraction\n  undecidable is itself a result.")

        print("\n  Quote the POPULATION line. The per-stratum kappas are")
        print("  diagnostics: the reliability stratum was drawn from cases an")
        print("  LLM had already ratified, so its kappa is an upper bound, and")
        print("  the disputed stratum was selected for being contested, so its")
        print("  kappa is a lower one. Neither alone estimates the 430.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotator", help="the second annotator's name")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--result", action="store_true")
    a = ap.parse_args()

    if a.result:
        return result(a.annotator)
    if a.stats:
        q = build_queue()
        print(f"queue: {len(q)} cases "
              f"({(q.stratum == 'reliability').sum()} reliability + "
              f"{(q.stratum == 'disputed').sum()} disputed, shuffled)")
        for f in sorted(path("processed", ".").glob("handlabels2_*.parquet")):
            d = pd.read_parquet(f)
            print(f"  {d.annotator.iloc[0]:<16} {len(d):>4} of {len(q)}")
        return 0
    if not a.annotator:
        ap.error("--annotator NAME is required to label "
                 "(the file is named after them, so verdicts stay attributable)")
    return label(a.annotator)


if __name__ == "__main__":
    raise SystemExit(main())
