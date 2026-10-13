# Decisions log

## Index by area

Chronological below; this is the way in. A decision is recorded here only if a
reasonable person would have chosen differently, or if the option rejected cost
something.

### Scale & sampling
- **Pilot-first, then re-measure everything** — the pilot's job was to prove the pipeline ran, not to produce numbers. 5 of 5 effects changed at scale.
- **Proportional stratification with largest-remainder rounding** for the 8,000-question baseline subset, so composition cannot bias the comparison.
- **Census + control, not a random sample**, for RQ3 and for hand-labelling. A rate on a defined stratum cannot be compared to a corpus-wide rate — the trap that produced an invalid 1.13%-vs-2.48% comparison.
- **Full corpus for RQ3 even though PERSISTED did not move** — the *denominator* (923 before the 2026-09-27 dedup; 823 after) was what only the whole corpus could supply.

### Models & providers
- **Four makers, not four sizes** — shared training data guarantees shared errors.
- **Behavioural identity gating before any paid run** (`check_provider.py`), after #31.
- **Content-addressed identity locally** — Ollama digests are derived from the weights, so substitution is impossible to hide. Verification, not inference.
- **4-bit accepted after a controlled 8-bit comparison** — thresholds fixed *before* seeing data.
- **Reduced context for Gemma-2 REJECTED** — it changes the answers (94.7% identical vs 100%). A ~7 h speedup declined.

### Grading
- **NLI entailment for TruthfulQA** — cosine is negation-blind.
- **Bidirectional entailment required**; no absolute threshold (terse correct answers score 0.029).
- **"I have no comment" items are ungradeable, not wrong** — 40 questions dropped, and both n's stated because 42,551 × 4 ≠ 170,364.
- **`majority_wrong` is the target, not `any_wrong`** — the latter is implied by the score and gave a flattering 0.911.
- **Hand-labelling blinded, two strata, unclear as a first-class option.**

### Tooling & deployment
- **No Postgres, no FastAPI, no React** — every stage reads one file and writes one file. Static pages, data baked in.
- **Numbers are never typed into a page** — `export_web.py` or they are not shown.
- **Two Vercel projects, not one root** (reversed on request; the cross-link is handled by `TOOL_URL`).
- **Output Directory instead of Root Directory** — the CLI cannot set the latter, and leaving it would have 404'd both live URLs on the next push.
- **Panels specified as jobs-to-be-done**, so the task abstraction falls out of the same design work.

### Records & process
- **Append, then curate.** These files are long because every wrong turn is kept with its cause.
- **Audit the day's own fixes** — three of four defects in one audit were fix-induced.
- **Keep the evidence** — `.predefect36.bak` and the poisoned retrieval cache are retained deliberately; they are the proof two critical defects were real.
- **Repo private until the defence**, `noindex` on both deployed pages. A private repo does not imply a private deployment.

Companion records: **RESULTS.md** (what is true) · **ISSUES.md** (what broke) ·
**EVOLUTION.md** (why the project looks different from the proposal).

---


Append-only. Every decision with the evidence that drove it, so nothing gets
re-litigated and nothing gets forgotten between sessions. Newest section last.

Companion files: `RESULTS.md` (numbers produced), `ISSUES.md` (open problems),
The thesis reframe is recorded in this file (see the 2026-07-27 entries).

---

## 2026-09-27 · The adversarial review: remove, re-derive, re-run — and the deadline moves to mid-October

**Decided by Shivani**, the same day the review reported.

**What happened.** Four agents were each given the repository and asked to find
the reason a headline number is wrong; every finding was re-verified from the
parquet layer before it was accepted. Thirteen defects survived (ISSUES #66–#78)
plus eleven smaller findings. Three of them move the headline: the corpus held
**8,489 duplicate questions** (#66), `majority_wrong` broke ties by taking
Llama's answer (#67), and the independence ratio pooled datasets whose difficulty
differs about six-fold (#68). After the fixes, `summary.json` reads AUC **0.840**
(was 0.862), **950** blind spots (was 1,054), and **3.3×** within-dataset
concordance (was 9.0× pooled).

### 1. Remove the duplicates, rather than keep them and disclose

**The choice.** 8,489 second copies are dropped (`datasets.duplicate_qids()`,
earlier qid kept) and every number is re-derived on 34,062 questions.

**Why.** A duplicate is not a data point; it is a question counted twice. A
disclosed duplicate still sits in every denominator, still double-weights the
dataset the detector handles best, and still lets a question's twin cross a
cross-validation fold (#73). Disclosure would have kept the better numbers and
added a paragraph explaining why they are not quite right.

**Rejected: keep and disclose.** Cheaper — no re-export, no chapter pass — and
the AUC would have stayed at 0.862. Rejected because it keeps a number the data
no longer supports. **Rejected: re-sample to restore 42,591.** It would have
changed the question set that both RQ3 arms and every hand label were measured
on, which cannot be re-run for the 2024 arm (local weights no longer configured).

### 2. A principled tie rule, and report what the others would have given

**The choice.** Largest cluster; size ties → larger summed confidence → the
single most confident answer; within the chosen cluster, majority verdict, tie →
the most confident member (`disagree.ensemble_answer_correct`).

**Why.** Every other candidate is either arbitrary (a fixed model wins) or
changes what the target means ("no majority = failure" makes the label partly a
function of the disagreement score — the circularity ISSUES #0 removed). The
chosen rule uses only what the ensemble itself reports.

**Rejected alternatives, with what they gave** (measured 27 Sep): old
Llama-first 0.849; each model breaking four-way splits 0.849–0.885; "no majority
= failure" 0.901. **The chosen rule gives the lowest AUC of all of them (0.840).**
That is recorded as the reason to trust it, not a cost: a rule chosen after
seeing that it flatters the result would be worth nothing.

### 3. Lead with the stratified concordance ratio

**The choice.** The independence headline is now *"within the same dataset, all
four are wrong together 3.3× as often as independence predicts"*
(`intervals.concordance`), with within-dataset φ 0.44–0.60. The pooled 6.1× is
kept, explained and demoted. "Order of magnitude" is deleted everywhere.

**Why.** The pooled ratio multiplies error rates averaged over strata of very
different difficulty; part of what it measures is that the datasets differ. The
within-dataset ratio answers the question the claim asks.

**Rejected: keep the pooled figure as the headline with a caveat.** It is the
larger, more quotable number and it is not wrong arithmetic. Rejected because the
caveat would have to say that two thirds of it is not the effect being claimed.
**Rejected: drop the pooled figure.** A reader who computes it will get 6.1× and
must be able to find it explained.

### 4. Re-run the failed and aliasless paid calls, rather than report around them

**The choice.** Pay to re-run: the blind-spot adjudications that were failed
calls (#71), the 430-case adjudicator *with* alias lists (#71), RQ4's re-selected
strata and 15 empty answers (#70), and RQ5's 85 missing Wikipedia rows with NLI
grading for TruthfulQA (#76). Until then each figure is quoted from the current
`summary.json` and marked **pending**; claim 17's κ is withdrawn rather than
quoted.

*(27 Sep 2026 re-run: done the same day, 0 failed calls, and #70, #71, #76 are
closed. Artifact rate 21.05% of all 950 (0 undecided); adjudicator κ 0.782 with
aliases (was 0.688), so claim 17 is restored; RQ4 +65.2% / +14.0% with the
misconception lift no longer significant (p = 0.077), dissociation +51.2%; RQ5
64.7% of 136 matched stay wrong. Genuine change 698 → 750, p = 0.101 (not significant). See the
ISSUES entries.)*

**Rejected: report the failed calls as UNCLEAR.** That is what the file said, and
it was false — the judge did not decline, the call failed (standing rule 1).
**Rejected: drop claim 17 entirely.** The question it answers (does an LLM agree
with the human better than the grader does?) is still worth answering; it was
answered with the two raters shown different answer keys, which is fixable.

### 5. The deadline moves from 30 September to mid-October 2026

**Supersedes the date in the 2026-08-30 entry below; its scope decision stands.**

**Why.** The advisor has not yet reached out about the submission, so the
30 September date — which this project treated as hard because submission
unblocks the **OPT application** — is not the binding constraint it was planned
as. The correction pass, the paid re-runs, the re-export, the chapter text and
the Word build cannot all be done well by 30 September, and the OPT timing does
not justify shipping numbers known to be pending.

**Rejected: submit on 30 September with the pending items disclosed.** Possible —
every pending figure has a current value — but it would submit a thesis whose
own ISSUES file lists three open defects. **Rejected: an open-ended extension.**
The OPT application still depends on submission; mid-October is a date, not a
direction.

---

## 2026-08-30 · The project is the thesis, and it ends on 30 September

> **The date in this entry is superseded by 2026-09-27 §5 (now mid-October 2026).
> The scope decision — the thesis only, the preprint out — stands.**

**Decided by Shivani.** Two changes, and they are one decision.

| | before | after |
|---|---|---|
| deadline | December 2026, with a ~1 November gate | **30 September 2026, hard, no gate** |
| scope | thesis **and** an arXiv preprint, served by one body of work | **the thesis only.** The preprint is out of the project |

**Why the date.** Submitting the thesis is what unblocks the **OPT
application**. Every previous version of this plan weighed a slipped thesis
against a missed paper deadline and concluded the thesis wins. That framing
understated it: the cost of slipping is not a publication, it is work
authorisation. The date is therefore a constraint, not a target.

**Why the preprint leaves rather than compresses.** It could have been squeezed
into September — the material exists, the abstract is written, and item 4.4
already decided how it opens. That is exactly why it is safe to defer: nothing
about it decays. Compressing it, by contrast, would have taken revision time
from the eight drafted chapters in the only ten weeks that cannot be recovered.
A preprint written in October from a submitted thesis is a better preprint than
one written in September from a thesis that is still moving.

**What this does NOT change.** No chapter, no result, no framing. The thesis
chapters never referenced the preprint or the December date — checked, and
only `PLAN.md` and `00-OUTLINE.md` carried them. Item 4.4's decision that the
preprint leads with the decorrelation recommendation stands, unschedued, for
whenever it is written.

**The option rejected**, and it cost something: keeping B in scope so that PhD
applications in early December would have a preprint to link. Deferring it means
applications either link a thesis or link nothing. That is a real loss, accepted
knowingly, because it is the only item on the plan whose deadline is softer than
September's.

---

## 2026-07-27 · The thesis is a TESTING project, not a claims project

**Decision.** Reframe as a *replication-and-falsification study with a visual
analytics instrument*: the cross-model-disagreement literature asserts things
nobody has stress-tested end to end. Build the instrument, run the tests, report
what breaks.

**Evidence.** Three claims failed on the 300-question local pilot:

| Claim | Source | Pilot result |
|---|---|---|
| Cross-model disagreement beats single-model uncertainty | Hamidieh NeurIPS 2025; Gorbett 2026 | **LOST** — ensemble 0.788 vs single-model SE 0.813, on every dataset |
| Correlated errors are structural to the paradigm | Correlated Errors in LLMs 2506.07962 | **REVERSED** — 8 of 9 silent-consensus cases healed across a generation jump |
| Confidence-weighting sharpens the signal | our own proposal | **LOST** — 0.776 weighted vs 0.788 unweighted |

Survived: confidence predicts error at **AUC 0.688 inside the unanimous region**
(where vote-counting is 0.5 by construction); two features beat one
(0.763 → 0.805 → **0.820**); map density survives the popularity control
(0.682 → **0.732**).

**Why.** Under the detector framing these are three losses. Under the testing
framing they are three findings, and negative results in this space are
essentially unpublished — which is exactly why the assumptions went unchecked.

---

## 2026-07-27 · Scale test is the spine, not a side experiment

**Decision.** Run the same three claims at two scales: the 7–9B local pilot
(done) and the hosted 24B–400B ensemble (to do). Report both. The pilot is the
small-scale arm of a two-scale study, **not** a superseded draft.

**Why.** Every outcome is publishable — claim fails at both scales (wrong in
general), holds only at large (scale-dependent, and nobody has stated the
threshold), or holds at both (the pilot was a small-model artifact, reported
honestly). The design cannot produce an unusable result.

---

## 2026-07-27 · Move off the laptop to hosted inference

**Decision.** Ensemble runs on DeepInfra. Not local, not Together.

**Evidence.**
- Measured local throughput **0.28 generations/sec** (900 gens in ~54 min, gen-1
  Track run). The 20k screening pass = 80,000 generations = **~3.3 days** of
  continuous GPU even on the 7–9B models.
- A 70B at Q4 is **~42 GB — exceeds the 32 GB system RAM**; it does not load at
  any speed. 27–32B loads but spills to RAM at ~1 tok/s (weeks).
- Hosted cost for the same work: single-digit dollars.

**Why DeepInfra and not Together.** Of **217** text models on Together, only
**three** are serverless *and* return logprobs, and only one of those is
70B-class — not enough for a four-maker ensemble. DeepInfra has all four makers
with logprobs.

**Why not frontier (Claude/GPT/Gemini).** `confidence = exp(mean log p)` needs
per-token logprobs. **Anthropic's API does not expose them**, so a frontier-only
ensemble would silently delete RQ1 — the strongest surviving result.

**Why one provider, not split across two.** Confidence is computed by the
serving stack, so mixing providers inside the ensemble bakes a *provider* offset
into what the analysis reads as a *model* difference (`min_conf` would track
whichever provider reports lower logprobs). Normally you would calibrate with an
overlap control, but **no logprobs-capable model exists on both** providers, so
the offset would be unmeasurable. Single provider avoids it rather than manages it.

---

## 2026-07-27 · BUG — logprob dialect, would have silently destroyed RQ1

**Finding.** "OpenAI-compatible" is two wire formats:

```
OpenAI / Ollama :  logprobs.content        -> [{"logprob": -0.86}, ...]
Together        :  logprobs.token_logprobs -> [-0.86, ...]
```

`generate.py` read only the first. Against Together every call returned **HTTP
200, a correct answer, and `confidence = NaN`**. The run would have completed
looking entirely successful with the whole confidence signal gone.

**Fix.** `generate.logprobs_of()` parses both dialects and drops nulls. Pinned by
`tests/test_generate.py` with real captured response fragments.

**Rule adopted.** `scripts/check_provider.py` before **every** paid run. A model
existing in a catalogue is not evidence it serves logprobs, and a 200 is not
evidence the response is usable.

---

## 2026-07-27 · Datasets LOCKED

**Decision.** Four datasets, ~43,000 questions. Evidence from
`scripts/probe_datasets.py --n 60` (240 answers each, hosted ensemble).

| Dataset | n | acc | all-wrong | Role |
|---|---|---|---|---|
| TriviaQA `rc.nocontext` | 17,944 | 70.8% | 11.7% | volume + the positives |
| PopQA | 14,267 | 39.2% | 35.0% | obscurity; **only** popularity metadata |
| HaluEval QA | 10,000 | 45.4% | 41.7% | misinformation arm at scale |
| TruthfulQA | 817 | 57.9%* | 23.3% | misconception probe, qualitative only |

\* graded without the NLI tier, so inflated — upper bound.

**Why these four.** They span the difficulty range deliberately. An AUC needs
questions the ensemble gets *right* as well as wrong; TriviaQA supplies the easy
end, PopQA and HaluEval the middle, TruthfulQA the engineered-failure end.
HaluEval has the best single profile (mid accuracy, highest all-wrong rate =
richest silent-consensus source).

**On TruthfulQA's size.** 817 rows, fewer after the non-adversarial filter — too
small to carry a statistical claim, and it no longer has to, because HaluEval
took that job at 12× the size with the same right/hallucinated structure. It is
kept for the one thing nothing else has: its own cause taxonomy
(Misconceptions / Conspiracies / Superstitions / Health / Politics), which is a
free **external** check on whether Diagnose's cause labels track anything real.

**Rejected, with the measurement:**
- **SimpleQA** — 25.4%, still floored. But *why* it improved is a finding: 91%
  wrong on the 7–9B ensemble → 74.6% wrong here. **The floor effect was
  scale-dependent, not a property of the dataset.** Dropped as smallest and
  least additive, not as broken.
- **HotpotQA** — 36.2% overall but splits badly: `comparison` rows 66.7% yes/no
  golds (clustering degenerates), `bridge` rows only 28.3%. Optional later as a
  bridge-only arm testing multi-hop *reasoning* failure vs knowledge failure.
- **LIAR2 / FEVER** — rejected on **schema, not accuracy**. No question and no
  gold answer string; answer space collapses to 2–3 discrete labels. Semantic
  clustering becomes meaningless and "all four agree" happens ~50% of the time
  by chance, which would gut the silent-consensus finding.

**Social/misinformation angle resolved without a project change.** HaluEval +
TruthfulQA *are* the misinformation arm, at 10,817 questions instead of 817 —
the socially-loaded framing with no method breakage and no new pipeline.

**Caution recorded.** An 8-question smoke test called SimpleQA usable and
HotpotQA dead; at n=60 both verdicts reversed. Do not act on small probes.

---

## 2026-07-27 · Agents enter via RQ4, not as a second thesis

**Decision.** The agent question enters as *"do blind spots survive tool use?"*
using the existing `rq4_retrieval.py`. A full multi-agent trajectory study stays
in the backlog.

**Why.** Retrieval *is* a tool, so RQ4 already tests the hypothesis "agents have
better tools, so these mistakes should reduce" — and it completes an argument
already being made. Retrieval fixes the blind spot → **fixable**; it doesn't →
**structural**, the model never knows to look it up. That is precisely the
fixable-vs-structural axis of the thesis.

**Backlog (not dropped):** B1, correlated failure across *independent* agents —
"silent consensus of reasoning". Needs a real novelty scan plus actually running
agents. A second thesis, or future work.

---

## 2026-07-27 · Ensemble LOCKED (gen-3), matched on active parameters

**Decision.** Four makers on DeepInfra, matched on *active* parameters:

| Maker | Model | Active | acc (n=600) | 95% CI |
|---|---|---|---|---|
| Meta | Llama-4-Maverick-17B-128E-FP8 | 17B | 55.3% | 51.3–59.3 |
| Alibaba | Qwen3-235B-A22B-Instruct-2507 | 22B | 54.5% | 50.5–58.4 |
| Mistral | Mistral-Small-3.2-24B-2506 | 24B | 47.3% | 43.4–51.3 |
| Google | gemma-3-27b-it | 27B | 41.7% | 37.8–45.7 |

**Why active parameters, not the number in the name.** Two are MoE:
Llama-4-Maverick is 17B active of ~400B total; Qwen3-235B-**A22B** is 22B active
of 235B. The original pick, Qwen3-Next-80B-**A3B**, was only **3B active** — the
smallest in the ensemble despite "80B" in its name. Swapping it for
Qwen3-235B-A22B tightened the band from 3–27B to 17–27B.

**A size-matched all-DENSE four-maker set does not exist** among logprob-serving
models: Google caps at gemma-3-27b, Mistral has exactly one usable model, Meta
has no dense model near 24B, and every usable Qwen is MoE. Active-parameter
matching is the closest achievable.

**Accuracy spread is real but tolerable.** Best vs worst = 13.6 points, intervals
separated. But Llama/Qwen are statistically indistinguishable, and Gemma/Mistral
overlap — it is a gradient, not one outlier. **Gemma kept** because (a) it is the
largest usable Google model, (b) dropping it costs a distinct training recipe,
which is the whole design axis, and (c) a weaker model dissenting is not
automatically noise — whether its dissent is informative is measured by the main
run's AUC, not decidable in advance. DeepSeek-V4 remains a usable alternative
fourth maker if the spread turns out to hurt.

**Model search method.** `scripts/find_models.py` probes every catalogue model
for four conditions: serverless, returns logprobs, answers directly (no
reasoning leak), non-degenerate logprobs. Of 60 candidates, **12 passed**;
rejections were 20 no-logprobs, 14 HTTP errors, 6 empty answers, 4 reasoning
leaks, 2 all-zero logprobs. Catalogue membership is not availability, and a 200
is not a usable response.

---

## 2026-07-27 · CONFOUND found in the Track design — generation vs scale

**Problem (raised by Shivani).** The planned Track ladder changes two things at
once:

| | Models | Era | Size |
|---|---|---|---|
| Gen-1 | Llama2-7B, Qwen1.5-7B, Mistral-0.1 | 2023 | ~7B |
| Gen-2 | Llama3.1-8B, Qwen2.5-7B, Mistral-7B, Gemma2-9B | 2024 | ~7–9B |
| Gen-3 | the hosted ensemble above | 2025–26 | 17–27B |

If blind spots heal from gen-2 to gen-3, **generation and scale are
inseparable** — exactly the uncontrolled-variable error this thesis exists to
catch others making. Second confound: gen-1/gen-2 ran locally at **4-bit
quantization**; gen-3 runs hosted at full precision.

**Fix — a within-maker Gemma ladder**, all on one provider at one precision:
- **Scale, generation fixed:** gemma-3-4b → 3-12b → 3-27b
- **Generation, scale ~fixed:** gemma-2-9b (local) → gemma-3-12b

Cheap (small models are the cheapest on the platform), one maker so nothing else
varies, and it separates the two axes instead of reporting a change that cannot
be attributed. `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` additionally allows
a same-model hosted-vs-local-Q4 comparison, which *measures* the quantization
confound rather than apologising for it.

**Rejected: splitting generations across providers.** Together has older models
DeepInfra dropped, and Track needs no logprobs, so it is tempting. But different
providers may serve different quantizations of the same weights, so a *provider*
effect would present as a *generation* effect — a third confound in an
experiment already fighting two. Gen-1/gen-2 are already on disk and the middle
rungs are all on DeepInfra, so Together is not needed here.

---

## 2026-07-27 · Track redesigned — gen-1 DROPPED, gen-2 rebuilt hosted

**Decision.** Track has two arms, both fully hosted:

| Arm | Ensemble | Answers |
|---|---|---|
| Gen-2 | Llama-3.1-8B · Qwen2.5-7B · Mistral-7B-v0.3 · gemma-2-9b | the "before" |
| Gen-3 | Llama-4-Maverick · Qwen3-235B-A22B · Mistral-Small-3.2 · gemma-3-27b | the "after" |
| Gemma 2×2 | gemma-2-9b / gemma-2-27b / gemma-3-12b / gemma-3-27b | generation vs scale |

**Gen-1 dropped.** Three simultaneous confounds:
1. **Ensemble size.** Gen-1 had THREE makers (no Gemma — it didn't exist in 2023)
   against four in gen-2/gen-3. Silent consensus is "all models agree and all are
   wrong", and three agreeing is mechanically more likely than four. The
   comparison measures ensemble size as much as generation. **This retroactively
   contaminates the existing "8 of 9 healed" result** — part of that drop is
   simply 3 models → 4 models, not healing.
2. **Precision.** Gen-1 ran locally at 4-bit; gen-3 runs hosted at full precision.
3. **Unfixable.** A hosted gen-1 is impossible: every Qwen 1.5 404s and Gemma did
   not exist. It would be two makers, which is worse.

Kept for the appendix with all three caveats stated. Two clean points beat three
contaminated ones — particularly in a thesis whose argument is that others failed
to control their variables.

**Gen-2 rebuilt hosted** (verified available 2026-07-27): the same four models as
the local ensemble, served at full precision. This removes the quantization
confound *and* enables a same-model local-Q4-vs-hosted-full comparison that
**measures** the quantization effect rather than apologising for it.

**Provider-behaviour finding.** DeepInfra's `Qwen2.5-7B-Instruct` emits `<think>`
blocks; the local `qwen2.5:7b` does not. Same model name, different provider,
different output. Handled by `generate.strip_reasoning()` (which also handles the
*truncated*, never-closed block that appears at max_tokens=64). Independent
evidence that the serving stack matters — and support for keeping every arm on
one provider.

---

## 2026-07-27 · Engineering changes forced by the above

- **`generate.run(tag=...)`** — runs write to separate files. Previously every
  run wrote `answers_pilot.parquet`, so re-running the frozen pilot on a new
  ensemble would have silently destroyed the local 7–9B results the entire
  small-vs-large comparison rests on. Those represent days of laptop GPU time and
  cannot be cheaply regenerated.
- **`generate.run(ensemble=...)`** — selects the config block, so Track arms need
  no config editing between runs.
- **Concurrency.** Questions within a model now run through a thread pool.
  The model-as-outer-loop ordering existed because only one model fits in 8 GB
  VRAM; on a hosted API that constraint is gone and serial calls are pure network
  latency — 172,000 sequential requests is roughly 48 hours of waiting.
  Chunked checkpointing so a crash costs one chunk, not one model.

---

## 2026-07-27 · Full pipeline audit before the paid run — 13 findings, all fixed

Run before committing to ~172,000 generations. Full report in `AUDIT.md`, task
**This section is thesis material**: it is the evidence
that the methodology was verified rather than assumed.

**2 Critical**
- `run_pilot.py` — the entry point documented in `README.md` rebuilt
  `questions_pilot.parquet` from the *current* dataset config and overwrote
  `answers_pilot.parquet` with the *current* ensemble. Running it as documented
  would have destroyed the local 7–9B arm — half the two-scale study, days of
  laptop GPU time, unregenerable. Now requires an explicit `--rebuild-questions`
  and takes `--tag` / `--ensemble`.
- `check_provider.py` validated `ensemble_hosted`, which had drifted from
  `ensemble` (Qwen3-Next vs Qwen3-235B). The gate built to prevent a bad paid run
  was checking models that would never run. Now takes `--ensemble`, defaulting to
  the key `generate.py` uses; the duplicate config key was deleted so it cannot
  drift again.

**7 Major**
- Four analysis modules (`embed`, `rq1_confidence`, `rq2_localize`, `screen`)
  hardcoded `_pilot` paths and would have analysed the **local** results while
  reporting them as current — plausible, confident, wrong numbers, no error.
- `grade.run()` re-graded every row with cosine, so running it after `nli`
  silently reverted TruthfulQA to the negation-blind grader; because `nli` only
  records `correct_cosine` when absent, the loss left no trace. The error runs in
  the *flattering* direction (real errors → apparent successes).
- `screen.py --pool 20000` against the 300-row pilot file screened 300 rows and
  printed a yield as though it had worked. That yield sizes the whole Audit
  population. Now refuses and explains.
- `track.py` referenced the deleted `ensemble_gen1` key (dead on call) and
  omitted the `gradeable` filter that `disagree.run()` applies — so the two Track
  arms were computed over **different question populations**.
- `track.generate_gen1` persisted failed generations and counted them as done on
  resume — transient failures became permanent holes.
- Tier-3 grading issued one encoder call per answer (~83% of rows reach it):
  ~143,000 single-item calls at full scale. Batched — verified **identical on all
  800 in-scope rows**, 50.1s → 5.2s.

**3 Minor + 1 Note** — unused parameter (auto-fixed); `rq4` hardcoded
`ensemble[0]`; `.env` holding a live key inside the OneDrive-synced tree (moved
to `~/.faultlines.env`, loader checks home first); order-dependent greedy
clustering documented.

**Pattern worth reporting.** Every serious bug found today was a **silent
failure** — HTTP 200 with an empty answer, a resume that skipped failures, a
grader that reverted itself, a gate checking the wrong list. None raised an
error; all would have produced confident, plausible, wrong numbers. The
countermeasure that actually worked was cheap runs that fail loudly before
expensive runs that fail silently: `check_provider.py` caught 3 bad model IDs and
the logprobs dialect, a `limit=2` smoke test caught a missing import, and a
12-question probe caught the `<think>` truncation.

**Verification:** 44 tests pass; `check_provider.py` green on all four models.

---

## 2026-07-27 · Concurrency raised 12 → 24 mid-run (4× throughput)

**Not a defect — a default that was correct at 300 questions and badly wrong at
170,000.** Recorded because the diagnostic is reusable.

**Symptom.** The full run settled at **3.3 generations/sec**, against a projected
2.5 hours. At that rate it would have taken ~10 hours.

**Three hypotheses, tested in order:**

1. *"Qwen3-235B is simply a slow model."* Plausible — it is a 235B MoE, and it
   had replaced a much faster Llama. **Refuted:** an 8-worker test hit 10.9
   gen/s while the live 12-worker process managed 3.3. Fewer workers cannot beat
   more workers on the same model.
2. *"Checkpoint writes are the bottleneck."* `generate.run()` rewrites the entire
   accumulated frame every 200 rows, which is genuinely O(n²) over a run.
   **Refuted by measurement:** 0.18 s at 53k rows, ≈ **4 minutes** across the
   whole corpus. A real inefficiency that does not matter at this scale.
3. *"The run is under-parallelised."* **Confirmed.**

**The measurement that settled it** — and the trap in taking it:

| workers | throughput |
|---|---|
| 12 | 6.9 gen/s |
| 24 | **25.9 gen/s** |

An earlier version of this benchmark sent the *same question* 8 times and
reported 10.9 gen/s. Providers cache identical requests, so that number was
meaningless. **Benchmark with distinct items drawn from the real corpus.**

**The reusable diagnostic.** Single-request latency was 2.64 s, so one worker
sustains ~0.38 gen/s and 12 workers *should* yield ~4.5 gen/s — while a 24-worker
burst reached 25.9. When `workers ÷ latency` sits far below what added
concurrency actually delivers, capacity is idle and the limit is client-side, not
provider-side.

**Outcome.** `generation.max_workers` is now a documented config value at 24.
Sustained rate **3.3 → 13.2 gen/s** (burst figures always flatter; 13.2 is the
number to plan against). Estimated completion 10 h → ~2.4 h. Failure rate stayed
at **0** after the change, so the retry/backoff absorbs the extra concurrency.

**Free verification of an earlier fix.** The restart printed the 9 accumulated
failures as retried rather than skipped — the resume path excludes
NaN-confidence rows, so transient holes cannot survive a restart. The design
fixed on suspicion was confirmed in production.

---

## 2026-07-27 · Observation — settings validated at pilot scale do not transfer

Three separate defects on the same day shared one root cause, and none was
visible at 300 questions. Recorded together because the lesson is one lesson.

| setting | correct at 300 questions | wrong at 170,364 | cost if unfixed |
|---|---|---|---|
| `max_workers: 12` | yes — no measurable difference | left ~75% of API capacity idle | ~7 extra hours |
| grade.py: one batched `embed()` call | yes — 800 rows, instant | ~700k texts, ~1 GB in one allocation | OOM / thrash |
| `disagree.py`: `cluster()` per question | yes — 291 calls, 28 s | 42,591 calls at 96 ms each | 68 min |

**Why the pilot could not have caught any of them.** Each is a *resource*
characteristic — latency utilisation, peak memory, per-call overhead — and all
three are linear or worse in corpus size while the pilot was 0.7% of it. Nothing
was wrong with the values; they were simply chosen where the cost was invisible.

**Note the direction of the second one.** The batching that made grading 10x
faster on the pilot is precisely what would have exhausted memory on the full
run. An optimisation is a trade, and the trade can flip sign as scale changes.

**The check that would have caught all three**, and is cheap to run before any
large job:

1. **Throughput vs latency.** Measure single-request latency, compute
   `workers ÷ latency`, and compare to observed throughput. A large gap means
   idle capacity. (Benchmark with DISTINCT inputs — providers cache identical
   requests and return a flattering, meaningless number.)
2. **Peak allocation.** For any "batch everything" step, multiply items x
   per-item size at FULL corpus scale, not pilot scale.
3. **Per-call overhead x N.** Time one call, multiply by the real N. 96 ms
   looks free until it is multiplied by 42,591.

**Consequence for the write-up:** the pilot validated *correctness*, not
*feasibility*. Those need separate checks, and the feasibility one has to be
done with full-scale arithmetic even when the run itself is still small.

---

## 2026-07-27 · Visual analytics gaps to close

Three gaps between "has a UI" and "is a VA contribution":

1. **No task abstraction.** Never stated who the tool is for or what job they do
   with it. Fix: one section — user, tasks T1–T4, design requirements traced to
   them. No code.
2. **The tool displays findings rather than producing them.** Results are
   computed in scripts and drawn on the map afterwards. Fix: 2–3 documented
   discovery walkthroughs where a human found something *through the interface*
   that no AUC states.
3. **No evaluation.** Fix: the light version — 3–4 domain people, 30 min each,
   task = "find a blind spot in this ensemble", record where they stumble and
   what they find. **Not** a new UI; `faultlines-tool/index.html` already exists.

---

## 2026-07-28 · Cost model was wrong by ~20× — and it changes the plan

**Observation.** The full 170,364-generation gen-3 run cost **$1.21**. The
estimate that shaped months of scoping was **$19–32**.

```
170,364 generations  ->  $1.21     ~$0.0000071 per generation
```

**Cause.** `max_tokens: 64`. Provider pricing is dominated by *output* tokens,
and the design forces short answers because the answer keys are short spans.
A constraint chosen for **grading accuracy** turned out to be the cost control,
and neither the estimate nor the budget conversation ever accounted for it.

**What this changes.** Everything previously deferred as "the expensive item" is
about a dollar:

| run | generations | cost |
|---|---|---|
| gen-3 full corpus | 170,364 | $1.21 |
| SE baseline, 8,000 stratified | 128,000 | ~$0.90 |
| gen-2 full corpus | 170,364 | ~$1.20 |
| Gemma 2×2 ladder | ~170,000 | ~$1.20 |

Budget after all four: **~$15 of $19.88 remaining.**

> **Amended 2026-08-03.** The SE row read `32,000 | ~$0.25`. That was the *row*
> count of `baseline.parquet` (8,000 questions × 4 models), not the generation
> count — each row carries 4 samples, so the arm is 128,000 generations and about
> $0.90. The conclusion is unchanged and the leftover budget line is left as it
> was written; the arithmetic error is the point worth keeping.

**Decision.** Stop treating cost as the binding constraint. The real constraints
are wall-clock (~2h per full arm) and provider rate limits. Specifically:
**the 8,000-question stratified subset for the SE baseline was unnecessary
frugality** — the full 42,551 would have cost ~$1.30. It was still the right
call to run 8,000 *first* (it answered the question in a quarter of the time),
but if the AUC comparison is ever challenged on subset size, extending it to the
full corpus costs a dollar and an hour, not a grant.

**For the write-up:** this is a reproducibility point worth stating plainly. The
entire empirical core of this thesis — 372,000+ generations across four model
families at full precision — costs under $5 to reproduce. That is a stronger
claim about the method's accessibility than anything in the results section.

---

## 2026-07-28 · Provider volatility is a reproducibility risk, and it is now measured

**Observation.** Three of the four gen-2 models disappeared from DeepInfra's
`/v1/models` catalogue **within 24 hours** of producing 1,200 clean rows:

```
Qwen/Qwen2.5-7B-Instruct              delisted, still servable
mistralai/Mistral-7B-Instruct-v0.3    delisted, still servable
google/gemma-2-9b-it                  delisted, still servable
meta-llama/Meta-Llama-3.1-8B-...      still listed
```

All three answered correctly with logprobs when called directly, and then
produced 42,591 generations each with **zero failures**. Delisted, not withdrawn.

**Why it matters beyond the bug** (recorded separately as ISSUES #27):

1. **The gen-2 arm had a shelf life nobody knew about.** Had this run been
   deferred another few weeks, the Track comparison might have become
   unreproducible — and *silently*, because a delisted model still works until
   the day it does not. The decision to run gen-2 at full corpus *today* rather
   than after the VA work was luck, not foresight.
2. **It is a limitation of hosted inference as a methodology**, and the honest
   counterweight to the "move off the laptop" decision (2026-07-27). Local
   Ollama weights are frozen on disk and reproducible in five years; a hosted
   model ID is a rented dependency that can vanish without notice or version
   bump. The project traded reproducibility for scale and precision. That trade
   was correct — 4-bit local models could not have produced these results — but
   it must be *stated*, not glossed.
3. **Mitigation, cheap and worth doing:** the raw generations are already
   checkpointed to parquet, so every arm is reproducible from stored outputs
   even after the models die. Analysis reproducibility survives; *generation*
   reproducibility does not. Say exactly that in the limitations section.

**Decision.** Run every planned hosted arm now rather than sequencing it after
the visual-analytics work. At ~$1.20 and ~2h each there is no reason to wait,
and delisting is a real clock.

---

## 2026-07-28 · Throughput settled at ~22 gen/s, and the earlier benchmark was wrong

**Observation.** Sustained rates across today's runs, 24 workers:

```
gen-3 full corpus      25.2 gen/s
SE baseline            ~20   gen/s   (4 sequential samples per question)
gen-2 full corpus      21-23 gen/s   sustained over 132k generations
```

A full 170k-generation arm is **~2 hours**. The pilot-era estimate was 48 hours
(sequential) and the first threaded attempt at 12 workers gave 3.3 gen/s.

**Recorded because the diagnosis was wrong twice.** The 12→24 worker entry
(2026-07-27) notes the two false hypotheses — a slow model, then checkpoint I/O
— but the deeper error was the benchmark itself: it sent **the same question**
eight times, which providers cache, so it measured cache hits rather than
throughput. **A benchmark that does not vary its input is not measuring the
system.** Same failure mode as the pilot generally: a number produced
confidently, at the wrong scale, that does not transfer.

**Rate limits, now quantified.** 88 HTTP 429s in the first 9,800 baseline rows
(~1%), and **zero** once retry-with-backoff was in place across 132,000+
generations. 24 workers is at the edge of comfortable, not past it — the
retries absorb the difference.

---

## 2026-07-28 · RQ3 moved to LOCAL weights — provider substitution made hosted untrustworthy

**Decision.** Rerun the gen-2 Track arm on local Ollama models rather than on any
hosted provider, and treat local weights as the *authoritative* source for
older-generation arms from now on.

**Evidence.** Both hosted routes are closed, for different reasons:

| model | DeepInfra | Together |
|---|---|---|
| Llama-3.1-8B | listed, real | 400 non-serverless |
| Qwen2.5-7B | delisted, real | serverless ✓ |
| Mistral-7B-v0.3 | delisted, **aliased to Mistral-Small-3.2** | 400 non-serverless |
| gemma-2-9b | delisted, **aliased to gemma-3-12b** | 400 dedicated-endpoint only |
| gemma-2-27b | delisted, **aliased to gemma-3-27b** | 400 non-serverless |

Not a budget problem. Together's "non-serverless" means renting a GPU instance by
the hour -- a different product, not a credit balance. The models are being
retired industry-wide.

**Why local is not a fallback but an upgrade.** Ollama models are
content-addressed: the digest is computed FROM the weights, so substitution
changes the digest by construction. That is *verification*, where the hosted
identity gate is only *inference from behaviour*. Recorded and asserted before
every run:

```
llama3.1:8b 46e0c10c039e · qwen2.5:7b 845dbda0ea48
mistral:7b  6577803aa9a0 · gemma2:9b  ff02c3702f32
```

Verified 2026-07-28 as the intended models, not smaller substitutes:
Llama 8.0B / Qwen 7.6B / Mistral 7.2B (v0.3, confirmed via the
`[AVAILABLE_TOOLS]` template absent from v0.1-v0.2) / Gemma 9.2B.

**Accepted limitation.** All four are 4-bit quantized (Q4_K_M; Q4_0 for Gemma)
against full-precision hosted gen-3. Same parameter counts and architectures,
lower numeric precision. Stated in the write-up. A *disclosed* compression is
strictly better than an *undisclosed* model swap.

**Design, and why not 4,000 random questions.** Measured laptop throughput is
**0.24 gen/s** (12-generation benchmark, two models) -- ~100x slower than hosted.
At a ~2% silent-consensus rate, 4,000 random questions yield ~80 usable cases for
~18 hours of GPU time. Instead:

```
1,054  ALL gen-3 silent-consensus questions -> measures PERSISTED and HEALED
1,500  random control                       -> measures EMERGED and the base rate
2,554  questions x 4 models = 10,216 generations ~ 12 h
```

Strata are recorded so the pooled rate can be reweighted to the corpus. This buys
~1,054 cases per arm against the pilot's 5-vs-7 -- an error margin of roughly
±3 points instead of ±40.

---

## 2026-07-28 · Every pilot-scale effect has shrunk at full scale — five for five

**Observation, now with enough instances to be a claim.**

| effect | pilot (300q) | full scale | direction |
|---|---|---|---|
| confidence-weighting delta | +0.008 | +0.003 | shrank |
| cross-model vs best single SE | +0.116 | +0.062 | shrank |
| PopQA AUC "degradation" | 0.761 (flagged as a finding) | 0.798 | vanished |
| RQ1 confidence in unanimous region | 0.688 | 0.600 | shrank |
| RQ2 map-density AUC | 0.747 | 0.705 | shrank |

**Five measured, five smaller. None grew.** A small sample lets a weak effect land
anywhere; the ones that landed *large* are the ones that got written up. That is
selection on the outcome, performed by the sample size rather than by anyone's
choice.

**How to apply.** Treat every remaining 300-question number as an **upper bound**,
not an estimate. Nothing pilot-scale enters the thesis as a result without a
full-scale rerun -- and reruns cost ~$1.20, so there is no excuse. Where a
full-scale rerun is impossible (RQ3 on retired models), say so explicitly rather
than quoting the pilot number as though it were equivalent.

**For the methodology chapter:** this is a cleaner demonstration of the
small-sample problem than anything in the literature review, because it is *this
project's own numbers*, measured twice, with everything except n held constant.

---

## 2026-07-28 · Precision comparison — 4-bit vs 8-bit, and the fp16 question

**Question raised by the user:** if we run one model at a time anyway, why not use
full precision rather than compressed weights?

**Answer, and the reason it changed the plan.** Two facts settle it:

1. **fp16 does not fit.** The four gen-2 models are 14–18 GB at fp16 against 8 GB
   of VRAM (RTX 4060 Laptop). They would run mostly CPU-resident off the 31.7 GB
   of system RAM, roughly 10–20x slower.
2. **The hosted comparison arm is not full precision either.**
   `Llama-4-Maverick-17B-128E-Instruct-FP8` is 8-bit *by name*, and DeepInfra does
   not publish serving precision for the other three. So "match full precision" is
   not an achievable target — there is nothing on the other side to match.

**Decision.** Run the comparison at **q8_0 (~8-bit)**, which is both achievable
(7.7–9.8 GB) and a closer match to the hosted arm's known FP8 than 4-bit is.
Recorded as `ensemble_local_q8`.

**Why run it at all rather than just switching.** 4-bit is ~4x faster, and the
full-corpus run is the expensive one. So the 2,554-question comparison decides
the 42,551-question run: if 4-bit reproduces 8-bit's answers, use 4-bit for the
full corpus; if not, the full run costs ~3x more wall-clock and needs a human
decision. **A cheap measurement deciding an expensive one** — the discipline that
was skipped on RQ4, where three expensive runs preceded the four-minute check
that invalidated all of them.

**Thresholds fixed BEFORE seeing the numbers** (`scripts/compare_precision.py`):
persistence within 5 pp, corpus blind-spot rate within 0.5 pp. Item-level
agreement and blind-spot-set Jaccard are reported alongside, because two arms can
match on averages while disagreeing about *which* questions are blind spots — and
it is the identity of the blind spots that RQ3 compares, not the count.

**Side benefit.** This closes an open ISSUES item carried since the pilot ("does
4-bit quantization degrade the disagreement signal?", previously NOT CLAIMABLE
because the two available runs differed in retry logic and think-stripping as
well as precision). Same weights, same questions, same grader, one variable.

---

## 2026-07-28 · Measured throughput on the laptop, and two estimates I got wrong

**Recorded because both errors were large and both were avoidable.**

| estimate | I said | actual | error |
|---|---|---|---|
| full-corpus hosted run cost | $19–32 | **$1.21** | 20x too high |
| local RQ3 run wall-clock | 11.8 h | **~40 min** | 18x too high |

**Cause of the second.** I benchmarked one generation at a time and measured
0.24 gen/s. The real run uses `max_workers: 24`, and local Ollama sustains
**4.5 q/s** on the 7–8B models. **A benchmark that does not reproduce the
production concurrency is not measuring the production system** — the same
mistake as the earlier hosted benchmark that sent the same question 8 times and
measured the provider's cache.

**Measured per-model rates, 4-bit, 24 workers:**

```
llama3.1:8b   4.5 q/s      fits in VRAM
qwen2.5:7b    4.5 q/s      fits in VRAM
mistral:7b    4.5 q/s      fits in VRAM
gemma2:9b     1.1-1.4 q/s  20%/80% CPU/GPU split -- 9.2B does not fit alongside context
```

Gemma is 3–4x slower than the rest *at 4-bit already*, and will be worse at
8-bit (9.8 GB against 8 GB VRAM). **Full-corpus estimate: ~17 h at 4-bit**, of
which Gemma alone is ~9 h. Quoted as measured, not extrapolated from the fastest
model.

**How to apply:** never quote a wall-clock or cost estimate that has not been
measured under production concurrency on the actual hardware. State which model
the rate came from, because a 4x spread across ensemble members makes a
single-model rate meaningless.

---

## 2026-07-29 · Repair the extended parquet in place, rather than re-run the chain

**Context.** Defect #36 left 159,988 of 170,364 rows with `gradeable = None` in
`answers_rq3local.parquet`, after ~9 hours of laptop generation had already
completed successfully.

**Options considered.**

| Option | Cost | Rejected because |
|---|---|---|
| Re-run `grade → nli → disagree` | ~40 min re-grade of 170k rows | `grade.run` refuses to touch `tier == "nli"` rows *by design* (cosine is negation-blind; re-grading would revert TruthfulQA verdicts in the flattering direction). Clearing `tier` to force it would re-grade all 170,364 rows, not just the 1,520 that needed it. |
| Re-run `nli` only | ~15 min of cross-encoder | Would fill `correct_cosine` from `correct`, which by then **is** the NLI verdict — silently reporting "0 verdicts changed" for the appended rows. Ordering makes this actively wrong, not just wasteful. |
| **Surgical repair, then `disagree`** ✅ | ~2 min | Chosen. |

**Decision.** Repair the two damaged columns directly, using the library's own
functions, then run `disagree` alone.

**Why this is safe rather than a shortcut.** `gradeable` is a pure function of
`(dataset, gold)` — recomputed from scratch for all 170,364 rows via
`nli.is_ungradeable`, so the repaired column cannot inherit a stale value and is
verifiable against the rule instead of against whatever was on disk. The NLI
verdicts themselves were never damaged: they were written under `mask`
(dataset == truthfulqa), which never touched the broken column.

**The one real loss, stated.** `correct_cosine` for 1,288 appended TruthfulQA
rows was gone from disk. Recomputed with `grade.grade_one` — the same
deterministic code path that produced it originally. It feeds a diagnostic only;
`disagree` never reads it.

**Constraint honoured throughout:** no reimplementation of the gradeable rule or
the cosine grader. Both were imported. Defect #33 was two copies of one retry
loop drifting apart, and #32/#35 were also fix-created. Three of four defects in
the last audit were introduced by that day's fixes, so a repair script that
re-derives a rule is a predictable next defect.

**Backup:** `answers_rq3local.parquet.predefect36.bak`, written before any
mutation, never overwritten on re-run.

---

## 2026-07-29 · `if "col" not in df.columns` is now a review flag

**Decision.** Treat every presence-gated column initialisation as suspect.

**Why.** Defects #23, #24, #26 and #36 are one bug wearing four costumes: a stage
assumed it was handed a complete file, and resume handed it a partial one.
Resume was added to survive multi-hour laptop runs and external kills — it did
its job four times — but it changed a global invariant that individual stages
still encode locally.

**How to apply.** A column must be filled **per row**, not per file. The pattern

```python
if "gradeable" not in df.columns:
    df["gradeable"] = True
```

is only correct for a file that is never extended. Use presence to decide
*whether to create*, and always follow with a per-row fill.

**Watch item.** `disagree.py` reads `df["gradeable"]` with a bare `~`. It now
receives a clean bool column, but it trusts its input. A defensive coercion there
was considered and rejected: two places asserting the same invariant is how the
grade/nli guard drifted in the first place. `nli.ensure_columns` owns it, and
`tests/test_nli.py` pins it.

---

## 2026-07-29 · RQ3 has TWO rates; quote 39.4% for persistence

**Decision.** Report **39.4%** as the persistence rate and **34.5%** as the
inherited share, always with their denominators. Never write "34.5% persist".

**Why.** The two numbers share a numerator (364 questions blind in both
generations) and differ in denominator:

```
persistence      364 / 923   = 39.4%   of gen-2's blind spots, how many SURVIVE
inherited share  364 / 1,054 = 34.5%   of gen-3's blind spots, how many were INHERITED
```

The subset design could only produce the second. Its question set was *defined*
as gen-3's 1,054 blind spots, which truncates gen-2's own blind-spot population
by construction — the same stratum-definition trap that produced the invalid
1.13%-vs-2.48% comparison recorded in Finding 4b. Measuring gen-2's full 923
required the whole corpus. That is why the full-corpus rerun was worth 9 hours of
laptop GPU even though PERSISTED itself did not move.

**How to apply.** "Do shared blind spots survive a model upgrade?" → 39.4%.
"Are today's blind spots inherited or new?" → 34.5% inherited, and note that
**690 emerged vs 364 persisted**: an upgrade creates blind spots nearly twice as
often as it passes them through — where *blind spot* means **undetectable**, not
newly wrong (2026-08-01 correction: 78% of the 690 were already wrong in 2024 and
merely disagreed). The subset's reweighted EMERGED estimate (~470)
was low by 32%, and it was the only quantity in that design carrying real
sampling error — which is exactly where the error landed.

**Also corrected:** the subset write-up labelled 690 as HEALED. At full corpus
HEALED is **559** and 690 is EMERGED. The subset could not distinguish them
because it never observed gen-2 blind spots outside gen-3's silent set.

---

## 2026-07-29 · Hand-labelling design — blinded, two strata, gen-3 arm

**Tool:** `scripts/handlabel.py`. Closes ISSUES 1b.

**Which arm.** The **gen-3 headline arm** (`answers.parquet`), not the local one.
Its TruthfulQA AUC (0.646) is the number quoted in the thesis. The local arm has
more low-margin cases (439 vs 330) but TruthfulQA contributes only 7 of its 923
blind spots, so relabelling it would change nothing that gets reported.

**Two strata, and why the control is not optional.**

| stratum | n | design |
|---|---|---|
| target | 330 | **census** — every case with \|margin\| < 0.10 |
| control | 100 | **seeded random sample** of the 1,030 cases with \|margin\| >= 0.10 |

Labelling only the low-margin cases would measure how often the grader errs
*where it already admits doubt* and say nothing about the 1,030 confident
verdicts that carry the weight of the reported number. The control stratum is
what turns "we fixed the coin flips" into a bounded statement about the dataset.

`--stats` reweights the two strata back to the corpus rather than pooling them.
Pooling would give the low-margin cases 76% of the weight when they are 24% of
the data — the identical trap recorded in Finding 4b's method note (the invalid
1.13%-vs-2.48% comparison).

**Blinded, and this is the load-bearing decision.** The machine verdict and the
margin are hidden, the model name is hidden, and the two strata are interleaved
by a seeded shuffle so the labeller cannot tell a coin flip from a confident case.

Rationale: watch-list item #3 — *every unintentional bias found in this project
has favoured our own hypothesis*. An unblinded labeller who can see "the machine
said WRONG" agrees with it more often than the evidence warrants. That anchoring
would shrink the measured correction, which is the flattering direction. Blinding
costs nothing here; a biased 430-case labelling pass cannot be repaired later.

`--stats` also reports **which way** the disagreements fall, because
watch-list item #2 says the grader's error runs one direction (over-generous).
That prediction is now testable rather than asserted.

**Reproducibility.** Queue order and the control sample are seeded from
`CFG["seed"]`, so the queue is identical on every run and resume is
deterministic. Autosave after every single judgement — a 430-case pass will span
several sittings and must never lose work.

**Recorded per case:** human verdict (correct/wrong/unclear), machine verdict,
margin, stratum, timestamp. `unclear` is a first-class option: forcing a binary
choice on a genuinely ambiguous item manufactures agreement.

---

## 2026-07-29 · Front-end rebuild — scope, and the four panels

**Context.** All model-dependent work and the hand-labelling are complete; zero
open issues. The remaining thesis contribution is the visual-analytics one, and
the tool is the artifact that will be expert-evaluated. Two web artifacts exist
and both display retracted pilot numbers (see ISSUES #37).

**Decision.** Rebuild `faultlines-tool` as the evaluated deliverable, at full
scale, with four panels. Each panel is specified as **the job it does**, not as a
chart type — the task abstraction is a required VA deliverable, so writing the
panels this way produces both artifacts from one act of design instead of
reverse-engineering tasks from an interface afterwards.

| panel | the job | the discovery it enables |
|---|---|---|
| **Map** | *where do the errors live?* | 42,551 questions positioned by question similarity; recolour by disagreement / wrong / blind spot / dataset / confidence. Whether blind spots are clustered or scattered — invisible in any table of averages. |
| **Audit inspector** | *why did all four models fail together here?* | the 1,054 blind spots with all four answers + confidences. Keeps the existing labelling controls so a session leaves data behind, not impressions. |
| **Generation diff** (new) | *did the upgrade fix this, or just hide it?* | per-question hidden in both / now visible / newly hidden, old vs new answers side by side. RQ3 made interactive: 364 / 559 / **690**. Each case states, from its own answers, why it is in its category — which is what exposed the 2026-08-01 labelling correction. |
| **Signal panel** | *how much should I trust the signal here?* | per-dataset AUC + the single-model baseline. 0.865 overall hides TruthfulQA 0.71 vs TriviaQA 0.87. |

**Deliberately NOT built** — no login, no server, no database, no build step. It
stays one static page with data baked in, deployed to the existing Vercel URL.
Rationale beyond laziness: expert-evaluation participants must be able to open a
link. Any setup friction is spent out of the 45 minutes someone lent us, and a
server is one more thing that can be down on the day.

**Generation diff is the panel worth the effort.** It is the only one showing
something no existing tool shows, and it carries the project's most
counterintuitive result — an upgrade *creates* blind spots nearly twice as often
as it inherits them. A reviewer can click through the actual questions rather
than take the ratio on trust.

**Data plan.** Export from `records.parquet` (has `x`,`y` for all 42,551) joined
to `records_rq3local.parquet` on `qid` for the diff, plus per-answer detail for
the 1,613-question union of both arms' blind spots. Coordinates rounded; the map
payload is arrays not objects. Target: map loads before case detail, so first
paint does not wait on the inspector data.

**The narrative site** (`faultlines-web`, "pipeline level by level") is a
communication artifact, not a VA contribution. Its stale numbers get corrected;
it does not get rebuilt, and it is not what gets evaluated.

---

## 2026-07-29 · Two artifacts, ONE deployed root

**Decision.** `faultlines-web/` is the single Vercel root and now contains
everything:

```
faultlines-web/
  index.html        the DECK -- replaces the PowerPoint
  tool/index.html   the TOOL -- the evaluated deliverable
  tool/data.json    2.97 MB, written by scripts/export_web.py
  summary.json      headline numbers for the deck
  pipeline.html     the previous level-by-level explainer, preserved
```

**Why the move.** The tool lived in a sibling directory `faultlines-tool/`, and
the deck linked to it as `../faultlines-tool/index.html`. That resolves when you
serve the parent folder locally and **404s in production**, because
`faultlines-web` *is* the deploy root — a parent directory does not exist there.
Caught by asking "what does this link resolve to on Vercel?" rather than by
clicking it locally, where it worked fine.

The alternative — deploying the parent `final_proposal/` folder — was rejected:
it would publish the .docx, the .pptx and the build notes alongside the site.

One root also means **one URL to send an evaluation participant**, which is the
constraint that drove the no-server decision in the first place.

**Consequence:** `export_web.py` writes to `faultlines-web/tool/data.json`. There
is exactly one copy of the 3 MB payload; nothing is duplicated for deployment.

---

## 2026-07-29 · The explainer becomes a DECK, not a scroll page

**Brief, verbatim:** *"too boring and while explaining, I require a lot of
vertical scrolling."*

**Decision.** One idea per screen, `←`/`→`/`space`/click to advance, and **no
page scrolling anywhere** (`html,body{overflow:hidden}`, every slide exactly one
viewport). Verified: 0 of 14 slides overflow at viewport heights 1293, 900, 768
and 700 px — the last two matter because that is a laptop and a projector.

Also added because it costs nothing and helps a live talk: a progress bar, dot
navigation, and `#n` deep links (`index.html#8` opens slide 8) with a
`hashchange` listener, so a pasted link works in an already-open tab.

**The narrative was re-sequenced to match how the project actually went**, which
is what "update it according to the decisions we took" required. It is no longer
a description of the pipeline; it is the argument:

```
1-2   the published claim, and that we reproduce it (0.862) -- so the signal is NOT the contribution
3     the gap: what if they all agree AND all are wrong
4     what was built
5-9   five results, one per slide
10    36 defects · 340,728 answers voided · one retracted result
11    every bias we found flattered our own hypothesis
12-14 the tool, where it stands, close
```

**Slides 10 and 11 are deliberate and are the differentiator.** A deck that
presents only clean results invites "how do you know?"; a deck that shows the
provider substitution and the three-times-repeated false RQ4 table answers it
before it is asked. The methodology *is* a finding here.

**Numbers are never typed into the deck.** It reads `summary.json`. The previous
version hard-coded a 300-question AUC of 0.788 in seven places and still showed
it days after the corpus run replaced it (ISSUES #37). A deck that cannot go
stale is worth the fetch.

---

## 2026-07-29 · REVERSED: two Vercel projects, not one root

**Supersedes the "ONE DEPLOYED ROOT" decision above.** Shivani's call, and the
reasoning is better than mine:

- The tool is the evaluated deliverable and deserves **its own citable URL** for
  the thesis, not a subpath of a slide deck.
- Editing a slide should not redeploy **3 MB** of `data.json`.

**What I had flagged as the cost of separate projects — a cross-link that 404s in
production — is handled rather than accepted.** `faultlines-web/index.html`
defines `TOOL_URL` once at the top:

```js
const TOOL_URL = '';    // paste the tool's URL after its first deploy
const isLocal  = ['localhost','127.0.0.1',''].includes(location.hostname);
const TOOL     = TOOL_URL || (isLocal ? '../faultlines-tool/index.html' : '');
```

Local dev resolves relatively; production resolves absolutely. If `TOOL_URL` is
still empty on a deployed page, `toolBtn()` renders a **visible disabled note**
("set TOOL_URL") instead of a dead link — a silent 404 on the one button that
leads to the contribution is the worst possible failure here, so it fails loudly.

**Reverted:** `export_web.py` writes `../faultlines-tool/data.json` again; the
`faultlines-web/tool/` directory is gone. Verified locally end-to-end: deck at
`/faultlines-web/`, tool link resolves and returns **200**.

---

## 2026-07-29 · Version control: the project has none, and that is the real risk

**Finding, not a preference.** `git rev-parse` in the project root:
`fatal: not a git repository`. There is **no version control at all** on:

- ~3,400 lines of RESULTS.md + ISSUES.md + DECISIONS.md — the record of 36
  defects, four retracted results and every design choice
- the pipeline that produced 170,364 graded answers
- two web artifacts

A single bad overwrite loses work that cannot be regenerated from anything except
9 hours of laptop GPU time and a paid API. Every safeguard built this month —
resume, digest verification, identity gating, the backup before the #36 repair —
protects the *data* and none of it protects the *code and the records*.

**Decision: create the repo. PRIVATE until after the defense.**

| | private now | public now |
|---|---|---|
| Vercel Hobby auto-deploy | ✅ works | ✅ works |
| academic integrity pre-submission | ✅ safe | ⚠️ results unpublished, defense not held |
| dataset redistribution | ✅ no exposure | ⚠️ TruthfulQA / PopQA / TriviaQA / HaluEval derivatives, licences unchecked |
| provider ToS on publishing model outputs | ✅ | ⚠️ unchecked |
| portfolio value | later | now |

Private costs nothing that matters today and removes four unresolved questions.
Flip it after the defense, when the records become an asset rather than an
exposure.

**One repo, two Vercel projects** — Vercel sets *Root Directory* per project, so
`faultlines-web/` and `faultlines-tool/` deploy independently from the same repo.
This is what makes the reversal above free.

**What must NOT be committed:** `faultlines_project/data/` is **287 MB** and
already in `.gitignore`. **But `faultlines-tool/data.json` (2.97 MB) MUST be**,
because Vercel builds from the repo and the tool cannot load without it — it sits
outside `faultlines_project/`, so the existing ignore rule does not catch it.
That asymmetry is the one easy mistake here.

**Secrets: clean, verified before advising.** No `.env` in the tree, and
`config.yaml` stores only environment *variable names* (`api_key_env:
"DEEPINFRA_API_KEY"`), never values. The key lives at `~/.faultlines.env`,
outside the project. Nothing to scrub.

---

## 2026-07-29 · Deployment — and the Root Directory the CLI cannot set

**Live:**

| project | URL | serves |
|---|---|---|
| `faultlines` | https://faultlines-peach.vercel.app | the deck (`faultlines-web/`) |
| `faultlines-tool` | https://faultlines-tool.vercel.app | the tool (`faultlines-tool/`) |

Both connected to `github.com/shiva-shivanibokka/faultlines` (private), so a push
to `main` redeploys both. Verified by pushing and watching the build fire.

### The trap that was caught before it fired

`vercel git connect` attached the repo to both projects and left **Root Directory
= `.`** — the repo root. `vercel project update` has no `--root-directory` flag,
so the CLI cannot change it; that setting is dashboard-only.

Left alone, the next `git push` would have built the **repo root** for both
projects. The repo root has no `index.html`. **Both live URLs would have 404'd,
silently, on the next commit** — and the failure would have surfaced at whatever
moment someone next opened the link.

**Fix without the dashboard:** for a static site with no build step, *Output
Directory* does the same job as Root Directory — it decides what gets published.

```
vercel project update faultlines      --output-directory faultlines-web
vercel project update faultlines-tool --output-directory faultlines-tool
```

Confirmed end to end: pushed a commit, the auto-deploy built, and both URLs serve
the right subfolder (`summary.json` 200, `data.json` 2.97 MB 200,
`pipeline.html` 200).

**Not attempted:** extracting the Vercel CLI's stored auth token to PATCH
`rootDirectory` through the REST API. It would have worked, and it is the wrong
habit — a credential on disk is not an input to a script. The supported flag
achieved the same result.

### noindex, added unprompted

The repo is private until the defence, but **a Vercel deployment is public by
default** — the two are independent, and it is easy to assume the first implies
the second. The deck now states the full defect log, the 340,728 voided
generations and every unpublished result. Both pages therefore carry:

```html
<meta name="robots" content="noindex,nofollow">
```

Anyone sent the link still gets it; search engines do not index unpublished
capstone results. Remove after the defence. This is not the same as access
control — Hobby-plan production URLs cannot be password-protected — so the URLs
should be treated as shareable-but-unlisted, not private.

### Files removed

`GraphLoom_Capstone_Proposal.docx` (a different project, on request) ·
`version-1/FaultLines_Capstone_Proposal_BACKUP_v1.docx` (superseded, and in git
history) · `__pycache__` ×3 · `.pytest_cache`.

**Kept against the instruction to remove clutter, because they are evidence:**

| file | why |
|---|---|
| `data/interim/answers_rq3local.parquet.predefect36.bak` | the pre-repair state for ISSUES #36 |
| `data/raw/retrieval_cache.json.poisoned.bak` | the poisoned cache from ISSUES #29 |

Neither is in git (`data/` is ignored), so deleting them locally destroys the only
copy — and with it the ability to demonstrate that two critical defects were real
and that the repairs were sound.

---

## 2026-07-29 · Tool refinement — rail crowding and a reset

**Two requests, one structural fix and one addition.**

### The rail was crowded because it held the wrong things

The 268 px rail carried four controls **and** three read-only tables. A 5-column
table in that width gave each numeric column ~40 px and truncated "popqa" to
"po…" — earlier patched with column-width percentages, which treated the symptom.

**The tables were never controls.** They are context: *how far to trust this*, *is
four models better than one*, *does retrieval fix it*. Nothing in them filters
anything. Moved to a horizontal strip **below the map**, three across, where they
have ~3× the width and read without truncation. The rail now holds only the four
things that change what you see.

### The strip defaults to collapsed on short screens — measured, not guessed

It costs 246 px. Map share of the viewport:

| viewport | open | collapsed |
|---|---|---|
| 900 px | 55% | 78% |
| 768 px | **47%** | 75% |
| 700 px | **42%** | 72% |

Below ~850 px the primary view loses more than half the screen to a secondary
panel. So: `ctx.open = innerHeight >= 850` **on first visit only** — after that the
user's own toggle is remembered in `localStorage`. Re-deciding for them on every
load would be the more annoying bug.

**The toggle calls `resize()`.** Not cosmetic: the hover hit-test uses a bucket
grid built from canvas dimensions, so a canvas that changed height without
rebuilding the grid would select the *wrong point* under the cursor — silently,
with no error. Verified after both open and close that a known point still
hit-tests to itself.

### `reset all filters` — button, and the `0` key

Five independent pieces of state (colour, datasets, show-only, generation diff,
brush). Putting them back was a five-click job, and a demo that opens from a
half-filtered state shows the wrong thing.

`resetAll()` restores **both** the internal state and the visual state — checkbox
`checked`, radio `checked`, which buttons are lit. Resetting only the former is the
obvious version of this bug: the tool would show everything while the controls
claimed a filter was still on. Verified: dirtied all five, reset, and confirmed all
five plus every control's appearance came back.

`clear selection` is kept alongside it — dropping the brush while keeping your
colour and dataset choices is a common move, and a single button cannot do both.

---

## 2026-08-01 · Tab 1 — the legend becomes the filter, and one colouring is deleted

Three changes, all from questions a reader asked that the interface should have
answered on its own.

### 1. The map states which model generation it shows

It is `records.parquet` — the **2025** ensemble, all 42,551 questions. The 2024
arm lives in `records_rq3local.parquet` and appears on the map only as bit 3 of
the flag word, surfaced in a hover tooltip. **Nothing on screen said this**, so
"is this map the old models or the new ones?" was unanswerable without reading
the exporter. The header now says it, and points at tab 3 for the comparison.

**Rejected: a second map for the 2024 arm.** The two arms are only meaningful
*compared*, and comparison is a juxtaposition task (TASKS T5), not a spatial one.
Two clouds of 42,551 dots side by side asks the reader to diff by eye, which is
precisely the operation a person cannot perform. The map answers *where*; tab 3
answers *did it change*.

### 2. Deleted the confidence-weighted disagreement colouring

Measured on the full corpus before deciding:

| | |
|---|---|
| Spearman, disagreement vs `n_clusters` | **0.981** |
| AUC vs `majority_wrong` — score / count | 0.865 / **0.862** |
| `disagreement_unweighted` | a **pure function** of `n_clusters` |
| cases the weighting actually reorders | **759 of 8,575** two-answer cases (8.9%) |

So the tool offered two colourings of **one** measurement. The extra information
in the weighted version is worth **+0.003 AUC** — which is RESULTS claim 9,
*"confidence-weighting is a wash at scale"*, showing up as interface clutter.

The count is the half that survives because it is the legible one: four crisp
bands a reader can name and filter, against a continuous score with no natural
breakpoints. Four colourings, not five.

**Also removed from the payload:** `d` (disagreement) and `c` (mean confidence).
`c` had never been read by any view. `data.json` **2.86 → 2.41 MB**. Verified by
diffing the regenerated file against the old one — `qid/x/y/ds/f/k`, cases and
stats all byte-identical, only the two arrays gone. The score remains in
`records.parquet`, which is the source of record; re-add three lines in
`export_web.py` if a view ever needs it.

### 3. The legend is now the filter

Clicking a legend band shows only those dots; bands multi-select; clicking again
undoes. Each band carries its live count.

- **One `bandOf(i)`** keyed off `state.colour` drives the legend, the colour and
  the filter together, so a band that is drawn is a band that filters. Three
  parallel definitions of "which group is this point in" is exactly how a legend
  starts lying about the picture.
- **Counts are computed with the pick temporarily cleared.** Otherwise every
  unselected band reads 0 and there is no visible way back.
- **A pick is dropped on recolour.** It belongs to the colouring it was made in;
  carrying it across would hide dots under a legend that no longer explains why.
- **Map-only, deliberately.** It does not filter the tab 2 queue: every audit
  case has `n_clusters == 1` by the definition of silent consensus, so a cluster
  filter would empty the queue every time. The brush remains the one control that
  crosses views, which keeps the linked-view contract in TASKS §3 a single arrow
  rather than a mesh.

**Why this matters beyond convenience.** A legend that is only a caption forces
every "show me just the X" question through a control in another panel, or
through nothing at all. Making the encoding itself the control is the cheapest
possible route from *seeing a group* to *isolating a group* — Brehmer & Munzner
**select** and **filter** on the same widget that already **encodes**.

### 4. The correctness colouring was a binary that hid the interesting half

`majority_wrong` is **the ensemble's own answer** — the largest cluster's, the one
you would actually be handed. Painted as a plain right/wrong binary it reads as
"all the models were wrong", which is false for a quarter of the red:

| band | n |
|---|---|
| all four right | 18,366 |
| majority right, one or more wrong | 8,779 |
| **majority wrong, one or more right** | **3,956** |
| all four wrong | 11,450 |

Those middle two rows are 12,735 questions — **30% of the corpus** — where the
models split on correctness, and they were invisible under a two-colour encoding.
They are also the entire mechanism of the thesis: disagreement is a usable signal
precisely *because* the middle exists, and silent consensus is dangerous
precisely *because* row 4 has no middle to fall into.

`any_wrong` is exported as bit 4 of the existing flag integer to make the split
possible — no new array, and it stays banned as a prediction target (it is
mechanically implied by the disagreement score; see `disagree.py`). Using a
forbidden-as-a-target quantity as a *display* dimension is fine and the comment at
both ends says which it is.

### 5. Cut "Show only" to one checkbox

Three buttons, two of which had become a legend click: *only where they answered
wrong* is the wrong band of the correctness colouring, *only the blind spots* is
the red band of the blind colouring. Same predicate, different words, second
control — and the wording was itself the ambiguity ("they answered wrong" =
which of them?).

What survived is the one thing a legend pick **cannot** express: restricting to
blind spots while colouring by something else, because a pick is cleared on
recolour by design. That is not a hypothetical — blind-only + colour by dataset
gives 461/222/366/**5**, which is the 99.5%-outside-TruthfulQA finding in two
clicks.

### 6. The map was rendering at two-thirds size

`XMIN/XMAX` came from `min`/`max`, so **214 of 42,551** stray points stretched the
frame **1.5×** horizontally and **1.35×** vertically. The main cloud was being
drawn small to leave room for a few dozen outliers.

Now scaled to the **0.25–99.75 percentile**, with the outliers **clamped to the
border rather than dropped** — no question silently leaves the map — and the
header states that 214 sit on the edge, because an unexplained line of dots along
a border is a false pattern. Rail 250 → 212 px, page gutters 18/24 → 12/16.

**The general rule this is an instance of:** an auto-scaled view is scaled by its
worst-behaved data point. Any min/max range over real data is a decision to let
outliers set the zoom level, and it should be made deliberately or not at all.

### 7. Two more controls deleted, and a hit test that was the real bug

**"Narrow it down" removed entirely.** Reduced to one checkbox in §5, then to
nothing: it was the blind band under a second name, and the composition that
justified it is covered by making the **dataset counts live**. Pick the blind
band and the rail reads 461/222/366/**5** without any control existing to say so.
A number already on screen replaced a widget — the cheapest possible version of
the feature.

Counts are computed with the dataset filter itself lifted; otherwise unticking a
set drives its own count to zero and there is no number left to tick back to.

**The unstable hover was not a dot-size problem.** `nearest()` returned the
closest point of any kind and the caller discarded it afterwards if it turned out
to be filtered out. Over a filtered region the cursor kept snapping to greyed-out
neighbours, so the tooltip flickered on and off as the mouse moved a pixel — a
dot could be plainly visible and impossible to land on. The filter belongs
**inside** the hit test. The search neighbourhood was also 3×3 cells at `CELL=16`
for a 22 px radius, which does not fit — widened to 5×5.

Measured afterwards on a filtered band: **48 of 49** positions in a ±3 px jitter
hold the tooltip, and all 49 resolve to the same question.

**A picked band now pops** — r=4.4 with a white halo, the treatment the blind
spots already had. That is a hit target as much as an emphasis: a 2.6 px dot is
not something a hand holds still on. Above 6,000 points it reverts to normal
size, where the halo distinguishes nothing and costs two extra fills per point.

### 8. "Majority wrong" now says by how much

The colouring answered *whose* answer was wrong but not *how alone* it was, which
is the next question every time. Two fields, packed into **bits 5–7 and 8–10 of
the flag integer that already ships** — no new array, no payload cost:

| field | meaning | range |
|---|---|---|
| `n_correct` | how many of the four were right | 0–4 |
| `n_major` | size of the largest answer cluster | 1–4 |

`n_major` is **recovered exactly** from `disagreement_unweighted`, which is
`1 - max(count)/n` by construction in `disagree.py`, so the displayed majority and
the published disagreement score cannot drift apart — there is only one
computation. `n_correct` comes from the answer rows.

The tooltip now reads *"2 of 4 gave the answer you would get · 1 of 4 got it
right"*, and says **"no majority — all four differed"** when `n_major` is 1
(9,639 questions, where "majority wrong" is a misnomer worth flagging in the UI).

**Verification, because packed bits are easy to get silently wrong:** `n_correct
== 0` agrees with the existing `all_wrong` flag on all 42,551 rows, and
`n_major == 4 and n_correct == 0` agrees with `silent_consensus` on all 42,551 —
two independent invariants, zero mismatches. Spot-checked `triviaqa-09955`
against its raw answer rows: 3 clusters, majority 2, 1 correct, majority wrong.

### 9. Two counts that read as one, and an effect that only fired sometimes

**The tooltip stated two different quantities in the same sentence shape.**

```
3 of 4 gave the answer you would get
1 of 4 got it right
```

One counts who **agreed**; one counts who was **right**. They share a
denominator, they sat on adjacent lines, and both ended in a verb phrase about
answers. A reader saw the same fact stated twice with two different numbers —
strictly worse than not showing it at all, because now the view looks
inconsistent with itself.

**The rule:** two quantities over the same denominator must be separated by a
**label in a fixed column**, never by the tail of a sentence. Rewritten as a
table, with the verdict promoted to a headline and the previously loose
"N different answers" line pulled in as a third labelled row:

```
The answer you would get is WRONG
agreed on it by       2 of the 4 models
answered correctly    1 of the 4 models
distinct answers      3 of a possible 4
```

**The pop only fired on one band of four.** It was gated at 6,000 points shown,
so "majority wrong, one or more right" (3,956) popped and the other three
(8,779 / 11,450 / 18,366) silently did not — one control behaving differently
depending on which band was clicked, with nothing on screen explaining the
difference.

**A conditional effect is worse than a weaker one**: the user cannot distinguish
a threshold from a bug, and the reasonable conclusion is that the tool is
unreliable. The radius now grades with the count (6.2/4.4 → 5.2/3.7 → 4.2/3.0)
and a pick always pops. Worst case measured: **18,366 points with halos redraw in
61 ms** and remain clearly separated from the greyed-out background — the
threshold was protecting against a cost that was not there.

**Both of these were found by a reader, not by a test** — the same pattern as the
RQ3 labelling correction (ISSUES watch-list 3b). Neither is expressible as an
assertion: one is about whether two true sentences can be told apart, the other
about whether an effect is *consistent* rather than *correct*. The presentation
layer keeps producing defects of a kind the test suite is structurally unable to
hold, which is an argument for the expert sessions being the real verification
step for the interface, not a formality after it.

---

## 2026-08-02 — the RQ5 web arm uses a keyed search API, and Tavily with the answer OFF

**1. Scraper -> API.** The first web arm parsed DuckDuckGo's HTML results page. It
passed a smoke test, then DDG blackholed the IP ~40 questions into the real run:
ConnectTimeout on every DDG host while Wikipedia and Bing returned 200. Every
search after that failed, **the models kept answering anyway**, and the run was
recording model behaviour under a dead tool — the exact RQ4 failure mode
(ISSUES #28-30), reproduced inside the arm built to show the lesson had landed.
Those 48 rows were quarantined, not used.

A keyed API has a published rate limit, which can be respected. A scraped page has
no contract; it tolerates you until it does not, and the failure is silent.

**2. The health gate now fires DURING the run, not in the summary.** The old gate
computed the failure rate at the end. It was correct and useless — it described a
run that was already worthless. `websearch.health_ok()` is now checked on every
failed search and trips a shared abort flag above 10%.

Implementation note worth keeping: the first version raised `SystemExit` from
inside a worker thread. **That kills the thread, silently, and the run continues** —
a safety net that looks present and does nothing. It is a `threading.Event` the
workers check instead.

**3. Tavily, with `include_answer=False`.** Tavily is search built for agents, so
it is the least dismissible tool available: nobody can answer this finding with
"you gave it a weak search tool". But it will also return an **LLM-written answer**
to the query, and passing that to the model would change the study. On a question
all four models got wrong, handing them a fifth model's answer measures
*model-vs-model*, not *does the open web contain the correction*. The flag is off,
and it is off deliberately — this line is the difference between the two studies.

`search_depth=basic` for the same reason and one more: 1 credit, and it is the
plain-search behaviour the comparison assumes.

**4. The arm runs on a stratified sample.** Free tiers are ~1,000 (Tavily) to
~2,500 (Serper) credits; the full arm needs ~6,000-8,000 searches. `--sample N`
takes a seeded sample stratified by dataset — stratified because the entire
comparison is per-dataset (obscurity vs misconception), and truthfulqa has only 4
questions, which a simple random sample would drop. Sampling is stated in the
write-up with n and CI, not hidden.

---

## 2026-08-03 — one scoring method everywhere: head-count, not confidence-weighted

**Raised by Shivani**, while asking whether confidence-weighting was novel. It is
not the novelty question that mattered — it was the follow-up: *"so did we do
headcount scoring or still continue with the weighted scoring?"* The answer was
**both, in different places**, and nobody had noticed.

### What was actually happening

| where | score used |
|---|---|
| headline AUC, slide 1 | head-count — **0.862** |
| the tool's colour bands | head-count |
| `majority_wrong` (is this question an error?) | head-count |
| **head-to-head vs single-model Semantic Entropy, slide 8** | **weighted — 0.864** |
| per-case `dis` shown inside the tool | weighted |

So the deck stated 0.862 on one slide and 0.864 on another for the same
measurement, and the slide that used the higher number was **the one comparing
us to a competing method**. The gap read +0.064 where RESULTS.md says +0.062.

Nothing was hidden — RESULTS.md has always carried both columns, which is how
the discrepancy was traceable at all. But "we used the weighted score for the
competitive comparison and the plain one for the headline" is not a sentence
worth having to say in a defence.

### Why head-count is the one that survives

Confidence-weighting was in the proposal as an improvement, argued rather than
measured. Measured, it is not one:

| arm | weighted | head-count | |
|---|---|---|---|
| 300-q pilot, 7–9B models | 0.776 | **0.788** | weighting **hurt** |
| 300-q, 17–27B models | **0.801** | 0.793 | weighting helped |
| full corpus, 42,551 | 0.865 | 0.862 | **+0.003 — a wash** |

The mechanism is calibration, and it is a finding in its own right. Weighting
assumes one model's "0.90" means the same as another model's "0.90". Within a
single model's own samples — which is what the Semantic Entropy literature
weights — that assumption is fair. **Across four different makers it is not**,
and small models are miscalibrated badly enough that weighting by them injects
noise rather than removing it. Bigger models are calibrated well enough for it to
help slightly. At full corpus the effect is +0.003, i.e. nothing.

**So there is nothing to buy with weighting and something to lose.** Head-count
is also the legible one: with four models it takes exactly four values
(0 / 0.25 / 0.5 / 0.75), which is why the tool's four colour bands are a pure
function of it and why the weighted colouring was already deleted (2026-08-01).

### Changed

`scripts/export_web.py` — `cross_model_same_qids`, the per-case `dis`, and
`dis_old` all switched to `disagreement_unweighted`. Slide 8 now reads **+0.062**,
matching RESULTS.md. `auc_weighted` is still exported alongside `auc`: it is the
evidence for this decision and deleting it would make the decision unreviewable.

The per-case switch fixes a small correctness bug as well. The tool prints
*"they all said the same thing"* when `dis < 0.02`, and on the weighted score
that sentence could appear for a case where they did not — three confident models
plus one hesitant dissenter can fall under 0.02. Unweighted, 0.00 means exactly
one meaning cluster, which is what the words claim.

### Rejected

**Keeping both and labelling them.** The deck already labelled them, in
RESULTS.md, and the discrepancy still reached a live page. A number a reader has
to check the provenance of is a number that will eventually be quoted wrong.

**Dropping the weighted score entirely.** It is the control that makes "we chose
head-count" a measurement rather than a preference.

### Follow-up the same day — RQ1's baseline was the same bug, and it mattered more

The sweep for other consumers of the weighted column found `rq1_confidence.py`.
There it was not cosmetic.

RQ1 asks **"what does adding confidence buy?"** and answers it with the gap
between two detectors:

```
Detector A   1 feature   the disagreement score
Detector B   4 features  disagreement, mean confidence, lowest confidence, n_clusters
```

Detector A's single feature was `disagreement` — **the confidence-weighted
score, which is computed from the confidences.** So the baseline contained the
very quantity the experiment exists to isolate, and the gap measured "extra
confidence on top of confidence", not "confidence versus none".

| Detector A's feature | A | B | gap |
|---|---|---|---|
| `disagreement` (weighted — contains confidence) | 0.854 | 0.872 | +0.018 |
| **`disagreement_unweighted` (head-count — contains none)** | **0.847** | **0.871** | **+0.024** |

**The correction makes the finding stronger, and that is the reason to state it
loudly rather than restate it quietly.** A change that moves a number in your own
favour is exactly the kind this project has committed to narrating — see the
"every bias found flattered our own hypothesis" watch-list entry.

The justification is not the larger number. It is that **a baseline cannot
contain the thing whose contribution it exists to measure.** The direction of the
correction is incidental, and the evidence that it is incidental is on the same
page: the identical change to `cross_model_same_qids` moved that number the other
way, +0.064 → +0.062.

Note also that Detector B barely moves, 0.872 → 0.871. It carries the confidence
columns either way. **The entire change is on the baseline**, which is where the
defect was.

Changed: `faultlines/rq1_confidence.py` (the dropna subset, `combo_cols`, and
`auc_disagreement_alone`), re-run on the full corpus — sklearn over existing
parquets, no generations, no cost. RESULTS.md Finding 6 updated with the old
numbers kept visible.

---

## 2026-08-25 — Four framing decisions taken after an external read of the repo

An outside review (`ASSESSMENT.md`, read-only, nothing measured by the pipeline)
computed statistics that did not previously exist anywhere in the project. Four
of them change what the write-up claims. Recording them here because each one is
a case where a reasonable person would have chosen differently.

### 1. The independence violation is the finding, not a caveat

Every framing so far asserted that four makers means four independent brains.
`pipeline.html` L2 even carried a note saying pairwise error correlation was
*worth measuring on a small slice before committing*. It was never measured.

Measured on the full corpus (`data/interim/answers.parquet`, 42,551 questions):

```
mean pairwise error correlation  phi = 0.667      (independence = 0)
observed  P(all four wrong)          26.888%
predicted P(all four wrong) if indep  3.002%
CONCORDANCE RATIO                        9.0x
```

**Decision: lead with this rather than defend against it.** The rejected option
was to report it in limitations, which is where it naturally belongs and which
is also where a reviewer would have found it first. The premise the entire
disagreement literature rests on is false by an order of magnitude; that is a
larger claim than the 2.5%, and the 2.5% becomes its consequence rather than its
headline.

**Note the distinction the write-up must keep sharp**, because it is easy to
collapse and the collapse is wrong: *all four wrong* (26.9%, 11,450 questions)
is NOT *silent consensus* (2.5%, 1,054). Four models can be wrong in four
different ways, and then the detector fires correctly. Silent consensus needs
them wrong AND agreeing. About 9% of all-wrong cases converge that way.

### 2. RQ5's tool comparison is dropped; the ceiling is the finding

Wikipedia 34/131 vs open web 38/131. Discordant pairs 8 web-only, 4 wiki-only,
**McNemar exact p = 0.388**. There is no measurable difference between the two
tools, and every framing of "the comparison IS the finding" has to go.

**Decision: lead with the ceiling instead** — *neither* tool repaired 67.9%
[59.5%, 75.3%] of matched cases. Agentic retrieval does not rescue silent
consensus regardless of tool. Well-powered, tight, and a better claim than the
one it replaces. The rejected option was to keep the comparison with a
"suggestive" hedge, which is how underpowered comparisons survive into papers.

### 3. The generation/scale confound is reframed rather than fixed

Recorded as a confound on 2026-07-27; the designed fix (the Gemma ladder) was
voided by #31. A hosted 2024-generation arm at 24-27B would cost about $5 and
three hours.

**Decision: do not run it. State what was actually measured.** The arms differ
in generation, scale and serving, and no fully size-matched four-maker set
exists — Meta ships no 2025-generation dense model below 17B active. The claim
becomes: *when a deployed ensemble is upgraded, which in practice means newer
AND larger, overall error falls 25% while the share of errors that are shared
rises 1.52x (95% CI 1.42-1.63).* That is the practitioner-relevant quantity, it
is true, and the decomposition becomes a named, costed future-work paragraph.

Reversible: if the thesis is on track on 1 November, the arm can still be run.
See `PLAN.md`.

### 4. Ensembles should be selected by measured correlation, not by rank

Follows from (1). If the premise fails by 9x, the actionable question is not
"can we make models independent" -- we cannot, they share the training corpus --
but "how much can decorrelation be bought, and how would you shop for it".

**Decision: add the decorrelation frontier** (`PLAN.md` 1.1). Eight models are
already on the identical 42,551 questions; 162 ensembles of size 2-4 can be
formed from them with **no new generations**. Plot phi against signal AUC and
see whether the lowest-correlation ensembles beat the highest-accuracy ones at
equal size.

This is the constructive half of the independence finding, and it is a
*selection* problem, which is what the visual-analytics contribution is for.

---

## 2026-08-26 — five decisions taken while closing Phase 4

### 1. No user study. The evaluation is analytical, and the chapter says so first.

**The choice.** `TASKS.md` §5 specifies a six-task expert study. It was not run,
and no attempt will be made to run it.

**Why.** The author relocated and cannot recruit. The alternative to admitting
that was to run something thinner and call it the study — two friends, a guided
session, a result nobody could disbelieve because nobody could fail.

**What was done instead**, and it is a recognised class of visualization
evaluation rather than a fallback invented for the occasion: a cognitive
walkthrough (Wharton et al. 1994) with two of its four questions *computed* from
the tool's own exported data; the documented record of what the instrument
surfaced during its own construction, which includes the correction that cut this
project's own headline; and measured performance.

**The cost is stated, not hidden.** §6.7 says plainly that every discovery in
§6.2 was made by the person who built the thing, and that one designer is not an
independent evaluator.

**Rejected: an LLM driving the six-task study.** Technically possible — the
unmoderated mode exists and logs every interaction — and genuinely novel. Also
contentious enough that a defence could be spent arguing about the method instead
of the thesis. Revisit for a VIS paper after graduation.

### 2. The outside judge is Olmo-3.1-32B, and two vetted candidates were dropped

**The choice.** When the cross-arm artifact comparison needed a judge outside
both ensembles, `judge_panel.py` offered four. Two are unusable and the comment
above them says none is a reasoning model (ISSUES #59).

**Why Olmo.** Trained on Dolma, a fully documented open corpus, which is the
strongest available break in *data* lineage — the variable this thesis argues
actually drives correlated error. It also returned 0 unparseable replies in 1,977
calls.

**Why not DeepSeek-V3.2.** It answers a short probe and returns an empty string
on a real one, because the reasoning budget is spent before any answer token is
emitted. **This is the reason a provider gate must be probed with the real
prompt**, not a short one: length is the variable that breaks reasoning models,
so a short probe tests the one thing that cannot fail.

### 3. UNCLEAR verdicts stay INSIDE the blind region

**The choice.** When a judge declines to decide, the case counts as *not shown to
be an artifact* rather than as an artifact.

**Why.** It is the conservative direction: it keeps a case in the blind region
rather than removing it, so it cannot manufacture a correction in the project's
favour. It also makes the two arms comparable — the 2025 arm has 56 UNCLEAR
verdicts and the 2024 arm has none, so a rate computed over *committed* verdicts
is partly a rate of declining.

**Consequence to remember:** this is why **20.59%** appears beside **21.74%**.
Same numerator, different denominator, both stated. The all-cases figure is the
one used for anything comparing the arms.

### 4. The tool keeps filtering on GRADED categories; the chapters quote the adjudicated ones

**The choice.** Tab 3's persisted / now-visible / newly-hidden filter still uses
364 / 559 / 690. Chapters 5, 6 and 7 quote 268 / 510 / 569.

**Why not change the filter.** Every case in the graded queue is a real case
worth reading, and a reader who filters to "newly hidden" wants to *read the
cases*, not to be shown a smaller queue that silently drops the ones a judge
overturned. The queue is for reading; the chapters are for claiming.

**Why this is not the ISSUES #42 defect again** — a real number quoted over the
wrong population. Because the tab now carries a table saying exactly this, in the
same screen as the counts. The rule is not *never show a graded number*; it is
*never show one without saying it is graded*.

### 5. The preprint leads with the recommendation, not the warning

**The choice.** The abstract now opens on the ensemble-selection rule — blind
spots track error correlation (+0.917) and not accuracy (−0.366) across all 154
ensembles — and uses the independence violation as the setup.

**Why.** "Your guardrail is blind 2.5% of the time" leaves a reader with a
problem and no move. "Pick the ensemble with the lower error correlation, not
the higher accuracy" is a decision they can act on, and it comes from a
measurement nobody else has made. For the PhD track that is the difference
between a paper that gets cited and one that gets nodded at.

**What this costs.** The 2.5% is the more alarming number and it now appears
later. That is the trade, taken deliberately.
