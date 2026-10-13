"""Repair for ISSUES #41 -- remove the pre-fix rows from the RQ5 parquet.

WHY THIS IS SAFE TO DO POSITIONALLY
`rq5_agentic.run()` checkpoints with `pd.concat([prev, pd.DataFrame(rows)])`,
where `prev` is the file exactly as it was loaded at startup. Parquet preserves
row order, and every checkpoint rebuilds from the same `prev`, so rows written by
earlier runs stay as a stable prefix of the file. The 160 rows produced before the
Wikipedia cooldown fix are therefore rows 0..159 -- confirmed by composition:

    Llama 100 · Qwen 20 · Mistral 20 · Gemma 20   = 160

which reconciles exactly with the 22:52 snapshot (Llama 1001, Qwen 199, Gemma 20,
Mistral 20 = 1240) minus the 1080 rows the 19:21 run recorded.

DO NOT RUN THIS WHILE THE JOB IS RUNNING. The process holds `prev` in memory and
rewrites the whole file at each checkpoint, so the deletion would be silently
undone at the next one. The guard below refuses if the job looks alive.

After this, re-run `python -m faultlines.rq5_agentic --arm wiki`. Resume skips
everything still present and re-does only the dropped pairs. Wikipedia is cached,
so the cost is model calls only.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import path  # noqa: E402

N_PREFIX = 160
EXPECTED = {"meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8": 100,
            "Qwen/Qwen3-235B-A22B-Instruct-2507": 20,
            "mistralai/Mistral-Small-3.2-24B-Instruct-2506": 20,
            "google/gemma-3-27b-it": 20}


def job_running() -> bool:
    """True if an rq5_agentic process is alive. Positional surgery on a file that
    something else is rewriting is a lost update, so this is a hard gate."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" |"
             " Where-Object { $_.CommandLine -like '*rq5_agentic*' }).Count"],
            capture_output=True, text=True, timeout=60).stdout.strip()
        return bool(out) and out != "0"
    except Exception:                                  # noqa: BLE001
        return True                                    # unknown -> refuse


def main() -> int:
    if job_running():
        print("REFUSING: an rq5_agentic process is still running.\n"
              "  It rewrites the whole parquet from memory at every checkpoint,\n"
              "  so this deletion would be undone. Wait for it to exit.")
        return 1

    dest = path("processed", "rq5_agentic.parquet")
    d = pd.read_parquet(dest)
    head = d.head(N_PREFIX)
    got = head.model.value_counts().to_dict()

    # The composition IS the evidence that the prefix is the pre-fix block. If it
    # does not match, the assumption behind positional deletion is wrong and
    # deleting 160 arbitrary rows would destroy good data.
    if got != EXPECTED:
        print("REFUSING: the first 160 rows are not the expected pre-fix block.")
        print(f"  expected: {EXPECTED}")
        print(f"  got:      {got}")
        return 2

    backup = dest.with_suffix(".parquet.prefix-bak")
    d.to_parquet(backup)
    d.iloc[N_PREFIX:].reset_index(drop=True).to_parquet(dest)

    print(f"backup   -> {backup}")
    print(f"dropped  {N_PREFIX} pre-fix rows ({len(d)} -> {len(d) - N_PREFIX})")
    for m, n in EXPECTED.items():
        print(f"  {m.split('/')[-1][:34]:<34} {n}")
    print("\nNow re-run:  python -m faultlines.rq5_agentic --arm wiki")
    print("Resume will re-do exactly these pairs and nothing else.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
