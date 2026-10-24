"""Tidy MBS Statistical Yearbook 2025 tables:
  1.5   population, land area, density, distance to Male' by inhabited island (Census 2022 based)
  10.14 resort list (resort, island, atoll, opening year, beds, distance to airport)
  10.15 tourist establishments (resorts/hotels/guesthouses) by island, Dec 2024
Usage: python -I yearbook_tidy.py <yearbook_dir> <out_dir>
"""
import re
import sys
from pathlib import Path

import openpyxl
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

ABBR_RE = re.compile(r"\(([A-Za-z. ]+)\)\s*$")


def atoll_from_header(s):
    m = ABBR_RE.search(str(s))
    return m.group(1).replace(".", "").replace(" ", "") if m else None


def rows(path):
    return list(openpyxl.load_workbook(path, read_only=True, data_only=True).active.iter_rows(values_only=True))


# ---- 1.5
out, atoll, atoll_name = [], "MLE", "Male' City"
for r in rows(SRC / "yb_1.5.xlsx")[5:]:
    r = list(r[:9]) + [None] * max(0, 9 - len(r))
    name = r[1]
    if name and r[2] is None and isinstance(name, str) and "(" in name:
        atoll, atoll_name = atoll_from_header(name), name.strip()
        continue
    if name and isinstance(r[2], (int, float)):
        nm = str(name).strip()
        out.append({"atoll_abbr": atoll, "atoll_header": atoll_name,
                    "island": nm.replace("*", "").strip(), "is_atoll_capital": "*" in nm,
                    "land_area_ha": r[2], "pop2022": r[3], "pop2022_mdv": r[4],
                    "density_per_ha": r[5], "dist_to_male_km": r[7]})
t15 = pd.DataFrame(out)
t15.to_csv(OUT / "yb2025_t1.5_island_area_pop_distance.csv", index=False, encoding="utf-8")
print("1.5 rows:", len(t15), " pop sum:", t15.pop2022.sum())

# ---- 10.14
out, atoll = [], None
R14 = rows(SRC / "yb_10.14.xlsx")
hdr = R14[4]
year_cols = {v: i for i, v in enumerate(hdr) if isinstance(v, int) and 2000 < v < 2100}
LAST_YEAR = max(year_cols)
for r in R14[5:]:
    if r[0] is None and r[1] and isinstance(r[1], str) and "Atoll" in r[1] and r[2] in (None, "-"):
        atoll = r[1].strip()
        continue
    if isinstance(r[0], (int, float)) and r[1]:
        isl = str(r[2] or "").strip()
        island = re.split(r"\.\s*", isl)[-1].strip() if "." in isl else isl
        prefix = isl[: len(isl) - len(island)].replace(".", "").replace(" ", "") if "." in isl else None
        out.append({"atoll_header": atoll, "atoll_abbr": prefix or atoll_from_header(atoll),
                    "resort": str(r[1]).strip(), "island_raw": isl,
                    "island": island,
                    "year_opened": r[3], "initial_beds": r[4], "dist_airport_km": r[5],
                    f"beds_{LAST_YEAR}": r[year_cols[LAST_YEAR]],
                    "operating_in_latest_year": bool(r[year_cols[LAST_YEAR]])})
t14 = pd.DataFrame(out)
t14.to_csv(OUT / "yb2025_t10.14_resorts.csv", index=False, encoding="utf-8")
print("10.14 resorts:", len(t14))

# ---- 10.15
out, atoll = [], None
for r in rows(SRC / "yb_10.15.xlsx")[5:]:
    if not r[0]:
        continue
    nm = str(r[0]).strip()
    if nm.startswith("Total") or nm.startswith("Greater Male"):
        atoll = "MLE" if nm.startswith("Greater") else atoll
        continue
    if ABBR_RE.search(nm):
        atoll = atoll_from_header(nm)
        continue
    def num(v):
        return None if v in ("-", None, "") else v
    out.append({"atoll_abbr": atoll, "island": nm, "resorts_n": num(r[1]), "resorts_beds": num(r[2]),
                "hotels_n": num(r[3]), "hotels_beds": num(r[4]), "guesthouses_n": num(r[5]), "guesthouses_beds": num(r[6])})
t1015 = pd.DataFrame(out)
t1015.to_csv(OUT / "yb2025_t10.15_tourist_establishments_by_island.csv", index=False, encoding="utf-8")
print("10.15 rows:", len(t1015))
