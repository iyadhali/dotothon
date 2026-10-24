"""Fetch World Bank WDI and WHO GHO (GHED) series for Maldives (economics layer).
Usage: python -I econ_fetch_wdi_ghed.py <economics_dir>
"""
import sys, json, urllib.request, csv, os, time
out = sys.argv[1]
WDI = {
 "SH.XPD.CHEX.GD.ZS":"Current health expenditure (% of GDP)",
 "SH.XPD.CHEX.PC.CD":"Current health expenditure per capita (current US$)",
 "SH.XPD.CHEX.PP.CD":"Current health expenditure per capita, PPP (current intl $)",
 "SH.XPD.GHED.CH.ZS":"Domestic general government health expenditure (% of CHE)",
 "SH.XPD.GHED.GD.ZS":"Domestic general government health expenditure (% of GDP)",
 "SH.XPD.GHED.GE.ZS":"Domestic general government health expenditure (% of general government expenditure)",
 "SH.XPD.GHED.PC.CD":"Domestic general government health expenditure per capita (current US$)",
 "SH.XPD.PVTD.CH.ZS":"Domestic private health expenditure (% of CHE)",
 "SH.XPD.OOPC.CH.ZS":"Out-of-pocket expenditure (% of CHE)",
 "SH.XPD.OOPC.PC.CD":"Out-of-pocket expenditure per capita (current US$)",
 "SH.XPD.EHEX.CH.ZS":"External health expenditure (% of CHE)",
 "SH.UHC.OOPC.10.ZS":"Population with household health spending >10% of total consumption or income (%)",
 "SH.UHC.OOPC.25.ZS":"Population with household health spending >25% of total consumption or income (%)",
 "SH.UHC.SRVS.CV.XD":"UHC service coverage index",
 "SE.XPD.TOTL.GD.ZS":"Government expenditure on education (% of GDP)",
 "SE.XPD.TOTL.GB.ZS":"Government expenditure on education (% of government expenditure)",
 "SE.XPD.TERT.ZS":"Expenditure on tertiary as % of government expenditure on education",
 "SE.XPD.TERT.PC.ZS":"Government expenditure per tertiary student (% of GDP per capita)",
 "SE.XPD.CTER.ZS":"Current education expenditure, tertiary (% of total expenditure in tertiary public institutions)",
 "SE.TER.ENRR":"School enrollment, tertiary (% gross)",
 "NY.GDP.MKTP.CD":"GDP (current US$)",
 "NY.GDP.MKTP.CN":"GDP (current LCU)",
 "NY.GDP.PCAP.CD":"GDP per capita (current US$)",
 "NY.GNP.PCAP.CD":"GNI per capita, Atlas (current US$)",
 "PA.NUS.FCRF":"Official exchange rate (LCU per US$)",
 "PA.NUS.PPP":"PPP conversion factor, GDP (LCU per intl $)",
 "NE.CON.PRVT.PC.KD":"Household final consumption expenditure per capita (constant 2015 US$)",
 "SI.POV.GINI":"Gini index",
 "SP.POP.TOTL":"Population, total",
 "FP.CPI.TOTL.ZG":"Inflation, consumer prices (annual %)",
}
GHO = {
 "GHED_CHEGDP_SHA2011":"Current health expenditure (CHE) as % of GDP",
 "GHED_CHE_pc_US_SHA2011":"CHE per capita in US$",
 "GHED_CHE_pc_PPP_SHA2011":"CHE per capita in PPP int$",
 "GHED_GGHE-DCHE_SHA2011":"Domestic general government health expenditure (GGHE-D) as % of CHE",
 "GHED_GGHE-DGDP_SHA2011":"GGHE-D as % of GDP",
 "GHED_GGHE-DGGE_SHA2011":"GGHE-D as % of general government expenditure",
 "GHED_GGHE-D_pc_US_SHA2011":"GGHE-D per capita in US$",
 "GHED_PVT-DCHE_SHA2011":"Domestic private health expenditure (PVT-D) as % of CHE",
 "GHED_OOPSCHE_SHA2011":"Out-of-pocket expenditure (OOPS) as % of CHE",
 "GHED_OOP_pc_US_SHA2011":"OOPS per capita in US$",
 "GHED_EXTCHE_SHA2011":"External health expenditure (EXT) as % of CHE",
 "FINPROTECTION_CATA_TOT_10_POP":"Catastrophic OOP >10% of household budget (%)",
 "FINPROTECTION_CATA_TOT_25_POP":"Catastrophic OOP >25% of household budget (%)",
}
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (datathon research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()
rows=[]
os.makedirs(f"{out}/worldbank_wdi/raw_json", exist_ok=True)
for code,name in WDI.items():
    url=f"https://api.worldbank.org/v2/country/MDV/indicator/{code}?format=json&per_page=200"
    try:
        b=get(url); open(f"{out}/worldbank_wdi/raw_json/{code}.json","wb").write(b)
        d=json.loads(b)
        n=0
        if len(d)>1 and d[1]:
            for r in d[1]:
                if r["value"] is not None:
                    rows.append(dict(indicator_code=code,indicator=name,year=int(r["date"]),value=r["value"],source_url=url)); n+=1
        print("WDI",code,n)
    except Exception as e:
        print("WDI FAIL",code,e)
    time.sleep(0.3)
rows.sort(key=lambda r:(r["indicator_code"],r["year"]))
with open(f"{out}/worldbank_wdi/wdi_maldives_economics_long.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
rows=[]
os.makedirs(f"{out}/who_ghed/raw_json", exist_ok=True)
for code,name in GHO.items():
    url=f"https://ghoapi.azureedge.net/api/{code}?$filter=SpatialDim%20eq%20%27MDV%27"
    try:
        b=get(url); open(f"{out}/who_ghed/raw_json/{code}.json","wb").write(b)
        d=json.loads(b)["value"]
        for r in d:
            rows.append(dict(indicator_code=code,indicator=name,year=r.get("TimeDim"),dim1=r.get("Dim1"),value=r.get("NumericValue"),source_url=url))
        print("GHO",code,len(d))
    except Exception as e:
        print("GHO FAIL",code,e)
rows.sort(key=lambda r:(r["indicator_code"],r["year"] or 0))
with open(f"{out}/who_ghed/who_gho_ghed_maldives_long.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
