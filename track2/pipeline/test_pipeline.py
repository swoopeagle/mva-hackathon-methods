"""Smoke test — assert-based, no framework.  python3 test_pipeline.py

Hits the live Open Targets / DGIdb APIs (cached after the first run).
Covers the three negative/positive controls required by track2/RUBRIC.md.
"""
import os

import directionality
import run
import score

CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")


def case(name):
    return run.run(os.path.join(CASES, name))[0]


def names(rows):
    return {r["name"].lower() for r in rows}


directionality._selftest()
score._selftest()

# --- the confirmed case -----------------------------------------------------
d = case("mva-child-01.yaml")
assert d["seed_gene"]["opentargets_known_drugs"] == 0, "BUB1B should have no known drugs"
top = d["ranked_candidates"]
assert top, "BUB1B must yield candidates via the mechanism walk"
assert "nicotinamide riboside" in names(top[:3]), names(top[:3])
assert all(c["total"] >= score.CUTOFF for c in top)
assert top == sorted(top, key=lambda c: -c["total"]), "must be ranked"
assert all(len(c["breakdown"]) == 7 for c in top), "all 7 rubric criteria scored"

# --- control (b): Mps1i must be ASSEMBLED and then VETOED -------------------
mps1_node = [n for n in d["nodes"] if n["id"] == "sac_kinase_mps1"][0]
assembled = {x["name"].lower() for x in d["rejected"] if x["node"] == "sac_kinase_mps1"}
assert assembled, "Mps1 inhibitors must surface in evidence assembly"
assert "bay-1161909" in assembled, assembled
assert not any(x["node"] == "sac_kinase_mps1" for x in top), "Mps1i must never survive"
rules = {r for x in d["rejected"] if x["node"] == "sac_kinase_mps1" for r in x["veto"]["rules"]}
assert {"a", "b"} <= rules, rules

# --- control (a): scrambled seed gene ---------------------------------------
t = case("ctrl-ttn.yaml")
assert t["ranked_candidates"] == [], "TTN must yield no candidates"
assert t["node_map"] is None and t["note"]

# --- positive control: ATM must recover NAD+ precursors ---------------------
a = case("ctrl-atm.yaml")
assert "nicotinamide riboside" in names(a["ranked_candidates"][:3]), names(a["ranked_candidates"])

# --- residual-protein gate: MAD2L1BP nonsense/nonsense kills the NAD lane ---
m = case("sib-mad2l1bp.yaml")
gated = [x for x in m["rejected"] if x["veto"]["stage"] == "gate"]
assert gated, "homozygous nonsense must void the stabilization lane"
assert "nicotinamide riboside" not in names(m["ranked_candidates"])

# --- honesty: CEP57 / CENATAC declare no direct node ------------------------
for f in ("sib-cep57.yaml", "sib-cenatac.yaml"):
    s = case(f)
    assert s["no_direct_node"] is True, f
    assert all(not c.get("gene_specific", True) for c in s["ranked_candidates"]), f

print("test_pipeline OK")
