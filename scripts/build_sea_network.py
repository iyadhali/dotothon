#!/usr/bin/env python3
"""
Build an empirical island-to-island SEA network from the FollowMe GPS traces (Aug 2025).

Method
------
1. Clean: keep points inside the Maldives (lat 0-7.5, lng 72-74); order each device by
   `timestamp` (the only time field with a time of day) — `device_date` is used only for QA.
2. Stays: a run of >=5 consecutive polls with speed <= 2 knots (and no >30 min gap) is a
   "stay". Its location is the median of the run's coordinates.
3. Trips: two consecutive stays of the same device form a directed trip; the travel time is
   the gap between leaving the first and arriving at the second.
4. Nodes: every stay is snapped to the nearest OCHA ADM2 island centroid (1,556 islands)
   within 6 km. Islands that are not in the Census spine are labelled uninhabited/resort.
5. Output: node table + directed edge table with trip counts and travel-time quantiles.

Usage: python scripts/build_sea_network.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GPS = ROOT / "data" / "FollowMe_august_2025"
OUT = ROOT / "data" / "derived"
OUT.mkdir(parents=True, exist_ok=True)

COLS = ["imei", "timestamp", "device_date", "latitude", "longitude", "speed"]
LAT0, LAT1, LNG0, LNG1 = 0.0, 7.5, 72.0, 74.0
STILL_KNOTS = 2.0        # at or below = stationary
MIN_POLLS = 5            # polls needed to call it a stay
SNAP_KM = 6.0            # max distance from a stay to an island centroid
R_EARTH = 6371.0088


def haversine(lat1, lon1, lat2, lon2):
    p = np.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin(dlon / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def load_islands() -> pd.DataFrame:
    """OCHA ADM2 centroids, flagged with Census population where the join exists."""
    geo = json.loads((ROOT / "data/external/mdv_admin2_islands.geojson").read_text())
    g = pd.DataFrame([f["properties"] for f in geo["features"]])[
        ["adm2_name", "adm2_pcode", "adm1_name", "center_lat", "center_lon", "area_sqkm"]
    ].rename(columns={"adm2_name": "name", "adm1_name": "atoll"})
    spine = pd.read_csv(ROOT / "data/external/island_spine.csv")
    spine = spine[spine.island_pcode.notna() & (spine.island_pcode != "MV")]
    g = g.merge(spine[["island_pcode", "population", "child_0_17", "atoll_name"]],
                left_on="adm2_pcode", right_on="island_pcode", how="left")
    g["type"] = np.where(g.population.notna(), "inhabited",
                np.where(g.area_sqkm > 0.02, "uninhabited", "resort_or_small"))
    # 423 ADM2 features are code-named lagoons / reclaimed areas (LD1203, LG...), not islands
    g["is_island"] = ~g.name.astype(str).str.match(r"^[A-Z]{2}\d+$")
    # Malé city is not an ADM2 island polygon — add it explicitly, it dominates traffic
    male = pd.DataFrame([dict(name="Malé City", adm2_pcode="MLE", atoll="Male",
                              center_lat=4.175495, center_lon=73.509347, area_sqkm=8.0,
                              island_pcode="MLE", population=211908, child_0_17=np.nan,
                              atoll_name="Male (city)", type="inhabited", is_island=True)])
    return pd.concat([g, male], ignore_index=True)


def read_day(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, usecols=COLS, dtype={"imei": "str"})
    d = d[d.latitude.between(LAT0, LAT1) & d.longitude.between(LNG0, LNG1)]
    d["ts"] = pd.to_datetime(d.timestamp, errors="coerce")
    d = d.dropna(subset=["ts", "latitude", "longitude"])
    d["speed"] = pd.to_numeric(d.speed, errors="coerce").fillna(0.0)
    d = d.sort_values(["imei", "ts"], kind="mergesort")
    return d[["imei", "ts", "latitude", "longitude", "speed"]]


def extract_stays(d: pd.DataFrame) -> pd.DataFrame:
    stat = d.speed.le(STILL_KNOTS).to_numpy()
    new_dev = d.imei.ne(d.imei.shift()).to_numpy()
    gap = d.ts.diff().dt.total_seconds().fillna(0).gt(1800).to_numpy()
    new_state = np.r_[True, stat[1:] != stat[:-1]]
    run = np.cumsum(new_dev | gap | new_state)
    d = d.assign(stat=stat, run=run)
    s = (d[d.stat].groupby("run", sort=False)
         .agg(imei=("imei", "first"), n=("ts", "size"),
              lat=("latitude", "median"), lon=("longitude", "median"),
              t0=("ts", "min"), t1=("ts", "max")))
    s = s[(s.n >= MIN_POLLS) & ((s.t1 - s.t0).dt.total_seconds() >= 120)]
    return s.sort_values(["imei", "t0"])


def trips_from_stays(s: pd.DataFrame) -> pd.DataFrame:
    s = s.reset_index(drop=True)
    same = s.imei.eq(s.imei.shift(-1))
    out = pd.DataFrame({
        "imei": s.imei, "lat1": s.lat, "lon1": s.lon,
        "lat2": s.lat.shift(-1), "lon2": s.lon.shift(-1),
        "dep": s.t1, "arr": s.t0.shift(-1),
    })[same.to_numpy()]
    out["hours"] = (out.arr - out.dep).dt.total_seconds() / 3600
    out = out[(out.hours > 0.02) & (out.hours < 24)]
    out["dep_hour"] = out.dep.dt.hour
    out["km"] = haversine(out.lat1.to_numpy(), out.lon1.to_numpy(),
                          out.lat2.to_numpy(), out.lon2.to_numpy())
    return out[out.km > 0.8]


def snap(df: pd.DataFrame, nodes: pd.DataFrame, lat_col: str, lon_col: str) -> np.ndarray:
    clat = nodes.center_lat.to_numpy()
    clon = nodes.center_lon.to_numpy()
    la = df[lat_col].to_numpy()
    lo = df[lon_col].to_numpy()
    best_d = np.full(len(df), np.inf)
    best_i = np.full(len(df), -1)
    for s in range(0, len(nodes), 256):
        d = haversine(la[:, None], lo[:, None], clat[None, s:s + 256], clon[None, s:s + 256])
        m = d.argmin(axis=1)
        v = d[np.arange(len(df)), m]
        upd = v < best_d
        best_d[upd] = v[upd]
        best_i[upd] = m[upd] + s
    best_i[best_d > SNAP_KM] = -1
    return best_i


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="process only the first N day files")
    ap.add_argument("--gps", type=Path, default=GPS, help="folder of daily FollowMe CSVs")
    args = ap.parse_args()

    nodes_all = load_islands()
    nodes = nodes_all[nodes_all.is_island].reset_index(drop=True)
    print(f"island nodes: {len(nodes):,} ({int((nodes.type=='inhabited').sum())} inhabited) "
          f"of {len(nodes_all):,} ADM2 features")
    files = sorted(args.gps.glob("*.csv"), key=lambda p: int(p.stem))
    if not files:
        raise SystemExit(f"no CSVs in {args.gps}")
    if args.limit:
        files = files[: args.limit]

    all_trips, stat_rows = [], []
    for i, f in enumerate(files, 1):
        d = read_day(f)
        s = extract_stays(d)
        t = trips_from_stays(s)
        all_trips.append(t)
        stat_rows.append(dict(file=f.name, points=len(d), devices=d.imei.nunique(),
                              stays=len(s), trips=len(t)))
        print(f"[{i:>2}/{len(files)}] {f.name:<7} points {len(d):>7,}  stays {len(s):>6,}  trips {len(t):>6,}",
              flush=True)

    trips = pd.concat(all_trips, ignore_index=True)
    trips["from"] = snap(trips, nodes, "lat1", "lon1")
    trips["to"] = snap(trips, nodes, "lat2", "lon2")
    trips = trips[(trips["from"] >= 0) & (trips["to"] >= 0)]
    trips["from_id"] = nodes.adm2_pcode.to_numpy()[trips["from"]]
    trips["to_id"] = nodes.adm2_pcode.to_numpy()[trips["to"]]
    trips = trips[trips.from_id != trips.to_id]          # drop intra-island wander
    trips["knots"] = trips.km / (trips.hours * 1.852)
    # a crossing must be physically possible: 0.5 kn (drifting) .. 55 kn (fastest speedboat)
    before = len(trips)
    trips = trips[trips.knots.between(0.5, 55)].copy()
    print(f"dropped {before - len(trips):,} physically impossible crossings "
          f"(implied speed outside 0.5-55 kn)")

    edges = (trips.groupby(["from_id", "to_id"])
             .agg(trips=("km", "size"), devices=("imei", "nunique"),
                  med_hours=("hours", "median"),
                  p10_hours=("hours", lambda x: x.quantile(0.10)),
                  p90_hours=("hours", lambda x: x.quantile(0.90)),
                  med_km=("km", "median"), med_knots=("knots", "median"),
                  am_share=("dep_hour", lambda x: float(((x >= 5) & (x <= 9)).mean())),
                  pm_share=("dep_hour", lambda x: float(((x >= 15) & (x <= 19)).mean())))
             .reset_index()
             .sort_values("trips", ascending=False))

    node_out = nodes[["adm2_pcode", "name", "atoll", "type", "population", "child_0_17",
                      "center_lat", "center_lon"]].rename(
        columns={"adm2_pcode": "node_id", "center_lat": "lat", "center_lon": "lon"})

    edges.to_csv(OUT / "sea_edges.csv", index=False)
    node_out.to_csv(OUT / "sea_nodes.csv", index=False)
    pd.DataFrame(stat_rows).to_csv(OUT / "sea_build_log.csv", index=False)

    print("\n" + "=" * 60)
    print(f"stays {sum(r['stays'] for r in stat_rows):,} | trips {len(trips):,} | "
          f"devices {trips.imei.nunique()} | directed edges {len(edges):,}")
    print(f"undirected island pairs {len(edges.assign(k=edges[['from_id','to_id']].min(axis=1)+'|'+edges[['from_id','to_id']].max(axis=1)).k.unique()):,}")
    print(f"median crossing speed {trips.knots.median():.1f} kn | "
          f"median crossing time {trips.hours.median():.2f} h")
    print("\ntop 12 edges by trips:")
    top = edges.head(12).merge(node_out[["node_id", "name"]], left_on="from_id", right_on="node_id")
    top = top.merge(node_out[["node_id", "name"]], left_on="to_id", right_on="node_id",
                    suffixes=("_from", "_to"))
    print(top[["name_from", "name_to", "trips", "devices", "med_hours", "med_km"]].to_string(index=False))
    print(f"\nwrote {OUT/'sea_edges.csv'} and {OUT/'sea_nodes.csv'}")


if __name__ == "__main__":
    main()
