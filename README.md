# Maldives Datathon 2026: Multi-Modal Accessibility

**Theme:** *Mapping Mobility through Data: Innovating Transport Insights for a Connected Maldives* (Maldives Bureau of Statistics, 24 Oct 2026)

How long, and how much, does it take people on each inhabited island to reach a school, a university or a hospital when you combine **land, sea and air** travel?

Global accessibility datasets such as HeiGIT/HDX route by car only. For the Maldives they report that about 47% of people can reach a school, and that extending the drive from 10 to 120 minutes adds less than one percentage point, because a car cannot leave its island. This project builds a sea- and air-aware network so the real picture is visible.

See [`MULTI_MODAL_ACCESSIBILITY_PLAN.md`](MULTI_MODAL_ACCESSIBILITY_PLAN.md) for the full plan.

A working prototype implements the first slice of that plan: a reference-day ferry
timetable, an estimated domestic-air layer, island access links, 48 destination
categories (health, education and 42 intervention services), a timetable-aware router,
selectable land/sea/air modes and specific routes, intervention coverage, an
add-facility / add-route / add-trip / cancel / delay simulator, an HDX land-only
benchmark panel, and a QGIS export. See [`VALIDATION.md`](VALIDATION.md) for checks,
numbers and limitations, and [`MULTIMODAL_IMPLEMENTATION.md`](MULTIMODAL_IMPLEMENTATION.md)
for the build contract.

---

## Approach

1. **Nodes:** 191 inhabited islands (Census 2022 population) plus airports, harbours and facility islands.
2. **Edges:**
   - **Sea:** RTL fast-ferry snapshot (149 recorded stops, of which 117 have a scheduled trip; 102 trips), with travel speeds measured from FollowMe boat GPS (about 110k trips; speedboats around 43 km/h, slow boats around 13 km/h).
   - **Air:** 20 operating airports; 31 operating airport pairs from the 40-row estimated domestic-route table, with block times and weekly frequencies.
   - **Land:** prototype access is walking at 4.5 km/h with a 1.25 detour factor, local transport at 25 km/h beyond 1.5 km, and explicit Addu/Laamu/Sinamalé road links at 40 km/h. Avas ride data informs future urban calibration.
   - **Transfers:** waiting comes from the next recorded departure, not half the interval, because these services are infrequent; boarding/check-in buffers are explicit (ferry 15 min, domestic air 45 min, 60 min at Velana).
3. **Destinations:** schools by highest grade taught (only 44 of 184 atoll islands teach grades 11–12), higher-education campuses, health facilities by level of care, and 42 diagnostic/specialist/dental intervention categories. The prototype serves 945 facilities (501 base facilities + 444 facilities with intervention claims) across 48 categories.
4. **Outputs implemented:** travel time to the nearest listed facility or intervention provider for each island, population within 60/120/240 minutes, reachable/unreachable/no-access/not-selected states, mode/confidence breakdowns, selectable land/sea/air modes and routes, service/facility simulator deltas, and an HDX land-only comparison. Cost, 2SFCA capacity weighting and demand modelling remain planned.
5. **Economics (planned):** generalized cost (fare + value of time + overnight stays), affordability as a share of income, and scenario testing for new routes or clinics.

## Working prototype

The prototype is served from prepared static artifacts, so no database or live
operator feed is needed. It runs on Node 24+ locally (the package declares Node 24+
and CI uses Node 24; Node 22 also runs with an engine warning).

```bash
cd web
npm install
npm run dev          # http://127.0.0.1:3000
```

No Mapbox token is required: without `NUXT_PUBLIC_MAPBOX_TOKEN` the app renders a
functional schematic map from `islands.geojson`. With a token it uses the Mapbox
polygon choropleth and the same data. Prepared artifacts:

- `web/public/data/multimodal.json` — 200 islands, 191 origins, 117 ferry stops,
  102 ferry trips, 20 airports, 62 estimated air services, 153 access edges,
  945 facilities, 48 categories; 1,120,880 B.
- `web/public/data/islands.geojson` — island polygons for the map.
- `web/public/data/heigit-baseline.json` — HDX/HeiGIT land-only benchmark (34 national
  and 43 unit rows), shown separately and never merged.
- `web/public/data/qgis/` — QGIS GeoJSON + QML export and landing page.
- `data/processed/multimodal/report.json` — join counts, exclusions, intervention
  reconciliation, coverage notes and every assumption.

Headline result at 08:00 on the reference day, hospital tier 1–3, all modelled modes:
**327,354 of 447,420 residents (73.2%)** can reach the nearest listed hospital;
land + sea without air is **322,715 (72.1%)**, and land-only is **297,008 (66.4%)**.
At 06:00 the land+sea figure is 83.5%, which shows how strongly the result depends on
the departure time. These are physical access to a listed facility's island, not
confirmed service availability. See [`VALIDATION.md`](VALIDATION.md).

## Repository layout

| Path | Contents |
|---|---|
| `research/` | Research notes (see index below) |
| `scripts/` | Python scripts for profiling, extraction and network building. Run with `.venv/Scripts/python.exe -I scripts/<name>.py <args>` |
| `data/external/` | Public-source layers: islands, census, OSM, air network, health, education, fares. See [`data/external/README.md`](data/external/README.md) |
| `data/external/_derived/mdv_islands_master.gpkg` | **Start here:** 1,556 islands with island/atoll codes, status (inhabited, resort, airport) and Census 2022 population |
| `data/processed/` | Derived tables (HeiGIT extracts, FollowMe trips) |
| `data/MACL`, `MTCC`, `Avas_Ride`, `FollowMe` | Official datathon datasets ([MBS release v1.0](https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases/tag/v1.0)). The large FollowMe CSVs are not versioned; download them from the release |
| `data/team-kandu/` | Team-shared RTL ferry and bus timetables and yearbook tables (from the MBS datasets repo) |
| `data/hdx-heigit-access/` | HeiGIT car-only accessibility indicators from [HDX](https://data.humdata.org/dataset/maldives-accessibility-indicators) (CC BY-SA) |
| `web/` | Working accessibility prototype (Nuxt + Vue + TypeScript + Mapbox GL JS) with a token-free schematic fallback |

## Research index

| # | Note | Topic |
|---|---|---|
| 01 | [datathon_context](research/01_datathon_context.md) | Rules, judging (2025 rubric: policy relevance, technical execution, presentation, innovation, replicability; 20% each), data providers |
| 02 | [data_profile_hdx_kandu](research/02_data_profile_hdx_kandu.md) | HeiGIT and Team Kandu profiling; the RTL timetable is about 80% of the way to a standard GTFS feed |
| 03 | [transport_network_and_methods](research/03_transport_network_and_methods.md) | Mode speeds, waiting and transfer times, graph design |
| 03 | [public_sources_verification](research/03_public_sources_verification.md) | Source verification |
| 04 | [data_profile_mbs_official](research/04_data_profile_mbs_official.md) | MACL, MTCC, Avas, FollowMe profiling and how each feeds the network |
| 04 | [build_feasibility](research/04_build_feasibility.md) | Build feasibility |
| 05 | [healthcare_data](research/05_healthcare_data.md) | Facility levels of care, beds, staff, morbidity, Aasandha, evacuations |
| 06 | [education_data](research/06_education_data.md) | Schools by grade range, higher-education campuses, migration for education |
| 07 | [air_network](research/07_air_network.md) | Airports, domestic routes, seaplanes, airport catchments |
| 08 | [heigit_accessibility_indicators](research/08_heigit_accessibility_indicators.md) | HDX car-only baseline: method, extracted tables, critique |
| 09a–c | dental / lab & diagnostic / specialist services | Health services by island (in progress) |
| 10–13 | spending / economic models / air fares / sea & land fares | Economic layer (in progress) |

## Key findings so far

- **Car-only models miss most of the country.** HeiGIT leaves out 11 of 21 atolls entirely, and its figures stay flat at about 46–48% coverage.
- **The Grade 10 cliff.** Only 44 of 184 atoll islands teach grades 11–12, and 48% of atoll grade 9–10 students live on islands without them. Education accounts for 43–53% of migration to Malé from the key atolls.
- **Health access depends on transfers.** In 2024 Aasandha recorded 4,426 emergency evacuations and 15,535 patients sent abroad. Inpatient beds per 1,000 people range from 1.6 to 11.0 across atolls (2020).

## Data caveats

- **MTCC passenger figures are randomly generated** (per the dataset's own README sheet). Only its route codes are real.
- **MACL** covers international flights at Velana only, with anonymised codes, so it has no domestic air data.
- **Avas** trip times look like booking-time estimates rather than observed trips.
- **FollowMe** has no vessel type, and contains GPS glitches and duplicate rows.
- **Island names** vary between sources. Always join on atoll code + normalised island name; see `scripts/census_island_join.py`.
- **Reference day, not a calendar.** The prototype treats all 102 recorded RTL trips as operating on 10 October 2026. The local snapshot has no weekday/exception calendar and no Kaafu/Zone 3 ferry stops.
- **Air is an estimate.** Domestic departures are generated from weekly frequency; they are not observed schedules and are never counted as verified.
- **Facility locations are island-level.** Results mean physical access to a listed facility's island, not confirmed opening hours, clinical services or capacity.
- **Missing coverage is not zero access.** 67 of 191 origin islands have no fixed access edge or frequency service in the prepared network. A category-specific result can report a lower no-access count because an origin that already hosts the selected facility returns a zero-minute journey instead of "no access".

## Setup

```bash
python -m venv .venv
.venv/Scripts/pip install pandas geopandas pyogrio polars pyarrow openpyxl pdfplumber pymupdf
.venv/Scripts/python.exe -I scripts/heigit_extract.py data/hdx-heigit-access data/processed/heigit
```

## Sources and licences

Maldives Bureau of Statistics (datathon datasets, Census 2022, Statistical Yearbook) · HeiGIT/HDX (CC BY-SA) · OpenStreetMap contributors (ODbL) · HDX COD-AB · geoBoundaries · WorldPop · OurAirports (public domain) · Ministry of Health · Ministry of Education / Ministry of Higher Education · WHO GHO · World Bank WDI. Per-file sources are listed in `data/external/README.md` and in each research note.

## Prototype documentation and agent tools

The web app implements the reference-day multimodal prototype, not the full
economic/demand model. Read its setup and architecture notes in
[web/README.md](web/README.md); the prepared-data schema and rebuild steps are in
[data/README.md](data/README.md). QGIS remains optional and is not a runtime
dependency.

```bash
cd web
npm install             # or: pnpm install
cp .env.example .env    # optional Mapbox token
npm run dev
```

Read-only agent tools discover local datasets, inspect schemas, return bounded CSV
samples and read research caveats. They can run as a dependency-free Python CLI or
local MCP stdio server; see [tools/README.md](tools/README.md) and
[mcp.example.json](mcp.example.json). Raw data remains local; see
[data/README.md](data/README.md).

```bash
python tools/data_mcp.py --call data_list_datasets
python tools/data_mcp.py --call data_describe_dataset --dataset-id rtl_trips
python -m unittest discover -s tools/tests -v
```

The research still describes future analysis (fares, demand, capacity, 2SFCA).
The prototype's scope, assumptions and verified numbers are recorded in
[VALIDATION.md](VALIDATION.md).

