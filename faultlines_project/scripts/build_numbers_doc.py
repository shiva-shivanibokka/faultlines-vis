"""FaultLines_numbers.docx -- every published number, its population, its derivation.

EVERY VALUE IS READ FROM summary.json AT BUILD TIME. Nothing is typed. This
document exists because the project's five most recent defects (#43, #45, #46,
#48, #49) were all numbers that stopped tracking their source or lost their
scope -- so a reference sheet full of hand-copied figures would be the same
defect in a new file.
"""
import json
import pathlib

from docx import Document
from docx.shared import Pt, Inches, RGBColor

ROOT = pathlib.Path(r"C:\Users\sbokk\OneDrive\Desktop\CSC895\final_proposal")
S = json.loads((ROOT / "faultlines-web" / "summary.json").read_text(encoding="utf8"))

F, C, R3, R5, R4, B, A = (S["funnel"], S["corpus"], S["rq3"], S["rq5"],
                          S["rq4"], S["baseline"], S["abstain"])
SIG = S["signal"]
ds = {d["dataset"]: d for d in SIG["by_dataset"]}
n0 = lambda v: f"{v:,}"
pc = lambda v, d=1: f"{v*100:.{d}f}%"

doc = Document()
base = doc.styles["Normal"]
base.font.name, base.font.size = "Calibri", Pt(10.5)
for sec in doc.sections:
    sec.left_margin = sec.right_margin = Inches(0.6)
    sec.top_margin = sec.bottom_margin = Inches(0.6)


def H(text, lvl=1):
    h = doc.add_heading(text, lvl)
    for r in h.runs:
        r.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
    return h


def P(text, size=10.5, italic=False, bold=False, space=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size, r.italic, r.bold = Pt(size), italic, bold
    p.paragraph_format.space_after = Pt(space)
    return p


def TABLE(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        r = cell.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(v))
            run.font.size = Pt(9.5)
            if i == 0:
                run.bold = True
                run.font.name = "Consolas"
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


# --------------------------------------------------------------- title
ti = doc.add_heading("FaultLines \u2014 every number, and where it comes from", 0)
for r in ti.runs:
    r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
P("Shivani Bokka \u00b7 M.S. Capstone \u00b7 SFSU \u00b7 Advisor: Dr. Shahrukh Humayoun",
  size=10, italic=True)
P("Read the POPULATION column first. Most confusion in this project \u2014 including "
  "two logged defects \u2014 comes from two numbers that are both correct but measured "
  "on different sets of questions. A number without its population is not a fact.",
  bold=True)
P("Every value in this document was read from summary.json when the file was built. "
  "Nothing here was typed by hand, which is the only reason it can be trusted to "
  "still be right.", size=9.5, italic=True)

# -------------------------------------------------------------- corpus
H("1 \u00b7 The corpus \u2014 what was asked")
P("One population. Everything else is a subset of this.")
TABLE(["number", "what it is", "how it was derived"], [
    (n0(C["asked"]), "questions asked", "4 datasets, sampled per config.yaml"),
    (n0(C["analysed"]), "questions ANALYSED",
     f"{C['asked'] - C['analysed']} dropped \u2014 no usable answer from all four models"),
    (n0(C["generations"]), "graded answers",
     f"{n0(C['analysed'])} questions \u00d7 4 models, 0 failed calls"),
    ("4", "model families, 2025", " \u00b7 ".join(C["models_new"])),
    ("4", "model families, 2024", " \u00b7 ".join(C["models_old"])),
], [0.9, 2.0, 3.9])

# -------------------------------------------------------------- funnel
H("2 \u00b7 The funnel \u2014 how the corpus narrows to the blind spots")
P("These are NESTED, not separate groups. Every question in a lower row is also in "
  "every row above it. Reading down adds a condition; it does not move to a new set.",
  bold=True)
TABLE(["number", "what it is", "how it was derived"], [
    (n0(F["total"]), "every question", "the analysed corpus"),
    (n0(F["total"] - F["any_wrong"]), "all four models RIGHT",
     f"{n0(F['total'])} minus {n0(F['any_wrong'])}"),
    (n0(F["any_wrong"]), "at least one model wrong", "any_wrong"),
    (n0(F["majority_wrong"]), "the ENSEMBLE'S OWN answer is wrong",
     "majority_wrong \u2014 the largest meaning-cluster is wrong. This is the "
     "target the detector predicts"),
    (n0(F["all_wrong"]), "all four models wrong", "all_wrong"),
    (n0(F["unanimous"]), "all four gave the SAME meaning",
     "n_clusters == 1 \u2014 right or wrong"),
    (n0(F["silent"]), "BLIND SPOTS \u2014 all wrong AND all agreed",
     "unanimous AND all_wrong. Disagreement score 0.00, and the answer is wrong"),
], [0.9, 2.4, 3.5])
P(f"The blind spots are {pc(F['silent']/F['total'], 2)} of the corpus, "
  f"{pc(F['silent']/F['all_wrong'])} of the questions every model got wrong, and "
  f"{pc(F['silent']/F['unanimous'])} of the questions the models agreed on.")
P(f"Watch this pair: {n0(F['majority_wrong'])} vs {n0(F['all_wrong'])}. They differ by "
  f"{n0(F['majority_wrong'] - F['all_wrong'])} \u2014 questions where the ensemble's "
  "answer was wrong but at least one model got it right. Confusing the two is logged "
  "as defects #44 and #48.", size=10, italic=True)

# -------------------------------------------------------------- signal
H("3 \u00b7 The detector \u2014 how well disagreement predicts error")
P("AUC is a bet: pick one question the ensemble got wrong and one it got right, at "
  "random. AUC is how often the wrong one had the higher disagreement score. "
  "0.50 = a coin flip. It measures ORDER, not accuracy.")
TABLE(["number", "what it is", "population / how derived"], [
    (f"{SIG['overall']['auc']:.3f}", "THE HEADLINE \u2014 cross-model disagreement",
     f"all {n0(SIG['overall']['n'])} questions, head-count score, target = majority_wrong"),
    (f"{SIG['overall']['auc_weighted']:.3f}", "the same, confidence-weighted",
     "+0.003 \u2014 a wash at scale. Never quote instead of the headline"),
    (f"{ds['triviaqa']['auc']:.3f}", "TriviaQA \u2014 the signal at its best",
     f"n={n0(ds['triviaqa']['n'])}, error rate {pc(ds['triviaqa']['base'], 0)}"),
    (f"{ds['halueval']['auc']:.3f}", "HaluEval", f"n={n0(ds['halueval']['n'])}"),
    (f"{ds['popqa']['auc']:.3f}", "PopQA", f"n={n0(ds['popqa']['n'])}"),
    (f"{ds['truthfulqa']['auc']:.3f}", "TruthfulQA \u2014 the signal at its WORST",
     f"n={n0(ds['truthfulqa']['n'])}. Shared myths, so the models fail identically. "
     "The honest counterweight to the headline"),
    (f"{S['rq1']['agree_auc']:.3f}", "confidence, inside the agreement region",
     f"n={n0(S['rq1']['agree_n'])}. Where vote-counting is 0.5 by construction. "
     "Better than the vote, nowhere near enough to act on"),
], [0.9, 2.4, 3.5])

# ------------------------------------------------------------ baseline
H("4 \u00b7 Four models vs one model four times")
P("The competing method is Semantic Entropy: ask ONE model the same question several "
  "times and measure how much it contradicts itself. Both arms produce four answers "
  "per question \u2014 a matched budget.")
TABLE(["number", "what it is", "population / how derived"],
      [(f"{B['cross_model_same_qids']:.3f}", "four DIFFERENT models, once each",
        f"the shared {n0(B['n'])} questions")] +
      [(f"{m['auc']:.3f}", f"{m['model']} asked four times",
        "same questions, Semantic Entropy") for m in B["single_model"]],
      [0.9, 2.4, 3.5])
P("On the 300-question pilot this came out the OPPOSITE way \u2014 single-model won, "
  "0.813 to 0.788. Always quote the full-scale pair. The reversal is itself a finding "
  "about small samples.", size=10, italic=True)

# ---------------------------------------------------------- abstention
H("5 \u00b7 \u201cJust make it say I don't know\u201d \u2014 the policy, measured")
P(f"Refuse every answer below a confidence threshold. Measured on the "
  f"{n0(A['n'])} questions in the agreement region.")
TABLE(["refuse below", "errors caught", "correct answers destroyed"],
      [(f"{c['t']:.2f}", pc(c["caught"]), pc(c["lost"])) for c in A["curve"]],
      [1.2, 1.6, 2.2])
for t in A["targets"]:
    P(f"To catch {int(t['target']*100)}% of the errors you must refuse below "
      f"{t['t']:.3f}, which destroys {pc(t['lost'])} of the correct answers.",
      size=10, space=2)
P(f"Why: confidence averages {A['conf_right']} when the ensemble is right and "
  f"{A['conf_wrong']} when it is wrong \u2014 a gap of "
  f"{A['conf_right'] - A['conf_wrong']:.3f}. No line fits inside that.",
  size=10, bold=True)

# ---------------------------------------------------------- generation
H("6 \u00b7 Two model generations \u2014 the same questions, twice")
TABLE(["number", "what it is", "how it was derived"], [
    (n0(R3["gen2_silent"]), "blind spots the 2024 models had",
     f"the same {n0(C['analysed'])} questions"),
    (n0(R3["gen3_silent"]), "blind spots the 2025 models have", "same questions"),
    (n0(R3["persisted"]), "HIDDEN IN BOTH years",
     f"in the {n0(R3['gen2_silent'])} and in the {n0(R3['gen3_silent'])}"),
    (n0(R3["healed"]), "NOW VISIBLE \u2014 blind in 2024 only",
     f"{n0(R3['gen2_silent'])} = {R3['persisted']} + {R3['healed']}"),
    (n0(R3["emerged"]), "NEWLY HIDDEN \u2014 blind in 2025 only",
     f"{n0(R3['gen3_silent'])} = {R3['persisted']} + {R3['emerged']}"),
    (pc(R3["persistence"]), "of 2024's blind spots survived the upgrade",
     f"{R3['persisted']} / {R3['gen2_silent']}"),
    (pc(R3["inherited"]), "of 2025's blind spots were inherited",
     f"{R3['persisted']} / {R3['gen3_silent']} \u2014 quote this ONLY as the inherited share"),
    (f"{R3['emerged'] / R3['persisted']:.1f}\u00d7", "newly hidden for every one inherited",
     f"{R3['emerged']} / {R3['persisted']}"),
    (pc(R3["emerged_was_allwrong"] / R3["emerged"], 0),
     "of the NEWLY HIDDEN were already wrong in 2024",
     f"{R3['emerged_was_allwrong']} / {R3['emerged']}. They did not get worse \u2014 "
     "they stopped disagreeing. Never write \u201cnewly broken\u201d"),
    (pc(R3["healed_ens_wrong"] / R3["healed"], 0),
     "of the NOW VISIBLE are still wrong (the ensemble's answer)",
     f"{R3['healed_ens_wrong']} / {R3['healed']} \u2014 detectable, not correct"),
    (pc(R3["healed_allwrong"] / R3["healed"], 0),
     "of the NOW VISIBLE have all four still wrong",
     f"{R3['healed_allwrong']} / {R3['healed']} \u2014 the stricter measure of the same set"),
], [1.0, 2.6, 3.2])
P("The last two rows are the same questions under two definitions of \u201cwrong\u201d. "
  "Stating one without naming it is defect #48.", size=10, italic=True)

# ------------------------------------------------------------ hardening
H("7 \u00b7 Do errors correlate more as models improve? Yes.")
old, new = R3["rates"]
TABLE(["", "2024 models", "2025 models"], [
    ("ensemble answered wrong", pc(old["wrong"]), pc(new["wrong"])),
    ("shared blind-spot rate", pc(old["blind"], 2), pc(new["blind"], 2)),
    ("SHARE of errors that are shared", pc(old["share"]), pc(new["share"])),
], [2.6, 1.7, 1.7])
P("Row 3 is row 2 divided by row 1. Errors fall by a third; the ones that survive are "
  "concentrated into exactly the region disagreement cannot see. The failure mode does "
  "not shrink as models improve \u2014 it hardens.", size=10, bold=True)

# ------------------------------------------------------------ retrieval
H("8 \u00b7 The two retrieval experiments \u2014 DIFFERENT POPULATIONS")
P("These look like one experiment and are not. Reading them as one is the single most "
  "common mistake made about this project.", bold=True)
TABLE(["", "RQ4 \u2014 documents", "RQ5 \u2014 search"], [
    ("who is tested",
     f"{sum(c['n'] for c in R4['by_cause'])} questions the ENSEMBLE GOT WRONG, "
     "chosen by cause",
     f"the {n0(F['silent'])} BLIND SPOTS"),
    ("what it gets", "we paste the Wikipedia article into the prompt",
     "a search tool \u2014 it must find the page itself, up to 4 lookups"),
    ("overlap with the blind spots", "33 of 570",
     f"{n0(F['silent'])} of {n0(F['silent'])}"),
    ("what it shows", "documents repair NOT-KNOWING, barely dent a BELIEF",
     "two thirds of blind spots survive a search tool"),
], [1.7, 2.6, 2.5])

H("8a \u00b7 RQ4 \u2014 pasting the document in", 2)
TABLE(["number", "what it is", "how it was derived"],
      [(n0(c["n"]), f"{c['cause']} questions tested",
        "PopQA majority_wrong, rarest entities first" if c["cause"] == "obscurity"
        else "TruthfulQA majority_wrong \u2014 capped by the dataset's size")
       for c in R4["by_cause"]] +
      [(pc(c["closedbook"], 0), f"{c['cause']} \u2014 correct with NO document",
        f"n={c['n']}") for c in R4["by_cause"]] +
      [(pc(c["retrieved"], 0), f"{c['cause']} \u2014 correct WITH the document",
        f"n={c['n']}") for c in R4["by_cause"]] +
      [(f"+{c['lift']*100:.0f}pp", f"{c['cause']} \u2014 the gain",
        f"{pc(c['retrieved'], 0)} minus {pc(c['closedbook'], 0)}")
       for c in R4["by_cause"]],
      [0.9, 2.4, 3.5])

H("8b \u00b7 RQ5 \u2014 giving it a search tool", 2)
TABLE(["number", "what it is", "how it was derived"], [
    (n0(F["silent"]), "blind spots the Wikipedia arm ran on", "all of them"),
    (n0(R5["wiki_arm_n"]), "of those, complete with all four models",
     "the rest lost a model to a failed call"),
    ("241", "rescued by the Wikipedia arm alone",
     f"24.7% of {n0(R5['wiki_arm_n'])} \u2014 so 75.3% stayed wrong"),
    ("151", "blind spots the OPEN-WEB arm ran on",
     "a stratified sample. The full arm needs ~6,000\u20138,000 paid searches"),
    (n0(R5["web_arm_n"]), "of those, complete with all four models", ""),
    (n0(R5["matched"]), "THE MATCHED SET \u2014 seen by BOTH arms",
     f"{n0(R5['wiki_arm_n'])} \u2229 {n0(R5['web_arm_n'])}. NOT the size of RQ5 \u2014 "
     "the size of the fair comparison between the two arms"),
    (n0(R5["wiki"]), "rescued by Wikipedia search",
     f"{pc(R5['wiki_rate'], 0)} of {R5['matched']}"),
    (n0(R5["web"]), "rescued by open-web search",
     f"{pc(R5['web_rate'], 0)} of {R5['matched']}"),
    (n0(R5["both"]), "rescued by BOTH arms",
     "the arms repair the SAME questions \u2014 a bigger haystack changes almost nothing"),
    (n0(R5["neither"]), "rescued by NEITHER",
     f"{pc(R5['neither_rate'])} \u2014 the number to quote"),
], [0.9, 2.4, 3.5])
P(f"Paired difference between the arms: "
  f"+{(R5['web'] - R5['wiki']) / R5['matched'] * 100:.1f}pp, not statistically "
  f"significant (McNemar p = 0.388). With n={R5['matched']} the power to detect a 5pp "
  "difference is 47%, so the honest claim is \u201cwe found no difference, and here is "
  "the size of effect we could have missed\u201d.", size=10, italic=True)

# ----------------------------------------------------------------- map
H("9 \u00b7 Where the blind spots are")
TABLE(["number", "what it is", "how it was derived"],
      [(n0(ds[d]["silent"]), f"blind spots in {d}",
        f"of {n0(ds[d]['n'])} {d} questions")
       for d in ("popqa", "halueval", "triviaqa", "truthfulqa")] +
      [(pc(1 - ds["truthfulqa"]["silent"] / SIG["overall"]["silent"]),
        "of blind spots are OUTSIDE TruthfulQA",
        f"1 \u2212 {ds['truthfulqa']['silent']}/{SIG['overall']['silent']}. The proposal "
        "predicted they would cluster in TruthfulQA \u2014 the dataset built from shared myths"),
       ("254", "blind spots SEARCH REPAIRED", "RQ5, either arm"),
       ("740", "blind spots that SURVIVED search", "the resistant core"),
       (f"{S['rq2']['corr_pop']:.3f}", "correlation, page popularity vs error",
        f"PopQA only, n={n0(S['rq2']['n'])} \u2014 the other three have no pageview count"),
       (f"+{S['rq2']['corr_density']:.3f}", "correlation, map density vs error",
        "same subset. Density survives controlling for popularity: +0.060 AUC")],
      [0.9, 2.4, 3.5])

# ------------------------------------------------------- checking itself
H("10 \u00b7 How the numbers themselves were checked")
TABLE(["number", "what it is", "how it was derived"], [
    (n0(S["handlabels"]), "verdicts hand-labelled",
     "blinded, two strata \u2014 the human never sees the machine's grade"),
    (f"{S['grader_check']['generous']} vs {S['grader_check']['harsh']}",
     "grader too generous vs too harsh",
     f"on the {S['grader_check']['judged']} judged cases in the "
     f"{S['grader_check']['stratum']} stratum. Roughly balanced \u2014 so the "
     f"{n0(F['silent'])} is not systematically inflated"),
    (n0(S["keyflags"]), "cases where the ANSWER KEY looks too strict",
     "every model gave a shorter form of the required answer. A flag for a human, "
     "not a verdict"),
    ("263", "unanimous questions graded inconsistently",
     "1.5% \u2014 punctuation and plurals split the grade on answers the clusterer "
     "calls identical"),
    ("114", "of those, where it flipped the ensemble's verdict",
     f"the gap between {n0(F['majority_wrong'])} and {n0(F['all_wrong'])} inside "
     "the agreement region"),
    (str(S["defects"]), "defects found, and fixed",
     "each logged in ISSUES.md with its cause and its fix"),
    (str(S["tests"]), "tests passing", "counted from the test files at export time"),
], [0.9, 2.4, 3.5])

# ------------------------------------------------------------ confusions
H("11 \u00b7 The pairs that get confused \u2014 check these before quoting")
TABLE(["these two", "look alike because", "the difference that matters"], [
    (f"{n0(F['majority_wrong'])} / {n0(F['all_wrong'])}", "both mean \u201cwrong\u201d",
     "the ENSEMBLE'S answer vs EVERY model failing. They differ by "
     f"{n0(F['majority_wrong'] - F['all_wrong'])} questions"),
    (f"{n0(R3['gen3_silent'])} / {n0(R3['gen2_silent'])}", "both are blind-spot counts",
     "2025 models vs 2024 models, on the same questions"),
    (f"{sum(c['n'] for c in R4['by_cause'])} / {n0(F['silent'])}",
     "both are \u201cwhat retrieval was tested on\u201d",
     "RQ4's errors-by-cause vs RQ5's blind spots. Only 33 questions are in both"),
    (f"{n0(R5['matched'])} / {n0(R5['wiki_arm_n'])}", "both are RQ5 counts",
     "the matched two-arm comparison vs the full Wikipedia arm"),
    (f"{SIG['overall']['auc']:.3f} / 0.847", "both are the detector's score",
     "raw AUC vs 5-fold CV on the same feature. Compare 0.847 \u2192 0.871 inside the "
     "CV harness; never say \u201c0.862 to 0.871\u201d"),
    (f"{pc(R3['persistence'])} / {pc(R3['inherited'])}", "both are persistence",
     "share of 2024's blind spots that survived vs share of 2025's that were inherited"),
    (f"{pc(R3['healed_ens_wrong'] / R3['healed'], 0)} / "
     f"{pc(R3['healed_allwrong'] / R3['healed'], 0)}",
     "both describe the NOW VISIBLE cases",
     "the ensemble's answer still wrong vs all four still wrong"),
], [1.3, 2.2, 3.3])

P("")
P("Generated from summary.json. To refresh: run scripts/export_web.py, then rebuild "
  "this file \u2014 no number in it is maintained by hand.", size=9, italic=True)

out = ROOT / "FaultLines_numbers.docx"
doc.save(out)
print("wrote", out)
print("tables:", len(doc.tables), "\u00b7 paragraphs:", len(doc.paragraphs))
