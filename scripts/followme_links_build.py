"""Build observed island->island sea links from FollowMe trips (Aug 2025)."""
import json, numpy as np, polars as pl, pandas as pd

R = "C:/Users/user/Music/Datathon/"
ACC = "C:/Users/user/AppData/Local/Temp/claude/C--Users-user-Music-Datathon/d458dfe7-195f-4f46-88be-e1f23eed6bc0/scratchpad/island_access.csv"
OUT = R + "data/processed/followme/"
m = json.load(open(R + "web/public/data/multimodal.json", encoding="utf-8"))
isl = {i["id"]: i for i in m["islands"]}
pts = [(i["id"], i["lat"], i["lon"]) for i in m["islands"]]
pts += [(s["islandId"], s["lat"], s["lon"]) for s in m["stops"] if s.get("islandId") in isl]
pid = np.array([p[0] for p in pts])
plat = np.radians([p[1] for p in pts])
plon = np.radians([p[2] for p in pts])
rad = np.array([3.0 if isl[p]["population"] > 8000 else 1.5 for p in pid])


def snap(lat, lon):
    out = []
    for i in range(0, len(lat), 5000):
        la = np.radians(lat[i:i + 5000])[:, None]
        lo = np.radians(lon[i:i + 5000])[:, None]
        a = np.sin((plat - la) / 2) ** 2 + np.cos(la) * np.cos(plat) * np.sin((plon - lo) / 2) ** 2
        d = 2 * 6371 * np.arcsin(np.sqrt(a))
        dd = np.where(d <= rad, d, np.inf)
        j = dd.argmin(1)
        out.append(np.where(np.isfinite(dd[np.arange(len(j)), j]), pid[j], ""))
    return np.concatenate(out)


t = pl.read_parquet(R + "data/processed/followme/fm_trips.parquet")
t = t.with_columns((pl.col("t0") + pl.duration(hours=5)).alias("loc0"))
t = t.with_columns(
    pl.col("loc0").dt.date().alias("day"),
    (pl.col("loc0").dt.hour() + pl.col("loc0").dt.minute() / 60).alias("hr"),
    pl.col("loc0").dt.weekday().is_in([5, 6]).alias("wkend"),  # Fri, Sat = Maldives weekend
)
o = snap(t["o_lat"].to_numpy(), t["o_lon"].to_numpy())
d = snap(t["d_lat"].to_numpy(), t["d_lon"].to_numpy())
t = t.with_columns(pl.Series("o_isl", o), pl.Series("d_isl", d))
stats = dict(total=t.height, o_snapped=int((o != "").sum()), d_snapped=int((d != "").sum()),
             both=int(((o != "") & (d != "")).sum()), same=int(((o != "") & (o == d)).sum()))
print(stats)
e = t.filter((pl.col("o_isl") != "") & (pl.col("d_isl") != "") & (pl.col("o_isl") != pl.col("d_isl")) & (pl.col("dur_min") <= 600))
stats["inter_island_trips"] = e.height
days_we = sum(1 for x in pd.date_range("2025-08-01", "2025-08-31") if x.weekday() in (4, 5))
days_wk = 31 - days_we

p = pl.col
g = e.group_by(["o_isl", "d_isl"]).agg(
    pl.len().alias("trips"), p("day").n_unique().alias("active_days"), p("imei").n_unique().alias("vessels"),
    p("dur_min").median().alias("median_min"), p("dur_min").quantile(0.8).alias("p80_min"),
    p("od_km").median().alias("distance_km"), p("od_kmh").median().alias("od_kmh"), p("detour").median().alias("detour"),
    p("hr").quantile(0.1).alias("first_dep_hour_p10"), p("hr").quantile(0.9).alias("last_dep_hour_p90"),
    p("wkend").sum().alias("n_we"))
top = e.group_by(["o_isl", "d_isl", "imei"]).len().group_by(["o_isl", "d_isl"]).agg(p("len").max().alias("topn"))
g = g.join(top, on=["o_isl", "d_isl"]).with_columns((p("topn") / p("trips")).alias("top_vessel_share"))
hh = e.group_by(["o_isl", "d_isl", p("hr").floor().cast(pl.Int32).alias("h")]).len()
hist = hh.group_by(["o_isl", "d_isl"]).agg(p("h"), p("len"))
hd = {(r["o_isl"], r["d_isl"]): json.dumps({int(a): int(b) for a, b in sorted(zip(r["h"], r["len"]))})
      for r in hist.iter_rows(named=True)}
g = g.to_pandas()
g["dep_hour_hist"] = [hd[(a, b)] for a, b in zip(g.o_isl, g.d_isl)]
g["active_days"] = g.active_days.clip(upper=31)
g["trips_per_day"] = g.trips / 31
g["tpd_weekday"] = (g.trips - g.n_we) / days_wk
g["tpd_weekend"] = g.n_we / days_we
g["speed_class"] = np.where(g.od_kmh >= 25, "fast", "slow")
g["from_island_id"], g["to_island_id"] = g.o_isl, g.d_isl
g["from_name"] = g.from_island_id.map(lambda x: isl[x]["name"])
g["to_name"] = g.to_island_id.map(lambda x: isl[x]["name"])

acc = pl.read_csv(ACC).select(["origin_island_id", "status"]).unique()
noacc = set(acc.filter(pl.col("status") == "no_origin_access")["origin_island_id"].to_list())
g["touches_no_access_origin"] = g.from_island_id.isin(noacc) | g.to_island_id.isin(noacc)

# RTL durations per island pair
stops = pd.read_csv(R + "data/team-kandu/rtl_stops.csv")
ms = {str(s["code"]): s["islandId"] for s in m["stops"]}
stops["islandId"] = stops.code.astype(str).map(ms)
nm2isl = dict(zip(stops.name, stops.islandId))
con = pd.read_csv(R + "data/team-kandu/rtl_connections.csv")
con["a"] = con.from_stop.map(nm2isl)
con["b"] = con.to_stop.map(nm2isl)
con = con.dropna(subset=["a", "b"])
con = con[con.a != con.b]
rtl = {}
for a, b, mn in zip(con.a, con.b, con.shortest_minutes):
    rtl.setdefault((a, b), []).append(mn)


def rt(a, b):
    v = rtl.get((a, b)) or rtl.get((b, a))
    return float(np.median(v)) if v else np.nan


g["rtl_median_min"] = [rt(a, b) for a, b in zip(g.from_island_id, g.to_island_id)]
g["rtl_served"] = g.rtl_median_min.notna()

cols = ["from_island_id", "to_island_id", "from_name", "to_name", "trips_per_day", "active_days", "vessels", "median_min",
        "p80_min", "distance_km", "speed_class", "first_dep_hour_p10", "last_dep_hour_p90", "touches_no_access_origin",
        "rtl_served", "rtl_median_min"]
extra = ["trips", "tpd_weekday", "tpd_weekend", "top_vessel_share", "detour", "od_kmh", "dep_hour_hist"]
g = g.sort_values("trips", ascending=False)
reg = g[(g.trips_per_day >= 0.5) & (g.active_days >= 10) & (g.vessels >= 2) & (g.top_vessel_share <= 0.8)
        & (g.detour <= 1.6) & (g.distance_km >= 1.5)]
rnd = ["trips_per_day", "tpd_weekday", "tpd_weekend", "median_min", "p80_min", "distance_km", "first_dep_hour_p10",
       "last_dep_hour_p90", "rtl_median_min", "top_vessel_share", "detour", "od_kmh"]
for df, f in [(reg, "observed_sea_links.csv"), (g, "observed_sea_links_all_candidates.csv")]:
    x = df[cols + extra].copy()
    x[rnd] = x[rnd].round(2)
    x.to_csv(OUT + f, index=False)
print("candidates", len(g), "regular", len(reg))

pop = {k: v["population"] for k, v in isl.items()}
na_pop = sum(pop[i] for i in noacc if i in pop)
cov = (set(reg.from_island_id) | set(reg.to_island_id)) & noacc
loose = g[(g.trips >= 5) & (g.vessels >= 2)]
cov_loose = (set(loose.from_island_id) | set(loose.to_island_id)) & noacc
print("noacc", len(noacc), na_pop, "covered", len(cov), sum(pop[i] for i in cov), "loose", len(cov_loose), sum(pop[i] for i in cov_loose))
c = reg[reg.touches_no_access_origin]
print(len(c), "regular links touching noaccess;", int(c.rtl_served.sum()), "rtl served")
v = reg[reg.rtl_served]
r = v.median_min / v.rtl_median_min
print("validation n", len(v), "median ratio", r.median(), r.quantile([.1, .25, .75, .9]).tolist(),
      "corr", np.corrcoef(v.median_min, v.rtl_median_min)[0, 1], "med abs diff", (v.median_min - v.rtl_median_min).abs().median())
for k in ("fast", "slow"):
    s = v[v.speed_class == k]
    print(k, len(s), (s.median_min / s.rtl_median_min).median())
print("within +-25%:", ((r > .75) & (r < 1.25)).mean())
rp = {tuple(sorted(k)) for k in rtl}
print("rtl island pairs", len(rp), "with regular obs", len({tuple(sorted(x)) for x in zip(v.from_island_id, v.to_island_id)}))
pd.set_option("display.width", 250)
print(c[["from_name", "to_name", "trips_per_day", "active_days", "vessels", "median_min", "distance_km", "speed_class", "rtl_served"]].head(70).to_string())
na = pd.DataFrame({"id": sorted(noacc)})
na["name"] = na.id.map(lambda x: isl[x]["name"])
na["atoll"] = na.id.map(lambda x: isl[x]["atoll"])
na["pop"] = na.id.map(pop)
na["covered"] = na.id.isin(cov)
na["loose"] = na.id.isin(cov_loose)
na.to_csv(OUT + "observed_links_noaccess_coverage.csv", index=False)
print(na.groupby("atoll").agg(n=("id", "size"), cov=("covered", "sum"), loose=("loose", "sum"), pop=("pop", "sum")))
print(na[~na.covered].sort_values("pop", ascending=False).head(25).to_string())
json.dump(stats, open(OUT + "_snap_stats.json", "w"))
