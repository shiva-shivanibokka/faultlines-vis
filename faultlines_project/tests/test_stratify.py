"""Stratified subsetting for the Semantic Entropy baseline.

The baseline on the full corpus is 681,456 generations -- 4x the main run and
beyond budget. A subset makes it affordable, but only if the subset still
resembles the corpus, otherwise the AUC measured on it does not transfer.
"""
import pandas as pd

from faultlines.baseline import stratified_subset


def corpus(counts):
    return pd.DataFrame([{"qid": f"{ds}-{i:05d}", "dataset": ds}
                         for ds, n in counts.items() for i in range(n)])


def test_returns_exactly_n_and_no_duplicates():
    df = corpus({"triviaqa": 17944, "popqa": 14267, "halueval": 10000, "truthfulqa": 380})
    out = stratified_subset(df, 8000, seed=42)
    assert len(out) == 8000
    assert out["qid"].nunique() == 8000


def test_preserves_corpus_proportions():
    df = corpus({"triviaqa": 17944, "popqa": 14267, "halueval": 10000, "truthfulqa": 380})
    out = stratified_subset(df, 8000, seed=42)
    for ds in df["dataset"].unique():
        want = (df["dataset"] == ds).mean()
        got = (out["dataset"] == ds).mean()
        assert abs(want - got) < 0.005, f"{ds}: corpus {want:.3f} vs subset {got:.3f}"


def test_a_tiny_dataset_gets_its_proportional_share_not_a_floor():
    # 50 of 9050 rows -> 0.55% of the corpus -> ~6 of 1000, NOT a minimum quota.
    # Documenting this because it is the reason TruthfulQA contributes only ~71
    # of the 8,000-question baseline subset: proportional allocation, working
    # as intended. Any per-dataset TruthfulQA claim must come from the ensemble
    # arm (all 380), not from the baseline.
    df = corpus({"big": 9000, "tiny": 50})
    out = stratified_subset(df, 1000, seed=42)
    assert len(out) == 1000
    got = (out["dataset"] == "tiny").sum()
    assert 4 <= got <= 8, f"expected ~6 (0.55% of 1000), got {got}"


def test_exhaustion_guard_holds_when_n_approaches_corpus_size():
    # the only regime where a dataset can run out
    df = corpus({"big": 900, "tiny": 10})
    out = stratified_subset(df, 905, seed=42)
    assert len(out) == 905
    assert (out["dataset"] == "tiny").sum() <= 10, "cannot take more than exists"


def test_n_larger_than_corpus_returns_the_whole_corpus():
    df = corpus({"a": 30, "b": 20})
    out = stratified_subset(df, 5000, seed=42)
    assert len(out) == 50


def test_is_deterministic_for_a_given_seed():
    df = corpus({"a": 500, "b": 500})
    a = stratified_subset(df, 200, seed=42)["qid"].tolist()
    b = stratified_subset(df, 200, seed=42)["qid"].tolist()
    assert a == b


def test_rounding_never_overshoots_n():
    # 7 datasets / 100 slots forces fractional quotas everywhere
    df = corpus({f"d{i}": 100 + i for i in range(7)})
    for n in (10, 33, 99, 100):
        assert len(stratified_subset(df, n, seed=1)) == n, n


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok ", name)
    print("\nstratification checks passed")
