"""HeiGIT accessibility summary. Usage: python -I heigit_summary.py <hdx-heigit-access dir>"""
import sys, site, os
sys.path.append(site.getusersitepackages())
import pandas as pd, geopandas as gpd, pyogrio

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 500)
D = sys.argv[1]
for cat in ["education", "hospitals", "primary_healthcare"]:
    gp = os.path.join(D, f"MDV_{cat}_access.gpkg")
    print(f"\n{'#' * 90}\n{cat}")
    for lyr, _ in pyogrio.list_layers(gp):
        g = gpd.read_file(gp, layer=lyr)
        g["implied_total_pop"] = (g["population"] / (g["population_share"] / 100)).round(0)
        gm = g.to_crs(32643)
        g["area_km2"] = gm.area / 1e6
        g["n_parts"] = g.geometry.apply(lambda x: len(x.geoms) if x is not None and hasattr(x, "geoms") else (0 if x is None else 1))
        g["empty"] = g.geometry.is_empty | g.geometry.isna()
        print(f"\n== layer {lyr}: units={g['name'].nunique()} ranges={sorted(g['range'].unique())} range_type={g['range_type'].unique()}")
        cols = ["name", "iso", "range", "population", "population_share", "population_interval", "implied_total_pop", "area_km2", "n_parts", "empty"]
        if lyr == "adm0":
            print(g[cols].to_string(index=False))
        else:
            # per unit: share at smallest and largest range, implied total pop
            agg = g.sort_values("range").groupby("name").agg(
                iso=("iso", "first"), implied_total_pop=("implied_total_pop", "median"),
                share_min_range=("population_share", "first"), share_max_range=("population_share", "last"),
                pop_max=("population", "last"), parts_sum=("n_parts", "sum"), area_km2_sum=("area_km2", "sum"),
                empty_rows=("empty", "sum"))
            print(agg.to_string())
            print("sum implied_total_pop over units:", agg["implied_total_pop"].sum())
    # check wide vs long consistency
    lg = pd.read_csv(os.path.join(D, f"MDV_{cat}_access_long.csv"))
    wd = pd.read_csv(os.path.join(D, f"MDV_{cat}_access_wide.csv"))
    print("\nlong population_type values:", lg["population_type"].value_counts().to_dict())
    print("wide rows", len(wd), "long rows", len(lg), "admin levels wide", wd["admin_level"].value_counts().to_dict())
    print("encoding check names:", sorted(wd["name"].unique()))
