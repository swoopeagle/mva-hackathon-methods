# Genomiser (non-coding) setup — Exomiser 15.1.0, GRCh38

The `genome` preset is Genomiser: same pipeline as `exome` but keeps regulatory/intergenic
variants and scores them with **ReMM**. Exomiser will not score non-coding variants without
the ReMM file wired in, so this is a prerequisite, not an option.

## 1. ReMM data (15 GB)

Official source: <https://remm.bihealth.org/download> (Kircher lab). Not bundled with the
Exomiser data releases, not on Zenodo.

```bash
mkdir -p ~/mva-tools/exomiser-cli-15.1.0/data/remm
cd ~/mva-tools/exomiser-cli-15.1.0/data/remm
curl -L -C - -O https://kircherlab.bihealth.org/download/ReMM/ReMM.v0.4.hg38.tsv.gz \
            -O https://kircherlab.bihealth.org/download/ReMM/ReMM.v0.4.hg38.tsv.gz.tbi \
            -O https://kircherlab.bihealth.org/download/ReMM/ReMM.v0.4.hg38.md5
md5 -q ReMM.v0.4.hg38.tsv.gz   # compare against the .md5 file
```

`-C -` matters: the transfer is long enough to get interrupted. The `.tbi` must sit next
to the `.tsv.gz` — Exomiser opens it via tabix.

## 2. application.properties

Only one key. The docs page only shows the hg19 example; the hg38 key is confirmed from
`lib/exomiser-spring-boot-autoconfigure-15.1.0.jar!/META-INF/spring-configuration-metadata.json`
(valid keys there: `exomiser.hg38.remm-path`, `exomiser.hg38.cadd-snv-path`,
`exomiser.hg38.cadd-in-del-path`).

```properties
exomiser.hg38.remm-path=${exomiser.data-directory}/remm/ReMM.v0.4.hg38.tsv.gz
```

CADD is optional and skipped: 2 more large files (v1.7 GRCh38 whole-genome SNVs + gnomAD
indels) for a marginal second pathogenicity opinion on coding variants we already score.

## 3. Run

```bash
cd ~/mva-tools/exomiser-cli-15.1.0
java -Xmx16g -jar exomiser-cli-15.1.0.jar analyse \
  --sample <sample.yml> --vcf <norm.chr.vcf.gz> --assembly GRCh38 \
  --preset genome \
  --output-format HTML,JSON,PARQUET,TSV_VARIANT \
  --output-directory <outdir> --output-filename <name>
```

`TSV_VARIANT` is worth adding: the JSONL variant records carry no `variantEffect` /
`transcriptAnnotations` field, so the per-variant functional class (the whole point of a
non-coding pass) is only available from the TSV (or the HTML).

## Verify ReMM actually engaged

Two lines must appear in the run log, otherwise the pass is a plain genome run with no
non-coding scoring and the result means nothing:

```
GenomeDataSourceLoader : Opening REMM data from source: .../ReMM.v0.4.hg38.tsv.gz
AbstractAnalysisRunner : Wrapping PathogenicityFilter{... target=NON_CODING} with
                         VariantDataProvider for sources [REMM, REVEL, MVP, SPLICE_AI, ALPHA_MISSENSE]
```

Positive control for the writeup: count contributing variants whose `FUNCTIONAL_CLASS` is
non-coding (`regulatory_region_variant`, `intergenic_variant`, `upstream_gene_variant`, …)
in the TSV. If that count is zero genome-wide, ReMM is not wired up — a "no non-coding
allele found" conclusion is only defensible when the pass demonstrably ranks non-coding
variants somewhere.

## Gotchas

- 16 GB heap on a 38 GB machine is comfortable. Runtime on ~5 M variants was ~3 min 20 s —
  the preset is not the bottleneck people expect; the 15 GB download is.
- Genome runs rank more genes than exome runs, so rank denominators are not comparable
  across presets; compare score gaps and relative ordering instead.
- Keep the pre-Genomiser `application.properties` as a `.bak` so the exome preset stays
  reproducible if the ReMM file is ever moved or deleted.
- Result (2026-08-26): the genome pass reproduced the exome pass's rank-1 gene and its two
  coding alleles, and added no non-coding candidate in any of the 9 MVA genes — while
  ranking contributing non-coding variants in 44 other genes. Recorded as a negative result,
  not a failed run.
