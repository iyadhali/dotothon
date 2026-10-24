"""Dump text of a PDF page-by-page to a .txt file (inspection helper).

Usage: python -I scripts/edu_pdf_dump.py <pdf> <out_txt> [first_page last_page]
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import pymupdf as fitz

pdf, out = sys.argv[1], sys.argv[2]
d = fitz.open(pdf)
a = int(sys.argv[3]) if len(sys.argv) > 3 else 1
b = int(sys.argv[4]) if len(sys.argv) > 4 else d.page_count
with open(out, "w", encoding="utf-8") as f:
    for i in range(a - 1, min(b, d.page_count)):
        f.write(f"\n===== PAGE {i+1} =====\n")
        f.write(d[i].get_text())
print(d.page_count, "pages ->", out)
