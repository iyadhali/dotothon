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


def main() -> None:
    acc = pd.read_csv(ROOT / "data" / "derived" / "island_access.csv")
    nodes = pd.read_csv(ROOT / "data" / "derived" / "sea_nodes.csv")
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
    (OUT.parent / "islands_points.json").write_text(json.dumps(pts, separators=(",", ":")))
    print(f"wrote islands_points.json — {len(pts)} points, "
          f"{(OUT.parent / 'islands_points.json').stat().st_size / 1e3:.0f} KB")
    bands = pd.Series([x["properties"]["band"] for x in feats]).value_counts().to_dict()
    print(f"wrote {OUT.relative_to(ROOT)} — {len(feats)} features, "
          f"{OUT.stat().st_size / 1e6:.2f} MB, bands {bands}")


if __name__ == "__main__":
    main()
