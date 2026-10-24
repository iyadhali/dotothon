"""Extract the 'Enrolment in <Atoll> Atoll Islands - as of Nov 2024' tables from the MoE
2024 School Statistics PDF into a tidy island-level CSV (enrolment by grade and sex,
all schools on the island combined).

Usage: python -I scripts/edu_island_enrolment_extract.py <pdf> <out_csv>
"""
import csv
import re
import sys

import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")
pdf_path, out = sys.argv[1], sys.argv[2]

GR = ["BN", "N", "LKG", "UKG"] + [f"GR{i}" for i in range(1, 13)]
COLS = [f"{g}_{s}" for g in GR for s in ("M", "F")]
TITLE = re.compile(r"Enrolment in (.+?)(?: Atoll Islands)?\s*-\s*as of Nov 2024", re.I)
NUM = re.compile(r"^-?\d+$")

rows = []
with pdfplumber.open(pdf_path) as pdf:
    for pno, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        m = TITLE.search(text)
        if not m:
            continue
        atoll = m.group(1).strip()
        for table in page.extract_tables():
            for r in table:
                cells = [(c or "").strip() for c in r]
                if not cells or not cells[0] or cells[0].lower() in ("island", "bn", "m"):
                    continue
                name = cells[0].replace("\n", " ")
                tm = TITLE.search(name)
                if tm:  # a second atoll table starts on the same page
                    atoll = tm.group(1).strip()
                    continue
                vals = cells[1:]
                nums = [v.replace(",", "") for v in vals]
                # expect 32 numeric-ish cells (16 grades x M/F) then subtotal M,F + pct
                if len(nums) < 34:
                    continue
                grade_cells = nums[:32]
                if not all(NUM.match(v) or v in ("", "-") for v in grade_cells):
                    continue
                g = [int(v) if NUM.match(v) else 0 for v in grade_cells]
                sub_m = int(nums[32]) if NUM.match(nums[32]) else 0
                sub_f = int(nums[33]) if NUM.match(nums[33]) else 0
                rtype = "atoll_total" if name.lower().startswith("atoll total") else "island"
                if sum(g) != sub_m + sub_f:
                    print("WARN subtotal mismatch", atoll, name, sum(g), sub_m + sub_f)
                rows.append([atoll, name, rtype] + g + [sub_m, sub_f, sum(g), pno])

with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["atoll", "island", "row_type"] + COLS + ["subtotal_M_pdf", "subtotal_F_pdf", "total_computed", "pdf_page"])
    w.writerows(rows)
print(len(rows), "rows ->", out)
