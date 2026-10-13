#!/usr/bin/env python
"""Every ensemble you could have built from the models already run.

Two questions share one piece of machinery, so they share one script.

  1. ENSEMBLE SIZE (PLAN 1.4).  The headline silent-consensus rate is measured
     on four models. A reviewer's first question is what it would have been on
     three, or two. Nobody accepts n=4 without the curve.

  2. THE DECORRELATION FRONTIER (PLAN 1.1).  Eight models have answered the
     identical corpus -- four from 2024, four from 2025. Every subset of them is
     an ensemble that could have been deployed, and it costs nothing to score.
     Plot each one's mean pairwise error correlation against the AUC of its
     disagreement signal and the question becomes: should you pick an ensemble
     for DECORRELATION rather than for average accuracy?

Both need the same thing -- disagreement scored over an arbitrary subset of
models -- and the expensive part is embedding answers, not clustering them. So
every distinct answer string in the corpus is embedded ONCE, and after that a
subset costs a few seconds.

    python scripts/ensemble_ablation.py --arm 2025        # the size ablation
    python scripts/ensemble_ablation.py --frontier        # all 8 models, sizes 2-4

Writes data/processed/ensemble_ablation.parquet. Runs no model and spends
nothing: every answer it scores was generated months ago.

VALIDATION.  The 2025 four-model row must reproduce the headline exactly --
the silent-consensus count and AUC read from records.parquet (950 and 0.840
on the deduplicated corpus; 1,054 and 0.862 before it) -- or the reimplementation of
the clustering is wrong and every other row is fiction. --check does only that.
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path          # noqa: E402
from faultlines.datasets import duplicate_qids          # noqa: E402
from faultlines.evaluate import auc              # noqa: E402
from faultlines.semantics import embed           # noqa: E402

THR = CFG["semantics"]["cluster_threshold"]
OUT = path("processed", "ensemble_ablation.parquet")

ARMS = {
    "2025": ("answers.parquet", "records.parquet"),
    "2024": ("answers_rq3local.parquet", "records_rq3local.parquet"),
}


# ----------------------------------------------------------------- loading
def load(arm: str) -> pd.DataFrame:
    """One row per (qid, model): the answer, whether it was right, and how sure.

    Ungradeable questions are dropped here for the same reason disagree.run
    drops them -- no correctness label exists, so any AUC over them is invented.
    """
    ans, _ = ARMS[arm]
    df = pd.read_parquet(path("interim", ans),
                         columns=["qid", "model", "answer", "confidence",
                                  "correct", "gradeable"])
    if "gradeable" in df.columns:
        df = df[df["gradeable"]]
    df = df[~df["qid"].isin(duplicate_qids())]          # ISSUES #66
    df["model"] = df["model"].map(lambda m: m.split("/")[-1])
    df["arm"] = arm
    return df.drop(columns=["gradeable"], errors="ignore")


def wide(df: pd.DataFrame) -> tuple[pd.Index, dict]:
    """Pivot to one row per qid, one column per model, for each field.

    Returns the qid index and a dict of model -> {answer, correct, confidence}
    aligned to it. Any qid missing a model is dropped: a subset scored over a
    ragged population is not comparable to one scored over a full one.
    """
    piv = {f: df.pivot_table(index="qid", columns="model", values=f,
                             aggfunc="first")
           for f in ("answer", "correct", "confidence")}
    keep = piv["answer"].dropna().index
    for f in piv:
        piv[f] = piv[f].loc[keep]
    return keep, piv


# ----------------------------------------------------------------- clustering
def cluster_ids(vecs: np.ndarray, thr: float = THR) -> np.ndarray:
    """semantics.cluster(), vectorised across questions instead of over models.

    vecs is (n_questions, k, dim), already L2-normalised, so a dot product IS
    cosine similarity. The algorithm is the same greedy single pass the project
    uses everywhere: each answer joins the first cluster whose SEED it is close
    enough to, else starts its own. The loops below are over k (at most four),
    never over n, so this is one numpy pass rather than 34,062 Python ones.

    Returns (n_questions, k) cluster ids in the same first-seen order that
    semantics.cluster() produces, which is what makes the two comparable.
    """
    n, k, _ = vecs.shape
    sim = vecs @ vecs.transpose(0, 2, 1)          # (n, k, k) cosine similarities
    ids = np.zeros((n, k), dtype=np.int8)
    seed = np.zeros((n, k), dtype=np.int8)        # seed[:, c] = index of c's seed
    ncl = np.ones(n, dtype=np.int8)               # answer 0 always opens cluster 0

    for i in range(1, k):
        placed = np.zeros(n, dtype=bool)
        for c in range(k):                        # at most k clusters exist
            live = (c < ncl) & ~placed
            if not live.any():
                continue
            s = sim[np.arange(n), i, seed[:, c]]
            hit = live & (s >= thr)
            ids[hit, i] = c
            placed |= hit
        # everything unplaced opens a new cluster, seeded by itself
        fresh = ~placed
        ids[fresh, i] = ncl[fresh]
        seed[fresh, ncl[fresh]] = i
        ncl[fresh] += 1
    return ids


def score_subset(models: tuple[str, ...], piv: dict,
                 vec_of: dict[str, np.ndarray]) -> dict:
    """Every quantity the project measures, for one candidate ensemble."""
    k = len(models)
    n = len(piv["answer"])
    vecs = np.stack([vec_of[m] for m in models], axis=1)        # (n, k, dim)
    correct = np.stack([piv["correct"][m].to_numpy().astype(bool)
                        for m in models], axis=1)               # (n, k)
    conf = np.nan_to_num(np.stack([piv["confidence"][m].to_numpy(dtype=float)
                                   for m in models], axis=1))

    ids = cluster_ids(vecs)
    weight = np.zeros((n, k))
    count = np.zeros((n, k), dtype=np.int8)
    for c in range(k):
        m = ids == c
        weight[:, c] = (conf * m).sum(1)
        count[:, c] = m.sum(1)

    total = weight.sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        dis = 1 - weight.max(1) / total
    dis = np.where(total > 0, dis, np.nan)
    dis_unw = 1 - count.max(1) / k
    n_clusters = (count > 0).sum(1)

    # The ensemble's actual answer is its largest meaning cluster, with the
    # tie rule of disagree.ensemble_answer_correct (ISSUES #67): size, then
    # summed confidence, then the single most confident member. Lexicographic
    # key; counts <= 4 and confidences <= 1, so the scales cannot collide.
    top = np.zeros((n, k))
    for c in range(k):
        top[:, c] = np.where(ids == c, conf, -1).max(1)
    key = count * 1e6 + weight * 1e2 + top
    key = np.where(count > 0, key, -np.inf)
    maj = key.argmax(1)
    in_maj = ids == maj[:, None]
    right = (correct & in_maj).sum(1)
    size = in_maj.sum(1)
    # a within-cluster tie goes to the most confident member of the cluster
    lead = np.where(in_maj, conf, -1).argmax(1)
    lead_right = correct[np.arange(n), lead]
    majority_wrong = np.where(2 * right != size, 2 * right < size, ~lead_right)

    all_wrong = ~correct.any(1)
    silent = (n_clusters == 1) & all_wrong

    wrong = ~correct
    rates = wrong.mean(0)
    phis = [float(np.corrcoef(wrong[:, i], wrong[:, j])[0, 1])
            for i, j in itertools.combinations(range(k), 2)]
    predicted = float(np.prod(rates))
    observed = float(all_wrong.mean())

    ok = ~np.isnan(dis)
    return {
        "models": " + ".join(models), "k": k, "n": int(n),
        "silent": int(silent.sum()),
        "silent_rate": float(silent.mean()),
        "majority_wrong_rate": float(majority_wrong.mean()),
        "shared_share": float(silent.sum() / max(majority_wrong.sum(), 1)),
        "auc": float(auc(majority_wrong[ok].astype(int), dis[ok])),
        "auc_unweighted": float(auc(majority_wrong.astype(int), dis_unw)),
        "phi_mean": float(np.mean(phis)),
        "phi_max": float(np.max(phis)),
        "err_mean": float(rates.mean()),
        "err_best": float(rates.min()),
        "all_wrong": observed,
        "all_wrong_if_independent": predicted,
        "ratio": observed / predicted if predicted else float("nan"),
    }


# ----------------------------------------------------------------- driver
def vectors(df: pd.DataFrame, piv: dict, qids: pd.Index) -> dict[str, np.ndarray]:
    """Embed every DISTINCT answer once, then hand each model its own array.

    The corpus has 170,364 answers and far fewer distinct strings -- short
    factual answers repeat heavily across models and questions -- so deduping
    before the encoder is most of the saving.
    """
    uniq = pd.unique(df["answer"].astype(str))
    print(f"   embedding {len(uniq):,} distinct answers "
          f"(of {len(df):,} total) ...", flush=True)
    vecs = embed(list(uniq))
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    where = {a: i for i, a in enumerate(uniq)}
    return {m: vecs[[where[str(a)] for a in piv["answer"][m].to_numpy()]]
            for m in piv["answer"].columns}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["2025", "2024"], default="2025")
    ap.add_argument("--frontier", action="store_true",
                    help="all 8 models across both arms, every subset of size 2-4")
    ap.add_argument("--check", action="store_true",
                    help="only verify the 4-model row reproduces the headline")
    a = ap.parse_args()

    arms = ["2025", "2024"] if a.frontier else [a.arm]
    df = pd.concat([load(x) for x in arms], ignore_index=True)
    qids, piv = wide(df)
    models = sorted(piv["answer"].columns)
    print(f"{len(qids):,} questions x {len(models)} models "
          f"({', '.join(arms)} arm{'s' if len(arms) > 1 else ''})")
    vec_of = vectors(df, piv, qids)

    if a.check:
        row = score_subset(tuple(sorted(piv["answer"].columns)), piv, vec_of)
        # Three independent checks, because one could pass by luck. The silent
        # count exercises the clustering; the two AUCs exercise the confidence
        # weighting and the majority_wrong tie-break separately. RESULTS.md
        # claim 1 is the HEAD-COUNT score (0.840) and records the weighted one
        # as 0.844, so both numbers already exist to be checked against.
        # Expected values are READ from records.parquet, not typed: they were
        # 1054 / 0.862 / 0.865 until the corpus was deduplicated (ISSUES #66)
        # and a typed expectation would have failed a correct run.
        rec = pd.read_parquet(path("processed", ARMS[a.arm][1]))
        want_unw = float(auc(rec.majority_wrong.astype(int),
                             rec.disagreement_unweighted))
        want_w = float(auc(rec.majority_wrong.astype(int), rec.disagreement))
        checks = [
            ("silent-consensus count", row["silent"],
             int(rec.silent_consensus.sum()), 0),
            ("AUC, head-count", row["auc_unweighted"], want_unw, 0.0015),
            ("AUC, confidence-weighted", row["auc"], want_w, 0.0015),
        ]
        print()
        ok = True
        for name, got, want, tol in checks:
            hit = abs(got - want) <= tol
            ok &= hit
            shown = f"{got:.4f}" if isinstance(got, float) else str(got)
            print(f"  {'ok ' if hit else 'BAD'}  {name:<26} {shown:>8}"
                  f"   expected {want}")
        print("\n  " + ("MATCH -- the reimplementation is faithful"
                        if ok else "MISMATCH -- do not trust any other row"))
        return 0 if ok else 1

    sizes = range(2, 5) if a.frontier else range(2, len(models) + 1)
    subsets = [s for k in sizes for s in itertools.combinations(models, k)]
    print(f"   scoring {len(subsets)} ensembles ...", flush=True)

    rows = []
    for i, s in enumerate(subsets, 1):
        rows.append(score_subset(s, piv, vec_of))
        if i % 25 == 0 or i == len(subsets):
            print(f"     {i}/{len(subsets)}", flush=True)
    out = pd.DataFrame(rows).sort_values(["k", "silent_rate"])
    out.to_parquet(OUT)

    print(f"\n-> {OUT.name}   {len(out)} ensembles\n")
    print("SIZE ABLATION -- silent-consensus rate by ensemble size")
    for k, g in out.groupby("k"):
        print(f"  k={k}  n={len(g):3d}   mean {g.silent_rate.mean():.3%}"
              f"   range {g.silent_rate.min():.3%} - {g.silent_rate.max():.3%}"
              f"   mean AUC {g.auc.mean():.3f}")

    if a.frontier:
        print("\nDECORRELATION FRONTIER -- does lower correlation beat lower error?")
        for k, g in out.groupby("k"):
            r_phi = g[["phi_mean", "auc"]].corr().iloc[0, 1]
            r_err = g[["err_mean", "auc"]].corr().iloc[0, 1]
            print(f"  k={k}   corr(phi, AUC) = {r_phi:+.3f}"
                  f"    corr(mean error, AUC) = {r_err:+.3f}")
        print("\n  best AUC at each size:")
        for k, g in out.groupby("k"):
            b = g.loc[g.auc.idxmax()]
            print(f"   k={k}  {b.auc:.3f}  phi {b.phi_mean:.3f}"
                  f"  err {b.err_mean:.1%}   {b.models}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
