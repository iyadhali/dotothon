"""Build an atoll-level health supply/utilisation summary from the downloaded sources.

Usage: python -I health_build_atoll_summary.py <health_root> <out_dir>

health_root = C:/Users/user/Music/Datathon/data/external/health
Outputs (out_dir):
  health_atoll_summary.csv           one row per atoll (+ Male' / Greater Male' where available)
  mbs_T6-3_2021yb_hospital_beds_2020_tidy.csv   facility-tier rows of beds/OP/IP 2020 (columns fixed)
  mbs_T18-28_aasandha_evac_by_atoll_2023_tidy.csv
  mbs_T6-3_2026yb_outpatients_by_atoll_tidy.csv
  mbs_T18-25_aasandha_expenditure_by_atoll_tidy.csv
"""
import csv
import os
import re
import site
import sys
from collections import defaultdict

sys.path.append(site.getusersitepackages())
import openpyxl  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
ATOLLS = ["HA", "HDh", "Sh", "N", "R", "B", "Lh", "K", "AA", "ADh", "V", "M", "F", "Dh", "Th", "L",
          "GA", "GDh", "Gn", "S"]
NORM = {a.upper().replace(" ", ""): a for a in ATOLLS}


def norm(code):
    if code is None:
        return None
    c = str(code).strip()
    m = re.search(r"\(([A-Za-z]{1,3})\)", c)  # "North Thiladhunmathi (HA)"
    if m:
        c = m.group(1)
    c = c.replace(" ", "").replace(".", "").upper()
    return NORM.get(c)


def rows_of(path, sheet=None):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    return [list(r) for r in ws.iter_rows(values_only=True)]


def wr(name, rows, fields):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("wrote", name, len(rows))


S = defaultdict(dict)
MBS = os.path.join(ROOT, "mbs_statistical_yearbook")

# --- population 2022 (census, resident incl. foreigners) + HR per 10k 2023 (MoH HR data)
hr = rows_of(os.path.join(ROOT, "moh_statistics_publications", "Human_resources_data_2022_and_2023__5dvltwmw.xlsx"),
             "Indicators")
start = next(i for i, r in enumerate(hr) if r[0] and str(r[0]).startswith("Table 1.0.2"))
hdr = hr[start + 1]
grp = []
cur = None
for c in hdr:
    cur = c if c else cur
    grp.append(cur)
for r in hr[start + 3:]:
    a = norm(r[0])
    if not a:
        if r[0] and str(r[0]).startswith("*"):
            break
        continue
    S[a]["pop2022_resident"] = r[1]
    for j, g in enumerate(grp):
        if g and "per 10,000" in str(g) and hr[start + 2][j] == "Both Sexes":
            key = "hr2023_" + re.sub(r"[^a-z]+", "_", str(g).lower().replace(" per 10,000 population", "")).strip("_") + "_per10k"
            S[a][key] = round(float(r[j]), 1) if r[j] is not None else None
S["Male'"]["pop2022_resident"] = 211908

# --- MBS 2021 yearbook Table 6.3: beds & flows by govt hospital tier, 2020
# NOTE: in the source the column headers 'Inpatient' and 'Outpatient' are swapped
# (values under 'Inpatient' are clearly outpatient visits); we relabel them here.
t = rows_of(os.path.join(MBS, "yb2021", "6.3.xlsx"))
tidy, atoll = [], None
for r in t:
    if not r or r[2] is None or r[1] is None and r[0] is None:
        continue
    lab = str(r[0]).strip() if r[0] else None
    if lab in ("TOTAL", "Location", "MALE'", "ATOLLS"):
        continue
    if lab:
        atoll = norm(lab) or ("Male'" if r[1] in ("Tertiary", "Hospital", "Public Health") else lab)
    if not isinstance(r[2], (int, float)):
        continue
    beds = r[4] if isinstance(r[4], (int, float)) else None
    ip = r[3] if isinstance(r[3], (int, float)) else None
    name = lab if (lab and not norm(lab)) else ""
    tidy.append({"location": atoll, "facility": name, "category": r[1], "outpatients_2020": r[2],
                 "inpatients_2020": ip, "inpatient_beds_2020": beds})
wr("mbs_T6-3_2021yb_hospital_beds_2020_tidy.csv", tidy,
   ["location", "facility", "category", "outpatients_2020", "inpatients_2020", "inpatient_beds_2020"])
for x in tidy:
    a = x["location"] if x["location"] in ATOLLS else "Male'"
    for k in ("inpatient_beds_2020", "inpatients_2020", "outpatients_2020"):
        if x[k]:
            S[a][k] = S[a].get(k, 0) + x[k]
    if x["category"] in ("Atoll Hospital", "Regional Hospital", "Tertiary*", "Hospital **", "Tertiary", "Hospital"):
        S[a]["hospital_beds_2020"] = S[a].get("hospital_beds_2020", 0) + (x["inpatient_beds_2020"] or 0)
        rank = {"Tertiary": 3, "Regional Hospital": 2, "Hospital": 1, "Atoll Hospital": 1}
        cat = x["category"].strip("* ") if a != "Male'" else "Tertiary"
        if rank.get(cat, 0) >= rank.get(S[a].get("top_tier_2020", ""), -1):
            S[a]["top_tier_2020"] = cat

# --- MBS 2026 yearbook Table 6.3: outpatient visits by atoll 2022-2023
t = rows_of(os.path.join(MBS, "yb2026", "6.3.xlsx"))
tidy = []
for r in t:
    a = norm(r[0]) or ("Male'" if r[0] and str(r[0]).startswith("Male") else None)
    if a and isinstance(r[1], (int, float)):
        tidy.append({"atoll": a, "op_2022_total": r[1], "op_2022_male": r[2], "op_2022_female": r[3],
                     "op_2023_total": r[4], "op_2023_male": r[5], "op_2023_female": r[6]})
        S[a]["op_visits_2023"] = r[4]
wr("mbs_T6-3_2026yb_outpatients_by_atoll_tidy.csv", tidy, list(tidy[0].keys()))

# --- MBS 2025 yearbook Table 18.28: emergency evacuations etc. by atoll 2023 (Aasandha)
t = rows_of(os.path.join(MBS, "yb2025", "18.28.xlsx"))
tidy = []
for r in t:
    a = norm(r[0]) or ("Male'" if r[0] and str(r[0]).strip() == "Male'" else None)
    if a and r[1] is not None:
        def num(v):
            return v if isinstance(v, (int, float)) else None
        tidy.append({"atoll": a, "emergency_evacuations_2023": num(r[1]),
                     "empaneled_hospitals_clinics_2023": num(r[3]), "empaneled_pharmacies_2023": num(r[4])})
        S[a]["emergency_evacuations_2023"] = num(r[1])
        S[a]["aasandha_empaneled_facilities_2023"] = num(r[3])
wr("mbs_T18-28_aasandha_evac_by_atoll_2023_tidy.csv", tidy, list(tidy[0].keys()))

# --- MBS 2026 yearbook Table 18.25: Aasandha expenditure by atoll 2014-2025 (MVR)
t = rows_of(os.path.join(MBS, "yb2026", "18.25.xlsx"))
years = None
tidy = []
for r in t:
    if r[1] == 2014 or r[1] == "2014":
        years = [int(y) for y in r[1:13]]
        continue
    if years is None:
        continue
    a = norm(r[0]) or ("Male'" if r[0] and str(r[0]).strip() == "Male'" else None)
    if a:
        for y, v in zip(years, r[1:13]):
            if isinstance(v, (int, float)):
                tidy.append({"atoll": a, "year": y, "aasandha_expenditure_mvr": round(v)})
        S[a]["aasandha_exp_2025_mvr"] = round(r[12]) if isinstance(r[12], (int, float)) else None
wr("mbs_T18-25_aasandha_expenditure_by_atoll_tidy.csv", tidy, ["atoll", "year", "aasandha_expenditure_mvr"])

# --- facility counts by atoll (MHS 2020 Table 1-14; public facilities with grade)
fac = list(csv.DictReader(open(os.path.join(ROOT, "moh_maldives_health_statistics",
                                            "MHS2020_T1-14_public_facilities_by_island.csv"), encoding="utf-8")))
for f in fac:
    a = f["atoll_code"] if f["atoll_code"] in ATOLLS else "Male'"
    k = "n_health_centres_2020" if f["category"] == "Health Center" else "n_hospitals_2020"
    S[a][k] = S[a].get(k, 0) + 1

# --- admissions 2020 by atoll (MHS 2020 Table 3-14)
for r in csv.DictReader(open(os.path.join(ROOT, "moh_maldives_health_statistics",
                                          "MHS2020_T3-14_admissions_by_atoll_sex_group_tidy.csv"), encoding="utf-8")):
    if r["sex"] != "both":
        continue
    a = "Male'" if r["atoll_code"] == "GMR" else norm(r["atoll_code"])
    if a:
        S[a]["admissions_2020_mhs"] = int(r["total"])

# --- derived ratios
for a, d in S.items():
    p = d.get("pop2022_resident")
    if p:
        if d.get("inpatient_beds_2020"):
            d["inpatient_beds_per_1000"] = round(1000 * d["inpatient_beds_2020"] / p, 2)
        if d.get("op_visits_2023"):
            d["op_visits_per_capita_2023"] = round(d["op_visits_2023"] / p, 2)
        if d.get("emergency_evacuations_2023") is not None:
            d["evacuations_per_1000_2023"] = round(1000 * d["emergency_evacuations_2023"] / p, 2)
        if d.get("aasandha_exp_2025_mvr"):
            d["aasandha_exp_per_capita_2025_mvr"] = round(d["aasandha_exp_2025_mvr"] / p)

fields = ["atoll", "pop2022_resident", "top_tier_2020", "n_hospitals_2020", "n_health_centres_2020",
          "inpatient_beds_2020", "hospital_beds_2020", "inpatient_beds_per_1000", "outpatients_2020",
          "inpatients_2020", "admissions_2020_mhs", "op_visits_2023", "op_visits_per_capita_2023",
          "emergency_evacuations_2023", "evacuations_per_1000_2023", "aasandha_empaneled_facilities_2023",
          "aasandha_exp_2025_mvr", "aasandha_exp_per_capita_2025_mvr"]
extra = sorted({k for d in S.values() for k in d if k.startswith("hr2023_")})
out = []
for a in ["Male'"] + ATOLLS:
    d = dict(S.get(a, {}))
    d["atoll"] = a
    out.append({k: d.get(k, "") for k in fields + extra})
wr("health_atoll_summary.csv", out, fields + extra)
