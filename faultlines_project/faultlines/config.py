"""Config loading + the shared record schema.

Everything tunable lives in config.yaml. Import CFG from here, never re-read
the file elsewhere.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Windows consoles default to cp1252, which cannot encode most of this corpus:
# PopQA is full of entity names like "Wladyslaw Slawny" (U+0142) and
# "Marie Sklodowska Curie". A bare print() of such a name raises
# UnicodeEncodeError and KILLS THE PROCESS.
#
# This is not hypothetical. It happened twice on 2026-07-28 (ISSUES #30): once
# from inside an except block that was handling a rate limit -- so the process
# died AND the traceback blamed Unicode rather than throttling -- and once in an
# ad-hoc verification script. The first was patched at the call site with an
# ASCII-fold helper, which fixed that one print and left every other print in
# the project exposed.
#
# Fixing it here, where every entry point already imports, covers all of them:
# errors="replace" degrades an unencodable character to "?" instead of raising.
# Config, not cosmetics -- a logging call must never be able to end a run.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):        # not a real tty (pytest capture)
        pass


def load_env() -> None:
    """Read ROOT/.env into os.environ, so API keys live in a gitignored file
    instead of a machine-wide variable.

    setdefault, not assignment: a real environment variable OUTRANKS the file.
    That way a one-off `TOGETHER_API_KEY=... python -m ...` still works without
    editing anything, and CI never gets silently overridden by a stray .env.

    Six lines rather than a python-dotenv dependency -- the format this needs
    is KEY=value and nothing else. `.env` is already in .gitignore; keep it so.
    """
    # Home first, repo second. The repo lives under OneDrive\Desktop\..., so a
    # .env here is replicated to Microsoft's cloud and to every device on the
    # account -- .gitignore stops git exposure, not cloud sync. The home copy is
    # outside the synced tree; the repo copy stays supported so a fresh clone
    # still works.
    candidates = [pathlib.Path.home() / ".faultlines.env", ROOT / ".env"]
    for f in candidates:
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()


@functools.lru_cache(maxsize=1)
def load() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for key, rel in cfg["paths"].items():
        p = ROOT / rel
        p.mkdir(parents=True, exist_ok=True)
        cfg["paths"][key] = p
    return cfg


CFG = load()
SEED = CFG["seed"]


def seq(x) -> list:
    """Coerce a maybe-None, maybe-ndarray cell into a plain list.

    Parquet hands back numpy arrays for list columns, and `x or []` raises
    ValueError on those ("truth value of an array is ambiguous"). Every module
    reading aliases / incorrect_answers must go through this.
    """
    if x is None:
        return []
    try:
        return [] if len(x) == 0 else list(x)
    except TypeError:          # scalar
        return [x]


def path(kind: str, name: str) -> pathlib.Path:
    """path('interim', 'answers.parquet') -> ROOT/data/interim/answers.parquet"""
    return CFG["paths"][kind] / name


def stage(kind: str, base: str, pilot: bool = True, tag: str = "") -> pathlib.Path:
    """stage('interim', 'answers', pilot=True, tag='_gen3')
        -> data/interim/answers_pilot_gen3.parquet

    One place to build these names instead of eight. The tag is what keeps
    ensemble runs apart: without it every arm writes answers_pilot.parquet and
    the previous arm's results are destroyed in place -- and the local 7-9B
    results represent days of laptop GPU time that cannot be regenerated.
    A silently-wrong filename here reads or overwrites the wrong experiment,
    so it is worth having exactly one implementation.
    """
    return path(kind, f"{base}{'_pilot' if pilot else ''}{tag}.parquet")


# The record every stage appends to. Written down once, here, so the columns
# never drift between modules.
#
# Level 1  qid, dataset, question, gold, aliases, meta
# Level 2  + model, answer, confidence
# Level 3  + correct
# Level 4  + disagreement (one row per question, not per answer)
# Level 5  + x, y
# Level 9  + label            (hand-assigned error type)
QUESTION_COLS = ["qid", "dataset", "question", "gold", "aliases", "meta"]
ANSWER_COLS = QUESTION_COLS + ["model", "answer", "confidence", "correct"]
