#!/usr/bin/env python
"""Does the model HOLD the wrong belief, or did it merely fail to find the fact?

RQ4 handed models a document and measured what retrieval repairs: obscurity
+67.8%, shared misconception +15.7%, a dissociation of +52.1%. RQ5 handed them a
search tool and found 67.9% of blind spots unmoved regardless of which tool.

Both ask the same question -- can the model FIND the right fact -- and neither
can separate it from a different one: does the model hold a belief that evidence
does not dislodge? Two prompt-only arms separate them, and neither needs a
document, a retriever, or a curated gold passage:

  COUNTER-EVIDENCE   the question, plus "some sources disagree with the common
                     answer; reconsider carefully". No new information at all,
                     only a reason to doubt. Anything it repairs was never a
                     retrieval failure.

  ABSTENTION         the question, plus explicit permission to say "I don't
                     know". "Just make it say it doesn't know" is the most
                     common suggestion this project receives; RQ1 answered it
                     with a threshold on confidence, which is not the same thing
                     as ASKING.

THE CONTROL IS THE POINT.  Both prompts are also run on questions the ensemble
already answered correctly. "Counter-evidence repaired 12% of blind spots" means
nothing if it also broke 12% of correct answers -- and telling a model it might
be wrong is exactly the kind of intervention that would.

    python scripts/belief_arms.py --limit 40      # pilot, ~320 generations
    python scripts/belief_arms.py                 # full, ~12,400 generations

Resumable: every completed (qid, model, arm) is checkpointed, so an interrupted
run continues rather than repeating. Writes data/processed/belief_arms.parquet.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path                    # noqa: E402
from faultlines.generate import ask_retry                  # noqa: E402
from faultlines.rq4_retrieval import _grade                # noqa: E402

SEED = CFG["seed"]
MODELS = [m["name"] for m in CFG["ensemble"]]
OUT = path("processed", "belief_arms.parquet")
CONTROL_N = 500
WORKERS = 24

ARMS = {
    "counter": (
        "{q}\n\nSome sources disagree with the common answer to this. "
        "Reconsider carefully, then give your answer."),
    "abstain": (
        "{q}\n\nIf you are not confident in the answer, reply with exactly: "
        "I don't know."),
}

# Matched loosely on purpose. A model told it may abstain does not always use
# the exact words, and counting only the exact string would undercount refusals
# and inflate the error rate -- which would flatter this project's argument that
# abstention does not work. Erring the other way instead.
ABSTAIN_MARKERS = ("i don't know", "i do not know", "i'm not sure",
                   "i am not sure", "unknown", "no comment", "cannot determine",
                   "not confident")


def is_abstention(answer: str) -> bool:
    a = str(answer).strip().lower().rstrip(".")
    return any(m in a for m in ABSTAIN_MARKERS)


def population(limit: int | None) -> pd.DataFrame:
    """The blind spots, plus a control of questions the ensemble got right.

    The control is seeded and drawn from the SAME corpus, so the only thing
    separating the two strata is the outcome being intervened on.
    """
    rec = pd.read_parquet(path("processed", "records.parquet"))
    blind = rec[rec.silent_consensus].copy()
    blind["stratum"] = "blind"

    ok = rec[(~rec.majority_wrong) & (rec.n_clusters == 1)]
    ctrl = ok.sample(n=min(CONTROL_N, len(ok)), random_state=SEED).copy()
    ctrl["stratum"] = "control"

    q = pd.concat([blind, ctrl], ignore_index=True)
    if limit:
        # Proportional, so a pilot still has both strata.
        q = pd.concat([q[q.stratum == s].head(max(1, limit // 2))
                       for s in ("blind", "control")], ignore_index=True)

    # records.parquet carries `gold` but not `aliases`, and grading without the
    # alias list is grading against one accepted spelling -- which is ISSUES #39
    # and the reason the answer-key-too-strict flag exists. Joined from the
    # answers frame, which is where the graders read it from too.
    al = (pd.read_parquet(path("interim", "answers.parquet"),
                          columns=["qid", "aliases"])
            .drop_duplicates("qid").set_index("qid")["aliases"])
    q["aliases"] = q["qid"].map(al)
    missing = int(q["aliases"].isna().sum())
    if missing:
        raise SystemExit(f"{missing} questions have no alias list -- refusing "
                         "to grade against a single spelling")
    return q[["qid", "dataset", "question", "gold", "aliases", "meta", "stratum"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--arm", choices=list(ARMS), default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and the prompts, generate nothing")
    a = ap.parse_args()

    q = population(a.limit)
    arms = [a.arm] if a.arm else list(ARMS)
    # dicts, not itertuples: rq4_retrieval._grade indexes its row as row["gold"],
    # and a namedtuple only answers to attributes. Reusing the project's grader
    # is the whole point -- a second grading path is a second set of bugs.
    jobs = [(r, m, arm) for r in q.to_dict("records")
            for m in MODELS for arm in arms]

    done = set()
    if OUT.exists():
        prev = pd.read_parquet(OUT)
        done = set(zip(prev.qid, prev.model, prev.arm))
        jobs = [j for j in jobs
                if (j[0]["qid"], j[1].split("/")[-1], j[2]) not in done]

    print(f"{len(q):,} questions "
          f"({(q.stratum == 'blind').sum()} blind + "
          f"{(q.stratum == 'control').sum()} control)"
          f" x {len(MODELS)} models x {len(arms)} arms")
    print(f"{len(jobs):,} generations to run"
          f"{f' ({len(done):,} already done)' if done else ''}")

    if a.dry_run:
        ex = q.iloc[0]
        for arm in arms:
            print(f"\n--- {arm} ---\n{ARMS[arm].format(q=ex.question)}")
        return 0
    if not jobs:
        print("nothing to do")
        return 0

    rows = []

    def one(job):
        r, model, arm = job
        ans, conf = ask_retry(model, ARMS[arm].format(q=r["question"]),
                              dataset=r["dataset"], label=f"{arm}:{r['qid']}")
        abst = is_abstention(ans)
        return {
            "qid": r["qid"], "dataset": r["dataset"], "stratum": r["stratum"],
            "model": model.split("/")[-1], "arm": arm,
            "answer": ans, "confidence": conf,
            "abstained": abst,
            # An abstention is not a correct answer. Grading it as one would
            # turn "I don't know" into a repair, which is the whole trap.
            "correct": False if abst else _grade(ans, r),
        }

    prior = pd.read_parquet(OUT) if OUT.exists() else None

    def save():
        """Checkpoint = everything that was on disk BEFORE this run, plus what
        this run has produced so far.

        Read `prior` once, outside. Re-reading OUT on every checkpoint appends
        the growing in-memory list to a file that already contains it, so the
        row count climbs superlinearly -- 22,320 rows for 4,320 real ones on the
        first full run. The duplicates were harmless to the numbers (they are
        exact copies) but they broke the progress check built on top of them,
        which reported the run finished when it was a third done.
        """
        out = pd.DataFrame(rows)
        if prior is not None:
            out = pd.concat([prior, out], ignore_index=True)
        out = out.drop_duplicates(["qid", "model", "arm"], keep="last")
        out.to_parquet(OUT)
        return out

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, row in enumerate(pool.map(one, jobs), 1):
            rows.append(row)
            if i % 400 == 0:
                save()          # a crash must not discard paid-for generations
                print(f"   {i:,}/{len(jobs):,}", flush=True)

    out = save()
    print(f"\n-> {OUT.name}   {len(out):,} rows")

    report(out)
    return 0


def report(d: pd.DataFrame) -> None:
    """Per question: did a majority of the four models answer correctly?

    A majority rather than "any", because one model out of four being right is
    what the ensemble ALREADY could not detect -- that is the silent-consensus
    definition. The ensemble is repaired when the answer it would actually give
    changes, and with four models that needs a majority.
    """
    g = (d.groupby(["arm", "stratum", "qid"])
           .agg(right=("correct", "sum"),
                abst=("abstained", "sum"),
                n=("correct", "size")).reset_index())
    g["repaired"] = g.right > g.n / 2
    g["all_abstained"] = g.abst == g.n

    print("\n" + "=" * 66)
    print("BELIEF ARMS")
    print("=" * 66)
    print(f"  {'arm':<10} {'stratum':<9} {'n':>5} {'majority right':>15} "
          f"{'any abstention':>15}")
    for (arm, st), s in g.groupby(["arm", "stratum"]):
        print(f"  {arm:<10} {st:<9} {len(s):>5} "
              f"{s.repaired.mean():>14.1%} {(s.abst > 0).mean():>15.1%}")

    print("\n  reading:")
    for arm in sorted(g.arm.unique()):
        b = g[(g.arm == arm) & (g.stratum == "blind")]
        c = g[(g.arm == arm) & (g.stratum == "control")]
        if not len(b) or not len(c):
            continue
        print(f"    {arm:<9} repaired {b.repaired.mean():.1%} of blind spots, "
              f"and broke {1 - c.repaired.mean():.1%} of correct answers")


if __name__ == "__main__":
    raise SystemExit(main())
