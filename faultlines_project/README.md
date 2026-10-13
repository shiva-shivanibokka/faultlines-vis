# FaultLines

Cross-model disagreement as a hallucination signal — and a map of *where* the
faults are. Capstone, SFSU M.S. Data Science & Artificial Intelligence.

Slide deck: <https://faultlines-peach.vercel.app> ·
tool: <https://faultlines-tool.vercel.app> ·
method, level by level: <https://faultlines-peach.vercel.app/pipeline.html>

## Where it stands (27 Sep 2026)

An adversarial review on 27 Sep found 13 defects (ISSUES #66–#78), the largest
being **8,489 duplicate questions** in the corpus. Everything was re-derived on
the deduplicated corpus; `faultlines-web/summary.json` is the source of every
number, and `RESULTS.md`'s claims table is the list of what may be quoted.

| | |
|---|---|
| corpus | 42,591 asked → 40 ungradeable → 8,489 duplicates → **34,062 analysed** |
| cross-model AUC (head-count) | **0.840** [0.836, 0.845] |
| vs best single-model Semantic Entropy | 0.838 vs 0.778 on 6,436 same questions |
| silent consensus (blind spots) | **950** (2.79%), an upper bound — ~21% are answer-key artifacts |
| independence assumption (models err independently) — false | all four wrong together **3.3×** as often as independence predicts, within dataset |
| paid re-runs (27 Sep, done) | RQ4 (#70), the LLM adjudications (#71), RQ5's missing rows (#76) — all closed; 0 failed calls |

---

## Setup

**Use the venv. Do not `pip install` this into your anaconda base env** — base
holds TensorFlow, opencv and mlxtend with mutually incompatible numpy pins, and
installing here will upgrade numpy out from under them and break h5py.

The venv lives at **`C:\venvs\faultlines`**, deliberately outside the project.
This folder sits deep under OneDrive, and torch ships a vendored path long
enough to blow Windows' 260-character `MAX_PATH` limit when installed here.

```bash
python -m venv C:\venvs\faultlines
C:\venvs\faultlines\Scripts\activate
pip install -r requirements.txt

```

Inference is **hosted** (DeepInfra), not local. Put your key in
`~/.faultlines.env` — deliberately outside this folder, which sits under
OneDrive:

```
DEEPINFRA_API_KEY=...
```

```bash
python scripts/check_provider.py       # ALWAYS run before a paid pass
```

Every command below assumes that venv is active. If you'd rather not activate,
call `C:\venvs\faultlines\Scripts\python.exe` explicitly.

Torch installs CPU-only, which is correct: answer generation happens remotely.
Torch only runs MiniLM over short strings.

`check_provider.py` is not optional. Catalogue membership is not availability,
and HTTP 200 is not a usable response — it has caught models that 400 as
non-serverless, and models that answer correctly while returning **no logprobs**,
which silently reduces every confidence to NaN. See ISSUES.md.

## Reproduce everything

```bash
python scripts/reproduce.py --list     # what each stage does, runs nothing
python scripts/reproduce.py --fast     # rebuild + check every figure, ~2 min
python scripts/reproduce.py            # the same, plus the 70 tests, ~25 min
```

It rebuilds `summary.json`, `data.json` and the three prerendered pages from
`records.parquet`, then checks the thesis figures registered in
`scripts/check_writeup.py` against them (plus a near-miss scan for mistyped
copies, and the cross-artifact invariants), re-runs the cognitive walkthrough and the
cross-generation artifact comparison, and finishes with the test suite.

**It does not re-run the generation stages, and says so.** Each arm is 170,364
generated answers. The 2025 arm ran on a paid hosted API; the 2024 arm ran on a
laptop GPU, about 138 hours of measured wall clock for that one pass, and it
cannot be regenerated at all -- it ran on local Ollama weights that
`config.yaml` no longer points at. Everything from *graded answers* onward is verified, which is
every claim in Chapters 5, 6 and 7. That the same four models asked again today
would answer the same way is **not** verified, because they would not.

---

## Run the pilot

*Historical: this is how the project started (week 2). The full run superseded it.*

```bash
pytest tests/ -q                                  # 70 tests, no models needed
python scripts/run_pilot.py --tag _myrun          # 300 questions end to end
```

**Always pass `--tag`.** Runs with different tags never touch each other's
files. Without it you overwrite the previous arm — and the frozen local 7-9B
pilot cannot be regenerated now that config points at hosted models.

`--rebuild-questions` regenerates the question set and is **destructive**: it
orphans every existing answers/records file, because qids are rebuilt from
scratch. It is off by default for that reason.

**Do this before writing any more code.** The pilot answers the one question
the entire project rests on: *do the four models fail differently?* If they
fail on the same questions, disagreement carries no information and Levels
7–15 have no foundation. Better to learn that in week 2 than in November.

It prints four things:

1. per-model accuracy — sanity check that the prompt is working at all
2. **pairwise error correlation** — the upstream risk
3. **ROC-AUC**, cross-model vs the best single-model Semantic Entropy baseline
4. the size of the all-agree-all-wrong population that Audit depends on

Each stage checkpoints to parquet and skips finished work, so a crash costs
minutes. `--report-only` re-prints from what is already on disk;
`--skip-baseline` drops Level 6 and runs roughly 4× faster.

## How to read the result

| Outcome | What it means | Do this |
|---|---|---|
| correlation 0.3–0.5, AUC ≥ 0.65 | healthy diversity | proceed to the full 42,591-question run |
| correlation 0.8+ | models too alike | swap one for a different *training recipe* — a synthetic-data-trained model decorrelates far more than another web-trained one. Not a bigger model. |
| AUC ≈ 0.50 | signal absent on this data | stop and talk to your advisor about scope |

Anchors from the literature: Farquhar's Semantic Entropy **0.790**;
Gorbett's cross-model **0.727** vs single-model **0.595**.
0.70 is respectable here, 0.80 strong, 0.95+ means suspect the grader.

## Layout

```
config.yaml            every tunable number. change it here, not in the code.
faultlines/
  config.py            loads config.yaml, defines the record schema
  datasets.py    L1    TriviaQA / PopQA / HaluEval / TruthfulQA -> one table
  generate.py    L2    hosted API, threaded, logprobs -> confidence
  grade.py       L3    exact -> alias -> semantic
  disagree.py    L4    meaning clusters, confidence-weighted -> one score
  embed.py       L5    MiniLM + UMAP, questions only
  baseline.py    L6    semantic entropy, matched 4-generation budget
  evaluate.py    L6    error correlation + ROC-AUC
  semantics.py         the one shared sentence transformer
  track.py             RQ3, silent-consensus overlap between two tagged arms
scripts/run_pilot.py   the whole thing, with a readable report
scripts/check_provider.py  the pre-run gate: serverless + logprobs + no reasoning leak
scripts/probe_datasets.py  measures whether a dataset has usable error variance
tests/                 70 tests, all offline
```

## What was built instead of the original plan

The proposal planned a FastAPI backend, Postgres + pgvector and a React tool.
None were needed: the tool in `../faultlines-tool/` is a static page that loads
one precomputed `data.json`, so it deploys with no server. See `EVOLUTION.md`.

## Three invariants worth not breaking

**Never score against a label the signal implies.** The prediction target is
`majority_wrong` (`evaluate.TARGET`), not `any_wrong`. With one gold answer, N
different answers means at most one can match, so "someone was wrong" is true by
arithmetic whenever the models split — scoring against it gave a meaningless
0.911 AUC on the 300-question pilot. Against `majority_wrong` the same pilot
data gave 0.800 (the full deduplicated corpus gives 0.840). See ISSUES.md #0.

**The answer key evaluates the signal, it never computes it.** Grading is
downstream of disagreement. Blur that line and the claim stops being falsifiable.

**Map position comes from question wording alone.** If position were derived
from the disagreement score, "high-disagreement questions cluster together"
would be true by construction — and Forecast could not place an unanswered
question without running a model.

## Where things are written down

| file | holds |
|---|---|
| `DECISIONS.md` | every decision + the evidence that drove it |
| `RESULTS.md` | every measured number |
| `ISSUES.md` | every problem hit, with a status table at the top |
| `AUDIT.md` | the pre-run codebase audit (13 findings, all fixed) |
| `DATASET_ANALYSIS.md` | why TruthfulQA/SimpleQA score low, and why more data won't fix it |

One caveat worth knowing before trusting a TruthfulQA number: **24% of its
gradeable NLI verdicts (330 of 1,360) sit below a 0.10 margin**, and a human
could not decide 26% of those (ISSUES.md 1b, closed by hand-labelling). Its AUC
is 0.683 with a 95% CI of [0.601, 0.764], six to eleven times wider than the
other datasets'. No TruthfulQA figure should be quoted without that interval.
