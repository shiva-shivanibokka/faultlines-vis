"""RQ2 - Localize the blind spots, and prove they carry signal beyond popularity.

If shared errors just tracked entity obscurity, this reduces to a known 2023
result (Kandpal; Mallen). The test: does error cluster on the map, and does that
clustering survive a control for entity popularity?

    python -m faultlines.rq2_localize [--pilot]

Runs on the committed pilot parquets; prints correlations and a nested logistic
comparison, writes data/processed/rq2_localize_pilot.parquet.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from faultlines import evaluate
from faultlines.config import SEED, stage


def popularity(records: pd.DataFrame) -> pd.Series:
    """log10(s_pop + 1) for PopQA rows; NaN for datasets without popularity."""
    def one(row):
        m = row["meta"]
        if row["dataset"] != "popqa" or not isinstance(m, dict) or m.get("s_pop") is None:
            return np.nan
        return float(np.log10(float(m["s_pop"]) + 1.0))
    return records.apply(one, axis=1)


def _neighbours(records: pd.DataFrame, k: int = 15) -> np.ndarray:
    """Indices of each row's k nearest map-neighbours, self excluded.

    Positional, not label-based: the caller indexes its own arrays with these.
    """
    from sklearn.neighbors import NearestNeighbors

    xy = records[["x", "y"]].to_numpy(dtype=float)
    k = min(k, len(records) - 1)
    nn = NearestNeighbors(n_neighbors=k + 1).fit(xy)   # +1: first neighbour is self
    _, idx = nn.kneighbors(xy)
    return idx[:, 1:]                                   # drop self


def neighbourhood_density(records: pd.DataFrame, k: int = 15) -> pd.Series:
    """For each question, the fraction of its k nearest map-neighbours (in x,y)
    that are majority_wrong. High density = a fault region, not a lone error.

    IMPORTANT: neighbours come from whatever frame is passed in. Called on the
    whole corpus this is the SHARED-MAP density -- what the tool draws, and what
    a user sees when they brush a region -- and a PopQA question's neighbours may
    then be TruthfulQA questions. Called on one dataset's rows it is the
    WITHIN-DATASET density. They are different quantities and the popularity
    control needs the second one; see popularity_control() and AUDIT note n1.
    """
    wrong = records["majority_wrong"].astype(int).to_numpy()
    idx = _neighbours(records, k)
    return pd.Series(np.array([wrong[row].mean() for row in idx]),
                     index=records.index)


def neighbour_mix(records: pd.DataFrame, dataset: str, k: int = 15) -> float:
    """Share of a dataset's map-neighbours that come from a DIFFERENT dataset.

    This is the number that says how much AUDIT n1 actually mattered. If it is
    near zero the datasets occupy separate regions of the map and mixing them
    changes nothing; if it is large the shared-map density was partly measuring
    other benchmarks.
    """
    ds = records["dataset"].to_numpy()
    idx = _neighbours(records, k)
    mask = ds == dataset
    if not mask.any():
        return float("nan")
    return float((ds[idx[mask]] != dataset).mean())


def popularity_control(records: pd.DataFrame) -> dict:
    """On PopQA: is the fault-region signal (density) still predictive after
    popularity is accounted for? Nested logistic AUC, 5-fold CV.

    Two densities are reported, and reporting both is the point.

    `density_map` is computed over the WHOLE corpus and then subset to PopQA,
    which is what this function did exclusively until 2026-08-25. It is the
    honest description of what the tool shows -- one shared UMAP, brushed by a
    user who is not filtering by dataset -- but as a CONTROL it is leaky: a
    PopQA question's neighbours can be TruthfulQA questions, so some of the
    signal attributed to "this PopQA neighbourhood is error-prone" is really
    "the adjacent benchmark is error-prone". AUDIT note n1.

    `density_popqa` recomputes neighbours over PopQA rows only. That is the
    control the claim needs: RQ2 exists to show the clustering is not just
    entity obscurity (Kandpal 2023; Mallen 2023), and a leaky feature would let
    a reviewer say the lift came from the leak.

    If the lift survives under `density_popqa`, the finding is stronger than it
    was and the mixed version stops being a liability. If it does not, that is
    the more important result and it must be reported as such.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    d = records.copy()
    d["popularity"] = popularity(d)
    d["density_map"] = neighbourhood_density(d)          # shared map, leaky
    pop = d[d["dataset"] == "popqa"].dropna(subset=["popularity"]).copy()
    y = pop["majority_wrong"].astype(int).to_numpy()
    out = {"n_popqa": int(len(pop))}
    if len(np.unique(y)) < 2 or len(pop) < 10:
        out["note"] = "too few PopQA rows / single class"
        return out
    # Recomputed on the subset, so every neighbour is a PopQA question.
    pop["density_popqa"] = neighbourhood_density(pop)
    out["neighbour_mix"] = neighbour_mix(d, "popqa")

    def cv_auc(cols):
        X = pop[cols].to_numpy(dtype=float)
        pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        # SHUFFLED folds (ISSUES #72). `cv=5` is StratifiedKFold WITHOUT
        # shuffling, and rows arrive in dataset blocks, so each fold was
        # mostly one dataset and every pooled out-of-fold AUC read low.
        proba = cross_val_predict(pipe, X, y, method="predict_proba",
                                  cv=StratifiedKFold(5, shuffle=True,
                                                     random_state=SEED))[:, 1]
        return evaluate.auc(y, proba)

    err = pop["majority_wrong"].astype(float)
    out["corr_pop_err"] = float(pop["popularity"].corr(err))
    out["corr_density_err"] = float(pop["density_map"].corr(err))
    out["corr_density_within_err"] = float(pop["density_popqa"].corr(err))
    out["corr_density_map_within"] = float(pop["density_map"].corr(pop["density_popqa"]))
    out["auc_popularity_only"] = cv_auc(["popularity"])
    out["auc_pop_plus_density"] = cv_auc(["popularity", "density_map"])
    out["auc_pop_plus_density_within"] = cv_auc(["popularity", "density_popqa"])
    out["auc_density_within_only"] = cv_auc(["density_popqa"])
    return out


def run(pilot: bool = True, tag: str = "") -> pd.DataFrame:
    records = pd.read_parquet(stage("processed", "records", pilot, tag))

    print("=" * 64)
    print("RQ2  DO BLIND SPOTS CLUSTER - BEYOND POPULARITY?")
    print("=" * 64)
    dens = neighbourhood_density(records)
    # is error clustered at all? density should separate wrong from right.
    y = records["majority_wrong"].astype(int).to_numpy()
    print(f"map-neighbourhood density AUC -> error : "
          f"{evaluate.auc(y, dens.to_numpy()):.3f}   (0.5 = errors are scattered)")

    ctrl = popularity_control(records)
    print(f"\npopularity control (PopQA, n={ctrl['n_popqa']}):")
    if "note" in ctrl:
        print("  " + ctrl["note"])
    else:
        print(f"  {ctrl['neighbour_mix']:.1%} of a PopQA question's {15} map-neighbours "
              f"are from another dataset")
        print(f"  the two densities correlate at r = {ctrl['corr_density_map_within']:+.3f}")
        print(f"  corr  popularity      ~ error : {ctrl['corr_pop_err']:+.3f}")
        print(f"  corr  density (map)   ~ error : {ctrl['corr_density_err']:+.3f}")
        print(f"  corr  density (popqa) ~ error : {ctrl['corr_density_within_err']:+.3f}")
        print()
        print(f"  AUC  popularity only                 : {ctrl['auc_popularity_only']:.3f}")
        print(f"  AUC  popularity + density (map)      : {ctrl['auc_pop_plus_density']:.3f}"
              f"   lift {ctrl['auc_pop_plus_density'] - ctrl['auc_popularity_only']:+.3f}")
        print(f"  AUC  popularity + density (popqa)    : "
              f"{ctrl['auc_pop_plus_density_within']:.3f}"
              f"   lift {ctrl['auc_pop_plus_density_within'] - ctrl['auc_popularity_only']:+.3f}"
              f"   <- THE CONTROL")
        print(f"  AUC  density (popqa) alone           : "
              f"{ctrl['auc_density_within_only']:.3f}")

    out_df = records[["qid", "dataset", "x", "y", "majority_wrong", "silent_consensus"]].copy()
    out_df["popularity"] = popularity(records).to_numpy()
    # `density` keeps its name: it is the shared-map value the tool draws, and
    # renaming it would break every consumer for no gain. The within-dataset
    # value is the control and lives beside it, NaN outside PopQA.
    out_df["density"] = dens.to_numpy()
    within = pd.Series(np.nan, index=records.index)
    for ds in records["dataset"].unique():
        rows = records[records["dataset"] == ds]
        if len(rows) > 16:
            within.loc[rows.index] = neighbourhood_density(rows)
    out_df["density_within_dataset"] = within.to_numpy()
    out = stage("processed", "rq2_localize", pilot, tag)
    out_df.to_parquet(out)
    print(f"\nwrote {out.name}  ({len(out_df)} rows)")
    return out_df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", default=True)
    ap.add_argument("--full", dest="pilot", action="store_false")
    ap.add_argument("--tag", default="")
    _a = ap.parse_args()
    run(_a.pilot, _a.tag)
