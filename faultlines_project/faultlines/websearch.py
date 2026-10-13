"""Open-web search, as a second tool arm for RQ5.

Wikipedia is a curated encyclopedia. The open web is where shared misconceptions
actually come from -- which is the mechanism RQ4 proposed but could not test:

    "retrieval draws from the same web that taught the misconception"

RQ4 only ever handed models Wikipedia passages, so that sentence was an
explanation, not a measurement. Running the same agent over open web results
tests it directly. The interesting outcome is not "web is better" -- it is
whether web search helps OBSCURITY (where more sources should mean more
coverage) while doing nothing for MISCONCEPTION (where more sources means more
copies of the same wrong belief).

WHY THIS IS AN API AND NO LONGER A SCRAPER
The first version parsed DuckDuckGo's HTML results page. It worked in testing and
then, ~40 questions into the real run, DuckDuckGo blackholed the IP entirely --
ConnectTimeout on every DDG host while Wikipedia and Bing still answered 200.
Every search after that returned "(the tool failed)", and the models kept
answering anyway, so the run was quietly recording model behaviour under a broken
tool. That is EXACTLY the RQ4 failure mode (ISSUES #28-30), reproduced by me, in
the arm built to demonstrate the lesson had been learnt.

Two things follow, and both are load-bearing:
  1. Use an interface with a contract. A provider that publishes a rate limit can
     be respected; a scraper can only be tolerated until it is not.
  2. The health gate has to fire DURING the run, not in the summary at the end.
     `_health` is exported for exactly this.

Swapping the scraper for an API also fixes the reproducibility story: a keyed
endpoint returns stable, documented results, where the HTML page could change
shape without notice.

CACHING
Search results change daily, so an uncached run is not reproducible even in
principle. Every query is cached under its provider. Failures are NEVER cached --
standing rule 3, and the reason RQ4 took four attempts. A cached empty list means
"this provider genuinely returned nothing"; a failure means "ask again".
"""
from __future__ import annotations

import json
import os
import threading
import time

import requests

from faultlines.config import path

# provider -> (env var holding the key, endpoint, how to send the key)
# Only providers with a published free/research tier and a documented rate limit.
PROVIDERS = {
    "tavily": {
        "env": "TAVILY_API_KEY",
        "url": "https://api.tavily.com/search",
        "note": "Search built for agents. 1,000 free credits/mo. tavily.com",
    },
    "serper": {
        "env": "SERPER_API_KEY",
        "url": "https://google.serper.dev/search",
        "note": "Google results. 2,500 free queries, no card. serper.dev",
    },
    "brave": {
        "env": "BRAVE_API_KEY",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "note": "Independent index. Free tier 1 q/s. brave.com/search/api",
    },
}

MIN_INTERVAL = 1.1      # under Brave's documented 1 q/s free-tier limit
RETRIES = 3
BACKOFF = 3.0

# Hard ceiling on billable searches. Cache hits are free and do not count.
#
# Running out of credits mid-run is the most likely failure here, and it fails
# the WORST way: the provider starts refusing, the models keep answering, and the
# tail of the run silently becomes "models without a tool" mixed into the same
# table as "models with a tool". That is the DuckDuckGo episode with a bill
# attached. Stopping at a number we chose is strictly better than stopping at a
# number the provider chose.
MAX_CALLS = int(os.environ.get("FAULTLINES_SEARCH_BUDGET", "900"))

_lock = threading.Lock()
_last = [0.0]
_cool = [0.0]
_CACHE: dict | None = None

# Exported so the caller can gate DURING the run. The DDG episode recorded 40
# questions' worth of answers against a dead tool before anything noticed.
_health = {"calls": 0, "failed": 0, "empty": 0}


def provider() -> str | None:
    """Which provider has a key present? None means the arm cannot run.

    Deliberately returns None rather than falling back to scraping. A silent
    downgrade to a source that can be blocked mid-run is the whole bug above.
    """
    for name, spec in PROVIDERS.items():
        if os.environ.get(spec["env"], "").strip():
            return name
    return None


def _cache() -> dict:
    global _CACHE
    if _CACHE is None:
        p = path("raw", "websearch_cache.json")
        _CACHE = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _CACHE


def _save() -> None:
    if _CACHE is not None:
        path("raw", "websearch_cache.json").write_text(
            json.dumps(_CACHE, ensure_ascii=False), encoding="utf-8")


def _throttle() -> None:
    """Global spacing plus a server-driven cooldown.

    Same shape as the Wikipedia limiter. The cooldown exists because a fixed
    interval assumes you know the limit; letting the server tell you is what took
    Wikipedia refusals from 23 in two minutes to zero.
    """
    while True:
        with _lock:
            now = time.time()
            cool = _cool[0] - now
            if cool <= 0:
                wait = MIN_INTERVAL - (now - _last[0])
                if wait <= 0:
                    _last[0] = now
                    return
                break
        time.sleep(min(cool, 5.0))
    time.sleep(max(wait, 0))
    with _lock:
        _last[0] = time.time()


def _request(name: str, query: str, k: int) -> list[str]:
    spec = PROVIDERS[name]
    key = os.environ[spec["env"]].strip()
    if name == "tavily":
        r = requests.post(spec["url"], timeout=25,
                          headers={"Authorization": f"Bearer {key}",
                                   "Content-Type": "application/json"},
                          # include_answer=False IS THE EXPERIMENT.
                          # Tavily will happily return an LLM-written answer to
                          # the question. Passing that to the model would measure
                          # "does another model's answer help", not "does the open
                          # web help" -- and on a question all four models got
                          # wrong, handing them a fifth model's answer is a
                          # different study with a much weaker claim.
                          # search_depth=basic keeps it 1 credit and keeps the
                          # tool comparable to a plain search.
                          json={"query": query, "max_results": k,
                                "include_answer": False,
                                "search_depth": "basic"})
    elif name == "serper":
        r = requests.post(spec["url"], timeout=25,
                          headers={"X-API-KEY": key,
                                   "Content-Type": "application/json"},
                          json={"q": query, "num": k})
    else:                                          # brave
        r = requests.get(spec["url"], timeout=25,
                         headers={"X-Subscription-Token": key,
                                  "Accept": "application/json"},
                         params={"q": query, "count": k})
    if r.status_code in (429, 403):
        with _lock:
            _cool[0] = max(_cool[0], time.time() + 30.0)
        raise requests.HTTPError(f"{r.status_code} rate limited")
    r.raise_for_status()
    j = r.json()
    items = {"tavily": j.get("results", []),
             "serper": j.get("organic", []),
             "brave": j.get("web", {}).get("results", [])}[name]
    out = []
    for it in items[:k]:
        title = (it.get("title") or "").strip()
        # tavily: content · serper: snippet · brave: description
        snip = (it.get("content") or it.get("snippet")
                or it.get("description") or "").strip()
        if title or snip:
            out.append(f"{title} — {snip}"[:900])
    return out


def search(query: str, k: int = 3) -> list[str]:
    """Top-k web results as 'Title — snippet'. [] means a TRUE miss OR a failure;
    call cached() to tell them apart."""
    name = provider()
    if name is None:
        _health["calls"] += 1
        _health["failed"] += 1
        return []
    ck = f"{name}{k}::{query}"
    c = _cache()
    if ck in c:
        return c[ck]                               # cache hits are not billable
    if _health["calls"] >= MAX_CALLS:
        _health["budget_hit"] = True
        return []                                  # not cached -> resumable
    _health["calls"] += 1
    for attempt in range(RETRIES):
        try:
            _throttle()
            out = _request(name, query, k)
            c[ck] = out                            # only a SUCCESS is cached
            _save()
            if not out:
                _health["empty"] += 1
            return out
        except Exception as exc:                   # noqa: BLE001
            if attempt == RETRIES - 1:
                _health["failed"] += 1
                print(f"  !! websearch {query[:40]!r} failed: "
                      f"{str(exc)[:60]}", flush=True)
                return []                          # NOT cached -- retried next run
            time.sleep(BACKOFF * (2 ** attempt))
    return []


def cached(query: str, k: int = 3) -> bool:
    """Did this query land in the cache? Distinguishes a true miss from a failure."""
    return f"{provider()}{k}::{query}" in _cache()


def health_ok(min_calls: int = 25, max_fail: float = 0.10) -> tuple[bool, str]:
    """Is the tool healthy enough to keep going? Checked DURING the run.

    The end-of-run gate told us the truth about RQ4 only after the run was
    already worthless. This is the same test, applied early enough to stop.
    """
    if _health.get("budget_hit"):
        return False, (f"search budget of {MAX_CALLS} billable queries is spent "
                       f"-- stopping before the provider starts refusing")
    c = _health["calls"]
    if c < min_calls:
        return True, ""
    rate = _health["failed"] / c
    if rate > max_fail:
        return False, (f"{_health['failed']}/{c} searches failed "
                       f"({rate*100:.0f}%) -- tool is broken, not the models")
    return True, ""
