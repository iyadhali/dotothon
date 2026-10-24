# Public-source verification for a Maldives facilities map and transport simulator

Research date: **24 October 2026**. This note distinguishes browsed first-party evidence from recommendations. Public pages may change. A listed API is not evidence that a complete extraction or reuse permission has been established.

## Finding

Both goals are feasible as a **facilities atlas plus timetable-based accessibility and scenario tool**. The most useful first version answers: "From this island, leaving at this time, which hospital or education service can I reach, and what changes if a ferry is cancelled or added?" A live fleet, passenger-demand, capacity, or congestion simulation needs additional operational data.

The architecture below is a recommendation based on the existing CSV inventory and the verified capabilities of the tools; it is not a claim that those pieces have already been integrated.

## Verified sources and their limits

| Need | First-party source and verified availability | Practical use and remaining work |
|---|---|---|
| National island geography | [MLSA National Mapping and GIS](https://www.mlsa.gov.mv/nationalmapping.php) describes OneMap as its authoritative national map and explicitly publishes the [island FeatureServer](https://services7.arcgis.com/yvCbn3q8PPtPLZIM/arcgis/rest/services/island_20240509/FeatureServer). The [island layer metadata](https://services7.arcgis.com/yvCbn3q8PPtPLZIM/ArcGIS/rest/services/island_20240509/FeatureServer/0) is readable and advertises polygon geometry and JSON, GeoJSON and PBF queries. | Strong candidate for island polygons and an island-name gazetteer. Fields include atoll, islandName, alternate name, category, usage, latitude and longitude. The layer has a 1,000-record limit and native EPSG:3857, so an extraction must handle paging and request/reproject to EPSG:4326. **A feature query and complete download were not verified in this session**: web query requests were unavailable and shell networking could not connect. Confirm reuse terms before redistribution. |
| Roads, jetties and candidate facility coordinates | [Geofabrik Maldives downloads](https://download.geofabrik.de/asia/maldives.html) lists OSM PBF, Shapefile and GeoPackage extracts, plus experimental vector tiles. | Reliable extraction path for the MVP; prefer a local dated PBF over repeated national Overpass queries. Completeness of each facility category must be audited against ministry lists. OSM absence means unknown coverage, not proof a facility does not exist. |
| Health facility identities and levels | The [Ministry health-facilities directory](https://health.gov.mv/en/health-facilities) lists named facilities and contacts. Its [December 2024 government facilities publication](https://health.gov.mv/en/publications/government-health-facilities-list-1) links a [readable PDF](https://health.gov.mv/storage/uploads/Vw9rVzYv/lcyhn3xt.pdf) with facility names, levels, registration numbers and operating licences. The [HEMS establishments directory](https://hems.health.gov.mv/establishments) is a public registry with status, ownership and level filters. | Use registration IDs and ministry names as the identity source, then match coordinates from OSM or manual verification. Exact coordinates, bed availability, opening hours and treatment capabilities were **not established** by these pages. HEMS rendered only a subset of detailed records in the retrieved view; do not claim all records were extracted. Do not equate licence class with verified emergency capability. |
| Schools and education coverage | The [Ministry schools page](https://www.moe.gov.mv/en/schools) publishes a named government-school directory and headline statistics. Its displayed update date is 23 May 2025. The [Ministry statistics publications index](https://projects.moe.gov.mv/dv/reports-and-publications?t=statistics) lists school-statistics reports. | Match names and atoll/island to the gazetteer and OSM; manually resolve duplicates. School level and courses matter: a primary school cannot substitute for an upper-secondary school or university. A nationwide coordinate download was not verified. |
| Island population | The [official Census 2022 results summary](https://statisticsmaldives.gov.mv/census-2022-results-summary/) links P3 (population by island, 2014–2022), P5 (island and sex, 2022), and usual-resident tables MG11/MG12. XLS and PDF links are present; XLS targets include [P3](https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2023/07/P3.xlsx) and [P5](https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2023/07/P5.xlsx). | Use an explicitly chosen resident-population denominator and retain the census year. The web tool cannot parse XLSX, so the files were not independently profiled here. Check the locally extracted population series against these source tables. Do not silently mix registered population with resident population or assign the full national total to administrative islands alone. |
| Ferries | The [RTL customer portal](https://www.rtl.mv/) exists, and [MTCC schedules](https://mtcc.mv/schedules-2/) is an official timetable index in search results. Published official PDFs include [Lhaviyani schedules](https://mtcc.mv/wp-content/uploads/2024/07/LH-RTL-Revised-Schedules.pdf). | Use the local dated RTL CSVs as a starting snapshot and validate service weekdays, effective dates, holidays, Friday variations and missing areas against operators. RTL returned no readable text in this browser; MTCC's index returned 403 on direct fetch. **No public RTL GTFS, GTFS-Realtime feed or supported transport API was verified.** Search failure is not proof none exists. |
| Airports | [OurAirports downloads](https://ourairports.com/data/) offers airports and runways CSVs, a data dictionary, nightly updates and public-domain terms. | Filter airports by `iso_country=MV`, preserve airport types and validate operational status. This provides coordinates, not a domestic flight schedule. Existing passenger/movement statistics must not be converted into scheduled passenger connections without separate evidence. |

The [OneMap app](https://www.onemap.mv/) loads as a JavaScript application with no readable text in this tool. The separate OneMap README site timed out. The FeatureServer metadata is the concrete geography finding; avoid describing the whole OneMap platform as an audited open-data API.

An extraction candidate, **not a successfully executed query in this session**, is:

```text
GET https://services7.arcgis.com/yvCbn3q8PPtPLZIM/ArcGIS/rest/services/island_20240509/FeatureServer/0/query
  ?where=1%3D1
  &outFields=OBJECTID,atoll,islandName,category,Usage
  &returnGeometry=true
  &outSR=4326
  &resultOffset=0
  &resultRecordCount=1000
  &f=geojson
```

Verify pagination support and compare returned IDs/counts before declaring national completeness. Keep the other available national geometry sources in the inventory as fallbacks, but inspect their actual layers and geometries: an ADM1/ADM2 boundary level is not automatically a complete set of inhabited-island land polygons.

## Software options verified against official documentation

**MapLibre GL JS** is a TypeScript/WebGL browser map renderer. It provides the suitable base for clickable facilities, island colouring, transport lines and layer controls. Start with small local GeoJSON assets and native map layers. Select a basemap separately; the renderer does not itself supply the underlying imagery or road tiles. [MapLibre introduction](https://maplibre.org/maplibre-gl-js/docs/)

**deck.gl is optional**. Its TripsLayer animates paths with timestamps, and its official guide documents MapLibre integration. Use it only if animation improves the demo; the small ferry network can also be animated with native map layers. Movement interpolated from schedules must be labelled **scheduled playback**, not observed vessel locations. Pin mutually compatible library versions when implementing. [TripsLayer](https://deck.gl/docs/api-reference/geo-layers/trips-layer), [MapLibre integration](https://deck.gl/docs/developer-guide/base-maps/using-with-maplibre)

**GTFS Schedule** can represent bus and ferry routes, ordered stop-times, service calendars and minimum transfer times. A usable conversion requires agency/stops/routes/trips/stop_times plus the applicable calendar or calendar_dates records; ferry is route type 4 and bus is type 3. Missing weekdays cannot be repaired by silently assuming daily operations. [GTFS reference](https://gtfs.org/documentation/schedule/reference/)

**OpenTripPlanner** consumes GTFS transit data and OSM PBF street data, and runs as a Java server. It is a credible subsequent routing backend when the feed and street-to-stop links are clean, but does not solve missing timetables or inconsistent island identities. Its deployment and graph-building work are extra tasks for a short datathon. [OTP basic tutorial](https://docs.opentripplanner.org/en/latest/Basic-Tutorial/)

**RAPTOR** is a timetable routing algorithm that considers arrival time and transfers, and supports dynamic scenarios without preprocessing. It is an algorithm to implement or adopt, not a turnkey Maldives transport feed. For this small network, a simple earliest-arrival connection scan or a time-expanded graph is also a reasonable first implementation. [Original RAPTOR paper, Microsoft Research](https://www.microsoft.com/en-us/research/publication/round-based-public-transit-routing/)

## Recommended MVP

1. **Create a canonical island table.** Give each island an internal stable ID; retain atoll, source IDs, English/Dhivehi aliases and population definition/year. Review ambiguous matches explicitly rather than accepting fuzzy matches automatically.
2. **Create a facility table.** Retain source registration ID, category, service level, island ID, coordinate, coordinate precision, source URL, source date and verification status. A point at an island centre must display "island-level location" rather than imply a precise building address.
3. **Create a dated service snapshot.** Convert the 102 locally profiled ferry trip patterns to ordered adjacent legs; preserve route and trip identity. Resolve calendars for a pilot region. Unscheduled island pairs remain a separate candidate network, excluded from the confirmed timetable baseline.
4. **Route by departure time.** Include access to the jetty, actual departure, wait, in-vehicle time, transfer buffer and final access to the facility. A passenger who misses the last boat must not be routed onto an imaginary immediate return. Keep an explicit search horizon and separate "unreachable under this scenario" from "data unavailable".
5. **Show comparison results.** Let a user cancel one trip/route, delay departures, add a hypothetical connection, or enable/disable a facility. Recalculate arrival time, transfers, people within a chosen threshold, and islands losing access. Report the number of included population records and unsupported islands alongside every population-share metric.
6. **Use one simple delivery stack.** Python/pandas/GeoPandas for ETL and validation; a Vite TypeScript app with MapLibre for the map; an in-memory routing module or small Python API for queries. Persist clean CSV/GeoJSON/JSON snapshots first. A spatial database and OTP can follow when scale or multiuser editing warrants them. QGIS remains useful for checking geometry and producing exported analysis maps.

For a datathon, a defensible regional ferry-plus-walking pilot is stronger than a nominal nationwide road/sea/air graph built from guessed calendars. The atlas can show national coverage while the simulator clearly marks the subset with usable timetables.

## Publication details to preserve

OSM is licensed under ODbL and requires attribution; check obligations for redistributed derived databases. [OSM copyright](https://www.openstreetmap.org/copyright)

The standard OSM tile service has capacity and caching requirements and prohibits bulk downloading for offline use. Use a suitable tile provider or self-hosted assets when an offline demo is required. [OSMF tile policy](https://operations.osmfoundation.org/policies/tiles/)

Keep the original source and extraction date on each data layer. Public page visibility alone does not establish reuse terms for ministry or operator datasets. No sensitive ride-level coordinates need to be published to demonstrate island accessibility.
