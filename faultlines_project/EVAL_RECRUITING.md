# Expert evaluation — recruiting, and how to run a session

> **STATUS 2026-08-26: this study was never run, and nobody is being recruited.**
> The author relocated during the window in which it would have happened.
> Chapter 6 reports an *analytical* evaluation instead and says so in its first
> paragraph.
>
> **This file is kept complete and unchanged below, deliberately.** The
> protocol, the message, the session script, the note sheet and the instrumented
> unmoderated mode at `?study=1` all still work, so anyone who picks this project
> up can run the study without redesigning it. §6.6 of the thesis lists the four
> things it would establish that the analytical evaluation cannot, and two of
> those are written as **falsifiable predictions** so they could be scored.
>
> Do not read the sentences below as a plan. Read them as a specification that
> was written before the results existed and then not run.

Everything needed to book and run the study in `TASKS.md` §5. Three parts:
a message to send, a script to follow, and a sheet to fill in.

**Target: 3–5 people, 45 minutes each, remote is fine.** Three is enough for a
capstone; four is comfortable. This is qualitative evidence that the instrument
supports the tasks it was designed for, not a study with statistics.

---

## Part 1 — who to ask

**Not visualization people.** Dr. Humayoun is the visualization expert and the
study does not test visualization craft. It tests whether someone who works with
model outputs can reach a finding with the tool.

| you want | in practice |
|---|---|
| **Someone shipping a system that queries several models** | the most valuable participant, and the easiest to find. Any engineer at a company using LLMs |
| **A safety or evaluation researcher** | an NLP or ML grad student |
| **Someone who has built or cleaned a QA dataset** | knows what a bad answer key looks like |

**They do not need to know anything about this project.** Knowing less is
better: the study measures whether the tool explains itself.

**Where to ask, roughly in order of yield**

1. **Dr. Humayoun and VI-Lab.** This is exactly what an advisor's network is
   for, and asking is not an imposition — it is the normal way these studies get
   staffed.
2. **SFSU CS grad students** working on anything ML-adjacent.
3. **Anyone you know in industry** doing LLM work. Remote, 45 minutes, no prep.
4. **Other capstone students** — a peer who has run a study will give you better
   feedback on the *protocol* than on the tool, which is also useful.

**Do not use:** anyone who has seen the results, anyone who helped build it, and
anyone you would feel awkward watching struggle. E3 measures whether the brush is
discovered *without prompting*, and you will prompt a friend without meaning to.

---

## Part 2 — the message to send

> **Subject: 45 minutes to try a tool for my thesis?**
>
> Hi ___,
>
> I'm finishing my M.S. in Data Science & AI at SFSU and I need three or four people to spend
> 45 minutes with the tool I built, so I can find out whether it works for
> someone who isn't me.
>
> **What it is.** I asked four different AI models the same 42,551 factual
> questions and studied the cases where all four agreed and all four were wrong —
> the blind spot in "ask several models and trust them when they agree." The tool
> lets you explore where those failures are.
>
> **What I'd ask you to do.** Six short tasks — find a case, decide whether a
> failure would survive a model upgrade, that sort of thing. I watch and take
> notes. **I won't help**, which is the whole point: I need to know what is
> obvious and what isn't.
>
> **What you need.** A browser and 45 minutes. No preparation, no background in
> my project, and it is genuinely more useful if you have none. Remote over
> Zoom/Meet is fine.
>
> You'd be credited in the acknowledgements. If it's useful, the project is at
> https://faultlines-peach.vercel.app — but please **don't read it beforehand**,
> because that would spoil what I'm measuring.
>
> Any 45 minutes in the next few weeks would help enormously.
>
> Thanks,
> Shivani

**Send it to more people than you need.** Expect roughly half to say yes and half
of those to reschedule at least once. To land four sessions, ask eight.

---

## Part 2b — the unmoderated option, which is probably the one to use

A moderated session costs **45 minutes of two calendars at the same time.** That
is what makes recruiting hard, not geography — and it is why this exists.

**Send this instead of booking a call:**

> https://faultlines-tool.vercel.app/?study=1
>
> It walks you through six short tasks, about half an hour, whenever suits you.
> At the end it gives you a file to send back. Nothing is uploaded anywhere.

The tool presents each task, records what you actually do with timings, asks you
to type an answer, and exports one JSON at the end. **You can stop and come back**
— it remembers where you were.

### What changes about the evidence

| moderated | unmoderated |
|---|---|
| think-aloud, so you hear the reasoning | only what they choose to type |
| your note: "found the brush ✓" | `{"what":"brush","t":252.4}` — timestamped |
| you might prompt without meaning to | **impossible to prompt** |
| realistically 3–4 people | realistically 8–12 |

Losing think-aloud is a real cost and Chapter 6 should say so. What is gained is
larger: every action is timestamped rather than remembered, there is no
experimenter effect at all, and the sample can be big enough that one confused
participant does not dominate the finding.

**Unmoderated remote usability testing is a standard method**, not a downgrade.
It is a different trade.

### Mixing the two is fine

The task wording is read verbatim from the moderated script below, so a mixed
sample is still one study. If you land two live sessions and six asynchronous
ones, report both and say which is which.

### What comes back

One file per participant: their typed answers, the labels they left in tab 2,
seconds spent per task, and every logged interaction. Save it to
`writeup/eval/` beside the note sheet.

**The interactions worth reading first**, because they answer the fixed criteria
directly:

| in the log | the criterion it answers |
|---|---|
| `brush` | E3 — was it discovered **without prompting**? |
| `diff-filter` | E4 — did they use persisted / emerged / healed? |
| `tab` | did they leave tab 1 at all, and when? |
| `skipped` | which tasks defeated people, which is a finding |

---

## Part 3 — the session script

Read the bracketed parts aloud. **Follow it identically every time** — a protocol
that drifts between participants produces notes that cannot be compared.

### Before they arrive

- Tool open at <https://faultlines-tool.vercel.app>, **tab 1**, nothing brushed
- Start a fresh label session in the tool so their E2 labels are theirs alone
- Note sheet open (Part 4), timer ready
- Recording on if they consented; otherwise type verbatim

### Opening (2 min)

> *"Thanks for doing this. I'm testing the tool, not you — if something is
> confusing that is the finding I need. Please think out loud, including when
> you're stuck or annoyed. I'm going to stay quiet and take notes, and I won't
> answer questions about how to use it, because what I most need to know is what
> people work out on their own. There are six tasks, about five minutes each."*

Then, one sentence of context and **no more**:

> *"Four different AI models were asked the same 42,551 factual questions. This
> tool shows where they all agreed and all got it wrong."*

**Do not** explain the views, the tabs, or what silent consensus is. If they ask,
say *"have a look and see what you make of it."*

### The six tasks

Read each aloud, then stop talking. If they are stuck for **90 seconds**, note
it, then offer the smallest possible nudge and **record that you nudged**.

| | say this | you are watching for |
|---|---|---|
| **E1** | *"You're about to ship a system that asks four models and flags disagreement. Which of these four question sets would you trust that guardrail on least, and why?"* | do they find TruthfulQA at 0.646? Do they question n=340 unprompted? |
| **E2** | *"Find a question where every model agreed and every model was wrong. Tell me what went wrong."* | **does anyone identify a grading artifact rather than a model error?** This is the one that matters most |
| **E3** | *"Are these shared failures spread evenly across the map, or concentrated? Show me."* | **is the brush discovered without prompting?** |
| **E4** | *"Here's a shared failure. Would upgrading your models fix it?"* | do they notice the axis is detectability, not correctness? Did their stated belief change? |
| **E5** | *"You have budget for one intervention. Retrieval, or a model upgrade?"* | do they combine two views to answer? |
| **E6** | *"Five minutes, look at whatever you like, keep talking."* | **what do they look for that isn't there?** |

### Closing (3 min)

> *"Two last things. What would you have wanted that wasn't here? And is there
> anything you thought the tool was telling you that turned out to be wrong?"*

Then export their labels from tab 2 and save the file as `E2_<name>.json`.

---

## Part 4 — the note sheet

One per participant. Copy this block into a file named
`writeup/eval/<name>.md`.

```
PARTICIPANT   ____________________     DATE ____________
BACKGROUND    (one line: what they do with model outputs)
CONSENT       recorded? Y / N        named in acknowledgements? Y / N

E1  completed unaided?  Y / N / nudged
    found TruthfulQA 0.646?          Y / N
    questioned n=340 unprompted?     Y / N
    verbatim:

E2  completed unaided?  Y / N / nudged
    ** identified a GRADING artifact rather than a model error?  Y / N **
    case they chose:
    verbatim:

E3  completed unaided?  Y / N / nudged
    ** discovered the brush WITHOUT prompting?  Y / N **
    verbatim:

E4  completed unaided?  Y / N / nudged
    noticed the axis is detectability, not correctness?  Y / N
    stated belief about upgrades BEFORE:
    stated belief AFTER:
    verbatim:

E5  completed unaided?  Y / N / nudged
    combined two views?              Y / N
    answer they gave, and their reason:

E6  what they looked for that was not there  (one line each -- THIS BECOMES
    THE FUTURE-WORK SECTION, so write down every one, even the silly ones):
    -
    -

ANYTHING THEY BELIEVED THAT WAS WRONG:

NUDGES GIVEN  (task, what you said, why)  -- a nudge is data, not a failure:

MINUTES TAKEN  E1 __  E2 __  E3 __  E4 __  E5 __  E6 __
```

---

## Part 5 — what gets reported

Chapter 6 reports **against the criteria fixed in Chapter 3**, not against
whatever the sessions happened to produce. Those criteria, unchanged:

1. **task completion without guidance** — the count of unaided completions per
   task, with every nudge stated;
2. **whether E2 surfaces the grading-artifact insight** — this is the sharpest
   test in the study, because that insight was found *by using the tool* during
   development and is not visible in any table;
3. **whether E4 changes their stated belief about upgrades** — recorded before
   and after, which is why the note sheet asks for both;
4. **every request for something absent** — the E6 list, in full.

**Report failures at full volume.** A study where three participants sail
through six tasks reads as a study that was steered. The nudges, the confusions
and the things they wanted and could not find are the parts a committee believes,
and §7.11 already states what the tool deliberately does not do — so a
participant asking for one of those is a confirmation, not a gap.

**Three participants is a small n and the chapter says so.** The claim this study
supports is *"the instrument supports these tasks for people who did not build
it"*, not *"the instrument is good"*. Keep the claim the size of the evidence.
