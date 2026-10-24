# FollowMe GPS pings, August 2025 (not stored in git)

The raw files are too large for the repository: 31 daily CSVs, about 1.9 GB unzipped, and 28 of them are over GitHub's 50 MB warning size. Download them from the official datathon release instead:

- **FollowMe.zip** (461 MB): https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases/download/v1.0/FollowMe.zip
- Release page: https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases/tag/v1.0

To restore the expected layout, unzip into `data/FollowMe/`. You should end up with `data/FollowMe/FollowMe_august_2025/1.csv … 31.csv` and `Summary of the available data.txt`.

## What's in it
GPS telemetry from FollowMe Maldives tracker devices, one CSV per day of August 2025. The devices are mostly boats, plus some vehicles. See https://followme.mv.

The columns below come from the bundled `Summary of the available data.txt`:

| column | meaning |
|---|---|
| poll_id | unique database row id |
| imei | tracking device IMEI or serial number |
| timestamp | time saved in the database |
| device_date | time reported by the tracking device |
| latitude, longitude | device position |
| speed | speed of the boat (units undocumented) |
| heading | heading or bearing |
| network | mobile network: 1 = Dhiraagu, 2 = Ooredoo |
| cellid | mobile network cell id |
| gsm_level | GSM signal level |

## Summary
- `followme_daily_summary.csv` gives one row per daily file. Columns: size, row count, unique devices, timestamp range, lat/lon range, share of pings with speed > 0, 95th-percentile speed, and network shares.
- It was produced by `scripts/followme_daily_summary.py` using polars.
- In each day: about 0.44–0.6 M pings, about 1,400–1,500 unique devices, and about 80% of pings have speed > 0.
- Each file also contains a few stray records. Some timestamps run up to 2026-10-08, and some longitudes are far outside the Maldives. Filter by date and by bbox (lat -1 to 7.2, lon 72.4 to 74).
- Derived trips: `data/processed/followme/fm_trips.parquet`, built by `scripts/followme_trips.py`.
