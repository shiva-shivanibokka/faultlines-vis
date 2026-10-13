#!/usr/bin/env python
"""Capture the thesis figures from the deployed instrument.

    python scripts/capture_figures.py            # -> writeup/figures/*.png
    python scripts/capture_figures.py --check    # report only, capture nothing

WHY THIS IS A SCRIPT AND NOT SEVEN COMMITTED PNGs

The figures are screenshots of the live tool, and a screenshot is an output,
not a source. Committing them puts ~1.9 MB of binary into a repository that is
otherwise text, and every recapture rewrites the whole blob. Committing the
capture instead keeps the repository to code and makes the figures rebuildable
by anyone who clones it.

WHAT THAT COSTS, STATED PLAINLY

These are captures of a deployed page on a date, so re-running this does not
reproduce the old images -- it produces current ones. If the tool changes, the
figures change, and the thesis text around them may no longer describe what the
reader sees. Chapter 3 and Chapter 5 quote numbers that appear *inside* these
screenshots; `check_writeup.py` checks the prose against the records but cannot
read a PNG. After a recapture, re-read the captions.

The front matter records the capture date for exactly this reason.

REQUIREMENTS
  * Google Chrome (the same binary `build_thesis.py` prints with)
  * the tool deployed and reachable -- these are live URLs, not local files,
    because the tool fetches data.json and will not run from file://
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIGDIR = ROOT / "writeup" / "figures"

TOOL = "https://faultlines-tool.vercel.app"
DECK = "https://faultlines-peach.vercel.app"

# name, url, viewport. The heights are chosen so the panel is fully in frame;
# build_thesis_docx.py scales each image down so it fits a page with its title
# and caption, so a tall capture costs nothing but pixels.
FIGURES = [
    ("fig3-1-map-blind",        f"{TOOL}/#t=map&c=blind", (1500, 1150)),
    ("fig3-2-case-queue",       f"{TOOL}/#t=blind",       (1500, 1250)),
    ("fig5-1-signal",           f"{TOOL}/#t=sig",         (1500, 1500)),
    ("fig5-2-map-name",         f"{TOOL}/#t=map&c=name",  (1500, 1150)),
    ("fig5-3-generation-diff",  f"{TOOL}/#t=gen",         (1500, 1250)),
    ("fig5-4-ensemble-picker",  f"{TOOL}/#t=pick",        (1500, 2150)),
    ("fig6-1-walkthroughs",     f"{DECK}/walkthroughs.html", (1500, 1500)),
]

CHROME_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)


def find_chrome() -> str | None:
    for p in CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    return (shutil.which("google-chrome") or shutil.which("chromium")
            or shutil.which("chrome"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report which figures are missing and exit")
    a = ap.parse_args()

    FIGDIR.mkdir(parents=True, exist_ok=True)
    missing = [n for n, _u, _s in FIGURES if not (FIGDIR / f"{n}.png").exists()]

    if a.check:
        if missing:
            print(f"{len(missing)} of {len(FIGURES)} figures missing:")
            for n in missing:
                print(f"  - writeup/figures/{n}.png")
            print("\nrun: python scripts/capture_figures.py")
            return 1
        print(f"all {len(FIGURES)} figures present")
        return 0

    chrome = find_chrome()
    if not chrome:
        print("Chrome not found. Install it, or capture the figures by hand "
              "from:\n  " + "\n  ".join(u for _n, u, _s in FIGURES))
        return 1

    failed = []
    for name, url, (w, h) in FIGURES:
        out = FIGDIR / f"{name}.png"
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--hide-scrollbars", f"--window-size={w},{h}",
            # the tool fetches data.json and renders with d3; a short budget
            # captures a half-drawn map that looks convincingly finished
            "--virtual-time-budget=14000",
            f"--screenshot={out}", url,
        ]
        # Remove the previous capture FIRST. Otherwise a capture that failed
        # outright leaves last week's PNG in place, it passes the size test
        # below, and this reports "ok" for an image it did not take. A missing
        # figure is loud (--check and the Word build both notice); a stale one
        # that was reported as fresh is not.
        out.unlink(missing_ok=True)
        why = ""
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            rc = r.returncode
            if rc != 0:
                why = f"chrome exited {rc}: {(r.stderr or '').strip()[-200:]}"
        except subprocess.TimeoutExpired:
            rc, why = -1, "chrome timed out after 180s"
        size = out.stat().st_size if out.exists() else 0
        # a page that failed to render still screenshots, as a near-empty file
        if rc == 0 and size <= 40_000:
            why = f"only {size} bytes -- the page probably did not render"
        ok = rc == 0 and size > 40_000
        if not ok:
            failed.append(name)
        print(f"  {'ok  ' if ok else 'FAIL'} {name:<26} "
              f"{size/1024:7.0f} KB  {url}")
        if why:
            print(f"       {why}")

    print(f"\n{len(FIGURES) - len(failed)}/{len(FIGURES)} captured "
          f"-> writeup/figures/")
    if failed:
        print("failed: " + ", ".join(failed) +
              "\n(is the tool deployed and reachable?)")
        return 1
    print("Captions quote numbers visible inside these images. If the tool has "
          "changed, re-read them before submitting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
