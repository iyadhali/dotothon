"""Pull per-facility professional listings from the MoH HEMS public registry and keep
ONLY aggregated profession counts (no personal names / registration numbers are stored).

Input : data/external/health/moh_hems_registry/hems_facilities_tidy.csv (existing scrape)
Output: <OUT_DIR>/hems_profession_counts_all.csv   (establishment x profession -> count)
        <OUT_DIR>/hems_dental_counts.csv           (establishments with any dental professional)

Usage: python -I dental_hems_professionals.py <HEMS_TIDY_CSV> <OUT_DIR>
"""
import csv
import json
import os
import sys
import time
import urllib.request

BASE = "https://hems.health.gov.mv"
UA = {"User-Agent": "Mozilla/5.0 (datathon research; contact see project README)"}
DENTAL_KEYS = ("dent", "orthodon", "oral", "maxillo", "periodon", "endodon", "prosthodon",
               "pedodon", "paedodon")


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            print("retry", url, e, file=sys.stderr)
            time.sleep(2 + 3 * i)
    return "[]"


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    fac = list(csv.DictReader(open(src, encoding="utf-8")))
    allrows = []
    for k, r in enumerate(fac):
        eid = r["establishment_id"]
        try:
            items = json.loads(get(f"{BASE}/establishments/{eid}/professionals"))
        except json.JSONDecodeError:
            items = []
        if isinstance(items, dict):
            items = items.get("data", [])
        counts = {}
        for it in items:
            profs = it.get("professions") or ([it.get("profession")] if it.get("profession") else [])
            if not profs:
                profs = [it.get("speciality_en") or "unknown"]
            for p in profs:
                counts[p] = counts.get(p, 0) + 1
        for p, c in counts.items():
            allrows.append({"establishment_id": eid, "name": r["name"], "status": r["status"],
                            "sector": r["sector"], "level": r["level"], "atoll_code": r["atoll_code"],
                            "island": r["island"], "contact": r["contact"], "profession": p,
                            "count": c, "n_listed_total": len(items)})
        if k % 25 == 0:
            print(f"{k}/{len(fac)}", file=sys.stderr)
        time.sleep(0.25)
    keys = ["establishment_id", "name", "status", "sector", "level", "atoll_code", "island",
            "contact", "profession", "count", "n_listed_total"]
    with open(os.path.join(out, "hems_profession_counts_all.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(allrows)
    dental = [x for x in allrows if any(d in x["profession"].lower() for d in DENTAL_KEYS)]
    with open(os.path.join(out, "hems_dental_counts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(dental)
    print(f"wrote {len(allrows)} rows; dental rows {len(dental)}", file=sys.stderr)


if __name__ == "__main__":
    main()
