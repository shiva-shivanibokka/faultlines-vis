#!/usr/bin/env python
"""Assemble the eight chapters into one PDF for reading end to end.

    python scripts/build_thesis.py            # -> writeup/FaultLines_thesis.pdf
    python scripts/build_thesis.py --html     # stop at the HTML, do not print

WHAT THIS IS FOR, AND WHAT IT IS NOT

It builds a **complete reading copy**: title page, abstract, acknowledgements,
contents, list of figures, eight chapters, and a verified reference list, with
page numbers throughout.

It is still NOT a submission artifact, and the distinction is narrower than it
used to be, which makes it easier to get wrong. What is here now: front matter,
a bibliography, and figures. What is still NOT here, and what only the university
can settle:

  * the **signature / approval page**, whose exact wording and signatory list
    come from the SFSU Graduate Division template, not from a guess;
  * the required **margins, line spacing and font**, which the template
    specifies and which the CSS below does not claim to match;
  * the **citation style** the department requires. The reference list is
    complete and verified but formatted in an author-date style close to APA;
    if the department wants IEEE numeric, only the rendering changes.

Check the current SFSU template before submitting. This file will render a
handsome document that is still the wrong shape if the template disagrees.

HOW

`markdown` renders each chapter; the pieces are wrapped in one HTML document with
print CSS; Chrome prints it headlessly. Chrome is used rather than a Python PDF
library because it is already on the machine, it handles the CSS paged-media
properties that put page numbers in the footer, and its rendering is the one the
author can preview by opening the same HTML in a browser.

THE ONE THING WORTH KNOWING

The word counts on the cover come from the same place `check_writeup.py` reads,
so a cover that says 31,990 words is derived rather than typed. This file has no
literal figures in it at all -- see ISSUES #43-#49 for why that rule exists.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRITEUP = ROOT / "writeup"
SUMMARY = ROOT / "faultlines-web" / "summary.json"

FRONT = "00-front-matter.md"

CHAPTERS = [
    ("ch1-introduction.md", "Introduction"),
    ("ch2-related-work.md", "Related Work"),
    ("ch3-design.md", "Design"),
    ("ch4-method.md", "Method"),
    ("ch5-results.md", "Results"),
    ("ch6-evaluation.md", "Evaluation"),
    ("ch7-limitations.md", "Limitations"),
    ("ch8-conclusion.md", "Conclusion"),
    ("ch9-references.md", "References"),
]

CSS = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm;
        @bottom-center { content: counter(page); font: 9pt Georgia, serif;
                         color: #666; } }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10.5pt/1.62 Georgia, 'Times New Roman', serif; color: #16181d;
       margin: 0; }
h1, h2, h3, h4 { font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
                 line-height: 1.25; color: #0f1115; text-wrap: balance; }
h1 { font-size: 21pt; margin: 0 0 4pt; page-break-before: always;
     border-bottom: 2px solid #0f1115; padding-bottom: 6pt; }
h1.nobreak { page-break-before: avoid; }
h2 { font-size: 13pt; margin: 20pt 0 5pt; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 14pt 0 4pt; page-break-after: avoid;
     color: #2a2f3a; }
h4 { font-size: 10pt; margin: 11pt 0 3pt; page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
p { margin: 0 0 7pt; }
ul, ol { margin: 0 0 8pt; padding-left: 17pt; }
li { margin-bottom: 2.5pt; }
code { font: 9pt 'Consolas', 'Courier New', monospace; background: #f4f5f7;
       padding: 0.5pt 3pt; border-radius: 2.5pt; }
pre { background: #f7f8fa; border-left: 2.5pt solid #c8ccd4; padding: 7pt 10pt;
      overflow-x: auto; page-break-inside: avoid; margin: 0 0 9pt; }
pre code { background: none; padding: 0; font-size: 8.5pt; line-height: 1.45; }
blockquote { margin: 9pt 0; padding: 6pt 12pt; border-left: 3pt solid #4a5568;
             background: #f7f8fa; page-break-inside: avoid; }
blockquote p:last-child { margin-bottom: 0; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 11pt;
        font-size: 8.8pt; page-break-inside: avoid; }
th, td { border: 0.5pt solid #ccd0d8; padding: 3.5pt 6pt; text-align: left;
         vertical-align: top; }
th { background: #eef0f4; font-family: 'Segoe UI', Helvetica, sans-serif;
     font-weight: 600; font-size: 8.4pt; }
tr:nth-child(even) td { background: #fafbfc; }
hr { border: 0; border-top: 0.5pt solid #d8dbe2; margin: 14pt 0; }
em { color: #33383f; }

/* figures -- a screenshot that breaks across a page break is unreadable, and a
   caption separated from its figure is worse than no caption */
p > img { display: block; max-width: 100%; height: auto; margin: 4pt auto 3pt;
          border: 0.5pt solid #ccd0d8; border-radius: 2pt; }
p:has(> img) { page-break-inside: avoid; page-break-after: avoid; margin-bottom: 2pt; }
p:has(> img) + p { page-break-before: avoid; font-size: 9pt; line-height: 1.5;
                   color: #33383f; padding: 0 6mm; margin-bottom: 12pt; }

/* cover */
.cover { page-break-after: always; padding-top: 34mm; text-align: center; }
.cover .t { font: 700 30pt/1.15 'Segoe UI', Helvetica, sans-serif;
            letter-spacing: -0.5pt; margin-bottom: 5pt; }
.cover .deg { margin-top: 30mm; font: 11pt/1.85 Georgia, serif; color: #2a2f3a; }
.front h1 { page-break-before: always; }
.lof { page-break-before: always; }
.lof td { border: 0; padding: 4pt 6pt; border-bottom: 0.5pt dotted #ccd0d8;
          vertical-align: top; }
.lof .n { width: 20mm; color: #666; font-family: 'Segoe UI', sans-serif;
          white-space: nowrap; }
.cover .s { font: 13pt/1.4 Georgia, serif; color: #444; margin-bottom: 34pt; }
.cover .who { font: 11.5pt/1.75 Georgia, serif; }
.cover .meta { margin-top: 40mm; font: 9pt/1.7 'Segoe UI', Helvetica, sans-serif;
               color: #666; }
.cover .warn { margin: 26pt auto 0; max-width: 116mm; font: 9pt/1.55 'Segoe UI',
               Helvetica, sans-serif; color: #8a5a12; background: #fdf6e7;
               border: 0.5pt solid #e8d9b0; padding: 8pt 11pt; text-align: left; }

/* contents */
.toc { page-break-after: always; }
.toc h1 { page-break-before: avoid; }
.toc table { font-size: 10pt; }
.toc td { border: 0; padding: 4pt 6pt; border-bottom: 0.5pt dotted #ccd0d8; }
.toc .n { width: 12mm; color: #666; font-family: 'Segoe UI', sans-serif; }
.toc .w { width: 30mm; text-align: right; color: #666; font-size: 8.5pt; }
"""


def cover(meta: dict) -> str:
    w = meta["words"]
    tgt = meta["target"]
    return f"""<div class="cover">
  <div class="t">FaultLines</div>
  <div class="s">Where several language models agree &mdash; and all get it wrong</div>
  <div class="who">
    <b>Shivani Bokka</b><br>
    M.S. Data Science &amp; Artificial Intelligence<br>
    San Francisco State University<br>
    <span style="color:#555">Advisor: Dr. Shahrukh Humayoun &middot; VI-Lab</span>
  </div>
  <div class="deg">
    A thesis submitted in partial fulfillment of the requirements<br>
    for the degree of Master of Science in Data Science and Artificial Intelligence<br>
    at San Francisco State University
  </div>
  <div class="warn"><b>Reading copy.</b>
    {meta['drafted']} of {meta['total']} chapters, {w:,} of ~{tgt:,} words, with
    front matter, figures and a verified reference list. <b>Still to apply before
    submission:</b> the SFSU signature/approval page, and the template's required
    margins, spacing and citation style &mdash; see the note at the top of
    <code>scripts/build_thesis.py</code>. Every numerical figure in these chapters
    is machine-checked against the exported records by
    <code>scripts/check_writeup.py</code>.</div>
  <div class="meta">Generated by <code>scripts/build_thesis.py</code></div>
</div>"""


def toc(meta: dict) -> str:
    by_n = {c["n"]: c for c in meta["chapters"]}
    rows = []
    for i, (_f, title) in enumerate(CHAPTERS, 1):
        c = by_n.get(str(i), {})
        words = c.get("words")
        rows.append(
            f'<tr><td class="n">{i}</td><td>{title}</td>'
            f'<td class="w">{words:,} words</td></tr>' if words else
            f'<tr><td class="n">{i}</td><td>{title}</td><td class="w"></td></tr>')
    return ('<div class="toc"><h1 class="nobreak">Contents</h1><table>'
            + "".join(rows) + "</table></div>")


# A caption often wraps, so the body must be allowed to cross newlines -- the
# first version used `.` without DOTALL and silently found 5 of 7. It reported
# the count, which is the only reason that was caught: a derived number that is
# printed is a number that gets checked.
FIG_RE = re.compile(r"^\*\*(Figure\s+([0-9]+\.[0-9]+))\s*[—-]\s*([\s\S]+?)\*\*",
                    re.MULTILINE)


def list_of_figures(rows: list) -> str:
    """Built by scanning the captions, so it cannot drift from the chapters.

    A hand-maintained list of figures is the same defect class as a
    hand-maintained claims table -- see ISSUES #63 and standing rule 7."""
    if not rows:
        return ""
    body = "".join(
        f'<tr><td class="n">{num}</td><td>{cap}</td></tr>' for num, cap in rows)
    return ('<div class="lof"><h1 class="nobreak">Figures</h1>'
            f'<table>{body}</table></div>')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="store_true", help="stop at the HTML")
    ap.add_argument("--out", default="FaultLines_thesis")
    a = ap.parse_args()

    try:
        import markdown
    except ImportError:
        print("needs `pip install markdown` in the project venv")
        return 1

    meta = json.loads(SUMMARY.read_text(encoding="utf-8"))["writeup"]

    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists",
                                       "attr_list"])
    front = WRITEUP / FRONT
    front_html = ""
    if front.exists():
        md.reset()
        front_html = ('<div class="front">'
                      + md.convert(front.read_text(encoding="utf-8"))
                      + "</div>")

    figs: list = []
    body: list = []
    missing = []
    for fname, _title in CHAPTERS:
        p = WRITEUP / fname
        if not p.exists():
            missing.append(fname)
            continue
        raw = p.read_text(encoding="utf-8")
        for _full, num, cap in FIG_RE.findall(raw):
            # the caption's first sentence is the entry; the rest is the gloss
            short = " ".join(cap.split()).split(". ")[0].rstrip(".")
            figs.append((num, short))
        md.reset()
        body.append(md.convert(raw))
    parts = [cover(meta), front_html, toc(meta), list_of_figures(figs)] + body
    if missing:
        print("missing: " + ", ".join(missing))
        return 1

    html = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>FaultLines</title><style>{CSS}</style></head>"
            f"<body>{''.join(parts)}</body></html>")

    absent = [m for m in re.findall(r'src="(figures/[^"]+)"', html)
              if not (WRITEUP / m).exists()]
    if absent:
        print(f"!! {len(absent)} figure(s) missing -- the PDF will show "
              f"broken images.")
        print("   run: python scripts/capture_figures.py")

    html_path = WRITEUP / f"{a.out}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"-> {html_path.name}   {len(html)/1024:.0f} KB   "
          f"{meta['words']:,} words   {len(figs)} figures"
          f"{'   + front matter' if front_html else '   NO FRONT MATTER'}")
    if a.html:
        return 0

    chrome = next((p for p in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ) if Path(p).exists()), shutil.which("chrome") or shutil.which("chromium"))
    if not chrome:
        print("Chrome not found. The HTML is written -- open it and print to PDF.")
        return 0

    pdf = WRITEUP / f"{a.out}.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([
            chrome, "--headless", "--disable-gpu", "--no-sandbox",
            f"--user-data-dir={tmp}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf}", html_path.as_uri(),
        ], capture_output=True, text=True, timeout=180)
    if not pdf.exists():
        print("Chrome did not produce a PDF:\n" + (r.stderr or "")[-600:])
        return 1
    print(f"-> {pdf.name}   {pdf.stat().st_size/1024/1024:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
