"""Level 4 — turn four answers into one disagreement score.

  1. group the four answers by MEANING, not by string
  2. weight each group by the summed confidence of its members
  3. score = 1 - (largest group's weight / total weight)

0 = the four models agreed. ->1 = they split, and the split is not explained
away by one low-confidence outlier.

Worked example (the one in the proposal):
  Canberra .99 | Canberra .98 | Canberra .97 | Sydney .30
  unweighted  1 - 3/4      = 0.25
  weighted    1 - 2.94/3.24 = 0.09
The weighting is the point: three confident models against one hesitant
dissenter is not real disagreement, and the unweighted score overstates it.

    python -m faultlines.disagree --pilot
"""
from __future__ import annotations

import argparse
import math

import pandas as pd

from .config import stage
from .semantics import cluster, cluster_many


def score(answers: list[str], confidences: list[float],
          ids: list[int] | None = None) -> dict:
    """Disagreement for one question. Returns the score plus its parts.

    ids lets a caller supply cluster assignments computed in a batch (see
    semantics.cluster_many); omitted, it clusters on the spot exactly as before.
    """
    ids = cluster(answers) if ids is None else ids
    weight: dict[int, float] = {}
    count: dict[int, int] = {}
    for c, conf in zip(ids, confidences):
        # a NaN confidence (failed generation) still counts as a vote, but
        # contributes no weight -- better than dropping the answer silently
        weight[c] = weight.get(c, 0.0) + (0.0 if math.isnan(conf) else conf)
        count[c] = count.get(c, 0) + 1

    total = sum(weight.values())
    n = len(answers)
    return {
        "disagreement": 1 - max(weight.values()) / total if total > 0 else float("nan"),
        "disagreement_unweighted": 1 - max(count.values()) / n,
        "n_clusters": len(set(ids)),
        "clusters": ids,
    }


def _conf(x) -> float:
    return 0.0 if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def ensemble_answer_correct(ids: list[int], confidences: list[float],
                            correct: list[bool]) -> bool:
    """Is the answer the ensemble would give correct? ISSUES #67.

    The ensemble's answer is its largest meaning cluster. Two ties need a rule,
    and until 2026-09-27 both were settled by accident:

      * CLUSTER SIZE. When the four models give four different answers (9,029
        questions, 26.5%, on the deduplicated corpus) or split two against two, there is no largest cluster.
        `value_counts().index[0]` returned the first cluster, which is the one
        holding the first answer in file order -- always Llama's. The headline
        AUC moved between 0.862 and 0.892 depending on which model happened to
        be listed first.
      * CORRECTNESS WITHIN THE CLUSTER. Answers the encoder merged can still be
        graded differently; `.mode().iloc[0]` on a 1-1 tie returned False, so
        the question was labelled wrong.

    Now: the largest cluster; a size tie goes to the larger SUMMED confidence
    (the same quantity the weighted score uses), and then to the cluster holding
    the single most confident answer. Within the cluster, the majority verdict;
    a tie goes to the most confident member. Every rule is a property of the
    answers, none of the order they were stored in.
    """
    members: dict[int, list[int]] = {}
    for i, c in enumerate(ids):
        members.setdefault(c, []).append(i)
    conf = [_conf(x) for x in confidences]

    def rank(c):
        m = members[c]
        return (len(m), sum(conf[i] for i in m), max(conf[i] for i in m))
    maj = max(members, key=rank)
    m = members[maj]
    right = sum(bool(correct[i]) for i in m)
    if 2 * right != len(m):
        return 2 * right > len(m)
    return bool(correct[max(m, key=lambda i: conf[i])])


def run(pilot: bool = True, tag: str = "") -> pd.DataFrame:
    src = stage("interim", "answers", pilot, tag)
    df = pd.read_parquet(src)

    # Questions with no gradeable answer key (TruthfulQA's "I have no comment")
    # are dropped: no correctness label exists, so any AUC computed over them is
    # invented. See nli.is_ungradeable.
    if "gradeable" in df.columns:
        dropped = df.loc[~df["gradeable"], "qid"].nunique()
        df = df[df["gradeable"]]
        if dropped:
            print(f"dropped {dropped} ungradeable questions (no usable answer key)")

    # The same question asked twice under two ids is one question (ISSUES #66).
    # Only the full corpus has a question table to deduplicate against; pilot
    # and tagged arms share qids with it, so they drop the same set.
    from .datasets import duplicate_qids
    dups = duplicate_qids()
    n_dup = df.loc[df["qid"].isin(dups), "qid"].nunique()
    df = df[~df["qid"].isin(dups)]
    if n_dup:
        print(f"dropped {n_dup} duplicate questions (same text, same gold)")

    # Cluster EVERY question's answers in one encoder call, then score from the
    # pre-computed ids. Same algorithm, same output -- but the per-question path
    # costs ~96 ms each, which is ~68 minutes on the 42,591-question corpus, and
    # nearly all of that is encoder start-up rather than work.
    groups = list(df.groupby("qid", sort=False))
    all_ids = cluster_many([g["answer"].tolist() for _, g in groups])

    rows = []
    for (qid, g), ids in zip(groups, all_ids):
        s = score(g["answer"].tolist(), g["confidence"].tolist(), ids=ids)
        # What the ensemble would ACTUALLY answer: the largest meaning cluster.
        # This is the honest prediction target -- see the note on any_wrong below.
        ids = s["clusters"]
        majority_wrong = not ensemble_answer_correct(
            ids, g["confidence"].tolist(), g["correct"].tolist())
        rows.append({
            "qid": qid,
            "dataset": g["dataset"].iloc[0],
            "question": g["question"].iloc[0],
            "gold": g["gold"].iloc[0],
            "meta": g["meta"].iloc[0],
            "disagreement": s["disagreement"],
            "disagreement_unweighted": s["disagreement_unweighted"],
            "n_clusters": s["n_clusters"],
            # THE PREDICTION TARGET. "Is the answer the ensemble would actually
            # give wrong?" Disagreement does not determine this -- models can
            # split with the majority still right, or agree and all be wrong.
            "majority_wrong": majority_wrong,
            # DO NOT use any_wrong as a headline target. It is mechanically
            # implied by the score: with one gold answer, N different answers
            # means at most one can match, so any_wrong is TRUE by arithmetic
            # whenever the models split. Measured on the pilot: n_clusters=3
            # gave any_wrong 100% of the time, n_clusters=2 gave 92.7%. Scoring
            # against it produced a flattering 0.911 AUC that meant nothing.
            # Kept only for diagnosis and to make the inflation visible.
            "any_wrong": bool((~g["correct"]).any()),
            "all_wrong": bool((~g["correct"]).all()),
            # the Audit population (Level 12): everyone agreed, everyone wrong
            "silent_consensus": bool(s["n_clusters"] == 1 and (~g["correct"]).all()),
        })

    out = pd.DataFrame(rows)
    dest = stage("processed", "records", pilot, tag)
    out.to_parquet(dest)

    print(f"-> {dest}  ({len(out)} questions)")
    print(f"mean disagreement   {out.disagreement.mean():.3f} "
          f"(unweighted {out.disagreement_unweighted.mean():.3f})")
    print(f"silent consensus    {out.silent_consensus.sum()} "
          f"({out.silent_consensus.mean():.1%})  <- the Audit population")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--tag", default="")
    _a = ap.parse_args()
    run(pilot=_a.pilot, tag=_a.tag)
