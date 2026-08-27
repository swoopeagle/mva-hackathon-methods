#!/bin/bash
# Fetch Exomiser + data bundles + GRCh38 reference into ~/mva-tools (outside repo).
# Resumable (curl -C -). ~35 GB total; run in background.
set -euo pipefail
T=~/mva-tools; mkdir -p "$T"; cd "$T"
get() { curl -L -C - -o "$2" "$1" || { echo "FAILED: $1"; exit 1; }; }
get https://github.com/exomiser/Exomiser/releases/download/15.1.0/exomiser-cli-15.1.0-distribution.zip exomiser-cli-15.1.0-distribution.zip
get https://data.monarchinitiative.org/exomiser/latest/2406_hg38.zip 2406_hg38.zip
get https://data.monarchinitiative.org/exomiser/latest/2406_phenotype.zip 2406_phenotype.zip
# GRCh38 no-alt analysis set (for bcftools norm left-alignment)
get https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.15_GRCh38/seqs_for_alignment_pipelines.ucsc_ids/GCA_000001405.15_GRCh38_no_alt_analysis_set.fna.gz GRCh38_no_alt.fna.gz
echo "downloads complete; unpacking exomiser"
# NOTE: macOS Archive Utility corrupts these zips per Exomiser docs — use ditto/unzip CLI only.
unzip -o -q exomiser-cli-15.1.0-distribution.zip
unzip -o -q 2406_hg38.zip -d exomiser-cli-15.1.0/data
unzip -o -q 2406_phenotype.zip -d exomiser-cli-15.1.0/data
gunzip -kf GRCh38_no_alt.fna.gz && samtools faidx GRCh38_no_alt.fna
echo ALL DONE
