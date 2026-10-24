"""Build the 'visiting / telemedicine / eye-ENT-derm' partial of specialist_services.csv.

Inputs:
  manual_rows.tsv  (hand-curated rows from news / websites, 11 tab-separated columns)
  hems_professionals_by_speciality.csv (aggregated counts from HEMS public registry)
  aasandha_empanelled_local.csv (used to confirm island of each private clinic)

Usage: python -I health_specialist_vte_build.py <manual_rows.tsv> <hems_prof.csv> <out.csv>
"""
import csv
import re
import sys
from collections import defaultdict

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]
HEMS_URL = "https://hems.health.gov.mv/establishments"
HEMS_DATE = "2026-10"

# establishment_id -> (island, atoll, facility_type, scope) ; island confirmed via Aasandha list
# scope 'all' = atoll polyclinic, emit every specialty; 'eed' = eye/ENT/derm only (Greater Male')
SITES = {
    "824": ("Hithadhoo", "S", "private_clinic", "all"),
    "432": ("Feydhoo", "S", "private_polyclinic", "all"),
    "782": ("Hithadhoo", "S", "private_hospital", "all"),
    "1258": ("Hithadhoo", "S", "private_clinic", "all"),
    "90": ("Kulhudhuffushi", "HDh", "private_clinic", "all"),
    "275": ("Kulhudhuffushi", "HDh", "private_polyclinic", "all"),
    "1460": ("Kulhudhuffushi", "HDh", "private_clinic", "all"),
    "869": ("Hanimaadhoo", "HDh", "private_clinic", "all"),
    "164": ("Thinadhoo", "GDh", "private_polyclinic", "all"),
    "235": ("Fuvahmulah", "Gn", "private_clinic", "all"),
    "236": ("Fuvahmulah", "Gn", "private_clinic", "all"),
    "29": ("Funadhoo", "Sh", "private_polyclinic", "all"),
    "434": ("Mahibadhoo", "ADh", "private_clinic", "all"),
    "42": ("Dharavandhoo", "B", "private_clinic", "all"),
    "153": ("Naifaru", "Lh", "private_clinic", "all"),
    "74": ("Naifaru", "Lh", "private_therapy_clinic", "all"),
    "128": ("Meedhoo", "R", "private_clinic", "all"),
    "1392": ("Kulhudhuffushi", "HDh", "specialist_eye_clinic", "all"),
    "1393": ("Gan", "L", "specialist_eye_clinic", "all"),
    "1395": ("Hithadhoo", "S", "specialist_eye_clinic", "all"),
    "397": ("Male'", "MLE", "specialist_eye_clinic", "eed"),
    "471": ("Male'", "MLE", "private_polyclinic", "eed"),
    "294": ("Male'", "MLE", "private_clinic", "eed"),
    "828": ("Male'", "MLE", "private_polyclinic", "eed"),
    "420": ("Hulhumale'", "MLE", "private_hospital", "eed"),
    "809": ("Male'", "MLE", "private_clinic", "eed"),
    "195": ("Hulhumale'", "MLE", "specialist_eye_clinic", "eed"),
    "354": ("Male'", "MLE", "private_clinic", "eed"),
    "760": ("Male'", "MLE", "private_clinic", "eed"),
    "886": ("Hulhumale'", "MLE", "private_clinic", "eed"),
    "92": ("Male'", "MLE", "private_clinic", "eed"),
    "56": ("Male'", "MLE", "specialist_eye_clinic", "eed"),
    "777": ("Male'", "MLE", "private_clinic", "eed"),
    "357": ("Male'", "MLE", "private_clinic", "eed"),
    "201": ("Hulhumale'", "MLE", "private_clinic", "eed"),
    "98": ("Hulhumale'", "MLE", "private_clinic", "eed"),
    "112": ("Hulhumale'", "MLE", "private_clinic", "eed"),
    "814": ("Male'", "MLE", "private_clinic", "eed"),
    "225": ("Male'", "MLE", "private_clinic", "eed"),
    "315": ("Male'", "MLE", "private_clinic", "eed"),
    "887": ("Male'", "MLE", "private_clinic", "eed"),
    "521": ("Male'", "MLE", "private_clinic", "eed"),
    "858": ("Male'", "MLE", "private_clinic", "eed"),
    "72": ("Hulhumale'", "MLE", "private_clinic", "eed"),
    "110": ("Male'", "MLE", "private_clinic", "eed"),
    "932": ("Male'", "MLE", "private_clinic", "eed"),
    "362": ("Hulhumale'", "MLE", "tertiary_hospital", "eed"),
    "522": ("Male'", "MLE", "specialist_eye_clinic", "eed"),
    "345": ("Hulhumale'", "MLE", "specialist_eye_clinic", "eed"),
    "523": ("Male'", "MLE", "private_polyclinic", "eed"),
}

RULES = [  # (regex on profession/speciality, category)
    (r"ophthalm|opthalm", "ophthalmology"),
    (r"optomet", "ophthalmology_optometry"),
    (r"otorhino|otolaryn|\bENT\b", "ent"),
    (r"dermat", "dermatology"),
    (r"cardiolog", "cardiology"),
    (r"paediatric surgeon", "surgery"),
    (r"paediatr|pediatr|neonat", "paediatrics"),
    (r"obstetric|gynaec|gynec", "maternity"),
    (r"orthopa|orthope", "orthopaedics"),
    (r"psychiatr", "psychiatry"),
    (r"psycholog|counsel", "psychiatry"),  # mental health (psychology/counselling merged)
    (r"physiother|occupational therap|speech", "physiotherapy"),
    (r"nephrolog", "nephrology"),
    (r"endocrin|diabet", "ncd_diabetes"),
    (r"rheumat", "rheumatology"),
    (r"gastroenter", "gastroenterology"),
    (r"pulmonolog", "pulmonology"),
    (r"general surgeon|neuro ?surgeon", "surgery"),
]
EED = {"ophthalmology", "ophthalmology_optometry", "ent", "dermatology"}


def classify(p):
    if re.search(r"dent|orthodont|pedodont|prosthodont|maxillofacial|radiolog|radiograph", p, re.I):
        return None
    for rx, cat in RULES:
        if re.search(rx, p, re.I):
            return cat
    return None


def main():
    manual, hems, out = sys.argv[1:4]
    rows = []
    for line in open(manual, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 11:
            rows.append(dict(zip(COLS, parts)))
    agg = defaultdict(lambda: defaultdict(list))
    names = {}
    for r in csv.DictReader(open(hems, encoding="utf-8")):
        eid = r["establishment_id"]
        if eid not in SITES:
            continue
        names[eid] = r["name"]
        cat = classify(r["profession_or_speciality"])
        if cat:
            agg[eid][cat].append(f"{r['profession_or_speciality']} x{r['count']}")
    for eid, cats in agg.items():
        island, atoll, ftype, scope = SITES[eid]
        has_oph = "ophthalmology" in cats
        for cat, profs in cats.items():
            if scope == "eed" and cat not in EED:
                continue
            if cat == "ophthalmology_optometry":
                if has_oph:
                    continue
                cat_out, det = "ophthalmology", "optometry only (no ophthalmologist registered): "
            else:
                cat_out, det = cat, "specialist(s) registered: "
            note = "" if atoll == "MLE" else "; atoll private clinic - specialists may visit periodically from Male'"
            rows.append({
                "facility_name": names[eid], "operator_type": "private", "facility_type": ftype,
                "island": island, "atoll": atoll, "service_category": cat_out,
                "service_detail": det + "; ".join(profs) + note,
                "evidence": "HEMS public registry: practising professionals listed for establishment "
                            f"{eid} (aggregated counts); island per Aasandha empanelled list",
                "source_url": f"{HEMS_URL}/{eid}/professionals", "source_date": HEMS_DATE,
                "confidence": "high" if cat != "ophthalmology_optometry" else "medium"})
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "rows ->", out, file=sys.stderr)


if __name__ == "__main__":
    main()
