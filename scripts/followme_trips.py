"""Extract vessel trips from FollowMe GPS and test whether endpoints snap to known island jetties.
Usage: python -I followme_trips.py <FollowMe_folder> <rtl_stops.csv> [<out_trips.parquet>]
Trip = run of moving points (speed>=3 kn) bounded by stationary points (speed<1 kn) with no internal gap >15 min.
"""
import sys
import glob
import os
import numpy as np
import polars as pl

sys.stdout.reconfigure(encoding="utf-8")
pl.Config.set_tbl_rows(40)
pl.Config.set_tbl_cols(20)
pl.Config.set_tbl_width_chars(250)

folder, stops_p = sys.argv[1], sys.argv[2]
out_p = sys.argv[3] if len(sys.argv) > 3 else None
files = glob.glob(os.path.join(folder, "*.csv"))
schema = {"poll_id": pl.Int64, "imei": pl.Utf8, "timestamp": pl.Utf8, "device_date": pl.Utf8,
          "latitude": pl.Float64, "longitude": pl.Float64, "speed": pl.Float64, "heading": pl.Float64,
          "network": pl.Utf8, "cellid": pl.Utf8, "gsm_level": pl.Utf8}
df = (pl.scan_csv(files, schema=schema, ignore_errors=True)
      .select("imei", "device_date", "latitude", "longitude", "speed")
      .with_columns(pl.col("device_date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False).alias("t"))
      .filter(pl.col("latitude").is_between(-1.0, 7.5) & pl.col("longitude").is_between(72.4, 74.0) & (pl.col("speed") <= 60))
      .select("imei", "t", "latitude", "longitude", "speed")
      .unique(subset=["imei", "t"]).sort(["imei", "t"]).collect())
print("clean points:", df.height)

R = 6371000.0
rad = np.pi / 180
df = df.with_columns(
    pl.col("t").diff().over("imei").dt.total_seconds().alias("dt"),
    pl.col("latitude").shift().over("imei").alias("plat"), pl.col("longitude").shift().over("imei").alias("plon"))
df = df.with_columns((2 * R * (((pl.col("latitude") - pl.col("plat")) * rad / 2).sin() ** 2
                      + (pl.col("plat") * rad).cos() * (pl.col("latitude") * rad).cos()
                      * (((pl.col("longitude") - pl.col("plon")) * rad / 2).sin() ** 2)).sqrt().arcsin()).fill_null(0).alias("step"))
# state: 1 moving, 0 stationary, -1 ambiguous (1-3 kn) -> treat ambiguous as moving-continuation
df = df.with_columns(pl.when(pl.col("speed") < 1).then(0).otherwise(1).alias("mv"))
# new segment when state changes OR there's a big gap
df = df.with_columns(((pl.col("mv") != pl.col("mv").shift().over("imei")) | (pl.col("dt") > 900) | pl.col("dt").is_null())
                     .cast(pl.Int32).cum_sum().over("imei").alias("seg"))
seg = (df.group_by("imei", "seg").agg(
    pl.col("mv").first(), pl.col("t").min().alias("t0"), pl.col("t").max().alias("t1"),
    pl.col("latitude").first().alias("lat0"), pl.col("longitude").first().alias("lon0"),
    pl.col("latitude").last().alias("lat1"), pl.col("longitude").last().alias("lon1"),
    pl.col("latitude").median().alias("latm"), pl.col("longitude").median().alias("lonm"),
    pl.col("step").slice(1).sum().alias("path_m"), pl.col("speed").filter(pl.col("speed") >= 3).median().alias("med_kn"),
    pl.col("dt").first().alias("gap_before"), pl.len().alias("n"))
    .sort("imei", "seg"))
# A trip = moving segment whose previous seg is stationary and next seg is stationary, contiguous (no gap>900 at boundaries)
seg = seg.with_columns(
    pl.col("mv").shift().over("imei").alias("pmv"), pl.col("mv").shift(-1).over("imei").alias("nmv"),
    pl.col("latm").shift().over("imei").alias("o_lat"), pl.col("lonm").shift().over("imei").alias("o_lon"),
    pl.col("latm").shift(-1).over("imei").alias("d_lat"), pl.col("lonm").shift(-1).over("imei").alias("d_lon"),
    pl.col("gap_before").shift(-1).over("imei").alias("gap_after"),
    ((pl.col("t1").shift().over("imei") - pl.col("t0").shift().over("imei")).dt.total_minutes()).alias("o_dwell_min"))
trips = seg.filter((pl.col("mv") == 1) & (pl.col("pmv") == 0) & (pl.col("nmv") == 0)
                   & (pl.col("gap_before") <= 900) & (pl.col("gap_after") <= 900))
trips = trips.with_columns(((pl.col("t1") - pl.col("t0")).dt.total_seconds() / 60).alias("dur_min"))
trips = trips.with_columns((2 * R * (((pl.col("d_lat") - pl.col("o_lat")) * rad / 2).sin() ** 2
                            + (pl.col("o_lat") * rad).cos() * (pl.col("d_lat") * rad).cos()
                            * (((pl.col("d_lon") - pl.col("o_lon")) * rad / 2).sin() ** 2)).sqrt().arcsin() / 1000).alias("od_km"))
trips = trips.filter((pl.col("od_km") >= 1.0) & (pl.col("dur_min") >= 3) & (pl.col("dur_min") <= 720))
trips = trips.with_columns((pl.col("path_m") / 1000 / (pl.col("dur_min") / 60)).alias("path_kmh"),
                           (pl.col("od_km") / (pl.col("dur_min") / 60)).alias("od_kmh"),
                           (pl.col("path_m") / 1000 / pl.col("od_km")).alias("detour"))
print("candidate trips (od>=1km):", trips.height, " devices with trips:", trips["imei"].n_unique())
print(trips.select("dur_min", "od_km", "path_kmh", "od_kmh", "detour", "med_kn", "o_dwell_min").describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))

# vessel class from device-level median moving speed
dev = df.filter(pl.col("speed") >= 3).group_by("imei").agg(pl.col("speed").median().alias("dev_kn"))
dev = dev.with_columns(pl.when(pl.col("dev_kn") >= 18).then(pl.lit("fast(>=18kn)"))
                       .when(pl.col("dev_kn") >= 9).then(pl.lit("medium(9-18kn)")).otherwise(pl.lit("slow(<9kn)")).alias("cls"))
print("devices by class:", dev["cls"].value_counts().sort("cls"))
trips = trips.join(dev, on="imei", how="left")
print(trips.group_by("cls").agg(pl.len().alias("trips"), pl.col("path_kmh").median().alias("med_path_kmh"),
                                pl.col("od_kmh").median().alias("med_od_kmh"), pl.col("detour").median().alias("med_detour"),
                                pl.col("dur_min").median().alias("med_dur")).sort("cls"))

# Snap endpoints to RTL stops (island jetties) within 1.5 km
st = pl.read_csv(stops_p).select("name", "atoll", "island", "lat", "lon").drop_nulls(["lat", "lon"])
S = st.select("lat", "lon").to_numpy()
names = st["name"].to_list()


def snap(lat, lon):
    lat = np.asarray(lat); lon = np.asarray(lon)
    out_n, out_d = [], []
    for i in range(0, len(lat), 20000):
        a = lat[i:i + 20000, None] * rad; b = lon[i:i + 20000, None] * rad
        h = np.sin((S[None, :, 0] * rad - a) / 2) ** 2 + np.cos(a) * np.cos(S[None, :, 0] * rad) * np.sin((S[None, :, 1] * rad - b) / 2) ** 2
        d = 2 * R * np.arcsin(np.sqrt(h)) / 1000
        j = d.argmin(axis=1)
        out_n += [names[k] for k in j]; out_d += d[np.arange(len(j)), j].tolist()
    return out_n, out_d


on, od = snap(trips["o_lat"].to_numpy(), trips["o_lon"].to_numpy())
dn, dd = snap(trips["d_lat"].to_numpy(), trips["d_lon"].to_numpy())
trips = trips.with_columns(pl.Series("o_stop", on), pl.Series("o_km", od), pl.Series("d_stop", dn), pl.Series("d_km", dd))
print("rtl stops loaded:", st.height)
for thr in (0.5, 1.0, 1.5):
    both = trips.filter((pl.col("o_km") <= thr) & (pl.col("d_km") <= thr)).height
    print(f"trips with both endpoints within {thr} km of an RTL stop: {both} ({both / trips.height:.1%})")
# Greater Male' area (Male, Hulhumale, Villimale, airport) share of endpoints
gm = trips.filter(pl.col("o_lat").is_between(4.15, 4.26) & pl.col("o_lon").is_between(73.48, 73.56)).height
print(f"trips originating in Greater Male' bbox: {gm} ({gm / trips.height:.1%})")
snapped = trips.filter((pl.col("o_km") <= 1.0) & (pl.col("d_km") <= 1.0) & (pl.col("o_stop") != pl.col("d_stop")))
odp = snapped.group_by("o_stop", "d_stop").agg(
    pl.len().alias("trips"), pl.col("imei").n_unique().alias("vessels"),
    pl.col("dur_min").median().round(1).alias("med_min"), pl.col("dur_min").quantile(0.1).round(1).alias("p10_min"),
    pl.col("od_km").median().round(1).alias("km"), pl.col("path_kmh").median().round(1).alias("kmh")).sort("trips", descending=True)
print("distinct snapped island-pair OD (directed):", odp.height, " with >=10 trips:", odp.filter(pl.col("trips") >= 10).height)
print(odp.head(30))
print("distinct RTL stops touched by snapped trips:", pl.concat([snapped["o_stop"], snapped["d_stop"]]).n_unique())
# Hour-of-day departures (for frequency / headway) in Greater Male'
print("trip departures by hour (all):")
print(trips.group_by(pl.col("t0").dt.hour().alias("h")).len().sort("h").transpose(include_header=False))
# Dwell at stops
stops_seg = seg.filter(pl.col("mv") == 0).with_columns(((pl.col("t1") - pl.col("t0")).dt.total_minutes()).alias("dwell"))
print("stationary segment dwell minutes:", stops_seg.select(pl.col("dwell").quantile(q).alias(str(q)) for q in (0.25, 0.5, 0.75, 0.9)))
if out_p:
    trips.drop("pmv", "nmv").write_parquet(out_p)
    print("wrote", out_p)
