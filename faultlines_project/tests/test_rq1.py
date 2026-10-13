"""RQ1 — confidence as a second feature, especially in the agreement region.

    python tests/test_rq1.py

Pins the feature-building and the agreement-region AUC logic on small synthetic
frames, so the real-data numbers printed by `python -m faultlines.rq1_confidence`
rest on tested plumbing.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from faultlines.rq1_confidence import features, agreement_region_auc


def _toy():
    # 2 questions, 4 models each. q1 unanimous+wrong (silent consensus),
    # q2 split. Confidences chosen so q1 mean=0.6, q2 mean=0.8.
    answers = pd.DataFrame([
        dict(qid="q1", model=m, confidence=c, correct=False)
        for m, c in zip("abcd", [0.5, 0.6, 0.7, 0.6])
    ] + [
        dict(qid="q2", model=m, confidence=c, correct=(m == "a"))
        for m, c in zip("abcd", [0.9, 0.8, 0.7, 0.8])
    ])
    records = pd.DataFrame([
        dict(qid="q1", n_clusters=1, disagreement=0.0, majority_wrong=True, silent_consensus=True),
        dict(qid="q2", n_clusters=3, disagreement=0.7, majority_wrong=False, silent_consensus=False),
    ])
    return answers, records


def test_features_one_row_per_record():
    answers, records = _toy()
    feat = features(answers, records)
    assert len(feat) == 2, feat
    assert set(feat["qid"]) == {"q1", "q2"}


def test_features_aggregate_confidence():
    answers, records = _toy()
    feat = features(answers, records).set_index("qid")
    assert abs(feat.loc["q1", "mean_conf"] - 0.6) < 1e-9, feat.loc["q1", "mean_conf"]
    assert abs(feat.loc["q1", "min_conf"] - 0.5) < 1e-9
    assert feat.loc["q1", "agree"] == True  # noqa: E712 — n_clusters==1
    assert feat.loc["q2", "agree"] == False  # noqa: E712


def test_agreement_region_auc_is_a_probability():
    # 6 unanimous questions, confidence anti-correlated with error -> AUC > 0.5
    feat = pd.DataFrame(dict(
        agree=[True] * 6,
        mean_conf=[0.9, 0.8, 0.7, 0.4, 0.3, 0.2],
        min_conf=[0.9, 0.8, 0.7, 0.4, 0.3, 0.2],
        majority_wrong=[False, False, False, True, True, True],
    ))
    out = agreement_region_auc(feat)
    assert 0.0 <= out["auc_mean_conf"] <= 1.0, out
    assert out["auc_mean_conf"] > 0.5, out  # low conf predicts error
    assert out["n_agree"] == 6


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
