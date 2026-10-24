"""Fetch Maldives OSM layers from the Overpass API and convert them to GeoJSON (EPSG:4326).

Usage:  python -I osm_fetch.py <out_dir> [layer ...]
Writes <out_dir>/raw/<layer>.json (raw Overpass) and <out_dir>/<layer>_<YYYYMMDD>.geojson
"""
import json
import sys
import time
import datetime as dt
from pathlib import Path

import requests
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import linemerge, polygonize, unary_union

BBOX = "-1.0,72.4,7.3,74.0"  # south,west,north,east - covers all Maldives atolls incl. Addu & Ihavandhippolhu
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

Q = {
    "islands": f"""
        nwr["place"~"^(island|islet)$"]({BBOX});
    """,
    "admin_boundaries": f"""
        relation["boundary"="administrative"]({BBOX});
    """,
    "places_settlements": f"""
        node["place"~"^(city|town|village|hamlet|suburb|neighbourhood|quarter|locality|isolated_dwelling)$"]({BBOX});
    """,
    "education": f"""
        nwr["amenity"~"^(school|university|college|kindergarten|language_school|training)$"]({BBOX});
        nwr["building"~"^(school|university|college)$"]({BBOX});
    """,
    "health": f"""
        nwr["amenity"~"^(hospital|clinic|doctors|dentist|pharmacy)$"]({BBOX});
        nwr["healthcare"]({BBOX});
        nwr["building"="hospital"]({BBOX});
    """,
    "sea_transport": f"""
        nwr["amenity"="ferry_terminal"]({BBOX});
        nwr["harbour"]({BBOX});
        nwr["leisure"="marina"]({BBOX});
        nwr["landuse"="harbour"]({BBOX});
        nwr["man_made"~"^(pier|quay|jetty)$"]({BBOX});
    """,
    "ferry_routes": f"""
        way["route"="ferry"]({BBOX});
    """,
    "air_transport": f"""
        nwr["aeroway"~"^(aerodrome|heliport|helipad|airstrip|runway|terminal|seaplane_base|water_runway)$"]({BBOX});
        nwr["seaplane"]({BBOX});
    """,
    "roads": f"""
        way["highway"]({BBOX});
    """,
    "landuse_resort_industrial": f"""
        nwr["tourism"~"^(resort|hotel|guest_house)$"]({BBOX});
        nwr["leisure"="resort"]({BBOX});
        nwr["landuse"~"^(industrial|military|port)$"]({BBOX});
    """,
}


def run_query(body: str) -> dict:
    q = f"[out:json][timeout:300][maxsize:536870912];\n(\n{body}\n);\nout body geom;"
    last = None
    for attempt in range(3):
        for ep in ENDPOINTS:
            try:
                print(f"  -> {ep}", flush=True)
                r = requests.post(ep, data={"data": q}, timeout=420,
                                  headers={"User-Agent": "MaldivesDatathon2026-research/1.0"})
                if r.status_code == 200 and r.text.lstrip().startswith("{"):
                    return r.json()
                last = f"{r.status_code} {r.text[:300]}"
                print("     failed:", last, flush=True)
            except Exception as e:  # noqa
                last = repr(e)
                print("     error:", last, flush=True)
        time.sleep(30)
    raise RuntimeError(last)


def way_geom(el, prefer_area=True):
    pts = [(p["lon"], p["lat"]) for p in el.get("geometry", []) if p]
    if len(pts) < 2:
        return None
    t = el.get("tags", {})
    closed = len(pts) >= 4 and pts[0] == pts[-1]
    linear_keys = ("highway", "route", "barrier")
    is_area = closed and prefer_area and (t.get("area") == "yes" or not any(k in t for k in linear_keys)) \
        and t.get("man_made") not in ("breakwater", "groyne") and t.get("aeroway") != "runway"
    if t.get("highway") in ("pedestrian", "platform") and t.get("area") == "yes":
        is_area = True
    if is_area:
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        return poly
    return LineString(pts)


def _parts(g):
    return list(g.geoms) if hasattr(g, "geoms") else [g]


def relation_geom(el):
    t = el.get("tags", {})
    outers, inners, lines = [], [], []
    for m in el.get("members", []):
        if m.get("type") != "way" or not m.get("geometry"):
            continue
        pts = [(p["lon"], p["lat"]) for p in m["geometry"] if p]
        if len(pts) < 2:
            continue
        ls = LineString(pts)
        (inners if m.get("role") == "inner" else outers).append(ls)
        lines.append(ls)
    if t.get("type") in ("multipolygon", "boundary") or "place" in t:
        def polys(ls_list):
            if not ls_list:
                return []
            return list(polygonize(_parts(unary_union(ls_list))))
        op = polys(outers)
        ip = polys(inners)
        if op:
            g = unary_union(op)
            if ip:
                g = g.difference(unary_union(ip))
            if not g.is_valid:
                g = g.buffer(0)
            return g
    if lines:
        parts = _parts(unary_union(lines))
        return linemerge(parts) if len(parts) > 1 else parts[0]
    if el.get("center"):
        return Point(el["center"]["lon"], el["center"]["lat"])
    return None


def to_features(data):
    feats = []
    seen = set()
    for el in data.get("elements", []):
        key = (el["type"], el["id"])
        if key in seen:
            continue
        seen.add(key)
        if el["type"] == "node":
            g = Point(el["lon"], el["lat"])
        elif el["type"] == "way":
            g = way_geom(el)
        else:
            g = relation_geom(el)
        if g is None or g.is_empty:
            continue
        c = g.representative_point() if g.geom_type != "Point" else g
        props = {"osm_type": el["type"], "osm_id": el["id"],
                 "osm_url": f"https://www.openstreetmap.org/{el['type']}/{el['id']}",
                 "geom_type": g.geom_type, "rep_lon": round(c.x, 7), "rep_lat": round(c.y, 7)}
        props.update(el.get("tags", {}))
        feats.append({"type": "Feature", "geometry": mapping(g), "properties": props})
    return feats


def main():
    out = Path(sys.argv[1])
    layers = sys.argv[2:] or list(Q)
    (out / "raw").mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    for name in layers:
        print(f"[{name}]", flush=True)
        raw_path = out / "raw" / f"{name}.json"
        if raw_path.exists():
            data = json.loads(raw_path.read_text(encoding="utf-8"))
        else:
            data = run_query(Q[name])
            raw_path.write_text(json.dumps(data), encoding="utf-8")
        feats = to_features(data)
        fc = {"type": "FeatureCollection",
              "name": name,
              "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
              "osm_base": data.get("osm3s", {}).get("timestamp_osm_base"),
              "features": feats}
        p = out / f"{name}_{stamp}.geojson"
        p.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
        print(f"  {len(data.get('elements', []))} elements -> {len(feats)} features -> {p.name} "
              f"(osm_base {fc['osm_base']})", flush=True)
        time.sleep(5)


if __name__ == "__main__":
    main()
