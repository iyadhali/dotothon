"""Profile MACL, Avas, MTCC tabular datasets.
Usage: python -I profile_mbs_tabular.py <macl_csv> <avas_rides_csv> <fare_csv> <mtcc_xlsx>
Reads data only; never executes anything from the data folders.
"""
import sys
import numpy as np
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_rows", 300)

macl_p, avas_p, fare_p, mtcc_p = sys.argv[1:5]


def basic(df, name):
    print("\n" + "#" * 100)
    print(f"# {name}: rows={len(df):,} cols={df.shape[1]}")
    print(df.dtypes.to_string())
    print("-- nulls")
    print(df.isna().sum().to_string())
    print("-- head")
    print(df.head(5).to_string())
    print("-- describe numeric")
    num = df.select_dtypes("number")
    if not num.empty:
        print(num.describe(percentiles=[0.01, 0.5, 0.99]).T.to_string())
    print("-- nunique")
    print(df.nunique().to_string())
    print("-- full duplicate rows:", df.duplicated().sum())


# ---------------------------------------------------------------- MACL
m = pd.read_csv(macl_p, dtype=str, keep_default_na=False, na_values=[""])
basic(m, "MACL raw (as str)")
intcols = [c for c in m.columns if c.startswith(("arr_", "dep_a", "dep_c", "dep_i", "transit_"))]
for c in intcols + ["record_id"]:
    bad = pd.to_numeric(m[c], errors="coerce").isna() & m[c].notna()
    if bad.any():
        print("non-numeric in", c, m.loc[bad, c].unique()[:10])
    m[c] = pd.to_numeric(m[c], errors="coerce")
for c in ["dep_date", "arrival_date"]:
    d = pd.to_datetime(m[c], format="%m/%d/%Y", errors="coerce")
    print(c, "unparsed:", (d.isna() & m[c].notna()).sum(), "min", d.min(), "max", d.max())
    m[c + "_dt"] = d
for c in ["flight_type", "region", "aircraft_category"]:
    print("\n-- value counts", c)
    print(m[c].value_counts(dropna=False).to_string())
print("\n-- top aircraft_type_code"); print(m["aircraft_type_code"].value_counts().head(30).to_string())
print("\n-- top carriers"); print(m["carrier_code"].value_counts().head(20).to_string())
print("n carriers", m.carrier_code.nunique(), "n routes", m.route_code.nunique())
print("\n-- rows by year")
print(m.groupby(m.dep_date_dt.dt.year).size().to_string())
print("\n-- dep_date != arrival_date:", (m.dep_date_dt != m.arrival_date_dt).sum())
print((m.dep_date_dt - m.arrival_date_dt).dt.days.value_counts().head(10).to_string())
# time parsing
def tmin(s):
    t = s.str.extract(r"^(\d{1,2}):(\d{2})$").astype(float)
    return t[0] * 60 + t[1]
m["ata_min"] = tmin(m["ata"].fillna(""))
m["atd_min"] = tmin(m["atd"].fillna(""))
print("ata unparsable:", (m.ata_min.isna() & m.ata.notna()).sum(), m.loc[m.ata_min.isna() & m.ata.notna(), "ata"].unique()[:10])
print("atd unparsable:", (m.atd_min.isna() & m.atd.notna()).sum(), m.loc[m.atd_min.isna() & m.atd.notna(), "atd"].unique()[:10])
m["ground_min"] = m.atd_min - m.ata_min
print("-- (atd - ata) minutes (turnaround at MLE if both present)")
print(m.ground_min.describe(percentiles=[.01, .05, .5, .95, .99]).to_string())
print("rows with ata only:", (m.ata.notna() & m.atd.isna()).sum(), "atd only:", (m.atd.notna() & m.ata.isna()).sum(), "both:", (m.ata.notna() & m.atd.notna()).sum(), "neither:", (m.ata.isna() & m.atd.isna()).sum())
# Domestic signal
for col in ["region"]:
    dom = m[m[col].str.contains("Dom|Maldiv|Local", case=False, na=False)]
    print("rows with domestic-looking region:", len(dom))
print("\n-- region x flight_type")
print(pd.crosstab(m.region.fillna("NA"), m.flight_type.fillna("NA")).to_string())
print("\n-- region x aircraft_category")
print(pd.crosstab(m.region.fillna("NA"), m.aircraft_category.fillna("NA")).to_string())
# route -> region uniqueness
rr = m.groupby("route_code").region.nunique()
print("routes mapping to >1 region:", (rr > 1).sum(), "of", len(rr))
rc = m.groupby("route_code").carrier_code.nunique()
print("carriers per route distribution:\n", rc.describe().to_string())
# route frequency for latest full year
last = m[m.dep_date_dt.dt.year == m.dep_date_dt.dt.year.max()]
print("latest year", m.dep_date_dt.dt.year.max(), "rows", len(last), "date span", last.dep_date_dt.min(), last.dep_date_dt.max())
print("\n-- top routes latest year with region")
top = last.groupby(["route_code", "region"]).size().sort_values(ascending=False).head(25)
print(top.to_string())
print("\n-- passengers by region (sum arr+dep adults, all years)")
m["pax"] = m[["arr_adults", "arr_children", "arr_infants", "dep_adults", "dep_children", "dep_infants"]].sum(axis=1)
print(m.groupby("region").agg(rows=("pax", "size"), pax_mean=("pax", "mean"), pax_med=("pax", "median")).to_string())
print("\n-- zero-pax rows:", (m.pax == 0).sum())
print("-- aircraft category for small types: (category list)")
print(m.groupby("aircraft_category").aircraft_type_code.unique().to_string())
print("\n-- monthly row counts last 24 months")
print(m.groupby(m.dep_date_dt.dt.to_period("M")).size().tail(24).to_string())

# ---------------------------------------------------------------- AVAS
a = pd.read_csv(avas_p)
basic(a, "Avas rides")
a["dt"] = pd.to_datetime(a.date_started, errors="coerce")
print("unparsed dates:", a.dt.isna().sum(), "range", a.dt.min(), a.dt.max())
print(a.status.value_counts(dropna=False).to_string())
print("-- rides per day stats"); print(a.groupby(a.dt.dt.date).size().describe().to_string())
print("-- rides by hour"); print(a.groupby(a.dt.dt.hour).size().to_string())
for c in ["pickup_lat", "dropoff_lat"]:
    print(c, a[c].quantile([0, .001, .01, .5, .99, .999, 1]).round(4).to_dict())
for c in ["pickup_lng", "dropoff_lng"]:
    print(c, a[c].quantile([0, .001, .01, .5, .99, .999, 1]).round(4).to_dict())
# haversine
R = 6371.0
la1, lo1, la2, lo2 = map(np.radians, [a.pickup_lat, a.pickup_lng, a.dropoff_lat, a.dropoff_lng])
h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
a["hav_km"] = 2 * R * np.arcsin(np.sqrt(h))
a["speed_kmh"] = a.distance_km / (a.time_sec / 3600)
a["detour"] = a.distance_km / a.hav_km.replace(0, np.nan)
print("-- distance_km / time_sec / hav / speed / detour")
print(a[["distance_km", "time_sec", "hav_km", "speed_kmh", "detour"]].describe(percentiles=[.01, .05, .5, .95, .99]).T.to_string())
print("zero distance:", (a.distance_km == 0).sum(), "zero time:", (a.time_sec == 0).sum(), "neg:", (a.distance_km < 0).sum(), (a.time_sec < 0).sum())
print("speed>80:", (a.speed_kmh > 80).sum(), "speed<3:", (a.speed_kmh < 3).sum())
# speed / time_sec linear relation?
c = a[(a.distance_km > 0) & (a.time_sec > 0)]
print("corr(distance,time)", c.distance_km.corr(c.time_sec))
fit = np.polyfit(c.distance_km, c.time_sec, 1)
print("linear fit time_sec = %.2f*km + %.2f" % tuple(fit))
resid = c.time_sec - np.polyval(fit, c.distance_km)
print("residual std sec", resid.std())
print("-- speed by hour (completed only)")
cc = c[c.status == "payment_completed"] if "payment_completed" in c.status.values else c
print(cc.groupby(cc.dt.dt.hour).speed_kmh.median().round(1).to_string())
# zones: assign coarse zone by bbox
def zone(lat, lng):
    z = np.full(len(lat), "other", dtype=object)
    male = (lat.between(4.165, 4.182)) & (lng.between(73.495, 73.520))
    vil = (lat.between(4.180, 4.200)) & (lng.between(73.520, 73.535))  # Hulhule airport (approx)
    hm1 = (lat.between(4.200, 4.225)) & (lng.between(73.530, 73.550))
    hm2 = (lat.between(4.225, 4.260)) & (lng.between(73.530, 73.560))
    vill = (lat.between(4.155, 4.168)) & (lng.between(73.480, 73.500))
    z[vil] = "Hulhule/VIA"; z[hm1] = "Hulhumale1"; z[hm2] = "Hulhumale2"; z[male] = "Male"; z[vill] = "Villimale"
    return z
a["oz"] = zone(a.pickup_lat, a.pickup_lng)
a["dz"] = zone(a.dropoff_lat, a.dropoff_lng)
print("-- coarse OD zones (bbox approx)")
print(pd.crosstab(a.oz, a.dz).to_string())
od = a[(a.status == "payment_completed")].groupby(["oz", "dz"]).agg(n=("time_sec", "size"), med_km=("distance_km", "median"), med_min=("time_sec", lambda s: s.median() / 60), med_kmh=("speed_kmh", "median"))
print(od.round(2).to_string())
print("-- distinct pickup coordinate pairs:", a[["pickup_lat", "pickup_lng"]].drop_duplicates().shape[0])
print("-- lat/lng decimal precision sample:", a.pickup_lat.astype(str).str.split(".").str[1].str.len().value_counts().head().to_dict())

fare = pd.read_csv(fare_p)
basic(fare, "Avas fare matrix")
print(fare.to_string())

# ---------------------------------------------------------------- MTCC
xl = pd.read_excel(mtcc_p, sheet_name=None)
for name, df in xl.items():
    basic(df, f"MTCC sheet {name}")
    for c in df.columns:
        if df[c].dtype == object and df[c].nunique() < 60:
            print(f"-- values {c}:", df[c].value_counts().to_dict())
fm = xl.get("ferry_monthly")
if fm is not None:
    print("\n-- ferry routes: first/last month and n months")
    print(fm.groupby(["zone", "atoll", "route_id"]).agg(first=("month", "min"), last=("month", "max"), n=("month", "size"), mean_pax=("passengers", "mean")).to_string())
bm = xl.get("bus_monthly")
if bm is not None:
    print(bm.groupby(["route_id", "route_name"]).agg(first=("month", "min"), last=("month", "max"), n=("month", "size")).to_string())
