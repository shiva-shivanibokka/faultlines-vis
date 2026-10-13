"""Issue B label-agreement maths. Pure functions only -- no transformer, no parquet."""
import numpy as np

from faultlines.labelcheck import agreement, normalize, read_kappa


def test_normalize_accepts_the_ways_a_human_actually_types_it():
    for raw in ("CORRECT", "correct", " Correct ", "c", "right", "true"):
        assert normalize(raw) == "CORRECT", raw
    for raw in ("WRONG", "wrong", " w ", "false"):
        assert normalize(raw) == "WRONG", raw


def test_normalize_rejects_non_verdicts_instead_of_guessing():
    # blank / undecided must NOT be coerced into a verdict -- an invented label
    # here would quietly fabricate agreement, which is the exact failure this
    # whole module exists to detect.
    for raw in (None, float("nan"), "", "  ", "?", "AMBIGUOUS", "maybe"):
        assert normalize(raw) is None, raw


def test_agreement_ignores_rows_the_human_left_blank():
    human = ["CORRECT", None, "WRONG"]
    grader = ["CORRECT", "WRONG", "WRONG"]
    a = agreement(human, grader)
    assert a["n"] == 2, "the blank row must be dropped, not scored"
    assert a["raw"] == 1.0


def test_perfect_and_inverted_agreement():
    both = ["CORRECT", "WRONG", "CORRECT", "WRONG"]
    assert agreement(both, both)["kappa"] == 1.0
    flipped = ["WRONG", "CORRECT", "WRONG", "CORRECT"]
    assert agreement(both, flipped)["kappa"] == -1.0


def test_kappa_punishes_the_skew_that_raw_agreement_hides():
    # A grader that always says WRONG on a 90%-WRONG band scores 90% raw
    # agreement while carrying zero information. Kappa must expose that --
    # this is the whole reason the module reports kappa and not just raw.
    human = ["WRONG"] * 9 + ["CORRECT"]
    lazy = ["WRONG"] * 10
    a = agreement(human, lazy)
    assert a["raw"] == 0.9, "raw agreement is flattered by the skew"
    assert a["kappa"] == 0.0, "kappa sees through it: no information beyond chance"


def test_kappa_undefined_only_when_nobody_disagrees_about_anything():
    # Both vectors one identical class: kappa is genuinely undefined (sklearn
    # returns nan). Distinct from the skew case above, where it is a real 0.0.
    a = agreement(["WRONG"] * 5, ["WRONG"] * 5)
    assert a["raw"] == 1.0
    assert np.isnan(a["kappa"])


def test_empty_input_returns_nan_not_a_crash():
    a = agreement([], [])
    assert a["n"] == 0 and np.isnan(a["raw"]) and np.isnan(a["kappa"])


def test_read_kappa_bands():
    assert "sound" in read_kappa(0.75)
    assert "poor" in read_kappa(0.10)
    assert "undefined" in read_kappa(float("nan"))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("\nall label-agreement checks passed")
