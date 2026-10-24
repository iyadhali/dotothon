"""Pack the OSM GeoJSON layers into one GeoPackage, split by geometry family (_pt / _ln / _pl) for QGIS,
and print per-layer tag summaries.
Usage: python -I osm_to_gpkg.py <osm_dir> <stamp YYYYMMDD>
"""
import collections
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
D, STAMP = Path(sys.argv[1]), sys.argv[2]
out = D / f"osm_maldives_{STAMP}.gpkg"
if out.exists():
    out.unlink()
FAM = {"Point": "pt", "MultiPoint": "pt", "LineString": "ln", "MultiLineString": "ln",
       "Polygon": "pl", "MultiPolygon": "pl"}
KEYS = ["amenity", "healthcare", "building", "aeroway", "harbour", "man_made", "leisure", "landuse",
        "tourism", "highway", "place", "admin_level", "route"]
for f in sorted(D.glob(f"*_{STAMP}.geojson")):
    name = f.stem.replace(f"_{STAMP}", "")
    g = gpd.read_file(f)
    # keep the most useful columns + all name:* (GPKG handles many columns, but trim very sparse ones)
    keep = [c for c in g.columns if c == "geometry" or g[c].notna().mean() >= 0.01 or c.startswith("name")
            or c in KEYS or c in ("osm_type", "osm_id", "osm_url", "rep_lon", "rep_lat")]
    g = g[keep]
    fams = g.geom_type.map(FAM)
    summ = []
    for fam in ("pt", "ln", "pl"):
        sub = g[fams == fam]
        if len(sub):
            sub.to_file(out, layer=f"{name}_{fam}", driver="GPKG")
            summ.append(f"{fam}:{len(sub)}")
    tagsum = []
    for k in KEYS:
        if k in g:
            c = collections.Counter(v for v in g[k] if isinstance(v, str))
            if c:
                tagsum.append(f"{k}=" + ", ".join(f"{a}:{b}" for a, b in c.most_common(8)))
    named = int(g["name"].notna().sum()) if "name" in g else 0
    print(f"## {name}: {len(g)} features ({' '.join(summ)}), named {named}")
    for t in tagsum:
        print("   ", t)
print("wrote", out)
