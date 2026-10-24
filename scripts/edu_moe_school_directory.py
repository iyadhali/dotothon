"""Scrape the Ministry of Education school directory (https://www.moe.gov.mv/en/schools).

Each school page gives: atoll, island, opened date, students, teachers, government staff
(self-reported by school to the ministry). Raw HTML is cached under
data/external/education/moe_school_directory/html/ and a tidy CSV is written to
data/external/education/moe_school_directory/moe_school_directory.csv

Run:  python -I scripts/edu_moe_school_directory.py
"""
import csv
import html as htmlmod
import re
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(r"C:\Users\user\Music\Datathon\data\external\education\moe_school_directory")
RAW = OUT / "html"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://www.moe.gov.mv"
UA = {"User-Agent": "Mozilla/5.0 (datathon research)"}


def get(url, path):
    if path.exists() and path.stat().st_size > 1000:
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read().decode("utf-8", errors="replace")
    path.write_text(data, encoding="utf-8")
    time.sleep(0.4)
    return data


def text_lines(s):
    t = re.sub(r"<(script|style|svg).*?</\1>", "", s, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    return [htmlmod.unescape(l.strip()) for l in t.split("\n") if l.strip()]


def num(lines, label):
    for i, l in enumerate(lines):
        if l == label and i + 1 < len(lines):
            m = re.match(r"[\d,]+", lines[i + 1])
            if m:
                return int(m.group(0).replace(",", ""))
    return None


def main():
    idx = get(BASE + "/en/schools", RAW / "_index.html")
    ids = []
    for m in re.finditer(r'href="/en/schools/(\d+)"', idx):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    print("school ids:", len(ids))
    rows = []
    for sid in ids:
        s = get(f"{BASE}/en/schools/{sid}", RAW / f"{sid}.html")
        L = text_lines(s)
        # Name: the line just before "Opened" (after "Atoll")
        name = atoll = island = opened = address = None
        if "Opened" in L:
            k = L.index("Opened")
            name = L[k - 1]
            atoll = L[k - 2]
            if atoll == "Atoll":
                atoll = L[k - 3]
            atoll = atoll.rstrip(".")
            opened = L[k + 2] if L[k + 1] == ":" else L[k + 1]
        status = "temporarily closed" if any("temporarily closed" in l for l in L) else "open"
        if "Contact Us" in L:
            k = L.index("Contact Us")
            atoll_code = L[k + 1].rstrip(".")
            island = L[k + 2]
            address = L[k + 3]
        else:
            atoll_code = None
        rows.append(dict(
            moe_school_id=sid, school=name, atoll=atoll, atoll_code=atoll_code,
            island=island, opened=opened, status=status,
            students=num(L, "Students"), teachers=num(L, "Teachers"),
            govt_staff=num(L, "Government Staff"), address=address,
            source_url=f"{BASE}/en/schools/{sid}",
        ))
    out = OUT / "moe_school_directory.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", out, len(rows))
    missing = [r["moe_school_id"] for r in rows if not r["island"]]
    print("missing island:", missing, file=sys.stderr)


if __name__ == "__main__":
    main()
