#!/usr/bin/env python3
"""
Normalise the three tabular organiser datasets into tidy CSVs the rest of the project can use.

The travel-time model runs on FollowMe GPS, but all four supplied datasets are ingested and made
queryable here, so a new drop of any of them is processed rather than ignored:

  MTCC.xlsx        bus_monthly / bus_daily / ferry_monthly  → mtcc_bus_monthly.csv,
                                                              mtcc_bus_daily.csv,
                                                              mtcc_ferry_monthly.csv
  MACL csv         flight movements 2012–2026               → macl_monthly.csv
  Avas csv         ride orders Aug–Sep 2026                 → avas_daily.csv
  Avas fares       zone matrix                              → avas_fare_matrix.csv

Two documented traps are handled explicitly:
  * MACL `dep_date` is **month/day/year** although Metadata.csv claims YYYY-MM-DD. 102,304 of
    168,959 rows have a second component > 12 and cannot be anything but month-first.
  * MTCC's README labels the ridership columns "sample value", so the output carries that flag.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "derived"


def mtcc() -> list[str]:
    xl = pd.ExcelFile(DATA / "MTCC.xlsx")
    written = []
    for sheet, name in [("bus_monthly", "mtcc_bus_monthly.csv"),
                        ("bus_daily", "mtcc_bus_daily.csv"),
                        ("ferry_monthly", "mtcc_ferry_monthly.csv")]:
        if sheet not in xl.sheet_names:
            continue
        df = xl.parse(sheet)
        df["supplier_note"] = "sample value (MTCC README)"
        df.to_csv(OUT / name, index=False)
        written.append(f"{name} ({len(df):,} rows)")
    return written


def macl() -> list[str]:
    files = sorted((DATA / "MACL").glob("*.csv"))
    src = next((f for f in files if "traffic" in f.name.lower()), None)
    if src is None:
        return []
    df = pd.read_csv(src)
    # month-first, and we assert it rather than trusting the metadata
    first = df.dep_date.astype(str).str.split("/").str[0].astype(int)
    second = df.dep_date.astype(str).str.split("/").str[1].astype(int)
    assert first.max() <= 12 < second.max(), "dep_date is not the expected month-first format"
    df["date"] = pd.to_datetime(df.dep_date, format="%m/%d/%Y", errors="coerce")
    df = df.dropna(subset=["date"])
    for col in ["arr_adults", "arr_children", "arr_infants",
                "dep_adults", "dep_children", "dep_infants"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["arrivals"] = df.arr_adults + df.arr_children + df.arr_infants
    df["departures"] = df.dep_adults + df.dep_children + df.dep_infants
    monthly = (df.assign(month=df.date.dt.to_period("M").astype(str))
               .groupby("month", as_index=False)
               .agg(flights=("record_id", "count"),
                    arrivals=("arrivals", "sum"),
                    departures=("departures", "sum"),
                    carriers=("carrier_code", "nunique")))
    monthly["passengers"] = monthly.arrivals + monthly.departures
    monthly.to_csv(OUT / "macl_monthly.csv", index=False)
    return [f"macl_monthly.csv ({len(monthly):,} months, "
            f"{monthly.month.min()}..{monthly.month.max()})"]


def avas() -> list[str]:
    files = sorted((DATA / "Avas_Ride").glob("avas_rides*.csv"))
    if not files:
        return []
    df = pd.read_csv(files[0], usecols=["date_started", "distance_km", "time_sec", "status"],
                     parse_dates=["date_started"])
    df["date"] = df.date_started.dt.date.astype(str)
    daily = (df.groupby("date", as_index=False)
             .agg(orders=("status", "size"),
                  completed=("status", lambda s: int((s == "payment_completed").sum())),
                  expired=("status", lambda s: int((s == "ride_expired").sum())),
                  median_km=("distance_km", "median"),
                  median_minutes=("time_sec", lambda s: round(s.median() / 60, 1))))
    daily["completed_share"] = (daily.completed / daily.orders).round(3)
    daily.to_csv(OUT / "avas_daily.csv", index=False)

    written = [f"avas_daily.csv ({len(daily):,} days, {daily.date.min()}..{daily.date.max()})"]
    fares = DATA / "Avas_Ride" / "car_fare_matrix.csv"
    if fares.exists():
        f = pd.read_csv(fares)
        zone_col = [c for c in f.columns if "to_zone" in c][0]
        long = f.melt(id_vars=["city", zone_col], var_name="to_zone", value_name="fare_mvr")
        long = long.rename(columns={zone_col: "from_zone"})
        long.to_csv(OUT / "avas_fare_matrix.csv", index=False)
        written.append(f"avas_fare_matrix.csv ({len(long)} zone pairs)")
    return written


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    done: list[str] = []
    for fn in (mtcc, macl, avas):
        try:
            done += fn()
        except Exception as exc:                     # a broken source must not stop the pipeline
            print(f"  ! {fn.__name__} failed: {exc}")
    print("normalised: " + (", ".join(done) if done else "nothing found"))


if __name__ == "__main__":
    main()
