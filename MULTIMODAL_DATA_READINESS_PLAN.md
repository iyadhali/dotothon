# Multimodal data readiness and implementation plan

Prepared **24 October 2026**, based on the local data inventory and research available at that date.

## Objective and current scope

Prepare a defensible Maldives network for resident journeys combining walking/road access, scheduled ferries and domestic flights, then calculate access to selected facilities and compare transport scenarios.

**Enough data exists to start a prototype. The main gap is reliable connections between modes, not additional map layers.** This document plans future work; the implemented web application remains a basic Nuxt, Nuxt UI and Mapbox scaffold. Saving this plan does not expand that implementation scope.

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
