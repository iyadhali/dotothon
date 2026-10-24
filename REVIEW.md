# Maldives Datathon 2026 — Challenge Card & Data Review

**Team:** A Team · **Mode:** Multi-Modal (Land, Sea, Air) · **Reviewed:** 24 Oct 2026, 10:06 MVT
**Reviewer scope:** the briefing PDF, everything in `data/`, and what open data can realistically be joined to it before the 18:00 freeze.

---

## 0. Verdict in six lines

1. **The card is compliant but strategically loose.** 33 of 50 words, describes a problem rather than a solution, no data/methods — all criteria the brief actually checks. But it names *two* service classes (education **and** "essential services") and an affordability claim the data cannot support. It is *not scored*, so fix the framing in the README + slides rather than re-submitting.
2. **The provided data is four operator datasets, not four national ones.** Avas = Greater Malé land only. MTCC = Greater Malé buses + 8 ferry routes in 3 of 6 RTL zones. MACL = Velana international gateway only. **Only FollowMe covers the whole archipelago** — one month of vessel GPS.
3. **Nothing in `data/` contains a school, a campus, an enrolment number, an island population, or a fare.** The education story lives entirely in data you must bring from outside. That is the single biggest project risk.
4. **The brief promises MBS Census 2022 and HIES 2019; the folder has neither.** Ask at the 10:00 mentoring visit, but do not wait — both are downloadable now (verified below, already staged in `data/external/`).
5. **FollowMe is the project's spine and it works.** I verified that individual vessels can be tracked across multiple islands within a single day from the raw GPS, so an island-to-island network can be reconstructed empirically instead of copied from a timetable. That is the "original question or method" the 10 % Innovation criterion is looking for.
6. **Recommended pivot:** stop framing this as "education access" in the abstract. Frame it as *"how far, how long, and how reliably can a student on island X reach the nearest upper-secondary school or university campus, by sea, land and air — and which islands are worst served per resident?"* Same card, a measurable question, and every dataset you were handed has a job.

---

## 1. Challenge card review

### 1.1 Rule compliance (brief pages 3, 8, 10, 12)

| Requirement (brief) | Card as submitted | Status |
|---|---|---|
| One card per team, 3–5 min to complete | single card | ✅ |
| "Describe the problem, not the solution" | no solution proposed | ✅ |
| "No datasets, methods or solutions needed yet" | none named | ✅ |
| Problem statement, max 50 words | 33 words | ✅ |
| Mode of transport: "Sea · Land · Air" | "Multi-Modal (Land, Sea, Air)" | ⚠️ not one of the three options |
| No private/restricted/confidential data | none referenced | ✅ |
| Not scored / not part of final judging | — | information only |

### 1.2 Five substantive risks

1. **"Multi-Modal" may not be an option on the form.** The card says "Sea · Land · Air" as *alternatives*. Because the card is unscored and can be refined during the day this is low-stakes, but the mentor routing at 10:00 is chosen from it — a single option (Sea, since the ferry/vessel data dominates) may get you a better-matched mentor. Confirm what was actually submitted and mention multi-modality verbally.
2. **Two service classes dilute the story.** "universities and schools … education **and essential services**" gives judges three possible projects. Impact (15 %) is scored on "a clear user and a clear action" — a fuzzy service class makes both fuzzy.
3. **"Affordable" is unsupported by the data.** The only price information in the entire folder is `car_fare_matrix.csv`: six Malé-area zones, fares MVR 30–120, symmetric, diagonal 30 — an airport-transfer table, not a fare model for inter-island travel. If you keep the word "affordable", a judge will ask for the fare evidence and you will not have it. Either drop it, or add the published MTCC/RTL fare schedule as a source.
4. **No named user, no named action.** Nothing in the card says *who* acts on the finding. MoE transport planning, MTCC route scheduling, and island councils are three different audiences with three different asks.
5. **Education access is asserted, not measured.** The card implies schools are unevenly reachable but the provided data cannot show a single school. The gap is closable (see §4) but the card currently promises more than the folder can deliver.

### 1.3 Suggested rewrite (49 words, problem-only, no solution)

> Schools and higher-education campuses sit on a few urban islands. The other inhabited islands depend on scheduled ferries and domestic flights to reach them, so many students face long, infrequent and costly journeys. We ask: how uneven is this multi-modal access to education, and where is it worst?

Why this is stronger: it names the mechanism (campuses concentrated, everyone else scheduled), keeps the human cost, and ends on a *question* — which is exactly the shape the brief's own example takes ("We want to investigate patterns … and find gaps in accessibility"). Use this in the README and on slide 1; leave the submitted form alone.

If you prefer to stay verbatim with what was submitted, at minimum add one sentence to the README naming the user and the decision: *"User: the Ministry of Education's transport planner. Decision: which islands get a new or higher-frequency link."*

---

## 2. What is actually in `data/`

| # | Dataset | Rows | Period | Geographic reach | Verdict |
|---|---|---|---|---|---|
| 1 | `Avas_Ride/avas_rides_aug_sep_2026.csv` | 371,788 | 1 Aug – 30 Sep 2026 (61 days) | **Greater Malé metro only** | usable for land last-mile leg; values look modelled |
| 2 | `Avas_Ride/car_fare_matrix.csv` | 6 | undated | 6 Malé-area zones | airport-transfer fares, not inter-island |
| 3 | `FollowMe_august_2025/*.csv` | 17,462,749 | 1–31 Aug 2025 | **national (1,776 devices)** | the only nation-wide dataset; needs heavy cleaning |
| 4 | `MACL/Airport traffic_Dataset_27092026.csv` | 168,959 | Jan 2012 – Jul 2026 | **Velana international only** | strong time series; anonymised carriers/routes |
| 5 | `MTCC.xlsx` (4 sheets) | 180 + 1,095 + 258 | 2023–2025 / 2025 | **Greater Malé buses + 8 ferry routes** | ridership labelled "sample value" by the supplier |

### 2.1 Avas Ride — 371,788 orders, Greater Malé only

- Bounding box: lat **4.1685–4.2401**, lng **73.5001–73.5512** → Malé, Hulhumalé Phase 1/2, Velana airport. 472 distinct pickup cells, **50,360 distinct OD pairs**.
- Status mix: `payment_completed` 86.11 %, `ride_expired` 7.33 %, `ride_completed` 6.56 %. **Ask the organisers what these mean** — 6.6 % "completed" against 86 % "payment completed" is not a normal funnel and the two labels are probably not mutually exclusive.
- No nulls; distance 1.98–13.69 km; `time_sec` 300.001–1,214 s.
- **The numbers look generated or heavily smoothed.** Implied speed is 38.1 km/h with σ = 3.0 across all 371,788 trips (min 23.1, max 51.4), and `time_sec` never falls below 300.001 s — a hard 5-minute floor. Real Malé traffic does not have a 3 km/h standard deviation. Distance/straight-line ratio is 1.52 on average (max 6.7), so geometry is at least plausible.
- Daily volume 4,643–12,920 orders (mean 6,095), peaking 15:00–19:00 and Fri/Sat.
- **Do:** use it as a *structure* (where the land last-mile demand concentrates, how far people travel inside the capital region), never as evidence of real behaviour, and never to generalise beyond Malé.
- `car_fare_matrix.csv`: 6×7 grid, one `city` value ("Male City"), zones Male / Hulhumale Ph1 / Velana Airport / Hulhumale Ph2 / Sea Plane / Domestic Terminal; MVR 30–120, symmetric, diagonal 30. Naming the "city" column suggests a larger table was collapsed — ask if the full matrix exists.

### 2.2 FollowMe — 17.46 M GPS points, 1,776 devices, Aug 2025

**This is the project.** Verified facts:

- 31 daily files, `device_date` = 1–31 Aug 2025. `timestamp` is the DB save time and runs to **2026-10-08**: 292,978 rows (1.68 %) were uploaded after August, with a maximum lag of 10,398 h. **Use `device_date` for all time analysis; use `timestamp` only for ingestion QA.** This is a silent bug waiting to happen.
- **Coordinates have junk.** 212,300 rows (1.22 %) sit outside the Maldives (lat −4.05 to 8.80, lng **15.0** to 78.4 — lng 15 is West Africa). Clean filter `lat 0–7.5, lng 72–74` leaves 17,250,449 rows.
- Also invalid: `speed > 60` (1,908 rows — speed is in **knots**, median 7), `heading > 360` (9 rows), `network` values 0 (141,793 rows), 68 (363), 8 (1) — only 1 and 2 are documented.
- Coverage: 53,272 distinct 0.01° cells, **2,185 cells with >1,000 polls** → essentially every inhabited island plus resorts. Top cells: (5.73, 73.36) 1.42 M polls, (3.85, 73.46) 0.41 M, (4.18, 73.51) 0.29 M.
- 76.6 % of in-bbox polls are moving (speed > 2). Median poll interval 6–7 s on some devices, 0 s on others (duplicate timestamps).
- **OD reconstruction verified.** Segmenting each device into stationary clusters (speed ≤ 2, ≥ 5 consecutive polls, median coordinates, dedupe on a 2-dp cell) yields 5–46 stays per device per day. Device `862997066425160` moved between (3.61, 72.73) → (3.61, 72.82) → (3.55, 72.88) → (3.62, 72.72) → (3.48, 72.78) within 2025-08-01 — a real multi-island itinerary in the Gaafu atolls. Device `868291073370286` held a hub at (5.73, 73.36) all day. **Build the island graph from this, not from a timetable.**
- **Trap:** the hourly profile peaks 02:00–06:00 and dips 13:00–19:00. That is a device duty-cycle artefact, **not** travel demand. Never present the raw hourly curve as "when people travel".
- **Trap:** 1.8 GB raw. GitHub blocks >100 MB files. Commit *derived* tables (stay points, OD edges, island centroids — a few thousand rows), never the raw CSVs.

### 2.3 MACL — 168,959 flight movements, 2012–2026

- **`dep_date` / `arrival_date` are `m/d/Y`, not `YYYY-MM-DD` as `Metadata.csv` claims.** Proof: the first component never exceeds 12 while the second reaches 31, so 102,304 rows (60 %) can only be month-first. Parsing with `%d/%m/%Y` silently misdates 60 % of the file and manufactures dates past the file's end. Correct parse gives **2012-01-01 → 2026-07-31** (last record 168959 = `7/31/2026`).
- `SCHEDULED` 167,151 / `CHARTER` 1,808. Regions: South Asia 60,600, Middle East 50,045, Southeast Asia 25,591, Europe 14,276, East Asia 12,640, Central Asia & CIS 5,657, Africa 115, Other 35.
- 112 carriers, 1,008 route codes, 19 aircraft types; Widebody 84,646 / Narrowbody 78,546 / Turboprop 5,767.
- Total passengers (arr + dep, all ages), millions: 2012 2.34 → 2019 4.04 → 2020 1.32 → 2022 3.94 → 2023 4.52 → 2024 4.95 → 2025 5.37 → 2026 (7 months) 3.02. The 2020 collapse is a clean, quotable shock.
- **Limitation: carriers and routes are anonymised** (`Carrier_008`, `Route_0175`), and this is **Velana International only** — there are no domestic island airports in the file. So MACL cannot answer "which island has an air link"; it answers "how much international demand lands at the gateway".
- Minor: `arrival_date` null in 1 row, `carrier_code` 1, `ata` 72, `atd` 71; times are strings like `"0:35"`; 49 records carry zero passengers.

### 2.4 MTCC — buses and ferries, 2023–2025

| Sheet | Rows | Coverage |
|---|---|---|
| `README` | 14 | data dictionary, and the critical phrase **"sample value"** |
| `bus_monthly` | 180 | Jan 2023–Dec 2025, 5 Greater Malé routes (R1, R2, R3, R4, R7) |
| `bus_daily` | 1,095 | 2025 only, **3 routes** (R1, R2, R4), 365 rows each |
| `ferry_monthly` | 258 | 2023-01–2025-12, **8 routes** in **3 of 6 RTL zones** |

- `total_pax = paid_pax + foc_pax` holds in every row of both bus sheets; `weekday` matches the real calendar with 0 mismatches.
- Bus pax per year: 5.39 M (2023) → 5.51 M (2024) → 5.71 M (2025), +2.3 % / +3.5 %. **FOC (free-of-charge) riders are 33.4 % of all bus passengers in 2025** — a strong policy hook (over-65, PWD, infants travel free).
- **Cross-sheet inconsistency:** 2025 totals do not reconcile. R1 monthly 2,094,295 vs daily 1,764,669; R2 1,564,244 vs 1,301,897; R4 486,316 vs 389,210. Plus daily covers only 3 of the 5 routes. **Never sum across sheets**; pick one sheet per claim and say which.
- Ferry: 8 routes (`H1, R2C1, R2C2, S1C1, S1C5, Z2R1, Z5R2, Z5R5`) across 4 atolls — Haa Alifu, Lhaviyani, Noonu, Gaafu Alifu & Gaafu Dhaalu. Zones 01/02/05 only. Yearly passengers 76,299 → 93,996 → 97,217. Six rows where a route starts mid-year (`Z2R1` 2024; `Z5R2`/`Z5R5` 2023). No FOC category.
- The README's own words — "sample value" — mean **you must not present these as official MTCC ridership**. Use them for route-level comparison and growth direction, and label them as supplied samples.

### 2.5 What the folder cannot answer (the honest gap table)

| Question the card implies | Answerable from `data/`? | Where the answer actually is |
|---|---|---|
| Which islands have a school / A-level / campus | ❌ | MoE school register (§4) |
| How many people live on island X | ❌ | Census 2022 island indicator sheet (§4) |
| Island-to-island ferry frequency and travel time | ✅ (FollowMe, Aug 2025) | derived, no open source needed |
| Scheduled route and timetable | ⚠️ partial | MTCC published schedule PDF |
| Domestic air links between islands | ❌ | airport list + published schedules |
| Island polygon / centroid | ❌ | OCHA ADM2 boundaries (§4) |
| Trip affordability | ❌ | MTCC/RTL fare schedule (thin) |
| Enrolment, attainment, dropout by island | ❌ | Census 2022 tables / HIES 2019 |

**Read that table as the project's work plan.** Four of eight rows are external data, and all four are downloadable today.

---

## 3. Coverage map — where each dataset has jurisdiction

| | Local (within island) | Inter-island | International |
|---|---|---|---|
| **Land** | Avas 371k trips + MTCC buses (Greater Malé only) | ✗ (Malé↔Hulhumalé only, via bridge/bus) | ✗ |
| **Sea** | ✗ | FollowMe 1,776 vessels nationwide (Aug 2025); MTCC 8 routes, 4 atolls | ✗ |
| **Air** | ✗ | ✗ (no domestic airports in the data) | MACL Velana, 2012–2026 |

Two blank cells matter: **inter-island air** and **national land**. The first is fixable from open data (19 airports: 5 international, 14 domestic). The second is not — which is why the project must be an *inter-island* accessibility study with Greater Malé as the land case study, not a national land-transport study.

---

## 4. Open and free data — verified this session

Everything below returned HTTP 200 from this machine at 10:03–10:06 today. The first two are already staged in `data/external/`.

### 4.1 Must-have (the project cannot run without these)

| Source | Why | Link | Status |
|---|---|---|---|
| **MBS Census 2022 — Island Level Indicator Sheet** | population, area, child population (0–17), density, median age per island | [page](https://statisticsmaldives.gov.mv/census-2022-island-and-atoll-level-indicator-sheets/) · [XLS direct](https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2023/09/Island-Level-Indicator-Sheet-Population.xlsx) | ✅ staged → `data/external/census2022_island_population.xlsx` (141 KB) |
| **OCHA / HDX — Maldives Subnational Administrative Boundaries (COD-AB)** | **island-level polygons: 1,556 ADM2 features** with name, atoll, area, centre lat/lon; 21 ADM1 atolls | [HDX dataset](https://data.humdata.org/dataset/a968d227-24c9-49ea-bbce-cee04ee94819) · [GeoJSON zip](https://data.humdata.org/dataset/a968d227-24c9-49ea-bbce-cee04ee94819/resource/3e277382-c09a-4496-bd46-c1a2a92bb835/download/mdv_admin_boundaries.geojson.zip) | ✅ staged → `data/external/mdv_admin2_islands.geojson` (17 MB) + `mdv_admin1_atolls.geojson` |
| **→ island spine (already built)** | the join of the two above: 187 rows × population, child 0–17, area, centroid, pcode | built by `scripts/build_island_spine.py` | ✅ `data/external/island_spine.csv` — **100 % of islands matched, area correlation 0.9996** |
| **MoE school register** | 219 government schools, 81,005 students, 9,952 teachers; per-atoll counts; one page per school with island in the name | [stats](https://www.moe.gov.mv/en/schools-stats) · [directory](https://www.moe.gov.mv/en/schools) · [2024 School Statistics PDF](https://education.gov.mv/storage/files/statistics/1782980847582-2024%20School%20Statistics.pdf) | ⬜ to fetch |
| **MNU campus list** | the 5 higher-education locations the card is really about — Malé main campus + **Kulhudhuffushi, Gan, Hithadhoo, Thinadhoo** | [mnu.edu.mv/about-us](https://mnu.edu.mv/about-us/) | ⬜ 5 rows, hand-enter |

### 4.2 Strong additions

| Source | Why | Link |
|---|---|---|
| MTCC / RTL ferry schedules (PDF) | real timetables + fares to benchmark the GPS-derived network | [CFN all-ferry schedule Aug 2026](https://mtcc.mv/wp-content/uploads/2025/02/CFN-All-ferry-Schedule-1-August-2026.pdf) · [schedules index](https://mtcc.mv/schedules-2/) |
| Airports of the Maldives | 19 airports = 5 international + 14 domestic; needed for the missing "inter-island air" cell | [Wikipedia list](https://en.wikipedia.org/wiki/List_of_airports_in_the_Maldives) · [MMTV: 19 airports, 4 under construction](http://en.mmtv.mv/1357) |
| OpenStreetMap — Geofabrik Maldives extract | airport and ferry-terminal points (see caveat below); roads for the Malé inset | [asia/maldives-latest.osm.pbf](https://download.geofabrik.de/asia/maldives-latest.osm.pbf) (3.5 MB) |
| RTL network zones | explains why MTCC covers 4 atolls: six zones, Zone 1 = HA/HDh/Sh, Zone 2 = Noonu/Raa/Baa/Lh, Zone 5 = GA/GDh, Zone 6 = Fuvahmulah… | [MMTV article](http://en.mmtv.mv/5998) |
| Census 2022 statistical releases | constituency + atoll tables if you need a second cut | [releases](https://statisticsmaldives.gov.mv/census-2022-statistical-releases/) |
| HIES 2019 (the one the brief promises) | household income/expenditure → the *affordability* leg | [statisticsmaldives.gov.mv/hies](https://statisticsmaldives.gov.mv/hies/) |

### 4.3 Tested and rejected — save yourselves the hour

- **OpenStreetMap is not a substitute for the island or school register.** Live Overpass count for the Maldives (24 Oct 2026): `amenity=school` **121** objects (vs 219 government schools), `place=island` **91** (vs ~190 inhabited islands), `aeroway=aerodrome` **26** (vs 19 real — good), `amenity=ferry_terminal` **69** (good). → use OSM for **airports and ferry terminals only**.
- **GADM has no usable Maldives file.** `gadm41_MDV_1/2/3.json` all return 404. Use the OCHA COD-AB above instead.
- **Don't scrape the 219 MoE school pages one by one** if time is short — the school *name* already contains the island ("Maarandhoo School", "Ha. Atoll Education Centre"), so the register list alone is enough to place schools at atoll level, and the ADM2 polygons resolve the rest.

### 4.4 The one join you must get right — and it is already done

Joining Census islands to island geometry on the island name alone **fails badly**. Measured: name-only matching produced 222 matches for 186 islands (127.8 % "coverage") because dozens of islands share a name across atolls (Funadhoo, Lhohi, Gan, Feydhoo…) and it silently assigns the wrong atoll to 37 % of matches.

The atoll-aware join in `scripts/build_island_spine.py` reaches **186/186 islands (100 %), 100 % of population**, with `corr(census area, OCHA area) = 0.9996` and a median absolute area difference of **0.006 km²** — i.e. the two independent sources agree, which is the strongest validation available for this join. Output: `data/external/island_spine.csv`.

What it took, and the traps to keep in mind:

- **37 islands are spelled differently in the two sources.** Resolved via `difflib` at a 0.72 cutoff plus two manual aliases. Examples: `Ugoofaaru`→`Un'goofaaru`, `Dhidhdhoo`→`Dhihdhoo`, `Kuribi`→`Kurin'bee`, `Gamu`→`Gan` (Laamu), `Maamigili`→`Maamin'gili`, `Fares-Maathodaa`→`Faresmaathodaa`. Do not "fix" these by hand in the data — keep both names in the table (`island`, `ocha_name`).
- **Atoll-code trap:** in the Census sheet **`M` = Meemu**, not Malé. Malé does not appear in the island sheet at all — the city total (211,908, "Male' including Villimale'") has to be read from the atoll sheet.
- **Exclude the four aggregate rows:** *Administrative Islands in Atolls* 236,911 · *Non Administrative Islands* 66,313 · *Resorts* 52,482 · *Industrial Islands* 13,831.
- **Coverage note to carry into the pitch:** the spine accounts for **448,819 of 515,132 residents (87 %)**, leaving 66,313 people in the "Non Administrative Islands" aggregate that the workbook does not itemise per island. That is a data-release gap, not a bug — ask about it at mentoring, and say so on the limitations slide.
- The island sheet's header is at row index 2 with merged cells; read with `header=None` and index columns by position (`0` atoll, `1` island, `2` population, `20` child 0–17, `49` area km², `50` density, `52` median age). Name-based parsing silently shifts by one column.

Populated islands by atoll (from the spine, 186 islands / 236,911 residents):

| Atoll | Islands | Population | | Atoll | Islands | Population |
|---|---|---|---|---|---|---|
| Seenu | 6 | 25,062 | | Alifu Dhaalu | 10 | 10,540 |
| Haa Dhaalu | 13 | 22,440 | | Thaa | 13 | 10,260 |
| Kaafu | 9 | 17,749 | | Gaafu Alifu | 9 | 9,190 |
| Raa | 15 | 17,581 | | Gnaviyani | 1 | 9,177 |
| Laamu | 11 | 14,699 | | Lhaviyani | 4 | 8,992 |
| Haa Alifu | 14 | 14,623 | | Alifu Alifu | 8 | 8,017 |
| Shaviyani | 14 | 13,698 | | Dhaalu | 6 | 6,637 |
| Gaafu Dhaalu | 9 | 12,758 | | Meemu | 8 | 5,490 |
| Noonu | 13 | 12,503 | | Faafu | 5 | 4,869 |
| Baa | 13 | 10,631 | | Vaavu | 5 | 1,995 |

Children aged 0–17 across those islands: **73,754 (31.1 %) — the demand denominator for every accessibility number you report.**

---

## 5. Recommended project — what I would actually build in seven hours

**Question.** For each inhabited island, how long and how reliably does it take a student to reach the nearest *upper-secondary school* and the nearest *university campus*, across sea + land + air — and which islands are worst served **per resident**?

**Unit of analysis:** the island (≈190 inhabited). **Outcome:** a population-weighted accessibility index with a ranked gap list.

**Method, in dependency order:**

1. **Island spine** — ✅ *already built:* `data/external/island_spine.csv` (187 rows, 100 % matched, validated against OCHA areas). Census population + child 0–17 + centroid per island. **Do not rebuild it; start from it.**
2. **Education supply** — ✅ *already built:* `data/derived/island_school_provision.csv` — per-island enrolment by grade, parsed from MoE *School Statistics 2024* pp. 22–37 (16 grade columns × M/F per island; every row is validated because its grade cells must sum to its printed sub-total). **It reconciles exactly with the national totals: grade 11–12 = 5,105 students, all students = 99,687 vs 98,845 published.** 44 islands teach grade 11–12; 181 teach grade 7–10; 4 MNU campuses (Malé, Kulhudhuffushi, Gan, Hithadhoo) and a fifth at Thinadhoo. *~40 min → 0, because it is done.*
3. **Sea network (the original bit)** — FollowMe: clean → stationary-cluster segmentation per device → stay points → OD edges with observed travel time and departure-hour distribution. Aggregate to island pairs. **This is your differentiator: an observed network instead of a published timetable.** *~2 h, the hardest step; precompute and cache.*
4. **Air network** — *not built yet, and it is the biggest remaining distortion:* Malé→Kulhudhuffushi is 508 min and 3 sailings by sea, ~50 min by air. 14 domestic airports (5 international) make air the difference between "2 days" and "same day". Add each domestic airport → Velana with scheduled block time + 1 h transfer, then re-run step 6. *~45 min, highest marginal value left.*
5. **Land leg** — ✅ *partly built:* the Addu causeway chain (Hithadhoo–Maradhoo–Maradhoofeydhoo–Feydhoo–Hulhudhoo–Meedhoo) is in the graph at 30 km/h, because without it the sea data reports 6 Addu islands as unreachable when they are in fact one land mass. Greater Malé buses (Avas + MTCC R1/R2/R4) are still missing as an intra-city cost. *~20 min left.*
6. **Accessibility** — ✅ *already built* (`scripts/build_reachability.py`): Floyd–Warshall over 1,134 nodes, edge = observed median crossing time, 1.0 h transfer, hop-budgeted at 2 sailings. Outputs `data/derived/island_access.csv` (187 inhabited islands) and `island_pairs.csv` (31,536 directed pairs = the A→B query in one file).

**Headline results already in hand:**
| measure | value |
|---|---|
| inhabited islands / residents covered | 187 / 448,819 (87 % of the 515,132 Census total) |
| children 0–17 | 73,754 (16.4 % of residents) |
| islands that teach grade 11–12 | 44 (+ Greater Malé as a region total) |
| can reach grade 11–12 within 2 h | 156 islands, 420,175 people |
| within 4 h | 181 islands, 443,519 people |
| no reachable post-16 school at all | 2 islands, 1,115 people (Nadellaa GDh, Muraidhoo HA — both *zero observed boat traffic*, i.e. a data gap, not a proven cut-off) |
| national higher-secondary NER | **29.9 %** (M 25.8, F 34.3) vs primary 91.9 % — the drop is the story |

**Deliverables for the 18:00 submission:**
- `README.md` — problem, how to run, **every source credited**, AI-assisted parts listed (the brief checks all four).
- Reproducible pipeline: `01_clean.py → 02_islands.py → 03_network.py → 04_access.py → 05_figures.py`, plus `requirements.txt`.
- Figures: (a) national accessibility map, (b) travel-time distribution, (c) "students beyond 2 h" by atoll, (d) Malé last-mile inset, (e) observed ferry-frequency heat map.
- An interactive map or a single-page dashboard if — and only if — step 6 is finished with 90 minutes to spare.
- One-page methods note including how AI was used.

**Kill-switch order if you fall behind:** drop the interactive map → drop the Greater Malé bus last-mile → never drop the air layer now that the sea-only timings show 8.5 h for Malé→Kulhudhuffushi, which overstates the barrier and would get picked apart in Q&A. Steps 1, 2, 3 and 6 are already code, so the remaining risk is presentation, not analysis.

---

## 6. How this scores against the published rubric

> **Updated 24 Oct, after the organisers circulated the real rubric.** Each criterion is scored
> **1–5** and weighted to 100; three things change our strategy: a **dashboard is explicitly not
> innovative on its own**, **Data Utilization restricts sources** to organiser-provided, shared
> self-collected, or public open data, and the tie-break is the average of **Impact + Scalability**.
> The full rubric, our self-assessment (~76/100 today) and the five actions ranked by points at
> stake live in [docs/judging-criteria.md](docs/judging-criteria.md).

| Criterion | Weight | What this project puts on the table |
|---|---|---|
| Technical execution | 20 % | clean pipeline, runnable in one command, explicit limits section (one month of GPS, sample ridership) |
| Data utilization | 15 % | 4 provided datasets + 4 public ones joined; rubric explicitly rewards "provided **or** public data, or both" |
| Impact | 15 % | named user (MoE transport planning), named action (route prioritisation), quantified (N students beyond 2 h) |
| Scalability & readiness | 15 % | index recomputes from any month of FollowMe; roadmap = quarterly refresh + fare layer |
| Relevance to theme | 10 % | island-to-island access is the defining Maldivian transport problem |
| Innovation | 10 % | deriving the ferry network from GPS rather than a timetable; accessibility-per-resident rather than raw counts |
| Teamwork | 10 % | the five steps are cleanly separable across five people |
| Clarity | 5 % | one question, one map, one number |

---

## 7. Risk register

| # | Risk | Mitigation |
|---|---|---|
| 1 | 1.8 GB of GPS vs GitHub's 100 MB file limit | commit derived stay/OD/island tables only; add a `make data` script for the raw download |
| 2 | MACL dates parsed day-first → 60 % of rows wrong | parse `m/d/Y`; assert max date ≤ 2026-07-31; note the `Metadata.csv` error in the README |
| 3 | MTCC numbers presented as official | label every MTCC figure "supplied sample values"; never sum across sheets |
| 4 | Avas read as real behaviour | report it as a structure/last-mile indicator; cite the σ = 3 km/h flatness as the reason |
| 5 | FollowMe `timestamp` used instead of `device_date` | one cleaning function, assert `device_date` within Aug 2025 |
| 6 | Island name join silently wrong | ✅ solved — use `data/external/island_spine.csv` (100 % matched, area-validated); keep its `ocha_name` column for cross-checks |
| 7 | Census/HIES never appear from the organisers | already downloaded and staged; no dependency on them |
| 8 | Judges ask "where is the affordability evidence?" | either drop the word or add the MTCC fare schedule; prepare a one-line answer |
| 9 | AI-use declaration forgotten → pre-check fail | declaration + README AI section before 17:00, not 17:55 |

---

## 8. Questions to put to the organisers at 10:00

1. The brief says MBS Census 2022 and HIES 2019 are provided — they are not in the folder. Will they be released today, and in what form (microdata or tables)?
2. `avas_rides` status values: is `payment_completed` a superset that includes `ride_completed`? What is `ride_expired`?
3. Is `car_fare_matrix.csv` an extract of a larger zone matrix, and are the fares MVR?
4. MTCC README says "sample value" — is that sampling (a fraction of real counts) or synthetic data?
5. Is FollowMe the full tracked fleet or a customer sample, and are all 1,776 devices vessels? Any device-to-vehicle metadata?
6. MACL: can the carrier/route anonymisation be reversed for the pitch (e.g. is Carrier_XXX Maldivian)? Is there a domestic-airport equivalent table?
7. Is there a permitted-data list beyond "MBS or public data"? Specifically, is scraping moe.gov.mv school pages acceptable?

---

## 9. Repo and submission checklist (from the brief, pages 8–12)

- [ ] GitHub repo public or shared with the organiser account — **link only, no zip**
- [ ] `README.md`: problem · how to run · data sources · AI-assisted parts
- [ ] `requirements.txt` with pinned versions
- [ ] comments on the key steps
- [ ] no passwords, API keys, or personal data anywhere in history
- [ ] slides PDF **≤ 8 slides** — cover: problem, data and method, findings, meaning for transport policy
- [ ] original `.pptx` (or a viewable Slides/Canva link) sent alongside the PDF
- [ ] declaration filled, one per team, submitted by the lead
- [ ] one-page methods note including how AI tools were used
- [ ] screenshot the confirmation message
- [ ] hard stop **18:00** — the organisers' clock, commits after that are ignored

---

## Appendix A — numbers worth quoting on a slide

| Fact | Value | Source |
|---|---|---|
| Inhabited islands with population in the Census atoll tables | 186 (236,911 residents) | Census 2022 island sheet |
| Government schools / students / teachers | 219 / 81,005 / 9,952 | [MoE](https://www.moe.gov.mv/en/schools-stats) |
| University campuses | 5 — Malé + Kulhudhuffushi, Gan, Hithadhoo, Thinadhoo | [MNU](https://mnu.edu.mv/about-us/) |
| Airports | 19 = 5 international + 14 domestic (4 more under construction) | [MMTV](http://en.mmtv.mv/1357) |
| Tracked vessels in FollowMe, Aug 2025 | 1,776 devices, 17.25 M valid points | `data/FollowMe_august_2025` |
| Velana passengers, 2025 | 5.37 M (2020: 1.32 M) | `data/MACL` |
| Bus free-of-charge share, 2025 | 33.4 % of all passengers | `data/MTCC.xlsx` |
| Ferry passengers in the supplied sample, 2025 | 97,217 across 8 routes | `data/MTCC.xlsx` |
| Malé-region ride orders, Aug–Sep 2026 | 371,788 over 61 days | `data/Avas_Ride` |

## Appendix B — staged external files

```
data/external/census2022_island_population.xlsx   141 KB  MBS Census 2022, island indicator sheet
data/external/census2022_atoll_population.xlsx     81 KB  MBS Census 2022, atoll indicator sheet
data/external/mdv_admin1_atolls.geojson           278 KB  OCHA COD-AB, 21 atolls
data/external/mdv_admin2_islands.geojson           17 MB  OCHA COD-AB, 1,556 islands (name, atoll, area, centroid)
data/external/island_spine.csv                      27 KB  ⭐ built: 187 rows, population + child 0-17 + centroid
scripts/fetch_external_data.sh                            re-downloads all of the above
scripts/build_island_spine.py                             regenerates island_spine.csv (reproducible)
```

The spine's columns: `atoll_code, atoll_name, island, population, child_0_17, area_km2, density, median_age, island_pcode, lat, lon, area_km2_ocha, ocha_name, matched, coverage_note`.

**Git note:** commit the two Census workbooks, both GeoJSONs and the spine (18 MB total — under GitHub's limit). Do **not** commit `data/FollowMe_august_2025/` (1.8 GB).

Licences to restate in the README/declaration: Census 2022 and MoE material — Government of Maldives, cite the publisher; OCHA COD-AB — open, credit OCHA FIS and the Maldives government source; OSM — ODbL, © OpenStreetMap contributors; Geofabrik extract — ODbL.
