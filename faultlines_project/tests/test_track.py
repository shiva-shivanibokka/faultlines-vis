"""Track - the persistence / overlap metric (pure; gen-1 generation is a hand-off).

    python tests/test_track.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import pandas as pd

from faultlines.track import persistence, _records_from_answers


def test_persistence_core_and_healing():
    gen1 = pd.DataFrame({"qid": ["a", "b", "c"], "silent_consensus": [True, True, False]})
    gen2 = pd.DataFrame({"qid": ["a", "b", "c"], "silent_consensus": [True, False, True]})
    p = persistence(gen1, gen2)
    assert p["persistent_core"] == 1, p          # a survives
    assert p["healed"] == 1, p                    # b fixed by the upgrade
    assert p["emerged"] == 1, p                   # c newly broken
    assert abs(p["jaccard"] - (1 / 3)) < 1e-9, p  # {a} / {a,b,c}
    assert abs(p["persist_rate"] - 0.5) < 1e-9, p # 1 of 2 gen1 silents survive


def test_records_from_answers_finds_silent_consensus():
    # one question, four models, all agree AND all wrong -> silent consensus
    ans = pd.DataFrame([
        dict(qid="q", model=m, answer="Joseph Smith", confidence=0.9, correct=False)
        for m in "abcd"
    ])
    rec = _records_from_answers(ans).set_index("qid")
    assert rec.loc["q", "silent_consensus"] == True, rec  # noqa: E712
    assert rec.loc["q", "n_clusters"] == 1


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


def test_records_from_answers_applies_the_gradeable_filter():
    """Must match disagree.run(), which drops gradeable == False rows.

    If the two disagree, the Track arms are computed over DIFFERENT question
    populations and the silent-consensus overlap compares mismatched sets --
    biasing the headline persistence number in an unknown direction.
    """
    import pandas as pd
    from faultlines.track import _records_from_answers

    rows = []
    for qid, gradeable in [("q1", True), ("q2", False)]:
        for m in ("a", "b"):
            rows.append({"qid": qid, "model": m, "answer": "Paris",
                         "confidence": 0.9, "correct": False,
                         "dataset": "popqa", "gradeable": gradeable})
    out = _records_from_answers(pd.DataFrame(rows))
    assert set(out["qid"]) == {"q1"}, \
        "ungradeable q2 must be dropped, exactly as disagree.run() drops it"
