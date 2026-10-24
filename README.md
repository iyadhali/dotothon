# Access to key services across the Maldives

**Maldives Datathon 2026 · A Team**

187 inhabited islands, 448,819 residents, one question: **how long does it take to reach the
nearest school teaching grade 11–12, health centre or hospital — and where would the next service
help most?**

The travel times are **not** taken from a timetable. They are reconstructed from a month of
anonymised vessel GPS (17.4 M points from 1,328 tracked devices), so the network in the model is
the one boats actually sailed in August 2025, not the one that was published.

**The headline:** 44 islands teach grade 11–12. **154 islands and 416,235 people** can reach one
within two hours; **33 fall outside** — 26 have an observed route that takes longer, and **7 have no
observed route at all**. Those 33 hold **32,584 residents and 9,591 children**. On the same
network, only **30 islands, 262,712 people and 48,768 children** can reach a hospital within two
hours, at a median of **4.79 hours**.

The app turns that into two decisions: which islands are worst served, and where a new school,
health centre or crossing would bring the most people within reach.

---

## The problem

The Maldives is 187 inhabited islands spread across 26 atolls. The services that determine
opportunity — a school teaching grades 11–12, a health centre, a hospital — are concentrated on a
few islands. For everyone else, access is a boat ride: whether one goes, when, how many transfers,
and how long the wait.

Two gaps stand out:

- **Education.** Only 44 islands teach grade 11–12. For 33 islands (32,584 residents, 9,591
  children), the nearest such school is more than two hours away or not reachable at all in the
  observed network. Nationally, **29.9 %** of 16–17-year-olds are enrolled in higher secondary,
  against **91.9 %** in primary.
- **Health.** Primary care is close to universal — 183 of 187 islands are within two hours of a
  health centre. Hospitals are not: 30 islands, 262,712 people and 48,768 children are within two
  hours, at a median of 4.79 hours. The same network produces both answers.

**Why it is hard to see.** The country publishes schedules and facility lists, but not an
origin–destination travel-time matrix. Ferry timetables are incomplete, seasonal, and do not say
whether a connection actually works. Decisions — where to put the next health centre, which island
gets a new school, which crossing to subsidise — are made without a measured network. We rebuild
that network from the GPS the boats themselves emitted, then run one Dijkstra per service type over
it.

**Who it is for.** Planners in the Ministry of Education and the Ministry of Health, atoll councils,
and transport operators choosing routes. The map answers what an island can reach today; the
simulator scores where a new facility or crossing would help the most people.

## How to run it

Requirements: Python 3, `make`, and the supplied data in `data/` (the GPS month is 1.8 GB).

```bash
make setup       # pip install -r requirements.txt
make all         # fetch open data, rebuild every stage, run 27 checks
make run         # rebuild the serving database and start Django on :8000
```

Open <http://127.0.0.1:8000>. The app has two pages: the **map** (`/`) and the **service simulator**
(`/simulator/`).

For an incremental rebuild:

```bash
make ingest                  # fingerprint sources, rebuild only the stages that changed
make watch                   # the same, polling every 10 s
python scripts/ingest.py --dry-run   # show what would rebuild
```

`make refresh GPS=/path/to/new/month` rebuilds everything from a new FollowMe month without
re-downloading open data.

There is no database server, no API key and no network call at runtime: one SQLite file
(`data/platform.sqlite`), vendored HTMX and Leaflet, so the demo runs offline. The first `make all`
needs internet for Census/OCHA (and optionally OSM); after that, rebuilds are local. Only
`build_sea_network.py` is slow — it reads 1.8 GB of GPS and takes about four minutes.

**What you can do in it:** click an island for its services, travel times and sailings; filter the
list to education or health and redraw the journeys; connect two islands and see the sailing/waiting
split; recolour the map by any service type; read the 33-island gap table below the map; and use the
simulator to score candidate facilities and one hypothetical crossing at a time.

The pipeline is nine standalone scripts, each reading files in `data/` and writing CSVs to
`data/derived/`:

```
scripts/build_island_spine.py      Census + OCHA → 187 inhabited islands
scripts/build_sea_network.py       31 GPS files → observed crossings (5,789 directed edges)
scripts/build_school_provision.py  MoE School Statistics → students per grade per island
scripts/seed_services.py           MoH, MoE, MNU, hospitals → services.csv
scripts/build_reachability.py      graph → hours to the nearest grade 11–12 school
scripts/build_service_access.py    register + graph → coverage for every service
scripts/build_simulator.py         coverage → placement.csv
scripts/build_placement.py         one new crossing → link_candidates.csv
scripts/build_database.py          derived CSVs → data/platform.sqlite
```

Re-running any stage is safe; nothing is mutated in place. `make check` asserts the 27 published
figures (the school table reconciles to the national total of 5,105 students in grades 11–12, and
island areas agree with OCHA at r = 0.9996).

## Data sources

Twelve sources feed the build. All are supplied for the datathon, published by the Government of
Maldives, open data from OCHA and Wikimedia, or maintained in this repository. `data/derived/source_manifest.md` records the file
count, size, mtime and group fingerprint of each; `data/platform.sqlite` keeps a `source_file` row
for every input ever ingested.

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
| **MTCC / RTL** bus and ferry ridership, 2023–2025 (`MTCC.xlsx`) | demand context; the supplier labels values "sample" | `mtcc_*.csv` | supplied at the event |
| **MACL** airport traffic, 2012–2026 (`data/MACL/`) | gateway demand context | `macl_monthly.csv` | supplied at the event |
| **Avas Ride** trips, Aug–Sep 2026, and car fares (`data/Avas_Ride/`) | Greater Malé last-mile demand and airport-transfer fares | `avas_daily.csv`, `avas_fare_matrix.csv` | supplied at the event |
| **`data/services.csv`** | the hand-maintained service register: source of truth, editable in the app | `service_access.csv` | this repository |

FollowMe, Census and OCHA build the travel-time graph; the MoE statistics and the service register
add the destinations; MTCC, MACL and Avas are context tables — ingested, normalised and
fingerprinted, but not combined with the GPS network. (The Avas fare matrix covers six Malé
airport-transfer zones at MVR 30–120; it is not an inter-island fare.)

**Also cited.** The submission deck uses the **HeiGIT / OpenAccessLens** car-only accessibility
baseline (HDX) for comparison and **MoH HEMS / Aasandha** reports for specialist-referral context;
neither feeds the model. **OpenStreetMap** is fetched optionally by `make external` (airports, ferry
terminals, roads) but feeds no served output since the air layer was removed.

Licences: Census, MoE and MoH material © Government of Maldives (credit the publisher); OCHA
boundaries open with attribution to OCHA FIS; the Wikipedia hospital list is CC BY-SA 4.0; MNU
campus pages are the university's public material.

## AI tools used

| Tool | Used for |
|---|---|
| **ChatGPT** | Planning — brainstorming, structuring the presentation, and refining the argument. |
| **OpenCode** | Planning — planning, outlining, and iterating on the presentation content. |
| **Claude** | Coding — implementation and debugging of the pipeline and the web app. |
| **Gamma** | Presentation — designing and formatting the submission deck. |

AI was used for drafting, code and slides, never for the numbers. Every figure in the app is
produced by a script in `scripts/` and re-checked by `make check` (27 assertions). Two independent
cross-checks are built in: the school table reconciles to the published national total of 5,105
students in grades 11–12, and island areas agree with OCHA boundaries at r = 0.9996. All
AI-assisted output was read, run and verified by the team before submission.

## Limits we state on purpose

- **One month of GPS.** August 2025 only; seasonal routes and monsoon cancellations are invisible.
- **Absence is not proof.** "No observed route" means no tracked vessel made the crossing in that
  month — not that no service exists. Seven inhabited islands have no observed sea traffic: five
  are Addu's causeway-linked islands (Feydhoo, Maradhoo, Meedhoo, Maradhoofeydhoo, Hulhudhoo),
  which are physically joined to Hithadhoo but have no tracked crossing in the data; the other two
  are Muraidhoo (Haa Alifu) and Nadellaa (Gaafu Dhaalu). The model does **not** invent land or air
  edges, so it reports what the data shows. Counted with Addu's road link, the gap is 28 islands,
  21,281 residents and 6,758 children.
- **1,776 device IDs, not the whole fleet.** The GPS contains 1,776 devices; 1,328 made crossings
  that entered the network. A device is not necessarily a vessel, and small dhoni traffic is
  certainly under-sampled.
- **Five sailings maximum.** Deliberate: a sixth hop is reported as not connected rather than
  given an implausible number.
- **No inter-island fares.** The only supplied fare table is the Greater Malé airport-transfer
  matrix (six zones, MVR 30–120), so affordability is not modelled.
- **No air links yet.** 14 domestic airports are the next step; today Addu (Hithadhoo) and
  Fuvahmulah come back as unreachable by sea, and northern routes such as Malé → Kulhudhuffushi
  cost 8.5 h by sea against about 50 min by air.

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

The judging audit trail is [docs/criteria-map.md](docs/criteria-map.md); the findings behind the
gap ranking are in [docs/findings.md](docs/findings.md); the pipeline detail is in
[docs/pipeline.md](docs/pipeline.md).
