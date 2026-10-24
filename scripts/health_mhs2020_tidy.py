"""Tidy-up of tables extracted from Maldives Health Statistics 2020 (MoH).

Usage: python -I health_mhs2020_tidy.py <dir containing MHS2020_jjokopyg.pdf and raw CSVs>

Produces (in the same dir):
  MHS2020_T3-14_admissions_by_atoll_sex_group_tidy.csv
  MHS2020_T1-16_workforce_by_atoll_profession_tidy.csv
  MHS2020_T4-8_top20_causes_of_death_GBD.csv
  MHS2020_T4-9_top20_causes_of_death_ICD.csv
"""
import csv
import os
import re
import site
import sys

sys.path.append(site.getusersitepackages())
import fitz  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = sys.argv[1]


def rd(name):
    return list(csv.DictReader(open(os.path.join(D, name), encoding="utf-8")))


def wr(name, rows, fields):
    with open(os.path.join(D, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("wrote", name, len(rows))


ATOLL_FIX = {"Ga": "GA"}

# ---- T3-14 admissions by atoll x sex x GBD main group
cols = ["cmpn_conditions", "ncd", "not_categorized", "ill_defined", "injuries", "not_stated", "total"]
out, atoll = [], None
for r in rd("MHS2020_T3-14_admissions_by_atoll_sex_group.csv"):
    lab = r["label"].strip()
    if lab.startswith("Table"):
        continue
    if lab in ("Male", "Female"):
        sex = lab.lower()
    else:
        atoll, sex = ATOLL_FIX.get(lab, lab), "both"
    rec = {"atoll_code": atoll, "sex": sex}
    rec.update({c: (r[c] or "0") for c in cols})
    out.append(rec)
wr("MHS2020_T3-14_admissions_by_atoll_sex_group_tidy.csv", out, ["atoll_code", "sex"] + cols)

# ---- T1-16 workforce by atoll x profession
cols = ["local_male", "local_female", "expat_male", "expat_female", "total"]
out = []
for r in rd("MHS2020_T1-16_workforce_by_atoll_profession.csv"):
    if r["label"] == r["parent"]:
        prof = "ALL"
    else:
        prof = r["label"]
    rec = {"atoll_code": r["parent"], "profession": prof}
    rec.update({c: (r[c] or "0") for c in cols})
    out.append(rec)
wr("MHS2020_T1-16_workforce_by_atoll_profession_tidy.csv", out, ["atoll_code", "profession"] + cols)

# ---- T4-8 / T4-9 top-20 causes of death (cells look like "Ischaemic heart 102 8% disease")
doc = fitz.open(os.path.join(D, "MHS2020_jjokopyg.pdf"))
CELL = re.compile(r"^(.*?)\s*(\d+)\s+(\d+)%\s*(.*)$")


def parse_cell(c):
    c = re.sub(r"\s+", " ", c or "").strip()
    m = CELL.match(c)
    if not m:
        return None
    return (m.group(1) + " " + m.group(4)).strip(), int(m.group(2)), int(m.group(3))


for pages, fname in (((265, 266), "MHS2020_T4-8_top20_causes_of_death_GBD.csv"),
                     ((267, 268), "MHS2020_T4-9_top20_causes_of_death_ICD.csv")):
    out = []
    for pn in pages:
        for tb in doc[pn - 1].find_tables().tables:
            for row in tb.extract():
                cells = [c for c in row if c not in (None, "")]
                if not cells or not str(cells[0]).strip().isdigit():
                    continue
                rank = int(cells[0])
                parsed = [parse_cell(c) for c in cells[1:]]
                parsed = [p for p in parsed if p]
                for grp, p in zip(("all", "female", "male"), parsed):
                    out.append({"rank": rank, "group": grp, "cause": p[0], "deaths": p[1], "pct": p[2]})
    wr(fname, out, ["rank", "group", "cause", "deaths", "pct"])
