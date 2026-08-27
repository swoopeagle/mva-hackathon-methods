# MVA Hackathon 2026 — Methods

Reproducible code and reports for our entry to **[Rare Disease, Real Kid: The MVA Hackathon 2026](https://sagebio-rare-disease-real-kid-mva-hackathon-2026.hf.space/)**, organised by Sage Bionetworks with the MVA Society, Hugging Face and BEACON.

> **These are hypotheses for further investigation. They are not treatment recommendations and not medical advice.** No drug named in the Track 2 report has been tested in a patient with mosaic variegated aneuploidy.

**No patient data appears in this repository.** The challenge dataset is gated and was never redistributed, never sent to any hosted LLM API, and is deleted per the challenge terms. Everything here is code, public reference data, or derived conclusions.

---

## Reports

| | |
|---|---|
| [`report/track1_methods.md`](report/track1_methods.md) | Track 1 — variant identification: pipeline, exclusions, calibration rationale |
| [`report/track2_report.md`](report/track2_report.md) | Track 2 — drug repurposing: mechanism, candidates, controls, n-of-1 design |
| [`report/methods_form_answers.md`](report/methods_form_answers.md) | Track 1 methods-description answers |

## Track 1 — variant identification

Phenotype-driven prioritisation of a single WGS case, with a deliberately filter-free pass over the known MVA gene panel because the MVA literature contains causal alleles that standard filtering discards (a regulatory hypomorph ~44 kb upstream of *BUB1B*, and an *Alu* insertion at a splice site).

```
01_normalize.sh    bcftools norm: split multiallelics, left-align, verify REF vs reference
02_exomiser.sh     Exomiser 15.1.0, hiPHIVE, exome preset
02b_genomiser.md   whole-genome non-coding pass with ReMM (setup notes + verification)
03_targeted.sh     no-filter sweep over the 9-gene MVA panel
04_mosaic.py       B-allele-frequency mosaic-aneuploidy check, per chromosome
05_submission.py   ranked submission CSV with a calibrated confidence curve
make_bed.sh        builds the panel BED (BUB1B padded 100 kb upstream)
```

`tools/fetch_tools.sh` fetches Exomiser, its data bundles and a GRCh38 reference (~35 GB).

Runtime after downloads: minutes on a laptop. No GPU, no cloud, no paid API.

## Track 2 — a gene-agnostic n-of-1 repurposing pipeline

A new case is **one YAML file** — gene, variant classes, residual-protein status, age band, contraindications. No code changes.

```
evidence.py        Open Targets + DGIdb, then a curated mechanism-node walk
                   (the seed genes are undruggable; the field is pre-therapeutic)
directionality.py  the differentiator: rejects candidates whose mechanism has the
                   wrong SIGN for a loss-of-function variant, plus three hard vetoes
score.py           applies RUBRIC.md, committed before any candidate was generated
run.py             evidence -> directionality -> feasibility -> score -> report
```

```bash
python3 track2/pipeline/run.py track2/cases/mva-child-01.yaml
python3 track2/pipeline/test_pipeline.py     # smoke test
```

**[`track2/RUBRIC.md`](track2/RUBRIC.md) was committed to version control before any results were generated.** Its git timestamp is the pre-registration. Scores were not tuned after the fact.

### Controls

| Run | Expected | Result |
|---|---|---|
| Scrambled seed (*TTN*) | nothing disease-specific | 0 candidates |
| Mps1/TTK inhibitors | assembled, then vetoed | surfaced live, vetoed |
| *ATM* / ataxia-telangiectasia | recovers the known answer | NAD⁺ precursors at ranks 1–2 |
| *CEP57*, *CENATAC*, *MAD2L1BP* | no gene-specific node exists | reports exactly that, invents nothing |
| Gate control | same node, opposite outcome | survives with residual protein, auto-vetoed without |

The gate control is the core claim in one run: the same mechanism node is retained for a genotype that leaves residual protein and automatically rejected for a homozygous-nonsense genotype. Same code, opposite conclusion, driven only by variant class.

## Licence

Code is MIT ([`LICENSE`](LICENSE)). Reports and documents are CC-BY-4.0, per the challenge terms.

## Acknowledgement

> This work was made possible through the Hackathon, organized by Sage Bionetworks in partnership with the MVA Society, Hugging Face, and BEACON (The Benchmarking, Evaluation, and Assessment Consortium for Science), with prize sponsorship from AWS and Anthropic. We are deeply grateful to the child and their family who generously contributed their data and their story to advance research into this rare disease. We acknowledge their trust in making this Hackathon possible.
