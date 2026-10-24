# Research and data preparation scripts

These are research utilities, not application runtime code. They inspect, fetch, clean and join datasets used by the Maldives mobility research. Some scripts are one-off investigations with hard-coded paths; read the script and its usage header before running it.

| Prefix / group | Purpose |
|---|---|
| `air_*`, `fares_*` | Airport/airline connectivity, fares, source extraction and validation |
| `build_island_status`, `census_island_join` | Island identities, census joins and status |
| `edu_*`, `higher_ed_*` | Schools, enrolment, educational provision and higher education |
| `health_*`, `dental_*`, `diag_*`, `imgfork_*` | Health facilities, clinical services and diagnostic-source research |
| `econ_*` | Economic indicators, budgets and health-spending source preparation |
| `followme_*`, `avas_*`, `macl_*` | Datathon GPS, ride and airport-traffic profiling |
| `heigit_*`, `osm_*`, `inspect_vec` | Accessibility models and geographic layers |
| `profile_*`, `kandu_*`, `yearbook_*`, `inventory_*` | General profiling, Team Kandu tables and dataset inventories |

The raw input files remain separate from the web starter. Paths and provenance are described in [data/README.md](../data/README.md), the source scripts, and [research notes](../research/README.md). Not all inputs are available in a fresh checkout.

The Python research environment commonly uses pandas, geopandas, pyogrio, polars, pyarrow, openpyxl, requests, pdfplumber and PyMuPDF; individual scripts may need other dependencies. These are not dependencies of the Nuxt starter or the standard-library agent tools. Network-fetching scripts contact the source websites and write local data; they are not invoked by the read-only MCP tools.

The published Python source was checked for syntax without executing its research/download workflows. No claim is made that every script runs against current upstream websites or missing local inputs.
