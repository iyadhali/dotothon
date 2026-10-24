"""Dump all sheets of one or more XLSX files as text (non-empty rows only).

Usage: python -I health_xlsx_dump.py [--max N] file1.xlsx [file2.xlsx ...]
"""
import site
import sys

# -I drops the user site-packages; re-add it explicitly (trusted, not the data dir)
sys.path.append(site.getusersitepackages())
import openpyxl  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

args = sys.argv[1:]
maxrows = 80
if args and args[0] == "--max":
    maxrows = int(args[1])
    args = args[2:]

for f in args:
    print(f"########## {f}")
    wb = openpyxl.load_workbook(f, data_only=True, read_only=True)
    for ws in wb.worksheets:
        print(f"=== sheet: {ws.title}")
        n = 0
        for row in ws.iter_rows(values_only=True):
            vals = ["" if v is None else str(v).strip() for v in row]
            if any(vals):
                while vals and not vals[-1]:
                    vals.pop()
                print(" | ".join(vals))
                n += 1
                if n >= maxrows:
                    print("... (truncated)")
                    break
