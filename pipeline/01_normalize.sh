#!/bin/bash
# Normalize the provided VCF for exact-match scoring safety.
# Usage: 01_normalize.sh <in.vcf.gz> <ref.fna> <out.vcf.gz>
set -euo pipefail
IN=$1; REF=$2; OUT=$3
bcftools head "$IN" | grep -m1 -i "reference\|##contig" || true   # eyeball build
bcftools norm -m -any -f "$REF" -c w "$IN" -Oz -o "$OUT"
tabix -f -p vcf "$OUT"
echo "normalized -> $OUT (keep the RAW vcf too; submissions must round-trip coordinates)"
