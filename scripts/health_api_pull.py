"""Pull national-level Maldives health indicators from WHO GHO OData API and World Bank API.

Usage: python -I health_api_pull.py <who_out_dir> <wb_out_dir>
Writes raw JSON per indicator plus a tidy long CSV per source.
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (datathon research)"}

WHO = {
    "WHS6_102": "Hospital beds (per 10 000 population)",
    "HWF_0001": "Medical doctors (per 10,000)",
    "HWF_0006": "Nursing and midwifery personnel (per 10,000)",
    "HWF_0010": "Dentists (per 10,000)",
    "WHS6_519": "Density of pharmaceutical personnel (per 10 000)",
    "BP_04": "Raised blood pressure, age-standardized",
    "NCD_GLUC_04": "Raised fasting blood glucose, age-standardized",
    "NCD_DIABETES_PREVALENCE_AGESTD": "Prevalence of diabetes, age-standardized",
    "NCD_BMI_30A": "Obesity among adults (age-std)",
    "NCD_PAA": "Insufficient physical activity adults (age-std)",
    "M_Est_tob_curr_std": "Current tobacco use (age-std)",
    "NCDMORT3070": "Probability of dying 30-70 from CVD, cancer, diabetes, CRD",
    "WHS2_131": "Age-standardized NCD mortality rate",
    "UHC_INDEX_REPORTED": "UHC Service Coverage Index (SDG 3.8.1)",
    "UHC_SCI_CAPACITY": "UHC sub-index service capacity and access",
    "GHED_OOPSCHE_SHA2011": "OOP as % of current health expenditure",
    "WHOSIS_000001": "Life expectancy at birth",
    "WHOSIS_000002": "Healthy life expectancy (HALE) at birth",
    "MDG_0000000026": "Maternal mortality ratio",
    "MDG_0000000007": "Under-five mortality rate",
    "WHOSIS_000003": "Neonatal mortality rate",
}

WB = {
    "SH.MED.BEDS.ZS": "Hospital beds (per 1,000 people)",
    "SH.MED.PHYS.ZS": "Physicians (per 1,000 people)",
    "SH.MED.NUMW.P3": "Nurses and midwives (per 1,000 people)",
    "SH.XPD.CHEX.GD.ZS": "Current health expenditure (% of GDP)",
    "SH.XPD.CHEX.PC.CD": "Current health expenditure per capita (current US$)",
    "SH.XPD.OOPC.CH.ZS": "Out-of-pocket expenditure (% of current health expenditure)",
    "SH.DYN.NCOM.ZS": "Mortality from CVD, cancer, diabetes or CRD between 30-70 (%)",
    "SH.STA.DIAB.ZS": "Diabetes prevalence (% of population ages 20 to 79)",
    "SH.UHC.SRVS.CV.XD": "UHC service coverage index",
    "SH.STA.BRTC.ZS": "Births attended by skilled health staff (%)",
    "SH.STA.MMRT": "Maternal mortality ratio (modeled)",
    "SP.DYN.LE00.IN": "Life expectancy at birth",
    "SH.DTH.COMM.ZS": "Cause of death, communicable/maternal/prenatal/nutrition (% of total)",
    "SH.DTH.NCOM.ZS": "Cause of death, non-communicable (% of total)",
    "SH.DTH.INJR.ZS": "Cause of death, injury (% of total)",
}


def get_json(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            print("retry", url, e, file=sys.stderr)
            time.sleep(3)
    return None


def main():
    who_dir, wb_dir = sys.argv[1], sys.argv[2]
    os.makedirs(os.path.join(who_dir, "raw_json"), exist_ok=True)
    os.makedirs(os.path.join(wb_dir, "raw_json"), exist_ok=True)

    rows = []
    for code, name in WHO.items():
        flt = urllib.parse.quote("SpatialDim eq 'MDV'")
        d = get_json(f"https://ghoapi.azureedge.net/api/{code}?$filter={flt}")
        if d is None:
            continue
        json.dump(d, open(os.path.join(who_dir, "raw_json", f"{code}.json"), "w"), indent=1)
        for v in d.get("value", []):
            rows.append({"indicator_code": code, "indicator": name, "year": v.get("TimeDim"),
                         "sex": v.get("Dim1") or "", "dim2": v.get("Dim2") or "",
                         "value": v.get("NumericValue"), "display": v.get("Value"),
                         "low": v.get("Low"), "high": v.get("High")})
    rows.sort(key=lambda r: (r["indicator_code"], str(r["year"]), r["sex"]))
    with open(os.path.join(who_dir, "who_gho_maldives_long.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("WHO rows", len(rows), file=sys.stderr)

    rows = []
    for code, name in WB.items():
        d = get_json(f"https://api.worldbank.org/v2/country/MDV/indicator/{code}?format=json&per_page=200")
        if not d or len(d) < 2 or d[1] is None:
            print("no data", code, file=sys.stderr)
            continue
        json.dump(d, open(os.path.join(wb_dir, "raw_json", f"{code}.json"), "w"), indent=1)
        for v in d[1]:
            if v.get("value") is not None:
                rows.append({"indicator_code": code, "indicator": name, "year": v["date"],
                             "value": v["value"]})
    rows.sort(key=lambda r: (r["indicator_code"], r["year"]))
    with open(os.path.join(wb_dir, "worldbank_wdi_maldives_health_long.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["indicator_code", "indicator", "year", "value"])
        w.writeheader()
        w.writerows(rows)
    print("WB rows", len(rows), file=sys.stderr)


if __name__ == "__main__":
    main()
