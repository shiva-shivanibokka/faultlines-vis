"""Does an ENTITY-IDENTITY tier fix the band where similarity fails?

    python scripts/lookup_grader.py            # evaluate on the 430 hand labels
    python scripts/lookup_grader.py --pairs    # just the six diagnostic pairs

THE QUESTION
Similarity graders are inverted on the hard band: measured on the grading
encoder, "Bangladesh"/"People's Republic of Bangladesh" (RIGHT) scores 0.776 and
"York"/"New York City" (WRONG) scores 0.891. No threshold separates them, so the
failure is an ORDERING failure and cannot be tuned away.

The hypothesis is that identity is answerable by LOOKUP rather than by
resemblance: resolve both strings to a canonical Wikipedia title and ask whether
they are the same article. That is a fact about the world, which is exactly what
an embedding cannot see.

WHY THIS IS A TIER AND NOT A REPLACEMENT
Lookup only speaks about named entities. "You'll need to change dollars into
euros for Germany and kroner for Norway" has no canonical title, and asking for
one produces noise. So the tier fires only when BOTH strings look like entity
mentions, and everything else falls through to the existing ladder untouched.
A tier that abstains is worth more than one that guesses.

REPRODUCIBILITY
Wikipedia is live and can change. Every resolution is cached to
data/raw/lookup_cache.json with the date, so a rerun reproduces this run exactly
and the claim is "as resolved on <date>" rather than "as Wikipedia is today".
That is the same contract RQ4's retrieval cache already runs under.

NEVER CACHE A FAILURE -- standing rule 3, learned from ISSUES #29, where 497 of
566 poisoned cache entries produced a clean, wrong, and perfectly reproducible
null result three times running.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import path  # noqa: E402
from faultlines.grade import normalise  # noqa: E402

_API = "https://en.wikipedia.org/w/api.php"
_UA = {"User-Agent": "FaultLines-capstone/1.0 (M.S. research; SFSU)"}
MIN_INTERVAL = 1.2
_last = [0.0]
_CACHE: dict | None = None

# An entity mention is short and has no sentence machinery. Tuned to ABSTAIN
# rather than to catch: a false "same entity" silently marks a wrong answer
# correct, which is the direction that shrinks the Audit population and flatters
# the whole thesis (watch-list item 3).
MAX_WORDS = 6
_VERBS = (" is ", " are ", " was ", " were ", " need ", " will ", " would ",
          " have ", " has ", " can ", " should ", " because ", " which ")


def entity_like(s: str) -> bool:
    t = f" {normalise(s)} "
    return (0 < len(t.split()) <= MAX_WORDS
            and not any(v in t for v in _VERBS)
            and "," not in s and ";" not in s)


def _cache() -> dict:
    global _CACHE
    if _CACHE is None:
        p = path("raw", "lookup_cache.json")
        _CACHE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _CACHE


def _save() -> None:
    if _CACHE is not None:
        path("raw", "lookup_cache.json").write_text(
            json.dumps(_CACHE, ensure_ascii=False), encoding="utf-8")


def resolve(term: str) -> str | None:
    """Canonical Wikipedia title for `term`, or None if it cannot be resolved.

    None means ABSTAIN, and is never cached -- a network failure and a genuine
    no-such-article must not become the same permanent answer.
    """
    key = normalise(term)
    if not key:
        return None
    c = _cache()
    if key in c:
        return c[key]
    for attempt in range(3):
        wait = MIN_INTERVAL - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = requests.get(_API, headers=_UA, timeout=20, params={
                "action": "query", "format": "json", "redirects": 1,
                "titles": term, "prop": "info"})
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            for pid, pg in pages.items():
                if str(pid) != "-1" and "title" in pg:
                    c[key] = pg["title"]          # cache SUCCESS only
                    return c[key]
            c[key] = None                          # a real "no such article"
            return None
        except Exception:
            time.sleep(2.0 * (attempt + 1))
    return None                                    # transient: do NOT cache


def same_entity(a: str, b: str) -> bool | None:
    """True/False if the lookup can decide, None to abstain."""
    if not (entity_like(a) and entity_like(b)):
        return None
    ta, tb = resolve(a), resolve(b)
    if ta is None or tb is None:
        return None
    return normalise(ta) == normalise(tb)


PAIRS = [("Bangladesh", "People's Republic of Bangladesh", True),
         ("York", "New York City", False),
         ("China", "People's Republic of China", True),
         ("Sheppey", "Isle of Sheppey", True),
         ("Gene Kelly", "Fred Astaire", False),
         ("Eisenhower", "Carroll W. McColpin", False)]


def diagnostic() -> None:
    print(f"{'pair':<50} {'verdict':>8} {'truth':>7}  ok")
    ok = 0
    for a, b, truth in PAIRS:
        v = same_entity(a, b)
        hit = v is truth
        ok += hit
        print(f"{a + ' / ' + b:<50} {str(v):>8} {str(truth):>7}  {'YES' if hit else 'no'}")
    _save()
    print(f"\n{ok}/{len(PAIRS)} decided correctly")


def evaluate() -> None:
    h = pd.read_parquet(path("processed", "handlabels.parquet"))
    h = h[h.human.notna()].copy()
    print(f"{len(h)} hand-labelled verdicts  "
          f"({(h.stratum == 'target').sum()} hard / {(h.stratum == 'control').sum()} control)")

    applicable = h.apply(lambda r: entity_like(r.answer) and entity_like(r.gold), axis=1)
    print(f"entity-like on BOTH sides: {applicable.sum()} "
          f"({applicable.mean() * 100:.1f}%) -- the tier abstains on the rest\n")

    verdicts, n = [], 0
    for _, r in h[applicable].iterrows():
        v = same_entity(r.answer, r.gold)
        verdicts.append(v)
        n += 1
        if n % 25 == 0:
            _save()
            print(f"  ... {n}/{int(applicable.sum())}", flush=True)
    _save()

    sub = h[applicable].copy()
    sub["lookup"] = verdicts
    decided = sub[sub.lookup.notna()]
    print(f"\nlookup DECIDED {len(decided)} of {len(sub)} applicable "
          f"({len(decided) / max(len(sub), 1) * 100:.0f}%)\n")

    if len(decided):
        base = (decided.machine == decided.human).mean()
        new = (decided.lookup == decided.human).mean()
        print(f"On the cases the lookup decides (n={len(decided)}):")
        print(f"  similarity grader agrees with the human : {base * 100:5.1f}%")
        print(f"  lookup tier      agrees with the human  : {new * 100:5.1f}%")
        flips = decided[(decided.machine != decided.human) & (decided.lookup == decided.human)]
        breaks = decided[(decided.machine == decided.human) & (decided.lookup != decided.human)]
        print(f"\n  FIXED by lookup  : {len(flips)}")
        print(f"  BROKEN by lookup : {len(breaks)}")
        for _, r in flips.head(6).iterrows():
            print(f"    fixed  {r.qid:<18} {str(r.answer)[:34]!r:<38} vs {str(r.gold)[:34]!r}")
        for _, r in breaks.head(6).iterrows():
            print(f"    BROKE  {r.qid:<18} {str(r.answer)[:34]!r:<38} vs {str(r.gold)[:34]!r}")

    out = path("processed", "lookup_eval.parquet")
    sub.to_parquet(out)
    print(f"\n-> {out}")



def keyflags() -> None:
    """The population the tier is actually FOR: the 60 answer-key flags.

    These are the cases where every model gave a shorter form of the gold answer
    -- short, entity-shaped, and undecidable by every similarity method tested.
    The hand-label set does not test this tier at all (TruthfulQA answers are
    sentences: 9 of 341 were entity-like on both sides), so evaluating there
    measures nothing. This is where the claim lives or dies.
    """
    import json as _json
    d = _json.loads((Path(__file__).resolve().parents[2] /
                     "faultlines-tool" / "data.json").read_text(encoding="utf-8"))
    cases = [c for c in d["cases"] if c.get("keyflag")]
    print(f"{len(cases)} answer-key-flagged cases\n")
    dec = same = diff = abst = 0
    rows = []
    for c in cases:
        ans = (c.get("new") or c.get("old") or [{}])[0].get("a", "")
        v = same_entity(ans, c["gold"])
        rows.append({"qid": c["qid"], "answer": ans, "gold": c["gold"], "same": v})
        if v is None:
            abst += 1
        else:
            dec += 1
            same += bool(v)
            diff += (not v)
        if (dec + abst) % 20 == 0:
            _save()
    _save()
    print(f"decided {dec}/{len(cases)} ({dec/max(len(cases),1)*100:.0f}%) · abstained {abst}")
    print(f"  SAME entity -> the model was right, the key was too strict : {same}")
    print(f"  DIFFERENT   -> the model really was wrong                  : {diff}\n")
    for r in rows:
        tag = {True: "SAME     ", False: "DIFFERENT", None: "abstain  "}[r["same"]]
        print(f"  {tag} {str(r['answer'])[:30]!r:<34} vs {str(r['gold'])[:40]!r}")
    pd.DataFrame(rows).to_parquet(path("processed", "lookup_keyflags.parquet"))



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", action="store_true", help="just the six diagnostic pairs")
    ap.add_argument("--keyflags", action="store_true",
                    help="the 60 answer-key flags -- the population this tier is FOR")
    a = ap.parse_args()
    if a.pairs:
        diagnostic()
    elif a.keyflags:
        keyflags()
    else:
        evaluate()
