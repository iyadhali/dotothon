"""Join public health facilities from MHS 2020 Table 1-14 (island + category + grade) with
the live MoH HEMS registry (2026 licence level) into one facility master list.

Usage: python -I health_facility_master.py <MHS2020_T1-14.csv> <hems_facilities_tidy.csv> <out.csv>
Match: same atoll code, fuzzy island-name match (difflib ratio >= 0.75) after normalisation.
"""
import csv
import difflib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
mhs_p, hems_p, out_p = sys.argv[1:4]


ALIAS = {"mulah": "mulaku"}


def nm(s):
    s = s.lower().replace("'", "")
    s = ALIAS.get(s, s)
    s = re.sub(r"[^a-z]", "", s)
    return s.replace("dh", "d").replace("th", "t").replace("ee", "i").replace("oo", "u")


TIER = {"Tertiary Hospital": "1_tertiary", "Regional Hospital": "2_regional_hospital",
        "Atoll Hospital": "3_atoll_hospital", "Hospital": "2_hospital_other",
        "Health Center": "4_health_centre", "Dhamanaveshi": "public_health_clinic"}

mhs = list(csv.DictReader(open(mhs_p, encoding="utf-8")))
hems = [h for h in csv.DictReader(open(hems_p, encoding="utf-8")) if h["sector"] == "public"]
used = set()
out = []
for m in mhs:
    cands = [h for h in hems if h["atoll_code"] == m["atoll_code"] and h["establishment_id"] not in used]
    if m["category"] == "Hospital":  # MHS 'Hospital' rows in S/GMR are private/other hospitals
        cands = []
    best, score = None, 0
    for h in cands:
        r = difflib.SequenceMatcher(None, nm(m["island"]), nm(h["island"])).ratio()
        # hospitals: prefer hospital-level licences, health centres: HC licences
        is_hosp = "Hospital" in m["category"]
        if is_hosp != ("Hospital" in h["level"] or "Tertiary" in h["level"]):
            r -= 0.3
        if r > score:
            best, score = h, r
    rec = {"atoll_code": m["atoll_code"], "island": m["island"], "mhs2020_category": m["category"],
           "mhs2020_grade": m["grade"], "tier": TIER.get(m["category"], "other"),
           "hems_establishment_id": "", "hems_name": "", "hems_level_2026": "", "hems_owner": "",
           "match_score": ""}
    if best and score >= 0.75:
        used.add(best["establishment_id"])
        rec.update({"hems_establishment_id": best["establishment_id"], "hems_name": best["name"],
                    "hems_level_2026": best["level"], "hems_owner": best["owner"],
                    "match_score": round(score, 2)})
    out.append(rec)
# HEMS public facilities not in MHS 2020 (new since 2020 or unmatched)
for h in hems:
    if h["establishment_id"] in used:
        continue
    out.append({"atoll_code": h["atoll_code"], "island": h["island"], "mhs2020_category": "",
                "mhs2020_grade": "", "tier": h["tier"], "hems_establishment_id": h["establishment_id"],
                "hems_name": h["name"], "hems_level_2026": h["level"], "hems_owner": h["owner"],
                "match_score": "hems_only"})
with open(out_p, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
n_match = sum(1 for r in out if r["match_score"] not in ("", "hems_only"))
print(f"MHS rows {len(mhs)}, matched {n_match}, MHS-only {sum(1 for r in out if r['match_score']=='')}, "
      f"HEMS-only {sum(1 for r in out if r['match_score']=='hems_only')}")
