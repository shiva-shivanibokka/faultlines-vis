# FaultLines — Results

> ## 2026-09-27 · Every figure in this file's top sections was re-derived
>
> On 27 Sep 2026 an adversarial review (ISSUES #66–#78) found that the corpus
> held **8,489 duplicate questions**, that `majority_wrong` broke ties by taking
> Llama's answer, and that the independence ratio pooled strata of very
> different difficulty. All three are fixed. **Every figure in the claims table,
> the interval table, the per-dataset and abstention tables and the Findings
> text quoted below was re-derived on the deduplicated corpus — 42,591 asked →
> 40 ungradeable → 8,489 duplicates → 34,062 analysed** — from
> `faultlines-web/summary.json` as regenerated that day by
> `scripts/export_web.py`, or from the named script re-run that day.
>
> **Earlier figures are superseded.** The dated sections further down are the
> project's history and are kept as written; where one of them would otherwise
> be quoted it carries a *superseded* marker. The three results that waited on
> a paid re-run (ISSUES #70, #71, #76) were re-run the same day, 27 Sep, with
> 0 failed calls; their figures below are final.

## WHAT TO QUOTE — the claims table

Every number below is measured on the full deduplicated corpus (34,062
questions) unless the *n* column says otherwise, and is read from
`summary.json` (block named in brackets) unless stated. If a claim is not in this
table, it is not ready to quote.

| # | claim | quote this | n | the caveat that must travel with it |
|---|---|---|---|---|
| 1 | Cross-model disagreement predicts ensemble error | **AUC 0.840** [0.836, 0.845] (`intervals.auc`) | 34,062 | head-count; weighted is 0.844. Compare only against claim 2's within-study baseline. Was 0.862 before dedup and the tie-rule fix (ISSUES #66, #67); the principled tie rule gives the *lowest* AUC of every rule tried |
| 2 | It beats single-model Semantic Entropy | **0.838 vs 0.778**, Δ **+0.060** [+0.050, +0.070] (`intervals.vs_semantic_entropy`, `baseline`) | 6,436 | same qids, same budget, **same head-count score as claim 1**; best single model is Mistral-Small-3.2. The 300-q pilot said the *opposite* |
| 3 | Shared blind spots exist and are measurable | **950** (2.79% [2.62%, 2.97%]) (`intervals.blind_rate`) | 34,062 | **an upper bound. 21.05% [18.58%, 23.76%] of the 950 are answer-key artifacts (200 of 950; every case decided, 0 undecided) — so 750 genuine, nearer 2.2%** (`artifact`). The 45 failed adjudication calls were re-run 27 Sep (ISSUES #71). Never quote 950 without it |
| 4 | They are not where the proposal predicted | **99.5% outside TruthfulQA** (945 of 950) | 34,062 | — |
| 5 | A larger share of errors is shared in the newer ensemble (one generation pair, 2024 → 2025) | **4.52% → 6.79%** shared share, ratio **1.50×** [1.39, 1.62] (`rq3`, `intervals.share_ratio`) | 34,062 | wrong-rate falls 53.45% → 41.08% at the same time. This is the safety argument. The *number* of genuine blind spots does not rise significantly (698 → 750, p = 0.101; claim 5b below) |
| 6 | Blind spots survive a model generation | **38.9%** (320/823) (`rq3.persistence`) | exact, both arms | quote 33.7% only for the *inherited share* (320/950) |
| 7 | An upgrade **hides** more than it inherits | **630 newly hidden vs 320 hidden in both** (1.97×) | exact | the axis is **detectability, not correctness** — 80% of the 630 (505) were already all wrong in 2024, they merely stopped disagreeing. Never write "newly broken" (2026-08-01 correction) |
| 8 | Retrieval fixes ignorance, not belief | **+65.2 vs +14.0 percentage points**, dissociation **+51.2 points** [+36.9, +65.3] (`intervals.rq4`) | 500 / 57 | re-run 27 Sep on the strata re-selected after #66/#67, 0 empty answers (ISSUES #70). **The misconception lift alone is no longer significant** (exact McNemar p = 0.077): retrieval *barely moves* misconceptions. The dissociation is the claim |
| 9 | Confidence-weighting is a wash at scale | **+0.004** (0.840 → 0.844) (`signal.overall`) | 34,062 | it *hurts* at 7–9B (−0.012, pilot scale, not re-derived). Never quote +0.008 alone |
| 10 | Hand-labelling ~~raises~~ does **not detectably** change TruthfulQA's AUC | **+0.042** (CI −0.000 – +0.089, **crosses zero**) | 340 | re-run 27 Sep (`handlabel.py --result`), 13 verdicts flip. Now on the HEAD-COUNT score like every other AUC (ISSUES #78; it had run on the weighted one). The claim that correcting labels raises the AUC is **withdrawn**: the direction is positive, the interval includes zero. Quote the delta and its interval, never the bare 0.725 |
| 11 | 4-bit quantization does not degrade the signal | aggregates stable; **weighted Jaccard 0.644**, agreement **94.4%** | 2,152 | re-run 27 Sep (`compare_precision.py`), stratum-weighted (ISSUES #75; unweighted 0.777 / 96.2%). **About a third of blind-spot membership changes with precision**: safe for *rates*, not for a specific question |
| **12** | **The independence premise the method rests on is false** | **within the same dataset, all four are wrong together 3.3× as often as independence predicts** [3.24, 3.41]; mean pairwise φ within each dataset **0.44–0.60** (`intervals.concordance`, `independence.stratified`) | 34,062 | **this leads the paper.** 10,819 observed vs 3,257 expected, summed within dataset. The pooled figure (31.8% vs 5.2%, **6.1×**, φ 0.654) is kept and demoted — pooling datasets whose difficulty differs ~6× manufactures co-failure (ISSUES #68). **Never quote 9.0× or "an order of magnitude".** NOT the same quantity as claim 3 — see the box below |
| **13** | **Agentic search does not rescue silent consensus** | **64.7% stay wrong** (88/136) [56.4%, 72.2%] (`intervals.rq5`) | 136 matched | quote the *ceiling*, never the wiki-vs-web difference (p = 0.80, noise). Re-run 27 Sep after the tool-loop off-by-one and cosine-graded TruthfulQA were fixed (ISSUES #76); matched = complete in both arms **and** still a blind spot |
| **14** | **The record carries signal where the vote is blind** | **AUC 0.592 → 0.772** (`rq1b`) | 12,181 | out-of-fold, **folds grouped by question text** (ISSUES #73). Answering the surest half runs at 3.00% error against an 8.37% base. Needs a labelled corpus to place a new question against — a deployment setting, not a cold start |
| **15** | **The blind region is a function of correlation, not capability** | corr(φ, silent rate) **+0.922**; holding mean error fixed **+0.918**; corr(error, silent rate) **−0.336** (`ablation`) | 70 four-model ensembles (of 154) | computed within size k=4, not across all 154 (k=2: +0.871, k=3: +0.910). Always quote the size curve with the rate: **2.79% at k=4, 4.01% at k=3, 7.51% at k=2** (2025 arm) |
| **16** | **Counter-evidence does not move the belief — under 1% either way** | counter-evidence repairs **0.74%** (7/950) and breaks **0.63%** (2/317) of controls by a majority; abstention permitted repairs **0/950** [0, 0.40%] (`belief`) | 950 + 317 control | **"Four broken for every one fixed" is RETIRED.** Counter-evidence "broke" 3.79% (12/317) only if 2–2 ties count; 10 of the 12 are ties. Abstention breaks 10.7% (34/317), 31 of them ties, 0.95% strict. Hedging is real: ≥1 model abstained on 55.1% of blind spots vs 28.4% of controls (1.94×, Fisher p = 9×10⁻¹⁷) but never converts |
| 17 | An LLM adjudicator agrees with the human better than the grader does | **κ 0.782 vs 0.459** (91.5% vs 79.2% agreement) (`adjudicator`) | 341 of 430 | re-measured 27 Sep **with alias lists** (ISSUES #71); the earlier κ 0.688 had the judge shown the gold answer only. Disagreements with the human 29 (was 45). Self-favouring: κ 0.816 on Qwen-family answers vs 0.771 on other makers' — a small gap in the self-favouring direction, disclosed, not a finding. **supplementary, NOT a second human** |
| **18** | **Inter-rater reliability, measured** | **κ = 0.970** [0.924, 1.000], agreement 99.0% (`irr`) | 115 labelled, weighted to 430 | stratum-weighted; 70 drawn from the **385** uncontested (not 296 — ISSUES #69) plus all 45 disputed. Quote the population figure, never one stratum. The second annotator sided with the first over the LLM 34 times to 3 |

> ### Claim 12 and claim 3 are different numbers. Do not collapse them.
>
> **All four wrong** — 31.8%, 10,819 questions. The four models are each wrong,
> but they can be wrong in four *different* ways. When they are, they disagree,
> the detector fires, and the case is caught. **Nothing is silent here.**
>
> **Silent consensus** — 2.8%, 950 questions. Wrong **and unanimous**. The
> detector reads "safe" and is wrong. A subset of the above: about **9% of
> all-wrong cases (950 of 10,819) converge on the same wrong answer**.
>
> Claim 12 attacks the *premise* — within the same dataset, the models are wrong
> together three times as often as the assumption every ensemble guardrail is
> built on predicts. Claim 3 is the *consequence* — the region where the failure
> is total rather than partial. Stating only claim 3 invites the reply *"2.8%, so
> the heuristic works 97% of the time"*, which misses the finding entirely.
>
> *(Until 2026-09-27 this box said "off by an order of magnitude", from the
> pooled 9.0×. That figure pooled strata and included duplicates — ISSUES #66,
> #68.)*

### Do NOT quote

| retracted / unusable | why |
|---|---|
| RQ3 "52% persist" | provider served gen-3 weights under gen-2 names (ISSUES #31) |
| the Gemma 2×2 ladder, any cell | same cause; 2 of 4 cells were duplicates |
| any RQ4 number before 2026-07-28 evening | retriever was returning nothing (ISSUES #28–30) |
| any TruthfulQA number without its caveat | n=340, and 26% of hard cases are undecidable by a human |
| `any_wrong` as a target | mechanically implied by the score — gave a flattering, meaningless 0.911 |
| anything measured at 300 questions | 5 for 5, effects shrank or vanished at scale |
| "newly broken" / "still broken" / "fixed" for the RQ3 categories | wrong axis. They are *newly hidden* / *hidden in both* / *now visible* — detectability, not correctness (2026-08-01) |
| "Beats Farquhar 0.790 / Gorbett 0.727" | different corpora, models and graders. A free shot for a reviewer. The within-study baseline in claim 2 is defensible and strong; use that (2026-08-25) |
| the RQ5 **wiki-vs-web difference** (+1.5pp on the current matched set; +3.4pp before the 27 Sep re-run, +3.1pp before that) | McNemar exact p = 0.80. It is noise. Quote the ceiling instead — 64.7% (88/136) (2026-08-25, updated 2026-09-27) |
| any lift, delta or rate **without its interval** | every number in the claims table now has one — see "Every claim, with its interval" below (2026-08-25) |
| **any figure computed on 42,551 questions** — 0.862, 1,054, 2.48%, 9.0×, 0.601 → 0.811, 364 / 559 / 690, κ 0.962 … | the corpus held 8,489 duplicate questions and the tie rule was arbitrary (ISSUES #66, #67). Superseded 2026-09-27 by the table above |
| **"an order of magnitude"** / **9.0×** / the pooled ratio as the headline | pooled across datasets of ~6× different difficulty (ISSUES #68). The headline is the within-dataset 3.3× |
| **"counter-evidence breaks four answers for every one it fixes"** | 10 of the 12 "broken" controls are 2–2 ties; requiring a majority wrong it is 2/317 (0.63%) against 7/950 repaired (0.74%) — parity, both under 1% (2026-09-27) |
| **Jaccard 0.780** / "~22% of blind spots differ between precisions" | unweighted over a stratified sample (ISSUES #75). Weighted: 0.644 |
| **κ 0.688** for the LLM adjudicator | the judge was shown no aliases (ISSUES #71). Re-measured with aliases 27 Sep: **0.782** |
| "the judge **misses one artifact in six**" | 10/62 is the share of the judge's WRONG calls a human called correct. The miss rate on artifacts the human caught is 10/40 = **25%** (2026-09-27) |
| the TruthfulQA **"~95 corrected, ~90% complete"** residual bound | a rate applied to the wrong denominator in `handlabel.py`. Exactly 70 labels were corrected; completion ≈ 67% (≈ 87% if UNCLEAR is undecidable). See "Residual error" below |

### Every claim, with its interval

**Re-derived 2026-09-27 by the exporter** — every row is read from the
`intervals` block of `faultlines-web/summary.json` (or the block named), which
`scripts/export_web.py` now computes. Until then this table had been computed by
hand once, on 2026-08-25, and typed in; nothing re-derived it when the data
changed (ISSUES #77). **No number in this file should be quoted without the
corresponding row.**

| claim | point estimate | 95% interval | test | verdict |
|---|---|---|---|---|
| 1 · headline AUC | 0.8403 | [0.8358, 0.8448] | Hanley–McNeil | real |
| 2 · cross-model beats single-model SE | Δ = +0.060 (0.838 vs 0.778) | [+0.0504, +0.0701] | paired bootstrap, 4,000 resamples, 6,436 same qids, p < 1/4000 | real |
| 3 · blind-spot rate | 2.789% (950 / 34,062) | [2.619%, 2.969%] | Wilson | real |
| 3b · artifact share of blind spots | 21.05% (200 of 950, all decided) | [18.58%, 23.76%] | Wilson (`artifact`) | real — failed calls re-run 27 Sep (#71) |
| 5 · shared-error share rises | 4.52% → 6.79%, ratio **1.502×** | [1.395, 1.616] | 4,000 paired bootstrap, p < 1/4000 | **real, and tight — still the strongest number in the project** |
| 5b · blind-spot rate rises 2.42% → 2.79% | Δ = +0.373% | [+0.179%, +0.566%] | McNemar exact (503 healed / 630 emerged), **p = 1.8×10⁻⁴** | real as graded; **not significant after answer-key adjudication** (genuine 698 → 750, exact McNemar p = 0.101; outside judge 678 → 716, p = 0.226) |
| 8 · RQ4 obscurity arm | +65.2% (n=500) | [+60.8%, +69.6%] | McNemar exact, p = 5.0×10⁻⁹¹ | overwhelming |
| 8 · RQ4 misconception arm | +14.0% (n=57) | [+0.8%, +27.3%] | McNemar exact, **p = 0.077** | **not significant** — the interval only just clears zero and the exact test does not reach 0.05 (was +15.7%, n=70, p = 0.027 before the 27 Sep re-run, #70) |
| 8 · **RQ4 dissociation** | **+51.2%** | [+36.9%, +65.3%] | 10,000 bootstrap, p < 1/10000 | the robust RQ4 claim |
| 12 · concordance, **within dataset** | **3.32×** (10,819 observed vs 3,257 expected) | [3.243, 3.405] | 2,000 bootstrap, resampled within dataset | **real — the headline** |
| 12b · concordance, pooled | 6.06× (31.76% vs 5.24%) | — | mean pairwise φ = 0.654 over 6 pairs | kept and demoted (#68) |
| 13 · RQ5 ceiling | 64.7% (88/136) | [56.4%, 72.2%] | Wilson | real — re-run 27 Sep (#76) |
| 13b · RQ5 wiki vs web | +1.5pp | [−4.3, +7.2]pp | McNemar exact, **p = 0.80** | **noise — do not quote** |
| 18 · inter-rater κ | 0.970 (population 430) | [0.924, 1.000] | 4,000 bootstrap within strata (`irr`) | real |
| RQ1 · confidence in the agreement region | AUC 0.5925 | [0.573, 0.612] | z = 9.5 vs 0.5; Mann–Whitney p = 6.1×10⁻²³; d = 0.50 | real, and **not operational** — see below |

**Per-dataset AUC, with intervals** (`intervals.auc_by_dataset`, base rate and
silent count from `signal.by_dataset`). TruthfulQA's is 6–11× wider than the
others and its lower bound is near chance. Attach it to every TruthfulQA number.

| dataset | n | AUC | 95% CI | width | base rate | silent |
|---|---|---|---|---|---|---|
| triviaqa | 9,962 | 0.861 | [0.848, 0.874] | 0.026 | 13.6% | 140 |
| halueval | 10,000 | 0.810 | [0.802, 0.819] | 0.017 | 50.3% | 366 |
| popqa | 13,760 | 0.793 | [0.786, 0.800] | 0.015 | 54.9% | 439 |
| **truthfulqa** | **340** | **0.683** | **[0.601, 0.764]** | **0.163** | 16.8% | 5 |

*(Superseded 2026-09-27: TriviaQA was 17,944 / 0.868 — 7,982 of those questions
were second copies — HaluEval 0.834, PopQA 14,267 / 0.798, TruthfulQA 0.646.
TruthfulQA and HaluEval had no duplicates; their AUCs moved with the tie rule,
ISSUES #67.)*

**RQ1's two confidence numbers are one finding, not a contradiction.** AUC 0.592
is a statement about *ranking*; 0.947-vs-0.929 is a statement about *separation*,
which is what a threshold needs. Both are true. (RQ1's 0.592 and RQ1b's
"confidence mean only" 0.5917 are the same quantity measured two ways —
Mann–Whitney on the raw score, and out-of-fold — not two results.) The
abstention economics (`intervals.abstain_table`, 12,181 unanimous questions,
1,020 wrong):

| threshold | abstains | errors caught | correct destroyed | precision | lift over 8.37% base |
|---|---|---|---|---|---|
| 0.900 | 1,233 | 238 (23%) | 995 (9%) | 19.3% | 2.31× |
| **0.941** | **4,268** | **510 (50%)** | **3,758 (34%)** | **11.9%** | **1.43×** |
| 0.970 | 8,914 | 788 (77%) | 8,126 (73%) | 8.8% | 1.06× |

> Publishable phrasing: *"Confidence carries real signal in the region where
> disagreement carries none by construction (AUC 0.592, 95% CI [0.573, 0.612],
> p < 10⁻²²). But the region is 92% correct answers and the distributions
> overlap heavily (d = 0.50): a threshold catching half the errors abstains on a
> third of correct answers and is still only 11.9% precise against an 8.4% base
> rate. **The signal is real; the margin is not operational.**"*

This pre-empts *"just make it say I don't know"* — the most common suggestion
this project receives — with a table rather than an opinion.

**Method.** Computed by `scripts/export_web.py` into `summary.json → intervals`
(ISSUES #77). Bootstraps use `numpy.random.default_rng` with fixed seeds and
2,000–10,000 resamples. AUC intervals are Hanley–McNeil; proportion intervals
are Wilson; paired binary comparisons are exact McNemar (`scipy.stats.binomtest`
on the discordant pairs); the concordance bootstrap resamples within dataset.
Sources: `data/interim/answers.parquet` (φ, error rates, concordance — gradeable
rows only), `data/processed/records.parquet` + `records_rq3local.parquet`
(McNemar, bootstrap, AUC), `rq4_retrieval.parquet`, `rq1_confidence.parquet`,
`data/interim/baseline.parquet`, and the RQ5 parquets. Rows 10 and 11 of the
claims table come from `handlabel.py --result` and `compare_precision.py`, re-run
27 Sep, and are not in `summary.json`.

### How to read the rest of this file

Newest and largest run first. Anything below the 2026-07-27 scale test is
300-question pilot work, kept because the **reversals between scales are
themselves a finding** — not because those numbers are current.

Companion records: **ISSUES.md** (what broke) · **DECISIONS.md** (why each choice)
· **EVOLUTION.md** (why the project looks different from the proposal).

---


**Read this file top-down: newest and largest run first.** Anything below the
2026-07-27 scale test is 300-question pilot work, kept because the *reversals*
between scales are themselves the finding — not because those numbers are the
current ones.

> **Superseded 2026-09-27.** The question counts in this table are as run. Since the
> 27 Sep dedup (ISSUES #66) every analysis uses **34,062** of the 42,551 gradeable
> questions; the generations were not re-run.

| arm | models | provider | questions | status |
|---|---|---|---|---|
| **gen-3 full** (untagged) | Llama-4-Maverick · Qwen3-235B · Mistral-Small-3.2-24B · Gemma-3-27B | DeepInfra | **42,551** | ✅ **headline** — identity-gated, all pairs 0% agreement |
| gen-3 pilot `_gen3` | same four | DeepInfra | 300 | ✅ scale test |
| SE baseline | same four, 4 samples each | DeepInfra | 8,000 | ✅ Finding 3 |
| **gen-2 local** `_rq3local` | llama3.1:8b · qwen2.5:7b · mistral:7b · gemma2:9b, **4-bit** | **laptop** | **42,551** | ✅ **RQ3 at full corpus** — digest-verified, 170,364 gen, 0 failures |
| gen-2 local 8-bit `_rq3local_q8` | same four at Q8_0 | laptop | 2,554 | ✅ precision control |
| gen-2 pilot `_gen2h` | Llama-3.1-8B · Qwen2.5-7B · Mistral-7B-v0.3 · Gemma-2-9B | DeepInfra | 300 | ⚠️ Mistral likely aliased — see ISSUES #31 |
| ~~gen-2 full `_gen2h`~~ | ~~same four~~ | ~~DeepInfra~~ | ~~42,551~~ | ❌ **VOID** — 2 of 4 models were gen-3 in disguise (`data/void/`) |
| ~~Gemma 2×2 ladder~~ | ~~gemma-2/3 at 9/12/27B~~ | ~~DeepInfra~~ | ~~42,551~~ | ❌ **VOID** — 2 of 4 cells were duplicates (`data/void/`) |
| gen-2 local `_pilot` | same four via Ollama, 4-bit | laptop | 300 | ✅ original pilot |
| gen-1 `_gen1_pilot` | llama2:7b · qwen:7b · mistral:v0.1 | laptop | 300 | ❌ dropped (3 makers, 4-bit) |

**Two arms totalling 340,728 generations are VOID** because the provider served
different models than requested. They executed flawlessly and measured nothing.
Retained as evidence, quarantined out of the working directories. The lesson is
in ISSUES #31; the countermeasure is `check_provider.py::identity_check()`.

---

## 2026-07-28 · FULL CORPUS — 42,591 questions asked, 42,551 analysed, 170,364 generations

The headline result. Four makers, four model families, hosted at full precision.
0 failed generations, 0 `<think>` leaks, 0 NaN confidences.

> **Superseded 2026-09-27.** This section is the run as recorded on 2026-07-28, on 42,551
> gradeable questions of which 8,489 were duplicates (ISSUES #66) and with an
> arbitrary tie rule (#67). Current: **n = 34,062, AUC 0.840 head-count / 0.844
> weighted, majority-wrong base rate 41.1%, 950 silent consensus (2.8%)**
> (`signal.overall`). The corpus is still **42,591 asked**; the funnel is now
> 42,591 → 40 ungradeable → 8,489 duplicates → 34,062 analysed, and 136,248 of
> the 170,364 generations per arm are analysed (`corpus`).

**Why two n's.** The corpus is **42,591** questions (× 4 models = 170,364
generations, which is what every arm actually ran). Analysis uses **42,551**.
The 40-question difference is TruthfulQA items whose gold answer is
*"I have no comment"* — TruthfulQA's marker for a question it judges to have no
factual answer. No correctness label exists for them, so any accuracy or AUC
computed over them would be invented. `nli.is_ungradeable` flags them,
`disagree.run` drops them and prints the count.

This is deliberate, not attrition, but it was previously written up as
"42,551 questions, 170,364 generations" — which does not multiply (42,551 × 4 =
170,204) and would read to a reviewer as an arithmetic error or a silent
40-question data loss. Both numbers are now stated with the reason. Quote
**42,591** for corpus size and **42,551** for any n on a metric.

```
n = 42,551 gradeable questions       majority-wrong base rate 36.2%

AUC unweighted                       0.862      strong
AUC confidence-weighted              0.865      strong
weighting delta                      +0.003

mean disagreement                    0.290  (unweighted 0.308)
silent consensus                     1,054  (2.5%)   <- the Audit population
```

Anchors for the write-up: Farquhar (Nature 2024) 0.790; Gorbett 2026 0.727
cross-model vs 0.595 single-model. **0.862 clears both.**

### FINDING 1 (restated at scale) — confidence-weighting is a WASH on large models

This supersedes the 300-question reading below. Three measurements now exist:

| arm | unweighted | weighted | Δ |
|---|---|---|---|
| local 7–9B, 300q | 0.788 | 0.776 | **−0.012** (hurts) |
| hosted 17–27B, 300q | 0.793 | 0.801 | **+0.008** (helps) |
| **hosted 17–27B, 42,551q** | **0.862** | **0.865** | **+0.003** (neutral) |

The sign flips from small to large models and then **shrinks toward zero as n
grows**, which is what a small real effect looks like when you stop measuring it
on 300 points. Honest statement for the thesis: *confidence-weighting is not the
improvement the proposal assumed; at scale it is neutral-to-marginally-positive,
and at 7–9B it is actively harmful.* The +0.008 should not be quoted alone.

**Consequence, 2026-08-03: the head-count score is now used EVERYWHERE** — the
headline, the Semantic-Entropy head-to-head, `majority_wrong`, RQ1's baseline,
the tool's colour bands and its per-case readout. Weighting buys +0.003 and costs
−0.012 on small models, so there is nothing to gain and something to lose, and a
single scoring method removes the possibility of quoting whichever variant
flatters a given result. `auc_weighted` is still exported as the control that
makes this a measurement rather than a preference. See DECISIONS 2026-08-03.

### FINDING 2 (resolved) — the Audit population is real

The pilot found **5** silent-consensus cases in 300 questions and every
downstream claim was noise-dominated. At full corpus:

```
silent consensus     1,054     spread across all four datasets
  popqa                461
  halueval             366
  triviaqa             222
  truthfulqa             5
```

**They are not concentrated in TruthfulQA.** The proposal expected shared blind
spots to live in the misconception-baiting dataset; 99.5% of them are elsewhere.
Shared error is a general property of the ensemble, not a TruthfulQA artifact —
and that materially widens what the Audit view is *for*.

ISSUES.md item C (*"Audit is data-starved"*) is closed by this number.

### Per-dataset AUC at full scale

> **Superseded 2026-09-27.** Current per-dataset figures, with intervals, are in the table
> at the top of this file: TriviaQA 9,962 / 0.861, HaluEval 10,000 / 0.810,
> PopQA 13,760 / 0.793, TruthfulQA 340 / 0.683. The reasoning below (PopQA's
> puzzle dissolving with n; TruthfulQA the weak one) still holds; the numbers in
> it are the 2026-07-28 ones.

| dataset | n | AUC | base rate | silent |
|---|---|---|---|---|
| triviaqa | 17,944 | **0.868** | 12% | 222 |
| halueval | 10,000 | 0.834 | 53% | 366 |
| popqa | 14,267 | 0.798 | 55% | 461 |
| truthfulqa | 340 | 0.646 | 21% | 5 |

- **The PopQA puzzle dissolved.** The 300-question run read 0.761 and was flagged
  below as an open worry — disagreement supposedly predicting error *worse* on
  obscure entities, on the one dataset RQ2's popularity control depends on. At
  n=14,267 it is **0.798**. It was small-sample noise. Recorded because it would
  have been written up as a finding.
- **HaluEval earns its place**: 0.834 at n=10,000, and the highest
  silent-consensus rate of any dataset (3.7%). This is the dataset that replaced
  TruthfulQA's statistical job.
- **TruthfulQA remains the weak one** (0.646, n=340) and still cannot carry a
  claim on its own. See ISSUES.md 1b for the NLI-margin limitation.

### FINDING 3 (settled at scale) — cross-model BEATS single-model

> **Superseded 2026-09-27.** On the deduplicated corpus the 8,000-question subset keeps
> **6,436** questions; cross-model head-count **0.838** against the best single
> model (Mistral-Small-3.2) **0.778**, Δ **+0.060 [+0.050, +0.070]**
> (`intervals.vs_semantic_entropy`, `baseline`). Qwen3-235B 0.761,
> Llama-4-Maverick 0.680, Gemma-3-27B 0.649. The mean-of-4 SE figure (0.855)
> and corr(disagreement, best SE) = +0.711 below were **not** re-derived on 27 Sep.

Semantic Entropy on all four gen-3 models, **8,000 questions** stratified
proportionally from the corpus, same 4-generation budget, same clustering. The
only variable is whether the four generations come from one model or four. Both
arms scored on the *same* qids (`baseline_subset_qids.parquet`), so composition
cannot bias the comparison.

**128,000 baseline generations** · 0 empty samples · 0 exhausted retries.
8,000 questions × 4 models × 4 samples each. `baseline.parquet` holds 32,000
*rows* — one Semantic-Entropy score per (question, model) — and each row carries
its 4 samples in the `samples` column. An earlier version of this line quoted the
row count as a generation count and understated the arm's cost by 4×. Verify with
`d.samples.map(len).sum()`, not `len(d)`.

| arm | AUC |
|---|---|
| **FaultLines cross-model (head-count)** — **quote this** | **0.862** |
| FaultLines cross-model (confidence-weighted) | 0.864 |
| mean-of-4 Semantic Entropy | 0.855 |
| SE — Mistral-Small-3.2 (best single) | 0.800 |
| SE — Qwen3-235B | 0.755 |
| SE — Llama-4-Maverick | 0.693 |
| SE — gemma-3-27b | 0.662 |

**+0.062 over the best single model.** This is the third claim reversal, and it
reverses the *pilot*, which had single-model winning 0.813 vs 0.788.

> **Both rows are kept, and the head-count row is the one to quote — including
> here.** Until 2026-08-03 the exported number for this comparison was the
> weighted 0.864 while the headline AUC was the head-count 0.862, so the deck
> showed two numbers for one measurement and the higher one sat next to the
> competing method. Head-count is now used everywhere: this comparison, the
> headline, `majority_wrong`, the tool's colour bands and its per-case readout.
> The weighted row stays as the control that makes the choice a measurement
> rather than a preference. See DECISIONS 2026-08-03 for the calibration
> evidence — weighting **hurt** at 7–9B (0.776 vs 0.788) and is worth +0.003 at
> full corpus.

| | small 7–9B, 300q | large 17–27B, 300q | large 17–27B, 8,000q |
|---|---|---|---|
| cross-model | 0.788 | 0.801 | **0.862** |
| best single SE | **0.813** | 0.685 | 0.800 |
| winner | single | cross | **cross** |

**Two caveats that must travel with this number:**

1. **The 300-question test overstated the gap.** It put the best SE at 0.685; at
   8,000 questions it is 0.800. Cross-model still wins, but by 0.06 rather than
   0.12 — half the size. Same direction, smaller effect. This is now the third
   time an effect shrank as n grew (see also Finding 1 and the PopQA puzzle);
   the pattern itself belongs in the methodology chapter.
2. **Averaging all four SE scores reaches 0.855** — within 0.007 of cross-model
   disagreement. So the honest claim is *not* "cross-model detects something
   self-consistency cannot." It is **"cross-model reaches the same signal for a
   quarter of the generations"** — 4 calls versus 16. corr(disagreement, best
   SE) = **+0.711**: overlapping, not identical. Efficiency is the defensible
   contribution; a categorically better detector is not.

Reproduce: `python -m faultlines.baseline --subset 8000`.

### FINDING 4 — RQ3: about a third of shared blind spots survive a generation

> **Superseded 2026-09-27.** Current (`rq3`, deduplicated, new tie rule): gen-2 blind spots
> **823** (2.42%), gen-3 **950** (2.79%); **persisted 320, healed 503, emerged
> 630**; persistence **38.9%** (320/823), inherited share **33.7%** (320/950);
> emerged ÷ persisted **1.97×**; 505 of the 630 emerged (80%) were already all
> wrong in 2024; of the 503 healed, the ensemble is still wrong on 406 and all
> four on 280. The per-dataset persistence table below was not re-derived.

> **Supersedes a RETRACTED result.** The hosted version of this ("52% persist",
> 448 of 860) is WITHDRAWN — two of the gen-2 arm's four models were gen-3 models
> served under gen-2 names (ISSUES #31). Data quarantined in `data/void/`. The
> numbers below come from **local Ollama weights verified by content digest**,
> which cannot be substituted.

Old ensemble: Llama-3.1-8B · Qwen2.5-7B · Mistral-7B-v0.3 · Gemma-2-9B, run
locally at 4-bit.

**UPGRADED 2026-07-29 to the FULL CORPUS.** Both arms now cover the identical
42,551 questions, so every quantity below is an exact count. No stratification,
no reweighting, no sampling error anywhere. 170,364 local generations, 0 failures,
**~138 hours of laptop GPU** (measured 2026-08-25 by `scripts/time_local.py`:
0.34 gen/s across the four models, 2.5–3.3 s per generation). (The last stage of
that run crashed on defect #36; see ISSUES — the generations were unaffected
and the repair is documented.)

> **This figure read “~9 hours” until 2026-08-25 and was wrong by ~15×.** It was
> never measured; `scripts/build_rq3_local.py` had been budgeting with 0.24 gen/s
> in the same repository the whole time. See ISSUES #54 — it is the only
> reproducibility claim in this file that a reader could have acted on and lost
> five days to.

```
questions           42,551   identical set in both arms

gen-2 blind spots      923   2.17%
gen-3 blind spots    1,054   2.48%

PERSISTED              364   blind in BOTH generations
HEALED                 559   the upgrade fixed them
EMERGED                690   new blind spots the upgrade CREATED
union                1,613   Jaccard 0.226
```

### Two rates, and they answer different questions

The single number "34.5%" was ambiguous, and at full corpus the ambiguity is
now measurable. Both are correct; they have different denominators.

| question | rate | reading |
|---|---|---|
| Of gen-2's blind spots, how many **survive** the upgrade? | **39.4%** (364/923) | *persistence* — the safety-relevant one |
| Of gen-3's blind spots, how many were **already** blind in gen-2? | **34.5%** (364/1,054) | *inherited share* |

The subset run could only measure the second: its question set was *defined* as
gen-3's 1,054 blind spots, so gen-2's own blind-spot population was truncated by
construction. Measuring gen-2's full 923 required running the whole corpus, which
is exactly what this arm now does. **Quote 39.4% for "do blind spots persist"**
and 34.5% for "are today's blind spots inherited".

### What the full corpus changed

| quantity | subset estimate | full corpus | error |
|---|---|---|---|
| PERSISTED | 364 | **364** | exact already — the 1,054 were all tested |
| gen-2 blind rate | 1.96% (~834) | **2.17% (923)** | understated by 9.6% |
| EMERGED | ~470 | **690** | **understated by 32%** |
| HEALED | 690 ✗ | **559** | the subset's "690" was in fact EMERGED, mislabelled |

The reweighted EMERGED estimate was the weakest number in the subset design and
it was wrong by a third. **Blind spots are created by an upgrade nearly twice as
often as they are inherited through one** (690 emerged vs 364 persisted).

> **Read `EMERGED` as *newly hidden*, `HEALED` as *now visible*, `PERSISTED` as
> *hidden in both*.** These are column names on a **detectability** axis, not a
> correctness one: 78% of the 690 were already all-wrong in 2024 and merely
> disagreed, and 52% of the 559 are still all-wrong in 2025. See the 2026-08-01
> correction at the end of this file before quoting any of them.

### Per-dataset persistence (of gen-2 blind spots)

| dataset | gen-2 blind | persisted | rate |
|---|---|---|---|
| popqa | 420 | 175 | **41.7%** |
| halueval | 295 | 112 | 38.0% |
| triviaqa | 201 | 76 | 37.8% |
| truthfulqa | 7 | 1 | 14.3% (n too small) |

Obscurity-driven blind spots (PopQA) persist most — consistent with RQ4, where
retrieval fixed obscurity (+68%) precisely because the deficit is missing
knowledge rather than a wrong belief. Scaling does not supply that knowledge;
retrieval does.

### Four measurements of the same quantity, for the record

| arm | persistence | why the number differs |
|---|---|---|
| pilot, 300 questions | 20% | 5 cases. Noise. |
| hosted, full corpus | 52% | **contaminated** — models compared with themselves |
| local subset, digest-verified | 34.5% | correct, but answers the *inherited share* question |
| **local FULL corpus** | **39.4%** | exact, both arms complete, no reweighting |

### FINDING 4b — errors get MORE correlated as models improve (CONFIRMED)

> **Superseded 2026-09-27.** Current (`rq3.rates`, `intervals.share_ratio`): majority wrong
> **53.45% → 41.08%**; shared blind-spot rate **2.42% → 2.79%**; share of each
> generation's errors that are shared **4.52% → 6.79%**, ratio **1.50×
> [1.39, 1.62]**. The new models make 23% fewer errors and the shared share rises
> by half. The finding survived deduplication with its direction and size intact.

Stated as a hypothesis on the 300-question pilot (5 vs 7 cases, "far too small to
claim"). **Now measured exactly on the full corpus — 42,551 questions, identical
set in both arms, no reweighting.** The earlier version of this table used
stratum-reweighted estimates; both columns below are direct counts.

| | gen-2 (old) | gen-3 (new) |
|---|---|---|
| majority wrong | **48.1%** (20,481) | **36.2%** (15,406) |
| all four wrong | 37.7% | 26.9% |
| shared blind-spot rate | **2.17%** (923) | **2.48%** (1,054) |
| **share of each generation's errors that are SHARED** | **4.5%** | **6.8%** |
| mean disagreement | 0.353 | 0.290 |

**The new models make 25% fewer errors, but a larger fraction of the errors they
do make are shared by every model in the ensemble** — 4.5% → 6.8%, a 51% relative
increase in the shared share. Scaling fixes many mistakes and concentrates what
remains into exactly the region cross-model disagreement cannot see.

**This finding SURVIVED exact measurement**, which is worth stating explicitly
given the project's record: the reweighted estimates (46.1% / 1.96% / 4.3%) came
in at 48.1% / 2.17% / 4.5% — same direction, same magnitude, slightly stronger.
It is the first effect in this project that did not shrink when measured at full
scale. The reason is design, not luck: it was estimated from a *proper stratified
sample with reweighting*, not from a 300-question convenience pilot. Every effect
that shrank at scale came from the latter (now 5 for 5).

This is the safety argument of the thesis, and it is the reason the Audit view
matters: the failure mode does not shrink with better models, it *hardens*.

**Method note — an invalid comparison caught before publication.** The first
attempt compared gen-2's blind-spot rate on the control stratum (1.13%) against
gen-3's corpus-wide rate (2.48%). That is meaningless: the control stratum was
DEFINED as questions that are not gen-3 blind spots, so gen-3 scores 0% there by
construction, not by measurement. Any stratified design invites this error —
the rate must be reweighted from both strata before the arms are comparable.

### FINDING 5 — RQ4: retrieval fixes ignorance, only partly fixes misconception

> **Superseded 2026-09-27.** 15 empty answers (7 closed-book, 8 retrieval) had
> been scored as wrong (ISSUES #70), and the strata were re-selected from the
> deduplicated records under the new tie rule. **Re-run 27 Sep, 0 empty answers**
> (`intervals.rq4`): obscurity n=500, closed-book 7.2% → retrieval 72.4%, lift
> **+65.2%** [+60.8%, +69.6%]; misconception n=57, 24.6% → 38.6%, lift **+14.0%**
> [+0.8%, +27.3%], exact McNemar **p = 0.077 — no longer significant**;
> dissociation **+51.2%** [+36.9%, +65.3%] (10,000 bootstrap). Retrieval *barely
> moves* misconceptions; point 1 below ("retrieval *does* partly repair
> misconceptions") is superseded with it. The dissociation is the claim.

`rq4_retrieval.py`, 570 cases, same model both arms (Llama-4-Maverick).

| stratum | n | closed-book | with retrieval | lift |
|---|---|---|---|---|
| **obscurity** (rarest PopQA entities) | 500 | 4% | **72%** | **+68%** |
| **misconception** (TruthfulQA errors) | 70 | 27% | 43% | **+16%** |

**A 4x dissociation.** Errors from missing knowledge are repairable by supplying
the document; errors from absorbed misconceptions largely are not, because
retrieval draws from the same web that taught the misconception.

Two corrections to the original prediction, both worth stating:

1. **The prediction was "obscurity HIGH, misconception ~0".** Obscurity came in
   at +68%, so the positive control fires. Misconception came in at **+16%, not
   ~0** -- retrieval *does* partly repair misconceptions. The finding is the
   **gap**, not a fix-vs-no-fix dichotomy.
2. **This took four attempts** (ISSUES #28-30). Attempts 1-3 reported "+0%" and
   would have been written up as *"retrieval does not fix obscurity"* -- a
   plausible, coherent, entirely false claim caused by a retriever that was not
   retrieving. Do not cite any RQ4 number generated before 2026-07-28 evening.

**Stated limitations:** the misconception arm is n=70, capped by TruthfulQA's
size, not by choice. Retrieval coverage tops out at ~70% gold-in-context, the
ceiling for Wikipedia lead sections on rare entities.

### FINDING 6 — RQ1 at full scale: confidence sees what the vote cannot

```
re-run 2026-09-27:  python -m faultlines.rq1_confidence --full   (34,062 questions)

unanimous region: 12,181 questions (36% of the corpus)
  AUC  low mean confidence -> error   0.592     (vote-counting is 0.5 here BY CONSTRUCTION)
  AUC  low min confidence  -> error   0.571

two features vs one (5-fold CV, SHUFFLED -- ISSUES #72):
  disagreement alone    0.839      head-count -- NO confidence in the baseline
  confidence alone      0.825
  combined (logistic)   0.862
  confidence is worth  +0.023
```

> **Re-run 2026-09-27.** Two things changed at once: the corpus lost its 8,489
> duplicates (ISSUES #66) and the folds are now shuffled — they were
> `cv=5`, an unshuffled `StratifiedKFold` over a file sorted by dataset
> (ISSUES #72). The published 0.847 / 0.831 / 0.871 (+0.024) below are
> superseded. The gain from adding confidence is unchanged to the third decimal
> place, so the conclusion stands.

> **Corrected 2026-08-03.** These read 0.854 / 0.831 / 0.872 until the one-feature
> baseline was switched from `disagreement` to `disagreement_unweighted`. The
> weighted score is *computed from* the confidences, so the old baseline already
> contained the very thing the experiment exists to isolate, and the reported gain
> was "extra confidence on top of confidence" rather than "confidence versus
> none". **The correction makes the finding stronger — +0.018 becomes +0.024 —
> which is exactly why it is worth stating rather than quietly restating.** The
> four-feature detector barely moves (0.872 → 0.871) because it carries the
> confidence columns either way; the whole change is on the baseline.

Where every model agrees, disagreement carries **no information by definition** —
and confidence still separates right from wrong at 0.592. Down from the pilot's
0.688, but measured on 12,181 questions instead of 50.

Combined (0.862) beats disagreement alone (0.839), which is the justification for
the "two features, not one blended score" design. Confidence gap holds at every
agreement level (0.947 vs 0.929 at unanimity, widening to 0.809 vs 0.764 at full
disagreement; re-run 27 Sep).

### FINDING 7 — RQ2 at full scale: errors cluster, beyond popularity

*Strengthened 2026-08-25 by closing AUDIT note n1 — see below.*

```
re-run 2026-09-27 (deduplicated, shuffled folds -- ISSUES #66, #72):
popularity alone (PopQA, n=13,760)             AUC 0.653
popularity + density, shared map               AUC 0.726   lift +0.073
popularity + density, WITHIN PopQA             AUC 0.741   lift +0.089   <- the control
density within PopQA, alone                    AUC 0.662
```

> **Superseded 2026-09-27:** these read 0.666 / 0.726 (+0.060) / 0.745 (+0.078)
> on n = 14,267 with unshuffled folds; corpus-wide map density alone read 0.705
> and was not re-derived. **The finding got stronger**: +0.089 within PopQA.
> corr(popularity, error) is now −0.287, corr(density, error) +0.277 on the
> shared map and **+0.303 within PopQA** (`rq2`). 25.3% of a PopQA question's
> neighbours come from another dataset (was 28.1%). The prose below keeps the
> 2026-08-25 figures.

**The map carries signal popularity does not.** This is the result that answers
"you have only rediscovered that rare entities are hard" (Kandpal 2023;
Mallen 2023): controlling for entity popularity, neighbourhood density still
adds **+0.078 AUC**.

corr(popularity, error) = −0.309 · corr(density, error) = +0.267 shared map,
**+0.303 within PopQA**.

#### The control that was missing, and why the number went UP

Until 2026-08-25 the density feature was computed over **all four datasets
mixed** and then subset to PopQA, so a PopQA question's neighbours could be
TruthfulQA questions. `AUDIT.md` note n1 flagged it as defensible but
undocumented. Measured, the leak was not small: **28.1% of a PopQA question's
15 nearest map-neighbours come from another dataset.**

That made the feature leaky as a *control* — part of "this PopQA neighbourhood
is error-prone" was really "the adjacent benchmark is error-prone" — and a
reviewer could have said the lift came from the leak.

Recomputing neighbours within PopQA only, the lift **rises from +0.060 to
+0.078**, about 30% larger. The two densities correlate at r = +0.839, so they
are measuring much the same thing; the within-dataset version measures it
without borrowing.

**Both are reported on purpose.** The shared-map density is what the tool draws
— one UMAP, brushed by a user who is not filtering by dataset — so it is the
honest description of what someone sees. The within-dataset density is the one
the *claim* rests on. They are different quantities and the write-up must not
quietly swap one for the other.

#### A second thing fell out of it

**Density within PopQA, on its own, reaches AUC 0.662 — statistically
indistinguishable from popularity's 0.666.** Popularity is a metadata field
PopQA ships (Wikipedia pageviews); density is computed from question text
alone, with no metadata at all.

So the map recovers, from the questions themselves, about as much as an
external popularity signal provides — and then adds +0.078 on top of it. That
matters for the instrument rather than for the finding: the three datasets
*without* a popularity field are not second-class citizens on the map.

### FINDING 8 — RQ1b: the vote is blind here, but the RECORD is not

*Added 2026-08-25. `scripts/rq1_multifeature.py`.*

RQ1 stopped at "confidence separates error at AUC 0.600 in the agreement
region, and no threshold on it is operational." That was true and it was only
ever about **one feature**. The record holds several more, computed months ago
and never combined.

Agreement region: **12,181 questions, 1,020 wrong, 8.37% base rate** (re-derived
2026-09-27 on the deduplicated corpus). The disagreement vote is 0 for every one
of them by construction.

| feature set | AUC | AUARC | risk @25% | risk @50% | risk @80% |
|---|---|---|---|---|---|
| confidence, mean only | 0.5814 (logistic: **0.5917**) | 0.0705 | 7.06% | 6.85% | 7.14% |
| confidence, all four (mean/min/max/spread) | 0.6354 | 0.0530 | 4.37% | 5.68% | 6.88% |
| + answer and question length | 0.7240 | 0.0395 | 2.56% | 3.69% | 5.45% |
| + map position (x, y) | 0.7496 | 0.0349 | 2.07% | 3.09% | 5.25% |
| + neighbourhood density (out-of-fold) | 0.7474 | 0.0350 | 1.84% | 3.14% | 5.26% |
| **+ popularity** | **0.7718** | **0.0328** | **2.10%** | **3.00%** | **4.81%** |
| density + position alone, no confidence | 0.6127 | 0.0597 | 5.32% | 5.91% | 7.06% |

Gradient boosting, 5-fold out-of-fold predictions, seed 42, **folds grouped by
normalised question text** (`StratifiedGroupKFold`, ISSUES #73). Read from
`data/processed/rq1_multifeature.parquet` as written 2026-09-27 by
`scripts/rq1_multifeature.py`. The exported "confidence mean only" (`rq1b.conf_auc`
= 0.5917) is the logistic row, and is the same quantity as RQ1's Mann–Whitney
0.592 — one number, not two.

> **Superseded 2026-09-27:** 17,664 questions, 6.61% base, 0.6011 → 0.8111, risk
> 1.61% / 1.04%. Two things inflated it: 8,489 duplicate questions (ISSUES #66)
> and row-level folds that let a question's twin — or the same text under
> another qid — sit in the training fold (#73). Neighbourhood density now adds
> nothing once position is in (0.750 → 0.747); popularity still adds +0.024 on top. `risk @c` is the
error rate among the `c` fraction the model was surest about — a
risk-coverage curve, not a threshold, because "you picked a bad threshold" is
otherwise a free objection.

**AUC 0.592 —> 0.772, a gain of +0.180.** Answer only the half it is
surest about and the error rate there is **3.00%** against 8.37% overall; the
surest quarter runs at **2.10%** (`rq1b`). *(Was 0.601 → 0.811, 1.61% / 1.04% —
superseded 2026-09-27, ISSUES #66, #73.)*

**Why this matters more than the number.** The project's central design claim is
that keeping the whole record — answers, grades, confidences, coordinates —
rather than just the score is what makes the findings possible. This is the
first direct test of that claim, and it is the strongest available argument for
it: in the region where the published signal is blind *by construction*, the
record still carries a usable one. Confidence alone was never the ceiling; it
was the only thing anyone had looked at.

**What it does not say.** Density and popularity need a labelled corpus to place
a new question against, so this is a deployment setting where a benchmark run
already exists — not a cold start. And it does not rescue silent
consensus as a *class*: it ranks within the region, it does not eliminate it.

> #### Two leaks were caught before this table was believed
>
> The first version of this experiment read **AUC 0.759** with a neighbourhood-
> density feature computed once over the whole corpus, as `rq2_localize.py`
> correctly does for its own purpose. Under cross-validation that carries test-
> fold labels into training features. Density is now rebuilt inside each fold
> from training labels only.
>
> The first *fix* was half a fix, and cost 0.05 AUC in the other direction:
> training rows still read their own label, because a row is its own nearest
> neighbour. The symptom was density making the model **worse** (0.780 —> 0.728),
> which looks nothing like a leak.
>
> A third row, "+ grader margin", was dropped entirely: `nli_margin` is
> **99.1% null** because NLI runs on TruthfulQA only. sklearn discarded the
> column at the imputer and printed a plausible negative result.
>
> Three near-misses in one experiment. See ISSUES standing rule 6.

---

### FINDING 9 — ensemble size, and what actually drives the blind region

*Added 2026-08-25. `scripts/ensemble_ablation.py`, validated against the
headline before use. Re-run 2026-09-27 on the deduplicated corpus: it reproduces
the 950 silent-consensus questions (`ablation`).*

Eight models have answered the identical corpus — four from 2024, four from
2025 — so every subset of them is an ensemble that could have been deployed,
and scoring one costs nothing. **154 ensembles** of size 2–4 (C(8,2)+C(8,3)+C(8,4)),
each fully re-clustered by meaning, no new generations.

#### Size: the headline rate is strongly size-dependent

Within the 2025 arm, so no generation is mixed in:

| ensemble size | ensembles | mean silent-consensus rate | range |
|---|---|---|---|
| 4 | 1 | **2.789%** | — |
| 3 | 4 | 4.012% | 3.861% – 4.184% |
| 2 | 6 | 7.506% | 7.125% – 8.837% |

Across all 154, including cross-generation ensembles: k=4 mean 2.332%
(1.568–3.441%), k=3 mean 3.599%, k=2 mean 7.318% (`ablation.by_size_all`).

*(Superseded 2026-09-27: 2.477% / 3.557% / 6.625% within the 2025 arm, and
2.075% / 3.194% / 6.497% across all 154, on the corpus with duplicates.)*

**Report the curve, never the bare 2.8%.** Dropping one model of four raises the
blind region by roughly half; dropping two nearly triples it. This supersedes
the exact-match proxy (2.033% / 2.975% / 5.659%) quoted before 2026-08-25, which
was a lower bound as designed.

#### What drives it: correlation, not capability

| | k=2 | k=3 | k=4 |
|---|---|---|---|
| corr(mean pairwise **&phi;**, silent-consensus rate) | **+0.871** | **+0.910** | **+0.922** |
| … **holding mean error rate fixed** (partial) | **+0.891** | **+0.906** | **+0.918** |
| corr(mean **error rate**, silent-consensus rate) | –0.025 | –0.218 | –0.336 |
| corr(φ, mean error rate) | –0.237 | –0.253 | –0.259 |

*(Re-derived 2026-09-27, `ablation`. Was +0.833 / +0.894 / +0.917 and –0.033 /
–0.247 / –0.366. The partial-correlation row is new: it answers the objection
that φ is capability in disguise — here it is not, since φ and error rate are
only weakly related and holding error fixed barely moves the correlation.)*

Across 154 ensembles the blind region is almost entirely predicted by how
**correlated** the models are, and barely at all — or inversely — by how
**accurate** they are. Within the 2025 arm alone, corr(&phi;, silent rate) is
**+0.944** at k=2 and **+0.946** at k=3 *(2026-08-25 figures, not re-derived
27 Sep)*.

**This is the constructive half of claim 12.** The independence premise fails —
3.3× within dataset (was quoted as 9.0× pooled, ISSUES #68); this says what to do
about it. You cannot buy your way out of the blind
region with better models — error rate does not predict it — but a less
correlated ensemble has a smaller one, and correlation is measurable before
deployment from a few hundred questions.

#### And the finding that contradicts the hypothesis

The obvious next step was "so pick your ensemble for decorrelation". **The data
says that trade is not free.**

| | k=2 | k=3 | k=4 |
|---|---|---|---|
| corr(&phi;, detection AUC), raw | +0.927 | +0.729 | +0.611 |
| corr(&phi;, detection AUC), controlling for mean error | +0.922 | +0.748 | +0.642 |

*(Re-derived 2026-09-27, `ablation.phi_auc` / `phi_auc_partial`; was +0.795 /
+0.602 / +0.441 raw and +0.763 / +0.519 / +0.347 partial.)*

Higher correlation gives a **worse** blind region and a **better** disagreement
signal, and the second is not explained away by capability. Decorrelating shrinks
the region the detector cannot see while weakening the detector over the region
it can.

The mechanism is not established here and should not be asserted. The
measurement is: **there is a real tension, it goes the opposite way to the
intuition, and any "choose decorrelated models" recommendation has to price it.**
This was written down as a prediction before the run and it was wrong, which is
the second falsified prediction in this project and belongs in the write-up next
to the first.

### FINDING 10 — the models HOLD the belief; they do not merely fail to find the fact

*Added 2026-08-25. `scripts/belief_arms.py`, 12,432 generations.*

RQ4 handed models a document. RQ5 handed them a search tool. Both ask the same
question — can the model **find** the right fact — and neither separates it
from a different one: does the model **hold a belief** that evidence does not
dislodge? Two prompt-only arms separate them, on all 1,054 blind spots plus a
seeded control of 500 questions the ensemble already answered correctly.

**The control is the finding's spine.** "Counter-evidence repaired 12%" means
nothing if it also broke 12% of correct answers, and telling a model it might be
wrong is exactly the intervention that would.

**Re-derived 2026-09-27** on the deduplicated corpus (`belief`): 950 blind spots,
and the seeded control is now **317** (was 500 before deduplication and the
tie-rule fix).

| arm | repaired, of 950 blind spots | broke, of 317 correct — counting 2–2 ties | broke — requiring a majority wrong |
|---|---|---|---|
| **counter-evidence** — *"some sources disagree; reconsider"* | **0.74%** (7) | 3.79% (12; 10 are ties) | **0.63%** (2) |
| **abstention permitted** — *"if unsure, say I don't know"* | **0.00%** (0) [0.00%, **0.40%**] | 10.73% (34; 31 are ties) | **0.95%** (3) |

**"Counter-evidence breaks four times as many answers as it repairs" is
RETIRED** (it read 0.76% repaired vs 3.00% broken on the old corpus). Ten of the
twelve "broken" controls are 2–2 ties — cases the old tie rule scored as broken
by an accident of column order (ISSUES #67). Requiring a majority to be wrong,
repair and breakage are at **parity, both under 1%**. The robust statement is the
one that survives either reading: **counter-evidence does not move the belief —
under 1% either way.** Giving the model a reason to doubt, with no new
information, moves 7 questions out of 950. The belief is not a retrieval failure
that a nudge can shake loose.

**Explicit permission to abstain repairs exactly nothing.** Zero of 950, with
a Wilson upper bound of 0.40%. This is the direct answer to *"just make it say I don't
know"* — not a threshold on confidence, which RQ1 already ruled out, but
**asking the model outright**.

#### And yet the abstention signal is real

| | blind spots (n=950) | control (n=317) |
|---|---|---|
| at least one model abstained | **55.1%** (523) | **28.4%** (90) |

**1.94× lift, Fisher exact p = 9.0×10⁻¹⁷** (computed 27 Sep from the `belief`
block's rates; was 52.8% vs 25.2%, 2.09×, p = 3×10⁻²⁵ on the old corpus; the
majority-abstained row was not re-derived). The models hedge more than
twice as often on the questions they are about to get wrong together. The signal
is there, it is overwhelming, and it **never converts**: a majority almost never
refuses, and no question becomes correct.

This is the behavioural twin of RQ1's *"real signal, unusable margin"*, arrived
at from the opposite direction — RQ1 measured a number the model emits, this
measured what it does when asked. Both say the same thing, which is the strongest
form the claim has taken.

Note also that **of the 34 controls the abstention arm "broke", 31 are 2–2 ties
and only 3 are a majority wrong** (re-derived 27 Sep; the 2026-08-25 reading was
35 of 37 refusals). The cost is not that permission makes models wrong; it is that
they decline questions they had right.

---

### FINDING 11b — the inter-rater figure, measured

*Added 2026-08-26. Second annotator: Devesh. `scripts/handlabel2.py`.*

**The largest open limitation in this project is closed.** All 430 hand verdicts
were one person's, so there was no inter-rater reliability figure at all.

115 cases were labelled independently, blinded to every prior verdict, in two
strata the annotator could not distinguish: 70 drawn from the **385** the LLM
adjudicator did not contest, and a census of all 45 it did.

| stratum | population | sampled | both committed | κ | agreement |
|---|---|---|---|---|---|
| uncontested | **385** | 70 | 47 | 1.000 | 100.0% |
| disputed | 45 | 45 | 37 | 0.528 | 91.9% |
| **population, stratum-weighted** | **430** | 115 | 84 | **0.970** | **99.0%** |

> **Cohen's κ = 0.970, 95% CI [0.924, 1.000]** (`irr`), 4,000 bootstrap
> resamples within strata, seed 42. Almost perfect agreement on the Landis & Koch
> scale.
>
> **Corrected 2026-09-27 (ISSUES #69).** The uncontested stratum was sized at 296
> — the cases both raters had decided — but the 70 were drawn from every case the
> adjudicator did not contest, 385, including 19 the first annotator had left
> UNCLEAR. The published κ 0.962 [0.904, 1.000] and 98.7% under-weighted the
> stratum where the annotators agree perfectly. The per-stratum rows are the same
> labels and did not change.

**Quote the population line, never a stratum alone.** The uncontested stratum
was selected for being uncontested, so its κ = 1.000 is an upper bound; the
disputed stratum was selected for being contested, so its 0.528 is a lower one.
Neither estimates the 430, and an earlier version of this analysis reported the
first as though it did (ISSUES #56).

#### Three things fell out of it

**The second annotator sided with the first, not the machine.** On the 37
disputed cases where both committed, Devesh agreed with the first annotator
**34 times** and with the LLM adjudicator **3**. The hand labels survive the
only independent test available to them.

**Both annotators found a similar fraction undecidable.** Devesh returned
*unclear* on 19% of cases; the first annotator found 26% of the low-margin band
undecidable. Two people arriving independently at a similar rate is evidence
that the *unclear* category is measuring something real about the questions
rather than one person's caution.

**It does not disturb Finding 11c.** Only **1** of the 45 disputes runs in the
direction that drives the artifact measurement — the adjudicator calling the
grader too strict where the human did not. The artifact calibration rests on 43
such cases, and those sit in the *uncontested* stratum precisely because human
and adjudicator agreed on them.

---

### FINDING 11 — a third rater on the hand labels

*Added 2026-08-25. `scripts/adjudicate.py`. **Supplementary. It is not a second
human and must never be reported as one.***

> **Re-measured 2026-09-27 with alias lists (ISSUES #71).** The adjudicator had
> been shown the gold answer only; the human had labelled against the gold
> **and** every alias. 40 of the 45 disputes were human = correct, judge = wrong
> — the signature of a narrower key. Re-run with the alias lists
> (`adjudicator` in `summary.json`), κ against the human rises **0.688 → 0.782**
> and the disputes fall **45 → 29**. The tables below are the re-run; the
> no-alias figures are kept in brackets for the record.

All 430 verdicts are one person's, so the project has no inter-rater reliability
figure — the kappas it reports are agreement with the *machine*. A second human
on 100 cases remains the fix and remains scheduled. A frontier model reading the
same question, answer and accepted answers, with both other verdicts withheld,
is what could be run today.

| pair | Cohen's &kappa; | agreement | n |
|---|---|---|---|
| **human vs LLM adjudicator** | **0.782** (no aliases: 0.688) | 91.5% (86.8%) | 341 |
| human vs automatic grader | 0.459 | 79.2% | 341 |
| LLM adjudicator vs automatic grader | 0.354 (0.308) | 72.2% (68.2%) | 428 |

The adjudicator agrees with the human **substantially better than the project's
own grader does** (0.782 vs 0.459), and it declined or produced unparseable
output on only 2 of 430 cases. By stratum: κ 0.885 on the control cases
(n = 97 of 100), 0.750 on the target cases (n = 244 of 330).

**The obvious objection, measured.** The adjudicator is a member of the ensemble
it is judging, so it might favour its own family's answers.

| answers produced by | &kappa; vs human | n |
|---|---|---|
| the adjudicator's own family | 0.816 (no aliases: 0.696) | 85 of 101 |
| the other three makers | 0.771 (0.686) | 256 of 329 |

**A small gap in the self-favouring direction** — 0.045 with aliases (0.010
without). It is disclosed, not claimed: at 85 against 256 cases it is not
evidence of self-favouring, and it is not evidence against it either. Stated
because it was the first thing a reviewer would ask, not because the answer was
known in advance.

**What this is for.** It produced **29 cases where the human and the adjudicator
disagree** (45 before the alias re-run), and those are exactly the rows the
second human should be handed first. *(The second-annotator sample of Finding
11b was drawn from the 45 no-alias disputes, and that frame is frozen — ISSUES
#69.)* An inter-rater study on a random 100 spends most of its budget on cases
nobody disputes.

### Grading at scale — the tier distribution

| tier | rows | note |
|---|---|---|
| exact | 76,970 | |
| wrong | 71,628 | |
| alias | 8,827 | |
| **contains** | **8,366** | the rows defect #19 would have mis-graded |
| semantic | 4,573 | **only 2.7%** reach the negation-blind cosine tier |

On the pilot ~83% of rows reached the semantic tier; at full scale it is 2.7%,
because `SHORT_SPAN` now covers TriviaQA and HaluEval. The grader's known
weakness (cosine is blind to negation) now touches a small minority of rows
rather than most of them.

Per-model accuracy: Llama-4-Maverick 61.8% · Qwen3-235B 61.3% ·
Mistral-Small-3.2 55.0% · Gemma-3-27B 53.7% — an 8.1-point spread, narrower than
the 13.6 points the 60-question probe suggested.

### TruthfulQA re-grading (NLI)

```
accuracy      49.9% (cosine) -> 80.1% (NLI)
verdicts changed              501 of 1,360
ungradeable dropped           160 answers (40 questions, gold = "I have no comment")
low-margin (<0.10)            330 of 1,360 (24%)
```

The 24% low-margin rate is a stated limitation, not a footnote: on those rows the
entailment model could not separate the true answer from the baited one either.

Reproduce: `generate` → `grade` → `nli` → `disagree` → `embed`, no `--pilot`, no tag.

---

## 2026-07-27 · SCALE TEST — the same 300 questions, small models vs large

The frozen pilot question set re-run on the hosted 17–27B ensemble. Identical
questions, identical code, identical grader; **only the models differ**. This is
the cleanest small-vs-large comparison the project can make.

|  | local 7–9B | hosted 17–27B | Δ |
|---|---|---|---|
| AUC unweighted | 0.788 | 0.793 | +0.005 |
| **AUC confidence-weighted** | **0.776** | **0.801** | **+0.025** |
| majority_wrong rate | 0.656 | 0.509 | −0.148 |
| silent consensus (of 291) | 5 | 7 | +2 |
| mean disagreement | 0.466 | 0.420 | −0.046 |

### FINDING 1 — confidence-weighting is SCALE-DEPENDENT (claim reversal)

On the small ensemble, weighting by confidence **hurt** (0.776 < 0.788). On the
large ensemble it **helps** (0.801 > 0.793). The proposal's confidence-weighted
score was not wrong — it needs models whose confidences are calibrated enough to
carry information. At 7–9B they are not.

This is the two-scale design paying off: the result is neither "the method works"
nor "the method fails" but *"the method has a size threshold nobody has stated."*

### FINDING 2 — errors get MORE correlated as models improve (hypothesis)

Silent consensus rose 5 → 7 while accuracy improved substantially (majority_wrong
0.656 → 0.509). As a share of remaining errors that is roughly **2.6% → 4.7%** —
it nearly doubled. Reading: better models make fewer mistakes, but the mistakes
that survive are more likely to be **shared**.

If it holds, this is the strong safety story and it runs *opposite* to the
gen-1 → gen-2 "blind spots heal" reading (which is itself contaminated — see
DECISIONS.md, gen-1 dropped).

**CAVEAT: 5 vs 7 cases. Far too small to claim.** Stated as a hypothesis for the
43k screening run to test, not as a result.

### FINDING 3 — cross-model BEATS single-model at scale (claim reversal #2)

Semantic Entropy run on all four gen-3 models, same 4-generation budget, same
clustering — the only variable is whether the four generations come from one
model or four.

| arm | AUC |
|---|---|
| **FaultLines cross-model (confidence-weighted)** | **0.801** |
| FaultLines cross-model (unweighted) | 0.793 |
| Semantic Entropy — Llama-4-Maverick (best single) | 0.685 |
| Semantic Entropy — Mistral-Small-3.2 | 0.677 |
| Semantic Entropy — Qwen3-235B | 0.673 |
| Semantic Entropy — gemma-3-27b | 0.634 |

| | small 7–9B | large 17–27B |
|---|---|---|
| cross-model | 0.788 | **0.801** |
| best single-model SE | **0.813** | 0.685 |
| winner | single | **cross** |

The ensemble barely moved (+0.013). **Semantic Entropy collapsed (−0.128).**
Proposed mechanism: larger models are more self-consistent, so sampling one
model four times increasingly returns the same answer *even when wrong* —
self-consistency stops discriminating. Cross-model diversity does not degrade
that way, because different makers remain wrong about different things.

So the published claim (Hamidieh 2025; Gorbett 2026) that cross-model
disagreement beats single-model uncertainty **fails at 7–9B and holds at
17–27B** — the opposite conclusion from the pilot, and a size threshold nobody
has stated.

### FINDING 4 — blind spots CHURN rather than persist (clean arm)

Gen-2 hosted → gen-3 hosted. Same four makers, same provider, same precision,
same ensemble size; only the generation changes.

| | |
|---|---|
| gen-2 silent consensus | 5 |
| gen-3 silent consensus | 7 |
| persistent core | **1** |
| healed | 4 |
| newly emerged | 6 |
| persist rate / Jaccard | 20% / 0.09 |

Only 1 of 5 survived the upgrade, but 6 new ones appeared. Blind spots neither
persist nor simply heal — **they move**. Numbers remain small; this is the
43k run's question.

Supersedes the earlier gen-1 → gen-2 result (8 of 9 healed), which is
contaminated by a 3-maker vs 4-maker ensemble-size difference — see
DECISIONS.md.

### OPEN — does 4-bit quantization degrade the disagreement signal?

The same four gen-2 models scored **AUC 0.788 locally at 4-bit** and **0.860
hosted at full precision**. If real, quantization costs ~0.07 AUC, which would
be a methodological finding in its own right. **Not yet claimable:** the two
runs also differ in retry logic and `<think>`-stripping. Needs an isolated
comparison before use.

### Per-dataset AUC (unweighted)

| dataset | local | hosted | Δ |
|---|---|---|---|
| popqa | 0.872 | 0.761 | −0.111 |
| simpleqa | 0.738 | 0.772 | +0.034 |
| truthfulqa | 0.517 | 0.661 | +0.144 |

- **TruthfulQA's flatness was substantially a small-model artifact** — 0.517 (coin
  flip) → 0.661 (weak but real). Partially answers ISSUES.md item B. **But** the
  NLI grader also re-graded differently on this run (TruthfulQA accuracy 54.2%
  cosine → 78.8% NLI), so models AND grading both changed. Do not quote +0.144
  without separating the two.
- **PopQA got notably worse and this is an open puzzle.** Disagreement predicts
  error *less* well on obscure entities once the models are larger — on the one
  dataset RQ2's popularity control depends on.

Reproduce: `generate --pilot --tag _gen3` → `grade/nli/disagree --tag _gen3`.

---

# Earlier build (2026-07-23)

Real numbers, on the existing 300-question pilot data, from tested code.
Everything here is reproducible with `C:\venvs\faultlines\Scripts\python.exe`.

## Phase A — analysis on existing pilot data (DONE)

### RQ1 · Measure — confidence sees what the vote cannot
`python -m faultlines.rq1_confidence --pilot` · tests: `tests/test_rq1.py` (3/3)

- **Agreement region (50 unanimous questions): confidence predicts error at AUC 0.688**
  — where vote-counting is 0.5 by construction. The white-box signal survives where the vote dies.
- Monotonic gap at every agreement level (conf_correct > conf_wrong for clusters 1,2,3,4).
- **Two features beat one (5-fold CV AUC on majority_wrong):**
  disagreement alone **0.763** → confidence alone **0.805** → combined **0.820**.
  Validates the "two features, not one blended score" reframe. Combined > the 0.788 headline.
- Coefficients (z-scored): n_clusters +0.934, min_conf −0.692, mean_conf −0.483, disagreement −0.266.

### RQ2 · Localize — clusters, and survives the popularity control
`python -m faultlines.rq2_localize --pilot` · tests: `tests/test_rq2.py` (2/2)

- **Map-neighbourhood density predicts error at AUC 0.747** — errors cluster, not scatter.
- **Popularity control (PopQA, n=100):** popularity alone AUC 0.682 → popularity + map density **0.732**.
  The map carries signal *beyond* the long-tail effect. Defuses "it's just Kandpal 2023".
- corr popularity~error −0.353; corr density~error +0.261.

### Level 6 · Baseline — COMPLETED (full 4,656-gen run) — the honest result

> **Context, do not quote standalone:** this is the *local 7–9B* pilot. Finding 3
> above reverses it on the hosted 17–27B ensemble (cross 0.801 vs single 0.685),
> and the 8,000-question full-scale rerun is in flight. Both readings are kept
> because the reversal is the finding.

The single-model Semantic-Entropy baseline BEATS the cross-model ensemble on raw AUC:

| arm | AUC |
|---|---|
| Semantic Entropy — gemma2:9b (best single) | **0.813** |
| FaultLines cross-model (unweighted) | 0.788 |
| FaultLines cross-model (confidence-weighted) | 0.776 |

**The "cross beats single" claim is NOT supported by the pilot** (it also reverses Gorbett's
0.727>0.595 ordering). Per-dataset, single-model SE wins everywhere (popqa 0.880 vs 0.845,
simpleqa 0.792 vs 0.687, truthfulqa 0.581 vs 0.534).

**Why-analysis (complementarity):** corr(disagreement, SE)=+0.613 — overlapping but not identical.
The signals are COMPLEMENTARY: gemma SE alone 0.792 → +disagreement 0.818 → full white-box stack
(disagreement+confidence+SE) **0.838**, which beats the best single model. Honest framing:
*cross-model disagreement is complementary to, not better than, single-model self-consistency;
the ensemble's contribution is the map + findings, not a better detector.*

### A0 · NLI wired into the pilot
`scripts/run_pilot.py` now runs grade → **nli** → disagree, closing the orphan gap.

## Hand-off commands (multi-hour GPU passes, run on the laptop with Ollama up)

```
# Complete Level 6 (single-model semantic-entropy baseline): ~4,656 live gens
C:\venvs\faultlines\Scripts\python.exe -m faultlines.baseline --pilot
C:\venvs\faultlines\Scripts\python.exe scripts/run_pilot.py --report-only   # now shows the SE row
```

## Phase C — the tool (DONE, built + tested)
`scripts/export_tool_data.py` → `faultlines-tool/data.json` (291 points, 36 cases, real stats).
`faultlines-tool/index.html` — self-contained dashboard, verified in-browser:
- The map: 291 questions by x,y, 5 color modes (error / silent consensus / disagreement / confidence / popularity).
- Silent-consensus view highlights the 5 blind-spot cases (e.g. "author of The Book of Mormon" →
  all four say "Joseph Smith", all wrong).
- Labeling inspector: click/step through cases, tag real-vs-harmless + cause (obscurity/staleness/
  misconception/reasoning), persists to localStorage, exports JSON. This is the RQ1/RQ4 ground-truth engine.
- Console clean. Serve with `python -m http.server` from `faultlines-tool/` (file:// blocks fetch).

## Phase B — scaling experiments (code BUILT + TESTED, full runs handed off)

### B1 · Datasets — TruthfulQA non-adversarial filter
`faultlines/datasets.py` `filter_non_adversarial()` + `config.yaml`. AbstentionBench was
**dropped** (ships a `datasets` script, unsupported in datasets≥4, no self-contained files).
Instead: TruthfulQA filtered to the non-adversarial subset (removes GPT-3 selection pressure
that confounds RQ3), SimpleQA formally dropped. Misconception volume comes from screening.
Tests `tests/test_datasets.py` (2/2).

### B2 · Screening design — the 5→thousands lift
`faultlines/screen.py`. Small live run: **15 questions → 2 all-agree (13% yield)**. At a 20k
pool that is ~2,600 silent-consensus candidates. Fixed a real GPU-thrashing bug: generate
model-by-model (outer loop), not per-question, so each model loads once on the 8 GB card.
Tests `tests/test_screen.py` (3/3). Full run: `python -m faultlines.screen --pilot --pool 20000`.

### B3 · RQ4 retrieval dissociation
`faultlines/rq4_retrieval.py`. Retrieval via the MediaWiki API (User-Agent required; cached).
Small live run validated the pipeline AND caught a methodology bug — the closed-book arm must
use the SAME model as the retrieval arm (fixed). On n=4/stratum the result is noise (backwards,
even), which is exactly why the full run on screened strata is needed. Tests `tests/test_rq4.py`
(2/2). **Honest state: code correct + validated; the *result* needs the full run.**

### B4 · Track — ~~cross-generation persistence~~ — **SUPERSEDED, DO NOT QUOTE**

This section reported gen-1 (llama2:7b / qwen:7b / mistral:v0.1) → gen-2 as
*9 silent → 5 silent, 8 of 9 healed, persist rate 11%*.

**That comparison is retired.** Gen-1 carries three confounds that all move the
number in the same direction: **3 makers vs 4** (mechanically inflates the
all-agree rate), **4-bit vs full precision**, and it cannot be re-run hosted
because the models are not served. Generation and ensemble size changed together,
so nothing in it is attributable to generation. See DECISIONS.md.

The clean replacement is **Finding 4** above (gen-2 hosted → gen-3 hosted: same
four makers, same provider, same precision, only the generation differs), and the
full-scale version is queued.

---

## Test suite: 59 tests passing

datasets 2 · disagree 7 · generate 4 · grade_contains 5 · labelcheck 3 · nli 6 ·
rq1 3 · rq2 2 · rq4 2 · screen 3 · stratify 4 · track 2 · (plus module smoke tests).

Run: `C:\venvs\faultlines\Scripts\python.exe -m pytest tests -q`

## Status — what is done and what is left

*Rewritten 2026-07-29. The previous version of this section listed the two VOID
arms as "running" and "not yet run", and listed RQ4 as not run when it had been
completed the day before. A stale status block is worse than none — it is the
thing you consult when deciding what to do next.*

### ✅ Model-dependent work — COMPLETE

| Item | Scale | Result |
|---|---|---|
| generate · grade · NLI · disagree · embed | 42,591 q / 170,364 gen | AUC **0.862**, 1,054-case Audit population |
| RQ1 — confidence vs vote | full corpus | Finding 6 |
| RQ2 — clustering + popularity control | full corpus | Finding 7 |
| RQ3 — cross-generation persistence | 2,554 stratified, digest-verified local | 34.5% inherited share — superseded by the row below |
| RQ3 — full corpus | 42,591 q × 4 local models, exact | **39.4%** persist · 690 emerged (Finding 4) |
| RQ4 — retrieval dissociation | full-scale strata | obscurity **+68%**, misconception **+16%** (Finding 5) |
| SE baseline (single-model competitor) | 8,000 stratified × 4 models × 4 samples = 128,000 gen | Finding 3 |
| Finding 4b — error correlation vs capability | gen-2 vs gen-3, full corpus | **CONFIRMED** |
| Quantization control — 4-bit vs 8-bit | 2,554 q, same weights | aggregate stable, Jaccard 0.780 |
| Context-window optimisation | 150-q verification | **negative** — reverted, see below |
| Identity gating | 8 probes × all arms | retracted 2 arms (340,728 gen) |

No further model inference is required for any claim in this document.
**All model-dependent work completed 2026-07-29.**

### ⬜ Remaining — none of it needs a GPU

- ~~**TruthfulQA hand-labelling** (ISSUES 1b)~~ — ✅ **DONE 2026-07-29.** 430
  cases, blinded, two strata. TruthfulQA AUC 0.651 → 0.712 (delta +0.061, 95% CI
  +0.018 to +0.109); corpus AUC unmoved at 0.8654. **ISSUES 1b closed — zero open
  issues, code or methodological.**
- ~~**task abstraction**~~ ✅ **DONE 2026-07-29** — `TASKS.md`: 3 personas, 7
  domain tasks mapped through Brehmer & Munzner why/what/how to the view that
  answers each, the linked-view contract, an explicit out-of-scope list, and 6
  evaluation tasks *derived from the abstraction* so the expert sessions measure
  the designed tasks rather than whatever the interface makes easy.
- **The remaining VA gaps** — discovery walkthroughs (~1 day), expert evaluation
  with 3–4 people (~2 days). **This is the visual-analytics contribution.** It is the largest remaining block of work and
  the one the thesis framing depends on; the measurement engine above is its
  evidence base, not a substitute for it.
- **Front-end rebuild** — the tool is the artifact that gets expert-evaluated.
  Four panels, specified as jobs-to-be-done so the task abstraction falls out of
  the same design work: **Map** (where do errors live), **Audit inspector** (why
  did all four fail together), **Generation diff** (did the upgrade fix or cause
  this — RQ3, interactive), **Signal panel** (how much to trust the signal here).
  Design in DECISIONS 2026-07-29. **Currently publishes retracted numbers —
  ISSUES #37.**
- **The write-up.**

### Order of the remaining work, and the one calendar risk

```
1  front-end rebuild        blocks 3 and 4
2  task abstraction         independent (writing); partly done by the panel specs
3  discovery walkthroughs   needs 1
4  expert evaluation        needs 1 and 3  <-- RECRUIT NOW
```

Items 1–3 move at the speed of work. Item 4 moves at the speed of other people's
calendars, so participant recruitment is the critical path and was started
2026-07-29 independently of the build.

### Deliberately abandoned (do not resurrect)

- `ensemble_gen2` hosted full corpus and the Gemma 2×2 ladder — VOID, models were
  substituted (ISSUES #31). Superseded by the digest-verified local arm.
- Reduced context length for Gemma-2 — changes its answers (see below).

---

## 2026-07-28/29 · Quantization: does 4-bit change the disagreement signal?

Closes an open question carried since the pilot, previously marked NOT CLAIMABLE
because the only two runs available differed in retry logic and think-stripping
as well as precision. This is the controlled version: **same weights, same 2,554
questions, same prompts, same grader — only the precision differs.**

| | 4-bit (Q4_K_M / Q4_0) | 8-bit (Q8_0) | delta |
|---|---|---|---|
| RQ3 persistence | 34.5% | 37.1% | +2.6 pp |
| corpus blind-spot rate | 1.96% | 1.63% | −0.33 pp |
| majority wrong | 67.0% | 66.8% | −0.2 pp |
| mean disagreement | 0.352 | 0.344 | −0.008 |
| **item-level agreement on majority_wrong** | | | **95.7%** |
| **blind-spot set overlap (Jaccard)** | | | **0.780** |

> **Re-derived 2026-09-27 (ISSUES #75), `scripts/compare_precision.py`, 2,152
> questions after dedup.** 4-bit vs 8-bit: persistence 33.7% vs 36.5%, corpus
> blind rate 2.23% vs 1.83%, majority wrong 71.8% vs 71.8%, mean disagreement
> 0.367 vs 0.358. **Stratum-weighted** item-level agreement **94.4%** and
> blind-spot Jaccard **0.644** (unweighted, as the table above computed them:
> 96.2% and 0.777). The sample is every gen-3 blind spot plus a random draw of
> the rest, so the unweighted overlap described the sample, not the corpus.
> Δ persistence 0.028 (tolerance 0.05) and Δ blind rate 0.0041 (tolerance
> 0.005): **the pre-registered verdict still passes. But about a third of
> blind-spot membership changes with precision, not a fifth** — the "~22%" and
> "~78% likely" below are superseded.

**Answer: quantization does not degrade the signal — it reshuffles membership.**

Every aggregate lands within a few points, and the RQ3 story ("about a third of
blind spots persist") is unchanged. But the **identity** of the blind spots moves:
343 shared out of 381 vs 402, Jaccard 0.780, so roughly **22% of individual blind
spots differ between precisions**.

That distinction matters for how the Audit view is used. A *rate* quoted from
4-bit models is trustworthy; a *specific question* identified as a shared blind
spot at one precision is ~78% likely to be one at another. Report the rate with
confidence and treat individual case lists as precision-dependent.

Why 8-bit rather than fp16: the hosted gen-3 arm is not full precision either
(`Llama-4-Maverick-17B-128E-Instruct-FP8`), so there is no full-precision
reference to match; fp16 would also be 14–18 GB against 8 GB of VRAM. See
DECISIONS.md.

## 2026-07-28/29 · Context window is NOT a free optimisation for Gemma-2

Attempted, measured, reverted. Recorded because the failure is informative.

`gemma2:9b` is the throughput bottleneck: 9.2B parameters do not fit in 8 GB
alongside a 4,096-token KV cache, so it runs 20% on the CPU at **1.5 q/s** while
the other three models run entirely on the GPU at **4.5 q/s**. Prompts on this
corpus are ~40 tokens (max 235) and answers are capped at 64, so ~300 tokens are
actually used — Ollama was reserving 14x more than needed.

Shrinking the window fixed the memory problem completely:

| context | VRAM | placement | answers identical to stored |
|---|---|---|---|
| 4096 (default) | 7.1 GB | 20%/80% CPU/GPU | **150/150 (100%)** |
| 2048 | 5.9 GB | **100% GPU** | 142/150 (94.7%) |
| 512 | 5.6 GB | **100% GPU** | 142/150 (94.7%) |

**The same 8 questions changed at both reduced settings, to the same wrong
answers** (`Sinbad -> Redd Foxx`, `Matt Reeves -> David E. Kelley`). Deterministic,
therefore not sampling noise — and the control at the default setting reproduced
150/150, proving local generation IS deterministic and the change was causal.

Gemma-2 uses sliding-window attention whose layout depends on the configured
context length, so the window is not a pure memory reservation for this
architecture the way it is for the others.

**Reverted.** ~7 hours of speedup is not worth 5% of one model's answers silently
changing mid-experiment. The full-corpus run uses the default, which is the only
setting verified byte-identical.

**Confound found and removed during the test:** restarting Ollama kills the parent
process but leaves `llama-server.exe` children running with models resident. Three
orphans held **7,893 of 8,188 MiB of VRAM**, which made an intermediate 2048 test
report 63% CPU placement — worse than default — and nearly produced the wrong
conclusion. Kill `llama-server` explicitly, and check `nvidia-smi` before
interpreting any placement measurement.

---

## 2026-07-29 · HAND-LABELLING — ISSUES 1b CLOSED

430 TruthfulQA verdicts hand-labelled on the gen-3 headline arm, blinded, in two
strata. Reproduce with `python scripts/handlabel.py --result`.

### The grader is excellent where it is confident, and near-arbitrary where it is not

| stratum | n labelled | raw agreement | **Cohen's kappa** | unclear |
|---|---|---|---|---|
| **control** (\|margin\| ≥ 0.10) | 97 | **99.0%** | **0.959** | 3/100 (3.0%) |
| **target** (\|margin\| < 0.10) | 244 | 71.3% | **0.322** | 86/330 (**26.1%**) |

This is the result the two-stratum design existed to produce, and it is a clean
dissociation. **The NLI grader is not broadly unreliable — it is unreliable in
exactly the band it already flags as uncertain.** One disagreement in 97 confident
cases (kappa 0.959, near-perfect) versus 70 in 244 uncertain ones (kappa 0.322,
poor). Had we labelled only the low-margin band, the honest conclusion would have
been "the grader agrees with a human 71% of the time" — which reads as an
indictment of the whole dataset and would have been wrong.

### 26% of the low-margin band is unlabelable BY A HUMAN

The finding that changes how this should be written up. A human, given
TruthfulQA's own reference answers and its own baited wrong answers, could not
decide **86 of 330** low-margin cases — against **3 of 100** controls, a 8.7×
difference.

**The low-margin band is not a grader weakness. It is intrinsic ambiguity in
TruthfulQA.** The entailment model's near-zero margin is a *correct report* of a
genuinely undecidable comparison, not a failure to compute. That reframes ISSUES
1b from "our grader is weak on 24% of TruthfulQA" to "24% of TruthfulQA does not
have a decidable answer under its own rubric" — a property of the benchmark that
belongs in the limitations chapter and is defensible under questioning.

### Corrected AUC — real, significant, and imprecise

| | AUC | 95% CI (4,000 bootstrap) | positives |
|---|---|---|---|
| as published | 0.651 | [0.580, 0.720] | 70 |
| **label-corrected** | **0.712** | [0.638, 0.784] | 60 |
| **delta** | **+0.061** | **[+0.018, +0.109]** | 16 verdicts flipped |

The delta does not cross zero, so the improvement is real. But **both intervals
are ±0.07 wide** because TruthfulQA has only 340 questions, and the two CIs
overlap heavily. Quote it as *"hand-correcting the labels raises TruthfulQA's AUC
by roughly 0.06 (95% CI 0.02–0.11)"* — never as a bare "0.712".

This is **3.5× the previously estimated correction** (+0.017, from 19 known
disagreements in DATASET_ANALYSIS.md). The earlier estimate was extrapolated from
a 50-case pilot; this is a census of the affected band.

`majority_wrong` was recomputed from scratch by re-clustering, and **the
reclustering reproduces the published column 340/340** before any corrected
number is reported — `--result` exits non-zero if it does not. Without that check
the corrected AUC would not be comparable to the published one.

### The headline is untouched

| | corpus AUC | silent consensus |
|---|---|---|
| as published | 0.8651 | 1,054 |
| label-corrected | **0.8654** | 1,052 |

341 of 170,364 answers were relabelled — 0.20% of the corpus. **The headline
0.865 does not move, and neither does the Audit population.** TruthfulQA is 340
of 42,551 questions; it cannot move a corpus number, which is the same reason
HaluEval was brought in to take over its statistical job (0.834 at n=10,000).

Stated plainly for the defence: *the weakest dataset got better, the headline did
not change, and we now know why the weakest dataset was weak.*

### Residual error is BOUNDED — what the control stratum bought

> **Corrected 2026-09-27.** This read *"330 answers, 28.7% were wrong → ~95
> corrected … the correction is ~90% complete"*. `handlabel.py` computed
> `0.287 × 330`: 28.7% is the error rate over the **244 committed** target
> verdicts (70/244), and applying it to all 330 counts the 86 UNCLEAR cases as
> though 28.7% of them had been corrected. None of them were — an UNCLEAR case
> keeps the machine verdict. The same shape as ISSUES #63: a rate applied to a
> denominator it was not measured on.

Recomputed from `data/processed/handlabels.parquet` and the TruthfulQA rows of
`answers.parquet` (1,360 gradeable answers: 330 with |margin| < 0.10, 1,030 at or
above):

```
corrected           target stratum: human != machine on 70 of 244 committed   = 70 exactly
still wrong, est.   86 UNCLEAR target cases x 70/244 (28.7%)                  ~ 24.7
                    1,030 high-margin answers x 1/97 (1.0%, control stratum)  ~ 10.6
completion          70 / (70 + 24.7 + 10.6)                                   ~ 66.5%  -> ~67%
  if UNCLEAR is undecidable (not an error to correct):  70 / (70 + 10.6)      ~ 86.8%  -> ~87%
```

**The correction is about two-thirds complete** — or about 87% if the UNCLEAR
cases are counted as having no correct label to restore, which is the reading the
"26% of the band is unlabelable by a human" finding above supports. The remaining
high-margin error is ~11 answers out of 1,360. (The control stratum's own one
disagreement is also corrected; counting it, 71 / (71 + 24.7 + 9.6) ≈ 67% and
71 / (71 + 9.6) ≈ 88%.) A single-stratum design could not have said any of this —
it could only have reported the fraction fixed, with no denominator for what
remains.

**The AUC correction, re-run 2026-09-27** (`handlabel.py --result`, which now uses
the same tie rule as `records.parquet` and still reproduces 340/340): TruthfulQA
0.683 [0.609, 0.754] as published → **0.725** [0.651, 0.794] label-corrected,
Δ **+0.042 [−0.000, +0.089] — the interval crosses zero**, 13 verdicts flip;
corpus 0.8403 → 0.8405, silent 950 → 948. Scored on the head-count score, as
every other AUC in the thesis is (ISSUES #78: this script and the ablation had
used the confidence-weighted score; on it the delta was +0.046 [+0.002, +0.095],
which also only just excluded zero). The tables above are the 2026-07-29 run.

### A standing prediction that FAILED — watch-list item #2 amended

Watch-list item #2 asserted that *every* grading weakness turns wrong answers
into apparent correct ones, so all grading noise flatters the AUC. On this band
it does not hold:

```
of 70 target disagreements:   machine too GENEROUS 31
                              machine too HARSH    39
```

Roughly balanced, tilting **harsh**. The prediction was formed from the cosine,
containment and semantic tiers — all of which were one-directional — and NLI was
the fix for exactly those. The correct reading is not that #2 was wrong, but that
**it was a property of the graders it was derived from, and the NLI replacement
does not inherit it.** Consistent with this, the correction *reduced* silent
consensus (1,054 → 1,052) rather than increasing it, which item #2's decision
rule flags as "deserving scrutiny" — the scrutiny is this paragraph, and the
harsh-leaning direction explains it.

Recorded because a failed prediction is more useful than a confirmed one, and
because item #2 is still used to justify reading the AUC as a mild over-estimate.
That justification now applies only to the pre-NLI graders.

---

## 2026-08-25 · CORRECTION — the artifact is 21.7%, not 5.6%

> **Superseded 2026-09-27.** On the deduplicated corpus the adjudicated population is the
> **950** blind spots, and after the 27 Sep re-run the judge has decided **all
> 950** (0 undecided): **21.05% [18.58%, 23.76%]** are artifacts (200 of 950), so
> **750 genuine** (`artifact`). By dataset: HaluEval 33.88% (366), TriviaQA
> 33.57% (140), PopQA 6.15% (439), TruthfulQA 40.00% (5). The 45 cases undecided
> before the re-run were **failed calls, not declines** (ISSUES #71) — as were
> the "56 UNCLEAR" below — and were re-asked on 27 Sep. *(Until then this box
> quoted 21.1% of 905 decided; the per-dataset n for PopQA and TriviaQA were the
> decided-only counts.)*

**The bound below is wrong, and wrong in the direction that flattered this
project.** It is left in place rather than rewritten, because how it was wrong
is the more useful thing.

`scripts/adjudicate_blind.py` put an LLM adjudicator to **all 1,054 blind
spots** — the population the claim is actually about — with the automatic grade
withheld. It committed to a verdict on 998.

| dataset | n | grader was too strict | 95% CI (Wilson) |
|---|---|---|---|
| HaluEval | 366 | **33.88%** | [29.22%, 38.87%] |
| TriviaQA | 196 | **32.65%** | [26.48%, 39.50%] |
| PopQA | 431 | 6.26% | [4.34%, 8.96%] |
| TruthfulQA | 5 | 40.00% | [11.76%, 76.93%] |
| **ALL** | **998** | **21.74%** | **[19.30%, 24.41%]** |

**Four times the previously reported bound.** A sample, unedited:

```
"Bangladesh"            for  "People's Republic of Bangladesh"
"Alfred Santell"        for  "Alfred Allen Santell also known as Al Santell..."
"1640s"                 for  "40's"
"The bumblebee bat"     for  "Bat"
"Constantine X Doukas"  for  "Konstantinos X Doukas"
"Smoking"               for  "Tobacco or alcohol"
```

### Why 5.6% was wrong, and it was not a measurement error

The 5.6% below is an **exact count of one kind of artifact**: cases where all
four answers sit *inside* the gold string and were rejected by the short-form
ratio guard. That test is syntactic. It cannot see `"1640s"` against `"40's"`,
or a transliteration, or `"Smoking"` against `"Tobacco or alcohol"`, because
none of those is a substring of anything.

**A bound on one failure mode was reported as a bound on the phenomenon.** The
number was right; the word "upper" was not.

### The judge was calibrated before this was believed

On the 430 hand-labelled cases both a human and the judge saw the same answers,
so the judge's precision on exactly this call is measurable rather than assumed:

| | |
|---|---|
| machine said WRONG, judge said CORRECT | 43 cases |
| the human agreed the answer was correct | **30 of 31** who committed — **96.8%** |
| the human said it really was wrong | 1 |
| machine said WRONG, judge said WRONG | 80 cases |
| the human called correct **anyway** | 10 of 62 — **16.1%** |

So the judge is **accurate when it flags, and conservative**. *(Corrected
2026-09-27: this said it "misses about one artifact in six that a human
catches". 10 of 62 is the share of the judge's **wrong** calls that the human
called correct — not a miss rate. Of the **40** cases the human called correct,
the judge flagged 30 and missed **10: a miss rate of 25%, one in four.**)*
**21.74% is therefore closer to a floor than a ceiling** — more so than the
original sentence said. Both calibration figures come from TruthfulQA and rest
on n = 31 and n = 62; they are a check on direction, not a correction factor,
and no correction factor is applied.

### What this changes, and what it does not

**Changes.** The blind-spot count is an upper bound with a much larger
correction than stated: roughly **825 genuine cases** rather than ~995, and a
rate nearer **1.94%** than 2.48%. Every rate whose denominator or numerator is
the blind-spot set inherits this, including RQ5's 67.9% ceiling and the belief
arms.

**Does not change.** The independence result (φ = 0.667, 9.0× at the time; now
3.3× within dataset, ISSUES #68) is computed from
per-answer correctness and never touches silent consensus. And the *comparisons*
are far more robust than the levels: both RQ3 arms are graded by the identical
pipeline, so a grader that is uniformly too strict shifts both and largely
cancels in the 2.17% —> 2.48% rise and the 1.518× shared-share ratio. That is
an argument, not a measurement, and it is stated as one — the direct test is to
re-run this adjudication on the 2024 arm, which is specified and not yet done.

**The artifact rate is wildly dataset-dependent** (6% on PopQA, 34% on HaluEval),
which is itself the most useful thing here: PopQA's Wikidata keys are tight,
HaluEval's and TriviaQA's are prose. Any single global figure conceals a 5×
spread.

---

## 2026-08-01 · The 1,054 is an UPPER BOUND — answer-key strictness, measured

> **SUPERSEDED 2026-08-25 by the section above. The 5.6% here is an exact count
> of the CONTAINMENT artifact, and was reported as though it bounded all
> artifacts. It does not. Kept because the reasoning is sound and only the scope
> claim was wrong.**

**Found by using the tool**, not by an audit: browsing tab 2, many "still broken"
cases showed every model giving a *correct but shorter* answer than the key
demanded. Measured rather than accepted.

### How big

| | |
|---|---|
| blind spots where **all four** answers sit inside the gold, rejected **only** by the short-form ratio guard | **59 of 1,054 = 5.6%** |
| same test, any containment direction | 79 of 1,054 = 7.5% |
| flagged in the tool (union of both arms) | 60 of 1,613 cases |

```
"Bangladesh."   for  "People's Republic of Bangladesh"           ratio 0.33
"China"         for  "People's Republic of China"                ratio 0.20
"The Hague."    for  "It is located in The Hague, Netherlands…"  ratio 0.05
"1978"          for  "1978 FIFA World Cup Final"                 ratio 0.16
```

Not all 59 are wrongly graded — `"Hurricane"` for `"1915 New Orleans hurricane"`
and `"Plants."` for `"flowering plants"` are arguably too vague to be right. So
**5.6% is an upper bound on the artifact, and the true blind-spot count is
somewhere between ~995 and 1,054.**

### Why the five grading tiers did not catch it

They ran. All of them. Corpus-wide tier distribution:

| tier | rows | share |
|---|---|---|
| exact | 76,956 | 45.2% |
| alias | 8,816 | 5.2% |
| contains (ratio-guarded) | 8,366 | 4.9% |
| **semantic (cosine)** | 3,839 | 2.3% |
| NLI entailment (TruthfulQA) | 1,520 | 0.9% |
| wrong | 70,867 | 41.6% |

**The similarity tier did run on these cases and rejected them on the evidence.**
Measured cosine for the 240 answers inside the flagged blind spots:

```
median 0.652   mean 0.638      threshold 0.80
pass at 0.80    4 of 240   2%
pass at 0.70   72 of 240  30%
pass at 0.65  122 of 240  51%
```

### Why lowering the threshold is NOT the fix

Because the encoder ranks a **wrong** pair above a **right** one on this corpus —
measured, and the reason the containment tier exists at all:

```
"Henley Rowing Club" vs "Leander Club"    0.781   DIFFERENT clubs
"Sheppey"            vs "Isle of Sheppey" 0.526   the SAME place
```

Dropping the threshold to 0.65 to admit "Bangladesh" also admits
"Henley Rowing Club = Leander Club". **No threshold separates them**, because the
distinction is factual, not semantic. This is a property of the embedding space,
not a tuning mistake.

### What was done instead

The tool now **flags** these cases rather than silently keeping or silently
re-grading them: an amber banner on the case, and a filter chip
*"⚑ Answer key looks strict (60)"*. A human decides — which is precisely the job
tab 2 exists to support, and precisely what the hand-labelling pass did for
TruthfulQA.

**For the write-up:** quote **1,054** with the sentence *"an upper bound; up to
5.6% may be answer-key artifacts rather than model errors, flagged in the tool
for review."* Reviewers will find these cases in minutes — better that the tool
points at them first.

**Direction of the error:** this one runs **harsh** (marks right answers wrong),
which *inflates* the Audit population. That is the third piece of evidence
against watch-list item #2's claim that grading error always runs generous — it
held for the cosine and containment tiers, and does not hold for the ratio guard
or for NLI.

---

## 2026-08-01 · CORRECTION — the RQ3 categories are about VISIBILITY, not correctness

**Found by a user reading tab 2 and asking "how is this newly broken when 2025
looks right?"** The data was correct; the *labels* were wrong, and they were
wrong in a way that misstates the finding.

### What the numbers actually are

| category | n | 2025 all wrong | 2024 all wrong | has a right answer |
|---|---|---|---|---|
| hidden in both (persisted) | 364 | 364 | 364 | none, either year |
| **newly hidden** (emerged) | 690 | 690 | **538 (78%)** | 2024: 152 |
| **now visible** (healed) | 559 | **293 (52%)** | 559 | 2025: 266 |

**Zero contradictions** — no "emerged" case has a correct 2025 answer. The
categories were computed correctly throughout.

### Why the old labels were wrong

- **"Newly broken" was wrong.** In **78%** of those cases the 2024 models were
  *also* all wrong — they simply **disagreed**, so a disagreement check would have
  flagged it. The models did not newly break. **They stopped disagreeing.**
- **"Fixed" was wrong.** **52%** of "healed" cases are *still* all wrong in 2025.
  They are not fixed; they merely became *detectable* again.

### The corrected framing — and it strengthens the finding

```
hidden in both  364   agreed on a wrong answer in both years
newly hidden    690   a check could catch it in 2024; in 2025 the models agree, so it cannot
now visible     559   invisible in 2024; in 2025 they disagree again, so a check can catch it
```

The thesis claim is **not** "newer models make more mistakes". It is sharper:

> **Newer models go blind on almost twice as many questions as they inherit** —
> not because they are more often wrong, but because they increasingly **agree**
> when they are wrong. The errors did not grow; the *warning* disappeared.

That is a better result than the one the old wording implied, and it is exactly
the safety argument: capability improved, detectability fell.

### Fixed in the tool

Each case now states, computed from its own answers, why it is in its category —
distinguishing the 152 that genuinely regressed from the 538 that merely stopped
disagreeing. The labelling controls also now say **which set of answers** you are
judging (2025 for newly hidden, 2024 for now visible, both for hidden-in-both),
which was previously ambiguous.

**For the write-up:** never write "newly broken" or "fixed" for these categories.
Use *newly hidden* / *now visible* / *hidden in both*, and state that the axis is
detectability.

---

## 2026-08-01 · An entity-LOOKUP tier: works in ONE DIRECTION, and that is enough

**The question a reader asked:** if similarity cannot decide identity, why not
look the two strings up and ask whether they are the same thing?

Built (`scripts/lookup_grader.py`) and measured, rather than argued.

### It fires on the six diagnostic pairs where everything else failed

| pair | truth | cosine (0.80 bar) | NLI | **lookup** |
|---|---|---|---|---|
| Bangladesh / People's Republic of Bangladesh | right | 0.776 ✗ | 0.827 | **✅ same** |
| York / New York City | **wrong** | 0.891 ✗ *(accepted!)* | 0.969 ✗ | **✅ different** |
| China / People's Republic of China | right | 0.596 ✗ | 0.257 | **✅ same** |
| Gene Kelly / Fred Astaire | wrong | 0.310 ✓ | — | ✅ different |
| Sheppey / Isle of Sheppey | right | 0.526 ✗ | — | ❌ different |
| Eisenhower / Carroll W. McColpin | wrong | 0.267 ✓ | — | abstains |

**4 of 6, and correct on both cases that no similarity method can separate.**

### On the hand-label set it measures nothing — and that is informative

Of 341 hand-labelled verdicts, **9 (2.6%)** are entity-shaped on both sides.
TruthfulQA answers are sentences. **The validation set cannot test this tier**,
which is worth saying out loud rather than reporting a meaningless number over
n=1.

### On the population it is FOR — the 60 answer-key flags

| | |
|---|---|
| decided | **20 of 60 (33%)** · abstained 40 |
| said **SAME** (model right, key too strict) | **7** |
| said **DIFFERENT** (model really wrong) | 13 |

**The 7 accepts are 7/7 correct** — one Bangladesh, six China/People's Republic
of China.

**The 13 rejects are mostly wrong.** `Laika` vs `Laika Entertainment`,
`1978` vs `1978 FIFA World Cup Final`, `Horror` vs `horror literature`,
`Lakeside` vs `Lakeside Shopping Centre` — in each the model gave the right
answer in a shorter form, and the lookup resolved the bare word to a *different*
article (Laika the dog, the year 1978, the literary genre). Only about 3 of 13
are defensible.

### The finding: an ASYMMETRIC tier

> **Lookup can be trusted to ACCEPT and must never be used to REJECT.**

Two independent reasons:

1. **Measured precision.** 7/7 on accept, roughly 3/13 on reject. A shortened
   entity mention resolves to a *different* article far more often than to none —
   the failure mode is systematic, not noise.
2. **Direction of error.** Accept-only can only *shrink* the Audit population.
   Watch-list item 3 says every unintentional bias in this project has favoured
   its own hypothesis; a tier that can only make the headline number **smaller**
   is the one direction that needs no defence.

**Effect if shipped as accept-only:** 7 of 1,054 resolved automatically, ~0.7%.
Small — and that is the point. It converts a *judgement call* into a *fact* for
the cases where a fact exists, and abstains on the other 93%, which stay exactly
what ISSUES 2b says they are: undecidable without a human.

**For the write-up.** This is the constructive half of "similarity cannot decide
identity". The negative result stands, the remedy is real but narrow, and its
narrowness is measured: 33% decidable, 12% safely decidable, 67% abstain.
`data/processed/lookup_keyflags.parquet` has every verdict.

---

# RQ5 — Agentic tool use. Wikipedia arm, complete (2026-08-02)

**The objection this answers.** Every reader of this thesis asks the same thing:
*surely a modern model with search would fix these.* RQ4 handed models passages
they did not ask for. RQ5 hands them a tool and lets them decide when and what to
look up — up to 4 lookups, their own queries, their own stopping point.

**Population:** the 1,054 silent-consensus questions — every one a case where all
four models agreed on the same wrong answer closed-book.

## The headline

Of **977** questions where all four models produced an answer with tools:

| outcome | n | share |
|---|---|---|
| at least one model now correct | 241 | **24.7%** |
| **still all four wrong** | **736** | **75.3%** |

**Three quarters of silent consensus survives the models being able to search.**

The models used the tool — this is not a story about an unused affordance:
**94.9% of runs called a tool, mean 2.01 calls.**

## Tool health — the gate that makes this quotable

**6,274 tool calls · 0 failed (0.0%) · 520 returned nothing (8.3%).**

This is the RQ4 lesson (#28-30) discharged. RQ4's first three attempts reported
models as incapable when the retrieval layer was silently refusing 16% of calls.
The 0% here is what earns the right to interpret the numbers above; the 8.3%
empty results are true misses (Wikipedia has no such article), not failures, and
the two are distinguishable because **success is cached and failure never is**.

## Per dataset — and the prediction this FALSIFIED

| dataset | composition | rescued |
|---|---|---|
| **popqa** | deliberately obscure long-tail entities | **13.8%** (62/450) |
| triviaqa | general trivia | 25.0% (52/208) |
| halueval | built to elicit hallucination | 39.4% (124/315) |
| truthfulqa | common misconceptions | 75.0% (3/4) — **n=4, do not quote** |

**Written before the run:** search should help OBSCURITY most (more sources, more
coverage) and MISCONCEPTION least. **The obscure set was helped LEAST.** The
prediction was wrong, and it was wrong in the direction that makes the finding
stronger — so it is reported as a falsified prediction, not quietly dropped.

**The honest reading, stated as a hypothesis and not yet tested:** RQ4's +68% on
obscurity was measured over *all* obscure questions. This is measured only on
obscure questions so hard that four independent models converged on one wrong
answer. Those are different populations by construction. **Checkable against the
existing RQ4 data — do that before making any claim about the mechanism.**

## Per model — and a finding hiding in the compliance numbers

| model | rescued | called a tool | mean calls |
|---|---|---|---|
| Qwen3-235B | 13.9% (140/1010) | **80.6%** | 1.85 |
| Mistral-Small-3.2 | 13.7% (143/1047) | 100% | 1.90 |
| Llama-4-Maverick | 13.0% (133/1020) | 98.5% | 2.07 |
| gemma-3-27b | 11.0% (116/1054) | 100% | 2.27 |

Rescue rate is remarkably flat: **11–14% across four makers**. One model at 13%
is a quirk; four converging is the result.

**Qwen skipped the tool on 1 question in 5** — on questions its own maker's model
got wrong closed-book. *Having* a tool and *using* a tool are separable, and the
gap is measurable. Worth its own line in the write-up.

### "Maybe the agent was just weak" — measured, not argued (2026-08-03)

The single most likely objection to RQ5. Three checks, all on data already on
disk, all pointing the same way.

**1. The tool worked.** Not broken, not ignored, not a null caused by plumbing.

| | runs | rescued |
|---|---|---|
| did **not** use the tool | 211 | **3.8%** |
| used the tool | 3,920 | **13.4%** |

**3.5× better with it than without.** So "your retrieval was broken" is not
available — this is the same arm that would have caught it (ISSUES #28–30 is why
the health gate exists).

**2. More of it did not help — the 4-lookup ceiling was not the constraint.**

| lookups used | runs | rescued |
|---|---|---|
| 1 | 1,229 | 13.6% |
| 2 | 1,410 | 13.6% |
| 3 | 822 | 14.5% |
| **4 (whole budget)** | 459 | **10.0%** |

Flat, then **down**. The runs that spent the entire budget did *worse* than the
runs that searched once — which is what "searched repeatedly and never found it"
looks like, not what "needed more searches" looks like. Raising the cap to 8 or
10 has no support in this curve. State it before a reviewer asks for the bigger
run.

**3. It was not one bad model.** Four makers, four independent implementations,
rescue rates 11.0 / 13.0 / 13.7 / 13.9 (table above).

**The claim this licenses:** the agent was not the limiting factor. It is not
*"tools do not help"* — they clearly do, 3.8% → 13.4%. It is **"tools help, and
they do not reach these questions."**

## What is NOT in the 977 — state this, do not bury it

1,054 asked, **977 counted, 77 dropped (7.3%)**. A dropped question is one where
some model exhausted its 4 lookups and never committed to an answer. Concentrated
in Qwen (1,010 of 1,054 complete) and absent in gemma/Mistral (100%).

These were **never silently retried into existence**: a run that produces no
answer is not recorded, so a resume re-attempts it. 42 of the first 53 retries
came back empty again — evidence these are systematically unanswerable under the
text protocol, not transient. `rq5_agentic.py` now logs the qid and lookup count
for each, so the next run can characterise them instead of just counting them.

## Provenance

All 4,131 rows come from one version of the pipeline. 160 rows produced before the
cooldown fix were identified positionally, verified by composition, dropped and
re-run — see ISSUES #41. Headline moved 24.4% → 24.7%, i.e. the contamination was
not material, but it is now provable rather than assumed.

**Open:** the open-web arm (`--arm web`) is built and smoke-tested but NOT run.
Until it is, the claim "retrieval draws from the same web that taught the
misconception" remains RQ4's *explanation*, not a measurement.

---

# RQ5 — the open-web arm. The CEILING is the finding (2026-08-02, retitled 2026-08-25)

> **Retitled.** This section was called *"the comparison IS the finding"*. It is
> not: the wiki-vs-web difference is +3.1pp on 12 discordant pairs, McNemar
> exact **p = 0.388**, and no framing of it as a difference between tools
> survives. What survives is better and is stated below — **neither** tool
> repaired 67.9% of matched cases. See DECISIONS.md 2026-08-25.

**Tool:** Tavily search API, `include_answer=False`, `search_depth=basic`.
The answer flag is off deliberately — see DECISIONS 2026-08-02 §3. Letting the
search provider's own LLM answer would have measured *model vs model*, not
*does the open web contain the correction*.

**n:** 151-question sample, stratified by dataset, seed 42. Sampled because free
search tiers are ~1,000 credits and the full arm needs ~6,000-8,000.
**Tool health: 956 searches · 0 failed (0.0%) · 0 empty.**

## The matched comparison — 131 questions run through BOTH arms

Comparing 29.1% against 24.7% would have been wrong: different question sets.
Restricted to the questions that completed in both arms, with all four models:

| | rescued | still all four wrong |
|---|---|---|
| Wikipedia | 34/131 — **26.0%** | 74.0% |
| open web | 38/131 — **29.0%** | 71.0% |

**Paired difference: +3.1pp, 95% CI [-2.1, +8.2]pp, McNemar exact p = 0.388.**

**There is no detectable difference between an encyclopedia and the open web.**

Only 12 of 131 questions disagreed at all (8 web-only, 4 Wikipedia-only). 30 were
fixed by both, **89 by neither**.

## The number to quote

> **Superseded 2026-09-27.** On the deduplicated blind-spot set the matched comparison has
> **136** questions (complete in both arms **and** still a blind spot);
> **88 (64.7%, Wilson [56.4%, 72.2%])** stay wrong under both arms; Wikipedia
> rescues 28.7% (39/136), the open web 30.1% (41/136), both 32, web only 9,
> Wikipedia only 7; difference +1.5pp [−4.3, +7.2], p = 0.80 (`rq5`,
> `intervals.rq5`). **Re-run 27 Sep (ISSUES #76):** the tool loop had stopped
> one turn early — all 85 then-missing Wikipedia-arm rows were "empty after 4
> tool calls" — and TruthfulQA answers had been graded by cosine rather than NLI.
> The Wikipedia arm is now complete on 948 of the 950 blind spots (2 Llama runs
> still return empty after 4 tool calls and are recorded as failed calls, not
> data); the web arm covers 136. RQ5 is now restricted to *current* blind spots:
> about 100 of the old 1,054 are no longer blind spots after the dedup and the
> fixed tie rule (ISSUES #66, #67).
> *(Before the re-run: 65.5%, 76/116, [56.5%, 73.5%]; +3.4pp, p = 0.388.)*

> **67.9% (89/131) of silent-consensus questions stay wrong when the models
> can search Wikipedia AND when they can search the open web.**
>
> 95% CI (Wilson) **[59.5%, 75.3%]**. Well-powered, tight, and the only RQ5
> claim that should appear in an abstract.

Two independent retrieval sources, one agentic protocol, four model makers — and
two thirds of the blind spots do not move.

## Per dataset (matched)

| dataset | n | Wikipedia | open web | diff |
|---|---|---|---|---|
| halueval | 38 | 42.1% | 42.1% | **+0.0pp** |
| popqa | 62 | 14.5% | 16.1% | +1.6pp |
| triviaqa | 30 | 30.0% | 40.0% | +10.0pp |

## Both of my predictions were wrong, and that is the honest record

**Prediction 1 (written before the wiki arm):** search helps OBSCURITY most.
**Wrong** — popqa was helped least in both arms (14.5%, 16.1%).

**Prediction 2 (written before the web arm):** the open web should beat Wikipedia
on obscurity, because more sources means more coverage.
**Wrong** — popqa moved +1.6pp, inside the noise. halueval moved +0.0pp exactly.

The triviaqa +10pp is the only movement, n=30, and it is not separable from chance
at this sample size. **Do not quote it as an effect.**

## What this sample can and cannot rule out

| true difference | power to detect it |
|---|---|
| 5pp | 47% |
| **10pp** | **97%** |
| 15pp+ | ~100% |

So: a **large** open-web advantage is ruled out. A **small** one (under ~5pp) is
not, and the CI says so. The claim this licenses is *"no substantial difference"*,
not *"identical"*. Anyone wanting the smaller effect needs the full 1,054 and a
paid tier — stated as future work, with the number, rather than implied away.

## Why this matters for RQ4

RQ4 explained its misconception result with a sentence it never tested:
*"retrieval draws from the same web that taught the misconception."* Every RQ4
document came from Wikipedia, so the open web was never actually consulted.

**It has now been consulted, and it behaves the same as the encyclopedia.** The
sentence is upgraded from an explanation to a measurement — on 131 questions, with
a stated CI, and with the prediction that motivated it recorded as falsified.

## 2026-08-03 · NAME COLLISION is a distinct blind-spot mechanism, and it is the dominant one in PopQA

**Found by sampling blind spots to pick a slide example**, not by an audit. The
first twenty PopQA blind spots drawn at random were almost all the same shape:
the question names an entity that shares its name with a far more famous one,
and all four models confidently answer about the famous one.

```
In what country is Troy?        all four: Turkey        key: United States
Who is the author of Night?     all four: Elie Wiesel   key: William Blake
What is Delhi the capital of?   all four: India         key: Tughlaq dynasty
Who was the director of Heat?   all four: Michael Mann  key: Paul Morrissey
In what country is Boca?        all four: Argentina     key: Italy
```

This is **not** issue #39 (short-form answers rejected by a strict key). The
models genuinely answered about the wrong entity. It is also **not** the same
thing as obscurity: the model is not missing a fact, it resolved a name to the
wrong referent.

### The test is mechanical, and it is Wikipedia's own

Wikipedia keeps the bare name as an article title when the name is unique, and
appends `, Qualifier` or ` (Qualifier)` **only when something else already owns
the bare name**. So

    ambiguous_name  :=  s_wiki_title != subj
                        and s_wiki_title startswith (subj + ',' or subj + ' (')

is Wikipedia telling us the name collides. No judgement, no hand-labelling, no
LLM in the loop. Titles come from `data/interim/popqa_wiki_titles.parquet`
(`scripts/fetch_popqa_titles.py`), which covers **13,068 / 13,068** unique PopQA
questions — full coverage, no imputation.

### How strongly it is enriched

| population | n | ambiguous name |
|---|---|---|
| all PopQA | 14,267 | 53.3% |
| ensemble got it **right** | 6,402 | **33.5%** |
| wrong, but they disagreed | 7,404 | 69.0% |
| **BLIND SPOTS** (all agree, all wrong) | 461 | **76.1%** |

### It is NOT just obscurity wearing a different hat

Blind-spot rate, split by subject popularity (`s_pop` quartiles) **and** name:

| popularity | unique name | ambiguous name | ratio |
|---|---|---|---|
| Q1 rarest | 1.51% | 5.88% | **3.9x** |
| Q2 | 1.07% | 5.33% | **5.0x** |
| Q3 | 1.64% | 4.00% | 2.4x |
| Q4 most popular | 2.26% | 3.30% | 1.5x |
| **all** | **1.65%** | **4.61%** | **2.8x** |

The effect survives at **every** popularity level, so it is not a proxy for
`s_pop`. It is largest among the rarest entities, i.e. obscurity and ambiguity
**compound** rather than substitute. RQ2's popularity control is unaffected --
this is a second axis, not a correction to the first.

### The confidence signature is consistent with collision, not ignorance

Like-for-like, unanimous PopQA questions only:

| | mean confidence | n answers |
|---|---|---|
| agreed & right | 0.944 | 10,268 |
| agreed & WRONG | 0.933 | 1,844 |

(The small right-over-wrong gap is the same effect RQ1 measures as AUC 0.600 in
the agreement region -- consistent, not a new claim.)

Within the blind spots, though, the split goes the other way:

| | mean confidence | n answers |
|---|---|---|
| blind spot, **ambiguous** name | **0.938** | 1,404 |
| blind spot, unique name | 0.916 | 440 |

A model that never learned a fact has no reason to be *more* certain. A model
that has confidently retrieved the **wrong** entity does. The 0.938 is what
"I know this, and I know the wrong one" looks like.

### What this changes

1. **A third failure mechanism, alongside obscurity and misconception.** The
   Diagnose tab's cause labels should carry it explicitly. It is the largest
   single mechanism in PopQA, which is 461 of the 1,054.
2. **It supplies RQ4's missing mechanism.** RESULTS already flags *"retrieval
   fixes obscurity (+68%)"* with the caveat that the mechanism was an untested
   hypothesis. Handing over `s_wiki_title`'s article does not teach a rare fact
   -- it **tells the model which Troy was meant**. Disambiguation is a cheaper and
   more plausible explanation of +68% than knowledge injection, and it predicts
   the misconception arm's +16%, where there is no referent to disambiguate.
   **Still a hypothesis** -- confirming it means re-scoring RQ4 split by
   `ambiguous_name`, which is one run on data already on disk.
3. **It sharpens RQ2 rather than threatening it.** "Rare things are harder"
   survives; "and names that collide are harder still, independently" is added.

### Stated limits

- **PopQA only.** 461 of 1,054 blind spots (43.7%). TriviaQA, HaluEval and
  TruthfulQA ship no entity titles, so the test cannot be run on the other 593.
  Do not state a corpus-wide ambiguity rate.
- The test detects a **collision-prone name**, not a proven mis-resolution. A
  question can carry a disambiguated title and still fail for plain ignorance.
  The 2.8x is an association, cleanly measured; the per-case reading is the
  tool's job.
- Reproduce: the block in this section's commit message, or re-derive from
  `popqa_wiki_titles.parquet` + `records.parquet` in ~15 lines.

## 2026-08-03 · RQ4's +68% is NOT disambiguation — hypothesis tested and FALSIFIED

The name-collision section above proposed that RQ4's obscurity lift might be
disambiguation rather than knowledge injection: handing over the article does not
teach a rare fact, it tells the model *which Troy was meant*. That was written as
an explicit hypothesis with a stated test. **The test was run the same day and the
hypothesis is wrong.**

RQ4's obscurity arm (n=500, all PopQA, all carrying a `s_wiki_title`) split by the
same mechanical ambiguity test:

| group | n | closed-book | with document | lift |
|---|---|---|---|---|
| ambiguous name | 241 | **1.2%** | 68.9% | **+67.6pp** |
| unique name | 259 | **6.6%** | 74.5% | **+68.0pp** |
| all (the published row) | 500 | 4.0% | 71.8% | +67.8pp |

| comparison | test | result |
|---|---|---|
| closed-book, ambiguous vs unique | Fisher exact | 3/241 vs 17/259, **p = 0.0024** |
| with-document, ambiguous vs unique | Fisher exact | 166/241 vs 193/259, p = 0.17 (n.s.) |
| **difference in LIFT** | 10k bootstrap | **−0.003, 95% CI [−0.087, +0.084]** — contains zero |

### What this actually shows

1. **Ambiguity is a real cause of closed-book error.** 1.2% vs 6.6% is a 5.5x gap
   at p = 0.0024. The mechanism is confirmed as a source of wrong answers, which
   is what the blind-spot enrichment (2.8x) already said.
2. **It does not explain the lift.** Retrieval repairs unique-name rare entities
   *just as much* as collision-prone ones. The lift difference is −0.003 with a
   CI straddling zero on both sides.
3. **So RQ4's +68% is genuine knowledge injection**, not a disambiguation
   artifact. The finding is stronger than it was this morning, not weaker --
   the most plausible deflationary explanation was tested and did not hold.

### Why this is worth keeping in the record

The hypothesis was mine (assistant-proposed, 2026-08-03) and it was attractive:
it explained +68% and +16% with one mechanism and would have been easy to assert
without testing. It cost one script on data already on disk to find out it was
false. **Written up because a falsified in-house hypothesis is a stronger defence
of RQ4 than never having raised it** -- an examiner who thinks of it now finds it
already answered, with a CI.

Ambiguity and knowledge-injection are therefore **independent**: ambiguity moves
the closed-book baseline, retrieval moves everyone equally.

## 2026-08-07 · "Just make it say I don't know" — the abstention policy, measured

The most common suggestion this project receives, in some form, from almost
everyone who hears it: *models already produce a confidence number; expose it,
and refuse to answer below a threshold.* RQ1 answers this obliquely (confidence
separates right from wrong at AUC **0.592** in the agreement region) but an AUC is
a **ranking** statistic and does not tell a reader what an actual policy would
cost. So the policy itself is now computed.

*Re-derived 2026-09-27 from `summary.json → abstain` on the deduplicated
corpus; the figures below are current.*

**Scope: the agreement region only** — the 12,181 questions where all four models
produced one meaning. That is deliberately the proposal's *best* case, because it
is the region where vote-counting is 0.00 by construction and confidence is the
only signal available. It still fails there.

### The policy: refuse every answer below confidence T

| refuse below | errors caught | **correct answers destroyed** |
|---|---|---|
| 0.80 | 2.6% | 0.3% |
| 0.90 | 23.3% | 8.9% |
| 0.95 | 56.2% | 44.2% |
| 0.97 | 77.3% | 72.8% |
| 0.99 | **96.2%** | **96.1%** |

Read the last row: at a threshold catching 96% of the errors the policy also
refuses 96% of the answers that were right. It is not a filter at that point, it
is an off switch.

Inverted, which is the form to quote:

| goal | required threshold | cost |
|---|---|---|
| catch **50%** of the errors | 0.941 | destroy **33.7%** of correct answers |
| catch **80%** of the errors | 0.973 | destroy **76.8%** of correct answers |

### Why — one number

In this region mean ensemble confidence is **0.947 when right** and **0.929 when
wrong**. A gap of 0.018. There is no threshold that fits inside it, because the
wrong answers are not at the bottom of the confidence distribution -- they are
distributed through it.

Confidence is `exp(mean log p)`: how unsurprised the model was **by its own
words**. It measures fluency, not truth, and a model that absorbed a false fact is
not surprised by it. This is the same fact RQ1 reports as AUC 0.592, restated as
an operating point rather than a ranking.

### Why it belongs in the write-up

1. It **pre-empts the single most common reviewer suggestion** with a measurement
   instead of an argument, and concedes the reasonable part first: at T = 0.90 the
   policy is real, catching 23% of errors for 8.9% of correct answers. It is not
   useless -- it is nowhere near sufficient, and the table shows exactly where it
   stops being worth it.
2. It is the **practical case for the whole thesis**: the confident-and-wrong
   region cannot be screened away by a confidence gate, which is why it needs an
   interface and a human rather than a threshold.
3. **Cost: one function on data already on disk.** Zero API spend.

### How it is computed

`scripts/export_web.py::abstain_stats()`, exported to `summary.json` as
`abstain`, and read by the deck's funnel slide -- **derived, never typed**. The
same file carried a hardcoded `"keyflags": 0` for weeks (ISSUES #43), so this
table is deliberately built through the exporter rather than written into the
slide as text.

**Caveat to state with it:** this is a *per-question mean* confidence threshold on
a four-model ensemble. A single-model deployment, a per-token policy, or a
purpose-trained abstention head are all different objects and this table does not
speak to them. It rules out the cheap version of the idea -- which is the version
being suggested -- not the research programme.

---

# 2026-08-07 · RQ4 and RQ5 do NOT share a population — and the tool now says so

**Found while wiring retrieval outcomes onto the map.** The two retrieval
experiments read as one story ("does giving the models sources help?") and are
not comparable, because they differ in *both* population and protocol:

| | RQ4 | RQ5 |
|---|---|---|
| **population** | `majority_wrong` errors — PopQA rarest-first (500) + TruthfulQA (70) | the **1,054 blind spots** |
| **protocol** | we paste the Wikipedia article into the prompt | an agent must *search* and decide what to read |
| **overlap with the blind spots** | **33 of 570** are gen-3 blind spots | 1,054 of 1,054 |

Selection is in `rq4_retrieval.strata()`: `errs = records[records["majority_wrong"]]`.

## Why this matters beyond bookkeeping

The first version of the map's search colouring folded all three arms into one
"retrieval fixed it" band. That would have put two populations and two protocols
under a single legend entry — a reader brushing a clump could not have told
whether a green dot meant *an agent found the answer* or *we handed it over*.
The published bits are now **RQ5 only**, and RQ4's per-case result ships to the
inspector where the arm can be named.

**The claim to write, precisely:** RQ4 says *documents repair ignorance and
barely touch a belief* — a statement about **causes of error**. RQ5 says
*two thirds of blind spots survive an agent with a search tool* — a statement
about the **audit population**. Neither generalises to the other's population,
and the deck has never claimed it did (slides 12 and 13 are separate).

## New: "Did search fix it?" on the map

> **Superseded 2026-09-27.** The band counts below are the 2026-08-07 ones over 1,054 blind
> spots on 42,551 questions; they were not re-derived here. The tool reads its
> current counts from `data.json`.

| band | n | meaning |
|---|---|---|
| search fixed it | **254** | at least one model recovered once it could search |
| searched — still all four wrong | **740** | the resistant core |
| blind spot, search incomplete | 60 | fewer than four models completed |
| not a blind spot | 41,497 | search was never pointed at it |

254 + 740 + 60 = 1,054. The open question this exists to answer, and which no
table can: **do the 740 sit in different clumps from the 254?** Nobody has
looked yet — it is a walkthrough candidate (`TODO` §2).

---

# 2026-08-08 · RESULTS.md audited against source — 43 of 43 reproduce

**The same blind spot as ISSUES #47, checked before it could bite.** Every
automated check this project owns compares an artifact against `summary.json`.
This file has no exporter behind it, and it is what the write-up gets assembled
from — so a stale number here would propagate into the thesis with nothing able
to notice.

Re-derived from the parquets, independently of the exporter:

| group | checks | result |
|---|---|---|
| the **claims table**, all 11 claims and their sub-figures | 29 | **29 reproduce** |
| body claims (#44's 114-gap and 263/1.5%, #39's 60 flags, the 8,000 subset, all four RQ5 arm counts) | 14 | **14 reproduce** |
| the grader-bias split | 1 | reproduces **at its stated scope** |

**Zero mismatches.**

## The one that needed its scope read

`31 generous vs 39 harsh` reproduces on the **target stratum**, which is what
this file says ("of 70 target disagreements"). Corpus-wide it is 31 vs **40** —
the control stratum contributes exactly one disagreement. The conclusion is
identical either way, and this file was right.

The **deck** was quoting the pair without the scope, and hardcoded. Both fixed:
`summary.json` now carries `grader_check` (stratum, judged, generous, harsh) and
the slide renders it with the stratum named. Same lesson as #48 — a correctly
scoped number, published without its scope, is one reader away from looking like
a contradiction between two of your own documents.

## Worth knowing for the write-up

Computing this hit the **object-dtype `~` hazard** again: `handlabels.human` is
an object column with `None` for the 89 unjudged cases, and `~` on object dtype
returns `-1`/`-2` rather than raising. `grader_check()` casts with `.astype(bool)`
after `dropna` and asserts the dtype. That is now the fourth appearance of this
hazard in the project (ISSUES #36 and two audit scripts), which is enough to
state it as a rule in the methodology chapter rather than as an anecdote:
**never apply `~` to a pandas column without first proving it is `bool` dtype.**

---

# 2026-08-10 · Name collision, sharpened: hold the question fixed and the effect is 7x

**Produced by drafting Walkthrough 1, and by getting it wrong first.** The draft
counted blind spots per question template and read the largest counts as hot
spots. Two of the five were **below** the corpus average — large because those
templates are common, not because they fail. A count is not a rate.

Correcting it produced a stronger result than the error did.

## Blind-spot rate is driven by AGREEMENT, not by error rate

*Re-derived 2026-09-27 on the deduplicated corpus (`walk.patterns`; base 2.79%).
The `In what country is X?` row is not in the exported set and is dropped.*

| question pattern | n | ensemble wrong | all four **agreed** | blind spots | vs 2.79% base |
|---|---|---|---|---|---|
| `screenwriter/producer/composer of X` | 4,197 | **69.1%** | 8.1% | 1.81% | **0.6x** |
| `Who was the director of X?` | 2,002 | 62.4% | **16.9%** | 5.24% | 1.9x |
| `What genre is X?` | 1,596 | 66.5% | 13.0% | 4.39% | 1.6x |
| `Who is the author of X?` | 1,495 | 55.4% | 21.9% | 3.95% | 1.4x |
| `In what city was X born?` | 585 | 63.9% | 14.2% | 4.10% | 1.5x |
| `What is the capital of X?` | 656 | 10.8% | 73.2% | 1.52% | **0.5x** |

The crew-role pattern is **the most-wrong pattern in the corpus** and one of the
least blind. The models fail *differently* each time — nobody famous is attached
to a film's producer — so disagreement catches them. This is slide 7's funnel
restated one template at a time: what makes a blind spot is not being wrong, it
is being wrong **together**.

## The cleanest cut in the project: one question, one variable

Within `Who was the director of X?` alone — same wording, same task, same four
models — split by whether the title is shared, using Wikipedia's own convention:

```
re-derived 2026-09-27 (walk.director):
title is unique      n =   508      blind-spot rate  0.98%   <- BELOW the 2.79% corpus base
title is TAKEN       n = 1,472      blind-spot rate  6.79%   <- 6.9x higher
```

**Nothing varies but the collidability of the name.** Not the question form, not
the task, not the models, not the dataset. It moves the blind-spot rate
about seven-fold (6.9×), and the unique-name half is *safer than the corpus
average*.

This is the sharpest statement of the collision mechanism the project has. It
supersedes nothing — the 2026-08-03 enrichment table (76.1% vs 33.5%, 2.8x
across popularity quartiles) still stands and is the population-level version.
This is the within-template version, and it controls for question form, which
the earlier table did not.

## Also measured, and minor

*(2026-08-10 figures, not re-derived.)* Blind spots sit **18% tighter** on the map than chance: mean nearest-neighbour
distance **0.105** against **0.128** for a random sample of 1,054 from the same
layout (seed 42). Real, modest; it justifies looking, and supports nothing on
its own. Quote it only as "not uniform", never as "clustered".

## What to quote

> Within a single question template, questions whose subject shares its name with
> something better known are **about 7x (6.9x)** more likely to become blind
> spots — 6.79% against 0.98% on 1,980 `director of X` questions (re-derived
> 2026-09-27, `walk.director`).

**Caveat that must travel with it:** PopQA only, because it is the only dataset
with linkable Wikipedia titles. And a share of these are arguably not model
errors at all — the models resolved a genuinely ambiguous name to its most famous
owner (`Who directed The Town?` → Ben Affleck, key says Mike Bartlett), which is
the benchmark curator's problem, not the model's.

---

# 2026-08-10 · STATED LIMITATION — RQ5 tested whether models can FIND the correction, not whether they can USE it

**Written into the record at Shivani's instruction, rather than waiting to be
asked at the defence.**

## The claim RQ5 supports

> 67.9% of silent-consensus questions stay wrong when the models can search
> Wikipedia **and** when they can search the open web.

## The claim it does NOT support

> *"These questions cannot be fixed by retrieval."*

Two different failures produce the same observation, and the RQ5 data cannot
separate them:

1. the model **never found** the page that contains the answer
2. the model **found it and answered wrong anyway**

`rq5_agentic.parquet` records `tool_calls` and `used_tools` per answer — how much
the model searched — but **not what came back**. The retrieval itself is
unaudited, and that is the gap.

## What the data does rule out

Not laziness, and not a broken tool:

```
resistant questions   mean 7.6 tool calls across the four models
rescued questions     mean 8.6
questions where nobody called the tool at all:   0 of 977
tool health during the run:  956 searches, 0 failed, 0 empty
```

They searched, and they searched nearly as hard on the ones they failed. So
"the agent was weak" is not available as an explanation. What remains open is
narrower and more interesting: **did it find the right page?**

## Why RQ4 does not close it

RQ4 pastes the article in, which removes the finding step entirely — but RQ4 runs
on a **different population**: 570 `majority_wrong` errors chosen by cause, of
which only **33** are blind spots. So the strongest available statement about
blind spots and documents rests on 33 questions.

## The experiment that would close it, costed

Run RQ4's protocol — paste the correct article directly into the prompt — on all
1,054 blind spots.

| | |
|---|---|
| scale | 1,054 questions × 4 models ≈ **4,200 generations** |
| Wikipedia side | free; ~1,054 fetches at the 1 req/sec throttle ≈ 18 minutes |
| cost | model API calls only, comparable to one small arm |
| what it buys | *"even handed the right document, N of them stay wrong"* — a far harder result to argue with than *"search did not rescue them"* |
| what it risks | it may show documents **do** fix most of them, which weakens RQ5's story. That is a real answer either way |
| what it costs elsewhere | reopens "all model work complete", true since 2026-07-29, and competes with the expert evaluation for the same weeks |

**Decision: not run.** The limitation is stated instead, here and in the
write-up. An examiner who spots the gap should find the project already there,
with the cost of closing it estimated and the reason for not spending it given.

## The sentence for the limitations chapter

> RQ5 shows that giving a model a search tool does not rescue two thirds of the
> blind-spot population. It does **not** show those questions are unfixable by
> retrieval: the experiment logs how much each model searched, not what it
> retrieved, so a failure to *locate* the correction and a failure to *use* it are
> indistinguishable in this data. Closing that would take ~4,200 generations with
> the article supplied rather than searched for; it was scoped, costed, and left
> undone in favour of the evaluation study.

**Related interface defect:** the tool asserted the stronger claim on every case,
including 619 that were never searched. Fixed as ISSUES #52 the same day.

---

# 2026-08-10 · The answer-key flag is structurally blind to the "one verbose model got credit" shape

**Found drafting Walkthrough 2**, auditing the 152 newly-hidden cases where the
2024 models had a correct answer and the 2025 models do not. Those look like
genuine regressions. Some are not.

```
Q     What is the name of the regional transportation authority ... Cira Centre?
gold  Southeastern Pennsylvania Transportation Authority

2024  SEPTA · SEPTA · SEPTA (Southeastern Pennsylvania Transportation Authority) OK · SEPTA
2025  SEPTA · SEPTA · SEPTA · SEPTA.
```

Every model in both years gave the same answer. One 2024 model expanded the
acronym and was marked correct. **That is a grading coin-flip recorded as a
regression.**

Same shape: `mums or chrysanths` vs four answers of "Chrysanthemums";
`Indian Territory` vs four answers of "Oklahoma".

## Why `key_too_strict()` cannot catch it

The flag requires that **EVERY** model answer sit inside the gold and be rejected
only by the short-form ratio guard. Here the whole mechanism is that *not* every
model did — one was verbose and passed. The predicate is `all(...)`, so a single
passing answer disqualifies the case by construction.

It fires on **4 of the 152**. That is not an estimate of the contamination; it is
the flag answering a different question.

## What to say instead

> **At most 152 of the 690 newly-hidden cases are genuine regressions**, and
> hand-checking a sample suggests meaningfully fewer. No test in this project
> reliably measures the contamination.

State it as a bound. A tempting middle option — string-similarity between the
2024 correct answer and the 2025 wrong ones — was tried twice while drafting and
**failed both times**: verbose 2024 answers ("King Michael (1921-2017) died
before Gheorghe Buzdugan (1938-2015)") contain the 2025 wrong answer as a
substring, so containment tests mark genuine regressions as artifacts. Two
heuristics, two wrong counts (46, then 37), neither published. Recorded because
the failure is the useful part: **the artifact and the regression are the same
string pattern, and only reading the case separates them.**

## Effect on the claims table

None. Claim 7 quotes **690 newly hidden vs 364 hidden in both** with the caveat
*"78% of the 690 were already wrong in 2024"* — that figure is `all_wrong` in the
2024 arm and is unaffected. The 152 is the complement and has never been quoted
as a count of regressions. This entry exists so that it never is.

**Related:** ISSUES #39 documents the flag's false positives. This is the other
direction — its false negatives — and the two together define what the flag can
and cannot be used for.

---

# 2026-08-26 · FINDING 12 — grading strictness is NOT constant across model generations, and the RQ3 comparison had assumed it was

`scripts/adjudicate_blind.py --arm 2024` · `scripts/artifact_by_arm.py` ·
exported as `summary.json` → `arms`

## What was assumed, and by whom

The 2025 arm's blind spots were adjudicated on 2026-08-25 and 21.74% turned out
to be grading artifacts rather than model failures — the correction that cut the
headline from 1,054 to about 825 (ISSUES #55). The 2024 arm was never
adjudicated, and **every RQ3 result compares the two arms.**

Chapter 7 handled that with an argument:

> The RQ3 *comparisons* are more robust than the levels, because both arms run
> through the identical grader and a uniform strictness largely cancels.

Reasonable, cheap to write, and **false in its premise.** The strictness is not
uniform. It has now been measured on both arms, by two judges.

## The measurement

> **Superseded 2026-09-27.** Current (`arms`, deduplicated, over all cases in each arm; the
> 2025 arm's 45 failed calls were re-run 27 Sep, so both arms are fully decided
> under Qwen, ISSUES #71):
>
> | judge | 2024 | 2025 | gap |
> |---|---|---|---|
> | **Qwen3-235B** | 15.19% [12.9%, 17.8%] · 125/823 | 21.05% [18.6%, 23.8%] · 200/950 | +5.9 pts |
> | **Olmo-3.1-32B** | 17.62% [15.2%, 20.4%] · 145/823 | 24.63% [22.0%, 27.5%] · 234/950 | +7.0 pts |
>
> Adjudicated RQ3: persisted / healed / emerged **239 / 459 / 511, 2.14×** (Qwen)
> and **231 / 447 / 485, 2.10×** (Olmo), against the graded 320 / 503 / 630,
> 1.97×. Genuine blind spots 698 → 750 (Qwen) and 678 → 716 (Olmo); **exact
> McNemar p = 0.101 and 0.226 — not significant under either judge** (ISSUES #74:
> the 0.138 below was an unpaired test on paired data). The tables below are the
> 2026-08-26 figures.

Rates below are over **all** cases in the arm, not just the ones the judge
committed on. The 2025 arm has 56 UNCLEAR verdicts and the 2024 arm none, so a
rate over committed verdicts is partly a rate of *declining* and the two are not
comparable. Over all cases they are, and treating UNCLEAR as *not shown to be an
artifact* is the conservative direction — it cannot manufacture a correction.
This is why 20.59% appears here beside the 21.74% quoted elsewhere: same
numerator, different and explicitly stated denominator.

| judge | in an arm? | 2024 | 2025 | gap | p |
|---|---|---|---|---|---|
| **Qwen3-235B** | yes — the 2025 ensemble | **15.71%** [13.50%, 18.20%] · 145/923 | **20.59%** [18.26%, 23.13%] · 217/1054 | **+4.9 pts** | 0.0051 |
| **Olmo-3.1-32B** | no | **18.09%** [15.74%, 20.71%] · 167/923 | **25.43%** [22.89%, 28.14%] · 268/1054 | **+7.3 pts** | 0.0001 |

## Three things it is not

**Not the judge marking its own homework.** The representative answer for a case
is the first model in sorted order, so every 2025 case was judged on
Qwen3-235B's answer *by Qwen3-235B*, while every 2024 case was judged on
gemma2:9b's (ISSUES #58). Self-favouring inflates exactly this gap, so both arms
were re-judged by Olmo-3.1-32B, which is in neither ensemble and trained on
Dolma. **The gap widened.** Olmo is more lenient on both arms — the level moves,
the difference does not.

**Not the dataset mix.** Applying the 2024 per-dataset rates to the 2025 mix
predicts 16.16%; the actual 2025 figure is 20.59%. Composition explains under a
tenth of it. The rate is higher in 2025 in **4 of 4 datasets under both judges**.

**Not verbosity, which was the obvious story and is wrong.** Newer models wrap
answers in more words, and extra words defeat a short-form matcher — so artifact
cases should be the long ones. They are not. Mean answer length is 1.61 words in
2024 and 1.87 in 2025, and *within* each arm the artifact cases are no longer
than the genuine ones (2025: 1.83 against 1.88 — marginally **shorter**).

> **The mechanism is not established, and this entry does not name one.** What
> is established is that the rate differs, and that it is not the judge, not the
> mix and not answer length. Naming a cause this project did not test is the
> mistake it has spent 59 defects learning to avoid.

## What it does to RQ3 — and it cuts both ways

Both arms now have a per-case verdict, so the three categories can be rebuilt
from the cases that survive adjudication in each arm rather than from the graded
counts. UNCLEAR stays *in* the blind region.

| | persisted | healed | emerged | emerged ÷ persisted |
|---|---|---|---|---|
| **published (graded)** | 364 | 559 | 690 | **1.90×** |
| adjudicated, Qwen3-235B | **268** | 510 | 569 | **2.12×** |
| adjudicated, Olmo-3.1-32B | 259 | 497 | 527 | **2.03×** |

**The headline ratio survives and slightly strengthens.** An upgrade still
creates about twice as many newly-hidden cases as it inherits — 2.12× against a
published 1.90×, and 2.03× under the outside judge. That was the claim, and it
is the number to keep quoting.

**The absolute counts shrink, and `persisted` shrinks most** — 364 → 268. A case
blind in *both* arms has to survive adjudication twice, so it is the category
most exposed to the correction. It is also the one the thesis leaned on least.

## The one claim that loses its significance

Genuine blind spots: **778 in 2024 → 837 in 2025**, +7.6%. On a corpus of 42,551
that is **p = 0.138** — no longer significant. The graded counts said +14.2%.
*(Superseded 2026-09-27: 0.138 came from a two-sample test; the arms answer the
same questions, and the paired exact McNemar test read 0.077 on these data. On
the deduplicated corpus it is 698 → 750, p = 0.101 (Qwen, after the 27 Sep
re-run of the 45 failed calls; 698 → 759, p = 0.055 before it) and 678 → 716,
p = 0.226 (Olmo) — still not significant. ISSUES #74.)*

> **Do NOT quote** "the blind region grew by 14%" as a measured growth. The
> direction is consistent under both judges; the magnitude is about half what
> the graded counts implied, and after correction the growth in *total* blind
> spots is not distinguishable from chance. **The ratio is the robust finding.
> The growth in the total is not.**

## Why this is a finding and not only a correction

Any longitudinal benchmark that grades automatically and compares a newer model
against an older one carries a strictness difference it has not measured, in the
direction that **penalises the newer model**. Nothing about that is specific to
this corpus, these four datasets or this grader. It was invisible here until both
arms were adjudicated, and one arm is the normal amount of adjudication a paper
does.

**Related:** ISSUES #55 (the 2025 correction this checks), #58 (the self-judging
confound), #59 (why the outside judge is Olmo and not DeepSeek). Supersedes the
"strictness cancels" argument in ch7 §7.4, which is retired rather than softened.

---

# 2026-08-26 · NULL RESULT — the agents do not make correlated DECISIONS, and the cheap version of the agent question is closed

`scripts/agent_concordance.py`. No new generations, no cost: RQ5's two agentic
arms already logged `used_tools` and `tool_calls` per model per question.

## The question

The backlogged agent angle (DECISIONS 2026-07-27, item 3) is *correlated failure
across independent agents* — silent consensus of **reasoning** rather than of
answers. It was costed as a second thesis. Before accepting that cost, the cheap
version was worth asking: the four models produce the same wrong answer, **do
they also make the same decisions about what to do?**

## The answer is no, three times over

| check | result |
|---|---|
| Is there variance to correlate? | **No.** Mistral and Gemma search on **100.0%** of questions, Llama on 98.5%. Only Qwen ever declines (80.1%) |
| Is unanimity above chance? | **Barely.** All four search on 80.1%; independence predicts **78.9%**. Ratio **1.02×** — against the **9.0×** this thesis then reported at the answer level (now 3.3× within dataset, 6.1× pooled — ISSUES #68) |
| Do the pairs agree? | **φ is undefined for 5 of the 6 pairs**, because a constant vector correlates with nothing |

The open-web arm gives the same picture on a smaller n: 83.1% observed against
82.0% expected, **1.01×**.

## Two near-misses, both caught before they were written down

**The first draft printed "mean pairwise correlation of the search decision:
+0.251".** That is the Llama–Qwen pair and *nothing else* — the other five were
NaN and were being silently dropped. One pair reported as a mean over six is a
fabricated finding. `mean_pairwise()` now returns the contributing pair count
and it is printed next to every mean.

**The second looked like a result that contradicted the thesis:** all four wrong
on **73.2%** of questions where they agreed to search, against **84.0%** where
they disagreed — i.e. behavioural *disagreement* predicting *more* error, the
opposite of the project's story. It is an artifact. All **194** "disagreement"
questions are *exactly* the 194 where Qwen skipped the tool. The comparison is
"one model did not use the tool" against "everyone did", and a model that skips
the tool doing worse is not a fact about concordance.

## The one real correlation, and why it is not evidence

Number of tool calls correlates at **+0.422** across all 6 pairs. That is a real
number and it has an innocent explanation this data cannot rule out: **harder
questions take more lookups for everyone.** Effort tracking difficulty is not
evidence of shared failure, and no design here separates the two.

## Why this is worth keeping

It converts a *guess* into a *measurement*. The 2026-07-27 decision to backlog
the agent angle was made on an estimate of cost; it now also rests on evidence
that **the angle cannot be bolted onto this thesis with data already on disk.**

**What would actually test it:** multi-step trajectories, where there is a real
decision every turn — which query to issue, which result to trust, when to stop.
One tool and one hop is not a decision space, and 80% of a binary that three
models never vary is not concordance.

**No new arm was added.** RQ5 still has exactly two agentic arms, Wikipedia and
open web. This is a re-analysis of their logs, not a third arm.
