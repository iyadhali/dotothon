"""Extract atoll-level summary tables from MoE School Statistics 2024 (pages 12, 13, 38).

Writes next to the PDF:
  ..._atoll_enrolment_by_sector.csv     (p12: schools & students by sector and sex)
  ..._atoll_schools_teachers.csv        (p38: schools by size, students, teachers local/expat)

Usage: python -I scripts/edu_extract_school_stats_atoll.py <pdf>
"""
import csv
import re
import sys
from pathlib import Path

import pymupdf

NAMES = {
    "GreaterMal": "Greater Male Region", "HaaAlifu": "Haa Alifu", "HaaDhaalu": "Haa Dhaalu",
    "AlifuAlifu": "Alifu Alifu", "AlifuDhaalu": "Alifu Dhaalu", "GaafuAlifu": "Gaafu Alifu",
    "GaafuDhaalu": "Gaafu Dhaalu", "AtollsTotal": "Atolls Total", "NationwideTotal": "Nationwide Total",
}


def clean_name(s):
    s = (s or "").strip()
    for k, v in NAMES.items():
        if s.startswith(k):
            return v
    return s


def n(s):
    s = re.sub(r"[^\d]", "", s or "")
    return int(s) if s else 0


def table(page):
    return page.find_tables().tables[0].extract()


def main():
    pdf = Path(sys.argv[1])
    d = pymupdf.open(pdf)
    stem = pdf.stem.replace(" ", "_")
    src = "https://www.moe.gov.mv/storage/files/statistics/1782980847582-2024%20School%20Statistics.pdf"

    rows = table(d[11])
    out = []
    for r in rows[3:]:
        if not r[0]:
            continue
        out.append(dict(year=2024, locality=clean_name(r[0]),
                        govt_schools=n(r[1]), govt_male=n(r[2]), govt_female=n(r[3]),
                        community_schools=n(r[4]), community_male=n(r[5]), community_female=n(r[6]),
                        private_schools=n(r[7]), private_male=n(r[8]), private_female=n(r[9]),
                        total_schools=n(r[10]), total_male=n(r[11]), total_female=n(r[12]),
                        total_students=n(r[13]), source_url=src + "#page=12"))
    f1 = pdf.parent / f"{stem}_atoll_enrolment_by_sector.csv"
    with open(f1, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)

    rows = table(d[37])
    out = []
    for r in rows[4:]:
        if not r[0]:
            continue
        out.append(dict(year=2024, locality=clean_name(r[0]),
                        schools_enrol_lt500=n(r[1]), schools_enrol_ge500=n(r[2]), schools_total=n(r[3]),
                        students_male=n(r[4]), students_female=n(r[5]), students_total=n(r[6]),
                        teachers_local_male=n(r[7]), teachers_local_female=n(r[8]),
                        teachers_expat_male=n(r[9]), teachers_expat_female=n(r[10]),
                        teachers_total=n(r[11]), source_url=src + "#page=38"))
    for o in out:
        o["pupil_teacher_ratio"] = round(o["students_total"] / o["teachers_total"], 2) if o["teachers_total"] else None
    f2 = pdf.parent / f"{stem}_atoll_schools_teachers.csv"
    with open(f2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader(); w.writerows(out)
    print("wrote", f1, f2)


if __name__ == "__main__":
    main()
