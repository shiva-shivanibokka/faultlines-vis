"""Dataset loading - the non-adversarial filter (pure; HF download not exercised here).

    python tests/test_datasets.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pandas as pd

from faultlines.datasets import filter_non_adversarial


def test_filter_drops_adversarial_only():
    df = pd.DataFrame({
        "question": ["q1", "q2", "q3"],
        "meta": [{"type": "Adversarial"}, {"type": "Non-Adversarial"}, {"type": None}],
    })
    out = filter_non_adversarial(df)
    assert list(out["question"]) == ["q2", "q3"], list(out["question"])


def test_filter_handles_missing_meta_gracefully():
    df = pd.DataFrame({"question": ["q1", "q2"], "meta": [None, {"type": "Non-Adversarial"}]})
    out = filter_non_adversarial(df)
    assert set(out["question"]) == {"q1", "q2"}, "None meta is kept (not adversarial)"


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


# ---- duplicate questions (ISSUES #66) ----
from faultlines.datasets import duplicate_qids


def _q(rows):
    return pd.DataFrame(rows, columns=["qid", "dataset", "question", "gold"])


def test_exact_twin_is_dropped_and_the_earlier_qid_kept():
    q = _q([("triviaqa-00002", "triviaqa", "Who wrote X?", "Ann"),
            ("triviaqa-00001", "triviaqa", "Who  wrote x? ", "ann")])
    assert duplicate_qids(q) == {"triviaqa-00002"}


def test_same_text_different_gold_is_not_a_duplicate():
    """Two films called 'Crash': one question text, two questions. RQ2's
    shared-title finding is built on exactly these, so they must survive."""
    q = _q([("popqa-00001", "popqa", "Who was the director of Crash?", "Paul Haggis"),
            ("popqa-00002", "popqa", "Who was the director of Crash?", "David Cronenberg")])
    assert duplicate_qids(q) == set()


def test_same_question_in_two_datasets_is_not_a_duplicate():
    q = _q([("popqa-00001", "popqa", "What is the capital of Peru?", "Lima"),
            ("triviaqa-00001", "triviaqa", "What is the capital of Peru?", "Lima")])
    assert duplicate_qids(q) == set()
