"""Smoke-test the hosted provider BEFORE committing to a paid run.

Three things can each silently ruin an 80,000-generation pass, and none of them
show up until you are hours in:

  1. the key is wrong                  -> 401 on every call
  2. a model ID has rotted             -> hosted catalogues churn constantly
  3. the model serves no logprobs      -> the WORST case. Generation succeeds,
     confidence comes back NaN, and the run completes "fine" -- with RQ1
     (confidence in the unanimous region, AUC 0.592) silently reduced to
     nothing. Checking a model exists is not enough; it has to
     actually return per-token logprobs.

Costs a handful of tokens. Run it before every paid pass.

    python scripts/check_provider.py
"""
from __future__ import annotations

import math
import sys

import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from faultlines import generate                       # noqa: E402
from faultlines.config import CFG                     # noqa: E402

G = CFG["generation"]
PROBE = "What is the capital of France?"

# Questions where DIFFERENT models genuinely diverge: obscure entities, not
# "capital of France" (every model says Paris, so agreement there proves
# nothing). Distinctiveness has to be measured where models can disagree.
IDENTITY_PROBES = [
    "Who was the screenwriter for The City?",
    "Who is the author of The Lie?",
    "What genre is Rise?",
    "Who was the composer of Chances Are?",
    "In what city was Jerrold Katz born?",
    "Who was the producer of The Pioneers?",
    "What is the religion of Juan Soldevilla y Romero?",
    "Who was the director of Hakeem's New Flame?",
]

# Above this, two model IDs are almost certainly the same served weights.
# Calibrated on measured data (ISSUES #31): genuinely different models in the
# same family and different sizes agree 9-15% (gemma-3-12b vs gemma-3-27b 15.3%,
# Qwen2.5-7B vs Qwen3-235B 9.0%). The SAME model across two runs reproduces at
# 86-93%. Aliased pairs measured 95.9% and 99.6%. 50% sits in the empty gap
# between "different models" and "same model", so it is not a knife edge.
IDENTITY_MAX = 0.50


def identity_check(names: list[str]) -> bool:
    """Refuse to run an ensemble whose members are secretly the same model.

    THE defect this whole script existed to prevent, and did not. DeepInfra
    served google/gemma-2-27b-it and google/gemma-3-27b-it as identical weights.
    Every earlier check passed: both were reachable, both answered, both returned
    logprobs. 170,364 generations later the Gemma ladder had two duplicate cells
    and the gen-2 Track arm contained two gen-3 models -- so RQ3's headline
    "52% of blind spots persist" was partly models being literally identical.

    Availability is not identity. Asking "does this respond?" cannot detect
    substitution; only comparing OUTPUTS across model IDs can.
    """
    print("\nidentity check -- are these actually different models?")
    answers: dict[str, list[str]] = {}
    for n in names:
        row = []
        for q in IDENTITY_PROBES:
            try:
                a, _ = generate.ask_retry(n, q, dataset="popqa", label=n)
            except Exception:                              # noqa: BLE001
                a = ""
            row.append(a.strip().lower())
        answers[n] = row

    ok = True
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            same = sum(a == b for a, b in zip(answers[x], answers[y]) if a or b)
            rate = same / len(IDENTITY_PROBES)
            flag = "  <-- SAME MODEL?" if rate > IDENTITY_MAX else ""
            print(f"  {rate:5.0%}  {x.split('/')[-1][:26]:28} vs {y.split('/')[-1][:26]}{flag}")
            if rate > IDENTITY_MAX:
                ok = False
    if not ok:
        print(f"\nFAIL  at least one pair agrees above {IDENTITY_MAX:.0%} on questions "
              f"where different models diverge.\n      The provider is serving one "
              f"model under several IDs. Do NOT run this ensemble here.")
    return ok


def main(ensemble: str = "ensemble", provider: str | None = None) -> int:
    if provider:
        generate.use_provider(provider)
    endpoint = G["endpoint"] if provider else G["hosted_endpoint"]
    key_env = G["api_key_env"] if provider else G["hosted_api_key_env"]

    # Point the real ask() at the hosted endpoint for the duration. Deliberate:
    # this smoke-tests the EXACT code path the run will use, rather than a
    # parallel reimplementation that could pass while the real one fails.
    G["endpoint"], G["api_key_env"] = endpoint, key_env
    generate.auth.cache_clear()

    if not generate.auth():
        print(f"FAIL  no key. Put {key_env}=... in faultlines_project/.env")
        return 1
    print(f"endpoint  {endpoint}")
    print(f"key       loaded from {key_env} (via .env)\n")

    r = requests.get(endpoint.replace("/chat/completions", "/models"),
                     headers=generate.auth(), timeout=60)
    if r.status_code != 200:
        print(f"FAIL  model list returned {r.status_code}: {r.text[:200]}")
        return 1
    payload = r.json()
    catalogue = {m.get("id") for m in (payload if isinstance(payload, list)
                                       else payload.get("data", []))}
    print(f"catalogue {len(catalogue)} models visible\n")

    ok = True
    for spec in CFG[ensemble]:
        name = spec["name"]
        # Catalogue absence is a HINT, not a verdict. Measured on DeepInfra
        # 2026-07-28: Qwen2.5-7B, Mistral-7B-v0.3 and gemma-2-9b-it had all
        # dropped out of /v1/models, yet all three answered correctly WITH
        # logprobs -- they are delisted, not withdrawn. Treating the listing as
        # authoritative made this gate block a run that would have worked, one
        # day after the same models produced 1,200 clean rows.
        #
        # So: warn, then let the real call decide. The only authoritative test of
        # "can I use this model" is using it, which is the same principle that
        # makes this script probe the live endpoint instead of trusting config.
        if name not in catalogue:
            near = sorted(c for c in catalogue
                          if c and name.split("/")[-1][:12].lower() in c.lower())
            print(f"DELISTED  {name}\n            not in /v1/models -- probing anyway")
            for n in near[:4]:
                print(f"            catalogue has: {n}")
        try:
            answer, conf = generate.ask_retry(name, PROBE, dataset="popqa", label=name)
            if not answer and math.isnan(conf):
                raise RuntimeError("no answer after retries")
        except Exception as e:                          # noqa: BLE001
            print(f"ERROR     {name}\n            {type(e).__name__}: {e}")
            if name not in catalogue:
                print("            (and it is delisted -- likely withdrawn for good)")
            ok = False
            continue
        if math.isnan(conf):
            print(f"NO LOGPROBS {name}  answered {answer[:30]!r} but confidence=NaN")
            print("            unusable -- RQ1 needs exp(mean log p)")
            ok = False
        else:
            print(f"OK        {name}\n            {answer[:40]!r}  confidence={conf:.3f}")

    # Only worth running once every model is individually usable -- otherwise the
    # agreement matrix is full of empty answers comparing equal to each other.
    if ok:
        ok = identity_check([s["name"] for s in CFG[ensemble]])

    print("\n" + ("all models usable AND distinct -- safe to run"
                  if ok else "NOT ready. Fix the above before any paid run."))
    return 0 if ok else 1


if __name__ == "__main__":
    import argparse
    _ap = argparse.ArgumentParser()
    _ap.add_argument("--ensemble", default="ensemble",
                     help="config key to validate, e.g. ensemble | ensemble_gen2_together")
    _ap.add_argument("--provider", default=None,
                     help="config key suffix: deepinfra | together")
    _a = _ap.parse_args()
    raise SystemExit(main(_a.ensemble, _a.provider))
