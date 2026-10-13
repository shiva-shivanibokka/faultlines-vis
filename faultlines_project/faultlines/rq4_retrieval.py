"""RQ4 - the retrieval dissociation.

Predicts that retrieval FIXES obscurity and staleness errors (a document supplies
the missing fact) but NOT shared misconceptions (retrieval draws from the same web
that taught the misconception). Obscurity is the positive control: retrieval must
work there, or a null on misconceptions is uninterpretable.

    python -m faultlines.rq4_retrieval --pilot --limit 8   # small live test
    python -m faultlines.rq4_retrieval --pilot             # full

Retrieval backend = the MediaWiki API (no local corpus, cached to disk).
"""
from __future__ import annotations

import argparse
import json
import re
import threading
import time

import pandas as pd
import requests

from faultlines import grade, nli
from faultlines.config import CFG, path, seq, stage
from faultlines.generate import ask_retry

_WIKI = "https://en.wikipedia.org/w/api.php"
_UA = {"User-Agent": "FaultLines-capstone/1.0 (M.S. research; SFSU)"}
_CACHE = None


def _cache_path():
    return path("raw", "retrieval_cache.json")


def _load_cache() -> dict:
    global _CACHE
    if _CACHE is None:
        p = _cache_path()
        _CACHE = json.loads(p.read_text()) if p.exists() else {}
    return _CACHE


def _save_cache() -> None:
    if _CACHE is not None:
        _cache_path().write_text(json.dumps(_CACHE))


RETR_RETRIES = 4
RETR_BACKOFF = 2.0
MIN_INTERVAL = 1.5          # seconds between MediaWiki calls, process-wide
_last_call = [0.0]
_throttle_lock = threading.Lock()
# When MediaWiki says 429, EVERY thread has to stop, not just the one that was
# told. A fixed interval assumes we know the limit; a cooldown lets the server
# tell us. Without this, four workers keep hammering while one backs off, so the
# limit is never actually respected and the retries themselves keep it tripped.
_cooldown_until = [0.0]


def note_429() -> None:
    with _throttle_lock:
        _cooldown_until[0] = max(_cooldown_until[0], time.time() + 20.0)

# Chars kept per passage. Measured 2026-07-28 on 50 obscurity cases, gold answer
# present in context: 600 -> 66%, 2000 -> 68%, full text at 3000 -> 70%. Length
# is NOT the binding constraint; ~70% is simply the ceiling for Wikipedia intros
# on the rarest PopQA entities, because some answers live only in an infobox.
# 2000 is the knee: +2 points over 600, bounded, still one lead section.
PASSAGE_CHARS = 2000


def _throttle() -> None:
    """One request per second, enforced globally.

    MediaWiki's anonymous limit is roughly this, and the previous version blew
    through it: it issued 1 search + up to 3 extract calls PER CASE with a single
    0.2s sleep after all four, i.e. ~2,280 requests for a 570-case sweep at ~5/s.
    That is what produced the 429s that got cached as empty results (#29).

    LOCKED as of 2026-08-01, when rq5_agentic began calling this from a thread
    pool. Unlocked, N threads each read the same _last_call, each compute the
    same "no wait needed", and all fire at once -- the exact burst pattern of
    #29b, reintroduced by a caller rather than by this function. A global rate
    limit that is not mutually excluded is not a rate limit.
    """
    while True:
        with _throttle_lock:
            now = time.time()
            cool = _cooldown_until[0] - now
            if cool <= 0:
                wait = MIN_INTERVAL - (now - _last_call[0])
                if wait <= 0:
                    _last_call[0] = now
                    return
                break
        time.sleep(min(cool, 5.0) if cool > 0 else 0.05)
    time.sleep(max(wait, 0))
    with _throttle_lock:
        _last_call[0] = time.time()


def _safe(s: str) -> str:
    """ASCII-safe for the Windows console.

    The retry logging crashed the entire RQ4 run on 'Wladyslaw Slawny' --
    cp1252 cannot encode U+0142 and print() raised UnicodeEncodeError from
    INSIDE the except block that was handling a 429. An error handler that
    cannot report its error takes the process down with it, and the failure it
    reports is not even the real one. PopQA is full of non-ASCII entity names,
    so this was certain to fire, not unlucky.
    """
    return s.encode("ascii", "replace").decode("ascii")


# PopQA is 15 fixed templates over (entity, relation). Searching the WHOLE
# question is passage search, not entity linking, and on entity questions it
# retrieves topically-adjacent noise: "Who was the screenwriter for The City?"
# returned ['Doctor Who', 'Don Roos', 'Brian Gunn']. Measured on the first clean
# run: the gold answer appeared in only 8% of retrieved contexts, so the
# obscurity arm was scoring the model's ability to use passages that did not
# contain the answer. Pulling the entity out and searching for THAT is the
# difference between a retriever and a keyword match.
# DERIVED from the data, not written from memory. The first version guessed and
# got 92.1% -- it had "who WAS the father of" where PopQA says "who IS the father
# of" (749 questions), and lacked "What is {} the capital of?" entirely (255),
# which is the reverse-direction template asking for the country given the city.
# Regenerate with:
#   t = pd.read_parquet('data/interim/popqa_wiki_titles.parquet')
#   t.apply(lambda r: r.question.replace(r.subj, '{}'), axis=1).value_counts()
_TEMPLATES = [
    re.compile(p, re.IGNORECASE) for p in (
        r"^what is (.+?)'s occupation\?$",
        r"^what is (.+?) the capital of\?$",          # reverse direction
        r"^who was the (?:composer|producer|director) of (.+?)\?$",
        r"^who is the (?:author|father|mother) of (.+?)\?$",
        r"^who was the screenwriter for (.+?)\?$",
        r"^in what city was (.+?) born\?$",
        r"^what genre is (.+?)\?$",
        r"^what is the religion of (.+?)\?$",
        r"^in what country is (.+?)\?$",
        r"^what sport does (.+?) play\?$",
        r"^what color is (.+?)\?$",
        r"^what is the capital of (.+?)\?$",
    )
]


def entity_of(question: str) -> str | None:
    """The subject entity of a PopQA template question, or None if no match."""
    for pat in _TEMPLATES:
        m = pat.match(question.strip())
        if m:
            return m.group(1).strip()
    return None


_TITLES: dict[str, str] | None = None


def wiki_title_of(question: str) -> str | None:
    """PopQA's own canonical article title for the question's subject, if known.

    Built by scripts/fetch_popqa_titles.py. Returns None for TruthfulQA and for
    any question not in the map, which correctly falls back to search.
    """
    global _TITLES
    if _TITLES is None:
        p = path("interim", "popqa_wiki_titles.parquet")
        if p.exists():
            t = pd.read_parquet(p)
            _TITLES = dict(zip(t["question"], t["s_wiki_title"]))
        else:
            _TITLES = {}
    return _TITLES.get(question) or None


def _wiki_cached(key: str, params: dict, label: str) -> list[str]:
    """One MediaWiki request: throttled, retried, cached ONLY on success.

    THE single implementation. `retrieve()` and `retrieve_title()` each carried
    their own copy of this loop, written within an hour of each other -- which is
    exactly defect #20's shape: a shared behaviour duplicated, so a later fix
    lands in one copy and the two silently disagree. The rule that matters most
    here (a failure is never cached, #29) is the one that must not drift.

    Both endpoints return the same `query.pages` shape, so the parsing is shared
    too rather than duplicated alongside the retry.
    """
    cache = _load_cache()
    if key in cache:
        return cache[key]
    for attempt in range(RETR_RETRIES):
        try:
            _throttle()
            r = requests.get(_WIKI, params=params, headers=_UA, timeout=30)
            if r.status_code == 429:
                note_429()          # stop ALL threads, not just this one
                raise requests.HTTPError("429 rate limited", response=r)
            r.raise_for_status()
            out = [txt[:PASSAGE_CHARS]
                   for pg in r.json().get("query", {}).get("pages", {}).values()
                   if (txt := (pg.get("extract") or "").strip())]
            cache[key] = out                    # only a SUCCESSFUL lookup is cached
            _save_cache()
            return out
        except Exception as exc:                # noqa: BLE001
            if attempt == RETR_RETRIES - 1:
                print(f"  !! {label} failed after {RETR_RETRIES}: "
                      f"{_safe(str(exc)[:60])}", flush=True)
                return []                       # NOT cached -- retry next run
            time.sleep(RETR_BACKOFF * (2 ** attempt))
    return []


def retrieve_title(title: str) -> list[str]:
    """Intro extract for an EXACT article title. No search step.

    This is the difference between a retriever and a keyword match. Wikipedia
    search on an obscure PopQA subject returns topically-adjacent noise --
    "Who is the author of The Lie?" retrieved an article about a 2014 film
    called The Good Lie, and the gold answer was present in only 8% of contexts.
    A titled lookup asks for the subject's own article and nothing else.
    """
    return _wiki_cached(f"T::{title}",
                        {"action": "query", "prop": "extracts", "exintro": 1,
                         "explaintext": 1, "redirects": 1, "titles": title,
                         "format": "json"},
                        f"title lookup {_safe(title[:40])}")


def retrieve(query: str, k: int = 3) -> list[str]:
    """Top-k Wikipedia intro snippets for the query. Cached; [] means a TRUE miss.

    Retried, and a FAILURE IS NEVER CACHED. The first version swallowed every
    exception into `out = []` and then wrote that empty list to the cache
    alongside genuine no-results, making the two indistinguishable forever.

    Measured on the first full RQ4 run (2026-07-28): **497 of 566 cache entries
    (88%) were empty, and 19 of 20 sampled returned results on retry.** MediaWiki
    throttled a 570-case sweep, every throttled call was cached as "nothing
    found", and the experiment reported that retrieval does not help obscure
    entities -- when retrieval had simply not run. The positive control failed
    silently and read as a finding.

    Same defect family as #23/#25: a failed call recorded as a result. Third
    place it appeared, and the first outside the model-calling path.
    """
    # ONE request per case, not four: generator=search feeds the search hits
    # straight into prop=extracts. Same data, a quarter of the traffic, and it
    # is the traffic volume that caused #29.
    return _wiki_cached(f"{k}::{query}",
                        {"action": "query", "generator": "search",
                         "gsrsearch": query, "gsrlimit": k, "prop": "extracts",
                         "exintro": 1, "explaintext": 1, "exlimit": "max",
                         "format": "json"},
                        f"retrieval {_safe(query[:40])}")



def context_question(question: str, contexts: list[str]) -> str:
    """Fold retrieved context into the question passed to ask()."""
    if not contexts:
        return question
    ctx = "\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(contexts))
    return f"Use these reference passages to answer.\n\n{ctx}\n\nQuestion: {question}"


def strata(records: pd.DataFrame, answers: pd.DataFrame) -> pd.DataFrame:
    """Select error cases by cause. Obscurity = PopQA majority_wrong (low popularity
    first); misconception = TruthfulQA majority_wrong. Returns one row per (qid) with
    gold/aliases/meta/dataset and a `cause` label."""
    def pop(m):
        return float(m["s_pop"]) if isinstance(m, dict) and m.get("s_pop") is not None else 1e12
    errs = records[records["majority_wrong"]].copy()
    obsc = errs[errs["dataset"] == "popqa"].copy()
    obsc["cause"] = "obscurity"
    obsc["_sort"] = obsc["meta"].map(pop)
    obsc = obsc.sort_values("_sort")  # rarest first
    misc = errs[errs["dataset"] == "truthfulqa"].copy()
    misc["cause"] = "misconception"
    cols = ["qid", "dataset", "question", "gold", "meta", "cause"]
    out = pd.concat([obsc[cols], misc[cols]], ignore_index=True)
    # attach aliases (records dropped them; pull from answers)
    al = answers.drop_duplicates("qid").set_index("qid")["aliases"]
    out["aliases"] = out["qid"].map(al)
    return out


def _grade(answer: str, row) -> bool:
    if row["dataset"] == "truthfulqa":
        meta = row["meta"] if isinstance(row["meta"], dict) else {}
        ok, _, _ = nli.grade_truthful(answer, seq(row["aliases"]), seq(meta.get("incorrect")))
        return ok
    return grade.grade_one(answer, row["gold"], seq(row["aliases"]), row["dataset"])[0]


def run(pilot: bool = True, limit: int | None = None,
        model: str | None = None) -> pd.DataFrame:
    sfx = "_pilot" if pilot else ""
    records = pd.read_parquet(path("processed", f"records{sfx}.parquet"))
    answers = pd.read_parquet(path("interim", f"answers{sfx}.parquet"))
    cases = strata(records, answers)
    if limit is not None:
        # balance the small test across strata
        cases = pd.concat([cases[cases.cause == c].head(limit // 2)
                           for c in ("obscurity", "misconception")], ignore_index=True)
    # Explicit, not positional: keying off ensemble[0] means reordering the
    # ensemble in config silently changes which model this experiment used.
    model = model or CFG["ensemble"][0]["name"]
    print(f"retrieval model: {model}")

    # Results are WRITTEN, not just printed. This loop makes two live calls per
    # case; printing a summary and dropping the rows meant every rerun paid for
    # the generations again, and the per-case answers -- which are what a human
    # actually inspects when the lift looks wrong -- were unrecoverable.
    dest = stage("processed", "rq4_retrieval", pilot, "")
    rows: list[dict] = []
    if dest.exists():                                   # resume
        prev = pd.read_parquet(dest)
        # An empty answer on EITHER arm is a failed call, not a result -- same
        # rule as generate/baseline/screen resume.
        ok = (prev["answer_cb"].fillna("").str.strip() != "") & \
             (prev["answer_rag"].fillna("").str.strip() != "")
        rows = prev[ok].to_dict("records")
        print(f"resuming: {len(rows)} cases on disk"
              + (f"; redoing {int((~ok).sum())} failed" if (~ok).any() else ""))
    # Only rows that are still in the selection count. The strata are chosen
    # from records.parquet, which changed when duplicates were removed and the
    # majority tie rule was fixed (ISSUES #66, #67): a row for a question that
    # is no longer selected is a result for a different experiment.
    wanted = set(cases["qid"])
    stale = sum(1 for r in rows if r["qid"] not in wanted)
    if stale:
        print(f"dropping {stale} rows no longer in the selection")
    rows = [r for r in rows if r["qid"] in wanted]
    done = {r["qid"] for r in rows}
    cases = cases[~cases["qid"].isin(done)]

    for n, (_, r) in enumerate(cases.iterrows(), 1):
        # Retrieval ladder, strongest first:
        #   1. PopQA's own s_wiki_title  -> exact article, no search
        #   2. entity name from the template -> search, but for the subject only
        #   3. the whole question -> passage search (correct for TruthfulQA,
        #      which is not templated and asks about general topics)
        title = wiki_title_of(r["question"])
        ctx = retrieve_title(title) if title else []
        if not ctx and (ent := entity_of(r["question"])):
            ctx = retrieve(ent)
        if not ctx:
            ctx = retrieve(r["question"])
        # SAME model, both arms — the only variable is the retrieved context,
        # so the delta is a clean measure of what retrieval fixes.
        #
        # Retried, and retried SEPARATELY. One try/except used to wrap both
        # calls: a failure on the retrieval arm discarded the closed-book answer
        # that had already succeeded, and set BOTH to "". Two empty answers grade
        # wrong-and-identical, so a transient 429 registered as "retrieval
        # changed nothing" -- precisely the null result this experiment is
        # testing for, manufactured by the harness.
        cb, _ = ask_retry(model, r["question"], dataset=r["dataset"], label=r["qid"])
        rag, _ = ask_retry(model, context_question(r["question"], ctx),
                           dataset=r["dataset"], label=r["qid"])
        rows.append({"qid": r["qid"], "cause": r["cause"], "n_ctx": len(ctx),
                     "closedbook_ok": _grade(cb, r), "retrieved_ok": _grade(rag, r),
                     "answer_cb": cb, "answer_rag": rag})
        if n % 25 == 0 or n == len(cases):
            pd.DataFrame(rows).to_parquet(dest)
            print(f"  {n}/{len(cases)}", flush=True)
    res = pd.DataFrame(rows)
    res.to_parquet(dest)
    print(f"-> {dest.name}  ({len(res)} cases)")

    print("=" * 64)
    print("RQ4  DOES RETRIEVAL FIX THE ERROR?  (same model, closed-book vs retrieval)")
    print("=" * 64)
    for cause in ("obscurity", "misconception"):
        s = res[res["cause"] == cause]
        if len(s):
            cb = s["closedbook_ok"].mean(); rag = s["retrieved_ok"].mean()
            print(f"  {cause:14s} n={len(s):3d}  closed-book {cb:.0%} -> retrieval {rag:.0%}  "
                  f"(lift {rag - cb:+.0%}, avg {s['n_ctx'].mean():.1f} passages)")
    print("  prediction: obscurity lift HIGH (positive control), misconception lift ~0")

    out = path("processed", f"rq4_retrieval{sfx}.parquet")
    res.to_parquet(out)
    print(f"\nwrote {out.name}  ({len(res)} rows)")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", default=True)
    ap.add_argument("--full", dest="pilot", action="store_false")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    run(a.pilot, a.limit)
