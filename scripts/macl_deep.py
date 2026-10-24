"""Deeper MACL checks: row semantics, domestic presence, headways. Usage: python -I macl_deep.py <macl_csv>"""
import sys
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)

m = pd.read_csv(sys.argv[1], dtype=str)
for c in [c for c in m.columns if c.startswith(("arr_", "transit_")) or c in ("dep_adults", "dep_children", "dep_infants")]:
    m[c] = pd.to_numeric(m[c], errors="coerce")
m["dep_dt"] = pd.to_datetime(m.dep_date, format="%m/%d/%Y", errors="coerce")
m["arr_dt"] = pd.to_datetime(m.arrival_date, format="%m/%d/%Y", errors="coerce")
print("arrival_date year 1970 rows:\n", m[m.arr_dt.dt.year < 2000][["record_id", "dep_date", "arrival_date", "ata", "atd", "route_code"]])
print("excel-serial time rows:\n", m[m.ata.fillna("").str.match(r"^\d{5}$") | m.atd.fillna("").str.match(r"^\d{5}$")][["record_id", "dep_date", "arrival_date", "ata", "atd"]].head(20))


def to_min(s):
    t = s.fillna("").str.extract(r"^(\d{1,2}):(\d{2})$").astype(float)
    return t[0] * 60 + t[1]


m["ata_m"], m["atd_m"] = to_min(m.ata), to_min(m.atd)
# Interpretation A: arrival at MLE on arrival_date+ata, departure from MLE on dep_date+atd
m["A_arr"] = m.arr_dt + pd.to_timedelta(m.ata_m, unit="m")
m["A_dep"] = m.dep_dt + pd.to_timedelta(m.atd_m, unit="m")
g = (m.A_dep - m.A_arr).dt.total_seconds() / 60
print("Interpretation A (arr at MLE, then dep from MLE) ground minutes:")
print(g.describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).to_string())
print("share negative:", (g < 0).mean())
print("ground minutes by aircraft_category (median):")
print(m.assign(g=g).groupby("aircraft_category").g.median().to_string())
print("rows where dep_date < arrival_date:", (m.dep_dt < m.arr_dt).sum(), " dep_date > arrival_date:", (m.dep_dt > m.arr_dt).sum())
print(m[m.dep_dt != m.arr_dt][["dep_date", "arrival_date", "ata", "atd", "aircraft_category", "transit_adults"]].head(12).to_string())

# Pax structure: arrival-only or departure-only rows?
arr = m[["arr_adults", "arr_children", "arr_infants"]].sum(axis=1)
dep = m[["dep_adults", "dep_children", "dep_infants"]].sum(axis=1)
tr = m[["transit_adults", "transit_children", "transit_infants"]].sum(axis=1)
print("rows arr>0&dep>0:", ((arr > 0) & (dep > 0)).sum(), " arr only:", ((arr > 0) & (dep == 0)).sum(), " dep only:", ((dep > 0) & (arr == 0)).sum(), " transit>0:", (tr > 0).sum())
print("max pax arr/dep/transit:", arr.max(), dep.max(), tr.max())

# Turboprop / possible domestic
tp = m[m.aircraft_category == "Turboprop"]
print("\nTurboprop rows by year:\n", tp.groupby(tp.dep_dt.dt.year).size().to_string())
print("Turboprop routes:\n", tp.groupby(["route_code", "region", "carrier_code"]).agg(n=("record_id", "size"), first=("dep_dt", "min"), last=("dep_dt", "max"), pax_med=("arr_adults", "median")).sort_values("n", ascending=False).head(15).to_string())
print("\nRegion 'Other' rows:\n", m[m.region == "Other"][["dep_date", "carrier_code", "route_code", "aircraft_category", "arr_adults", "dep_adults"]].head(15).to_string())
# Daily movements count: domestic MLE traffic is ~100+/day; check observed per day
daily = m.groupby("dep_dt").size()
print("\nmovements per day (2025):", daily[daily.index.year == 2025].describe().to_string())

# Headway feasibility for a top route
last = m[(m.dep_dt >= "2025-08-01") & (m.dep_dt < "2026-08-01")]
top = last.route_code.value_counts().head(5)
print("\nTop routes Aug-2025..Jul-2026 weekly freq:")
for r, n in top.items():
    print(r, last[last.route_code == r].region.iloc[0], "flights/week=%.1f" % (n / 52), " mean headway h=%.1f" % (24 * 7 / (n / 52)))
print("\nrecord_id monotonic with date?", m.record_id.astype(int).is_monotonic_increasing, " dates sorted?", m.dep_dt.is_monotonic_increasing)
