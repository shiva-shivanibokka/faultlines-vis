# Task abstraction

> **Status note (2026-10-08).** Written before the 2026-09-27 deduplication; its figures (1,054, 42,551, 0.646, 364/559/690, +68%) are superseded — current figures are in the RESULTS.md claims table. The tool now has five views (a fifth, *Which ensemble?*, was added), and the six-task expert study in §5 was **not run**; the thesis evaluation is analytical (Chapter 6).

**What this file is for.** A visual-analytics contribution is judged on whether the
tool supports real tasks, not on whether the views look good. This file states
*who* uses FaultLines, *what* they are trying to find out, and *which view answers
it* — in the vocabulary of the field (Munzner's nested model; Brehmer & Munzner's
what/why/how typology) rather than in screenshots.

It is written **before** the discovery walkthroughs and the expert evaluation on
purpose: the evaluation tasks in §5 are derived from this abstraction, so the
study measures the tasks the tool was designed for instead of whatever the
interface happens to make easy.

---

## 1. Who this is for

| | who | the decision they own | why they cannot use a table |
|---|---|---|---|
| **P1** | **ML engineer shipping a system** that queries several models and compares answers | "Is disagreement a good enough guardrail to ship behind — and where will it fail silently?" | needs to see *where* the guardrail fails, not its average accuracy |
| **P2** | **Safety / evaluation researcher** studying error correlation across models | "Does the failure mode get better or worse as models improve?" | needs to compare two model generations case by case, not in aggregate |
| **P3** | **Benchmark curator** assessing whether a dataset measures what it claims | "Are these 'model errors' real, or artifacts of my answer key?" | needs to read the actual answers against the actual reference |

P1 is the primary persona. P2 and P3 emerged from the data — P2 from Finding 4b,
P3 from the discovery that a quarter of TruthfulQA's hard cases are undecidable.

---

## 2. Domain tasks — in the user's own words

| | task | persona | grounded in |
|---|---|---|---|
| **T1** | *"How much error does disagreement actually catch on data like mine?"* | P1 | RESULTS Finding 1 · per-dataset AUC 0.646–0.868 |
| **T2** | *"Show me the cases where all my models agreed and were all wrong."* | P1, P2 | the 1,054-case Audit population |
| **T3** | *"Are those failures scattered at random, or concentrated in a topic?"* | P1 | Finding 2 · blind spots cluster, and 99.5% fall outside the dataset that was supposed to hold them |
| **T4** | *"Is this a genuine model error, or is my answer key wrong?"* | P3 | 26% of TruthfulQA's low-margin cases are undecidable by a human |
| **T5** | *"If I upgrade the models, does this specific failure go away — and would I still be able to see it if it didn't?"* | P2 | Finding 4 · 364 hidden in both / 559 now visible / 690 newly hidden |
| **T6** | *"Is this the kind of failure that documents would fix?"* | P1 | Finding 5 · obscurity +68%, misconception +16% |
| **T7** | *"Is asking four models actually better than asking one four times?"* | P1 | Finding 3 · 0.864 vs 0.800 |

**The distinguishing task is T5.** T1–T4, T6 and T7 could each be answered by a
well-chosen static figure. T5 cannot: it requires holding one question fixed while
switching the model generation, and the interesting cases are individually
surprising rather than statistically summarizable.

---

## 3. Abstract tasks (Brehmer & Munzner: why / what / how)

| | **why** — action | **what** — target | **how** — method | view |
|---|---|---|---|---|
| **T1** | Analyze → *consume* → **Summarize** | attribute **distribution** (disagreement vs correctness), per subset | encode: table; **manipulate → filter** by dataset | Signal panel |
| **T2** | Search → **Locate** (target known, location unknown) | **outliers** — the agree-and-wrong set | **reduce → filter** to a flagged subset; **select** | Map (blind-spot colouring) → Inspector |
| **T3** | Analyze → **Discover** | **features / spatial distribution** — clustering vs dispersion | encode: 2-D similarity layout; **navigate**, **select** by region (brush) | Map |
| **T4** | Analyze → *produce* → **Annotate** | a **single item**, its attributes and its reference | encode: juxtaposed text; **change** state (label) | Inspector |
| **T5** | Query → **Compare** | **two attributes of one item** across a condition (generation) | **arrange → juxtapose** the two arms; **partition** by persisted/healed/emerged | Generation diff |
| **T6** | Query → **Compare** | attribute **dependency** — cause vs repair rate | encode: paired bars | Signal panel (retrieval) |
| **T7** | Query → **Compare** | **extremes** across methods on a fixed question set | encode: ranked bars | Signal panel (baseline) |

### Why these views and not others

- **T3 demands a spatial layout, not a chart.** "Are the failures concentrated?" is
  a question about *structure*, and any aggregate destroys it. The 2-D projection
  is the only encoding in the tool that can be wrong in an interesting way — and
  it earns its place because the answer (they cluster) is invisible in every table
  in RESULTS.md.
- **T2 → T4 is deliberately a two-step.** Locating the population and judging a
  single case are different tasks with different encodings; collapsing them into
  one view would mean either 1,054 unreadable rows or a detail view with no
  context.
- **T5 uses juxtaposition, not superimposition or animation.** The comparison is
  between two sets of four short text answers; the reader has to *read* both, so
  they must be simultaneously visible and separately labelled.
- **T1, T6, T7 are honestly just tables.** They are consume-level tasks with a
  handful of numbers. Making them interactive would be decoration, and saying so
  is more defensible than adding a chart to look thorough.

### Linked-view contract

```
Map ──brush(region)──▶ filters the Inspector queue
Map ──click(point)───▶ selects that case in the Inspector  (or says it is not a blind spot)
Inspector ──diff filter──▶ persisted | emerged | healed  (also re-filters the queue)
Signal panel ─────────▶ read-only context; never filters
```

Verified in the browser: a brush reducing the map to 6,927 of 42,551 points cut
the Inspector queue to 377 of 1,613 cases.

---

## 4. Scope — what the tool deliberately does NOT do

Stating this protects the evaluation: a reviewer who expects these will report
them as gaps, and a reviewer who knows they are out of scope will not.

| not supported | why |
|---|---|
| Live querying of models | the corpus is frozen; provenance matters more than freshness (ISSUES #31) |
| Editing or re-running the pipeline from the UI | the tool is for *reading* results, and a static page cannot be trusted to mutate a 287 MB parquet layer |
| Uncertainty on the 2-D layout | the projection has no error bars; positions are suggestive, and the tool must not imply otherwise |
| Statistical testing in the UI | CIs are computed in `scripts/handlabel.py --result` and reported in RESULTS.md, not invented on the fly |
| More than two model generations | 2024 vs 2025 is the comparison the data supports; the Gemma ladder that would have given a third axis is void |

---

## 5. Evaluation tasks — derived from §2, ready for the expert sessions

Each is a *task*, not a feature tour. Success criteria are stated so the session
produces data rather than impressions. Target: 35–45 minutes, 3–4 reviewers.

| | given to the reviewer | measures | task |
|---|---|---|---|
| **E1** | "You are about to ship a system that asks four models and flags disagreement. Which of the four datasets would you trust that guardrail on least, and why?" | T1 | Signal panel; expect them to find TruthfulQA 0.646 and, ideally, to question n=340 |
| **E2** | "Find a question where every model agreed and every model was wrong. Tell me what went wrong." | T2, T4 | locate → inspect; expect at least one to identify a *grading* artifact rather than a model error |
| **E3** | "Are these shared failures spread evenly across the map, or concentrated? Show me." | T3 | whether the brush is discovered without prompting |
| **E4** | "Here is a shared failure. Would upgrading your models fix it?" | T5 | the generation diff; expect surprise at 690 newly hidden > 364 hidden in both — and watch whether they notice the axis is detectability, not correctness |
| **E5** | "You have engineering budget for one intervention. Retrieval, or a model upgrade?" | T5, T6 | whether they combine two views to reach a defensible answer |
| **E6** | Open exploration, 5 min, think-aloud | — | what they look for that is not there |

**What is being measured**, stated before running it so it cannot drift: (a) task
completion without guidance, (b) whether E2 surfaces the grading-artifact insight,
(c) whether E4 changes their stated belief about upgrades, (d) every request for
something absent — that list becomes the future-work section.

**Recording:** verbatim notes per task, plus the tool's own exported labels from
E2 — a session leaves data behind, not only opinions.

---

## 6. Traceability

Every task above is answerable from a finding already in RESULTS.md, and every
panel exists to serve at least one task. Neither direction is decorative:

| view | serves | finding it makes reachable |
|---|---|---|
| Map | T2, T3 | Finding 2 — blind spots cluster, and not where predicted |
| Inspector | T2, T4 | ISSUES 1b — a quarter of TruthfulQA's hard cases are undecidable |
| Generation diff | T5 | Finding 4 / 4b — 690 emerged; errors correlate more as models improve |
| Signal panel | T1, T6, T7 | Findings 1, 3, 5 |

**Next:** the discovery walkthroughs (§ to be added) trace an actual path through
these views to a finding that was not visible in a table — the natural candidates
are Finding 2 (via T3) and Finding 4 (via T5).
