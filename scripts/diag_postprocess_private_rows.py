"""Post-process private_labs/rows.csv: fill unspecified islands (Greater Male' assumption, low confidence) and drop spurious HEMS-derived rows. Usage: python -I diag_postprocess_private_rows.py rows.csv"""
import csv, sys
p = sys.argv[1]
r = list(csv.DictReader(open(p, encoding="utf-8")))
DROP = ("MIOT", "Recovery Room", "Dhoonidhoo", "JIRAA", "CHARM", "CareOne")
out = []
for x in r:
    if any(d.lower() in x["facility_name"].lower() for d in DROP) and x["evidence"].startswith("HEMS professionals"):
        continue
    if not x["island"]:
        x["island"] = "Male/Hulhumale (island not stated in HEMS)"
        x["atoll"] = "K"
        x["confidence"] = "low"
        x["service_detail"] += " [island assumed Greater Male'; verify]"
    out.append(x)
with open(p, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(r[0].keys())); w.writeheader(); w.writerows(out)
print(len(out))
