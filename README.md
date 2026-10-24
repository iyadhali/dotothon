# Access to upper-secondary education across the Maldives

**Maldives Datathon 2026 · Team A · Sea · Land · Air**

187 inhabited islands, 448,819 residents, and one question: **how long does it take a student on
island A to reach a school that teaches grade 11–12 — and which islands are worst served?**

The unusual part: the travel times are **not** taken from a timetable. They are reconstructed from
a month of anonymised vessel GPS (17.4 M points from 1,328 tracked craft), so the network in the
model is the one boats actually sailed in August 2025, not the one that was published.

**44 islands** teach grade 11–12. **159 islands, 427,538 people** can reach one within two hours;
**28 cannot**, and those 28 hold 6,758 children aged 0–17. **2 islands** have no observed route at
all. Nationally, only **29.9 %** of 16–17-year-olds are enrolled in higher secondary, against
91.9 % in primary.

---

## Run it

```bash
pip install -r requirements.txt
make ingest                  # fingerprint the four datasets, rebuild what changed
cd web && python manage.py runserver 8000
```

**New data is processed automatically.** Drop a file where the old one lived
(`data/MTCC.xlsx`, `data/MACL/*.csv`, `data/Avas_Ride/*.csv`, or a new
`data/FollowMe_<month>/` folder) and the pipeline rebuilds only the stages that depend on it:

```bash
make watch                   # poll every 10 s, ingest on change
make ingest                  # or one incremental pass
python scripts/ingest.py --dry-run   # show what would rebuild
```

Each run writes `data/derived/source_manifest.md` — what was ingested, when, how big, and how many
rows came out — and the web app picks up rebuilt tables without a restart. Full detail:
[docs/pipeline.md](docs/pipeline.md).

Open <http://127.0.0.1:8000>. No database, no migrations, no API keys, no network calls — the
HTMX and Leaflet bundles are vendored, so it runs offline on venue wifi.

### What you can do in it

The home page **is** the map: 187 inhabited islands, sized by population and coloured by observed
travel time to the nearest grade 11–12 school. Everything else floats over it.

| Interaction | What it does |
|---|---|
| **Hover** an island | name, atoll, residents and travel time in a tooltip |
| **Click** an island | profile card (population, children, provision, nearest school and campus, observed crossings) |
| **Legend chips** | filter the map to one travel-time band; click again to clear |
| **Zoom in** | the 21 atoll outlines and their names appear, then island names, then real coastlines |
| **Atoll dropdown** | fly to that atoll's bounding box; `?lat=…&lon=…&z=…` opens a shared view |
| **Search / list** | live filter over 187 islands; hover a row to light up its island, Enter to open the top hit |
| **Island → island** | pick two islands: the best journey within two sailings, drawn on the map and split into sailing time and connection waiting |
| **Island → service** | pick one island and a category (education, health): every service type it can reach, who provides it, how long it takes, and the journeys drawn together |
| **Reset** (or `Esc`) | clear filters, route and selection |
| | |
| **Decision tables** | below the map: worst-served ranking, and the 28 islands beyond two hours with the link that would fix each |
| **Provenance** | the footer prints when the data was last built and from how much of it |
| **Colour by** | switch the whole map between education (grade 11–12, university campus, grade 7–10) and health (health centre, hospital) — same network, any service category |
| **Travel time to the nearest** | hours to the nearest provider of *each* service type, and the island that provides it |

### Services, not just schools

The model was built for education, but the network underneath is general. `data/services.csv` is a
register of 569 facilities — 409 education (primary, lower and higher secondary, four campuses) and
160 health (155 health centres, 5 hospitals) — each attached to an island, so accessibility is one
Dijkstra over one graph per service type:

| Service | Islands with one | Islands within 2 h | People within 2 h | Median hours |
|---|---|---|---|---|
| Primary school | 182 | 187 | 448,819 | 0.0 |
| Grades 7–10 | 180 | 187 | 448,819 | 0.0 |
| **Grades 11–12** | 43 | **156** | 422,602 | 0.56 |
| University campus | 4 | 50 | 305,772 | 3.34 |
| Health centre | 155 | 186 | 439,642 | 0.0 |
| **Hospital** | 4 | **35** | 274,015 | 4.56 |

The contrast is the argument: **primary care reaches almost every island (186 of 187 within two
hours), secondary care does not — only 35 islands, 274,015 people and 51,601 children can reach a
hospital within two hours, at a median of 4.6 hours.** The same network that shows a school gap
shows a sharper hospital gap, and the register is editable, so the answer stays honest when a new
facility opens.

## How it is built

```
FollowMe GPS (17.4M points, Aug 2025) ─┐
OCHA island boundaries (1,556 units) ──┼─► scripts/build_island_spine.py ──► island_spine.csv
MBS Census 2022 (population) ──────────┘

FollowMe GPS ──► scripts/build_sea_network.py ──► sea_edges.csv  (5,789 directed crossings)

MoE School Statistics 2024 ──► scripts/build_school_provision.py ──► island_school_provision.csv

                      └──► scripts/build_reachability.py ──► island_access.csv + island_pairs.csv
                                                             │
                                            web/build_web_data.py ──► Django + HTMX app
```

Each stage is a standalone script that reads CSVs from `data/` and writes CSVs to `data/derived/`.
Re-running any stage is safe; nothing is mutated in place.

```bash
python scripts/build_island_spine.py        # Census 2022 ⋈ OCHA boundaries  → 187 islands
python scripts/build_sea_network.py         # 31 GPS files → stays → crossings   (~4 min)
python scripts/fetch_schools.py             # MoE school register (validation only)
python scripts/build_school_provision.py    # MoE PDF → students per grade per island
python scripts/build_reachability.py        # graph → hours to the nearest school
```

Only `build_sea_network.py` is slow (it reads 1.8 GB of GPS). Everything else finishes in seconds.

## The model, in one paragraph

A **stay** is five or more consecutive GPS polls at or below 2 knots; two consecutive stays of one
device make a **trip**, whose duration is observed rather than computed. Stays are snapped to the
nearest OCHA island centroid within 6 km. Crossings whose implied speed falls outside 0.5–55 knots
are dropped as GPS errors (1,303 of them). Islands joined by road — Addu's six census islands, and
Malé's bridge to Hulhumalé — are connected explicitly at 30 km/h, because boat data cannot see a
causeway. Journeys cost the observed median crossing time per leg plus **1 hour** for each
connection, and are capped at **two sailings**: a third sailing is reported as *not accessible*
rather than given an implausible number.


### A platform, not a dashboard

The four datasets are not read by the app. They are read by a pipeline that fingerprints every
source, rebuilds only the stale stages, and writes one SQLite file:

```
sources ──▶ ingest (sha256 fingerprint per group) ──▶ derived tables ──▶ data/platform.sqlite ──▶ app
```

| Piece | Where |
|---|---|
| Source inventory + fingerprints | `data/derived/.ingest.json`, `source_manifest.json` |
| Stage plan (dry-run prints it) | `scripts/ingest.py`, `make ingest` |
| Watch for new drops | `scripts/watch_data.py`, `make watch` (logs to `data/derived/ingest.log`) |
| Schema + views the app queries | `db/schema.sql` |
| Loader | `scripts/build_database.py` → `data/platform.sqlite` |
| Placement model | `scripts/build_simulator.py` (the placement model) → `placement.csv` |

Drop a new `MACL/*.csv` or a new `FollowMe_*/` month, run `make ingest`, and the map, the services
register and the simulator all move together. The app opens the database read-only and reloads
itself when the file changes, so nothing needs restarting.

**Placement ranking** is computed by `scripts/build_simulator.py` and stored in the `placement` table; it is the "so what" layer behind the map's decision tables.

## Data sources

| Source | Used for | Link |
|---|---|---|
| **FollowMe** anonymised vessel GPS, Aug 2025 | observed sea network | supplied at the event |
| **MTCC** bus and ferry ridership, 2023–2025 | context (labelled "sample values" by the supplier) | supplied at the event |
| **MACL** airport traffic, 2012–2026 | context on gateway demand | supplied at the event |
| **Avas Ride** trips, Aug–Sep 2026 | Greater Malé last-mile context | supplied at the event |
| **MBS Census 2022** island and atoll indicator sheets | population, children 0–17, area | [statisticsmaldives.gov.mv](https://statisticsmaldives.gov.mv/census-2022-island-and-atoll-level-indicator-sheets/) |
| **Ministry of Education, School Statistics 2024** | enrolment by grade, per island | [moe.gov.mv](https://education.gov.mv/storage/files/statistics/1782980847582-2024%20School%20Statistics.pdf) |
| **OCHA / HDX Maldives administrative boundaries** | island polygons and centroids | [data.humdata.org](https://data.humdata.org/dataset/a968d227-24c9-49ea-bbce-cee04ee94819) |
| **MNU** campus locations | 5 higher-education sites | [mnu.edu.mv](https://mnu.edu.mv/about-us/) |

Licences: Census and MoE material © Government of Maldives; OCHA boundaries open with attribution
to OCHA FIS; OpenStreetMap data (not used in the served map) is ODbL.

## Limits we state on purpose

- **One month of GPS.** August 2025 only; seasonal routes and monsoon cancellations are invisible.
- **Absence is not proof.** "No observed route" means no tracked vessel made the crossing in that
  month — not that no service exists. Nine inhabited islands have no observed sea traffic, of
  which eight are the Addu/Fuvahmulah road-connected islands, which the model repairs with land
  links.
- **1,776 devices, not the whole fleet.** The GPS covers 1,328 craft making crossings; small
  dhoni traffic is certainly under-sampled.
- **Two sailings maximum.** Deliberate: it stops a four-hop journey being reported as "accessible".
- **No fares.** The provided data has none, so affordability is not modelled here.
- **No air links yet.** 14 domestic airports are the next step; today three capital routes
  (Addu, Fuvahmulah, Thinadhoo) come back as unreachable by sea, which is exactly the gap air
  would fill.

## How this maps to the judging criteria

Nothing in this repo exists unless it moves a criterion — the audit trail is
**[docs/criteria-map.md](docs/criteria-map.md)**.

| Criterion | Weight | Where it is earned |
|---|---|---|
| Technical execution | 20 % | the demo runs offline; every number re-derivable; `make check` asserts 13 published figures; limits stated |
| Impact | 15 % | **[docs/findings.md](docs/findings.md)** — a named user, an explicit decision, 28 islands ranked by children |
| Scalability | 15 % | `make refresh GPS=<new month>`; one command per stage; no database to migrate |
| Data Utilization | 15 % | organiser data + official public data only; school totals reconcile to 5,105; island areas agree with OCHA at r = 0.9996 |
| Innovation | 10 % | the method — an observed network reconstructed from GPS, not a published timetable |
| Relevance | 10 % | island-to-island access to post-16 education, 187 islands |
| Clarity | 5 % | one question, one map, one number |
| Teamwork | 10 % | five separable pipeline stages for five people |

## Repository layout

```
data/                     provided datasets + external/ (open data, downloaded) + derived/ (pipeline output)
scripts/                  the pipeline: spine → sea network → school provision → reachability → query
web/                      Django + HTMX explorer (config/, access/, templates/, static/)
REVIEW.md                 the review: challenge card, dataset teardown, risks
docs/judging-criteria.md  the actual rubric, our self-assessment and ranked actions
docs/criteria-map.md      which artifact earns which criterion, and what we refuse to build
docs/findings.md          the decision brief: who benefits, what they could do differently
docs/pipeline.md          automatic ingestion: fingerprints, stages, manifest, what rebuilds when
Makefile                  make / make refresh GPS=<dir> / make check / make run
```

## AI assistance

This project used an AI coding assistant (DeepSeek Harness) to profile the provided datasets,
write the pipeline and the web app, and draft this README. Every number in the app comes from a
script in `scripts/` that can be re-run; the two cross-checks we rely on are stated in the code —
the school table reconciles to the published national total of 5,105 students in grades 11–12,
and island areas reconcile to OCHA boundaries at r = 0.9996. All AI-assisted code was read,
run, and verified by the team.
