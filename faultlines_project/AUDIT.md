# Repo Audit Report — faultlines_project

**Date:** 2026-07-27
**Stack detected:** Python 3.11 · pandas/pyarrow · sentence-transformers · scikit-learn · umap-learn · requests
**Scope:** `faultlines/` (14 modules), `scripts/` (5), `tests/` (9), `config.yaml`. Excluded: `data/` (artifacts), `docs/`.
**Trigger:** pre-flight before a ~172,000-generation paid run.
**Status:** ✅ **ALL 13 FINDINGS RESOLVED 2026-07-27.** 44 tests pass;
`check_provider.py` green. The 12-task fix plan was executed in full and then
deleted — every task's diff is in git-less form inside the module docstrings and
comments, and each fix carries the measurement that motivated it.

## Summary

- Total findings: **13**
- Auto-fixed (trivial-safe): **1**
- Fixed after review: **12**
- Outstanding: **0**
- Critical: **2** | Major: **7** | Minor: **3** | Notes: **1**

## Production-readiness scorecard

| Category | Status | Notes |
|---|---|---|
| Correctness | ✅ | Config-key drift removed; `track.py` repaired and verified against live data |
| Silent failures | ✅ | `tag` threaded through every module; grader no longer self-reverts; screen fails loudly |
| Security | ✅ | No hardcoded secrets; `.env` moved out of the OneDrive tree |
| Concurrency | ✅ | Thread pools are bounded, per-chunk, and join before checkpointing |
| Performance | ✅ | Grader batched: verified identical, 50.1s -> 5.2s |
| Architecture | ✅ | `tag` threading complete across all pipeline modules |
| Production-readiness | ✅ | Destructive rebuild is now opt-in behind `--rebuild-questions` |
| Test coverage | ⚠️ | 44 tests. Resume/checkpoint paths verified manually, not yet automated |

## The two Critical findings

### C1 — `scripts/run_pilot.py:145-152` destroys the small-scale arm

`main()` calls `datasets.build(pilot=True)` then `generate.run(pilot=True)` with no `tag`.
Run today, that:

1. rebuilds `questions_pilot.parquet` from the **new** dataset config (TriviaQA/PopQA/HaluEval/TruthfulQA), replacing the frozen 300-question set with different `qid`s entirely, and
2. overwrites `answers_pilot.parquet` using the **current** ensemble — which is now the hosted gen-3 models.

**Why it matters:** that file holds the local 7–9B results. It is one half of the two-scale comparison that is the thesis's spine, it represents days of laptop GPU time, and it cannot be regenerated now that config points at hosted models. This is the documented entry point in `README.md`, so the destructive path is the *advertised* one.

### C2 — `scripts/check_provider.py:61` validates a stale model list

It reads `CFG["ensemble_hosted"]`, which still contains `Qwen3-Next-80B-A3B`, while `CFG["ensemble"]` — what `generate.py` actually uses — contains `Qwen3-235B-A22B`. Verified drifted.

**Why it matters:** this is the gate that exists specifically to prevent a bad 172k run. It currently green-lights models that will not be used and never tests one that will. The `--tag`/logprob bugs it caught earlier today were caught *because* it checked the right list; it no longer does.

## Findings (all resolved)

Recorded as found, so the report shows what the audit caught. Per-task fixes and
verification commands are recorded in each fix's own code comments. Each
entry below describes the state
**before** the fix.

**Cross-file contract violations (pass 6)**
- **M1** `track.py:68` — `CFG["ensemble_gen1"]` raises `KeyError`; the key was renamed `ensemble_gen1_DROPPED`. Track's generation path is dead code as written.
- **M2** `track.py:48-57` — `_records_from_answers()` omits the `gradeable` filter that `disagree.run():58-62` applies. Gen-1 and gen-2 records are therefore computed over **different question populations**, so the persistence overlap compares mismatched sets. This silently biases the headline Track number.

**Silent failures (pass 2)**
- **M3** `embed.py`, `rq1_confidence.py`, `rq2_localize.py`, `screen.py` — no `tag` support; all hardcode `records_pilot.parquet` / `answers_pilot.parquet`. Running RQ1 or RQ2 now analyses the **local 7–9B** results while reporting them as current. Produces confident, plausible, wrong numbers with no error.
- **M4** `grade.py:83-91` — `run()` recomputes `correct` for *all* rows using cosine. Running `grade` after `nli` silently reverts TruthfulQA to negation-blind grading, and because `correct_cosine` is only set when absent, the NLI verdicts vanish with no trace.
- **M5** `track.py:60-85` — failed generations (NaN confidence) are written to disk and then counted as `done` on resume, so transient failures become permanent holes. Same bug fixed in `generate.py` today; `track.py` was not updated.

**Missing code (pass 5)**
- **M6** `screen.py:34-36` — the pool is drawn from `questions{sfx}.parquet` with `min(pool, len(q))`. `--pool 20000` against the 300-row pilot file screens 300 rows and prints a yield as though it succeeded. No warning that the request was silently truncated.

**Performance (pass 10)**
- **M7** `grade.py:75` — tier-3 grading calls `embed()` once per answer. Measured on the gen-3 run: only 191 of 1,200 rows were decided by tiers 1–2, so ~83% reach the encoder. At 43k questions × 4 models that is ~143,000 single-item encoder invocations instead of batched calls.

**Minor**
- **m1** `semantics.py:28-48` — greedy clustering is order-dependent. Deterministic in practice (answers arrive in fixed model order) but not guaranteed by contract.
- **m2** `.env` holds a live DeepInfra key inside a **OneDrive-synced** folder. `.gitignore` prevents git exposure but not cloud replication.
- **m3** `rq4_retrieval.py:123` hardcodes `CFG["ensemble"][0]` as the retrieval model — silently changes meaning whenever the ensemble is reordered.

**Note**
- **n1 — CLOSED 2026-08-25.** `rq2_localize.py` — neighbourhood density was computed over all datasets mixed, then subset to PopQA, so a PopQA question's neighbours could be TruthfulQA questions. Measured: **28.1%** of them were. `popularity_control()` now reports both the shared-map density (what the tool draws) and a density recomputed within PopQA (what the control needs), and `rq2_localize.parquet` carries both columns. **The lift rose from +0.060 to +0.078** — the leak had been costing the finding about 30% of its effect, not inflating it. See RESULTS.md Finding 7.

## Auto-fixed (trivial-safe)

- `rq2_localize.py:47` — removed unused parameter `feat1` from `popularity_control()`; the function recomputes density internally and never read the argument. Both call sites are in the same file and were updated. Behaviour-neutral.

## Clean areas

- **`generate.py`** — the retry/backoff and success-only resume added today are correct; failures are no longer persisted as done.
- **`evaluate.py`** — `auc()` correctly returns NaN rather than raising on a single-class slice; `TARGET = majority_wrong` is well-reasoned and documented against the circularity trap.
- **`config.py`** — `.env` loader uses `setdefault`, so real environment variables correctly outrank the file.
- **Concurrency** — every `ThreadPoolExecutor` is scoped to a `with` block that joins before the checkpoint write; no shared mutable state across workers.
- **Security** — no hardcoded credentials anywhere in source, config, tests, or comments.
