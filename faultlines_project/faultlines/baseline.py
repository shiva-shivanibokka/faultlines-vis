"""Level 6 — the fair fight: cross-model disagreement vs Semantic Entropy.

Semantic Entropy (Kuhn 2023; Farquhar, Nature 2024) samples ONE model several
times at temperature, groups its own answers by meaning, and measures the
spread. It detects SELF-inconsistency. FaultLines detects CROSS-MODEL
disagreement. The question is whether four different models beat one model
asked four times.

The design point worth saying out loud: both arms get the SAME generation
budget (4 generations per question) and the SAME clustering, so the only
variable is whether those four generations come from one model or four.
That isolates model diversity, which is the actual claim.

Reading the AUC:  0.50 useless | 0.70 respectable | 0.80 strong | 0.95+ suspect
a leak in the grading. Anchors: Farquhar 0.790; Gorbett 0.727 cross vs 0.595 single.

    python -m faultlines.baseline --pilot
"""
from __future__ import annotations

import argparse
import math
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from .config import CFG, stage
from .generate import ask_retry
from .semantics import cluster

B = CFG["baseline"]


def entropy(answers: list[str]) -> float:
    """Shannon entropy over MEANING clusters, not over strings.

    Four different phrasings of one answer = one cluster = zero entropy.
    That is the whole idea of the method: it is not measuring wording.
    """
    ids = cluster(answers)
    n = len(ids)
    counts: dict[int, int] = {}
    for c in ids:
        counts[c] = counts.get(c, 0) + 1
    return -sum((k / n) * math.log(k / n) for k in counts.values())


def stratified_subset(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    """n rows, allocated across datasets in proportion to their size.

    Three things this gets right that a naive `df.sample(n)` does not:

    1. **Proportional, not equal.** An equal split would give TruthfulQA the same
       weight as TriviaQA despite being 1/47th the size, so the subset would stop
       resembling the corpus and the AUC measured on it would not transfer.
    2. **Largest-remainder rounding.** Proportional shares are fractional; naive
       rounding overshoots or undershoots n. This allocates the floor to each,
       then hands the leftover slots to the largest fractional parts, so the
       total is EXACTLY n.
    3. **Exhaustion guard (defensive).** The min() and the `room` filter stop a
       dataset being allocated more rows than it has. Note this cannot trigger
       under proportional allocation -- a quota of n * size/total never exceeds
       size while n <= total -- so it only matters if the allocation rule is
       ever changed to something non-proportional. Kept deliberately, because a
       future "minimum 500 per dataset" floor WOULD make it reachable.

    What this does NOT do: guarantee any dataset is large enough to support a
    per-dataset claim. TruthfulQA gets ~71 of 8,000 here, which is fine because
    the baseline's job is one POOLED comparison; TruthfulQA-specific numbers come
    from the ensemble arm, which carries all 380.

    Seeded, so the same subset is reproducible.
    """
    sizes = df["dataset"].value_counts()
    avail = sizes.to_dict()
    quota = {k: n * v / len(df) for k, v in avail.items()}

    take = {k: min(int(q), avail[k]) for k, q in quota.items()}
    # hand out remaining slots by largest fractional part, skipping exhausted sets
    while sum(take.values()) < n:
        room = {k: quota[k] - take[k] for k in take if take[k] < avail[k]}
        if not room:
            break                                   # corpus smaller than n
        take[max(room, key=room.get)] += 1

    parts = [g.sample(n=take[ds], random_state=seed)
             for ds, g in df.groupby("dataset") if take.get(ds)]
    out = pd.concat(parts).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    print(f"stratified subset: {len(out)} of {len(df)}")
    for ds in sorted(take):
        print(f"  {ds:11} {take[ds]:>6,} of {avail[ds]:>6,}"
              f"   corpus {avail[ds]/len(df):5.1%} -> subset {take[ds]/len(out):5.1%}")
    return out


def run(pilot: bool = True, limit: int | None = None, tag: str = "",
        ensemble: str = "ensemble", subset: int | None = None) -> pd.DataFrame:
    """tag must match the ensemble arm this baseline is FOR.

    The single model has to come from the same ensemble being tested -- the
    claim is "four models once vs ONE OF THOSE FOUR four times". Pointing the
    baseline at a model outside the ensemble measures model choice instead of
    model diversity, which is a different (and uninteresting) experiment.
    """
    src = stage("processed", "records", pilot, tag)
    df = pd.read_parquet(src)
    if limit is not None:
        df = df.head(limit)
    if subset is not None:
        # The comparison is made on THESE qids for both arms, so composition
        # cannot bias it -- ensemble and baseline see identical questions. The
        # subset only affects how far the number generalises, which is why the
        # chosen qids are written out for the ensemble side to match against.
        df = stratified_subset(df, subset, CFG["seed"])
        qids = stage("processed", "baseline_subset_qids", pilot, tag)
        df[["qid", "dataset"]].to_parquet(qids)
        print(f"  subset qids -> {qids.name}")
    dest = stage("interim", "baseline", pilot, tag)

    models = ([m["name"] for m in CFG[ensemble]] if B["run_on_all_models"]
              else [CFG[ensemble][0]["name"]])

    rows = []
    if dest.exists():
        prev = pd.read_parquet(dest)
        # Keep only rows where EVERY sample generated. An empty sample means the
        # call failed, and the same trap generate.run() already guards against
        # applies here: if failures counted as "done", resume would make a
        # transient 429 into permanent contamination. Worse than a hole, because
        # the empty string is not missing -- it clusters as its own meaning and
        # inflates that question's entropy.
        ok = prev["samples"].apply(lambda s: all(str(x).strip() for x in s))
        rows = prev[ok].to_dict("records")
        if (~ok).any():
            print(f"resuming: {len(rows)} clean rows on disk; "
                  f"regenerating {int((~ok).sum())} with an empty sample")
    done = {(r["model"], r["qid"]) for r in rows}

    workers = int(CFG["generation"].get("max_workers", 12))
    chunk = int(CFG["generation"].get("checkpoint_every", 200))

    for model in models:
        todo = [r for r in df.to_dict("records") if (model, r["qid"]) not in done]
        print(f"\n{model}: {len(todo)} questions x {B['n_samples']} samples")

        def sample(q, _m=model):
            """Only the GENERATION is threaded; entropy() is computed after.

            entropy() calls the sentence-transformer to cluster by meaning, and
            hammering one encoder from many threads is not worth the risk for a
            step that is already fast.
            """
            out = []
            for _ in range(B["n_samples"]):
                # same prompt AND the same retry policy as the ensemble arm --
                # the baseline must differ only in WHERE the four generations
                # come from. Retrying one arm and not the other is a difference
                # in the harness masquerading as a difference in method.
                a, _ = ask_retry(_m, q["question"], temperature=B["temperature"],
                                 dataset=q["dataset"], label=q["qid"])
                out.append(a)
            return q, out

        for start in range(0, len(todo), chunk):
            batch = todo[start:start + chunk]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                got = list(pool.map(sample, batch))
            for q, samples in got:
                rows.append({"qid": q["qid"], "model": model,
                             "semantic_entropy": entropy(samples),
                             "samples": samples})
            print(f"  {min(start + chunk, len(todo))}/{len(todo)}", flush=True)
            pd.DataFrame(rows).to_parquet(dest)

    out = pd.DataFrame(rows)
    out.to_parquet(dest)
    print(f"\n-> {dest}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="only first N questions (slice test)")
    ap.add_argument("--tag", default="", help="ensemble arm, e.g. _gen3")
    ap.add_argument("--ensemble", default="ensemble")
    ap.add_argument("--subset", type=int, default=None,
                    help="stratified sample of N questions (cost control)")
    a = ap.parse_args()
    run(pilot=a.pilot, limit=a.limit, tag=a.tag, ensemble=a.ensemble, subset=a.subset)
