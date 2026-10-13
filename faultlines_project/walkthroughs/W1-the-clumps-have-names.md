> **Superseded 2026-08-10 by `faultlines-web/walkthroughs.html`**, which is the
> canonical version: it renders every statistic from `summary.json` instead of
> holding copies, and each step that can be is a **link** into the tool rather
> than an instruction to drag.
>
> This file is kept for the record of what the draft got wrong — that record is
> the useful part — but **do not quote figures from it.** Two copies of a number
> is how #43, #45, #46, #47 and #49 happened.

# Walkthrough 1 — the same question, twice, with one thing changed

**Task:** T3 — *"Are those failures scattered at random, or concentrated in a topic?"*
**Persona:** P1, the ML engineer deciding whether to ship behind a disagreement gate.
**View:** the Map, then the Audit Inspector.
**Time:** about six minutes in the tool, plus one offline check.

> **Rewritten 2026-08-10, after the first draft failed on contact.**
> Two things went wrong when Shivani walked it, and both are recorded here rather
> than tidied away.
>
> 1. **The tool was lying.** Drawing a box filtered tab 2 correctly, but every
>    number in tab 2 still showed the population total — so the box looked
>    broken. Fixed as ISSUES #50.
> 2. **My step 4 was wrong.** I counted blind spots per question template and
>    presented the biggest counts as hot spots. Two of the five were *below* the
>    corpus average — they were big because those templates are common, not
>    because they fail. **A count is not a rate.** Corrected below, and the
>    correction produced a much sharper finding than the error did.

---

## Why this path exists

A table tells you *how many* blind spots there are. It cannot tell you whether
they are anywhere in particular — and that is the difference between *"2.5% of
our questions fail silently"*, which sounds like a rounding error you accept, and
*"our failures have a describable shape"*, which is something you can route
around.

---

## The path

### 1 · Open the tool. Do not touch anything yet.

Tab 1 loads coloured by **"All agreed & all wrong"**:

```
all agreed & all wrong     1,054
everything else           41,497
```

The map places questions by wording alone, so nearby dots are similarly-worded
questions.

### 2 · Are the red dots even?

No — and the size of the effect matters. Blind spots sit **18% tighter** than
chance: mean distance to the nearest other blind spot is **0.105**, against
**0.128** for a random sample of 1,054 questions from the same map.

> Real, and modest. The claim is **not** "blind spots are tightly clustered".
> It is *"they are not uniform"* — enough to justify looking, not enough to
> conclude anything on its own.

### 3 · Drag a box around a dense knot, then open tab 2.

Tab 2 now shows a blue bar:

```
Showing only the 47 cases inside the box you drew on the map.   [✕ clear the box]
```

and the tab badge reads `47 of 1,613`. *(Before #50 was fixed, both read 1,613
and the box appeared to do nothing.)*

Read the first several cases. They look like this:

```
Who was the director of Rocky?
Who was the director of The Town?
Who was the director of The Ring?
Who was the director of Glass?
```

Not a topic — **a sentence pattern.** That is the hypothesis. The tool has now
done its job; the next step confirms it, and the tool cannot do that part.

### 4 · Confirm it offline — and this is where the first draft went wrong

**[OFFLINE STEP]** The tool has no way to count question patterns across the
population. The check below is a script, and the walkthrough should say so
rather than pretend the interface did it.

The naive version — count blind spots per pattern — is misleading:

| pattern | blind spots | **but the rate is** | vs the 2.48% base |
|---|---|---|---|
| `Who was the screenwriter/producer/composer of X?` | **79** | 1.76% | **0.7× — cooler than average** |
| `Who was the director of X?` | 107 | 5.29% | 2.1× |
| `What genre is X?` | 71 | 4.38% | 1.8× |
| `Who is the author of X?` | 62 | 4.08% | 1.6× |
| `In what city was X born?` | 24 | 4.10% | 1.7× |
| `What is the capital of X?` | 10 | 1.44% | **0.6× — cooler than average** |

The crew-role pattern has the second-highest **count** and a **below-average
rate**. There are simply 4,500 such questions. Reading the count as a hot spot is
a straightforward count-vs-rate mistake, and I made it.

### 5 · The real mechanism, found by fixing that mistake

Why is `screenwriter of X` **the most-wrong pattern in the corpus** and yet
almost never a blind spot?

| pattern | ensemble wrong | all four **agreed** | blind spots |
|---|---|---|---|
| `screenwriter/producer/composer of X` | **68.1%** | 8.1% | 1.76% |
| `director of X` | 62.3% | **17.0%** | 5.29% |
| `capital of X` | 10.1% | 73.6% | 1.44% |

**The blind-spot rate does not track how often they are wrong. It tracks how
often they are wrong *together*.** Crew-role questions fail more than any other
pattern — and the models fail *differently* each time, so disagreement catches
them. Nobody famous directed *Rocky*'s sound design; the models guess, and guess
differently.

That is the funnel from slide 7, restated one template at a time.

### 6 · Now the sharpest cut — hold the question fixed and change one thing

Take only `Who was the director of X?` — same wording, same task, same four
models — and split it by whether the film's title is **shared with something
else**. The test is Wikipedia's own convention and involves no judgement:

> Wikipedia keeps the bare name as a title when nothing else claims it, and adds
> a qualifier — `Glass (2019 film)` — **only when the bare name is already taken.**

```
Who was the director of X?          n        blind-spot rate

   title is unique                 511            0.98%     ← BELOW the 2.48% corpus base
   title is TAKEN                1,488            6.85%     ← 7x higher
```

**Same question. Same models. The only thing that changes is whether the title is
shared — and it moves the blind-spot rate seven-fold.** It is not the sentence
pattern. It is the collidable name.

### 7 · Read one, to see what a collision looks like from the inside

```
Who was the director of The Town?      gold: Mike Bartlett

Llama-4-Maverick     Ben Affleck        confidence 0.993
Qwen3-235B           Ben Affleck        confidence 1.000
Mistral-Small-3.2    Ben Affleck        confidence 0.991
Gemma-3-27B          Ben Affleck.       confidence 0.965
```

Ben Affleck directed a 2010 *film* called *The Town*. Mike Bartlett created a
2012 *television series* called *The Town*. The question does not say which.

**[YOUR REACTION — 1]** *Before reading on: write one sentence on what you think
happened here. Whatever you write is the honest reaction, and it is the sentence
a reader will believe.*

The models are not ignorant. **They resolved an ambiguous name to its most famous
owner**, and the key meant the other one. Three more from the same clumps:

| question | all four said | the key says |
|---|---|---|
| Who directed **The Ring**? | Gore Verbinski | Trey Parker |
| Who directed **Glass**? | M. Night Shyamalan | Chris Kennedy |
| In what city was **Robin Williams** born? | Chicago | Christchurch |

The last one is worth sitting with. The famous Robin Williams *was* born in
Chicago. The key is about a New Zealander of the same name.

---

## What this path reaches

**A third failure mechanism.** The project had *obscurity* (never learned it) and
*misconception* (learned something false). This is neither: the model knows the
fact and **attaches it to the wrong referent**. Every model resolves toward fame,
because they were all trained on a web where the famous one dominates — so they
fail **identically**, which is exactly the condition disagreement cannot see.

Corpus-wide, the same test gives **76.1%** of blind spots on an ambiguous name
against **33.5%** of questions the ensemble got right, and the effect survives in
every popularity quartile (**2.8×** overall). **351 of the 1,054 blind spots** are
PopQA entities whose bare name is taken.

---

## The limitation this path also reaches — do not skip it

Some of these are **not model errors**, and the tool surfaces that rather than
hiding it.

`What is the currency of Lithuania?` — all four answered **Euro**; the key says
**Litas**. Lithuania adopted the euro in 2015. **The models are right and the key
is stale.**

So the honest statement of the 1,054:

> Questions where every model agreed and every model was *marked* wrong. Some are
> genuine shared failures; some are ambiguous questions where the models chose a
> defensible different referent; a few are stale or over-strict keys.

**This is a strength, not a hole.** It is persona P3's task — *"is this a real
model error, or is my answer key wrong?"* — arriving unbidden while running P1's.
One path, two tasks, and the second was not designed for.

The 60 answer-key flags bound part of it, but they only catch *shorter-form*
answers. Nothing automatic catches "right about a different Robin Williams" — so
the inspector asks a human.

**[YOUR REACTION — 2]** *Does the 1,054 feel weaker to you now, or does the tool
feel stronger? That sentence, in your words, is the core of the limitations
section.*

---

## What this walkthrough proves about the tool — and what it does not

**Does:** the map and inspector took a reader from *"2.5% fail silently"* to a
falsifiable hypothesis — *"it is about collidable names"* — in about six minutes,
by looking. No table of averages produces that.

**Does not:** the tool cannot *confirm* it. Steps 4, 5 and 6 are scripts. That
division is legitimate — a visual-analytics tool is judged on supporting
**discovery**, and confirmation is a separate act — but the walkthrough must say
which is which, and this one now does.

**The obvious improvement it suggests:** a map colouring for **"is this name
shared?"**. The data already exists (`popqa_wiki_titles.parquet`, full coverage),
it is one more bit in the map payload, and it would let the tool close its own
loop instead of handing off to pandas at the interesting moment. *Not built —
Shivani's call.*

---

## Numbers used here, and where each comes from

| number | source | verified |
|---|---|---|
| 1,054 · 42,551 · 2.48% base | `summary.json` | ✅ |
| 0.105 vs 0.128 nearest-neighbour | `rq2_localize.parquet`, seed 42 | ✅ |
| all per-pattern counts **and rates** | `records.parquet` | ✅ |
| wrong / unanimous / blind per pattern | `records.parquet` | ✅ |
| **0.98% vs 6.85%** within `director of X` | `records` × `popqa_wiki_titles` | ✅ |
| 53.3 / 33.5 / 69.0 / **76.1%** | `popqa_wiki_titles.parquet` | ✅ reproduces `RESULTS.md` exactly |
| 2.8× across popularity quartiles | `RESULTS.md` 2026-08-03 | ✅ |
| all case transcripts | `data.json`, opened individually | ✅ |

*New here and not yet in `RESULTS.md`: the 18%-tighter clustering measure, the
per-pattern rate table, and the 0.98%-vs-6.85% split. The last is the strongest
single number this walkthrough produced and should be added.*
