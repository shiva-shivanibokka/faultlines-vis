"""Level 5 — put every question on a 2-D map.

Position comes from the QUESTION WORDING ALONE. It never sees a model answer.
Two reasons that matters, both load-bearing:

  1. non-circularity -- if position were derived from the disagreement score,
     "high-disagreement questions cluster together" would be true by
     construction. Because position comes from wording, any clustering of
     colour is a real result.
  2. Forecast needs it -- a brand new, unanswered question can be embedded and
     placed without running a single model. That is what makes zero-model-call
     risk prediction possible at all.

Colour comes from the Level 4 score, and the toggle to actual correctness is
the headline visual test.

    python -m faultlines.embed --pilot
"""
from __future__ import annotations

import argparse

import pandas as pd

from .config import CFG, SEED, stage
from .semantics import embed as encode


def run(pilot: bool = True, tag: str = "") -> pd.DataFrame:
    import umap

    src = stage("processed", "records", pilot, tag)
    df = pd.read_parquet(src)

    vecs = encode(df["question"].tolist())          # questions only. never answers.
    u = CFG["umap"]
    xy = umap.UMAP(n_neighbors=min(u["n_neighbors"], len(df) - 1),
                   min_dist=u["min_dist"],
                   n_components=u["n_components"],
                   random_state=SEED).fit_transform(vecs)

    df["x"], df["y"] = xy[:, 0], xy[:, 1]
    df.to_parquet(src)
    # the 384-d vectors go to their own file -- they are what pgvector will
    # eventually hold, and they bloat the record table for no reason
    pd.DataFrame(vecs, index=df["qid"]).to_parquet(
        stage("processed", "question_vectors", pilot, tag))
    print(f"-> mapped {len(df)} questions")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--tag", default="")
    _a = ap.parse_args()
    run(pilot=_a.pilot, tag=_a.tag)
