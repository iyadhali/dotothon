"""Extract MHS 2020 Table 1-14 (public health facilities by island, category and grade)
using word coordinates (the grade is encoded only by which column holds the '1').

Usage: python -I health_mhs2020_facilities.py <MHS2020.pdf> <first_page> <last_page> <out.csv>
"""
import csv
import site
import sys
from collections import defaultdict

sys.path.append(site.getusersitepackages())
import fitz  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    pdf, p1, p2, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    doc = fitz.open(pdf)
    rows = []
    for pn in range(p1, p2 + 1):
        words = doc[pn - 1].get_text("words")
        lines = defaultdict(list)
        for w in words:
            lines[round(w[1])].append(w)
        hdr = None
        for y in sorted(lines):
            ws = sorted(lines[y], key=lambda w: w[0])
            txt = [w[4] for w in ws]
            if "Location" in txt and "Island" in txt and "Category" in txt:
                # x centres of grade columns 1..4, 'No Grade', 'Total'
                cols = {}
                for w in ws:
                    if w[4] in ("1", "2", "3", "4"):
                        cols[w[4]] = (w[0] + w[2]) / 2
                    elif w[4] == "No":
                        cols["none"] = (w[0] + w[2]) / 2 + 10
                    elif w[4] == "Total":
                        cols["total"] = (w[0] + w[2]) / 2
                hdr = cols
                continue
            if hdr is None or len(ws) < 3:
                continue
            if ws[0][0] > 110:  # rows start with the atoll code at the left margin
                continue
            atoll = ws[0][4]
            island = " ".join(w[4] for w in ws if 110 <= w[0] < 220)
            cat = " ".join(w[4] for w in ws if 220 <= w[0] < 330)
            nums = [w for w in ws if w[0] >= 330]
            grade = ""
            for w in nums:
                xc = (w[0] + w[2]) / 2
                key = min(hdr, key=lambda k: abs(hdr[k] - xc))
                if key != "total":
                    grade = key
            if not island or not cat:
                continue
            rows.append({"page": pn, "atoll_code": atoll, "island": island, "category": cat,
                         "grade": grade})
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["page", "atoll_code", "island", "category", "grade"])
        w.writeheader()
        w.writerows(rows)
    print("wrote", len(rows), "facilities")


if __name__ == "__main__":
    main()
