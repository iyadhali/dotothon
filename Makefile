# One-command pipeline. Every target is safe to re-run.
#
#   make            → same as `make all`
#   make refresh GPS=/path/to/new/month   → rebuild everything from a new FollowMe folder
#   make check      → assert the published numbers still hold (used before submission)
#
# Override the interpreter if yours is elsewhere:  make all PY=/usr/bin/python3

PY      ?= python3
GPS     ?= data/FollowMe_august_2025
PORT    ?= 8000

.PHONY: all ingest watch setup external spine gps schools provision model access simulator placement webdata database check run refresh

all: external spine gps provision model access simulator placement webdata database check

setup:
	$(PY) -m pip install -r requirements.txt

# open data: Census 2022, OCHA boundaries, Geofabrik extract (see scripts/fetch_external_data.sh)
external:
	bash scripts/fetch_external_data.sh

# 187 inhabited islands: Census population joined to OCHA island polygons
spine:
	$(PY) scripts/build_island_spine.py

# 31 days of GPS → stays → observed crossings (the slow one, ~4 min)
gps:
	$(PY) scripts/build_sea_network.py --gps "$(GPS)"

# MoE School Statistics 2024 → students per grade per island
provision:
	$(PY) scripts/build_school_provision.py

# graph + school layer → hours to the nearest grade 11–12 school, and the gap table
model:
	$(PY) scripts/build_reachability.py

# service register + the same graph → coverage for every education and health service
access:
	$(PY) scripts/seed_services.py --if-missing
	$(PY) scripts/build_service_access.py

# coverage ranking → placement.csv (where a new facility covers the most people)
simulator:
	$(PY) scripts/build_simulator.py

# one hypothetical crossing at a time → travel_time.csv + link_candidates.csv
placement:
	$(PY) scripts/build_placement.py

# map points for the Django app
webdata:
	$(PY) web/build_web_data.py

# every derived CSV → data/platform.sqlite (the only thing the app reads)
database:
	$(PY) scripts/build_database.py

# incremental ingest: fingerprint every source group, rebuild only what changed
ingest:
	$(PY) scripts/ingest.py

# same, but watch forever: new files dropped into data/ are processed automatically
watch:
	$(PY) scripts/watch_data.py --every 10

# only the data/incoming pass
absorb:
	python3 scripts/absorb_incoming.py

# assert the numbers we publish still hold
check:
	$(PY) scripts/check_outputs.py

run: database webdata
	cd web && $(PY) manage.py runserver $(PORT)

# full rebuild on a new month of GPS without touching open data
refresh: spine gps provision model access simulator placement webdata database check

guard: ## install the push guard (only a-team-accessibility-model may be pushed)
	sh scripts/git-guard/install.sh
