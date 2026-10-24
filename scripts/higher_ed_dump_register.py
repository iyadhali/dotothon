"""Print the text of the MoHE 'Register of Higher Education and Training Institutions' PDF
with Thaana script stripped (inspection helper).

Usage: python -I scripts/higher_ed_dump_register.py <pdf> <out_txt>
"""
import re
import sys

import pymupdf as fitz

sys.stdout.reconfigure(encoding="utf-8")
pdf, out = sys.argv[1], sys.argv[2]
d = fitz.open(pdf)
with open(out, "w", encoding="utf-8") as f:
    for i, page in enumerate(d):
        f.write(f"\n===== PAGE {i+1} =====\n")
        t = re.sub(r"[ހ-޿،]+", "", page.get_text())
        for line in t.splitlines():
            if line.strip():
                f.write(line.strip() + "\n")
print(d.page_count, "pages ->", out)
