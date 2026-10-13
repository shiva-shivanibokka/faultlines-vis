"""Which datasets actually earn a place in the study?

A dataset is only useful here if the ensemble gets a WORKABLE share of it wrong.
Two ways to be useless, and both have already bitten this project:

  ceiling  ~95%+ correct -> almost no errors, nothing for the AUC to separate
  floor    ~10% correct  -> almost no successes; SimpleQA was dropped for
                            exactly this on the 7-9B models (91% wrong)

Roughly 40-85% accuracy is the usable band. Below/above it the dataset cannot
support a detection result no matter how good the signal is.

The same run also answers the size-heterogeneity question -- per-model accuracy
shows whether one ensemble member is so weak it becomes the perpetual dissenter
and distorts the disagreement score.

Rows are pulled from the HF datasets-server API, so nothing is downloaded: a
60-row sample costs one HTTP call instead of a 90k-row dataset.

    python scripts/probe_datasets.py            # ~60 q x 6 datasets x 4 models
    python scripts/probe_datasets.py --n 20     # quicker smoke test
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from faultlines.config import CFG                        # noqa: E402
from faultlines.generate import ask                      # noqa: E402
from faultlines.grade import grade_one                   # noqa: E402

ROWS = "https://datasets-server.huggingface.co/rows"

# Candidates that are no longer in config (rejected 2026-07-27) but still worth
# being able to re-probe on demand -- the rejection reasons were measurements,
# and a bigger/newer ensemble could in principle overturn them.
EXTRA = {
    "simpleqa": ("basicv8vc/SimpleQA", "default",    "test"),
    "hotpotqa": ("hotpotqa/hotpot_qa", "distractor", "validation"),
}


def sets(include_rejected: bool) -> list[tuple[str, str, str, str]]:
    """Datasets to probe, driven by config so there is ONE source of truth.

    Reading config rather than a second hard-coded list means a dataset locked
    in config.yaml is automatically the thing being measured here -- the two
    cannot drift apart.
    """
    out = [(name, spec["hf_id"], spec.get("subset", "default"), spec["split"])
           for name, spec in CFG["datasets"].items()]
    if include_rejected:
        out += [(n, *v) for n, v in EXTRA.items()]
    return out


def wilson(k: int, n: int) -> tuple[float, float]:
    """95% Wilson score interval for a proportion.

    Wilson rather than the textbook normal interval: at n in the hundreds with
    proportions near 0.3-0.5 the normal approximation is already sloppy, and it
    can produce bounds outside [0, 1]. This is the interval that decides whether
    a gap between two models is real or sampling noise, so it should be the one
    that behaves at these sample sizes.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    z, p = 1.96, k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def extract(name: str, row: dict) -> dict | None:
    """One HF row -> {question, gold, aliases, tag}. None = unusable row."""
    if name == "popqa":
        alts = json.loads(row["possible_answers"])
        return {"question": row["question"], "gold": alts[0], "aliases": alts, "tag": ""}
    if name == "triviaqa":
        a = row["answer"]
        return {"question": row["question"], "gold": a["value"],
                "aliases": a.get("aliases") or [], "tag": ""}
    if name == "truthfulqa":
        return {"question": row["question"], "gold": row["best_answer"],
                "aliases": row["correct_answers"], "tag": row.get("category", "")}
    if name == "simpleqa":
        return {"question": row["problem"], "gold": row["answer"],
                "aliases": [row["answer"]], "tag": ""}
    if name == "hotpotqa":
        # split by type: `comparison` rows are largely yes/no, which collapses
        # meaning-clustering the same way a classification dataset would.
        return {"question": row["question"], "gold": row["answer"],
                "aliases": [row["answer"]], "tag": row.get("type", "")}
    if name == "halueval":
        return {"question": row["question"], "gold": row["right_answer"],
                "aliases": [row["right_answer"]], "tag": ""}
    return None


PAGE = 100      # datasets-server hard-caps `length` at 100; asking for more 422s


def fetch(name: str, hf: str, cfg: str, split: str, n: int) -> list[dict]:
    """Pull n rows, paginating because the API refuses length > 100."""
    out: list[dict] = []
    for offset in range(0, n, PAGE):
        r = requests.get(ROWS, params={"dataset": hf, "config": cfg, "split": split,
                                       "offset": offset,
                                       "length": min(PAGE, n - offset)}, timeout=90)
        r.raise_for_status()
        rows = r.json()["rows"]
        if not rows:
            break                                   # split shorter than n
        for item in rows:
            rec = extract(name, item["row"])
            if rec and rec["question"] and str(rec["gold"]).strip():
                rec |= {"dataset": name, "qid": f"{name}-{len(out):04d}"}
                out.append(rec)
    return out


def main(n: int, include_rejected: bool) -> int:
    models = [m["name"] for m in CFG["ensemble"]]
    SETS = sets(include_rejected)
    print(f"probing {len(SETS)} datasets x {n} questions x {len(models)} models")
    print(f"endpoint {CFG['generation']['endpoint']}\n")

    items = []
    for name, hf, cfg, split in SETS:
        try:
            got = fetch(name, hf, cfg, split, n)
            items += got
            print(f"  {name:11} {len(got):>3} questions")
        except Exception as e:                                  # noqa: BLE001
            print(f"  {name:11} FETCH FAILED {type(e).__name__}: {str(e)[:60]}")
    print()

    if not items:
        print("no questions fetched -- nothing to probe. Fix the fetch errors above.")
        return 1

    jobs = [(it, m) for it in items for m in models]

    def one(job):
        it, m = job
        try:
            answer, conf = ask(m, it["question"], dataset=it["dataset"])
        except Exception:                                       # noqa: BLE001
            answer, conf = "", float("nan")
        ok, tier = grade_one(answer, it["gold"], it["aliases"], it["dataset"])
        return {**it, "model": m, "answer": answer, "confidence": conf,
                "correct": ok, "tier": tier}

    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(one, jobs))
    df = pd.DataFrame(rows)

    print("=" * 66)
    print("PER-DATASET  (usable band is roughly 40-85% accuracy)")
    for ds, g in df.groupby("dataset"):
        a = g["correct"].mean()
        per_q = g.groupby("qid")["correct"]
        allw = (per_q.sum() == 0).mean()          # every model wrong
        verdict = ("CEILING - too easy" if a > .88 else
                   "FLOOR - too hard" if a < .30 else "usable")
        print(f"  {ds:11} acc {a:5.1%}   all-wrong {allw:5.1%}   {verdict}")

    print("\n  NOTE truthfulqa is graded here WITHOUT the NLI tier, so its accuracy is")
    print("       inflated by the cosine/negation weakness (ISSUES.md #1) -- treat it")
    print("       as an upper bound. It does not change the keep/drop decision.")

    print("\nPER-MODEL  (a big gap = one model becomes the perpetual dissenter)")
    print("  95% CI shown: if two models' intervals OVERLAP, the sample cannot")
    print("  tell them apart and you must not drop one on this evidence.")
    stats = []
    for m, g in df.groupby("model"):
        k, tot = int(g["correct"].sum()), len(g)
        lo, hi = wilson(k, tot)
        stats.append((m, k / tot, lo, hi, tot))
    for m, p, lo, hi, tot in sorted(stats, key=lambda x: -x[1]):
        print(f"  {m.split('/')[-1][:38]:40} {p:5.1%}  [{lo:4.1%} - {hi:4.1%}]  n={tot}")

    if len(stats) > 1:
        best, worst = max(stats, key=lambda x: x[1]), min(stats, key=lambda x: x[1])
        sep = "SEPARATED - the gap is real" if worst[3] < best[2] else \
              "OVERLAPPING - need more questions to call it"
        print(f"\n  best vs worst: {best[1]:.1%} vs {worst[1]:.1%}  -> {sep}")

    print("\nHOTPOTQA BY TYPE  (comparison rows are yes/no -> clustering degenerates)")
    hp = df[df["dataset"] == "hotpotqa"]
    for t, g in hp.groupby("tag"):
        yn = g["gold"].astype(str).str.lower().isin(["yes", "no"]).mean()
        print(f"  {t or '(none)':12} acc {g['correct'].mean():5.1%}  yes/no golds {yn:5.1%}")

    dest = CFG["paths"]["processed"] / "dataset_probe.parquet"
    df.to_parquet(dest)
    print(f"\n-> {dest}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60, help="questions per dataset")
    ap.add_argument("--include-rejected", action="store_true",
                    help="also probe simpleqa/hotpotqa (re-test the rejections)")
    a = ap.parse_args()
    raise SystemExit(main(a.n, a.include_rejected))
