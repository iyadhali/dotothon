"""Per-day summary of FollowMe GPS CSVs (August 2025) so the repo can carry a small
summary instead of the 1.9 GB raw files.
Usage: python -I followme_daily_summary.py <FollowMe_august_2025 dir> <out_csv>
"""
import glob
import os
import sys

import polars as pl

src, out = sys.argv[1], sys.argv[2]
rows = []
for p in sorted(glob.glob(os.path.join(src, "*.csv")), key=lambda x: int(os.path.basename(x)[:-4])):
    lf = pl.scan_csv(p, infer_schema_length=10000)
    s = lf.select(
        pl.len().alias("rows"),
        pl.col("imei").n_unique().alias("unique_devices"),
        pl.col("timestamp").min().alias("ts_min"),
        pl.col("timestamp").max().alias("ts_max"),
        pl.col("latitude").min().alias("lat_min"),
        pl.col("latitude").max().alias("lat_max"),
        pl.col("longitude").min().alias("lon_min"),
        pl.col("longitude").max().alias("lon_max"),
        (pl.col("speed") > 0).mean().alias("share_moving"),
        pl.col("speed").quantile(0.95).alias("speed_p95"),
        (pl.col("network") == 1).mean().alias("share_dhiraagu"),
        (pl.col("network") == 2).mean().alias("share_ooredoo"),
    ).collect()
    d = s.to_dicts()[0]
    d = {"file": os.path.basename(p), "size_mb": round(os.path.getsize(p) / 1e6, 1), **d}
    rows.append(d)
    print(d["file"], d["rows"], d["unique_devices"], flush=True)
df = pl.DataFrame(rows)
df.write_csv(out)
print("total rows", df["rows"].sum())
