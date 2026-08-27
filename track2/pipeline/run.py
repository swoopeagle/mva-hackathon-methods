"""Run one case: evidence -> directionality -> rubric score.

    python3 run.py ../cases/mva-child-01.yaml

Writes track2/out/<case_id>/report_data.json and candidates.md.
Public data only; no patient data ever enters this repo or an API call.
"""
import json
import os
import sys

import yaml

import directionality
import evidence
import score

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")

BANNER = ("**Not medical advice.** These are hypotheses generated for research "
          "follow-up, not treatment recommendations.")


def run(case_path):
    with open(case_path) as f:
        case = yaml.safe_load(f)
    gene = case["gene"]
    ev = evidence.assemble(gene)
    survivors, vetoed = directionality.filter_candidates(ev["nodes"], case)
    ranked, demoted = score.score_all(survivors)

    data = {
        "case": case,
        "banner": BANNER,
        "rubric": {"weights": score.WEIGHTS, "max": score.MAX_SCORE,
                   "cutoff": score.CUTOFF, "source": "track2/RUBRIC.md (pre-registered)"},
        "seed_gene": {
            "symbol": gene,
            "opentargets_known_drugs": len(ev["seed"]["opentargets"]["drugs"]),
            "opentargets_tractability": ev["seed"]["opentargets"]["tractability"],
            "opentargets_source": ev["seed"]["opentargets"]["source"],
            "dgidb_interactions": len(ev["seed"]["dgidb"]["interactions"]),
            "dgidb_source": ev["seed"]["dgidb"]["source"],
        },
        "node_map": ev.get("node_map"),
        "no_direct_node": ev.get("no_direct_node", False),
        "note": ev.get("note"),
        "nodes": [{k: v for k, v in n.items() if k != "candidates"} for n in ev["nodes"]],
        "ranked_candidates": ranked,
        "deprioritized": demoted,
        "rejected": vetoed,
    }

    outdir = os.path.join(OUT, case["case_id"])
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "report_data.json"), "w") as f:
        json.dump(data, f, indent=1)
    md = markdown(data)
    with open(os.path.join(outdir, "candidates.md"), "w") as f:
        f.write(md)
    return data, md, outdir


def markdown(d):
    c = d["case"]
    L = ["# Candidate table — %s (%s)" % (c["case_id"], c["gene"]), "", d["banner"], "",
         "Variant classes: %s | residual protein: %s | age band: %s"
         % (", ".join(v["class"] for v in c.get("variants", [])) or "n/a",
            c.get("residual_protein"), c.get("age_band")), "",
         "Seed gene `%s`: Open Targets known drugs = **%d**, DGIdb interactions = **%d** "
         "(sources: %s / %s). The seed is undruggable, so the pipeline walks the "
         "curated mechanism node map."
         % (d["seed_gene"]["symbol"], d["seed_gene"]["opentargets_known_drugs"],
            d["seed_gene"]["dgidb_interactions"], d["seed_gene"]["opentargets_source"],
            d["seed_gene"]["dgidb_source"]), ""]

    if d.get("note"):
        L += ["> %s" % d["note"], ""]
    if d.get("no_direct_node"):
        L += ["> **No direct drug node for this gene; Objective-B buffering lane only.** "
              "Candidates below are not gene-specific — they are the generic "
              "aneuploidy-buffering lane, and are labelled as such rather than "
              "dressed up as mechanism-matched hits.", ""]

    L += ["## Ranked candidates (rubric max %d, cutoff %d)" % (d["rubric"]["max"], d["rubric"]["cutoff"]), ""]
    if not d["ranked_candidates"]:
        L += ["_None. The pipeline returns no candidate rather than a fabricated one._", ""]
    else:
        L += ["| # | Drug | Node | Obj | Score | 1 | 2 | 3 | 4 | 5 | 6 | 7 | Gene-specific |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for i, x in enumerate(d["ranked_candidates"], 1):
            raws = {b["criterion"]: b["raw"] for b in x["breakdown"]}
            L.append("| %d | **%s** | %s | %s | **%d/%d** | %s | %s |"
                     % (i, x["name"], x["node"], x["objective"], x["total"],
                        d["rubric"]["max"],
                        " | ".join(str(raws[k]) for k in range(1, 8)),
                        "yes" if x.get("gene_specific", True) else "no (generic lane)"))
        L.append("")
        L.append("### Score breakdown")
        for x in d["ranked_candidates"]:
            L += ["", "**%s** — %d/%d (%s)" % (x["name"], x["total"], d["rubric"]["max"], x["node_label"]),
                  ""]
            for b in x["breakdown"]:
                L.append("- C%d %s: **%d** x%d = %d — %s"
                         % (b["criterion"], b["name"], b["raw"], b["weight"],
                            b["weighted"], b["justification"]))
            if x.get("facts", {}).get("caution"):
                L.append("- ⚠ **Caution:** %s" % x["facts"]["caution"].strip())
            if x.get("pmids"):
                L.append("- PMIDs: %s" % ", ".join(str(p) for p in x["pmids"]))

    L += ["", "## Deprioritized (scored below cutoff, or not curated)", ""]
    if not d["deprioritized"]:
        L.append("_None._")
    else:
        L += ["| Drug | Node | Score | Why |", "|---|---|---|---|"]
        uncurated = [x for x in d["deprioritized"] if not x["scored"]]
        for x in d["deprioritized"]:
            if not x["scored"]:
                continue
            L.append("| %s | %s | %d | Weighted %d < cutoff %d. |"
                     % (x["name"], x["node"], x["total"], x["total"], d["rubric"]["cutoff"]))
        if uncurated:
            # Collapsed: the API walk returns dozens of clinical-stage analogues.
            # Full list is in report_data.json.
            by_node = {}
            for x in uncurated:
                by_node.setdefault(x["node"], []).append(x["name"])
            for node, names in sorted(by_node.items()):
                L.append("| _%d not-curated API hits_ | %s | n/a | Surfaced by the "
                         "API walk, no curated facts in drug_facts.yaml — left "
                         "unscored rather than guessed (%s%s). Full list in "
                         "report_data.json. |"
                         % (len(names), node, ", ".join(sorted(names)[:4]),
                            ", ..." if len(names) > 4 else ""))

    L += ["", "## Rejected by the directionality filter (hard vetoes)", ""]
    if not d["rejected"]:
        L.append("_None._")
    else:
        L += ["| Drug | Class | Node | Veto | Reason |", "|---|---|---|---|---|"]
        for x in d["rejected"]:
            v = x["veto"]
            L.append("| %s | %s | %s | %s | %s |"
                     % (x["name"], v["drug_class"] or "—", x["node"],
                        "/".join(v["rules"]), v["reason"].strip().replace("\n", " ")))
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        data, md, outdir = run(p)
        print("== %s -> %s" % (p, outdir))
        print(md)
