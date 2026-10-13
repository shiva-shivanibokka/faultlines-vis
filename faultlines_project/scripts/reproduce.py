#!/usr/bin/env python
"""Rebuild every published figure from what is on disk, and check it.

    python scripts/reproduce.py            # everything, ~25 min (tests dominate)
    python scripts/reproduce.py --fast     # skip the test suite, ~2 min
    python scripts/reproduce.py --list     # what each stage does, run nothing

WHY THIS EXISTS

There is a real pipeline behind this project and, until 2026-08-26, no single
entry point into it. A committee member who can rebuild one figure believes all
of them; one who cannot has to take twenty thousand words on trust. This is that
entry point.

It also protects the thesis from the failure mode its own defect log shows five
times over -- ISSUES #43, #45, #46, #47, #49 -- a number that was correct when it
was typed. Every stage below DERIVES; nothing here re-types anything.

WHAT IT DOES NOT DO, AND WHY THAT IS STATED RATHER THAN HIDDEN

It does not re-run the generation stages. Each arm is 170,364 answers: the
2025 arm cost real money on a hosted API, and the local 2024 arm took about 138
hours of wall clock at the measured 0.34 gen/s. Those answers are frozen on disk precisely so that every downstream number is
recomputed from a fixed corpus rather than from a fresh sample. `--list` names
the paid stages and what they would cost.

So this verifies **everything from graded answers onward**, which is every claim
in Chapters 5, 6 and 7. It does not verify that the same four models asked again
today would answer the same way. They would not, and Chapter 7 says so.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

# (key, headline, argv, what a reader should see)
STAGES = [
    ("export", "Rebuild summary.json, data.json and the prerendered pages",
     ["scripts/export_web.py"],
     "the corpus, the AUC, the blind-spot count and every panel figure, "
     "recomputed from records.parquet and baked into the three web pages"),
    ("figures", "Check every figure in the thesis against those files",
     ["scripts/check_writeup.py"],
     "every figure in the chapters, checked against summary.json, plus two "
     "cross-artifact invariants. The count is printed by the script rather "
     "than named here -- naming it is how it goes stale. This is the stage "
     "that fails if a chapter has drifted from the data"),
    ("scripts", "Parse-check every inline script in the tool and the pages",
     ["scripts/run_parse_check.py"],
     "the deck is prerendered so a syntax error there fails loudly; the TOOL "
     "is not, and a broken edit would ship silently and be found by a person "
     "opening the link"),
    ("walkthrough", "Re-run the cognitive walkthrough",
     ["scripts/walkthrough_audit.py"],
     "the six-task table, and the two tasks predicted to defeat a new user"),
    ("arms", "Compare the grading-artifact rate between generations",
     ["scripts/artifact_by_arm.py"],
     "both arms' artifact rates, the composition check and what they do to RQ3"),
    ("agents", "Re-check the agent-decision null",
     ["scripts/agent_concordance.py"],
     "a NULL result, kept so it is not re-derived: four agents do not make "
     "correlated decisions about whether to search, and the two ways that "
     "nearly looked like a finding are printed with it"),
    ("tests", "The test suite",
     ["-m", "pytest", "tests", "-q", "--no-header", "-p", "no:cacheprovider"],
     "70 tests, all offline. Slowest stage by far -- --fast skips it"),
]

PAID = [
    ("generation", "170,364 answers x 2 arms",
     "~138 h measured for the local 2024 arm alone, and that arm cannot be regenerated at all: it ran on "
     "local Ollama weights that config no longer points at"),
    ("adjudication", "950 + 823 LLM verdicts on the blind spots (2025 + 2024 arms)",
     "about $1 per arm; scripts/adjudicate_blind.py --arm {2024,2025}"),
    ("hand labels", "430 + 115 human verdicts",
     "two people, and the second one closed the largest limitation in the "
     "thesis at kappa 0.970"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="skip the test suite")
    ap.add_argument("--list", action="store_true", help="describe, run nothing")
    ap.add_argument("--only", help="run one stage by key")
    a = ap.parse_args()

    stages = [s for s in STAGES if not (a.fast and s[0] == "tests")]
    if a.only:
        stages = [s for s in STAGES if s[0] == a.only]
        if not stages:
            print(f"no stage {a.only!r}; keys: "
                  f"{', '.join(s[0] for s in STAGES)}")
            return 2

    if a.list:
        print("STAGES -- each derives, none re-types\n")
        for k, head, argv, why in STAGES:
            print(f"  {k:<12} {head}\n  {'':<12} {why}\n")
        print("NOT RE-RUN HERE, and deliberately:\n")
        for k, what, why in PAID:
            print(f"  {k:<12} {what}\n  {'':<12} {why}\n")
        return 0

    print("=" * 74)
    print("REPRODUCING FAULTLINES FROM WHAT IS ON DISK")
    print("=" * 74)
    print(f"  {len(stages)} stages   python = {PY}")
    if a.fast:
        print("  --fast: the test suite is skipped, so this checks the FIGURES")
        print("  and not the code that produced them.")
    print()

    results, t0 = [], time.time()
    for i, (key, head, argv, _why) in enumerate(stages, 1):
        print("-" * 74)
        print(f"[{i}/{len(stages)}] {key} — {head}")
        print("-" * 74, flush=True)
        t = time.time()
        r = subprocess.run([PY, *argv], cwd=ROOT)
        dt = time.time() - t
        # 77 = a stage that could not run here (run_parse_check without
        # node). A skip is neither a pass nor a failure, and it must not let
        # the closing line claim every figure was verified.
        skipped = r.returncode == 77
        results.append((key, r.returncode == 0, skipped, dt))
        state = "SKIPPED" if skipped else ("ok" if r.returncode == 0 else "FAILED")
        print(f"\n  {key}: {state} in {dt:.0f}s\n", flush=True)

    print("=" * 74)
    print("RESULT")
    print("=" * 74)
    for key, ok, sk, dt in results:
        print(f"  {'SKIP' if sk else 'ok  ' if ok else 'FAIL'}  {key:<12} {dt:>7.0f}s")
    bad = [k for k, ok, sk, _ in results if not ok and not sk]
    skip = [k for k, _, sk, _ in results if sk]
    print(f"\n  {len(results) - len(bad) - len(skip)}/{len(results)} stages passed"
          f"{f', {len(skip)} skipped' if skip else ''} in {time.time() - t0:.0f}s")
    if bad:
        print(f"\n  FAILED: {', '.join(bad)}")
        print("  Do not commit and do not quote a figure until this is green.")
        print("  If it is `figures`, either a chapter drifted or the data moved;")
        print("  check_writeup names the row, and knowing WHICH is the whole job.")
        return 1
    if skip:
        print(f"\n  SKIPPED: {', '.join(skip)} -- not verified on this machine.")
        return 1
    print("\n  Every published figure was rebuilt from the records and matches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
