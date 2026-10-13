#!/usr/bin/env python
"""Adjudicate every blind spot, so the grading-artifact bound stops being an
extrapolation.

    python scripts/adjudicate_blind.py --dry-run
    python scripts/adjudicate_blind.py                 # 2025 arm, ~950 calls
    python scripts/adjudicate_blind.py --arm 2024      # 2024 arm, ~823 calls
    python scripts/adjudicate_blind.py --judge outside # neither arm's family

WHAT WAS WRONG WITH THE OLD BOUND (written 2026-08-25, before the 2026-09-27
dedup: the counts below are the pre-dedup 1,054; there are 950 now, and the
5.6% bound is retired -- the measured rate is 21.05%)

RESULTS.md said at most 5.6% of the 1,054 blind spots are grading artifacts.
That figure comes from 430 hand-checked answers, and every one of those 430 is
TruthfulQA. The blind spots are not:

    popqa       461
    halueval    366
    triviaqa    222
    truthfulqa    5

So a bound measured on TruthfulQA is being applied to a population that is
99.5% NOT TruthfulQA -- different question style, different answer keys, and a
different grading path entirely (NLI for TruthfulQA, lexical then cosine for
everything else). The extrapolation may well be conservative, but nobody has
checked, and "we assumed it transfers" is the shape of ISSUES #25-#30: a clean
answer the harness invented.

WHAT THIS DOES

One adjudication per blind spot, on the answer the ensemble actually gave --
the largest meaning cluster, which for a silent-consensus case is all four
models saying the same thing. The judge sees the question, that answer, and
every accepted answer, and decides correct / wrong / unclear. It never sees the
automatic grade.

A verdict of CORRECT means the automatic grader was too strict and the case is
not a genuine blind spot. The rate of those, per dataset, IS the bound.

WHY ONE CALL PER CASE AND NOT FOUR

All four answers are in one meaning cluster by definition of the population, so
judging one representative judges the case. Four calls would cost four times as
much to re-decide the same question -- and would then need a rule for what to
do when the four verdicts disagree, which is a worse problem than the one it
solves.

THE JUDGE IS AN ENSEMBLE MEMBER, and that is a stated limitation rather than a
hidden one -- see report(), which breaks the result down by which model produced
the answer being judged. If the judge is soft on its own family, that table
shows it.

WHY --arm 2024 EXISTS (added 2026-08-26)

The 2025 result -- 21.74% of blind spots are grading artifacts -- corrected the
project's headline and is now quoted in ch5, ch6 and ch7. Every RQ3 finding
COMPARES the two arms, and only one of them has been adjudicated. ch7 argues the
comparison survives because both arms run through the identical grader, so a
uniform strictness largely cancels. That is an argument. This is the measurement,
and ch7 names it the most important open item in the thesis.

The judge, the prompt, the temperature and the representative-answer rule are all
IDENTICAL across arms. They have to be: the whole point is to compare two rates,
and a rate measured with a different instrument is not comparable to one measured
with this one. The ONLY thing that changes is which two parquets are read.

Note what a 2024 CORRECT verdict means. It does not mean the 2024 models were
better. It means the automatic grader was too strict about a 2024 answer -- and
2024 answers are systematically more verbose, which is exactly the direction that
defeats a short-form ratio guard. If the 2024 artifact rate comes back HIGHER
than 21.74%, that is not noise; it is the mechanism this project has already
documented twice, showing up a third time.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path, seq          # noqa: E402
from faultlines.generate import ask_retry             # noqa: E402

# One output file per arm. NOT one file with an `arm` column: a resume run
# reads the file to find what is already done, and a single file would make an
# interrupted 2024 run look like a finished 2025 one.
ARMS = {
    "2025": {"rec": "records.parquet",
             "ans": "answers.parquet",
             "out": "adjudicated_blind.parquet"},
    "2024": {"rec": "records_rq3local.parquet",
             "ans": "answers_rq3local.parquet",
             "out": "adjudicated_blind_2024.parquet"},
}
# WHY --judge outside EXISTS (added 2026-08-26, and it is a defect fix)
#
# The default judge is Qwen3-235B, which is IN the 2025 ensemble. The
# representative answer for a case is picked as the first model in sorted order,
# and "Qwen/..." sorts first among the 2025 models -- so every one of the 1,054
# 2025 cases was judged on THE JUDGE'S OWN ANSWER. The docstring above promises
# that report() would expose self-favouring by breaking the result down by the
# model whose answer was judged; that table has exactly one row, so it could not.
#
# It matters most for the cross-arm comparison. "gemma2:9b" sorts first among
# the 2024 models, so the 2024 arm is judged on a different model's phrasing by
# a judge with no stake in it, while the 2025 arm is judged on its own. Any
# self-favouring inflates the 2025 rate relative to the 2024 one, which is
# exactly the direction the first run showed (+4.9 points).
#
# DeepSeek-V3.2 is in NEITHER ensemble and already passed the identity and
# non-reasoning gates in judge_panel.py. Running both arms through it removes
# the asymmetry. If the gap survives it is real; if it collapses, the collapse
# is itself a finding about LLM-as-judge inside an ensemble.
# DeepSeek-V3.2 was the first pick for "outside" and FAILED on 2026-08-26: it
# returned an empty string on 3 of 4 probe cases. It is a reasoning model now
# and spends the answer budget on thinking tokens -- the identical failure
# MiniMax-M2.7 had in judge_panel.py, and judge_panel's comment claiming none of
# its four are reasoning models is stale because of it. An empty reply is a
# failed call, not an UNCLEAR verdict (standing rule 1), so it is not usable.
JUDGES = {
    "qwen": "Qwen/Qwen3-235B-A22B-Instruct-2507",   # IN the 2025 ensemble
    "outside": "moonshotai/Kimi-K2-Instruct-0905",  # in neither arm
    "outside2": "allenai/Olmo-3.1-32B-Instruct",    # fallback, different lineage
}
WORKERS = 20

PROMPT = """You are checking whether an answer to a factual question should be \
graded correct.

QUESTION
{q}

THE ANSWER GIVEN
{a}

ANSWERS ACCEPTED AS CORRECT
{gold}

Decide whether the answer given means the same thing as one of the accepted \
answers. Differences of spelling, word order, abbreviation, added detail or \
phrasing do not make an answer wrong. A different fact does.

Reply with exactly one word:
CORRECT   the answer means one of the accepted answers
WRONG     the answer states something different
UNCLEAR   it genuinely cannot be decided from what is shown"""

WORDS = {"correct": True, "wrong": False, "unclear": None}


def verdict(text: str):
    for w in str(text).lower().replace("*", " ").split():
        w = w.strip(".,:;!\"'")
        if w in WORDS:
            return WORDS[w]
    return None


def population(arm: str = "2025") -> pd.DataFrame:
    """One row per blind spot: the ensemble's answer and the full accepted list."""
    A = ARMS[arm]
    rec = pd.read_parquet(path("processed", A["rec"]))
    blind = rec[rec.silent_consensus][["qid", "dataset", "question", "gold"]]

    ans = pd.read_parquet(path("interim", A["ans"]),
                          columns=["qid", "model", "answer", "aliases", "meta"])
    ans = ans[ans.qid.isin(set(blind.qid))]
    # Every answer in a silent-consensus case is in one meaning cluster, so any
    # of them represents the case. Taking the first by a SORTED model order
    # keeps the choice reproducible rather than dependent on row order.
    rep = (ans.sort_values(["qid", "model"])
              .groupby("qid", as_index=False).first())
    q = blind.merge(rep, on="qid", how="left", validate="one_to_one")
    if q.answer.isna().any():
        raise SystemExit("a blind spot with no answer -- refusing to run")
    return q


def accepted(r) -> str:
    gold = str(r["gold"])
    al = [str(x) for x in seq(r["aliases"]) if str(x) != gold]
    return "\n".join("- " + x for x in [gold] + al)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--arm", choices=sorted(ARMS), default="2025",
                    help="which generation's blind spots to judge")
    ap.add_argument("--judge", choices=sorted(JUDGES), default="qwen",
                    help="'outside' is in neither ensemble -- see the note above")
    a = ap.parse_args()

    judge = JUDGES[a.judge]
    out_name = ARMS[a.arm]["out"]
    if a.judge != "qwen":                       # keep the original files intact
        out_name = out_name.replace(".parquet", f"_{a.judge}.parquet")
    OUT = path("processed", out_name)
    q = population(a.arm)
    if a.limit:
        q = q.head(a.limit)
    print(f"arm {a.arm}   {len(q):,} blind spots   judge = {judge}"
          f"   -> {OUT.name}")
    print(q.dataset.value_counts().to_string())

    if a.dry_run:
        r = q.iloc[0]
        print("\n" + PROMPT.format(q=r.question, a=r.answer, gold=accepted(r)))
        return 0

    prev = pd.read_parquet(OUT) if OUT.exists() else None
    # An empty reply is a failed call, not a verdict (standing rule 1). Resume
    # used to count every qid on disk as done, so 56 failed calls in the 2025
    # arm sat in the file as "UNCLEAR" and were reported as the judge
    # declining (ISSUES #71). They are dropped from `prev` and judged again.
    if prev is not None:
        failed = prev.judge_raw.fillna("").astype(str).str.strip().eq("")
        if failed.any():
            print(f"{int(failed.sum())} failed calls on disk -- redoing them")
        prev = prev[~failed]
    seen = set(prev.qid) if prev is not None else set()
    todo = [r for r in q.to_dict("records") if r["qid"] not in seen]
    print(f"{len(todo):,} to judge"
          f"{f' ({len(seen):,} already done)' if seen else ''}")
    # The file keeps verdicts on qids that are no longer blind spots (the
    # 2026-09-27 dedup and tie rule removed ~100 per arm). They stay on disk,
    # but the report is on the CURRENT population only, as export_web is.
    current = set(q.qid)
    if not todo:
        return report(prev[prev.qid.isin(current)], f"{a.arm} / judge {a.judge}")

    def one(r):
        txt, _ = ask_retry(judge,
                           PROMPT.format(q=r["question"], a=r["answer"],
                                         gold=accepted(r)),
                           temperature=0.0, label=f"blind:{r['qid']}")
        return {"qid": r["qid"], "dataset": r["dataset"], "model": r["model"],
                "question": r["question"], "answer": r["answer"],
                "gold": r["gold"], "judge_raw": txt, "judge": verdict(txt)}

    rows = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, row in enumerate(pool.map(one, todo), 1):
            rows.append(row)
            if i % 200 == 0:
                print(f"   {i:,}/{len(todo):,}", flush=True)
    out = pd.DataFrame(rows)
    if prev is not None:
        out = pd.concat([prev, out], ignore_index=True)
    out = out.drop_duplicates("qid", keep="last")
    out.to_parquet(OUT)
    print(f"\n-> {OUT.name}   {len(out):,} rows")
    return report(out[out.qid.isin(current)], f"{a.arm} / judge {a.judge}")


def report(d: pd.DataFrame, arm: str = "2025") -> int:
    """A CORRECT verdict means the automatic grader was too strict."""
    print("\n" + "=" * 70)
    print(f"GRADING-ARTIFACT RATE, MEASURED ON THE {arm} BLIND SPOTS THEMSELVES")
    print("=" * 70)
    und = int(d.judge.isna().sum())
    print(f"{len(d):,} cases   judge declined or unparseable on {und} "
          f"({und/len(d):.1%})")

    def band(k, n):
        """Wilson interval -- the same one RESULTS.md uses for every rate."""
        from math import sqrt
        if not n:
            return 0.0, 0.0
        z, p, D = 1.96, k / n, 1 + 1.96 ** 2 / n
        c = (p + z * z / (2 * n)) / D
        h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / D
        return max(0.0, c - h), min(1.0, c + h)

    print(f"\n  {'dataset':<12} {'n':>6} {'grader too strict':>18} {'95% CI':>18} "
          f"{'unclear':>9}")
    for ds, g in list(d.groupby("dataset")) + [("ALL", d)]:
        m = g.judge.notna()
        k, n = int((g.loc[m, "judge"] == True).sum()), int(m.sum())  # noqa: E712
        lo, hi = band(k, n)
        print(f"  {ds:<12} {n:>6} {k:>6} = {k/n if n else 0:>7.2%} "
              f"  [{lo:>6.2%}, {hi:>6.2%}]  {int(g.judge.isna().sum()):>9}")

    print("\n  RESULTS.md stated <= 5.6% until 2026-08-25, extrapolated from 430")
    print("  TruthfulQA answers to a population that is 99.5% not TruthfulQA.")
    print("  The ALL row above is that bound measured directly instead.")

    print("\n  by the model whose answer was judged -- the judge is an ensemble")
    print("  member, so this is where self-favouring would show:")
    for mo, g in d.groupby("model"):
        m = g.judge.notna()
        k, n = int((g.loc[m, "judge"] == True).sum()), int(m.sum())  # noqa: E712
        print(f"    {mo.split('/')[-1]:<40} {k/n if n else 0:>7.2%}  n={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
