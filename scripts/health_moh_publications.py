"""List MoH (health.gov.mv) publications for selected categories / departments, resolve
each item's file link(s), and optionally download them.

Usage:
  python -I health_moh_publications.py list <out_tsv> "category=34" "category=14" "department=27" ...
  python -I health_moh_publications.py download <in_tsv> <out_dir> [<title_regex>]
"""
import csv
import html
import os
import re
import sys
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (datathon research)"}
BASE = "https://health.gov.mv/en/publications"


def get(url, binary=False):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            print("retry", url, e, file=sys.stderr)
            time.sleep(3)
    return None


def list_items(filt):
    items, page = [], 1
    while True:
        url = f"{BASE}?search=&{filt}&page={page}"
        if "department" not in filt:
            url = f"{BASE}?search=&{filt}&department=&page={page}"
        t = get(url) or ""
        found = re.findall(r'href=(https://health\.gov\.mv/en/publications/[^\s>"]+)>.*?publication-title">(.*?)</p>',
                           t, re.S)
        if not found:
            break
        items += [(u, html.unescape(re.sub(r"\s+", " ", ti)).strip()) for u, ti in found]
        pages = [int(x) for x in re.findall(r"page=(\d+)", t)]
        if page >= (max(pages) if pages else 1):
            break
        page += 1
        time.sleep(0.4)
    return items


def resolve(item_url):
    t = get(item_url) or ""
    main = t.split("</nav>", 1)[-1]
    date = re.search(r"\b(\d{2} [A-Z][a-z]+ \d{4})\b", main)
    files = re.findall(r'href="(https?://[^"]+?(?:\.pdf|\.xlsx?|\.docx?|\.csv|sharepoint[^"]*))"', main)
    files = [f for f in files if "ndgeuyyb.pdf" not in f]  # nav link present on every page
    return (date.group(1) if date else ""), list(dict.fromkeys(files))


def main():
    if sys.argv[1] == "list":
        out = sys.argv[2]
        rows = []
        for filt in sys.argv[3:]:
            for u, ti in list_items(filt):
                date, files = resolve(u)
                rows.append({"filter": filt, "title": ti, "date": date, "page_url": u,
                             "files": " ".join(files)})
                time.sleep(0.3)
            print(filt, "->", sum(1 for r in rows if r["filter"] == filt), file=sys.stderr)
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["filter", "title", "date", "page_url", "files"], delimiter="\t")
            w.writeheader()
            w.writerows(rows)
    elif sys.argv[1] == "download":
        src, out = sys.argv[2], sys.argv[3]
        rx = re.compile(sys.argv[4], re.I) if len(sys.argv) > 4 else None
        os.makedirs(out, exist_ok=True)
        for r in csv.DictReader(open(src, encoding="utf-8"), delimiter="\t"):
            if rx and not rx.search(r["title"]):
                continue
            for fu in r["files"].split():
                if "sharepoint" in fu:
                    print("SKIP sharepoint", r["title"], fu, file=sys.stderr)
                    continue
                safe = re.sub(r"[^A-Za-z0-9]+", "_", r["title"])[:80].strip("_")
                fn = os.path.join(out, f"{safe}__{os.path.basename(fu)}")
                if os.path.exists(fn):
                    continue
                data = get(fu, binary=True)
                if data:
                    open(fn, "wb").write(data)
                    print("saved", fn, len(data), file=sys.stderr)


if __name__ == "__main__":
    main()
