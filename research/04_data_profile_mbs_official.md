# 04 — Profile of the official MBS Datathon 2026 datasets

*Profiled 2026-10-24. Use case: multi-modal (land/sea/air) accessibility of schools, universities and hospitals, by island.*

**Method.** All files were treated as untrusted data and only read. Profiling scripts are in `C:\Users\user\Music\Datathon\scripts\`:
`profile_mbs_tabular.py` (MACL, Avas, MTCC), `profile_mtcc.py` (raw sheet dump), `macl_deep.py`, `avas_check.py`, `profile_followme.py` and `followme_trips.py`. FollowMe was read with polars lazy `scan_csv`.
The scripts ran with `python -I` from a venv at `C:\Users\user\Music\Datathon\.venv`. Isolated mode ignores user site-packages, so the venv was needed.
Run `.venv\Scripts\python -I scripts\<name>.py <data paths>` to reproduce.

---

## TL;DR

| Dataset | What it really is | Usefulness for the island accessibility network |
|---|---|---|
| **FollowMe** (1.8 GB, 31 daily CSVs, 17.46 M rows) | **Real GPS pings from 1,776 vessels** (boat trackers), Aug 2025, nationwide | **High.** Gives empirical sea speeds, island-to-island travel times, route geometry, departure-time profiles. This is the main real sea-edge source. |
| **MTCC.xlsx** (4 sheets) | Monthly/daily **passenger counts** for 5 Greater Malé bus routes and 8 RTL ferry routes. **The README says all passenger figures are randomly generated.** | **Low.** No schedules, durations, stops or coordinates. Route codes are real and partly join to the RTL timetable scrape (`team-kandu/rtl_*.csv`). |
| **Avas_Ride** (371,788 rides + 6×6 fare matrix) | Ride-hailing trips in **Greater Malé only** (Malé, Hulhulé/VIA, Hulhumalé Ph1/Ph2), Aug–Sep 2026 | **Medium, for the capital only.** Gives road OD times, but the distance and time look like **routing-engine estimates** rather than observed values. Implied speed is about 38 km/h and nearly constant. |
| **MACL** (168,959 rows, 2012-01 → 2026-07) | **International aircraft turnarounds at Velana (MLE)**. Carrier, route and aircraft codes are **anonymised**. | **Very low for domestic access.** No domestic flights, no airport/IATA codes, no flight durations. ATA/ATD are times on the ground at MLE. |

**Bottom line.** Only FollowMe gives real inter-island travel times. Domestic air must come from elsewhere: OurAirports (`external/ourairports`, 31 MV records) and Maldivian/Manta schedules (e.g. `team-kandu/maldivian_destinations.csv`).
Scheduled ferry frequency must come from the RTL timetables (`team-kandu/rtl_trips.csv`, `rtl_connections.csv`), not MTCC.

---

## 1. MACL — Airport traffic (Maldives Airports Company Ltd)

Files: `MACL\MACL\Metadata.csv` (data dictionary) and `Airport traffic_Dataset_27092026.csv` (21 MB).

### Schema (from Metadata.csv, checked against the data)
| Column | Type | Notes |
|---|---|---|
| record_id | int | Unique, monotonic with date |
| flight_type | cat | SCHEDULED 167,151 · CHARTER 1,808 |
| dep_date, arrival_date | date (`M/D/YYYY`) | Metadata says `YYYY-MM-DD`, but the file uses US format |
| carrier_code | cat | **Anonymised** `Carrier_001…112` (112 values; 1 null) |
| route_code | cat | **Anonymised** `Route_0001…` (1,008 values). Each route maps to exactly 1 region. |
| region | cat | Region of the *foreign* airport: South Asia 60,600 · Middle East 50,045 · SE Asia 25,591 · Europe 14,276 · East Asia 12,640 · Central Asia & CIS 5,657 · Africa 115 · Other 35. **No "Domestic" value.** |
| aircraft_type_code | cat | Anonymised `Type_001…019` |
| aircraft_category | cat | Widebody 84,646 · Narrowbody 78,546 · Turboprop 5,767 |
| arr_/transit_/dep_ × adults/children/infants | int | Passenger counts per movement; max arr 623, dep 546 |
| ata, atd | time `H:MM` | Actual arrival and actual departure (at MLE) |

### What one row is
**One aircraft turnaround at Velana International Airport (MLE).** The aircraft arrives from a foreign airport (ATA) and departs again (ATD).
- 161,227 rows have both arriving and departing passengers.
- About 4,000 rows are arrival-only and about 3,700 are departure-only.
- Median ATD − ATA is 78 min for narrowbodies, 115 min for widebodies and 46 min for turboprops. These are typical turnaround times, which supports this reading.

### Coverage
- **Time:** 2012-01-01 → 2026-07-31. About 10–16 k rows per year; 2020 is a COVID dip (4,463 rows). Movements per day in 2025: mean 44 (range 32–63).
- **Geography:** MLE only. The other end of each movement is known only by world region.
- **Turboprop rows:** 5,767 rows (South Asia / Other). They are almost all `Carrier_110` and `Carrier_061` on a handful of routes, with 40–60 passengers. These look like regional international flights (e.g. Maldivian Dash-8 services to India), **not domestic flights**.
- **Domestic flights are missing.** Real domestic MLE traffic is roughly 100+ movements per day, but the whole file averages 44 per day.

### Data-quality issues
- 11 rows have `arrival_date` = 1970-01-01 or 01-03 (epoch null placeholder).
- 15 rows (Dec 2020) have ATA/ATD stored as **Excel serial dates** (e.g. `44187`).
- ATA is null in 72 rows and ATD in 71.
- dep_date ≠ arrival_date in 6,864 rows. In 5,279 of them dep_date is *earlier* than arrival_date, which contradicts the turnaround reading. The date semantics are ambiguous, so derive turnaround times only for same-day rows.
- 8.5 % of computed ground times are negative because of midnight crossings and the date issues above.
- 49 rows have zero passengers.
- The date format does not match the metadata.

### Answers for the use case (Q1)
- **Airports/routes:** only MLE. International only. Routes are anonymised, with no IATA codes or destinations; only the region is given.
- **Flight-level times:** yes, flight-level records with ATA and ATD, but both times are *at MLE*. There is no origin/destination timestamp, so **flight durations cannot be derived**.
- **Domestic route frequencies / headways:** **not possible**, because domestic flights are not in the file. International headways can be computed per anonymised route, e.g. the top route has 29 flights/week, a mean headway of about 5.8 h. That is only relevant to an "international gateway" layer, not to island access.
- **Possible use:** context only, such as the MLE gateway role, tourist volumes by region, and seasonality. Domestic air edges should be built from OurAirports locations (`external/ourairports`, 31 MV records incl. seaplane bases) plus published domestic schedules (Maldivian / Manta / Villa). Duration can be approximated as great-circle distance / ~350 km/h (turboprop) + taxi overhead.

---

## 2. MTCC.xlsx — Bus and ferry ridership (MTCC / RTL)

### Sheets
| Sheet | Rows | Columns | Grain |
|---|---|---|---|
| README | 14 | table, column, description | Data dictionary and notes |
| bus_monthly | 180 | month, year, month_num, route_id, route_name, paid_pax, foc_pax, total_pax | route × month, Jan 2023–Dec 2025, 5 routes |
| bus_daily | 1,095 | date, weekday, route_id, route_name, paid_pax, foc_pax, total_pax | route × day, calendar 2025, routes R1, R2, R4 |
| ferry_monthly | 258 | month, year, month_num, zone, atoll, route_id, passengers | route × month, Jan 2023–Dec 2025, 8 routes |

No nulls and no duplicate rows.

**Critical caveat (README, row 12):**
> "Sample data: Route names and codes are real; **all passenger figures are randomly generated and are not actual MTCC / RTL data.**"

The README also says the generator added seasonality, a Friday dip, disruption dips, and staggered zone starts (Zone 05 from Jul 2023, Noonu from Jul 2024).

### Coverage
- **Bus routes (Greater Malé):**
  - R1 Hulhumalé Ph1 – Malé (West Park)
  - R2 Hulhumalé Ph1 – Malé (Carnival)
  - R3 Malé (West Park) – Velana Airport
  - R4 Hulhumalé Ph1 – Velana Airport
  - R7 Hulhumalé Ph2 – Malé (West Park)
- **Ferry routes (RTL):**

| Zone | Atoll | Routes | Months |
|---|---|---|---|
| RTL Zone 01 | Haa Alifu | H1, S1C1, S1C5 | 36 |
| RTL Zone 02 | Lhaviyani | R2C1, R2C2 | 36 |
| RTL Zone 02 | Noonu | Z2R1 | 18 (from 2024-07) |
| RTL Zone 05 | Gaafu Alifu & Gaafu Dhaalu | Z5R2, Z5R5 | 30 (from 2023-07) |

  Mean ferry passengers per route-month: 442–1,839.
- **Not included:** stop lists, island names (only atoll), schedules, departure times, trip durations, distances or coordinates.

### Answers for the use case (Q2)
- **Sea edges with travel time and frequency:** **no.** MTCC gives only (synthetic) monthly passenger totals per route code.
- **What to do instead:** join `route_id` to the RTL timetable scrape in `team-kandu/`:
  - `rtl_routes.csv` (49 routes, `trips_per_day`)
  - `rtl_trips.csv` (stop-by-stop times)
  - `rtl_stops.csv` (149 stops with lat/lon)
  - `rtl_connections.csv` (615 stop pairs with `trips_per_day`, first/last departure, `shortest_minutes`)
- **Match rate:** 3 of 8 MTCC ferry codes match directly (H1, S1C1, Z5R5). S1C5, R2C1, R2C2, Z2R1 and Z5R2 are missing from the current RTL list, probably renumbered or discontinued.
- **Atoll label mismatch:** the RTL H1 route runs Ha.Ihavandhoo – HDh.Kulhudhuffushi and crosses into Haa Dhaalu, but MTCC labels it "Haa Alifu".
- **MTCC passengers** should be used at most for illustrative demand weighting, and must be flagged as synthetic.

---

## 3. Avas Ride — ride-hailing (Greater Malé)

### avas_rides_aug_sep_2026.csv (41 MB, 371,788 rows, 8 columns)
| Column | dtype | Range / values |
|---|---|---|
| date_started | datetime str | 2026-08-01 00:00:24 → 2026-09-30 23:59:54 (61 days; 4.6 k–12.9 k rides/day; peaks on 2026-09-10 and 09-12) |
| pickup_lat / dropoff_lat | float | 4.1685 – 4.2401 |
| pickup_lng / dropoff_lng | float | 73.5001 – 73.5512 |
| distance_km | float (3 dp) | 1.984 – 13.688 (median 8.22) |
| time_sec | float | **300.001** – 1,214 (median 761) |
| status | cat | payment_completed 320,140 · ride_expired 27,247 · ride_completed 24,401 |

- No nulls and no duplicate rows. Every coordinate pair is unique, which suggests jitter or anonymisation; decimal precision varies from 8 to 16 places.
- **One row** = one ride request with pickup/dropoff coordinates and a trip distance and time.
- **Geography:** only the Greater Malé road network (Malé, Hulhulé/Velana airport, Hulhumalé Phase 1 and Phase 2, joined by the Sinamalé Bridge). Villimalé is excluded because lng ≥ 73.50. **No other islands.**

**Approximate OD mix** (bbox zoning; completed rides):

| OD pair | Trips | Median km | Median min | Median km/h |
|---|---|---|---|---|
| Malé ↔ Hulhumalé Ph1 | ~81 k each way | 8.1–8.2 | 12.3–12.6 | 39 |
| Malé ↔ Hulhumalé Ph2 | ~36–39 k each way | 9.8–10.1 | 14.9–15.7 | 39 |
| Malé ↔ Airport | ~3 k / 31 k | 4.2–4.5 | 7.7–8.3 | 33 |
| Intra-Malé | 1,509 (very few) | 2.5 | 5.3 | 29 |

**Data-quality and validity concerns:**
- **Speed is almost constant:** median 38.7 km/h with SD about 3 km/h.
  - The median varies by only 36.7–39.1 km/h across hours and by 38.6–38.7 km/h across weekdays. There is no rush-hour signal.
  - `time_sec ≈ 84.8·km + 71`, with a residual SD of only 38 s.
- **Expired rides** (never taken) carry the same distance/time distribution as completed rides (median 38.5 km/h).
  → `distance_km`/`time_sec` are almost certainly **routing-engine estimates at booking**, not GPS-observed trips. The data may also be synthetic or perturbed.
- **Hard floors:** time_sec ≥ 300 s and distance ≥ ~2 km. Short trips were filtered out, which is why intra-Malé trips are nearly absent.
- The median ratio of route distance to haversine distance is 1.45, which is plausible for the bridge and the island grid.

**Answers for the use case (Q3):**
- **Islands:** yes, Malé / Hulhulé / Hulhumalé only.
- **Road speeds:** yes, but they are free-flow, router-like speeds (about 39 km/h on the bridge corridor and about 29 km/h inside Malé). Treat them as optimistic.
- **OD travel times:** yes. The ride data supports a Greater-Malé road OD matrix (or a time = 85 s/km + 71 s rule) for last-mile links to the airport, hospitals (IGMH, ADK, Hulhumalé Hospital), schools and universities (MNU, Villa College) and ferry/seaplane terminals.
- For other inhabited islands, OSM road speeds or walking speeds are needed. Most islands are under 2 km across.

### car_fare_matrix.csv (6×6)
- A symmetric zone-to-zone **flat fare in MVR** for "Male City" covering Male, Hulhumale Phase 1, Velana International Airport, Hulhumale Phase 2, Sea Plane and Domestic Terminal.
- Intra-zone fare is 30. Example inter-zone fares: Malé–Hulhumalé Ph1 85, Malé–Airport 70, Hulhumalé Ph2–Sea Plane 120.
- There are no coordinates. It is useful for a generalized-cost (money) layer and for seeing that the **seaplane and domestic terminals are distinct nodes** at VIA.

---

## 4. FollowMe — vessel GPS tracking

### Structure
- `FollowMe\FollowMe_august_2025\1.csv … 31.csv`, one file per **day of August 2025** (file N contains only `device_date` on 2025-08-N). There are 31 CSVs plus `Summary of the available data.txt`, 1.8 GB in total.
- All files share an identical header. Total **17,462,749 rows**, 441 k–660 k rows per day, and **1,776 distinct devices** (1,432–1,566 active per day).

### Schema (from the Summary file, checked)
| Column | dtype | Notes |
|---|---|---|
| poll_id | int64 | Unique DB id (no duplicates) |
| imei | str | Tracker IMEI (pseudonymous vessel id; **no vessel name, type or registration**) |
| timestamp | datetime | DB save time; spans 2025-08-01 → **2026-10-08** because of buffered uploads (99th-percentile lag about 5.8 days; 52 k rows with negative lag) |
| device_date | datetime | GPS fix time; strictly within 2025-08-01 00:00:00 → 08-31 23:59:59. **Appears to be UTC:** trip departures peak 01–09 h (06–14 local, UTC+5) and are near zero 19–23 h. |
| latitude, longitude | float | 99.96 % inside Maldives bbox (−0.7 … 7.1 N, 72.6 … 73.8 E) |
| speed | float | "Speed of the boat"; 98.9 % integers; 18.5 % zero. **Units appear to be knots:** speed derived from consecutive fixes / reported speed ≈ 1.9 (1 kn = 1.852 km/h). |
| heading | float | 0–359 normally; max 11,951 (invalid) |
| network | str | 1 = Dhiraagu (16.86 M), 2 = Ooredoo (0.46 M); undocumented 0, 68, 8 |
| cellid | str | Mostly numeric; 1.45 % hex (e.g. `CBAD`); 83 nulls |
| gsm_level | str | 0–31 |

### What one row is
One GPS fix from one vessel tracker. Fixes come every **~30 s while moving** (median dt 30 s; IQR 20–60 s) and as a **~30-min heartbeat while idle** (95th percentile about 1,812 s).

### Geographic coverage
- **Nationwide**, from Addu/Fuvahmulah (−0.7°) to Haa Alifu (7.1°). Moving points are densest in Greater Malé and Kaafu, with heavy traffic in Baa/Raa/Lhaviyani (5.1–5.8°).
- The top stationary clusters by device count:
  - Malé south harbour (4.16, 73.50; 820 devices)
  - Hulhulé/VIA jetties (4.20, 73.52; 707)
  - Thilafushi / Gulhifalhu (4.18, 73.44; 615)
  - Malé north (4.18, 73.50)
  - Hulhumalé (4.22, 73.52)
  - then Baa (Eydhafushi / Dharavandhoo / Dhonfanu), Raa, Lhaviyani, K. Kaashidhoo and others.
- Devices by latitude span: 150 under 5 km (local), 611 at 5–50 km, 827 at 50–300 km and 188 over 300 km (long-haul, incl. cargo/dhoni runs).

### Data-quality issues
- 6,277 fixes outside Maldives (e.g. lon = 15.0, lat −4.0 / 8.8). These are GPS glitches.
- Speed > 60 kn: 1,908 rows (max 770).
- 197,936 exact duplicates on (imei, device_date, lat, lon).
- 3,823 "teleport" jumps (> 150 km/h implied over ≤ 10 min).
- Heading > 360 in some rows.
- Gaps of 30 min or more when idle, so stops need a minimum dwell rule.
- No vessel typology: fishing boats, cargo dhonis, resort/tourist speedboats, public speedboats and ferries are mixed together.

### Trip extraction test (`followme_trips.py`)
**Rule:** a trip is a moving run (speed ≥ 1 kn) between stationary fixes, with no internal gap over 15 min, origin–destination distance ≥ 1 km, and duration 3 min–12 h.
- **110,074 trips from 1,655 vessels** in August. Median 16 min and 7 km; detour (path / straight line) median 1.09, 95th percentile 1.83.
- **Vessel speed classes** (by each device's median moving speed):

| Class | Devices | Trips | Median path speed | Median duration |
|---|---|---|---|---|
| Fast (≥ 18 kn, speedboats) | 669 | 76 k | 43 km/h (≈ 23 kn) | 14 min |
| Medium (9–18 kn) | 289 | 15 k | 19 km/h | 15 min |
| Slow (< 9 kn, dhonis / ferries / cargo) | 767 | 19 k | 13 km/h (≈ 7 kn) | 27 min |

- **Snapping endpoints to the 149 RTL stops** (island jetties with coordinates):
  - 18 % of trips have both ends within 1 km of an RTL stop.
  - 28 % of trips start in Greater Malé, where RTL stops are not listed.
  - The remainder are resorts, fishing grounds, Thilafushi/industrial sites and uninhabited islands.
  - Snapped trips touch **148 of 149 RTL islands** and form **1,557 directed island pairs, 467 of them with ≥ 10 trips**. Examples: Ga.Kooddoo→Ga.Villingili 377 trips, 2.1 km, median 5.8 min. R.Dhuvaafaru→R.Ungoofaaru 165 trips, 4.7 km, 8.5 min. L.Fonadhoo→L.Hithadhoo 12.9 km, 21 min. S.Hulhumeedhoo→S.Feydhoo 13.8 km, 16 min.
- **Example long-haul vessel:** it shuttles Dhigurah area (3.537 N, 72.931 E) ↔ Malé (4.188, 73.526), about 101 km in 100–110 min (about 58 km/h ≈ 31 kn), roughly twice a day. This is a typical scheduled speedboat service.

### Answers for the use case (Q4)
- **What it is:** a commercial **boat/vessel tracking feed** (the "FollowMe" fleet tracker). It is not bus GPS and not AIS. Coverage spans the whole country.
- **Real speeds:** **yes.** The bimodal speed distribution gives mode-specific sea speeds: speedboat about 40–45 km/h, dhoni/ferry about 12–15 km/h. Detour factor about 1.1.
- **Route geometries:** **yes.** The ~30 s fixes trace real channels and reef passes. Polylines can be built per island pair.
- **Dwell times:** possible with a proper stop detector (stationary ≥ 3–5 min within 150–200 m). The quick state-flip segmentation over-splits stops, so dwell and stop statistics need this refinement.
- **Ferry trajectories between islands:** **yes.** There are empirical OD durations for hundreds of island pairs. Trip counts per hour per pair can serve as a *service-intensity* proxy.
  - Caveat: they mix public, private and fishing traffic, so they are **not** equal to public-ferry headways. Use RTL timetables for scheduled frequency and FollowMe for realistic in-vehicle times and for informal speedboat links that RTL does not cover.
- **Privacy:** IMEIs are persistent device ids. Aggregate to OD/edge level and do not publish raw tracks per IMEI.

---

## 5. Join keys and name normalisation (Q5)

| Dataset | Spatial key available | Island / place naming |
|---|---|---|
| MACL | none (MLE only; anonymised routes; region) | — |
| MTCC | `route_id` (H1, S1C1, Z5R5 …), `zone` ("RTL Zone 05"), `atoll` (full names, e.g. "Gaafu Alifu & Gaafu Dhaalu") | Bus: "Male (West Park)", "Velana Airport", "Hulhumale Phase 1" |
| Avas rides | lat/lon (Greater Malé) | none |
| Avas fare matrix | zone names | "Male", "Hulhumale Phase 1/2", "Velana International Airport", "Sea Plane", "Domestic Terminal" |
| FollowMe | lat/lon (nationwide) | none (coordinates only) |
| team-kandu RTL (supplement) | stop lat/lon, `route` code | "Atoll-prefix.Island" e.g. `Ha.Ihavandhoo`, `Gdh.Thinadhoo`, `Sh.Kan'ditheemu` |
| OurAirports (supplement) | IATA/ICAO, lat/lon, ISO 3166-2 `MV-xx` | "Funadhoo Airport", municipality |

**The only reliable cross-dataset key is coordinates** (snap to island polygons or points), plus `route_id` for MTCC ↔ RTL. Build a master island gazetteer (official island code, atoll code, name variants, centroid/polygon) and join everything to it spatially.

**Normalisation issues seen:**
- **Diacritics and apostrophes:** Malé / Male / Male' ; Hulhumalé / Hulhumale ; Kan'ditheemu vs Kanditheemu.
- **Atoll naming systems:**
  - full name ("Haa Alifu", "Gaafu Dhaalu")
  - administrative letter code (Ha, HDh, Sh, N, R, B, Lh, K, AA/Aa, ADh, V, M, F, Dh, Th, L, GA/Ga, GDh/Gdh, Gn, S)
  - ISO `MV-07` style codes
  - geographic atoll names (Thiladhunmathi, North/South Malé Atoll).
  Combined labels also appear, e.g. MTCC "Gaafu Alifu & Gaafu Dhaalu".
- **Separator inconsistency:** `Ha.Ihavandhoo` (no space) vs `Aa. Bodufolhudhoo` (space) across the team-kandu files; "Zone 5" vs "RTL Zone 05".
- **Homonyms:** many island names repeat across atolls (Thinadhoo in Gdh and V; Villingili in Ga vs Villingili/Villimalé in Malé; Maalhos in B and AA; Fonadhoo, Hithadhoo …). **Always key on atoll + island.**
- **Airport naming:** "Velana International Airport" / "Velana Airport" / VIA / MLE / Hulhulé. The Avas fare matrix separates the domestic terminal and the seaplane base, which are distinct nodes on the same island.
- **Cross-atoll routes:** the RTL H1 route crosses atolls but is labelled with a single atoll in MTCC.
- **Time zones:** FollowMe `device_date` appears to be UTC (+5 h to local). MACL and Avas appear to be local time.

---

## 6. How each dataset feeds the network

| Network layer | Dataset | What we take | Status / caveat |
|---|---|---|---|
| **Sea edges — in-vehicle time** | **FollowMe** | Median and p10 trip duration per island pair; speed by vessel class (fast ≈ 43 km/h, slow ≈ 13 km/h); detour ≈ 1.1 for edges with no observations | Real data (Aug 2025). Clean outliers; detect stops properly; device_date is UTC. |
| **Sea edges — geometry** | **FollowMe** | Track polylines per island pair | Aggregate; privacy-safe |
| **Sea edges — frequency / wait** | RTL timetables (team-kandu) → headway → wait ≈ ½ headway; FollowMe trips/day as an informal-service proxy | MTCC route_id joins 3/8 directly | MTCC itself has no schedules |
| **Sea demand weights** | MTCC ferry_monthly | Passengers by route-month | **Synthetic (README)**, so illustrative only |
| **Road edges — Greater Malé** | **Avas rides** | OD time matrix / `t = 85 s·km + 71 s`; ~39 km/h corridor, ~29 km/h intra-Malé | Router-estimate-like, free-flow, optimistic; Greater Malé only |
| **Road cost (MVR)** | Avas fare matrix | Zone fares incl. Sea Plane and Domestic Terminal nodes | 6 zones only |
| **Bus layer — Greater Malé** | MTCC bus sheets (+ team-kandu `rtl_bus_*`) | Route list; ridership (synthetic) | Use the RTL bus departures for frequency |
| **Air edges — domestic** | *Not in MBS data.* OurAirports + Maldivian/Manta schedules | Airport nodes; duration ≈ distance / 350 km/h + overheads | MACL unusable for domestic |
| **International gateway context** | MACL | MLE movements and passengers by region and year | Anonymised routes; context only |
| **Last-mile on outer islands** | none of the four | Walking / OSM roads | — |

---

## 7. Recommended next steps
1. Build an **island gazetteer**: official code, atoll code, name variants, polygon or centroid. Snap the FollowMe stop clusters and the RTL/airport points to it.
2. Refine FollowMe stop detection (≥ 3 min stationary within 200 m). Then produce an `island_pair_edges.parquet` with columns n_trips, vessels, median/p10/p90 duration, speed class mix and departures by hour (local time).
3. Build the scheduled-ferry layer from `team-kandu/rtl_trips.csv` and `rtl_connections.csv` (headway → expected wait). Use FollowMe to validate RTL `shortest_minutes`.
4. For Greater Malé, fit the Avas time model, apply a congestion uplift (e.g. ×1.3–1.5 at peak, since the data shows no peak effect), and add terminal nodes (ferry terminals, VIA domestic terminal, seaplane base).
5. Treat MTCC passenger numbers and Avas times as **indicative**. State this clearly in any deliverable.
