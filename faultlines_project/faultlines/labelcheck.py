"""Issue B — is TruthfulQA's 0.534 AUC a FINDING, or is it label noise?

THE QUESTION
TruthfulQA scores 0.534 against majority_wrong -- a coin flip. Two readings, and
until now nothing separated them:

  1. GENUINE. TruthfulQA is built so models fail *together* on shared
     misconceptions. Disagreement cannot detect a fault everyone shares. That
     makes 0.534 the expected result and it strengthens the Audit narrative.
  2. LABEL NOISE. 31% of NLI verdicts have a margin below 0.10, i.e. the
     entailment model could not separate the correct answer from the baited one
     either. Enough noise in the labels flattens any AUC toward 0.5.

THE TEST
Hand-label a sample of the low-margin band, then ask how often the automatic
grader agreed with a human ON EXACTLY THE CASES IT FOUND HARDEST:

  high agreement -> the labels are sound even where the margin is thin, so the
                    flat AUC is not coming from the labels. Reading 1 holds.
  low agreement  -> the verdicts in that band are near-arbitrary, 0.534 is not
                    interpretable, and it must be reported as a limitation.

The CSV also carries an independent llm_judge_label, so this doubles as the
inter-annotator agreement work: human vs NLI, human vs LLM judge, NLI vs LLM
judge, three ways.

WHAT THIS DOES NOT CLAIM
The 50 rows are a SAMPLE of the low-margin band, not the whole of it. Splicing
them back in gives a partial correction and a direction of travel -- it is not a
clean-label AUC, and the report says so rather than pretending otherwise.

    python -m faultlines.labelcheck --pilot
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from .config import path
from .evaluate import TARGET, auc, read_auc

CSV = "truthfulqa_lowmargin_50.csv"

# What counts as a decision. Anything else (blank, "?", "AMBIGUOUS") means the
# human declined to call it, which is itself informative and is reported
# separately rather than being coerced into a verdict.
VERDICTS = {"CORRECT", "WRONG"}


def normalize(label) -> str | None:
    """'correct ' -> 'CORRECT'. Returns None for anything that isn't a verdict."""
    if label is None or (isinstance(label, float) and np.isnan(label)):
        return None
    s = str(label).strip().upper()
    if s in VERDICTS:
        return s
    # tolerate the obvious shorthands rather than silently dropping the row
    return {"C": "CORRECT", "W": "WRONG", "RIGHT": "CORRECT",
            "TRUE": "CORRECT", "FALSE": "WRONG"}.get(s)


def agreement(a: list[str], b: list[str]) -> dict:
    """Raw agreement + Cohen's kappa over two label vectors.

    Kappa matters here because raw agreement lies when the classes are skewed:
    if 90% of the band is WRONG, a grader that always says WRONG scores 90%
    agreement while carrying no information at all. Kappa corrects for exactly
    that chance agreement.

    Returns nan kappa (not an exception) when only one class is present -- on a
    50-row sample that is a real possibility, and it means 'undefined', not 0.
    """
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return {"n": 0, "raw": float("nan"), "kappa": float("nan")}
    x, y = zip(*pairs)
    raw = float(np.mean([i == j for i, j in zip(x, y)]))
    single_class = len(set(x) | set(y)) < 2
    return {
        "n": len(pairs),
        "raw": raw,
        "kappa": float("nan") if single_class else float(cohen_kappa_score(x, y)),
    }


def read_kappa(k: float) -> str:
    """Landis & Koch bands, the convention this literature reports against."""
    if np.isnan(k):
        return "undefined - only one class in the sample"
    if k >= 0.81:
        return "almost perfect"
    if k >= 0.61:
        return "substantial - labels are sound"
    if k >= 0.41:
        return "moderate - treat with caution"
    if k >= 0.21:
        return "fair - the band is close to arbitrary"
    return "poor - these verdicts carry no information"


def load_labeled() -> pd.DataFrame:
    """The hand-label CSV, with every label column normalized."""
    df = pd.read_csv(path("processed", CSV), encoding="utf-8-sig")
    for col in ("human_label", "nli_verdict", "llm_judge_label"):
        df[col] = df[col].map(normalize) if col in df.columns else None
    return df


def regrade(df: pd.DataFrame, pilot: bool = True) -> dict:
    """Splice the human labels into the answers and recompute the TruthfulQA AUC.

    Deliberately operates on an in-memory copy: this is a what-if, and it must
    not overwrite the real graded parquet that every other result depends on.
    """
    from .disagree import score, ensemble_answer_correct  # late: pulls in the transformer

    answers = pd.read_parquet(
        path("interim", "answers_pilot.parquet" if pilot else "answers.parquet"))
    if "gradeable" in answers.columns:
        answers = answers[answers["gradeable"]]

    truth = answers[answers["dataset"] == "truthfulqa"].copy()
    if truth.empty:
        return {"error": "no truthfulqa rows in the answers parquet"}

    decided = df[df["human_label"].notna()]
    key = {(r.qid, r.model): r.human_label == "CORRECT"
           for r in decided.itertuples()}

    patched = truth.copy()
    hits = patched.apply(lambda r: (r["qid"], r["model"]) in key, axis=1)
    patched.loc[hits, "correct"] = [
        key[(r["qid"], r["model"])] for _, r in patched[hits].iterrows()]

    def majority_wrong_auc(frame: pd.DataFrame) -> float:
        rows = []
        for qid, g in frame.groupby("qid", sort=False):
            s = score(g["answer"].tolist(), g["confidence"].tolist())
            ids = s["clusters"]
            rows.append({
                "disagreement_unweighted": s["disagreement_unweighted"],
                TARGET: not ensemble_answer_correct(
                    ids, g["confidence"].tolist(), g["correct"].tolist()),
            })
        r = pd.DataFrame(rows)
        return auc(r[TARGET].values, r["disagreement_unweighted"].values)

    return {
        "spliced": int(hits.sum()),
        "flipped": int((patched.loc[hits, "correct"]
                        != truth.loc[hits, "correct"]).sum()),
        "auc_before": majority_wrong_auc(truth),
        "auc_after": majority_wrong_auc(patched),
    }


def run(pilot: bool = True, skip_auc: bool = False) -> pd.DataFrame:
    df = load_labeled()
    done = int(df["human_label"].notna().sum())
    total = len(df)

    print(f"hand-labelled  {done}/{total}")
    if done == 0:
        print(f"\nNothing to check yet. Open data/processed/{CSV}, fill the")
        print("human_label column with CORRECT or WRONG, save, and re-run.")
        print("Judge the ANSWER against the question and the correct_answers")
        print("column -- do not look at nli_verdict first, it biases the label.")
        return df
    if done < total:
        print(f"({total - done} rows still blank -- numbers below are partial)")

    h = df["human_label"].tolist()
    print("\n-- agreement on the low-margin band --")
    for name, other in (("NLI grader", "nli_verdict"),
                        ("LLM judge", "llm_judge_label")):
        if other not in df.columns:
            continue
        a = agreement(h, df[other].tolist())
        print(f"human vs {name:<11} n={a['n']:<3} raw {a['raw']:.0%}  "
              f"kappa {a['kappa']:.2f}  {read_kappa(a['kappa'])}")

    if {"nli_verdict", "llm_judge_label"} <= set(df.columns):
        a = agreement(df["nli_verdict"].tolist(), df["llm_judge_label"].tolist())
        print(f"NLI  vs LLM judge   n={a['n']:<3} raw {a['raw']:.0%}  "
              f"kappa {a['kappa']:.2f}  {read_kappa(a['kappa'])}")

    nli = agreement(h, df["nli_verdict"].tolist())
    print("\n-- verdict --")
    if np.isnan(nli["kappa"]):
        print("Undefined: the sample has only one class. Label more rows.")
    elif nli["kappa"] >= 0.61:
        print("The grader agrees with a human even where its margin was thinnest,")
        print("so the flat TruthfulQA AUC is NOT an artefact of the labels.")
        print("Reading 1 holds: the models fail TOGETHER on shared misconceptions,")
        print("which is a fault disagreement cannot see. That is a finding, and it")
        print("is the strongest evidence the Audit narrative has.")
    else:
        print("The grader does not track a human in this band, so the TruthfulQA")
        print("verdicts there are near-arbitrary and 0.534 is not interpretable.")
        print("Report the low-margin rate as a limitation and do not lean on any")
        print("TruthfulQA AUC without cleaner labels.")

    if not skip_auc:
        print("\n-- what-if: human labels spliced back in --")
        r = regrade(df, pilot=pilot)
        if "error" in r:
            print(r["error"])
        else:
            print(f"rows replaced  {r['spliced']}  (verdict changed on {r['flipped']})")
            print(f"truthfulqa AUC {r['auc_before']:.3f} -> {r['auc_after']:.3f}  "
                  f"({read_auc(r['auc_after'])})")
            print("PARTIAL correction -- these are a sample of the low-margin band,")
            print("not all of it. Read the direction, not the decimal.")
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--skip-auc", action="store_true",
                    help="agreement only; skips loading the sentence transformer")
    a = ap.parse_args()
    run(pilot=a.pilot, skip_auc=a.skip_auc)
