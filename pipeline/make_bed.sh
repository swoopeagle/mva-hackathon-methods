#!/bin/bash
# Build mva_genes.bed (GRCh38) for the no-filter targeted pass.
# ±50kb pad; BUB1B gets 100kb upstream (known intergenic regulatory hypomorph at -44kb).
set -euo pipefail
OUT=${1:-mva_genes.bed}; : > "$OUT"
genes="BUB1B CEP57 TRIP13 CENATAC CEP192 MAD2L1BP SLF2 SMC5 MAD1L1"
for g in $genes; do
  json=$(curl -s --max-time 30 --retry 3 --retry-delay 15 "https://rest.ensembl.org/lookup/symbol/homo_sapiens/$g?content-type=application/json")
  read -r chr start end strand <<< "$(echo "$json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['seq_region_name'], d['start'], d['end'], d['strand'])")"
  pad_up=50000; pad_dn=50000
  if [ "$g" = BUB1B ]; then if [ "$strand" = "1" ]; then pad_up=100000; else pad_dn=100000; fi; fi
  s=$((start - pad_up)); [ $s -lt 1 ] && s=1
  echo -e "chr${chr}\t$((s-1))\t$((end + pad_dn))\t${g}" >> "$OUT"
done
sort -k1,1 -k2,2n -o "$OUT" "$OUT"; cat "$OUT"
