"""Level 1 — sample the three datasets into one normalised table.

Three datasets, three jobs:
  PopQA      an obscurity dial (popularity is a real number per question) -> Forecast
  SimpleQA   a clean short answer key                                     -> Type
  TruthfulQA questions built to bait a confident wrong answer             -> Audit

Output: data/interim/questions.parquet with QUESTION_COLS.
Sampling is seeded, so this is reproducible.

    python -m faultlines.datasets --pilot
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from .config import CFG, SEED, path

# HF column names differ per dataset. If a loader below raises KeyError, print
# ds.column_names and fix the mapping here -- that is the only thing that rots.


def _popqa(ds) -> pd.DataFrame:
    return pd.DataFrame({
        "question": ds["question"],
        # possible_answers ships as a JSON-encoded list string
        "gold": [json.loads(a)[0] for a in ds["possible_answers"]],
        "aliases": [json.loads(a) for a in ds["possible_answers"]],
        # s_pop = subject popularity (Wikipedia pageviews). This IS the
        # obscurity dial Forecast leans on -- carry it through.
        "meta": [{"s_pop": s, "o_pop": o, "prop": p}
                 for s, o, p in zip(ds["s_pop"], ds["o_pop"], ds["prop"])],
    })


def _simpleqa(ds) -> pd.DataFrame:
    return pd.DataFrame({
        "question": ds["problem"],
        "gold": ds["answer"],
        "aliases": [[a] for a in ds["answer"]],
        "meta": [{"topic": m} for m in ds["metadata"]],
    })


def _truthfulqa(ds) -> pd.DataFrame:
    return pd.DataFrame({
        "question": ds["question"],
        "gold": ds["best_answer"],
        "aliases": ds["correct_answers"],
        # incorrect_answers = the baited answers. Audit needs these to tell
        # "all four agreed on the trap" apart from "all four were wrong in
        # four different ways". category is TruthfulQA's own taxonomy
        # (Misconceptions, Superstitions, ...) -- a free external check on
        # whether Diagnose's cause labels line up with anything real.
        "meta": [{"incorrect": i, "category": c, "type": t}
                 for i, c, t in zip(ds["incorrect_answers"], ds["category"], ds["type"])],
    })


def _triviaqa(ds) -> pd.DataFrame:
    """answer is a struct: {value, aliases, normalized_aliases, ...}.

    The alias list is unusually rich here (every Wikipedia redirect for the
    entity), which is exactly why TriviaQA needs no NLI tier -- the exact/alias
    tiers catch almost everything and the semantic tier rarely fires.
    """
    return pd.DataFrame({
        "question": ds["question"],
        "gold": [a["value"] for a in ds["answer"]],
        "aliases": [list(a.get("aliases") or []) for a in ds["answer"]],
        "meta": [{} for _ in ds["question"]],
    })


def _halueval(ds) -> pd.DataFrame:
    """HaluEval QA ships right_answer AND hallucinated_answer per question.

    The hallucinated answer is carried in meta under the SAME key TruthfulQA
    uses ("incorrect"), so nli.py's entailment grader works on both without a
    special case -- and so Audit can tell "all four fell for the same specific
    trap" apart from "all four were wrong in four different ways".
    """
    return pd.DataFrame({
        "question": ds["question"],
        "gold": ds["right_answer"],
        "aliases": [[a] for a in ds["right_answer"]],
        "meta": [{"incorrect": [h], "knowledge": k}
                 for h, k in zip(ds["hallucinated_answer"], ds["knowledge"])],
    })


LOADERS = {"popqa": _popqa, "simpleqa": _simpleqa, "truthfulqa": _truthfulqa,
           "triviaqa": _triviaqa, "halueval": _halueval}


def filter_non_adversarial(df: pd.DataFrame) -> pd.DataFrame:
    """Drop TruthfulQA's Adversarial rows (selected against GPT-3), keeping only
    the Non-Adversarial subset. Removing that selection pressure is what makes a
    cross-generation persistence test (RQ3) valid rather than confounded."""
    keep = df["meta"].map(lambda m: (m or {}).get("type") != "Adversarial")
    return df[keep].reset_index(drop=True)


def build(pilot: bool = True) -> pd.DataFrame:
    from datasets import load_dataset  # heavy import, keep it local

    n_key = "n_pilot" if pilot else "n_full"
    frames = []
    for name, spec in CFG["datasets"].items():
        args = [spec["hf_id"]] + ([spec["subset"]] if "subset" in spec else [])
        ds = load_dataset(*args, split=spec["split"])
        df = LOADERS[name](ds)
        if spec.get("non_adversarial"):
            before = len(df)
            df = filter_non_adversarial(df)
            print(f"  {name}: kept {len(df)}/{before} non-adversarial")
        n = min(spec[n_key], len(df))
        df = df.sample(n=n, random_state=SEED).reset_index(drop=True)
        df.insert(0, "dataset", name)
        df.insert(0, "qid", [f"{name}-{i:05d}" for i in range(n)])
        frames.append(df)
        print(f"  {name:11s} {n:5d} sampled from {len(ds)}")

    out = pd.concat(frames, ignore_index=True)
    dest = path("interim", "questions_pilot.parquet" if pilot else "questions.parquet")
    out.to_parquet(dest)
    print(f"-> {dest}  ({len(out)} questions)")
    return out



def _dup_key(df: pd.DataFrame) -> pd.Series:
    norm = lambda s: (s.astype(str).str.lower()
                      .str.replace(r"\s+", " ", regex=True).str.strip())
    sep = "\x1f"                      # ASCII unit separator: in no question
    return df["dataset"] + sep + norm(df["question"]) + sep + norm(df["gold"])


def duplicate_qids(questions: pd.DataFrame | None = None) -> set:
    """qids that repeat an earlier question: same dataset, same text, same gold.

    ISSUES #66. TriviaQA's rc.wikipedia and rc.web configurations carry the SAME
    question under two ids, and sampling from their union put 7,982 questions
    into the corpus twice -- 17,944 TriviaQA rows were 9,962 questions. PopQA
    adds a few hundred rows whose template, subject label and answer are all
    identical. A model cannot tell such a pair apart, so they are one question
    counted twice: they inflate every n, narrow every interval, and in a
    row-wise cross-validation one twin trains the model that scores the other.

    The EARLIER qid (sorted order) is kept, so the choice is deterministic and
    identical for every arm that shares the question set. PopQA rows that share
    a question text but not a gold answer (two films called "Crash") are NOT
    duplicates -- they are different questions that happen to read the same,
    and RQ2's shared-title finding is built on exactly them.

    Every stage that defines the analysed population calls this; nothing
    downstream should re-derive it.
    """
    q = questions if questions is not None else         pd.read_parquet(path("interim", "questions.parquet"))
    q = q.sort_values("qid")
    return set(q.loc[_dup_key(q).duplicated(keep="first"), "qid"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="use n_pilot counts")
    build(pilot=ap.parse_args().pilot)
