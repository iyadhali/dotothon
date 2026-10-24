# Multimodal implementation — build contract

Status: **implemented and validated** (24 October 2026). This file is the shared contract for the
implementation that follows [`MULTIMODAL_DATA_READINESS_PLAN.md`](MULTIMODAL_DATA_READINESS_PLAN.md).
It was written before the code so parallel work agreed on artifacts, assumptions and
acceptance checks. Results are recorded in [`VALIDATION.md`](VALIDATION.md); it does not
replace the plan's data caveats.

## 1. Outcome

A working, honest prototype with three parts:

1. **Prepared data** — a canonical island/stop/airport/service/facility network built
   from the local CSVs, with explicit confidence and a review queue for unresolved joins.
2. **Timetable-aware router** — one TypeScript implementation used by the web app and by
   a Node CLI (no second routing implementation in Python).
3. **Web application** — a national accessibility map, an origin/category/time planner,
   journey breakdowns, coverage/confidence reporting, and add/cancel/delay scenarios.

Everything must distinguish **verified ferry timetable**, **estimated air frequency
model**, and **user scenario**. Missing coverage must never be presented as zero access.

## 2. Non-negotiable modelling rules

- Baseline transit = the 102 recorded RTL ferry trips in `data/team-kandu/rtl_trips.csv`,
  reconstructed per `route_id` + `trip`, direction preserved, single recorded time used
  for both arrival and departure.
- The local snapshot has **no service calendars**. The baseline uses a clearly labelled
  **reference-day assumption**: every recorded RTL trip operates on the reference day.
  This assumption is visible in the UI and in every export.
- Air is included only as an **estimated frequency model** (`estimated=yes` in
  `data/external/air/domestic_routes.csv`). It is a separate toggle, never mixed into
  "verified" results. Departure times are generated from published weekly frequency;
  this is documented, not presented as an observed schedule.
- Do not use half the departure interval for waiting on timetabled ferries. Waiting is
  computed from the actual next departure.
- A traveller who stays aboard the same trip pays no new boarding buffer at intermediate
  stops. A transfer pays the boarding/check-in buffer, and a documented transfer penalty.
- No physical access link may imply crossing water by proximity. Same-island access,
  explicit road links, explicit airport speedboat links and published ferry stops only.
- Origins are the **191 inhabited islands** in `mdv_islands_master.csv`, population
  `pop2022`, total **447,420**. Census city total (211,908) and wards are not added on top
  of the four Greater Malé island rows. Report coverage against 515,132 republic total and
  name the omitted scopes (1,399 harbour-area residents, 66,313 non-admin-island persons).
- Facilities are island-level (`location_precision = island`). Report **physical access to
  a listed facility**, not confirmed service availability or building-level travel time.
- Do not invent departures to fill the national map. Generated air departures live in the
  estimated layer only and are labelled as such.

## 3. Data artifacts

The Python pipeline writes:

```
data/processed/multimodal/network.json        # canonical network + facilities + categories
data/processed/multimodal/islands.geojson     # simplified polygons for map, node islands only
data/processed/multimodal/aliases.csv         # review queue for every source join
data/processed/multimodal/report.json         # counts, coverage, unresolved, assumptions
web/public/data/multimodal.json               # copy served by the web app
web/public/data/islands.geojson               # copy served by the web app
```

`network.json` shape (TypeScript source of truth:
`web/shared/routing/types.ts`):

```jsonc
{
  "meta": {
    "schemaVersion": 1,
    "generatedAt": "2026-10-24T...",
    "timezone": "Indian/Maldives",
    "referenceDay": "2026-10-10",
    "serviceDayAssumption": "All 102 recorded RTL trips operate on the reference day; calendars are unverified.",
    "population": { "origins": 447420, "republic2022": 515132, "originCount": 191 },
    "assumptions": [
      { "id": "walk_speed", "value": "4.5 km/h", "confidence": "assumption", "source": "research/03_transport_network_and_methods.md" }
    ],
    "counts": { "islands": 200, "origins": 191, "stops": 117, "airports": 20, "ferryTrips": 102, "airServices": 32, "facilities": 0 },
    "routingDefaults": {
      "ferryBoardMinutes": 15, "ferryAlightMinutes": 2,
      "airBoardMinutes": 45, "airBoardMinutesMle": 60, "airAlightMinutes": 15,
      "transferPenaltyMinutes": 10, "additionalBoardPenaltyMinutes": 5,
      "maxJourneyMinutes": 1440
    }
  },
  "islands": [
    { "id": "MV007005", "name": "Dharavandhoo", "atoll": "B", "atollName": "Baa",
      "lat": 5.156, "lon": 73.130, "population": 997, "status": "inhabited",
      "isOrigin": true, "airportIata": "DRV" }
  ],
  "stops": [
    { "id": "RTL:207", "code": "207", "name": "B.Dharavandhoo", "islandId": "MV007005",
      "lat": 5.159, "lon": 73.134, "scheduled": true }
  ],
  "airports": [
    { "id": "MLE", "iata": "MLE", "name": "Velana International Airport",
      "islandId": "MV009052", "lat": 4.19183, "lon": 73.529099 }
  ],
  "accessEdges": [
    { "from": "island:MV007005", "to": "stop:RTL:207", "mode": "walk", "minutes": 2.4,
      "confidence": "estimated_access",
      "basis": "island representative point to stop, 4.5 km/h, 1.25 detour", "distanceKm": 0.15 }
  ],
  "services": [
    { "id": "ferry:259:1", "kind": "timetabled", "mode": "ferry", "operator": "RTL",
      "routeId": "259", "routeCode": "Z2R18", "zone": "Zone 2",
      "confidence": "verified_timetable", "calendar": "reference_day_all_recorded_trips",
      "source": "data/team-kandu/rtl_trips.csv",
      "stops": [
        { "stopId": "RTL:207", "name": "B.Dharavandhoo", "sequence": 1, "arrival": 905, "departure": 905 }
      ] },
    { "id": "air:MLE-DDD", "kind": "frequency", "mode": "air", "fromNode": "airport:MLE",
      "toNode": "airport:DDD", "fromAirport": "MLE", "toAirport": "DDD",
      "airline": "Maldivian", "weeklyFrequency": 28, "departuresPerDay": 4,
      "operatingWindow": { "start": 360, "end": 1080 }, "blockMinutes": 48,
      "departures": [450, 570, 690, 810], "confidence": "estimated_frequency",
      "status": "operating", "source": "data/external/air/domestic_routes.csv" }
  ],
  "facilities": [
    { "id": "health:hems:645", "name": "Raa Alifushi Health Center", "islandId": "MV006001",
      "categories": ["health_any", "health_centre"], "tier": "4_health_centre",
      "kind": "health", "precision": "island", "source": "data/external/health/_derived/public_health_facility_master.csv",
      "sourceDate": "2026-10-24", "reviewed": true }
  ],
  "categories": [
    { "id": "health_hospital", "label": "Hospitals (atoll, regional, tertiary)",
      "definition": "public_health_facility_master tier 1–3", "facilityCount": 0, "islandCount": 0,
      "confidenceNote": "Facility identity is official; location precision is island." }
  ]
}
```

Node ID convention: `island:<island_id>`, `stop:<stop_id>`, `airport:<iata>`.
Times are integer **minutes after midnight** in `Indian/Maldives` (UTC+5); arrival may
exceed 1440 only when next-day is explicitly requested.

`islands.geojson` is a `FeatureCollection` of polygons for the node islands only
(inhabited + airport islands), properties: `islandId`, `name`, `atoll`, `population`,
`status`, `isOrigin`, `lat`, `lon`. Simplify enough to keep the file under ~2 MB.

## 4. Router contract (`web/shared/routing`)

`types.ts` defines the public types. `router.ts` exports:

```ts
planJourney(network, request): Journey | null
planJourneyWithStatus(network, request): JourneyPlan   // { status, journey }
computeAccessibility(network, request): { perOrigin, summary }
applyScenario(network, scenario): MultimodalNetwork
createServiceFromPattern(network, routeId, newFirstDepartureMinute, id?): TimetabledService
```

`JourneyPlan.status` uses the same `OriginAccessStatus` as `OriginAccess`, so a single-origin
lookup can distinguish `no_destination`, `no_origin_access` and `not_reachable`.

```ts
interface JourneyRequest {
  originIslandId: string
  departureMinute: number              // 0..1439
  category: string                     // one category id
  includeEstimatedAir: boolean         // default true
  allowNextDay: boolean                // default false
  scenario?: Scenario
  maxJourneyMinutes?: number           // default 1440
}

interface Scenario {
  addedTrips?: TimetabledService[]
  cancelledServiceIds?: string[]
  delayMinutesByServiceId?: Record<string, number>
}
```

Journey output must include: origin/destination island, destination facility ids,
absolute arrival minute, elapsed minutes, per-leg mode/from/to/departure/arrival/wait/
ride, totals for access/wait/ride, number of transfers, `serviceConfidence`
(`verified` when every transit leg is timetabled and air is not used, otherwise
`estimated`), day offset, and a human-readable status.

Access statuses per origin: `reachable`, `not_reachable` (services exist but no itinerary
within horizon), `no_origin_access` (the origin island node has no incident fixed access/road
edge **and** no frequency service departing from it), `no_destination` (category has no
eligible facility).

`computeAccessibility` returns `perOrigin` keyed by island id and a summary with
`populationTotal`, `populationReachable`, `within60/120/240`, `unreachablePopulation`,
`noOriginAccessPopulation`, `noDestinationPopulation`, `coverage`,
`reachableVerifiedPopulation`, `reachableEstimatedPopulation`, and origin counts for each
status. The status populations plus `populationReachable` should reconcile with
`populationTotal` when a category has facilities.

### Router semantics (checklist for tests)

- Dijkstra over `(node, lastMode)` labels with earliest arrival; FIFO departure scan.
- Boarding buffer: ferry 15 min, air 45 min (60 at MLE). Alight: ferry 2, air 15.
- Transfer penalty: +10 min when the next board mode differs from the previous ride;
  +5 per boarding after the first. Staying aboard a timetabled trip costs nothing.
- Frequency services: generated departures; board the first departure ≥ ready + buffer.
- `allowNextDay` repeats the reference day at +1440 min exactly once and reports
  `dayOffset: 1`; default metrics never use it.
- Adding a trip cannot worsen earliest arrival; cancelling cannot improve it.
- Direct, same-vehicle intermediate stop, feasible/missed transfer, last departure,
  reverse direction and next-day cases must be covered by tests.
- `no_origin_access` is a coverage state, not a travel time.

## 5. Pipeline rules (`scripts/multimodal/build_network.py`)

- Canonical islands: `data/external/_derived/census2022_to_codab_crosswalk.csv`
  (`atoll_abbr` + `census_island` → `adm2_pcode`) plus the four Greater Malé island rows
  from `mdv_islands_master.csv` (`MV021001`, `MV021002`, `MV021003`, `MV009052`).
  Population and coordinates from `mdv_islands_master.csv` keyed by `adm2_pcode`.
- Alias matching: exact normalised key, then conservative phonetic/fuzzy match within the
  same atoll; every fuzzy row is written to `aliases.csv` with method and score and
  `reviewed=false`. Manual overrides for known cases (Malé, Hulhumalé, Villimalé,
  airport-only islands, `L.Gan`, `S.Hulhumeedhoo`, `Th.Veymandoo`, etc.).
  **Never silently merge an ambiguous name.**
- Stops: only `scheduled=yes` stops that are referenced by a trip; connect stop to its
  island with a same-island access edge (never across water). Access minutes: distance
  from island representative point to stop, 1.25 detour, 4.5 km/h; distances > 1.5 km use
  25 km/h local transport + 5 min wait (assumption, labelled).
- Airports: match `airports.csv` to an island (by `island` + atoll, with manual aliases).
  Access rules: same island → walk; airport-only island with a ferry stop on it → walk
  airport↔stop; Addu link road (GAN ↔ Feydhoo/Hithadhoo chain) and Laamu link road
  (KDO ↔ Fonadhoo/Gan L chain) → road edges; MLE/Hulhule ↔ Malé and Hulhumalé → road
  edges (Sinamalé Bridge); remaining airport-only islands → estimated speedboat to the
  nearest inhabited island (25 km/h, 10 min boarding, labelled assumption).
- Air services: use `domestic_routes.csv`; include `status` containing "operating"
  only in the default estimated layer; record excluded routes in the report. Treat each
  pair as bidirectional with `weekly_frequency_each_way` and `block_time_min`.
  `departuresPerDay = max(1, round(weeklyFrequency / 7))`; departures spread evenly over
  06:00–18:00. This is an assumption, recorded in `meta.assumptions`.
- Facilities: health from `public_health_facility_master.csv` (tier/category), education
  from `institutions_master.csv` (type/highest_grade/offers_grade_11_12). Map each to an
  island through the alias table; unresolved facilities are excluded from destination
  sets but counted in `report.json` and `aliases.csv`.
- Categories (exact ids):
  - `health_hospital` — tiers `1_tertiary`, `2_regional_hospital`, `2_general_hospital`,
    `2_hospital_other`, `3_atoll_hospital`, `3_atoll_hospital_small`
  - `health_regional_tertiary` — tiers starting `1_` or `2_`
  - `health_any` — every public health facility
  - `education_grade_11_12` — `offers_grade_11_12` true
  - `education_higher_ed` — campus/institute types excluding `preschool`, `school`,
    `higher secondary school`, `institute (Quran centre)`, `institution total (all campuses)`
  - `education_school` — `school` + `higher secondary school`
- GeoJSON: filter `data/external/hdx-cod-ab/extracted/mdv_admin2.geojson` to node islands,
  simplify (Douglas–Peucker, pure Python), round coordinates, keep file < 2 MB.
- Idempotent: same inputs → byte-identical JSON except `meta.generatedAt` (allow a
  `--generated-at` override for tests). No network access. No third-party dependencies
  beyond pandas (already available) and the standard library.
- Tests: `python -m unittest discover -s scripts/multimodal/tests -v` (also wire a copy
  or import into `tools/tests` if cheap) covering: all trip stops resolve; every trip
  time ordered; no access edge crosses islands; every airport has an access path; every
  service references known nodes; population total 447,420; origin count 191; category
  counts stable; alias review file contains every fuzzy match.

## 6. Web application

- Page `/` becomes the prototype: header with confidence badge, left control rail
  (origin, category, departure time, include air, threshold, scenario), map, journey card,
  national metrics, assumptions/coverage panel.
- Map: reuse Mapbox component when `NUXT_PUBLIC_MAPBOX_TOKEN` is set; otherwise render a
  functional schematic SVG map from the same GeoJSON (islands as polygons/circles, ferry
  route lines, airports, facilities) so the app is demonstrable in CI and without a token.
- Choropleth: travel time bands 0–30/30–60/60–120/120–240/240+ min, unreachable, no
  origin access — each visually distinct, never conflated.
- National metrics: population within 60/120/240 min for the selected category; coverage
  and confidence; scenario delta (population newly reachable / mean change).
- Journey card: legs with mode icons, departure/arrival, wait/ride/access breakdown,
  transfers, destination facilities, confidence, reference-day note, next-day alternative
  if requested.
- Scenario controls: add morning trip (route pattern + new first departure), cancel a
  service, delay a service by 30 min. Compare baseline vs scenario.
- No raw datathon data in `public/`; only the prepared artifacts above.
- TypeScript strict; `pnpm typecheck` and `pnpm build` must pass. Do not add a chart library
  or a second map library unless unavoidable.
- Accessibility: keyboard-operable selects, visible focus, labelled controls, text
  alternatives for colour-only information, responsive at 360 px.

## 7. Validation and acceptance

- Router tests (Node): pilot corridor Z2R18, add/cancel/delay, missed departure, last
  departure, reverse direction, same-vehicle intermediate stop, next day, air toggle,
  monotonicity, no-origin-access. Run with `node --experimental-strip-types --test`.
- CLI check: `web/scripts/check-routing.ts` prints national summary + pilot checks and
  exits non-zero on failure.
- Data tests (Python) as in §5.
- Web: `npm` (host lacks pnpm) may be used locally, but CI uses pnpm; keep package.json
  scripts compatible with both. Run `npm run typecheck`, `npm run build`, and the routing
  tests before claiming success.
- Manual pilot table in `VALIDATION.md`: direct journey, same-vehicle stop, missed
  transfer, last departure, reverse direction, next-day, and one scenario end-to-end,
  each with expected/actual values and the data source.
- Update `README.md`, `web/README.md`, `data/README.md` and `MULTIMODAL_DATA_READINESS_PLAN.md`
  status so they no longer say the simulator is unimplemented; keep the plan's caveats.

## 8. Ownership / write scopes

| Area | Owner | Writes |
|---|---|---|
| Contract, types, fixture, integration, docs, final checks | Lead | `MULTIMODAL_IMPLEMENTATION.md`, `web/shared/routing/types.ts`, `web/shared/routing/fixtures/**`, root docs, `README.md`, `web/README.md`, `data/README.md`, `VALIDATION.md` |
| Pipeline | `data-pipeline` | `scripts/multimodal/**`, `data/processed/multimodal/**`, `web/public/data/**`, tests under `scripts/multimodal/tests/**` |
| Router | `router` | `web/shared/routing/router.ts`, `web/shared/routing/scenario.ts`, `web/shared/routing/*.test.ts`, `web/scripts/**` |
| Web UI | `web-ui` | `web/app/**`, `web/nuxt.config.ts`, `web/app/assets/**` |
| Package scripts / CI | Lead after integration | `web/package.json`, `.github/workflows/**` |

Shared files (types, contract, package.json) are Lead-owned; ask before changing.
Teammates must not edit another area's files. Coordinate through the Lead. Report back
with: files changed, commands run + results, open issues, and anything the Lead must
integrate.

## 9. Definition of done

1. `network.json` + `islands.geojson` exist, validate, and are served by the app.
2. Router tests pass, including the pilot corridor numbers.
3. `pnpm/npm typecheck` and `pnpm/npm build` pass (or the exact blocking error is reported
   honestly — never claim a pass that was not run).
4. App works without a Mapbox token (schematic map) and with one (Mapbox layers).
5. National metrics, journey card, scenario delta and confidence/coverage panel render.
6. `VALIDATION.md` records the acceptance checks; README/status docs updated.
7. No raw data, credentials or caches added to the web bundle or commit.

### Outcome (24 October 2026)

1. **Met.** v1 artifacts exist, validate and are served (396,002 B network, 280,262 B GeoJSON); v2 sizes are in §10.7.
2. **Met.** 26/26 router tests and the real-data CLI pass, including the pilot corridor.
3. **Met.** Typecheck and build pass; see `VALIDATION.md` for commands and bundle size.
4. **Partially verified.** The token-free schematic path is verified. The Mapbox path
   typechecks/builds and its failure fallback was tested, but this host has no valid
   token, so the hosted basemap was not visually verified.
5. **Met.** Map, journey card, national metrics, scenario delta, confidence and coverage
   panel render in the built app.
6. **Met.** `VALIDATION.md`, `README.md`, `web/README.md`, `data/README.md` and status
   docs are updated.
7. **Met.** Only prepared artifacts are served; no raw CSVs, token or cache is committed.
   `package-lock.json` was removed after the local npm install.

See [`VALIDATION.md`](VALIDATION.md) for the manual acceptance table and limits.

## 10. Extension contract (v2, 24 October 2026)

The extension keeps the v1 network/artifacts compatible. New fields are optional; a v1
artifact still loads. The shared source of truth is `web/shared/routing/types.ts`.

### 10.1 Transport scope and route selection

`JourneyRequest` and `AccessibilityRequest` gain:

- `allowedModes?: ('land' | 'sea' | 'air')[]` — omitted means all modes. `land` covers
  `walk`/`road`; `sea` covers ferry services, `sea` frequency services and
  `speedboat`/`ferry_transfer` access; `air` covers air frequency services.
- `disabledRouteIds?: string[]` — timetabled `routeId` values and frequency service ids
  (`air:...`, `ferry:...`, user `scenario:...`).
- `disabledServiceIds?: string[]` — exact service ids; takes precedence.
- `includeEstimatedAir` remains accepted for v1 callers but is ignored when
  `allowedModes` is present. `includeEstimatedAir: false` without `allowedModes` is
  equivalent to removing `air`.

The router must rebuild its graph when the selection changes and apply the filter to
both access edges and services. An origin left without an outgoing edge because of the
filter is `no_origin_access` in the raw result; the UI labels it “not selected” when a
filter is active. Disabling a route may never improve an earliest arrival when all other
inputs are fixed; enabling it may never worsen it (monotonicity test with one route).

### 10.2 Intervention categories

Facilities may carry:

- `serviceCategories: string[]` — ids of the form `service:<category>`, also present in
  `facility.categories` so the router can use them as destination categories.
- `serviceEvidence: { category, detail, confidence, source, sourceDate }[]` — one row
  per service category, from the source CSV.
- `userAdded?: boolean`.

`CategoryDefinition` gains `kind: 'facility' | 'intervention'`, `group` and `source`.
Intervention categories are built only from evidence rows; no service is inferred from a
facility tier unless the row itself says so. Resort/guest-only rows are excluded and
counted in `meta.serviceData`.

Source files (read-only inputs):

- `data/external/health/services/diagnostics/diagnostic_services.csv`
- `data/external/health/services/specialist/specialist_services.csv`
- `data/external/health/services/dental/dental_services.csv`

Expected category ids: `service:<service_category>` (e.g. `service:lab_basic`,
`service:blood_bank`, `service:dialysis`, `service:dental`). A facility is one unique
`(normalised facility_name, islandId)` pair; merge evidence rows for the same pair.
Join island by normalised atoll + island name against the reviewed island master; if the
island cannot be resolved, exclude the row and count it. Preserve `confidence`,
`service_detail` and source URL/date. The facility geometry is the island centroid with
`precision: "island"`.

### 10.3 Scenario additions

`Scenario` gains `addedFacilities`, `addedServices` (including `FrequencyService` with
`mode: "sea"`) and `addedAccessEdges`. `applyScenario` appends clones; it must not mutate
the base network. A user-added sea/air frequency service uses island/airport nodes
directly and is routed with boarding/alighting buffers (sea = ferry buffers). A user
land link is an `AccessEdge` with `mode: "road"` and an explicit `assumption` basis. A
user facility must have a stable `scenario:facility:<id>` id, `userAdded: true`,
`precision: "island"`, and at least one existing category.

### 10.4 HDX/HeiGIT baseline

Add `web/public/data/heigit-baseline.json`, built read-only from
`data/processed/heigit/heigit_headline_adm0.csv` and `heigit_unit_summary.csv`. Schema:

```json
{
  "source": "HeiGIT/HDX ...",
  "method": "land/car-only isochrones; WorldPop",
  "warning": "Land-only benchmark. Not merged with the multimodal denominator.",
  "national": [{ "category": "education", "threshold": "5 km", "share": 46.92, "population": 207761 }],
  "units": [{ "admLevel": "ADM1", "name": "Addu", "category": "education", "within5km": 21.04 }]
}
```

Only publish values present in the source tables; do not interpolate. The UI shows the
national rows and the land-only/omitted-unit/WorldPop caveats.

### 10.5 QGIS publication export

`scripts/multimodal/export_qgis.py` writes `data/processed/multimodal/qgis/`:

- `islands.geojson` (polygon copy from `web/public/data/islands.geojson`)
- `facilities.geojson` (points, properties incl. categories, service categories)
- `ferry_routes.geojson` (LineString per timetabled service, ordered stops)
- `air_routes.geojson` (LineString per air frequency pair)
- `access_edges.geojson` (LineString with mode/minutes/confidence)
- `access_style.qml` (single QML style for the island layer; if a valid QML is hard to
  generate with stdlib, ship a small hand-written QML and document it)
- `README.md` (open the GeoJSON in QGIS, style, export, upload to Mapbox as a tileset)

The script is stdlib-only (no geopandas/GDAL dependency) and must be deterministic.
The web app continues to read `/data/multimodal.json` and `/data/islands.geojson`; QGIS
is an authoring/publication path, not a runtime dependency.

### 10.6 Checks for the extension

- `npm run test:routing` must include: land-only excludes ferries/air; disabled route
  removes only that route; baseline result unchanged when all modes/routes are enabled;
  added facility changes a category; added sea link changes a journey; added land link
  only when both endpoints are islands.
- `npm run check:routing` must print the mode presets and the intervention category count.
- Pipeline tests must cover resort exclusion, unresolved islands, duplicate
  facility/evidence merge, and the exact expected category counts.
- `npm run typecheck` and `npm run build` after UI integration.

### 10.7 Outcome (24 October 2026)

**Met, with the stated limitations.**

1. **Met.** `types.ts` and `router.ts` support `allowedModes`, `disabledRouteIds`/`disabledServiceIds`, intervention categories and scenario additions; the v1 fixture still passes.
2. **Met.** Pipeline emits 945 facilities / 48 categories; intervention reconciliation is in `report.json` (1,405 rows read, 12 resort, 7 unresolved, 107 duplicates merged, 444 facilities, 42 categories). 50 pipeline tests pass.
3. **Met.** Router tests cover land-only, disabled routes, baseline equivalence, added facility, added sea link and added land link; 38/38 pass; CLI prints presets and the intervention count.
4. **Met.** UI has presets/custom modes, a 49-ferry/31-air-pair route checklist, grouped intervention categories and panel, facility/sea/land simulator, HDX benchmark panel and QGIS link; typecheck/build pass.
5. **Met.** `export_qgis.py` writes deterministic GeoJSON/QML/README and the browser copy; `/data/qgis/index.html` is served. Mapbox remains an authoring path; the no-token schematic fallback is verified.
6. **Met.** HDX panel is labelled land/car-only, shows national and unit rows, explains WorldPop/omitted units, and is not merged into the multimodal denominator.

**Not verified on this host:** a real Mapbox token and a desktop QGIS session. The Mapbox code typechecks/builds and its failure fallback is exercised; QGIS layers are deterministic but not visually opened.
