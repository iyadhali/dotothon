"""Dump LFS 2024-25 annex tables. Usage: python -I econ_dump_lfs.py <xlsx>"""
import sys, openpyxl
wb=openpyxl.load_workbook(sys.argv[1],data_only=True)
for ws in wb:
    print("==",ws.title)
    for r in ws.iter_rows(values_only=True):
        if any(c is not None for c in r): print([(round(c,1) if isinstance(c,float) else c) for c in r if c is not None])
