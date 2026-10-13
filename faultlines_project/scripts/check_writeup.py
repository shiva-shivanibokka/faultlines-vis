#!/usr/bin/env python
"""Check that every figure asserted in the write-up is the one the data holds.

The write-up is prose, so nothing regenerates it and nothing notices when a
number in it drifts from `summary.json`. That is exactly the shape of ISSUES #43
(a published constant with a live source and no link back to it) and #54 (a
figure with no source at all), and a thesis is the most expensive place to
discover it.

Each entry below names a chapter, a string that must appear in it, and the
live value that string has to match. The live value is pulled from
`summary.json` or computed from the stored parquets -- never typed twice.

    python scripts/check_writeup.py                 # check; exit 1 on any failure
    python scripts/check_writeup.py --occurrences   # also print every place each
                                                    # needle occurs, for a human audit

Exit code 1 if anything disagrees, so it can gate a commit.

TWO INDEPENDENT GUARDS (hardened 2026-09-27)

1. Presence. Each needle must occur in its chapter as a figure (found()).
   On its own this is weak: 102 of 244 needles occur two or more times in
   their chapter, so a WRONG second copy ("1,045" where the other copy says
   "1,054") passed, because the right copy satisfied the search.

2. Near-miss scan (near_misses()). For every numeric token in every needle,
   every number in the same chapter that is formatted the same way (same
   integer width, same comma grouping, same decimals, same %/x suffix), is NOT
   equal to it, is close to it (one digit different, two adjacent digits
   swapped, or within 1% relative), and sits in prose that shares vocabulary
   with the real occurrences of the value, is reported as a failure. That is
   the shape of a typo'd copy of a checked figure. A number that is itself a
   checked value anywhere in the thesis is never a near-miss (it is accounted
   for), and genuinely distinct quantities that happen to look alike are
   whitelisted in NEAR_MISS_OK with the reason, so the whitelist is the audit
   trail. Neither guard alone is sufficient; together a wrong copy has to be
   both the only copy (fails guard 1) or a lookalike (fails guard 2).

Also failures, not skips: a chapter file that does not exist, and a
summary.json block that is missing or empty (see REQUIRED). Values are always
read from summary.json -- a re-export changes the needles, never this file.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

# The literals being checked are full of phi, en dashes and minus signs, and a
# Windows console defaults to cp1252, which cannot encode them. Without this the
# checker crashes on its own output rather than on a mismatch -- a tool that
# fails at the point of reporting is worse than no tool.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
WRITEUP = ROOT / "writeup"
S = json.loads((ROOT / "faultlines-web" / "summary.json").read_text(encoding="utf-8"))


def norm(t: str) -> str:
    """Fold the characters that differ typographically but not numerically.

    Prose uses a real minus sign (U+2212) and real dashes; f-strings emit ASCII.
    A checker that fails on that is reporting typography as a data error, and a
    checker that cries wolf gets switched off -- which is the actual risk here.
    """
    return (t.replace("−", "-").replace("–", "-")
             .replace("—", "-").replace(" ", " ")
             .replace(" ", " "))


def pc(x, d=1, sign=False):
    s = f"{x * 100:.{d}f}%"
    return ("+" + s) if sign and x > 0 else s


class Rx(str):
    """A needle that is a regular expression rather than a literal.

    Used for figures the prose states in WORDS ("nearly four times", "sixty-five
    logged defects"). Plain containment is wrong for those: "four times" is a
    substring of "nearly four times", so a check for the one passed on the
    other. A regex with word boundaries and look-behinds says exactly which
    wording is required.
    """


_ONES = ("zero one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n: int) -> str:
    """0..99 as English words, hyphenated the way the prose writes them."""
    if n < 20:
        return _ONES[n]
    t, o = divmod(n, 10)
    return _TENS[t] + ("" if o == 0 else "-" + _ONES[o])


def ratio_wording(r: float, then: str) -> Rx:
    """The wording a ratio supports, as a word-bounded regex.

    Within 0.1 of an integer n: "n times" and NOT "nearly n times". Between
    n-0.5 and n-0.1: "nearly n times". Otherwise "more than n times" (n the
    floor). The old check fell back to the bare substring "four times", which
    "nearly four times" contains, so it passed whatever the ratio was.

    `then` is the regex for the words that must follow ("more densely"), so
    the needle pins the one sentence making the claim: ch3 also says "asking
    one four times", which a bare "four times" would match.
    """
    n = round(r)
    if abs(r - n) <= 0.1:
        head = rf"(?<!nearly )(?<!almost )\b{words(n)}\s+times"
    elif r < n:
        head = rf"\b(?:nearly|almost)\s+{words(n)}\s+times"
    else:
        head = rf"\bmore\s+than\s+{words(int(r))}\s+times"
    return Rx(head + then)


# Every block the checks read, and the fields inside it that must be present
# and non-empty. Several sections used to be wrapped in `if S.get(...)`, so an
# export that wrote {} for a block made those checks VANISH -- the run got
# shorter and still said "all figures match". A missing block is now a failure.
REQUIRED = {
    "signal": ["overall", "by_dataset"],
    "independence": ["phi_mean", "all_wrong", "all_wrong_if_independent", "ratio",
                     "stratified"],
    "ablation": ["n_ensembles", "by_size_2025", "phi_silent", "err_silent",
                 "phi_silent_partial", "phi_auc", "phi_auc_partial"],
    "intervals": ["auc", "vs_semantic_entropy", "share_ratio", "concordance",
                  "blind_rate", "rq4", "rq5", "rq1"],
    "rq1b": ["conf_auc", "best_auc", "best_risk50", "base"],
    "belief": ["counter", "abstain"],
    "adjudicator": ["human_judge", "human_machine", "judge_machine",
                    "self_own", "self_other", "disagreements"],
    "rq3": ["rates", "persisted", "healed", "emerged", "gen2_silent",
            "emerged_was_allwrong", "persistence"],
    "rq4": ["by_cause"],
    "rq5": ["matched", "wiki", "web", "neither", "neither_rate"],
    "rq2": ["corr_pop", "corr_density_within"],
    "funnel": ["all_wrong", "unanimous", "majority_wrong", "any_wrong"],
    "baseline": ["single_model", "n"],
    "abstain": ["n_wrong", "conf_right", "conf_wrong"],
    "corpus": ["asked", "analysed", "generations", "models_new", "models_old"],
    "grader_check": ["judged", "generous", "harsh"],
    "walk": ["base", "patterns", "director", "emerged"],
    "arms": ["judges", "primary"],
    "irr": ["annotators", "strata"],
    "artifact": ["rate", "lo", "hi", "genuine", "n_judged", "by_dataset"],
    "defects": [],
    "handlabels": [],
}


def _empty(v) -> bool:
    return v is None or (isinstance(v, (dict, list, str)) and len(v) == 0)


def missing_blocks() -> list[str]:
    out = []
    for block, fields in REQUIRED.items():
        if block not in S or _empty(S[block]):
            out.append(f"summary.json[{block!r}] is missing or empty")
            continue
        for f in fields:
            if not isinstance(S[block], dict) or f not in S[block] \
                    or _empty(S[block][f]):
                out.append(f"summary.json[{block!r}][{f!r}] is missing or empty")
    return out


def checks() -> list[tuple[str, str, str]]:
    """(chapter file, literal that must appear, what it is)."""
    I, A, R, B_, J = S["independence"], S["ablation"], S["rq1b"], S["belief"], S["adjudicator"]
    sig, rq3 = S["signal"]["overall"], S["rq3"]
    tqa = [d for d in S["signal"]["by_dataset"] if d["dataset"] == "truthfulqa"][0]
    by25 = {r["k"]: r for r in A["by_size_2025"]}
    phi_s = {r["k"]: r["r"] for r in A["phi_silent"]}
    err_s = {r["k"]: r["r"] for r in A["err_silent"]}

    c7 = "ch7-limitations.md"
    out = [
        # Three significant figures, which is what the prose uses everywhere.
        # Checking against the stored 4dp value would force the write-up to
        # quote a precision a correlation does not carry.
        (c7, f"φ = {I['phi_mean']:.3f}", "mean pairwise error correlation"),
        (c7, f"{I['all_wrong'] * 100:.3f}%", "observed all-four-wrong"),
        (c7, f"{I['all_wrong_if_independent'] * 100:.3f}%", "predicted if independent"),
        (c7, f"{I['ratio']:.1f}×", "concordance ratio"),
        (c7, f"{sig['silent']:,}", "silent-consensus count"),
        (c7, f"{sig['n']:,}", "corpus size"),
        (c7, pc(sig["silent"] / sig["n"], 1), "silent-consensus rate"),
        # The chapter states the RELATIVE fall (25%) and the shared-share ratio,
        # not the absolute 2025 rate. Checking for "36%" was checking for a
        # string the chapter never claims -- a badly specified check is a false
        # alarm, and false alarms are how a checker gets switched off.
        (c7, f"{(rq3['rates'][0]['wrong'] - rq3['rates'][1]['wrong']) / rq3['rates'][0]['wrong'] * 100:.0f}%",
         "relative fall in error rate"),
        (c7, f"{by25[4]['silent'] * 100:.2f}%", "k=4 blind rate"),
        (c7, f"{by25[3]['silent'] * 100:.2f}%", "k=3 blind rate"),
        (c7, f"{by25[2]['silent'] * 100:.2f}%", "k=2 blind rate"),
        (c7, f"{by25[3]['lo'] * 100:.2f}% – {by25[3]['hi'] * 100:.2f}%", "k=3 range"),
        (c7, f"{by25[2]['lo'] * 100:.2f}% – {by25[2]['hi'] * 100:.2f}%", "k=2 range"),
        (c7, f"+{phi_s[4]:.3f}", "corr(phi, silent) at k=4"),
        (c7, f"{err_s[4]:.3f}", "corr(err, silent) at k=4"),
        (c7, f"{R['conf_auc']:.3f}", "confidence-alone AUC"),
        (c7, f"{R['best_auc']:.3f}", "best multi-feature AUC"),
        (c7, pc(R["best_risk50"], 2), "risk at 50% coverage"),
        (c7, pc(R["base"], 2), "agreement-region base rate"),
        (c7, f"{J['human_judge']:.3f}", "human vs adjudicator kappa"),
        (c7, f"{J['human_machine']:.3f}", "human vs grader kappa"),
        (c7, f"{J['judge_machine']:.3f}", "adjudicator vs grader kappa"),
        (c7, f"{J['self_own']:.3f}", "kappa on own-family answers"),
        (c7, f"{J['self_other']:.3f}", "kappa on other makers' answers"),
        (c7, f"**{J['disagreements']} cases", "disputed cases for the second human"),
        (c7, f"{tqa['n']}", "TruthfulQA n"),
        (c7, f"{tqa['auc']:.3f}", "TruthfulQA AUC"),
        (c7, f"{S['handlabels']}", "hand-label count"),
    ]

    # ---- chapter 5, the results chapter ----
    c5 = "ch5-results.md"
    F, ds = S["funnel"], {d["dataset"]: d for d in S["signal"]["by_dataset"]}
    B, rq4 = S["baseline"], {c["cause"]: c for c in S["rq4"]["by_cause"]}
    V, ab, W = S["rq5"], S["abstain"], S["walk"]
    pat = {x["name"]: x for x in W["patterns"]}
    out += [
        (c5, f"{S['corpus']['asked']:,}", "questions asked"),
        (c5, f"{S['corpus']['analysed']:,}", "questions analysed"),
        (c5, f"{S['corpus']['generations']:,}", "generations"),
        (c5, f"{F['all_wrong']:,}", "all-four-wrong count"),
        (c5, f"{F['unanimous']:,}", "agreement-region size"),
        (c5, f"{F['majority_wrong']:,}", "ensemble-wrong count"),
        (c5, f"{F['any_wrong']:,}", "any-wrong count"),
        (c5, f"{sig['auc']:.3f}", "headline AUC"),
        (c5, f"{sig['auc_weighted']:.3f}", "weighted AUC"),
        (c5, f"{B['single_model'][0]['auc']:.3f}", "best single-model SE AUC"),
        (c5, f"{B['n']:,}", "baseline subset size"),
        (c5, f"{ab['n_wrong']:,}", "wrong in the agreement region"),
        # :.3f, not str(): the exporter rounds to 3dp and JSON drops the
        # trailing zero, so str(0.930) is "0.93" while the prose correctly
        # writes "0.930". Substring matching hid that; found() does not.
        (c5, f"{ab['conf_right']:.3f}", "mean confidence when right"),
        (c5, f"{ab['conf_wrong']:.3f}", "mean confidence when wrong"),
        (c5, f"{rq3['rates'][0]['wrong'] * 100:.2f}%", "2024 ensemble wrong rate"),
        (c5, f"{rq3['rates'][1]['wrong'] * 100:.2f}%", "2025 ensemble wrong rate"),
        (c5, f"{rq3['rates'][0]['share'] * 100:.2f}%", "2024 shared share"),
        (c5, f"{rq3['rates'][1]['share'] * 100:.2f}%", "2025 shared share"),
        (c5, f"{rq3['persisted']}", "persisted count"),
        (c5, f"{rq3['healed']}", "healed count"),
        (c5, f"{rq3['emerged']}", "emerged count"),
        (c5, f"{rq3['gen2_silent']}", "2024 blind-spot count"),
        (c5, f"{rq3['emerged_was_allwrong']}", "emerged that were already wrong"),
        (c5, pc(rq3["persistence"], 1), "persistence rate"),
        (c5, f"{rq4['obscurity']['lift'] * 100:.1f}%", "RQ4 obscurity lift"),
        (c5, f"{rq4['misconception']['lift'] * 100:.1f}%", "RQ4 misconception lift"),
        (c5, f"{rq4['obscurity']['retrieved'] * 100:.1f}%", "RQ4 obscurity retrieved"),
        (c5, f"{rq4['misconception']['closedbook'] * 100:.1f}%", "RQ4 misconception closed-book"),
        (c5, f"{V['matched']}", "RQ5 matched n"),
        (c5, f"{V['wiki']}/{V['matched']}", "RQ5 wikipedia rescued"),
        (c5, f"{V['web']}/{V['matched']}", "RQ5 web rescued"),
        (c5, f"{V['neither']}/{V['matched']}", "RQ5 neither"),
        (c5, pc(V["neither_rate"], 1), "RQ5 ceiling"),
        (c5, f"{S['rq2']['corr_pop']}", "corr popularity/error"),
        (c5, f"+{S['rq2']['corr_density_within']}", "corr density/error within PopQA"),
        (c5, f"{pat['director of X']['rate'] * 100:.2f}%", "director-of-X blind rate"),
        (c5, f"{pat['capital of X']['rate'] * 100:.2f}%", "capital-of-X blind rate"),
        (c5, f"{pat['director of X']['n']:,}", "director-of-X n"),
        (c5, f"{S['grader_check']['judged']}", "target cases judged"),
        (c5, f"{S['grader_check']['generous']}", "generously graded"),
        (c5, f"{S['grader_check']['harsh']}", "harshly graded"),
        (c5, f"{B_['counter']['repaired'] * 100:.2f}%", "counter-evidence repair rate"),
        (c5, f"{B_['counter']['broke'] * 100:.2f}%", "counter-evidence damage rate"),
        (c5, f"{B_['abstain']['broke'] * 100:.2f}%", "abstention damage rate"),
        (c5, pc(B_["abstain"]["abstain_blind"], 1), "abstention rate on blind spots"),
        (c5, pc(B_["abstain"]["abstain_control"], 1), "abstention rate on controls"),
        (c5, f"{A['n_ensembles']}", "ensembles scored"),
    ]
    # ---- chapter 6, the analytical evaluation ----
    c6 = "ch6-evaluation.md"
    out += [
        (c6, f"{sig['n']:,}", "corpus size"),
        (c6, f"{rq3['emerged']}", "emerged count"),
        (c6, f"{rq3['persisted']}", "persisted count"),
        (c6, f"{A['n_ensembles']}", "ensembles, for the renderer argument"),
        (c6, f"{sig['silent']:,}", "blind-spot count"),
    ]
    # ---- the 27 Sep correction pass: the new headline figures ----
    # Each of these LEADS a chapter since the correction, and until they were
    # added here no needle guarded any of them: the chapters led with numbers
    # the checker could not see, while it still checked the demoted pooled ones.
    IV = S["intervals"]
    CO, ST = IV["concordance"], S["independence"]["stratified"]
    pa_s = {r["k"]: r["r"] for r in A["phi_silent_partial"]}
    pa_a = {r["k"]: r["r"] for r in A["phi_auc_partial"]}
    ph_a = {r["k"]: r["r"] for r in A["phi_auc"]}
    irr0 = S["irr"]["annotators"][0]
    # one or two decimals: the abstract says 3.3×, the results chapter 3.32×
    stratified = Rx(rf"(?<![\d.])(?:{CO['ratio']:.1f}|{CO['ratio']:.2f})×")
    ci_conc = f"[{CO['lo']:.2f}, {CO['hi']:.2f}]"
    phi_range = f"{ST['phi_min']:.2f}–{ST['phi_max']:.2f}"
    for ch in ("00-front-matter.md", "ch1-introduction.md", c5,
               "ch7-limitations.md", "ch8-conclusion.md"):
        out.append((ch, stratified, "stratified concordance ratio"))
        out.append((ch, phi_range, "within-dataset phi range"))
    for ch in ("ch1-introduction.md", c5, "ch7-limitations.md"):
        out.append((ch, ci_conc, "stratified concordance CI"))
    for ch in (c5, "ch7-limitations.md"):
        out += [
            (ch, f"{ST['observed']:,}", "stratified observed all-wrong"),
            (ch, f"{ST['expected']:,.0f}", "stratified expected all-wrong"),
            (ch, f"+{pa_s[4]:.3f}", "partial corr(phi, blind) at k=4"),
            (ch, f"+{ph_a[2]:.3f}", "corr(phi, AUC) at k=2, head-count"),
            (ch, f"+{pa_a[2]:.3f}", "partial corr(phi, AUC) at k=2"),
            (ch, f"+{pa_a[4]:.3f}", "partial corr(phi, AUC) at k=4"),
        ]
    AU, VS, SR = IV["auc"], IV["vs_semantic_entropy"], IV["share_ratio"]
    out += [
        ("ch2-related-work.md", f"+{pa_s[4]:.3f}", "partial r answering D. Kim"),
        ("ch1-introduction.md", f"[{AU['lo']:.3f}, {AU['hi']:.3f}]", "headline AUC CI"),
        (c5, f"[{AU['lo']:.3f}, {AU['hi']:.3f}]", "headline AUC CI"),
        # Appendix A (tables moved out of the chapters, 2026-09-27)
        ("ch10-appendix.md", f"**{AU['auc']:.3f}**", "adopted tie rule AUC, appendix"),
        ("ch10-appendix.md", f"{S['corpus']['analysed']:,}", "questions analysed, appendix"),
        ("ch10-appendix.md", f"{S['corpus']['duplicates']:,}", "duplicates removed, appendix"),
        (c5, f"+{VS['delta']:.3f}", "cross-model minus single-model SE"),
        (c5, f"[+{VS['lo']:.3f}, +{VS['hi']:.3f}]", "SE margin CI"),
        (c5, f"{SR['ratio']:.2f}×", "shared-share ratio"),
        (c5, f"[{SR['lo']:.2f}, {SR['hi']:.2f}]", "shared-share ratio CI"),
        (c5, f"{S['rq2']['auc_pop']:.3f}", "popularity-only AUC"),
        (c5, f"{S['rq2']['auc_pop_density_within']:.3f}", "popularity + within density"),
        (c5, f"{S['rq2']['auc_density_within']:.3f}", "density within PopQA, alone"),
        ("ch2-related-work.md", f"{S['rq2']['auc_density_within']:.3f}", "density alone"),
        ("ch2-related-work.md", f"{S['rq2']['auc_pop']:.3f}", "popularity alone"),
        (c5, f"{B_['counter']['broke_strict'] * 100:.2f}%", "counter damage, majority wrong"),
        (c5, f"{B_['abstain']['broke_strict'] * 100:.2f}%", "abstention damage, majority wrong"),
        (c5, f"{S['arms']['judges'][0]['rq3']['p_growth']:.3f}", "genuine growth, exact McNemar"),
        ("ch7-limitations.md", f"{S['arms']['judges'][0]['rq3']['p_growth']:.3f}",
         "genuine growth, exact McNemar"),
    ]
    # the cross-arm artifact gap's test, and the one dataset where it holds
    # alone -- typed from a script printout until 27 Sep (ISSUES #77)
    J0 = S["arms"]["judges"][0]
    for ch in ("ch4-method.md", c5, "ch7-limitations.md"):
        # ch7 carries it as a bare table cell, so the needle is the number
        out.append((ch, f"{J0['p_gap']:.4f}", "artifact gap across arms, two-proportion"))
    out.append(("ch4-method.md", f"p = {J0['by_dataset']['popqa']['p']:.3f}",
                "artifact gap inside PopQA"))
    # the adjudicator's calibration against the human, with aliases (#71)
    A_ = S["artifact"]
    for ch, fmt in (("ch4-method.md", "{k} times out of {n}"),
                    (c5, "{k} times out of {n}"),
                    ("ch7-limitations.md", "{k} of {n}")):
        out.append((ch, fmt.format(k=A_["judge_precision_k"], n=A_["judge_precision_n"]),
                    "judge flags the human agrees with"))
        out.append((ch, f"{A_['judge_misses'] * 100:.1f}%", "grader-sided cases human calls correct"))
    # the reliability stratum's population: 385, not 296 (ISSUES #69)
    for ch in ("ch4-method.md", c5, "ch7-limitations.md"):
        out.append((ch, Rx(rf"\b70\b[^.]{{0,40}}\b{S['irr']['strata']['reliability']}\b"),
                    "reliability stratum drawn from"))
        out.append((ch, f"{irr0['kappa']:.3f}", "inter-rater kappa"))

    # This block and the walk, arms, irr and artifact sections below were each
    # wrapped in `if S.get(...)`, so an export that wrote {} for a block made
    # its checks vanish silently. REQUIRED now fails the run on a missing block
    # before checks() is ever called, so they read the blocks unconditionally.
    out += [
        (c6, f"{S['artifact']['rate'] * 100:.2f}%", "artifact rate"),
        (c6, f"[{S['artifact']['lo'] * 100:.2f}%, {S['artifact']['hi'] * 100:.2f}%]",
         "artifact CI"),
        (c6, f"{S['artifact']['genuine']}", "genuine blind spots"),
    ]

    # ---- 6.2b, the two discovery walkthroughs ----
    # Added 2026-08-26 with the section. Every figure it quotes also appears on
    # walkthroughs.html, which reads them from summary.json at load -- so without
    # these rows the published page and the chapter could drift apart silently,
    # which is exactly how #43/#45/#46/#47/#49 happened. The 72/28 box counts are
    # deliberately NOT here: they describe one brush rectangle rather than a
    # population, and ISSUES #57 records why they stay literal.
    W = S["walk"]
    out.append((c6, f"{W['base'] * 100:.2f}%", "walkthrough corpus base"))
    by_name = {q["name"]: q for q in W["patterns"]}
    for name in ("crew role of X", "director of X", "capital of X"):
        q = by_name[name]
        out += [
            (c6, f"{q['n']:,}", f"{name} n"),
            (c6, f"{q['rate'] * 100:.2f}%", f"{name} blind-spot rate"),
            (c6, f"{q['wrong'] * 100:.1f}%", f"{name} wrong rate"),
            (c6, f"{q['unanimous'] * 100:.1f}%", f"{name} unanimous rate"),
        ]
    # 5.4b carries the same split as 6.2b -- check it in both, because two
    # chapters quoting one measurement is exactly the drift #43-#49 shape.
    for half in ("unique", "shared"):
        d = W["director"][half]
        for c in (c5, c6):
            out += [
                (c, f"{d['n']:,}", f"director title {half} n"),
                (c, f"{d['rate'] * 100:.2f}%", f"director title {half} rate"),
            ]
    em = W["emerged"]
    out += [
        (c6, f"{em['already_allwrong']}", "already all-wrong in 2024"),
        (c6, f"{em['n'] - em['already_allwrong']}", "the remainder, bounded"),
        (c6, f"{rq3['healed']}", "now visible"),
    ]

    # ---- the cross-generation artifact comparison (Finding 12) ----
    # Added 2026-08-26. These figures appear in ch5 5.5 and 5.10, ch7 7.4 and
    # 7.4b, and ch8's claims list, and every one of them was typed by hand into
    # prose while `summary.json` holds the derived original. That is exactly the
    # shape of #43/#45/#46/#47/#49, so it gets checked in every chapter it
    # appears in rather than in one.
    AA = S["arms"]
    for J in AA["judges"]:
        where = ["ch5-results.md", "ch7-limitations.md"]
        tag = J["label"]
        for c in where:
            out += [
                (c, f"{J['arm']['2024']['rate'] * 100:.2f}%",
                 f"{tag} 2024 artifact rate"),
                (c, f"{J['arm']['2025']['rate'] * 100:.2f}%",
                 f"{tag} 2025 artifact rate"),
            ]
        # The RQ3 split, rebuilt on genuine cases. ch7's table is graded
        # against the primary judge only; ch5 carries both judges.
        for c in (where if J["key"] == AA["primary"] else ["ch5-results.md"]):
            out += [
                (c, f"**{J['rq3']['persisted']}**",
                 f"{tag} persisted, genuine"),
                (c, f"{J['rq3']['ratio']:.2f}\u00d7", f"{tag} emerged/persisted"),
            ]
        if J["key"] == AA["primary"]:
            g24 = J["arm"]["2024"]["genuine"]
            g25 = J["arm"]["2025"]["genuine"]
            out += [
                ("ch5-results.md", f"{g24} \u2192 {g25}",
                 "genuine blind spots, both arms"),
                ("ch7-limitations.md", f"{g24} \u2192 {g25}",
                 "genuine blind spots, both arms"),
                ("ch5-results.md",
                 f"| {J['rq3']['healed']} | {J['rq3']['emerged']} |",
                 "healed and emerged, genuine"),
            ]

    # ---- inter-rater reliability ----
    IR = S["irr"]
    a0 = IR["annotators"][0]
    for c in ("ch5-results.md", "ch7-limitations.md", "ch8-conclusion.md"):
        out += [
            (c, f"{a0['kappa']:.3f}", "inter-rater kappa"),
            (c, f"[{a0['lo']:.3f}, {a0['hi']:.3f}]".replace("1.000", "1.000"),
             "inter-rater CI"),
        ]
    out += [
        ("ch5-results.md", f"{a0['agreement'] * 100:.1f}%", "IRR agreement"),
        ("ch5-results.md", f"{a0['labelled']}", "cases labelled"),
        ("ch5-results.md", f"{a0['population']}", "comparable population"),
        ("ch7-limitations.md", f"{a0['agreement'] * 100:.1f}%", "IRR agreement"),
        ("ch7-limitations.md", f"{a0['labelled']}", "cases labelled"),
    ]

    # ---- the artifact correction, everywhere it is quoted ----
    AR = S["artifact"]
    by = {r["dataset"]: r for r in AR["by_dataset"]}
    for c in ("ch5-results.md", "ch7-limitations.md", "ch8-conclusion.md"):
        out += [
            (c, f"{AR['rate'] * 100:.2f}%" if c != "ch8-conclusion.md"
                else f"{AR['rate'] * 100:.1f}%", "artifact rate"),
            (c, f"{AR['genuine']}", "genuine blind spots"),
        ]
    out += [
        ("ch5-results.md", f"[{AR['lo'] * 100:.2f}%, {AR['hi'] * 100:.2f}%]",
         "artifact CI"),
        ("ch5-results.md", f"{by['halueval']['rate'] * 100:.2f}%", "halueval artifact"),
        ("ch5-results.md", f"{by['popqa']['rate'] * 100:.2f}%", "popqa artifact"),
        ("ch5-results.md", f"{by['triviaqa']['rate'] * 100:.2f}%", "triviaqa artifact"),
        ("ch5-results.md", f"{AR['n_judged']}", "adjudicated n"),
        ("ch7-limitations.md", f"{by['halueval']['rate'] * 100:.2f}%", "halueval artifact"),
        ("ch7-limitations.md", f"{by['popqa']['rate'] * 100:.2f}%", "popqa artifact"),
    ]

    # ---- chapters 1, 2 and 8 ----
    c1, c2, c8 = "ch1-introduction.md", "ch2-related-work.md", "ch8-conclusion.md"
    for c in (c1, c2, c8):
        out += [
            (c, f"{I['phi_mean']:.3f}", "phi"),
            (c, f"{I['ratio']:.1f}", "concordance ratio"),
        ]
    out += [
        (c1, f"{sig['auc']:.3f}", "headline AUC"),
        (c1, f"{sig['n']:,}", "corpus size"),
        (c1, f"{sig['silent']:,}", "blind-spot count"),
        (c1, pc(sig["silent"] / sig["n"], 1), "blind-spot rate"),
        (c1, f"{I['all_wrong'] * 100:.1f}%", "all-four-wrong rate"),
        (c1, f"{I['all_wrong_if_independent'] * 100:.1f}%", "independence prediction"),
        (c1, f"{rq4['obscurity']['lift'] * 100:.1f}%", "obscurity lift"),
        (c1, f"{rq4['misconception']['lift'] * 100:.1f}%", "misconception lift"),
        (c1, pc(V["neither_rate"], 1), "RQ5 ceiling"),
        (c1, f"{rq3['emerged']}", "emerged"),
        (c1, f"{rq3['persisted']}", "persisted"),
        (c1, f"{R['conf_auc']:.3f}", "confidence-alone AUC"),
        (c1, f"{R['best_auc']:.3f}", "best AUC"),
        (c1, pc(R["best_risk50"], 2), "risk at half coverage"),
        (c1, pc(R["base"], 2), "agreement base rate"),
        (c1, f"{B_['counter']['repaired'] * 100:.2f}%", "counter repair"),
        (c1, f"{B_['counter']['broke'] * 100:.2f}%", "counter damage"),
        (c1, f"+{phi_s[4]:.3f}", "corr phi/silent k=4"),
        (c1, f"{err_s[4]:.3f}", "corr err/silent k=4"),
        (c1, f"{A['n_ensembles']}", "ensembles"),
        # "{n} defects", not "{n}": the bare number passed for four weeks on
        # ch1's "[59.5%, 75.3%]" and ch4's "kappa 0.959" while both chapters
        # still said 57. ISSUES #60.
        (c1, f"{S['defects']} defects", "defect count"),

        (c2, f"{sig['auc']:.3f}", "headline AUC"),

        (c2, f"{I['all_wrong'] * 100:.1f}%", "all-four-wrong rate"),
        (c2, f"{ds['truthfulqa']['auc']:.3f}", "TruthfulQA AUC"),
        (c2, f"{ds['triviaqa']['auc']:.3f}", "TriviaQA AUC"),
        (c2, f"{A['n_ensembles']}", "ensembles"),
        # Two decimals here, three in the chapter-5 and chapter-7 tables. A
        # summarising sentence may round; what must hold is that the rounding is
        # CORRECT, which is what checking the 2dp form against the live value
        # does. Forcing one precision everywhere would push "+0.917" into a
        # sentence where "+0.92" reads better, and precision is not accuracy.
        (c2, f"+{phi_s[4]:.2f}", "corr phi/silent, rounded"),
        (c2, f"{err_s[4]:.2f}", "corr err/silent, rounded"),
        (c2, f"{R['conf_auc']:.3f}", "confidence AUC"),
        (c2, f"{R['best_auc']:.3f}", "best AUC"),
        (c2, f"{sig['silent']:,}", "blind-spot count"),

        (c8, f"{sig['auc']:.3f}", "headline AUC"),
        (c8, f"{sig['silent']:,}", "blind-spot count"),
        (c8, pc(sig["silent"] / sig["n"], 1), "blind-spot rate"),
        (c8, f"{I['all_wrong'] * 100:.1f}%", "all-four-wrong rate"),
        (c8, f"{rq3['emerged']}", "emerged"),
        (c8, f"{rq3['persisted']}", "persisted"),
        (c8, pc(V["neither_rate"], 1), "RQ5 ceiling"),
        (c8, f"{B_['abstain']['broke'] * 100:.2f}%", "abstention damage"),
        (c8, pc(B_["abstain"]["abstain_blind"], 1), "abstention on blind"),
        (c8, pc(B_["abstain"]["abstain_control"], 1), "abstention on control"),
        (c8, f"{R['conf_auc']:.3f}", "confidence AUC"),
        (c8, f"{R['best_auc']:.3f}", "best AUC"),
        (c8, pc(R["best_risk50"], 2), "risk at half"),
        (c8, f"{by25[4]['silent'] * 100:.2f}%", "k=4 rate"),
        (c8, f"{by25[3]['silent'] * 100:.2f}%", "k=3 rate"),
        (c8, f"{by25[2]['silent'] * 100:.2f}%", "k=2 rate"),
        (c8, f"{A['n_ensembles']}", "ensembles"),
        (c8, f"+{phi_s[4]:.3f}", "corr phi/silent"),
        (c8, f"{err_s[4]:.3f}", "corr err/silent"),
        # ch8 no longer quotes the disputed count -- the second annotator
        # closed that item, and the row now records the closure instead.
    ]

    # ---- chapter 3, the design chapter ----
    c3 = "ch3-design.md"
    dir_cap = pat["director of X"]["rate"] / pat["capital of X"]["rate"]
    out += [
        (c3, f"{sig['auc']:.3f}", "headline AUC"),
        (c3, f"{sig['silent']:,}", "blind-spot count"),
        (c3, pc(sig["silent"] / sig["n"], 1), "blind-spot rate"),
        (c3, f"{ds['truthfulqa']['auc']:.3f}", "TruthfulQA AUC"),
        (c3, f"{ds['truthfulqa']['n']}", "TruthfulQA n"),
        (c3, f"{rq3['emerged']}", "emerged count"),
        (c3, f"{rq3['persisted']}", "persisted count"),
        (c3, f"{rq3['healed']}", "healed count"),
        (c3, f"{rq4['obscurity']['lift'] * 100:.1f}%", "obscurity lift"),
        (c3, f"{rq4['misconception']['lift'] * 100:.1f}%", "misconception lift"),
        (c3, f"{B['single_model'][0]['auc']:.3f}", "best single-model AUC"),
        (c3, f"{S['corpus']['analysed']:,}", "corpus size"),
        # ch3 quotes the RATIO in words, not the two rates. Checking for the
        # digits was checking for a string the chapter never claims -- the same
        # false-alarm class as the "36%" check in ch7. This checks the wording
        # the arithmetic supports: 5.29/1.44 = 3.67, which is "nearly four
        # times" and is not "four times".
        # Word-bounded, and the else-branch now asserts the wording the ratio
        # actually supports: the old fallback needle "four times" is a
        # substring of "nearly four times", so it passed either way.
        (c3, ratio_wording(dir_cap, r"\s+more\s+densely\b"),
         "director-vs-capital ratio, in words"),
        # The same claim, worded per chapter; added with the fix above.
        (c1, ratio_wording(dir_cap, r"\s+denser\b"), "director-vs-capital ratio, in words"),
        (c5, ratio_wording(dir_cap, r"\s+more\s+likely\b"),
         "director-vs-capital ratio, in words"),
    ]

    # ---- chapter 4, the method chapter ----
    c4 = "ch4-method.md"
    out += [
        (c4, f"{S['corpus']['analysed']:,}", "corpus size"),
        (c4, f"{S['corpus']['generations']:,}", "generations"),
        (c4, f"{sig['auc']:.3f}", "head-count AUC"),
        (c4, f"{sig['auc_weighted']:.3f}", "weighted AUC"),
        (c4, f"{I['phi_mean']:.3f}", "phi"),
        (c4, f"{I['all_wrong'] * 100:.1f}%", "all-four-wrong rate"),
        (c4, pc(sig["silent"] / sig["n"], 1), "silent-consensus rate"),
        (c4, f"{S['defects']} defects", "defect count"),
        (c4, f"{S['handlabels']}", "hand-label count"),
        (c4, f"{sig['silent']:,}", "silent-consensus count"),
        (c4, f"{A['n_ensembles']}", "ensembles scored"),
    ]
    for d in ("triviaqa", "halueval", "popqa", "truthfulqa"):
        out.append((c4, f"{ds[d]['n']:,}", f"{d} n in ch4"))

    for d in ("triviaqa", "halueval", "popqa"):
        out.append((c5, f"{ds[d]['n']:,}", f"{d} n"))
        out.append((c5, f"{ds[d]['auc']:.3f}", f"{d} AUC"))
        out.append((c5, pc(ds[d]["base"], 1), f"{d} base error rate"))
        out.append((c5, f"{ds[d]['silent']}", f"{d} blind spots"))

    # ---- two derived figures the near-miss scan surfaced (2026-09-27) ----
    # Both were typed into the prose with no check, and each sits beside a
    # checked figure it resembles (52.1% by 52.8%, 34.4% by 39.4%), so a slip
    # in either would have been invisible. Derived here, not re-typed.
    dissoc = rq4["obscurity"]["lift"] - rq4["misconception"]["lift"]
    for c in (c5, c7):
        out.append((c, f"+{dissoc * 100:.1f}%", "RQ4 dissociation (lift gap)"))
    PJ = next(j for j in S["arms"]["judges"] if j["key"] == S["arms"]["primary"])
    out.append((c5, f"{PJ['rq3']['persisted'] / PJ['arm']['2024']['genuine'] * 100:.1f}% "
                    f"adjudicated ({PJ['rq3']['persisted']}/{PJ['arm']['2024']['genuine']})",
                "persistence, adjudicated"))

    # ---- the front matter: the abstract, acknowledgements, method note ----
    # Added 2026-09-27. The abstract is the most-read page of the thesis and
    # was the one page nothing checked. Every figure in it that has a field in
    # summary.json is here; the ones that do not (the "four developers", the
    # capture date, the checker's own figure count, the four wrong citations)
    # are listed in the report that added this block, not invented a field for.
    c0 = "00-front-matter.md"
    n_models = len(S["corpus"]["models_new"]) + len(S["corpus"]["models_old"])
    out += [
        (c0, f"{S['corpus']['analysed']:,}", "questions analysed"),
        (c0, Rx(rf"(?i)\b{words(n_models)}\s+open-weight\s+models\b"),
         "models, in words"),
        (c0, Rx(rf"(?i)\b{words(len(S['corpus']['models_new']))}\s+newer\s+models\b"),
         "newer models, in words"),
        # The abstract leads with the STRATIFIED concordance ratio and phi range
        # (checked with the other chapters above); the pooled figures live in
        # ch5 and ch7, where there is room to say why pooling inflates them.
        (c0, f"{sig['auc']:.3f}", "headline AUC"),
        (c0, f"{S['intervals']['share_ratio']['ratio']:.2f}×", "shared-share ratio"),
        (c0, f"{sig['silent']:,}", "blind-spot count"),
        (c0, f"{S['artifact']['rate'] * 100:.1f}%", "artifact rate"),
        (c0, f"{S['artifact']['genuine']:,}", "genuine blind spots"),
        (c0, f"{A['n_ensembles']}", "ensembles scored"),
        (c0, f"r = +{phi_s[4]:.2f}", "corr phi/silent at k=4, rounded"),
        (c0, f"r = {err_s[4]:.2f}", "corr err/silent at k=4, rounded"),
        (c0, Rx(rf"(?<![\d.,]){S['irr']['annotators'][0]['labelled']}\s+blinded\s+cases\b"),
         "second annotator's cases"),
        (c0, Rx(rf"(?i)\b{words(S['defects'])}\s+logged\s+defects\b"),
         "defect count, in words"),
    ]
    return out


A = S.get("ablation", {})


def invariants() -> list[tuple[bool, str, str]]:
    """Cross-artifact agreement, checked rather than hoped for.

    The tool draws a coarse 40-point risk-coverage curve; the write-up quotes
    the exact figure. They are two renderings of one number, out of two files,
    and nothing connects them -- which is the shape of every stale-figure defect
    in ISSUES. Interpolating the curve the way the panel does and comparing is
    the whole check. It caught a 0.09-point disagreement the day it was written:
    the panel was reading the next stored sample instead of interpolating, so it
    showed 1.70% where the results chapter says 1.61%.
    """
    out = []
    tool = ROOT / "faultlines-tool" / "data.json"
    if not tool.exists():
        return out
    D = json.loads(tool.read_text(encoding="utf-8"))
    P, R = D.get("panels", {}), S.get("rq1b", {})
    curves = {c["features"]: c for c in P.get("riskcov", [])}
    best = curves.get(R.get("best_features"))
    if best and R.get("best_risk50") is not None:
        x, y = best["x"], best["y"]
        i = 0
        while i < len(x) - 1 and x[i + 1] < 0.5:
            i += 1
        j = min(i + 1, len(x) - 1)
        span = x[j] - x[i]
        t = 0 if span <= 0 else max(0.0, min(1.0, (0.5 - x[i]) / span))
        got = y[i] + t * (y[j] - y[i])
        out.append((abs(got - R["best_risk50"]) < 0.0005,
                    "tool curve at 50% == rq1b.best_risk50",
                    f"{got:.4f} vs {R['best_risk50']:.4f}"))
    if P.get("frontier") and A.get("n_ensembles"):
        out.append((len(P["frontier"]) == A["n_ensembles"],
                    "tool frontier rows == exported ensemble count",
                    f"{len(P['frontier'])} vs {A['n_ensembles']}"))
    return out


def _pattern(literal: str) -> str:
    """The regex found() searches for. See found() for why it is not `in`."""
    if isinstance(literal, Rx):
        return str(literal)
    lead = literal[0].isdigit()
    trail = literal[-1].isdigit()
    pat = re.escape(literal)
    if lead:
        pat = r"(?<![\d])(?<![\d][.,])" + pat
    if trail:
        pat = pat + r"(?![\d])(?![.,][\d])"
    return pat


def occurrences(literal: str, text: str) -> list[re.Match]:
    if not literal:
        return []
    return list(re.finditer(_pattern(literal), text))


def found(literal: str, text: str) -> bool:
    """Is `literal` in `text` as a FIGURE, rather than as a substring?

    Added 2026-08-26 as the root fix for ISSUES #60. The check used to be a
    plain `in`, so the defect count "59" matched inside ch1's "[59.5%, 75.3%]"
    and ch4's "kappa 0.959" and reported ok for four weeks while both chapters
    said 57. Forty-nine other checks used needles of three digits or fewer and
    had the same exposure -- "364" sits inside "1,364" and "364.5" -- so
    hardening the match is the fix, not editing forty-nine needles.

    A numeric literal must not be flanked by anything that would make it part
    of a LARGER number: a digit, or a decimal point or comma with a digit on the
    far side. `690` therefore matches "690 emerged" and "(690)" but not "1,690",
    "0.690" or "6901". Literals that do not begin or end with a digit -- table
    fragments, "9.0x" -- keep plain containment, because their surrounding
    punctuation already makes them distinctive. Wordings are Rx needles and are
    searched as the regex they are.
    """
    return bool(occurrences(literal, text))


# ---------------------------------------------------------------------------
# The near-miss scan: the second, independent guard.
#
# found() proves a right copy exists. It cannot prove there is no wrong one,
# and about 100 needles occur more than once in their chapter. This looks for
# the wrong one directly: a number formatted exactly like a checked figure and
# a slip of the pen away from it -- one digit different, two adjacent digits
# swapped, or within 1% -- anywhere in the same chapter.
#
# WHY IT DOES NOT FILTER ON SURROUNDING WORDS. The first version required a
# lookalike to share two content words with the real copy's paragraph, on the
# theory that a wrong copy talks about the same thing. It missed the very case
# that motivated it: ch1 says "1,054 questions, 2.5% of the corpus" in one
# paragraph and "repairs exactly none of the 1,054" in another, and the two
# share no content word at all. Prose restates a figure precisely in order to
# use it in a new context, so context is not what identifies a copy. What
# does separate a typo from a different quantity here is structural, and
# those are the exclusions:
#
#   * the lookalike is itself a value the records hold (record_keys) -- e.g.
#     0.600 is rq1.agree_auc, not a slip for rq1b's 0.601;
#   * it is an endpoint of a bracketed interval -- CI bounds sit within a
#     percent of their estimate by construction;
#   * it is whitelisted in NEAR_MISS_OK, with the phrase that anchors it and
#     the reason it is a different quantity.
#
# Everything else is a failure. Short figures (under MIN_DIGITS significant
# digits: "2.5%", "31") are not scanned -- every two-digit percentage is one
# digit from dozens of others, and those needles are listed as weak instead.
# Sign is not compared: "+0.917" and "0.917" are one token.
# ---------------------------------------------------------------------------

# A number as prose writes it. Not preceded by a word character, a point or a
# comma (so "ch5", "E3", "0.5" inside "10.5" and the tail of "1,054" are not
# tokens), and not followed by a word character or by ".5"/",054" (so
# "5.4b" section references and the head of a longer number are not either).
NUM = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(%|×)?"
                 r"(?![\w%×])(?![.,]\d)")

REL_TOL = 0.01          # "within 1%" -- a rounding slip, e.g. 26.9% vs 27.1%
MIN_DIGITS = 3          # 2.5% vs 3.5% is a different number, not a typo


class Tok:
    __slots__ = ("text", "start", "end", "int", "frac", "suffix", "comma")

    def __init__(self, m: re.Match):
        self.text, self.start, self.end = m.group(0), m.start(), m.end()
        self.comma = "," in m.group(1)
        self.int = m.group(1).replace(",", "")
        self.frac = m.group(2) or ""
        self.suffix = m.group(3) or ""

    @property
    def digits(self) -> str:
        return self.int + self.frac

    @property
    def shape(self):
        return (len(self.int), self.comma, len(self.frac), self.suffix)

    @property
    def key(self):
        return (self.shape, self.digits)

    @property
    def value(self) -> float:
        return float(f"{self.int}.{self.frac or 0}")


def tokens(text: str) -> list[Tok]:
    return [Tok(m) for m in NUM.finditer(text)]


def _swapped(a: str, b: str) -> bool:
    d = [i for i in range(len(a)) if a[i] != b[i]]
    return len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] \
        and a[d[1]] == b[d[0]]


def lookalike(t: Tok, v: Tok) -> bool:
    """Same format, not equal, and a plausible slip of the pen away."""
    if t.shape != v.shape or t.digits == v.digits:
        return False
    a, b = t.digits, v.digits
    if sum(x != y for x, y in zip(a, b)) == 1 or _swapped(a, b):
        return True
    hi = max(abs(t.value), abs(v.value))
    return hi > 0 and abs(t.value - v.value) / hi <= REL_TOL


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


_RECORD_KEYS: set | None = None


def record_keys() -> set[tuple]:
    """Every numeric leaf of summary.json, in every format the prose uses.

    A number the records actually hold is a real quantity, not a slip of the
    pen for its neighbour: 0.600 is rq1.agree_auc, not a typo of rq1b's 0.601;
    0.602 is corr(phi, AUC) at k=3. Without this the scan flags the thesis's
    own correct figures, and a check that cries wolf gets switched off.
    The residual risk is a typo that lands exactly on some other stored value
    in the same format (0.862 -> 0.826 does: 0.8261 is the k=3 ablation AUC).
    """
    global _RECORD_KEYS
    if _RECORD_KEYS is not None:
        return _RECORD_KEYS
    vals: list[float] = []

    def walk(v):
        if isinstance(v, bool):
            return
        if isinstance(v, (int, float)):
            vals.append(float(v))
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk({k: v for k, v in S.items() if k != "writeup"})
    keys = set()
    for x in vals:
        forms = [f"{abs(x):.{d}f}" for d in range(0, 5)]
        forms += [f"{abs(x) * 100:.{d}f}%" for d in range(0, 4)]
        forms += [f"{abs(x):.{d}f}×" for d in range(0, 3)]
        if x == int(x):
            forms.append(f"{int(abs(x)):,}")
        for f in forms:
            keys |= {t.key for t in tokens(f)}
    _RECORD_KEYS = keys
    return keys


# "[0.858, 0.866]" around 0.862 is a confidence interval: its endpoints sit
# within a percent of the estimate BY CONSTRUCTION, and are not copies of it.
INTERVAL = re.compile(r"\[[^\[\]]{0,60}?,[^\[\]]{0,60}?\]")


# Lookalikes that are genuinely different quantities. Keyed by
# (chapter, the lookalike as written, a phrase within 80 characters of it).
# The anchor phrase pins the entry to one sentence, so a real typo that
# happens to produce the same digits elsewhere in the chapter is NOT silenced;
# keying by the lookalike rather than by the figure it resembles means the
# entry survives a re-export that moves the checked figure. Every entry says
# what the lookalike IS -- an entry without a reason is a wrong number being
# silenced.
NEAR_MISS_OK: dict[tuple[str, str, str], str] = {
    # Each entry covers ONE sentence (chapter, token, anchor within 80 chars)
    # and gives the reason the lookalike is a different quantity. Pruned on
    # 2026-09-27 of every entry the corrected chapters no longer contain.
    # ---- tie-rule AUC ceiling vs the growth p-value (2026-09-30: p is now
    # 0.101, one digit from the 0.901 ceiling of the tie-rule range) ----
    ("ch7-limitations.md", "0.901", "0.849 and"):
        "highest AUC among the six alternative tie rules; not a p-value",
    ("ch7-limitations.md", "0.901", "rules span"):
        "highest AUC among the six alternative tie rules; not a p-value",
    ("ch7-limitations.md", "0.901", "tie rules give"):
        "highest AUC among the six alternative tie rules; not a p-value",
    # ---- chapter 2 ----
    ("ch2-related-work.md", "0.603", "range 0.161"):
        "upper end of a cited paper's phi range; not the confidence AUC",
    ("ch2-related-work.md", "0.161", "range 0.161"):
        "lower end of a cited paper's phi range (Kohli 2026); not an AUC",
    # ---- chapter 4 ----
    ("ch4-method.md", "300", "questions"):
        "the 300-question pilot; not TruthfulQA's n",
    # ---- chapter 5 ----
    ("ch5-results.md", "507", "PopQA adds"):
        "PopQA duplicate rows removed (ISSUES #66); not the healed count",
    ("ch5-results.md", "0.635", "all four (mean"):
        "RQ1b table cell, confidence features only; not an AUC elsewhere",
    ("ch5-results.md", "3.69%", "question length"):
        "RQ1b table cell, risk at 50% coverage with length features",
    ("ch5-results.md", "0.750", "map position"):
        "RQ1b table cell, + map position",
    ("ch5-results.md", "3.09%", "map position"):
        "RQ1b table cell, risk at 50% coverage with map position",
    ("ch5-results.md", "0.747", "out-of-fold"):
        "RQ1b table cell, + out-of-fold density",
    ("ch5-results.md", "0.811", "published figure"):
        "the withdrawn RQ1b AUC, quoted as history (ISSUES #73)",
    ("ch5-results.md", "0.322", "low-margin"):
        "grader-vs-human kappa on the low-margin stratum; not a partial r",
    ("ch5-results.md", "1.64", "words"):
        "mean answer length in words, 2024 arm",
    ("ch5-results.md", "1.89", "words"):
        "mean answer length in words, 2025 arm",
    ("ch5-results.md", "428", "automatic grader"):
        "n of the adjudicator-vs-grader row (with-alias run, #71)",
    ("ch5-results.md", "0.959", "control"):
        "grader-vs-human kappa on the control stratum; not the inter-rater kappa",
    ("ch5-results.md", "99.5%", "outside TruthfulQA"):
        "share of blind spots outside TruthfulQA; not IRR agreement",
    # ---- chapter 7 ----
    ("ch7-limitations.md", "0.644", "item-level agreement"):
        "weighted Jaccard of the precision control (#75); not a partial r",
    ("ch7-limitations.md", "341", "human vs"):
        "n of the two human kappa rows (with-alias run, #71); not TruthfulQA's n",
    ("ch7-limitations.md", "0.781", "Leander Club"):
        "encoder similarity of two club names; not a kappa",
    ("ch7-limitations.md", "0.811", "quoted"):
        "the withdrawn RQ1b AUC, quoted as history (ISSUES #73)",
    # ---- appendix ----
    ("ch10-appendix.md", "0.849", "file order"):
        "AUC under the old tie rule (Llama first); not the adopted 0.840",
    ("ch10-appendix.md", "0.849", "Llama's answer"):
        "AUC with four-way splits labelled by Llama; not the adopted 0.840",
    ("ch7-limitations.md", "0.959", "control stratum"):
        "grader-vs-human kappa on the control stratum (ISSUES #60)",
    ("ch7-limitations.md", "0.759", "first version read"):
        "a superseded density figure quoted as history; not a kappa",
    ("ch7-limitations.md", "0.198", "denominator"):
        "kappa's denominator, 1 - chance agreement; not a correlation",
    ("ch7-limitations.md", "428", "automatic grader"):
        "n of the adjudicator-vs-grader kappa row; not the hand-label count",
    ("ch7-limitations.md", "99.6%", "identical outputs"):
        "share of identical outputs among duplicates; not IRR agreement",
    ("ch7-limitations.md", "99.5%", "somewhere else"):
        "share of misconceptions outside TruthfulQA; not IRR agreement",
}


def _whitelisted(c: str, t: Tok, text: str, used: set) -> bool:
    # Whitespace-folded on both sides: prose is hard-wrapped, so an anchor
    # phrase is often split across a line break.
    window = " ".join(text[max(0, t.start - 80):t.end + 80].split())
    for (wc, wt, anchor) in NEAR_MISS_OK:
        if wc == c and wt == t.text and " ".join(anchor.split()) in window:
            used.add((wc, wt, anchor))
            return True
    return False


def near_misses(checked: list[tuple[str, str, str]], texts: dict[str, str]):
    """Returns (failures, unused whitelist entries).

    A failure is (chapter, line, lookalike, figure, figure's label, context).
    """
    known = set(record_keys())
    per_chapter: dict[str, dict[tuple, tuple[Tok, list[str]]]] = {}
    # Figures that are themselves interval endpoints ("[0.904, 1.000]"): a
    # lookalike of one of THESE inside brackets is exactly the slip to catch,
    # so the interval exemption does not apply to them.
    endpoint_keys = set()
    for c, lit, what in checked:
        if isinstance(lit, Rx):
            continue
        for t in tokens(norm(lit)):
            known.add(t.key)       # a checked value anywhere is accounted for
            if "[" in lit:
                endpoint_keys.add(t.key)
            if len(t.digits.lstrip("0")) >= MIN_DIGITS or len(t.digits) >= 4:
                per_chapter.setdefault(c, {}).setdefault(t.key, (t, []))[1].append(what)

    out, used, reported = [], set(), set()
    for c, needles in per_chapter.items():
        text = texts.get(c)
        if text is None:
            continue
        spans = [(m.start(), m.end()) for m in INTERVAL.finditer(text)]
        for t in tokens(text):
            if t.key in known:
                continue
            bracketed = any(a <= t.start and t.end <= b for a, b in spans)
            for v, whats in needles.values():
                if not lookalike(t, v):
                    continue
                if bracketed and v.key not in endpoint_keys:
                    continue
                if _whitelisted(c, t, text, used):
                    break
                if (c, t.start) in reported:
                    continue
                reported.add((c, t.start))
                ctx = text[max(0, t.start - 60):t.end + 60].replace("\n", " ")
                out.append((c, line_of(text, t.start), t.text, v.text, whats[0], ctx))
    unused = [k for k in NEAR_MISS_OK if k not in used]
    return out, unused


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--occurrences", action="store_true",
                    help="print every occurrence of every needle, with context, "
                         "so a human can audit the copies the check does not "
                         "distinguish between")
    a = ap.parse_args()

    bad = 0
    gone = missing_blocks()
    if gone:
        print("  summary.json is incomplete -- these blocks feed checks that "
              "would otherwise vanish:")
        for g in gone:
            print(f"  BAD  {g}")
        print(f"\n{len(gone)} MISSING BLOCK(S). Re-run export_web.py; nothing "
              f"else was checked.")
        return 1

    checked = checks()
    texts: dict[str, str] = {}
    missing_ch: set[str] = set()
    for chapter in dict.fromkeys(c for c, _l, _w in checked):
        f = WRITEUP / chapter
        if f.exists():
            texts[chapter] = norm(f.read_text(encoding="utf-8"))
        else:
            missing_ch.add(chapter)
            bad += 1
            print(f"  BAD  {chapter} does not exist -- its checks cannot run")

    for chapter, literal, what in checked:
        if chapter in missing_ch:
            continue
        text = texts[chapter]
        lit = literal if isinstance(literal, Rx) else norm(literal)
        hits = occurrences(lit, text)
        ok = bool(hits)
        bad += not ok
        shown = f"/{literal}/" if isinstance(literal, Rx) else repr(literal)
        print(f"  {'ok ' if ok else 'BAD'}  {what:<42} {shown}  [{chapter[:3]}]")
        if a.occurrences:
            for m in hits:
                s = max(0, m.start() - 50)
                ctx = text[s:m.end() + 50].replace("\n", " ")
                print(f"         L{line_of(text, m.start()):<5} …{ctx}…")

    # A needle of one to three characters can appear anywhere -- inside a
    # confidence interval, a kappa, a year, another figure's decimals -- and a
    # check that matches by accident reports "ok" forever while the prose is
    # wrong. That happened (ISSUES #60): the defect count passed on ch1's
    # "[59.5%, 75.3%]" and ch4's "kappa 0.959" while both chapters said 57.
    # found() closes the substring collision. What it cannot close is a
    # needle so short that it legitimately appears elsewhere as its own figure
    # -- a bare "5" or "12". Those are still worth naming.
    weak = [(c, v, w) for c, v, w in checked
            if not isinstance(v, Rx) and len(str(v).strip()) < 3]
    if weak:
        print(f"\n  {len(weak)} check(s) use a needle under 3 characters. "
              f"found() stops them matching INSIDE a larger number, but a bare "
              f"short figure can still occur elsewhere on its own:")
        for c, v, w in weak:
            print(f"    {w:<40} {v!r:>10}  in {c}")

    multi = sum(1 for c, lit, _w in checked if c in texts
                and len(occurrences(lit if isinstance(lit, Rx) else norm(lit),
                                    texts[c])) > 1)
    nm, unused = near_misses(checked, texts)
    print(f"\n  near-miss scan  ({multi} of {len(checked)} needles occur more "
          f"than once in their chapter; presence alone cannot vouch for the "
          f"other copies)")
    for c, ln, got, want, what, ctx in nm:
        bad += 1
        print(f"  BAD  {c}:{ln}  {got!r} looks like {want!r} ({what})")
        print(f"         …{ctx}…")
    if nm:
        print("       Fix the prose if it is a slip; if it is a different "
              "quantity, add it to NEAR_MISS_OK with an anchor and a reason.")
    else:
        print(f"  ok   no lookalike of a checked figure "
              f"({len(NEAR_MISS_OK) - len(unused)} whitelisted as distinct "
              f"quantities)")
    # Not a failure: a re-export can move a checked figure so that a
    # whitelisted number no longer resembles it, and prose edits delete
    # sentences. A stale entry silences nothing, but it should be pruned.
    for k in unused:
        print(f"  note whitelist entry matched nothing, prune it: {k}")

    inv = invariants()
    if inv:
        print("\n  cross-artifact invariants")
        for ok, what, detail in inv:
            bad += not ok
            print(f"  {'ok ' if ok else 'BAD'}  {what:<42} {detail}")

    print(f"\n  {len(checked)} figures checked in {len(texts)} files")
    print(f"{'all figures match the records' if not bad else f'{bad} FAILURES'}")
    if bad:
        print("Either the write-up is stale or the data moved. Do not commit "
              "until you know which.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
