#!/usr/bin/env python
"""A panel of judges from OUTSIDE the ensemble, so the obvious objection cannot
be raised at all.

    python scripts/judge_panel.py --check     # identity gate, spends ~nothing
    python scripts/judge_panel.py             # judge all 430, ~3 x 430 calls
    python scripts/judge_panel.py --result

WHY

`adjudicate.py` used Qwen3-235B, which is a member of the ensemble it judges.
Self-favouring was measured and not found (kappa 0.696 on its own family's
answers against 0.686 on the others'), but "we checked and it was fine" is a
weaker position than "the question does not arise". These three judges share no
developer with the ensemble:

    DeepSeek-V3.2             different developer, different pipeline
    Kimi-K2-Instruct          Moonshot; instruct, not a reasoning model
    Olmo-3.1-32B-Instruct     Allen Institute, trained on Dolma -- a fully
                              documented open corpus. The strongest available
                              break in DATA lineage, which is the thing this
                              thesis argues actually drives correlated error
    phi-4                     Microsoft; a synthetic-data-heavy recipe, which
                              is the decorrelation lever config.yaml names

Three judges vote, majority, ties resolved to UNCLEAR rather than to either
verdict -- a tie is genuinely an undecided case and forcing it would invent
agreement.

TWO CHECKS BEFORE PAYING, both of them lessons this project already learned:

  IDENTITY (#31)  a provider once served 2025 weights under 2024 names. --check
                  puts the same probes to all three and refuses to proceed if
                  any pair answers identically, because a panel of three that is
                  secretly one model is worse than a single judge honestly
                  labelled.
  POSITION BIAS   LLM judges are known to be swayed by the order options are
                  presented in, and almost nobody checks. Every case is judged
                  twice, once with the accepted answers first and once with the
                  bait first, and the flip rate is reported. A judge that
                  changes its mind on order is not measuring the answer.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import path, seq               # noqa: E402
from faultlines.generate import ask, ask_retry        # noqa: E402

OUT = path("processed", "judge_panel.parquet")
SRC = path("processed", "handlabels.parquet")

# Four developers, none in the ensemble, none of them a REASONING model.
# MiniMax-M2.7 was the first pick and failed the gate below: it spends its
# 64-token budget on reasoning tokens and returns an empty string, which is
# standing rule 1 -- an empty answer is a failed call, not a result. Four are
# listed so the panel still has three if one is unavailable on the day.
# Olmo is the interesting one: trained on Dolma, a fully documented open
# corpus, and therefore the strongest available break in DATA lineage -- which
# is what this thesis argues actually drives correlated error.
JUDGES = [
    "deepseek-ai/DeepSeek-V3.2",
    "moonshotai/Kimi-K2-Instruct-0905",
    "allenai/Olmo-3.1-32B-Instruct",
    "microsoft/phi-4",
]

HEAD = """You are checking whether an answer to a factual question should be \
graded correct.

QUESTION
{q}

THE ANSWER GIVEN
{a}
"""
ACCEPT = "\nANSWERS ACCEPTED AS CORRECT\n{gold}\n"
BAIT = "\nANSWERS COUNTED AS WRONG\n{bait}\n"
TAIL = """
Decide whether the answer given means the same thing as one of the accepted \
answers. Differences of spelling, word order, abbreviation, added detail or \
phrasing do not make an answer wrong. A different fact does.

Reply with exactly one word:
CORRECT   the answer means one of the accepted answers
WRONG     the answer states something different
UNCLEAR   it genuinely cannot be decided from what is shown"""

WORDS = {"correct": True, "wrong": False, "unclear": None}


def verdict(text: str):
    for w in str(text).lower().replace("*", " ").split():
        w = w.strip(".,:;!\"'")
        if w in WORDS:
            return WORDS[w]
    return None


def prompt(r, bait_first: bool) -> str:
    gold = str(r["gold"])
    al = [str(x) for x in seq(r.get("aliases")) if str(x) != gold]
    g = ACCEPT.format(gold="\n".join("- " + x for x in [gold] + al))
    meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
    inc = [str(x) for x in seq(meta.get("incorrect"))]
    b = BAIT.format(bait="\n".join("- " + x for x in inc)) if inc else ""
    body = (b + g) if bait_first else (g + b)
    return HEAD.format(q=r["question"], a=r["answer"]) + body + TAIL


def check() -> int:
    """Identity gate. Delegates to the project's own calibrated check.

    The first version of this function invented its own probes -- "capital of
    Australia", "17 x 3", "symbol for gold" -- and its own rule that a pair
    answering all three identically must be one model. Three genuinely
    different models answered Canberra / 51 / Au, so the gate refused a
    perfectly good panel.

    That was a second implementation of something the project already had, and
    it had the bug the original was designed around. `check_provider.py` probes
    with deliberately OBSCURE questions, where different models diverge and the
    same model repeats itself, and its 50% threshold sits in a gap measured on
    real data: different models in the same family agree 9-15%, the same model
    across two runs reproduces at 86-93%, and the two aliased pairs that caused
    ISSUES #31 measured 95.9% and 99.6%.

    Availability is still not identity, and an easy question is not a probe.
    """
    from scripts.check_provider import identity_check

    live = {}
    print(f"probing {len(JUDGES)} candidate judges\n")
    for m in JUDGES:
        try:
            a, _ = ask(m, "Name the capital of Australia in one word.")
        except Exception as e:                             # noqa: BLE001
            print(f"  DEAD {m}\n         {e}")
            continue
        # Standing rule 1: an empty answer is a failed call, not a result. This
        # is what dropped MiniMax-M2.7 -- a reasoning model spends the 64-token
        # budget before it speaks and returns "".
        if not a.strip():
            print(f"  DROP {m}\n         returned an empty answer "
                  f"-- unusable as a judge")
            continue
        live[m] = a.strip()[:40]
        print(f"  OK   {m}\n         {live[m]!r}")

    if len(live) < 3:
        print(f"\nonly {len(live)} judges usable -- a majority vote needs three")
        return 1
    ok = identity_check(list(live))
    print("\n" + ("all usable and distinct -- safe to run" if ok else
                  "REFUSING: the provider is serving one model under several "
                  "IDs.\nA panel that is secretly one judge is worse than one "
                  "judge honestly labelled."))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--result", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    if a.check:
        return check()
    if a.result:
        return report(pd.read_parquet(OUT))

    h = pd.read_parquet(SRC)
    ctx = (pd.read_parquet(path("interim", "answers.parquet"),
                           columns=["qid", "model", "aliases", "meta"])
             .set_index(["qid", "model"]))
    idx = pd.MultiIndex.from_arrays([h["qid"], h["model"]])
    h["aliases"] = ctx["aliases"].reindex(idx).to_numpy()
    h["meta"] = ctx["meta"].reindex(idx).to_numpy()
    if h.aliases.isna().any():
        raise SystemExit("missing alias lists -- the judges would see a "
                         "different standard from the human")
    if a.limit:
        h = h.head(a.limit)

    prev = pd.read_parquet(OUT) if OUT.exists() else None
    seen = set(zip(prev.qid, prev.model, prev.judge_model, prev.order)) \
        if prev is not None else set()
    jobs = [(r, m, o) for r in h.to_dict("records") for m in JUDGES
            for o in ("accept_first", "bait_first")
            if (r["qid"], r["model"], m, o) not in seen]
    print(f"{len(h)} cases x {len(JUDGES)} judges x 2 orders = "
          f"{len(h)*len(JUDGES)*2} judgements; {len(jobs)} to run")
    if not jobs:
        return report(prev)

    def one(job):
        r, m, order = job
        txt, _ = ask_retry(m, prompt(r, order == "bait_first"),
                           temperature=0.0, label=f"{m.split('/')[-1]}:{r['qid']}")
        return {"qid": r["qid"], "model": r["model"], "judge_model": m,
                "order": order, "human": r["human"], "machine": r["machine"],
                "stratum": r["stratum"], "raw": txt, "verdict": verdict(txt)}

    rows = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        for i, row in enumerate(pool.map(one, jobs), 1):
            rows.append(row)
            if i % 300 == 0:
                print(f"   {i}/{len(jobs)}", flush=True)
    out = pd.DataFrame(rows)
    if prev is not None:
        out = pd.concat([prev, out], ignore_index=True)
    out = out.drop_duplicates(["qid", "model", "judge_model", "order"], keep="last")
    out.to_parquet(OUT)
    print(f"\n-> {OUT.name}   {len(out)} rows")
    return report(out)


def kappa(a: pd.Series, b: pd.Series):
    m = a.notna() & b.notna()
    x, y = a[m].astype(bool), b[m].astype(bool)
    if not len(x):
        return float("nan"), 0
    po = float((x == y).mean())
    pe = float(x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean()))
    return ((po - pe) / (1 - pe) if pe < 1 else float("nan")), int(len(x))


def vote(v):
    """Majority of three. A tie resolves to UNCLEAR, never to a verdict."""
    c = Counter(x for x in v if x is not None)
    if not c:
        return None
    top, n = c.most_common(1)[0]
    if sum(1 for k, m in c.items() if m == n) > 1:
        return None
    return top if n * 2 > len(v) else None


def report(d: pd.DataFrame) -> int:
    print("\n" + "=" * 70)
    print("JUDGE PANEL  --  three judges, none of them in the ensemble")
    print("=" * 70)

    print("\n  position bias: does the verdict change when the bait is shown first?")
    for jm, g in d.groupby("judge_model"):
        p = g.pivot_table(index=["qid", "model"], columns="order",
                          values="verdict", aggfunc="first")
        both = p.dropna()
        flip = (both["accept_first"] != both["bait_first"]).mean() if len(both) else float("nan")
        print(f"    {jm.split('/')[-1]:<26} {flip:>6.1%} flipped   n={len(both)}")

    # Order is a nuisance variable, so the panel votes over BOTH orderings of
    # every judge -- six votes per case. A judge that flips on order therefore
    # contributes a tie rather than a verdict, which is the honest treatment.
    piv = d.pivot_table(index=["qid", "model"], columns=["judge_model", "order"],
                        values="verdict", aggfunc="first")
    panel = piv.apply(lambda r: vote(list(r)), axis=1)

    first = pd.read_parquet(SRC).set_index(["qid", "model"])
    hum = first["human"].reindex(panel.index)
    mach = first["machine"].reindex(panel.index)

    print(f"\n  {'pair':<34} {'kappa':>7} {'agree':>8} {'n':>6}")
    for name, x, y in [("human vs PANEL", hum, panel),
                       ("human vs machine grader", hum, mach),
                       ("PANEL vs machine grader", panel, mach)]:
        k, n = kappa(x, y)
        m = x.notna() & y.notna()
        po = (x[m].astype(bool) == y[m].astype(bool)).mean() if m.any() else float("nan")
        print(f"  {name:<34} {k:>7.3f} {po:>8.1%} {n:>6}")

    print("\n  each judge on its own, against the human:")
    for jm, g in d.groupby("judge_model"):
        v = g.pivot_table(index=["qid", "model"], columns="order",
                          values="verdict", aggfunc="first")
        agree_only = v[v["accept_first"] == v["bait_first"]]["accept_first"] \
            if "bait_first" in v else v.iloc[:, 0]
        k, n = kappa(first["human"].reindex(agree_only.index), agree_only)
        print(f"    {jm.split('/')[-1]:<26} kappa {k:>6.3f}   n={n} "
              f"(order-stable cases only)")

    und = int(panel.isna().sum())
    print(f"\n  panel returned no majority on {und} of {len(panel)} "
          f"({und/len(panel):.1%}) -- ties and order flips both land here")
    print("\n  This panel shares no developer with the ensemble, so the "
          "self-favouring\n  objection does not arise. It still is not a second "
          "human.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
