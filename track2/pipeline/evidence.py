"""Evidence assembly: Open Targets Platform + DGIdb + a curated mechanism node map.

The seed gene in an MVA case has NO approved drugs (BUB1B returns 0 from Open
Targets). So the pipeline does not stop at the seed -- it walks a curated
mechanism node map (nodes_<GENE>.yaml) encoding literature chains, and queries
the live APIs for every node that has a real protein target.

Public data only. No API keys.
"""
import hashlib
import json
import os
import sys

import requests
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "..", "out", "cache")
OT = "https://api.platform.opentargets.org/api/v4/graphql"
DGIDB = "https://dgidb.org/api/graphql"
TIMEOUT = 30

TARGET_Q = """query($id:String!){target(ensemblId:$id){approvedSymbol
 tractability{label modality value}
 drugAndClinicalCandidates{count rows{maxClinicalStage
   drug{id name drugType maximumClinicalStage
     mechanismsOfAction{rows{mechanismOfAction actionType}}}}}}}"""

SEARCH_Q = ('query($q:String!){search(queryString:$q,entityNames:["target"])'
            "{hits{id name}}}")


def _post(url, payload):
    """POST with a JSON file cache. Returns (data, source) where source is
    live | cache | unavailable. If an API is down we serve the cached response
    structure and the report records that it was not fetched live."""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1((url + json.dumps(payload, sort_keys=True)).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, key + ".json")
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            raise RuntimeError(data["errors"])
        with open(path, "w") as f:
            json.dump(data, f)
        return data, "live"
    except Exception as e:  # network down, rate limit, schema drift
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f), "cache"
        print("  ! API unavailable and no cache: %s" % e, file=sys.stderr)
        return None, "unavailable"


def ensembl_id(symbol):
    data, src = _post(OT, {"query": SEARCH_Q, "variables": {"q": symbol}})
    if not data:
        return None, src
    for hit in data["data"]["search"]["hits"]:
        if hit["name"] == symbol:
            return hit["id"], src
    return None, src


def open_targets(symbol):
    """Known drugs + tractability for one target symbol."""
    eid, src = ensembl_id(symbol)
    if not eid:
        return {"symbol": symbol, "source": src, "drugs": [], "tractability": []}
    data, src = _post(OT, {"query": TARGET_Q, "variables": {"id": eid}})
    if not data:
        return {"symbol": symbol, "source": src, "drugs": [], "tractability": []}
    t = data["data"]["target"]
    drugs = []
    for row in t["drugAndClinicalCandidates"]["rows"]:
        d = row["drug"]
        moa = d.get("mechanismsOfAction") or {"rows": []}
        drugs.append({
            "name": d["name"],
            "chembl": d["id"],
            "drug_type": d["drugType"],
            "max_stage": row["maxClinicalStage"],
            "moa": [m["mechanismOfAction"] for m in moa["rows"]],
            "action_types": sorted({m["actionType"] for m in moa["rows"] if m["actionType"]}),
        })
    return {
        "symbol": t["approvedSymbol"],
        "ensembl": eid,
        "source": src,
        "tractability": [x["label"] for x in t["tractability"] if x["value"]],
        "drugs": drugs,
    }


def dgidb(symbol):
    q = ('{genes(names:["%s"]){nodes{name interactions{'
         "drug{name conceptId approved} interactionTypes{type directionality} "
         "interactionScore}}}}") % symbol
    data, src = _post(DGIDB, {"query": q})
    if not data:
        return {"symbol": symbol, "source": src, "interactions": []}
    nodes = data["data"]["genes"]["nodes"]
    out = []
    for n in nodes:
        for i in n["interactions"]:
            out.append({
                "name": i["drug"]["name"],
                "approved": i["drug"]["approved"],
                "action_types": sorted({t["type"] for t in i["interactionTypes"] if t["type"]}),
                "directionality": sorted({t["directionality"] for t in i["interactionTypes"]
                                          if t.get("directionality")}),
                "score": i["interactionScore"],
            })
    return {"symbol": symbol, "source": src, "interactions": out}


def load_nodes(gene):
    path = os.path.join(HERE, "nodes_%s.yaml" % gene)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def assemble(gene):
    """Seed-gene evidence + one candidate list per mechanism node.

    Candidates carry their node's direction_needed so directionality.py can
    check the sign, and their origin (curated literature chain vs. pulled live
    off the node target by the API walk)."""
    seed = {"opentargets": open_targets(gene), "dgidb": dgidb(gene)}
    nodemap = load_nodes(gene)
    if nodemap is None:
        return {"gene": gene, "seed": seed, "node_map": None, "nodes": [],
                "note": "No curated mechanism node map for %s. "
                        "Pipeline emits no candidates." % gene}

    nodes = []
    for node in nodemap.get("nodes", []):
        ev = {}
        if node.get("target_symbol"):
            ev = {"opentargets": open_targets(node["target_symbol"]),
                  "dgidb": dgidb(node["target_symbol"])}
        cands = []
        for d in node.get("drugs", []):
            cands.append(dict(d, node=node["id"], node_label=node["label"],
                              direction_needed=node["direction_needed"],
                              objective=node["objective"], origin="curated",
                              pmids=node.get("pmids", []),
                              requires_residual_protein=node.get("requires_residual_protein", False),
                              gene_specific=node.get("gene_specific", True)))
        # API walk: drugs acting on this node's target that we did not curate
        seen = {c["name"].lower() for c in cands}
        for d in (ev.get("opentargets") or {}).get("drugs", []):
            if d["name"].lower() in seen:
                continue
            cands.append(dict(d, node=node["id"], node_label=node["label"],
                              direction_needed=node["direction_needed"],
                              objective=node["objective"], origin="opentargets",
                              pmids=node.get("pmids", []),
                              requires_residual_protein=node.get("requires_residual_protein", False),
                              gene_specific=node.get("gene_specific", True)))
        nodes.append(dict(node, target_evidence=ev, candidates=cands))

    return {"gene": gene, "seed": seed, "node_map": nodemap.get("meta", {}),
            "no_direct_node": nodemap.get("no_direct_node", False),
            "nodes": nodes}


if __name__ == "__main__":
    print(json.dumps(assemble(sys.argv[1] if len(sys.argv) > 1 else "BUB1B"), indent=1))
