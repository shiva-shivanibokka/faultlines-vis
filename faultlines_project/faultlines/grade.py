"""Level 3 — mark every answer right or wrong. No human involved.

Three tiers, cheapest first, stop at the first that fires:
  1. exact      normalised string equality
  2. alias      the dataset's own list of accepted answers
  3. semantic   cosine >= grade_threshold against gold or any alias

The answer key is used to EVALUATE the signal, never to compute it. That split
is what keeps the whole claim falsifiable.

KNOWN WEAKNESS -- the semantic tier is blind to negation. "Bears wear armor"
scores >0.80 against "Bears do not wear armor" and is marked CORRECT. Sentence
embeddings put a claim and its negation close together; that is a property of
the encoder, not a bug here. It bites TruthfulQA specifically, whose whole
design is true-vs-plausible-false pairs, and it makes errors look like
successes -- which would shrink the Audit population and flatter the AUC.
Measured, not guessed: run_pilot.py reports how many TruthfulQA items were
decided by the semantic tier. If that number is large, the fix is an NLI
entailment check for TruthfulQA only. Do not raise the threshold globally --
that would break paraphrase matching on PopQA, which the tests pin.

    python -m faultlines.grade --pilot
"""
from __future__ import annotations

import argparse
import re
import string

import pandas as pd

from .config import seq, stage
from .semantics import embed

_ARTICLES = re.compile(r"\b(a|an|the)\b")

# Datasets whose golds are SHORT SPANS ("Betty Comden", "1964"), where a
# containment hit is meaningful. TruthfulQA is excluded: its golds are full
# sentences, so a substring match says nothing and negation would invert the
# meaning while still containing the words.
# Was ("popqa", "simpleqa") -- written before TriviaQA and HaluEval existed, and
# still naming SimpleQA after it was dropped. TriviaQA is 42% of the corpus, so
# the omission silently mis-graded the largest dataset.
SHORT_SPAN = ("popqa", "simpleqa", "triviaqa", "halueval")

# The answer must be at least this fraction of the candidate to count as a
# short form. "Sheppey"/"Isle of Sheppey" is 0.47 and is correct; "York"/"New
# York City" is 0.31 and is NOT ("York" alone is a different city). A pure
# substring test with no ratio guard would accept both.
_SHORT_FORM_RATIO = 0.4

# Rows per batched encode in run(). ~5 texts per row, so 5k rows is ~25k texts
# -- fast, and bounded memory regardless of corpus size.
EMBED_CHUNK = 5000


def contains_either_way(answer: str, candidate: str) -> bool:
    """Word-boundary containment in BOTH directions, both normalised.

    answer >= candidate : the model said more than asked. "Gene Kelly and Betty
        Comden" contains the gold "Betty Comden" and is not a hallucination.
    answer <= candidate : the model gave a legitimate short form. "Sheppey" for
        "Isle of Sheppey", "Roots" for "Roots: The Saga of an American Family".
        Ratio-guarded, because this direction is the one that can go wrong.

    Why not just lower the semantic threshold instead: measured on this corpus,
    cosine puts "Henley Rowing Club" vs "Leander Club" at 0.781 (two DIFFERENT
    clubs) and "Sheppey" vs "Isle of Sheppey" at 0.526 (the same place). The
    encoder ranks a wrong answer above a right one, so no threshold separates
    them. Containment is lexical and gets both cases right.
    """
    if len(candidate) < 4 or not answer:
        return False
    if f" {candidate} " in f" {answer} ":
        return True
    if f" {answer} " in f" {candidate} ":
        return len(answer) / len(candidate) >= _SHORT_FORM_RATIO
    return False


def normalise(s: str) -> str:
    """Lowercase, strip punctuation and articles, collapse whitespace.

    The standard SQuAD-style normalisation. Without it, "Canberra." and
    "the Canberra" both count as wrong at tier 1 and everything falls
    through to the expensive tier for no reason.
    """
    s = s.lower().translate(str.maketrans("", "", string.punctuation))
    return " ".join(_ARTICLES.sub(" ", s).split())


def grade_lexical(answer: str, gold: str, aliases,
                  dataset: str | None = None) -> tuple[bool, str] | None:
    """Tiers 1-2 only (exact / alias / contains). None = needs the semantic tier.

    Split out so run() can resolve every cheap row first and then embed the
    remainder in ONE batched call. Measured on the gen-3 pilot: only 191 of
    1,200 rows were decided lexically, so ~83% reach the encoder -- at 43k
    questions x 4 models that was ~143,000 single-item encoder invocations.
    """
    if not answer.strip():
        return False, "empty"

    a = normalise(answer)
    candidates = [gold] + seq(aliases)

    if a == normalise(gold):
        return True, "exact"
    if any(a == normalise(c) for c in candidates):
        return True, "alias"
    if dataset in SHORT_SPAN:
        if any(contains_either_way(a, normalise(c)) for c in candidates):
            return True, "contains"
    return None


def grade_one(answer: str, gold: str, aliases, dataset: str | None = None) -> tuple[bool, str]:
    """Returns (correct, which_tier_decided_it).

    DELEGATES tiers 1-2 to grade_lexical rather than repeating them. It used to
    carry its own copy, and when the containment tier was fixed only the copy in
    grade_lexical was updated -- leaving grade_one still gated on the stale
    ("popqa", "simpleqa") list. run() uses grade_lexical, but track.py calls
    grade_one directly, so Track arms would have kept mis-grading TriviaQA while
    the main pipeline graded it correctly. One implementation, one place to fix.
    """
    cheap = grade_lexical(answer, gold, aliases, dataset)
    if cheap is not None:
        return cheap

    # tier 3: only open-ended answers get this far
    candidates = [gold] + seq(aliases)
    vecs = embed([answer] + candidates)
    from .config import CFG
    thr = CFG["semantics"]["grade_threshold"]
    if max(float(vecs[0] @ v) for v in vecs[1:]) >= thr:
        return True, "semantic"
    return False, "wrong"


def run(pilot: bool = True, tag: str = "") -> pd.DataFrame:
    src = stage("interim", "answers", pilot, tag)
    df = pd.read_parquet(src)

    # Do NOT re-grade rows already decided by NLI. grade_one() is cosine-based
    # and cosine is blind to negation ("bears wear armor" scores >0.80 against
    # "bears do NOT wear armor"), so re-running grade after nli would revert
    # TruthfulQA to the broken grader. Worse, nli.py only records correct_cosine
    # when the column is absent, so the NLI verdicts would vanish with nothing
    # left to show it happened -- and the error runs in the FLATTERING direction,
    # turning real errors into apparent successes.
    if "tier" in df.columns:
        keep = df["tier"] == "nli"
        if keep.any():
            print(f"NOTE {int(keep.sum())} rows already NLI-graded -- leaving them "
                  f"untouched. Re-run `nli --tag ...` if you want them re-decided.")
    else:
        keep = pd.Series(False, index=df.index)

    todo = df.index[~keep]
    from .config import CFG
    thr = CFG["semantics"]["grade_threshold"]

    # Pass 1: lexical tiers, no encoder.
    graded: list[tuple[bool, str] | None] = []
    pending: list[tuple[int, list[str]]] = []      # (position, [answer, *candidates])
    for pos, r in enumerate(df.loc[todo].itertuples()):
        cheap = grade_lexical(r.answer, r.gold, r.aliases, r.dataset)
        graded.append(cheap)
        if cheap is None:
            pending.append((pos, [r.answer] + [r.gold] + seq(r.aliases)))

    # Pass 2: batched encoding, CHUNKED. One call for everything would be ~700k
    # texts at full corpus scale (~1 GB of float32 vectors plus the encoder's own
    # working set) -- the batching that makes the pilot fast is what would OOM
    # the full run. Chunks keep the speedup and bound peak memory.
    if pending:
        done_rows = 0
        for c0 in range(0, len(pending), EMBED_CHUNK):
            block_rows = pending[c0:c0 + EMBED_CHUNK]
            flat, spans = [], []
            for _, texts in block_rows:
                spans.append((len(flat), len(texts)))
                flat.extend(texts)
            vecs = embed(flat)
            for (pos, _), (start, n) in zip(block_rows, spans):
                b = vecs[start:start + n]
                hit = max(float(b[0] @ v) for v in b[1:]) >= thr
                graded[pos] = (hit, "semantic" if hit else "wrong")
            done_rows += len(block_rows)
            if len(pending) > EMBED_CHUNK:
                print(f"  semantic tier {done_rows}/{len(pending)}", flush=True)
        print(f"semantic tier: {len(pending)} rows in "
              f"{(len(pending) + EMBED_CHUNK - 1)//EMBED_CHUNK} batched encode(s)")
    if "correct" not in df.columns:
        df["correct"], df["tier"] = False, ""
    df.loc[todo, "correct"] = [g[0] for g in graded]
    df.loc[todo, "tier"] = [g[1] for g in graded]

    df.to_parquet(src)
    print(df.groupby("model")["correct"].mean().round(3).to_string())
    print("\ntier that decided it:")
    print(df["tier"].value_counts().to_string())
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--tag", default="")
    _a = ap.parse_args()
    run(pilot=_a.pilot, tag=_a.tag)
