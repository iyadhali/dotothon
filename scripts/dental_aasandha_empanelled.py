"""Scrape Aasandha 'Empanelled Facilities - Local' list (provider name + island).

https://www.aasandha.mv/empanelled-facilities-local?page=N   (20 rows/page)
Usage: python -I dental_aasandha_empanelled.py <OUT_DIR>
Outputs: <OUT_DIR>/pages/page_NN.html, <OUT_DIR>/aasandha_empanelled_local.csv
"""
import csv
import html
import os
import re
import sys
import time
import urllib.request

URL = "https://www.aasandha.mv/empanelled-facilities-local?page={}"
UA = {"User-Agent": "Mozilla/5.0 (datathon research; contact see project README)"}


def get(u):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            print("retry", u, e, file=sys.stderr)
            time.sleep(3)
    return ""


def parse(t):
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        tds = [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(tds) >= 2 and tds[0]:
            rows.append(tds[:2])
    return rows


def main():
    out = sys.argv[1]
    os.makedirs(os.path.join(out, "pages"), exist_ok=True)
    first = get(URL.format(1))
    last = max([int(x) for x in re.findall(r"empanelled-facilities-local\?page=(\d+)", first)] + [1])
    allr = []
    for p in range(1, last + 1):
        t = first if p == 1 else get(URL.format(p))
        open(os.path.join(out, "pages", f"page_{p:02d}.html"), "w", encoding="utf-8").write(t)
        allr += parse(t)
        time.sleep(0.4)
    with open(os.path.join(out, "aasandha_empanelled_local.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["provider", "island"])
        w.writerows(allr)
    print(f"{last} pages, {len(allr)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
