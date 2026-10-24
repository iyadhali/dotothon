#!/usr/bin/env bash
# Fetch the open datasets this project depends on.
# Everything lands in data/external/. Raw files are NOT committed to git from here
# onward except the two small Census workbooks — see .gitignore notes at the bottom.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT="data/external"
mkdir -p "$OUT"

say() { printf '\n== %s\n' "$1"; }

say "MBS Census 2022 — island level indicator sheet"
curl -fsSL -o "$OUT/census2022_island_population.xlsx" \
  "https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2023/09/Island-Level-Indicator-Sheet-Population.xlsx"

say "MBS Census 2022 — atoll level indicator sheet"
curl -fsSL -o "$OUT/census2022_atoll_population.xlsx" \
  "https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2023/09/Atoll-Level-Indicator-Sheet-Population.xlsx"

say "OCHA / HDX — Maldives subnational boundaries (ADM2 = 1,556 islands)"
TMP="$(mktemp -d)"
curl -fsSL -o "$TMP/mdv.zip" \
  "https://data.humdata.org/dataset/a968d227-24c9-49ea-bbce-cee04ee94819/resource/3e277382-c09a-4496-bd46-c1a2a92bb835/download/mdv_admin_boundaries.geojson.zip"
unzip -o -q "$TMP/mdv.zip" -d "$TMP/x"
cp "$TMP/x/mdv_admin2.geojson" "$OUT/mdv_admin2_islands.geojson"
cp "$TMP/x/mdv_admin1.geojson" "$OUT/mdv_admin1_atolls.geojson"
rm -rf "$TMP"

say "OpenStreetMap — Geofabrik Maldives extract (airports, ferry terminals, roads)"
if command -v osmium >/dev/null 2>&1; then
  curl -fsSL -o /tmp/maldives-latest.osm.pbf "https://download.geofabrik.de/asia/maldives-latest.osm.pbf"
  osmium export /tmp/maldives-latest.osm.pbf -f geojson \
    -o "$OUT/osm_maldives.geojson" \
    -e "nwr/aeroway=aerodrome,amenity=ferry_terminal,amenity=school"
else
  echo "   osmium not installed — skipping. macOS: brew install osmium-tool"
fi

say "Done. Files:"
ls -lh "$OUT"

cat <<'NOTE'

Notes
-----
* data/FollowMe_august_2025/ is 1.8 GB of raw GPS. Never commit it; commit the derived
  stay/OD tables instead (a few thousand rows) and let this script's sibling reproduce them.
* data/external/island_spine.csv is generated, not downloaded — see scripts/build_island_spine.py.
* Licences to restate in README + the submission declaration:
    - Census 2022 / MoE material: Government of Maldives (credit the publisher)
    - OCHA COD-AB: open, credit OCHA FIS and the Maldives government source
    - OSM: ODbL, (c) OpenStreetMap contributors
NOTE
