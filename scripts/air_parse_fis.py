"""Parse Velana FIS (fis.com.mv) flight records from:
  - live API JSON dumps   (velana_fis/flights_*.json)
  - Next.js HTML pages    (velana_fis/*.html, velana_fis/wayback/*.html) with embedded flight JSON
Writes a de-duplicated CSV of domestic flight legs observed at MLE.

Usage: python -I air_parse_fis.py <velana_fis_dir> <out_csv>
"""
import csv
import glob
import json
import os
import re
import sys

src, out = sys.argv[1], sys.argv[2]
KEYS = ["id", "flightNumber", "airline", "airlineCode", "origin", "originCode",
        "destination", "destinationCode", "scheduledTime", "estimatedTime", "status",
        "type", "category", "date", "viaRoutes"]

recs = {}


def add(f, srcfile):
    if not isinstance(f, dict) or "flightNumber" not in f:
        return
    k = (f.get("date"), f.get("type"), f.get("flightNumber"), f.get("scheduledTime"))
    r = {kk: f.get(kk) for kk in KEYS}
    r["viaRoutes"] = "|".join(f.get("viaRoutes") or []) if isinstance(f.get("viaRoutes"), list) else ""
    r["source_file"] = os.path.basename(srcfile)
    recs.setdefault(k, r)


for p in glob.glob(os.path.join(src, "**", "*.json"), recursive=True):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    for f in d.get("flights", []):
        add(f, p)

obj_re = re.compile(r'\{\\?"id\\?":\\?"(?:arrival|departure)-.*?\\?"date\\?":\\?"\d{4}-\d{2}-\d{2}\\?"[^{}]*\}')
for p in glob.glob(os.path.join(src, "**", "*.html"), recursive=True):
    t = open(p, encoding="utf-8", errors="ignore").read()
    for m in obj_re.finditer(t):
        s = m.group(0).replace('\\"', '"').replace('"$undefined"', 'null')
        try:
            add(json.loads(s), p)
        except Exception:
            pass

rows = sorted(recs.values(), key=lambda r: (r["date"] or "", r["scheduledTime"] or "", r["flightNumber"]))
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=KEYS + ["source_file"])
    w.writeheader()
    w.writerows(rows)
dom = [r for r in rows if r["category"] == "domestic"]
print(f"{len(rows)} flights, {len(dom)} domestic; dates:",
      sorted({r['date'] for r in dom}))
