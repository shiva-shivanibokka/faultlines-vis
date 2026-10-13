"""RQ3 / Track - do the blind spots persist across a model generation?

Compares two TAGGED arms that went through the identical
generate -> grade -> nli -> disagree path on the SAME frozen questions, and
measures the item-level overlap of silent consensus between them. A persistent
core means blind spots are inherited from the shared training corpus rather
than being idiosyncrasies of one model generation.

Both arms must be hosted at the same precision and hold the same maker count:
the original gen-1 arm (Llama2/Qwen1.5/Mistral-0.1, local 4-bit) was DROPPED
because it had three makers against four, and "all models agree" is
mechanically more likely with three -- so the comparison measured ensemble size
as much as generation. See DECISIONS.md.

    # compare gen-2 hosted against gen-3 (both already produced by run_pilot):
    python -m faultlines.track --pilot --old-tag _gen2h --new-tag _gen3

The overlap metric is pure and unit-tested; the generation step is the
download-gated hand-off.
"""
from __future__ import annotations

import argparse
import time

import pandas as pd

from faultlines.config import CFG, stage
from faultlines.disagree import score
from faultlines.grade import grade_one


def persistence(gen1: pd.DataFrame, gen2: pd.DataFrame) -> dict:
    """Item-level overlap of silent_consensus between two ensemble runs on the
    same qids. Returns the persistent core and Jaccard overlap."""
    s1 = set(gen1.loc[gen1["silent_consensus"], "qid"])
    s2 = set(gen2.loc[gen2["silent_consensus"], "qid"])
    inter = s1 & s2
    union = s1 | s2
    return {
        "gen1_silent": len(s1),
        "gen2_silent": len(s2),
        "persistent_core": len(inter),
        "healed": len(s1 - s2),        # broken in gen1, fixed in gen2
        "emerged": len(s2 - s1),       # new blind spots in gen2
        "jaccard": (len(inter) / len(union)) if union else 0.0,
        "persist_rate": (len(inter) / len(s1)) if s1 else 0.0,
    }


def _records_from_answers(answers: pd.DataFrame) -> pd.DataFrame:
    """Collapse a per-(qid,model) answer table into per-question silent_consensus,
    reusing the same disagreement scoring as the main pipeline.

    The gradeable filter below is NOT optional: disagree.run() drops
    gradeable == False rows (TruthfulQA's "I have no comment" golds, where no
    correctness label exists). Without the same filter here, the two Track arms
    are built over different question populations and the overlap compares
    mismatched sets -- biasing persistence in an unknown direction.
    """
    if "gradeable" in answers.columns:
        answers = answers[answers["gradeable"]]
    rows = []
    for qid, grp in answers.groupby("qid"):
        s = score(grp["answer"].tolist(), grp["confidence"].tolist())
        allwrong = bool((~grp["correct"]).all())
        rows.append({"qid": qid, "n_clusters": s["n_clusters"],
                     "silent_consensus": (s["n_clusters"] == 1 and allwrong)})
    return pd.DataFrame(rows)


def generate_older(pilot: bool = True, ensemble: str = "ensemble_gen2",
                   tag: str = "_older") -> pd.DataFrame:
    """Run an OLDER ensemble on the frozen questions.

    Parameterised rather than hardcoded: this used to read CFG["ensemble_gen1"],
    which no longer exists (that arm was dropped -- three makers vs four, plus
    4-bit-vs-full-precision, made it uncomparable). Naming the config key here
    means Track arms are chosen at the call site instead of by editing config.
    """
    from faultlines.generate import ask_retry

    q = pd.read_parquet(stage("interim", "questions", pilot, ""))
    dest = stage("interim", "answers", pilot, tag)

    rows, done = [], set()
    if dest.exists():
        prev = pd.read_parquet(dest)
        # SUCCESSES ONLY -- a failed row carries confidence NaN, and counting it
        # as done turns a transient timeout into permanent missing data.
        good = prev[prev["confidence"].notna()]
        rows = good.to_dict("records")
        done = set(zip(good["model"], good["qid"]))
        if len(prev) > len(good):
            print(f"retrying {len(prev) - len(good)} previously failed")

    for spec in CFG[ensemble]:
        m = spec["name"]
        todo = [it for _, it in q.iterrows() if (m, it["qid"]) not in done]
        print(f"  {m}: {len(todo)} questions")
        for j, it in enumerate(todo, 1):
            a, c = ask_retry(m, it["question"], dataset=it["dataset"], label=it["qid"])
            ok = grade_one(a, it["gold"], it["aliases"], it["dataset"])[0]
            rows.append({"qid": it["qid"], "model": m, "answer": a,
                         "confidence": c, "correct": ok, "dataset": it["dataset"]})
            if j % 25 == 0 or j == len(todo):
                pd.DataFrame(rows).to_parquet(dest)
    out = pd.DataFrame(rows)
    out.to_parquet(dest)
    print(f"wrote {dest.name}")
    return out


def run(pilot: bool = True, old_tag: str = "_gen2h", new_tag: str = "_gen3") -> dict:
    """Compare two tagged arms. Both must come from the SAME pipeline path
    (generate -> grade -> nli -> disagree) or the populations will not match."""
    new_path = stage("processed", "records", pilot, new_tag)
    old_path = stage("processed", "records", pilot, old_tag)
    for p_ in (old_path, new_path):
        if not p_.exists():
            print(f"missing {p_.name}. Run the pipeline for that tag first.")
            return {}
    gen1 = pd.read_parquet(old_path)
    gen2 = pd.read_parquet(new_path)
    p = persistence(gen1, gen2)
    print("=" * 60)
    print("RQ3  DO SILENT-CONSENSUS BLIND SPOTS PERSIST?")
    print(f"     {old_tag} -> {new_tag}")
    print("=" * 60)
    print(f"  older silent : {p['gen1_silent']}")
    print(f"  newer silent : {p['gen2_silent']}")
    print(f"  persistent core : {p['persistent_core']}   "
          f"(persist rate {p['persist_rate']:.0%}, Jaccard {p['jaccard']:.2f})")
    print(f"  healed by upgrade : {p['healed']}   newly emerged : {p['emerged']}")
    return p


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", default=True)
    ap.add_argument("--full", dest="pilot", action="store_false")
    ap.add_argument("--generate", action="store_true",
                    help="run the OLDER ensemble named by --ensemble")
    ap.add_argument("--ensemble", default="ensemble_gen2")
    ap.add_argument("--old-tag", default="_gen2h")
    ap.add_argument("--new-tag", default="_gen3")
    a = ap.parse_args()
    if a.generate:
        generate_older(a.pilot, a.ensemble, a.old_tag)
    else:
        run(a.pilot, a.old_tag, a.new_tag)
