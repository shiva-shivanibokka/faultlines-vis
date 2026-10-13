# How FaultLines changed shape

> **Status note (2026-10-08).** This chronology stops at early August 2026 and its figures predate the 2026-09-27 deduplication (e.g. 0.862, 1,054, 9.0×) — they are superseded by the RESULTS.md claims table. The thesis has five research questions (RQ1–RQ5); the deck now has 26 slides. Comparisons with published AUCs on other corpora (Farquhar, Gorbett) are not like-for-like and should not be quoted.

**What this file is.** The three other records answer *what is true* (RESULTS),
*what broke* (ISSUES) and *why each choice was made* (DECISIONS). None of them
answers **"why does the project look different from the proposal?"** — and that is
the question a committee asks first.

Read it as: what was planned → what happened → what it cost → what it means.

The "planned" column comes from `../FaultLines_Project_Notes.md` (2026-07-14) and
`../FaultLines_Build_Notes.md` (2026-07-18), which are kept unedited precisely so
this comparison is evidence rather than recollection.

---

## The one-paragraph version

The proposal set out to build a hallucination detector from cross-model
disagreement and evaluate it on 300 questions, with TruthfulQA as the centrepiece
and a Postgres + FastAPI + React stack. What exists instead is a **visual-analytics
thesis** about the region that detector *cannot see*, measured on 42,591 questions
with a static single-page tool and no backend at all. Four of the proposal's own
claims reversed when measured at scale, one dataset turned out to be too small and
too ambiguous to carry a claim, one provider silently served the wrong models and
cost two entire experiment arms, and the signal the proposal was built around
turned out to be prior work rather than the contribution.

None of that was a change of mind. Each one is a measurement.

---

## 1. The contribution moved: from the signal to its blind spot

| | |
|---|---|
| **planned** | Build a detector: disagreement between models predicts hallucination. |
| **happened** | It works — **AUC 0.862**, above Farquhar 0.790 and Gorbett 0.727. And that is exactly the problem: reproducing a published effect is not a contribution. |
| **now** | The contribution is **silent consensus** — 1,054 questions where every model agreed and every model was wrong. A disagreement detector is blind there *by construction*. |

This is the single most important change in the project and it came from the
result being *too good*, not from it failing. See RESULTS Findings 2 and 4b.

## 2. Pilot-first → full corpus, because the pilot lied

| | |
|---|---|
| **planned** | 300 questions, "pilot-first: measure error correlation before writing more code." |
| **happened** | Every effect measured at 300 questions was **smaller or absent at 42,551 — five times out of five.** |
| **cost** | Four claims had to be restated, and one entire finding was withdrawn. |

| claim | at 300 questions | at full corpus |
|---|---|---|
| confidence-weighting helps | +0.008 (helps) | **+0.003** (a wash) |
| single-model beats cross-model | 0.813 vs 0.788 (single wins) | **0.862 vs 0.800** (cross wins) |
| PopQA breaks the signal | 0.761 (a worry, nearly written up) | **0.798** — it was noise |
| blind spots churn rather than persist | 20% persist (5 cases) | **39.4%** (923 cases) |

**What it means for the write-up:** the methodology chapter has to say that the
pilot's job was never to produce numbers — it was to find out whether the pipeline
ran. Every number it produced that survived did so by re-measurement, not by
inheritance.

## 3. TruthfulQA was the centrepiece; HaluEval took its job

| | |
|---|---|
| **planned** | TruthfulQA is built from shared human misconceptions, so shared model error should concentrate there. It was the natural home of the whole thesis. |
| **happened** | TruthfulQA is **340 questions** after filtering, AUC **0.646**, and hand-labelling showed **26% of its hard cases are undecidable even for a human** under its own reference answers. |
| **and** | **99.5% of the 1,054 blind spots are somewhere else.** |
| **now** | HaluEval (n=10,000, AUC 0.834, the highest blind-spot rate of any dataset) carries the statistical weight. TruthfulQA is reported with a caveat and never alone. |

**What it means:** the prediction that motivated the dataset choice was wrong, and
the wrongness is a better finding than the prediction would have been — shared
error is a general property of ensembles, not an artifact of one adversarial
benchmark.

## 4. The stack that was never built

| | |
|---|---|
| **planned** | Postgres + pgvector, FastAPI, a React tool. |
| **happened** | Parquet files on disk, and two static HTML pages with the data baked in. **Zero** of the planned infrastructure exists. |
| **why** | Nothing in the analysis needs a query planner: every stage reads one file and writes one file. A server would have added deployment, auth and uptime to a project whose evaluation depends on a reviewer being able to *open a link*. |

**What it means:** this is the cheapest-looking decision in the project and the
one that most protected the schedule. It is worth one honest sentence in the
write-up rather than being hidden.

## 5. A provider served the wrong models, and it cost two arms

| | |
|---|---|
| **planned** | Compare a 2024 ensemble against a 2025 one on hosted infrastructure. Cheap, fast, no GPU. |
| **happened** | DeepInfra answered **Gemma-2 requests with Gemma-3 weights** — 99.6% identical outputs. Mistral-7B ≈ Mistral-Small-3.2 at 89.3%. |
| **cost** | **340,728 generations voided.** Two complete arms. The RQ3 result of "52% of blind spots persist" was retracted. |
| **now** | RQ3 was rebuilt on **local Ollama weights verified by content digest** — the digest is derived from the file, so a substituted model is a different digest. Nine hours of laptop GPU. Answer: **39.4%**. |

**What it means:** "the model I asked for is the model that answered" is an
assumption, not a fact, and the write-up needs a paragraph on model provenance.
The countermeasure (`check_provider.py::identity_check`) is now a gate on every
paid run. See ISSUES #31.

## 6. RQ4 produced a clean, publishable, false answer — three times

| | |
|---|---|
| **planned** | Test whether retrieval repairs the errors. Expect it to fix obscurity and not fix misconceptions. |
| **happened** | Three consecutive runs reported **"+0% — retrieval does not fix obscurity"**, in coherent tables that would have gone straight into the thesis. |
| **cause** | The retriever was returning nothing and the harness was grading the silence. Gold-answer-in-context: **8%**. |
| **now** | With the retriever actually retrieving (70% coverage): obscurity **+68%**, misconception **+16%**. The opposite of the reported result, and a 4× dissociation. |

**What it means:** this is the strongest single argument for the project's own
methodology. A pipeline that can produce a confident wrong table three times is
the normal case; the check that caught it was not statistical, it was *"is the
answer even in the text we retrieved?"* See ISSUES #28–30.

## 7. From a scrolling explainer to a deck

| | |
|---|---|
| **planned** | A scrollytelling page walking through the pipeline level by level. |
| **happened** | Explaining from it required constant vertical scrolling, and it kept showing the **300-question pilot AUC of 0.788 in seven places** for days after the corpus run replaced it. |
| **now** | 14 fixed slides, keyboard-driven, **no scrolling anywhere**, and every number read from `summary.json` so it cannot go stale. The old page is kept at `pipeline.html`. |

**What it means:** a published artifact is a result. It now sits in the same review
loop as RESULTS.md — no figure appears on a public page unless the exporter
produced it. See ISSUES #37.

---

## 8. The RQ3 finding was restated — same numbers, different axis

| | |
|---|---|
| **reported as** | 364 still broken · 559 fixed · **690 newly broken** — a claim about *correctness* |
| **actually measured** | 364 hidden in both · 559 now visible · **690 newly hidden** — a claim about *detectability* |
| **the number that exposed it** | **78%** of the 690 were already all-wrong in 2024; they merely **disagreed**. And **52%** of the "fixed" 559 are still all-wrong |
| **cost** | none to the data — zero contradictions, nothing recomputed. The claim itself was wrong on a public page for two days |

The corrected claim is the stronger one: **newer models go blind on nearly twice
as many questions as they inherit, not by being more often wrong but by agreeing
when they are.** Capability up, detectability down — the safety argument, stated
in the terms it was actually measured in.

**What it means:** a pipeline can be entirely correct and still publish a wrong
finding, through the words above the numbers. It was caught by a person reading
individual cases in the tool — which is also the clearest evidence in the project
for the visual-analytics framing. See ISSUES watch-list 3b.

---

## What did NOT change

Worth stating, because a list of reversals can read as a project that lost its way:

- **The research questions.** RQ1–RQ4 are the ones in the proposal.
- **The core measure.** Cross-model semantic disagreement, confidence-weighted by
  `exp(mean log p)`, exactly as specified — including the white-box logprob edge.
- **Four different makers, not four sizes of one model.** The proposal's reasoning
  (shared training data guarantees shared errors) held, and the identity gate
  exists to enforce it.
- **The Audit view.** The proposal called silent consensus the interesting case
  before there was any evidence for it. There are now 1,054 instances.

The thesis answers the questions it set out to answer. What changed is the scale
at which they can be answered, which dataset can carry which claim, and — the one
real reframing — **that the finding is the blind spot rather than the detector.**

---

## Chronology

| date | event |
|---|---|
| 2026-07-14 | proposal notes: five-finding arc, TruthfulQA centrepiece |
| 2026-07-18 | build notes: pilot-first scope, Postgres/FastAPI/React planned |
| 2026-07-19 | pipeline built, 300-question pilot runs |
| 2026-07-27 | scale test: **three claim reversals** in one day |
| 2026-07-28 | full corpus, 42,591 q. SE baseline. **#31 provider substitution → 2 arms void.** RQ4 fixed on the 4th attempt |
| 2026-07-28/29 | RQ3 rebuilt locally, digest-verified, 9 h GPU. Quantization control. Context-window finding (negative) |
| 2026-07-29 | **#36** resume/column defect caught by a crash that hid a truncated statistic. 430 verdicts hand-labelled → ISSUES 1b closed, **zero open issues**. Deck + tool rebuilt and deployed. Repo created |
| 2026-08-01 | Task abstraction written. Answer-key strictness measured → 1,054 published as an **upper bound** (#39). **RQ3 restated**: the categories are about *detectability*, not correctness — found by reading the tool, not by a test (watch-list 3b) |

Measurement is complete as of 2026-07-29. What remains is the visual-analytics
evaluation and the write-up.
