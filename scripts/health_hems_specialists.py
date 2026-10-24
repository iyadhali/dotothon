"""Aggregate registered professionals by speciality per health establishment from the
MoH HEMS public registry (https://hems.health.gov.mv/establishments/<id>/professionals).

Personal names / registration numbers are DROPPED; only counts per (profession, speciality)
per establishment are kept.

Usage: python -I health_hems_specialists.py <hems_establishments.csv> <OUT_CSV>
"""
import csv
import json
import sys
import time
import urllib.request

BASE = "https://hems.health.gov.mv"
UA = {"User-Agent": "Mozilla/5.0 (datathon research; aggregate counts only)"}


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            print("retry", url, e, file=sys.stderr)
            time.sleep(2 * (i + 1))
    return None


def main():
    src, out = sys.argv[1], sys.argv[2]
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    res = []
    fails = 0
    for k, r in enumerate(rows):
        if r.get("status", "").lower() == "closed":
            continue
        txt = get(f"{BASE}/establishments/{r['establishment_id']}/professionals")
        if txt is None:
            fails += 1
            continue
        try:
            data = json.loads(txt)
        except json.JSONDecodeError:
            fails += 1
            continue
        items = data if isinstance(data, list) else data.get("data", [])
        counts = {}
        for it in items:
            profs = it.get("professions") or [it.get("profession") or ""]
            for p in profs:
                p = str(p).strip()
                counts[p] = counts.get(p, 0) + 1
        for p, c in counts.items():
            res.append({"establishment_id": r["establishment_id"], "name": r["name"],
                        "level": r["level"], "owner": r["owner"], "profession_or_speciality": p,
                        "count": c, "n_people_listed": len(items)})
        if k % 50 == 0:
            print(k, "done", file=sys.stderr)
        time.sleep(0.25)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["establishment_id", "name", "level", "owner",
                                          "profession_or_speciality", "count", "n_people_listed"])
        w.writeheader()
        w.writerows(res)
    print(f"wrote {len(res)} rows; fails={fails}", file=sys.stderr)


if __name__ == "__main__":
    main()
