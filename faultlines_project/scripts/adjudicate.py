#!/usr/bin/env python
"""A third rater on the 430 hand-labelled cases, so the human is not alone.

All 430 verdicts in `handlabels.parquet` are one person's. The kappas the
project reports (0.959 control / 0.322 target) are agreement with the MACHINE
grader, not with another human, so there is no inter-rater reliability figure at
all -- the standard thing an examiner asks for, and `pipeline.html` L14 already
admits it.

A second human on 100 cases is the real fix and is scheduled. This is the
supplementary check that can be run today: a frontier model reads the same
question, the same answer and the same accepted gold answers, and makes the same
call -- correct, wrong, or genuinely unclear -- with both the human verdict and
the machine verdict withheld.

**It is not a substitute and must never be reported as one.** What it buys:

  - a kappa against a rater whose failure modes differ from the NLI pipeline's,
    on all 430 rather than a subset
  - an explicit list of every case where the two disagree, which is the material
    a second human should be given first
  - a check nobody in this project has run: does the adjudicator agree with the
    human MORE on answers its own family produced? If it does, self-favouring
    bias is real here and the whole exercise is weaker than it looks.

    python scripts/adjudicate.py --dry-run
    python scripts/adjudicate.py

Writes data/processed/adjudicated.parquet. ~430 generations.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path, seq       # noqa: E402
from faultlines.generate import ask_retry          # noqa: E402

OUT = path("processed", "adjudicated.parquet")
SRC = path("processed", "handlabels.parquet")

# The largest model in the ensemble. Using an ensemble member as adjudicator is
# a real limitation and is reported rather than hidden: the self-favouring check
# in report() exists precisely because of it. The task is different from the one
# it is being judged on -- deciding whether "Sheppey" matches "Isle of Sheppey"
# is grading, not answering -- but that argument is not a substitute for the
# measurement, so the measurement is taken.
JUDGE = "Qwen/Qwen3-235B-A22B-Instruct-2507"
JUDGE_FAMILY = "Qwen"

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
    """First recognisable word wins; anything else is a refusal to decide.

    Deliberately strict about the vocabulary and lenient about position: models
    prepend things. Returning None for unparseable output puts it in the same
    bucket as UNCLEAR, which is the conservative direction -- it cannot
    manufacture agreement.
    """
    for w in str(text).lower().replace("*", " ").split():
        w = w.strip(".,:;!\"'")
        if w in WORDS:
            return WORDS[w]
    return None


def kappa(a: pd.Series, b: pd.Series) -> float:
    """Cohen's kappa on the rows where BOTH raters committed to true/false."""
    m = a.notna() & b.notna()
    a, b = a[m].astype(bool), b[m].astype(bool)
    if not len(a):
        return float("nan")
    po = float((a == b).mean())
    pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def accepted(r) -> str:
    """Gold first, then every alias -- the list the human saw."""
    gold = str(r["gold"])
    al = [str(x) for x in seq(r["aliases"]) if str(x) != gold]
    return "\n".join("- " + x for x in [gold] + al)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    h = pd.read_parquet(SRC)
    # THE ALIAS LISTS (ISSUES #71). The human labelled against the gold AND
    # every accepted alias; this judge was shown the gold alone, so a "wrong"
    # here could mean "not the canonical wording". 40 of the 45 human/judge
    # disputes were human=correct, judge=wrong -- the signature of a narrower
    # key. handlabels.parquet stores no aliases, so they are joined back in.
    al = (pd.read_parquet(path("interim", "answers.parquet"),
                          columns=["qid", "aliases"])
            .drop_duplicates("qid").set_index("qid")["aliases"])
    h["aliases"] = h.qid.map(al)
    if h.aliases.isna().any():
        raise SystemExit("a case with no alias list -- refusing to run")
    if a.limit:
        h = h.head(a.limit)

    if a.dry_run:
        r = h.iloc[0]
        print(PROMPT.format(q=r.question, a=r.answer, gold=accepted(r)))
        print(f"\n{len(h)} cases, judge = {JUDGE}")
        return 0

    done = pd.read_parquet(OUT) if OUT.exists() else None
    if done is not None:                        # failed calls are not verdicts
        done = done[done.judge_raw.fillna("").astype(str).str.strip().ne("")]
    seen = set(zip(done.qid, done.model)) if done is not None else set()
    todo = [r for r in h.to_dict("records") if (r["qid"], r["model"]) not in seen]
    print(f"{len(h)} cases, {len(todo)} to judge, judge = {JUDGE}")
    if not todo:
        return report(done)

    def one(r):
        txt, _ = ask_retry(JUDGE,
                           PROMPT.format(q=r["question"], a=r["answer"],
                                         gold=accepted(r)),
                           temperature=0.0, label=f"adj:{r['qid']}")
        return {"qid": r["qid"], "model": r["model"], "stratum": r["stratum"],
                "human": r["human"], "machine": r["machine"],
                "margin": r["margin"], "question": r["question"],
                "answer": r["answer"], "gold": r["gold"],
                "judge_raw": txt, "judge": verdict(txt)}

    with ThreadPoolExecutor(max_workers=16) as pool:
        rows = list(pool.map(one, todo))
    out = pd.DataFrame(rows)
    if done is not None:
        out = pd.concat([done, out], ignore_index=True)
    out.to_parquet(OUT)
    print(f"-> {OUT.name}   {len(out)} rows")
    return report(out)


def report(d: pd.DataFrame) -> int:
    print("\n" + "=" * 68)
    print("THIRD RATER  --  supplementary, NOT a substitute for a second human")
    print("=" * 68)
    und = d.judge.isna().sum()
    print(f"{len(d)} cases   judge declined or was unparseable on {und} "
          f"({und/len(d):.1%})")

    print(f"\n  {'pair':<28} {'kappa':>7} {'agree':>8} {'n':>6}")
    for name, x, y in [("human  vs  judge", d.human, d.judge),
                       ("human  vs  machine", d.human, d.machine),
                       ("judge  vs  machine", d.judge, d.machine)]:
        m = x.notna() & y.notna()
        print(f"  {name:<28} {kappa(x, y):>7.3f} "
              f"{(x[m].astype(bool) == y[m].astype(bool)).mean():>8.1%} {m.sum():>6}")

    # n is the number of rows the kappa was COMPUTED on -- both raters
    # committed -- not the number of rows in the stratum. Printing len(g) here
    # showed 100 and 330 against kappas measured on 97 and 244, which is the
    # denominator-mismatch shape of ISSUES #43.
    def n_both(x, y):
        return int((x.notna() & y.notna()).sum())

    print("\n  by stratum, human vs judge:")
    for st, g in d.groupby("stratum"):
        print(f"    {st:<9} kappa {kappa(g.human, g.judge):>6.3f}   "
              f"n={n_both(g.human, g.judge)} of {len(g)}")

    # The check that exists because the judge is an ensemble member.
    print("\n  self-favouring check -- does the judge agree with the human MORE")
    print("  on answers its own family produced?")
    own = d.model.str.contains(JUDGE_FAMILY, case=False)
    for lab, g in [(f"{JUDGE_FAMILY} answers", d[own]), ("other models", d[~own])]:
        print(f"    {lab:<16} kappa {kappa(g.human, g.judge):>6.3f}   "
              f"n={n_both(g.human, g.judge)} of {len(g)}")

    dis = d[d.human.notna() & d.judge.notna() &
            (d.human.astype(bool) != d.judge.astype(bool))]
    print(f"\n  {len(dis)} cases where the human and the judge disagree.")
    print("  These are the rows a second human should be handed first.")
    for r in dis.head(5).itertuples():
        print(f"    [{'human right' if r.human else 'human wrong'} / judge "
              f"{'correct' if r.judge else 'wrong'}]  {str(r.question)[:58]}")
        print(f"        answered {str(r.answer)[:44]!r}   gold {str(r.gold)[:34]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
