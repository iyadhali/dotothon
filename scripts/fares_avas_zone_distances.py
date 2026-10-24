"""Median trip distance/time between Greater Malé fare zones from Avas ride logs.

Zones are rough bounding boxes (lat/lon) for Malé, Hulhulé (airport), Hulhumalé
Phase 1 and Phase 2. Only completed rides (status == payment_completed) are used.

Usage: python -I fares_avas_zone_distances.py <avas_rides.csv> <out.csv>
"""
import csv
import statistics
import sys
from collections import defaultdict

ZONES = {
    # name: (lat_min, lat_max, lon_min, lon_max)
    "Male": (4.160, 4.185, 73.495, 73.523),
    "Velana International Airport": (4.178, 4.205, 73.523, 73.540),
    "Hulhumale Phase 1": (4.205, 4.226, 73.530, 73.552),
    "Hulhumale Phase 2": (4.226, 4.265, 73.520, 73.560),
}


def zone(lat, lon):
    for z, (a, b, c, d) in ZONES.items():
        if a <= lat < b and c <= lon < d:
            return z
    return None


def main():
    src, out = sys.argv[1], sys.argv[2]
    acc = defaultdict(lambda: ([], []))
    n = 0
    with open(src, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["status"] != "payment_completed":
                continue
            try:
                o = zone(float(r["pickup_lat"]), float(r["pickup_lng"]))
                d = zone(float(r["dropoff_lat"]), float(r["dropoff_lng"]))
                km, sec = float(r["distance_km"]), float(r["time_sec"])
            except (ValueError, KeyError):
                continue
            if not o or not d or km <= 0 or km > 40:
                continue
            acc[(o, d)][0].append(km)
            acc[(o, d)][1].append(sec / 60)
            n += 1
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["from_zone", "to_zone", "n_rides", "median_km", "median_min"])
        for (o, d), (kms, mins) in sorted(acc.items()):
            w.writerow([o, d, len(kms), round(statistics.median(kms), 2), round(statistics.median(mins), 1)])
    print(f"{n} completed rides assigned to zones -> {out}")


if __name__ == "__main__":
    main()
