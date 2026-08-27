#!/usr/bin/env python3
"""Build Track 1 submission CSV (official schema, max 10 rows).
Input TSV (tab-sep, no header), one row per prediction, ordered by rank:
  chrom_1 pos_1 ref_1 alt_1 [chrom_2 pos_2 ref_2 alt_2] epcr finding_type notes
  (single-variant rows leave the 4 pair fields as '-')
Usage: 05_submission.py <in.tsv> <proband_id> > out.csv
Checks: <=10 rows, epcr in (0,1] monotone non-increasing, chr-prefix present.
"""
import csv, sys

rows = [r for r in csv.reader(open(sys.argv[1]), delimiter="\t") if r]
proband = sys.argv[2]
assert len(rows) <= 10, f"{len(rows)} rows > 10"
w = csv.writer(sys.stdout)
w.writerow("proband_id chrom_1 pos_1 ref_1 alt_1 chrom_2 pos_2 ref_2 alt_2 epcr finding_type notes".split())
prev = 1.0
for r in rows:
    c1, p1, ref1, alt1, c2, p2, ref2, alt2, epcr, ftype, notes = r
    epcr = float(epcr)
    assert 0 < epcr <= 1 and epcr <= prev + 1e-9, f"epcr not monotone: {epcr}"
    prev = epcr
    assert c1.startswith("chr"), f"chrom_1 must be chr-prefixed: {c1}"
    assert ftype in ("primary", "secondary"), ftype
    pair = ["", "", "", ""] if c2 == "-" else [c2, p2, ref2, alt2]
    if pair[0]: assert pair[0].startswith("chr")
    w.writerow([proband, c1, p1, ref1, alt1, *pair, f"{epcr:.2f}", ftype, notes])
