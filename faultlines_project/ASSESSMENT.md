> **Read this with a date in mind.** Written before 2026-08-25. Two of its
> conclusions have since been overtaken by events and are wrong if quoted today:
> the expert evaluation is described as critical-path and blocked on recruiting
> (**it was never run** — Chapter 6 is an analytical evaluation, and PLAN 2.1
> explains the change), and the grading-artifact bound it works from is 5.6%
> (**measured at 20.6% in the 2025 arm and 15.7% in the 2024 one** — RESULTS
> Findings 11 and 12). Everything else stands. `PLAN.md` is the live list.

# FaultLines — external assessment

**Date:** 2026-08-24
**Prepared by:** Claude (Opus 5), read-only review of the repository
**Scope read:** `faultlines/` (all modules), `scripts/`, `tests/`, `config.yaml`,
`RESULTS.md`, `ISSUES.md`, `DECISIONS.md`, `AUDIT.md`, `TASKS.md`, `TODO.md`,
`EVOLUTION.md`, `DATASET_ANALYSIS.md`, `faultlines-web/*.html`,
`faultlines-web/summary.json`, and the stored parquet records under `data/`.

**What this file is NOT.** It is not a project record like `RESULTS.md`. Nothing
here was measured by the pipeline. Everything in Part 2 §4 was computed by me,
read-only, from files already on disk — the commands are given so you can
reproduce or reject any of it.

**Two questions it answers:**
1. Is FaultLines publishable, and what does a hostile reviewer attack first?
2. Which improvements serve the December thesis *and* the PhD applications, so
   the work is done once rather than twice?

---

## HOW TO READ THIS FILE

| Part | What | Read when |
|---|---|---|
| **Part 1** | Plain language. No jargon. The whole assessment in words you would use out loud. | First. Also before any conversation about it. |
| **Part 2** | The technical assessment. Numbers, statistics, file references. | When deciding what to do. |
| **Part 3** | Action ledger — the do-once list, costed and ranked. | When planning the next 15 weeks. |

Part 1 and Part 2 say the same things. Part 1 is not a summary — it is a
translation. If they ever disagree, Part 2 is correct and Part 1 has a bug.

---
---

# PART 1 — PLAIN LANGUAGE

## 1.1 What you actually built, said simply

You asked four different AI models the same 42,551 questions. Then you looked at
the cases where **all four gave the same answer and all four were wrong**.

That matters because the standard safety trick in the industry is: *ask several
models, and if they disagree, something is probably wrong*. Your project finds
the blind spot in that trick. When every model agrees on the same wrong answer,
the warning light stays off. There are 1,054 such questions in your corpus —
about 2.5%.

Then you asked the obvious follow-up: **does this get better as models improve?**
You ran the same questions through 2024-era models and 2025-era models. Newer
models made 25% fewer mistakes overall — but a *bigger share* of the mistakes
they still made were shared by all four. The problem got smaller and denser at
the same time.

That is a real finding, and it is the kind of finding a PhD admissions reader
notices.

## 1.2 Is it good enough to publish?

**Yes — as a workshop paper, today, with about twelve hours of tidying.**

Not yet as a main-conference paper. The gap is not intelligence or ambition. It
is two specific things: you have no error bars anywhere, and one variable in
your main experiment moved when it should have stayed still.

Both are fixable. I fixed the first one for you in Part 2 §4 — the numbers are
there, ready to paste in.

## 1.3 The three things a reviewer attacks first

### Attack 1: "Your four models are not independent, and your whole argument assumes they are."

Your project says, in several places, that four models from four different
companies are "four independent brains" whose mistakes are independent.

I measured whether that is true. **It is not, and it is not close.**

If the four models really failed independently, they would all be wrong on the
same question about **3%** of the time. In your data they are all wrong
**27%** of the time. That is **nine times more often than independence
predicts**.

This is the single biggest hole — and also, if you turn it around, the single
best thing in the project. Right now you assume independence and then act
surprised when it breaks. Instead, **lead with the break**:

> "Everyone builds guardrails on the assumption that different models fail
> differently. They don't — they fail together nine times more often than that
> assumption allows. And in the 2.5% where they fail *identically*, the guardrail
> is not weak, it is blind."

That is a much stronger paper than the one you have now, and it costs you a few
paragraphs, not an experiment.

### Attack 2: "You changed two things at once."

Your 2024 models were small (7–9 billion parameters). Your 2025 models were big
(17–27 billion active, and two of them are a different architecture).

So when you say "the problem gets worse with newer models," a reviewer says:
**"Or with bigger models. You can't tell which, because you changed both."**

You already spotted this — it's in `DECISIONS.md` from July, credited to you.
You designed a fix (the Gemma ladder). The fix ran and was destroyed because the
hosting provider quietly served the wrong models. That is bad luck, not bad
work.

Two ways out, and either is fine:

- **Fix it.** Run a 2024-era arm at the *big* size. Costs about **$5** and
  **three hours**. Uses code you already have.
- **Reframe it.** Say what you actually measured: *"when teams upgrade, they get
  newer AND bigger models together, and the shared-failure share rises."* That
  is honest, it is the thing practitioners actually experience, and it costs
  nothing.

**If the thesis is at risk in November, reframe. Do not put graduation at risk
for a $5 experiment.**

### Attack 3: "Only one person decided what counts as a wrong answer."

You hand-checked 430 cases. You did it blinded, in two groups, properly. That
part is genuinely well designed.

But you are one person. For a paper that claims to say what a real error is,
reviewers want a second human to check some of the same cases and see whether
you agree.

**Fix:** ask a labmate to do 100 of them. One sitting. The tool is already built
and already hides the answers from the labeller. This closes the objection
permanently and cannot be added after the fact.

## 1.4 The statistics — what survived and what didn't

You had no error bars. I computed them. Here is the plain version.

**Survived, comfortably — these are real:**

- Shared blind spots went up (2.17% → 2.48%). Real. The odds of seeing this by
  chance are about 1 in 4,000.
- The share of errors that are shared went up by half (4.5% → 6.8%). Real, and
  the measurement is *tight* — this is your strongest number.
- Disagreement predicts errors well (AUC 0.862). Real.
- Asking four models beats asking one model four times. Real, and the gap is
  solid.
- Giving a model a document fixes "it never knew this fact" but mostly not "it
  believes something false." **The contrast between those two is the robust
  result** — much more so than either number on its own.

**Survived, but shakier than you've been saying:**

- The "misconception" arm has only 70 questions. The true effect is somewhere
  between +3% and +29%. That is a tenfold range. Never quote "+16%" on its own.
- Every TruthfulQA number sits on 340 questions and has an error bar four times
  wider than your other datasets. Always attach it.

**Did not survive — this one you need to change:**

- In the search experiment (131 questions), Wikipedia scored 26% and open web
  scored 29%. **That difference is noise.** There is no real gap between the two
  tools.
- **But the actual finding there is better anyway:** *neither* tool fixed
  **68%** of the cases. Giving the model a search engine does not rescue it from
  this failure mode, no matter which search engine. That result is solid and
  interesting. Lead with it and drop the tool comparison.

## 1.5 Your two confidence numbers are not contradictory

You were worried about this. You're right, and the data backs you up.

- **Number one:** in the region where all models agree, the model's own
  confidence still separates right from wrong a bit (AUC 0.600).
- **Number two:** but confidence averages 0.948 when right and 0.930 when wrong
  — almost the same, and no cutoff works.

These are not in conflict. One is about **ranking** ("is the wrong answer
usually *less* confident?" — yes, slightly). The other is about **cutting**
("can I draw a line?" — no).

Here is the sentence that makes it undeniable:

> If you refuse to answer whenever confidence is below 0.941, you catch **half**
> the errors — but you also throw away **a third of your correct answers**, and
> only **1 in 10** of the things you refused was actually wrong.

Real signal. Useless margin. One finding, and it is the answer to the most
common suggestion you get ("just make it say I don't know").

## 1.6 Which paper to write

Your project has two personalities:

- **The tool personality.** Four linked views, a proper task analysis, a
  labelling workspace. This is visualization research. It belongs at IEEE VIS.
- **The finding personality.** Shared failures harden as models improve. This is
  machine learning / NLP research. It belongs at an ICLR workshop.

**Which is better built?** The tool. Your `TASKS.md` is real visualization
scholarship, not decoration.

**Which should you submit?** The finding. Three reasons:

1. The tool's evidence isn't in yet — the expert evaluation hasn't happened, and
   without it a VIS paper is a system description.
2. VIS deadlines are around March 2027, after your applications.
3. **The professors you're targeting are NLP people.** A visualization paper
   reads to them as next door. The finding reads as their field.

Write **one** preprint, in the finding framing, with the tool as your method.
Keep `TASKS.md` for the thesis, where it is a strong design chapter. Do not try
to write both papers this autumn.

## 1.7 The thing that actually matters for applications

Nothing you write will be published before your December deadlines. You know
this.

So the thing that does the work is **a preprint on arXiv with a link, by around
20 November 2026.** A faculty member clicks it, reads two pages, and forms an
opinion. That is the whole mechanism.

What makes yours land, and what most applicants do not have:

- **A prediction you made that turned out wrong**, recorded as wrong. You
  predicted the blind spots would cluster in TruthfulQA. 99.5% of them are
  somewhere else.
- **Two experiments you threw away.** 340,728 model answers, executed perfectly,
  binned because the provider served the wrong models. You quarantined them with
  a README explaining why. Most people would have published them.
- **A defect log of 52 bugs**, grouped by *class* rather than by date, with the
  lesson extracted from each.

Those three things say "this person can be trusted with a measurement" more
loudly than any accuracy number. Put them in the writeup. Do not bury them in an
appendix.

## 1.8 What to do about the website

Your `pipeline.html` page still describes the project you *planned*, not the one
you *ran*. It says three datasets (there are four), names a benchmark you never
used, describes the models running on your laptop (the main run was on a rented
server), and — worst — it shows a model comparison where both sides are the same
size.

That last one matters, because **the size mismatch is exactly the thing a
reviewer is going to question**. The page appears to promise the control you
don't actually have. Anyone who reads the page and then the results will think
you're hiding it.

Full list in Part 2 §3. This is a few hours of editing, and it's high priority
because the page is public and linked.

---
---

# PART 2 — TECHNICAL ASSESSMENT

## 2.1 Research standing

**Verdict: a strong ICLR-workshop paper today; Findings-tier with ~3 weeks of
targeted work; not main-conference this cycle.**

What is genuinely research-shaped:

- A question that is not a benchmark-chase: *where does the disagreement
  heuristic structurally fail, and does that region grow with capability?*
- A **controlled paired design** — 42,551 identical qids through both arms,
  exact counts, no stratified reweighting, no sampling error in the RQ3
  quantities.
- **A falsified prior prediction, recorded as falsified** (99.5% of blind spots
  outside TruthfulQA).
- **340,728 generations voided and quarantined** (`data/void/`) after ISSUES #31
  — the provider served gen-3 weights under gen-2 names, 99.6% identical
  answers. The countermeasure (`check_provider.py::identity_check()`, then
  content-digest verification via Ollama) is stronger than the failure.
- A retracted headline (RQ3 "52% persist", 448/860) superseded by a
  digest-verified rerun.
- `ISSUES.md` grouped by defect *class* with four standing rules extracted.

The deficit is **statistical hygiene** and **one uncontrolled variable**.

### Hostile-reviewer objections, ordered

**#1 — The independence premise is empirically false by ~9×, and the framing
rests on it.**

Computed from `data/interim/answers.parquet`, 42,551 questions:

| pair (2025 ensemble) | φ | Jaccard |
|---|---|---|
| Qwen3-235B \| gemma-3-27b | 0.650 | 0.656 |
| Qwen3-235B \| Llama-4-Maverick | 0.662 | 0.654 |
| Qwen3-235B \| Mistral-Small-3.2 | 0.673 | 0.673 |
| gemma-3-27b \| Llama-4-Maverick | 0.653 | 0.656 |
| gemma-3-27b \| Mistral-Small-3.2 | 0.706 | 0.723 |
| Llama-4-Maverick \| Mistral-Small-3.2 | 0.661 | 0.662 |
| **mean pairwise φ** | **0.667** | |

Per-model error rates: Qwen3-235B 38.372% · gemma-3-27b 45.951% ·
Llama-4-Maverick 38.008% · Mistral-Small-3.2 44.794%.

```
observed  P(all four wrong)                26.888%
predicted P(all four wrong) if independent  3.002%
CONCORDANCE RATIO                              9.0x
```

`pipeline.html` L2 asserts *"four independent brains, so their mistakes are
independent."* `pipeline.html` L2 `note` even says to measure pairwise error
correlation before trusting the method — it was never reported.

**Reframe as the contribution.** The heuristic's premise fails by 9×; the
residual 2.5% is where it fails totally. Put the 9.0× in the abstract.

**#2 — Generation/scale confound.** See §2.2.

**#3 — Ensemble size is arbitrary and the headline quantity is size-sensitive.**
Exact-match agreement proxy (lower bound on meaning-agreement), same corpus:

| ensemble | silent-consensus rate |
|---|---|
| 4 models | **2.033%** |
| 3 models — drop Qwen3-235B | 3.043% |
| 3 models — drop gemma-3-27b | 2.848% |
| 3 models — drop Llama-4-Maverick | 3.127% |
| 3 models — drop Mistral-Small-3.2 | 2.881% |
| *3-model mean* | *2.975%* |
| 2 models (six pairs) | 5.177% – 6.889% |
| *2-model mean* | *5.659%* |

You already know this mechanism — it is why gen-1 was dropped (3 makers vs 4).
No reviewer accepts *n*=4 without the curve. Costs one re-clustering pass, zero
new generations. NOTE: the full meaning-clustered version of this ablation
exceeded a 10-minute budget when I attempted it; run it as a background job.

**#4 — Single annotator, no inter-rater agreement.** 430 verdicts, blinded, two
strata, κ reported against the *machine* (0.959 control / 0.322 target). No
second human. `pipeline.html` L14 admits it.

**#5 — The cross-paper AUC comparison.** `RESULTS.md` claim 1 caveat: *"Beats
Farquhar 0.790 / Gorbett 0.727."* Different corpora, models and graders. **Cut
it.** The within-study baseline (§2.4) is defensible and strong.

**#6 — Semantic Entropy at n=4 samples.** Matched-budget is principled and well
argued, but Farquhar uses ~10. Pre-empt in text; optionally add an n=10 arm on
one model.

**#7 — RQ2 popularity control mixes neighbourhoods across datasets.** Your own
`AUDIT.md` note n1: density computed over all datasets, then subset to PopQA, so
a PopQA question's neighbours may be TruthfulQA questions. RQ2 is the finding
that defuses Kandpal 2023 — do not leave this open.

**#8 — Silent consensus partly a grading artifact.** Already bounded at ≤5.6%
(59/1,054) with the reasoning for why no threshold fixes it (the encoder ranks
`"Henley Rowing Club" vs "Leander Club"` at 0.781 above `"Sheppey" vs "Isle of
Sheppey"` at 0.526). This is **defended**, not exposed. Lead with it.

---

## 2.2 The scale confound

### What the records actually contain

| arm | models | scale | precision | provider | n |
|---|---|---|---|---|---|
| 2024 `_rq3local` | Llama-3.1-8B · Qwen2.5-7B · Mistral-7B-v0.3 · Gemma-2-9B | **7–9B dense** | local 4-bit | Ollama, RTX 4060 8 GB | 42,551 |
| 2025 headline | Llama-4-Maverick · Qwen3-235B · Mistral-Small-3.2 · Gemma-3-27B | **17–27B active, 2 MoE** | hosted, mixed / FP8 | DeepInfra | 42,551 |

Verified: `records.parquet` and `records_rq3local.parquet` share an identical
qid index (42,551 rows each). Counts are exact.

**Three variables move together:** generation, scale, serving precision/provider.
Precision is *partially* controlled (`_rq3local_q8`, 2,554 questions, Jaccard
0.780 — safe for rates, not for a specific question). Generation and scale are
not controlled at all.

`DECISIONS.md` 2026-07-27 records the confound, credited to you, with the
designed fix (Gemma 2×2 ladder). The ladder ran on DeepInfra and was voided —
gemma-2-27b was served as gemma-3-27b, gemma-2-9b as gemma-3-12b; 2 of 4 cells
were duplicates.

**Note the ladder would not have fixed the headline claim anyway.** As configured
(`ensemble_gemma_ladder`) it compares four Gemma variants as *single models*. It
separates generation from scale for **accuracy**; silent consensus is an
ensemble-level construct requiring four makers. It answers an adjacent question.

### Can a size-matched arm be run from existing code?

**Yes — a config block plus four CLI invocations. No new code.**

Already parameterised:
- `generate.run(ensemble=, tag=)` — `generate.py`, selects the config block
- `--tag` threaded through `grade` / `nli` / `disagree` (AUDIT M3 fix)
- `track.run(pilot=, old_tag=, new_tag=)` — `track.py`
- `check_provider.py --ensemble <key>` — defaults to the key `generate.py` uses

```bash
python scripts/check_provider.py --ensemble ensemble_2024_large
python -m faultlines.generate --ensemble ensemble_2024_large --tag _big24 --full
python -m faultlines.grade    --tag _big24 --full
python -m faultlines.nli      --tag _big24 --full
python -m faultlines.disagree --tag _big24 --full
python -m faultlines.track --full --old-tag _big24 --new-tag ""
```

**The obstacle is model availability, not code.** Meta has no 2025-generation
small dense model — Llama 4 starts at 17B active and is MoE-only. `config.yaml`
already states this: *"A size-matched all-DENSE four-maker set does not exist
among models that serve logprobs."* RQ3 needs no logprobs (agreement +
correctness only), which widens the field, but not for Meta.

**Better design — size-match upward, not downward.** Add a **2024-generation arm
at 24–27B**, hosted on the *same provider* as the 2025 arm:

| contrast | isolates |
|---|---|
| 2025-big vs **2024-big** | **generation**, scale roughly fixed, provider fixed ← the claim |
| **2024-big** vs 2024-small | **scale**, generation fixed |

Candidates: Qwen2.5-32B, Gemma-2-27B, Mistral-Small-2409-22B, Llama-3.1-70B.
Llama-3.1-70B is a size mismatch inside that arm — state it, don't hide it.
Run `identity_check()` first; ISSUES #31 is the reason this arm exists.

### Cost

| route | generations | wall clock | cost |
|---|---|---|---|
| **Hosted, full corpus, 4 models** | 170,364 | **~1.8–3 h** at 24 workers (your measured 25.9 gen/s) | ~13M tokens → **≈ $1–6** |
| Hosted, stratified subset (1,054 silent + 1,500 control) | 10,216 | ~7 min | **< $0.50** |
| Local Ollama, full corpus | 170,364 | **see warning** | $0 |
| Rented A100/H100 + vLLM | 170,364 | ~1.5–3 h | ~$3–8 + setup |

Storage: ~34 MB answers + ~5.5 MB records per arm. Non-issue.

**Do not rent a GPU.** For 7–27B models this is an API job costing less than
lunch. vLLM setup, weight downloads and a billing meter buy you nothing here.

**Verify current provider pricing before committing** — I cannot check live
rates, and hosted catalogues churn (that is ISSUES #31's whole lesson).

> ### ⚠ Your local-throughput figures contradict each other by 20×
>
> `RESULTS.md:243` — the 170,364-generation local run took *"~9 hours of laptop
> GPU"* (= 5.26 gen/s).
> `scripts/build_rq3_local.py` — uses a **measured 0.24 gen/s**, which puts the
> same run at **197 hours**.
>
> On an RTX 4060 8 GB, 7–9B at 4-bit, one model at a time, 64-token outputs,
> ~9 hours is not plausible. Time 200 generations (15 minutes) before planning
> anything local — and fix whichever number is wrong before a reviewer reads the
> reproducibility section.

### Recommendation

Run the 2024-big hosted arm **if the thesis is on track by early November**
(~3 h, ~$5). Otherwise **reframe**:

> "As deployed ensembles are upgraded — which in practice means newer *and*
> larger — the share of errors that are shared rises 1.52× (95% CI 1.42–1.63)
> while the overall error rate falls 25%."

Honest, exactly what was measured, practitioner-relevant, free. The size-matched
arm then becomes a named, costed, one-paragraph future-work item, which reads as
command of the design rather than a hole.

---

## 2.3 Documentation drift

All items are `faultlines-web/pipeline.html` unless noted.

**Clean:** the results deck (`index.html`) — it reads from `summary.json`.
`walkthroughs.html`, `RESULTS.md`, `ISSUES.md`, `DECISIONS.md`, `config.yaml`,
`TASKS.md` — all consistent with the data. Drift is concentrated in the pipeline
page, which appears frozen at the pre-pivot design.

### Datasets

| # | location | says | actually |
|---|---|---|---|
| D1 | L1 kicker, `io`, canvas | "Three datasets" / "3 datasets · by role" | **four**: PopQA, TriviaQA, HaluEval, TruthfulQA |
| D2 | L1 `tips.i`, `why`, canvas row 2 | **AbstentionBench** as misconception arm | never used — rejected on schema (ships a `datasets` script, unsupported in `datasets>=4`) |
| D3 | L1 canvas | TriviaQA and HaluEval **absent** | they carry the statistics: TriviaQA n=17,944, HaluEval n=10,000 |
| D4 | L1 `why` | "SimpleQA dropped — 91% of ensemble answers wrong" | 91% was the 7–9B local ensemble; hosted was 74.6%. `config.yaml` records it was dropped for *size*, not the floor effect |
| D5 | L14 note | "sourcing from **all three datasets**" | four |
| D6 | L1 `tips.p` | silent consensus **"~1.7%"** | 2.48% (2025) / 2.17% (2024) |

### Model roster

| # | location | says | actually |
|---|---|---|---|
| M1 | RQ3 level canvas | **"gen 2 · current"** = Llama-3.1 · Qwen-2.5 · Mistral-0.3 · Gemma-2 | that is the **old** arm; current is Llama-4-Maverick · Qwen3-235B · Mistral-Small-3.2 · Gemma-3-27B |
| M2 | RQ3 level canvas | **"gen 1 · older"** = Llama 2 7B · Qwen 1.5 7B · Mistral 0.1 | gen-1 was **dropped** (3 makers, 4-bit, unfixable). Appears nowhere in results |
| M3 | RQ3 level `tools` | "Ollama · **Gen-1 ensemble**" | comparison is gen-2-local vs gen-3-hosted |
| M4 | L2 `io` | "4 open models, one at a time, **4-bit**" | headline arm is hosted, 24 concurrent workers |
| M5 | L2 `tips.p` / `narr` / `note` | "8 GB fits only one"; "on a **laptop GPU**"; "**Black-box APIs never expose** this" | headline run is a black-box API that *does* expose logprobs — which is why the pivot was possible |
| M6 | L2 `tools` | "Ollama · 4-bit GGUF / RTX 4060 · 8 GB" | DeepInfra |
| M7 | L14 risk register | "All four models run 4-bit so they fit a single laptop GPU" | only the 2024 arm |

> **M1–M3 are the priority.** They make the page describe a *size-matched*
> comparison (7B vs 7–9B) that was never run — precisely the claim under
> question. A reader who opens the page and then `RESULTS.md` will conclude the
> confound is being concealed.

### Annotation

| # | location | says | actually |
|---|---|---|---|
| A1 | L9 `io`, canvas, `why` | "~250 rows" / "About 250 hand labels" | **430** verdicts |
| A2 | L9 canvas | "learns from your 250 tags, then **types the remaining thousands automatically**. About 50 of its guesses are spot-checked" | **no classifier was ever built** — no mention in RESULTS or DECISIONS. RQ4 strata are rule-based (rarest PopQA entities / TruthfulQA errors) |
| A3 | L9 `why`, L14 | labels are *cause* tags (obscurity / staleness / misconception) anchoring RQ1 and RQ4 | the 430 are **grader-agreement verdicts** on TruthfulQA closing ISSUES 1b — a different purpose |

### Method

| # | location | says | actually |
|---|---|---|---|
| P1 | L1 `narr`, `tips.p/o` | screening: run over a large pool, **"grade just those"**, keep "a few hundred all-agree cases" | full corpus generated **and graded** — 42,551 questions, 170,364 answers. `screen.py` was built and tested on 15 questions, not used for the headline |
| P2 | RQ3 `note` | "Run on the **non-adversarial subset only**" | run on the full corpus; the non-adversarial filter applies to TruthfulQA only |
| P3 | L6 `why` | "0.74 is only impressive next to something" | pilot-era placeholder; the number is 0.862 |
| P4 | L2 `note` | pairwise error correlation "worth measuring on a small slice before committing" | never reported. It is **0.667** — see §2.1 |

---

## 2.4 Statistics

Computed read-only from stored records. Reproduce with the project venv:
`C:\venvs\faultlines\Scripts\python.exe`. Sources: `records.parquet`,
`records_rq3local.parquet`, `rq1_confidence.parquet`, `rq4_retrieval.parquet`,
`baseline.parquet`, `answers.parquet`.

### Survives comfortably

| claim | statistic | verdict |
|---|---|---|
| Blind-spot rate 2.17% → 2.48% | McNemar exact, paired n=42,551, discordant 559 healed / 690 emerged, **p = 2.32×10⁻⁴**; Δ = **+0.308%** [+0.145%, +0.471%] | real |
| Shared-error share 4.5% → 6.8% | 4,000 paired bootstrap: Δ = **+2.33%** [+1.92%, +2.76%]; relative **1.518×** [1.418, 1.629]; p < 1/4000 | **real, and tight — your strongest number** |
| Headline AUC | **0.8617**, 95% CI [0.858, 0.866] (Hanley–McNeil) | real |
| Cross-model beats single-model SE | cross 0.8615 vs best single SE 0.8002 (Mistral-Small-3.2); Δ = **+0.0613** [+0.0523, +0.0700], paired bootstrap on 8,000 same qids, p < 1/4000 | real |
| RQ4 obscurity | n=500, 4.0% → 71.8%, lift **+67.8%** [+60.5%, +75.1%], 344 fixed / 5 broken, McNemar **p = 7.4×10⁻⁹⁵** | overwhelming |
| **RQ4 dissociation** | **+52.1%** [+39.1%, +65.0%], 10,000 bootstrap, p < 1/10000 | **this, not either arm alone, is the robust claim** |
| Blind-spot count | 1,054 = 2.477% [2.334%, 2.629%] Wilson | fine |

Other single-model SE baselines, same 8,000 qids: Qwen3-235B 0.7547 ·
Llama-4-Maverick 0.6931 · gemma-3-27b 0.6616.

### Survives but weakly — restate

**RQ4 misconception arm, n=70.** 27.1% → 42.9%, lift **+15.7%**, 95% CI
**[+2.9%, +28.5%]**, discordant 16 fixed / 5 broken, McNemar **p = 0.027**.
Significant, but the interval spans a tenfold range of effect sizes.

> Quote as: *"partly repaired, +16% (95% CI 3–29%, n=70)"* — never "+16%" bare.

### Does not survive

**RQ5 search arm, n=131 matched:**

| | count | rate | 95% CI (Wilson) |
|---|---|---|---|
| Wikipedia tool | 34/131 | 26.0% | [19.2%, 34.1%] |
| Open web | 38/131 | 29.0% | [21.9%, 37.3%] |
| **Neither** | 89/131 | **67.9%** | **[59.5%, 75.3%]** |

Discordant: 8 web-only, 4 wiki-only → **McNemar exact p = 0.388.**
**The web-vs-wiki difference is noise.** Any framing of "the comparison IS the
finding" as a *difference between tools* must change.

**What survives is better:** *neither* tool repaired 67.9% [59.5%, 75.3%] of
matched cases. Agentic retrieval does not rescue silent consensus regardless of
tool. Well-powered, tight, and interesting. Lead with it.

### Per-dataset AUC (Hanley–McNeil)

| dataset | n | AUC | 95% CI | width |
|---|---|---|---|---|
| triviaqa | 17,944 | 0.868 | [0.859, 0.878] | 0.020 |
| halueval | 10,000 | 0.834 | [0.826, 0.842] | 0.016 |
| popqa | 14,267 | 0.798 | [0.791, 0.806] | 0.014 |
| **truthfulqa** | **340** | **0.646** | **[0.570, 0.722]** | **0.152** |

TruthfulQA's interval is ~10× wider and its lower bound approaches 0.5. Attach
the CI to every TruthfulQA number — you already do this for the hand-label
delta (+0.061 [+0.018, +0.109]); extend the habit.

---

## 2.5 The two confidence numbers — one finding

**They are not contradictory, and the code supports stating it as one finding.**

- **AUC 0.600** — threshold-free *ranking*: P(a wrong answer is less confident
  than a right one).
- **0.948 vs 0.930** — *separation on an absolute scale*, which is what a
  threshold must exploit.

From `rq1_confidence.parquet`, agreement region n = 17,664 (1,168 wrong /
16,496 right, base rate 6.61%):

```
AUC 0.5998    95% CI [0.582, 0.617]    z vs 0.5 = 11.1
Mann-Whitney U  p = 1.82e-30           Cohen's d = 0.439
P(a random wrong answer is MORE confident than a random right one) = 40.0%
```

Real beyond dispute — 11 standard errors from chance. And unusable as a gate:

| threshold | abstains | errors caught | correct destroyed | precision | lift over 6.61% base |
|---|---|---|---|---|---|
| 0.900 | 1,546 | 270 (23%) | 1,276 (8%) | 17.5% | 2.64× |
| 0.930 | 4,250 | 480 (41%) | 3,770 (23%) | 11.3% | 1.71× |
| **0.941** | **5,966** | **585 (50%)** | **5,381 (33%)** | **9.8%** | **1.48×** |
| 0.950 | 7,840 | 662 (57%) | 7,178 (44%) | 8.4% | 1.28× |
| 0.970 | 12,963 | 904 (77%) | 12,059 (73%) | 7.0% | 1.05× |
| 0.990 | 17,001 | 1,125 (96%) | 15,876 (96%) | 6.6% | 1.00× |

**Publishable phrasing:**

> "Confidence carries real signal in the region where disagreement carries none
> by construction (AUC 0.600, 95% CI [0.582, 0.617], p < 10⁻³⁰). But the region
> is 93% correct answers and the distributions overlap heavily (d = 0.44): a
> threshold catching half the errors abstains on a third of correct answers and
> is still only 9.8% precise against a 6.6% base rate. The signal is real; the
> margin is not operational."

This pre-empts "just make it say I don't know" — which your own docs call the
most common suggestion the project receives.

---

## 2.6 Venue

**The artifact better supports VIS. The stronger paper to submit is the ML one.**

### Why the artifact supports VIS

`TASKS.md` is real VIS scholarship, not a retrofit:
- three grounded personas (P1 ML engineer, P2 safety researcher, P3 benchmark
  curator), with P2/P3 emerging *from the data*
- seven domain tasks, each traced to a specific finding
- a complete Brehmer & Munzner why/what/how table
- an explicit linked-view contract with a verified number (brush to 6,927 of
  42,551 points cut the inspector queue to 377 of 1,613)
- a scope section naming what the tool deliberately does **not** do
- a six-task evaluation protocol with success criteria **fixed before running**
- it argues against itself: *"T1, T6, T7 are honestly just tables. Making them
  interactive would be decoration."*

**T5 is a genuine visualization contribution.** Holding one question fixed while
switching model generation, where the interesting cases are individually
surprising rather than statistically summarisable, is a thing no static figure
can do.

### Why the ML paper is the one to submit

1. **The VIS evidence is not in.** The expert evaluation hasn't run; `TODO.md`
   #3 marks it critical-path, blocked on recruiting. Without it a VIS paper is a
   system description. With n=3–4 it is a short paper, not a full one.
2. **VIS deadlines are ~March 2027**, after your applications.
3. **Your target faculty are NLP/ML.** Bansal, Stengel-Eskin, Neubig, Fried. A
   VIS paper reads as adjacent; the ML finding reads as their field, in their
   vocabulary — faithfulness, uncertainty calibration, pre-deployment
   evaluation.

**One preprint, ML framing, instrument as method.** Keep `TASKS.md` intact for
the thesis design chapter and a post-graduation VIS short paper. Do not write
both this autumn.

---
---

# PART 3 — ACTION LEDGER

## 3.1 The do-once list — work that serves BOTH the thesis and the applications

This is the section you asked for. Every row below is **required or clearly
beneficial for the December thesis** *and* **directly strengthens the preprint**.
Doing these once means not redoing them.

| | work | hours | serves thesis | serves PhD | notes |
|---|---|---|---|---|---|
| **1** | **CIs / significance everywhere** (§2.4 done — paste in) | 3–4 | ✅ results + limitations chapters | ✅ removes the largest structural weakness | Best ratio in the list. Also kills the RQ5 tool-comparison claim before a reviewer does |
| **2** | **Reframe independence violation as the finding** (φ=0.667, 9.0×) | 3–4 | ✅ strengthens the thesis argument | ✅ becomes the abstract | Upgrades the thesis, not just the paper |
| **3** | **Fix `pipeline.html` drift** (§2.3), M1–M3 first | 4–6 | ✅ it is a submitted artifact | ✅ publicly linked | Page currently advertises a control you don't have |
| **4** | **Real limitations section** — confound, independence, ≤5.6% key artifact, single annotator, n=70, n=340, ensemble size | 4–6 | ✅ **required chapter** | ✅ the section that most changes a PhD reader's rating | Material already exists, scattered across ISSUES/RESULTS |
| **5** | **Second annotator, 100 of the 430**, report Cohen's κ | 5–8 (mostly theirs) | ✅ defensible under examination | ✅ closes objection #4 | `handlabel.py` is already blinded and resumable. **Cannot be added retroactively** |
| **6** | **Ensemble-size ablation** (4→3→2) | 4–6 | ✅ threats-to-validity | ✅ closes objection #3 | Re-clustering only, no new generations. Run as a background job |
| **7** | **Expert evaluation** (`TASKS.md` §5) | 2 days + scheduling | ✅ **CRITICAL PATH — thesis requires it** | ✅ enables the later VIS paper | Already the #1 item in `TODO.md`. Moves at other people's calendar speed — start recruiting now |
| **8** | **RQ2 density within PopQA only** | 2–3 | ✅ fixes a real methodological hole | ✅ closes objection #7 | `AUDIT.md` n1 |
| **9** | **Restore related-work material** (`TODO.md` #1) | 2–3 | ✅ **blocked chapter** | ✅ preprint needs it | `git checkout f41d989 -- version-1/...` |

**Total for rows 1–6, 8, 9: roughly 28–40 hours of your time**, plus row 7 which
was already on the critical path.

## 3.2 PhD-only — do after the thesis is safe

| | work | hours / cost | when |
|---|---|---|---|
| **10** | **2024-generation arm at 24–27B**, same provider | ~3 h wall clock, **~$5**, ~2 h of your time | Only if the thesis is on track by early November. Otherwise reframe (§2.2) |
| **11** | **Post the preprint to arXiv** (cs.CL, cross-list cs.HC) | 2–3 h | **By ~20 November 2026**, regardless of state |
| **12** | **Plain-text 2-page writeup for cold emails** | 8–10 h | Alongside the preprint |
| **13** | **SE baseline at n=10** on one model | ~1 h, < $2 | Optional; pre-empt in text if skipped |

## 3.3 Explicitly do NOT do

| | why |
|---|---|
| Rent an A100/H100 | This is a $5 API job. vLLM setup + weight downloads + a billing meter buy nothing |
| Run the Gemma 2×2 ladder | As configured it compares single models; cannot address the ensemble-level claim. Good idea, different question |
| Build the cause classifier `pipeline.html` L9 describes | It was never built and is not needed. Delete the claim instead |
| Write two papers | One preprint, ML framing |
| Chase a main-conference deadline this cycle | The work isn't there, and a rejection inside your applications window helps nothing |
| Quote "Beats Farquhar 0.790 / Gorbett 0.727" | Different corpora, models, graders. Free shot for a reviewer |

## 3.4 Open questions to resolve before planning

1. **Local throughput: 9 hours or 197 hours?** Time 200 generations. 15 minutes,
   settles a 20× discrepancy in a reproducibility claim. (§2.2)
2. **Is the thesis on track as of ~1 November?** This is the single gate that
   decides whether row 10 happens or the reframing does.
3. **Who is the second annotator?** Row 5 needs a name, not a plan.
4. **Current provider pricing** — verify before committing to row 10.

## 3.5 The one-paragraph summary

Yes, this is publishable at workshop tier, today, with about twelve hours of
statistics and framing work. What you have that most workshop submissions do not
is a controlled paired design at real scale, a prediction that failed and was
recorded as failing, two arms you voided and quarantined rather than published,
and a defect log that reads like someone who has internalised why measurement is
hard. What you are missing is confidence intervals — now computed, in §2.4 — a
second annotator, and one controlled variable that costs about five dollars to
fix and which you can honestly reframe if the thesis needs the time. **Nothing
here reads like someone who can only build.** Say so plainly in the writeup, and
make sure the limitations section is the one a reader remembers.

---

## Appendix — reproducing the computed statistics

All figures in §2.1 and §2.4 came from read-only reads of existing parquet files
using the project venv. Nothing was written. The relevant sources:

| statistic | file(s) |
|---|---|
| pairwise φ, error rates, concordance ratio | `data/interim/answers.parquet` |
| ensemble-size ablation (exact-match proxy) | `data/interim/answers.parquet` |
| McNemar on blind-spot rate; shared-share bootstrap | `data/processed/records.parquet` + `records_rq3local.parquet` |
| headline + per-dataset AUC CIs | `data/processed/records.parquet` |
| baseline paired bootstrap | `data/interim/baseline.parquet` + `records.parquet` |
| RQ4 McNemar + dissociation bootstrap | `data/processed/rq4_retrieval.parquet` |
| RQ5 Wilson intervals + McNemar | `faultlines-web/summary.json` (`rq5` block) |
| RQ1 AUC CI + abstention economics | `data/processed/rq1_confidence.parquet` |

Bootstraps used `numpy.random.default_rng` with fixed seeds (42, 7, 11) and
4,000–10,000 resamples. AUC intervals use Hanley–McNeil; proportion intervals
use Wilson; paired binary comparisons use exact McNemar (`scipy.stats.binomtest`
on the discordant pairs). `statsmodels` is **not** installed in the project venv
— Wilson intervals were computed directly.
