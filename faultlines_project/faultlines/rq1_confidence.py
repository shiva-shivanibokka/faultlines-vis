"""RQ1 - Measure silent consensus, and detect it with confidence.

The disagreement vote is 0.5 by construction in the agreement region (all four
models gave one answer, so there is nothing to count). This module asks whether
ensemble *confidence* still separates right from wrong there - a white-box signal
a black-box method cannot access - and whether confidence + disagreement as two
features beat disagreement alone.

    python -m faultlines.rq1_confidence [--pilot]

Runs on the committed pilot parquets; prints real numbers, writes the feature
table to data/processed/rq1_confidence_pilot.parquet.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from faultlines import evaluate
from faultlines.config import SEED, stage


def features(answers: pd.DataFrame, records: pd.DataFrame) -> pd.DataFrame:
    """One row per record qid with the four-model confidence aggregates joined
    onto the per-question disagreement fields."""
    g = (answers.groupby("qid")["confidence"]
         .agg(mean_conf="mean", min_conf="min", max_conf="max", conf_std="std")
         .reset_index())
    keep = ["qid", "dataset", "n_clusters", "disagreement",
            "disagreement_unweighted", "majority_wrong", "silent_consensus"]
    have = [c for c in keep if c in records.columns]
    feat = records[have].merge(g, on="qid", how="inner")
    feat["conf_std"] = feat["conf_std"].fillna(0.0)
    feat["agree"] = feat["n_clusters"] == 1
    return feat


def agreement_region_auc(feat: pd.DataFrame) -> dict:
    """AUC of (low) confidence -> majority_wrong, restricted to the agreement
    region where vote-counting is 0.5 by construction. Lower confidence should
    mean more error, so we score the NEGATED confidence."""
    reg = feat[feat["agree"] == True]  # noqa: E712
    y = reg["majority_wrong"].astype(int).to_numpy()
    out = {"n_agree": int(len(reg))}
    for col in ("mean_conf", "min_conf"):
        out[f"auc_{col}"] = evaluate.auc(y, -reg[col].to_numpy())
    return out


def logit_model(feat: pd.DataFrame) -> dict:
    """5-fold CV logistic regression: does (disagreement + confidence) beat
    disagreement alone at predicting majority_wrong?"""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    # HEAD-COUNT, not the confidence-weighted score. This module's whole question
    # is "what does adding confidence buy?", and the answer is the GAP between
    # the one-feature and four-feature detectors. Until 2026-08-03 the one-feature
    # baseline was `disagreement`, which is BUILT OUT OF the confidences -- so the
    # gap measured "extra confidence on top of confidence", not "confidence vs
    # none", and it understated the finding: +0.018 against a contaminated
    # baseline, +0.024 against a clean one. A baseline cannot contain the thing
    # whose contribution it exists to isolate. See DECISIONS 2026-08-03.
    d = feat.dropna(subset=["disagreement_unweighted", "mean_conf",
                            "min_conf", "n_clusters"]).copy()
    y = d["majority_wrong"].astype(int).to_numpy()
    if len(np.unique(y)) < 2:
        return {"note": "single class, cannot fit"}

    def cv_auc(cols):
        X = d[cols].to_numpy(dtype=float)
        pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        # SHUFFLED folds (ISSUES #72). `cv=5` is StratifiedKFold WITHOUT
        # shuffling, and rows arrive in dataset blocks, so each fold was
        # mostly one dataset and every pooled out-of-fold AUC read low.
        proba = cross_val_predict(pipe, X, y, method="predict_proba",
                                  cv=StratifiedKFold(5, shuffle=True,
                                                     random_state=SEED))[:, 1]
        return evaluate.auc(y, proba)

    combo_cols = ["disagreement_unweighted", "mean_conf", "min_conf", "n_clusters"]
    # a coefficient read on the full fit, for the write-up
    from sklearn.preprocessing import StandardScaler as _S
    Xs = _S().fit_transform(d[combo_cols].to_numpy(dtype=float))
    coef = LogisticRegression(max_iter=1000).fit(Xs, y).coef_[0]
    return {
        "auc_disagreement_alone": cv_auc(["disagreement_unweighted"]),
        "auc_conf_alone": cv_auc(["mean_conf", "min_conf"]),
        "auc_combined": cv_auc(combo_cols),
        "coef": dict(zip(combo_cols, [round(float(c), 3) for c in coef])),
        "n": int(len(d)),
    }


def run(pilot: bool = True, tag: str = "") -> pd.DataFrame:
    answers = pd.read_parquet(stage("interim", "answers", pilot, tag))
    records = pd.read_parquet(stage("processed", "records", pilot, tag))
    feat = features(answers, records)

    print("=" * 64)
    print("RQ1  DOES CONFIDENCE SEE WHAT THE VOTE CANNOT?")
    print("=" * 64)
    reg = agreement_region_auc(feat)
    print(f"agreement region: {reg['n_agree']} unanimous questions "
          f"({(feat['agree']).mean():.0%} of all)")
    print(f"  AUC  low mean_conf -> error : {reg['auc_mean_conf']:.3f}   "
          f"(vote-counting is 0.5 here by construction)")
    print(f"  AUC  low min_conf  -> error : {reg['auc_min_conf']:.3f}")

    print("\nby agreement level (mean ensemble confidence, correct vs wrong):")
    for nc in sorted(feat["n_clusters"].unique()):
        s = feat[feat["n_clusters"] == nc]
        r = s[~s["majority_wrong"]]; w = s[s["majority_wrong"]]
        print(f"  clusters={nc}  n={len(s):3d}  "
              f"conf_correct={r['mean_conf'].mean():.3f}(n={len(r)})  "
              f"conf_wrong={w['mean_conf'].mean():.3f}(n={len(w)})")

    print("\ntwo features vs one (5-fold CV AUC on majority_wrong):")
    m = logit_model(feat)
    if "note" in m:
        print("  " + m["note"])
    else:
        print(f"  disagreement alone      : {m['auc_disagreement_alone']:.3f}")
        print(f"  confidence alone        : {m['auc_conf_alone']:.3f}")
        print(f"  combined (logistic)     : {m['auc_combined']:.3f}   n={m['n']}")
        print(f"  coefficients (z-scored) : {m['coef']}")

    out = stage("processed", "rq1_confidence", pilot, tag)
    feat.to_parquet(out)
    print(f"\nwrote {out.name}  ({len(feat)} rows)")
    return feat


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", default=True)
    ap.add_argument("--full", dest="pilot", action="store_false")
    ap.add_argument("--tag", default="")
    _a = ap.parse_args()
    run(_a.pilot, _a.tag)
