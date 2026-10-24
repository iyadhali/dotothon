"""Build a single island master layer (COD-AB 1,556 islands) with census population and an island status class.

Usage: python -I build_island_status.py <external_dir>
Inputs  (under <external_dir>):
  _derived/islands_codab_with_census2022.gpkg      (from census_island_join.py)
  _derived/yb2025_t10.14_resorts.csv               (from yearbook_tidy.py)
  _derived/yb2025_t1.5_island_area_pop_distance.csv
  osm-overpass/landuse_resort_industrial_*.geojson, osm-overpass/islands_*.geojson
  ourairports/airports_MV.csv
Output:
  _derived/mdv_islands_master.gpkg  layers: islands (polygons), island_points (representative points)
  _derived/mdv_islands_master.csv   (attributes, no geometry)
"""
import glob
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # own scripts dir only (python -I drops it)
from census_island_join import norm_name, ATOLL  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
EXT = Path(sys.argv[1])
D = EXT / "_derived"
UTM = 32643  # WGS 84 / UTM zone 43N - metric CRS covering the Maldives

isl = gpd.read_file(D / "islands_codab_with_census2022.gpkg", layer="islands")
isl["name_key"] = isl["adm2_name"].map(norm_name)

import re  # noqa: E402
from rapidfuzz import fuzz, process  # noqa: E402


def match_to_codab(names, atoll_pcodes, min_score=85):
    """Return (adm2_pcode, method) per row: exact key -> 'A and B' parts -> fuzzy within atoll."""
    out = []
    for nm, ap in zip(names, atoll_pcodes):
        cand = isl[isl.adm1_pcode == ap]
        if not isinstance(nm, str) or cand.empty:
            out.append((None, "UNMATCHED"))
            continue
        res = None
        for i, part in enumerate([nm] + re.split(r"\s+(?:and|&)\s+|\s*&\s*", nm)):
            k = norm_name(part)
            hit = cand[cand.name_key == k]
            if len(hit):
                res = (hit.sort_values("area_sqkm", ascending=False).iloc[0].adm2_pcode, "exact_key" if i == 0 else "part_exact")
                break
        if res is None:
            b = process.extractOne(norm_name(nm), cand.name_key.tolist(), scorer=fuzz.ratio)
            if b and b[1] >= min_score:
                res = (cand.iloc[b[2]].adm2_pcode, f"fuzzy_{b[1]:.0f}")
        out.append(res or (None, "UNMATCHED"))
    return out

# --- resorts (MBS yearbook 2025 table 10.14; source: Ministry of Tourism)
res = pd.read_csv(D / "yb2025_t10.14_resorts.csv")
canon = {k.lower(): k for k in ATOLL}
res["atoll_abbr"] = res["atoll_abbr"].map(lambda a: canon.get(str(a).lower(), a))
res["adm1_pcode"] = res["atoll_abbr"].map(lambda a: ATOLL.get(a, (None,))[0])
res["name_key"] = res["island"].map(norm_name)
m = res.copy()
mm = match_to_codab(m.island, m.adm1_pcode)
m["adm2_pcode"], m["match_method"] = [a for a, _ in mm], [b for _, b in mm]
print("resort list rows:", len(res), " matched to COD-AB island by atoll+name:", m.adm2_pcode.notna().sum())
u = m[m.adm2_pcode.isna()]
print("  unmatched resorts:", "; ".join((u.atoll_abbr.fillna("?").astype(str) + " " + u.island.fillna("?").astype(str)).tolist()))
m[["atoll_abbr", "resort", "island", "adm2_pcode", "match_method", "beds_2024", "operating_in_latest_year"]].to_csv(
    D / "yb2025_resorts_to_codab_crosswalk.csv", index=False, encoding="utf-8")
rgrp = m[m.adm2_pcode.notna()].groupby("adm2_pcode").agg(
    resort_names=("resort", "; ".join), resort_beds_2024=("beds_2024", "sum"),
    resort_operating_2024=("operating_in_latest_year", "max")).reset_index()
isl = isl.merge(rgrp, on="adm2_pcode", how="left")

# --- OSM hints (resort / industrial landuse, island names)
isl_m = isl.to_crs(UTM)
lu_files = sorted(glob.glob(str(EXT / "osm-overpass" / "landuse_resort_industrial_*.geojson")))
if lu_files:
    lu = gpd.read_file(lu_files[-1]).to_crs(UTM)
    for col in ("tourism", "leisure", "landuse"):
        if col not in lu:
            lu[col] = None
    resort_osm = lu[(lu.tourism == "resort") | (lu.leisure == "resort")]
    ind = lu[lu.landuse.isin(["industrial", "port"]) & lu.geom_type.isin(["Polygon", "MultiPolygon"])]
    hit = gpd.sjoin(isl_m[["adm2_pcode", "geometry"]], resort_osm[["geometry"]], predicate="intersects", how="inner")
    isl["osm_resort_hint"] = isl.adm2_pcode.isin(hit.adm2_pcode)
    inter = gpd.overlay(isl_m[["adm2_pcode", "geometry"]], ind[["geometry"]], how="intersection", keep_geom_type=True)
    inter["a"] = inter.area
    share = (inter.groupby("adm2_pcode").a.sum() / isl_m.set_index("adm2_pcode").area).dropna()
    isl["osm_industrial_share"] = isl.adm2_pcode.map(share).fillna(0).round(3)
else:
    isl["osm_resort_hint"] = False
    isl["osm_industrial_share"] = 0.0

osm_isl_files = sorted(glob.glob(str(EXT / "osm-overpass" / "islands_*.geojson")))
if osm_isl_files:
    oi = gpd.read_file(osm_isl_files[-1])
    oi = oi[oi.geom_type.isin(["Polygon", "MultiPolygon"])].to_crs(UTM)
    pts = isl_m[["adm2_pcode", "geometry"]].copy()
    pts["geometry"] = pts.representative_point()
    j = gpd.sjoin(pts, oi[["osm_id", "name", "geometry"]], predicate="within", how="left").drop_duplicates("adm2_pcode")
    isl["osm_island_id"] = isl.adm2_pcode.map(j.set_index("adm2_pcode").osm_id)
    isl["osm_island_name"] = isl.adm2_pcode.map(j.set_index("adm2_pcode")["name"])

# --- airports (OurAirports, excl. seaplane bases), within 1 km of island
ap = pd.read_csv(EXT / "ourairports" / "airports_MV.csv", keep_default_na=False)
ap = gpd.GeoDataFrame(ap, geometry=gpd.points_from_xy(ap.longitude_deg.astype(float), ap.latitude_deg.astype(float)), crs=4326).to_crs(UTM)
ap_land = ap[ap["type"] != "seaplane_base"]
near = gpd.sjoin_nearest(ap_land[["ident", "iata_code", "name", "geometry"]], isl_m[["adm2_pcode", "geometry"]],
                         max_distance=1000, distance_col="d_m")
agg = near.groupby("adm2_pcode").agg(airport_names=("name", "; ".join), airport_iata=("iata_code", lambda s: "; ".join(x for x in s if x))).reset_index()
isl = isl.merge(agg, on="adm2_pcode", how="left")

# --- yearbook 1.5 distance to Male (inhabited islands)
t15 = pd.read_csv(D / "yb2025_t1.5_island_area_pop_distance.csv")
t15["atoll_abbr"] = t15["atoll_abbr"].map(lambda a: canon.get(str(a).lower(), a))
t15["adm1_pcode"] = t15["atoll_abbr"].map(lambda a: ATOLL.get(a, (None,))[0])
t15["name_key"] = t15["island"].map(norm_name)
fix = {("MV021", norm_name("Male'")): "MV021001", ("MV021", norm_name("Villingili")): "MV021002",
       ("MV021", norm_name("Hulhumale'")): "MV021003", ("MV019", norm_name("Meedho")): "MV019001"}
cw = pd.read_csv(D / "census2022_to_codab_crosswalk.csv")
cw["name_key"] = cw.census_island.map(norm_name)
cw = cw.dropna(subset=["adm2_pcode"]).drop_duplicates(["adm1_pcode", "name_key"])
t15 = t15.merge(cw[["adm1_pcode", "name_key", "adm2_pcode"]], on=["adm1_pcode", "name_key"], how="left")
t15["adm2_pcode"] = [fix.get((a, k), p) for a, k, p in zip(t15.adm1_pcode, t15.name_key, t15.adm2_pcode)]
miss = t15.adm2_pcode.isna()
t15.loc[miss, "adm2_pcode"] = [a for a, _ in match_to_codab(t15[miss].island, t15[miss].adm1_pcode, 80)]
t15.loc[(t15.adm1_pcode == "MV015") & (t15.name_key == norm_name("Gan")), "adm2_pcode"] = "MV015013"
print("yearbook 1.5 rows:", len(t15), " matched:", t15.adm2_pcode.notna().sum(),
      " unmatched:", t15[t15.adm2_pcode.isna()].island.tolist())
isl = isl.merge(t15.dropna(subset=["adm2_pcode"]).drop_duplicates("adm2_pcode")[
    ["adm2_pcode", "is_atoll_capital", "land_area_ha", "dist_to_male_km"]].rename(
    columns={"land_area_ha": "yb_land_area_ha", "dist_to_male_km": "yb_dist_to_male_km"}), on="adm2_pcode", how="left")


# --- status
def status(r):
    if r.inhabited_census2022:
        return "inhabited"
    if isinstance(r.resort_names, str):
        return "resort" if r.resort_operating_2024 else "resort_closed_or_planned"
    if isinstance(r.airport_names, str):
        return "airport"
    if r.osm_resort_hint:
        return "resort_osm_hint"
    if r.osm_industrial_share >= 0.25:
        return "industrial_osm_hint"
    return "uninhabited_or_unknown"


isl["status"] = isl.apply(status, axis=1)

# --- WorldPop 2022 constrained (R2025A) zonal sum per island (all_touched: tiny islands < 1 pixel)
wp = EXT / "worldpop" / "mdv_pop_2022_CN_100m_R2025A_v1.tif"
if wp.exists():
    from rasterstats import zonal_stats
    zs = zonal_stats(isl.geometry, str(wp), stats=["sum"], all_touched=True, nodata=-99999)
    isl["worldpop2022_sum"] = [round(z["sum"] or 0, 1) for z in zs]
isl["is_atoll_capital"] = isl["is_atoll_capital"].fillna(False).astype(bool)
isl["join_key"] = isl["adm1_pcode"] + "|" + isl["name_key"]
print(isl.status.value_counts().to_string())

isl.to_file(D / "mdv_islands_master.gpkg", layer="islands", driver="GPKG")
pts = isl.copy()
pts["geometry"] = isl.to_crs(UTM).representative_point().to_crs(4326)
pts.to_file(D / "mdv_islands_master.gpkg", layer="island_points", driver="GPKG")
pts["lon"], pts["lat"] = pts.geometry.x.round(6), pts.geometry.y.round(6)
pts.drop(columns="geometry").to_csv(D / "mdv_islands_master.csv", index=False, encoding="utf-8")
print("islands:", len(isl), " inhabited pop2022 sum:", int(isl.pop2022.sum()))
