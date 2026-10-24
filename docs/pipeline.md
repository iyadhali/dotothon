# Data pipeline — how new data gets processed

The four datasets were delivered as files, so that is how new data arrives: **drop the file where
the old one lived and the pipeline rebuilds itself.** Nothing to re-wire, no code change, no
restart of the web app.

```
data/incoming/<file>      any csv, xlsx or json                 → SQLite: source_file + raw_record
data/FollowMe_<month>/    any folder matching data/FollowMe*  → sea network (the travel-time model)
data/MTCC.xlsx            overwrite                            → tidy bus + ferry tables
data/MACL/*.csv           overwrite                            → monthly airport traffic
data/Avas_Ride/*.csv      overwrite                            → daily ride demand + fare matrix
```

## The database is reconciled, not rebuilt

`scripts/build_database.py` upserts every table on its natural key, prunes rows the artifacts no
longer contain, and writes one `data_change` row per touched table. The second run in a row prints
`nothing changed`, which is the test that it is a projection and not an append log. `--rebuild`
remains available when you really want a clean file.

`scripts/absorb_incoming.py` (stage `incoming`) is what makes a *new* dataset land in the database:
it registers each file in `source_file` with its sha256, routes known filenames to the stage that
consumes them, and stores everything else row-by-row in `raw_record` so it is queryable before any
stage understands it. Re-dropping the same bytes is a no-op.

## Three ways to run it

| Command | What it does |
|---|---|
| `make ingest` | one incremental pass — fingerprints every source, rebuilds only the stale stages |
| `make watch` | the same, forever: polls every 10 s and ingests the moment a file changes |
| `python scripts/ingest.py --dry-run` | prints what *would* run, changes nothing |
| `python scripts/ingest.py --force` | rebuild everything regardless of fingerprints |

## How it decides what to rebuild

Each source group is fingerprinted — a SHA-256 over `(path, size, mtime)` for every file. That is
cheaper than reading 1.9 GB of GPS just to decide whether to read it, and it catches exactly what
"new data" looks like in practice. The fingerprints are stored in `data/derived/.ingest.json`, so
the next run knows which inputs produced which outputs.

| Stage | Runs when | Produces |
|---|---|---|
| `spine` | Census or boundary files changed | `island_spine.csv` (187 islands) |
| `normalise` | MTCC, MACL or Avas changed | `mtcc_*.csv`, `macl_monthly.csv`, `avas_daily.csv`, `avas_fare_matrix.csv` |
| `sea` | the FollowMe folder changed | `sea_edges.csv`, `sea_nodes.csv` |
| `provision` | the MoE statistics PDF changed | `island_school_provision.csv` |
| `reachability` | any of the above rebuilt | `island_access.csv`, `island_pairs.csv`, `priority_gaps.csv` |
| `web` | reachability rebuilt | `islands_points.json` (the map data) |
| `check` | always | 13 assertions on the numbers we publish |

The web app does **not** need restarting: `web/access/data.py` keys its in-memory model on the
mtimes of the derived tables, so the next request rebuilds it. A judge can watch a file land and
the map change a few seconds later.

## What a run leaves behind

`data/derived/source_manifest.json` and `source_manifest.md` — what was ingested, when, how big,
and how many rows came out. The web app prints the build time in its footer, so the provenance of
every number on screen is visible without opening a terminal.

```
$ make ingest
sources
  followme     31 files   1,892.7 MB  unchanged
  mtcc          1 files       0.1 MB  new
  ...
plan
  normalise     because mtcc changed
  check         because always
✓ ingest complete in 1s
```

## Two source traps the ingest fixes for you

- **MACL dates are month/day/year**, even though `MACL/Metadata.csv` documents `YYYY-MM-DD`.
  102,304 of 168,959 rows have a second component above 12, so day-first parsing silently
  corrupts 60 % of the file. `normalise_sources.py` asserts the format before parsing.
- **MTCC ridership is labelled "sample value"** by the supplier's own README. The tidy tables carry
  that flag as a `supplier_note` column so it cannot be lost downstream.

## Adding a dataset that did not exist before

Add one entry to `source_files()` and one row to `STAGES` in `scripts/ingest.py`. That is the whole
integration: fingerprints, staleness, the watcher, the manifest and the web reload all follow from
those two registries — there is no second place to update.
