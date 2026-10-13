#!/usr/bin/env python
"""Shell for scripts/parse_check.mjs so reproduce.py can run it like any stage.

The check itself is JavaScript because the thing being checked is JavaScript:
parsing it with node is the only way to find out whether a browser will accept
it. If node is not installed this SKIPS -- but a skip is not a pass, so it
exits with its own status, EXIT_SKIPPED (77, the automake "skipped" code),
rather than 0. Exiting 0 made reproduce.py count an unchecked tool as a checked
one. Whether a skip should block the pipeline is reproduce.py's decision; this
script's job is only to not lie about what it did.

    0   every inline script parsed
    1+  node ran and reported a parse failure (node's own exit code)
    77  node is not on PATH; nothing was checked
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MJS = Path(__file__).resolve().parent / "parse_check.mjs"
EXIT_SKIPPED = 77

if shutil.which("node") is None:
    print("  SKIP  node not on PATH; the inline scripts were not parse-checked")
    raise SystemExit(EXIT_SKIPPED)
raise SystemExit(subprocess.run([shutil.which("node"), str(MJS)], cwd=ROOT).returncode)
