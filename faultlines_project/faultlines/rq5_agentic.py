"""RQ5 - do shared blind spots survive TOOL USE?

    python -m faultlines.rq5_agentic --limit 8      # smoke test
    python -m faultlines.rq5_agentic                # the current blind spots (950)

THE QUESTION, AND WHY IT IS WORTH PAYING FOR
The obvious objection to this whole thesis is "a modern agent with search would
just fix these". RQ4 already answered a weaker version -- handing a model a
retrieved passage repairs obscurity (+65.2 points) and barely touches
misconception (+14.0 points, not significant) -- but the model was *given* a document, it did not *choose* to look
anything up. This arm gives each model search and read tools and lets it decide
when, what, and whether to use them.

The measurement is NOT "can an agent answer harder questions". It is:

    of the blind-spot questions (950 on the deduplicated corpus; the first
    run used the pre-dedup 1,054) where all four models agreed on the same wrong
    answer, how many are STILL all-wrong, and how many are still SILENT
    (all-wrong AND agreeing) once every model can look things up?

A drop in all-wrong is the optimistic reading. A drop in *silence* that is
smaller than the drop in wrongness is the pessimistic one, and it is the reading
that matters: it would mean tools make models right more often without making
their remaining errors any easier to detect.

WHY A TEXT PROTOCOL AND NOT NATIVE FUNCTION CALLING
Measured 2026-08-01 against the provider: Qwen3-235B, Mistral-Small-3.2 and
Gemma-3-27B accept an OpenAI `tools` payload; **Llama-4-Maverick returns 405.**
Using native tools would silently give three models a capability the fourth does
not have, and "four makers with the same capability" is the invariant the entire
silent-consensus claim rests on -- an ensemble where one member cannot search is
measuring model choice, not tool use. A plain text protocol is worse ergonomics
and a strictly better experiment.

STANDING RULES OBSERVED
  1. An empty answer is a failed call, not a result -- never written as done.
  2. `if "col" not in df.columns` is a review flag -- this module appends whole
     rows and never patches a column in place.
  3. Never cache a failure -- the Wikipedia layer is rq4_retrieval's, which was
     rebuilt around exactly that rule after ISSUES #29.
"""
from __future__ import annotations

import argparse
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

from faultlines import grade
from faultlines.config import CFG, SEED, path
from faultlines.generate import auth
from faultlines import rq4_retrieval as rq4
from faultlines import websearch
from faultlines.rq4_retrieval import _load_cache, retrieve, retrieve_title

G = CFG["generation"]
MAX_STEPS = 4           # tool calls before the model must answer
SNIPPET = 900           # chars per tool result
RETRIES = 3
BACKOFF = 2.0
CKPT = 20               # rows between checkpoints
# 5 threads against the model API. The binding constraint is Wikipedia's 1.5s
# global lock, not the provider, so more workers buy nothing once the cache is
# cold -- and #29b is what happens when that limit is treated as advisory.
WORKERS = 4

# Wikipedia's limit is stricter under the agent's access pattern than under RQ4's
# (one call per case, spread over hours) -- at 1.5s with 5 workers, 10.8% of tool
# calls exhausted their retries on 429. Raised for this module only, at import,
# because a 10% broken tool is exactly the state that produced RQ4's three clean
# wrong tables. Slower and measurable beats faster and uninterpretable.
rq4._orig_interval = rq4.MIN_INTERVAL
rq4.MIN_INTERVAL = 1.8

SYSTEM = """You are answering a factual question. You may look things up.

To use a tool, reply with EXACTLY one line and nothing else:
SEARCH: <what to search for>
READ: <exact Wikipedia article title>

You will then be shown the result and may use another tool.
When you are ready, reply with EXACTLY one line and nothing else:
ANSWER: <the answer, as few words as possible>

You have at most {n} tool uses. If the tools do not help, answer from your own
knowledge. Do not explain. Do not write anything except one SEARCH, READ or
ANSWER line."""

_ACT = re.compile(r"^\s*(SEARCH|READ|ANSWER)\s*:\s*(.+)", re.I | re.M)


def _chat(model: str, messages: list[dict]) -> str:
    """One completion. Raises on failure so the caller can drop the row."""
    body = {"model": model, "messages": messages,
            "temperature": G["temperature"], "max_tokens": 160}
    for m in CFG["ensemble"]:
        if m["name"] == model and m.get("params"):
            body.update(m["params"])
    last = None
    for a in range(RETRIES):
        try:
            r = requests.post(G["endpoint"], headers=auth(), json=body, timeout=120)
            if r.status_code == 200:
                return (r.json()["choices"][0]["message"]["content"] or "").strip()
            last = f"HTTP {r.status_code}"
        except Exception as e:                       # noqa: BLE001
            last = type(e).__name__
        time.sleep(BACKOFF * (a + 1))
    raise RuntimeError(f"{model}: {last}")


# ONE Wikipedia call at a time, across every worker thread. The rate limiter in
# rq4_retrieval spaces the START of requests but does not stop five from being in
# flight at once, and MediaWiki 429s on concurrency as well as on rate -- observed
# immediately at WORKERS=5. Holding the lock across the whole call costs wall
# clock and buys the only thing that matters here.
_wiki_lock = threading.Lock()

# TOOL HEALTH. RQ4 reported "retrieval does not fix obscurity" three times in
# clean tables while the retriever was returning nothing (ISSUES #28-30). The
# check that caught it was not statistical -- it was "did the tool actually
# work?". An agentic arm can fail the same way and look like a finding: if every
# SEARCH returns "(the tool failed)", this measures a broken tool and reports it
# as models being incapable. So the failures are counted and the summary refuses
# to interpret the numbers when they are high.
_health = {"calls": 0, "failed": 0, "empty": 0}

# Set when the tool layer decides it is broken. Threads cannot end the process --
# a SystemExit raised in a worker kills only that worker, silently -- so the
# workers cooperate: each checks this before starting, and queued work drains
# without doing anything. See the abort in _tool_web.
_abort = threading.Event()

# Which sources the agent can reach. Two ARMS, not a swap: the comparison is the
# finding. Wikipedia is curated and reproducible; the open web is where shared
# misconceptions actually come from, which is the mechanism RQ4 asserted but
# never tested. Running the identical agent over both is the only way to tell
# "the models cannot be helped" from "the encyclopedia did not have it".
ARM = ["wiki"]


def _tool(kind: str, arg: str) -> str:
    if ARM[0] == "web":
        return _tool_web(kind, arg)
    key = f"T::{arg}" if kind == "READ" else f"2::{arg}"
    with _wiki_lock:
        try:
            hits = retrieve_title(arg) if kind == "READ" else retrieve(arg, k=2)
        except Exception:                            # noqa: BLE001
            _health["calls"] += 1; _health["failed"] += 1
            return "(the tool failed)"
        _health["calls"] += 1
        if not hits:
            # An exhausted-retry 429 and a genuine "no such article" BOTH return
            # [] -- which is the #29 ambiguity one level up, now in the health
            # metric instead of in the data. They are distinguishable by the one
            # invariant that module guarantees: a SUCCESS is cached, a FAILURE
            # never is. Absent from the cache => the call failed.
            if key in _load_cache():
                _health["empty"] += 1
                return "(nothing found)"
            _health["failed"] += 1
            return "(the tool failed)"
    return "\n---\n".join(h[:SNIPPET] for h in hits[:2])


def _tool_web(kind: str, arg: str) -> str:
    """Open-web arm. READ and SEARCH both become a web query -- there are no
    article titles out here, and pretending otherwise would quietly give the web
    arm a capability the protocol does not actually offer it."""
    hits = websearch.search(arg, k=3)
    _health["calls"] += 1
    if not hits:
        # same success-is-cached / failure-is-not test as the Wikipedia arm
        if websearch.cached(arg, 3):
            _health["empty"] += 1
            return "(nothing found)"
        _health["failed"] += 1
        # ABORT rather than carry on. On 2026-08-02 DuckDuckGo blackholed the IP
        # and every subsequent search failed, but the models kept answering, so
        # 40 questions of "model behaviour with a dead tool" were recorded as
        # data. The end-of-run health gate reported it correctly and far too
        # late. A tool that has stopped working must stop the run, not colour it.
        ok, why = websearch.health_ok()
        if not ok and not _abort.is_set():
            _abort.set()
            print(f"\n!! ABORTING: {why}\n"
                  "   Rows already written are fine; resume re-does only what is\n"
                  "   missing. Fix the tool, then re-run.\n", flush=True)
        return "(the tool failed)"
    return "\n---\n".join(hits)


def run_one(model: str, question: str) -> tuple[str, int, bool]:
    """-> (answer, tool calls used, whether it ever called a tool)."""
    msgs = [{"role": "system", "content": SYSTEM.format(n=MAX_STEPS)},
            {"role": "user", "content": question}]
    used = 0
    # MAX_STEPS tool turns, one turn that may be the "no tool uses left"
    # nudge, and one more to READ the reply to it. It was MAX_STEPS + 1, so a
    # model that asked for a fifth tool got the nudge and the loop ended before
    # it could answer: every one of the 85 missing Wikipedia-arm rows was
    # "empty after 4 tool calls" (ISSUES #76).
    for _ in range(MAX_STEPS + 2):
        out = _chat(model, msgs)
        m = _ACT.search(out)
        if not m:
            # No protocol line. Treat the whole reply as the answer rather than
            # discarding it -- a model that answers plainly has still answered,
            # and scoring that as a failure would penalise instruction-following
            # rather than knowledge.
            return out, used, used > 0
        kind, arg = m.group(1).upper(), m.group(2).strip()
        if kind == "ANSWER":
            return arg, used, used > 0
        if used >= MAX_STEPS:
            msgs.append({"role": "user",
                         "content": "No tool uses left. Reply with ANSWER: <answer>."})
            continue
        used += 1
        msgs += [{"role": "assistant", "content": f"{kind}: {arg}"},
                 {"role": "user", "content": _tool(kind, arg) +
                  "\n\nUse another tool or reply ANSWER: <answer>."}]
    return "", used, used > 0


def grade_like_closed_book(a: str, q) -> tuple[bool, str]:
    """The SAME grader the closed-book arm used -- a different one would make
    the comparison measure grading, not tools. For TruthfulQA that is NLI
    against the correct AND incorrect answer lists, not the cosine tier:
    this called grade_one for every dataset until 2026-09-27 (ISSUES #76).
    """
    if q.dataset == "truthfulqa":
        from faultlines import nli
        from faultlines.config import seq
        meta = q.meta if isinstance(q.meta, dict) else {}
        ok, _, _ = nli.grade_truthful(a, seq(q.aliases), seq(meta.get("incorrect")))
        return bool(ok), "nli"
    return grade.grade_one(a, q.gold, q.get("aliases"), dataset=q.dataset)


def population() -> pd.DataFrame:
    """The silent-consensus questions (950 since the dedup), with gold and aliases."""
    rec = pd.read_parquet(path("processed", "records.parquet"))
    rec = rec[rec.silent_consensus].copy()
    ans = pd.read_parquet(path("interim", "answers.parquet"),
                          columns=["qid", "gold", "aliases"]).drop_duplicates("qid")
    return rec.merge(ans, on="qid", how="left", suffixes=("", "_a"))


def run(limit: int | None = None, sample: int | None = None,
        resume_only: bool = False) -> None:
    suffix = "" if ARM[0] == "wiki" else "_" + ARM[0]
    dest = path("processed", f"rq5_agentic{suffix}.parquet")
    done = set()
    if dest.exists():
        prev = pd.read_parquet(dest)
        done = set(zip(prev.model, prev.qid))
        print(f"resuming: {len(prev)} rows already recorded")
    else:
        prev = pd.DataFrame()

    pop = population()
    if resume_only:
        # Finish the questions already in the file and nothing else. The web
        # sample is seeded against population(), which shrank from 1,054 to 950
        # with the dedup, so --sample would now draw a DIFFERENT sample and pay
        # to start it rather than complete the one the thesis reports.
        pop = pop[pop.qid.isin(set(prev.qid))] if len(prev) else pop.iloc[:0]
        print(f"resume-only: {len(pop)} current blind spots already in the file")
    elif sample:
        # Free search tiers are ~2,500 queries; the full arm needs ~8,000, so the
        # web arm runs on a sample. Stratified by dataset because the whole point
        # of the comparison is per-dataset (obscurity vs misconception) -- a
        # simple random sample could under-fill truthfulqa, which has only 4.
        # Seeded, so "which questions" is a fact about the config, not the run.
        # Plain loop, not groupby().apply(): pandas >= 2.2 excludes the grouping
        # column from the frame handed to apply, so the result came back with no
        # `dataset` column at all. Crashed on the very next line, which is the
        # good outcome -- but a silent version difference deciding the shape of
        # the sample is not something to leave in.
        parts, total = [], len(pop)
        for ds, g in pop.groupby("dataset"):
            n = min(len(g), max(1, round(sample * len(g) / total)))
            parts.append(g.sample(n, random_state=SEED))
        pop = pd.concat(parts).reset_index(drop=True)
        print(f"sampled {len(pop)} of {total}, stratified by dataset, seed={SEED}")
        print(pop.dataset.value_counts().to_string())
    if limit:
        pop = pop.head(limit)
    models = [m["name"] for m in CFG["ensemble"]]
    total = len(pop) * len(models)
    print(f"{len(pop)} blind spots x {len(models)} models = {total} agent runs")

    # Models stay in the OUTER loop and questions are threaded within one model.
    # That ordering matters for cost, not just speed: the first model warms the
    # Wikipedia cache for every question, so models 2-4 mostly hit disk. Threading
    # across models instead would have four cold passes racing for the same
    # 1.5s-spaced rate limit.
    rows, fails = [], 0
    lock = threading.Lock()
    n = [0]

    def one(model, q):
        nonlocal fails
        if _abort.is_set():
            return                                # drain the queue, do no work
        try:
            a, used, tooled = run_one(model, q.question)
        except Exception as e:                        # noqa: BLE001
            with lock:
                fails += 1
                print(f"  ! {q.qid} {model.split('/')[-1][:20]} {e}", flush=True)
            return                                    # rule 1: not recorded as done
        if not a.strip():
            # Silent before: the qid was lost, so a question that NEVER answers
            # looked identical to a transient blip and got retried every resume.
            # The 2026-08-01 restart burned ~42 calls rediscovering that.
            with lock:
                fails += 1
                print(f"  ~ {q.qid} {model.split('/')[-1][:20]} empty after "
                      f"{used} tool calls", flush=True)
            return
        ok, tier = grade_like_closed_book(a, q)
        with lock:
            rows.append({"qid": q.qid, "dataset": q.dataset, "model": model,
                         "answer": a, "correct": bool(ok), "tier": tier,
                         "tool_calls": used, "used_tools": tooled,
                         "gold": q.gold})
            n[0] += 1
            if len(rows) % CKPT == 0:
                pd.concat([prev, pd.DataFrame(rows)], ignore_index=True).to_parquet(dest)
                print(f"  {n[0]}/{total}  ok={sum(r['correct'] for r in rows)}"
                      f"  tooled={sum(r['used_tools'] for r in rows)}  fails={fails}",
                      flush=True)

    for model in models:
        if _abort.is_set():
            break
        todo = [q for _, q in pop.iterrows() if (model, q.qid) not in done]
        print(f"  {model.split('/')[-1]}: {len(todo)} to run", flush=True)
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            list(ex.map(lambda q: one(model, q), todo))
        pd.concat([prev, pd.DataFrame(rows)], ignore_index=True).to_parquet(dest)
    if rows:
        pd.concat([prev, pd.DataFrame(rows)], ignore_index=True).to_parquet(dest)
    print(f"\n-> {dest}   {len(rows)} new rows, {fails} failed calls (not recorded)")
    c = _health["calls"]
    if c:
        bad = _health["failed"] / c
        print(f"\nTOOL HEALTH: {c} tool calls · "
              f"{_health['failed']} failed ({bad*100:.1f}%) · "
              f"{_health['empty']} returned nothing ({_health['empty']/c*100:.1f}%)")
        if bad > 0.10:
            print("  !! MORE THAN 10% OF TOOL CALLS FAILED. Do not interpret the\n"
                  "     numbers below -- this is the RQ4 failure mode (ISSUES #28-30):\n"
                  "     a broken tool reported as models being incapable. Re-run the\n"
                  "     missing rows; the cache makes that cheap.")
    summarise()


def summarise() -> None:
    suffix = "" if ARM[0] == "wiki" else "_" + ARM[0]
    dest = path("processed", f"rq5_agentic{suffix}.parquet")
    if not dest.exists():
        return
    d = pd.read_parquet(dest)
    full = d.groupby("qid").filter(lambda g: g.model.nunique() == len(CFG["ensemble"]))
    print(f"\n{len(d)} rows · {d.qid.nunique()} questions · "
          f"{full.qid.nunique()} with all four models")
    print(f"used a tool: {d.used_tools.mean()*100:.1f}%   "
          f"mean tool calls: {d.tool_calls.mean():.2f}")
    if not len(full):
        return
    g = full.groupby("qid")
    all_wrong = g.correct.apply(lambda s: not s.any())
    any_right = g.correct.apply(lambda s: s.any())
    print(f"\nOf {len(all_wrong)} former blind spots, WITH TOOLS:")
    print(f"  at least one model now right : {int(any_right.sum())} "
          f"({any_right.mean()*100:.1f}%)")
    print(f"  still all four wrong         : {int(all_wrong.sum())} "
          f"({all_wrong.mean()*100:.1f}%)")
    for ds, sub in full.groupby("dataset"):
        gg = sub.groupby("qid").correct.apply(lambda s: s.any())
        print(f"    {ds:<12} fixed {int(gg.sum()):>4} of {len(gg):>4}  ({gg.mean()*100:.1f}%)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="first N blind spots (smoke test)")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--sample", type=int,
                    help="stratified sample of N questions (web arm: free search "
                         "tiers are ~2500 queries, the full arm needs ~8000)")
    ap.add_argument("--arm", choices=["wiki", "web"], default="wiki",
                    help="wiki = Wikipedia only (reproducible); web = open web search")
    ap.add_argument("--resume-only", action="store_true",
                    help="complete only questions already in the arm's file")
    a = ap.parse_args()
    ARM[0] = a.arm
    summarise() if a.summary else run(a.limit, a.sample, a.resume_only)
