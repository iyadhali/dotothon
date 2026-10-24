"""Extract HeiGIT HDX accessibility data into tidy CSVs + GeoJSON.
Usage: python -I heigit_extract.py <hdx-heigit-access dir> <output dir>"""
import sys, site, os
sys.path.append(site.getusersitepackages())
import pandas as pd, geopandas as gpd, pyogrio

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(OUT, "geojson"), exist_ok=True)
CATS = ["education", "hospitals", "primary_healthcare"]

# 1. combined long table (all categories, all admin levels, total + sub-populations)
long = pd.concat([pd.read_csv(os.path.join(SRC, f"MDV_{c}_access_long.csv")) for c in CATS], ignore_index=True)
long["range_type"] = long["range_type"].str.lower()
long["range_km"] = (long["range"] / 1000).where(long["range_type"] == "distance")
long["range_min"] = (long["range"] / 60).where(long["range_type"] == "time")
long.to_csv(os.path.join(OUT, "heigit_access_long_all.csv"), index=False)

# 2. national headline curve (total population)
tot = long[long["population_type"] == "total"]
adm0 = tot[tot["admin_level"] == "ADM0"][["category", "range_type", "range_km", "range_min", "population", "population_share"]]
adm0.sort_values(["category", "range_km", "range_min"]).to_csv(os.path.join(OUT, "heigit_headline_adm0.csv"), index=False)

# 3. per-unit summary at key thresholds (ADM1 = atolls/cities, ADM2 = islands where present)
THRESH = {"education": ("range_km", [5, 10, 50]), "hospitals": ("range_min", [10, 30, 60, 120]),
          "primary_healthcare": ("range_min", [10, 30, 60, 120])}
rows = []
for (lvl, name, uid, cat), g in tot[tot["admin_level"].isin(["ADM1", "ADM2"])].groupby(["admin_level", "name", "id", "category"]):
    col, ths = THRESH[cat]
    r = {"admin_level": lvl, "name": name, "id": uid, "iso": g["iso"].dropna().iloc[0] if g["iso"].notna().any() else "",
         "category": cat,
         "implied_total_pop": round((g["population"] / (g["population_share"] / 100)).median())}
    for t in ths:
        hit = g[g[col] <= t]
        unit = "km" if col == "range_km" else "min"
        r[f"share_within_{t}{unit}"] = hit["population_share"].max() if len(hit) else 0.0
    rows.append(r)
summ = pd.DataFrame(rows)
summ.to_csv(os.path.join(OUT, "heigit_unit_summary.csv"), index=False)

# 4. coverage matrix: which units appear in which category (absent = HeiGIT found no reachable facility)
cov = tot[tot["admin_level"].isin(["ADM1", "ADM2"])].groupby(["admin_level", "name", "category"]).size().unstack("category").notna()
cov = cov.reindex(columns=CATS, fill_value=False)
cov.to_csv(os.path.join(OUT, "heigit_coverage_matrix.csv"))

# 5. GeoJSON per gpkg layer (EPSG:4326) for QGIS / web maps
for c in CATS:
    gp = os.path.join(SRC, f"MDV_{c}_access.gpkg")
    for lyr, _ in pyogrio.list_layers(gp):
        g = gpd.read_file(gp, layer=lyr).to_crs(4326)
        g.to_file(os.path.join(OUT, "geojson", f"heigit_{c}_{lyr}.geojson"), driver="GeoJSON")
        print(f"{c}/{lyr}: {len(g)} features")

print("long rows", len(long))
print("\nADM0 headline:\n", adm0.to_string(index=False))
print("\nCoverage counts:\n", cov.groupby("admin_level").sum().to_string())
print("\nADM1 summary:\n", summ[summ["admin_level"] == "ADM1"].drop(columns=["id"]).to_string(index=False))
