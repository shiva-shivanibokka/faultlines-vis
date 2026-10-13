"""Does 4-bit quantization change WHICH questions the models get wrong?

Answers the open question carried in ISSUES since the pilot ("does 4-bit
quantization degrade the disagreement signal?"), which was previously marked
NOT CLAIMABLE because the only two runs available differed in several ways at
once. This is the controlled version: identical weights, identical questions,
identical prompts, identical grading -- ONLY the precision differs.

Why 8-bit and not fp16: the hosted gen-3 ensemble is not full precision either
(Llama-4-Maverick-17B-128E-Instruct-FP8 is 8-bit by name, and the other three
providers do not publish their serving precision), so "match full precision" is
not achievable. Matching ~8-bit is, and fp16 would be 14-18 GB per model against
8 GB of VRAM.

Exit code 0 = 4-bit is a faithful stand-in, safe to use for the full corpus run.
Exit code 1 = precision matters; the full run needs 8-bit and a human decision,
because it roughly triples the wall-clock.

    python scripts/compare_precision.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from faultlines.config import path  # noqa: E402

# Tolerances. Chosen BEFORE seeing the numbers, which is the only time a
# threshold can be chosen honestly.
MAX_PERSISTENCE_DELTA = 0.05      # 5 percentage points on the headline
MAX_SILENT_DELTA = 0.005          # 0.5 pp on the blind-spot rate


def main() -> int:
    q4 = pd.read_parquet(path("processed", "records_rq3local.parquet"))
    q8 = pd.read_parquet(path("processed", "records_rq3local_q8.parquet"))
    g3 = pd.read_parquet(path("processed", "records.parquet"))
    strat = pd.read_parquet(path("interim", "questions_rq3local.parquet"))[["qid", "stratum"]]

    q4 = q4.merge(strat, on="qid").set_index("qid")
    q8 = q8.merge(strat, on="qid").set_index("qid")
    # only questions in the analysed (deduplicated) corpus -- ISSUES #66
    shared = q4.index.intersection(q8.index).intersection(pd.Index(g3.qid))
    q4, q8 = q4.loc[shared], q8.loc[shared]

    g3_silent = set(g3.loc[g3["silent_consensus"], "qid"])
    N, n_sil = len(g3), len(g3_silent)
    n_out = N - n_sil

    print("=" * 66)
    print("PRECISION COMPARISON  4-bit vs 8-bit, same models, same questions")
    print("=" * 66)
    print(f"questions compared: {len(shared):,}\n")

    rows = []
    for lbl, d in (("4-bit", q4), ("8-bit", q8)):
        sil = d[d["stratum"] == "silent"]
        ctl = d[d["stratum"] == "control"]
        p_in = sil["silent_consensus"].mean()
        p_out = ctl["silent_consensus"].mean()
        rate = (n_sil * p_in + n_out * p_out) / N
        rows.append({"arm": lbl, "persistence": p_in, "corpus_silent_rate": rate,
                     "majority_wrong": d["majority_wrong"].mean(),
                     "mean_disagreement": d["disagreement_unweighted"].mean()})
    t = pd.DataFrame(rows).set_index("arm")
    print(t.to_string(float_format=lambda v: f"{v:.4f}"))

    d_pers = abs(t.loc["4-bit", "persistence"] - t.loc["8-bit", "persistence"])
    d_sil = abs(t.loc["4-bit", "corpus_silent_rate"] - t.loc["8-bit", "corpus_silent_rate"])

    # Item-level agreement matters more than matching averages: two arms can hit
    # the same rate while being wrong about different questions, and it is the
    # IDENTITY of the blind spots that RQ3 compares.
    #
    # STRATUM-WEIGHTED (ISSUES #75). The sample is every gen-3 blind spot plus
    # a random draw of the rest, so each control question stands for ~25 in
    # the corpus. The persistence rate above was weighted; these two were not,
    # and read as if the blind-spot stratum were most of the corpus -- the same
    # defect as #56. Each question is weighted by its stratum's N / sampled.
    w = np.where(q4["stratum"] == "silent",
                 n_sil / max(1, (q4["stratum"] == "silent").sum()),
                 n_out / max(1, (q4["stratum"] == "control").sum()))
    agree_raw = (q4["majority_wrong"] == q8["majority_wrong"]).mean()
    agree = float((w * (q4["majority_wrong"] == q8["majority_wrong"])).sum() / w.sum())
    a4, a8 = q4["silent_consensus"].to_numpy(bool), q8["silent_consensus"].to_numpy(bool)
    s4 = set(q4.index[a4])
    s8 = set(q8.index[a8])
    jac_raw = len(s4 & s8) / max(1, len(s4 | s8))
    jac = float((w * (a4 & a8)).sum() / max(1e-12, (w * (a4 | a8)).sum()))

    print(f"\nitem-level agreement on majority_wrong : {agree:.1%}"
          f"   (unweighted, sample only: {agree_raw:.1%})")
    print(f"blind-spot set overlap (Jaccard)       : {jac:.3f}"
          f"   (unweighted: {jac_raw:.3f}; {len(s4 & s8)} shared, "
          f"{len(s4)} vs {len(s8)} in the sample)")
    print(f"\ndelta persistence      : {d_pers:.3f}  (tolerance {MAX_PERSISTENCE_DELTA})")
    print(f"delta corpus blind rate: {d_sil:.4f} (tolerance {MAX_SILENT_DELTA})")

    ok = d_pers <= MAX_PERSISTENCE_DELTA and d_sil <= MAX_SILENT_DELTA
    print("\n" + ("VERDICT: 4-bit is a faithful stand-in. Safe for the full corpus run."
                  if ok else
                  "VERDICT: precision CHANGES the result. The full run needs 8-bit "
                  "(~3x wall-clock) -- ask before committing."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
