"""Parse the MoH Quality Assurance 'private health facilities' registry PDF (name, reg no,
licence, issued date, address, contact) into CSV.

Usage: python -I dental_parse_private_registry.py <PDF> <OUT_CSV>
"""
import csv
import re
import site
import sys

sys.path.append(site.getusersitepackages())
import pymupdf as fitz  # noqa: E402


def normreg(s):
    return re.sub(r"[^0-9A-Z]", "", s.upper())


def main():
    pdf, out = sys.argv[1], sys.argv[2]
    lines = []
    for p in fitz.open(pdf):
        lines += [x.strip() for x in p.get_text().splitlines() if x.strip()]
    rows = []
    i = 0
    while i < len(lines) - 4:
        m = re.match(r"^(\d{1,3})\s+(.+)$", lines[i])
        if m and re.match(r"^HF", lines[i + 1].replace(" ", ""), re.I):
            reg = lines[i + 1]
            lic = lines[i + 2]
            date = lines[i + 3]
            addr = lines[i + 4]
            contact = lines[i + 5] if i + 5 < len(lines) else ""
            rows.append({"no": m.group(1), "name": m.group(2), "reg_no": reg, "reg_norm": normreg(reg),
                         "license_no": lic, "issued": date, "address": addr, "contact": contact})
            i += 5
        else:
            i += 1
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} facilities", file=sys.stderr)


if __name__ == "__main__":
    main()
