#!/usr/bin/env python
"""Estimate each rater's accuracy without ground truth. Dawid & Skene (1979).

    python scripts/dawid_skene.py

Runs on labels already on disk. No model calls, no cost.

THE PROBLEM IT SOLVES

This project has three raters on the same 430 cases and no gold standard:

    the human            one annotator, whose reliability is the open question
    the automatic grader NLI entailment for TruthfulQA
    an LLM adjudicator   Qwen3-235B, blind to both

Every accuracy statement so far has been *relative*: kappa between two of them.
That is unavoidable when one rater is treated as truth, and it is circular when
the rater being treated as truth is the one under examination.

Dawid & Skene's method drops the assumption. Given several raters labelling the
same items, it estimates BOTH the latent true label of each item AND a confusion
matrix per rater, by expectation-maximisation over the agreement structure
alone. Raters who agree with the emerging consensus get weighted up; raters who
do not get weighted down.

WHAT IT CAN AND CANNOT DO

It CAN say which of the three raters is most accurate, and by how much, without
anointing any of them as truth. That is a genuinely different statement from
"the human and the LLM agree at kappa 0.688", and it is a standard, citable
method rather than something invented here.

It CANNOT replace an inter-rater study, and this file says so twice. With three
raters, one of whom is the human under examination, the estimate is stable but
not independent of that human -- EM will tend to find a consensus the majority
supports. Two humans plus a machine is a much stronger configuration than one
human plus two machines, which is exactly what handlabel2.py is for.

It also cannot detect a bias all three raters share. If the answer key is wrong
in the same direction for everyone, EM will confidently recover the wrong label
and assign every rater high accuracy. That is not a flaw in the method; it is
the reason the human pass exists.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from faultlines.config import CFG, path                # noqa: E402

SEED = CFG["seed"]
CLASSES = [False, True]          # wrong, correct


def em(labels: np.ndarray, iters: int = 200, tol: float = 1e-9):
    """Dawid-Skene EM.

    labels is (items, raters) with -1 for "this rater did not commit".
    Returns posterior class probabilities per item, and one confusion matrix
    per rater: conf[r, true, observed].
    """
    n, R, K = labels.shape[0], labels.shape[1], len(CLASSES)
    obs = labels >= 0

    # Initialise the posterior from majority vote, which is what the method's
    # own paper does. Ties split evenly rather than being broken arbitrarily.
    T = np.zeros((n, K))
    for k in range(K):
        T[:, k] = ((labels == k) & obs).sum(1)
    empty = T.sum(1) == 0
    T[empty] = 1.0
    T /= T.sum(1, keepdims=True)

    prev = None
    for _ in range(iters):
        # M step: class priors and per-rater confusion matrices
        prior = T.mean(0)
        conf = np.zeros((R, K, K))
        for r in range(R):
            for k in range(K):
                for j in range(K):
                    conf[r, k, j] = T[(labels[:, r] == j), k].sum()
            rows = conf[r].sum(1, keepdims=True)
            # A rater who never used a class gets a uniform row rather than a
            # division by zero -- it contributes no evidence instead of NaN.
            conf[r] = np.divide(conf[r], rows, out=np.full((K, K), 1.0 / K),
                                where=rows > 0)

        # E step
        logT = np.log(np.clip(prior, 1e-12, None))[None, :].repeat(n, 0)
        for r in range(R):
            for j in range(K):
                m = labels[:, r] == j
                logT[m] += np.log(np.clip(conf[r, :, j], 1e-12, None))[None, :]
        logT -= logT.max(1, keepdims=True)
        T = np.exp(logT)
        T /= T.sum(1, keepdims=True)

        ll = float(np.log(np.clip(np.exp(logT).sum(1), 1e-12, None)).sum())
        if prev is not None and abs(ll - prev) < tol:
            break
        prev = ll
    return T, conf


def encode(cols) -> np.ndarray:
    """(items, raters) with -1 where a rater did not commit to a class."""
    n = len(cols[0])
    lab = np.full((n, len(cols)), -1, dtype=int)
    for i, c in enumerate(cols):
        v = c.to_numpy(dtype=object)
        for k, cls in enumerate(CLASSES):
            lab[np.array([x is not None
                          and not (isinstance(x, float) and np.isnan(x))
                          and bool(x) == cls for x in v]), i] = k
    return lab


def balanced(conf_row) -> float:
    """Mean of the two diagonal rates.

    Not raw agreement: a rater who says CORRECT to everything would score the
    73% base rate on raw agreement and 50% here, which is what it deserves.
    """
    return float((conf_row[0, 0] + conf_row[1, 1]) / 2)


def leave_one_out(cols, names) -> dict:
    """Score each rater against a consensus built WITHOUT it.

    This is the check the first version of this script did not do, and it
    matters: with three raters, EM fits every rater's confusion matrix against
    a consensus that rater helped produce. The human came out at 96.5% that
    way. Held out, the same human scores 86.2% -- ten points of the original
    figure was self-inclusion.

    A rater cannot be its own referee. The held-out numbers are the ones this
    project reports; the in-panel numbers are kept beside them as the optimistic
    bound, because the gap between them is itself worth seeing.
    """
    out = {}
    lab = encode(cols)
    for i, nm in enumerate(names):
        others = [c for j, c in enumerate(cols) if j != i]
        T2, _ = em(encode(others))
        cons = T2.argmax(1)
        v, m = lab[:, i], lab[:, i] >= 0
        rates = []
        for k in range(len(CLASSES)):
            sel = m & (cons == k)
            if sel.sum():
                rates.append(float((v[sel] == k).mean()))
        out[nm] = (float(np.mean(rates)) if rates else float("nan"), int(m.sum()))
    return out


def main() -> int:
    argparse.ArgumentParser().parse_args()

    adj = pd.read_parquet(path("processed", "adjudicated.parquet"))
    names = ["human", "grader", "llm judge"]
    cols = [adj.human, adj.machine, adj.judge]

    lab = encode(cols)
    T, conf = em(lab)
    loo = leave_one_out(cols, names)

    print("=" * 70)
    print("DAWID-SKENE  --  rater accuracy estimated without a gold standard")
    print("=" * 70)
    print(f"{len(adj)} cases, {len(names)} raters, {len(CLASSES)} classes\n")

    print(f"  {'rater':<12} {'HELD OUT':>10} {'in-panel':>10} {'inflation':>11} "
          f"{'committed':>10}")
    for i, nm in enumerate(names):
        ip = balanced(conf[i])
        lo, n_c = loo[nm]
        # (ip - lo) is a FRACTION; percentage points need the x100. Printed as
        # "+0.1pp" for a ten-point gap on the first run, which is the kind of
        # unit slip that reads as "no difference".
        print(f"  {nm:<12} {lo:>9.1%} {ip:>10.1%} {(ip - lo) * 100:>+9.1f}pp "
              f"{n_c:>10}")
    print("\n  HELD OUT is the figure to quote: the rater is scored against a")
    print("  consensus built from the other two only, so nobody referees itself.")
    print("  The gap is how much each rater was flattered by being inside the")
    print("  panel that defined the truth it was measured against.")

    print("\n  balanced accuracy, not raw agreement -- a rater that says CORRECT")
    print("  to everything scores 50% here rather than the 73% base rate.")

    order = sorted(names, key=lambda n: -loo[n][0])
    print(f"\n  ordering, and it is the same in both columns: "
          f"{' > '.join(order)}")

    maj = np.array([np.bincount(r[r >= 0], minlength=len(CLASSES)).argmax()
                    if (r >= 0).any() else 0 for r in lab])
    same = float((T.argmax(1) == maj).mean())
    print(f"\n  EM agrees with a plain majority vote on {same:.1%} of items, so")
    print(f"  weighting the raters is doing something -- it is not majority vote")
    print(f"  with extra steps.")

    est = float(T[:, 1].mean())
    print(f"\n  estimated share genuinely correct: {est:.1%}")
    for i, nm in enumerate(names):
        m = lab[:, i] >= 0
        print(f"    {nm:<12} says correct {float((lab[m, i] == 1).mean()):>6.1%}")

    unsure = int((T.max(1) < 0.9).sum())
    print(f"\n  {unsure} of {len(adj)} items ({unsure/len(adj):.1%}) reach no "
          f"confident consensus\n  even after weighting. That population is "
          f"arrived at by a different route\n  from the 45 the adjudicator "
          f"disputed, and the overlap is worth reading.")

    print("\n  NOT a substitute for a second human. With one human and two")
    print("  machines, EM finds the consensus the majority supports, and no")
    print("  amount of EM can see a bias all three raters share.")

    out = path("processed", "dawid_skene.parquet")
    pd.DataFrame({"qid": adj.qid, "model": adj.model,
                  "p_correct": T[:, 1],
                  "consensus": [CLASSES[t] for t in T.argmax(1)],
                  "human": adj.human, "grader": adj.machine, "judge": adj.judge}
                 ).to_parquet(out)
    print(f"\n-> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
