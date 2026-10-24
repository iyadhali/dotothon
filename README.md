# Maldives Datathon 2026: Multi-Modal Accessibility

**Theme:** *Mapping Mobility through Data: Innovating Transport Insights for a Connected Maldives* (Maldives Bureau of Statistics, 24 Oct 2026)

How long, and how much, does it take people on each inhabited island to reach a school, a university or a hospital when you combine **land, sea and air** travel?

Global accessibility datasets such as HeiGIT/HDX route by car only. For the Maldives they report that about 47% of people can reach a school, and that extending the drive from 10 to 120 minutes adds less than one percentage point, because a car cannot leave its island. This project builds a sea- and air-aware network so the real picture is visible.

See [`MULTI_MODAL_ACCESSIBILITY_PLAN.md`](MULTI_MODAL_ACCESSIBILITY_PLAN.md) for the full plan.

---

## Approach

1. **Nodes:** 191 inhabited islands (Census 2022 population) plus airports, harbours and facility islands.
2. **Edges:**
   - **Sea:** RTL fast-ferry timetable (149 stops, 102 daily trips), with travel speeds measured from FollowMe boat GPS (about 110k trips; speedboats around 43 km/h, slow boats around 13 km/h).
   - **Air:** 20 operating airports and 40 domestic routes, with flight times and weekly frequencies.
   - **Land:** Greater Malé road times (Avas ride data: about 85 s per km + 71 s), plus the Addu and Laamu link roads.
   - **Transfers:** waiting time of half the interval between departures, plus boarding and check-in time.
3. **Destinations:** schools by highest grade taught (only 44 of 184 atoll islands teach grades 11–12), higher-education campuses, and health facilities by level of care and specialty.
4. **Outputs:** travel time and cost to the nearest service for each island, population beyond time thresholds, which travel modes reach which islands, and capacity-weighted access (2SFCA, which scores access against facility capacity).
5. **Economics:** generalized cost (fare + value of time + overnight stays), affordability as a share of income, and scenario testing for new routes or clinics.

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
| `web/` | Interactive map app (Nuxt + Mapbox), in progress |

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

## Setup

```bash
python -m venv .venv
.venv/Scripts/pip install pandas geopandas pyogrio polars pyarrow openpyxl pdfplumber pymupdf
.venv/Scripts/python.exe -I scripts/heigit_extract.py data/hdx-heigit-access data/processed/heigit
```

## Sources and licences

Maldives Bureau of Statistics (datathon datasets, Census 2022, Statistical Yearbook) · HeiGIT/HDX (CC BY-SA) · OpenStreetMap contributors (ODbL) · HDX COD-AB · geoBoundaries · WorldPop · OurAirports (public domain) · Ministry of Health · Ministry of Education / Ministry of Higher Education · WHO GHO · World Bank WDI. Per-file sources are listed in `data/external/README.md` and in each research note.
