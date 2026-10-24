"""Fetch the public HEMS professionals list for every establishment in hems_facilities_tidy.csv
and summarise lab / imaging / pathology staff per establishment.

Usage: python -I diag_fetch_hems_professionals.py <hems_facilities_tidy.csv> <out_dir>
Writes <out_dir>/raw/<id>.json, <out_dir>/hems_professionals_long.csv, <out_dir>/hems_diagnostic_staff_by_facility.csv
"""
import csv
import json
import os
import re
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
src, outdir = sys.argv[1], sys.argv[2]
raw = os.path.join(outdir, "raw")
os.makedirs(raw, exist_ok=True)
facs = list(csv.DictReader(open(src, encoding="utf-8")))

CATS = {
    "lab_tech": r"laborator|phlebotom",
    "pathologist": r"patholog|haematolog|hematolog",
    "microbiologist": r"microbiolog",
    "radiographer": r"radiograph|x-?ray|imaging tech|sonograph|ultrasound|mammograph",
    "radiologist": r"radiolog",
    "transfusion": r"transfusion|blood bank",
    "gastro_endoscopy": r"gastroenterolog|endoscop",
}

long_rows = []
summary = []
for i, f in enumerate(facs):
    eid = f["establishment_id"]
    path = os.path.join(raw, f"{eid}.json")
    if not os.path.exists(path):
        url = f"https://hems.health.gov.mv/establishments/{eid}/professionals"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (datathon research)", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            open(path, "wb").write(data)
        except Exception as e:  # noqa: BLE001
            print("fail", eid, e)
            continue
        time.sleep(0.4)
    try:
        people = json.load(open(path, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        people = []
    counts = {k: 0 for k in CATS}
    titles = {}
    for p in people:
        prof = " / ".join(p.get("professions") or []) or (p.get("profession") or "") or (p.get("speciality_en") or "")
        spec = p.get("speciality_en") or ""
        text = f"{prof} {spec}"
        long_rows.append([eid, f["name"], f["sector"], f["level"], f["atoll_code"], f["island"], p.get("name_en", ""), prof, spec])
        for k, rx in CATS.items():
            if k == "pathologist" and re.search(r"speech|language", text, flags=re.I):
                continue
            if re.search(rx, text, flags=re.I):
                counts[k] += 1
                titles.setdefault(k, set()).add(prof or spec)
    summary.append({
        "establishment_id": eid, "name": f["name"], "status": f["status"], "sector": f["sector"], "level": f["level"],
        "atoll_code": f["atoll_code"], "island": f["island"], "n_professionals": len(people), **counts,
        "diag_titles": "; ".join(sorted({t for s in titles.values() for t in s})),
    })
    if i % 50 == 0:
        print(i, eid, f["name"], len(people))

with open(os.path.join(outdir, "hems_professionals_long.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["establishment_id", "facility", "sector", "level", "atoll_code", "island", "professional", "profession", "speciality"])
    w.writerows(long_rows)
with open(os.path.join(outdir, "hems_diagnostic_staff_by_facility.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
    w.writeheader()
    w.writerows(summary)
print("done", len(summary), "facilities;", len(long_rows), "professional rows")
