# Track 1 Methods Description Form — Answers

> **Result (submission 1, 2026-08-27): Rank points 100.0/100 · F-max 1.000 · full match at
> rank 1.** Both metrics are at ceiling on the first scored submission; the remaining five
> slots were deliberately left unspent.

*Paste-ready text for the official methods xlsx. One form per model (up to 6 models).
Model-specific fields are marked; everything else is stable across models.*

---

### 1. Team name

`swoopeagle` (project codename: checkpoint-charlie)

---

### 2. Model number / name

**[MODEL-SPECIFIC]** Model 1 — `swoopeagle_exomiser-union`

*(Naming convention for later slots: `swoopeagle_<short-model-name>`, matching the
submission filename `swoopeagle_<model-name>.csv`. Keep the model number in this form
identical to the number under which the CSV was uploaded.)*

---

### 3. Describe your model in detail

A deterministic, phenotype-driven variant-prioritisation pipeline with a deliberate
no-filter rescue pass over the known MVA gene set, plus an orthogonal mosaicism check used
as corroborating evidence.

**Stage 0 — Normalisation.** The provided GRCh38 VCF is normalised with
`bcftools norm -m -any -f <GRCh38.fna> -c w`: multiallelic records are split into biallelic
ones and indels are left-aligned and trimmed against the reference. 39,804 indels were
realigned by this step. Because scoring is an exact match on (chrom, pos, ref, alt), any
un-normalised indel would be a silent miss. The provided VCF uses bare contig names while
the reference and the submission template are chr-prefixed; we maintain explicit rename
maps in both directions, keep the raw VCF for coordinate round-tripping, and emit
chr-prefixed coordinates. Every emitted REF allele is verified against the reference FASTA
at the emitted position before submission.

**Stage 1 — Phenotype-driven prioritisation.** Exomiser 15.1.0 (data release 2406_hg38 /
2406_phenotype), assembly GRCh38, hiPHIVE prioritiser, all inheritance modes (AD, AR, XD,
XR, MT). Phenotype input is the proband's HPO term set (8 terms), rendered locally into a
phenopacket. Exomiser combines phenotype similarity, variant pathogenicity, population
frequency and inheritance-model fit into a per-gene combined score. Result: BUB1B ranked
1 of 363 genes, combined score 0.650 versus 0.206 for the runner-up, phenotype component
0.59. The top genotype under the autosomal-recessive model is a compound heterozygote in
BUB1B: chr15:40209701 `stop_gained` (ClinVar Pathogenic/Likely pathogenic) and
chr15:40220612 novel missense (variant pathogenicity 0.92); both PASS, both ultra-rare.

**Stage 2 — No-filter targeted rescue pass.** Every variant record — no frequency,
consequence, FILTER or quality threshold applied — inside a BED covering nine
MVA-associated genes (BUB1B, CEP57, TRIP13, CENATAC, CEP192, MAD2L1BP, SLF2, SMC5, MAD1L1),
each padded ±50 kb, with BUB1B padded 100 kb on the upstream side. The upstream padding is
deliberate: the classic MVA1 genotype pairs a truncating allele with a *hypomorphic* allele,
and the hypomorph is repeatedly non-coding — a distal regulatory variant ~44 kb upstream of
BUB1B was TALEN-validated as reducing BUB1B transcript (PNAS 2014), and a 2025 fetal case
paired a coding frameshift with exactly such an upstream variant. Standard filtering
discards these. This pass exists so that no candidate second allele can be lost to a
filter; its output (2,549 records) is screened by fixed rules for rare non-coding, UTR,
synonymous, splice-region and low-quality candidates.

**Stage 3 — Mosaicism check (corroboration, not ranking).** Per-chromosome B-allele
frequency at high-confidence heterozygous sites (FMT/DP ≥ 15), summarised as the fraction of
sites outside the 0.4–0.6 band. Against a within-sample baseline of ~0.25–0.28, chr21
(0.422), chr22 (0.437), chr20 (0.389), chr9 (0.335) and chr17 (0.316) are outliers — the
variegated mosaic-aneuploidy signature, read out of the same VCF by a signal entirely
independent of the variant calls. This does not enter the ranking; it is the third
independent evidence line supporting the call.

**Stage 4 — Merge, rank and calibrate.** Candidates from Stages 1 and 2 are merged and
ordered by a fixed, documented rule hierarchy: ClinVar assertion status > biallelic hit in a
known MVA gene > variant pathogenicity score > phenotype score. EPCR is then shaped rather
than merely ordered, per the published scoring behaviour: 1–2 predictions at ≥ 0.9, hedge
rows in a 0.4–0.6 shoulder, everything else ≤ 0.15. Because a compound-het pair line with
one incorrect member scores zero, the pair is submitted once as the high-confidence bet and
each allele is *also* submitted as an adjacent single in the shoulder tier, so a
partially-correct pair degrades to half credit instead of to nothing.

**Stage 5 — Emission.** `05_submission.py` writes the official schema and asserts: ≤ 10
rows; EPCR in (0,1] and monotone non-increasing with rank; chr prefix present on both
members of every row; `finding_type ∈ {primary, secondary}`.

---

**Stage 3 — Independent whole-genome non-coding pass.** Exomiser 15.1.0 `--preset genome`
with ReMM v0.4 hg38 (md5-verified) over all 4,962,060 variant records. BUB1B reproduced at
rank 1 of 492 genes, with exactly the same two coding alleles and **no non-coding BUB1B
variant of any class**. This negative is load-bearing rather than vacuous: in the same run,
44 other genes received a *contributing* non-coding variant (13 regulatory_region, 14
intergenic, 19 upstream, 5 downstream, plus UTR and intronic), with non-coding-driven genes
ranking as high as 3. The pass could surface a non-coding allele and did not find one here.

**Stage 4 — Panel-wide exclusion.** The no-filter sweep was extended to all nine MVA genes
(~1.8 Mb including flanks), gnomAD v4.1-joined, strand-aware. Across the eight non-BUB1B
genes there is **not one rare coding variant**; all 19 rare variants are intronic or
intergenic, and SpliceAI on all 21 rare non-candidates gave a panel-wide maximum delta of
0.02. No competing biallelic hypothesis exists on the panel.

**Stage 5 — Orthogonal mosaicism corroboration.** Per-chromosome B-allele-frequency analysis
at heterozygous sites shows band-splitting on five different chromosomes (chr9, 17, 20, 21,
22: 0.32–0.44 of sites outside a 0.40–0.60 band, against a 0.25–0.28 diploid baseline) —
the variegated multi-chromosome mosaic-aneuploidy signature that a BUB1B checkpoint defect
predicts. This contributes no rank points; it is independent confirmation that the genotype
and the observed cytogenetics agree.

**Confirmed alleles.** chr15:40209701 T>G = c.2210T>G p.(Leu737*), stop_gained, exon 17/23,
NMD-predicted, ClinVar 533901 P/LP; chr15:40220612 T>G = c.3006T>G p.(Asn1002Lys), missense,
final exon (NMD-escaping, so residual protein expected), within the kinase domain,
1/1,112,006 in gnomAD. SpliceAI excludes a cryptic splice effect for both (delta 0.03/0.02).
The truncation removes the entire kinase domain (UniProt O60566 residues 766–1050) including
ATP-binding Lys795 and catalytic Asp882.

---

### 4. Is the output fully automated, or was there manual curation?

**Fully automated.** The ranked list is produced end-to-end by scripts
(`01_normalize.sh` → `02_exomiser.sh` / `03_targeted.sh` → `04_mosaic.py` →
`05_submission.py`). There is no sampling, no random seed, and no model call anywhere in
the ranking path; re-running the pipeline on the same VCF, HPO list and data release
reproduces the submitted ranking byte-for-byte.

Human judgement is confined to *pipeline design decisions made before the data were
scored* — which genes go in the targeted BED and how far they are padded, the rule
hierarchy used to merge candidates, and the EPCR tier boundaries. All of these are
committed in the public repository as code and documentation, not applied per-variant after
seeing the results.

---

### 5. Describe any manual review performed

No manual reordering of the ranking was performed, and no variant was added to or removed
from the output by hand.

Manual review was limited to verification and pre-registered design:

1. **Design decisions, made before results:** the nine-gene MVA panel and its padding
   (including the 100 kb upstream BUB1B window motivated by the published non-coding
   hypomorph precedent), the candidate-merge rule hierarchy, and the EPCR tier structure.
   All are in the repository as code.
2. **Verification of automated output:** REF alleles checked against the reference FASTA;
   coordinate convention and chr-prefixing checked; row count, EPCR range and monotonicity
   checked (these are enforced as assertions, so verification is itself automated).
3. **Reading the no-filter rescue output** to confirm that no rare candidate second allele
   had been set aside — a negative-evidence check that did not change the ranking for this
   proband.

---

### 6. Did you use public data only, or proprietary data?

**Public data and public tools only.** No proprietary database, no commercial variant
classification service, and no licensed knowledge base was used at any stage.

---

### 7. Describe the public data used

| Resource | Version / release | Use |
|---|---|---|
| Challenge dataset (`SageBio/mva-hackathon-2026-data`) | as provided, CC-BY-4.0 | proband VCF and HPO term list |
| GRCh38 reference genome | GRCh38 (chr-prefixed FASTA + `.fai`) | normalisation, left-alignment, REF verification |
| Exomiser | CLI 15.1.0 | phenotype-driven prioritisation (hiPHIVE) |
| Exomiser data release | `2406_hg38`, `2406_phenotype` | bundled variant/phenotype knowledge base |
| Human Phenotype Ontology | via Exomiser 2406_phenotype | phenotype similarity |
| ClinVar | via Exomiser 2406_hg38 | pathogenicity assertions |
| gnomAD population frequencies | via Exomiser 2406_hg38 | rarity filtering / frequency score |
| Ensembl REST (`lookup/symbol`) | live query, build GRCh38 | gene coordinates for the targeted BED |
| bcftools / htslib | <TODO: pin version> | normalisation, region extraction, BAF query |
| SpliceAI | <TODO — pending run> | splice-impact scores for reported and near-exonic candidate alleles |
| Genomiser / REMM | <TODO — pending run> | independent non-coding ranking |
| Published literature | see report §10 | scoring calibration (Stenton et al. 2024); BUB1B non-coding hypomorph (PNAS 2014); BUB1B Alu insertion (Hum Genome Var 2017) |

---

### 8. Describe any proprietary data used

**None.** No proprietary or restricted-access data, database, or software was used.

---

### 9. Can your model output compound-heterozygous variant pairs?

**Yes.** Exomiser is run with all inheritance modes enabled, including autosomal recessive,
and scores compound-heterozygous genotypes as a unit. The submission format is used to its
full extent: a pair is emitted as a single row with both `chrom_1..alt_1` and
`chrom_2..alt_2` populated.

For this proband the model's primary call **is** a compound heterozygote in BUB1B —
chr15:40209701 (`stop_gained`, ClinVar P/LP) with chr15:40220612 (novel missense,
pathogenicity 0.92) — the canonical MVA1 genotype of one truncating plus one non-truncating
allele.

We also hedge deliberately. Because the published scoring rule awards **zero** to a pair
line with one correct and one incorrect member, the two alleles are additionally submitted
as separate single-variant rows immediately below the pair row, so that a partially-correct
pair still earns credit for the allele that is right.

**Limitation stated openly:** phase is *inferred*, not demonstrated. Only the proband was
sequenced, and the two alleles are in different exons, far beyond read-pair distance, so
*cis* versus *trans* cannot be established from these data. The compound-het call rests on
the canonical genotype shape and the phenotype match; parental or long-read sequencing would
be the confirmatory step.

---

### 10. How were secondary findings handled?

Secondary findings are screened for automatically and reported separately from the primary
diagnostic call, as `finding_type = secondary` rows with a per-row justification in the
notes column. The screen matches ClinVar Pathogenic / Likely-pathogenic assertions in the
normalised VCF against the ACMG SF v3.2 secondary-findings gene list; it is independent of
the phenotype-driven ranking, so a secondary finding can never displace or dilute the
primary call.

Reported secondary findings are explicitly labelled as unconfirmed research-grade
observations requiring accredited-laboratory confirmation and genetic counselling before any
clinical use. No return-of-results decision is implied or recommended by this submission.

> **TODO — results pending.** The secondary-findings screen is being completed separately.
> Insert the final list (gene, variant, ClinVar assertion, ACMG SF category) or the explicit
> statement "no ACMG SF v3.2 Pathogenic/Likely-pathogenic findings identified" before
> submitting this form.

---

### 11. Runtime and cost estimate

**Runtime:** approximately **5–15 minutes end-to-end on a single laptop** (Apple Silicon
MacBook, 16 GB heap allocated to Exomiser), once reference data are in place:

| Stage | Approximate wall time |
|---|---|
| `bcftools norm` + index + contig rename | ~2–5 min |
| Exomiser 15.1.0, exome preset | ~3–8 min |
| No-filter targeted pass (9-gene BED) | seconds |
| BAF mosaicism scan | ~1 min |
| Submission build + validation | seconds |

**One-time setup:** downloading Exomiser, the 2406 data release and the GRCh38 reference is
roughly **35 GB** and is bandwidth-bound (hours on a domestic connection). This is a
one-time cost, not a per-proband cost.

**Cost: approximately $0.** No cloud compute, no GPU, no API calls, no paid database
subscription, no licensed software. Every tool is free and open-source and every database
is publicly downloadable. The marginal cost of running the pipeline on an additional
proband is the electricity for ten minutes of laptop CPU.

---

### 12. Method abstract (500 words), with strengths and limitations

*(Word count: ~490.)*

We report a deterministic, fully automated, public-data-only pipeline for diagnostic variant
prioritisation from a single proband's genome and HPO terms, applied to proband EX2312012.

**Method.** The provided GRCh38 VCF is normalised with `bcftools norm -m -any -f ref -c w`,
splitting multiallelics and left-aligning indels; 39,804 indels were realigned. Because
scoring is an exact coordinate match, we also reconcile the VCF's bare contig naming with
the chr-prefixed convention of the reference and the submission template, maintaining rename
maps in both directions and verifying every emitted REF against the reference FASTA.
Exomiser 15.1.0 (data release 2406) with the hiPHIVE prioritiser and all inheritance models
ranks candidate genes by combined phenotype, pathogenicity, frequency and inheritance
evidence. In parallel, a no-filter rescue pass extracts *every* variant record — no
frequency, consequence, FILTER or quality threshold — across nine MVA-associated genes
padded ±50 kb, with BUB1B padded 100 kb upstream. Finally, per-chromosome B-allele
frequency at heterozygous sites (DP ≥ 15) is summarised to detect mosaic aneuploidy.

**Result.** BUB1B ranks 1 of 363 genes (combined 0.650 vs 0.206 for the runner-up;
phenotype component 0.59), with a compound-heterozygous genotype of chr15:40209701
(`stop_gained`, ClinVar Pathogenic/Likely pathogenic) and chr15:40220612 (novel missense,
pathogenicity 0.92) — both PASS, both ultra-rare — the canonical MVA1 configuration of one
truncating and one non-truncating allele. Independently, the BAF scan shows a variegated
signature: chr21 0.422, chr22 0.437, chr20 0.389, chr9 0.335, chr17 0.316 of heterozygous
sites outside the 0.4–0.6 band, against a ~0.25–0.28 within-sample baseline. Three evidence
lines that could each have failed separately — phenotype, genotype, and cytogenetic
signature — agree.

**Strengths.** (i) Reproducible: no sampling, no random seed, no model call in the ranking
path; the same inputs yield byte-identical output. (ii) Cheap and portable: ~5–15 minutes on
a laptop, ~$0 marginal cost, no proprietary data. (iii) Robust to the failure mode that
loses MVA cases — the classic second allele is a *hypomorph*, often non-coding (a
TALEN-validated regulatory variant 44 kb upstream of BUB1B; an Alu insertion near intron 8),
and our no-filter pass is designed so no such candidate can be lost to a filter.
(iv) Calibrated to the published scoring rules: EPCR is shaped into confident / shoulder /
tail tiers for F-max, and the compound-het pair is hedged with adjacent singles because a
half-wrong pair line scores zero.

**Limitations.** No trio, so phase is inferred, not proven — the two alleles lie beyond
read-pair distance and *cis*/*trans* is unresolved. Single sample, no internal control or
cohort. The mosaicism statistic is whole-chromosome only: it is blind to segmental events,
estimates no cell fraction, and carries no formal null model. Structural variants, mobile
elements and repeat expansions are largely invisible in the provided VCF, so the Alu-
insertion class of second allele cannot be excluded without alignment-level review. The
second allele is computationally scored, not functionally validated; establishing it as
hypomorphic requires BubR1 quantification in patient cells. This is a research analysis, not
a clinical diagnosis.


---

### 13. AI assistant disclosure (required from 28 Aug 2026)

### AI assistant disclosure

Per the challenge's methods-description requirement (added 28 August 2026):

**Provider and model:** Anthropic Claude via Claude Code — Claude Fable 5 (orchestration)
and Claude Opus 5 (execution subagents).
**Plan/tier:** Claude Max (5x) subscription.
**Data-handling setting:** Consumer subscription terms; no patient data sent to the API (see below).

**How it was used, and the boundary we enforced.** Claude was used substantially: literature
synthesis, code authorship for both pipelines, drafting and editing of these reports, and
orchestration of parallel research agents. It was *not* used as an oracle for the variant
call — the Track 1 ranking is produced by deterministic tools (Exomiser, bcftools, SpliceAI)
with no model call anywhere in the ranking path.

**No patient data was ever sent to a hosted LLM API.** This was an architectural decision
made at the outset, in response to the organisers' guidance to interpret the data-use clauses
conservatively pending formal clarification. Concretely: the gated VCF, FASTQ, clinical
phenotype document, HPO term list, and every derived file remained on local disk and were
processed only by locally-executed tools. Scripts bridged files to tools; the assistant's
context received only aggregates, variant *classes*, gene symbols, scores, and the two
*BUB1B* allele coordinates that appear in our public submission by design. Phenotype terms
were extracted from the clinical document by a local script and written directly into an
Exomiser phenopacket without ever being displayed to or read by the model.

Every PMID cited in this report was verified programmatically against the NCBI PubMed API
rather than trusted from model output; this check caught and corrected several incorrect
citations during drafting, including two in an early draft of our own mechanism section.
