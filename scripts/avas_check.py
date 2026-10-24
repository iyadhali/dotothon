"""Avas sanity checks: is distance/time observed or a router estimate? Usage: python -I avas_check.py <avas_csv>"""
import sys
import numpy as np
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
a = pd.read_csv(sys.argv[1], parse_dates=["date_started"])
a["kmh"] = a.distance_km / a.time_sec * 3600
print(a.groupby("status").agg(n=("kmh", "size"), med_kmh=("kmh", "median"), sd_kmh=("kmh", "std"), med_km=("distance_km", "median"), med_s=("time_sec", "median")).round(2))
print("time_sec<=301:", (a.time_sec <= 301).sum(), " time_sec in [300,300.01]:", a.time_sec.between(300, 300.01).sum())
print("time_sec histogram near floor:", np.histogram(a.time_sec, bins=[300, 305, 310, 320, 340, 400])[0])
print("distance_km histogram near floor:", np.histogram(a.distance_km, bins=[1.9, 2.0, 2.2, 2.5, 3, 4])[0])
a["dow"] = a.date_started.dt.day_name()
print(a.groupby("dow").kmh.median().round(2))
print("daily counts top 5:\n", a.groupby(a.date_started.dt.date).size().sort_values(ascending=False).head(5))
print("pickup within 50m of dropoff:", ((a.pickup_lat - a.dropoff_lat).abs() < 0.0005).sum())
# Male-only trips: both ends in Male island bbox
male = a.pickup_lat.between(4.165, 4.182) & a.pickup_lng.between(73.495, 73.520) & a.dropoff_lat.between(4.165, 4.182) & a.dropoff_lng.between(73.495, 73.520)
print("intra-Male trips:", male.sum(), " median kmh:", a.loc[male, "kmh"].median().round(1), " median km:", a.loc[male, "distance_km"].median())
