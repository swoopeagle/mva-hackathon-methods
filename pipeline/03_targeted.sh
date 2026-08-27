#!/bin/bash
# No-filter pass over MVA genes: every variant, however weird, into a TSV for local review.
# Usage: 03_targeted.sh <norm.vcf.gz> <mva_genes.bed> <out.tsv>
set -euo pipefail
VCF=$1; BED=$2; OUT=$3
bcftools view -R "$BED" "$VCF" \
 | bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t%QUAL\t%FILTER\t[%GT]\t[%AD]\t[%DP]\n' > "$OUT"
wc -l "$OUT"
# ponytail: annotation (gnomAD AF, consequence, SpliceAI) added in a second pass once VCF in hand
