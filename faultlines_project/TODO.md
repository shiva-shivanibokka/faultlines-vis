# TODO

> **Superseded 2026-08-25 by `PLAN.md`.** That file merges these four items with
> the `TASKS.md` evaluation obligation, the write-up itself (which was never on
> any list and is the largest item in the project), and the work that came out
> of `ASSESSMENT.md`. It is phased, costed, and marked for which of the two
> goals each row serves. **Work from `PLAN.md`, not from here.**
>
> Kept because the reasoning below - particularly item 1's note on what should
> have been flagged before the deletion - is worth not losing.


Deferred work, in dependency order. Anything not here is done — see
`RESULTS.md` (what is true), `ISSUES.md` (zero open), `TASKS.md` (task
abstraction), `EVOLUTION.md` (how the project changed).

**Nothing below needs a GPU, an API credit, or a provider to behave.**

---

## 1. Restore the related-work material  ⬜ *deferred 2026-07-29*

Removing `version-1/` also removed the only related-work and citations
groundwork in the project. It is needed for the write-up.

```
version-1/FaultLines_RelatedWork_Analysis.md
version-1/FaultLines_RelatedWork.pptx
version-1/FaultLines_RelatedWork_v2.pptx
version-1/FaultLines_Sources_and_Method.docx
version-1/FaultLines_Detailed_Companion.docx
```

Recover with:

```bash
git checkout f41d989 -- version-1/FaultLines_RelatedWork_Analysis.md \
  version-1/FaultLines_RelatedWork.pptx version-1/FaultLines_RelatedWork_v2.pptx \
  version-1/FaultLines_Sources_and_Method.docx \
  version-1/FaultLines_Detailed_Companion.docx
```

Then move them to a `writeup/` folder so the repo does not reacquire
`version-1/`'s superseded drafts.

**Note for the record:** this should have been flagged *before* the deletion.
"Superseded drafts" was true of the old proposal documents and **not** true of
the sources and related-work analysis, which have no replacement anywhere in the
project. The instruction was to remove unnecessary files; the error was mine in
classifying these as unnecessary without checking what depended on them.

## 2. Discovery walkthroughs  ⬜ *deferred 2026-07-29* · ~1 day

2–4 documented paths through the tool that reach a finding a table does not show.
Candidates already identified in `TASKS.md` §6:

| path | reaches | task |
|---|---|---|
| Map → colour by blind spots → brush a dense region → inspector | blind spots **cluster**, and 99.5% sit outside the dataset the proposal predicted | T3 |
| Inspector → generation diff → filter *newly hidden* | **690 newly hidden vs 364 hidden in both** — an upgrade hides more blind spots than it inherits. The walkthrough should reach the 78% (already wrong in 2024, merely disagreeing), since that is what makes it a detectability finding | T5 |
| Inspector on a single case | the **grading-artifact** discovery: all eight models across both generations answered "Bangladesh" where the reference answer was "People's Republic of Bangladesh" | T4 |
| Signal panel → filter to one dataset | 0.862 overall hides **0.646** on TruthfulQA | T1 |

**Claude can draft these from the data. It cannot manufacture the "I did not
expect that."** Walk each path yourself afterwards and say where it felt wrong —
that reaction is the part a reader believes.

## 3. Expert evaluation  ⬜ · ~2 days + scheduling — **CRITICAL PATH**

Protocol is written: `TASKS.md` §5, six tasks with success criteria fixed in
advance so the study cannot drift. What is missing is **people**.

This is the only remaining item that moves at other people's calendar speed
rather than at work speed. Recruiting was taken on by Shivani 2026-07-29.

## 4. The write-up  ⬜

Raw material that already exists, so this is assembly rather than invention:

| chapter | source |
|---|---|
| results + limitations | `RESULTS.md` — starts with the "what to quote" claims table |
| methodology / how the project changed | `EVOLUTION.md` |
| threats to validity | `ISSUES.md` — grouped by class, with the four standing rules |
| design chapter | `TASKS.md` — personas, tasks, why/what/how, out-of-scope |
| related work | **blocked on item 1** |

---

## Done — for contrast

- all model work: 5 research questions, 42,591 questions, 170,364 graded answers, 0 failures
- 430 verdicts hand-labelled, blinded, two strata → ISSUES 1b closed
- 42 defects found and fixed · **zero open issues** · 62 tests passing
- deck + tool built, browser-tested, deployed, auto-deploying from a private repo
- task abstraction
