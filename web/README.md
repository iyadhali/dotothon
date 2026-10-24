# Island Access Atlas — web prototype

Nuxt + Vue + TypeScript prototype for reference-day multimodal access in the
Maldives. It combines a recorded RTL ferry snapshot, an estimated domestic-air
frequency layer, explicit island/airport access links, 48 health/education/intervention
categories, selectable land/sea/air modes and specific routes, a timetable-aware router,
facility/route/link simulators, an HDX land-only benchmark and a QGIS export.

It is an accessibility model, **not** a demand forecast or fare calculator. Read
[`../VALIDATION.md`](../VALIDATION.md) for the verified numbers, manual acceptance
table and limitations, and [`../MULTIMODAL_IMPLEMENTATION.md`](../MULTIMODAL_IMPLEMENTATION.md)
for the build contract.

## Run locally

Requirements: Node 24+ (the package declares `>=24`; the prototype also runs on
Node 22 with an `EBADENGINE` warning), npm or pnpm. Python 3 for the separate data
pipeline and agent tools.

```bash
npm install
cp .env.example .env      # optional; add NUXT_PUBLIC_MAPBOX_TOKEN
npm run dev               # http://127.0.0.1:3000
```

Without a token the app renders a functional **schematic map** built from
`public/data/islands.geojson` and makes no Mapbox requests. With a token it uses the
Mapbox polygon choropleth; if the style or WebGL fails it falls back to the schematic
and shows a notice. Never put a secret token in public runtime configuration.

```bash
npm run db:build
npm run db:check
npm run test:db
npm run typecheck
npm run test:routing
npm run check:routing
npm run build
npm run preview
```

Run `typecheck` and `build` **sequentially**; concurrent runs race Nuxt's `.nuxt`
cache and can produce a spurious blank build failure. CI uses pnpm and Node 24.

## What is on the page

- **Header:** product name, reference-day and "calendar unverified" badges, confidence legend.
- **Controls:** searchable 191-island origin picker grouped by atoll; grouped destination
  category (health, education, diagnostics/procedures, specialist services, dental) with
  facility/island counts; departure time; 60/120/240-minute threshold; network preset
  (all modes / no air / land only) plus custom Land/Sea/Air toggles; and a searchable
  49-ferry-route / 31-air-pair checkbox list with all/none.
- **Network filter:** excludes selected routes from the graph; a `not_selected` state
  is distinct from no infrastructure and the banner explains the user choice.
- **Map:** travel-time bands (0–30, 30–60, 60–120, 120–240, 240+), not-selected,
  unreachable, no-origin-access and no-destination states, ferry routes split
  verified/estimated, estimated sea routes, airports, facility dots, click/keyboard
  origin selection.
- **Journey card:** every leg with mode, departure/arrival, wait/ride/access/transfer
  minutes, confidence, destination facilities, reference-day note, and an optional
  next-day alternative only when same-day is unreachable.
- **National metrics:** residents within 60/120/240 minutes, reachable/unreachable/
  no-origin-access counts, origin coverage and verified/estimated evidence mix.
- **Network controls:** presets and custom modes plus the route checklist; "not selected"
  is shown separately from missing infrastructure.
- **Intervention coverage:** diagnostic/specialist/dental service categories, with
  facility claims, operating type, confidence, source date and reachability from the
  selected origin; resorts are excluded upstream.
- **Simulator:** add a facility (name, type, island, category), add a sea route or a
  land link, alongside the existing add-trip/cancel/delay timetable scenarios; the map,
  bands, journey card, national metrics, newly covered origins and scenario delta update.
- **HDX comparison:** land-only HeiGIT numbers (national + unit rows) shown as a labelled
  benchmark, not merged into the multimodal denominator.
- **Scenario comparison:** baseline vs user scenario, including changed origins and
  population delta.
- **Coverage & assumptions:** population scope, island-level facility precision,
  reference-day rule, artifact counts, model assumptions, intervention reconciliation
  and coverage notes.
- **QGIS/Mapbox footer:** links the published QGIS export; Mapbox Studio is
  publication-only, not a runtime dependency.

## Data and read API

The prepared JSON is the source of truth; `npm run db:build` compiles it into a
read-only SQLite database at `server/assets/maldives.sqlite`. Nitro serves that file as
a server asset, copies it to a writable temp directory on first use, and opens it with
`node:sqlite` (`DatabaseSync`, read-only). The API is:

| Route | Returns |
|---|---|
| `/api/network` | Full `MultimodalNetwork` (same shape as `public/data/multimodal.json`) |
| `/api/islands` | GeoJSON `FeatureCollection` of the 200 islands |
| `/api/hdx` | HDX/HeiGIT benchmark object (same shape as `public/data/heigit-baseline.json`) |
| `/api/health` | Liveness + database schema/counts; 503 when the DB is unavailable |

The page tries the API first, then the static files, then the bundled fixture. The
header says which source is active (`SQLite API`, `Static fallback`, `Fixture data`).
If the DB is missing/corrupt the API returns 503 and the static path is used; no data
is silently replaced.

Artifacts:

- `public/data/multimodal.json` — 200 islands, 191 origins, 117 ferry stops, 20 airports,
  102 ferry trips, 62 estimated air services, 153 access edges, 945 facilities,
  48 categories; 1,120,880 B.
- `public/data/islands.geojson` — 200 island polygons / representative points.
- `public/data/heigit-baseline.json` — HDX/HeiGIT land-only benchmark.
- `public/data/qgis/` — QGIS GeoJSON/QML export and `index.html`.
- `server/assets/maldives.sqlite` — generated serving DB (gitignored, ~2.3 MB).

The source of truth is `../scripts/multimodal/build_network.py` (plus
`build_hdx_baseline.py` and `export_qgis.py`); it writes
`../data/processed/multimodal/*` and copies the browser artifacts. See
[`../data/README.md`](../data/README.md). `scripts/build-db.ts` validates fixed counts
and deep parity before replacing the DB; `scripts/db.test.ts` covers build, parity,
tamper rejection and missing-input handling.

## Code map

| Path | Purpose |
|---|---|
| `app/pages/index.vue` | Page composition and page-level state |
| `app/components/` | Header, control rail, network controls, map panel, schematic/Mapbox maps, legend, journey card, national metrics, scenario comparison, intervention/HDX/simulator panels, coverage panel |
| `app/composables/useMultimodal.ts` | Loads artifacts, debounces metrics, plans journeys, computes scenarios |
| `app/plugins/routing-engine.client.ts` | Registers the router in the UI's late-binding engine boundary |
| `app/utils/` | Bands (incl. `not_selected`), engine boundary, selection presets, category groups, formatting, GeoJSON/routes helpers |
| `shared/routing/types.ts` | Network/journey/accessibility contract |
| `shared/routing/router.ts` | Timetable-aware Dijkstra, accessibility and scenarios |
| `shared/routing/router.test.ts` | 38 router unit tests (pilot, boundary, reverse, next-day, air toggle, mode/route filters, additions, monotonicity) |
| `scripts/check-routing.ts` | Real-data invariants, national summary and pilot table |
| `scripts/build-db.ts` | Builds/validates the read-only SQLite asset from prepared JSON |
| `scripts/sqlite-schema.sql` | Database schema (`user_version=1`) |
| `scripts/db.test.ts` | Builder, parity, tamper and missing-source tests |
| `server/utils/database.ts` | Server-asset materialisation, read-only `node:sqlite` access |
| `server/api/network.get.ts` | SQLite-backed network API |
| `server/api/islands.get.ts` | SQLite-backed GeoJSON API |
| `server/api/hdx.get.ts` | SQLite-backed HDX benchmark API |
| `server/api/health.get.ts` | Health endpoint with database schema/counts |

## Modelling rules visible in the UI

- The RTL snapshot has no service calendar: every recorded trip is assumed to operate
  on the reference day (10 October 2026). This is labelled on the page.
- Waiting uses the **next actual departure**, never half the departure interval, for
  infrequent ferries. Staying aboard the same trip pays no new boarding buffer.
- Air and sea-frequency services are estimated layers (weekly frequency → generated
  departures); estimated legs are labelled and can be excluded by mode/route.
- Network selection is a user scenario: excluding a route does not erase physical
  infrastructure, and removed access appears as `not_selected`, never as zero demand.
- Facility access is island-level; intervention claims are evidence records, not a
  confirmation that a service is open, staffed or bookable.
- Missing data appears as `unreachable` or `no origin access`, never as zero demand.

## Known limits

- No Mapbox token on this host, so the hosted basemap was not visually verified; the
  schematic path is verified and the Mapbox failure fallback is tested.
- No Kaafu/Zone 3 ferry stops in the local RTL snapshot; Malé is reachable only via
  air or the bundled Malé–Vilimalé frequency model.
- 67 origins have no fixed access/frequency service; 128 aliases remain unresolved
  (120 education, 8 health) and are excluded from the served base facility list.
- 444 intervention facilities and 42 service categories come from diagnostic,
  specialist and dental evidence tables; 12 resort/guest-only rows and 7 unresolved
  islands are excluded and listed in `report.json`.
- Fares, demand, capacity and 2SFCA are out of scope; seaplanes, charters and emergency
  services are excluded.
- The old `app/components/MaldivesMap.client.vue` starter component is unused.

References: [Nuxt](https://nuxt.com/docs/4.x/getting-started/introduction),
[Nuxt UI](https://ui.nuxt.com/docs/getting-started/installation/nuxt),
[Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/).
