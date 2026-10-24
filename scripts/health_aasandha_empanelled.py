"""Download Aasandha 'Empanelled Facilities - Local' list (paginated HTML) and tidy it.

Usage: python -I health_aasandha_empanelled.py <RAW_DIR> <OUT_CSV>
Columns: provider_name, island_raw, atoll_prefix, island
"""
import csv
import html
import os
import re
import sys
import time
import urllib.request

BASE = "https://www.aasandha.mv/empanelled-facilities-local"
UA = {"User-Agent": "Mozilla/5.0 (datathon research)"}


def get(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            print("retry", url, e, file=sys.stderr)
            time.sleep(3)
    return ""


def main():
    raw, out = sys.argv[1], sys.argv[2]
    os.makedirs(raw, exist_ok=True)
    rows = []
    page = 1
    last = 39
    while page <= last:
        url = BASE if page == 1 else f"{BASE}?page={page}"
        t = get(url)
        open(os.path.join(raw, f"page_{page:03d}.html"), "w", encoding="utf-8").write(t)
        m = re.findall(r"page=(\d+)", t)
        if m:
            last = max(last, max(int(x) for x in m))
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, flags=re.S):
            tds = [html.unescape(re.sub(r"<[^>]+>", "", td)).strip()
                   for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
            if len(tds) >= 2 and tds[0]:
                isl = tds[1]
                mm = re.match(r"^\s*([A-Za-z]+)\.\s*(.*)$", isl)
                rows.append({"provider_name": tds[0], "island_raw": isl,
                             "atoll_prefix": mm.group(1) if mm else "",
                             "island": mm.group(2).strip() if mm else isl})
        page += 1
        time.sleep(0.5)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["provider_name", "island_raw", "atoll_prefix", "island"])
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "rows", file=sys.stderr)


if __name__ == "__main__":
    main()
