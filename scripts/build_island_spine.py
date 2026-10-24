#!/usr/bin/env python3
"""
Build data/external/island_spine.csv — one row per inhabited island, with population
(Census 2022) joined to geometry (OCHA COD-AB ADM2).

This is step 1 of the accessibility pipeline: every later join (schools, ferry network,
air network, accessibility score) hangs off this table.

Verified output (24 Oct 2026): 186 atoll islands + Malé city row, 187 rows,
100 % of the 186 Census islands matched to an ADM2 polygon, island area correlation
with OCHA 0.9996 (median absolute difference 0.006 km2).

Reading rules that matter
-------------------------
1. Header rows: the real header is at row index 2, sub-headers at 3, data starts at 6.
   Read with header=None and index columns by position — merged cells make name-based
   parsing unreliable.
2. Exclude the four aggregate rows (they are totals, not islands):
   "Administrative Islands in Atolls", "Non Administrative Islands",
   "Resorts", "Industrial Islands".
3. Census atoll codes are NOT the ISO codes: 'M' is Meemu (not Malé), 'Adh' is
   Alifu Dhaalu, 'F' is Faafu, 'Dh' is Dhaalu, 'L' is Laamu, 'S' is Seenu.
   Malé is absent from the island sheet entirely — it comes from the atoll sheet.
4. Join on (atoll, normalised island name) — never on island name alone: 37 islands
   carry a different transliteration in the two sources ("Ugoofaaru" vs "Un'goofaaru",
   "Gamu" vs "Gan"), and dozens share a name across atolls (Funadhoo, Lhohi, Feydhoo).
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "external"
CENSUS = EXT / "census2022_island_population.xlsx"
ATOLL = EXT / "census2022_atoll_population.xlsx"
GEO = EXT / "mdv_admin2_islands.geojson"
OUT = EXT / "island_spine.csv"

ATOL_CODE = {
    "HA": "Haa Alifu", "HDh": "Haa Dhaalu", "Sh": "Shaviyani", "N": "Noonu",
    "R": "Raa", "B": "Baa", "Lh": "Lhaviyani", "K": "Kaafu", "M": "Meemu",
    "V": "Vaavu", "F": "Faafu", "Dh": "Dhaalu", "Th": "Thaa", "L": "Laamu",
    "GA": "Gaafu Alifu", "GDh": "Gaafu Dhaalu", "S": "Seenu", "Gn": "Gnaviyani",
    "AA": "Alifu Alifu", "Adh": "Alifu Dhaalu",
}
AGGREGATES = {
    "Administrative Islands in Atolls", "Non Administrative Islands",
    "Resorts", "Industrial Islands",
}
# transliterations that fuzzy matching alone does not reach
ALIAS = {"kuribi": "kurinbi", "gamu": "gan"}

# column positions in the island sheet (header=None)
C_ATOLL, C_ISLAND, C_POP, C_MALE, C_FEMALE = 0, 1, 2, 3, 4
C_CHILD, C_AREA_SQKM, C_DENSITY, C_MEDIAN_AGE = 20, 49, 50, 52


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def load_geometry() -> pd.DataFrame:
    props = pd.DataFrame([f["properties"] for f in json.loads(GEO.read_text())["features"]])
    g = props[["adm2_name", "adm2_pcode", "adm1_name", "area_sqkm", "center_lat", "center_lon"]]
    g["k"] = g.adm2_name.map(norm)
    return g


def load_census() -> pd.DataFrame:
    raw = pd.read_excel(CENSUS, sheet_name="Indicator Island", header=None)
    d = raw.iloc[6:, [C_ATOLL, C_ISLAND, C_POP, C_MALE, C_FEMALE, C_CHILD, C_AREA_SQKM, C_DENSITY, C_MEDIAN_AGE]].copy()
    d.columns = ["atoll_code", "island", "population", "male", "female",
                 "child_0_17", "area_km2", "density", "median_age"]
    numeric = ["population", "male", "female", "child_0_17", "area_km2", "density", "median_age"]
    d[numeric] = d[numeric].apply(pd.to_numeric, errors="coerce")
    d = d.dropna(subset=["island", "population"])
    d = d[d.population > 0]
    d = d[~d.island.isin(AGGREGATES)]
    d["atoll_name"] = d.atoll_code.map(ATOL_CODE)
    if d.atoll_name.isna().any():
        sys.exit(f"unmapped atoll codes: {sorted(d[d.atoll_name.isna()].atoll_code.unique())}")
    d["k"] = d.island.map(norm).replace(ALIAS)
    return d


def match_island(row, g: pd.DataFrame):
    cand = g[g.adm1_name == row.atoll_name]
    if cand.empty:
        return None
    exact = cand[cand.k == row.k]
    if len(exact):
        return exact.iloc[0]
    best = difflib.get_close_matches(row.k, cand.k.tolist(), n=1, cutoff=0.72)
    return cand[cand.k == best[0]].iloc[0] if best else None


def male_city_row() -> dict:
    """Malé is not in the island sheet; take the city total from the atoll sheet."""
    raw = pd.read_excel(ATOLL, sheet_name="Atoll", header=None)
    hit = raw[raw[1].astype(str).str.startswith("Male'")]
    if hit.empty:
        sys.exit("could not find the Male' row in the atoll sheet")
    pop = int(hit.iloc[0, 2])
    return dict(
        atoll_code="MLE", atoll_name="Male (city)",
        island="Malé City (incl. Villimalé, Hulhumalé)",
        population=pop, child_0_17=None, area_km2=8.0, density=None, median_age=None,
        island_pcode="MV", lat=4.175495, lon=73.509347, area_km2_ocha=None,
        ocha_name=None, matched=True,
        coverage_note="from Atoll-Level sheet row \"Male' (including Villimale')\"; no per-island detail",
    )


def main() -> None:
    g = load_geometry()
    d = load_census()
    rows = []
    for _, r in d.iterrows():
        hit = match_island(r, g)
        note = ""
        if hit is not None and norm(hit.adm2_name) != r.k:
            note = f'census "{r.island}" = OCHA "{hit.adm2_name}"'
        if hit is None:
            note = "UNMATCHED — check transliteration"
        rows.append(dict(
            atoll_code=r.atoll_code, atoll_name=r.atoll_name, island=r.island,
            population=int(r.population),
            child_0_17=None if pd.isna(r.child_0_17) else int(r.child_0_17),
            area_km2=r.area_km2,
            density=None if pd.isna(r.density) else round(r.density, 1),
            median_age=r.median_age,
            island_pcode=hit.adm2_pcode if hit is not None else None,
            lat=round(hit.center_lat, 6) if hit is not None else None,
            lon=round(hit.center_lon, 6) if hit is not None else None,
            area_km2_ocha=round(hit.area_sqkm, 4) if hit is not None else None,
            ocha_name=hit.adm2_name if hit is not None else None,
            matched=hit is not None,
            coverage_note=note,
        ))
    sp = pd.concat([pd.DataFrame(rows), pd.DataFrame([male_city_row()])], ignore_index=True)
    sp.to_csv(OUT, index=False)

    m = sp[sp.matched & sp.area_km2_ocha.notna()]
    print(f"rows {len(sp)} | islands matched {int(sp.matched.sum())}/{len(d)} "
          f"| population covered {int(sp.population.sum()):,}")
    print(f"area correlation vs OCHA {m.area_km2.corr(m.area_km2_ocha):.4f} "
          f"| median abs diff {abs(m.area_km2 - m.area_km2_ocha).median():.4f} km2")
    print(f"unmatched: {sp[~sp.matched].island.tolist()}")
    print(f"child population 0-17: {int(sp.child_0_17.sum()):,} "
          f"({100 * sp.child_0_17.sum() / sp[sp.atoll_code != 'MLE'].population.sum():.1f} % of atoll population)")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
