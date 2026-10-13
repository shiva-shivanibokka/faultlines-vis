"""Build the RQ3 local rerun question set, and verify the local models by digest.

WHY THIS EXISTS
DeepInfra serves gen-2 model IDs with gen-3 weights (ISSUES #31) and Together
will not serve them serverless at all, so the hosted RQ3 result is retracted.
Ollama weights are content-addressed: the digest is derived FROM the file, so a
substituted model is a different digest. That is stronger than the behavioural
identity gate -- it is verification rather than inference.

WHY NOT 4,000 RANDOM QUESTIONS
Silent consensus runs at ~2%, so a random 4,000 yields ~80 usable cases and
spends ~18 laptop-hours (measured: 0.24 gen/s) on questions that carry no
information about persistence. This set instead takes:

  ALL gen-3 silent-consensus questions  -> measures PERSISTED and HEALED directly
  a random control sample               -> measures EMERGED, and the base rate

Both strata are recorded, so the pooled rate can be reweighted back to the
corpus. Comparing ~1,054 cases per arm instead of the pilot's 5-vs-7 is the
difference between an anecdote and a confidence interval.

    python scripts/build_rq3_local.py
"""
from __future__ import annotations

import subprocess
import sys

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path  # noqa: E402

CONTROL_N = 1500

# Digests recorded 2026-07-28 from `ollama list`. If one of these changes, the
# model on disk is NOT the model that produced the frozen pilot, and the Track
# comparison would silently change meaning -- exactly the failure #31 was.
EXPECTED = {
    "llama3.1:8b": "46e0c10c039e",
    "qwen2.5:7b": "845dbda0ea48",
    "mistral:7b": "6577803aa9a0",
    "gemma2:9b": "ff02c3702f32",
}


def verify_digests() -> bool:
    """Content-addressed identity check. The local answer to defect #31."""
    try:
        out = subprocess.run(["ollama", "list"], capture_output=True, text=True,
                             timeout=60, check=True).stdout
    except Exception as exc:                                    # noqa: BLE001
        print(f"FAIL  could not run `ollama list`: {exc}")
        return False

    have = {}
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2:
            have[parts[0]] = parts[1]

    ok = True
    print("model identity by content digest:")
    for name, want in EXPECTED.items():
        got = have.get(name)
        if got == want:
            print(f"  OK        {name:14} {got}")
        elif got is None:
            print(f"  MISSING   {name:14} not installed -- `ollama pull {name}`")
            ok = False
        else:
            print(f"  CHANGED   {name:14} expected {want}, found {got}")
            print(f"              the weights on disk are NOT the ones that produced")
            print(f"              the frozen pilot. Do not mix the two arms.")
            ok = False
    return ok


def main() -> int:
    if not verify_digests():
        print("\nNOT ready -- fix the models above before running.")
        return 1

    rec = pd.read_parquet(path("processed", "records.parquet"))
    qs = pd.read_parquet(path("interim", "questions.parquet"))

    silent = set(rec.loc[rec["silent_consensus"], "qid"])
    pool = rec.loc[~rec["qid"].isin(silent), "qid"]
    control = pool.sample(n=min(CONTROL_N, len(pool)), random_state=CFG["seed"])

    keep = silent | set(control)
    out = qs[qs["qid"].isin(keep)].copy()
    # Build the set ONCE. It used to be `lambda q: ... q in set(silent) ...`,
    # which reconstructed a 1,054-element set for every one of 2,554 rows.
    out["stratum"] = out["qid"].map(lambda q: "silent" if q in silent else "control")

    dest = path("interim", "questions_rq3local.parquet")
    out.to_parquet(dest)

    n_models = len(CFG["ensemble_local"])
    gens = len(out) * n_models
    print(f"\n-> {dest.name}")
    print(f"   silent-consensus stratum : {(out.stratum == 'silent').sum():,}")
    print(f"   random control stratum   : {(out.stratum == 'control').sum():,}")
    print(f"   total questions          : {len(out):,}")
    print(f"   generations              : {gens:,} "
          f"({n_models} models)  ~{gens / 0.24 / 3600:.1f} h at 0.24 gen/s")
    print(out.groupby(["stratum", "dataset"]).size().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
