# PLAN

**One list. Everything that is still to do, in the order it should be done.**

## 2026-09-27 · Deadline moved to mid-October; the correction pass and what remains

**The deadline is now mid-October 2026, not 30 September.** The advisor has not
yet reached out about submission, so the date this plan treated as hard (it
unblocks the OPT application) moves. The scope does not: the thesis only. See
`DECISIONS.md` § *2026-09-27* §5. Everything below that says "30 September"
is kept as written and superseded by this paragraph.

**What happened on 27 Sep.** An adversarial review found thirteen defects and
eleven smaller findings (ISSUES #66–#78). The code for all of them is fixed and
`summary.json` was re-exported on the deduplicated corpus: 34,062 questions, AUC
0.840, 950 blind spots, 3.3× within-dataset concordance. `RESULTS.md`,
`ISSUES.md`, `DECISIONS.md` and both READMEs are updated.

**What remains, in order:**

| | item | who | status |
|---|---|---|---|
| C.1 | **Paid re-runs** — blind-spot adjudication failed calls and the 430-case adjudicator with alias lists (#71); RQ4's re-selected strata and empty answers (#70); RQ5's 85 missing Wikipedia rows with NLI for TruthfulQA (#76) | needs an API key | ✅ **done 27 Sep**, 0 failed calls |
| C.2 | **Re-export** — `python scripts/export_web.py`, then `python scripts/check_writeup.py` | | ✅ re-exported 27 Sep after C.1; the checker's flags are C.3's work list |
| C.3 | **Chapter text** — fix whatever the checker flags after C.2; replace every *pending* figure; restore or retire claim 17 | | ⬜ in progress 27 Sep on the post-re-run figures. Claim 17 is **restored** (κ 0.782 with aliases) |
| C.4 | **Figures and Word build** — `capture_figures.py`, then `build_thesis_docx.py`, then the four Word-only steps in 2.12 | half `👤` | ⬜ |
| C.5 | Close #70, #71, #76 in `ISSUES.md` and change its header | | ✅ done 27 Sep |

---

Created 2026-08-25. This file **replaces `TODO.md`** and supersedes the action
ledger in `ASSESSMENT.md` §3. `TASKS.md` stays as the design document it is; its
§5 evaluation protocol appears here as a scheduled item rather than a plan.

## The goal, and what is no longer in the project

**Amended 2026-08-30**, and this is the largest scope change since the plan was
written. The deadline moved forward by ten weeks and the second goal left the
project entirely. See `DECISIONS.md` § *2026-08-30*.

| | goal | deadline | what it is judged on |
|---|---|---|---|
| **A** | **The capstone — this is the whole project.** M.S. Data Science & AI, SFSU, advisor Dr. Shahrukh Humayoun | ~~30 September 2026, hard~~ **mid-October 2026** (moved 2026-09-27) | a visual-analytics thesis: does the instrument let someone *discover* things |
| ~~B~~ | ~~PhD applications · arXiv preprint, ML framing~~ — **out of scope.** Still wanted, still worth writing, but it is not part of the capstone and it happens *after* the thesis is submitted | after submission | — |

**There is no longer a conflict to resolve.** Previous versions of this file
spent their opening on which goal wins. A is now the only goal in the project, so
every row below is judged on one question: does it move the thesis toward
submission on 30 September.

**Why the date is hard, and not a preference.** Submitting the thesis is what
unblocks the **OPT application**. A slipped September does not cost a paper
deadline — it costs work authorisation, which is a category of consequence
nothing else on this plan comes near. Anything that does not move the thesis is
**deferred, not traded off**: it keeps its reasoning, loses its schedule.

**The gate is retired.** It existed to decide whether Phase 3 would be written
properly or assembled fast. Phase 3 is no longer in the project, so there is
nothing left for it to decide.

---


## THE CHECKLIST

Every item in this plan, in one place. Tick here **and** in the phase section so
they cannot disagree. `👤` marks the rows that need somebody other than me.

| | item | phase | who | status |
|---|---|---|---|---|
| 0.1 | `pipeline.html` drift, 26 corrections | 0 | | ✅ 25 Aug |
| 0.2 | ISSUES #53 + DECISIONS entry | 0 | | ✅ 25 Aug |
| 0.3 | Confidence intervals on every claim | 0 | | ✅ 25 Aug |
| 0.4 | RQ5 restated on its ceiling | 0 | | ✅ 25 Aug |
| 0.5 | Independence reframed as claim 12 | 0 | | ✅ 25 Aug |
| 0.6 | Related-work material recovered | 0 | | ✅ 25 Aug |
| 0.7 | Local throughput measured (ISSUES #54) | 0 | | ✅ 25 Aug |
| 0.8 | Independence figures into the exporter | 0 | | ✅ 25 Aug |
| 0.9 | Status folded into the deck | 0 | | ✅ 25 Aug |
| 1.1 | Decorrelation frontier, 154 ensembles | 1 | | ✅ 25 Aug |
| 1.2 | Behavioural arms: counter-evidence, abstention | 1 | | ✅ 25 Aug |
| 1.3 | Multi-feature signal + risk–coverage | 1 | | ✅ 25 Aug |
| 1.4 | Ensemble-size ablation | 1 | | ✅ 25 Aug |
| 1.5a | LLM adjudicator on all 430 | 1 | | ✅ 25 Aug |
| 1.5b | **Second human: 115 cases, two strata** | 1 | `👤` | ✅ **done 2026-08-26 by Devesh. κ = 0.962 [0.904, 1.000]**, stratum-weighted over 341 |
| 1.6 | RQ2 density within PopQA only | 1 | | ✅ 25 Aug |
| 2.0 | Thesis outline + `writeup/` structure | 2 | | ✅ 25 Aug |
| 2.1 | **Evaluation — analytical, no participants** | 2 | | ✅ **done 2026-08-26.** Cognitive walkthrough (`walkthrough_audit.py`), discovery provenance, measured performance. The six-task study was **not run** and ch6 says so; protocol, materials and an instrumented unmoderated mode remain in the repo for anyone who picks it up |
| 2.2 | Two discovery walkthroughs | 2 | half | ✅ **written**, and **walked 2026-08-26**. Reaction 1 is in ch6 §6.2b, reaction 2 in ch7 §7.4, reaction 3 in **ch6 §6.7** (written 7 Sept), and the step-1 prediction confirms the wrong turn. ✅ **closed** |
| 2.12 | **SFSU Word submission copy** | 2 | half | ✅ **built 7 Sept** — `scripts/build_thesis_docx.py` writes the chapters into the *official* SFSU template, so margins, section breaks and the roman→arabic page numbering are inherited rather than imitated. 7 figures with alt text, 70 tables with marked header rows, template furniture stripped. `👤` **four steps remain that only Word can do:** update the ToC/LoT/LoF fields (Ctrl+A, F9), run the Accessibility Checker, replace the generated table-title stubs (`writeup/TABLE_TITLES_TO_FIX.md`), and fill in the committee names |
| 2.3 | Design chapter | 2 | | ✅ 25 Aug |
| 2.4 | Results chapter | 2 | | ✅ 25 Aug |
| 2.5 | Limitations chapter | 2 | | ✅ 25 Aug |
| 2.6 | Method / how the project changed | 2 | | ✅ 25 Aug |
| 2.7 | Related work | 2 | | ✅ 25 Aug · **citations verified 7 Sept** — every one resolved to an authoritative record. Four were wrong (ISSUES #64) and one 2026 paper had to be added: Kohli's *Nine judges, two effective votes*, which measures the same independence deficit for judging panels. Novelty claim 1 narrowed, §2.4b written |
| 2.9 | **Reference list** — the thesis had none | 2 | | ✅ **done 7 Sept.** `ch9-references.md`, ~40 works, each with a DOI or arXiv id and each checked against the publisher's record rather than memory |
| 2.10 | **Figures** — the thesis had none | 2 | | ✅ **done 7 Sept.** Seven captures of the deployed instrument in `writeup/figures/`, embedded in ch3/ch5/ch6 with captions that say what to look at and where the number came from. The list of figures is derived by scanning the captions, not typed |
| 2.11 | **Front matter** — abstract, acknowledgements, title page, list of figures | 2 | | ✅ **done 7 Sept.** `00-front-matter.md`; `build_thesis.py` now assembles the whole document. **The signature page and the SFSU template's margins/spacing/citation style are still not applied** and cannot be guessed |
| 2.8 | Introduction + conclusion | 2 | | ✅ 25 Aug |
| ~~3.1~~ | ~~Preprint, ML framing~~ | 3 | | ➖ **out of scope 30 Aug** — after submission |
| ~~3.2~~ | ~~arXiv~~ | 3 | | ➖ **out of scope 30 Aug** — after submission |
| ~~3.3~~ | ~~Two-page writeup for cold emails~~ | 3 | | ➖ **out of scope 30 Aug** — after submission |
| 4.1 | **Adjudicate the 2024 arm's 923 blind spots** | 4 | | ✅ **done 2026-08-26.** 15.71% vs 20.59%, p = 0.005 · confirmed by a judge in neither arm · **RESULTS Finding 12** |
| 4.2 | **Fix the two defects the walkthrough found** | 4 | | ✅ **done 2026-08-26.** E3 and E5 both 1 → 0 unaffordanced steps · before/after in ch6 §6.3b |
| 4.3 | One command rebuilds every figure | 4 | | ✅ **done 2026-08-26.** `scripts/reproduce.py` · 5 stages, 19 s with `--fast` |
| 4.4 | Lead the preprint with decorrelation | 4 | | ✅ **decided 2026-08-26.** Abstract rewritten below · the recommendation leads, the violation sets it up |

**33 of 33 in-scope rows done** (recounted 2026-08-30, after the three Phase 3 rows left the project). Every Phase 4 row closed on 2026-08-26. The checklist is closed: reaction 3 was written on 2026-09-07 and is in ch6 §6.7. What remains is not on this list because it is not writing — it is the SFSU format check, which is administrative and runs at the university's speed (row 2.12). All eight thesis chapters are drafted — **34,798 of ~35,500 words** (read from `summary.json`, not typed; the earlier **33,511** here was neither, and is the same defect class as #63) — with **223 figures machine-checked** (`check_writeup.py`, counted by the script rather than typed) against `summary.json` plus two cross-artifact invariants, and **65 defects found, 65 fixed, zero open**. No `👤` rows are left: the second annotator is done (κ = 0.962), and Chapter 6 is analytical — the record of what the instrument found while being built, two documented discovery paths, a cognitive walkthrough, and measured performance. It states at the top that no user study was run, and §6.7 states what that cannot establish.

**Everything still open is writing, plus one half-sentence.** §6.2b now carries both discovery walkthroughs in full. What it cannot carry is what it felt like to walk them, so `writeup/eval/walkthrough-log.md` carries the verified links and three reaction prompts. **Two are answered and placed**, and one of them — *“I don't think the model is going wrong here”* — was **not** either reaction the walkthrough was designed around, which is the only reason it carries information. The third prompt's answer is still blank.

**Nothing on this list is blocked.** After 2.2 the remaining rows are Phase 3 (the preprint) and four new Phase 4 rows — “What would move this from good to hard to argue with”, added 2026-08-26 because the checklist ran out of blocked items and the question changed from *what is left* to *what is worth doing*. None of the four needs another person and none costs more than a dollar.

---

## Phase 0 — this week (~16 h)

Cheap, unblocks everything, and every row serves A.

| | work | h | goal | status |
|---|---|---|---|---|
| 0.1 | **`pipeline.html` drift** — 26 corrections across 5 classes | 5 | A + B | ✅ **done 2026-08-25**, commit `5721f3d` |
| 0.2 | **Log it**: ISSUES #53, and a `DECISIONS.md` entry for the reframes | 1 | A | ✅ **done 2026-08-25** |
| 0.3 | **CIs and significance into `RESULTS.md`** — new “Every claim, with its interval” section; claims 12 and 13 added; the Farquhar/Gorbett comparison retired | 3–4 | A + B | ✅ **done 2026-08-25** |
| 0.4 | **Restate RQ5.** Section retitled from “the comparison IS the finding” to “the CEILING is the finding”; Wilson interval attached; the difference moved to *Do NOT quote* | 1 | A + B | ✅ **done 2026-08-25** |
| 0.5 | **Independence reframe** — claim 12 in `RESULTS.md` with the “do not collapse claim 12 and claim 3” box, and deck slide 3b | 3 | A + B | ✅ **done 2026-08-25** |
| 0.6 | **Restore related-work material** into `writeup/` | 1 | A | ✅ **done 2026-08-25.** `TODO.md`’s command was wrong: `f41d989` is the commit that *deleted* them, so it needs `f41d989^`. Five files recovered |
| 0.7 | **Time local generations** — `scripts/time_local.py` | 0.5 | A | ✅ **done 2026-08-25. Measured 0.34 gen/s → ~138 h.** `RESULTS.md`’s “~9 h” was wrong by 15× and had never been measured — logged as ISSUES #54 |
| 0.8 | **Independence figures moved into the exporter** — φ, per-model error rates, observed vs predicted all-wrong, ratio. Claim 12 existed only in prose | 1 | A + B | ✅ **done 2026-08-25** |
| 0.9 | **Status folded into the deck** — the independence measurement as a new slide, “where it stands” rewritten, and a plan-and-asks slide. A standalone `status.html` was built first and removed: the deck IS the presentation, and a second page splits one link into two | 3 | A | ✅ **done 2026-08-25** |

**Why 0.5 is not just paper-polish:** the thesis argues that a disagreement-based
instrument is worth building. "The models are 9× more correlated than the
heuristic assumes" is the strongest possible argument *for* building it. It
belongs in chapter 1, not in limitations.

---

**Three deployed artifacts, and no more.** The tool (`faultlines-tool/`, the one
that gets expert-evaluated), the deck (`faultlines-web/index.html`, which stands
in for the PPT and is where status and findings both go), and the walkthroughs
(`walkthroughs.html`). `pipeline.html` predates this rule and stays because it is
linked and now correct. **Do not add a fourth page** — when something changes,
update the deck.

**Phase 0 is complete.** Every row above is done. The advisor-facing page is
live at `/status.html` and carries the three asks — evaluation participants, a
second annotator, and a scope call on 1.1 — which are the only items on this
plan that cannot be started alone.

---

## Phase 1 — September: the experiments that are still worth running (~22 h)

All four are cheap, all use the corpus you already have, and each closes a
specific reviewer objection **and** produces a figure the thesis needs.

### 1.1 — The decorrelation frontier `A + B` · ✅ **done 2026-08-25**

You have **eight** models on the identical 42,551 questions — four from 2024,
four from 2025. From eight models you can form **154** ensembles of size 2–4 (C(8,2)+C(8,3)+C(8,4)). The figure was quoted as 162 until 2026-08-25; the arithmetic had been asserted, not done.

For each: compute mean pairwise error correlation φ, and the AUC of its
disagreement signal. Plot φ against AUC.

**The claim this tests:** *ensembles should be chosen for decorrelation, not for
average accuracy.* If the lowest-φ ensembles beat the highest-accuracy ensembles
at equal size, that is an actionable design rule nobody has stated, and it comes
out of data already on disk.

**Why it is the best item on this list:**

- it is the constructive half of the independence finding — it stops the paper
  being purely negative
- it is a **selection** problem, which is what visual analytics is *for*, so it
  becomes a tool panel and a thesis contribution, not just a figure
- it costs zero API calls

**Caveat to state:** mixing 2024 and 2025 models is artificial as a deployment,
but that is precisely the point — you are asking what happens when you pick for
decorrelation rather than for rank.


> **Result, and it contradicted the hypothesis.** Across all 154 ensembles the blind
> region is almost perfectly predicted by how **correlated** the models are
> (r = +0.83 / +0.89 / +0.92 at k = 2/3/4) and barely at all by how **accurate**
> they are (−0.03 / −0.25 / −0.37). That is the constructive half of claim 12:
> you cannot buy your way out with better models, but correlation is measurable
> before deployment.
>
> **But the trade is not free.** Correlation also tracks detection AUC (+0.79 /
> +0.60 / +0.44, and +0.76 / +0.52 / +0.35 controlling for mean error), so
> decorrelating shrinks the region the detector cannot see while weakening it
> over the region it can. Predicted the opposite; recorded as the second
> falsified prediction in the project.
>
> **Ablation (2025 arm):** 2.48% at k=4, 3.56% at k=3, 6.63% at k=2. Supersedes
> the exact-match proxy, which was a lower bound as designed. RESULTS Finding 9.

### 1.2 — Two behavioural arms on the blind spots `A + B` · ✅ **done 2026-08-25**

> **Result: the belief does not move.** Counter-evidence repaired 0.76% of the 1,054
> blind spots and broke 3.00% of 500 correct controls — it breaks four for every one
> it fixes. Explicit permission to abstain repaired **zero**, upper bound 0.36%.
>
> **But the hedging is real and never converts.** At least one model abstained on
> 52.8% of blind spots against 25.2% of controls — 2.09×, Fisher p = 3×10⁻²⁵ —
> while a *majority* almost never refused and no question became correct. The
> behavioural twin of RQ1's “real signal, unusable margin”, reached from the other
> side. RESULTS Finding 10.


Replaces the gold-passage arm (which needs 131 documents curated by hand). Both
of these are prompt variants over the existing 1,054 blind spots plus a control:

| arm | prompt | what it separates |
|---|---|---|
| **counter-evidence** | "Some sources disagree with that. Reconsider." | *belief persistence* from *retrieval failure* — no documents needed |
| **abstention permitted** | "Answer, or say you do not know." | whether the model *could* have declined, which is what everyone suggests it should do |

~4,000 generations. Minutes, not hours.

**Why these and not gold passages:** RQ4 already ran the gold-document
experiment on a different slice and gave you the dissociation (+52.1%). These
two ask the question RQ4 cannot: not *does a document fix it*, but *does the
model hold the belief*. And 1.2's abstention arm feeds directly into 1.3.

### 1.3 — Fix the margin: multi-feature signal + risk–coverage `A + B` · ✅ **done 2026-08-25**

Confidence alone gives AUC 0.600 in the agreement region and no usable
threshold. Do not stop there — the region has more features already computed:

- per-model confidence **spread** (four models agree on the answer; their
  confidences still differ)
- NLI margin (`nli_margin`, already in `answers.parquet`)
- entity popularity (PopQA ships it)
- dataset, answer length, agreement-cluster size

Fit a small model (logistic regression, then gradient boosting) on these and
report the **risk–coverage curve** and AUARC, which is the standard framing for
exactly this question. Held-out split, no tuning on the test half.

Either outcome is a result:

- **beats 0.600 materially** → "the vote is blind here but the record is not,
  and here is what to read instead"
- **does not** → "the region is not merely hard for confidence, it is hard for
  everything we can measure" — a much stronger negative than the current one

**And it is a tool feature.** A signal panel where the user composes features
and watches the risk–coverage curve move is a genuine interactive contribution,
not a chart with a slider on it.


> **Result: AUC 0.601 → 0.811**, out-of-fold, +0.210. Answer only the half it is
> surest about and the error rate is **1.61%** against a 6.61% base; the surest
> quarter runs at 1.04%. The first direct test of the project's design claim —
> that keeping the whole record beats keeping the score — and it passes.
>
> **Two leaks caught before it was believed** (standing rule 6): density computed
> over the whole corpus carried test-fold labels (read 0.759), and the first fix
> was half a fix because a row is its own nearest neighbour. A third feature set
> was 99.1% null and printed a plausible negative. RESULTS Finding 8.

### 1.4 — Ensemble-size ablation `A + B` · ✅ **done 2026-08-25**

4 → 3 → 2 models, with proper meaning-clustering (the exact-match proxy already
says 2.03% / 2.98% / 5.66%). No reviewer accepts *n*=4 without the curve. Run it
overnight; it timed out at 10 minutes when attempted interactively.

### 1.5 — Second annotator `A + B` · ⚠ **half done 2026-08-25**

> The **LLM adjudicator is done**: κ 0.688 against the human, versus 0.459 for the
> project's own grader, with no detectable self-favouring (0.696 on its own
> family's answers vs 0.686 on the others'). It produced **45 cases where the
> human and the adjudicator disagree** — which is what the second human should be
> handed, instead of a random 100 that mostly nobody disputes.
>
> *(27 Sep 2026 re-run with alias lists, ISSUES #71: now κ 0.782 against the
> human, 0.816 on its own family's answers vs 0.771 on the others' — a small gap
> in the self-favouring direction — and 29 disputes, not 45.)*
>
> **The human half is still open and still needs a name.** This does not replace
> it and RESULTS Finding 11 says so twice.


100 of the existing 430, same blinded `handlabel.py`, report Cohen's κ.
**Cannot be added retrospectively.** Needs a name this month, not a plan.

Add an **LLM adjudicator over all 430** alongside it (~$1, 1 h) — reported as
supplementary, never as a substitute for the human κ.

### 1.6 — RQ2 density within PopQA only `A` · ✅ **done 2026-08-25**

> **Result: the finding got stronger.** 28.1% of a PopQA question's 15 map-neighbours
> came from another dataset, so the leak was real. Recomputing within PopQA raises the
> lift over popularity from **+0.060 to +0.078** and the correlation from +0.267 to
> +0.303. Both densities are now reported and both are exported — the shared-map one is
> what the tool draws, the within-dataset one is what the claim rests on.
>
> Bonus: density within PopQA **alone** reaches AUC 0.663 against popularity's 0.666.
> The map recovers from question text what an external metadata field provides, which
> matters for the three datasets that have no popularity column.


`AUDIT.md` note n1: neighbourhood density is computed over all four datasets and
then subset to PopQA, so a PopQA question's neighbours can be TruthfulQA
questions. RQ2 is the finding that defuses Kandpal 2023 — do not leave it open.

---

## Phase 2 — October: the thesis itself (~60–100 h) — **CRITICAL PATH**

This is the largest single item in the project and the only one that graduates
you. It was missing from every previous list.

| | chapter | source material | h |
|---|---|---|---|
| 2.1 | ~~Expert evaluation~~ → **analytical evaluation** | ✅ done 2026-08-26. The six-task study was **not run** and nobody is being recruited. ch6 is a cognitive walkthrough, the record of what the tool found while being built, and measured performance | done |
| 2.2 | Discovery walkthroughs — **2 paths, not 4** | `TASKS.md` §6; `walkthroughs.html` covers part | 8 |
| 2.3 | Design chapter | `TASKS.md` — personas, why/what/how, out-of-scope | 12 |
| 2.4 | Results chapter | `RESULTS.md` + Phase 0.3 intervals | 20 |
| 2.5 | **Limitations chapter** | scattered across `ISSUES.md` / `DECISIONS.md` — see below | 8 |
| 2.6 | Method / how the project changed | `EVOLUTION.md` | 10 |
| 2.7 | Related work | blocked on 0.6 | 12 |
| 2.8 | Intro + conclusion | last | 8 |

~~**2.1 is the critical path and it moves at other people's speed.**~~
**Retired 2026-08-26.** There is no recruiting and no critical path through
other people. The study was not run, Chapter 6 is analytical and says so in its
first paragraph, and §6.7 states what that cannot establish. The protocol and
materials stay in the repository so anyone who picks the project up can run it.

**2.2 — you must walk these yourself.** Claude can draft the path from the data;
it cannot manufacture "I did not expect that", and that reaction is the part a
reader believes.

**2.5 — the limitations chapter is the one that most changes a reader's rating**,
for both A and B. It must name, without being asked:

1. the generation/scale confound, and why it was not separated
2. the independence violation (φ = 0.667), reframed
3. the grading artifact, **measured at 21.74% [19.30%, 24.41%]** — the ≤ 5.6% this list originally named was an exact count of one artifact class reported as a bound on all of them (ISSUES #55)
4. single annotator (or, after 1.5, the κ)
5. the misconception arm's n=70 and its [+2.9%, +28.5%] interval
6. TruthfulQA's n=340 and its 10×-wider intervals
7. ensemble size, with the curve from 1.4

---

## Phase 3 — AFTER submission. NOT part of the project.

**Out of scope as of 2026-08-30.** The preprint is still worth writing and
every input it needs already exists — but it is not part of the capstone, it
does not compete for September, and **no row below may be started before the
thesis is submitted.** This section is kept in full so the reasoning survives,
not as work to be scheduled.

| | work | h | when |
|---|---|---|---|
| 3.1 | Preprint, ML framing — finding is the contribution, instrument is the method | 15 | after submission |
| 3.2 | Post to arXiv (cs.CL, cross-list cs.HC) | 3 | after submission |
| 3.3 | Two-page plain-text writeup for cold emails | 8 | after submission |

**The abstract leads with the RECOMMENDATION, not with the warning** (item 4.4,
decided 2026-08-26). The independence violation and the 2.5% are both true and
both leave a practitioner with a problem and no move. The decorrelation result
gives them one, nobody else has measured it, and promoting it costs nothing:

> Ensemble disagreement is a standard hallucination signal and it rests on an
> untested premise — that models from different developers fail independently.
> On 42,551 questions answered by eight models from four developers across two
> generations, the premise fails by an order of magnitude: all four are wrong
> together 26.9% of the time against 3.0% under independence, a 9.0× concordance
> ratio (mean pairwise φ = 0.667). We then score every ensemble of size 2–4 that
> those eight models can form (n = 154) and find that **the blind-spot rate
> tracks how correlated an ensemble's errors are (r = +0.917) and not how
> accurate it is (r = −0.366)** — so the more accurate ensemble is frequently
> the more dangerous one, and ensembles should be selected for decorrelation
> rather than for accuracy. Upgrading does not help: overall error falls 25%
> while the share of errors that are shared rises 1.52× (95% CI 1.42–1.63), and
> an upgrade creates about twice as many newly-undetectable failures as it
> inherits. We also show that automatic grading is **not** equally strict across
> generations — 15.7% of the older ensemble's shared failures are answer-key
> artifacts against 20.6% of the newer one's (p = 0.005, confirmed by a judge
> outside both ensembles) — which biases any longitudinal benchmark against the
> newer model.

**Why this order.** "Your guardrail is blind 2.5% of the time" is a warning; a
reader can only worry about it. "Pick the ensemble with the lower error
correlation, not the higher accuracy" is a **decision they can make on Monday**,
and it is derived from a measurement no one else has made. The violation becomes
the setup. The rule becomes the result.

**The grading-strictness finding earns its sentence** because it generalises
past this corpus: it is a caution about a method, not about these four models.

**Include the two voided experiments** as a Methods paragraph on provider
verification. 340,728 generations discarded because the provider served 2025
weights under 2024 names. Most people would have published them.

---

## Cut — deliberately not doing

| | why |
|---|---|
| The size-matched 2024-big arm (~$5) | Reframe instead. Becomes a named, costed future-work paragraph, which reads as command of the design rather than a hole |
| Gold-passage arm for RQ5 | Superseded by 1.2, which is cheaper and asks a sharper question |
| Semantic Entropy at n=10 | Pre-empt in text |
| Rent an A100/H100 | This was always a $5 API job |
| The Gemma 2×2 ladder | Compares single models; cannot address an ensemble-level claim |
| A cause classifier | Never built, not needed. The claim is now deleted from `pipeline.html` |
| A second (VIS) paper this autumn | After graduation, once the expert evaluation is in |
| Two more of the four walkthroughs | Two good ones beat four thin ones |
| "Beats Farquhar 0.790 / Gorbett 0.727" | Different corpora, models, graders. A free shot for a reviewer |

---

## What would move this from good to hard to argue with

Added 2026-08-26, when the checklist ran out of blocked rows and the question
became *what is worth doing* rather than *what is left*. Four items. None needs
another person, none needs more than a dollar, and each closes a specific thing
a reviewer can currently push on. Ordered by payoff per hour.

| | what | cost | what it closes |
|---|---|---|---|
| **4.1** | **Adjudicate the 2024 arm's 923 blind spots** | ~$1, ~1 h | the last argued-not-measured claim in the thesis |
| **4.2** | **Act on the walkthrough's own two findings** | ~6 h, code only | turns an inspection into a design iteration |
| **4.3** | **A one-command reproduction** | ~4 h | the cheapest credibility in the project |
| **4.4** | **Lead the preprint with decorrelation, not with 2.5%** | free, a decision | whether the ML paper is actionable or merely alarming |

### 4.1 — the 2024 arm has never been adjudicated `A + B` · ✅ **done 2026-08-26**

`adjudicate_blind.py` read all **1,054** blind spots in the 2025 arm and found
**21.74%** to be grading artifacts rather than model failures (ISSUES #55). The
**923** blind spots in the 2024 arm have had no such pass.

Everything in RQ3 compares the two arms. Chapter 7 currently argues that the
comparison survives the artifact correction *because both arms share a grader*.
That is a reasonable argument and it is **not a measurement**, which is why ch7
names it the most important open item in the thesis. The script exists, the
judge is calibrated (96.8% precision, misses 16.1%, conservative in the
direction that matters), and the run costs about a dollar.

**Two outcomes, both publishable.** If the 2024 artifact rate lands near 21.7%,
the comparison holds and a paragraph of hedging becomes a number. If it lands
far away, that is a *finding* — the artifact rate itself moved between
generations.

> **It landed far away.** 15.71% against 20.59%, p = 0.005, confirmed at a wider
> gap by a judge in neither ensemble. The "strictness cancels" argument is
> retired. The RQ3 **ratio** survives and strengthens (2.12× adjudicated against
> 1.90× graded); the growth in the **total** blind region loses its significance
> (+7.6%, p = 0.138) and is withdrawn. Two defects fell out of doing it:
> ISSUES #58, the judge grading its own answers in every 2025 case, and #59, two
> of the four vetted outside judges being unusable. RESULTS Finding 12,
> ch5 §5.5 and §5.10, ch7 §7.4 and §7.4b.

### 4.2 — the walkthrough found two defects; fix them `A` · ✅ **done 2026-08-26**

§6.3 predicts three failures. Two are design defects the tool could simply not
have:

- **E3's brush has no visible affordance.** It is a drag on a bare canvas,
  mentioned only in step 3 of a "Try this" panel. A dashed hint rectangle on
  first arrival, or a labelled *select a region* control, removes the guess.
- **E5 is the only two-view task and nothing links the views.** No side-by-side,
  no shared filter, no prompt to compare. A single "compare with the generation
  diff" control would close it.

**Why this is worth more than the six hours it costs.** Right now Chapter 6
says *here is what would go wrong for a user.* After this it says **the
inspection found two defects and the instrument was revised in response, and
here is the before and the after.** That loop — validate, then re-enter the
design — is exactly what Munzner's nested model asks for, and it is the strongest
possible answer to "you evaluated your own tool": the evaluation *changed* the
tool, which a rubber-stamp evaluation never does.

Keep the pre-fix walkthrough output in the chapter. The comparison **is** the
result, and deleting the failing version would destroy the evidence.

> **Done.** Both went 1 → 0 unaffordanced steps. `PATH_BEFORE` in
> `walkthrough_audit.py` holds the 25 Aug grading verbatim so the script prints
> the before and the after side by side, and ch6 §6.3b reports both — including
> the two things the fix did **not** solve: E3 can still be answered by eye, and
> E5's new card compares *for* the participant, which is a weaker task than the
> one it replaced.

### 4.3 — one command rebuilds every figure `A + B` · ✅ **done 2026-08-26**

There is a real pipeline behind this project and no single entry point into it.
A `RUNBOOK.md` plus a `make all` equivalent that goes parquet → `export_web.py`
→ `check_writeup.py` → `pytest`, ending in *225 figures match, 62 tests pass*,
is a few hours of work.

**It is the cheapest credibility available.** A committee member who can rebuild
one figure believes all of them; one who cannot has to take 20,000 words on
trust. It also protects the thesis from its own worst failure mode, which this
record shows five times over: a number that was right when it was typed.

> **Done**, and it grew a stage nobody planned. `scripts/reproduce.py` runs
> export → figures → **parse-check** → walkthrough → arms → tests, in 19 s with
> `--fast`. The parse-check stage exists because the deck is prerendered and a
> syntax error there fails loudly, while the **tool is not** — a broken edit
> would have shipped silently and been found by a person opening the link.
> `--list` names the paid stages and what they would cost, so what is *not*
> verified is stated rather than implied.

### 4.4 — the preprint's headline is a decision, not a finding `B` · ✅ **decided 2026-08-26**

The abstract in Phase 3 leads with the independence violation and 2.5% silent
consensus. Both are true and both are **warnings** — they tell a practitioner
their guardrail is worse than they thought and leave them there.

The ensemble ablation produced something else: across all **154** ensembles
buildable from the eight models, error correlation predicts the blind-spot rate
at **+0.917** while mean accuracy predicts it at **−0.366**. Read plainly:
**choose an ensemble for decorrelation, not for accuracy** — and the more
accurate ensemble is often the more dangerous one.

That is a *recommendation somebody can act on tomorrow*, derived from a
measurement nobody else has made, and it costs nothing to promote it. The
independence violation becomes the setup; the decorrelation rule becomes the
result. For the PhD track this is the difference between a paper that gets cited
and one that gets nodded at.

### Considered and not doing

| | why |
|---|---|
| **An LLM driving the six-task study** | The unmoderated mode and a vision model make it technically possible, and it is genuinely novel. It is also contentious enough that a committee could spend the whole defence on the method rather than the thesis. The honest analytical evaluation in ch6 is worth more than a disputed synthetic one. Revisit for the VIS paper, after graduation |
| **Re-running with a fifth model family** | Does not test a new claim. The independence result is already 9.0x |
| **Re-embedding the map with a better encoder** | The clustering measure is 18% tighter than chance, which is modest, and a prettier map does not make it less modest |

---

## Open questions blocking planning

All four of the original questions are answered, and they are kept here with
their answers because a planning file that quietly deletes what it was once
worried about cannot be checked afterwards.

1. ~~**Who is the second annotator?**~~ **Devesh**, 2026-08-26. 115 cases
   blind, κ = 0.962 [0.904, 1.000] stratum-weighted over 341.
2. ~~**Who are the expert-evaluation participants?**~~ **Nobody.** The study was
   not run and Chapter 6 is analytical, which §6.1 states in its first
   paragraph and §6.7 costs out in full.
3. ~~**9 hours or 197 hours?**~~ **~138 h**, measured at 0.34 gen/s by
   `time_local.py`. `RESULTS.md`'s "~9 h" was wrong by 15× and had never been
   run — ISSUES #54.
4. ~~**Is Phase 2 on track on 1 November?**~~ **Retired 2026-08-30.** The gate
   decided whether Phase 3 was written properly or assembled fast, and Phase 3
   is no longer in the project. The question that replaces it has no branch in
   it: *are the eight drafts revised, formatted and submitted by 30 September?*
   All 8 are drafted at **34,798 of ~35,500 words**, so what remains is
   revision and formatting rather than writing — which is the one kind of
   remaining work that can be scheduled with any confidence.

**The one live question that is not on this list:** is the analytical evaluation
enough for the committee? Only Dr. Humayoun can answer it, it is the first ask
on the deck's plan slide, and 4.2 below is the strongest thing that can be done
if the answer is "nearly".

---

## What this file replaced

- `TODO.md` #1 → 0.6 · #2 → 2.2 (reduced to two paths) · #3 → 2.1 · #4 → Phase 2
- `ASSESSMENT.md` §3.1 rows 1–9 → 0.3, 0.5, 0.1, 2.5, 1.5, 1.4, 2.1, 1.6, 0.6
- `ASSESSMENT.md` §3.2 rows 10–13 → cut, cut, 3.2, 3.3
- New, not previously on any list: **1.1, 1.2, 1.3, and the whole of Phase 2**
