#!/usr/bin/env python3
"""
Build `data/services.csv` — the register of key services, one row per facility, attached to an
island. This file is the **source of truth** and is meant to be edited: by hand, or through the
"Add a service" form in the app. Re-running this script keeps any row it did not create.

Seeded from official sources, never invented:

  health / health_centre   164 facilities, scraped from the Ministry of Health facility list
                           https://health.gov.mv/en/health-facilities (cached in
                           data/external/moh_health_facilities.html so the build works offline)
  health / hospital        a PARTIAL seed — the Wikipedia list of Maldives hospitals and the
                           hospitals it names. The ministry site states there are 23 government
                           hospitals but does not publish their names on that page, so the rest are
                           meant to be added through the form. Marked in `notes`.
  education / school_*     derived from MoE School Statistics 2024 per-island enrolment by grade
                           (primary Gr 1-6, lower secondary Gr 7-10, higher secondary Gr 11-12)
  education / college      the five MNU campuses (Malé, Kulhudhuffushi, Gan, Hithadhoo, Thinadhoo)

    python scripts/seed_services.py            # create the file if it is missing
    python scripts/seed_services.py --force    # rebuild from sources (drops manual rows)
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import re
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "services.csv"
MOH_HTML = DATA / "external" / "moh_health_facilities.html"

ATOLLS = ["Haa Alifu", "Haa Dhaalu", "Shaviyani", "Noonu", "Raa", "Baa", "Lhaviyani", "Kaafu",
          "Male", "Vaavu", "Faafu", "Dhaalu", "Meemu", "Thaa", "Laamu", "Gaafu Alifu",
          "Gaafu Dhaalu", "Gnaviyani", "Seenu", "Alifu Alifu", "Alifu Dhaalu"]
COLS = ["service_id", "category", "service_type", "name", "atoll", "island",
        "lat", "lon", "source", "added_at", "notes"]

# Hospitals named by https://en.wikipedia.org/wiki/List_of_hospitals_in_the_Maldives
# (atoll, island, name). The article is a stub: treat as a starter set, not the full 23.
HOSPITALS = [
    ("Male", "Malé City", "Indira Gandhi Memorial Hospital"),
    ("Male", "Malé City", "ADK Hospital"),
    ("Laamu", "Gamu", "Gan Regional Hospital"),
    ("Faafu", "Nilandhoo", "Faafu Atoll Hospital"),
    ("Seenu", "Hithadhoo", "Addu Equatorial Hospital"),
]
CAMPUSES = [("Male", "Malé City", "The Maldives National University"),
            ("Haa Dhaalu", "Kulhudhuffushi", "MNU Kulhudhuffushi Campus"),
            ("Gaafu Dhaalu", "Thinadhoo", "MNU Thinadhoo Campus"),
            ("Seenu", "Hithadhoo", "MNU Hithadhoo Campus"),
            ("Seenu", "Gan", "MNU Gan Campus")]


def norm(s) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def sid(category: str, ident: str) -> str:
    h = hashlib.sha1(ident.encode()).hexdigest()[:8]
    return f"{(category or 'svc')[:3]}-{h}"


def load_spine() -> pd.DataFrame:
    sp = pd.read_csv(DATA / "external" / "island_spine.csv")
    sp["k"] = sp.island.map(norm)
    return sp


def male_row(sp: pd.DataFrame):
    """Malé is a city, not an atoll island: it has its own row keyed on atoll_code MLE."""
    hit = sp[sp.atoll_code == "MLE"]
    return hit.iloc[0] if len(hit) else None


def resolve(sp: pd.DataFrame, atoll: str, island: str):
    cand = sp[sp.atoll_name == atoll]
    if cand.empty:
        return None
    hit = cand[cand.k == norm(island)]
    if len(hit):
        return hit.iloc[0]
    near = difflib.get_close_matches(norm(island), cand.k.tolist(), n=1, cutoff=0.75)
    return cand[cand.k == near[0]].iloc[0] if near else None


def parse_moh(sp: pd.DataFrame) -> list[dict]:
    """'Haa Alifu Thuraakunu Health Centre' -> (Haa Alifu, Thuraakunu)."""
    rows = []
    text = MOH_HTML.read_text(encoding="utf-8", errors="replace")
    names = []
    for block in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", block, re.S)]
        if cells and cells[0] and "health facility" not in cells[0].lower():
            names.append(cells[0])

    unresolved = 0
    for name in names:
        atoll = next((a for a in ATOLLS if name.startswith(a + " ")), None)
        island = None
        if atoll:
            island = name[len(atoll):].replace("Health Centre", "").strip()
        else:
            for a in ATOLLS:                     # "Amina Dhiyo Health Centre" style
                pass
        if atoll is None:
            # no atoll prefix: match the leading words against every island name
            lead = name.replace("Health Centre", "").strip()
            for n in range(len(lead.split()), 0, -1):
                probe = " ".join(lead.split()[:n])
                hit = sp[sp.k == norm(probe)]
                if len(hit) == 1:
                    atoll, island = hit.iloc[0].atoll_name, hit.iloc[0].island
                    break
        row = resolve(sp, atoll, island) if atoll and island else None
        if row is None:
            unresolved += 1
            continue
        rows.append(dict(category="health", service_type="health_centre", name=name,
                         atoll=row.atoll_name, island=row.island,
                         lat=round(float(row.lat), 5), lon=round(float(row.lon), 5),
                         source="MoH health facility list",
                         notes="" if atoll else "atoll inferred from island name"))
    print(f"  health centres: {len(rows)} resolved, {unresolved} could not be matched")
    return rows


def hospitals(sp: pd.DataFrame) -> list[dict]:
    rows = []
    for atoll, island, name in HOSPITALS:
        row = male_row(sp) if island == "Malé City" else resolve(sp, atoll, island)
        if row is None:
            print(f"  ! hospital not resolved: {atoll} / {island}")
            continue
        rows.append(dict(category="health", service_type="hospital", name=name,
                         atoll=row.atoll_name, island=row.island,
                         lat=round(float(row.lat), 5), lon=round(float(row.lon), 5),
                         source="Wikipedia list of hospitals in the Maldives",
                         notes="starter set — the ministry lists 23 government hospitals; "
                               "add the rest with this form"))
    print(f"  hospitals: {len(rows)} seeded")
    return rows


def education(sp: pd.DataFrame) -> list[dict]:
    prov = pd.read_csv(DATA / "derived" / "island_school_provision.csv")
    rows = []
    tiers = [("is_primary", "school_primary", "primary school (Gr 1-6)"),
             ("is_lower_secondary", "school_lower_secondary", "lower secondary (Gr 7-10)"),
             ("is_higher_secondary", "school_higher_secondary", "higher secondary (Gr 11-12)")]
    for r in prov.itertuples():
        if getattr(r, "is_region_total", False):
            continue
        for flag, stype, label in tiers:
            if not getattr(r, flag):
                continue
            row = (male_row(sp) if r.atoll == "Greater Malé"
                   else resolve(sp, r.atoll, r.island))
            if row is None:
                continue
            rows.append(dict(category="education", service_type=stype,
                             name=f"{row.island} — {label}",
                             atoll=row.atoll_name, island=row.island,
                             lat=round(float(row.lat), 5), lon=round(float(row.lon), 5),
                             source="MoE School Statistics 2024", notes=""))
    for atoll, island, name in CAMPUSES:
        row = male_row(sp) if island == "Malé City" else resolve(sp, atoll, island)
        if row is None:
            print(f"  ! campus not resolved: {atoll} / {island}")
            continue
        rows.append(dict(category="education", service_type="college", name=name,
                         atoll=row.atoll_name, island=row.island,
                         lat=round(float(row.lat), 5), lon=round(float(row.lon), 5),
                         source="MNU campus list", notes=""))
    print(f"  education services: {len(rows)}")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rebuild, dropping manually added rows")
    ap.add_argument("--if-missing", action="store_true",
                    help="seed only when data/services.csv does not exist yet (used by ingest)")
    args = ap.parse_args()

    if OUT.exists() and not args.force:
        print(f"{OUT.relative_to(ROOT)} exists — keeping it (use --force to rebuild)")
        return

    sp = load_spine()
    print("seeding services")
    rows = parse_moh(sp) + hospitals(sp) + education(sp)
    df = pd.DataFrame(rows)
    # the atoll is part of the identity: Hithadhoo, Feydhoo, Meedhoo, Gan and Hulhudhoo all exist
    # in more than one atoll, so "type|name" silently drops the second one
    df.insert(0, "service_id", [sid(r.category, f"{r.service_type}|{r.atoll}|{r.name}")
                                for r in df.itertuples()])
    df["added_at"] = date.today().isoformat()
    df = df[COLS].drop_duplicates("service_id")
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)} — {len(df):,} services "
          f"({df.category.value_counts().to_dict()})")
    print(df.service_type.value_counts().to_string())


if __name__ == "__main__":
    main()
