#!/usr/bin/env bash
# Poll Velana FIS live API (https://www.fis.com.mv/api/flights) to build a multi-day
# domestic schedule. Run for >=7 days to get true weekly frequencies.
# Usage: bash air_poll_fis.sh <out_dir> [iterations=72] [sleep_sec=1200]
OUT="${1:-C:/Users/user/Music/Datathon/data/external/air/velana_fis/live}"
N="${2:-72}"; S="${3:-1200}"
mkdir -p "$OUT"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
for i in $(seq 1 "$N"); do
  ts=$(date -u +%Y%m%dT%H%MZ)
  curl -s -m 60 -A "$UA" https://www.fis.com.mv/api/flights -o "$OUT/flights_${ts}.json"
  sleep "$S"
done
