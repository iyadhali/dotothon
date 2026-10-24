# Local research datasets

Raw datasets are not bundled with the web prototype. Existing public-source files already versioned in this repository are preserved separately.

Start with the [official MBS datathon releases](https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases). Extract the datasets into the paths described in [the agent catalogue](../tools/data-catalogue.json). Relevant local layouts are `team-kandu/`, `MACL/MACL/`, `MTCC/`, `Avas_Ride/` and `FollowMe/FollowMe_august_2025/`.

Additional public-source paths and research references are described in the catalogue and [research notes](../research/04_build_feasibility.md). Do not assume availability of a public download means every field is accurate, complete or licensed for redistribution. Review source terms before committing derived data.

An agent can inspect the catalogue without downloading anything:

```powershell
python tools/data_mcp.py --call data_list_datasets
```

Files absent on a new checkout are reported as unavailable. `data_describe_dataset` and `data_sample_rows` inspect locally supplied files only. No raw data is automatically copied into `web/public/`.

## Prepared multimodal artifacts

The prototype does not read the raw CSVs at runtime. `scripts/multimodal/build_network.py`
builds the network/intervention artifacts; `build_hdx_baseline.py` extracts the HDX
benchmark; `export_qgis.py` writes the QGIS layers (pandas + standard library, no
network access):

| Path | Contents |
|---|---|
| `processed/multimodal/network.json` | Canonical islands, stops, airports, access edges, services, 945 facilities, 48 categories (6 base + 42 intervention) and metadata |
| `processed/multimodal/islands.geojson` | 200 island polygons / representative points |
| `processed/multimodal/aliases.csv` | 818 join decisions: 512 exact, 56 fuzzy, 122 manual, 128 unresolved |
| `processed/multimodal/report.json` | Build counts, exclusions, intervention reconciliation, coverage and assumptions |
| `processed/multimodal/qgis/` | Islands, 945 facilities, 102 ferry routes, 31 air pairs, 153 access edges, QML style and README |
| `../web/public/data/multimodal.json` + `islands.geojson` | Byte-identical browser artifacts served by the app |
| `../web/public/data/heigit-baseline.json` | 34 national + 43 unit HDX/HeiGIT land-only rows (no interpolation) |
| `../web/public/data/qgis/` | Published QGIS GeoJSON/QML export and `index.html` |

Inputs used: `data/external/_derived/mdv_islands_master.csv`,
`census2022_to_codab_crosswalk.csv`, `census2022_population_by_island.csv`,
`data/team-kandu/rtl_stops.csv`, `rtl_trips.csv`, `rtl_routes.csv`,
`data/external/air/airports.csv`, `domestic_routes.csv`,
`data/external/health/_derived/public_health_facility_master.csv`,
`data/external/education/institutions_master.csv`,
`data/external/health/services/diagnostics/diagnostic_services.csv`,
`.../specialist/specialist_services.csv`, `.../dental/dental_services.csv`,
`data/hdx-heigit-access/MDV_*.csv`, and
`data/external/hdx-cod-ab/extracted/mdv_admin2.geojson`.

```bash
python3 scripts/multimodal/build_network.py
python3 scripts/multimodal/build_hdx_baseline.py
python3 scripts/multimodal/export_qgis.py
python3 -m unittest discover -s scripts/multimodal/tests -v
```

The 128 unresolved aliases (120 education, 8 health) and 50 zero-category base
facilities are excluded from the served list and remain in `report.json` for review.
The intervention layer reads 1,405 service rows, excludes 12 resort/guest-only rows
and 7 unresolved islands, merges 107 duplicates and serves 444 facilities/42
categories; the exact reconciliation is in `report.json`. Do not serve raw CSVs from
`web/public/`; the app only needs the prepared artifacts above. See
[`../VALIDATION.md`](../VALIDATION.md) for counts and limitations.
