"""Profile mma_series.csv and observations.csv. Usage: python -I kandu_timeseries.py <team-kandu dir>"""
import sys, site, os
sys.path.append(site.getusersitepackages())
import pandas as pd

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
pd.set_option("display.max_colwidth", 120)
D = sys.argv[1]

m = pd.read_csv(os.path.join(D, "mma_series.csv"))
print("MMA rows", len(m), "series", m.series_id.nunique())
print(m.dtypes)
print(m.isna().sum())
s = m.groupby(["series_id", "group", "name", "unit", "frequency", "source"]).agg(
    n=("value", "size"), start=("date", "min"), end=("date", "max"), path=("path", "first")).reset_index()
print(s.to_string(index=False))
print(m.groupby("group").series_id.nunique())
print(m.source.value_counts())
print("dup (series,date):", m.duplicated(["series_id", "date"]).sum())

o = pd.read_csv(os.path.join(D, "observations.csv"), low_memory=False)
print("\nOBS rows", len(o)); print(o.dtypes); print(o.isna().sum())
g = o.groupby(["source_table", "metric", "unit", "period"]).agg(
    n=("value", "size"), geos=("geo", "nunique"), start=("date", "min"), end=("date", "max"),
    subgroups=("subgroup", "nunique"), groups=("group", "nunique"), editions=("edition", lambda x: sorted(x.unique()))).reset_index()
print(g.to_string(index=False))
for t in sorted(o.source_table.unique()):
    sub = o[o.source_table == t]
    print(f"\n-- table {t}: geos sample", sorted(sub.geo.dropna().unique())[:60])
    print("   groups", sub.group.dropna().unique()[:15], "subgroups", sub.subgroup.dropna().unique()[:15])
    print(sub.head(3).to_string(index=False))
print("\nvalue non-numeric:", pd.to_numeric(o.value, errors="coerce").isna().sum())
print("dup keys:", o.duplicated(["date", "period", "geo", "group", "subgroup", "metric", "source_table", "edition"]).sum())
print("source_url unique:", o.source_url.nunique())
