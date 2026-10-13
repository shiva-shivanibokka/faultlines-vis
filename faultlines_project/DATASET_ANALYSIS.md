# Why SimpleQA and TruthfulQA score low — and whether more data fixes it

> Moved from `data/processed/` 2026-07-27. It was buried next to the parquet
> artifacts, which is why its decisive result (label noise is NOT the cause of
> TruthfulQA's weak AUC) went unnoticed for a week. Conclusions still hold; the
> 2026-07-27 scale test then identified the actual cause as MODEL SIZE — see
> RESULTS.md.

Analysis run 2026-07-19 on the 300-question pilot.
**Short answer: no, a bigger sample does not fix either one.**

---

## 1. The 50 low-margin TruthfulQA cases were labelled

50 lowest-margin NLI verdicts (|margin| 0.0000–0.0030) were re-judged case by
case against TruthfulQA's own correct/incorrect answer lists.

> ⚠️ **These are LLM-judge labels, not human labels.** They are a stronger
> grader than the small NLI cross-encoder, but still a model. They do **not**
> satisfy the proposal's hand-labelling methodology, and they cannot be reported
> as inter-annotator agreement. The blank `human_label` column in
> `truthfulqa_lowmargin_50.csv` is there for real human labels.

| | |
|---|---|
| agreement with NLI | **31/50 = 62%** |
| **Cohen's kappa** | **0.240** (poor — barely above chance) |
| NLI said RIGHT | 28 |
| judge said RIGHT | 25 |

NLI's failures on these were not subtle. It graded **"Newton won the Physics
Nobel Prize in 1705"** as RIGHT, and **"Einstein performed averagely in high
school"** — the exact baited myth — as RIGHT. In the other direction it marked
correct answers wrong, e.g. one that properly rejects the Longfellow-invented
"The British are coming" quote.

**Conclusion: low-margin NLI verdicts are near-arbitrary.** Confirmed, not
suspected.

## 2. But label noise is NOT why TruthfulQA scores 0.534

This was the decisive test. Correcting all 19 disagreements and recomputing:

| labels | TruthfulQA AUC | overall AUC |
|---|---|---|
| NLI | 0.534 | 0.776 |
| judge-corrected | **0.551** | 0.778 |

Fixing every bad label moved it **0.017**. Still a coin flip.

**The weak TruthfulQA signal is real, not a grading artifact.**

## 3. Will a bigger sample help? No.

Bootstrapped AUC at increasing n, 1000 resamples each:

| dataset | n=25 | n=50 | n=75 | n=100 | CI width at n=100 |
|---|---|---|---|---|---|
| PopQA | 0.843 | 0.843 | 0.844 | 0.843 | 0.198 |
| SimpleQA | 0.690 | 0.683 | 0.687 | 0.684 | 0.263 |
| TruthfulQA | 0.531 | 0.530 | 0.537 | 0.530 | 0.256 |

**The point estimates are flat.** Only the confidence interval narrows. Scaling
to 1000 questions per dataset buys *precision on the same number* — it does not
move the number.

This is the general principle worth stating in the write-up: **more data reduces
variance, not bias.** Neither of these problems is a variance problem.

## 4. What each problem actually is

### SimpleQA — a floor effect, not a signal failure

**91% of ensemble answers are wrong.** With ~9 correct answers in 100, there is
almost nothing for the score to separate. That ratio is scale-invariant: 1000
questions gives ~90 negatives instead of ~9 — steadier, same ceiling.

SimpleQA was built so that *frontier* models score ~40%. Handing it to 7–8B
models produces a floor effect by design.

**Options:**

1. **Reframe its job (recommended).** SimpleQA's value to this project is its
   clean, unambiguous answer key, which is what **Type (Finding A)** needs. It
   was never the detection dataset. Report its AUC honestly and explain the floor
   effect rather than treating 0.687 as a disappointment.
2. **Stratify by difficulty.** Sample within SimpleQA's `answer_type` and `topic`
   metadata to build a tractable slice with a workable correct/incorrect balance.
   Principled, and it makes the difficulty gradient itself a variable.
3. **Do not** simply add more SimpleQA questions expecting improvement.

### TruthfulQA — the weak signal IS the finding

Class balance is fine (33% positives). Labels are not the cause (§2). What is
left is the substantive explanation:

**TruthfulQA is built from misconceptions that models share.** When all four
models absorb the same myth from the same web corpus, they agree — and
agreement is exactly what this method reads as "safe". Disagreement cannot
detect a fault that every model has.

That is not a failure of the project. **It is Audit's founding premise,
measured.** The honest framing:

> Cross-model disagreement detects errors that arise from *differing* knowledge
> (PopQA, AUC 0.845). It is near-blind to errors from *shared* misconceptions
> (TruthfulQA, AUC 0.534). That blind spot is not incidental — it is structural,
> and quantifying it is what Audit is for.

This turns the weakest number in the report into a defensible result, and it
predicts something checkable: silent-consensus cases should concentrate where
disagreement is low and error is high.

## 5. What to do instead of scaling

| goal | do this | not this |
|---|---|---|
| tighter intervals | scale to 2,800 as planned | — |
| better SimpleQA numbers | stratify by difficulty; reframe its role as Type's dataset | add more SimpleQA questions |
| explain TruthfulQA | report the shared-misconception blind spot as an Audit result | chase a higher AUC |
| trustworthy TruthfulQA labels | human-label the ~34% low-margin cases | trust NLI on them |
| stronger detection claim | combine disagreement + confidence as features (ISSUES.md item A) | keep multiplying them |

**One genuinely useful scale-up:** more data *would* help the Audit population,
which is currently 5 cases. That is a counting problem, and counting problems do
improve with n.
