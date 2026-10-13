"""The one sentence transformer, shared by grading, clustering and the baseline.

Deliberately a single module: Level 3, Level 4 and Level 6 must use the SAME
encoder and the SAME threshold, or the baseline comparison smuggles in an
advantage and Level 6 proves nothing.
"""
from __future__ import annotations

import functools

import numpy as np

from .config import CFG


@functools.lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(CFG["semantics"]["model"])


def embed(texts: list[str]) -> np.ndarray:
    """L2-normalised, so cosine similarity is just a dot product."""
    return encoder().encode(list(texts), normalize_embeddings=True,
                            show_progress_bar=False)


def cluster_many(groups: list[list[str]], threshold: float | None = None) -> list[list[int]]:
    """cluster() over many groups, with ONE encoder call for all of them.

    Identical algorithm and identical output to calling cluster() per group --
    the greedy pass below is the same loop, it just reads pre-computed vectors.
    Measured: cluster() costs ~96 ms per question, so the per-question path is
    ~68 minutes on the 42,591-question corpus, almost all of it encoder
    start-up rather than actual work.
    """
    thr = CFG["semantics"]["cluster_threshold"] if threshold is None else threshold
    flat, spans = [], []
    for g in groups:
        spans.append((len(flat), len(g)))
        flat.extend(g)
    if not flat:
        return [[] for _ in groups]
    allvecs = embed(flat)

    out: list[list[int]] = []
    for start, n in spans:
        vecs = allvecs[start:start + n]
        seeds: list[int] = []
        ids: list[int] = []
        for i, v in enumerate(vecs):
            for c, s in enumerate(seeds):
                if float(v @ vecs[s]) >= thr:
                    ids.append(c)
                    break
            else:
                ids.append(len(seeds))
                seeds.append(i)
        out.append(ids)
    return out


def cluster(texts: list[str], threshold: float | None = None) -> list[int]:
    """Group answers that mean the same thing. Returns a cluster id per text.

    Greedy single-pass: each text joins the first cluster whose seed it is
    close enough to, else starts its own. With 4 answers the difference
    between this and proper agglomerative clustering is nil.
    ponytail: greedy is fine at n=4; revisit if the baseline ever samples 20+.
    """
    thr = CFG["semantics"]["cluster_threshold"] if threshold is None else threshold
    vecs = embed(texts)
    seeds: list[int] = []          # index of each cluster's first member
    ids: list[int] = []
    for i, v in enumerate(vecs):
        for c, s in enumerate(seeds):
            if float(v @ vecs[s]) >= thr:
                ids.append(c)
                break
        else:
            ids.append(len(seeds))
            seeds.append(i)
    return ids


def similar(a: str, b: str, threshold: float | None = None) -> bool:
    thr = CFG["semantics"]["grade_threshold"] if threshold is None else threshold
    v = embed([a, b])
    return float(v[0] @ v[1]) >= thr
