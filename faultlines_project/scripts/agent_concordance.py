#!/usr/bin/env python
"""Do four independent agents make the same DECISIONS, not just give the same answers?

    python scripts/agent_concordance.py

Runs no model and spends nothing. Everything is already in rq5_agentic.parquet.

THE ANSWER IS NO, AND THAT IS THE POINT OF KEEPING THIS SCRIPT

The backlogged "agent angle" (DECISIONS 2026-07-27 item 3) is *correlated failure
across independent agents* -- silent consensus of reasoning rather than of
answers. It was costed as a second thesis and it stays backlogged.

RQ5 had already run four models as agents with a search tool over the blind
spots, logging `tool_calls` and `used_tools` per model per question. So the cheap
version of the question could be asked for nothing: the models produce the same
wrong ANSWER -- do they also make the same DECISIONS about what to do?

**Measured 2026-08-26: there is nothing here.** This script exists so that
nobody -- including a future version of this project -- spends a week
rediscovering that. It prints the null and the three reasons it is a null.

WHY IT IS A NULL, IN THE ORDER THE CHECKS WERE RUN

1. THE SEARCH DECISION HAS ALMOST NO VARIANCE TO CORRELATE. Mistral and Gemma
   search on 100.0% of questions. Llama searches on 98.5%. Only Qwen ever really
   declines, at 80.1%. Four agents cannot be shown to decide independently or
   dependently when three of them always do the same thing.

2. UNANIMITY IS EXACTLY WHAT INDEPENDENCE PREDICTS. All four search on 80.1% of
   questions; multiplying the four individual rates predicts 78.9%. A ratio of
   **1.02x**. Compare the answer-level result this thesis is built on, where the
   same pooled calculation gives **6.1x** (3.3x within dataset; 9.0x before the
   2026-09-27 dedup). There is no concentration to explain.

3. THE ONE CORRELATION THAT LOOKS REAL IS ONE PAIR REPORTED AS SIX. phi on the
   search decision is undefined for five of the six model pairs, because a
   constant vector has no correlation with anything. An earlier version of this
   script dropped the NaNs and printed the survivor as a "mean pairwise
   correlation of +0.251". That is the Llama-Qwen pair and nothing else, and
   presenting it as a mean over pairs would have been a fabricated finding.
   The count of contributing pairs is now printed beside every mean.

And the one result that superficially contradicted the thesis -- "all four wrong
73.2% when they agreed to search against 84.0% when they disagreed" -- is
entirely an artifact. All 194 disagreement cases are *exactly* the 194 cases
where Qwen skipped the tool. The comparison is not "agents that disagreed" but
"questions where one model did not use the tool", and a model that skips the
tool doing worse is not a finding about agent concordance.

WHAT WOULD ACTUALLY TEST IT, if anyone picks the agent angle up: multi-step
trajectories where there is a real decision each turn -- which query to issue,
which result to trust, when to stop -- so that the decision space is wide enough
for independence to mean something. One tool and one hop is not that.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import path                      # noqa: E402

ARMS = {"wikipedia": "rq5_agentic.parquet", "open web": "rq5_agentic_web.parquet"}


def mean_pairwise(frame: pd.DataFrame, cols) -> tuple[float, int, int]:
    """Mean correlation, HOW MANY PAIRS CONTRIBUTED, and how many were possible.

    Returning the pair count is the whole point. Dropping undefined pairs and
    reporting the survivors as a mean is how one pair became a "mean pairwise
    correlation" in the first draft of this script.
    """
    total = list(combinations(cols, 2))
    vals = []
    for a, b in total:
        x, y = frame[a].astype(float), frame[b].astype(float)
        # A constant column has no correlation with anything. Testing for that
        # BEFORE calling corr() is what keeps numpy from emitting a
        # divide-by-zero warning -- and, more to the point, it is the fact the
        # caller needs: the pair did not contribute.
        if x.std() == 0 or y.std() == 0:
            continue
        v = x.corr(y)
        if v == v:
            vals.append(v)
    return (sum(vals) / len(vals) if vals else float("nan"), len(vals), len(total))


def main() -> int:
    for arm, fname in ARMS.items():
        p = path("processed", fname)
        if not p.exists():
            print(f"{fname} missing -- skipping {arm}")
            continue
        d = pd.read_parquet(p)
        d["short"] = d.model.str.split("/").str[-1].str.slice(0, 22)

        n_models = d.short.nunique()
        full = d.groupby("qid").short.nunique()
        d = d[d.qid.isin(set(full[full == n_models].index))]

        print("=" * 74)
        print(f"AGENT DECISION CONCORDANCE  --  {arm} arm")
        print("=" * 74)

        piv = d.pivot_table(index="qid", columns="short", values="used_tools",
                            aggfunc="first").astype(bool)
        cnt = d.pivot_table(index="qid", columns="short", values="tool_calls",
                            aggfunc="first")
        models = list(piv.columns)
        print(f"  {len(piv):,} questions answered by all {n_models} models\n")

        print("  CHECK 1 -- is there any variance in the decision to search?")
        print(f"    {'model':<24} {'searched':>9} {'std':>7} {'mean calls':>11}")
        flat = 0
        for m in models:
            sd = piv[m].astype(int).std()
            flat += sd == 0
            print(f"    {m:<24} {piv[m].mean():>8.1%} {sd:>7.3f} "
                  f"{cnt[m].mean():>11.2f}")
        print(f"    -> {flat} of {n_models} models NEVER vary. There is almost")
        print("       nothing to correlate.")

        print("\n  CHECK 2 -- is unanimity more common than independence predicts?")
        agree = piv.sum(axis=1)
        unan = float(((agree == 0) | (agree == n_models)).mean())
        exp1, exp0 = 1.0, 1.0
        for m in models:
            q = piv[m].mean()
            exp1 *= q
            exp0 *= (1 - q)
        exp = exp1 + exp0
        print(f"    observed all-or-none      {unan:>7.1%}")
        print(f"    expected if independent   {exp:>7.1%}")
        print(f"    ratio                     {unan/exp:>7.2f}x"
              f"    (the ANSWER-level ratio is 6.1x pooled, 3.3x within dataset)")

        print("\n  CHECK 3 -- how many model pairs actually contribute a number?")
        r, k, tot = mean_pairwise(piv.astype(int), models)
        print(f"    search decision:  mean {r:+.3f} over {k} of {tot} pairs"
              + ("   <- ONE PAIR. Not a mean." if k <= 1 else ""))
        r2, k2, tot2 = mean_pairwise(cnt, models)
        print(f"    number of calls:  mean {r2:+.3f} over {k2} of {tot2} pairs")
        print("    The call-count correlation is real, and it has an innocent")
        print("    explanation this data cannot rule out: harder questions take")
        print("    more lookups for everyone. Effort tracking difficulty is not")
        print("    evidence of shared failure.")

        if "correct" in d.columns:
            print("\n  CHECK 4 -- the result that looked like a finding, and is not")
            allwrong = d.groupby("qid").correct.apply(lambda s: ~s.any())
            j = pd.DataFrame({"unan": (agree == 0) | (agree == n_models),
                              "allwrong": allwrong.reindex(piv.index)}).dropna()
            a1 = j.loc[j.unan, "allwrong"].mean()
            a0 = j.loc[~j.unan, "allwrong"].mean()
            print(f"    all four wrong when they agreed to search:  {a1:>6.1%} "
                  f"(n={int(j.unan.sum())})")
            print(f"    all four wrong when they disagreed:         {a0:>6.1%} "
                  f"(n={int((~j.unan).sum())})")
            dis = piv.index[agree < n_models]
            skips = {m: int((~piv.loc[dis, m]).sum()) for m in models}
            top = max(skips, key=skips.get)
            print(f"    -> of the {len(dis)} 'disagreement' questions, "
                  f"{skips[top]} are {top} skipping the tool.")
            if skips[top] == len(dis):
                print("       That is ALL of them. This compares 'one model did")
                print("       not use the tool' against 'everyone did', which is")
                print("       not a fact about concordance.")
        print()

    print("=" * 74)
    print("VERDICT: NO FINDING. RECORDED SO IT IS NOT RE-DERIVED.")
    print("=" * 74)
    print("  The cheap version of the agent question has been asked and returns")
    print("  nothing. That is worth knowing and worth keeping: it means the")
    print("  agent angle cannot be bolted onto this thesis with data already on")
    print("  disk, and the 2026-07-27 decision to backlog it as separate work")
    print("  stands on measurement now rather than on estimate.")
    print()
    print("  What would actually test it: multi-step trajectories, where there")
    print("  is a real decision each turn -- which query, which result to trust,")
    print("  when to stop. One tool and one hop is not a decision space.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
