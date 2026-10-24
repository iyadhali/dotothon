"""Dump HIES 2019 indicator workbooks and WDI PPP/CPI series. Usage: python -I econ_dump_hies.py <economics_dir>"""
import sys, openpyxl, csv
d=sys.argv[1]
for f in ["mbs_hies2019/Income-Indicator-HIES2019.xlsx","mbs_hies2019/HIES2019-Expenditure-indicators.xlsx"]:
    wb=openpyxl.load_workbook(d+"/"+f,data_only=True)
    for ws in wb:
        print("==",f,ws.title,ws.dimensions)
        for r in ws.iter_rows(values_only=True):
            if any(c is not None for c in r): print([(round(c,1) if isinstance(c,float) else c) for c in r if c is not None])
for r in csv.DictReader(open(d+"/worldbank_wdi/wdi_maldives_economics_long.csv",encoding="utf8")):
    if r["indicator_code"] in("PA.NUS.PPP","FP.CPI.TOTL.ZG") and int(r["year"])>=2017: print(r["indicator_code"],r["year"],r["value"])
