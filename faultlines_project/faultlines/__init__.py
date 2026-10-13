"""FaultLines — mapping where language models disagree, and what that predicts.

Module names map one-to-one onto the levels in the walkthrough at
https://faultlines-peach.vercel.app so the code and the explanation never drift:

    datasets.py   Level 1  sample the three datasets
    generate.py   Level 2  ask the four models
    grade.py      Level 3  mark right/wrong
    disagree.py   Level 4  one disagreement score per question
    embed.py      Level 5  place questions on the map
    baseline.py   Level 6  semantic entropy, matched budget
    evaluate.py   Level 6  error correlation + ROC-AUC
    semantics.py           the one shared sentence transformer
"""
__version__ = "0.1.0"
