"""The scoring logic, pinned to the worked example in the proposal.

    python tests/test_disagree.py

Run this after any change to disagree.py or the clustering threshold. If the
0.25 -> 0.09 example stops holding, the number in your proposal and the number
in your code have diverged, and you will find out here rather than in the viva.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from faultlines.disagree import score
from faultlines.grade import grade_one, normalise
from faultlines.baseline import entropy


def test_worked_example():
    """Three confident models vs one hesitant dissenter."""
    s = score(["Canberra", "Canberra", "Canberra", "Sydney"], [.99, .98, .97, .30])
    assert s["n_clusters"] == 2, s
    assert abs(s["disagreement_unweighted"] - 0.25) < 1e-9
    assert abs(s["disagreement"] - 0.0926) < 0.001, s["disagreement"]


def test_weighting_is_not_cosmetic():
    """Same 3-1 split, but the dissenter is confident -> a much higher score.

    This is the reason for weighting at all. If these two came out the same,
    the confidence term would be doing nothing.
    """
    timid = score(["Canberra"] * 3 + ["Sydney"], [.99, .98, .97, .30])
    bold = score(["Canberra"] * 3 + ["Sydney"], [.51, .52, .53, .99])
    assert bold["disagreement"] > timid["disagreement"] * 3
    assert timid["disagreement_unweighted"] == bold["disagreement_unweighted"]


def test_unanimous_scores_zero():
    s = score(["Paris"] * 4, [.9, .9, .9, .9])
    assert s["disagreement"] == 0.0 and s["n_clusters"] == 1


def test_paraphrase_is_agreement_not_disagreement():
    """The whole point of clustering by meaning instead of by string."""
    s = score(["Canberra", "Canberra, Australia", "It is Canberra", "Canberra"],
              [.9] * 4)
    assert s["n_clusters"] == 1, f"paraphrases split into {s['n_clusters']} clusters"


def test_nan_confidence_survives():
    """A failed generation must not crash the score or vanish silently."""
    s = score(["Canberra", "Canberra", "Canberra", ""], [.9, .9, .9, float("nan")])
    assert 0 <= s["disagreement"] <= 1


def test_grading_tiers():
    assert normalise("The Canberra.") == "canberra"
    assert grade_one("Canberra", "Canberra", []) == (True, "exact")
    assert grade_one("the canberra.", "Canberra", []) == (True, "exact")
    assert grade_one("ACT", "Canberra", ["ACT"])[1] == "alias"
    assert grade_one("Sydney", "Canberra", [])[0] is False
    assert grade_one("", "Canberra", []) == (False, "empty")


def test_entropy_measures_meaning_not_wording():
    """Four phrasings of one answer = one cluster = zero entropy."""
    assert entropy(["Canberra", "Canberra, Australia", "It is Canberra", "Canberra"]) == 0.0
    assert entropy(["Canberra", "Sydney", "Melbourne", "Perth"]) > 1.0


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
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)


# ---- the ensemble's answer when there is no largest cluster (ISSUES #67) ----
from faultlines.disagree import ensemble_answer_correct


def test_four_way_split_does_not_depend_on_order():
    """Four different answers: the most confident one is the ensemble's, wherever
    it sits in the list. The old rule took whichever answer came first."""
    ids, conf = [0, 1, 2, 3], [0.40, 0.90, 0.30, 0.50]
    correct = [False, True, False, False]
    assert ensemble_answer_correct(ids, conf, correct) is True
    # same answers, stored in a different order -> same verdict
    order = [3, 2, 1, 0]
    assert ensemble_answer_correct([ids[i] for i in order], [conf[i] for i in order],
                                   [correct[i] for i in order]) is True


def test_two_two_split_goes_to_larger_summed_confidence():
    ids = [0, 0, 1, 1]
    conf = [0.50, 0.50, 0.90, 0.80]          # cluster 1 sums higher
    assert ensemble_answer_correct(ids, conf, [True, True, False, False]) is False
    assert ensemble_answer_correct(ids, conf, [False, False, True, True]) is True


def test_largest_cluster_wins_regardless_of_confidence():
    ids = [0, 0, 0, 1]
    conf = [0.20, 0.20, 0.20, 0.99]
    assert ensemble_answer_correct(ids, conf, [True, True, True, False]) is True


def test_within_cluster_tie_goes_to_most_confident_member():
    """Merged answers graded differently, one each way: the old rule called this
    wrong unconditionally (pandas .mode() on a 1-1 tie returns False)."""
    ids = [0, 0, 1, 2]
    conf = [0.95, 0.60, 0.10, 0.10]
    assert ensemble_answer_correct(ids, conf, [True, False, False, False]) is True
    assert ensemble_answer_correct(ids, conf, [False, True, False, False]) is False


def test_nan_confidence_counts_as_zero_weight():
    ids = [0, 1]
    assert ensemble_answer_correct(ids, [float("nan"), 0.1], [True, False]) is False
