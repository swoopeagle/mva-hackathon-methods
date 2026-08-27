"""Direction-of-effect filter — the differentiator.

Global rankers do not know whether a child's variant makes protein, or which
way a node must move. Three things are checked, in order:

  1. Named-class vetoes  — the three hard vetoes pre-registered in RUBRIC.md.
  2. Sign check          — drug action vs. the node's direction_needed.
  3. Residual-protein gate — a stabilization lane is void if no protein is made.

Vetoes are absolute: a vetoed candidate never reaches scoring, regardless of
how well it would have scored.
"""
import re

# RUBRIC.md hard vetoes:
#   (a) mechanism increases chromosome missegregation
#   (b) efficacy depends on an intact SAC
#   (c) aneuploidy-selective lethality as chronic systemic therapy
VETOES = [
    {
        "drug_class": "Mps1/TTK inhibitors",
        "rules": ["a", "b"],
        "patterns": [r"\bttk\b", r"\bmps1\b", r"bay[- ]?1161909", r"bay[- ]?1217389",
                     r"empesertib", r"cft[- ]?8634", r"\bs81694\b", r"\bnms[- ]?p715\b"],
        "reason": ("Further inhibiting the apex SAC kinase in a patient whose SAC is "
                   "already germline-deficient increases missegregation (veto a) and "
                   "presumes checkpoint competence it does not have (veto b)."),
    },
    {
        "drug_class": "Aurora kinase inhibitors",
        "rules": ["a"],
        "patterns": [r"aurora", r"alisertib", r"barasertib", r"danusertib",
                     r"tozasertib", r"\bmln8054\b", r"chiauranib"],
        "reason": ("Aurora A/B inhibition degrades error correction and increases "
                   "chromosome missegregation (veto a)."),
    },
    {
        "drug_class": "KIF11/KSP inhibitors",
        "rules": ["a", "b"],
        "patterns": [r"\bkif11\b", r"\bksp\b", r"kinesin spindle", r"ispinesib",
                     r"filanesib", r"litronesib", r"\bsb[- ]?743921\b"],
        "reason": ("Monopolar-spindle agents kill via SAC-dependent mitotic arrest; "
                   "germline SAC-deficient cells escape the arrest and exit with "
                   "massive missegregation instead (vetoes a and b)."),
    },
    {
        "drug_class": "Taxanes / vinca alkaloids",
        "rules": ["a", "b"],
        "patterns": [r"paclitaxel", r"docetaxel", r"cabazitaxel", r"vincristine",
                     r"vinblastine", r"vinorelbine", r"vindesine", r"vinflunine",
                     r"eribulin", r"tubulin", r"microtubule"],
        "reason": ("Wrong lesion and wrong dependency: the defect is checkpoint "
                   "failure, not microtubule hyper-stability (Ertych, Nat Cell Biol "
                   "2014, PMID 24976383), and these agents require an intact SAC to "
                   "arrest (vetoes a and b)."),
    },
    {
        "drug_class": "Aneuploidy-selective compounds",
        "rules": ["c"],
        "patterns": [r"\baicar\b", r"acadesine", r"17[- ]?aag", r"tanespimycin",
                     r"chloroquine", r"hydroxychloroquine", r"\bhsp90\b",
                     r"geldanamycin"],
        "reason": ("These kill aneuploid cells preferentially (Tang, Cell 2011, PMID "
                   "21315436). The patient's OWN somatic tissue is mosaically "
                   "aneuploid, so as chronic systemic therapy this is self-directed "
                   "cytotoxicity (veto c). Rational only as tumour-directed therapy."),
    },
    {
        "drug_class": "TRIP13 inhibitors",
        "rules": ["a"],
        "patterns": [r"trip13", r"dcz0415"],
        "reason": ("Wrong direction: MVA TRIP13 alleles are loss-of-function; TRIP13 "
                   "inhibitors were built against TRIP13 OVERexpression in cancer. "
                   "Further reducing MCC disassembly capacity worsens mitotic error "
                   "(veto a). Also unapproved."),
    },
    {
        "drug_class": "SAC-abrogating tool compounds",
        "rules": ["a", "b"],
        "patterns": [r"reversine", r"\bplk4\b", r"centrinone"],
        "reason": "Directly abrogates checkpoint signalling / centriole duplication (vetoes a, b).",
    },
]

# Which drug action types satisfy which node direction.
_ACTIVATE = {"AGONIST", "ACTIVATOR", "POSITIVE ALLOSTERIC MODULATOR", "OPENER",
             "STABILISER", "PARTIAL AGONIST", "RELEASING AGENT"}
_INHIBIT = {"INHIBITOR", "ANTAGONIST", "BLOCKER", "NEGATIVE ALLOSTERIC MODULATOR",
            "DEGRADER", "DISRUPTING AGENT", "INVERSE AGONIST"}


def _text(cand):
    return " ".join([cand.get("name", "")] + list(cand.get("moa", []))).lower()


def _class_veto(cand):
    t = _text(cand)
    for v in VETOES:
        for p in v["patterns"]:
            if re.search(p, t):
                return {"stage": "class", "rules": v["rules"],
                        "drug_class": v["drug_class"], "reason": v["reason"],
                        "matched": p}
    return None


def _sign_veto(cand):
    """Wrong-sign check. Only fires when the drug's action type is known --
    curated nutrient/supplement candidates carry no action type and are governed
    by their node's direction, which we curated by hand."""
    acts = {a.upper() for a in cand.get("action_types", [])}
    if not acts:
        return None
    want = cand["direction_needed"]
    if want == "activate" and acts & _INHIBIT and not acts & _ACTIVATE:
        bad = "inhibits"
    elif want == "inhibit" and acts & _ACTIVATE and not acts & _INHIBIT:
        bad = "activates"
    else:
        return None
    return {"stage": "sign", "rules": ["sign"], "drug_class": None,
            "reason": ("Wrong sign: node %s must be %sed, but this drug %s it "
                       "(action types: %s)."
                       % (cand["node"], want.rstrip("e"), bad, ", ".join(sorted(acts))))}


def _gate_veto(cand, case):
    if not cand.get("requires_residual_protein"):
        return None
    residual = str(case.get("residual_protein", "unknown")).lower()
    if residual in ("likely", "yes", "true"):
        return None
    return {"stage": "gate", "rules": ["residual_protein"], "drug_class": None,
            "reason": ("Node %s stabilises existing protein; case residual_protein=%s, "
                       "so there is nothing to stabilise. Lane void."
                       % (cand["node"], residual))}


def check(cand, case):
    """Return a veto dict, or None if the candidate survives."""
    return _class_veto(cand) or _sign_veto(cand) or _gate_veto(cand, case)


def filter_candidates(nodes, case):
    """Split every node's candidates into (survivors, vetoed)."""
    survivors, vetoed = [], []
    for node in nodes:
        for c in node["candidates"]:
            v = check(c, case)
            (vetoed if v else survivors).append(dict(c, veto=v) if v else c)
    return survivors, vetoed


def _selftest():
    case = {"residual_protein": "likely"}
    mps1 = {"name": "BAY-1161909", "moa": ["Dual specificity protein kinase TTK inhibitor"],
            "action_types": ["INHIBITOR"], "node": "sac_kinase_mps1",
            "direction_needed": "inhibit"}
    v = check(mps1, case)
    assert v and "a" in v["rules"] and "b" in v["rules"], v
    nr = {"name": "Nicotinamide riboside", "node": "sirt2_bubr1",
          "direction_needed": "activate", "requires_residual_protein": True}
    assert check(nr, case) is None
    assert check(nr, {"residual_protein": "no"})["stage"] == "gate"
    wrong = {"name": "Some SIRT2 inhibitor", "action_types": ["INHIBITOR"],
             "node": "sirt2_bubr1", "direction_needed": "activate"}
    assert check(wrong, case)["stage"] == "sign"
    assert check({"name": "Paclitaxel", "node": "x", "direction_needed": "inhibit"},
                 case)["drug_class"] == "Taxanes / vinca alkaloids"
    assert check({"name": "AICAR", "node": "x", "direction_needed": "inhibit"},
                 case)["rules"] == ["c"]
    print("directionality self-test OK")


if __name__ == "__main__":
    _selftest()
