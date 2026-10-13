"""RQ4 - retrieval dissociation: the pure (no-network) logic.

    python tests/test_rq4.py

Network retrieval + live generation are exercised by the --limit small run, not here.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pandas as pd

from faultlines.rq4_retrieval import context_question, strata


def test_context_question_folds_passages():
    q = context_question("Who wrote X?", ["Alpha fact.", "Beta fact."])
    assert "Who wrote X?" in q
    assert "Alpha fact." in q and "Beta fact." in q
    assert context_question("bare", []) == "bare", "no context -> unchanged"


def test_strata_splits_by_cause_and_rarest_first():
    records = pd.DataFrame([
        dict(qid="p1", dataset="popqa", question="q1", gold="g1",
             meta={"s_pop": 50.0}, majority_wrong=True),
        dict(qid="p2", dataset="popqa", question="q2", gold="g2",
             meta={"s_pop": 5.0}, majority_wrong=True),
        dict(qid="t1", dataset="truthfulqa", question="q3", gold="g3",
             meta={"incorrect": ["bad"]}, majority_wrong=True),
        dict(qid="r1", dataset="popqa", question="q4", gold="g4",
             meta={"s_pop": 1.0}, majority_wrong=False),  # not an error -> excluded
    ])
    answers = pd.DataFrame([
        dict(qid="p1", aliases=["g1"]), dict(qid="p2", aliases=["g2"]),
        dict(qid="t1", aliases=["g3"]), dict(qid="r1", aliases=["g4"]),
    ])
    s = strata(records, answers)
    assert set(s["qid"]) == {"p1", "p2", "t1"}, "only errors, no r1"
    obsc = s[s.cause == "obscurity"]
    assert list(obsc["qid"]) == ["p2", "p1"], "rarest (lowest s_pop) first"
    assert set(s[s.cause == "misconception"]["qid"]) == {"t1"}


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1; print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"  ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
