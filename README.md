# FaultLines

**A visual-analytics tool for the place where asking several language models stops
working — when they all agree, and all of them are wrong.**

M.S. Data Science & Artificial Intelligence capstone · San Francisco State University · VI-Lab
Shivani Bokka · advisor Dr. Shahrukh Humayoun

**Live:** [slide deck](https://faultlines-peach.vercel.app) ·
[the tool](https://faultlines-tool.vercel.app) ·
[discovery walkthroughs](https://faultlines-peach.vercel.app/walkthroughs.html) ·
[pipeline explainer](https://faultlines-peach.vercel.app/pipeline.html)

---

## The idea in one paragraph

Published work says that if several language models disagree about an answer, one
of them is probably hallucinating — so disagreement makes a useful warning light.
That reproduces here at **AUC 0.840** over 34,062 distinct questions. It is not
the contribution, and it is not compared against published figures from other
corpora; the within-study comparison is in the table below.

The contribution is the region the signal cannot see. When every model makes the
**same** mistake, there is no disagreement to detect — perfect consensus, high
confidence, wrong answer. This project measures that region (**950 questions**,
*silent consensus*, or blind spots), shows that it does not shrink when a 2024 ensemble is
replaced by a 2025 one, and builds the tool that finds it.

## Headline results

*Re-derived 27 Sep 2026 on the deduplicated corpus after an adversarial review
(`faultlines_project/ISSUES.md` #66–#78). Every figure is read from
`faultlines-web/summary.json`; the full list, with intervals and caveats, is the
claims table at the top of `faultlines_project/RESULTS.md`. Earlier figures
(0.862, 1,054, 9.0×) are superseded.*

| | |
|---|---|
| Corpus | 42,591 asked → 40 ungradeable → 8,489 duplicate questions removed → **34,062 analysed** (136,248 graded answers per arm) |
| Cross-model disagreement | **AUC 0.840** [0.836, 0.845] |
| vs best single-model Semantic Entropy | **0.838 vs 0.778**, Δ +0.060 [+0.050, +0.070], same 6,436 questions, same budget |
| The independence assumption | models from different developers are assumed to make mistakes independently. They do not: within the same dataset, all four are wrong together **3.3×** as often as independence predicts |
| Shared blind spots found | **950** (2.79%) — an upper bound: 21.05% are answer-key artifacts (750 genuine). 99.5% are *not* in the misconception dataset |
| Errors across a model upgrade (2024 → 2025 ensemble) | 53.45% → 41.08% wrong, but the share of errors that are shared rises **4.52% → 6.79%** (1.50× [1.39, 1.62]), grader's count. The *number* of blind spots does not rise significantly once answer keys are re-checked: 698 → 750 genuine, exact McNemar p = 0.101 |
| Blind spots across a model generation | 320 hidden in both · 503 now visible · **630 newly hidden** |
| Retrieval repairs ignorance, not belief | obscurity **+65.2 points** (7.2% → 72.4% right) · misconception **+14.0 points** (not significant, p = 0.077) · the gap **+51.2 points** is the finding |
| Blind spots follow correlation, not accuracy | among the 70 four-model ensembles (of 154 tried), silent-failure rate vs mean pairwise error correlation **r = +0.92** (+0.918 holding error fixed); vs error rate **r = −0.34** |
| Web search does not rescue them | an agent that can search leaves **64.7%** (88 of 136) wrong under both search engines (Wikipedia and the open web) |
| Counter-evidence does not move them | shown evidence against their answer, the models fix **0.74%** (7 of 950); allowed to say "I don't know", **0 of 950** |
| The answer record still carries signal | where the vote is blind, a model trained on the record lifts AUC **0.592 → 0.772** |
| Human labels are reliable | 430 blinded verdicts; second annotator on 115: **κ = 0.970** [0.924, 1.000] |

The uncomfortable one is the model upgrade: **the newer models make fewer mistakes, but a larger
fraction of what remains is shared** — the kind of mistake a disagreement check
cannot see. That is the safety argument. What it does not show is that the total
number of blind spots grows (that rise is not significant once answer keys are
re-checked), or that this is a trend: it is one generation pair, and model size
and generation change together.

The generation row is the same argument case by case, and its axis is
**detectability, not correctness**: 80% of the 630 "newly hidden" were already
wrong in 2024 and merely *disagreed* about it. Newer models go blind on nearly
twice as many questions as they inherit (1.97×) — not by being more often wrong,
but by agreeing when they are.

## What changed, and when

| date | what happened | effect on the numbers |
|---|---|---|
| through Aug 2026 | full run: four 2025 models and four 2024 models on 42,591 questions; defects found and fixed along the way (`ISSUES.md`) | first headline set (AUC 0.862, 1,054 blind spots, 9.0×) — **all superseded** |
| 27 Sep 2026 | adversarial review found **8,489 duplicate questions**, a tie rule that favoured one model, and a pooled independence ratio inflated by mixing datasets (#66–#78). Corpus deduplicated to 34,062; tie rule fixed; ratio computed within each dataset | AUC 0.862 → **0.840**; 1,054 → **950** blind spots; 9.0× → **3.3×**; every figure re-derived |
| 27 Sep 2026 | **paid re-runs** of the three results that needed new model calls: retrieval (RQ4, #70), LLM answer-key adjudication (#71), agentic search (RQ5, #76) — 0 failed calls | misconception retrieval lift now **not significant** (p = 0.077); artifact share **21.05%** (750 genuine); web-search ceiling **64.7%** |
| 30 Sep 2026 | second adversarial review: every number in the thesis, slides and tool re-checked against the data; prose rewritten in plain language | double rounding fixed (pooled φ 0.653 → **0.654**, p 0.102 → **0.101**); ablation correlations correctly attributed to the **70 four-model ensembles**, not all 154; one answer-key case and several references corrected; slide 23 ("who is it for") added |

## Layout

```
faultlines_project/     the pipeline, the tests, and the records
  faultlines/           one module per stage: datasets → generate → grade
                        → nli → disagree → embed → evaluate
  scripts/              export_web.py, handlabel.py, check_provider.py, …
  tests/                70 tests
  RESULTS.md            what is true -- starts with a "what to quote" claims table
  ISSUES.md             what broke -- 78 defects, grouped by class
  DECISIONS.md          why each choice was made, and the options rejected
  EVOLUTION.md          why the project looks different from the proposal
  TASKS.md              task abstraction + the expert-evaluation protocol
faultlines-web/         the deck (index.html) — replaces the slide deck
                        walkthroughs.html — two discovery paths through the tool
                        pipeline.html — the earlier level-by-level explainer
faultlines-tool/        the tool, five views: map · read the cases · did upgrading
                        help? · how good is the signal? · which ensemble?
```

## Running it

```bash
# run from faultlines_project/; the interpreter lives outside the tree (see DECISIONS.md)
C:\venvs\faultlines\Scripts\python.exe -m pytest tests -q

# regenerate both web payloads from the parquet layer
python scripts/export_web.py

# hand-label TruthfulQA verdicts (blinded, two strata, resumable)
python scripts/handlabel.py            # label
python scripts/handlabel.py --result   # kappa + corrected AUC
```

`data/` is **not** in this repo — about 300 MB of graded answers and embeddings
(plus a 212 MB pre-deduplication backup).
Regenerate with the pipeline. `faultlines-tool/data.json` **is** committed; the
tool cannot load without it.

Both web folders are served as static files with no build step. Each is its own
Vercel project root. After deploying the tool, paste its URL into `TOOL_URL` at
the top of `faultlines-web/index.html`.

## Read this before trusting any number

`ISSUES.md` is not an afterthought — it is part of the methodology, and the
short version is worth stating up front:

- **78 defects** found; all of them are fixed and closed — the last three after
  a paid re-run on 27 Sep 2026. Several produced coherent,
  publishable-looking tables that were wrong — including, found on 27 Sep 2026,
  **8,489 questions asked twice** under different ids, which — together with a
  tie rule that favoured one model — had inflated the headline AUC from 0.840
  to 0.862.
- **340,728 generations were voided** because a provider served different model
  weights under the requested model names (Gemma-2 requests answered by Gemma-3,
  99.6% identical outputs). Two whole experiment arms measured nothing.
- **RQ4 took four attempts.** The first three reported "retrieval does not fix
  obscurity" — a clean, coherent, false result caused by a retriever returning
  nothing while the harness scored the silence. The check that caught it: *is the
  correct answer even present in the retrieved text?* 8% → 70%.
- **Every effect measured on 300 questions was smaller or absent at full scale**
   — five times out of five.
- **Almost every unintentional bias found favoured this project's own hypothesis**
  (the exceptions, such as the inter-rater weighting fix in ISSUES #69, are logged).

That last point is why the methodology chapter is about how each number was
attacked, not just what it came out as. "Small, and in our favour" is not a
defensible sentence.

## What is in this repository

This is the **code and results** repository: the pipeline, the tests, the project
records, the slide deck and the tool. **The thesis document itself is not included**
while it is under review; every figure it quotes is reproducible from what is here,
and `faultlines_project/RESULTS.md` is the list of what may be quoted.

## Status

*As of 8 Oct 2026. Submission is planned for mid-October 2026.*

| | |
|---|---|
| ✅ pipeline and five research questions — 34,062 questions analysed, 136,248 graded answers per arm (170,364 generated) | re-derived 27 Sep on the deduplicated corpus |
| ✅ 430 verdicts hand-labelled, blinded, two strata; second annotator on 115 | κ = 0.970 [0.924, 1.000] |
| ✅ deck, tool, walkthroughs and pipeline explainer built and deployed | links at the top |
| ✅ **task abstraction** — `TASKS.md` | 3 personas · 7 domain tasks · 6 evaluation tasks |
| ✅ evaluation — **analytical, no participants**: cognitive walkthrough, discovery provenance, measured performance | the six-task expert study was not run, and Chapter 6 says so |
| ✅ the write-up — eight chapters, references and an appendix; built to the SFSU format (220 pages) | 30 Sep: full adversarial fact check and plain-language pass; 2 Oct: final pre-submission fact check; `check_writeup.py` passes on every figure |
| ✅ figures recaptured from the deployed tool | 30 Sep |
| ⬜ advisor review and submission | mid-October 2026 |

## Datasets

PopQA · TriviaQA · HaluEval · TruthfulQA. Each retains its original licence;
derived answers are not redistributed here.
