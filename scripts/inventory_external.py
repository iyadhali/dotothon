"""Inventory every data file under data/external: size, rows/features, CRS. Prints a markdown table.
Usage: python -I inventory_external.py <external_dir>
"""
import sys
from pathlib import Path

import pandas as pd
import pyogrio

sys.stdout.reconfigure(encoding="utf-8")
EXT = Path(sys.argv[1])
VEC = {".geojson", ".gpkg", ".shp"}
print("| file | size | rows/features | CRS | layers |")
print("|---|---|---|---|---|")
for f in sorted(EXT.rglob("*")):
    if not f.is_file() or f.name.lower() == "readme.md" or "raw" in f.parts and f.suffix == ".json":
        continue
    rel = f.relative_to(EXT).as_posix()
    size = f.stat().st_size
    sz = f"{size/1e6:.1f} MB" if size > 1e6 else f"{size/1e3:.0f} KB"
    n, crs, lay = "", "", ""
    try:
        if f.suffix.lower() in VEC:
            layers = pyogrio.list_layers(f)
            parts = []
            for name, _ in layers:
                info = pyogrio.read_info(f, layer=name)
                parts.append(f"{name}:{info['features']}")
                crs = info["crs"] or ""
            n = "; ".join(parts) if len(parts) > 1 else parts[0].split(":")[1]
            lay = str(len(layers))
        elif f.suffix.lower() == ".csv":
            n = str(len(pd.read_csv(f, low_memory=False)))
        elif f.suffix.lower() == ".tif":
            import rasterio
            with rasterio.open(f) as r:
                n, crs = f"{r.width}x{r.height} px", str(r.crs)
        elif f.suffix.lower() in (".xlsx", ".xls"):
            x = pd.ExcelFile(f)
            n = f"{len(x.sheet_names)} sheet(s)"
    except Exception as e:  # noqa
        n = f"ERR {e.__class__.__name__}"
    print(f"| {rel} | {sz} | {n} | {crs} | {lay} |")
