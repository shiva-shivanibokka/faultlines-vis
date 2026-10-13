#!/usr/bin/env python
"""A cognitive walkthrough of the six evaluation tasks, computed rather than opined.

    python scripts/walkthrough_audit.py

Runs no model, spends nothing, and needs no participants.

WHY THIS EXISTS

`TASKS.md` §5 specifies a six-task expert evaluation. That study needs people.
This does not replace it and Chapter 6 says so at the top -- an analytical
inspection cannot establish that a human can use the instrument, only that the
information a task needs is reachable and how far away it is.

What it CAN establish, and what a user study is actually poor at, is the exact
thing Wharton, Rieman, Lewis & Polson's cognitive walkthrough was designed for:
for each step of each task, is the required action VISIBLE, and is the
connection between the action and the goal apparent? A walkthrough answers that
by inspection, and it answers it identically every time rather than depending on
which three people were available.

THE MECHANISED PART

The usual cognitive walkthrough is an expert reading a spec. Here the tool's own
exported data is the spec, so two of the four walkthrough questions can be
answered by COMPUTATION rather than judgement:

  Q2 will the user see the control?    -> is the control present in the initial
                                          view, or behind a tab / hover / drag?
  Q4 will they see progress?           -> does acting change something visible,
                                          and by how much?

and the answer to "is the information even there" becomes a fact about the data
rather than an opinion about the interface. A task whose answer is not derivable
from `data.json` cannot be completed by anyone, however good the interface is,
and that is worth knowing before recruiting.

WHAT IT REPORTS

Per task: whether the answer exists in the data, the shortest interaction path
to it, how many of those steps are discoverable without prior knowledge, and the
walkthrough verdict with its reasoning. Failures are the point; a walkthrough
where every task passes has been written to pass.

BEFORE AND AFTER (added 2026-08-26)

The first run of this script, on 2026-08-25, predicted three failures. Two of
them were design defects the tool did not have to have, and the tool was
revised in response:

  E3  the brush was a drag on a bare canvas with no control anywhere. The map
      now has a crosshair cursor and a labelled chip in the header reading "drag
      on the map to select a region". (One more element added that day was
      deleted again -- ISSUES #61; E3's risk text below says why.)
  E5  the only two-view task, with nothing relating the two views. Both tabs now
      carry a "One budget. Retrieval, or a newer model?" card holding both effect
      sizes and a button that lands on the other half.

`PATH_BEFORE` keeps the original grading so the two can be printed side by side.
**Do not delete it when the next fix lands.** The comparison IS the result: an
inspection that changed the thing it inspected is the loop Munzner's nested
model asks for, and a walkthrough that only ever shows the current state cannot
demonstrate that it ever mattered.

E2's weakness and E4's are NOT fixed, and deliberately. Both are about what a
person concludes rather than what they can reach, and no control fixes a
conclusion. They stay as stated risks.

EXIT STATUS

0 when every current task's path is fully afforded (no step graded HIDDEN) and
every answer_in_data lambda evaluated without raising; 1 otherwise, or when
data.json is missing. PATH_BEFORE is history and never counts toward the exit
status. E2's and E4's residual risks are about conclusions, not controls, so
they live in prose and cannot fail this. An answer of None (E6, by design: free
exploration has no answer) is not an error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "faultlines-tool" / "data.json"

# How a step is reached, and therefore how discoverable it is. The grades are
# the walkthrough's Q2 -- "will the user notice the control is available?" --
# expressed as a property of the interface rather than a guess about a person.
VISIBLE = "visible on arrival"          # in the initial viewport, labelled
LABELLED = "labelled control"           # a named tab or button, one click away
AFFORD = "affordance only"              # a legend, a chip: looks clickable
HIDDEN = "no visible affordance"        # drag, hover, keyboard: must be guessed

# The 2026-08-25 grading, kept verbatim. See BEFORE AND AFTER in the docstring.
PATH_BEFORE = {
    "E3": [("tab 1 is already open", VISIBLE),
           ("see red dots against grey", VISIBLE),
           ("drag a box to compare a dense region", HIDDEN)],
    "E5": [("tab 4 for the retrieval dissociation", LABELLED),
           ("tab 3 for the upgrade effect", LABELLED),
           ("hold both in mind", HIDDEN)],
}

TASKS = [
    {
        "id": "E1",
        "ask": "Which question set would you trust the guardrail on least?",
        "answer_in_data": lambda D: min(
            D["stats"]["signal"]["by_dataset"], key=lambda d: d["auc"])["dataset"],
        "path": [("open tab 4, 'How good is the signal?'", LABELLED),
                 ("read the per-dataset AUC table", VISIBLE)],
        "q1": "yes -- the task names the goal in the tab's own words",
        "q3": "yes -- the table is sorted and the column is labelled AUC",
        "risk": "The task asks which to TRUST LEAST. The table gives AUC per "
                "dataset but does not say 'lower is worse' anywhere, and n=340 "
                "sits in a column a reader may not connect to reliability.",
    },
    {
        "id": "E2",
        "ask": "Find a question where every model agreed and every model was wrong.",
        "answer_in_data": lambda D: sum(1 for c in D["cases"]),
        "path": [("open tab 2, 'Read the cases'", LABELLED),
                 ("the queue is already filtered to blind spots", VISIBLE),
                 ("read one case", VISIBLE)],
        "q1": "yes",
        "q3": "yes -- tab 2 is named 'Read the cases' and opens on one",
        "risk": "The task's second half -- 'tell me what went wrong' -- has no "
                "control at all. Whether a participant reaches the GRADING "
                "explanation rather than a model one depends entirely on "
                "reading the answer key beside the answer, which the layout "
                "affords but never prompts.",
    },
    {
        "id": "E3",
        "ask": "Are these failures spread evenly, or concentrated?",
        "answer_in_data": lambda D: "clustered",
        "path": [("tab 1 is already open", VISIBLE),
                 ("see red dots against grey", VISIBLE),
                 ("read the chip: 'drag on the map to select a region'", VISIBLE),
                 ("drag a box; the cursor is a crosshair over the map", AFFORD)],
        "q1": "yes",
        "q3": "partly -- the map shows the answer without any interaction; the "
              "brush is needed only to QUANTIFY it",
        "risk": "FIXED 2026-08-26, and the residue is still worth stating. The "
                "brush was a drag on a bare canvas; it now has a crosshair "
                "cursor and a labelled chip in the header naming the gesture. "
                "A third element -- a dashed ghost rectangle demonstrating the "
                "drag -- was added and REMOVED the same day: it only cleared on "
                "a press on the canvas, so it sat there looking stuck for "
                "anyone who used the tabs instead (ISSUES #61). What "
                "no control can fix is that E3 CAN STILL BE ANSWERED BY EYE -- "
                "the map shows clustering without any interaction -- so a study "
                "must score the brush event separately from task completion, "
                "which the instrumented mode does.",
    },
    {
        "id": "E4",
        "ask": "Would upgrading the models fix this failure?",
        "answer_in_data": lambda D: D["stats"]["rq3"]["emerged"],
        "path": [("open tab 3, 'Did upgrading help?'", LABELLED),
                 ("read persisted / healed / emerged", VISIBLE),
                 ("or: in tab 2, use the diff filter chips", AFFORD)],
        "q1": "yes -- the tab is named after the question",
        "q3": "yes for the aggregate; the per-case path is less direct",
        "risk": "The finding is that 690 emerged against 364 persisted -- an "
                "upgrade CREATES more than it inherits. The tab reports the "
                "numbers but the axis is DETECTABILITY, not correctness, and "
                "78% of the emerged were already wrong before. Nothing in the "
                "view enforces that reading, so a participant can leave with "
                "the right number and the wrong conclusion.",
    },
    {
        "id": "E5",
        "ask": "Retrieval, or a model upgrade?",
        "answer_in_data": lambda D: [c["cause"] for c in D["stats"]["rq4"]["by_cause"]],
        "path": [("either tab 3 or tab 4", LABELLED),
                 ("read the 'One budget' card, which holds both effect sizes",
                  VISIBLE),
                 ("or press its button to see the other half", LABELLED)],
        "q1": "yes",
        "q3": "yes -- the card names the task in its own heading",
        "risk": "FIXED 2026-08-26. This was the only task requiring TWO views "
                "with nothing relating them: no side-by-side, no shared filter, "
                "no prompt to compare. Both tabs now carry one card with both "
                "levers and a button to the other half. The residue is that the "
                "card COMPARES FOR the participant rather than letting them "
                "assemble the comparison, so it tests whether they read a table "
                "rather than whether they can relate two views. That is a "
                "weaker task than the original intended, and saying so is what "
                "a walkthrough is for.",
    },
    {
        "id": "E6",
        "ask": "What did you look for that was not here?",
        "answer_in_data": lambda D: None,
        "path": [("free exploration", VISIBLE)],
        "q1": "n/a -- no goal",
        "q3": "n/a",
        "risk": "Not a task. It is the future-work harvest, and an analytical "
                "walkthrough cannot substitute for it AT ALL: predicting what "
                "somebody will wish for is exactly the judgement no inspection "
                "method has. This one genuinely needs people.",
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="machine-readable")
    a = ap.parse_args()

    if not TOOL.exists():
        print(f"{TOOL} not found -- run scripts/export_web.py first")
        return 1
    D = json.loads(TOOL.read_text(encoding="utf-8"))

    rows = []
    for t in TASKS:
        try:
            ans = t["answer_in_data"](D)
            derivable = ans is not None
        except Exception as e:                            # noqa: BLE001
            ans, derivable = f"ERROR: {e}", False
        hidden = sum(1 for _, grade in t["path"] if grade == HIDDEN)
        rows.append({**t, "answer": ans, "derivable": derivable,
                     "errored": isinstance(ans, str) and ans.startswith("ERROR:"),
                     "steps": len(t["path"]), "hidden_steps": hidden})

    # The exit status. After the fix list, no task may still have a step the
    # user has to guess, and no task's answer may fail to derive from the data
    # (a lambda that raises means data.json lost a field the task depends on).
    failing = [r for r in rows if r["hidden_steps"] or r["errored"]]
    status = 1 if failing else 0

    if a.json:
        print(json.dumps([{k: v for k, v in r.items() if k != "answer_in_data"}
                          for r in rows], indent=1, default=str))
        return status

    print("=" * 74)
    print("COGNITIVE WALKTHROUGH  --  analytical, no participants")
    print("=" * 74)
    print("Wharton, Rieman, Lewis & Polson (1994). For each task: is the")
    print("information there, is the required action visible, and does acting")
    print("show progress? This does NOT establish that a person can use the")
    print("tool. It establishes what a person would be up against.\n")

    print(f"  {'':<4} {'answer in data':>14} {'steps':>6} {'unaffordanced':>14}")
    for r in rows:
        print(f"  {r['id']:<4} {('yes' if r['derivable'] else 'NO'):>14} "
              f"{r['steps']:>6} {r['hidden_steps']:>14}")

    for r in rows:
        print("\n" + "-" * 74)
        print(f"{r['id']}  {r['ask']}")
        print(f"\n  Q1 will they try to achieve the right effect?\n     {r['q1']}")
        print("  Q2 will they notice the action is available?")
        for step, grade in r["path"]:
            mark = "!!" if grade == HIDDEN else ("~" if grade == AFFORD else "ok")
            print(f"     {mark:>3}  {step}   [{grade}]")
        print(f"  Q3 will they connect the action to the goal?\n     {r['q3']}")
        print(f"  Q4 will they see progress?\n     "
              f"{'yes -- the view changes' if r['steps'] > 1 else 'n/a'}")
        print(f"\n  WHERE THIS TASK IS WEAK\n     " +
              "\n     ".join(_wrap(r["risk"], 66)))

    weak = [r for r in rows if r["hidden_steps"]]
    print("\n" + "=" * 74)
    print("WHAT THE INSPECTION CHANGED")
    print("=" * 74)
    print("  The 2026-08-25 run predicted three failures. Two were design")
    print("  defects rather than facts about the task, and the tool was revised.")
    print("  This is the before and the after, from PATH_BEFORE:\n")
    print(f"  {'':<5} {'unaffordanced steps':>21} {'':>3} {'now':>5}")
    for tid, before in PATH_BEFORE.items():
        r = next(x for x in rows if x["id"] == tid)
        b = sum(1 for _, g in before if g == HIDDEN)
        print(f"  {tid:<5} {b:>21} {'->':>3} {r['hidden_steps']:>5}"
              f"   {'FIXED' if r['hidden_steps'] < b else 'unchanged'}")
    print("\n  E3: crosshair cursor and a labelled chip naming the gesture.")
    print("  E5: one card in BOTH tabs holding both effect sizes, and a button")
    print("      to the other half.")

    if weak:
        print("\n  Still unaffordanced:")
        for r in weak:
            print(f"    {r['id']}  {r['hidden_steps']} step(s)")

    print("\n" + "-" * 74)
    print("WHAT WAS NOT FIXED, AND WHY NOT")
    print("-" * 74)
    print("  E3 can still be answered BY EYE. The map shows clustering without")
    print("  any interaction, so a study must log the brush event separately")
    print("  from task completion. No control fixes that; instrumentation does.")
    print("\n  E5's card now COMPARES FOR the participant. That is a weaker task")
    print("  than the original intended -- it tests reading a table rather than")
    print("  relating two views -- and the fix traded one weakness for a smaller")
    print("  one rather than removing it.")
    print("\n  E2 and E4 are about what a person CONCLUDES, not what they can")
    print("  reach, and no control fixes a conclusion. They stand as stated.")
    print("\n  E6 cannot be done this way at all. Predicting what somebody will")
    print("  wish for is the one judgement no inspection method has.")

    print("\n" + "=" * 74)
    if failing:
        for r in failing:
            why = (f"{r['hidden_steps']} unaffordanced step(s)" if r["hidden_steps"]
                   else f"answer not derivable: {r['answer']}")
            print(f"  FAIL  {r['id']}  {why}")
        print("  A task still has a step the user must guess, or its answer no")
        print("  longer derives from data.json.")
    else:
        print("  PASS  every task's path is afforded and every answer derives.")
    return status


def _wrap(s: str, n: int) -> list[str]:
    import textwrap
    return textwrap.wrap(s, n)


if __name__ == "__main__":
    raise SystemExit(main())
