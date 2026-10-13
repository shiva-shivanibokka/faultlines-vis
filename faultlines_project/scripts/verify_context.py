"""Verify that shrinking Ollama's context allocation does not change answers.

WHY
Ollama reserves KV-cache VRAM for a full 4,096-token conversation, multiplied by
its parallel request slots. Measured on this corpus, prompts are ~40 tokens
(max 235) and answers are capped at 64, so ~300 tokens are actually used --
about 14x less than reserved. On gemma2:9b that reservation is the difference
between fitting in 8 GB of VRAM and spilling to the CPU:

    gemma2:9b  4-bit   7.1 GB   20%/80% CPU/GPU   1.1-1.4 q/s
    gemma2:9b  8-bit    11  GB   50%/50% CPU/GPU   0.4     q/s
    the other three models        100% GPU          4.5     q/s

Shrinking the window should be a pure memory optimisation: nothing is truncated,
so the computation is identical. THAT IS EXACTLY THE KIND OF "should" THAT HAS
BEEN WRONG ALL DAY, so it gets measured rather than assumed -- against answers
already on disk, generated at the old setting.

    python scripts/verify_context.py --model gemma2:9b --n 120
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from faultlines import generate                    # noqa: E402
from faultlines.config import CFG, path            # noqa: E402


def main(model: str, n: int, tag: str) -> int:
    generate.use_provider("local")

    src = path("interim", f"answers{tag}.parquet")
    df = pd.read_parquet(src)
    have = df[(df["model"] == model) & (df["answer"].str.strip() != "")]
    if have.empty:
        print(f"FAIL  no stored answers for {model} in {src.name}")
        return 1
    sample = have.sample(n=min(n, len(have)), random_state=CFG["seed"])

    print(f"re-asking {len(sample)} questions already answered by {model}")
    print("comparing against answers generated at the ORIGINAL context setting\n")

    same = diff = 0
    examples = []
    for _, r in sample.iterrows():
        now, _ = generate.ask_retry(model, r["question"], dataset=r["dataset"],
                                    label=r["qid"])
        if now.strip() == str(r["answer"]).strip():
            same += 1
        else:
            diff += 1
            if len(examples) < 5:
                examples.append((r["qid"], str(r["answer"])[:45], now[:45]))

    rate = same / len(sample)
    print(f"identical answers: {same}/{len(sample)} ({rate:.1%})")
    if examples:
        print("\nfirst differences:")
        for qid, before, after in examples:
            print(f"  {qid}\n    before: {before!r}\n    after : {after!r}")

    # Local generation is temperature 0, so the only honest bar is EXACT match.
    # A few tenths of a percent can come from nondeterministic kernel scheduling;
    # anything more means the context change altered the computation.
    ok = rate >= 0.99
    print("\n" + ("VERDICT: identical. The reduced context window is safe to use."
                  if ok else
                  "VERDICT: answers CHANGED. Revert the context setting -- the "
                  "speedup is not worth an unexplained difference mid-experiment."))
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma2:9b")
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--tag", default="_rq3local")
    a = ap.parse_args()
    raise SystemExit(main(a.model, a.n, a.tag))
