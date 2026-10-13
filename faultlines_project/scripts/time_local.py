#!/usr/bin/env python
"""Measure local generation throughput, because two files disagree by 20x.

RESULTS.md:243 says the 170,364-generation local run took "~9 hours of laptop
GPU", which is 5.26 gen/s. build_rq3_local.py budgets with a MEASURED 0.24
gen/s, which puts the same run at 197 hours. One of those is wrong and it sits
in a reproducibility claim, so it gets measured rather than argued about.

Runs N real questions through each local model in turn, exactly as the real
pass does -- one model at a time, same endpoint, same prompt, same max_tokens.
The first call to each model pays the load-into-VRAM cost; that is reported
separately, because in the real run it is paid once per model and amortised
over 42,551 questions, not once per question.

    python scripts/time_local.py            # 15 questions x 4 models
    python scripts/time_local.py --n 50

Writes nothing. Prints a table and the implied wall clock for a full pass.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path                      # noqa: E402
from faultlines.generate import prompt_for                   # noqa: E402

ENDPOINT = CFG["generation"]["local_endpoint"]
MODELS = [m["name"] for m in CFG["ensemble_local"]]


def one(model: str, question: str, dataset: str | None) -> float:
    """Seconds for a single generation. Raises rather than swallowing."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_for(dataset)},
            {"role": "user", "content": question},
        ],
        "temperature": CFG["generation"]["temperature"],
        "max_tokens": CFG["generation"]["max_tokens"],
    }
    t0 = time.perf_counter()
    r = requests.post(ENDPOINT, json=body, timeout=CFG["generation"]["timeout_s"])
    r.raise_for_status()
    r.json()["choices"][0]["message"]["content"]
    return time.perf_counter() - t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=15, help="questions per model")
    a = ap.parse_args()

    src = path("interim", "questions_rq3local.parquet")
    if not src.exists():
        src = path("interim", "questions.parquet")
    q = pd.read_parquet(src).head(a.n)
    print(f"{len(q)} questions x {len(MODELS)} models  <-  {src.name}\n")

    rows, total_steady = [], 0.0
    for model in MODELS:
        try:
            load = one(model, q.iloc[0].question, q.iloc[0].dataset)
        except Exception as exc:                     # a missing model is data
            print(f"  {model:<16} SKIPPED -- {exc}")
            continue
        times = []
        for r in q.itertuples():
            try:
                times.append(one(model, r.question, r.dataset))
            except Exception as exc:
                print(f"  !! {model} {r.qid}: {exc}")
        med = statistics.median(times)
        rows.append((model, load, med, 1 / med))
        total_steady += 1 / med
        print(f"  {model:<16} first call {load:6.2f}s   median {med:6.3f}s"
              f"   {1/med:6.2f} gen/s")

    if not rows:
        print("\nno models responded -- is `ollama serve` running?")
        return 1

    # The real pass is sequential: each model does all 42,551 questions, so the
    # rate that matters is the HARMONIC total, not the sum of parallel rates.
    per_model_secs = sum(1 / r[3] * 42_551 for r in rows)
    print(f"\n  full pass, {len(rows)} models x 42,551 questions "
          f"= {len(rows)*42_551:,} generations")
    print(f"  implied wall clock: {per_model_secs/3600:6.1f} h"
          f"   ({len(rows)*42_551/per_model_secs:.2f} gen/s overall)")
    print("\n  RESULTS.md:243 claims ~9 h (5.26 gen/s)")
    print("  build_rq3_local.py budgets 0.24 gen/s (197 h)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
