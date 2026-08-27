#!/bin/bash
# Exomiser 15.1.0 pass. Usage: 02_exomiser.sh <sample.yml> <norm.chr.vcf.gz> <outdir> <name> [preset]
# sample.yml = phenopacket built by local script from hpo_ids.txt (patient data stays local).
# Data setup: ~/mva-tools/exomiser-cli-15.1.0 with 2406_hg38 + 2406_phenotype in data/,
# application.properties pointing at them. VCF must be chr-named (chr_add.map) to match ref.
set -euo pipefail
SAMPLE=$1; VCF=$2; OUT=$3; NAME=$4; PRESET=${5:-exome}
cd ~/mva-tools/exomiser-cli-15.1.0
java -Xmx16g -jar exomiser-cli-15.1.0.jar analyse \
  --sample "$SAMPLE" --vcf "$VCF" --assembly GRCh38 \
  --preset "$PRESET" \
  --output-directory "$OUT" --output-filename "$NAME"
# ponytail: genome preset needs REMM data (Genomiser) -- fetch + wire before non-coding pass
