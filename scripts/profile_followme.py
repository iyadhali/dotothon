"""Profile FollowMe boat-tracker CSVs with polars lazy scanning (never loads raw text wholesale).
Usage: python -I profile_followme.py <FollowMe_folder_with_csvs>
"""
import sys
import glob
import os
import polars as pl
sys.stdout.reconfigure(encoding="utf-8")

pl.Config.set_tbl_rows(60)
pl.Config.set_tbl_cols(20)
pl.Config.set_tbl_width_chars(250)

folder = sys.argv[1]
files = sorted(glob.glob(os.path.join(folder, "*.csv")), key=lambda p: int(os.path.basename(p).split(".")[0]))
print("n csv files:", len(files))

schema = {
    "poll_id": pl.Int64, "imei": pl.Utf8, "timestamp": pl.Utf8, "device_date": pl.Utf8,
    "latitude": pl.Float64, "longitude": pl.Float64, "speed": pl.Float64, "heading": pl.Float64,
    "network": pl.Utf8, "cellid": pl.Utf8, "gsm_level": pl.Utf8,
}

# header check per file
hdrs = set()
for f in files:
    with open(f, "r", encoding="utf-8", errors="replace") as fh:
        hdrs.add(fh.readline().strip())
print("distinct headers:", hdrs)

lf = pl.scan_csv(files, schema=schema, include_file_paths="file", ignore_errors=True)
lf = lf.with_columns(
    pl.col("file").str.extract(r"(\d+)\.csv$").cast(pl.Int32).alias("day_file"),
    pl.col("timestamp").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False).alias("ts"),
    pl.col("device_date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False).alias("dd"),
).drop("file")

df = lf.collect()
print("total rows:", df.height)
print(df.schema)
print(df.head(5))
print("-- nulls")
print(df.null_count())
print("-- numeric describe")
print(df.select("latitude", "longitude", "speed", "heading").describe(percentiles=[0.001, 0.01, 0.5, 0.99, 0.999]))

per_file = df.group_by("day_file").agg(
    pl.len().alias("rows"), pl.col("imei").n_unique().alias("imeis"),
    pl.col("dd").min().alias("dd_min"), pl.col("dd").max().alias("dd_max"),
    pl.col("ts").min().alias("ts_min"), pl.col("ts").max().alias("ts_max"),
).sort("day_file")
print(per_file)

print("distinct imei overall:", df["imei"].n_unique())
print("duplicate poll_id:", df.height - df["poll_id"].n_unique())
print("exact dup (imei, device_date, lat, lon):", df.height - df.select("imei", "dd", "latitude", "longitude").unique().height)
print("device_date range:", df["dd"].min(), df["dd"].max(), " timestamp range:", df["ts"].min(), df["ts"].max())
lag = (df["ts"] - df["dd"]).dt.total_seconds()
print("ingest lag (timestamp - device_date) sec quantiles:", [lag.quantile(q) for q in (0.01, 0.5, 0.9, 0.99)], "neg:", (lag < 0).sum())
print("dd outside Aug-2025:", df.filter((pl.col("dd") < pl.datetime(2025, 8, 1)) | (pl.col("dd") >= pl.datetime(2025, 9, 1))).height)
print("-- network values:", df["network"].value_counts().sort("count", descending=True).head(10))
print("-- gsm_level top:", df["gsm_level"].value_counts().sort("count", descending=True).head(5))
print("cellid non-numeric share:", df.filter(~pl.col("cellid").str.contains(r"^\d+$")).height / df.height)
print("lat==0 or lon==0:", df.filter((pl.col("latitude") == 0) | (pl.col("longitude") == 0)).height)
# Maldives bbox approx lat -0.8..7.2, lon 72.5..73.9
outside = df.filter(~(pl.col("latitude").is_between(-1.0, 7.5) & pl.col("longitude").is_between(72.4, 74.0)))
print("outside Maldives bbox:", outside.height)
print(outside.select("latitude", "longitude").describe())
print("speed==0 share:", (df["speed"] == 0).mean(), " speed>60:", (df["speed"] > 60).sum(), " speed>100:", (df["speed"] > 100).sum())
print("speed value histogram:", df.select(pl.col("speed").cut([0.001, 1, 5, 10, 15, 20, 25, 30, 40, 60, 100])).to_series().value_counts().sort("speed"))
print("fraction integer speeds:", (df["speed"] == df["speed"].round(0)).mean())

# Per device stats
dev = df.group_by("imei").agg(
    pl.len().alias("n"), pl.col("dd").min().alias("first"), pl.col("dd").max().alias("last"),
    pl.col("day_file").n_unique().alias("days"),
    pl.col("latitude").min().alias("lat_min"), pl.col("latitude").max().alias("lat_max"),
    pl.col("longitude").min().alias("lon_min"), pl.col("longitude").max().alias("lon_max"),
    (pl.col("speed") > 2).mean().alias("moving_share"), pl.col("speed").max().alias("vmax"),
)
print("-- per device n points describe")
print(dev.select("n", "days", "moving_share", "vmax", "lat_min", "lat_max").describe(percentiles=[0.1, 0.5, 0.9]))
dev = dev.with_columns(((pl.col("lat_max") - pl.col("lat_min")) * 111).alias("lat_span_km"))
print("devices by lat span km:", dev.select(pl.col("lat_span_km").cut([1, 5, 20, 50, 100, 300])).to_series().value_counts().sort("lat_span_km"))

# Sampling interval and derived speeds per device (sorted by device time)
s = df.select("imei", "dd", "latitude", "longitude", "speed", "heading").unique(subset=["imei", "dd"]).sort(["imei", "dd"])
s = s.with_columns(
    pl.col("dd").diff().over("imei").dt.total_seconds().alias("dt_s"),
    pl.col("latitude").shift().over("imei").alias("lat0"),
    pl.col("longitude").shift().over("imei").alias("lon0"),
)
rad = 3.141592653589793 / 180
s = s.with_columns(
    (2 * 6371000 * (((pl.col("latitude") - pl.col("lat0")) * rad / 2).sin() ** 2
     + (pl.col("lat0") * rad).cos() * (pl.col("latitude") * rad).cos()
     * (((pl.col("longitude") - pl.col("lon0")) * rad / 2).sin() ** 2)).sqrt().arcsin()).alias("step_m")
)
s = s.with_columns((pl.col("step_m") / pl.col("dt_s") * 3.6).alias("v_kmh"))
print("-- sampling interval dt_s quantiles:", [s["dt_s"].quantile(q) for q in (0.05, 0.25, 0.5, 0.75, 0.95, 0.99)])
mv = s.filter((pl.col("dt_s") > 0) & (pl.col("dt_s") <= 120) & (pl.col("speed") > 3))
print("moving pairs:", mv.height)
print("ratio derived km/h / reported speed (median):", (mv["v_kmh"] / mv["speed"]).median(),
      " -> if ~1.85 speed is knots, ~1.0 km/h")
print("derived km/h quantiles (moving):", [round(mv["v_kmh"].quantile(q), 1) for q in (0.05, 0.25, 0.5, 0.75, 0.95, 0.99)])
print("reported speed quantiles (moving):", [mv["speed"].quantile(q) for q in (0.05, 0.25, 0.5, 0.75, 0.95, 0.99)])
print("teleport jumps (>150 km/h derived, dt<=600):", s.filter((pl.col("v_kmh") > 150) & (pl.col("dt_s") <= 600) & (pl.col("dt_s") > 0)).height)
print("dt_s==0 duplicates within device:", s.filter(pl.col("dt_s") == 0).height)

# Spatial density: 0.05 deg grid (~5.5 km) counts of stationary points, top cells
grid = df.filter(pl.col("speed") < 0.5).with_columns(
    (pl.col("latitude") / 0.02).floor().mul(0.02).round(2).alias("glat"),
    (pl.col("longitude") / 0.02).floor().mul(0.02).round(2).alias("glon"),
).group_by("glat", "glon").agg(pl.len().alias("n"), pl.col("imei").n_unique().alias("devs")).sort("devs", descending=True)
print("distinct 0.02deg cells with stationary points:", grid.height)
print(grid.head(30))
mvgrid = df.filter(pl.col("speed") > 3).with_columns(
    (pl.col("latitude") / 0.1).floor().mul(0.1).round(1).alias("glat")).group_by("glat").agg(pl.len().alias("n"), pl.col("imei").n_unique().alias("devs")).sort("glat")
print("moving points by 0.1-deg latitude band (north-south coverage):")
print(mvgrid)

# One example device: trip segmentation (stop = speed<1 for >=10 min)
top = dev.filter((pl.col("lat_span_km") > 20) & (pl.col("lat_span_km") < 150)).sort("n", descending=True).head(1)["imei"][0]
ex = s.filter(pl.col("imei") == top).with_columns((pl.col("speed") > 2).alias("mov"))
ex = ex.with_columns((pl.col("mov") != pl.col("mov").shift()).fill_null(True).cum_sum().alias("seg"))
segs = ex.group_by("seg").agg(pl.col("mov").first(), pl.col("dd").min().alias("t0"), pl.col("dd").max().alias("t1"),
                              pl.col("latitude").first().alias("lat0"), pl.col("longitude").first().alias("lon0"),
                              pl.col("latitude").last().alias("lat1"), pl.col("longitude").last().alias("lon1"),
                              pl.col("step_m").sum().alias("dist_m"), pl.len().alias("n")).sort("seg")
segs = segs.with_columns(((pl.col("t1") - pl.col("t0")).dt.total_minutes()).alias("mins"))
print(f"example device {top[:6]}*** segments (first 40, mov=True moving):")
print(segs.filter(pl.col("mins") >= 10).head(40))
