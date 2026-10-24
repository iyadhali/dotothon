"""Generic CSV/GPKG profiler. Usage: python -I profile_csvs.py <file> [<file> ...]
Data paths are passed as arguments; nothing in the data folder is executed."""
import sys, site
sys.path.append(site.getusersitepackages())  # -I disables user site; add it explicitly
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
pd.set_option("display.max_colwidth", 60)


def profile_df(df, name):
    print(f"\n{'=' * 100}\n{name}\nrows={len(df)} cols={df.shape[1]}")
    print("\n-- dtypes / nulls / nunique / min / max")
    rows = []
    for c in df.columns:
        s = df[c]
        try:
            mn, mx = s.min(), s.max()
        except Exception:
            mn = mx = "n/a"
        rows.append((c, str(s.dtype), int(s.isna().sum()), int(s.nunique(dropna=True)), str(mn)[:40], str(mx)[:40]))
    print(pd.DataFrame(rows, columns=["col", "dtype", "nulls", "nunique", "min", "max"]).to_string(index=False))
    print("\n-- head(5)")
    print(df.head(5).to_string())
    for c in df.columns:
        if df[c].dtype == object and 1 < df[c].nunique() <= 25:
            print(f"\n-- value_counts {c}")
            print(df[c].value_counts(dropna=False).head(25).to_string())


for path in sys.argv[1:]:
    if path.lower().endswith(".gpkg"):
        import pyogrio, geopandas as gpd
        print(f"\n{'#' * 100}\nGPKG {path}")
        for lyr in pyogrio.list_layers(path):
            info = pyogrio.read_info(path, layer=lyr[0])
            print(f"layer={lyr[0]} geom={lyr[1]} crs={info['crs']} features={info['features']} fields={list(info['fields'])}")
        for lyr in pyogrio.list_layers(path):
            g = gpd.read_file(path, layer=lyr[0])
            print("bounds", g.total_bounds)
            profile_df(pd.DataFrame(g.drop(columns="geometry", errors="ignore")), f"{path} :: {lyr[0]}")
    else:
        df = pd.read_csv(path, low_memory=False)
        profile_df(df, path)
