"""Flatten DHS Program API JSON (Maldives DHS 2016-17) into tidy CSVs.

Usage: python -I health_dhs_tidy.py <dhs_dir>
Reads <dhs_dir>/raw_json/*.json, writes dhs_MV2016_national.csv and dhs_MV2016_subnational.csv
"""
import csv
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = sys.argv[1]
KEEP = ["IndicatorId", "Indicator", "CharacteristicCategory", "CharacteristicLabel", "Value",
        "DenominatorWeighted", "DenominatorUnweighted", "CILow", "CIHigh", "IsPreferred",
        "SurveyYear", "ByVariableLabel"]

for kind in ("national", "subnational"):
    rows = []
    for f in sorted(glob.glob(os.path.join(D, "raw_json", f"dhs_MV2016_{kind}*.json"))):
        rows += json.load(open(f, encoding="utf-8"))["Data"]
    with open(os.path.join(D, f"dhs_MV2016_{kind}.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEEP, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    cats = sorted({r["CharacteristicCategory"] for r in rows})
    print(kind, len(rows), "rows; categories:", cats[:20])
