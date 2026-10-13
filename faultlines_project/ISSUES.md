# Issues log

## 78 defects found. All 78 are fixed and closed; the last three (#70, #71, #76) closed on 2026-09-27, when the paid re-run their corrected numbers waited on landed with 0 failed calls.

*(#43, #44 added 2026-08-03 by a measurement audit; #45-#47 on 2026-08-07, #48-#49 on 2026-08-08, #50-#52 on 2026-08-10, #53-#55 on 2026-08-25, #56-#62 on 2026-08-26 — both were wrong numbers in
published files, neither had been noticed by reading the pages; **#63 on 2026-08-31**, a wrong number in the claims table itself; **#64-#65 on 2026-09-07**, found by building the reference list and re-checking the rules' own figures; **#66-#78 on 2026-09-27**, by an adversarial review — the largest batch since July, and the first to move the headline AUC. See "2026-09-27 · Adversarial review" below.)*

Grouped by **class**, because the classes are what the write-up needs — the
chronological batches below are how they were found, not what they mean.

| class | defects | what it looked like | the lesson |
|---|---|---|---|
| **A failed call recorded as an answer** | #5, #23, #24, #26, **#70**, **#71**, **#76** | empty strings entering the data as if a model had produced them — and, on 27 Sep, as *wrong* answers (#70), as a judge *declining* (#71) and as a missing row (#76) | one retry policy (`ask_retry`), and *an empty answer is a failed call, not a result* — rule 1 was written in July and three later scripts still broke it |
| **Unique ids are not unique questions** | **#66**, **#73** | 8,489 questions asked twice under different qids; cross-validation folds that put a question's twin on the other side of the split | every check that worked on `qid` passed, because qids are unique by construction. Deduplicate by content (rule 8) |
| **An unstated rule decided the label** | **#67** | a four-way split has no majority, and the code silently took Llama's answer | a tie is a design decision. State the rule, and report what the other rules would have given |
| **Pooling across strata manufactured an effect** | **#68** | datasets whose difficulty differs ~6x multiplied together as though they were one population: 9.0x pooled before dedup (6.1x after), 3.3x within dataset | a ratio of averages over unequal strata is partly a statement about the strata |
| **An analysis that did not match its design** | #56, **#69**, **#72**, **#74**, **#75** | wrong stratum size; unshuffled folds on a sorted file; an unpaired test on paired data; an unweighted overlap on a weighted sample | the test has to be chosen from the design, not from the first function that returns a p-value |
| **A number computed once, by hand** | #54, **#77** | every claim's interval was computed in one session and typed in; nothing re-derived them when the data moved | an interval is a number. It goes through the exporter or it does not exist (rule 4) |
| **Resume vs in-place column writes** | #23, #24, #26, **#36** | a stage assumed it saw a whole file; resume handed it a partial one | `if "col" not in df.columns` is a **review flag**. Fill per row, never per file |
| **A cache that made failure permanent** | #29, #29b | 88% of retrievals "found nothing" — the nothing was cached | never cache a failure; throttle before you need to |
| **Model provenance** | **#31** | provider served Gemma-3 under a Gemma-2 name, 99.6% identical | 340,728 generations void. Verify identity *behaviourally* before paying, and by *content digest* where possible |
| **A null result the harness invented** | #25, #28, #29, #30 | "retrieval does not fix obscurity", three times, in clean tables | check the *mechanism*, not the output: was the gold answer even in the retrieved text? |
| **The fix that broke something** | #32, #33, #34, #35 | three of four defects in one audit were created by that day's fixes | audit the fixes, same day, as their own change |
| **A gate that failed closed** | #27 | a safety check blocked a run on three models that worked fine | a gate needs its own false-positive rate stated, like the detector it protects |
| **The error handler that killed the process** | #30 | `UnicodeEncodeError` *inside* an `except` handling a 429 | a logging call must never be able to end a run — fixed globally in `config.py` |
| **CSS specificity** | **#38** | tool showed a permanent loading screen while working perfectly underneath | `.hidden = true` loses to an ID selector; console was clean because nothing errored |
| **A published artifact going stale** | **#37**, **#53** | the live site served a retracted AUC of 0.788 for days; the pipeline page described a study that was never run | a published page **is a result** and belongs in the same review loop |
| **A limit, not a bug** | **#39** | the answer-key flag also fires on genuinely wrong short answers | not fixable by tuning — see "Why nothing works". Reframed as a judgement call rather than removed |
| **A bound on one failure mode, reported as a bound on the phenomenon** | **#55** | "at most 5.6% of blind spots are grading artifacts" — measured by a containment test, so blind to every artifact that is not a substring. Directly measured: **21.7%** | a bound is only as wide as the test that produced it. Name the failure mode in the sentence |
| **A citation never resolved to a record** | **#64** | four wrong venues or names in prose that had no reference list to check against, including the advisor's own tool | a claim about the literature is a claim. Rule 5 applies |
| **A rate applied to its own measurement denominator** | **#63** | the 21.74% artifact rate was measured on 998 committed verdicts and applied back to 998, giving ~780 where the population figure is **825** | a rate has two denominators. Name the one it is *applied to* |
| **A stratified sample analysed as though it were random** | **#56** | the inter-rater stratum was drawn from cases an LLM had already ratified, and its κ = 1.000 was quoted as the population figure | the analysis has to match the design. Weight by N/n, or do not stratify |

### The standing rules these produced

1. **An empty answer is a failed call, not a result** — and must not count as done on resume.
2. **`if "col" not in df.columns` is a review flag.** Four defects, one shape.
3. **Never cache a failure.**
4. **A published artifact is a result.** No number reaches a public page unless the exporter produced it.
5. **A number with no source is worse than a stale number** (#54). A stale number has a source that moved on, so re-running the exporter catches it. An estimate that was never measured has nothing to diverge from, so nothing will ever flag it. Prose figures need a source or a measurement script.
6. **Nothing is reported until it has been attacked once.** Added 2026-08-25 at Shivani's instruction, after three near-misses in a single afternoon. Before any result leaves this repository — into a page, a paper, a message, or a conversation — it gets one deliberate pass whose *only* goal is to find the reason it is wrong: reproduce a known number with the new code, check every engineered feature for label leakage, confirm the denominator, and count the thing that was asserted rather than counted. The pass is not optional because the result looks clean; a clean-looking result is exactly what #31 and #54 both were.

#### What rule 6 caught on the day it was written

| near-miss | what the first run said | what it was |
|---|---|---|
| `ensemble_ablation.py` | AUC 0.865 against a documented 0.862, called a MISMATCH | two different documented scores — head-count 0.862 and confidence-weighted 0.865. The check was comparing the wrong one, and the code was right |
| `rq1_multifeature.py` | AUC 0.759 from neighbourhood density | **cross-fold label leakage.** Density is built from neighbours' correctness, computed once over the whole corpus, so test-fold labels were reaching training features |
| `rq1_multifeature.py` again | density made the model *worse* after the first fix | the fix was half-done: training rows still read **their own** label, because a row is its own nearest neighbour. Costing 0.05 AUC, and the symptom looked nothing like a leak |
| `+ grader margin` feature set | a clean negative result | `nli_margin` is **99.1% null** — NLI runs on TruthfulQA only. sklearn dropped the column at the imputer and printed a plausible row |
| "162 ensembles" | quoted in the deck and in PLAN.md | C(8,2)+C(8,3)+C(8,4) = **154**. Arithmetic asserted, never done |
| the second-annotator tool | a working labelling pass | it built its queue from `handlabels.parquet`, which records what the first annotator DECIDED and not what they were SHOWN. No `aliases`, no `meta` -- so the second annotator would have seen **one** accepted answer instead of three and **no bait list at all**, on all 115 cases. Two people applying different standards do not produce an inter-rater figure |
| the same tool, again | correctly blinded | `show()` never printed the prior verdicts, but `human`, `machine` and `margin` were sitting in the dataframe the annotator's own process was holding. Dropped from the frame rather than left unprinted |

Seven now, all in work that looked finished, and the last two were caught in a
dry run of a tool that had not been used on anything yet. That is the argument
for the rule: the second one would not have produced a wrong number, it would
have produced a number measuring the wrong thing, which is harder to notice
later and impossible to fix retrospectively.

7. **A summary of a record is a record, and needs its own check.** Adopted
   2026-08-31 after #63. `RESULTS.md`'s claims table is the only part of this
   project that other documents are *instructed* to quote from, and it was the
   only part with nothing checking it — `check_writeup.py` validates the
   thesis chapters against `summary.json`, and the chapters were right. The
   table underneath them was not.

   **Every figure in the claims table must be derivable from the body of the
   same file.** A number that appears in the table and nowhere below it has no
   source, which is rule 5 one level up. Two specific things to check, because
   they are what #63 actually was:

   - **Which denominator.** A rate estimated on a subset (because some cases
     were undecidable, or filtered, or unreachable) has *two* denominators —
     the one it was measured on and the one it is applied to. Name the second
     one in the sentence. #63 applied 21.74% back to the 998 committed verdicts
     it was estimated from instead of to the 1,054 population, and 781 is as
     plausible-looking as 825.
   - **Two figures for one quantity are fine; two *unexplained* figures are
     not.** 825 and 837 are both correct for their stated denominators, and the
     only reason that took minutes rather than a day is that `RESULTS.md`
     already said why — *same numerator, different and explicitly stated
     denominator*. Where a second figure exists, the sentence that introduces
     it carries the reason.

   **The rule has a known weakness and it is stated rather than hidden:** as
   written it asks for a person to re-derive the table by hand, and a manual
   pass is exactly the kind of obligation that gets skipped in a busy month. The
   mechanical version — extract every figure in the claims table, assert each
   appears in the body below it — would have caught #63, because `780`
   appears nowhere else in the file. Until that exists, this rule is enforced by
   reading, which is how #63 was found in the first place.

8. **Unique ids are not unique questions — deduplicate by content.** Adopted
   2026-09-27 after #66. A `qid` is minted by this pipeline, one per row it
   ingests, so it is unique by construction and a check that asks "are the
   qids unique?" cannot fail. TriviaQA's `rc.nocontext` split lists a question
   once per evidence source, and PopQA repeats template-subject-answer rows;
   8,489 of 42,551 gradeable questions were second copies, and every
   uniqueness check in the project passed over them for two months. The check
   that means something is on **content**: the same question text *and* the
   same gold answer (`datasets.duplicate_qids()`). Same text with a
   *different* gold is two questions (two films called *Crash*) and stays.
   The same rule applies to anything that splits data — a cross-validation
   fold, a train/test split, a bootstrap unit — which must group by question
   content, not by row (#73).

### Methodological watch list — cautions, not defects

| | |
|---|---|
| Effects shrink as n grows | **5 for 5.** Anything from a 300-question sample should be assumed smaller |
| The grader's error ran one direction | over-generous, flattering the AUC — **but see the amendment**: hand-labelling found NLI errs 31 generous / 39 harsh, so this applies only to the pre-NLI graders |
| Bias has favoured our own hypothesis | every unintentional bias found. "Small, and in our favour" is not a defensible sentence |
| Hosted models have a shelf life | delisting and substitution are normal; pin and verify |
| **Similarity cannot decide identity** | three graders fail on the same band, and NLI fails *inverted*. See "Why nothing works" below — the single most reusable observation in this file |
| **A correct pipeline can publish a wrong finding — through its labels** | the RQ3 categories were computed on *detectability* and displayed on *correctness*. Zero data errors, wrong result on screen. No test can assert against a category name — see watch-list 3b |

### Open items

**None, as of the 2026-09-27 re-run.** Three items were opened earlier the same
day, all waiting on one thing — an API key for a paid re-run. It ran that day
with 0 failed calls, and all three are closed:

| # | what the re-run produced | quoted until then |
|---|---|---|
| **#70** | RQ4 on the strata re-selected after #66/#67, 0 empty answers: obscurity **+65.2%** (n=500), misconception **+14.0%** (n=57, p = 0.077, no longer significant), dissociation **+51.2%** | +68.9% (n=479) / +15.7% (n=70), marked *pending* |
| **#71** | (a) the 45 failed blind-spot adjudications re-judged: all 950 decided, artifact rate **21.05%** [18.58%, 23.76%], 750 genuine; (b) the 430-case adjudicator re-run *with* alias lists: κ **0.782** against the human, disputes 45 → 29 | 21.1% of 905 decided, marked *pending*; claim 17's κ 0.688 withdrawn |
| **#76** | the missing RQ5 Wikipedia-arm rows re-run (948 of 950 complete) and TruthfulQA graded by NLI: **64.7%** (88/136 matched) stay wrong | 65.5% of 116 matched, marked *pending* |

*(Until 2026-09-27 this section said "None" — true of the code on 2026-07-29,
and true of the defects known on 2026-09-07. For most of 27 Sep it listed the
three items above; it says "None" again because the re-run closed them.)*

---

## 2026-09-27 · Adversarial review — defects #66–#78

**How found.** On 27 Sep 2026 four agents were each given the repository and one
instruction: find the reason a headline number is wrong. Every finding was then
re-verified independently — re-derived from the parquet layer, not accepted from
the reviewer — before it was logged. Thirteen numbered defects (#66–#78) and eleven smaller
findings survived. It is standing rule 6 applied to the whole project at once,
five weeks after it was written, and it found more than any batch since July.

**What it did to the headline.** Everything below was re-derived on the
deduplicated corpus and re-exported to `faultlines-web/summary.json`
(regenerated 27 Sep by `scripts/export_web.py`). The biggest single mover is #66.

| quantity | before | after (`summary.json`) |
|---|---|---|
| questions analysed | 42,551 | **34,062** (`corpus.analysed`) |
| AUC, head-count | 0.862 | **0.840** [0.836, 0.845] (`intervals.auc`) |
| silent-consensus blind spots | 1,054 (2.48%) | **950** (2.79%) (`intervals.blind_rate`) |
| independence headline | 9.0× pooled | **3.3× within dataset** (`intervals.concordance`); pooled now 6.1× |
| RQ1b | 0.601 → 0.811 | **0.592 → 0.772** (`rq1b`) |
| inter-rater κ | 0.962 | **0.970** (`irr.kappa`) |

### #66 · CRITICAL · the corpus asked 8,489 questions twice

**What.** TriviaQA's `rc.nocontext` validation split lists each question once per
evidence source (web and Wikipedia). Sampling the whole split put **7,982**
TriviaQA questions into the corpus twice, under two qids. PopQA added **507**
rows with identical template, subject and answer. **8,489** second copies in all.

**How found.** A reviewer asked why the out-of-fold RQ1b model did so well
(0.811 in a region where the vote is blind by construction). The answer was that
a question's twin was often in the training fold. Every earlier uniqueness check
had tested `qid`, which this pipeline mints and which is therefore unique by
construction.

**Effect on the numbers.** Every corpus-level figure moved. AUC 0.862 → 0.840;
blind spots 1,054 → 950; TriviaQA n 17,944 → 9,962; generations analysed
170,364 → 136,248 (170,364 were still *generated* per arm). 7,982 of the
8,489 were TriviaQA, the dataset with the highest AUC and the lowest error rate,
so the duplicates over-weighted exactly the questions the detector handles best.
How much of the AUC drop is dedup and how much is the tie rule (#67) is not
separated here: both landed in the same re-export.

**Fix.** `faultlines/datasets.py: duplicate_qids()` — same question text **and**
same gold; the earlier qid is kept. Applied upstream of `disagree.run`, so every
downstream stage sees 34,062. PopQA rows sharing text but not gold (two films
called *Crash*) are distinct questions and stay; RQ2's shared-title finding is
built on them. **The 2-D map was not refit**: each removed twin sat on the same
point as the question it duplicated, so every remaining question keeps its
position and every walkthrough link stays valid. New standing rule 8.
Tests added in `tests/test_datasets.py`.

**Files.** `faultlines/datasets.py`, `faultlines/disagree.py`,
`scripts/export_web.py`, `tests/test_datasets.py`; every number downstream.

### #67 · the majority tie rule was "whichever answer Llama gave"

**What.** `majority_wrong` asks whether the ensemble's answer is wrong, which
needs a rule when there is no largest meaning-cluster: four different answers
(**9,029** questions, 26.5% of the corpus) or a 2–2 split (1,233). The code took
the cluster holding the first answer in file order — always Llama-4-Maverick's.
Within a cluster, a correctness tie went to "wrong".

**How found.** The review asked what `majority_wrong` means when there is no
majority, and the code's answer was an accident of column order.

**Effect.** 1,455 labels changed. Sensitivity on the final corpus (measured
27 Sep, not exported): the principled rule gives AUC **0.840**; the old
Llama-first rule 0.849; labelling four-way splits by Qwen 0.856, Llama 0.849,
Gemma 0.885, Mistral 0.885; treating "no majority" as failure 0.901. **The
principled rule gives the lowest value of any of them** — the fix is the
conservative choice, not the flattering one.

**Fix.** `disagree.ensemble_answer_correct`: largest cluster; size ties → larger
summed confidence → single most confident answer; within the chosen cluster,
majority verdict, tie → the most confident member. `handlabel.py --result` uses
the same function and re-verifies 340/340. Tests in `tests/test_disagree.py`.

**Files.** `faultlines/disagree.py`, `scripts/handlabel.py`, `tests/test_disagree.py`.

### #68 · the independence headline pooled strata whose difficulty differs ~6×

**What.** Claim 12 multiplied four per-model error rates, each averaged over the
whole corpus, and compared the product with the observed all-four-wrong rate. The
datasets differ roughly six-fold in difficulty (TriviaQA ~8% all-wrong, PopQA
~45%), and pooling alone manufactures co-failure: if every model finds the same
dataset hard, they are "wrong together" even if independent within it.

**How found.** A reviewer recomputed the ratio within each dataset.

**Effect.** Pooled, pre-dedup: 26.9% observed vs 3.0% expected, **9.0×**, "an
order of magnitude". Pooled, deduplicated: 31.8% vs 5.2%, 6.1×, φ 0.654
(`independence.*`). **Within dataset: 10,819 observed vs 3,257 expected, 3.3×
[3.24, 3.41]** (`intervals.concordance`, bootstrap resampled within dataset);
mean pairwise φ within each dataset 0.44–0.60. The premise is still false —
three times as often is not independence — but the size of the claim fell by
two thirds.

**Fix.** The stratified ratio leads everywhere (author's decision, DECISIONS
2026-09-27). The pooled figure is kept, explained and demoted. "Order of
magnitude" is deleted from every document. `export_web.py` exports
`independence.stratified` and `intervals.concordance`.

**Files.** `scripts/export_web.py`, `RESULTS.md`, all chapters that quoted 9.0×.

### #69 · the inter-rater stratum was weighted with the wrong population

**What.** Finding 11b drew 70 cases "from the 296 uncontested"; the uncontested
stratum is **385** (430 hand-labelled − 45 disputed). The stratum weights, and
so the population κ, used 296 and a population of 341.

**How found.** Re-deriving the stratum sizes from the sampling frame:
19 of the 70 drawn cases have no first-annotator verdict, which is impossible if
they came from the 296 cases both raters had decided.

**Effect.** κ 0.962 [0.904, 1.000] → **0.970 [0.924, 1.000]**; agreement
98.7% → 99.0% (`irr.*`, population 430). Small, in the favourable direction, and
logged because the sentence describing the design was wrong.

**Fix.** `scripts/handlabel2.py: strata_sizes()` reads the stratum sizes from
the frame the sample was actually drawn against, frozen as
`adjudicated_noalias_irrframe.parquet` so that the #71 re-run cannot move the
strata of a sample already labelled.

**Files.** `scripts/handlabel2.py`, `scripts/export_web.py`.

### #70 · FIXED 2026-09-27 (after a paid re-run) · 15 empty RQ4 answers were counted as wrong

**What.** Fifteen RQ4 calls returned an empty string — 7 closed-book, 8 with
retrieval (`rq4_retrieval.parquet`, 570 rows) — and the grader scored each empty
string as a wrong answer. Standing rule 1 again.

**How found.** The review counted empty `answer` fields in `rq4_retrieval.parquet`.

**Effect.** Empty answers fell on both arms, so the direction of the bias on the
lift is not known in advance. The published +67.8% is now shown as +68.9%
(n=479) on the re-selected strata but is **not final**:
the strata were chosen from `records.parquet`, which changed under #66 and #67,
and the misconception stratum is now **57** cases rather than 70.

**Fix.** Code: `rq4_retrieval.py` treats an empty answer on either arm as a
failed call to be re-asked on resume, and drops rows no longer in the selection.
**Numbers: pending a paid re-run.**

**FIXED 2026-09-27.** Re-run on the re-selected strata; 0 empty answers on
either arm (557 rows). Obscurity n=500: closed-book 7.2% → retrieval 72.4%,
lift **+65.2%** [+60.8%, +69.6%]. Misconception n=57: 24.6% → 38.6%, lift
**+14.0%** [+0.8%, +27.3%], exact McNemar **p = 0.077 — no longer significant**
(was +15.7%, n=70, p = 0.027). Dissociation **+51.2%** [+36.9%, +65.3%],
10,000 bootstrap — still decisive. Retrieval now *barely moves*
misconceptions; the dissociation is the claim.

**Files.** `faultlines/rq4_retrieval.py`.

### #71 · FIXED 2026-09-27 (after a paid re-run) · 56 "UNCLEAR" adjudications were failed calls, and the 430-case adjudicator never saw the aliases

**What.** Two defects in the LLM adjudication.

1. `adjudicate_blind.py` resumed by counting every qid on disk as done. **56**
   2025-arm calls had returned nothing; they sat in the file as UNCLEAR and were
   reported as the judge *declining* to decide. On the deduplicated set the
   equivalent is 45 of 950 (`artifact.undecided`). *(27 Sep 2026 re-run: now 0.)*
2. `adjudicate.py` (the 430-case comparison behind claim 17) showed the judge
   the gold answer only, while the human had labelled against the gold **and**
   every alias. **40 of the 45** human/judge disputes were human = correct,
   judge = wrong — the signature of a narrower key, not a harsher judge.

**How found.** (1) by reading `judge_raw` for the UNCLEAR rows: all empty;
(2) by comparing the prompt the judge received with the screen the human saw.

**Effect.** (1) The artifact rate is computed over decided cases, so the rate is
roughly unaffected, but "the judge declined 56 times" was false. (2) Claim 17's
κ 0.688 compared two raters shown different answer keys; it is **withdrawn until
re-measured** and `adjudicator` is empty in `summary.json`. *(27 Sep 2026
re-run: now κ 0.782 — see below.)*

A smaller finding filed here: RESULTS and ch5 said the judge "misses about one
artifact in six". **10 of 62** is the share of the judge's *wrong* calls that the
human called correct — a different quantity. The miss rate on artifacts the
human caught is **10 / 40 = 25%** (the human called 40 of the judge-reviewed cases
correct: 30 the judge also flagged, 10 it did not). The direction of the
conclusion — 21% is nearer a floor than a ceiling — holds, and more strongly.

**Fix.** Failed calls are dropped on resume and re-asked; `adjudicate.py` joins
the alias lists back from `answers.parquet` and refuses to run if any case lacks
one. **Numbers: pending a paid re-run.**

**FIXED 2026-09-27.** (1) All 45 failed calls re-asked; **0 undecided**, all
950 decided. Artifact rate **21.05%** [18.58%, 23.76%], 200 of 950, **750
genuine** (was 21.1% of 905 decided, 759 genuine). Per dataset: HaluEval 33.88%
(366), PopQA 6.15% (439), TriviaQA 33.57% (140), TruthfulQA 40.00% (5). Knock-on
in #74: Qwen genuine growth 698 → 750, exact McNemar p = **0.102** (was 0.055);
adjudicated RQ3 239 / 459 / 511, 2.14× (was 520, 2.18×). (2) `adjudicate.py`
re-run with the alias lists: κ against the human **0.782** (91.5% agreement,
n = 341), was 0.688; human vs grader 0.459 unchanged; adjudicator vs grader
0.354 (n = 428). **Disputes with the human fell 45 → 29** — the 40-of-45
pattern above was the missing-alias signature. Unparseable 2 of 430.
Self-favouring: κ 0.816 on Qwen-family answers (85) vs 0.771 on the other
makers' (256), a small gap in the self-favouring direction, disclosed and not
claimed. The second-annotator frame stays frozen on the 45 no-alias disputes
(#69).

**Files.** `scripts/adjudicate_blind.py`, `scripts/adjudicate.py`.

### #72 · RQ1 and RQ2 cross-validated on unshuffled folds

**What.** `rq1_confidence.py` and `rq2_localize.py` called
`cross_val_predict(..., cv=5)`, which is an *unshuffled* `StratifiedKFold`. The
input file is sorted by dataset (checked: `records.parquet` runs TriviaQA,
PopQA, HaluEval in blocks), so each fold was dominated by one or two datasets and
each model was tested on a dataset mix it had not trained on.

**How found.** Reading the CV call in both modules during the review.

**Effect.** RQ1's two-feature comparison, re-run 27 Sep
(`python -m faultlines.rq1_confidence --full`, shuffled, seed from config, on
34,062): disagreement alone **0.839**, confidence alone **0.825**, combined
**0.862** — a +0.023 gain for confidence, against the published 0.847 / 0.831 /
0.871 (+0.024). The dedup (#66) and the shuffle change landed together, so the
movement is not attributed to either alone; the conclusion is unchanged. RQ2
re-run: popularity alone 0.653, + within-PopQA density 0.741 (+0.089) — the
finding got stronger.

**Fix.** `StratifiedKFold(5, shuffle=True, random_state=seed)` in both.

**Files.** `faultlines/rq1_confidence.py`, `faultlines/rq2_localize.py`.

### #73 · RQ1b's folds leaked across duplicate questions

**What.** `rq1_multifeature.py` built neighbourhood density out-of-fold (the two
leaks rule 6 caught in August), but its folds were over *rows*. A question's
duplicate (#66) — or the same question text under another qid — could sit in the
training fold, carrying its own label into the density feature and the model.

**How found.** Same review question as #66: why is the out-of-fold model so good?

**Effect.** AUC 0.601 → 0.811 becomes **0.592 → 0.772** (`rq1b.*`); risk at 50%
coverage 3.00%, at 25% 2.10%, against an 8.37% base (was 1.61% / 1.04% / 6.61%).
The record still carries signal where the vote is blind — about 0.18 AUC of it,
not 0.21.

**Fix.** `StratifiedGroupKFold(5, shuffle=True)` grouped by normalised question
text, on the deduplicated corpus.

**Files.** `scripts/rq1_multifeature.py`.

### #74 · the genuine blind-region growth used an unpaired test

**What.** "Genuine blind spots 778 → 837, p = 0.138" compared two proportions as
if the arms were independent samples. They are the **same questions** answered by
two ensembles; the right test is exact McNemar on the discordant pairs.

**How found.** The review asked which test produced 0.138; the answer was a
two-sample proportion test over the corpus size twice. On the pre-dedup data the
paired test read 0.077, not 0.138.

**Effect.** On the deduplicated corpus, genuine 698 → 759 (Qwen judge) and
678 → 716 (Olmo judge); exact McNemar p = **0.055** (Qwen) and **0.226** (Olmo)
(`arms.judges[].rq3.p_growth`). **Still not significant under either judge.**
*(27 Sep 2026 re-run, after #71's 45 failed calls were re-asked: Qwen now
698 → 750, p = **0.102**; Olmo unchanged. Less significant than before.)*
The conclusion ("the growth in the total is not distinguishable from chance; the
ratio is the robust finding") stands.

**Fix.** `scripts/artifact_by_arm.py` computes McNemar exact on per-question
genuine-blind status in both arms.

**Files.** `scripts/artifact_by_arm.py`, `scripts/export_web.py`.

### #75 · the 4-bit vs 8-bit control reported unweighted overlap on a weighted sample

**What.** The precision control ran on a stratified 2,554-question sample
(now 2,152 after dedup): every gen-3 blind spot plus a random draw of the rest,
so each control question stands for ~25 in the corpus. Persistence was
stratum-weighted; Jaccard and item-level agreement were not — #56's defect in a
different script.

**How found.** The review noticed the control used stratum weights for its rates
and not for its overlap.

**Effect.** Jaccard 0.780 → **0.644** (weighted); agreement 95.7% → **94.4%**
(unweighted on the deduplicated sample: 0.777 and 96.2%). Re-run 27 Sep,
`scripts/compare_precision.py`. The pre-registered tolerances still pass
(Δ persistence 0.028 < 0.05; Δ blind rate 0.0041 < 0.005), so 4-bit remains a
faithful stand-in for **rates**. But about a third of blind-spot *membership*
changes with precision, not a fifth: a specific question's blind-spot status at
one precision is a weaker guide to the other than claim 11 said.

**Fix.** Weighted overlap in `compare_precision.py`; the unweighted figure is
printed beside it.

**Files.** `scripts/compare_precision.py`.

### #76 · FIXED 2026-09-27 (after a paid re-run) · RQ5's tool loop stopped one turn early, and TruthfulQA was graded by cosine

**What.** Two defects in `rq5_agentic.py`.

1. The loop ran `MAX_STEPS + 1` turns. A model that asked for a fifth tool call
   got the "no tool uses left" nudge and the loop ended before it could answer.
   **Every one of the 85 missing Wikipedia-arm rows** was "empty after 4 tool
   calls".
2. Answers were graded with `grade_one` for every dataset, including TruthfulQA,
   where the closed-book arm used NLI. The comparison partly measured grading.

**How found.** Tracing why the matched set is smaller than the sample.

**Effect.** The current matched set is 116 questions (after dedup), with 76
(**65.5%**, [56.5%, 73.5%]) rescued by neither arm; the wiki-vs-web difference is
p = 0.388, noise. The 85 missing rows are all cases where a model wanted a fifth
tool call; whether they would have been rescued is not known, so neither is the
direction of the bias.

A smaller finding filed here: the tool's per-case note said *"here because the
2024 models were blind on it"* on **60** cases that are 2025 blind spots with an
incomplete search result — a note written for "now visible" cases, shown on
"newly hidden" ones (e.g. `halueval-00166`). The two situations now have
separate sentences.

**Fix.** Loop runs `MAX_STEPS + 2`; `grade_like_closed_book()` uses NLI for
TruthfulQA. **Numbers: pending a paid re-run.**

**FIXED 2026-09-27.** With the off-by-one fixed, the Wikipedia arm is complete
on **948 of the 950** current blind spots; 2 Llama runs still return empty after
4 tool calls and are recorded as failed calls, not data. The web arm covers 136.
Matched questions (complete in both arms **and** still a blind spot): **136**
(was 116). Still all four wrong with tools: **88 of 136 = 64.7%** [56.4%, 72.2%]
(was 65.5% [56.5%, 73.5%] of 116). Wikipedia rescues 39/136 (28.7%), the web
41/136 (30.1%); web minus Wikipedia +1.5pp [−4.3, +7.2], p = 0.80 — still noise.

Two changes made for the re-run, filed here rather than numbered: (a)
`export_web.py` now restricts RQ5 to the **current** blind spots — RQ5 had run on
the pre-dedup 1,054, and about 100 of those are no longer blind spots after the
dedup and the fixed tie rule (#66, #67), so "did search fix it?" was being asked of questions that
were no longer silent; (b) `rq5_agentic.py` gained `--resume-only`, which
completes only the questions already in an arm's file. The web sample is seeded
against `population()`, which shrank from 1,054 to 950 with the dedup, so
`--sample` would have drawn a *different* sample and paid to start it rather
than complete the one the thesis reports.

**Files.** `faultlines/rq5_agentic.py`, `faultlines-tool/index.html`,
`scripts/export_web.py`.

### #77 · every claim's interval was computed by hand, once

**What.** RESULTS.md's "Every claim, with its interval" table (2026-08-25) was
computed in one read-only session and typed in. Nothing re-derived it. When the
data changed (#66, #67) every row went stale silently — rule 5's "a number with
no source", in the one table that exists to give numbers their uncertainty.

**How found.** The review asked which script produces the table. None did.

**Effect.** Every interval changed, because every point estimate did (#66,
#67). The significance verdicts are re-read from the exported block, not carried
over.

**Fix.** `export_web.py` now computes them: `intervals.*` in `summary.json`
(Hanley–McNeil AUC, Wilson proportions, exact McNemar, paired and within-stratum
bootstraps, fixed seeds). The RESULTS table is re-written from that block.

**Files.** `scripts/export_web.py`, `RESULTS.md`.

### #78 · two analyses scored a different detector from the one they are compared with

**What.** The headline detector is the head-count score (`disagreement_unweighted`,
DECISIONS 2026-08-03: "head-count everywhere"). The ensemble ablation and the
TruthfulQA label-correction both scored the confidence-weighted `disagreement`
instead, so Chapter 5 set correlations and deltas computed on one detector beside
an AUC computed on another, under the same name.

**How found.** The records pass of the same review noted that `handlabel.py`
printed a corpus AUC of 0.8443 where the headline is 0.8403 — the two scores, not
one.

**Effect.** On the ablation, corr(φ, detection AUC) at k=2 moves from +0.781 to
**+0.927** (partial +0.766 → +0.922); at k=3/k=4 +0.718/+0.626 → +0.729/+0.611.
The direction of claim 15's trade is unchanged and at k=2 it is sharper. On claim
10, the label-correction delta moves from +0.046 [+0.002, +0.095] to **+0.042
[−0.000, +0.089]: the interval now crosses zero**, and the claim that correcting
the labels raises TruthfulQA's AUC is withdrawn.

**Fix.** `export_web.ablation_stats()` and the frontier panel read
`auc_unweighted`; `handlabel.py` scores `disagreement_unweighted`. The weighted
column stays in the parquet as the source of record.

**Files.** `scripts/export_web.py`, `scripts/handlabel.py`, `RESULTS.md`,
ch5/ch7/ch8.

### Smaller findings of the same review

Not numbered separately: each is filed under the defect whose class it belongs
to, and the header count does not include them.

| finding | effect | fix | filed under |
|---|---|---|---|
| The abstract said all four were wrong on "26.9% **of their errors**" | 26.9% was a share of *questions*; as a share of errors the sentence was false | abstract corrected in the 27 Sep chapter pass | #68 |
| The independence statistics were computed over `answers.parquet` **including the 40 ungradeable** TruthfulQA questions | small; every other figure excludes them | filtered on `gradeable` | #68 |
| The front matter overclaimed what `check_writeup.py` does (a fixed "223 figures", and a description implying every figure is verified) | it verifies the figures it has needles for, and the count had moved | wording narrowed to what the checker does, no hardcoded count | #77 (and #45's class) |
| `check_writeup.py` **passed a wrong copy of a repeated number**: a needle that finds its figure once is satisfied, so a mistyped second copy in the same chapter went unchecked | a wrong duplicate figure could sit in a chapter with the checker green | `near_misses()`: any number formatted like a checked figure, close to it (one digit off, two digits swapped, or within 1%), and in prose about the same thing, fails; deliberate lookalikes are whitelisted with a reason in `NEAR_MISS_OK` | #77 (and #60's class) |
| The tool's labelling panel printed `Math.round((obs+mis)*0.27)` — "roughly 1 in 4" searching would fix | a typed rate from another population (the RQ5 sample), contradicting "about 1 in 6" in the same tab | now counts the reader's own labelled cases that have a search result | #77 (rule 5) |
| A deck tooltip repeated **#48** — "about half are still wrong" (`majority_wrong` prose) over an `all_wrong` number | same understatement as #48, in a place #48's fix did not reach | now says all four are still wrong on about half | #77 (#48 recurring) |
| The tool's dataset checkboxes were not synced from the URL | a link carrying `ds=` filtered the queue while every box still read checked | `syncDsBoxes()` after every `applyHash()` | #62 recurring |
| An invalid `p=` in a link gave a **blank map** | a pick from another colouring hid every point | picks are kept only if they are bands of the colouring in force | #62 recurring |
| `capture_figures.py` reported **ok** when Chrome failed | a failed capture left last week's PNG in place, which passed the size test | the old PNG is deleted first; a non-zero exit or timeout fails | #77 (a check that could not fail) |
| `walkthrough_audit.py` described a deleted UI element (ISSUES #61) and **always exited 0** | the cognitive walkthrough could not fail in `reproduce.py` | text corrected; exits 1 if any task has a hidden step or an underivable answer | #77 (a check that could not fail) |
| The judge "misses one artifact in six" | 10/62 is the share of the judge's WRONG calls the human called correct; the miss rate on artifacts the human caught is 10/40 = **25%** | corrected in RESULTS and the chapters | #71 |

**The lesson of the batch.** Nine of the twelve would have been found by asking
one question of each result: *what, exactly, is the unit here?* A qid is not a
question (#66, #73); a pooled rate is not a within-dataset rate (#68); two arms
over the same questions are not two samples (#74); a weighted sample is not the
corpus (#75); an empty string is not an answer (#70, #71, #76). The project's
checks were strong on *values* — `check_writeup.py` has hundreds of needles —
and had nothing that asked about *units*.

---


Problems hit while building and running the pilot, what was done about each,
and what is still open. Newest first within each section.

Started 2026-07-19, during the first 300-question pilot run.

---

## 2026-07-28 · Baseline run — 4 more defects, one of them biased toward our own hypothesis

Found by a **new method: watching a live run's stderr**, which the 2026-07-27
session's six methods did not cover. All four are the same underlying mistake —
*a failed API call recorded as if it were a model's answer* — in the four places
that call the API. Defect #5 fixed exactly this in `generate.py` and the sweep
stopped there.

| # | Defect | Found by | Severity |
|---|---|---|---|
| 23 | **`baseline.py` recorded 429 failures as empty samples, no retry** — inflated Semantic Entropy in the arm we are competing against | live-run monitoring | **critical** |
| 24 | `baseline.py` resume counted empty-sample rows as done → contamination permanent across restarts | sibling prediction (#5) | major |
| 25 | `rq4_retrieval.py` wrapped BOTH arms in one `try` — a failure on the retrieval arm discarded the closed-book answer that had already succeeded | sibling prediction (#5) | **critical** |
| 26 | `screen.py` no retry, and resume counted empty answers as done | sibling prediction (#5) | major |
| 27 | **`check_provider.py` blocked a working run** — treated `/v1/models` absence as fatal and never made the call | queued-run failure | major |

### #23 in detail — the one that matters for the result

`baseline.py` caught its own exceptions and appended `""` to the sample list:

```python
except Exception as e:
    print(f"  !! {q['qid']}: {e}")
    a = ""
out.append(a)
```

The empty string is then a **real sample** as far as `entropy()` is concerned. It
clusters on its own, so it manufactures self-inconsistency that never happened.
Measured on the first 9,800 rows of the 8,000-question run:

```
82 rows carried >= 1 empty sample   (1.0%)
mean entropy, rows with empties     0.713
mean entropy, clean rows            0.207     <- 3.4x
```

**Why this is worse than an ordinary bug:** the ensemble arm has had retries
since #6. The baseline arm did not. So provider throttling degraded *only the
competitor*, and it degraded it by adding noise to the exact quantity — Semantic
Entropy — whose AUC is being compared against ours. The bias ran in the
direction that **flatters this project's hypothesis**, which is the direction to
distrust on principle. At 1.0% the effect on AUC is small; the reason to fix it
rather than footnote it is that "small, and in our favour" is not a defensible
sentence in a viva.

### #25 in detail — a null result the harness could have invented

RQ4 asks whether retrieval fixes an error, by comparing closed-book vs
retrieval-augmented answers **from the same model**. Both calls sat inside one
`try`. A failure on the second call sent `cb = rag = ""`, so the closed-book
answer that had already come back was thrown away and both arms graded
wrong-and-identical — i.e. *"retrieval changed nothing."* That is precisely the
null hypothesis RQ4 exists to test. Not yet run, so no data is affected.

### #27 in detail — the safety gate that failed the wrong way

The gen-2 full run was queued behind `check_provider.py`, which has caught real
problems before (3 dead Together IDs, the logprobs dialect). It refused:

```
MISSING   Qwen/Qwen2.5-7B-Instruct
MISSING   mistralai/Mistral-7B-Instruct-v0.3
MISSING   google/gemma-2-9b-it
NOT ready. Fix the above before any paid run.
```

Those three models had produced **1,200 clean rows the previous day**. Probed
directly:

```
SERVABLE  Qwen/Qwen2.5-7B-Instruct            'Paris'  conf=0.985
SERVABLE  mistralai/Mistral-7B-Instruct-v0.3  'Paris'  conf=0.806
SERVABLE  google/gemma-2-9b-it                'Paris'  conf=0.855
```

They were **delisted from `/v1/models`, not withdrawn.** The gate checked the
catalogue, found them absent, and `continue`d — *skipping the live call that
would have answered the question correctly.* A heuristic was allowed to
short-circuit the authoritative test.

**Fixed:** absence now prints `DELISTED ... probing anyway` and the real call
decides. If the call also fails, the message says the model is likely withdrawn
for good. Confirmed by the run that followed: **132,000+ generations on those
three delisted models, 0 failures.**

**Why this one is worth reporting.** Defects 1–26 all produced *wrong numbers*.
This one produced *no numbers* — it failed closed, which feels safe and is the
behaviour a gate is supposed to have. But a false refusal is still a false
result: it would have removed RQ3's only clean comparison from the thesis, and
the log said `NOT ready`, which reads like the models are broken rather than the
check. **A gate needs its own false-positive rate stated, exactly like the
detector it protects.** That symmetry is worth a paragraph in the write-up,
since this project's entire subject is a detector that must not cry wolf.

### The fix — one retry policy, not four

Four modules had four copies of the retry loop (or the absence of one).
`generate.ask_retry()` is now the single implementation and `generate.py`,
`baseline.py`, `track.py`, `screen.py` and `rq4_retrieval.py` all call it. This
is the direct lesson of defect #20: fixing a shared behaviour in one copy and
leaving the others is worse than not fixing it, because the components then
disagree with each other instead of being uniformly wrong.

The resume rule is now uniform too, and stated once: **a row containing an empty
answer is a failed call, not a result, and must not count as done.**

### CHECKED AND CLEARED (2026-07-28) — grading-tier asymmetry between Track arms

**Raised as a possible confound, measured, dismissed. Kept because the check is
the reusable part, and because the alarm itself was a misread.**

**The alarm.** The live grading log printed `semantic tier 45,000/92,966` on the
gen-2 arm against 4,573 rows on gen-3, and I read that as a twentyfold difference
in how often the negation-blind cosine tier was *deciding* verdicts. If true it
would matter: RQ3 counts **silent consensus** (all four models agree AND all four
are wrong), and every wrong answer the grader mistakenly passes **removes a case
from that population** — so an arm graded more generously would show artificially
fewer blind spots.

**The misread.** `92,966` is the number of rows *sent to the encoder*, not rows
*decided as* semantic. Almost all of them come back below threshold and are
recorded as `wrong`. Actual decided tiers:

| tier | gen-3 | gen-2 |
|---|---|---|
| exact | 76,956 | 62,685 |
| wrong | 70,867 | 88,126 |
| alias | 8,816 | 7,633 |
| contains | 8,366 | 7,043 |
| **semantic** | **3,839 (2.3%)** | **3,357 (2.0%)** |
| nli | 1,520 | 1,520 |

**2.3% vs 2.0%** — not 2.7% vs 54.6%. The arms are graded almost identically.

**Three measurements, all clearing it:**

1. **Tier mix inside the silent-consensus population**: 99.2% `wrong` (gen-2) and
   99.5% `wrong` (gen-3). Structural — a question only becomes silent consensus
   if every answer is wrong, and `wrong` is the terminal verdict. The semantic
   tier cannot *create* a case, only remove one.
2. **Encoder pass rate**: gen-3 5.1%, gen-2 **3.7%**. Cosine is *less* generous
   on gen-2, so any residual bias runs **opposite** to the concern — it would
   inflate gen-2's count, not suppress it.
3. **Direct exposure** — questions whose only correct answers came from the
   semantic tier, i.e. the cases that could have been silent consensus but were
   graded out: **gen-3 1,030 · gen-2 998.** Within 32 of each other. Symmetric,
   and far too small to manufacture a 52% persistence rate.

**Conclusion: RQ3's full-scale numbers are not a grading artifact.** Quote them
without this caveat.

**What to keep.** The check itself — *tier mix inside the population under study,
not corpus-wide* — is the right test whenever two arms with different accuracy
are compared on an all-wrong subset. And the discipline held: the check was
specified before the number was visible, which is the only time it can be
specified honestly. That it cleared rather than confirmed is not a wasted step;
an unfalsified concern is worth exactly as much as a falsified one, and this one
cost four minutes.

**The lesson about the alarm.** A progress counter (`45,000/92,966`) was read as
a result. Progress output is not measurement output, and the two look identical
in a terminal. Recompute from the data before raising a confound — I did not,
and the corpus-wide claim in this file was wrong for about twenty minutes.

### Method note for the write-up

Sibling prediction (the cheapest method in the 07-27 table) found three of these
four — but only *after* live-run monitoring surfaced the first one. It is a
force multiplier on a known defect, never a way to find the first instance.
That is the argument for keeping a run visible while it executes rather than
waiting for the exit code: **#23 raised no error and would have finished
"successfully."**

---

## 2026-07-27 · Debugging session — 22 defects found, all fixed

Recorded for the write-up. The analytically interesting cut is **how each was
found**, because no single method found more than half.

### Summary

| # | Defect | Found by | Severity |
|---|---|---|---|
| 1 | 3 of 4 chosen model IDs not serverless (400) | pre-run gate | blocking |
| 2 | **logprobs dialect** — Together returns `token_logprobs`, code read only OpenAI's `content` | pre-run gate | **critical** |
| 3 | Qwen2.5-7B `<think>` truncated by `max_tokens` → empty answers | targeted probe | **critical** |
| 4 | the fix for #3 (`enable_thinking=false`) **breaks** Qwen3-235B | targeted probe | critical |
| 5 | failed generations persisted, counted as done on resume | output inspection | **critical** |
| 6 | 8.3% transient failure rate under 12-way concurrency, biased to TruthfulQA | output inspection | major |
| 7 | `run_pilot.py` (the documented entry point) destroys the frozen pilot | code audit | **critical** |
| 8 | `check_provider.py` validated a drifted `ensemble_hosted` key | code audit | **critical** |
| 9 | `tag` missing in embed / rq1 / rq2 / screen → analyse the wrong experiment | code audit | major |
| 10 | `grade.run()` silently reverts NLI verdicts to cosine | code audit | major |
| 11 | `screen --pool 20000` silently screens 300 and reports a yield | code audit | major |
| 12 | `track.py` reads deleted `ensemble_gen1` key → KeyError | code audit | major |
| 13 | `track.py` omits the `gradeable` filter `disagree.run()` applies | code audit | major |
| 14 | `track.py` repeats the #5 resume bug | code audit | major |
| 15 | `grade.py` tier-3: ~143k single-item encoder calls at full scale | code audit | minor |
| 16 | `rq4` hardcodes `ensemble[0]` | code audit | minor |
| 17 | `rq2.popularity_control` unused parameter | code audit | trivial |
| 18 | `.env` with a live key inside a cloud-synced folder | code audit | minor |
| 19 | **containment tier stale list mis-graded TriviaQA (42% of corpus)** | slice test | **critical** |
| 20 | `grade_one` kept a *duplicate* of the #19 logic — fixed in one copy only | key sweep | **critical** |
| 21 | `disagree.py` repeats #15 → 68 min on the full corpus | sibling prediction | minor |
| 22 | progress monitor double-counted defects (18 reported, 9 real) | self-check | trivial |

### Discovery methods, and what each was blind to

| method | found | structurally could NOT find |
|---|---|---|
| **Pre-run gate** (`check_provider.py`) | 1, 2 | anything past the first API call |
| **Targeted probe** of one model | 3, 4 | anything not being probed |
| **Output inspection** | 5, 6, 19 | logic that never produced visible output |
| **Code audit** (13 passes) | 7–18 | `"Sheppey"` marked wrong — correct-looking code, wrong result |
| **Key sweep** (grep literals vs config) | 20 | anything not keyed on a config value |
| **Sibling prediction** | 21, 24, 25, 26 | novel bugs with no precedent — needs a first instance to generalise from |
| **Live-run monitoring** (2026-07-28) | 23 | anything that fails without printing |
| **Queued-run failure** (2026-07-28) | 27 | anything that fails *permissively* — a gate that wrongly passes leaves no trace |

**The finding worth reporting:** the code audit read 14 modules and never saw #19,
because `SHORT_SPAN = ("popqa", "simpleqa")` is a deliberate, well-commented
decision that is only wrong if you know the dataset list changed hours earlier.
The slice test caught it in one line of output. Conversely the slice test could
never have found #20, because the duplicate code path *produced no output* — it
is only reachable from `track.py`.

**Cheapest method by far was #21's:** after fixing a bug, ask whether its sibling
module has the same one. Found in 30 seconds, no audit, no run.

**#20 is the cautionary one.** Fixing #19 by adding a new function and leaving the
old copy in place made things *worse* than not fixing it: the main pipeline and
`track.py` would have graded TriviaQA **differently**, producing disagreement
between components rather than uniform, detectable wrongness.

### Failure classification

**Every critical defect was a SILENT failure** — HTTP 200 with an empty answer,
a resume that skipped failures, a grader that reverted itself, a gate checking
the wrong list, a truncated screen reporting a yield. **None raised an error.**
All would have produced confident, plausible, wrong numbers.

The countermeasure that worked: **cheap runs that fail loudly before expensive
runs that fail silently.** A 12-question probe caught #3. A `limit=2` smoke test
caught a missing import. A 200-question slice caught #19 before 172,000
generations were graded with it.

### Residual failure rate (not a defect)

The live full run shows **9 failures in 39,000 generations (0.023%)** — transient
API timeouts that exhausted 3 retries. Down from the 8.3% measured before the
retry fix (#6). These are backfilled by a resume pass, because the `done` set now
excludes NaN-confidence rows (#5).

---

## RESOLVED 2026-07-27 — the containment tier silently mis-graded TriviaQA

**Severity: high.** Found by a 200-question slice test before the full run.

`grade_one` applied the containment tier only to `("popqa", "simpleqa")` — a
list written before TriviaQA and HaluEval existed, and still naming SimpleQA
after it was dropped. TriviaQA is **42% of the corpus**.

Measured on the slice: **31% of TriviaQA's "wrong" verdicts were correct
answers.** Examples — `"Sheppey"` for gold `"Isle of Sheppey"`, `"12th fret"`
for `"12th"`.

**Why lowering the semantic threshold is NOT the fix.** Cosine similarity is
unreliable on short entity spans. Measured on this corpus:

| pair | cosine | truth |
|---|---|---|
| "Henley Rowing Club" vs "Leander Club" | **0.781** | WRONG answer |
| "Sheppey" vs "Isle of Sheppey" | **0.526** | RIGHT answer |

The encoder ranks a wrong answer *above* a right one, so no threshold separates
them — the same class of failure as the TruthfulQA negation blindness (#1),
but for proper nouns rather than negation. Dropping the threshold to 0.70 to
rescue "Sheppey" would also accept "Henley Rowing Club" as "Leander Club".

**Fix.** `contains_either_way()` — word-boundary containment in both
directions, with a length-ratio guard on the risky direction. The ratio matters:
`"Sheppey"/"Isle of Sheppey"` is 0.47 and correct, `"York"/"New York City"` is
0.31 and is a *different city*. A bare substring test accepts both. Applied to
`SHORT_SPAN = (popqa, simpleqa, triviaqa, halueval)`; TruthfulQA stays excluded
because its golds are sentences.

**Verified:** re-graded the slice — **0 rows flipped correct → wrong**;
TriviaQA 85.5% → 89.0%, HaluEval 44.5% → 47.0%, TruthfulQA unchanged. Pinned by
`tests/test_grade_contains.py` (7 tests).

**Consequence for earlier numbers.** The dataset-probe figures recorded in
`config.yaml` and `DECISIONS.md` (TriviaQA 70.8%, HaluEval 45.4%) were measured
with the buggy grader and therefore **understate accuracy**. They were used only
to choose datasets, and the choice does not change — but do not quote them as
accuracy results.

---

## RESOLVED 2026-07-27 — a fix that made things worse: duplicated grading logic

Fixing the containment tier (#19) added `grade_lexical()` as a NEW function and
left `grade_one()`'s original inline copy in place, still gated on the stale
`("popqa", "simpleqa")` list.

`grade.run()` uses `grade_lexical`. **`track.py:112` calls `grade_one` directly.**
So the main pipeline graded TriviaQA correctly while every Track arm graded it
wrongly — the two components would have *disagreed with each other*, which is
worse than both being wrong, because the error is no longer uniform or
detectable by comparison.

Found by grepping every dataset-name string literal against the config keys, a
check the original audit ran for *ensemble* keys but not *dataset* keys.

**Fix:** `grade_one` now delegates to `grade_lexical`. One implementation.
Pinned by `test_grade_one_and_grade_lexical_agree_on_the_containment_tier`.

**Lesson for the write-up:** a fix applied to one of two duplicate
implementations is worse than no fix at all.

---

## RESOLVED 2026-07-27 — `disagree.py` repeated the grader's N+1 encoder pattern

`disagree.run()` called `cluster()` once per question; `cluster()` calls the
sentence transformer. Measured **96.2 ms per question**, i.e. **~68 minutes** on
the 42,591-question corpus, nearly all of it encoder start-up rather than work.

Found not by audit or by running anything, but by **asking whether the sibling of
an already-fixed module had the same bug** — the cheapest technique used all day.

**Fix:** `semantics.cluster_many()` embeds every question's answers in one call
and runs the identical greedy pass over pre-computed vectors. `score()` accepts
pre-computed `ids`.

**Verified identical, twice:** 0 mismatches on 300 synthetic groups (37x faster),
and re-running `disagree` on the gen-3 data reproduced the on-disk records
exactly — 0 differences across `disagreement`, `disagreement_unweighted`,
`n_clusters`, `majority_wrong`, `silent_consensus`.

Projected: **49 min -> 1.3 min.**

---

## Status at a glance (batch history — updated 2026-08-03)

### The count lives in the header at the top of this file, and nowhere else.

> This heading used to carry its own total ("39 defects found, 38 fixed"), which
> went stale on 2026-07-29 and disagreed with the header by five for a week — a
> hardcoded number that stopped tracking its source, i.e. exactly defect #43 in
> prose form. The table below is the batch *history*; it does not total itself.

| batch | count | status |
|---|---|---|
| 2026-07-27 debugging session | #1–22 | **ALL FIXED** |
| 2026-07-28 baseline run | #23–27 | **ALL FIXED** |
| 2026-07-28 RQ4 (four attempts) | #28–30, 29b | **ALL FIXED** |
| 2026-07-28 provider identity | #31 | **FIXED** — gate added; 2 arms VOID, quarantined |
| 2026-07-28 audit of that day's own fixes | #32–35 | **ALL FIXED** |
| 2026-07-29 resume × in-place column write | #36 | **FIXED** + 3 regression tests |
| 2026-07-29 deployment & UI | #37, #38 | **FIXED** — stale live numbers; `[hidden]` losing to an ID selector |
| 2026-08-01 answer-key ambiguity | #39 | **NOT FIXABLE** — documented limit, flag reworded |
| 2026-08-03 measurement audit | #43, #44 | **BOTH FIXED** — a hardcoded `0` in the exporter, and a sentence naming the wrong one of two adjacent definitions |
| 2026-08-07 explaining the deck aloud | #45 | **FIXED** — a third hardcoded count; the total is now derived from this file |
| 2026-08-07 sweep for the #45 pattern | #46 | **FIXED** — the map's stray count was measured on one axis and described as two |
| 2026-08-07 the one page with no exporter | #47 | **FIXED 2026-08-08** — `pipeline.html` published the pilot, including a *reversed* baseline result, one click from the deck; now reads `summary.json` like the deck and the tool |
| 2026-08-08 first audit of tabs 3 and 4 | #48 | **FIXED** — "about half are still wrong" put `majority_wrong` prose over an `all_wrong` number, understating by 26 points |
| 2026-08-10 reported by Shivani | #49 | **FIXED** — `<divclass=` broke slide 18's rendering; plus a stale "42 defects" the literal sweep's own noise filter could not see |
| 2026-08-10 walking Walkthrough 1 | #50 | **FIXED** — the map's box filtered tab 2 and nothing in tab 2 said so. First defect found by *using* the tool |
| 2026-08-10 reading tab 2 | #51 | **FIXED** — the panel explaining why labelling matters was hidden until you had already labelled |
| 2026-08-10 reading tab 2 | #52 | **FIXED** — "every case here was re-run with search" was true of 61% and shown on 100%, contradicting the per-case line below it |
| 2026-08-25 → 2026-09-07 | #53–#65 | **ALL FIXED** — see the entries near the end of this file |
| **2026-09-27 adversarial review** | **#66–#78** | **ALL FIXED** — #70, #71, #76 closed the same day after a paid re-run — duplicates, the tie rule, the pooled independence ratio, and nine more. See "2026-09-27 · Adversarial review" near the top |

Test suite: **62 passing**. Last full debug 2026-08-01: 13 parquet files clean,
8/8 cross-file invariants hold, deployed == source on all 4 web files.

### Methodological items — all closed

| item | status |
|---|---|
| 1b. razor-thin NLI margins | **✅ RESOLVED 2026-07-29** — 430 cases hand-labelled. Zero open items. |
| A. confidence weighting | RESOLVED — reversed at scale, now neutral (+0.003) |
| B. TruthfulQA weak signal | ANSWERED — small-model artifact, not label noise |
| C. Audit data-starved | **CLOSED** by the full run — 1,054 cases, not 5 |
| 1. negation-blind grader | FIXED (`nli.py`) |
| 2. low model accuracy | RESOLVED (hosted ensemble) |
| 3. Ollama upgrade | OBSOLETE |
| containment tier mis-graded TriviaQA | FIXED 2026-07-27 |

### Permanent scars — closed, not fixable

| item | consequence |
|---|---|
| #31 provider substitution | 340,728 generations VOID (`data/void/`). Hosted RQ3 retracted; rebuilt locally. |
| Gemma-2 context sensitivity | ~7 h speedup rejected — reduced context changes its answers. |
| `correct_cosine` for 1,288 rows (#36) | Overwritten on disk; recomputed with the original grader. Diagnostic only. |

### Standing watch list (cautions, not defects)

See "Open methodological watch list" below: effects shrink as n grows (5/5),
grader error runs one direction, bias has favoured our hypothesis, hosted models
have a shelf life. Plus, added 2026-07-29: **resume interacts with every in-place
column write** — `if "col" not in df.columns` is a review flag (#23/#24/#26/#36).

---

## Entries (historic detail preserved for the write-up)

### A. ~~Confidence weighting does not help~~ — RESOLVED (twice)

**Superseded 2026-07-23 and again 2026-07-27.** First: RQ1 showed the fix is to
treat confidence and disagreement as two FEATURES, not one blended score
(0.763 -> 0.805 -> 0.820 combined). Then the scale test REVERSED the original
finding outright -- weighting helps on 17-27B models (0.801 vs 0.793 unweighted)
and only hurt at 7-9B. The method was never wrong; it needs models whose
confidences are calibrated. See RESULTS.md Finding 1.

<details><summary>original entry (kept for the write-up)</summary>


**Measured on the full pilot, all four models.** Plain vote-counting beats the
confidence-weighted disagreement score on two of three datasets:

| dataset | weighted | unweighted | delta |
|---|---|---|---|
| PopQA | 0.845 | **0.872** | −0.027 |
| SimpleQA | 0.687 | **0.738** | −0.051 |
| TruthfulQA | **0.534** | 0.517 | +0.016 |
| **overall** | 0.776 | **0.788** | −0.013 |

This matters because the proposal presents the confidence-weighted score as an
improvement, using the worked example 0.25 (unweighted) → 0.09 (weighted). That
example still shows what the weighting *does*; it no longer supports the claim
that weighting makes the signal *better*.

**Confidence is not useless** — that is the important nuance. On its own it
predicts error at AUC **0.749** (mean confidence 0.768 when right, 0.581 when
wrong). So both signals carry information; multiplying them into a single number
is what loses it.

**Recommended direction:** treat confidence and disagreement as two *features*
rather than one blended score — a small logistic regression over
(disagreement, mean confidence, min confidence, n_clusters). That is a stronger
story than either alone and is a better answer to "why is your score shaped like
that?" than the current derivation.

**Decision needed:** whether to (a) reframe the score in the proposal as
combining two features, (b) keep weighting and report it honestly as
neutral-to-slightly-negative, or (c) run the regression first and decide after.
Option (c) costs about an hour on data already on disk.

</details>

### B. ~~TruthfulQA carries no signal~~ — ANSWERED, cause identified

**The weak signal is real, but it is a SMALL-MODEL artifact, not label noise.**
Two independent tests agree that noise is not the cause: correcting all 19
LLM-judge disagreements moved the AUC 0.534 -> 0.551 (+0.017), and re-splicing
those labels in 2026-07-27 moved it +0.013. Meanwhile the hosted 17-27B ensemble
took TruthfulQA from 0.517 to 0.661. Cause = model scale.

Human hand-labelling is still worth doing, but it is now **confirmatory** (it
supplies the inter-annotator agreement the proposal promises), not decisive.

<details><summary>original entry (kept for the write-up)</summary>


AUC by dataset, against `majority_wrong`:

| dataset | AUC | |
|---|---|---|
| PopQA | 0.845 | strong |
| SimpleQA | 0.687 | weak but real |
| **TruthfulQA** | **0.534** | coin flip |

TruthfulQA scored **0.806 with cosine grading and 0.534 with NLI grading**. The
strong number was an artifact of the broken grader (#1), which is exactly why it
was worth fixing before reporting anything.

Two readings, not yet separable:

1. **Genuine.** TruthfulQA is built so models fail *together* on shared
   misconceptions. Disagreement cannot detect a fault everyone shares — which is
   the premise of Audit, and would make this a *finding* rather than a failure.
2. **Label noise.** 31% of TruthfulQA verdicts have an NLI margin below 0.10,
   i.e. near-arbitrary. Enough noise in the labels will flatten any AUC.

**How to separate them:** hand-label ~50 low-margin TruthfulQA cases and
recompute. If the AUC stays near 0.5 with clean labels, reading 1 holds and it
strengthens the Audit narrative. Half a day, and it doubles as the
inter-annotator agreement work already on the list.

</details>

### C. ~~Audit is data-starved~~ — BEING FIXED BY THE FULL RUN

The pilot's 5 silent-consensus cases came from 300 questions. The full corpus is
**42,591**, i.e. 142x. At the pilot rate that is ~700 cases before screening.

<details><summary>original entry (kept for the write-up)</summary>


**5 silent-consensus cases in 300 questions** (all-agree-all-wrong): 1 PopQA,
3 SimpleQA, 1 TruthfulQA. Scaling to 2,800 gives roughly **45**.

Two things worth noting. Most of them are *not* in TruthfulQA, which is where the
proposal expects to find them — so sourcing silent-consensus cases from all three
datasets is now clearly necessary rather than a contingency. And 45 hand-analysed
cases is a thin basis for a headline finding.

**Options:** keep Audit as a qualitative case study over ~45 examples and say so;
or relax the definition from "all four agree" to "three of four agree and all are
wrong", which will yield substantially more cases while still capturing the
blind-spot phenomenon. The second changes what the finding claims, so it is your
call.

</details>

### 1. ~~Semantic grader blind to negation~~ — FIXED by `nli.py`

Entailment grading against TruthfulQA's own `incorrect_answers` replaced cosine
for that dataset. The entry below predates the fix and is kept because the
*measurement* in it is write-up material.

<details><summary>original entry (kept for the write-up)</summary>


**Severity: high.** This one can quietly corrupt results.

Sentence embeddings place a claim and its negation close together. Measured
directly:

```
"Bears wear armor"  vs gold "Bears do not wear armor"
  -> cosine > 0.80 -> graded CORRECT
```

In the pilot, **37% of TruthfulQA answers were decided by that tier**, above the
35% threshold at which I flagged it unsafe. So TruthfulQA accuracy is inflated
by an unknown amount.

Why it matters more than it looks: the error runs in the *flattering* direction.
Real errors get recorded as successes, which

- **shrinks the Audit population** (all-agree-all-wrong cases get scored as
  all-agree-all-right and disappear), and
- **inflates the AUC**, because genuine errors are relabelled as non-errors.

Both make the project look better than it is, which is the dangerous kind of bug.

**Fix written, not yet run:** `faultlines/nli.py`. Instead of asking "does the
answer resemble the gold?", it asks a natural-language-inference cross-encoder
to choose between TruthfulQA's own `correct_answers` and `incorrect_answers`.
Those baited wrong answers are exactly the near-miss negations that fool cosine,
so forcing a choice between them attacks the failure head-on. Applied to
TruthfulQA only — NLI on a bare noun phrase ("Betty Comden") is meaningless, and
PopQA/SimpleQA are already handled by the exact/alias/contains tiers.

Deliberately **not** fixed by raising the global cosine threshold: that would
break paraphrase matching on PopQA, which the tests pin.

Run after the pilot completes:

```bash
python -m faultlines.nli --pilot
python scripts/run_pilot.py --report-only
```

It preserves the old verdict in a `correct_cosine` column so the two gradings can
be compared, and reports how many verdicts flipped. Expect accuracy to **drop** —
that is the correct direction.

</details>

### 1b. NLI margins are razor-thin — ✅ RESOLVED 2026-07-29 by hand-labelling

**Measured at full corpus 2026-07-29** (previously 29% on 72 rows — that sample
was itself the product of defect #36, see below):

```
gradeable truthfulqa answers   1,360
low margin (<0.10)               439    32.3%
verdicts NLI changed vs cosine   529    38.9%
accuracy   cosine 50.4%  ->  nli 71.5%
```

**Nearly a third of TruthfulQA verdicts are near-arbitrary** — the entailment
model could not separate the correct answer from the baited one either. Confirmed
against an LLM judge at Cohen's kappa 0.240. This does NOT explain the weak
TruthfulQA AUC (see B — that is a small-model artifact), but it does mean **no
TruthfulQA number may be quoted without this caveat**.

The 38.9% flip rate is the other half of the story and is worth reporting in its
own right: **grader choice changes more than a third of TruthfulQA verdicts**, and
it moved accuracy by +21 points. A dataset whose score depends that heavily on
the grading method cannot carry a headline claim regardless of hand-labelling.

### RESOLVED — 430 cases hand-labelled, blinded, two strata

Full result in RESULTS.md (2026-07-29). The three things that closed it:

1. **The grader is fine where it claims confidence.** Control stratum: 99.0%
   agreement, **kappa 0.959**, 1 disagreement in 97. Target stratum: kappa 0.322.
   The unreliability is confined to the band the grader itself flags.
2. **26.1% of the low-margin band could not be decided BY A HUMAN** (86 of 330)
   against 3.0% of controls. The near-zero margin is a correct report of genuine
   ambiguity in TruthfulQA, not a computation failure. This reframes the issue
   from "our grader is weak" to "a quarter of TruthfulQA is undecidable under its
   own rubric" — a benchmark property, and defensible.
3. **Residual error is bounded at ~11 of 1,360 answers.** The correction is ~90%
   complete. Only the control stratum makes that statement possible.

TruthfulQA AUC 0.651 → **0.712**, delta **+0.061 (95% CI +0.018 to +0.109)**,
does not cross zero. Corpus AUC unmoved: 0.8651 → 0.8654 (341 of 170,364 answers
relabelled). Reproduce: `python scripts/handlabel.py --result`.

**The caveat that must still travel with any TruthfulQA number:** n=340, both
bootstrap CIs are ±0.07 wide and they overlap. Quote the delta, not the point
estimate. And 89 unclear cases retain their machine verdict — the conservative
choice, since dropping them would shrink n and guessing them would invent labels.

<details><summary>original entry (kept for the write-up)</summary>


Found while building the fix for #1, before running it.

The entailment grader compares the answer against TruthfulQA's correct answers
*and* its baited incorrect ones, then picks the winning side. It works — every
correct answer tested grades right and every bait grades wrong — but the
**absolute** scores are sometimes tiny, and the margin between the two sides can
be almost nothing:

```
answer                                                correct  bait   verdict
"Nothing happens to you"                                0.446  0.000  OK
"Nothing"                                               0.029  0.000  OK  (thin)
"The watermelon seeds pass through your digestive..."   0.974  0.971  OK  (+0.004!)
"You grow watermelons in your stomach"                  0.000  0.997  WRONG
```

The third row is a correct answer that beat the bait by 0.004. That is a coin
flip, not a judgement. So `nli.py` records a **`nli_margin`** column and
`run_pilot.py` reports how many verdicts fall below 0.10. Those are the cases to
hand-check rather than trust.

Two design points worth keeping:

- **Bidirectional entailment is required.** Forward-only scores 0.000 for every
  terse answer above, because "Nothing" cannot entail a sentence carrying extra
  detail. One-directional grading would mark correct short answers wrong — the
  same class of bug as #6.
- **Do not add an absolute threshold.** "Nothing" scores 0.029 and is correct.
  A floor would throw away true answers.

The label index was verified empirically (`{0: contradiction, 1: entailment,
2: neutral}`) against three unambiguous cases rather than trusted from docs — a
wrong index would have silently inverted every grade.

</details>

### 2. ~~Low model accuracy~~ — RESOLVED by the hosted ensemble

<details><summary>original entry (kept for the write-up)</summary>


Pilot, first two models:

| | PopQA | SimpleQA | TruthfulQA |
|---|---|---|---|
| llama3.1:8b | 29% | 12% | 39% (unreliable, see #1) |
| qwen2.5:7b | 24% | — | — |

SimpleQA at 12% is **not** a bug — the benchmark is built so frontier models
score around 40%, so 7–8B models scoring low is expected. Spot-checked wrong
answers are genuine confident hallucinations, not grading failures:

> *Who was the composer of Chances Are?* → "Robert Goulet" (gold: Maurice Jarre)
> *Who is the author of Revolution?* → "Hugo" (gold: Russell Brand)

Plenty of errors is good for signal. The thing to watch is the opposite risk:
if models are wrong in *four different ways* on most questions, disagreement
saturates near 1.0 and stops discriminating. The pilot's AUC will show this.

</details>

### 3. ~~Ollama upgrade pending~~ — OBSOLETE

The project no longer runs on Ollama. Inference is hosted (DeepInfra); the local
path is retained only to reproduce the frozen 7-9B pilot.

<details><summary>original entry (kept for the write-up)</summary>


Deferred until the pilot finishes so all 1,200 generations come from one
inference version. `data/processed/RUN_PROVENANCE.txt` records the version used.
If the upgrade changes inference behaviour, **re-run the pilot rather than
topping it up** — mixing inference versions inside one sample is not defensible.

---

</details>

## RESOLVED

### 0. The AUC label was implied by the score (circularity)

**The most important thing the pilot found.** Caught before reporting, on the
first three models.

The original prediction target was `any_wrong` — "was any of the four models
wrong on this question?" That label is **mechanically determined by the
disagreement score**. There is one gold answer, so if N models give N different
answers, at most one can match: "someone was wrong" follows by arithmetic, not
by evidence.

Measured on the pilot:

| distinct answer clusters | → `any_wrong` true |
|---|---|
| 3 | **100.0%** |
| 2 | 92.7% |
| 1 (all agree) | 41.5% |

Scoring a predictor against a label its own input determines is circular. It
produced a flattering **0.911 AUC** that would have looked like a headline
result and meant nothing.

This is the same failure the project already guards against on the map — where
position must come from question wording alone, so that clustering by
disagreement is a finding rather than a construction. The rule was applied to
the map and missed here.

**Fixed:** the target is now `majority_wrong` — is the answer the ensemble would
*actually give* wrong? Disagreement does not determine this: models can split
with the majority still correct, or agree unanimously and all be wrong.

| target | AUC | verdict |
|---|---|---|
| `any_wrong` | 0.911 | inflated — discarded |
| **`majority_wrong`** | **0.800** | the honest number |
| `all_wrong` | 0.750 | consistent |

0.800 sits right where the literature does (Farquhar 0.790, Gorbett 0.727
cross-model), which is itself a sanity check: a result far *above* published
work on the same task should have prompted suspicion, and did.

`evaluate.TARGET` is now a single named constant so the target cannot drift
silently, and `run_pilot.py` prints the cluster/label crosstab plus both AUCs
side by side every run, so the inflation stays visible rather than being
quietly fixed and forgotten.

**Watch this for SimpleQA:** its AUC is 0.571 (useless) because 91% of its
answers are wrong — almost no correct answers remain to separate. That is a
property of the dataset's difficulty for 7–8B models, not a failure of the
signal. PopQA 0.826 and TruthfulQA 0.806 both hold.

### 4. `aliases or []` crashes on parquet data

`ValueError: The truth value of an array with more than one element is ambiguous.`
Parquet returns numpy arrays, and truthiness on an ndarray raises. Fixed with an
explicit length check in `grade.py`. Caught by a 6-question dry run before the
full run wasted an hour.

### 5. Answers containing the gold were marked wrong

`"Gene Kelly and Betty Comden"` vs gold `"Betty Comden"` → graded wrong. Not a
hallucination; marking it so inflates the error rate the pilot exists to measure.

Added a **containment tier**, restricted to PopQA and SimpleQA. Deliberately not
applied to TruthfulQA: its golds are sentences, a substring hit means nothing
there, and negation ("bears do NOT wear armor") would flip the meaning while
still containing the words. Guarded against short-token false positives with a
4-character minimum and whitespace boundaries.

### 6. TruthfulQA prompt/answer-key shape mismatch

The system prompt demanded "shortest correct answer, no full sentence", but
TruthfulQA golds are **full sentences** ("Bears don't wear anything when they
fight in the wild"). Terse answers could never match at the exact or alias tier,
so a third of the pilot would have been marked wrong for a prompt artifact
rather than a real error.

Fixed by making `system_prompt` per-dataset in `config.yaml`. The baseline uses
the same per-dataset prompt, so the two arms still differ only in *where* the
four generations come from.

### 7. `truthful_qa` dataset id no longer resolves

`HfUriError: Repository id must be 'namespace/name'`. Changed to
`truthfulqa/truthful_qa`. PopQA and SimpleQA column mappings were verified
correct against live data at the same time.

### 8. Pilot log appeared frozen

Python block-buffers stdout when redirected to a file, so a running job showed
no output for ~15 minutes and looked hung. It was fine — Ollama had burned 310s
of CPU. Fixed with a flushing `print` in `run_pilot.py`. Progress can also be
read directly from the checkpoint parquet at any time.

### 9. venv could not be created inside the project

`[WinError 206] The filename or extension is too long` — the project sits deep
under OneDrive and torch ships a vendored path that blows Windows' 260-character
`MAX_PATH` limit.

venv moved to **`C:\venvs\faultlines`**, outside the project. Documented in the
README.

### 10. numpy upgrade broke the anaconda base environment

**My mistake.** I ran `pip install sentence-transformers` without a venv active,
which hit anaconda base and upgraded numpy 1.26.4 → 2.4.6, breaking h5py and
TensorFlow for unrelated projects. Restored to 1.26.4 and verified h5py and
TensorFlow 2.19 import again.

Note that base has a **pre-existing unsolvable conflict**: TensorFlow needs
numpy<2.2 while opencv and mlxtend need ≥2. 1.26.4 is the side h5py was compiled
against.

**Rule going forward: never `pip install` with the bare `python` on PATH.** Use
`C:\venvs\faultlines\Scripts\python.exe` explicitly.

---

## Watch list — not yet problems

- **Audit may be data-starved.** TruthfulQA is 817 questions total; the
  all-agree-all-wrong subset could be a few dozen. Issue #1 makes it look
  smaller than it is. Real size unknown until the NLI re-grade runs.
- **Quantization noise.** All four models run 4-bit, so some measured
  disagreement may be a quantization artifact rather than a knowledge
  difference. Quantization is identical across all four so the noise is at least
  uniform. Report as a limitation regardless.
- **No inter-annotator agreement** on the ~250 planned hand labels (Level 9).
  Cheap fix: a second labeller on 50 cases, report the agreement rate.

---

## Open methodological watch list (2026-07-28)

Things that are not defects but will shape future decisions. Recorded so they
are not rediscovered late.

### 1. Effects keep shrinking as n grows — three for three

| effect | small n | large n |
|---|---|---|
| confidence-weighting delta | +0.008 (300q) | +0.003 (42,551q) |
| cross-model vs best single SE | +0.116 (300q) | +0.062 (8,000q) |
| PopQA AUC "degradation" | 0.761 (300q) — flagged as a finding | 0.798 (14,267q) — noise |

**Every effect measured at 300 questions has been smaller or absent at scale.
None has grown.** The pilot did not merely have wide error bars, it was
systematically optimistic — plausibly because a small sample lets a real but
weak effect land anywhere, and the ones that landed *large* are the ones that
got written up. That is selection on the outcome, performed by the sample size.

**How to apply:** treat every remaining 300-question number as an upper bound,
not an estimate. Nothing pilot-scale enters the thesis as a result without a
full-scale rerun — and the reruns cost ~$1.20 each, so there is no excuse.

### 2. The grader's error runs in one direction

Every known grading weakness (cosine negation-blindness, containment without a
ratio guard, semantic tier generosity) turns **wrong answers into apparent
correct ones**. None turns correct into wrong. That means all grading noise
*shrinks* the silent-consensus population and *flatters* the AUC.

**How to apply:** a grading fix that increases the Audit population is expected
and confirmatory; one that decreases it deserves scrutiny. And any AUC quoted
should be read as a mild over-estimate, which is worth one sentence in the
limitations rather than a defensive paragraph.

### 2b. WHY NOTHING WORKS — similarity cannot decide identity

**The most reusable observation in this project.** Recorded 2026-08-01 after
three separate automated methods failed on the same cases.

**The problem.** Every model answers "Bangladesh"; the key demands "People's
Republic of Bangladesh". Right answer, marked wrong. Now: every model answers
"York"; the key says "New York City". Wrong answer, marked wrong — correctly.
**Automatically separating those two situations is the task.**

**What was tried, and the numbers:**

| method | RIGHT case (Bangladesh) | WRONG case (York) | outcome |
|---|---|---|---|
| character-length ratio | 0.33 | 0.31 | indistinguishable |
| cosine similarity (the grading tier, threshold 0.80) | **0.776** — rejected | **0.891** — accepted | **INVERTED, measured 2026-08-01.** Earlier logged as "~0.65" from memory; re-measured on the actual encoder. The wrong pair scores *higher* than the right one, so no threshold separates them: pass Bangladesh at 0.776 and York (0.891) passes too; reject York above 0.891 and Bangladesh goes with it. Also "China"/"People's Republic of China" **0.596**, "Sheppey"/"Isle of Sheppey" **0.526** — both right, both below two *wrong* pairs |
| **NLI bidirectional entailment** | 0.827 | **0.969** | **inverted.** The wrong pair scores highest of ten controls; "China"/"People's Republic of China" scores 0.257, second lowest |
| Wikipedia canonical title | Bangladesh = Bangladesh ✅ | York ≠ New York City ✅ | 4/6 — right on both hard cases, misses "Sheppey"/"Isle of Sheppey" |

**Both learned graders are inverted on the hard band, not merely weak.** Cosine
and NLI independently rank "York"/"New York City" *above* "Bangladesh"/"People's
Republic of Bangladesh". That kills the obvious objection — *"you just picked a
bad threshold"* — with an ordering argument rather than a tuning argument. There
is no threshold, because the two cases are on the wrong sides of each other.

**THE REASON, and this is the part to carry into the write-up:**

> Embeddings and entailment models encode **similarity**. The question being
> asked is **identity** — are these two strings the same thing in the world?
>
> "York" *is* highly similar to "New York City". That similarity is precisely
> **why it is a plausible wrong answer**. So the grader fails for the same reason
> the model did: both are reasoning from resemblance, and resemblance is exactly
> what a good distractor exploits.
>
> Lowering a threshold to admit the right answers necessarily admits the wrong
> ones, because on this axis they are not separated. There is no threshold.
> The information is not in the representation.

**How to apply.**

1. **Do not tune.** Any bar that admits "Bangladesh" admits "York" and
   "Leander Club = Henley Rowing Club". Proven, not assumed.
2. **Do not add another similarity model.** NLI was the strongest tool available
   and it was *worse than cosine* here. A fourth would be a fourth failure.
3. **A knowledge base is the only method that helped** — entity resolution
   answers an identity question with identity data. Wikipedia redirects got 4/6.
   Machinery exists in `rq4_retrieval.py`; not built, because 60 cases do not
   justify a network dependency.
4. **Surface the band, do not hide it.** The tool flags these cases as a
   judgement call and a human decides. This is the design justification for the
   Audit view existing at all.

**The generalisation:** *automated grading of open-ended QA has an irreducible
ambiguous band.* Any paper reporting a single accuracy number on this kind of
task is reporting a point estimate over a band it did not measure. This project
measured it: **5.6% of the Audit population**, which is why 1,054 is published as
an upper bound.

### 3. Bias has consistently favoured our own hypothesis

Defect #23 (baseline arm had no retry) degraded only the competitor. The grading
asymmetry above shrinks only the harder-to-explain population. The pilot
overstated every effect that got written up.

**None of these were deliberate**, and that is the point worth recording: the
project's defaults quietly lean toward its hypothesis, so "does this error help
or hurt my claim?" is now a required question for every defect found, not an
optional one. Where the answer is "it helps", the fix is not optional either.

### 3b. A CORRECT pipeline can still publish a WRONG finding — through its labels

**Recorded 2026-08-01. Found by the user, not by a test, not by me.** Reading the
tool's Generation-diff tab: *"how can 'newly broken' show the right answer in the
2025 models but the wrong answer in the 2024 models?"*

**The check.** Every one of the 690 was re-examined. **Zero contradictions** — no
`emerged` case has a correct 2025 answer. The clustering, the grading, the
category assignment and the export were all correct. Nothing in the data or the
code was wrong.

**What was wrong was the word.** The categories were displayed as *newly broken /
still broken / fixed*, i.e. on an axis of **correctness**. They are computed on an
axis of **detectability**:

| shown as | is actually | the number that exposes it |
|---|---|---|
| "newly broken" 690 | **newly hidden** | **538 (78%)** were *also* all wrong in 2024 — they merely **disagreed**, so a check caught them. Only 152 genuinely regressed. |
| "fixed" 559 | **now visible** | **293 (52%)** are *still* all wrong in 2025. Nothing was fixed; the disagreement came back. |
| "still broken" 364 | **hidden in both** | correct as displayed, for the wrong reason |

So the displayed finding was "newer models break 690 questions" — a claim about
capability that the data does not make, that is trivially attackable, and that
**understates** the real result. The real one is about detectability:

> Newer models go **blind** on nearly twice as many questions as they inherit —
> not because they are more often wrong, but because they increasingly **agree**
> when they are wrong.

**Why this class of defect is invisible to the whole apparatus.** 62 tests, a
13-file parquet integrity check, an export reconciliation against RESULTS.md and
a browser pass all agree the numbers are right — because **they are right**. No
assertion can be written against a category *name*. The defect lives in the gap
between the column `emerged` and the English word rendered above it, and that gap
is only crossed by a human reading the screen and saying "that does not match
what I am looking at."

**Two consequences worth carrying into the write-up.**

1. This is the second finding-level error caught by the user rather than by the
   test suite (the first: the deployed page serving the retracted 0.788, #37).
   Both were in the **presentation layer**, which had no review loop at all until
   #37 forced one. Correct data displayed under a wrong name is a wrong result —
   it should be logged with the same weight as a numerical defect, and it now is.
2. It is a direct argument for the visual-analytics framing. A table of
   `364 / 559 / 690` is *unfalsifiable by inspection* — the mislabelling survives
   it indefinitely. Rendering the individual cases next to their own answers is
   what made the contradiction visible in seconds. **The tool caught an error in
   the thesis the tool exists to support.**

**How to apply:** every category label on a public surface must be traceable to
the predicate that computes it. Where the predicate is `all_wrong_2025 &
~all_wrong_flag_2024`, the label may not say "broken" — it says what the
predicate says. Checked once across the tool, the deck and all five records
(2026-08-01).

### 4. Hosted models have a shelf life (see 2026-07-28 in DECISIONS.md)

Three of four gen-2 models were delisted within 24 hours of first use. Raw
generations are checkpointed, so analysis is reproducible; regeneration is not.

**How to apply:** run every planned hosted arm now, not after the VA work.

---

## 2026-07-28 (later) · #31 — the provider served DIFFERENT MODELS under the requested names

**The most serious defect of the project. It invalidated a headline result that
had already been reported.**

### Evidence

Identical answer strings, same run, same questions:

| pair | identical answers | verdict |
|---|---|---|
| gemma-3-12b vs gemma-3-27b | 15.3% | genuinely different (control) |
| gemma-2-9b vs gemma-2-27b | 15.4% | genuinely different (control) |
| Qwen2.5-7B vs Qwen3-235B | 9.0% | genuinely different (control) |
| **gemma-2-27b vs gemma-3-27b** | **99.6%** | **same served weights** |
| **gemma-2-9b vs gemma-3-12b** | **95.9%** | **same served weights** |
| Mistral-7B-v0.3 vs Mistral-Small-3.2 | 89.3% | almost certainly same weights |

Calibration: the SAME model queried in two different runs reproduces at 86–93%.
Genuinely different models agree at 9–18%. 95.9% and 99.6% are at or above the
same-model reproducibility ceiling, so those pairs are one model with two names.

### When

```
2026-07-27 (models still listed)   gemma-2-9b vs gemma-3-27b    2.3%   <- REAL
2026-07-28 (delisted)              gemma-2-9b vs gemma-3-12b   95.9%   <- aliased
```

The substitution coincides with the delisting recorded the same morning. Mistral
looks aliased on BOTH days (80.3% / 89.3%), so that one may predate the delisting.

### What it invalidated

- **RQ3 full-scale ("52% of blind spots persist") — RETRACTED.** Two of the gen-2
  arm's four models were gen-3 models, so the comparison was partly a model
  against itself.
- **The Gemma 2x2 ladder — VOID.** Two of four cells were duplicates. 170,364
  generations, executed flawlessly, measuring nothing.
- Yesterday's 300-question RQ3 is partially salvageable: Gemma was real, Mistral
  probably was not.

### What it did NOT invalidate

The gen-3 ensemble was put through the new identity gate and **all six pairs
agree 0%**. The full-corpus AUC 0.862, the 1,054-case Audit population, the
per-dataset table and the Semantic Entropy baseline all stand.

### Why every previous check passed

`check_provider.py` verified: reachable ✓, answers ✓, returns logprobs ✓. All
three were true of the substitute. **Availability is not identity.** No
single-model probe can detect substitution; only comparing OUTPUTS ACROSS model
IDs can, because the defect is a relationship between two names, not a property
of either one.

This is the same blind spot the project studies: a check that looks at each item
alone cannot see a property that only exists between items. FaultLines detects
hallucination by comparing models to each other rather than examining one model
harder. The gate now does the same thing for model identity.

### Fix

`check_provider.py::identity_check()` — asks every model in an ensemble the same
8 obscure-entity questions (deliberately NOT "capital of France", where all
models agree and agreement proves nothing) and refuses to run if any pair agrees
above 50%. Threshold sits in the empty gap between the 9–18% different-model band
and the 86–99% same-model band, so it is not a knife edge.

Verified against the known-bad ensemble: flags the two aliased pairs at 100% and
passes the four real pairs at 0%.

### Provider availability, measured 2026-07-28

| model | DeepInfra | Together |
|---|---|---|
| Llama-3.1-8B | listed, real | 400 non-serverless |
| Qwen2.5-7B | delisted, real | serverless ✓ |
| Mistral-7B-v0.3 | delisted, **aliased** | 400 non-serverless |
| gemma-2-9b | delisted, **aliased** | 400 dedicated-endpoint only |
| gemma-2-27b | delisted, **aliased** | 400 non-serverless |

**No serverless provider will honestly serve the gen-2 ensemble.** This is not a
budget problem; the models are being retired industry-wide. The only trustworthy
source is local weights, which are content-addressed and cannot be substituted.

---

## 2026-07-28 · RQ4 took FOUR attempts — defects 28, 29, 29b, 30

Recorded in full because the sequence is the clearest example in the project of
a **silent failure producing a publishable-looking result**. Three consecutive
runs produced coherent tables. All three were wrong.

| # | Defect | Severity |
|---|---|---|
| 28 | `rq4_retrieval.run()` printed its summary and never wrote the results | major |
| 29 | `retrieve()` cached FAILURES as "nothing found", permanently | **critical** |
| 29b | MediaWiki hammered at ~5 req/s against a ~1 req/s limit — the cause of #29 | major |
| 30 | The retry logger crashed the run on a non-ASCII entity name | major |

### #28 — results printed, not saved

Two live API calls per case, 570 cases, and `run()` ended with `print()`. Every
rerun paid for the generations again, and the per-case answers -- the thing a
human actually inspects when a lift looks wrong -- were unrecoverable. Now
writes `rq4_retrieval.parquet`, checkpoints every 25 cases, and resumes on the
same rule as every other module: an empty answer on either arm is a failed call,
not a result.

### #29 — the cache that made failures permanent

`retrieve()` swallowed every exception into `out = []` and wrote that empty list
to the cache next to genuine no-results. MediaWiki throttled a 570-case sweep and
**497 of 566 cache entries (88%) were stored as "nothing found"**. Because the
cache is checked before the network, a rerun would have reproduced the same wrong
answer forever and looked deterministic doing it.

Retested: **19 of 20 cached-as-empty queries returned results on retry.**

Same defect family as #23 and #25 -- a failed call recorded as a result -- and the
first instance OUTSIDE the model-calling path, which is exactly why the sibling
sweep missed it. Every module calling `ask()` had been checked; the module
calling Wikipedia had not.

**Fixed:** retried with backoff, and a failure is NEVER cached. 497 poisoned
entries purged (backed up to `retrieval_cache.json.poisoned.bak`).

### #29b — the request pattern that caused it

The original issued **1 search + up to 3 extract calls per case** with a single
0.2s sleep after all four: ~2,280 requests for a 570-case sweep at ~5/s, against
an anonymous limit of ~1/s. The 429s were guaranteed by the design, not bad luck.

**Fixed:** one request per case via `generator=search` feeding `prop=extracts`,
plus a process-wide 1.5s throttle. A quarter of the traffic for the same data.

### #30 — the error handler that killed the process

```
UnicodeEncodeError: 'charmap' codec can't encode '\u0142'
  ... in retrieve(), line 98, INSIDE the except block handling a 429
```

Retry logging died on **Władysław Sławny**: cp1252 cannot encode `ł`, so
`print()` raised from inside the handler dealing with the rate limit. The process
died, and the traceback blamed Unicode rather than throttling.

**An error handler that cannot report its error takes the process down with it
AND misdirects the diagnosis.** PopQA is full of non-ASCII entity names, so this
was certain to fire. All retry logging is now ASCII-safe via `_safe()`.

### The retrieval-quality problem underneath all of them

Even with every bug above fixed, the experiment was still measuring nothing,
because Wikipedia *search* on an entity question returns topically-adjacent
noise. Measured as "is the gold answer present in the retrieved context at all":

| retrieval strategy | gold in context |
|---|---|
| full-question search | **8%** |
| entity name extracted from the PopQA template | 22% |
| `s_wiki_title` -- PopQA's own canonical article title | **~70%** |

`datasets.py::_popqa` had kept `s_pop`/`o_pop`/`prop` and dropped `s_wiki_title`.
Recovered via `scripts/fetch_popqa_titles.py` (100% coverage of the corpus) and
joined on question text; the frozen corpus was not regenerated.

Passage length was tested and **is not the constraint** -- 600 chars 66%, 2000
chars 68%, full text 70%. ~70% is simply the ceiling for Wikipedia lead sections
on rare entities, because some answers live only in an infobox. `PASSAGE_CHARS`
set to 2000, the knee.

### Why this sequence matters for the write-up

| attempt | retrieval | obscurity lift | would have been reported as |
|---|---|---|---|
| 1 | search + cached 429s | +0% | "retrieval does not fix obscurity" |
| 2 | search | +0% | same |
| 3 | entity search | +2% | same |
| 4 | `s_wiki_title` | **+68%** | the actual result |

**Attempts 1-3 all produced a defensible-sounding claim that was the opposite of
the truth.** Nothing about the output looked broken; the tables were internally
consistent and the numbers were plausible. What killed each version was one
check that nobody asks by default: *is the answer even present in the context?*
That check cost four minutes and invalidated three runs.

**The general lesson:** a positive control only controls if you verify the
control fired. "The control showed no effect" is not a result -- it is a reason
to doubt the instrument.

### Also fixed in passing

`check_provider.py` had NO retry, so a transient 429 reported a working model as
broken. Same false-negative shape as #27, in the same file. Now uses `ask_retry`.

---

## 2026-07-28 (evening) · Audit of the code written TODAY — defects 32–35

A lot of code went in under time pressure today (`ask_retry`, `use_provider`,
the whole retrieval ladder, the identity gate, four new scripts). Audited on the
same principle that found #21: after fixing a defect, ask whether the fix's own
siblings share it.

| # | Defect | Impact on results | Status |
|---|---|---|---|
| 32 | `entity_of()` regex **guessed** the PopQA templates: 92.1% coverage | **none** — see below | fixed, 100% |
| 33 | `rq4_retrieval` grew **two** copies of the retry+cache loop | none yet | consolidated |
| 34 | Unicode crash fixed at ONE call site, leaving every other print exposed | none yet | fixed globally |
| 35 | `build_rq3_local` rebuilt a 1,054-element set per row | none, just slow | fixed |

### #32 — the regex guessed instead of deriving

`_TEMPLATES` was written from memory of what PopQA questions look like. Measured
against the real corpus: **92.1%**. The misses:

```
Who is the father of {}?     570   <- I wrote "who WAS the father of"
What is {} the capital of?   363   <- reverse-direction template, absent entirely
Who is the mother of {}?     187   <- same tense error
```

**Fixed by deriving the templates from the data** rather than guessing again:
substitute each row's known `subj` out of its question and count distinct
results. 16 real templates; coverage now **100.0%** (3 stragglers are malformed
source rows — literally `"Who is the author of ?"` with an empty subject).

**Impact on the RQ4 result: none.** `entity_of` is only the *fallback* in the
retrieval ladder, and `s_wiki_title` covers **100%** of the PopQA questions RQ4
used, so the fallback never fired. A latent defect, caught before it mattered —
but it would have mattered the moment the title map was unavailable.

**The lesson is the same one as #29b and the throughput benchmark:** a value
derived from the actual data beats one written from memory, and the derivation
was three lines.

### #33 — the fix that duplicated itself

`retrieve()` and `retrieve_title()` each carried their own throttle-retry-cache
loop, written within an hour of each other **while fixing #29**. That is defect
#20's exact shape: a shared behaviour in two copies, so a later fix lands in one
and the pair silently diverges. The rule that must never drift here is *a failure
is never cached* — the whole substance of #29.

Collapsed into `_wiki_cached(key, params, label)`. Both endpoints return the same
`query.pages` shape, so parsing is shared too. `for attempt in range` now appears
**once** in the module. Both paths live-verified after the refactor.

### #34 — a call-site patch where a root-cause fix was needed

#30 was fixed with `_safe()` on the two retry log lines. That fixed those two
lines. The very next thing that printed a Wikipedia extract — a verification
script — **crashed on "Marie Skłodowska Curie"** with the identical
`UnicodeEncodeError`.

Root cause is that Windows consoles default to cp1252 and this corpus is full of
non-ASCII entity names. Fixed once, in `config.py`, which every entry point
already imports:

```python
for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")
```

**A logging call must never be able to end a run.** Patching the call site treats
the symptom; the class of bug is "any print of corpus text can kill the process".

### What the audit did NOT find

Checked and clean, stated rather than padded:

- **Resume rules** — all five modules that write answers (`generate`, `baseline`,
  `track`, `screen`, `rq4_retrieval`) exclude failed rows from `done`. No drift.
- **No remaining failure-as-result paths** — every `= []` / `= ""` is an
  accumulator initialiser, not a swallowed exception.
- **One retry policy for model calls** — `ask_retry` is the only one; no module
  reimplements it.
- **`use_provider()` global mutation** — process-scoped and intentional; the only
  other reader (`check_provider`) sets it explicitly before use.
- **59 tests pass** after every change.

### Method note

Three of these four were introduced by *today's fixes*, not by the original code.
Fixing #29 created #33. Fixing #30 created the false confidence behind #34.
**The most dangerous moment for a codebase is immediately after a defect is
fixed**, because attention moves on while the fix is still fresh and unreviewed.
Worth a line in the write-up alongside the discovery-method table.

---

## #36 · CRITICAL · `nli.py` initialised columns by PRESENCE, so resume left 159,988 rows None

**Found** 2026-07-29, by the full-corpus local run exiting 1 at its last stage
after ~9 hours of generation. **Fixed** same day. Regression tests added.

### Symptom

```
File "faultlines/disagree.py", line 64, in run
    dropped = df.loc[~df["gradeable"], "qid"].nunique()
TypeError: bad operand type for unary ~: 'NoneType'
```

### Cause

`nli.run` initialised three columns only when the column was **absent**:

```python
if "gradeable" not in df.columns:
    df["gradeable"] = True
```

That assumes an answers file is either fully fresh or fully processed. The
full-corpus run broke the assumption: it **extended** a file that had already
been through nli — 2,554 questions on disk from the quantization subset, 40,037
appended per model. The column existed, so nothing was initialised, and pandas
left `None` in every appended row.

```
answers_rq3local.parquet   170,364 rows
  gradeable       None 159,988   True 10,216   False 160
  correct_cosine  None 160,148
```

### Why this is worse than a crash

The crash was the *lucky* consequence. The damaging one is silent, and it had
already happened by the time the crash fired:

```python
gradeable = mask & df["gradeable"]      # None -> False
```

Every appended row was treated as **ungradeable**, so `nli.run` printed

```
truthfulqa accuracy  46.1% (cosine) -> 59.7% (nli)
verdicts changed     28 of 72
```

over **72 of 1,360** gradeable rows — 5.3% of the data — with no indication that
the population was truncated. The repaired figures over the full population:

| statistic | printed (n=72) | true (n=1,360) |
|---|---|---|
| cosine accuracy | 46.1% | **50.4%** |
| NLI accuracy | 59.7% | **71.5%** |
| verdicts changed | 28 (38.9%) | **529 (38.9%)** |
| low-margin <0.10 | 21 (29%) | **439 (32.3%)** |

Had `disagree` not crashed, RQ3 would have been computed on ~6% of the corpus
and reported as a full-corpus result. **The crash was dtype luck**: object-dtype
`None` raises on `~`, but a nullable-boolean `NA` would have propagated silently
and dropped 147,000 rows while looking entirely normal.

### Blast radius — checked, contained

Every answers file was audited. Only the extended one is affected:

| file | rows | `gradeable` None |
|---|---|---|
| `answers.parquet` (gen-3 headline, AUC 0.862) | 170,364 | **0** ✅ |
| `answers_rq3local_q8.parquet` (8-bit control) | 10,216 | **0** ✅ |
| `answers_pilot*.parquet` (3 files) | 1,200 ea | **0** ✅ |
| `answers_rq3local.parquet` | 170,364 | **159,988** ❌ |

No published result was affected. The condition requires nli to have run on a
file that is *later extended*, which only the full-corpus local rerun did.

### Fix

1. **Root cause** — extracted the init into `nli.ensure_columns(df)`, which fills
   **per row** and never gates on column presence. `gradeable` → `fillna(True)`
   then `astype(bool)`; `correct_cosine` → `.where(notna, df["correct"])`;
   `nli_margin` → `pd.to_numeric(errors="coerce")`.
2. **Repair** — `scratchpad/repair_rq3local.py`. Recomputes `gradeable` from
   scratch via the library's own `is_ungradeable` (it is a pure function of
   dataset+gold, so fully recoverable, no model needed) and recomputes
   `correct_cosine` for 1,448 TruthfulQA rows via the library's own
   `grade.grade_one`. Backup at `answers_rq3local.parquet.predefect36.bak`.
   No reimplementation of either rule — a second copy is how #33 happened.
3. **Tests** — `tests/test_nli.py::test_ensure_columns_fills_appended_rows`
   plus fresh-frame and idempotence cases. Mutation-checked against the old
   logic: it counts **3 of 10** rows and `~` raises. The test fails on old code.

### What was NOT recoverable

`correct_cosine` for the 1,288 appended TruthfulQA rows was genuinely lost on
disk — `correct` had been overwritten with the NLI verdict and saved. Recomputed
with the same deterministic cosine grader that produced it originally. Affects a
diagnostic only; `disagree` never reads it.

### Standing lesson (fourth entry in this pattern)

**Resume interacts with every in-place column write.** Defects #23, #24, #26 and
now #36 are all the same shape: a stage assumed it sees a whole file, and resume
handed it a partial one. Any new `if "col" not in df.columns` is now a review
flag by default.

And the meta-observation holds again: **the corruption ran in the flattering
direction.** 59.7% reported vs 71.5% true would have understated NLI's benefit,
but the *mechanism* — silently shrinking n to 5% — is the same mechanism that
produced the retracted 52% RQ3 and the three wrong RQ4 tables. A number computed
on an unverified population is the recurring failure of this project, not an
incident.

---

## #37 · ✅ RESOLVED — the DEPLOYED site published retracted numbers

**Found** 2026-07-29 while scoping the front-end rebuild. **Open** until the
rebuild ships.

`final_proposal/faultlines-web/index.html` is live at faultlines-peach.vercel.app
and states **AUC 0.788** in seven places. That is the 300-question gen-2 local
pilot figure. The corpus result is **0.865**, and Finding 1 explicitly records
that the pilot's confidence-weighting conclusion *reversed* at scale.

`faultlines-tool` is worse in a quieter way: **291 points and 5 blind spots**,
i.e. the pilot's Audit population, which ISSUES item C recorded as too small to
support any claim. The real figures are 42,551 and 1,054.

**Why this is logged as a defect rather than a to-do.** Everything else in this
project was wrong *in private* and got caught before publication. This is wrong
*in public*, on a URL that may already have been shared with an advisor, and it
is wrong in the flattering-to-nobody direction: it understates the work by two
orders of magnitude on the Audit population, which is the thesis's central
contribution.

**Fix:** the front-end rebuild (DECISIONS 2026-07-29). Both artifacts get current
numbers; the tool gets rebuilt at full scale, the narrative site gets its numbers
corrected only.

**Standing rule added:** a published artifact is a result. It belongs in the same
review loop as RESULTS.md — no number reaches a public page that has not been
checked against the current parquet.

---

## #38 · `[hidden]` lost to an ID selector — the tool showed a permanent loading screen

**Found** 2026-07-29 on the first browser open of the rebuilt tool. **Fixed** same day.

The page set `#loading{display:grid}` and `#app{display:grid}`, then hid the
overlay with `element.hidden = true`. **An ID selector outranks the UA
stylesheet's `[hidden]{display:none}`**, so the overlay kept its `display:grid`
and stayed painted over the app forever.

```
hidden attribute : true
computed display : grid        <-- still visible
overlay height   : 1061px      <-- covering the whole viewport
```

**The failure mode is the interesting part.** The tool was *working perfectly
underneath*: 42,551 points drawn in 25 ms, all 1,613 cases queued, every filter
live. `console` was clean — no error, because nothing errored. A screenshot
showed only "loading 42,551 questions…". Anyone opening it would have reported
"the tool doesn't load", and the obvious next move — debugging the fetch or the
canvas — would have been in entirely the wrong place.

Diagnosed by comparing the DOM to the painted frame: the DOM said the app was
visible, the pixels said otherwise, which narrows it to CSS immediately.

**Fix:** `[hidden]{display:none!important}`, with a comment naming the cause.
One of the few legitimate uses of `!important` — it is asserting the UA default
against a specificity accident, not winning a cascade fight.

**Lesson:** `.hidden = true` is not reliable on any element whose `display` is
set by an ID or class selector. Prefer a state class, or ship the `!important`
rule once per page.

---

## #37 UPDATE — artifacts rebuilt, reconciled against RESULTS.md (deploy since done)

Both artifacts now read their numbers from `summary.json` / `tool/data.json`,
generated by `scripts/export_web.py`, and every figure was reconciled against
RESULTS.md before shipping. Two mismatches were caught in that reconciliation and
are worth recording because both would have put a number on a public page that
contradicts the thesis:

| quantity | first draft | RESULTS.md | cause |
|---|---|---|---|
| per-dataset AUC | 0.800 / 0.873 / 0.840 / 0.651 | 0.798 / 0.868 / 0.834 / 0.646 | draft used the **confidence-weighted** column, RESULTS quotes **unweighted** |
| RQ4 lift | obscurity 71.7%, misconception 31.4% | **+68% / +16%** | draft computed *"share of closed-book failures that retrieval fixed"*; Finding 5 defines lift as *retrieval rate − closed-book rate over the whole stratum* |

Both are defensible quantities. Neither is *the* quantity, and a page showing
one while the thesis shows the other is indefensible. The exporter now computes
both AUC variants and labels them, and matches Finding 5's definition exactly,
each with the reason in a comment.

Also fixed in the same pass: a copy-paste defect where `auc` and `auc_weighted`
were computed from the same column, so the page would have shown two identical
numbers under different names.

### ✅ CLOSED 2026-07-29 — both artifacts deployed and verified live

| | |
|---|---|
| deck | https://faultlines-peach.vercel.app |
| tool | https://faultlines-tool.vercel.app |

Verified against production, not localhost: deck serves the new 14-slide deck
with `summary.json` (200) and `TOOL_URL` wired; tool loads **42,551 points,
1,613 cases, AUC 0.862, 1,054 blind spots** from a 2.97 MB `data.json` (200).
The retracted 0.788 is gone from every public surface.

**A near-miss recorded in DECISIONS:** connecting the repo left Root Directory at
`.` on both projects, which would have 404'd both live URLs on the next push.
Fixed via `--output-directory` before it fired. Consistent with this issue's own
lesson — a published artifact is a result, and its *deployment config* is part of
the result.

---

## #39 · The answer-key flag has false positives — by necessity, not by mistake

**Found** 2026-08-01, in the same debugging pass that introduced it. Kept, with
the wording corrected.

`export_web.key_too_strict()` flags a blind spot when every model answer sits
inside the gold but was rejected by the 0.4 short-form ratio guard. Edge-case
testing showed it also flags **"York" for "New York City"** (ratio 0.31) — which
is genuinely wrong, and is the exact case the ratio guard exists to reject.

**This is not fixable by tuning, and that is the finding.** Three independent
automated methods were tested against the same ten controls:

| method | "Bangladesh" / "People's Republic of Bangladesh" (RIGHT) | "York" / "New York City" (WRONG) | separates? |
|---|---|---|---|
| char-length ratio | 0.33 | 0.31 | **no** — nearly identical |
| cosine similarity | ~0.65 | — | **no** — also puts two *different* rowing clubs at 0.781 and the *same* island at 0.526 |
| **NLI entailment** | 0.827 | **0.969** | **no — inverted.** Scores the wrong pair highest of all ten, and "China"/"People's Republic of China" lowest but one (0.257) |
| Wikipedia canonical title | Bangladesh = Bangladesh ✅ | York ≠ New York City ✅ | **4 of 6** — nails formal names, misses "Sheppey"/"Isle of Sheppey" |

**Why nothing works.** The distinction is *entity identity*, a fact about the
world. Embeddings and entailment models encode **similarity**, and "York" is
extremely similar to "New York City" — that is precisely why it is a plausible
wrong answer. The methods fail for the same reason the models did.

**Consequence for the flag:** it marks *the ambiguous band*, not *the mis-graded
cases*. The banner now says so — "judgement call", with both example directions
shown and an explicit note that no automatic method separates them. Claiming
these were all mis-graded would be the same over-reach the project keeps catching
elsewhere.

**The one method worth building if this matters more later:** Wikipedia/Wikidata
canonical-title resolution. It got 4 of 6 and, importantly, got the two hardest
right. The retrieval machinery already exists in `rq4_retrieval.py`. Costs a
network round trip per pair and rate limits; not worth it for 60 cases, worth
reconsidering if the ambiguous band grows.

**Recorded as a methodological finding, not just a defect:** *automated grading
of open-ended QA has an irreducible ambiguous band that must be surfaced rather
than hidden.* That is an argument for the tool existing.

---

## #40 · A render failure that showed the WRONG CASE, silently — in the labelling view

**Found** 2026-08-01, while reading tab 2 rather than testing it. **Severity: the
highest of any interface defect so far**, because it corrupts data the project
depends on rather than merely displaying something wrong.

### What happened

Replacing a hard-coded "60 of 1,613 cases" in the copy with a counted value, I
added at module top level:

```js
const NKEY = CASES.filter(c => c.keyflag).length;
```

`CASES` is only assigned inside the `fetch(...).then(...)` callback. So this
statement ran while `CASES` was still `undefined` and **threw at load**.

**Function declarations are hoisted, so the tool still worked.** `boot()` ran
from the async callback, every view rendered, the console showed one error at
startup that looked like noise. The only symptom was that the card reading `NKEY`
could not be built.

### Why that is dangerous rather than annoying

`renderCase()` assigns `d.innerHTML` as one expression. If building the string
throws, **the assignment never happens and the previous case stays on screen** —
while `state.idx` has already moved to the new one.

```js
function setLabel(patch){
  const q = queue[state.idx];        // the NEW case
  state.labels[q] = ...              // <- your judgement lands here
}
```

So a labeller reading case B would have their verdict recorded against case A,
with **nothing on screen indicating anything was wrong**. Tab 2 exists to produce
hand labels; this is silent corruption of the only output it has.

Reproduced deterministically: `queue[state.idx]` = `halueval-00011`, painted card
= `halueval-00025`, position counter correctly reading "1 of 60".

### Fix, and the three separate guards

1. `NKEY` is assigned in `boot()` with the rest of the payload — the root cause.
2. The card build is wrapped. A failure replaces the card with an explicit "this
   case could not be displayed" **and returns before wiring the label buttons**,
   so no judgement can be recorded against an unseen case.
3. A post-render invariant compares the painted qid against the queue head and
   logs loudly on mismatch — the check that would have caught this in one second.

### The general rule

**A view that fails must fail loudly. Stale content is worse than a blank screen**
— it is indistinguishable from correct output, and here it silently rewrites the
user's data. Any render path that can throw between "the state moved" and "the
screen updated" needs the two resynchronised or the interaction disabled.

**Related:** this is the third defect in a row found by reading the interface
rather than by a test (watch-list 3b, the two-counts tooltip, this). The first two
were unfalsifiable by assertion. **This one was not** — the invariant in guard 3
is exactly the assertion that was missing, and it now exists. Worth stating in the
write-up: the presentation layer had no invariants at all until it produced a
defect that could corrupt the study's own data.

---

## 41 — FIXED 2026-08-02. Pre-fix rows survive in the RQ5 parquet because resume trusts the file, not the run

**Found:** 2026-08-01, by the heartbeat watch, not by a test.

`rq5_agentic.run()` resumes by reading `(model, qid)` pairs out of the destination
parquet and skipping them. That is correct for crash recovery and wrong for
*correctness recovery*: the file records **that** a row exists, never **which
version of the pipeline produced it**.

At 22:52 the file held 1,240 rows. Only 1,080 came from the run started 19:21,
i.e. after the Wikipedia cooldown fix (#28-30 lineage). The other 160 predate it,
and so were produced while roughly 16% of tool calls were being refused.

**Composition, measured rather than inferred** — Llama 100 · Qwen 20 · Mistral 20
· Gemma 20. An earlier draft of this entry guessed "~120 Qwen" by subtracting
per-model totals; that was wrong, and it mattered, because it named the wrong
models for re-running. The correct figures reconcile exactly:
1001-100 = 901 Llama and 199-20 = 179 Qwen, and 901+179 = the 1,080 the 19:21 run
reported. **Subtracting aggregates is not evidence; reading the rows is.**

### Why it is not cosmetic

Those rows saw a *degraded* tool. A model that could not retrieve is more likely
to stay wrong, so the stale rows bias the headline the **favourable** way — toward
"tools do not rescue silent consensus", which is precisely the claim being made.
A bias pointing at your own conclusion is the dangerous direction.

Worse, the 40 gemma/Mistral rows will be **silently skipped** when the run reaches
those two models, so they land in the final table untouched and unlabelled.

Checked and clean: no answer text contains `(the tool failed)` or
`(nothing found)`, so no row echoes a failure verbatim. The concern is the
counterfactual — what those models would have answered with a working tool.

### Why the fix is deferred, not applied

The process holds `prev` in memory and rewrites the whole parquet at every
checkpoint. Editing the file now is a lost update: the next checkpoint restores
the stale rows. **The fix has to run after the job exits**, which is why this is
logged open rather than fixed.

### The stale rows ARE identifiable, positionally

The first draft of this entry assumed they were not, and proposed re-running all
683 Qwen rows to be safe. Unnecessary. Every checkpoint rebuilds the file as
`pd.concat([prev, new])` where `prev` is the file as loaded at startup, and
parquet preserves row order — so rows from earlier runs remain a **stable prefix**.
Rows 0..159 are exactly the pre-fix block, and their model composition (above) is
the check that proves it rather than assumes it.

### Fix, when the run ends

`scripts/rq5_drop_prefix_rows.py`. It backs the file up, verifies the prefix
composition matches the expected 100/20/20/20 and **refuses if it does not**, then
drops rows 0..159. Re-running `rq5_agentic --arm wiki` then re-does exactly those
160 pairs, because resume skips everything still present. Wikipedia is cached, so
the cost is model calls only — 160 rows, not 683.

It also **refuses to run while an `rq5_agentic` process is alive**, since the
checkpoint would silently undo the deletion. Verified: the gate fires.

### The general rule, and the schema change it implies

**A resume key must identify the pipeline, not just the work.** Storing only
`(model, qid)` makes "already done" and "done correctly" the same statement.
Add a `run_id`/`code_version` column so a resume can skip completed work *from
this version* and re-do everything else. Same root cause as the RQ4 lesson: a
cache that cannot distinguish a good result from a bad one will serve the bad one
forever, confidently.

### Outcome

`scripts/rq5_drop_prefix_rows.py` ran clean after the job exited. The composition
gate matched **exactly** (Llama 100 · Qwen 20 · Mistral 20 · Gemma 20), which is
what turned the positional argument from an assumption into a verified fact —
had it not matched, the script would have refused rather than deleted 160 rows on
a guess. 4,078 -> 3,918, backup at `rq5_agentic.parquet.prefix-bak`, then a resume
re-ran exactly those pairs.

**Effect on the headline: 24.4% -> 24.7%.** The contamination was not material.
That is the useful part of the result, not a reason it was not worth doing: the
bias was *toward the paper's own conclusion*, so leaving it unmeasured would have
meant defending a number nobody could prove was clean.

**Carried forward as a schema change, not just a fix:** `(model, qid)` is not a
sufficient resume key. Add `run_id`/`code_version` before any future long run, so
"already done" and "done by the current code" stop being the same statement.

---

## 42 — FIXED 2026-08-02. The tool quoted a real number from the wrong population

**Found:** by the user asking "is the UI up to date with everything?" — not by a
test, and not by me. Fourth finding in a row surfaced by reading the interface.

Tab 2's label help and impact panel told reviewers:

> *"A fact too rare for any model to have learned. Giving them documents fixes
> these **(+68%)**."*

and computed `Math.round(obs * 0.68)` — "retrieval repairs about N of your N
obscurity cases".

**+68% is a genuine RQ4 result.** It is also measured over *every* obscure
question in the corpus. **Tab 2 contains only silent-consensus cases** — the
subset where all four models agreed on one wrong answer. RQ5 has now measured
that exact population with models free to search for themselves:

| | fixed |
|---|---|
| all silent-consensus (both arms, matched n=131) | ~1 in 4 |
| popqa / obscurity specifically | ~1 in 6 |

**A reviewer was being told the fix works about four times better than it does on
the cases in front of them.**

### Why this class is worse than a wrong number

Nothing here was false. The figure was accurate, sourced, and defensible in
isolation — it was simply about a different set of questions than the one on
screen. **A correct statistic shown next to the wrong population is harder to
catch than an error**, because every check that asks "is this number right?"
passes. The check that catches it is "is this number *about this*?", and nothing
in the test suite can ask that.

It also sat in the deliverable being evaluated, aimed at the people whose
judgements become E2 data. Reviewers would have labelled causes while believing
retrieval fixes two thirds of obscurity cases here. It fixes a sixth.

### Fix

Label help and the impact box now quote the RQ5 figure measured on this
population, and a red caveat states plainly that these cases already survived
search — Wikipedia and open web, up to four self-directed lookups each — with the
matched n and the between-source difference. Node `--check` clean; no other stale
RQ4 extrapolation remains in the tool.

### Rule

**Every number rendered in the interface must name the population it was measured
on.** Where a figure comes from a different population than the view it appears
in, it is wrong regardless of how correct it is.

---

## #43 · `summary.json` published a hardcoded `keyflags: 0` while the real count was 60

**Found 2026-08-03 by a measurement audit** (re-deriving every published number
from the source parquets), not by a reader noticing.

`scripts/export_web.py` built the `stats` dict with the literal

```python
"keyflags": 0,
```

and then, **twenty lines later and after the dict was already written**, computed
the true value purely so it could be printed to the console:

```python
nflag = sum(1 for c in cases if c["keyflag"])
print(f"   answer-key-too-strict flags: {nflag} of {len(cases)} cases")
```

`lookup_keyflags.parquet` holds **60** flagged cases, and the tool's own
per-case `keyflag` field (which comes from `cases`, not from `stats`) is correct
— so the tool has always shown the right flags. Only the aggregate in
`summary.json` was wrong.

**Severity: latent, not active.** Nothing reads `stats.keyflags` yet, which is the
only reason a slide never said "0 answer-key flags". It was a wrong number sitting
in a published file waiting for its first reader — and this session very nearly
became that reader.

**Fixed:** `nflag` is computed *before* the dict and the field is `"keyflags": nflag`.

**Class:** *A published artifact going stale* (#37's class). Extends standing rule
4 — **no number reaches a public file as a literal.** A constant in an exporter
does not track its source, and the exporter is exactly where that is least
visible. If a value cannot be derived, it does not belong in `stats`.

## #44 · The deck's funnel sentence described `majority_wrong` while showing the `all_wrong` number

**Found the same way, by checking definitional invariants rather than values.**

`records.parquet` satisfies every definitional invariant tested — `n_clusters==1`
is exactly `disagreement_unweighted==0`, `silent_consensus` is exactly
`unanimous & all_wrong`, `all_wrong` implies `majority_wrong` implies `any_wrong`
— with one exception that is **not** a data error:

```
unanimous & majority_wrong : 1,168
unanimous & all_wrong      : 1,054   <- silent_consensus
gap                        :   114
```

### Why the gap exists, and why it is not a bug

Clustering and grading answer different questions with the same threshold.
Clustering compares the four answers **to each other**; grading compares each
answer **to the gold**. So four answers can be one meaning-cluster and still
receive different grades:

```
Q: Which post was held by Dame Eliza Manningham-Buller from 2002 to 2007?
   gold: Head of MI5
   wrong     "Director-General of MI5"
   wrong     "Director General of MI5"
   wrong     "Director General of MI5"
   CORRECT   "Director General of MI5."      <- a full stop flipped the grade

Q: Dageurreotype is a mid-1800s form of?      gold: Photograph
   wrong "Photography."  CORRECT "Photography"  CORRECT "Photography"  wrong "Photography."
```

**263 of 17,664 unanimous questions (1.5%) are graded inconsistently across
answers the clusterer calls identical** — punctuation and pluralisation. In 114
of them the ensemble's own answer landed on the wrong side.

Sampled cases all point the same way: the models were **right** and the key was
harsh. So `all_wrong` — the stricter definition — is doing the correct job by
excluding them, and **1,054 stands**. This is the same phenomenon as #39,
measured from the other end.

### What was actually wrong

The **words**, not the number. `index.html` read:

> agreed on 17,664 questions, and on **6.0%** of those *the thing they agreed on was wrong*

"The thing they agreed on was wrong" is `majority_wrong` = **6.6%**. The number
printed was `silent/unanimous` = `all_wrong` = **6.0%**. A sentence labelled with
the wrong one of two adjacent, both-defensible quantities.

**Fixed:** the sentence now reads *"every model was wrong"*, which is what
`all_wrong` means and what slide 6's own heading already said. The `f_unan`
tooltip now states both figures and why they differ.

### The robustness number this exposed, worth quoting if challenged

| label the headline AUC is computed on | AUC |
|---|---|
| `majority_wrong` (published, principled — "was the ensemble's output wrong?") | **0.862** |
| `all_wrong` | 0.818 |

**0.044 of sensitivity to the label choice — nearly twice the +0.024 that
confidence buys.** `majority_wrong` remains correct (the detector predicts whether
the ensemble's *answer* is wrong, not whether every member failed), but the
spread must be stated rather than discovered by an examiner. Note the direction:
the 114 sit at disagreement 0.00 and are labelled wrong, so they **cost** the
published AUC — 0.862 is conservative, not flattered.

**Class:** new — *two defensible definitions, one sentence.* The lesson matches
the 2026-08-03 head-count decision exactly: when two quantities are both
defensible, pick one, use it everywhere, and make the prose name the one it shows.

---

## #45 · Slide 15 said "42 defects" while this file said 44 — a third hardcoded count

**Found by reading the deck aloud to explain it, not by any check.** That is the
point: nothing in the pipeline could have caught it, because nothing in the
pipeline knew the number existed.

```
ISSUES.md header : 44 defects found, 44 fixed        (correct, updated 2026-08-03)
index.html sl.15 : "42 defects found, 42 fixed"      (stale since 2026-08-03)
```

Four days of the deployed deck understating its own defect count by two.

### Why this keeps happening to the same kind of number

This is the third instance of one failure mode, and the three together define it:

| | the number | where it went stale |
|---|---|---|
| **#43** | `keyflags` | a literal `0` in the exporter while the parquet held 60 |
| **(prose)** | the batch-table total | "39 found, 38 fixed" for a week |
| **#45** | the defect total | `42` on a slide while the header said `44` |

Every one is a **monotonically increasing count that is published in more than
one place**. Such a number cannot be maintained by discipline: the moment it
changes, every copy is wrong until someone remembers all of them. The only stable
fix is to have exactly one writable copy and derive the rest.

### Fix

`export_web.py` gained `defect_count()`, which regex-reads the `## N defects
found` line out of `ISSUES.md` and publishes it as `summary.json.defects`. The
slide now renders `${S.defects}`. It raises `SystemExit` on a miss rather than
falling back to a default — an export that fails loudly beats a slide that
renders a wrong number quietly.

Incrementing this file's header to **45** for this very entry is what re-exported
the correct value, so the mechanism verified itself on the first use.

**Class:** *a hardcoded count that stopped tracking its source* — same class as
#43, now with a named rule: **a count that appears twice is a defect; derive the
second copy or delete it.**

---

## #46 · The map said "214 far-out questions" and the real number is 399

**Found by deriving a number instead of trusting it.** Sweeping both pages for
the #45 pattern -- a figure with a live source and no link back to it -- turned
up the stray count in the map header. Replacing the literal with a count taken
from the same percentile frame the renderer uses returned **399**, not 214.

### The number was wrong, not stale

The frame is 2-D and each axis is clamped independently:

```js
px = ox + (cl(MAP.x[i], XMIN, XMAX) - XMIN) * sx
py = H - (oy + (cl(MAP.y[i], YMIN, YMAX) - YMIN) * sy)
```

So a point inside the x-range but outside the y-range is *also* drawn on the
border. 214 is what you get counting **one axis**: 0.25% of 42,551 in each tail
is 106, and 2 x 106 = 213. The original count measured x and the header
described the frame.

```
strays on x only        ~214     <- what was published
strays on either axis    399     <- what is actually drawn on the border
```

Nearly twice as many dots sit on the border as the header admitted. That matters
precisely because the header exists to stop a reader treating the edge row as a
pattern -- understating it by half weakens the warning it was written to give.

### Fix

`<b id="n-strays">` filled in `size()` immediately after XMIN/XMAX/YMIN/YMAX are
computed, from the same comparison the clamp performs. The count can no longer
describe a different frame from the one being drawn.

**Class:** *a hardcoded count that stopped tracking its source* -- #43, #45, #46.
This one is the first of the three where the derivation found an error already
published, rather than preventing a future one. Same sweep also derived slide
10's six RQ3 rates, the 99.5%, the hand-label total, the RQ5 paired delta and
the two search-repair counts; every one of those matched, which is what makes
399-vs-214 believable rather than a suspicion about the method.

---

## #47 · `pipeline.html` still publishes the PILOT, and one of its numbers is reversed — reachable in one click from the deck

**Found by checking a file nobody had opened all project.** `pipeline.html` has
one commit in its history (`b97d09e`) and was written *before* the full run. The
deck links to it from the tool slide.

### It is not merely stale

| the page says | the full run says |
|---|---|
| "**Pilot done, full run pending.** A 300-question pilot has been run" | 42,551 questions · 170,364 graded answers · 0 failures |
| "ensemble **0.788** vs best single-model SE **0.813** — **single wins every dataset**" | cross-model **0.862** vs best single **0.800** — **cross wins**, budget-matched |
| confidence in the agree region **0.653** | RQ1 **0.600** |
| PopQA 0.845 · TruthfulQA 0.534 | 0.868 · 0.646 |
| "Novelty ... remains **pending** a final literature search" | settled; recorded in RESULTS |

The second row is the problem. It is not an old number, it is the **opposite
finding** — and it contradicts slide 9 of the deck, which is one of the five
headline claims. A reviewer following the link from the results deck lands on a
page telling them the ensemble loses.

**This is #37 recurring** — "the DEPLOYED site published retracted numbers" —
on the one page the deploy check never looked at, because it has no
`summary.json` to compare against. Every automated check this project owns keys
off the exporter. `pipeline.html` reads no data, so nothing could catch it.

### Fix applied

A banner at the top of the page stating that every figure is pilot-era, naming
the reversal explicitly, and pointing at the deck and RESULTS.md; and the deck's
link now carries "· proposal-era numbers" so the label is visible *before* the
click, not after.

### Properly fixed 2026-08-08 — the page is now under the same harness

The banner was the stop-gap. The real fix is that `pipeline.html` now **reads
`summary.json`**, like the deck and the tool:

- prose fields (`narr`, `why`, `whySkip`, `note`) and tooltips carry `{{token}}`
  placeholders, substituted in `render()` by `sub()`
- strings inside `draw()` — the risk-register cells — use `F("token")`
- unknown tokens render **visibly**; before the fetch lands they render `…`
  rather than a stale number. *An unresolved placeholder is an obvious defect;
  a confident wrong figure is not.*
- a fetch failure shows a banner and costs the figures, not the page

`summary.json` gained `rq1` (agreement-region AUC 0.600, n=17,664) and `rq2`
(corr popularity −0.309, density +0.267 on PopQA's 14,267) so the last two
typed figures had a source to come from. Both reproduce the RESULTS values
exactly.

**The reversals are stated where they happened, not overwritten.** Level 6 and
the risk register now say *"this reversed between scales"* and give both
numbers, because which figures moved between 300 questions and 42,551 is
itself a result — RESULTS claim 2. The risk-register row *"do the four models
fail together?"* used to read "0.639, healthy diversity, risk retired"; it now
reads **yes, on 1,054 questions**, and notes that the proportion worsens as
models improve. A risk that turns out to be real is not a design failure.
Publishing the pilot's answer after the full run contradicted it would have
been.

Verified headless: 16 levels render, **zero unresolved tokens**, every figure
matching source.

### The lesson, which generalises past this file

**A verification harness only covers what it can compare against a source.**
`export_web.py` made every number in the deck and the tool checkable, and the
side effect was that the one page outside the exporter became the only place a
retracted number could survive four months. Ask of any artifact: *what would
have to be true for a check to notice this is wrong?* If the answer is
"someone reads it", it is unchecked.

**Class:** *published numbers that no longer track their source* — with #43,
#45, #46. The largest of the four, and the only one that reverses a claim.

---

## #48 · "about half are still wrong" — prose that reads `majority_wrong` over an `all_wrong` number

**Found by auditing tabs 3 and 4, which had never been checked.** The
generation-diff card said, of the 559 *now visible* cases:

> hidden in 2024; in 2025 the models disagree again, so a check can catch them —
> **about half are still wrong**

`52%` is real and documented — RESULTS' RQ3 table records `293 (52%)` — but it
is the **all-four-wrong** count. "Still wrong", in a sentence about whether a
check can catch the ensemble's answer, reads as the **ensemble's own answer**:

```
healed, 559 cases, state in 2025
  ensemble's own answer wrong (majority_wrong)   438   78.4%   <- what the prose means
  all four wrong              (all_wrong)        293   52.4%   <- what the number was
                                                        gap: 26 points
```

**This is #44 in mirror image.** There, the deck's funnel sentence described
`majority_wrong` while showing the `all_wrong` figure. Here the same two
definitions sit under the same kind of sentence, in the other artifact. The
2026-08-03 rule was: *when two quantities are both defensible, pick one, use it
everywhere, and make the prose name the one it shows.* Neither of these named it.

The understatement ran against her own argument, which is why nobody caught it
by reading: "about half" is a weaker finding than the truth. **26 points of
weaker.**

### Fix

Both figures published (`rq3.healed_ens_wrong`, `rq3.healed_allwrong`,
`rq3.emerged_was_allwrong`) and both stated, each naming its measure. The card
now reads *"the ensemble is still wrong on 78% of them — detectable, not
correct"*; the filter help gives 78% and 52% with the definitions attached.

The 78% and 52% in `FILTER_HELP` were also **hardcoded** — the #43/#45/#46 class
again, in the one file the last sweep did not reach because those strings sit in
a module-scope constant that cannot see `ST`. They are now filled at load.

**Class:** *two defensible definitions, one sentence* (with #44) — and *a
published number that no longer tracks its source* (with #43, #45, #46). It is
the first defect to belong to both.

---

## #49 · `<divclass="slide">` — a deleted space stopped slide 18 rendering, and I wrote it

**Reported by Shivani: "something is wrong with slide 18, it is not rendered
properly."** Three separate faults on one slide, and the first is mine.

### 1 · The render bug

```html
`<divclass="slide">        <- no space. class= is not an attribute, it is part of the tag name
```

Introduced 2026-08-07 in `af5bd82`, inserting the persona slide. The `old_string`
of that edit ended with `` `<div `` — trailing space — and the `new_string` ended
`` `<div ``  without it. The browser parses `<divclass=...>` as an unknown
element, so `.slide{display:none}` and `.slide.on{display:flex}` never apply and
the slide renders as an unstyled always-visible block.

**Why every existing check missed it.** All of them read the *rendered text*:
tooltip keys, `undefined`/`NaN`, unresolved templates, figures against source.
None looked at whether the markup was well-formed. A slide can carry perfectly
correct numbers and still be broken.

Added to the render check, and it now passes on all 19:

```js
o.filter(s => !/^\s*<div class="slide"/.test(s))   // -> 0
```

### 2 · "42 defects found and fixed" — stale by six

`48` at the time of reporting. This is #43/#45/#46 for the fourth time, and it
survived the 2026-08-07 sweep that was written to end exactly this class —
because that sweep filtered to `n >= 100` to skip CSS pixel values, and `42` is
below the cut. **A filter written to reduce noise silently defined a blind spot.**
Re-run without the bound, the deck yields thirteen literals; twelve are
legitimate (published external scores, the deliberately-quoted pilot reversal,
years, step numbers) and the thirteenth was this.

Now `${S.defects}`. `62 tests passing` was hardcoded beside it and is now
`${S.tests}`, counted by `count_tests()` — which **raises** if anyone adds
`@pytest.mark.parametrize`, because a `def test_` count would stop equalling
what pytest collects and the export should fail rather than drift.

### 3 · "Task abstraction" listed under Remaining

Done since 2026-07-29 and recorded as done in `TODO.md`; the closing slide still
showed it as outstanding. Moved to the Done column.

**Class:** three at once — *a hardcoded count that stopped tracking its source*
(#43, #45, #46, #48), *stale status prose*, and a new one: **a defect that no
check could see because every check was reading content, not structure.**

The lesson that generalises: after building a verifier, ask what shape of defect
it *cannot* express. The figure checks could not express "the tag is malformed",
and the literal sweep's own noise filter could not express "42".

---

## #50 · The map's box filtered tab 2 correctly, and nothing in tab 2 said so

**Reported by Shivani, walking Walkthrough 1: "in tab 2, the number of questions
chosen are not going down."**

The filter worked. `rebuildQueue()` restricts the case queue by `inBrush()` and
always has. What failed is that **every number a reader looks at in tab 2 was the
population total, set once at load and never updated**:

```js
document.getElementById('nb').textContent      = CASES.length   // the tab badge
document.getElementById('lede-n').textContent  = CASES.length   // "1,613 questions, each..."
```

Only the small `12 of 47` position counter moved, and it sits below the fold of
attention. So: draw a box, switch to tab 2, and the headline still reads
**1,613**. The correct conclusion for a user to draw is *"the box did nothing"*,
and that is the conclusion she drew.

**A filter with no visible consequence is indistinguishable from a broken
filter.** This is the same principle already written into this tool for the
labelling panel — *"labelling with no visible consequence is data entry"* — not
applied to the brush.

### Fix

- the tab badge and the lede now follow the **queue**, not the population;
  filtered they read `47 of 1,613`
- a blue bar at the top of tab 2 states *"Showing only the 47 cases inside the
  box you drew on the map"*, with its own **✕ clear the box**, so the state is
  both visible and escapable from the tab where it is confusing
- the filter **chips keep their population totals** on purpose — a chip labels
  the filter, not the result, and chips that renumbered as you filtered would
  make it impossible to see what you had narrowed *from*

### Why no check caught it

Every check reads the *rendered artifact*. This is a defect in the **relationship
between two views** — the map filtered, the inspector obeyed, and the inspector's
own description of itself did not. Nothing static can see that; only walking the
path can. It is the first defect in this project found by **using** the tool
rather than by reading or measuring it, which is the argument for the expert
evaluation in one line.

**Class:** new — *a control whose effect is real and invisible.*

---

## #51 · The panel explaining why labelling matters appeared only after you had labelled

**Reported by Shivani, two questions in a row:** *"instead of just seeing what
went wrong, we have a grader. why?"* and then *"where is this computations being
shown?"*

Both questions have the same answer — the `#impact` box — and it was `hidden`
until the first verdict:

```js
if(!judged.length){ box.hidden=true; return }
```

So a reader arriving at tab 2 saw labelling buttons, four cause options and a
keyboard hint, and **nothing at all saying why they would press any of them**.
The explanation of why the work matters was gated behind doing the work.

This is #50's shape again — *a control whose consequence is real and invisible* —
and the tool already had the principle written into this very panel:

> *"Labelling with no visible consequence is data entry."*

The consequence was implemented. It was just unreachable until you had already
guessed it was worth reaching for.

### Fix

The box now renders in a "before" state: the standing **1,054**, labelled *"this
is an estimate, not a fact"*, and one sentence on what a verdict does to it —
*"the grader cannot tell. You can."* After the first verdict it switches to the
live estimate exactly as before.

Verified in both states:

```
no labels                -> "What your labels will do"  · 1,054, estimate not fact
4 labels, 1 not-really   -> "What your labels are saying" · 791, range 562-1,019
```

### Why this keeps happening in the same place

#50 and #51 are both about **the interface failing to describe its own state**,
and both were found by a person using the tool rather than by any check. Every
verifier this project owns compares a rendered artifact against a source; none
can express *"a reader would not know why to start"*. That is the entire
argument for the expert evaluation, arriving twice in one week from a sample
size of one.

**Class:** *a control whose consequence is real and invisible* — with #50.

---

## #52 · "Every case here was re-run with search" — it was true of 61%, and the panel said it on all of them

**Found because Shivani asked what the `n=131 matched` line meant and whether it
was necessary.** Reading the paragraph it belongs to answered a different
question: the paragraph was false for more than a third of the cases it appeared
on.

The note sat above every case in tab 2:

> **These already survived the obvious fix.** Every case here was re-run with each
> model free to search for itself — its own queries, up to four lookups,
> Wikipedia and open-web search tried separately.

Measured against the payload it was rendered over:

```
cases in tab 2                     1,613
  Wikipedia arm ran on               977   (61%)
  open-web arm ran on                148   ( 9%)
  BOTH tried                         131   ( 8%)
  NEITHER tried                      619   (38%)
```

**All 559 "now visible" cases were never searched at all**, and the reason is
structural rather than an oversight: RQ5 ran on the 1,054 questions the *2025*
models are blind on, and the healed cases are in the corpus because the *2024*
models were blind on them. They were never in that population.

### The panel contradicted itself on screen

The per-case retrieval line — added 2026-08-07 — already printed the truth three
inches below:

```
—  documents pasted in:         not run
✗  agent searched Wikipedia:    still wrong
—  agent searched the open web: not run
```

So a reviewer read *"every case here was re-run ... Wikipedia and open-web search
tried separately"* directly above *"not run"* for the same question. Two views of
one fact, one derived and one asserted, disagreeing in the same viewport. This is
#43's lesson — a published constant that no longer tracks its source — showing up
as **prose** rather than as a number.

### Fix

`toolNote(c)` is now computed per case and says what happened to *that* question:

- **never searched** → says so, names why (wrong generation's population), and
  tells the reader to judge on the answers alone
- **searched, still wrong** → the original claim, now true where it is shown
- **search rescued it** → says the answers above are the *closed-book* failure,
  not the final word. This case never had a note before and needed one most

The population claim survives, stated as a population claim, and the
`n=131 matched · web−wiki +3.1pp` shorthand is now a sentence: *"on the 131
questions run through both, the open web rescued 3.1 percentage points more, a
gap small enough to be chance."*

Verified: **0 of 1,613** cases carry a note contradicting their own data.

**Class:** *prose that overclaims relative to the data beneath it* — with #44 and
#48. Third instance, and the first where the interface stated the contradiction
and its own refutation simultaneously.

---

## #53 - pipeline.html described the study as designed, not as run

**Found:** 2026-08-25, by an external read of the repository against the page.
**Fixed:** same day, commit `5721f3d`.
**Class:** *a published artifact going stale* - with #37. Second instance, and
the larger one: #37 was a stale number, this was a stale **design**.

`faultlines-web/pipeline.html` was frozen at the pre-pivot proposal. Twenty-six
statements had drifted from the data, in five groups:

| group | said | actually |
|---|---|---|
| **datasets** | three datasets; AbstentionBench as the misconception arm; silent consensus ~1.7% | four (TriviaQA 17,944 and HaluEval 10,000 were absent entirely); AbstentionBench rejected on ingest and never used; 2.48% |
| **models** | RQ3 compared "gen 2 - current" (Llama 3.1 / Qwen 2.5 / Mistral 0.3 / Gemma 2) against a "gen 1" ensemble; L2 described four 4-bit models on an 8 GB laptop | "gen 2" IS the old arm; gen-1 was dropped before producing any result; the headline arm is hosted, 24 workers, 17-27B active |
| **method** | corpus screened to the all-agree cases, "grade just those"; baseline AUC 0.74 | all 42,551 generated AND graded; `screen.py` built, tested on 15 questions, not used for the headline; AUC 0.862 |
| **storage / stack** | Postgres + pgvector, FastAPI, React, D3, Neon | parquet files on disk; the tool is one static page with vanilla JS over a 2D canvas |
| **labels** | "~250 tags that train a classifier", cause tags feeding RQ1 and RQ4 | 430 grader-agreement verdicts; **no classifier was ever built**; RQ4 strata are rule-based |

### Why this one is worse than a wrong number

The RQ3 diagram named four 7-9B models on one side and four 7-9B models on the
other. It therefore **appeared to show a size-matched generation comparison** -
which is exactly the control the study does not have, and exactly the first
thing a reviewer attacks. A reader who opened the public page and then read
`RESULTS.md` would conclude the confound was being concealed rather than
missed.

A page that is merely out of date costs credibility once. A page that advertises
a control you do not have costs it permanently.

### Also fixed, and it changed meaning rather than numbers

L2 carried a note saying pairwise error correlation was *"worth measuring on a
small slice before committing"*. It had never been measured. It is **0.667**,
and all four models are wrong together 26.9% of the time against 3.0% under
independence. The panel now states that as the project's finding. See
`DECISIONS.md` 2026-08-25.

### Fix

Every level's prose and its canvas rewritten against `summary.json` and the
parquet records; the confound stated on the level that has it; the storage and
stack levels rewritten to describe what exists, with a sentence on what was
designed and dropped and why. Re-baked with `prerender.mjs` so the JavaScript-free
copy matches. Script re-parsed clean; levels 1, 2, 8, 9 and RQ3 rendered and
checked.

**Lesson, extending #37's standing rule:** *a published artifact is a result* -
and a **diagram** is a claim. Prose drift gets noticed on a re-read; a canvas
that draws four model names nobody has looked at in two months does not.

---

## #54 - a reproducibility claim that was never measured, wrong by 15x

**Found:** 2026-08-25, by measuring it.
**Fixed:** same day.
**Class:** *a published artifact going stale* - with #37 and #53 - but with a
sharper edge: this one was never true, rather than having become untrue.

`RESULTS.md` described the 170,364-generation local run as taking
**"~9 hours of laptop GPU"**. That is 5.26 gen/s.

`scripts/build_rq3_local.py`, in the same repository, budgets its own work with
a comment reading **"measured: 0.24 gen/s"** - 197 hours for the same run. The
two numbers sat 20x apart, in the same project, for four weeks.

### The measurement

`scripts/time_local.py`, 12 real questions through each of the four local
models in turn, same endpoint, same prompt, same `max_tokens`:

| model | first call | median | rate |
|---|---|---|---|
| llama3.1:8b | 12.68 s | 3.039 s | 0.33 gen/s |
| qwen2.5:7b | 10.76 s | 2.881 s | 0.35 gen/s |
| mistral:7b | 9.00 s | 2.498 s | 0.40 gen/s |
| gemma2:9b | 13.13 s | 3.262 s | 0.31 gen/s |

**0.34 gen/s overall -> ~138 hours for the full pass.** The
`build_rq3_local.py` figure was close and in the right order; the RESULTS.md
figure was wrong by about 15x.

### Why it matters more than a typo

Every other number in `RESULTS.md` is a *finding* - if it is wrong, a reader
disagrees with a conclusion. This one is an *instruction*. It is the number
someone uses to decide whether they can reproduce the work on their own laptop,
and "9 hours" reads as an overnight run while 138 hours reads as most of a
week. It is the only figure in the file a reader could have acted on and lost
days to.

It also flatters the project, which is the direction this repo has committed to
narrating loudly - see the watch-list entry on every bias found running in our
own favour.

### Why it was not caught

The three published pages are audited against `summary.json` because the
exporter produces them. This number is in a prose paragraph, was typed by hand,
and had no source at all - it was not a stale reading of a live value, it was
an estimate that never became a measurement. `screen.py`'s and
`build_rq3_local.py`'s constants were the only other place the quantity
appeared, and nothing compared them.

### Fix

Measured, corrected in place with the old value shown, and
`scripts/time_local.py` committed so the claim is re-checkable rather than
re-typed.

**Lesson, and it is a new one:** *a number with no source is worse than a stale
number.* A stale number has a source that has moved on, so re-running the
exporter catches it. An estimate that was never measured has nothing to diverge
from, so nothing will ever flag it. Prose figures need a source or a
measurement script, same as published ones.

---

## #55 - the grading-artifact bound was four times too small, and flattered us

**Found:** 2026-08-25, by adjudicating the population the claim is about instead
of extrapolating to it.
**Fixed:** same day.
**Class:** new - *a bound on one failure mode, reported as a bound on the
phenomenon*.

`RESULTS.md` stated since 2026-08-01 that **at most 5.6%** of the 1,054 blind
spots are answer-key artifacts. That figure is an exact count of ONE kind of
artifact: cases where all four answers sit INSIDE the gold string and were
rejected by the short-form ratio guard.

It is a syntactic containment test. It cannot see:

```
"1640s"                 for  "40's"                      not a substring
"Constantine X Doukas"  for  "Konstantinos X Doukas"     transliteration
"Smoking"               for  "Tobacco or alcohol"        semantic
"The bumblebee bat"     for  "Bat"                       answer is LONGER
```

The number was right. The word **upper** was not.

### Measured directly

`scripts/adjudicate_blind.py` put an adjudicator to all 1,054 with the automatic
grade withheld. It committed on 998:

| dataset | n | grader too strict | 95% CI |
|---|---|---|---|
| HaluEval | 366 | **33.88%** | [29.22%, 38.87%] |
| TriviaQA | 196 | **32.65%** | [26.48%, 39.50%] |
| PopQA | 431 | 6.26% | [4.34%, 8.96%] |
| **ALL** | **998** | **21.74%** | **[19.30%, 24.41%]** |

About **825 of the 1,054 are genuine**, and the rate is nearer 1.94% than 2.48%.

### The judge was calibrated before this was believed

On the 430 cases where a human saw the same answers: when the judge said the
grader was too strict, the human agreed **30 of 31** times (96.8%); where the
judge sided with the grader, the human still called **16.1%** correct. Accurate
when it flags, conservative overall - so 21.74% is closer to a floor.

### Why this one is the bad kind

Every unintentional bias found in this project has run in the direction that
flatters its own hypothesis, and this is the fifth. A too-small artifact bound
makes the blind region look larger and more real than it is, which is the
project's headline.

It also survived four weeks of review by three published pages and a results
record, because nothing in the sentence was false. **A bound is only as wide as
the test that produced it, and the sentence has to name the test.**

### Fix

Corrected in `RESULTS.md` with the old section kept and marked superseded;
propagated to chapters 5, 7 and 8, the exporter (`summary.json.artifact`), the
claims table, and the deck. `scripts/check_writeup.py` now verifies the new
figures in all three chapters, so they cannot drift apart.

**Open, and named as the most important item in the thesis:** the same
adjudication has NOT been run on the 2024 arm. The RQ3 comparison is *argued* to
survive because both arms share one grader and a uniform strictness cancels.
That is an argument. The measurement costs about a thousand calls.

---

## #56 - a stratified sample analysed as though it were random

**Found:** 2026-08-26, when the second annotator's result came back as a perfect
kappa of 1.000 and that was treated as a symptom rather than a success.
**Fixed:** same day, with no additional work from the annotator.
**Class:** new - *a stratified sample analysed as though it were random*.

`handlabel2.py` was written to avoid an obvious trap: handing a second annotator
only the 45 cases an LLM adjudicator had contested. That subset is 89% one
class, so chance agreement alone is 0.802 and kappa has almost no room to move.
Correct diagnosis.

The fix introduced the mirror of the same error. The "reliability" stratum was
drawn from the **296 cases the adjudicator did NOT contest**, on the reasoning
that keeping the strata disjoint made each kappa mean one thing. But those 296
are pre-filtered for being easy, so agreement on them estimates reliability on
the easy subset and not on the 430.

```
  reliability stratum   kappa 1.000   agreement 100.0%   n=47
```

**A kappa of exactly 1.000 is a result about the sampling frame, not about the
annotators.** The first version of `--result` printed it under the heading THE
REPORTED FIGURE.

### The fix needed no more labelling

This IS a stratified sample with known stratum sizes -- 70 drawn from 296, and a
census of all 45 -- so weighting each sampled case by N/n reconstructs the
population table. That is a *stronger* design than simple random sampling; it
simply has to be analysed as the stratified sample it is.

```
  uncontested   296   sampled  70   compared 47   kappa 1.000   100.0%
  disputed       45   sampled  45   compared 37   kappa 0.528    91.9%
  POPULATION    341   sampled 115   compared 84   kappa 0.962    98.7%
                                    95% CI [0.904, 1.000]
```

The per-stratum figures are kept as diagnostics because they **bracket** the
estimate: the uncontested stratum is an upper bound, the disputed stratum a
lower one, and the weighted figure sits between them where it should.

### A second defect found while fixing the first

The bootstrap count was 4,000 in the script and 2,000 in the exporter, which put
`[0.904, 1.000]` in the prose and `[0.906, 1.000]` in `summary.json`. Two
sources for one number, third decimal. `BOOTSTRAP_N` now lives in one module and
the exporter imports it.

**Lesson.** *The analysis has to match the design.* Deliberate stratification is
good practice and it silently invalidates every statistic computed as though the
sample were simple. Either weight by N/n, or do not stratify.

**Related:** #55 the day before, which was the same shape in a different guise -
a measurement that was correct about what it measured and wrong about what it
was reported to measure.

---

## #57 - the provenance table miscounted its own page

**Found:** 2026-08-26, while writing the discovery walkthroughs into the thesis
(PLAN 2.2) and re-deriving every figure they quote.
**Fixed:** same day.
**Class:** recurrence of *a document holding a number with a live source* - the
class behind #43, #45, #46, #47 and #49 - in the one place it should have been
impossible.

`walkthroughs.html` closes with a table titled **"Every number on this page, and
its source"**, followed by a note naming the figures that are *not* read from
`summary.json`. That note said:

> Two figures on this page are not yet in summary.json ... the 18%-tighter
> clustering measure, and the **47-case example box** in step 3 of walkthrough 1.

**There is no 47-case box on that page.** Step 3 of walkthrough 1 shows **72
cases, 28 of them "Who was the director of X?"**, reached by the addressable box
`#c=blind&b=3.17,12.45,4.57,13.93`. The 47 is a *different* drag, described in
`walkthroughs/W1-the-clumps-have-names.md`, from before the page gained
deep-linkable views. The note was written against the markdown, the page moved,
and the note did not.

**Why this one is worse than the five before it.** #43 through #49 were numbers
drifting inside ordinary prose. This is the drift-catching mechanism drifting:
the note exists specifically to tell a reader which figures are unverified, so a
reader who checked it was told to go and audit a figure that is not on the page
while the figure that *is* went unnamed. A provenance table that miscounts its
own page is worse than no provenance table, because it converts a reader's
diligence into wasted effort and quiet false assurance.

**The fix.** The note now names all three unsourced figures, states that the
72/28 counts are a property of one link rather than of the corpus, and records
that both were re-derived from `data.json` on 2026-08-26 by applying the same
brush coordinates:

```
points in box: 2384
cases (blind-spot queue) in box: 72
director-of questions in box: 28
```

Both copies in the file were patched - the template and the prerendered baked
copy - with the replacement asserted at exactly 2 matches, which is the guard
that has caught baked-copy skew three times before.

**Not done, and deliberately.** The 72/28 could be moved into the exporter and
derived like everything else. They were left literal because they describe one
URL rather than a population, and a figure that changes meaning when the box
moves does not belong in `summary.json` beside corpus statistics. The note says
so, which is the honest version of the trade.

**Lesson.** *The mechanism that catches drift is itself a document.* Anything
that lists what has not been verified has to be re-read whenever the thing it
describes changes, and it is the last document anybody thinks to re-read.

### A second defect found while fixing the first

Checking that §6.2b's cross-reference resolved turned up the same class one
chapter over. Chapter 7's section heading read:

> ## 7.4 Silent consensus is partly a grading artifact, and the bound is 5.6%

Its own first paragraph, three lines below, reads *"This section reported 5.6%
until 2026-08-25 and it was four times too small"* and gives 21.74%. The body was
rewritten when #55 landed; **the heading was not**, and a heading is the part a
reader skims and the part that becomes the table of contents. Corrected to *"and
the measured rate is 21.7%"*. `PLAN.md`'s limitations checklist carried the same
stale bound and was corrected with it.

`check_writeup.py` did not catch this, and could not have: it checks that
figures *present* in the prose match the records, and 5.6% is a figure that was
correct about the thing it originally measured. **A checker that verifies values
cannot verify claims.** That gap is real and is left open deliberately rather
than papered over with a regex.

**Related:** #43, #45, #46, #47, #49 - same class. #50, the count that read
1,613 in two places when one of them meant 47.

---

## #58 - the judge graded its own answers, in every case, for four weeks

**Found:** 2026-08-26, on the first cross-arm comparison. The 2024 arm came back
at 15.71% and the 2025 arm at 20.59%, and before writing that down the obvious
question was asked: *whose answer is being judged?*
**Fixed:** same day, by re-judging both arms with a model in neither ensemble.
**Class:** new - *an evaluator inside the population it evaluates*.

`adjudicate_blind.py` judges one representative answer per case, on the stated
reasoning that every answer in a silent-consensus case is in one meaning cluster
so judging one judges the case. The representative is picked as **the first
model in sorted order**, which is reproducible and was chosen for exactly that
reason.

    "Qwen/Qwen3-235B-A22B-Instruct-2507"   sorts first among the 2025 models
    "gemma2:9b"                            sorts first among the 2024 models

The judge is **Qwen3-235B**. So all 1,054 of the 2025 cases were judged on the
judge's own answer, and all 923 of the 2024 cases were judged on an answer the
judge had no stake in. The 21.74% that corrected this project's headline
(ISSUES #55) was measured entirely on the judge's own output.

**The script's own docstring promised this would be visible.** It says the judge
is an ensemble member and that `report()` breaks the result down by the model
whose answer was judged, *"so if the judge is soft on its own family, that table
shows it"*. That table has **one row**. A diagnostic whose output cannot vary
is not a diagnostic, and it printed reassuringly for four weeks.

**Why it mattered more than it looks.** For the single-arm figure the case-level
claim survives: the four answers are in one meaning cluster, so if the judge
says the representative means the gold answer, the grader was too strict on all
four. But the cross-arm COMPARISON is a different animal. Self-favouring inflates
the 2025 rate relative to the 2024 one, and that is precisely the direction the
first result showed. The finding and its most likely artifact were the same
shape.

**The fix, and what it found.** Both arms were re-judged by
**Olmo-3.1-32B-Instruct**, in neither ensemble and trained on Dolma - the
strongest available break in data lineage, which is the variable this thesis
argues drives correlated error.

| judge | in an arm? | 2024 | 2025 | gap | p |
|---|---|---|---|---|---|
| Qwen3-235B | **yes, 2025** | 15.71% | 20.59% | +4.9 pts | 0.0051 |
| Olmo-3.1-32B | no | 18.09% | 25.43% | **+7.3 pts** | 0.0001 |

**The gap widened.** Olmo is more lenient on both arms, which moves the level and
not the difference. So the effect is not self-favouring - and the check that
would have caught it if it were is now in the repository rather than in a
docstring's promise.

**Lesson.** *A diagnostic that cannot come out badly is not a diagnostic.*
Before trusting a breakdown, check that the column it breaks down by actually
varies. Ours had one value and printed a percentage next to it every run.

**Related:** #55, the correction this measurement was checking. #33, the other
time an evaluator was inside the thing it evaluated.

---

## #59 - two of the four vetted outside judges are unusable, and the note says they are fine

**Found:** 2026-08-26, while picking a judge for #58.
**Fixed:** same day - one usable judge identified and the stale claim corrected.
**Class:** recurrence of *a comment that outlived the thing it described*, the
same class as #57 the same day.

`judge_panel.py` carries a list of four outside judges under the comment
*"Four developers, none in the ensemble, none of them a REASONING model"*, with
a note that MiniMax-M2.7 was rejected for burning its token budget on reasoning
tokens and returning an empty string. Probing all four:

| candidate | trivial prompt | real adjudication prompt |
|---|---|---|
| `deepseek-ai/DeepSeek-V3.2` | `CORRECT` | **empty on 3 of 4** |
| `moonshotai/Kimi-K2-Instruct-0905` | **empty** | **empty on 6 of 6** |
| `microsoft/phi-4` | `Incorrect` - not one of the three allowed words | not tried |
| `allenai/Olmo-3.1-32B-Instruct` | `CORRECT` | 0 unparseable in 1,977 calls |

DeepSeek-V3.2 is the trap. It answers a **short** prompt correctly and returns
an empty string on a **long** one, because the reasoning budget is consumed
before any answer token is emitted. A gate that probes with
*"what is the capital of Australia"* passes it; the real workload does not. That
is the same failure MiniMax-M2.7 had, in a model the comment above it lists as
not a reasoning model.

**Standing rule 1 applies and was applied:** an empty reply is a failed call,
not an UNCLEAR verdict. Had `verdict()` been allowed to map empty to UNCLEAR,
the run would have completed with a plausible artifact rate built from 75%
nothing.

**Lesson.** *Probe the gate with the real prompt, not a short one.* Length is
the variable that breaks reasoning models, so a length-free probe tests the one
thing that cannot fail.

**Related:** #31, models served under names that were not what they claimed.
Standing rule 1.

---

## #60 - the figure checker passed by coincidence, and had been for weeks

**Found:** 2026-08-26, immediately after adding two defects to the log and
noticing that `check_writeup.py` reported *"all figures match the records"*
while five files still said **57 defects**.
**Fixed:** same day, at the root.
**Class:** new - *a verifier whose match is weaker than its claim*. This is the
worst class in the log so far, because every other defect was found by a check
and this one was IN the checks.

## What it did

`check_writeup.py` asserts that a figure in `summary.json` appears in the
chapter that quotes it. The assertion was a plain substring test:

```python
ok = norm(literal) in text
```

The defect-count check searches for `str(S["defects"])`. When the count went to
59, the needle became `"59"` - and:

| chapter | what matched | what the prose actually said |
|---|---|---|
| `ch1-introduction.md` | `[59.5%, 75.3%]` | "57 defects were found and fixed" |
| `ch4-method.md` | `kappa 0.959` | "57 defects were found and fixed" |

Both chapters were wrong. Both checks printed `ok`. **A confidence interval and
a kappa were standing in for a defect count.**

## How much else was exposed

A guard was added to name every needle shorter than four characters, and it
found **49 of them** - `690`, `364`, `559`, `154`, `340`, `430`, `222`, `366`,
`461` and more, each of which sits happily inside a larger number. `364` matches
inside `1,364` and `364.5`. None of those was actually wrong on the day, but
none of them was being *checked* either, and there was no way to tell which from
the output.

## The fix, and why it is not "edit 49 needles"

Editing the needles would have made 49 checks stronger and left the mechanism
that produced the defect exactly as it was. `found()` now requires a numeric
literal to appear as a **figure** rather than as a substring: not preceded by a
digit or by a digit-and-separator, not followed by one. `690` matches
`690 emerged` and `(690)` and not `1,690`, `0.690` or `6901`. Literals that do
not begin or end with a digit - table fragments, phrases, `9.0x` - keep plain
containment, because their punctuation already makes them distinctive.

**It found a second defect on its first run.** The check for mean confidence
when wrong searched for `"0.93"`, because the exporter rounds to 3dp and JSON
drops the trailing zero. The prose correctly writes `0.930`. Under substring
matching `0.93` matched inside `0.930` and passed for weeks; under `found()` it
failed immediately, which is the correct behaviour and the needle is now
formatted `:.3f`. **The very first thing a stricter check found was a check that
had never actually been checking.**

## What it means for the 240 checks

They are worth more today than they were yesterday, and the honest statement of
what they guaranteed before is narrower than what was claimed. Every figure with
a unit, a comma or a decimal point - `2.48%`, `42,551`, `0.862`, `[19.30%,
24.41%]` - was genuinely checked all along, because those needles cannot occur
inside another number. The exposure was confined to bare integers, and that is
where both real failures were found.

**Lesson.** *A verifier has to be attacked at least as hard as the thing it
verifies.* This one was written to catch drift in prose, was trusted for weeks
on the strength of its own green output, and was never once asked the question
it asks of everything else: **could this pass while being wrong?**

**Related:** #57 the same day, where the note listing what was NOT verified was
itself wrong - the same shape one level up. #45, #46, #47, #49, the drift this
checker exists to catch and mostly does.

---

## #61 - a hint that could not be dismissed, added the same day it was removed

**Found:** 2026-08-26, **by the author using the tool**, not by any check.
**Fixed:** same day, by deleting it.
**Class:** new - *a mitigation that becomes the defect it was added to prevent*.

The E3 fix for the cognitive walkthrough (§6.3b) added three things to make the
brush discoverable: a crosshair cursor, a labelled chip in the map header, and a
**dashed "ghost" rectangle** pulsing over the map on first arrival to demonstrate
the gesture.

The ghost cleared on a press **on the canvas**. A reader who instead used the
tabs, the legend, the dataset filters or the scrollbar left it sitting there,
pulsing, indefinitely. The report was *"it should not be there, like it is
stuck"* - and that reading is correct: an animated dashed box that will not go
away is indistinguishable from a rendering fault. **It made the tool look
broken in order to explain a gesture.**

**The fix is deletion, not a timer.** A timed dismissal would have kept a
mechanism whose only job is to disappear correctly, and the walkthrough grade
does not need it: the crosshair cursor and the labelled chip are what moved E3
off *no visible affordance*, and both are permanent, static and impossible to get
stuck. `walkthrough_audit.py`'s E3 path is updated to name the chip rather than
the ghost, and E3 still grades 0 unaffordanced steps.

**Lesson.** *An affordance that has to be dismissed is a liability; one that is
simply always visible is not.* The chip costs a line of the header forever and
can never misbehave. The ghost was cleverer and worse.

**Related:** #38, the loading overlay that stayed up over a working tool - the
same shape, and the reason `.hidden` is not trusted anywhere in this codebase.

---

## #64 - four citations were wrong, and one of them was the advisor's own tool

**Found:** 2026-09-07, building the reference list the thesis did not have, by
checking every citation against an authoritative record instead of against
memory.
**Fixed:** same day.
**Class:** new - *a citation carried in prose for months and never resolved to a
record*.

The chapters cited about forty works and the thesis had **no reference list at
all** - so no citation had ever been resolved to a bibliographic record. Building
one surfaced four errors:

| what it said | what it is |
|---|---|
| **MultiCa** (Dilawer & Humayoun, EICS 2024) | the tool is **MultiCaM-Vis**. This is the advisor's own paper, and the wrong name is the single most embarrassing error available in this document |
| Multi-Agent Debate (Du et al., **2023**) | the 2023 arXiv preprint was published at **ICML 2024**. Citing the preprint year for a work that has a venue reads as not having checked |
| Hamidieh et al., **NeurIPS 2025** | a **NeurIPS 2025 workshop** paper (Reliable ML). Naming the conference without the workshop overstates prior art, which cuts against this thesis's own interest and is exactly why it has to be right |
| Kossen et al., 2024 | **ICML 2024 Workshop on Foundation Models in the Wild**, arXiv:2406.15927 |

**Why nothing caught it.** `check_writeup.py` validates numbers against
`summary.json`. A citation is not a number and has no record to be checked
against, so the automated pass that protects every figure in this thesis protects
none of its citations. The reference list is now that record, and each entry
carries the DOI or arXiv identifier it was verified against.

**Lesson.** *A claim about the literature is a claim, and standing rule 5 applies
to it.* A citation that has never been resolved to a record has the same standing
as a number that was never counted.

**Related:** #63 (a summary of a record being wrong while the analysis was
right), and standing rule 7, which #64 extends from records to citations.

## #65 - the count that justifies standing rule 6 was stated three ways

**Found:** 2026-09-07, in the same pass.
**Fixed:** same day.
**Class:** #54 again - *a number with no source*, this time inside the rules.

Standing rule 6 is justified by how many near-misses prompted it. The project
said:

| where | count |
|---|---|
| `ISSUES.md` rule 6 | **three** near-misses in a single afternoon |
| the table directly under it | **seven** rows, and the words "Seven now" |
| `ch1-introduction.md` | **five** |
| `ch4-method.md` | **five** |

Three was correct on the day the rule was written; seven is the running total the
table has reached. **Five was never correct**, and appeared in both chapters.

The chapters now say three prompted it and seven have been caught, which is the
only statement consistent with the table. The irony is recorded rather than
smoothed over: the rule that says *nothing is reported until it has been attacked
once* was itself reported four times with an unattacked number in it.

## #63 - the claims table applied a rate to the denominator it was measured on

**Found:** 2026-08-31, by Shivani, reading the advisor summary back against the
thesis and asking why two documents disagreed.
**Fixed:** same day, one number.
**Class:** new - *a rate applied to its own measurement denominator instead of to
the population*.

`RESULTS.md`'s claims table is the file's own authority. Its header says: *if a
claim is not in this table, it is not ready to quote.* Claim 3 read:

> ~21.7% ... are answer-key artifacts, measured on all 1,054 - so **~780
> genuine**, nearer 1.9%

Every other statement of that quantity in the project says **825**: the body of
this same file, `ch5-results.md` twice, `ch7-limitations.md` twice, and the
deployed deck. The one place a reader is told to quote from was the one place
that was wrong.

### Where ~780 came from

The 21.74% artifact rate is measured **on the 998 cases where the adjudicator
committed**, not on all 1,054 - there are 56 UNCLEAR verdicts. The genuine count
is the rate applied to the *population*:

```
1,054 x (1 - 0.2174)  =  825      <- correct, and what the body says
  998 x (1 - 0.2174)  =  781      <- what the claims table said
```

The rate was applied back to the sample it was estimated from. The body of the
file, written in the same commit (`b168e5a`, 2026-08-25), applied it to 1,054 and
got 825.

**A wrong first hypothesis, recorded because it was cheap to disprove and would
have been recorded as the cause.** The 2024 arm's genuine count is **778**, which
is close enough to ~780 that cross-arm contamination looked like the obvious
explanation. `git log -S` disproves it: 778 was first computed on 2026-08-26,
the day *after* ~780 was written. Rule 6 applied to a defect's cause and not
only to a result.

### Why nothing caught it

`check_writeup.py` checks figures **in the thesis chapters** against
`summary.json`. The chapters were right. Nothing checks `RESULTS.md`'s claims
table against `RESULTS.md`'s own body, and nothing ever compared the two numbers
because they never appear in the same file position. 825 and 780 are also both
plausible - neither is a typo, an order of magnitude, or a sign error, and both
round to "about eight hundred".

It survived six days and was found by a person noticing that a summary document
and the thesis disagreed.

### The other two numbers here are NOT defects

Worth stating, because anyone re-checking this will meet them and they look like
the same problem:

| number | what it is |
|---|---|
| **825** | 1,054 x (1 - 21.74%). The rate over the **998 committed verdicts**, applied to the population. The headline genuine count |
| **837** | 1,054 x (1 - 20.59%). The same numerator over **all 1,054**, treating UNCLEAR as *not shown to be an artifact*. Used only for the cross-arm comparison, where both arms need one denominator |
| **778** | 923 x (1 - 15.71%). The **2024** arm |

`RESULTS.md` already states why 20.59% appears beside 21.74% - *same numerator,
different and explicitly stated denominator*. That note is why this was
resolvable in minutes rather than being a second defect.

**Lesson.** *A rate has two denominators - the one it was measured on and the one
it is applied to - and they are usually not the same one.* When a rate is
estimated on a subset because some cases were undecidable, writing the count down
means choosing which population it describes. Say which, in the sentence.

**Standing rule 7, adopted 2026-08-31** — *a summary of a record is a record,
and needs its own check.* Written up in full with the standing rules at the top
of this file, including the two checks it decomposes into (which denominator, and
whether a second figure for the same quantity carries its reason) and the
weakness it still has: as written it is enforced by a person reading, and the
mechanical version does not exist yet.

**Related:** #54 (a number with no source), #55 (the adjudication that produced
the 21.74%), #57 (a provenance table that miscounted its own page) - all three
are a record file being wrong about itself while the analysis underneath it was
right.

## #62 - the tool ignored its own address bar

**Found:** 2026-08-26, during a full manual debug pass in a real browser, driving
every tab and control after the day's changes.
**Fixed:** same day, in two parts.
**Class:** new - *a stated design property that was only true at page load*.

Chapter 3 §3.5c claims **"every view has an address"**: the colouring, filters,
tab and brush all live in the URL so a link is a screen. `walkthroughs.html`
depends on it - two of its steps are deep links rather than instructions to drag.

### Part one: nothing listened for a hash change

`applyHash()` ran **once, at boot**. There was no `hashchange` listener, so
changing the URL without a reload did nothing:

```
location.hash = '#c=name'   ->  address bar: #c=name
                                the map:     still the previous colouring
```

A reader following the *second* walkthrough link while the tool was already open
in that tab got a URL describing a view they were not being shown. Same for
pasting a link into an open tab, and for the browser **Back** button, which was
inert throughout.

`pushHash()` uses `replaceState`, which does not fire `hashchange`, so the tool
cannot loop by reacting to its own writes. That is a property of `replaceState`
rather than of this code, so the guard is left explicit for whoever changes it.

### Part two, found by testing part one: a link was a PATCH, not a view

With the listener in, following `#c=blind&b=3.17,...` and then `#c=name` left the
**box from the first link still applied**. `applyHash()` only sets the keys a
link carries, so applying it over a live view produces a *merge*.

The consequence is precisely the thing addressability was introduced to fix.
Walkthrough step 6 is captioned *"no dragging, identical for everyone"* and it
was showing **72 cases instead of the whole map** - and the tool then wrote the
stale brush back into the address bar, so *Copy link to this view* would have
shared a view nobody chose.

**The fix is to reset to defaults before applying the hash**, which is what boot
already effectively does by applying it to a fresh state. The two paths now
agree. **A link either describes a complete view or it does not describe one.**

**Why no automated check caught either half.** `check_writeup.py` verifies
figures, the parse-check verifies syntax, and the test suite never opens a
browser. Both halves of this are behaviour that only exists when a person
navigates, and both were found by doing exactly that.

**Lesson.** *A property that is only established at load is not a property of the
application.* Anything the design chapter claims as always-true needs to be
exercised after the page is already running.

**Related:** #50, where two counts of the same thing disagreed - also a
consistency claim that held on first paint and not afterwards.
