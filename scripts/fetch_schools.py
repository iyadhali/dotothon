#!/usr/bin/env python3
"""
Scrape the Ministry of Education school directory into data/derived/schools.csv.

Source: https://www.moe.gov.mv/en/schools  (219-220 government schools; the directory page
links every school as /en/schools/<id>). Each page carries the atoll, the island, the school
name, student/teacher/staff counts, and a free-text "School Introduction" that usually states
the grade range ("offers from foundation stage to grade 10").

Output columns: school_id, school_name, atoll, island, students, teachers,
                grade_min, grade_max, levels, url

Run once and commit the CSV — the pipeline must not depend on live scraping at judging time.
"""
from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/derived/schools.csv"
CACHE = ROOT / "data/derived/raw_school_pages"
BASE = "https://www.moe.gov.mv"
INDEX = f"{BASE}/en/schools"
UA = {"User-Agent": "Mozilla/5.0 (compatible; datathon-research/1.0)"}


def fetch(url: str, tries: int = 3) -> str:
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(1.5 * (k + 1))
    return ""


def text_of(html: str) -> str:
    s = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


ATOL = {
    "ha": "Haa Alifu", "hdh": "Haa Dhaalu", "sh": "Shaviyani", "n": "Noonu", "r": "Raa",
    "b": "Baa", "lh": "Lhaviyani", "k": "Kaafu", "m": "Meemu", "v": "Vaavu", "f": "Faafu",
    "dh": "Dhaalu", "th": "Thaa", "l": "Laamu", "ga": "Gaafu Alifu", "gdh": "Gaafu Dhaalu",
    "s": "Seenu", "gn": "Gnaviyani", "aa": "Alifu Alifu", "adh": "Alifu Dhaalu",
}


def norm_atoll(s: str) -> str:
    k = re.sub(r"[^a-z]", "", s.lower())
    return ATOL.get(k, s.strip())


def parse(sid: str, html: str) -> dict | None:
    t = text_of(html)
    # "Haa Alifu. Atoll Maarandhoo School Opened : 07 October 1967 Students 167 + Teachers 33 +"
    m = re.search(r"([A-Z][A-Za-z'\s]+?)\.?\s*Atoll\s+(.{3,120}?)\s+Opened", t)
    atoll = island = name = None
    if m:
        atoll = norm_atoll(m.group(1))
        name = m.group(2).strip()
        island = re.sub(r"\s*School$|\s*Education Centre$", "", name).strip()
    if not name:
        m2 = re.search(r"([A-Za-z'\.\- ]{2,40}Atoll)\s+(.{3,100}?)\s+(?:Opened|Students)", t)
        if m2:
            atoll, name = norm_atoll(m2.group(1)), m2.group(2).strip()
    students = re.search(r"Students\s+(\d+)", t)
    teachers = re.search(r"Teachers\s+(\d+)", t)
    # grade range from the intro text
    g_all = [int(x) for x in re.findall(r"grade\s*(\d{1,2})", t, flags=re.I)]
    g_min = g_max = None
    if g_all:
        g_max = max(g_all)
        g_min = 1 if re.search(r"foundation|grade\s*1\b", t, flags=re.I) else None
    return dict(
        school_id=sid,
        school_name=name,
        atoll=atoll,
        island=island,
        students=int(students.group(1)) if students else None,
        teachers=int(teachers.group(1)) if teachers else None,
        grade_max=g_max,
        grade_min=g_min,
        url=f"{BASE}/en/schools/{sid}",
    )


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    index_html = fetch(INDEX)
    ids = sorted(set(re.findall(r"/schools/(\d+)", index_html)), key=int)
    print(f"school ids found: {len(ids)}")

    def grab(sid: str) -> tuple[str, str]:
        f = CACHE / f"{sid}.html"
        if f.exists() and f.stat().st_size > 5000:
            return sid, f.read_text(encoding="utf-8", errors="replace")
        h = fetch(f"{BASE}/en/schools/{sid}")
        if h:
            f.write_text(h, encoding="utf-8")
        return sid, h

    with ThreadPoolExecutor(max_workers=8) as ex:
        pages = list(ex.map(grab, ids))

    rows = [r for sid, h in pages if h and (r := parse(sid, h))]
    df = pd.DataFrame(rows).sort_values(["atoll", "island"]).reset_index(drop=True)
    df.to_csv(OUT, index=False)
    print(f"parsed {len(df)} schools -> {OUT.relative_to(ROOT)}")
    print(f"  students {int(df.students.fillna(0).sum()):,} | teachers {int(df.teachers.fillna(0).sum()):,}")
    print(f"  atolls: {df.atoll.nunique()} | islands: {df.island.nunique()}")
    print(f"  grade range parsed: {df.grade_max.notna().sum()} / {len(df)}")
    print("\n  offering beyond grade 10 (A-level / higher secondary):")
    print(df[df.grade_max >= 11].groupby(["atoll", "island"]).size().to_string())


if __name__ == "__main__":
    main()
