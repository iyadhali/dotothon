# 02 — Data profile: HeiGIT accessibility (HDX) + Team Kandu transport CSVs

Profiled 2026-10-24. The data files were treated as untrusted and nothing inside them was executed. Scripts live in `C:\Users\user\Music\Datathon\scripts\` and were run with `python -I <script> <data path>`:

| Script | Purpose |
|---|---|
| `profile_csvs.py` | Generic profile of a CSV or GPKG: dtypes, nulls, nunique, min/max, head, value counts; GPKG layers, CRS, geometry, feature counts |
| `heigit_summary.py` | HeiGIT coverage per admin unit, headline shares, implied population base, isochrone areas and polygon parts |
| `kandu_timeseries.py` | Catalogue of `mma_series` and `observations` |
| `kandu_rtl_deepdive.py` | RTL stops, routes, trips and connections checks, GTFS readiness, bus tables, cross-file joins |
| `kandu_census_join.py` | Cleans the census rows; exact and fuzzy matching of RTL, ODI and airline names to census islands |

Note: `python -I` ignores user site-packages, and pip put pandas, geopandas and pyogrio there. Each script therefore appends `site.getusersitepackages()` to `sys.path` by hand.

---

## TL;DR

1. **HeiGIT gives only a partial, car-only picture and is not usable as ground truth for the Maldives.**
   - Units with zero access are simply left out, not reported as 0%:
     - education: 10 of 21 ADM1 units
     - hospitals: 9 of 21
     - primary healthcare: 3 of 21 (Malé, Kaafu, Alif Alif)
   - National headline figures:
     - **46.9%** of people are within 5 km of a school, saturating at **47.9%** from 15 km to 50 km.
     - **45.2%** are within 10 min of a hospital, rising only to **45.9%** at 120 min.
     - **38.5% / 38.9%** for primary healthcare (10 / 120 min).
   - The flat curves are the tell-tale sign of no sea crossings. Isochrones never leave the island the facility is on, and OSM facility coverage is incomplete: almost every inhabited island has a school, yet only about 43 polygon parts are reachable.
2. **RTL ferry data is roughly 80% of the way to GTFS for Zones 1, 2, 4, 5 and 6.**
   - It has 149 stops with coordinates, 49 routes and 102 timed daily trips (390 stop-times, monotonic, no gaps).
   - Missing pieces: calendar/service days, Zone 3 (Kaafu, Alif Alif, Alif Dhaalu, Vaavu, Meemu: the Malé region), and 61 routes that are "unscheduled" (stop lists without times).
   - Headways barely apply: most routes run 2 trips a day (out in the morning, back in the afternoon).
   - `odi_connections` partially covers the missing Zone 3 with island pairs and coordinates, but no times.
3. **`mma_series` holds 32 national macro series** from the Maldives Monetary Authority (MMA) statistics database: CPI transport, fuel imports, tourism, insurance, BoP transport. They are **not useful for island-level accessibility**, except as context.
   - **`observations` is valuable.** Statistical Yearbook table 3.3 holds the **Census 2022 resident population for all 186 inhabited "admin" islands** plus the Malé wards, and registered population for 2023–2025. That is the per-island denominator we need.
   - It also holds monthly domestic-airport passenger and aircraft-movement series.

---

## A. HeiGIT "Maldives – Accessibility Indicators" (`data\hdx-heigit-access\`)

### Files and structure

| File | Rows | Notes |
|---|---|---|
| `MDV_education_access.gpkg` | adm0 = 10, adm1 = 200, adm2 = 220 features | range_type = DISTANCE, 5–50 km in 5 km steps (10 bands) |
| `MDV_education_access_wide.csv` / `_long.csv` | 220 / 440 | long: population_type ∈ {total, school_age} |
| `MDV_hospitals_access.gpkg` | adm0 = 12, adm1 = 216, adm2 = 192 | range_type = TIME, 600–7200 s (10–120 min, 10-min steps, 12 bands) |
| `MDV_hospitals_access_wide.csv` / `_long.csv` | 216 / 1296 | long: total, under_5, school_age, adults, women_childbearing, elderly |
| `MDV_primary_healthcare_access.gpkg` | adm0 = 12, adm1 = 72, adm2 = 48 | TIME, 10–120 min |
| `MDV_primary_healthcare_access_wide.csv` / `_long.csv` | 72 / 432 | same six population types as hospitals |

- **Layers.** Every GPKG has layers `adm0`, `adm1` and `adm2`. All are MultiPolygon in EPSG:4326, with bounds of about 72.89–73.58 E and −0.69–6.99 N.
- **What a row is.** One row is one (admin unit × range band). Its geometry is the **isochrone or distance band clipped to that admin unit**, not the admin boundary. For example, the total adm0 reachable area is only about 30–34 km² for education and about 9.7 km² for primary healthcare.
- **Population columns.** These are the cumulative `population` and `population_share` (% of the unit's population) at that range. `*_interval` columns hold the increment over the previous band.
- **Columns (wide):**
  - `name, iso, id, country, admin_level, category, range_type, range, population, population_share, population_interval, population_interval_share`
  - plus `{school_age|under_5|adults|women_childbearing|elderly}_population[_share|_interval|_interval_share]`
  - Dtypes: ints for counts, floats for shares (%), object for IDs. Zero nulls apart from `iso`.
- **`id`** is an opaque HeiGIT/geoBoundaries-style ID, such as `51498476B18155918690693` for adm1 and `70690204B…` for adm2. **`iso`** is ISO 3166-2 (`MV-01` … `MV-MLE`) on ADM1 and empty on ADM2.

### Admin coverage (answer to Q1a): only some units

There are 21 ISO ADM1 units (20 atolls plus Malé City). Units with no reachable facility are **absent rather than zero**:

| Category | ADM1 units present | Missing ADM1 |
|---|---|---|
| education | Addu, Alif Alif, Haa Alif, Haa Dhaalu, Kaafu, Laamu, Malé, Noonu, Raa, Thaa (10) | Alif Dhaalu, Baa, Dhaalu, Faafu, Fuvahmulah, Gaafu Alif, Gaafu Dhaalu, Lhaviyani, Meemu, Shaviyani, Vaavu |
| hospitals | Addu, Alif Alif, Gaafu Dhaalu, Haa Alif, Haa Dhaalu, Kaafu, Laamu, Malé, Thaa (9) | 12 units, including Fuvahmulah, Baa, Raa, Noonu, Shaviyani and Lhaviyani |
| primary_healthcare | Alif Alif, Kaafu, Malé (3) | 18 units: OSM-tagged PHC exists only around Malé |

- ADM2 uses the older geographic atoll names: Addoo, Hadhdhunmathee, Kolhumadulu, North/South Thiladhunmathe, North/South Maalhosmadulu, South Miladhunmadulu, South Huvadhoo, and Male'.
- **ADM2 "Male'" appears twice**, with two distinct IDs:
  - `…B12193603739109`, implied population about 148.7k: Malé city plus Hulhumalé
  - `…B31972615950169`, about 72k
  - Always key on `id`, not `name`.
- Spelling differs between levels: ADM1 uses "Malé" (UTF-8 é, which renders as `Mal�` on a cp1252 console), while ADM2 uses "Male'".

### Car-only? (answer to Q1b)

- The files do not record the routing profile. The HDX/HeiGIT methodology uses openrouteservice isochrones with the car profile (not verified in this session).
- The internal evidence is consistent with **road-only routing and no sea legs**:
  - Coverage saturates very quickly: education stays flat after 15 km, hospitals add only 0.65 pp between 10 and 120 min.
  - Reachable geometry is about 35–47 polygon parts nationally, roughly the number of islands with an OSM-mapped facility.
  - Nothing reaches across lagoons, except at Malé–Hulhulé–Hulhumalé, which is bridge- and causeway-connected.
- Implication: **HeiGIT measures "people on the same island (road-connected) as a mapped facility".** It does not model the multi-modal ferry, speedboat or air access that our project is about.

### Headline numbers (ADM0, total population)

The implied population base is **442,770**, i.e. `population / population_share`. That is a gridded population layer (probably WorldPop), compared with the Census 2022 figure of 515,132.

| Indicator | Cumulative share |
|---|---|
| Within 5 km of a school | **46.92%** (207,761) |
| Within 10 km of a school | 47.57% |
| Within 15–50 km of a school | **47.87%** (flat) |
| Within 10 min of a hospital | **45.24%** (200,318) |
| Within 30 min of a hospital | 45.39% |
| Within 60 min of a hospital | 45.76% |
| Within 120 min of a hospital | **45.89%** |
| Within 10 min of primary healthcare | **38.51%** |
| Within 120 min of primary healthcare | **38.86%** |

**Per-unit shares at the largest range** (education / hospitals):

| Unit | Education | Hospitals |
|---|---|---|
| Malé | 99.2% | 99.8% |
| Kaafu | 97.6% | 77.4% |
| Alif Alif | 88.2% | 89.6% |
| Laamu | 61.9% | 66.5% |
| Haa Dhaalu | 42.2% | 42.2% |
| Addu | 21.4% | 21.5% |
| Haa Alif | 9.1% | 9.1% |
| Raa | 5.3% | — |
| Thaa | 3.3% | 3.3% |

Gaafu Dhaalu hospitals: 86.0%.

### Data-quality issues (HeiGIT)

- **Zero-access units are dropped.** A naive average over the listed units overstates access. Left-join onto a full ADM1 list and fill with 0.
- **The population denominator disagrees with the census.** Implied per-unit populations vs. Census 2022 resident population of inhabited islands:

  | Unit | HeiGIT implied | Census 2022 |
  |---|---|---|
  | Raa | 41.6k | 17.6k |
  | Thaa | 28.4k | 10.3k |
  | Alif Alif | 1.4k | 8.0k |
  | Kaafu | 7.8k | 17.7k |

  The gridded population appears misallocated, possibly onto resorts, reefs or uninhabited islands. Do not use HeiGIT's population for per-island work.
- **Facility completeness depends on OSM.** Primary healthcare covers only 3 units, which is clearly incomplete; Maldives has a health centre on almost every inhabited island.
- **No per-island granularity.** The smallest unit is ADM2 (old atoll groups). The clipped isochrone polygons can still be intersected with island polygons to say which islands contain a mapped and reachable facility.
- Duplicate ADM2 name "Male'" (see above). The wide and long CSVs are consistent: long = wide × population types.

**Verdict:** use HeiGIT as a **baseline / foil**, e.g. "car-only models say 47% have access; adding ferries changes that". Also use it as a cheap source of OSM facility locations, via the isochrone seeds. Do not use it as the accessibility answer.

---

## B. Team Kandu CSVs (`data\team-kandu\`)

All files are UTF-8 with comma separators. Columns ending in `fetched_at` or `checked_at` show the scrape date of **2026-10-10** (a Saturday).

### B1. RTL ferry network

#### `rtl_stops.csv`: 149 rows; one row = one ferry stop (island jetty)

| col | dtype | notes |
|---|---|---|
| code | int | 101–249, unique |
| name | str | `Atoll.Island`, e.g. `B.Eydhafushi`; unique |
| atoll | str | 15 codes: HA, HDh, Sh, N, R, B, Lh, F, Dh, Th, L, GA, GDh, Gn, S |
| island | str | 142 unique; 7 island names repeat across atolls (Feydhoo, Goidhoo, Maamendhoo, Magoodhoo, Meedhoo, Nilandhoo, Vaadhoo) |
| lat, lon | float | **0 nulls**; lat −0.68 to 7.10. Plausible: stays within about 46 km of the atoll median; nearest neighbour min 1.07 km, median 4.2 km |
| routes | str | space-separated route codes; 32 nulls (unserved stops) |
| scheduled | yes/no | 117 yes, 32 no |

- **No stops in K, AA, ADh, V or M (RTL Zone 3, the Malé region).**
- All 7 Lh stops have `scheduled=no`.
- Atoll-code casing is inconsistent: `Ha`, `Hdh`, `Ga` and `Gdh` in `name` vs `HA`, `HDh`, `GA` and `GDh` in `atoll`.

#### `rtl_routes.csv`: 49 rows; one row = one scheduled route

- Columns: `route_id` (int), `route` (code), `zone` (Zone 1, 2, 4, 5, 6; **no Zone 3**), `description` ("A - B"), `stops` (comma list), `trips_per_day` (1–6), `color` (hex), `fetched_at`.
- Route code families include `Z2R*`, `Z4R*`, `Z5R*`, `Z6R*`, `Z2H*`, `Z4H*`, `Z2UBC*`, and Zone 1's `H1`, `H2`, `R1C*`, `R1V*`, `S1C*`, `S1V*`, `S2C*`. The prefixes are inconsistent.

#### `rtl_trips.csv`: 390 rows; one row = one stop-time

- Columns: `route_id, route, zone, trip, order, stop, time (HH:MM)`.
- 102 trips in total (route × trip ordinal). Per route: 1 trip (6 routes), 2 trips (39), 4 trips (3), 6 trips (1).
- Service window **06:00–18:35**, no overnight.
- Consistency checks:
  - All trips have monotonic times; no zero or negative legs. Legs run 5–100 min, median 20.
  - The trip count matches `trips_per_day` for every route.
  - Every trip stop exists in `rtl_stops`.
  - `routes.stops` equals the trip stop set for all routes.
- Only one time per stop, so arrival = departure.

#### `rtl_connections.csv`: 615 rows; one row = a directed stop pair reachable on one boat without transfer

- Columns: `from_stop, to_stop, from/to_atoll, trips_per_day (1–4), first_departure, last_departure, shortest_minutes (5–155, median 40), routes`.
- Derived from `rtl_trips`. 596 of the 615 pairs have a reverse pair, and 66 are inter-atoll, e.g. Dh↔F and GA↔GDh.
- Handy as a ready-made graph edge list.

#### `rtl_unscheduled.csv`: 61 rows; one row = a route with a stop sequence but no times

- Columns: `zone, route, description, stops ("A > B > C")`. Zones: Zone 1 = 34, Zone 2 = 19, Zones 4–6 = 8.
- Covers Lhaviyani (R2C*), some Baa routes and others.
- **One row has `route = "ERROR"`**, with every stop doubled (`Sh.Noomaraa > Sh.Noomaraa > …`). It duplicates scheduled route S2C5, so drop it.

#### How close is this to GTFS? (answer to Q2)

| GTFS file | Source | Status |
|---|---|---|
| agency.txt | — | trivial to write (RTL / MTCC) |
| stops.txt | rtl_stops (code, name, lat, lon) | ✅ complete for the 149 stops |
| routes.txt | rtl_routes (route_id, route → short_name, description → long_name, color) | ✅ use `route_type = 4` (ferry) |
| trips.txt | distinct (route_id, trip) | ✅ build `trip_id = route + "_" + trip`; `direction_id` derivable from origin (43 of 49 routes are bidirectional) |
| stop_times.txt | rtl_trips | ✅ arrival = departure = `time`; `stop_sequence = order` |
| calendar.txt | — | ❌ **missing**: one day's snapshot (Saturday); weekday/Friday variation unknown, so assume a daily service and flag it |
| shapes / fares / frequencies | — | ❌ none for ferries (bus routes have `fare_mvr`) |
| Coverage | — | ❌ **Zone 3 absent**; 61 unscheduled routes; 32 stops unserved |

- **Headways.** With mostly 2 trips/day, the meaningful service metrics are **daily frequency, first/last departure and the ability to make a same-day return**, not headway. Example headways: H1 465 min; R1C6 20/405/20 min; R1C7 360/60/180 min.
- **Verdict.** A valid GTFS feed can be generated in about 1 hour of scripting, enough for r5py, OpenTripPlanner or a custom time-expanded Dijkstra. Add calendar assumptions and patch Zone 3 from `odi_connections` or another source.

#### Coverage against the census (via observations table 3.3; see B3)

- RTL stop islands match **113 of 149 exactly** to census island names. With normalisation of Dhivehi transliteration (drop the nasal "n" before d/b/g, the apostrophe and the trailing "u" or "aa"), **about 141 match**.
- The 8 genuine non-matches are airport or industrial islands absent from the census list: Ga.Kooddoo, Gdh.Maavarulu, R.Ifuru, Lh.Madivaru, Lh.Felivaru, Lh.Maafilaafushi. Two more need manual checks: L.Gan (= census "L Gamu") and Hdh.Kurin'bee.
- Matching examples:
  - Correct: Bandidhoo→Badidhoo, Dhihdhoo→Dhidhdhoo, Ungoofaaru→Ugoofaaru, Hon'dehdhoo→Hoadedhdhoo
  - Fuzzy false positive: Gdh.Kaadehdhoo→Gadhdhoo
  - Partial: S.Hulhumeedhoo is census "Hulhudhoo" + "Meedhoo"
  - A manual crosswalk is needed for about 30 names.
- About **148 of 186 inhabited atoll islands (about 188k of 237k atoll residents) have an RTL stop**.
- The largest unserved islands are mostly Zone 3: L Gamu 4.8k (likely an alias), K Maafushi 4.5k, ADh Maamigili 2.8k, ADh Mahibadhoo 2.6k, K Kaashidhoo, K Himmafushi, AA Thoddoo, K Thulusdhoo, K Huraa, M Mulah.

### B2. RTL buses (Greater Malé plus 7 island systems)

- **`rtl_bus_routes.csv`** (28 rows; one row = one bus route):
  - Areas: Greater Malé 15, Addu City 3, Laamu 3, Hdh. Kulhudhufushi 2, N.Kendhikulhudhoo 2, Fuvahmulah, R.Dhuvaafaru, Ha.Dhidhdhoo.
  - Columns: `area, route_number, name, from_stop, to_stop, stops (9–90), fare_mvr (5–15; 4 null), minibus, trips_per_day (17 null; only the Greater Malé big-bus routes have it, 17–105), departures_left_when_fetched, color, fetched_male_time (2026-10-10 19:53)`.
  - One `to_stop` has a trailing tab (`Villimale Hospital\t`).
- **`rtl_bus_stops.csv`** (612 rows; one row = one stop on one route):
  - Columns: `order, stop, code, lat, lon`, with 402 unique stops, all with coordinates and one coordinate per code.
  - Good for intra-island links: Addu Link Road (LR01/02, 90 stops), Laamu Fonadhoo–Gan link road, Malé–Hulhumalé–Villimalé.
- **`rtl_bus_departures.csv`** (1,686 rows; one row = a departure at a stop):
  - Only **11 Greater Malé routes** and **only departures after the scrape time (19:54–23:59)**. It is a partial evening snapshot, not a full timetable.
  - Use `trips_per_day` instead, or re-scrape earlier in the day.

### B3. `observations.csv`: Statistical Yearbook tables (9,196 rows; long format)

- **Columns:** `date (YYYY or YYYY-MM), period (year/month), geo, group, subgroup, metric, unit, value (float, 0 nulls), source_table, edition (2024–2026), source_url (statisticsmaldives.gov.mv yearbook xlsx)`.
- **One row** = one value for geo × date × (group, subgroup) × metric, from one yearbook table edition. There are no duplicate keys.

| source_table | Metric | Geo | Span | Rows |
|---|---|---|---|---|
| **3.3** | **census_population**, census_foreign_population (2022); registered_population (2023–25) | **186 inhabited atoll islands** + 10 Malé wards/areas + totals | 2022–2025 | 996 |
| 8.23 | parking_violations by vehicle type | national | 2020–23 | 153 |
| 10.12 | resort_beds | by atoll | 2009–25 | 331 |
| 10.9 | tourist_arrivals, tourist_bed_nights | national | monthly 2014–25 | 252 |
| 11.13 / 11.14 / 11.15 | passengers dom./intl. arr./dep. at Velana, Hanimaadhoo and Maafaru airports | airport | monthly 2023–25 | 432 |
| **11.16** | passengers IN/OUT at **17 domestic airports** | airport | monthly 2015–25 | 2,994 |
| **11.17** | aircraft_movements at 16 domestic airports | airport | monthly 2011–24 | 1,546 |
| 11.18 / 11.19 / 11.20 | aircraft movements (scheduled, non-scheduled, charter) at Velana, Gan and Hanimaadhoo | airport | monthly 2023–25 | 864 |
| 11.21 | passengers at Gan | airport | monthly 2023–25 | 252 |
| 11.3 | registered and newly registered vehicles by type | national | 2010–23 | 1,374 |

**Census table 3.3 structure** (key for us):

- `group` = atoll code (AA, ADh, B, Dh, F, GA, GDh, Gn, HA, HDh, K, L, Lh, M, N, R, S, Sh, Th, V).
- `subgroup` = island name, and `geo` = "`<atoll> <island>`", e.g. `AA Bodufolhudhoo` = 704.
- 186 island rows sum to **236,911** (= "Admin islands").
- Malé rows have `group = null`: Maale 211,908, made up of Henveiru, Galolhu, Machchangolhi, Maafannu, Vilimaale, Hulhumaale Ph1/Ph2, Hulhule, and Harbours.
- Totals rows: `Republic` = 515,132 and `Admin islands` = 236,911.
- **Bug:** `S Non-admin islands` (66,313, i.e. resorts and industrial islands nationally) is wrongly tagged `group = S`. Exclude it, or Addu will be inflated 3.6×.
- Check: Republic 515,132 = Maale 211,908 + admin islands 236,911 + non-admin 66,313.
- **Do not sum all rows**, because totals are mixed in.

**Other quality notes for `observations`:**

- `source_table` must be read as **string**. As a float, `11.20` becomes `11.2` and `3.30` becomes `3.3`, and 11.3 and 11.30 could collide.
- Airport names are spelled inconsistently across tables: "ADh. Maamigilli" vs "ADh. Maamigili", "GA. Kooddoo" vs "GA. Koodoo", "Kulhudhufushi" vs "Kuludhufushi".
- `qa_flags.csv` documents revisions and total mismatches in table 11.17. For example, the 2014 GA. Koodoo monthly values sum to 2,902 against a printed total of 826, and the 2024 vs 2025 editions disagree. Prefer the latest edition.

### B4. `mma_series.csv`: MMA statistics database extracts (6,818 rows, 32 series)

- **Columns:** `series_id, group, name, path (database breadcrumb), unit, frequency, date (period end), value, source`. 0 nulls; no duplicate (series, date).
- **One row** = one observation of one series.
- **Groups:**

  | Group | Series |
  |---|---|
  | prices | CPI total and transport for National / Malé / Atolls; Malé petrol and diesel indices; 1985–2026 monthly |
  | fuel_imports | imports of petroleum, petrol, diesel (marine gas oil), aviation gas, transport equipment; jet-fuel re-exports; USD monthly 2004–26 |
  | tourism | arrivals and occupancy 1988–2026; arrival flights 2012–26 |
  | economy | transport and communication GVA (quarterly and monthly); loans to the transport sector |
  | insurance | marine cargo, marine hull, motor, aviation premiums and claims; quarterly 2015–26 |
  | services | BoP transport passenger and freight, credit/debit; annual 2011–2026 |

- Several **names repeat** ("Total index" ×3, "Transport" ×4, "Passenger"/"Freight" ×2). Disambiguate with `path`, e.g. National vs Malé' vs Atolls CPI, or BoP credit vs debit.
- **Usefulness:** low for island-level accessibility. Two narrative uses:
  - the diesel/marine gas oil price index or imports as a ferry cost-pressure proxy
  - Malé vs Atolls CPI transport divergence
- Sources inside the file are mixed (MBS, Customs, Tourism Ministry, MACL, MMA). MMA is the aggregator.

### B5. Other small files

- **`maldivian_destinations.csv`** (27 rows; one row = a Maldivian airline destination):
  - Columns: `code` (IATA), `name`, `domestic` (19 yes / 8 no), `fetched_at`.
  - Domestic includes GAN, DRV, FMT, FND, FVM, HAQ, HRF, IFU, KDM, KDO, KDU (Kulhudhuffushi), MAQ, MRL, MDV, MLE, MUL, TMF, among others.
  - Names are city or airport-island names ("Addu City", "Male", "Kooddoo", "Maavarulu"). About 9 match census islands directly; the rest need a manual airport→served-island crosswalk.
  - **There are no schedules or frequencies.** Use observations 11.16/11.17 for volumes.
- **`odi_connections.csv`** (58 rows; one row = an island pair with a direct sea link, checked 2026-10-10):
  - Columns: `island_a, island_b, atoll_a, atoll_b, lat/lon_a, lat/lon_b, checked_at`.
  - Covers **only K, AA, ADh and V**, i.e. exactly the Zone 3 gap in RTL. 24 islands; hubs are "K. Malé" (23 links) and "Velana Hulhule Airport" (19).
  - **3 rows have null coordinates for "Adh. Hangnaameedhoo".**
  - No times or frequencies, so it can only provide edges with assumed speeds (e.g. distance / 25 kn for a speedboat).
  - Name format is `"Aa. Island"`, unlike RTL's `"B.Island"` and census `"AA Island"`.
  - "ODI" is unexplained, perhaps a speedboat/ferry booking site. Ask Team Kandu.
- **`parse_log.csv`** (37 rows): Kandu's scrape log per yearbook edition and table (all `ok`, row counts). Provenance only.
- **`qa_flags.csv`** (32 rows): `kind` ∈ {revised 24, arrival_departure_imbalance 7, total_mismatch 1}, mostly table 11.17. Provenance and quality only.

---

## Joinable keys across files

| From | To | Key / method | Quality |
|---|---|---|---|
| rtl_trips.stop / rtl_connections.from/to_stop / rtl_unscheduled.stops | rtl_stops.name | exact | 100% |
| rtl_trips.route_id | rtl_routes.route_id | exact | 100% |
| rtl_stops (atoll, island) | observations 3.3 (group, subgroup) | normalised name within atoll | 113 exact, about 141 with transliteration normalisation, about 8 true non-matches (airport/industrial islands) |
| odi island_a/b ("Aa. X") | census (AA, X) | split on ". ", normalise | 19/24; misses: K. Malé / K. Hulhumalé (map to Malé wards), Velana airport (Hulhule), Adh. Dhangethi/Hangnaameedhoo (census "Dhagethi"/"Hangnameedhoo") |
| maldivian_destinations.name | census / airports in obs 11.16–11.17 | manual crosswalk (airport island → served island) | weak; about 9 direct |
| HeiGIT ADM1 `iso` (MV-xx) | census atoll code | static ISO↔atoll-letter table (e.g. MV-13 = R, MV-08 = Th, MV-MLE = Malé) | easy, 21 rows |
| HeiGIT geometry | islands | spatial intersect of the isochrone polygons with island polygons (needs an island layer) | needed for any island-level reuse |
| rtl_bus_stops (lat/lon) | facilities / islands | spatial | good; coordinates complete |

**Recommended canonical island key:** `atoll_code` (census style: AA, ADh, B, Dh, F, GA, GDh, Gn, HA, HDh, K, L, Lh, M, N, R, S, Sh, Th, V) + `island_norm`.

- `island_norm` = lowercase, ASCII only, no apostrophes, with "n" before d/b/g/dh removed and trailing u/aa variants collapsed.
- Then add a hand-maintained alias table of about 30 rows, e.g. L.Gan→Gamu, S.Hulhumeedhoo→Hulhudhoo + Meedhoo, Kurin'bee.

---

## Recommendations

1. **Population denominator:** use Census 2022 from `observations` table 3.3, filtered to island rows plus the Malé wards. Do not use HeiGIT's population.
2. **Ferry graph:** build GTFS from the rtl_* files (stops, routes, trips, stop_times; calendar = daily, flagged as an assumption). Merge the `rtl_unscheduled` sequences as edges with assumed times. Add `odi_connections` as untimed edges for Zone 3 (K/AA/ADh/V), with assumed speeds. Zone 3 timetables (RTL Zone 3 / MTCC Malé-region) remain the biggest gap. Ask Team Kandu or re-scrape.
3. **Air layer:** use `maldivian_destinations` for the domestic network nodes and observations 11.16 for passenger volumes. Schedules are still needed.
4. **HeiGIT:** cite it as the "car-only baseline: about 47% within reach". Use it to show what multi-modal modelling adds. Reuse its OSM facility seeds only after cross-checking against the official school and health facility lists.
5. **Hygiene:**
   - Read `source_table` as a string.
   - Drop the `ERROR` row from `rtl_unscheduled`.
   - Drop the mis-tagged `S Non-admin islands` row.
   - Strip whitespace and tabs from bus stop names.
   - Key on HeiGIT `id`, not on the ambiguous names.
