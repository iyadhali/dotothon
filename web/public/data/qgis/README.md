# Multimodal Maldives QGIS export

Generated from `data/processed/multimodal/network.json` and `islands.geojson`.
CRS: EPSG:4326 (WGS 84). Coordinates are island centroids for facilities and
island access, not building locations.

Layers:
- `islands.geojson` — 200 node islands (inhabited + airport-only).
- `facilities.geojson` — 945 island-precision facilities
  (444 intervention layer).
- `ferry_routes.geojson` — 102 recorded RTL trips.
- `air_routes.geojson` — 31 operating domestic airport pairs
  (directed services are collapsed to one line per pair).
- `access_edges.geojson` — 153 same-island, link-road and
  airport speedboat access edges.
- `access_style.qml` — categorized line style by `mode`.

Caveats: RTL records one reference day, not a full calendar. Domestic air
departures are estimated frequencies, not observed schedules. Seaplane and
resort water-aerodrome services are excluded. Facility categories are
island-level evidence, not confirmed clinical services.
