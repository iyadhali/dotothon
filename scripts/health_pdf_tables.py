"""Helpers to locate and extract tables from health PDFs with PyMuPDF.

Usage:
  python -I health_pdf_tables.py find <pdf> "<regex>"            -> list pages whose text matches
  python -I health_pdf_tables.py dump <pdf> <p1>[-<p2>]           -> print tables found on pages (1-based)
  python -I health_pdf_tables.py text <pdf> <p1>[-<p2>]           -> print plain text of pages
  python -I health_pdf_tables.py csv  <pdf> <p1>[-<p2>] <out.csv> -> write all table rows (page, table, cells)
"""
import csv
import re
import site
import sys

sys.path.append(site.getusersitepackages())
import fitz  # noqa: E402  (PyMuPDF)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def pages(spec):
    if "-" in spec:
        a, b = spec.split("-")
        return range(int(a), int(b) + 1)
    return [int(spec)]


def main():
    cmd, pdf = sys.argv[1], sys.argv[2]
    doc = fitz.open(pdf)
    if cmd == "find":
        rx = re.compile(sys.argv[3], re.I)
        for i, p in enumerate(doc):
            t = p.get_text()
            if rx.search(t):
                m = rx.search(t)
                print(i + 1, "|", t[max(0, m.start() - 40):m.end() + 60].replace("\n", " "))
    elif cmd == "text":
        for pn in pages(sys.argv[3]):
            print(f"===== page {pn}")
            print(doc[pn - 1].get_text())
    elif cmd in ("dump", "csv"):
        rows = []
        for pn in pages(sys.argv[3]):
            tabs = doc[pn - 1].find_tables()
            for ti, tb in enumerate(tabs.tables):
                for r in tb.extract():
                    cells = [("" if c is None else re.sub(r"\s+", " ", str(c)).strip()) for c in r]
                    rows.append([pn, ti] + cells)
        if cmd == "dump":
            for r in rows:
                print(" | ".join(str(x) for x in r))
        else:
            with open(sys.argv[4], "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
            print("wrote", len(rows), "rows")


if __name__ == "__main__":
    main()
