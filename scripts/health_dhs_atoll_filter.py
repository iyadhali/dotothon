"""Filter coordinate-extracted MDHS tables to the atoll breakdown rows.

Usage: python -I health_dhs_atoll_filter.py <raw.csv> <out.csv>
Keeps rows whose label ends with 'Atoll' plus the 'Malé' region row and 'Total'.
"""
import csv
import sys

src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding="utf-8")))
keep = []
seen_male = False
for r in rows:
    lab = r["label"].strip()
    if lab.endswith("Atoll"):
        r["atoll_code"] = lab.replace(" Atoll", "")
        keep.append(r)
    elif lab == "Total":
        r["atoll_code"] = "Total"
        keep.append(r)
fields = ["atoll_code"] + [k for k in rows[0].keys() if k not in ("page", "parent", "indent", "label")]
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(keep)
print("wrote", len(keep), "rows")
