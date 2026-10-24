"""Print a quick summary of vector files: layer, feature count, CRS, geometry types, columns, sample rows.
Usage: python -I inspect_vec.py <file> [<file> ...]   (env NROWS=3)
"""
import os
import sys

import pyogrio
import geopandas as gpd
import pandas as pd

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 40)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
N = int(os.environ.get("NROWS", "3"))

for f in sys.argv[1:]:
    for lyr in pyogrio.list_layers(f)[:, 0]:
        g = gpd.read_file(f, layer=lyr)
        print(f"=== {os.path.basename(f)} :: {lyr}  n={len(g)}  crs={g.crs.to_string() if g.crs else None}")
        print("   geom:", g.geom_type.value_counts().to_dict())
        print("   cols:", list(g.columns))
        print(g.drop(columns="geometry").head(N).to_string())
