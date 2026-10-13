#!/usr/bin/env python
"""Is confidence the ONLY thing left to read where the vote is blind?

RQ1 established that in the agreement region -- every model gave the same
answer, so disagreement is 0 by construction -- the ensemble's own confidence
still separates right from wrong at AUC 0.600. Real signal, and useless as a
gate: a threshold catching half the errors abstains on a third of correct
answers and is still only 9.8% precise against a 6.6% base rate.

The obvious next question was never asked. Confidence is one feature, and the
record already holds several more, computed months ago and never combined.

Either answer is a result:

  BEATS 0.600 materially -> "the vote is blind here but the RECORD is not, and
      here is what to read instead". That is an argument for keeping the record,
      which is this project's central design claim.
  DOES NOT -> "this region is not merely hard for confidence, it is hard for
      everything we can measure". A stronger negative than the current one.

Reported as a risk-coverage curve rather than a threshold, because selective
prediction is how the question is asked in the literature and because
"you picked a bad threshold" is otherwise a free objection.

    python scripts/rq1_multifeature.py

Writes data/processed/rq1_multifeature.parquet. Runs no model and costs nothing.

TWO TRAPS, both hit on the first run of this script, both left visible here
because the numbers before and after differ by a lot.

1. NEIGHBOURHOOD DENSITY LEAKS ACROSS FOLDS.  `density` is the share of a
   question's nearest map-neighbours that the ensemble got wrong. Computed once
   over the whole corpus -- which is what rq2_localize.py does, correctly, for
   its own purpose -- it carries the labels of questions that land in the test
   fold. Cross-validating on it reports a score no deployment could reach. It
   is recomputed inside each fold here, from training labels only.

2. `nli_margin` IS TRUTHFULQA-ONLY.  The grader runs NLI on TruthfulQA and
   cosine everywhere else, so the column is 99.1% null. The first run listed it
   as a feature set, sklearn quietly dropped it at the imputer, and the row
   looked like a real negative result. It is reported separately now, on the
   subset where it exists, and is not mixed into the main comparison.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path          # noqa: E402

SEED = CFG["seed"]
K_NN = 15
OUT = path("processed", "rq1_multifeature.parquet")


# ----------------------------------------------------------------- features
def build() -> pd.DataFrame:
    """The agreement region, with every feature the record already holds.

    Restricted to n_clusters == 1 on purpose: that is where the disagreement
    vote is 0 for every question, so it is the region this project claims is
    structurally invisible. Anywhere else disagreement dominates and the
    question is uninteresting.
    """
    f = pd.read_parquet(path("processed", "rq1_confidence.parquet"))
    f = f[f["agree"]].set_index("qid")

    rec = pd.read_parquet(path("processed", "records.parquet")).set_index("qid")
    loc = pd.read_parquet(path("processed", "rq2_localize.parquet")).set_index("qid")
    ans = pd.read_parquet(path("interim", "answers.parquet"),
                          columns=["qid", "answer", "nli_margin"])

    g = ans.groupby("qid")["nli_margin"]
    f["nli_margin_mean"] = g.mean()
    f["nli_margin_min"] = g.min()

    # Length, as a proxy for specificity. A one-word answer and a sentence fail
    # differently, and nothing in the project has ever looked.
    alen = ans.assign(l=ans["answer"].astype(str).str.len()).groupby("qid")["l"]
    f["answer_len"] = alen.mean()
    f["question_len"] = rec["question"].astype(str).str.len()

    # x and y come from UMAP over question TEXT only -- no model output, no
    # labels -- so they are safe to use as ordinary features. `density` is not,
    # and is built per fold below instead of read from rq2_localize.
    f["x"], f["y"] = rec["x"], rec["y"]
    f["popularity"] = loc["popularity"]
    f["dataset"] = rec["dataset"]
    f["group"] = (rec["question"].astype(str).str.lower()
                  .str.replace(r"\s+", " ", regex=True).str.strip()
                  .reindex(f.index).factorize()[0])
    return f


CONF = ["mean_conf", "min_conf", "max_conf", "conf_std"]
SHAPE = ["answer_len", "question_len"]
XY = ["x", "y"]
DENS = ["density_oof"]
POP = ["popularity"]

SETS = {
    "confidence mean only": ["mean_conf"],
    "confidence, all four": CONF,
    "+ answer / question length": CONF + SHAPE,
    "+ map position (x, y)": CONF + SHAPE + XY,
    "+ neighbourhood density": CONF + SHAPE + XY + DENS,
    "+ popularity": CONF + SHAPE + XY + DENS + POP,
    "density + position alone": XY + DENS,
}


# ----------------------------------------------------------------- evaluation
def fold_density(xy: np.ndarray, y: np.ndarray, tr: np.ndarray,
                 te: np.ndarray, k: int = K_NN,
                 drop_self: bool = False,
                 groups: np.ndarray | None = None) -> np.ndarray:
    """Neighbourhood error rate for the query rows, from TRAINING labels only.

    This is the whole fix for trap 1. A query question is placed on the map --
    which needs no label -- and asks its k nearest TRAINING neighbours how often
    the ensemble was wrong on them. Nothing about its own outcome, or any test
    question's, reaches the feature.

    `drop_self` is trap 1's second half, and it cost 0.05 AUC before it was
    caught. The training rows need this feature too, and their neighbours come
    from the training set -- which CONTAINS THEM. Without dropping the first
    neighbour, a training row reads its own label and a test row does not, so
    the model learns to trust a feature that means something different at
    prediction time. The symptom was density making the boosted model WORSE
    (0.780 -> 0.728), which is not what a leak normally looks like.
    """
    from sklearn.neighbors import NearestNeighbors
    if groups is None:
        extra = 1 if drop_self else 0
        nn = NearestNeighbors(n_neighbors=min(k + extra, len(tr))).fit(xy[tr])
        _, idx = nn.kneighbors(xy[te])
        return y[tr][idx[:, extra:]].mean(1)
    # ISSUES #73. "Self" is the whole GROUP, not the row: a question text that
    # appears twice sits at the same point on the map, so dropping only the
    # row still hands a training row its twin's label -- the leak drop_self
    # exists to close, one step removed. Over-fetch, then discard every
    # neighbour that shares the query's group (which includes the row itself).
    pad = 8
    nn = NearestNeighbors(n_neighbors=min(k + pad, len(tr))).fit(xy[tr])
    _, idx = nn.kneighbors(xy[te])
    gtr, out = groups[tr], np.empty(len(te))
    for i, (q, row) in enumerate(zip(te, idx)):
        keep = row[gtr[row] != groups[q]][:k]
        out[i] = y[tr][keep].mean() if len(keep) else np.nan
    return out


def risk_coverage(y: np.ndarray, score: np.ndarray) -> pd.DataFrame:
    """Answer the most-confident questions first; error rate vs coverage.

    `score` is predicted RISK, so ascending order is most-confident-first. At
    coverage c the system has answered the c fraction it was surest about and
    abstained on the rest; risk is the error rate among what it answered. A
    useful signal bends this curve down at low coverage; a useless one leaves it
    flat at the base rate, which is what a single confidence threshold does.
    """
    order = np.argsort(score, kind="mergesort")
    errs = y[order].cumsum()
    n = np.arange(1, len(y) + 1)
    return pd.DataFrame({"coverage": n / len(y), "risk": errs / n})


def evaluate(f: pd.DataFrame, cols: list[str], y: np.ndarray,
             kind: str) -> dict:
    """5-fold out-of-fold prediction, with the density feature rebuilt per fold."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedGroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    def fresh():
        if kind == "logistic":
            # Popularity is null for the three datasets with no pageview count,
            # so it is imputed rather than dropped -- dropping would silently
            # restrict every comparison to PopQA.
            return make_pipeline(SimpleImputer(strategy="median"),
                                 StandardScaler(),
                                 LogisticRegression(max_iter=2000))
        return HistGradientBoostingClassifier(     # handles NaN natively
            random_state=SEED, max_iter=300, learning_rate=.06,
            max_leaf_nodes=15, l2_regularization=1.0)

    xy = f[["x", "y"]].to_numpy(dtype=float)
    p = np.zeros(len(y))
    # GROUPED by question text (ISSUES #73). Rows were split one by one, and a
    # question asked twice put one copy in training and one in test: the
    # published 0.811 was partly the model recognising a question whose answer
    # it had been shown. The corpus is now deduplicated, but PopQA still holds
    # same-text questions about different entities, so the grouping stays.
    groups = f["group"].to_numpy()
    cv = StratifiedGroupKFold(5, shuffle=True, random_state=SEED)
    for tr, te in cv.split(xy, y, groups):
        d = f[cols].copy()
        if "density_oof" in cols:
            col = np.full(len(f), np.nan)
            col[te] = fold_density(xy, y, tr, te, groups=groups)
            # training rows need a value too, and theirs must be built the same
            # way a test row's is: from OTHER rows only. See drop_self.
            col[tr] = fold_density(xy, y, tr, tr, drop_self=True, groups=groups)
            d["density_oof"] = col
        X = d.to_numpy(dtype=float)
        m = fresh().fit(X[tr], y[tr])
        p[te] = m.predict_proba(X[te])[:, 1]

    rc = risk_coverage(y, p)
    # A coarse copy of the curve, for the panel that draws it. 40 points is
    # enough to see the shape and small enough to ship inside data.json; the
    # full 17,664-point curve is recoverable from the parquet if anyone needs
    # it. Stored as a column of lists so one row carries one whole curve.
    step = max(1, len(rc) // 40)
    curve = rc.iloc[step - 1::step]
    return {
        "curve_x": [round(v, 4) for v in curve.coverage],
        "curve_y": [round(v, 5) for v in curve.risk],
        "auc": float(roc_auc_score(y, p)),
        "auarc": float(np.trapezoid(rc["risk"], rc["coverage"])),
        "risk_at_25": float(rc.risk.iloc[int(len(rc) * .25) - 1]),
        "risk_at_50": float(rc.risk.iloc[len(rc) // 2 - 1]),
        "risk_at_80": float(rc.risk.iloc[int(len(rc) * .8) - 1]),
        "base": float(y.mean()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="logistic only")
    a = ap.parse_args()

    f = build()
    f["density_oof"] = np.nan                     # placeholder; built per fold
    y = f["majority_wrong"].astype(int).to_numpy()

    print("=" * 72)
    print("RQ1b  IS CONFIDENCE THE ONLY THING LEFT TO READ?")
    print("=" * 72)
    print(f"agreement region: {len(f):,} questions, "
          f"{y.sum():,} wrong ({y.mean():.2%} base rate)")
    print("the disagreement vote is 0 for every one of them, by construction")
    print(f"popularity present for {f.popularity.notna().mean():.1%} of them; "
          f"nli_margin for {f.nli_margin_mean.notna().mean():.1%}\n")

    kinds = ["logistic"] if a.quick else ["logistic", "boosted"]
    rows = []
    for kind in kinds:
        print(f"--- {kind} ---")
        print(f"  {'feature set':<28} {'AUC':>7} {'AUARC':>8} "
              f"{'risk@25%':>9} {'risk@50%':>9} {'risk@80%':>9}")
        for name, cols in SETS.items():
            r = evaluate(f, cols, y, kind)
            rows.append({"model": kind, "features": name,
                         "n_features": len(cols), **r})
            print(f"  {name:<28} {r['auc']:>7.4f} {r['auarc']:>8.4f} "
                  f"{r['risk_at_25']:>9.2%} {r['risk_at_50']:>9.2%} "
                  f"{r['risk_at_80']:>9.2%}")
        print()

    out = pd.DataFrame(rows)
    out.to_parquet(OUT)

    base = float(y.mean())
    lo = out[out.features == "confidence mean only"].auc.max()
    hi = out.loc[out.auc.idxmax()]
    print(f"base rate, answer everything      {base:.2%} risk")
    print(f"confidence alone                  AUC {lo:.4f}")
    print(f"best                              AUC {hi.auc:.4f}"
          f"   [{hi.model}, {hi.features}]")
    print(f"                                  {hi.auc - lo:+.4f}")
    print(f"\nAnswer only the half it is surest about and the error rate there is "
          f"{hi.risk_at_50:.2%}, against {base:.2%} if you answer everything.")
    print(f"Answer the surest quarter and it is {hi.risk_at_25:.2%}.")
    print(f"\n-> {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
