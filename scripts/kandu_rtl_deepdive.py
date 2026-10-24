"""Deep-dive on RTL ferry tables, bus tables, census rows, and cross-file joins.
Usage: python -I kandu_rtl_deepdive.py <team-kandu dir> <hdx-heigit-access dir>"""
import sys, site, os, re, math
sys.path.append(site.getusersitepackages())
import pandas as pd, numpy as np

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
pd.set_option("display.max_colwidth", 100)
D, H = sys.argv[1], sys.argv[2]
r = lambda f, **k: pd.read_csv(os.path.join(D, f), **k)
stops, routes, trips, conns, uns = r("rtl_stops.csv"), r("rtl_routes.csv"), r("rtl_trips.csv"), r("rtl_connections.csv"), r("rtl_unscheduled.csv")
obs = r("observations.csv", dtype={"source_table": str}, low_memory=False)
odi = r("odi_connections.csv"); dest = r("maldivian_destinations.csv")
bstops, broutes, bdep = r("rtl_bus_stops.csv"), r("rtl_bus_routes.csv"), r("rtl_bus_departures.csv")


def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))


print("== RTL STOPS")
print("dup names", stops.name.duplicated().sum(), "dup islands", stops.island.duplicated().sum())
print(stops[stops.island.duplicated(keep=False)].sort_values("island").to_string(index=False))
print("name != atoll.island:", (stops.name != stops.atoll + "." + stops.island).sum())
print(stops[stops.name != stops.atoll + "." + stops.island].to_string(index=False))
# coordinate outliers: distance from atoll median
med = stops.groupby("atoll")[["lat", "lon"]].median()
stops["km_from_atoll_median"] = [hav(a, b, *med.loc[t]) for a, b, t in zip(stops.lat, stops.lon, stops.atoll)]
print(stops.sort_values("km_from_atoll_median", ascending=False).head(8)[["name", "atoll", "lat", "lon", "km_from_atoll_median"]].to_string(index=False))
print("atoll lat ranges:\n", stops.groupby("atoll").agg(n=("name", "size"), lat_min=("lat", "min"), lat_max=("lat", "max"), sched=("scheduled", lambda x: (x == "yes").sum())).sort_values("lat_max", ascending=False).to_string())
# nearest neighbour distances
coords = stops[["lat", "lon"]].values
nn = [min(hav(*coords[i], *coords[j]) for j in range(len(coords)) if j != i) for i in range(len(coords))]
stops["nn_km"] = nn
print("nn_km describe", stops.nn_km.describe().round(2).to_dict())
print(stops.nsmallest(5, "nn_km")[["name", "lat", "lon", "nn_km"]].to_string(index=False))

print("\n== RTL ROUTES vs TRIPS")
print("zones:", sorted(routes.zone.unique()), " route prefixes:", sorted(set(re.sub(r"\d+$", "", x) for x in routes.route)))
print(routes[~routes.route.str.startswith("Z")].to_string(index=False))
t = trips.copy()
t["mins"] = t.time.str.split(":").apply(lambda x: int(x[0]) * 60 + int(x[1]))
per = t.groupby(["route", "trip"]).agg(n=("stop", "size"), start=("mins", "min"), end=("mins", "max"),
                                         first=("time", "first"), monotonic=("mins", lambda x: x.is_monotonic_increasing)).reset_index()
print("trips:", len(per), " non-monotonic trips:", (~per.monotonic).sum())
print(per[~per.monotonic].to_string(index=False))
nt = per.groupby("route").trip.nunique().rename("n_trips_in_trips")
cmp = routes.set_index("route")[["trips_per_day"]].join(nt)
print("trips_per_day mismatch vs trips file:\n", cmp[cmp.trips_per_day != cmp.n_trips_in_trips].to_string())
print("trips per route dist:", nt.value_counts().sort_index().to_dict())
print("total daily trips:", len(per), " service window:", t.time.min(), "-", t.time.max())
print("routes in routes not in trips:", set(routes.route) - set(trips.route), " in trips not routes:", set(trips.route) - set(routes.route))
print("trip stops not in rtl_stops:", sorted(set(trips.stop) - set(stops.name)))
# leg durations
t = t.sort_values(["route", "trip", "order"])
t["leg"] = t.groupby(["route", "trip"]).mins.diff()
print("leg minutes describe:", t.leg.describe().round(1).to_dict(), " zero/neg legs:", (t.leg <= 0).sum())
# headways: departures from first stop per route
hw = per.sort_values(["route", "start"]).groupby("route").start.apply(lambda x: list(np.diff(x.values)))
print("headway sample (min):", hw[hw.apply(len) > 0].head(10).to_dict())
# direction: does each route have both directions?
first_stop = t[t.order == 1].groupby("route").stop.nunique()
print("routes with >1 distinct origin (bi-directional):", (first_stop > 1).sum(), "of", len(first_stop))
# routes.stops list vs trip stops
rs = routes.set_index("route").stops.str.split(r",\s*").apply(lambda l: set(s.replace(". ", ".").strip() for s in l))
ts = t.groupby("route").stop.apply(set)
bad = [(k, rs[k] ^ ts.get(k, set())) for k in rs.index if rs[k] != ts.get(k, set())]
print("routes.stops vs trip stops mismatches:", bad[:10])

print("\n== CONNECTIONS (derivable from trips?)")
print("unique OD pairs", conns[["from_stop", "to_stop"]].drop_duplicates().shape[0], " inter-atoll:", (conns.from_atoll != conns.to_atoll).sum())
print(conns[conns.from_atoll != conns.to_atoll].head(10).to_string(index=False))
print("shortest_minutes describe", conns.shortest_minutes.describe().to_dict())
print("symmetric pairs:", conns.merge(conns, left_on=["from_stop", "to_stop"], right_on=["to_stop", "from_stop"]).shape[0])

print("\n== UNSCHEDULED")
print(uns[uns.route.str.contains("ERROR")].to_string(index=False))
ustops = set(s.strip() for l in uns.stops.str.split(">") for s in l if s.strip())
print("unscheduled stop names not in rtl_stops:", sorted(ustops - set(stops.name))[:40])
print("stops scheduled=no:", sorted(stops[stops.scheduled == "no"].name))

print("\n== BUS")
print("bus stop codes w/ multiple coords:", bstops.groupby("code")[["lat", "lon"]].nunique().gt(1).any(axis=1).sum())
print("bus stops lat==0 or nulls:", ((bstops.lat == 0) | bstops.lat.isna()).sum())
print("bus stops with tab/whitespace in name:", bstops.stop.str.contains(r"\t|\s$").sum(), broutes.to_stop.str.contains(r"\t").sum())
print(broutes[["area", "route_number", "name", "stops", "trips_per_day", "departures_left_when_fetched", "minibus", "fare_mvr"]].to_string(index=False))
print("departures time range", bdep.time.min(), bdep.time.max(), "routes", bdep.route_number.nunique())

print("\n== CENSUS (obs table 3.3)")
c = obs[obs.source_table == "3.3"]
for mtr in c.metric.unique():
    cm = c[c.metric == mtr]
    print(mtr, "rows", len(cm), "years", sorted(cm.date.unique()), "sum", cm.value.sum(), "null subgroup", cm.subgroup.isna().sum())
cp = c[c.metric == "census_population"]
print("non-island geos (subgroup null):", cp[cp.subgroup.isna()][["geo", "group", "value"]].to_string(index=False))
print("top 8 census islands:\n", cp.nlargest(8, "value")[["geo", "group", "subgroup", "value"]].to_string(index=False))
print("atolls in census:", sorted(cp.group.dropna().unique()))
print("geos with comma:", c[c.geo.str.contains(",")].geo.unique())

print("\n== JOINS")
cen = cp.dropna(subset=["subgroup"]).copy()
norm = lambda s: re.sub(r"[^a-z]", "", str(s).lower().replace("é", "e"))
cen["k_isl"] = cen.subgroup.map(norm); cen["k_full"] = cen.group.map(norm) + "|" + cen.k_isl
stops["k_isl"] = stops.island.map(norm); stops["k_full"] = stops.atoll.map(norm) + "|" + stops.k_isl
m_full = stops.k_full.isin(cen.k_full); m_isl = stops.k_isl.isin(cen.k_isl)
print(f"rtl_stops -> census: exact atoll+island {m_full.sum()}/{len(stops)}, island-only {m_isl.sum()}/{len(stops)}")
print("unmatched rtl stops:", sorted(stops[~m_isl].name))
print("unmatched (atoll+island) but matched island-only:", sorted(stops[m_isl & ~m_full].name))
print(f"census islands with an RTL stop: {cen.k_full.isin(stops.k_full).sum()}/{len(cen)}; pop covered {cen[cen.k_full.isin(stops.k_full)].value.sum():.0f}/{cen.value.sum():.0f}")
odi_isl = pd.concat([odi[["island_a", "atoll_a"]].set_axis(["isl", "atoll"], axis=1), odi[["island_b", "atoll_b"]].set_axis(["isl", "atoll"], axis=1)]).drop_duplicates()
odi_isl["k_isl"] = odi_isl.isl.str.split(". ", n=1, regex=False).str[-1].map(norm)
print("odi islands", len(odi_isl), " matched census island-only:", odi_isl.k_isl.isin(cen.k_isl).sum(), " unmatched:", sorted(odi_isl[~odi_isl.k_isl.isin(cen.k_isl)].isl))
print("odi rows with null coords:\n", odi[odi.lat_a.isna()].to_string(index=False))
print("odi overlap with rtl_stops (island):", odi_isl.k_isl.isin(stops.k_isl).sum())
dest["k"] = dest.name.map(norm)
print("airline domestic dests:", sorted(dest[dest.domestic == "yes"].name))
print("airline dest matched to census island:", dest[dest.domestic == "yes"].k.isin(cen.k_isl).sum())
# combined ferry coverage by atoll: census pop with any RTL/ODI stop
cen["has_rtl"] = cen.k_full.isin(stops.k_full) | cen.k_isl.isin(stops.k_isl)
cen["has_odi"] = cen.k_isl.isin(odi_isl.k_isl)
print(cen.groupby("group").agg(islands=("geo", "size"), pop=("value", "sum"), rtl=("has_rtl", "sum"), odi=("has_odi", "sum")).to_string())
# HeiGIT names vs census atoll codes
hw = pd.read_csv(os.path.join(H, "MDV_hospitals_access_wide.csv"))
print("HeiGIT ADM1 names/iso:", hw[hw.admin_level == "ADM1"][["name", "iso"]].drop_duplicates().values.tolist())
