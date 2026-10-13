"""Screening design - the fix for the 5-silent-consensus bottleneck.

Silent consensus is ~1.7% of random questions, so random sampling is fishing.
Instead the four models are run over a LARGE pool and only the all-agree cases
are kept (those are where silent consensus can occur); a random control slice is
retained to report the honest base rate. Grading then happens only on the kept set.

    python -m faultlines.screen --pilot --limit 15      # small live test
    python -m faultlines.screen --pilot --pool 20000    # full (hours; hand-off)

Reuses generate.ask (4 models) and semantics.cluster (meaning grouping).
"""
from __future__ import annotations

import argparse

import pandas as pd

from faultlines.config import CFG, SEED, stage
from faultlines.generate import ask_retry
from faultlines.semantics import cluster


def screen_one(answers: list[str]) -> dict:
    """Given the four models' answers to one question, decide agreement."""
    ids = cluster(answers)
    n = len(set(ids))
    return {"n_clusters": n, "all_agree": n == 1}


def run(pilot: bool = True, limit: int | None = None, pool: int | None = None,
        tag: str = "", ensemble: str = "ensemble") -> pd.DataFrame:
    src = stage("interim", "questions", pilot, "")
    q = pd.read_parquet(src)
    if pool is not None:
        # REFUSE to silently shrink. The old code did min(pool, len(q)), so
        # `--pool 20000` against the 300-row pilot file screened 300 rows and
        # printed a yield percentage as though it had worked. That yield is what
        # sizes the entire Audit population, so a silently truncated screen
        # produces a real-looking number from a fraction of the intended data.
        if pool > len(q):
            raise SystemExit(
                f"pool={pool} but {src.name} holds only {len(q)} questions.\n"
                f"Build the full question set first:\n"
                f"  python -m faultlines.datasets        # (no --pilot)\n"
                f"Refusing to silently screen {len(q)} and report it as {pool}.")
        q = q.sample(n=pool, random_state=SEED)
    if limit is not None:
        q = q.head(limit)
    models = [m["name"] for m in CFG[ensemble]]

    dest = stage("processed", "screened", pilot, tag)

    # Generate model-by-model (OUTER loop over models), not question-by-question:
    # on an 8 GB GPU only one model fits, so per-question model-swapping would
    # reload weights on every call. This mirrors generate.run()'s VRAM ordering.
    gens = stage("interim", "screen_gens", pilot, tag)
    grows = pd.read_parquet(gens).to_dict("records") if gens.exists() else []
    # Failed calls are stored with an empty answer; excluding them from `done`
    # is what makes resume retry them instead of freezing them into the data.
    # Same rule as generate.run() and baseline.run().
    grows = [r for r in grows if str(r["answer"]).strip()]
    done = {(r["model"], r["qid"]) for r in grows}
    items = q.to_dict("records")
    for m in models:
        todo = [it for it in items if (m, it["qid"]) not in done]
        print(f"  {m}: {len(todo)} questions")
        for j, it in enumerate(todo, 1):
            a, _ = ask_retry(m, it["question"], dataset=it["dataset"], label=it["qid"])
            grows.append({"qid": it["qid"], "model": m, "answer": a})
            if j % 25 == 0 or j == len(todo):
                pd.DataFrame(grows).to_parquet(gens)

    # assemble per question and cluster
    gdf = pd.DataFrame(grows)
    meta = q.set_index("qid")
    rows = []
    for qid, grp in gdf.groupby("qid"):
        answers = grp["answer"].tolist()
        sc = screen_one(answers)
        rows.append({"qid": qid, "dataset": meta.loc[qid, "dataset"],
                     "question": meta.loc[qid, "question"], "gold": meta.loc[qid, "gold"],
                     "n_clusters": sc["n_clusters"], "all_agree": sc["all_agree"],
                     "answers": answers})
    res = pd.DataFrame(rows)
    res.to_parquet(dest)
    kept = res[res["all_agree"]]
    print("=" * 60)
    print(f"SCREENED {len(res)} questions  ->  {len(kept)} all-agree "
          f"({len(kept) / max(1, len(res)):.0%} yield)")
    print("  all-agree cases are the silent-consensus candidates; grade only these.")
    print(f"wrote {dest.name}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", default=True)
    ap.add_argument("--full", dest="pilot", action="store_false")
    ap.add_argument("--limit", type=int, default=None, help="first N questions (small test)")
    ap.add_argument("--pool", type=int, default=None, help="random pool size (full run)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--ensemble", default="ensemble")
    a = ap.parse_args()
    run(a.pilot, a.limit, a.pool, a.tag, a.ensemble)
