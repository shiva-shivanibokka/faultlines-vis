"""RQ2 - localization and the popularity control.

    python tests/test_rq2.py

Pins the popularity extraction and the map-neighbourhood density on small hand
-built frames, so the real popularity-control numbers rest on tested plumbing.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from faultlines.rq2_localize import popularity, neighbourhood_density


def test_popularity_reads_s_pop_and_handles_missing():
    records = pd.DataFrame([
        dict(qid="a", dataset="popqa", meta={"s_pop": 99.0}),
        dict(qid="b", dataset="popqa", meta={"s_pop": 0.0}),
        dict(qid="c", dataset="truthfulqa", meta={"incorrect": ["x"]}),
    ])
    pop = popularity(records)
    assert abs(pop.iloc[0] - np.log10(100.0)) < 1e-9, pop.iloc[0]
    assert abs(pop.iloc[1] - np.log10(1.0)) < 1e-9  # log10(0+1)=0
    assert np.isnan(pop.iloc[2]), "non-popqa must be NaN"


def test_neighbourhood_density_on_a_line():
    # five points on the x-axis; a tight wrong-pair near x=0..2
    records = pd.DataFrame([
        dict(qid="p0", x=0.0, y=0.0, majority_wrong=False),
        dict(qid="p1", x=1.0, y=0.0, majority_wrong=True),
        dict(qid="p2", x=2.0, y=0.0, majority_wrong=True),
        dict(qid="p3", x=10.0, y=0.0, majority_wrong=False),
        dict(qid="p4", x=11.0, y=0.0, majority_wrong=False),
    ])
    dens = neighbourhood_density(records, k=2).to_numpy()
    # p0's two nearest (p1,p2) are both wrong -> 1.0, the maximum
    assert abs(dens[0] - 1.0) < 1e-9, dens
    assert dens[0] == dens.max()
    assert all(0.0 <= d <= 1.0 for d in dens)


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
