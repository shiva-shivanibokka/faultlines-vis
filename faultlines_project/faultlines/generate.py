"""Level 2 — ask each model every question, one model at a time.

Confidence = exp(mean token log p), the inverse of perplexity. This is the
white-box edge: it exists only because the models are open-weight and local.
Verified working on Ollama 0.32 via the OpenAI-compatible endpoint.

Models are looped in the OUTER loop on purpose -- 8 GB VRAM holds one at a
time, so swapping per question would thrash. Resumable: already-finished
(model, qid) pairs are skipped, so a crash costs minutes not hours.

    python -m faultlines.generate --pull        # fetch the four models
    python -m faultlines.generate --pilot
"""
from __future__ import annotations

import argparse
import functools
import math
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

from .config import CFG, path

G = CFG["generation"]
RETRIES = 3          # transient 429/timeout under concurrency
BACKOFF = 1.5        # seconds, doubled per attempt


@functools.lru_cache(maxsize=1)
def auth() -> dict:
    """Bearer header when the configured key env var is set, {} otherwise.

    This is the whole cost of moving off the laptop: Together, Fireworks,
    DeepInfra and OpenAI all speak the same /v1/chat/completions shape Ollama
    does, logprobs included, so only the endpoint and this header change.
    Ollama ignores an Authorization header, so the local path is unaffected.
    """
    key = os.environ.get(G.get("api_key_env") or "", "").strip()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def use_provider(name: str) -> None:
    """Point generation at a named provider_* config block, for this process.

    Exists because a model ID is not a model. DeepInfra served gemma-2-27b-it
    and gemma-3-27b-it as the SAME weights (99.6% identical answers), which
    silently turned the Track and ladder experiments into comparisons of a model
    with itself. Running the older arm on a second provider is the only way to
    separate a real generation gap from one provider's substitution policy.
    """
    block = CFG.get(f"provider_{name}")
    if not block:
        raise SystemExit(f"no provider_{name} in config.yaml")
    G["endpoint"] = block["endpoint"]
    G["api_key_env"] = block["api_key_env"]
    auth.cache_clear()                       # the key env var just changed
    print(f"provider: {name}  ({block['endpoint']})")


def confidence(logprobs: list[float]) -> float:
    """exp(mean log p). 1.0 = certain, ->0 = the model was guessing."""
    if not logprobs:
        return float("nan")
    return math.exp(sum(logprobs) / len(logprobs))


def logprobs_of(choice: dict) -> list[float]:
    """Per-token logprobs from a /v1/chat/completions choice, either dialect.

    "OpenAI-compatible" is not one wire format. Two shapes exist and both are
    live on providers this project targets:

        OpenAI / Ollama : logprobs.content -> [{"logprob": -0.4}, ...]
        Together        : logprobs.token_logprobs -> [-0.4, ...]

    Reading only the first shape against a provider that speaks the second
    yields [] -> confidence NaN, on a request that returned HTTP 200 with a
    perfectly good answer. Measured on Together's Llama-3.3-70B: the run would
    have completed "successfully" with every confidence NaN and RQ1 -- the
    strongest surviving result -- silently reduced to nothing. Hence: parse
    both, and let check_provider.py fail loudly if neither is present.
    """
    lp = choice.get("logprobs") or {}
    if lp.get("content"):
        return [t["logprob"] for t in lp["content"] if t.get("logprob") is not None]
    return [v for v in (lp.get("token_logprobs") or []) if v is not None]


_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_OPEN_THINK = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    """Remove <think> blocks a provider leaks into user-facing content.

    Needed because the SAME model name behaves differently per provider: the
    local Ollama qwen2.5:7b returns a bare answer, while DeepInfra's
    Qwen2.5-7B-Instruct prefixes a <think> block. That is a serving artifact,
    not model output, and leaving it in would make the grader mark correct
    answers wrong and would pollute meaning-clustering with reasoning prose.

    The unclosed case matters as much as the closed one: at max_tokens=64 the
    block is often TRUNCATED mid-thought, so there is no </think> to match and a
    naive paired-tag regex leaves the whole thing in place.
    """
    if not text:
        return ""
    out = _THINK.sub(" ", text)
    if "<think>" in out.lower():        # truncated block, never closed
        out = _OPEN_THINK.sub(" ", out)
    return out.strip()


@functools.lru_cache(maxsize=1)
def model_params() -> dict:
    """Per-model request-body overrides, collected from every ensemble* block.

    Exists because one provider quirk CANNOT be fixed globally, verified in both
    directions on DeepInfra 2026-07-27:

      Qwen2.5-7B-Instruct  emits a <think> block that max_tokens=64 truncates
                           before the answer, so the stripped answer is EMPTY.
                           chat_template_kwargs.enable_thinking=false fixes it.
      Qwen3-235B-A22B      returns EMPTY *with* that same flag, and is fine
                           without it.

    So the flag repairs one model and breaks another. Rejected alternatives, both
    of which fix Qwen2.5 but introduce an asymmetry between ensemble members --
    fatal when the whole measurement is cross-model disagreement:
      - raising max_tokens for one model  -> unequal generation budget
      - '/no_think' in the system prompt  -> different prompt for one model
    """
    out: dict[str, dict] = {}
    for key, val in CFG.items():
        if not (key.startswith("ensemble") and isinstance(val, list)):
            continue
        for spec in val:
            if isinstance(spec, dict) and spec.get("params"):
                out[spec["name"]] = spec["params"]
    return out


def prompt_for(dataset: str | None) -> str:
    """TruthfulQA needs sentence answers; the others need bare spans. See config."""
    sp = G["system_prompt"]
    return sp.get(dataset, sp["default"]) if isinstance(sp, dict) else sp


def ask(model: str, question: str, temperature: float | None = None,
        dataset: str | None = None) -> tuple[str, float]:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_for(dataset)},
            {"role": "user", "content": question},
        ],
        "temperature": G["temperature"] if temperature is None else temperature,
        "max_tokens": G["max_tokens"],
        "logprobs": True,
        "top_logprobs": 1,
    }
    body.update(model_params().get(model, {}))     # per-model provider quirks
    r = requests.post(G["endpoint"], json=body, headers=auth(), timeout=G["timeout_s"])
    r.raise_for_status()
    choice = r.json()["choices"][0]
    answer = strip_reasoning(choice["message"]["content"])
    return answer, confidence(logprobs_of(choice))


def ask_retry(model: str, question: str, temperature: float | None = None,
              dataset: str | None = None, label: str = "") -> tuple[str, float]:
    """ask() with backoff. Returns ("", nan) only after RETRIES failures.

    Lives here, and is used by baseline.py too, because the two arms MUST fail
    the same way. baseline.py used to catch its own exceptions and record the
    empty string as if it were the model's answer -- so a 429 became a real
    sample, clustered on its own, and manufactured Semantic Entropy that never
    happened. Measured on the first 9,800 rows of the 8k baseline: 82 rows
    carried an empty sample and averaged entropy 0.713 against 0.207 for clean
    rows, 3.4x.

    That asymmetry ran in the direction that FLATTERS this project's hypothesis
    -- the ensemble arm retried, the baseline arm did not, so throttling
    degraded only the competitor. One retry policy, one place to change it.
    """
    for attempt in range(RETRIES):
        try:
            return ask(model, question, temperature=temperature, dataset=dataset)
        except Exception as e:          # one bad question must not kill the run
            if attempt == RETRIES - 1:
                print(f"  !! {label or question[:40]!r} {model}: {e}", flush=True)
            else:
                time.sleep(BACKOFF * (2 ** attempt))
    return "", float("nan")


def pull() -> None:
    if auth():
        print("hosted provider configured -- nothing to pull, the models are remote")
        return
    for m in CFG["ensemble"]:
        print(f"pulling {m['name']} ...")
        subprocess.run(["ollama", "pull", m["name"]], check=True)


def run(pilot: bool = True, tag: str = "", ensemble: str = "ensemble",
        limit: int | None = None, questions: str | None = None) -> pd.DataFrame:
    """tag keeps runs in SEPARATE files.

    Without it every run writes answers_pilot.parquet, so re-running the frozen
    pilot on a new ensemble would silently destroy the local 7-9B results that
    the whole small-vs-large comparison depends on. Those cannot be regenerated
    cheaply -- they are days of laptop GPU time. Always pass a tag.

    ensemble names which config block to use (ensemble / ensemble_gen2 /
    ensemble_gemma_ladder), so Track arms need no config editing between runs.
    """
    # `questions` names an explicit subset file. Needed for the RQ3 local rerun,
    # which is deliberately NOT a random sample: at a ~2% blind-spot rate, 4,000
    # random questions yield ~80 usable cases and spend 18 laptop-hours on
    # questions that carry no information. Targeting the known silent-consensus
    # population plus a control sample buys ~1,000 cases per arm in 12 hours.
    qs = pd.read_parquet(path("interim", questions) if questions else
                         path("interim", "questions_pilot.parquet" if pilot
                              else "questions.parquet"))
    if limit is not None:
        # Slice test. A new dataset's loader can pass a 3-row spot check and
        # still break on the real generate -> grade path (the Qwen <think>
        # truncation did exactly that), so run a few hundred rows before
        # committing to six figures of generations.
        qs = qs.groupby("dataset", group_keys=False).head(max(1, limit // qs["dataset"].nunique()))
        print(f"LIMIT {len(qs)} questions ({qs['dataset'].nunique()} datasets, stratified)")
    base = "answers_pilot" if pilot else "answers"
    dest = path("interim", f"{base}{tag}.parquet")

    done: set[tuple[str, str]] = set()
    rows: list[dict] = []
    if dest.exists():                       # resume
        prev = pd.read_parquet(dest)
        # Keep only SUCCESSES. A failed generation is stored with confidence
        # NaN, and if those counted as "done" a transient timeout would become
        # permanent missing data -- at 43k questions an 8% failure rate bakes in
        # ~14k holes that no rerun ever fills, because resume skips them.
        good = prev[prev["confidence"].notna()]
        rows = good.to_dict("records")
        done = set(zip(good["model"], good["qid"]))
        failed = len(prev) - len(good)
        print(f"resuming: {len(done)} answers on disk"
              + (f"; retrying {failed} previously failed" if failed else ""))

    # Model stays the OUTER loop, but questions within a model now run
    # concurrently. The outer ordering existed because only one model fits in
    # 8 GB VRAM; on a hosted API that constraint is gone and serial calls are
    # pure latency -- 172k sequential requests is ~48 hours of waiting on the
    # network. Chunked so a crash costs one chunk, not one model.
    workers = int(G.get("max_workers", 12))
    chunk = int(G.get("checkpoint_every", 200))

    for spec in CFG[ensemble]:
        model = spec["name"]
        todo = [r for r in qs.to_dict("records") if (model, r["qid"]) not in done]
        print(f"\n{model}  ({spec['maker']})  {len(todo)} to go")
        t0, seen = time.time(), 0

        def one(q, _m=model, _maker=spec["maker"]):
            # Retry transient failures in-run. Measured on the gen-2 arm: 25/300
            # Mistral calls failed under 12-way concurrency, 24 of them on
            # TruthfulQA (the longest system prompt), and every retry succeeded
            # immediately -- so these are timeouts/throttling, not bad questions.
            # Without this the holes land in the data and quietly bias whichever
            # dataset happens to be slowest.
            answer, conf = ask_retry(_m, q["question"], dataset=q["dataset"],
                                     label=q["qid"])
            return {**q, "model": _m, "maker": _maker,
                    "answer": answer, "confidence": conf}

        for start in range(0, len(todo), chunk):
            batch = todo[start:start + chunk]
            with ThreadPoolExecutor(max_workers=workers) as pool:
                rows.extend(pool.map(one, batch))
            seen += len(batch)
            rate = seen / max(1e-6, time.time() - t0)
            print(f"  {seen}/{len(todo)}  {rate:.1f} q/s", flush=True)
            pd.DataFrame(rows).to_parquet(dest)   # checkpoint

    out = pd.DataFrame(rows)
    out.to_parquet(dest)
    print(f"\n-> {dest}  ({len(out)} answers)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pull", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--tag", default="",
                    help="output suffix, e.g. _gen3 -> answers_pilot_gen3.parquet")
    ap.add_argument("--ensemble", default="ensemble",
                    help="config key: ensemble | ensemble_gen2 | ensemble_gemma_ladder")
    ap.add_argument("--limit", type=int, default=None,
                    help="slice test: N questions stratified across datasets")
    ap.add_argument("--provider", default=None,
                    help="config key suffix: deepinfra | together | local")
    ap.add_argument("--questions", default=None,
                    help="explicit question-set filename in data/interim/")
    a = ap.parse_args()
    if a.provider:
        use_provider(a.provider)
    if a.pull:
        pull()
    else:
        run(pilot=a.pilot, tag=a.tag, ensemble=a.ensemble, limit=a.limit,
            questions=a.questions)
