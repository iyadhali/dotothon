#!/usr/bin/env python3
"""
Build the small GeoJSON the web map serves.

The OCHA source has 1,556 features (17 MB). The map only needs the 187 inhabited islands, with
the accessibility attributes attached, and coordinates rounded to 5 decimal places (~1 m), which
drops the file to a size a phone on venue wifi can load.

Run before starting the server:  python web/build_web_data.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "access" / "static" / "access" / "islands.geojson"


def band(h, own: bool) -> str:
    if h is None or (isinstance(h, float) and h != h):
        return "unknown"
    if own or h == 0:
        return "own"
    if h <= 2:
        return "under2"
    if h <= 4:
        return "under4"
    if h <= 8:
        return "under8"
    return "over8"


def round_coords(c, dp=5):
    if isinstance(c, (int, float)):
        return round(c, dp)
    return [round_coords(x, dp) for x in c]


def _flatten_pairs(c, out: list) -> None:
    """Collect every [lon, lat] leaf from a (Multi)Polygon coordinate tree."""
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        out.append(c)
        return
    for x in c:
        _flatten_pairs(x, out)


def write_atolls() -> None:
    """Atoll outlines, so the national map shows the country's 21 rings and not just dots."""
    src = json.loads((ROOT / "data" / "external" / "mdv_admin1_atolls.geojson").read_text())
    feats = []
    for f in src["features"]:
        p = f["properties"]
        name = p.get("adm1_name") or p.get("adm1_pcode")
        geom = f["geometry"]
        pts: list = []
        _flatten_pairs(geom["coordinates"], pts)
        # a rough centroid is enough for a label
        lat = sum(x[1] for x in pts) / len(pts)
        lon = sum(x[0] for x in pts) / len(pts)
        feats.append({
            "type": "Feature",
            "geometry": {"type": geom["type"], "coordinates": round_coords(geom["coordinates"], 4)},
            "properties": {"name": name, "code": p.get("adm1_pcode"),
                           "centroid": [round(lat, 4), round(lon, 4)],
                           "upright": p.get("adm1_name")},
        })
    out = OUT.parent / "atolls.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
    print(f"wrote {out.name} — {len(feats)} atolls, {out.stat().st_size / 1e3:.0f} KB")


def main() -> None:
    acc = pd.read_csv(ROOT / "data" / "derived" / "island_access.csv")
    nodes = pd.read_csv(ROOT / "data" / "derived" / "sea_nodes.csv")
    if "lat" not in acc.columns:            # island_access carries its own coordinates
        acc = acc.merge(nodes[["node_id", "lat", "lon"]], on="node_id", how="left")
    by_id = acc.set_index("node_id")

    src = json.loads((ROOT / "data" / "external" / "mdv_admin2_islands.geojson").read_text())
    feats = []
    for f in src["features"]:
        p = f["properties"]
        pcode = p.get("adm2_pcode")
        if pcode not in by_id.index:
            continue
        r = by_id.loc[pcode]
        hours = None if pd.isna(r.hours_to_hs) else float(r.hours_to_hs)
        feats.append({
            "type": "Feature",
            "geometry": {"type": f["geometry"]["type"],
                         "coordinates": round_coords(f["geometry"]["coordinates"])},
            "properties": {
                "id": pcode,
                "name": p["adm2_name"],
                "atoll": p["adm1_name"],
                "pop": int(r.population),
                "kids": int(r.child_0_17),
                "hours": hours,
                "own": bool(r.has_own_higher_secondary),
                "band": band(hours, bool(r.has_own_higher_secondary)),
                "nbrs": int(r.sea_neighbours),
                "reach": int(r.islands_reachable),
                "lat": None if pd.isna(r.lat) else round(float(r.lat), 5),
                "lon": None if pd.isna(r.lon) else round(float(r.lon), 5),
            },
        })

    # per-island hours for every service type, so the map can be recoloured client-side
    sa_path = ROOT / "data" / "derived" / "service_access.csv"
    if sa_path.exists():
        sa = pd.read_csv(sa_path)
        metrics = {f"{cat}:{t}": g.set_index("node_id").hours.to_dict()
                   for (cat, t), g in sa.groupby(["category", "service_type"])}
        for f in feats:
            f["properties"]["m"] = {
                k: (None if pd.isna(v.get(f["properties"]["id"])) else round(float(v[f["properties"]["id"]]), 2))
                for k, v in metrics.items()}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))

    # The national map plots ~9 px circles at that zoom, so a points file is what the browser
    # actually needs: 30 KB instead of 2.2 MB, and it keeps the page instant on venue wifi.
    pts = [{"id": f["properties"]["id"], "name": f["properties"]["name"],
            "atoll": f["properties"]["atoll"], "pop": f["properties"]["pop"],
            "hours": f["properties"]["hours"], "own": f["properties"]["own"],
            "band": f["properties"]["band"],
            "lat": f["properties"]["lat"], "lon": f["properties"]["lon"]}
           for f in feats if f["properties"]["lat"] is not None]
    # Malé is a city, not an OCHA island polygon, so it has no feature — but without a point for
    # it no journey to or from the capital can be drawn on the map.
    male = acc[acc.node_id == "MLE"]
    if len(male):
        r = male.iloc[0]
        pts.append({"id": "MLE", "name": "Malé City", "atoll": "Male",
                    "pop": int(r.population), "hours": 0.0, "own": True, "band": "own",
                    "lat": round(float(r.lat), 5), "lon": round(float(r.lon), 5)})
    # per-island hours for every service type, so the map can be recoloured client-side
    sa_path = ROOT / "data" / "derived" / "service_access.csv"
    if sa_path.exists():
        sa = pd.read_csv(sa_path)
        metrics = {f"{cat}:{t}": g.set_index("node_id").hours.to_dict()
                   for (cat, t), g in sa.groupby(["category", "service_type"])}
        for p in pts:
            p["m"] = {k: (None if pd.isna(v.get(p["id"])) else round(float(v[p["id"]]), 2))
                      for k, v in metrics.items()}
    (OUT.parent / "islands_points.json").write_text(json.dumps(pts, separators=(",", ":")))
    print(f"wrote islands_points.json — {len(pts)} points, "
          f"{(OUT.parent / 'islands_points.json').stat().st_size / 1e3:.0f} KB")
    write_atolls()
    write_links()

    bands = pd.Series([x["properties"]["band"] for x in feats]).value_counts().to_dict()
    print(f"wrote {OUT.relative_to(ROOT)} — {len(feats)} features, "
          f"{OUT.stat().st_size / 1e6:.2f} MB, bands {bands}")


def write_links():
    """Every observed island pair as a line, so the map can show the measured network itself.

    One undirected line per pair (the sea_edges file stores both directions), keeping pairs that
    were seen at least twice — a single trip is as likely to be a GPS artefact as a route.
    """
    root = ROOT
    edges = pd.read_csv(root / "data" / "derived" / "sea_edges.csv")
    nodes = pd.read_csv(root / "data" / "derived" / "sea_nodes.csv").set_index("node_id")
    edges["key"] = [tuple(sorted((a, b))) for a, b in zip(edges.from_id, edges.to_id)]
    pairs = (edges.groupby("key")
             .agg(trips=("trips", "sum"), hours=("med_hours", "median")).reset_index())
    pairs = pairs[pairs.trips >= 2]
    feats = []
    for r in pairs.itertuples(index=False):
        a, b = r.key
        if a not in nodes.index or b not in nodes.index:
            continue
        feats.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [
                [round(float(nodes.loc[a, "lon"]), 4), round(float(nodes.loc[a, "lat"]), 4)],
                [round(float(nodes.loc[b, "lon"]), 4), round(float(nodes.loc[b, "lat"]), 4)]]},
            "properties": {"trips": int(r.trips), "hours": round(float(r.hours), 2)},
        })
    out = OUT.parent / "links.geojson"
    out.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
    print(f"wrote links.geojson — {len(feats)} observed pairs, {out.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
