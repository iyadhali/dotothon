#!/bin/sh
# usage: diag_fetch.sh <subdir> <name> <url>  -> saves raw html, prints http code + size
D=/c/Users/user/Music/Datathon/data/external/health/services/diagnostics/sources/$1
mkdir -p "$D"
code=$(curl -s -L -m 40 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" -o "$D/$2" -w "%{http_code}" "$3")
echo "$code $(wc -c < "$D/$2") $D/$2"
