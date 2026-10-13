"""The 300-question pilot. Run this BEFORE building anything else.

It answers the one question that sits upstream of the whole project:
do the four models fail differently enough for disagreement to mean anything?

    python scripts/run_pilot.py                 # everything
    python scripts/run_pilot.py --skip-baseline # 4x faster, no Level 6 numbers
    python scripts/run_pilot.py --report-only   # re-print from existing parquet

Each stage is resumable, so a crash costs minutes, not the whole run.
"""
from __future__ import annotations

import argparse
import functools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Python block-buffers stdout when it is redirected to a file, so a run piped
# to a log shows nothing for an hour and looks hung. Flush every print.
print = functools.partial(print, flush=True)  # noqa: A001

import pandas as pd

from faultlines import baseline, datasets, disagree, embed, evaluate, generate, grade, nli
from faultlines.config import stage

pd.set_option("display.width", 120)


def rule(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def report(tag: str = "") -> None:
    answers = pd.read_parquet(stage("interim", "answers", True, tag))
    records = pd.read_parquet(stage("processed", "records", True, tag))
    bl_path = stage("interim", "baseline", True, tag)
    bl = pd.read_parquet(bl_path) if bl_path.exists() else None
    print(f"(reporting on tag {tag!r})")

    rule("1. DOES EACH MODEL ACTUALLY WORK?")
    print(answers.groupby("model").agg(
        accuracy=("correct", "mean"),
        mean_confidence=("confidence", "mean"),
        empty_answers=("answer", lambda s: (s.str.len() == 0).sum()),
    ).round(3).to_string())
    print("\nAn accuracy near zero usually means the prompt is being ignored,")
    print("not that the model is bad. Eyeball a few answers before believing it.")

    rule("1b. HOW MUCH IS THE GRADER GUESSING?")
    print(pd.crosstab(answers["dataset"], answers["tier"]).to_string())
    tqa = answers[answers["dataset"] == "truthfulqa"]
    sem_rate = (tqa["tier"] == "semantic").mean() if len(tqa) else 0
    nli_rate = (tqa["tier"] == "nli").mean() if len(tqa) else 0

    if nli_rate > 0.5:
        thin = (answers["nli_margin"].abs() < 0.10).sum() if "nli_margin" in answers else 0
        n_tqa = len(tqa)
        print(f"\nTruthfulQA is graded by NLI entailment ({nli_rate:.0%} of its rows).")
        print("Cosine is not used there: it is blind to negation ('bears wear armor'")
        print("scores >0.80 against 'bears do not wear armor'), which on this dataset")
        print("turns real errors into apparent successes.")
        print(f"\nBut {thin} of {n_tqa} NLI verdicts ({thin / max(1, n_tqa):.0%}) have a margin")
        print("below 0.10 -- the entailment model could not separate the correct answer")
        print("from the baited one either. Those verdicts are near-arbitrary, and they")
        print("are the leading suspect for TruthfulQA's weak AUC in section 3.")
        print("  >> hand-label ~50 of them to find out whether the weak AUC is real")
        print("     signal loss or just label noise.")
    else:
        print(f"\nTruthfulQA decided by the negation-blind semantic tier: {sem_rate:.1%}")
        if sem_rate > 0.35:
            print("  >> HIGH. Run `python -m faultlines.nli --pilot` before believing")
            print("     any TruthfulQA or Audit number.")

    rule("2. THE UPSTREAM RISK: DO THEY FAIL DIFFERENTLY?")
    corr = evaluate.pairwise_error_correlation(answers)
    print(corr.round(3).to_string())
    vals = [corr.iloc[i, j] for i in range(len(corr)) for j in range(len(corr)) if i < j]
    mean_corr = sum(vals) / len(vals) if vals else float("nan")
    print(f"\nmean off-diagonal correlation: {mean_corr:.3f}")
    if mean_corr >= 0.8:
        print("  >> TOO ALIKE. Swap one model for a different TRAINING RECIPE")
        print("     (synthetic-data-trained), not for a bigger model.")
        print("     Hedge: high correlation also means MORE silent-consensus")
        print("     cases, which makes Audit richer, not poorer.")
    elif mean_corr >= 0.3:
        print("  >> healthy diversity. proceed to the full run.")
    else:
        print("  >> unusually low. check the grader is not marking everything wrong.")

    rule("3. THE SIGNAL: DOES DISAGREEMENT PREDICT ERROR?")
    print(f"target: {evaluate.TARGET}  (is the answer the ensemble would give wrong?)\n")
    print(evaluate.compare(records, bl).round(3).to_string(index=False))
    print("\n0.50 useless | 0.70 respectable | 0.80 strong | 0.95+ suspect a leak")
    print("anchors: Farquhar 0.790 | Gorbett 0.727 cross vs 0.595 single")

    print("\nper dataset:")
    for ds, g in records.groupby("dataset"):
        v = evaluate.auc(g[evaluate.TARGET].values, g["disagreement"].values)
        base = g[evaluate.TARGET].mean()
        print(f"  {ds:12s} {v:.3f}  ({base:.0%} of questions are positives)  "
              f"{evaluate.read_auc(v)}")
    print("\nA dataset where nearly every answer is wrong has almost no negatives")
    print("left to separate, so its AUC is unstable regardless of the signal.")

    rule("3b. SANITY: IS THE LABEL IMPLIED BY THE SCORE?")
    print(pd.crosstab(records["n_clusters"], records["any_wrong"],
                      normalize="index").round(3).to_string())
    print("\nRows for n_clusters > 1 sitting near 1.00 are EXPECTED and are why")
    print("any_wrong is not the target: one gold answer means N different answers")
    print("cannot all match, so 'someone was wrong' follows by arithmetic.")
    infl = evaluate.auc(records["any_wrong"].values, records["disagreement"].values)
    real = evaluate.auc(records[evaluate.TARGET].values, records["disagreement"].values)
    print(f"\nAUC vs any_wrong      {infl:.3f}  <- inflated, do not report this")
    print(f"AUC vs {evaluate.TARGET:14s} {real:.3f}  <- the honest number")

    rule("4. THE BLIND SPOT: HOW BIG IS THE AUDIT POPULATION?")
    sc = records.groupby("dataset")["silent_consensus"].agg(["sum", "mean", "count"])
    print(sc.rename(columns={"sum": "silent", "mean": "rate", "count": "n"})
          .round(3).to_string())
    total = int(records["silent_consensus"].sum())
    print(f"\n{total} all-agree-all-wrong cases in this pilot.")
    print("These score near zero disagreement and drag the AUC DOWN while being")
    print("genuine errors -- which is exactly why Audit is a separate finding.")
    if total < 10:
        print("  >> thin. If it stays thin at full scale, pull silent-consensus")
        print("     cases from all three datasets rather than TruthfulQA alone.")

    rule("WHAT TO DO NEXT")
    print("correlation healthy + AUC >= 0.65  -> proceed to the full 2,800 run")
    print("correlation 0.8+                   -> swap a model, re-run this pilot")
    print("AUC ~= 0.50                        -> stop. scope conversation with")
    print("                                      your advisor before building more.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-baseline", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--tag", default="",
                    help="output suffix, e.g. _gen3. Runs with different tags "
                         "never touch each other's files.")
    ap.add_argument("--ensemble", default="ensemble",
                    help="config key: ensemble | ensemble_gen2 | ensemble_gemma_ladder")
    ap.add_argument("--rebuild-questions", action="store_true",
                    help="DESTRUCTIVE. Regenerate questions_pilot.parquet from the "
                         "CURRENT dataset config. This replaces the frozen question "
                         "set and orphans every existing answers/records file, "
                         "because qids are rebuilt from scratch.")
    a = ap.parse_args()

    if not a.report_only:
        # The question set is NOT rebuilt by default. It used to be, which made
        # the documented no-flag invocation destroy the frozen 300-question pilot
        # AND overwrite answers_pilot.parquet with whatever ensemble config
        # currently pointed at -- erasing the local 7-9B arm of the two-scale
        # study, which is days of laptop GPU time and cannot be regenerated now
        # that config points at hosted models.
        if a.rebuild_questions:
            rule("LEVEL 1  sample the datasets (REBUILDING - destructive)")
            datasets.build(pilot=True)
        else:
            rule("LEVEL 1  skipped -- reusing the existing question set")
            print("pass --rebuild-questions to regenerate it (destroys prior runs)")
        rule("LEVEL 2  ask the models");        generate.run(pilot=True, tag=a.tag, ensemble=a.ensemble)
        rule("LEVEL 3  grade every answer");    grade.run(pilot=True, tag=a.tag)
        rule("LEVEL 3b re-grade TruthfulQA by NLI"); nli.run(pilot=True, tag=a.tag)
        rule("LEVEL 4  score disagreement");    disagree.run(pilot=True, tag=a.tag)
        rule("LEVEL 5  map the questions");     embed.run(pilot=True, tag=a.tag)
        if not a.skip_baseline:
            rule("LEVEL 6  semantic entropy baseline")
            baseline.run(pilot=True, tag=a.tag, ensemble=a.ensemble)

    report(tag=a.tag)


if __name__ == "__main__":
    main()
