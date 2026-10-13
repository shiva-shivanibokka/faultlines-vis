"""The two numbers the pilot exists to produce.

  pairwise_error_correlation -- do the four models fail on the SAME questions?
      This sits upstream of everything. If they fail together, the whole
      method has no foundation. Phi coefficient over the boolean wrong/right
      vectors, which is just Pearson on 0/1 -- the right measure for two
      binary variables.

  auc -- does the disagreement score separate wrong answers from right ones?
      Compared against the best single-model Semantic Entropy on the same
      questions with the same generation budget.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def pairwise_error_correlation(answers: pd.DataFrame) -> pd.DataFrame:
    """Square matrix of phi correlations between models' error patterns.

    Reading it:
      ~0.3-0.5  healthy diversity, proceed
      0.8+      the models are too alike -- swap one for a different TRAINING
                RECIPE (a synthetic-data-trained model decorrelates far more
                than another web-trained one), not for a bigger model
    """
    wrong = (answers.assign(wrong=~answers["correct"])
             .pivot(index="qid", columns="model", values="wrong").astype(float))
    return wrong.corr()


def auc(y_wrong: np.ndarray, score: np.ndarray) -> float:
    """ROC-AUC for 'this score predicts the answer was wrong'.

    Returns nan rather than raising when a class is missing -- on a 100-question
    slice it is entirely possible that nothing was wrong.
    """
    mask = ~np.isnan(score)
    y, s = np.asarray(y_wrong)[mask], np.asarray(score)[mask]
    if len(set(y.tolist())) < 2:
        return float("nan")
    return roc_auc_score(y, s)


def read_auc(v: float) -> str:
    if np.isnan(v):
        return "n/a - only one class present"
    if v >= 0.95:
        return "suspect a leak in the grading"
    if v >= 0.80:
        return "strong"
    if v >= 0.70:
        return "respectable for hallucination detection"
    if v >= 0.60:
        return "weak but real"
    return "coin flip - useless"


TARGET = "majority_wrong"
"""The label to score against.

NOT any_wrong. With a single gold answer, N models giving N different answers
means at most one can match, so any_wrong is true by arithmetic whenever the
models split -- the score implies the label instead of predicting it. Pilot
evidence: n_clusters=3 -> any_wrong 100%, n_clusters=2 -> 92.7%, producing a
meaningless 0.911 AUC. Against majority_wrong the same data gives 0.800, which
is a real number and sits right where the literature does (Farquhar 0.790).
"""


def compare(records: pd.DataFrame, baseline: pd.DataFrame | None) -> pd.DataFrame:
    """Cross-model disagreement vs each single model's Semantic Entropy."""
    y = records[TARGET].values
    rows = [{"arm": "FaultLines (4 models x 1)", "model": "ensemble",
             "auc": auc(y, records["disagreement"].values)},
            {"arm": "FaultLines unweighted", "model": "ensemble",
             "auc": auc(y, records["disagreement_unweighted"].values)}]

    if baseline is not None and len(baseline):
        for model, g in baseline.groupby("model"):
            m = records.merge(g, on="qid", how="inner")
            rows.append({"arm": "Semantic Entropy (1 model x 4)", "model": model,
                         "auc": auc(m[TARGET].values,
                                    m["semantic_entropy"].values)})

    out = pd.DataFrame(rows)
    out["reading"] = out["auc"].map(read_auc)
    return out.sort_values("auc", ascending=False, na_position="last")
