"""Island-level education supply summary (for accessibility destinations).

Combines:
  * MoE School Statistics 2024 island x grade enrolment (highest grade enrolled on island,
    whether grades 11-12 / higher secondary are available on the island);
  * registered HEI / TVET campuses per island (register Oct 2026), split into full campuses and
    outreach centres, plus the list of institutions present.
Greater Male' Region islands are not in the 2024 island tables; they are added from the register
only (Male' City has full provision incl. higher secondary).

Output: data/external/education/island_education_supply.csv

Usage: python -I scripts/edu_island_supply.py
"""
import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

E = Path(r"C:\Users\user\Music\Datathon\data\external\education")


ALIAS = {"fuvahmulah": "fuvamulah", "uligamu": "uligan", "hoadedho": "hoandedho",
         "maradhofeydho": "maradho"}


def key(atoll, island):
    s = unicodedata.normalize("NFKD", island or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z]", "", s)
    s = s.replace("dhdh", "ddh").replace("hdh", "dh").replace("ngili", "gili").replace("ee", "i").replace("nm", "mm")
    s = re.sub(r"(.)\1+", r"\1", s)  # collapse doubled letters (aa, ll, vv ...)
    s = ALIAS.get(s, s)
    return (atoll or "").lower(), s


def read(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    ss = read(E / "moe_school_statistics" / "1782980847582-2024_School_Statistics_island_enrolment_by_grade_wide.csv")
    reg = read(E / "moe_registered_colleges" / "registered_hei_campuses_2026.csv")
    hei = defaultdict(lambda: {"campus": set(), "outreach": set(), "inst": set()})
    names = {}
    for r in reg:
        if r["location_stated"] != "True" or not r["island"]:
            continue
        atoll = "Male' City" if r["island"] in ("Male'", "Hulhumale'", "Villimale'") else r["atoll"]
        k = key(atoll, r["island"])
        names[k] = (atoll, r["island"])
        bucket = "outreach" if r["campus_type"] in ("outreach centre", "quran centre (gofi)") else "campus"
        hei[k][bucket].add(r["institution"] + " - " + r["campus"])
        hei[k]["inst"].add(r["institution"])
    rows, done = [], set()
    for s in ss:
        if s["is_atoll_total"] == "True":
            continue
        k = key(s["atoll"], s["island"])
        done.add(k)
        h = hei.get(k)
        rows.append(dict(atoll=s["atoll"], island=s["island"], school_enrolment_2024=s["total"],
                         highest_grade_enrolled_2024=s["highest_grade_enrolled"],
                         grade_9_10_enrolment=s["grade_9_10_enrolment"],
                         grade_11_12_enrolment=s["grade_11_12_enrolment"],
                         higher_secondary_on_island=s["has_higher_secondary"],
                         hei_campuses=len(h["campus"]) if h else 0,
                         hei_outreach_centres=len(h["outreach"]) if h else 0,
                         hei_institutions="; ".join(sorted(h["inst"])) if h else "",
                         source="MoE School Statistics 2024 (p22-37) + HEI register Oct 2026"))
    for k, h in hei.items():
        if k in done:
            continue
        atoll, island = names[k]
        rows.append(dict(atoll=atoll, island=island, school_enrolment_2024="",
                         highest_grade_enrolled_2024="GR12" if atoll == "Male' City" else "",
                         grade_9_10_enrolment="", grade_11_12_enrolment="",
                         higher_secondary_on_island=True if atoll == "Male' City" else "",
                         hei_campuses=len(h["campus"]), hei_outreach_centres=len(h["outreach"]),
                         hei_institutions="; ".join(sorted(h["inst"])),
                         source="HEI register Oct 2026 (island not matched to 2024 school island table)"))
    f = E / "island_education_supply.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    unmatched = [r["atoll"] + "/" + r["island"] for r in rows if "not matched" in r["source"]]
    print(f, len(rows), "rows; HEI islands not matched to school table:", unmatched)


if __name__ == "__main__":
    main()
