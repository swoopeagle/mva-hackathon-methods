"""Score surviving candidates against the pre-registered rubric (track2/RUBRIC.md).

The rubric was committed before any candidate results existed and is applied
here verbatim: seven criteria, 0-2 each, weights 3/2/2/2/2/1/1, max 26,
candidates below 13 go to the deprioritized table.
"""
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))

# From track2/RUBRIC.md -- do not edit without a rubric-change commit.
WEIGHTS = {1: 3, 2: 2, 3: 2, 4: 2, 5: 2, 6: 1, 7: 1}
CRITERIA = {
    1: "Mechanistic directionality",
    2: "Human genetic / model support",
    3: "Approval status",
    4: "Pediatric dosing precedent",
    5: "Chronic-use safety in this patient context",
    6: "Measurable PD biomarker available",
    7: "Falsifiability (a defined kill experiment)",
}
MAX_SCORE = sum(WEIGHTS.values()) * 2   # 26
CUTOFF = 13

with open(os.path.join(HERE, "drug_facts.yaml")) as _f:
    FACTS = yaml.safe_load(_f)


def score_one(cand):
    facts = FACTS.get(cand["name"].lower())
    if not facts:
        return dict(cand, scored=False, total=0, breakdown=[],
                    status="no_curated_facts",
                    note=("Surfaced by the API walk but not curated in "
                          "drug_facts.yaml; not scored rather than guessed."))
    breakdown = []
    total = 0
    for k in sorted(WEIGHTS):
        raw, why = facts["scores"][k]
        w = WEIGHTS[k]
        total += raw * w
        breakdown.append({"criterion": k, "name": CRITERIA[k], "raw": raw,
                          "weight": w, "weighted": raw * w, "justification": why})
    return dict(cand, scored=True, total=total, breakdown=breakdown,
                status="candidate" if total >= CUTOFF else "deprioritized",
                facts={k: v for k, v in facts.items() if k != "scores"})


def score_all(survivors):
    scored = [score_one(c) for c in survivors]
    scored.sort(key=lambda c: (-c["total"], c["name"]))
    ranked = [c for c in scored if c["status"] == "candidate"]
    demoted = [c for c in scored if c["status"] != "candidate"]
    return ranked, demoted


def _selftest():
    c = {"name": "Nicotinamide riboside", "node": "sirt2_bubr1"}
    s = score_one(c)
    assert s["scored"] and s["total"] == 20, s["total"]
    assert s["status"] == "candidate"
    assert score_one({"name": "Fisetin", "node": "x"})["status"] == "deprioritized"
    assert score_one({"name": "BAY-1161909", "node": "x"})["status"] == "no_curated_facts"
    assert MAX_SCORE == 26
    print("score self-test OK")


if __name__ == "__main__":
    _selftest()
