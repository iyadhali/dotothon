# Access to upper-secondary education across the Maldives

**Maldives Datathon 2026 · A Team · Sea · education · health**

187 inhabited islands, 448,819 residents, and one question: **how long does it take a student on
island A to reach a school that teaches grade 11–12 — and which islands are worst served?**

The unusual part: the travel times are **not** taken from a timetable. They are reconstructed from
a month of anonymised vessel GPS (17.4 M points from 1,328 tracked devices), so the network in the
model is the one boats actually sailed in August 2025, not the one that was published.

**44 islands** teach grade 11–12. **154 islands, 416,235 people** can reach one within two hours;
**33 fall outside that** — 26 have an observed route that takes longer, and **7 have no observed
route at all**. Those 33 hold **32,584 residents and 9,591 children** aged 0–17. Nationally, only
**29.9 %** of 16–17-year-olds are enrolled in higher secondary, against 91.9 % in primary.

---

## Run it

```bash
pip install -r requirements.txt
make ingest                  # fingerprint every source, rebuild what changed
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

Open <http://127.0.0.1:8000>. One SQLite file, no database server, no migrations, no API keys, no
network calls — the HTMX and Leaflet bundles are vendored, so it runs offline on venue wifi.

### What you can do in it

**Two pages, one network.** The **map** answers what an island can reach. The **service simulator**
(`/simulator/`) answers where the next school, health centre or crossing would help the most
people.

| Interaction | What it does |
|---|---|
| **Click an island** (or the atoll picker) | the island's services load: every service type, who provides it, how many hours and how many sailings |
| **All · Education · Health** | filter the service list; the map redraws the journeys to those providers |
| **Hour meters** | each row's bar is scaled to 8 hours, coloured by the same band as the map |
| **Three numbers on top** | how many service types are on the island, how many are within two hours, and which one is worst |
| **Connect to another island** | pick a second island and the journey from the selected one is drawn on the map with its sailing/waiting split |
| **Colour the map by** | recolour 187 islands by any service type — education or health, same network |
| **Legend chips** | filter the map to one travel-time band |
| **Zoom in** | atoll outlines and names, then island names, then coastlines; circles scale with population |
| **Atoll picker** | dim everything outside that atoll and fly to it; `?lat=…&lon=…&z=…` shares a view |
| **Reset** (or `Esc`) | clear the filters, the journey and the selection |
| **Decision tables** | below the map: the 33 islands beyond two hours, with the link that would fix each sea-only gap |
| **Plan a build** (simulator) | pick a service type and candidate sites; each pick is scored by the residents, islands and children it brings within two hours, and the next pick is scored after it |
| **Where to build connectivity** (simulator) | one new crossing at a time (≤ 60 km, 20 knots plus 0.5 h), ranked by residents newly within two hours or time saved |

Every picker is a searchable combobox: type three letters, arrow, enter.

### Services, not just schools

The model was built for education, but the network underneath is general. `data/services.csv` is
the service register — **572 entries, one per island offering each level or facility**: 412
education (183 primary, 181 lower secondary, 44 higher secondary, four campuses) and 160 health
(155 health centres, 5 hospitals), each attached to an island. Accessibility is one Dijkstra over
one graph per service type:

| Service | Islands with one | Islands within 2 h | People within 2 h | Median hours |
|---|---|---|---|---|
| Primary school | 183 | 185 | 446,239 | 0.0 |
| Grades 7–10 | 181 | 185 | 446,239 | 0.0 |
| **Grades 11–12** | 44 | **154** | 416,235 | 0.56 |
| University campus | 4 | 45 | 294,469 | 3.47 |
| Health centre | 155 | 183 | 422,593 | 0.0 |
| **Hospital** | 4 | **30** | 262,712 | 4.79 |

The contrast is the argument: **primary care reaches almost every island (183 of 187 within two
hours), secondary care does not — only 30 islands, 262,712 people and 48,768 children can reach a
hospital within two hours, at a median of 4.79 hours.** The same network that shows a school gap
shows a sharper hospital gap, and the register is editable, so the answer stays honest when a new
facility opens.

Two register caveats, stated rather than hidden: the seed lists five MNU campuses (Malé,
Kulhudhuffushi, Thinadhoo, Hithadhoo, Gan) and four are placed, because Gan has no separate row in
the 187-island spine; and the five hospitals are the ones named by the seed, because the Ministry
of Health page does not publish the names of all 23.

## How it is built

Each stage is a standalone script that reads files in `data/` and writes CSVs to `data/derived/`.
Re-running any stage is safe; nothing is mutated in place.

1. `build_island_spine.py` — Census 2022 joined to OCHA polygons → `island_spine.csv` (187
   inhabited islands).
2. `build_sea_network.py` — 31 GPS files → stays → trips → `sea_edges.csv` (5,789 directed
   crossings).
3. `build_school_provision.py` — MoE School Statistics 2024 → enrolment by grade and island →
   `island_school_provision.csv`.
4. `seed_services.py` — MoH facility list, MoE directory, MNU campuses, hospital list →
   `services.csv` (572 entries).
5. `build_reachability.py` — spine + sea edges + provision → `island_access.csv`,
   `island_pairs.csv`, `priority_gaps.csv`.
6. `build_service_access.py` — `services.csv` + the graph → `service_access.csv`,
   `service_summary.csv`.
7. `build_simulator.py` — coverage → `placement.csv`.
8. `build_placement.py` — one hypothetical crossing at a time → `travel_time.csv`,
   `link_candidates.csv`.
9. `build_database.py` — every derived CSV → `data/platform.sqlite`; `web/build_web_data.py` adds
   the map points.

### The database is the system of record

`data/platform.sqlite` is what the app reads — no page touches a CSV. The pipeline **reconciles**
the database rather than replacing it:

```
data/derived/*.csv  ──► scripts/build_database.py ──► data/platform.sqlite  ──► Django (read-only)
                              upsert by natural key        + data_change log
```

- every table has a natural key (`island.node_id`, `sea_edge(from_id,to_id)`, `service.service_id`,
  `service_access(node_id,service_type)` …), so a build inserts what is new, updates what moved,
  deletes what disappeared, and **writes nothing when nothing changed**;
- each reconciliation logs one row per touched table into `data_change` (`inserted, updated,
  deleted`), so "who changed what, when" is a query, not a guess;
- `source_file` records every input file ever seen with its sha256, and `data_change` plus
  `meta.built_at` are surfaced in the app footer (`SQLite · rebuilt 24 Oct 15:31 · 1 new file`).

### New data

Drop it in `data/incoming/` and run `make ingest`:

```bash
cp ~/Downloads/new_health_post.csv data/incoming/
make ingest           # fingerprints → absorbs → reconciles → rebuilds the web payloads → checks
```

- files whose name maps to a known source (`services`, `mtcc`, `macl`, `avas`, `followme`,
  `census`, `boundaries`, `moh`, `moe`) are routed to that source and the stage that consumes it
  re-runs;
- anything else is still kept: its rows land in `raw_record` as JSON, one row per record, so a new
  dataset is queryable from the database the moment it arrives, before any stage understands it;
- a re-drop of the same bytes is a no-op (sha256 match), and `python scripts/absorb_incoming.py
  --dry-run` says what would happen without touching anything.

```bash
make absorb           # only the data/incoming pass
python scripts/build_database.py --rebuild   # throw the file away and start clean
```

```bash
python scripts/build_island_spine.py          # Census 2022 ⋈ OCHA boundaries  → 187 islands
python scripts/build_sea_network.py           # 31 GPS files → stays → crossings   (~4 min)
python scripts/fetch_schools.py               # MoE school directory (validation only)
python scripts/build_school_provision.py      # MoE PDF → students per grade per island
python scripts/seed_services.py --if-missing  # MoH + MoE + MNU + hospitals → services.csv
python scripts/build_service_access.py        # register + graph → coverage per service
python scripts/build_reachability.py          # graph → hours to the nearest school
python scripts/build_simulator.py             # coverage → placement.csv
python scripts/build_placement.py             # one new crossing → link_candidates.csv
python scripts/build_database.py              # derived CSVs → data/platform.sqlite
```

Only `build_sea_network.py` is slow (it reads 1.8 GB of GPS). Everything else finishes in seconds.

## The model, in one paragraph

A **stay** is five or more consecutive GPS polls at or below 2 knots; two consecutive stays of one
device make a **trip**, whose duration is observed rather than computed. Stays are snapped to the
nearest OCHA island centroid within 6 km. Crossings whose implied speed falls outside 0.5–55 knots
are dropped as GPS errors (1,303 of them). Every edge is an observed crossing — no road or air link
is invented, so a pair with no boat in the month is reported as *not connected* rather than bridged
on an assumption. Journeys cost the observed median crossing time per leg plus **1 hour** for each
connection, and may use **up to five sailings** (long chains such as Baa → Lhaviyani → Kaafu →
Malé are real itineraries, not errors); a sixth is reported as not connected rather than given an
implausible number.


### A platform, not a dashboard

The source datasets are not read by the app. They are read by a pipeline that fingerprints every
source, rebuilds only the stale stages, and writes one SQLite file:

```
sources ──▶ ingest (sha256 fingerprint per group) ──▶ derived tables ──▶ data/platform.sqlite ──▶ app
```

| Piece | Where |
|---|---|
| Source inventory + fingerprints | `data/derived/.ingest.json`, `source_manifest.json` |
| Stage plan (dry-run prints it) | `scripts/ingest.py`, `make ingest` |
| Watch for new drops | `scripts/watch_data.py`, `make watch` (logs to `data/derived/ingest.log`) |
| Service register (source of truth) | `data/services.csv`, editable in the app |
| Schema + views the app queries | `db/schema.sql` |
| Loader | `scripts/build_database.py` → `data/platform.sqlite` |
| Placement ranking | `scripts/build_simulator.py` → `placement.csv` |
| Build-page candidates | `scripts/build_placement.py` → `travel_time.csv`, `link_candidates.csv` |

Drop a new `MACL/*.csv` or a new `FollowMe_*/` month, run `make ingest`, and the map, the services
register and the simulator all move together. The app opens the database read-only and reloads
itself when the file changes, so nothing needs restarting.

**Two "so what" layers** sit behind the simulator: `placement.csv` ranks where a new facility
covers the most people, islands and children; `link_candidates.csv` scores one hypothetical
crossing at a time (≤ 60 km, 20 knots plus half an hour) by the residents it brings within two
hours and the time it saves.

## Data sources

Twelve sources feed the build. `data/derived/source_manifest.md` records the file count, size,
mtime and group fingerprint of each; `data/platform.sqlite` keeps a `source_file` row for every
input ever ingested.

| Source | What we take | Produces | Access |
|---|---|---|---|
| **FollowMe** anonymised vessel GPS, Aug 2025 — 31 daily CSVs, 17.4 M points, 1,328 devices | stays, trips and observed crossing times | `sea_edges.csv` (5,789 directed edges), `sea_nodes.csv` | supplied at the event |
| **MBS Census 2022** island- and atoll-level indicator sheets (2 × xlsx) | population, children 0–17, area, density, median age | `island_spine.csv` | [statisticsmaldives.gov.mv](https://statisticsmaldives.gov.mv/census-2022-island-and-atoll-level-indicator-sheets/) |
| **OCHA / HDX** Maldives subnational boundaries, ADM1 + ADM2 GeoJSON | 1,556 island polygons; centroids and areas, used to snap GPS stays | `island_spine.csv` | [data.humdata.org](https://data.humdata.org/dataset/a968d227-24c9-49ea-bbce-cee04ee94819) |
| **MoE School Statistics 2024** (PDF) | enrolment by grade, sex and island; reconciles to the published 5,105 in grades 11–12 | `island_school_provision.csv` | [education.gov.mv](https://education.gov.mv/storage/files/statistics/1782980847582-2024%20School%20Statistics.pdf) |
| **MoE school directory** (`moe.gov.mv/en/schools`, 220 schools; cached) | school names, atoll/island, roll and grade range — validation of the PDF | `schools.csv` | [moe.gov.mv](https://www.moe.gov.mv/en/schools) |
| **MoH health facility list** (`health.gov.mv/en/health-facilities`; cached HTML) | 164 listed facilities; 155 placed as health centres | `services.csv` | [health.gov.mv](https://health.gov.mv/en/health-facilities) |
| **Wikipedia — list of hospitals in the Maldives** | starter set of five hospitals (the MoH page does not name them) | `services.csv` | [wikipedia.org](https://en.wikipedia.org/wiki/List_of_hospitals_in_the_Maldives) |
| **MNU campus list** | five published campuses; four placed (Gan has no separate spine row) | `services.csv` | [mnu.edu.mv](https://mnu.edu.mv/about-us/) |
| **MTCC** bus and ferry ridership, 2023–2025 (`MTCC.xlsx`) | demand context; the supplier labels values "sample" | `mtcc_*.csv` | supplied at the event |
| **MACL** airport traffic, 2012–2026 (`data/MACL/`) | gateway demand context | `macl_monthly.csv` | supplied at the event |
| **Avas Ride** trips, Aug–Sep 2026, and car fares (`data/Avas_Ride/`) | Greater Malé last-mile demand and airport-transfer fares | `avas_daily.csv`, `avas_fare_matrix.csv` | supplied at the event |
| **`data/services.csv`** | the hand-maintained service register: source of truth, editable in the app | `service_access.csv` | this repository |

FollowMe, Census and OCHA build the travel-time graph; the MoE statistics and the service register
add the destinations; MTCC, MACL and Avas are context tables — ingested, normalised and
fingerprinted, but not combined with the GPS network. (The Avas fare matrix covers six Malé
airport-transfer zones at MVR 30–120; it is not an inter-island fare.)

Licences: Census, MoE and MoH material © Government of Maldives (credit the publisher); OCHA
boundaries open with attribution to OCHA FIS; the Wikipedia hospital list is CC BY-SA 4.0; MNU
campus pages are the university's public material. An optional OpenStreetMap extract (airports,
ferry terminals, roads) is fetched by `make external` when `osmium` is installed; since the air
layer was removed it feeds no served output and stays for the next iteration.

## Limits we state on purpose

- **One month of GPS.** August 2025 only; seasonal routes and monsoon cancellations are invisible.
- **Absence is not proof.** "No observed route" means no tracked vessel made the crossing in that
  month — not that no service exists. Seven inhabited islands have no observed sea traffic: five
  are Addu's causeway-linked islands (Feydhoo, Maradhoo, Meedhoo, Maradhoofeydhoo, Hulhudhoo),
  which are physically joined to Hithadhoo but have no tracked crossing in the data; the other two
  are Muraidhoo (Haa Alifu) and Nadellaa (Gaafu Dhaalu). The model does **not** invent land or air
  edges, so it reports what the data shows. Counted with Addu's road link, the gap is 28 islands,
  21,281 residents and 6,758 children.
- **1,776 devices, not the whole fleet.** The GPS covers 1,328 devices that made crossings; a
  device is not necessarily a vessel, and small dhoni traffic is certainly under-sampled.
- **Five sailings maximum.** Deliberate: a sixth hop is reported as not connected rather than
  given an implausible number.
- **No inter-island fares.** The only supplied fare table is the Greater Malé airport-transfer
  matrix (six zones, MVR 30–120), so affordability is not modelled.
- **No air links yet.** 14 domestic airports are the next step; today Addu (Hithadhoo) and
  Fuvahmulah come back as unreachable by sea, and northern routes such as Malé → Kulhudhuffushi
  cost 8.5 h by sea against about 50 min by air.

## How this maps to the judging criteria

Nothing in this repo exists unless it moves a criterion — the audit trail is
**[docs/criteria-map.md](docs/criteria-map.md)**.

| Criterion | Weight | Where it is earned |
|---|---|---|
| Technical execution | 20 % | the demo runs offline; every number re-derivable; `make check` asserts 27 published figures; limits stated |
| Impact | 15 % | **[docs/findings.md](docs/findings.md)** — a named user, an explicit decision, 33 islands ranked by children |
| Scalability | 15 % | `make ingest` / `make watch` rebuild only the stale stages; one command per stage; no database server to migrate |
| Data Utilization | 15 % | twelve sources catalogued above; organiser data + official public data only; school totals reconcile to 5,105; island areas agree with OCHA at r = 0.9996 |
| Innovation | 10 % | the method — an observed network reconstructed from GPS, not a published timetable |
| Relevance | 10 % | island-to-island access to post-16 education and health care, 187 islands |
| Clarity | 5 % | one question, one map, one simulator |
| Teamwork | 10 % | five separable pipeline stages for five people |

## Repository layout

```
data/                     supplied datasets + external/ (open data, downloaded) + derived/ (pipeline output)
data/platform.sqlite      the serving database (rebuilt, never hand-edited)
db/schema.sql             the tables and views the app queries
scripts/                  the pipeline: spine → sea → provision → services → access → simulator → placement → database → check
web/                      Django + HTMX: map (/) and service simulator (/simulator/)
docs/                     findings, criteria map, judging notes, pipeline, screenshots
REVIEW.md                 the review: challenge card, dataset teardown, risks
Makefile                  make / make ingest / make watch / make check / make run
```

## AI assistance

This project used an AI coding assistant (DeepSeek Harness) to profile the provided datasets,
write the pipeline and the web app, and draft this README. Every number in the app comes from a
script in `scripts/` that can be re-run; the two cross-checks we rely on are stated in the code —
the school table reconciles to the published national total of 5,105 students in grades 11–12,
and island areas reconcile to OCHA boundaries at r = 0.9996. All AI-assisted code was read,
run, and verified by the team.
