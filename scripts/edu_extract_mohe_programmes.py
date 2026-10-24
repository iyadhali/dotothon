"""Extract "Locally Available Higher Education Programmes as of 2025" (MoHE) into a tidy CSV.

Uses PyMuPDF table detection for row/cell boxes and re-assigns page words to cells
(the default table extractor drops spaces in this PDF).

Writes  <pdf_dir>/locally_available_programmes_2025.csv  and a per-institution summary
<pdf_dir>/locally_available_programmes_2025_by_institution.csv

Usage: python -I scripts/edu_extract_mohe_programmes.py <pdf>
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf

sys.stdout.reconfigure(encoding="utf-8")


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def main():
    pdf = Path(sys.argv[1])
    d = pymupdf.open(pdf)
    out = []
    for page in d:
        words = page.get_text("words")

        def cell_text(c):
            x0, y0, x1, y1 = c
            ws = [w for w in words if x0 <= (w[0] + w[2]) / 2 <= x1 and y0 <= (w[1] + w[3]) / 2 <= y1]
            ws.sort(key=lambda w: (w[5], w[6], w[7]))
            return clean(" ".join(w[4] for w in ws))

        for t in page.find_tables().tables:
            for row in t.rows:
                cells = [cell_text(c) if c else "" for c in row.cells]
                if len(cells) < 4 or not re.fullmatch(r"\d+", cells[0]):
                    continue
                m = re.search(r"(\d+)", cells[3])
                out.append(dict(seq=int(cells[0]), institution=cells[1], programme=cells[2],
                                mnqf_level=int(m.group(1)) if m else None, page=page.number + 1))
    src = ("https://mohe.gov.mv/images/resources/resources/Locally%20Available%20Programmes%20as%20of%202025.pdf")
    for r in out:
        r["source_url"] = src
    f = pdf.parent / "locally_available_programmes_2025.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    by = defaultdict(Counter)
    for r in out:
        by[r["institution"]][r["mnqf_level"]] += 1
    rows = []
    for inst, c in sorted(by.items(), key=lambda kv: -sum(kv[1].values())):
        levels = sorted(k for k in c if k is not None)
        rows.append(dict(institution=inst, n_programmes=sum(c.values()),
                         mnqf_levels=";".join(str(x) for x in levels),
                         min_level=min(levels) if levels else None, max_level=max(levels) if levels else None,
                         source_url=src))
    f2 = pdf.parent / "locally_available_programmes_2025_by_institution.csv"
    with open(f2, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    seqs = [r["seq"] for r in out]
    print(f"{len(out)} programmes; seq {min(seqs)}..{max(seqs)}; missing seq: "
          f"{sorted(set(range(1, max(seqs) + 1)) - set(seqs))[:20]}")
    for r in rows:
        print(r["institution"], r["n_programmes"], r["mnqf_levels"])


if __name__ == "__main__":
    main()
