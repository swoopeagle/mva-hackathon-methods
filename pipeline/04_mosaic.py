#!/usr/bin/env python3
"""DIY mosaic-aneuploidy check from the VCF: per-chromosome B-allele-frequency
spread at het sites + site counts. Mosaic trisomy => BAF band-splitting away from 0.5.
Usage: 04_mosaic.py <norm.vcf.gz>   (needs bcftools in PATH)
Output: per-chrom summary TSV to stdout. Depth-based check runs separately via mosdepth on BAM.
"""
import subprocess, sys, statistics as st
from collections import defaultdict

vcf = sys.argv[1]
cmd = ["bcftools", "query", "-i", 'GT="het" && FMT/DP>=15', "-f", "%CHROM\t[%AD]\n", vcf]
baf = defaultdict(list)
with subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True).stdout as p:
    for line in p:
        chrom, ad = line.split("\t")
        parts = ad.strip().split(",")
        if len(parts) < 2: continue
        try: ref, alt = int(parts[0]), int(parts[1])
        except ValueError: continue
        if ref + alt >= 15:
            baf[chrom].append(alt / (ref + alt))

print("chrom\tn_het\tbaf_mean\tbaf_sd\tfrac_outside_0.4_0.6")
for c, vals in sorted(baf.items(), key=lambda kv: kv[0]):
    if len(vals) < 200: continue
    out = sum(1 for v in vals if v < 0.4 or v > 0.6) / len(vals)
    print(f"{c}\t{len(vals)}\t{st.mean(vals):.3f}\t{st.stdev(vals):.3f}\t{out:.3f}")
# ponytail: whole-chrom aggregate only; per-arm/segment resolution via MAD-seq if signal warrants
