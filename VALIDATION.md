# Validation — multimodal accessibility prototype

Validated **24 October 2026** on macOS. The prototype answers: *given the published
RTL ferry snapshot, an estimated domestic-air frequency layer, selectable land/sea/air
modes and specific routes, how long does it take a resident of each inhabited island to
reach a listed hospital, regional hospital, education facility, or a facility claiming a
selected diagnostic/specialist/dental intervention on the stated reference day?*

Reference day: **10 October 2026** (single RTL timetable snapshot). Time zone:
Indian/Maldives (UTC+5). Population scope: the **191 inhabited administrative
islands, 447,420 residents** (Census 2022). See `web/public/data/multimodal.json`
`meta` for the machine-readable version.

## 1. Checks run

Run sequentially from the repository root and `web/`.

| Command | Result |
|---|---|
| `python -m unittest discover -s tools/tests -v` | **7 tests OK** |
| `python3 -m unittest discover -s scripts/multimodal/tests -v` | **50 tests OK** |
| `cd web && npm run test:routing` | **38 tests, 38 pass** |
| `cd web && npm run test:db` | **4 tests, 4 pass** (build, parity, tamper, missing source) |
| `cd web && npm run db:check` | **exit 0**, digest `526d70e09d1321161267fdf74adb1786e0d2f7fe720625361269ccc7163cd1f7` |
| `cd web && npm run check:routing` | **exit 0** (invariants + national summary + pilot) |
| `cd web && npm run typecheck` | **exit 0** |
| `cd web && npm run build` | **exit 0**, `Σ Total size: 7.07 MB (1.43 MB gzip)` including the ~2.3 MB SQLite asset |
| Built server `GET /api/health` | **200** `{"status":"ok","application":"maldives-mobility","database":{"available":true,"schemaVersion":1,"islands":200,"facilities":945,"services":166,"categories":48}}` |
| Built server `GET /api/network` | **200**, 924,599 bytes (compact JSON, same payload as source) |
| Built server `GET /api/islands` | **200**, 280,261 bytes, `application/geo+json` |
| Built server `GET /api/hdx` | **200**, 6,742 bytes |
| Built server with `MULTIMODAL_DB_PATH` missing | `/api/network` and `/api/health` **503** `database_unavailable` |
| Built server with a corrupt DB file | `/api/network` **503** `database_unavailable` (quick-check/missing-table guard) |
| Built server `GET /` | **200**, title `Island Access Atlas — Maldives multimodal accessibility` |
| Built server `GET /data/multimodal.json` | **200**, 1,120,880 bytes (static fallback) |
| Built server `GET /data/islands.geojson` | **200**, 280,261 bytes |
| Built server `GET /data/heigit-baseline.json` | **200**, 10,004 bytes |
| Built server `GET /data/qgis/index.html` | **200**, QGIS landing page |
| Headless Chrome, API path | Header `SQLite API`; journey/national metrics match static build; no console errors |
| Headless Chrome, API blocked | Header `Static fallback`; same journey/metrics; no fixture banner |
| Headless Chrome, API + static blocked | Header `Fixture data`; labelled sample network |
| Headless Chrome, 1440 px and 390 px | Page renders; controls, map, journey card, national metrics, scenario and coverage panels present; no page exceptions |

Local checks ran on Node **v22.23.1** with an `EBADENGINE` warning because
`web/package.json` declares Node `>=24`; the build and tests pass anyway. CI uses
Node 24. Run `typecheck` and `build` **sequentially** — running them concurrently
races Nuxt's `.nuxt` cache and can produce a spurious blank build failure.

Mapbox was **not** visually verified: this host has no `NUXT_PUBLIC_MAPBOX_TOKEN`.
The token-free schematic map is the verified path. The Mapbox component typechecks
and builds, and its failure fallback was exercised with a fake token and
WebGL-disabled headless Chrome, but the hosted basemap itself is unverified.

## 2. Prepared network

Built by `scripts/multimodal/build_network.py` from local CSVs only (pandas + stdlib,
no network access). Outputs are byte-identical in two locations:

| Artifact | Size | Contents |
|---|---|---|
| `data/processed/multimodal/network.json` = `web/public/data/multimodal.json` | 1,120,880 B | 200 islands, 191 origins, 117 stops, 20 airports, 102 ferry trips, 62 directed air services, 2 frequency ferry services, 153 access edges, 945 facilities, 48 categories (6 base + 42 intervention) |
| `data/processed/multimodal/islands.geojson` = `web/public/data/islands.geojson` | 280,262 B | 200 island polygons / representative points for the map |
| `data/processed/multimodal/aliases.csv` | 51,740 B | 818 alias rows: 512 exact, 56 fuzzy, 122 manual, 128 unresolved |
| `data/processed/multimodal/report.json` | 153,287 B | Counts, join methods, intervention reconciliation, exclusions, coverage notes, assumptions |
| `web/public/data/heigit-baseline.json` | 10,004 B | 34 national + 43 unit HDX rows, no interpolation |
| `data/processed/multimodal/qgis/` | 7 files | Islands, facilities, ferry/air routes, access edges, QML + README |

### 2.1 SQLite serving layer

`web/scripts/build-db.ts` compiles the three JSON artifacts above into
`web/server/assets/maldives.sqlite` (2,342,912 B, digest
`526d70e0…3cd1f7`). The file is gitignored and rebuilt by `npm run db:build`; `dev` and
`build` run the builder first. The schema (`user_version=1`) keeps normalized entity
columns plus `payload_json`/`feature_json` so the API returns the exact source shape.
The builder validates fixed counts (200/191/117/20/153/166/945/48/200 features/34+43 HDX),
foreign keys, `integrity_check`, and deep payload parity before replacing the file.

`web/server/utils/database.ts` materializes the Nitro server asset into a writable temp
directory, opens it read-only with `node:sqlite` (`DatabaseSync`, `PRAGMA query_only=ON`)
and caches the handle. Routes: `/api/network`, `/api/islands`, `/api/hdx`; `/api/health`
reports schema/counts. A missing, unreadable or wrong-schema DB returns **503
`database_unavailable`**; the page then falls back to the same static JSON and labels
the source `Static fallback`, then to `Fixture data` only if both fail. The SQLite layer
is read-only this iteration: user scenarios are computed in the browser and are not
persisted.

Network composition:

- **Ferries:** 49 routes, 102 recorded trips, 117 scheduled stops. Direction and trip
  identity preserved; one recorded time used as both arrival and departure.
- **Air:** 20 airports, 31 operating airport pairs, 62 directed services. Times are
  generated evenly in 06:00–18:00 at `max(1, round(weekly/7))` per day from the
  estimated weekly frequency table. Not observed schedules.
- **Access:** 138 walk edges, 13 road edges, 2 airport speedboat edges. Road links:
  Addu, Laamu, Sinamalé, Hulhulé–Hulhumalé. No proximity link crosses water.
- **Facilities:** 501 base facilities (189 health, 312 education) plus 444
  intervention facilities = 945 total. Base exclusions: 50 zero-category rows
  (36 preschool, 14 Quran centre) and 120 education rows (104 blank, 12 aggregate,
  4 no-match). Intervention layer: 1,405 rows read, 12 resort/guest-only rows and
  7 unresolved islands excluded, 107 duplicate rows merged, 1,386 used, 1,279 evidence
  items, 42 `service:*` categories. All facility locations are **island-level**.
- **Population:** 447,420 = 191 inhabited islands. Excluded from routing: 1,399
  harbour-area residents and 66,313 people in non-administrative localities
  (republic total 515,132). The four Greater Malé rows are not double-counted.

## 3. National results

All figures are residents who can reach the nearest facility of the category on
the reference day, departing 08:00 unless stated. Denominator 447,420.

| Category | Network | Reachable | Coverage | Within 60 min | Within 120 min | Within 240 min |
|---|---:|---:|---:|---:|---:|---:|
| Hospital (tier 1–3) | land + sea | 322,715 | 72.128% | 298,554 | 310,941 | 312,917 |
| Hospital (tier 1–3) | multimodal | 327,354 | 73.165% | 298,554 | 310,941 | 316,712 |
| Hospital (tier 1–3), 06:00 | land + sea | 373,581 | 83.5% | 297,008 | 308,640 | 368,019 |
| Regional/tertiary hospital | land + sea | 292,930 | 65.5% | — | — | — |
| Regional/tertiary hospital | multimodal | 313,675 | 70.1% | — | — | — |
| Education: grades 11–12 | land + sea | 363,250 | 81.188% | 325,257 | 330,931 | 331,789 |
| Education: grades 11–12 | multimodal | 366,048 | 81.813% | 325,257 | 330,931 | 334,587 |

### 3.1 Network selection results (08:00, hospital tier 1–3)

The same prepared network, with user-selectable transport scope. `Land only` is the
closest analogue to the HDX/HeiGIT benchmark; `Land + sea` is the verified-timetable
baseline without estimated air.

| Network selection | Reachable | Coverage | Within 60 min | Within 120 min | Within 240 min | Verified / estimated |
|---|---:|---:|---:|---:|---:|---:|
| Multimodal (land+sea+air) | 327,354 | 73.165% | 298,554 | 310,941 | 316,712 | 320,799 / 6,555 |
| Land + sea | 322,715 | 72.128% | 298,554 | 310,941 | 312,917 | 322,715 / 0 |
| Land only | 297,008 | 66.382% | 297,008 | 297,008 | 297,008 | 297,008 / 0 |
| Sea only (air off) | 284,991 | 63.697% | 284,991 | 284,991 | 284,991 | 284,991 / 0 |

Disabling ferry route `Z2R18` (route 259) removes only its 572 residents from the
multimodal 08:00 hospital figure: 327,354 → 326,782, and the Maalhos pilot journey
becomes `not_reachable`. This is a user network selection, surfaced as
`not_selected`, not a claim that the ferry does not exist.

### 3.2 Intervention coverage

The intervention layer is built from the diagnostics (396 rows), specialist (787) and
dental (222) evidence tables. Selecting `service:dialysis` resolves to 33 facility
claims on 25 islands; from Maalhos, 1 of 33 is reachable on the reference day
(Eydhafushi, 7 h 37 min), while the Malé claims are not reachable. The panel shows
operator type, confidence, source date and evidence text. These are **claims of
service**, not confirmation that the service is open, staffed or bookable; resorts are
excluded.

### 3.3 HDX/HeiGIT land-only comparison

`web/public/data/heigit-baseline.json` contains the published HDX/HeiGIT values without
interpolation: 34 national rows (education 5–50 km; hospitals and primary care
10–120 min) and 43 unit rows. National 5 km/60 min shares are education **46.92%**,
hospitals **45.24%**, primary healthcare **38.51%**. The benchmark is labelled
land/car-only, uses WorldPop rather than the Census 2022 origin universe, omits units
with no coverage, and is never merged into the multimodal denominators. 22 unit rows
carry no distance value and are shown as time-threshold units.

### 3.4 QGIS export

`scripts/multimodal/export_qgis.py` writes `data/processed/multimodal/qgis/` and the
browser copy `web/public/data/qgis/`: islands, 945 facilities, 102 ferry routes,
31 air pairs, 153 access edges, `access_style.qml` and a README. The web footer links
`/data/qgis/index.html`. Mapbox Studio is a publication path only; the app does not
depend on QGIS or Mapbox at runtime. The QGIS layers were not opened in a desktop QGIS
session on this host; their GeoJSON is generated deterministically from the same
network and validated by the pipeline tests.

Two results are deliberate, not bugs:

- **Departure time dominates.** More than a quarter of the ferry trips (28 of 102)
  have already left by 08:00; 06:00 reaches 83.5% of residents for hospitals, 08:00
  only 72.1%. This is timetable honesty, and the UI exposes the departure time.
- **Air adds a modest, labelled amount.** At 08:00 it adds 4,639 residents relative to
  land + sea (6,555 with an estimated air leg, 320,799 verified-only). Air and
  sea-frequency services are selectable modes, and estimated legs stay labelled.

Origin-access coverage: **124 of 191 origins** (383,671 residents) have an incident
access edge or frequency service; **67 origins** (63,749 residents) have none in the
reference-day network. The router's `no_origin_access` status for a category is
slightly lower where an origin already hosts a facility (that origin gets a 0-minute
reachable journey instead). This is a coverage statement, **not proof that transport
is absent**.

## 4. Manual pilot table

Pilot corridor: Baa Atoll, route `Z2R18` (`ferry:259:1`),
Dharavandhoo (MV007006) → Maalhos (MV007007) → Eydhafushi (MV007008), departing
15:05. Timetable source: `data/team-kandu/rtl_trips.csv`.

| Acceptance check | Expected | Actual | Source |
|---|---|---|---|
| Direct journey: Dharavandhoo 14:05 → Eydhafushi | Ferry 15:05→15:30, plus 7 min final access = **15:37** (92 min elapsed) | **15:37**, 92 min, wait 53, ride 25, access 12, transfer 2, 3 legs, 1 ferry, 0 transfers, verified | Router CLI / `planJourney` on prepared network |
| Same-vehicle intermediate stop: Maalhos 08:00 → Eydhafushi | 1 ferry leg, no new boarding buffer at Maalhos; arrive 15:37 | **1 ferry leg**, 0 transfers, arrival 15:37, wait 430, ride 15, access 10 | Router CLI on prepared network |
| Missed departure boundary: Dharavandhoo 14:43 / 14:44 | 14:43 catches 15:05 ferry; 14:44 misses it | **14:43 reachable** (wait 15); **14:44 `not_reachable`** | Router CLI on prepared network |
| Reverse direction and last departure (fixture boundary) | Maalhos 958 boards, arrives Dharavandhoo 994; 959 misses | **958 arrive 994**; **959 `not_reachable`**; ferry dep 975/arr 990 | `web/shared/routing/router.test.ts` fixture |
| Next day: Dharavandhoo 16:40 | Repeat the same timetable once, 24 h later: ferry 2345→2370, plus 7 min access = **2377**, day 1 | **2377**, dayOffset 1, elapsed 1377, wait 1338, ride 25, access 12 | Router CLI on prepared network |
| Air toggle: Dharavandhoo 07:00 → nearest regional/tertiary hospital | Air-off: no itinerary. Air-on: estimated air + ferry itinerary, labelled estimated | Air-off **`not_reachable`**; air-on **Ugoofaaru 593** (173 min), 5 legs, 2 transit, 1 transfer, estimated; air leg DRV→IFU + ferry 250 | Router CLI on prepared network + `domestic_routes.csv` |
| Scenario end-to-end: add Z2R18 at 14:20, request 13:20 | Baseline 15:37 (137 min); scenario 14:52 (92 min); 45 min gain | Baseline **937/137**; scenario **892/92**; service `ferry:259:1:added:860` | `applyScenario` + `planJourney` |
| Scenario national delta: 08:00 hospital, add Z2R18 at 08:15 | Newly reachable population within 60 min, baseline vs scenario | +572 within 60 (298,554→299,126); +572 within 120; +572 within 240; only Maalhos changes (arrival 937→527) | `computeAccessibility` baseline/scenario |

The fixture values (reverse/last departure) exist to pin the router's boundary
semantics; they are not claims about the real Baa timetable. The real-network
checks use the prepared artifacts and the recorded RTL snapshot.

## 5. What was deliberately not validated / not built

- **No service calendars.** All 102 RTL trips are assumed to run on the reference
  day. Real weekday/Friday exceptions are not modelled; Zone 3 and Kaafu are absent
  from the local RTL snapshot, so Malé is reachable only via air or the bundled
  Malé–Vilimalé frequency ferry model.
- **Air is estimated.** Weekly frequency is converted to generated departure times;
  no observed domestic schedule, aircraft capacity or booking availability is modelled.
- **Facilities are island-level.** No building coordinates, opening hours, clinical
  services, bed capacity or enrolment. Results are *physical access to a listed
  facility's island*, not confirmed service availability.
- **No fares, demand or capacity.** Generalized cost, affordability, 2SFCA and
  observed passenger demand are out of scope; MTCC passenger counts are synthetic
  and were not used as demand.
- **Seaplanes, charters, emergency/sea-ambulance services** are excluded from the
  resident baseline. The Thilamalé bridge (target 2027) is not in the 2026 baseline.
- **Mapbox basemap** is unverified without a token; the schematic map is the verified
  fallback.
- **Network filters are user scenarios.** Excluding a mode or route is not a statement
  that the infrastructure is absent; the UI and metrics use a separate `not_selected`
  state.
- **Intervention claims are not operating capacity.** They are evidence records from
  diagnostics/specialist/dental tables, with confidence and source dates; no opening
  hours, staffing or booking availability are modelled.
- **HDX is a separate benchmark.** Its WorldPop denominator, land-only method and
  omitted units mean it should not be read as validation of the multimodal numbers.
- **QGIS layers were not visually opened in QGIS here.** The export is deterministic
  and tested; the web map remains the verified rendering path.
- **67 origins have no access** in the prepared network. This is reported as missing
  coverage, never as zero travel demand.

## 5a. Update, 24 October evening: gap-filling sea layers, fares, island access report

`scripts/multimodal/augment_network.py` (run after `build_network.py`) adds two sea layers:

- **MTCC 2023 timetable**: 30 trips (21 run on Saturdays; each carries its published running days, none on Friday), 46 stops, only in the atolls with no RTL stop
  in the snapshot (AA, ADh, K, V, M, Lh). Source: the MTCC all-atolls timetable PDF
  (16 Jul 2023), recovered from the Wayback Machine; `research/15_ferry_timetable_gaps.md`.
  One island did not match (Felivaru, Lh).
- **Observed boat links**: 154 regular island-to-island links from FollowMe GPS (Aug 2025)
  that touch an island the RTL network could not reach, as estimated-frequency `sea`
  services under route id `observed-boats` (switchable). These are movements of any
  tracked boat, not a public timetable; departures are spread evenly over the observed
  hours, so this layer is **optimistic**. `research/14_followme_observed_links.md`.

Results, 08:00, hospital tier 1–3 (denominator 447,420):

| Network | Reachable | Atoll residents: hospital on island / by travel | No transport data |
|---|---:|---|---:|
| Before (RTL + estimated air) | 327,354 (73.2%) | 31.8% / 15.6% | 67 islands, 63,749 |
| After, multimodal | 363,648 (81.3%) | 31.8% / 32.9% | 6 islands, 4,335 |
| After, no air | 359,009 (80.2%) | 31.8% / 30.9% | 6 islands, 4,335 |

Regional/tertiary hospital, 08:00: 78.9% multimodal, 72.8% without air (atolls: 60.1% / 48.6%).
Grade 11–12, 08:00: 89.7% (atolls 80.5%). Hospital at 06:00: 95.6%, which shows the
optimism of the evenly spread observed-boat departures; quote 08:00 figures, and the
"before" row as the timetable-only lower bound.

**Fares** (`scripts/multimodal/build_fares.py` → `web/public/data/fares.json`): RTL ferry
fare = 33.8 + 1.79 × great-circle km (fit to the official gazette step tariff, n = 1,837,
r² 0.87); Maldivian domestic resident fares per airport pair (36 pairs, regular fare,
estimated where only promotional fares were found), distance model otherwise; Greater Malé
taxi tariff fit for road links; Malé–Vilimalé ferry MVR 3. Observed-boat legs are priced at
the RTL tariff (estimated). Scheduled speedboats have no resident tariff and stay unpriced.
Sources: `research/12_air_fares.md`, `research/13_sea_land_fares.md`.

**Island access report** (`web/shared/routing/nearby.ts`, panel "What can … reach?"): for a
clicked island, the 3 nearest reachable islands per service with door-to-door time, one-way
and round-trip resident fare, and whether the trip home works the same day after a 2-hour
appointment; otherwise a night away (default MVR 950: MVR 700 lodging + 250 meals,
`data/external/economics/value_of_time.json`) is added. Unknown fares are shown as "+".
CLI: `node --experimental-strip-types web/scripts/nearby-demo.ts Thuraakunu 06:00`.

**External validation** (`research/16_external_validation.md`): modelled access tracks
Aasandha spend per person (ρ = −0.60, p = 0.01, n = 17 atolls) and the share of 16–19 year
olds in education where coverage is good (ρ = −0.74, p = 0.004, n = 13); it does not
significantly predict emergency evacuations (ρ = +0.28, p = 0.25). Exploratory, small n.
Ferry durations: observed FollowMe trips are a median 0.65× the RTL timetable time
(speedboats included), with rank correlation 0.80.

Checks after this update: router tests 48/48 (38 existing + 10 for nearest destinations,
island-to-island, fares and same-day return), `check:routing` OK, `typecheck` OK, `build`
OK, pipeline tests OK (17 skipped without local source CSVs), tools tests 7/7.

## 6. Reproduction

```bash
# from repository root
python3 scripts/multimodal/build_network.py
python3 scripts/multimodal/augment_network.py   # MTCC 2023 + observed boat links
python3 scripts/multimodal/build_fares.py
python3 scripts/multimodal/build_hdx_baseline.py
python3 scripts/multimodal/export_qgis.py
python3 -m unittest discover -s scripts/multimodal/tests -v
python3 -m unittest discover -s tools/tests -v

cd web
npm run test:routing
npm run check:routing
npm run typecheck
npm run build
PORT=3000 node .output/server/index.mjs
```

The pipeline test suite skips source-dependent tests when the local source CSVs
(`data/team-kandu/`, `data/external/`) are absent, but the committed prepared
artifacts are sufficient to run the web app and the routing CLI.

## SQLite v2: analysis tables

`web/server/assets/maldives.sqlite` is now schema `user_version = 2`. On top of the v1 network tables it holds curated analysis tables compiled by `web/scripts/build-db.ts` from `web/public/data/extras/*.json`, which `python scripts/multimodal/build_extras.py` writes from the local research datasets (`data/` is gitignored, so the extras JSON is the committed copy; about 2.7 MB in total). The extras directory is optional: if it is missing the tables are created empty and the build logs a skip line. Each file's `meta.rowCount` is checked against its records and against the database by `db:build`, `db:check` and `test:db`.

| Table | Rows | Source |
| --- | ---: | --- |
| `fares_air` | 36 | `web/public/data/fares.json`, `data/external/fares/air_fares.csv` |
| `fare_models` | 3 | `data/external/fares/sea_land_fares_model.json` |
| `island_profile` | 200 | `multimodal.json` + `island_education_supply.csv` + `health_atoll_summary.csv` (atoll code join; 179 islands have an education row, unmatched rows listed in the file's `meta.notes`) |
| `health_facilities` | 197 | `data/external/health/_derived/public_health_facility_master.csv` (181 matched to an island id; the rest are Male' / Greater Male region or blank rows) |
| `economics` | 109 | `data/external/economics/value_of_time.json`, `key_figures.csv` |
| `observed_sea_links` | 481 | `data/processed/followme/observed_sea_links.csv` (core columns) |
| `validation_atoll` | 42 | `data/processed/validation/atoll_access_vs_outcomes.csv` (21 atolls x estimated_air 0/1) |
| `island_access` | 13,752 | `web/scripts/export-accessibility.ts`: 191 origins x 12 categories x departures 06:00/08:00/14:00 x estimated_air 0/1, plus best-of-day `best_elapsed_minutes` |
| `extras_meta` | 8 | per-table `meta` blocks |

Endpoints (read-only, `503 database_unavailable` when the database is missing): `/api/fares`, `/api/islands/[id]/profile`, `/api/access?category=&departure=` (departure 360, 480 or 840; optional `estimatedAir`; bad input is a 400), `/api/economics`, `/api/validation`, `/api/sea-links` (optional `island`). `/api/health` reports the extras row counts.
