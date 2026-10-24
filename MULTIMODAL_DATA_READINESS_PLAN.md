# Multimodal data readiness and implementation plan

Prepared **24 October 2026**, based on the local data inventory and research available at that date.

## Objective and current scope

Prepare a defensible Maldives network for resident journeys combining walking/road access, scheduled ferries and domestic flights, then calculate access to selected facilities and compare transport scenarios.

**Enough data exists to start a prototype. The main gap is reliable connections between modes, not additional map layers.** This document plans the work; the implementation described in [`MULTIMODAL_IMPLEMENTATION.md`](MULTIMODAL_IMPLEMENTATION.md) is now built. It covers the reference-day ferry snapshot, an estimated domestic-air layer, island access links, 48 health/education/intervention categories, selectable land/sea/air modes and routes, timetable-aware routing, facility/route/link simulation, an HDX land-only benchmark and a QGIS export. The remaining gaps below are still gaps: there are no verified service calendars, flight departure times or building-level facility locations. See [`VALIDATION.md`](VALIDATION.md) for what was verified and what was not.

## Available foundation

- An island/census master and source crosswalks in `data/external/_derived/`.
- OSM road geometry and candidate facility, harbour and airport locations.
- Official health and education identities and island-level facility registers.
- Ferry stop coordinates and a reference stop-time snapshot in `data/team-kandu/`.
- Airport locations, inferred airport catchments and estimated domestic air connections.
- Air-fare records and parsed ferry tariff tables.

Important findings from the local files:

| File | Finding | Consequence |
|---|---|---|
| `data/external/air/domestic_routes.csv` | All 40 route records are marked `estimated=yes`. | Suitable for an explicitly estimated connectivity model; not a verified weekly timetable. |
| `data/external/air/airport_catchment.csv` | 191 island records, inferred access modes and straight-line distances. | Replace inferred access with actual road/ferry/speedboat connections where available. |
| `data/external/health/_derived/public_health_facility_master.csv` | Facility identities and islands; no coordinate columns. | Building-level access still needs geocoding and validation. |
| `data/external/education/institutions_master.csv` | Institutions/campuses and island information; no coordinate columns. | Distinguish an island-level location from a verified building or entrance. |
| `data/external/fares/air_fares.csv` | 186 of 248 records have low confidence. | Fare data exists, but cheapest-route and affordability results require validation. |
| `data/external/fares/sea_land_sources/rtl_gazette_fares_parsed.csv` | Parsed tariffs include publication dates and cancellation fields. | Resolve effective tariffs rather than treating every historical record as current. |

These paths describe local datasets; this plan does not upload them to GitHub.

## Prioritized gaps

| Priority | Required work | Deliverable |
|---|---|---|
| 1 — service calendars | Verify ferry operating weekdays, exceptions and missing Zone 3 coverage. Obtain complete flight departure/arrival schedules and validity dates. | Dated, directed services with stop-times, operating calendars, exceptions and provenance. |
| 2 — transfers | Verify island–jetty, jetty–airport, airport–town and terminal connections, including boarding/check-in allowances. | Explicit transfer/access links with mode, duration, availability and confidence. |
| 3 — facility coordinates | Match official health, school and campus records to actual buildings or entrances. | Facility coordinates with precision and verification fields; unresolved records remain visibly approximate. |
| 4 — identifiers | Link stop codes, airport IATA codes and facility IDs to canonical island identifiers. | Reviewed crosswalks and a queue of unresolved/ambiguous joins. |
| 5 — fares | Validate effective dates, cancelled tariffs, passenger categories and estimates. | Applicable fare rules with currency, category, source date and confidence. |
| 6 — validation | Check representative end-to-end journeys against operator information. | Documented itinerary checks and a reproducible validation set. |

Collecting a week of observed flights improves coverage but does not replace published service calendars. Preserve the distinction between scheduled and observed movements, and between active, ceased and hypothetical services.

## Implementation sequence

1. **Choose a reviewed pilot corridor.** Include an inhabited origin, its jetty/airport access, a domestic flight where applicable, onward transport and a verified destination facility. Compare local/regional alternatives. Obtain the full weekly schedule for this corridor first.
2. **Reconcile identifiers.** Reuse the island master and existing crosswalks. Assign canonical IDs to transport stops, airports and facilities; manually review uncertain aliases instead of silently accepting fuzzy matches.
3. **Normalize transport services.** Preserve direction, trip identity, departure/arrival times, calendar validity and source confidence. Use `Indian/Maldives` (UTC+5). Keep incomplete or hypothetical services separate from the verified baseline.
4. **Build physical access and transfer links.** Turn the road geometry into a routable walking/road graph, check connected components, and connect real terminals and entrances. Prevent proximity-based links from jumping across water. Verify transfers or expose clearly labelled configurable assumptions.
5. **Locate eligible destinations.** Retain facility category, service level, operating status and location precision. Distinguish primary care, hospitals, school grades and higher-education campuses. If hours or capabilities are unknown, report physical access to a listed facility rather than confirmed service availability.
6. **Implement timetable-aware routing.** Calculate elapsed journey time including access, waiting, travel, transfers and final access. Do not substitute half the departure interval for timetable-based waiting on infrequent services. Preserve staying aboard the same vehicle, missed departures and overnight/service-day boundaries.
7. **Validate, then expand.** Check the pilot against known journeys before extending nationally. Add verified fares after time-based journeys work.

## Initial modelling defaults

- Model resident travel by walking/road access, scheduled ferries and domestic flights.
- Minimize elapsed time first. Add fare-based alternatives separately.
- Do not automatically treat resort seaplanes, charters or emergency transport as ordinary resident services; verify eligibility and booking constraints.
- Separate verified services, estimates and user-created scenarios in both the data and interface.
- Distinguish missing coverage from no journey found under a complete model.
- Use a stated, non-overlapping population denominator for accessibility statistics.

QGIS can help inspect and prepare geographic layers, but it is not required to run the Mapbox application or build the routing engine.

## Pilot acceptance checks

- Every included stop, airport and destination has a reviewed island identity and location precision.
- Every baseline service has either a verified calendar or an explicit reference-day assumption visible in results.
- Every mode change includes a physical connection and a documented transfer/boarding allowance.
- Validate direct journeys, same-vehicle intermediate stops, feasible and missed transfers, last departures, reverse-direction journeys and next-day behaviour.
- Adding a service cannot worsen earliest arrival with other inputs fixed; removing one cannot improve it.
- Report coverage and confidence alongside journey/accessibility results. Never invent departures to complete the national map.

## Additional data for operational simulation

Predicting passenger loads, queues, capacity shortages, congestion or operating feasibility requires additional real demand/OD data, vehicle capacities, fleet assignments, turnaround constraints, and observed delays/cancellations. Weather and disruption information can support later reliability scenarios.

MTCC passenger figures are synthetic and must not be used as evidence of observed demand. A routing/accessibility prototype can proceed before these operational inputs are obtained, provided its assumptions are explicit.

## Supporting research

- [Build feasibility and routing recommendations](research/04_build_feasibility.md)
- [Air network methods and limitations](research/07_air_network.md)
- [Healthcare data gaps](research/05_healthcare_data.md)
- [Education data gaps](research/06_education_data.md)
- [Air fares and confidence](research/12_air_fares.md)
- [Earlier accessibility plan](MULTI_MODAL_ACCESSIBILITY_PLAN.md)
- [Boilerplate setup and stack decisions](web/README.md)

**Next acquisition:** a complete weekly timetable for the selected pilot corridor, followed by verified terminal locations and transfer times. Network structure and identifier reconciliation can proceed while these inputs are obtained.

## Extension plan (24 October 2026): selectable modes, interventions and simulation

### Why this extension

The HeiGIT/HDX layers map education and primary-healthcare accessibility with a **land/car-only** model. They are a useful published benchmark, not a multimodal network: they cannot use ferries or domestic flights, omit units with no coverage, and allocate WorldPop population rather than Census 2022 origin populations. The prototype must therefore (a) show the land-only benchmark explicitly, (b) let the user choose the transport scope, and (c) make service availability, not just facility presence, selectable.

### Design requirements

1. **Transport scope is a first-class input.** Add `allowedModes` (`land`, `sea`, `air`), and route/service exclusions to journey and accessibility requests. Presets: *Multimodal* (land+sea+air), *Land + sea* (no air), *Land only* (HeiGIT-like, road/walk only). The filtered graph must rebuild; an origin unreachable only because a mode is switched off is reported as *not selected*, not as missing infrastructure.
2. **Routes are selectable.** The UI lists ferry routes (49) and estimated air pairs (31), initially all enabled; unchecking a route removes its services from the graph and marks results `network_filter` in the interface. Access edges follow the mode filter.
3. **Interventions are data, not code.** Extend categories with intervention categories built from the health-service evidence CSVs:
   - `data/external/health/services/diagnostics/diagnostic_services.csv` (396 rows; 11 categories incl. lab_basic, blood_bank, xray, ultrasound, ct, mri, mammography, endoscopy, histopathology, pcr_molecular, lab_advanced);
   - `data/external/health/services/specialist/specialist_services.csv` (787 rows; 30 categories incl. dialysis, cardiology, oncology, maternity, emergency);
   - `data/external/health/services/dental/dental_services.csv` (222 rows).
   Resort/guest-only clinics are excluded from resident access. Each service facility carries confidence, evidence and source date; selecting an intervention shows the facilities that claim it and the selected origin's access to those islands. Tier-inferred rows stay labelled.
4. **Simulation is extensible.** Scenario overlays may add:
   - a facility (school, health centre, hospital, or a facility with selected intervention tags);
   - a land link (road/bridge minutes between two islands) or a scheduled/frequency sea link between two island nodes;
   - a new service (frequency sea link or extra timetabled ferry trip), plus the existing cancel/delay controls.
   The scenario recomputes the map and metrics and reports newly covered population/origins, changed origins, and the assumption behind the addition.
5. **QGIS → Mapbox publication.** The pipeline exports stable GeoJSON layers (islands, facilities, ferry routes, air routes, access edges) plus a QML style and a short QGIS/Mapbox workflow. QGIS remains optional desktop tooling; the web app reads the same published GeoJSON.
6. **HDX comparison.** Add a side-by-side panel showing HeiGIT national shares (education ≤5 km 46.92%; hospitals ≤60 min 45.24%; primary healthcare ≤60 min 38.51%) and its land-only/omitted-unit caveats. Do not merge HeiGIT populations or polygons into the multimodal denominator.

### Phases

| Phase | Work | Owner | Acceptance |
|---|---|---|---|
| P1 | Contract/types: `TravelMode`, mode/route filters, intervention categories, scenario additions, HDX baseline types | Lead | `types.ts` compiles; fixture remains valid |
| P2 | Pipeline: intervention facilities/categories, service evidence, HDX baseline JSON, QGIS export; tests | data-pipeline | 37+ tests pass; artifacts validate; resort rows excluded |
| P3 | Router: filtered graph, mode/route exclusions, added facilities/links/services; tests | router | Existing 26 tests pass plus new filter/scenario tests; no regression |
| P4 | UI: mode presets + route checklist, intervention category group + facility panel, simulator forms, HDX panel, QGIS links | web-ui | Typecheck/build; controls update map, journey, metrics; impact visible |
| P5 | Integration: regenerate artifacts, docs (`README`, `web/README`, `data/README`, `VALIDATION`), final checks | Lead | All checks green; docs describe the extension |

### Acceptance additions

- Land-only preset reproduces a no-ferry/no-air graph; switching modes changes coverage and explains why.
- Disabling a route removes only its services; enabling it cannot worsen earliest arrival with other inputs fixed.
- Each intervention category resolves to facilities with evidence; no facility is assigned a service without a source row; resort rows are excluded and counted.
- Adding a facility or link produces a computable delta and a labelled assumption; no invented timetables.
- QGIS export opens as layers; Mapbox path still falls back without a token.
- HDX comparison is labelled land-only, with its omitted-unit and population caveats visible.

### Implementation status (24 October 2026)

All five phases are implemented and validated in this checkout:

- **P1:** `web/shared/routing/types.ts` carries modes, filters, intervention categories and scenario additions; the v1 fixture remains valid.
- **P2:** pipeline emits 945 facilities / 48 categories (501 base + 444 intervention), 1,405 service rows reconciled (12 resort and 7 unresolved excluded, 107 duplicates merged), 50 tests; HDX JSON and QGIS export published.
- **P3:** router supports mode presets, route/service exclusions, added facilities/sea links/land links and timetable scenarios; 38 tests plus a 106-check CLI.
- **P4:** the UI exposes network presets/custom modes, a 49-ferry/31-air-pair route checklist, grouped intervention categories and coverage panel, facility/sea/land simulator, HDX panel and QGIS links; typecheck/build pass.
- **P5:** artifacts regenerated and published; `README.md`, `web/README.md`, `data/README.md` and `VALIDATION.md` describe the extension; final checks green.

See [`VALIDATION.md`](VALIDATION.md) for numbers, manual acceptance checks and limits.
