"""Two-way containment for short-span datasets.

Motivated by a measured failure: TriviaQA (42% of the corpus) was excluded from
the containment tier because the dataset list still read ("popqa", "simpleqa"),
written before TriviaQA and HaluEval existed. 31% of its "wrong" verdicts were
correct answers.

Lowering the semantic threshold is NOT the fix. Measured on this corpus:
  cosine("Henley Rowing Club", "Leander Club") = 0.781   <- WRONG answer
  cosine("Sheppey",            "Isle of Sheppey") = 0.526 <- RIGHT answer
The encoder ranks a wrong answer above a right one, so no threshold separates
them. Containment is lexical and gets both right.
"""
from faultlines.grade import SHORT_SPAN, contains_either_way, normalise


def c(a, b):
    return contains_either_way(normalise(a), normalise(b))


def test_answer_containing_the_gold_is_correct():
    # the model said more than was asked, but included the right answer
    assert c("Gene Kelly and Betty Comden", "Betty Comden")
    assert c("12th fret", "12th")


def test_legitimate_short_forms_are_correct():
    assert c("Sheppey", "Isle of Sheppey")


def test_short_form_ratio_guard_rejects_a_different_entity():
    # "York" IS a word-boundary substring of "New York City" but is a different
    # city. Without the ratio guard this direction would accept it.
    assert not c("York", "New York City")


def test_unrelated_entities_stay_wrong_even_when_topically_similar():
    # cosine puts these at 0.781; containment correctly rejects them
    assert not c("Henley Rowing Club", "Leander Club")
    assert not c("Brad Falchuk", "Chris Martin")


def test_substring_that_is_not_a_word_is_rejected():
    assert not c("cat", "concatenation")


def test_short_candidates_are_ignored():
    # <4 chars: too weak a signal to credit
    assert not c("something else entirely", "USA")


def test_truthfulqa_is_excluded_from_containment():
    # sentence golds: a substring hit means nothing and negation would invert
    # the meaning while still containing the words
    assert "truthfulqa" not in SHORT_SPAN
    assert {"triviaqa", "halueval", "popqa"} <= set(SHORT_SPAN)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok ", name)
    print("\ncontainment checks passed")


def test_grade_one_and_grade_lexical_agree_on_the_containment_tier():
    """They must not drift. grade_one used to carry its own copy of the tier
    logic, so fixing the stale ("popqa","simpleqa") list in one left the other
    broken -- and track.py calls grade_one directly."""
    from faultlines.grade import grade_one
    for ds in ("triviaqa", "halueval", "popqa"):
        assert grade_one("Sheppey", "Isle of Sheppey", [], ds) == (True, "contains"), ds
        assert grade_one("12th fret", "12th", [], ds) == (True, "contains"), ds
    # truthfulqa must NOT get containment (sentence golds)
    got = grade_one("Sheppey", "Isle of Sheppey", [], "truthfulqa")
    assert got[1] != "contains"
