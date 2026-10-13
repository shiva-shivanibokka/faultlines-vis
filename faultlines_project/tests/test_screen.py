"""Screening - the all-agree filter (pure logic; live gen is the --limit run).

    python tests/test_screen.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from faultlines.screen import screen_one


def test_unanimous_is_all_agree():
    s = screen_one(["Canberra", "Canberra", "Canberra", "Canberra"])
    assert s["all_agree"] is True and s["n_clusters"] == 1, s


def test_paraphrase_still_all_agree():
    # clustering is by meaning, so paraphrases count as agreement
    s = screen_one(["Canberra", "Canberra, Australia", "It is Canberra", "Canberra"])
    assert s["all_agree"] is True, f"paraphrases split into {s['n_clusters']}"


def test_split_is_not_all_agree():
    s = screen_one(["Canberra", "Sydney", "Melbourne", "Canberra"])
    assert s["all_agree"] is False and s["n_clusters"] >= 2, s


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
