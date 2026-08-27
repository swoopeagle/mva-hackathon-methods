# Track 2 pipeline — gene-agnostic n-of-1 repurposing

Public data only. No patient data, no API keys, stdlib + `requests` + `PyYAML`.

```
python3 run.py ../cases/mva-child-01.yaml     # -> ../out/<case_id>/
python3 test_pipeline.py                      # smoke test + all controls
```

| File | Role |
|---|---|
| `evidence.py` | Open Targets GraphQL + DGIdb + mechanism-node walk. Seed genes in MVA have **zero** known drugs, so the pipeline walks `nodes_<GENE>.yaml` instead of stopping. Responses cached to `../out/cache/`; falls back to cache if an API is down and records the source in the report. |
| `nodes_<GENE>.yaml` | Curated, PMID-cited mechanism chains. Each node has a `direction_needed` sign. `no_direct_node: true` is an honest, expected output. |
| `directionality.py` | **The differentiator.** Named-class vetoes (the three hard vetoes of RUBRIC.md) → sign check vs. node direction → residual-protein gate. |
| `drug_facts.yaml` | Per-drug approval/formulation/pediatric/safety facts + curated 0-2 rubric scores, each with a one-line justification. |
| `score.py` | Applies `RUBRIC.md` verbatim (weights 3/2/2/2/2/1/1, max 26, cutoff 13). |
| `run.py` | case YAML → `report_data.json` + `candidates.md`. |

Adding a case = one YAML. Adding a gene = one `nodes_<GENE>.yaml`.

**Not medical advice.** Hypotheses for research follow-up.
