"""Census rows cleanup + fuzzy join of RTL/ODI/airline names to census islands.
Usage: python -I kandu_census_join.py <team-kandu dir>"""
import sys, site, os, re, difflib
sys.path.append(site.getusersitepackages())
import pandas as pd

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
D = sys.argv[1]
obs = pd.read_csv(os.path.join(D, "observations.csv"), dtype={"source_table": str}, low_memory=False)
stops = pd.read_csv(os.path.join(D, "rtl_stops.csv"))
odi = pd.read_csv(os.path.join(D, "odi_connections.csv"))
dest = pd.read_csv(os.path.join(D, "maldivian_destinations.csv"))
c = obs[(obs.source_table == "3.3") & (obs.metric == "census_population")]
print("rows with null group:\n", c[c.group.isna()][["geo", "subgroup", "value"]].to_string(index=False))
odd = c[c.group.notna() & c.subgroup.str.contains("admin|Total|Harbour|Resort|Industrial|Other", case=False)]
print("odd island-level rows:\n", odd[["geo", "group", "subgroup", "value"]].to_string(index=False))
isl = c[c.group.notna() & ~c.subgroup.str.contains("admin islands", case=False)]
print("island rows:", len(isl), "sum:", isl.value.sum(), "per atoll count:", isl.group.value_counts().to_dict())
r = obs[(obs.source_table == "3.3") & (obs.metric == "registered_population")]
print("registered pop per year:", r.groupby("date").agg(n=("value", "size"), geos=("geo", "nunique")).to_dict())

norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower().replace("é", "e"))
isl = isl.assign(k=isl.subgroup.map(norm), atoll=isl.group.str.lower())
res = []
for _, s in stops.iterrows():
    cand = isl[isl.atoll == s.atoll.lower()]
    k = norm(s.island)
    if k in set(cand.k):
        res.append((s["name"], "exact", k, None)); continue
    m = difflib.get_close_matches(k, list(cand.k), n=1, cutoff=0.75)
    res.append((s["name"], "fuzzy" if m else "none", k, m[0] if m else None))
res = pd.DataFrame(res, columns=["stop", "match", "key", "census_key"])
print(res.match.value_counts().to_dict())
print(res[res.match != "exact"].to_string(index=False))
matched = set(res[res.match == "exact"].key) | set(res.census_key.dropna())
isl["has_rtl"] = isl.k.isin(matched)
print(f"census islands w/ RTL stop (exact+fuzzy): {isl.has_rtl.sum()}/{len(isl)}  pop {isl[isl.has_rtl].value.sum():.0f}/{isl.value.sum():.0f}")
print("largest islands without RTL stop:\n", isl[~isl.has_rtl].nlargest(15, "value")[["geo", "value"]].to_string(index=False))
for nm in dest[dest.domestic == "yes"].name:
    m = difflib.get_close_matches(norm(nm), list(isl.k), n=1, cutoff=0.7)
    print("airline", nm, "->", m)
