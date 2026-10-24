#!/usr/bin/env python3
"""Build the multimodal Maldives network artifacts.

Inputs (all local, no network access):
  data/external/_derived/mdv_islands_master.csv
  data/external/_derived/census2022_to_codab_crosswalk.csv
  data/external/_derived/census2022_population_by_island.csv
  data/team-kandu/rtl_stops.csv, rtl_trips.csv, rtl_routes.csv
  data/external/air/airports.csv, domestic_routes.csv
  data/external/health/_derived/public_health_facility_master.csv
  data/external/education/institutions_master.csv
  data/external/hdx-cod-ab/extracted/mdv_admin2.geojson

Outputs:
  data/processed/multimodal/network.json
  data/processed/multimodal/islands.geojson
  data/processed/multimodal/aliases.csv
  data/processed/multimodal/report.json
  web/public/data/multimodal.json
  web/public/data/islands.geojson

Only pandas + the Python standard library are used.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import math
import re
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
EXTERNAL = DATA / "external"
RTL = DATA / "team-kandu"
DEFAULT_OUT = DATA / "processed" / "multimodal"
DEFAULT_PUBLIC = ROOT / "web" / "public" / "data"

MASTER_CSV = EXTERNAL / "_derived" / "mdv_islands_master.csv"
CROSSWALK_CSV = EXTERNAL / "_derived" / "census2022_to_codab_crosswalk.csv"
CENSUS_CSV = EXTERNAL / "_derived" / "census2022_population_by_island.csv"
STOPS_CSV = RTL / "rtl_stops.csv"
TRIPS_CSV = RTL / "rtl_trips.csv"
ROUTES_CSV = RTL / "rtl_routes.csv"
AIRPORTS_CSV = EXTERNAL / "air" / "airports.csv"
AIR_ROUTES_CSV = EXTERNAL / "air" / "domestic_routes.csv"
HEALTH_CSV = EXTERNAL / "health" / "_derived" / "public_health_facility_master.csv"
EDUCATION_CSV = EXTERNAL / "education" / "institutions_master.csv"
GEOJSON_SRC = EXTERNAL / "hdx-cod-ab" / "extracted" / "mdv_admin2.geojson"
DIAGNOSTIC_SERVICES_CSV = (
    EXTERNAL / "health" / "services" / "diagnostics" / "diagnostic_services.csv"
)
SPECIALIST_SERVICES_CSV = (
    EXTERNAL / "health" / "services" / "specialist" / "specialist_services.csv"
)
DENTAL_SERVICES_CSV = EXTERNAL / "health" / "services" / "dental" / "dental_services.csv"

REFERENCE_DAY = "2026-10-10"
SCHEMA_VERSION = 1
TIMEZONE = "Indian/Maldives"

# Transport parameters from MULTIMODAL_IMPLEMENTATION.md / research/03.
WALK_SPEED_KMH = 4.5
WALK_DETOUR = 1.25
LOCAL_TRANSPORT_SPEED_KMH = 25.0
LOCAL_TRANSPORT_BOARD_MIN = 5
LOCAL_TRANSPORT_THRESHOLD_KM = 1.5
SPEEDBOAT_SPEED_KMH = 25.0
SPEEDBOAT_BOARD_MIN = 10
ROAD_SPEED_KMH = 40.0
ROAD_PENALTY_MIN = 3
ROAD_DETOUR = 1.15
AIR_WINDOW_START = 360
AIR_WINDOW_END = 1080
GEOJSON_TOLERANCE = 0.00005
GEOJSON_DECIMALS = 5

ROUTING_DEFAULTS = {
    "ferryBoardMinutes": 15,
    "ferryAlightMinutes": 2,
    "airBoardMinutes": 45,
    "airBoardMinutesMle": 60,
    "airAlightMinutes": 15,
    "transferPenaltyMinutes": 10,
    "additionalBoardPenaltyMinutes": 5,
    "maxJourneyMinutes": 1440,
}

ATOL_SHORT = {
    "MV001": "HA",
    "MV002": "HDh",
    "MV003": "Sh",
    "MV004": "N",
    "MV005": "Lh",
    "MV006": "R",
    "MV007": "B",
    "MV008": "AA",
    "MV009": "K",
    "MV010": "V",
    "MV011": "F",
    "MV012": "Dh",
    "MV013": "M",
    "MV014": "Th",
    "MV015": "L",
    "MV016": "GA",
    "MV017": "GDh",
    "MV018": "Gn",
    "MV019": "S",
    "MV020": "ADh",
    "MV021": "MLE",
}

ATOL_NORMALISE = {
    "ha": "HA",
    "hdh": "HDh",
    "sh": "Sh",
    "n": "N",
    "lh": "Lh",
    "r": "R",
    "b": "B",
    "aa": "AA",
    "k": "K",
    "v": "V",
    "f": "F",
    "dh": "Dh",
    "m": "M",
    "th": "Th",
    "l": "L",
    "ga": "GA",
    "gdh": "GDh",
    "gn": "Gn",
    "s": "S",
    "adh": "ADh",
    "mle": "MLE",
    "k-male": "MLE",
    "male' city": "MLE",
    "male city": "MLE",
}

GREATER_MALE_IDS = ["MV021001", "MV021002", "MV021003", "MV009052"]

# Census spellings are canonical except where every transport/facility source uses a
# different established name.  The census name is retained in report.json.
DISPLAY_NAME_OVERRIDES = {
    "MV015013": {
        "name": "Gan",
        "censusName": "Gamu",
        "reason": (
            "Census 2022 spells this Laamu island 'Gamu'; RTL and the health/education "
            "registers call it 'Gan'. 'Gan' is used for display and the census spelling "
            "is retained as an alias/report entry."
        ),
    }
}

AIRPORT_ISLAND_NAMES = {
    "MV001031": "Hoarafushi Airport",
    "MV005066": "Madivaru",
    "MV006053": "Ifuru",
    "MV015045": "Kadhdhoo",
    "MV016054": "Kooddoo",
    "MV017013": "Kaadedhdhoo",
    "MV017141": "Maarehaa",
    "MV017143": "Maavarulu",
    "MV019033": "Gan",
}

HEALTH_HOSPITAL_TIERS = {
    "1_tertiary",
    "2_regional_hospital",
    "2_general_hospital",
    "2_hospital_other",
    "3_atoll_hospital",
    "3_atoll_hospital_small",
}

EDUCATION_HIGHER_ED_TYPES = {
    "college campus",
    "university campus",
    "university campus (outreach centre)",
    "institute",
    "institute (outreach centre)",
    "TVET institute",
}

EDUCATION_SCHOOL_TYPES = {"school", "higher secondary school"}

# Manual aliases.  Keys are (source, normalised_atoll, normalised_name).
# Values are one island id or a list when one source feature serves two islands.
MANUAL_ALIASES = {
    # RTL stops on airport islands / name variants that fuzzy matching must not guess.
    ("rtl_stops", "GA", "kooddoo"): "MV016054",
    ("rtl_stops", "GDh", "kaadehdhoo"): "MV017013",
    ("rtl_stops", "GDh", "maavarulu"): "MV017143",
    ("rtl_stops", "R", "ifuru"): "MV006053",
    ("rtl_stops", "GDh", "hondehdhoo"): "MV017002",
    ("rtl_stops", "HA", "hoarafushi"): "MV001006",
    ("rtl_stops", "L", "gan"): "MV015013",
    ("rtl_stops", "S", "gan"): "MV019033",
    ("rtl_stops", "S", "feydhoo"): "MV019004",
    ("rtl_stops", "Sh", "feydhoo"): "MV003004",
    ("rtl_stops", "GDh", "thinadhoo"): "MV017010",
    ("rtl_stops", "V", "thinadhoo"): "MV010002",
    ("rtl_stops", "S", "hulhumeedhoo"): ["MV019006", "MV019001"],
    ("rtl_stops", "GDh", "faresmaathoda"): "MV017008",
    ("rtl_stops", "HDh", "nolhivaram"): "MV002009",
    ("rtl_stops", "Th", "veymandoo"): "MV014011",
    # Health master uses Greater Malé atoll code K and older spellings.
    ("health", "K", "male"): "MV021001",
    ("health", "K", "hulhumale"): "MV021003",
    ("health", "K", "villimale"): "MV021002",
    ("health", "S", "hithadhoo"): "MV019002",
    ("health", "S", "hulhumeedhoo"): "MV019006",
    ("health", "L", "gan"): "MV015013",
    ("health", "HDh", "kurinbee"): "MV002010",
    ("health", "B", "maalhohu"): "MV007007",
    # Education register: Greater Malé, Addu, and a handful of place-name variants.
    ("education", "K", "male"): "MV021001",
    ("education", "MLE", "male"): "MV021001",
    ("education", "MLE", "malecity"): "MV021001",
    ("education", "K", "hulhumale"): "MV021003",
    ("education", "MLE", "hulhumale"): "MV021003",
    ("education", "K", "villimale"): "MV021002",
    ("education", "MLE", "villimale"): "MV021002",
    ("education", "S", "gan"): "MV019033",
    ("education", "S", "hithadhoo"): "MV019002",
    ("education", "S", "feydhoo"): "MV019004",
    ("education", "S", "meedhoo"): "MV019001",
    ("education", "S", "hulhumeedhoo"): "MV019006",
    ("education", "HDh", "kurinbee"): "MV002010",
    ("education", "L", "gan"): "MV015013",
    ("education", "L", "ganmukurimagu"): "MV015013",
    ("education", "L", "isdhookalaidhoo"): "MV015001",
    ("education", "GA", "konday"): "MV016007",
    ("education", "Sh", "feevaku"): "MV003005",
    ("education", "N", "lhohee"): "MV004007",
    ("education", "M", "mulaku"): "MV013004",
    # Intervention service tables use Greater Malé spellings and a few older variants.
    ("intervention", "K", "male"): "MV021001",
    ("intervention", "MLE", "male"): "MV021001",
    ("intervention", "K", "hulhumale"): "MV021003",
    ("intervention", "MLE", "hulhumale"): "MV021003",
    ("intervention", "K", "villimale"): "MV021002",
    ("intervention", "MLE", "villimale"): "MV021002",
    ("intervention", "GA", "villingili"): "MV016002",
    ("intervention", "HA", "dhidhoo"): "MV001010",
    ("intervention", "S", "hulhumeedhoo"): "MV019006",
    ("intervention", "S", "meedhooaddu"): "MV019001",
    ("intervention", "HDh", "nolhivaram"): "MV002009",
    ("intervention", "HA", "uligan"): "MV001002",
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and not value.strip()


def norm(value) -> str:
    """Lowercase ASCII-ish key used for exact joins."""
    if is_blank(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = text.lower().strip()
    text = text.replace("\u2019", "'").replace("`", "'").replace("\u00b4", "'")
    text = text.replace("'", "")
    return re.sub(r"[^a-z0-9]+", "", text)


def phonetic(value) -> str:
    """Conservative Dhivehi-aware skeleton.

    Census spellings routinely elide the naviyani 'n' before a consonant
    (Bandidhoo -> Badidhoo, Kondey -> Kodey), hypercorrect 'h' placement
    (Gahdhoo -> Gadhdhoo), and vowel endings.  The skeleton collapses those
    differences while remaining atoll-scoped during matching.
    """
    text = norm(value)
    text = re.sub(r"n(?=[bcdfghjklmnpqrstvwxyz])", "", text)
    text = text.replace("h", "")
    return re.sub(r"[aeiou]", "", text)


def normalise_atoll(value) -> str:
    if is_blank(value):
        return ""
    raw = str(value).strip()
    return ATOL_NORMALISE.get(raw.lower(), raw)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    q = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(q)))


def parse_hhmm(value) -> int:
    text = str(value).strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if not match:
        raise ValueError(f"bad HH:MM time: {value!r}")
    hour, minute = int(match.group(1)), int(match.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"bad HH:MM time: {value!r}")
    return hour * 60 + minute


def json_safe(value):
    """Recursively convert numpy/pandas values and reject NaN/Infinity."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    try:
        import numpy as np  # pandas dependency

        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            as_float = float(value)
            if math.isnan(as_float) or math.isinf(as_float):
                return None
            return as_float
    except ImportError:  # pragma: no cover
        pass
    return value


def write_json(path: Path, payload, *, indent: int | None = 1) -> int:
    text = json.dumps(
        json_safe(payload),
        ensure_ascii=False,
        allow_nan=False,
        indent=indent,
        separators=(",", ": ") if indent else (",", ":"),
    )
    data = (text + "\n").encode("utf-8")
    path.write_bytes(data)
    return len(data)


def alias_score(method: str, score) -> str:
    if method in {"exact", "manual"}:
        return "1.000"
    if method == "fuzzy" and score is not None:
        return f"{float(score):.3f}"
    return ""


def alias_reviewed(method: str) -> str:
    return "true" if method in {"exact", "manual"} else "false"


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class IslandResolver:
    def __init__(self, islands, master, manual, census_names=None):
        self.islands = {row["id"]: row for row in islands}
        self.by_id = master
        self.census_names = census_names or {}
        self.index: dict[tuple[str, str], set[str]] = defaultdict(set)
        for island in islands:
            pcode = island["id"]
            master_row = master.loc[pcode]
            variants = [
                island["name"],
                self.census_names.get(pcode),
                master_row.get("adm2_name"),
                master_row.get("adm2_name1"),
                master_row.get("adm2_name2"),
                master_row.get("adm2_name3"),
                master_row.get("adm2_ref_name"),
            ]
            for variant in variants:
                if not is_blank(variant):
                    self.index[(island["atoll"], norm(variant))].add(pcode)
        self.manual = manual
        self.manual_counts = Counter()

    def _fuzzy(self, name: str, atoll: str):
        candidates = [isl for isl in self.islands.values() if isl["atoll"] == atoll]
        if not candidates:
            return None
        target = norm(name)
        target_phon = phonetic(name)
        scored = []
        for island in candidates:
            candidate_name = island["name"]
            ratio = difflib.SequenceMatcher(None, target, norm(candidate_name)).ratio()
            bonus = 1.0 if target_phon == phonetic(candidate_name) else 0.95
            scored.append((ratio * bonus, ratio, island["id"], candidate_name))
        scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
        best = scored[0]
        second = scored[1] if len(scored) > 1 else (0.0, 0.0, None, None)
        if best[1] >= 0.80 and (best[0] - second[0]) >= 0.05 and best[2] != second[2]:
            return {"method": "fuzzy", "island_ids": [best[2]], "score": round(best[1], 4)}
        return None

    def resolve(self, source: str, atoll_value, name, allow_fuzzy: bool = True) -> dict:
        atoll = normalise_atoll(atoll_value)
        key = (source, atoll, norm(name))
        if key in self.manual:
            value = self.manual[key]
            ids = list(value) if isinstance(value, (list, tuple)) else [value]
            return {"method": "manual", "island_ids": ids, "score": 1.0}

        ids = self.index.get((atoll, norm(name)))
        if ids:
            if len(ids) == 1:
                return {"method": "exact", "island_ids": [next(iter(ids))], "score": 1.0}
            return {
                "method": "unresolved",
                "island_ids": [],
                "score": None,
                "reason": "ambiguous exact name within atoll",
            }

        if allow_fuzzy:
            fuzzy = self._fuzzy(name, atoll)
            if fuzzy:
                return fuzzy

        return {
            "method": "unresolved",
            "island_ids": [],
            "score": None,
            "reason": "no matching island in atoll",
        }


# ---------------------------------------------------------------------------
# Islands
# ---------------------------------------------------------------------------


def load_master() -> pd.DataFrame:
    return pd.read_csv(MASTER_CSV, encoding="utf-8-sig").set_index("adm2_pcode")


def build_islands(master: pd.DataFrame):
    crosswalk = pd.read_csv(CROSSWALK_CSV, encoding="utf-8-sig")
    island_rows = crosswalk[crosswalk["census_level"] == "island"]
    if len(island_rows) != 187 or island_rows["adm2_pcode"].nunique() != 187:
        raise ValueError("crosswalk island rows are not the expected 187 unique pcodes")

    islands = []
    census_names = {}
    for row in island_rows.itertuples():
        pcode = row.adm2_pcode
        master_row = master.loc[pcode]
        census_name = str(row.census_island).strip()
        census_names[pcode] = census_name
        display_name = DISPLAY_NAME_OVERRIDES.get(pcode, {}).get("name", census_name)
        islands.append(
            {
                "id": pcode,
                "name": display_name,
                "atoll": str(row.atoll_abbr).strip(),
                "atollName": str(master_row["adm1_name"]).strip(),
                "lat": round(float(master_row["lat"]), 6),
                "lon": round(float(master_row["lon"]), 6),
                "population": int(round(float(master_row["pop2022"]))),
                "status": "inhabited",
                "isOrigin": True,
            }
        )

    for pcode in GREATER_MALE_IDS:
        master_row = master.loc[pcode]
        census_names[pcode] = str(master_row["adm2_name"]).strip()
        islands.append(
            {
                "id": pcode,
                "name": str(master_row["adm2_name"]).strip(),
                "atoll": ATOL_SHORT[master_row["adm1_pcode"]],
                "atollName": str(master_row["adm1_name"]).strip(),
                "lat": round(float(master_row["lat"]), 6),
                "lon": round(float(master_row["lon"]), 6),
                "population": int(round(float(master_row["pop2022"]))),
                "status": "inhabited",
                "isOrigin": True,
            }
        )

    airport_rows = master[master["status"] == "airport"].sort_index()
    if len(airport_rows) != 9:
        raise ValueError(f"expected 9 airport-status islands, found {len(airport_rows)}")
    for pcode, master_row in airport_rows.iterrows():
        census_names[pcode] = AIRPORT_ISLAND_NAMES[pcode]
        islands.append(
            {
                "id": pcode,
                "name": AIRPORT_ISLAND_NAMES[pcode],
                "atoll": ATOL_SHORT[master_row["adm1_pcode"]],
                "atollName": str(master_row["adm1_name"]).strip(),
                "lat": round(float(master_row["lat"]), 6),
                "lon": round(float(master_row["lon"]), 6),
                "population": 0,
                "status": "airport",
                "isOrigin": False,
            }
        )

    islands.sort(key=lambda item: item["id"])
    if len(islands) != 200:
        raise ValueError(f"expected 200 node islands, found {len(islands)}")

    by_id = {item["id"]: item for item in islands}
    for pcode, master_row in master.iterrows():
        airport_iata = master_row.get("airport_iata")
        if pcode in by_id and not is_blank(airport_iata):
            by_id[pcode]["airportIata"] = str(airport_iata).strip()

    origins = [item for item in islands if item["isOrigin"]]
    population = sum(item["population"] for item in origins)
    if len(origins) != 191:
        raise ValueError(f"expected 191 origin islands, found {len(origins)}")
    if population != 447_420:
        raise ValueError(f"expected population 447420, found {population}")
    return islands, census_names


# ---------------------------------------------------------------------------
# Stops and access
# ---------------------------------------------------------------------------


def access_edge(
    from_node: str,
    to_node: str,
    *,
    mode: str,
    minutes: int,
    confidence: str,
    basis: str,
    distance_km: float | None = None,
    assumed: bool = False,
) -> dict:
    edge = {
        "from": from_node,
        "to": to_node,
        "mode": mode,
        "minutes": int(minutes),
        "confidence": confidence,
        "basis": basis,
    }
    if distance_km is not None:
        edge["distanceKm"] = round(float(distance_km), 2)
    if assumed:
        edge["assumed"] = True
    return edge


def stop_access_edge(island, stop) -> dict:
    distance = haversine_km(island["lat"], island["lon"], stop["lat"], stop["lon"])
    effective = distance * WALK_DETOUR
    if effective <= LOCAL_TRANSPORT_THRESHOLD_KM:
        minutes = max(1, math.ceil(effective / WALK_SPEED_KMH * 60))
        return access_edge(
            f"island:{island['id']}",
            f"stop:{stop['id']}",
            mode="walk",
            minutes=minutes,
            confidence="estimated_access",
            basis=(
                "island centroid to RTL stop: 4.5 km/h walk with 1.25 detour "
                f"({distance:.2f} km direct)"
            ),
            distance_km=distance,
        )
    minutes = max(1, math.ceil(distance / LOCAL_TRANSPORT_SPEED_KMH * 60) + LOCAL_TRANSPORT_BOARD_MIN)
    return access_edge(
        f"island:{island['id']}",
        f"stop:{stop['id']}",
        mode="road",
        minutes=minutes,
        confidence="assumption",
        basis=(
            "island centroid to RTL stop >1.5 km: estimated local transport "
            f"25 km/h + {LOCAL_TRANSPORT_BOARD_MIN} min ({distance:.2f} km direct)"
        ),
        distance_km=distance,
        assumed=True,
    )


def build_stops(master, islands, resolver, aliases):
    stops_df = pd.read_csv(STOPS_CSV, encoding="utf-8-sig")
    scheduled = stops_df[stops_df["scheduled"].astype(str).str.strip().str.lower() == "yes"].copy()
    scheduled = scheduled.sort_values("code")
    if len(scheduled) != 117:
        raise ValueError(f"expected 117 scheduled stops, found {len(scheduled)}")

    islands_by_id = {item["id"]: item for item in islands}
    stops = []
    for row in scheduled.itertuples():
        code = str(int(row.code))
        result = resolver.resolve("rtl_stops", row.atoll, row.island)
        method = result["method"]
        ids = result["island_ids"]
        reason = result.get("reason", "")
        if not ids:
            raise ValueError(f"unresolved RTL stop {row.name!r} ({row.atoll})")
        primary = ids[0]
        aliases.append(
            {
                "source": "rtl_stops",
                "source_atoll": str(row.atoll).strip(),
                "source_name": str(row.island).strip(),
                "island_id": primary,
                "island_name": islands_by_id[primary]["name"],
                "method": method,
                "score": alias_score(method, result.get("score")),
                "reviewed": alias_reviewed(method),
                "reason": reason,
            }
        )
        for extra in ids[1:]:
            aliases.append(
                {
                    "source": "rtl_stops",
                    "source_atoll": str(row.atoll).strip(),
                    "source_name": str(row.island).strip(),
                    "island_id": extra,
                    "island_name": islands_by_id[extra]["name"],
                    "method": method,
                    "score": alias_score(method, result.get("score")),
                    "reviewed": alias_reviewed(method),
                    "reason": "combined Hulhumeedhoo stop (Hulhudhoo + Meedhoo landmass)",
                }
            )
        stops.append(
            {
                "id": f"RTL:{code}",
                "code": code,
                "name": str(row.name).strip(),
                "islandId": primary,
                "lat": round(float(row.lat), 6),
                "lon": round(float(row.lon), 6),
                "scheduled": True,
            }
        )

    edges = []
    for stop in stops:
        if "." in stop["name"] and stop["name"].split(".", 1)[1].strip() == "Hulhumeedhoo":
            for island_id in ("MV019006", "MV019001"):
                edges.append(
                    access_edge(
                        f"island:{island_id}",
                        f"stop:{stop['id']}",
                        mode="walk",
                        minutes=5,
                        confidence="assumption",
                        basis=(
                            "combined Hulhumeedhoo stop serves the Hulhudhoo + Meedhoo "
                            "landmass; 5 min walk (assumption)"
                        ),
                        distance_km=0.35,
                        assumed=True,
                    )
                )
            continue
        island = islands_by_id[stop["islandId"]]
        edges.append(stop_access_edge(island, stop))
    return stops, edges


def build_ferry_services():
    trips = pd.read_csv(TRIPS_CSV, encoding="utf-8-sig")
    routes = pd.read_csv(ROUTES_CSV, encoding="utf-8-sig")
    stops = pd.read_csv(STOPS_CSV, encoding="utf-8-sig")

    code_by_name = {
        str(row.name).strip(): str(int(row.code)) for row in stops.itertuples()
    }
    if len(code_by_name) != len(stops):
        raise ValueError("RTL stop names are not unique")
    route_by_id = {int(row.route_id): row for row in routes.itertuples()}

    services = []
    for (route_id, trip), group in trips.groupby(["route_id", "trip"], sort=True):
        group = group.sort_values("order")
        route = route_by_id[int(route_id)]
        service_stops = []
        for row in group.itertuples():
            stop_name = str(row.stop).strip()
            stop_code = code_by_name[stop_name]
            minute = parse_hhmm(row.time)
            service_stops.append(
                {
                    "stopId": f"RTL:{stop_code}",
                    "name": stop_name,
                    "sequence": int(row.order),
                    "arrival": minute,
                    "departure": minute,
                }
            )
        services.append(
            {
                "id": f"ferry:{int(route_id)}:{int(trip)}",
                "kind": "timetabled",
                "mode": "ferry",
                "operator": "RTL",
                "routeId": str(int(route_id)),
                "routeCode": str(route.route),
                "zone": str(route.zone),
                "confidence": "verified_timetable",
                "calendar": "reference_day_all_recorded_trips",
                "source": "data/team-kandu/rtl_trips.csv",
                "stops": service_stops,
            }
        )

    if len(services) != 102:
        raise ValueError(f"expected 102 RTL trips, found {len(services)}")
    services.sort(key=lambda item: (int(item["routeId"]), int(item["id"].split(":")[-1])))
    return services


# ---------------------------------------------------------------------------
# Airports and air services
# ---------------------------------------------------------------------------


def build_airports(master, airports_df, islands, resolver, aliases):
    islands_by_id = {item["id"]: item for item in islands}
    operational = airports_df[
        airports_df["iata"].notna()
        & airports_df["status"].astype(str).str.strip().str.lower().str.startswith("operational")
    ].copy()
    operational = operational.sort_values("iata")
    if len(operational) != 20:
        raise ValueError(f"expected 20 operational airports, found {len(operational)}")

    airports = []
    for row in operational.itertuples():
        iata = str(row.iata).strip()
        hosts = master[master["airport_iata"].astype(str).str.strip() == iata]
        if len(hosts) != 1:
            raise ValueError(f"expected exactly one master airport_iata row for {iata}, found {len(hosts)}")
        host_pcode = hosts.index[0]
        host = islands_by_id[host_pcode]
        same_name = norm(row.island) == norm(host["name"])
        method = "exact" if same_name else "manual"
        aliases.append(
            {
                "source": "airports",
                "source_atoll": str(row.atoll_code).strip(),
                "source_name": str(row.island).strip(),
                "island_id": host_pcode,
                "island_name": host["name"],
                "method": method,
                "score": alias_score(method, 1.0),
                "reviewed": "true",
                "reason": "" if same_name else "airport island joined via master airport_iata",
            }
        )
        airports.append(
            {
                "id": iata,
                "iata": iata,
                "name": str(row.name).strip(),
                "islandId": host_pcode,
                "lat": round(float(row.lat), 6),
                "lon": round(float(row.lon), 6),
            }
        )
    return airports


def airport_access_edges(airports, islands, stops):
    islands_by_id = {item["id"]: item for item in islands}
    stops_by_island = defaultdict(list)
    for stop in stops:
        stops_by_island[stop["islandId"]].append(stop)
    edges = []

    def walk(from_node, to_node, lat1, lon1, lat2, lon2, basis, assumed=False, confidence="estimated_access"):
        distance = haversine_km(lat1, lon1, lat2, lon2)
        minutes = max(1, math.ceil(distance * WALK_DETOUR / WALK_SPEED_KMH * 60))
        edges.append(
            access_edge(
                from_node,
                to_node,
                mode="walk",
                minutes=minutes,
                confidence=confidence,
                basis=basis,
                distance_km=distance,
                assumed=assumed,
            )
        )

    def road(pcode_a, pcode_b, basis):
        a, b = islands_by_id[pcode_a], islands_by_id[pcode_b]
        distance = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]) * ROAD_DETOUR
        minutes = max(1, math.ceil(distance / ROAD_SPEED_KMH * 60) + ROAD_PENALTY_MIN)
        edges.append(
            access_edge(
                f"island:{pcode_a}",
                f"island:{pcode_b}",
                mode="road",
                minutes=minutes,
                confidence="assumption",
                basis=basis,
                distance_km=distance,
                assumed=True,
            )
        )

    def speedboat(from_node, pcode, basis):
        target = islands_by_id[pcode]
        # caller supplies coordinates through closure variables
        origin_lat, origin_lon = speedboat.origin
        distance = haversine_km(origin_lat, origin_lon, target["lat"], target["lon"])
        minutes = max(1, math.ceil(distance / SPEEDBOAT_SPEED_KMH * 60) + SPEEDBOAT_BOARD_MIN)
        edges.append(
            access_edge(
                from_node,
                f"island:{pcode}",
                mode="speedboat",
                minutes=minutes,
                confidence="assumption",
                basis=basis,
                distance_km=distance,
                assumed=True,
            )
        )

    for airport in airports:
        host = islands_by_id[airport["islandId"]]
        iata = airport["iata"]
        airport_node = f"airport:{iata}"
        walk(
            f"island:{host['id']}",
            airport_node,
            host["lat"],
            host["lon"],
            airport["lat"],
            airport["lon"],
            "airport terminal on host island; 4.5 km/h walk with 1.25 detour",
        )

        # Airports with an RTL stop on the same island are reached on foot from the jetty.
        if host["status"] == "airport":
            island_stops = stops_by_island.get(host["id"], [])
            if island_stops:
                for stop in island_stops:
                    walk(
                        airport_node,
                        f"stop:{stop['id']}",
                        airport["lat"],
                        airport["lon"],
                        stop["lat"],
                        stop["lon"],
                        "airport terminal to same-island RTL ferry stop; walk estimate",
                    )

        if iata == "HRF":
            town = islands_by_id["MV001006"]
            walk(
                airport_node,
                "island:MV001006",
                airport["lat"],
                airport["lon"],
                town["lat"],
                town["lon"],
                (
                    "Hoarafushi Airport (MV001031) to Hoarafushi town (MV001006) via the "
                    "short causeway/walk (~1 km); labelled assumption"
                ),
                assumed=True,
                confidence="assumption",
            )
        elif iata == "LMV":
            speedboat.origin = (airport["lat"], airport["lon"])
            speedboat(
                airport_node,
                "MV005002",
                (
                    "no RTL ferry on Lh Madivaru; estimated speedboat to Naifaru "
                    "(nearest inhabited island), 25 km/h + 10 min boarding"
                ),
            )
        elif iata == "FMT":
            speedboat.origin = (airport["lat"], airport["lon"])
            speedboat(
                airport_node,
                "MV017008",
                (
                    "Maarehaa airport island has no RTL stop; estimated speedboat transfer "
                    "to Faresmaathodaa town (MV017008), 25 km/h + 10 min boarding"
                ),
            )
        elif iata == "MLE":
            road("MV021001", "MV009052", "Sinamalé Bridge, Malé to Hulhulé (1.39 km); 40 km/h + 3 min assumption")
            road("MV021003", "MV009052", "Hulhulé to Hulhumalé link road/causeway; 40 km/h + 3 min assumption")
        elif iata == "KDO":
            road("MV015008", "MV015045", "Laamu Link Road: Fonadhoo to Kadhdhoo Airport; 40 km/h + 3 min assumption")
            road("MV015045", "MV015013", "Laamu Link Road: Kadhdhoo Airport to Gan (Laamu); 40 km/h + 3 min assumption")
        elif iata == "GAN":
            road("MV019002", "MV019003", "Addu Link Road: Hithadhoo to Maradhoo; 40 km/h + 3 min assumption")
            road("MV019003", "MV019005", "Addu Link Road: Maradhoo to Maradhoofeydhoo; 40 km/h + 3 min assumption")
            road("MV019005", "MV019004", "Addu Link Road: Maradhoofeydhoo to Feydhoo; 40 km/h + 3 min assumption")
            road("MV019004", "MV019033", "Addu Link Road: Feydhoo to Gan (airport); 40 km/h + 3 min assumption")
    return edges


def generated_departures(count: int) -> list[int]:
    """Evenly spread `count` departures over the 06:00-18:00 operating window."""
    if count <= 1:
        return [720]
    step = (AIR_WINDOW_END - AIR_WINDOW_START) / count
    return [
        int(round(AIR_WINDOW_START + step * (index + 0.5)))
        for index in range(count)
    ]


def build_air_services(airports, excluded_routes):
    routes = pd.read_csv(AIR_ROUTES_CSV, encoding="utf-8-sig")
    airport_iatas = {airport["iata"] for airport in airports}
    services = []
    operating = routes[
        routes["status"].astype(str).str.contains("operating", case=False, na=False)
    ].copy()
    if len(operating) != 32:
        raise ValueError(f"expected 32 rows with status containing 'operating', found {len(operating)}")

    included_pairs = set()
    for row in operating.itertuples():
        origin = str(row.origin_iata).strip().upper()
        destination = str(row.dest_iata).strip().upper()
        status = str(row.status).strip()
        if len(origin) != 3 or len(destination) != 3 or origin not in airport_iatas or destination not in airport_iatas:
            excluded_routes.append(
                {
                    "from": origin,
                    "to": str(row.dest_iata).strip(),
                    "status": status,
                    "reason": (
                        "operating row is an aggregate seaplane/resort-water-aerodrome entry "
                        "with no IATA destination and no frequency or block time; not a "
                        "scheduled airport pair"
                    ),
                }
            )
            continue
        if is_blank(row.weekly_frequency_each_way) or is_blank(row.block_time_min):
            excluded_routes.append(
                {
                    "from": origin,
                    "to": destination,
                    "status": status,
                    "reason": "missing weekly frequency or block time",
                }
            )
            continue

        pair = tuple(sorted((origin, destination)))
        if pair in included_pairs:
            raise ValueError(f"duplicate operating airport pair {origin}-{destination}")
        included_pairs.add(pair)

        weekly = max(1, int(round(float(row.weekly_frequency_each_way))))
        per_day = max(1, int(round(weekly / 7)))
        block = int(round(float(row.block_time_min)))
        departures = generated_departures(per_day)
        for start, end in ((origin, destination), (destination, origin)):
            services.append(
                {
                    "id": f"air:{start}-{end}",
                    "kind": "frequency",
                    "mode": "air",
                    "fromNode": f"airport:{start}",
                    "toNode": f"airport:{end}",
                    "fromAirport": start,
                    "toAirport": end,
                    "airline": str(row.airline).strip(),
                    "weeklyFrequency": weekly,
                    "departuresPerDay": per_day,
                    "operatingWindow": {"start": AIR_WINDOW_START, "end": AIR_WINDOW_END},
                    "blockMinutes": block,
                    "departures": departures,
                    "confidence": "estimated_frequency",
                    "status": status,
                    "source": "data/external/air/domestic_routes.csv",
                }
            )

    # Non-operating rows are recorded, not silently dropped.
    for row in routes.itertuples():
        status = str(row.status).strip()
        if "operating" in status.lower():
            continue
        from_iata = str(row.origin_iata).strip().upper()
        to_iata = str(row.dest_iata).strip().upper()
        if "ceased" in status.lower():
            reason = "excluded: ceased/ceasing service (Manta exiting domestic ATR operations)"
        elif "suspended" in status.lower():
            reason = "excluded: suspended / resuming unconfirmed"
        else:
            reason = "excluded: observed July 2026 only; not operating in the October 2026 reference snapshot"
        excluded_routes.append(
            {"from": from_iata, "to": to_iata, "status": status, "reason": reason}
        )

    services.sort(key=lambda item: item["id"])
    return services, len(included_pairs)


def build_villemale_ferry():
    departures = list(range(360, 1320, 15))
    services = []
    for start, end in (("MV021001", "MV021002"), ("MV021002", "MV021001")):
        services.append(
            {
                "id": f"ferry:{start}-{end}",
                "kind": "frequency",
                "mode": "ferry",
                "fromNode": f"island:{start}",
                "toNode": f"island:{end}",
                "weeklyFrequency": len(departures) * 7,
                "departuresPerDay": len(departures),
                "operatingWindow": {"start": 360, "end": 1320},
                "blockMinutes": 7,
                "departures": departures,
                "confidence": "estimated_frequency",
                "status": "published frequency (modelled; not observed timetable)",
                "source": "research/03_transport_network_and_methods.md",
            }
        )
    return services


# ---------------------------------------------------------------------------
# Facilities
# ---------------------------------------------------------------------------


def health_categories(tier: str) -> list[str]:
    categories = ["health_any"]
    if tier in HEALTH_HOSPITAL_TIERS:
        categories.append("health_hospital")
    if tier.startswith(("1_", "2_")):
        categories.append("health_regional_tertiary")
    return categories


def build_health_facilities(resolver, islands, aliases):
    health = pd.read_csv(HEALTH_CSV, encoding="utf-8-sig")
    if len(health) != 197:
        raise ValueError(f"expected 197 health rows, found {len(health)}")
    islands_by_id = {item["id"]: item for item in islands}
    facilities = []
    excluded = []
    seen_ids = set()

    for index, row in health.iterrows():
        atoll_raw = "" if is_blank(row["atoll_code"]) else str(row["atoll_code"]).strip()
        name_raw = "" if is_blank(row["island"]) else str(row["island"]).strip()
        facility_name = "" if is_blank(row["hems_name"]) else str(row["hems_name"]).strip()
        tier = "" if is_blank(row["tier"]) else str(row["tier"]).strip()

        if not facility_name or is_blank(row["hems_establishment_id"]):
            aliases.append(
                {
                    "source": "health",
                    "source_atoll": atoll_raw,
                    "source_name": name_raw,
                    "island_id": "",
                    "island_name": "",
                    "method": "unresolved",
                    "score": "",
                    "reviewed": "false",
                    "reason": "aggregate/placeholder row with no facility name or establishment id",
                }
            )
            excluded.append(
                {
                    "source": "health",
                    "row": int(index) + 1,
                    "atoll": atoll_raw,
                    "island": name_raw,
                    "name": facility_name,
                    "tier": tier,
                    "reason": "missing hems_name / hems_establishment_id",
                }
            )
            continue

        if not name_raw or not atoll_raw:
            aliases.append(
                {
                    "source": "health",
                    "source_atoll": atoll_raw,
                    "source_name": name_raw,
                    "island_id": "",
                    "island_name": "",
                    "method": "unresolved",
                    "score": "",
                    "reviewed": "false",
                    "reason": "no island/atoll recorded in health master",
                }
            )
            excluded.append(
                {
                    "source": "health",
                    "row": int(index) + 1,
                    "atoll": atoll_raw,
                    "island": name_raw,
                    "name": facility_name,
                    "tier": tier,
                    "reason": "no island/atoll recorded in health master",
                }
            )
            continue

        result = resolver.resolve("health", atoll_raw, name_raw)
        method = result["method"]
        ids = result["island_ids"]
        aliases.append(
            {
                "source": "health",
                "source_atoll": atoll_raw,
                "source_name": name_raw,
                "island_id": ids[0] if ids else "",
                "island_name": islands_by_id[ids[0]]["name"] if ids else "",
                "method": method,
                "score": alias_score(method, result.get("score")),
                "reviewed": alias_reviewed(method),
                "reason": result.get("reason", ""),
            }
        )
        if not ids:
            excluded.append(
                {
                    "source": "health",
                    "row": int(index) + 1,
                    "atoll": atoll_raw,
                    "island": name_raw,
                    "name": facility_name,
                    "tier": tier,
                    "reason": result.get("reason", "unresolved island"),
                }
            )
            continue

        facility_id = f"health:hems:{int(float(row['hems_establishment_id']))}"
        if facility_id in seen_ids:
            continue
        seen_ids.add(facility_id)
        facility = {
            "id": facility_id,
            "name": facility_name,
            "islandId": ids[0],
            "kind": "health",
            "categories": health_categories(tier),
            "precision": "island",
            "source": "data/external/health/_derived/public_health_facility_master.csv",
            "reviewed": method in {"exact", "manual"},
        }
        if tier:
            facility["tier"] = tier
        mhs_category = row.get("mhs2020_category")
        if not is_blank(mhs_category):
            facility["type"] = str(mhs_category).strip()
        facilities.append(facility)

    return facilities, excluded


def build_education_facilities(resolver, islands, aliases):
    education = pd.read_csv(EDUCATION_CSV, encoding="utf-8-sig")
    if len(education) != 483:
        raise ValueError(f"expected 483 education rows, found {len(education)}")
    islands_by_id = {item["id"]: item for item in islands}
    facilities = []
    excluded = []
    duplicate_rows = []
    seen_locations = set()

    for index, row in education.iterrows():
        institution = "" if is_blank(row["institution"]) else str(row["institution"]).strip()
        row_type = "" if is_blank(row["type"]) else str(row["type"]).strip()
        campus = "" if is_blank(row["campus"]) else str(row["campus"]).strip()
        island_raw = "" if is_blank(row["island"]) else str(row["island"]).strip()
        atoll_raw = "" if is_blank(row["atoll_code"]) else str(row["atoll_code"]).strip()
        atoll_text = "" if is_blank(row["atoll"]) else str(row["atoll"]).strip()

        if row_type == "institution total (all campuses)":
            aliases.append(
                {
                    "source": "education",
                    "source_atoll": atoll_raw,
                    "source_name": island_raw,
                    "island_id": "",
                    "island_name": "",
                    "method": "unresolved",
                    "score": "",
                    "reviewed": "false",
                    "reason": "aggregate institution-total row (all campuses)",
                }
            )
            excluded.append(
                {
                    "source": "education",
                    "row": int(index) + 1,
                    "institution": institution,
                    "type": row_type,
                    "island": island_raw,
                    "reason": "aggregate institution-total row",
                }
            )
            continue

        if not island_raw or not (atoll_raw or atoll_text):
            reason = "blank island/atoll in education register"
            aliases.append(
                {
                    "source": "education",
                    "source_atoll": atoll_raw or atoll_text,
                    "source_name": island_raw,
                    "island_id": "",
                    "island_name": "",
                    "method": "unresolved",
                    "score": "",
                    "reviewed": "false",
                    "reason": reason,
                }
            )
            excluded.append(
                {
                    "source": "education",
                    "row": int(index) + 1,
                    "institution": institution,
                    "type": row_type,
                    "island": island_raw,
                    "reason": reason,
                }
            )
            continue

        atoll_lookup = atoll_raw or atoll_text
        result = resolver.resolve("education", atoll_lookup, island_raw)
        method = result["method"]
        ids = result["island_ids"]
        aliases.append(
            {
                "source": "education",
                "source_atoll": atoll_raw or atoll_text,
                "source_name": island_raw,
                "island_id": ids[0] if ids else "",
                "island_name": islands_by_id[ids[0]]["name"] if ids else "",
                "method": method,
                "score": alias_score(method, result.get("score")),
                "reviewed": alias_reviewed(method),
                "reason": result.get("reason", ""),
            }
        )
        if not ids:
            excluded.append(
                {
                    "source": "education",
                    "row": int(index) + 1,
                    "institution": institution,
                    "type": row_type,
                    "island": island_raw,
                    "reason": result.get("reason", "unresolved island"),
                }
            )
            continue

        location_key = (institution, campus, island_raw)
        if location_key in seen_locations:
            duplicate_rows.append(
                {
                    "row": int(index) + 1,
                    "institution": institution,
                    "campus": campus,
                    "island": island_raw,
                }
            )
            continue
        seen_locations.add(location_key)

        categories = []
        offers = row.get("offers_grade_11_12")
        offers_true = bool(offers) if isinstance(offers, bool) else str(offers).strip().lower() == "true"
        if offers_true:
            categories.append("education_grade_11_12")
        if row_type in EDUCATION_HIGHER_ED_TYPES:
            categories.append("education_higher_ed")
        if row_type in EDUCATION_SCHOOL_TYPES:
            categories.append("education_school")

        name = institution
        if campus and campus.lower() not in {"all", "(no campus listed)"}:
            name = f"{institution} — {campus}"

        facility = {
            "id": f"education:{int(index) + 1:04d}",
            "name": name,
            "islandId": ids[0],
            "kind": "education",
            "categories": categories,
            "precision": "island",
            "source": "data/external/education/institutions_master.csv",
            "reviewed": method in {"exact", "manual"},
        }
        if row_type:
            facility["type"] = row_type
        facilities.append(facility)

    return facilities, excluded, duplicate_rows


# ---------------------------------------------------------------------------
# GeoJSON
# ---------------------------------------------------------------------------


def perpendicular_distance(point, start, end) -> float:
    if start == end:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    x, y = point
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def douglas_peucker(points, tolerance):
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    max_distance = 0.0
    index = 0
    for candidate in range(1, len(points) - 1):
        distance = perpendicular_distance(points[candidate], start, end)
        if distance > max_distance:
            max_distance = distance
            index = candidate
    if max_distance > tolerance:
        left = douglas_peucker(points[: index + 1], tolerance)
        right = douglas_peucker(points[index:], tolerance)
        return left[:-1] + right
    return [start, end]


def simplify_ring(ring, tolerance=GEOJSON_TOLERANCE, decimals=GEOJSON_DECIMALS):
    if len(ring) < 4:
        rounded = [[round(float(x), decimals), round(float(y), decimals)] for x, y in ring]
        return rounded
    points = ring[:-1] if ring[0] == ring[-1] else ring
    simplified = douglas_peucker(points, tolerance)
    if simplified[0] != simplified[-1]:
        simplified = simplified + [simplified[0]]
    rounded = []
    for x, y in simplified:
        point = [round(float(x), decimals), round(float(y), decimals)]
        if not rounded or rounded[-1] != point:
            rounded.append(point)
    if len(rounded) < 4:
        rounded = [
            [round(float(x), decimals), round(float(y), decimals)] for x, y in points
        ]
        rounded.append(rounded[0])
    if rounded[0] != rounded[-1]:
        rounded.append(rounded[0])
    return rounded


def simplify_geometry(geometry):
    if geometry["type"] == "Polygon":
        coordinates = [simplify_ring(ring) for ring in geometry["coordinates"]]
    elif geometry["type"] == "MultiPolygon":
        coordinates = [
            [simplify_ring(ring) for ring in polygon]
            for polygon in geometry["coordinates"]
        ]
    else:
        raise ValueError(f"unsupported geometry type: {geometry['type']}")
    return {"type": geometry["type"], "coordinates": coordinates}


INTERVENTION_SOURCES = (
    (
        "diagnostics",
        DIAGNOSTIC_SERVICES_CSV,
        "Diagnostics & procedures",
        396,
    ),
    (
        "specialist",
        SPECIALIST_SERVICES_CSV,
        "Specialist services",
        787,
    ),
    (
        "dental",
        DENTAL_SERVICES_CSV,
        "Dental",
        222,
    ),
)

SERVICE_LABELS = {
    "blood_bank": "Blood bank",
    "ct": "CT scan",
    "endoscopy": "Endoscopy",
    "histopathology": "Histopathology",
    "lab_advanced": "Advanced laboratory",
    "lab_basic": "Basic laboratory",
    "mammography": "Mammography",
    "mri": "MRI",
    "pcr_molecular": "PCR / molecular testing",
    "ultrasound": "Ultrasound",
    "xray": "X-ray",
    "dental": "Dental services",
    "cardiology": "Cardiology",
    "dermatology": "Dermatology",
    "developmental_therapy": "Developmental therapy",
    "dialysis": "Dialysis",
    "drug_rehab": "Drug rehabilitation",
    "emergency": "Emergency care",
    "ent": "ENT",
    "fertility": "Fertility",
    "gastroenterology": "Gastroenterology",
    "geriatrics": "Geriatrics",
    "hyperbaric": "Hyperbaric medicine",
    "icu": "Intensive care",
    "maternity": "Maternity",
    "ncd_diabetes": "NCD / diabetes",
    "nephrology": "Nephrology",
    "nicu": "Neonatal intensive care",
    "oncology": "Oncology",
    "ophthalmology": "Ophthalmology",
    "orthopaedics": "Orthopaedics",
    "paediatrics": "Paediatrics",
    "physiotherapy": "Physiotherapy",
    "psychiatry": "Psychiatry",
    "pulmonology": "Pulmonology",
    "rheumatology": "Rheumatology",
    "sports_medicine": "Sports medicine",
    "surgery": "Surgery",
    "telemedicine": "Telemedicine",
    "thalassaemia": "Thalassaemia",
    "urology": "Urology",
    "visiting_specialist": "Visiting specialist",
}

RESORT_ROW_RE = re.compile(r"\b(resort|guest|safari|liveaboard|hotel)\b", re.IGNORECASE)
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def build_intervention_facilities(resolver, islands):
    """Build the additive evidence-based intervention service layer.

    Rows on resort/guest-only islands and rows whose island cannot be resolved
    are excluded from the served facility list but counted in the returned
    metadata.  Facilities are merged on (normalised facility name, island id);
    duplicate evidence rows for the same category collapse to the strongest,
    most recent evidence item.
    """
    islands_by_id = {item["id"]: item for item in islands}
    rows_used = []
    excluded_resort = []
    unresolved = []
    source_counts = {}
    source_category_sets = {}
    manual_counts = Counter()

    for source_key, source_path, group, expected_rows in INTERVENTION_SOURCES:
        frame = pd.read_csv(source_path, encoding="utf-8-sig", dtype=str)
        if len(frame) != expected_rows:
            raise ValueError(
                f"expected {expected_rows} {source_key} rows, found {len(frame)}"
            )
        source_counts[source_key] = len(frame)
        source_category_sets[source_key] = set(frame["service_category"].dropna().astype(str))

        for index, row in frame.iterrows():
            atoll_raw = "" if is_blank(row["atoll"]) else str(row["atoll"]).strip()
            island_raw = "" if is_blank(row["island"]) else str(row["island"]).strip()
            facility_name = (
                "" if is_blank(row["facility_name"]) else str(row["facility_name"]).strip()
            )
            category = (
                "" if is_blank(row["service_category"]) else str(row["service_category"]).strip()
            )
            row_number = int(index) + 2  # 1-based, including the CSV header

            if island_raw and RESORT_ROW_RE.search(island_raw):
                excluded_resort.append(
                    {
                        "source": source_key,
                        "row": row_number,
                        "atoll": atoll_raw,
                        "island": island_raw,
                        "name": facility_name,
                        "reason": "resort/guest-only island row excluded",
                    }
                )
                continue

            if not facility_name or not category:
                unresolved.append(
                    {
                        "source": source_key,
                        "row": row_number,
                        "atoll": atoll_raw,
                        "island": island_raw,
                        "name": facility_name,
                        "reason": "blank facility name or service category",
                    }
                )
                continue

            result = resolver.resolve(
                "intervention", atoll_raw, island_raw, allow_fuzzy=False
            )
            if result["method"] not in {"exact", "manual"} or not result["island_ids"]:
                unresolved.append(
                    {
                        "source": source_key,
                        "row": row_number,
                        "atoll": atoll_raw,
                        "island": island_raw,
                        "name": facility_name,
                        "reason": result.get("reason", "unresolved island"),
                    }
                )
                continue

            island_id = result["island_ids"][0]
            if result["method"] == "manual":
                manual_counts[(atoll_raw, island_raw, island_id)] += 1
            rows_used.append(
                {
                    "source": source_key,
                    "sourcePath": str(source_path.relative_to(ROOT)),
                    "group": group,
                    "facilityName": facility_name,
                    "islandId": island_id,
                    "atoll": atoll_raw,
                    "island": island_raw,
                    "category": category,
                    "detail": (
                        "" if is_blank(row["service_detail"]) else str(row["service_detail"]).strip()
                    ),
                    "confidence": (
                        "" if is_blank(row["confidence"]) else str(row["confidence"]).strip().lower()
                    ),
                    "sourceUrl": "" if is_blank(row["source_url"]) else str(row["source_url"]).strip(),
                    "sourceDate": (
                        "" if is_blank(row["source_date"]) else str(row["source_date"]).strip()
                    ),
                    "facilityType": (
                        "" if is_blank(row["facility_type"]) else str(row["facility_type"]).strip()
                    ),
                }
            )

    grouped = defaultdict(list)
    for record in rows_used:
        grouped[(norm(record["facilityName"]), record["islandId"])].append(record)

    facilities = []
    duplicate_evidence_merged = 0
    category_stats = {}
    for (name_key, island_id), records in sorted(grouped.items()):
        records.sort(
            key=lambda item: (
                item["source"],
                item["facilityName"],
                item["category"],
                -CONFIDENCE_RANK.get(item["confidence"], 0),
                item["sourceDate"],
            )
        )
        display_names = Counter(item["facilityName"] for item in records)
        display_name = sorted(display_names.items(), key=lambda item: (-item[1], item[0]))[0][0]
        best_by_category = {}
        for record in records:
            category = record["category"]
            score = (
                CONFIDENCE_RANK.get(record["confidence"], 0),
                record["sourceDate"],
                len(record["detail"]),
                record["detail"],
                record["sourceUrl"],
            )
            previous = best_by_category.get(category)
            if previous is None:
                best_by_category[category] = (score, record)
            else:
                duplicate_evidence_merged += 1
                if score > previous[0]:
                    best_by_category[category] = (score, record)
        evidence = []
        categories = []
        for category in sorted(best_by_category):
            _, record = best_by_category[category]
            evidence.append(
                {
                    "category": f"service:{category}",
                    "detail": record["detail"],
                    "confidence": record["confidence"],
                    "source": record["sourcePath"],
                    "sourceDate": record["sourceDate"],
                }
            )
            categories.append(f"service:{category}")
            stats = category_stats.setdefault(
                category,
                {
                    "facilityIds": set(),
                    "islandIds": set(),
                    "evidenceRows": 0,
                    "confidence": Counter(),
                    "sources": set(),
                    "group": record["group"],
                    "sourcePath": record["sourcePath"],
                },
            )
            stats["facilityIds"].add(f"{name_key}:{island_id}")
            stats["islandIds"].add(island_id)
            stats["evidenceRows"] += 1
            stats["confidence"][record["confidence"] or "unknown"] += 1
            stats["sources"].add(record["sourcePath"])

        sources = sorted({item["sourcePath"] for item in records})
        dates = [item["sourceDate"] for item in records if item["sourceDate"]]
        facility_types = Counter(item["facilityType"] for item in records if item["facilityType"])
        slug = re.sub(r"[^a-z0-9]+", "-", name_key).strip("-") or "facility"
        facility = {
            "id": f"health:service:{slug}:{island_id}",
            "name": display_name,
            "islandId": island_id,
            "kind": "health",
            "categories": categories,
            "serviceCategories": categories,
            "serviceEvidence": evidence,
            "userAdded": False,
            "precision": "island",
            "source": "; ".join(sources),
            "reviewed": True,
        }
        if dates:
            facility["sourceDate"] = max(dates)
        if facility_types:
            facility["type"] = sorted(
                facility_types.items(), key=lambda item: (-item[1], item[0])
            )[0][0]
        facilities.append(facility)

    facilities.sort(key=lambda item: item["id"])
    service_meta = {
        "source": "; ".join(str(path.relative_to(ROOT)) for _, path, _, _ in INTERVENTION_SOURCES),
        "note": (
            "Evidence-based intervention and specialist service layer. Categories are "
            "derived only from the three service CSVs; they are not inferred from facility tier."
        ),
        "rowsRead": sum(source_counts.values()),
        "rowsExcludedResort": len(excluded_resort),
        "rowsExcludedUnresolvedIsland": len(unresolved),
        "categories": len(category_stats),
        "facilities": len(facilities),
        "confidenceNote": (
            "Service evidence carries the source confidence (high/medium/low) and date; "
            "facility locations are island centroids, not building coordinates."
        ),
        "rowsUsed": len(rows_used),
        "bySourceFile": dict(sorted(source_counts.items())),
    }

    unresolved_groups = Counter((item["source"], item["atoll"], item["island"]) for item in unresolved)
    report = {
        "rowsRead": sum(source_counts.values()),
        "rowsExcludedResort": len(excluded_resort),
        "rowsExcludedUnresolvedIsland": len(unresolved),
        "rowsUsed": len(rows_used),
        "facilities": len(facilities),
        "categories": len(category_stats),
        "evidenceItems": sum(len(item["serviceEvidence"]) for item in facilities),
        "duplicateEvidenceRowsMerged": duplicate_evidence_merged,
        "bySourceFile": dict(sorted(source_counts.items())),
        "unresolvedRows": unresolved,
        "unresolvedGroups": [
            {
                "source": source,
                "atoll": atoll,
                "island": island,
                "rows": count,
            }
            for (source, atoll, island), count in sorted(unresolved_groups.items())
        ],
        "resortRows": excluded_resort,
        "manualOverrides": [
            {
                "source": "intervention",
                "atoll": atoll,
                "island": island,
                "islandId": island_id,
                "islandName": islands_by_id[island_id]["name"],
                "rows": count,
            }
            for (atoll, island, island_id), count in sorted(manual_counts.items())
        ],
    }
    return facilities, service_meta, report, category_stats


def intervention_category_definitions(category_stats):
    definitions = []
    for category in sorted(category_stats):
        stats = category_stats[category]
        confidence = stats["confidence"]
        definitions.append(
            {
                "id": f"service:{category}",
                "label": SERVICE_LABELS.get(category, category.replace("_", " ").title()),
                "definition": (
                    f"Facilities with source evidence of {SERVICE_LABELS.get(category, category)} "
                    f"in the {stats['group'].lower()} service table. No service is inferred "
                    "from facility tier."
                ),
                "confidenceNote": (
                    f"{stats['evidenceRows']} evidence rows; confidence high "
                    f"{confidence.get('high', 0)} / medium {confidence.get('medium', 0)} / "
                    f"low {confidence.get('low', 0)}. Resort/guest-only and unresolved-island "
                    "rows are excluded."
                ),
                "kind": "intervention",
                "group": stats["group"],
                "source": stats["sourcePath"],
                "facilityCount": len(stats["facilityIds"]),
                "islandCount": len(stats["islandIds"]),
            }
        )
    return definitions


def build_geojson(islands):
    with open(GEOJSON_SRC, encoding="utf-8") as handle:
        source = json.load(handle)
    features_by_id = {
        feature["properties"]["adm2_pcode"]: feature for feature in source["features"]
    }
    features = []
    missing = []
    for island in sorted(islands, key=lambda item: item["id"]):
        feature = features_by_id.get(island["id"])
        if feature is None or feature.get("geometry") is None:
            missing.append(island["id"])
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "islandId": island["id"],
                    "name": island["name"],
                    "atoll": island["atoll"],
                    "population": island["population"],
                    "status": island["status"],
                    "isOrigin": island["isOrigin"],
                    "lat": island["lat"],
                    "lon": island["lon"],
                },
                "geometry": simplify_geometry(feature["geometry"]),
            }
        )
    if missing:
        raise ValueError(f"missing polygons for node islands: {missing}")
    if len(features) != 200:
        raise ValueError(f"expected 200 geojson features, found {len(features)}")
    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# Report and main
# ---------------------------------------------------------------------------


def origin_access_summary(islands, access_edges, services):
    """Origins with any incident access edge or frequency service.

    This is a coverage statement, not a reachability claim: an origin can have an
    access edge and still have no destination itinerary on a given day.
    """
    origins = [island for island in islands if island["isOrigin"]]
    origin_ids = {island["id"] for island in origins}
    by_id = {island["id"]: island for island in origins}

    access_edge_ids = set()
    for edge in access_edges:
        for side in (edge["from"], edge["to"]):
            if side.startswith("island:"):
                island_id = side[len("island:"):]
                if island_id in origin_ids:
                    access_edge_ids.add(island_id)

    frequency_ids = set()
    for service in services:
        if service.get("kind") != "frequency":
            continue
        for side in (service.get("fromNode"), service.get("toNode")):
            if isinstance(side, str) and side.startswith("island:"):
                island_id = side[len("island:"):]
                if island_id in origin_ids:
                    frequency_ids.add(island_id)

    with_access = access_edge_ids | frequency_ids
    without_access = origin_ids - with_access

    def describe(ids):
        return [
            {
                "id": island_id,
                "name": by_id[island_id]["name"],
                "atoll": by_id[island_id]["atoll"],
                "population": by_id[island_id]["population"],
            }
            for island_id in sorted(ids)
        ]

    by_atoll = {}
    for island in origins:
        entry = by_atoll.setdefault(
            island["atoll"],
            {
                "atoll": island["atoll"],
                "atollName": island["atollName"],
                "origins": 0,
                "withAccess": 0,
                "withoutAccess": 0,
                "population": 0,
                "populationWithAccess": 0,
                "populationWithoutAccess": 0,
            },
        )
        entry["origins"] += 1
        entry["population"] += island["population"]
        if island["id"] in with_access:
            entry["withAccess"] += 1
            entry["populationWithAccess"] += island["population"]
        else:
            entry["withoutAccess"] += 1
            entry["populationWithoutAccess"] += island["population"]

    return {
        "origins": len(origins),
        "withAccess": len(with_access),
        "withoutAccess": len(without_access),
        "populationOrigins": sum(island["population"] for island in origins),
        "populationWithAccess": sum(by_id[i]["population"] for i in with_access),
        "populationWithoutAccess": sum(by_id[i]["population"] for i in without_access),
        "withAccessViaAccessEdge": len(access_edge_ids),
        "withAccessViaFrequencyOnly": len(frequency_ids - access_edge_ids),
        "byAtoll": [by_atoll[key] for key in sorted(by_atoll)],
        "islandsWithAccess": describe(with_access),
        "islandsWithoutAccess": describe(without_access),
        "note": (
            "Counts origin islands with an incident access edge or frequency service in "
            "this reference-day network. The 67 islands without access have no fixed "
            "RTL/air link in the source data; this is not proof that no transport exists."
        ),
    }


def assignment(value: str):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        raise argparse.ArgumentTypeError("use an ISO-8601 timestamp, e.g. 2026-10-10T00:00:00+05:00")
    return value


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generated-at",
        type=assignment,
        default=None,
        help="ISO-8601 generatedAt override (default: now in Indian/Maldives)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="directory for processed artifacts",
    )
    parser.add_argument(
        "--public-dir",
        type=Path,
        default=DEFAULT_PUBLIC,
        help="web public data directory for the byte-identical copies",
    )
    parser.add_argument(
        "--skip-public",
        action="store_true",
        help="do not write web/public/data copies (used by tests)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = args.generated_at
    if generated_at is None:
        generated_at = datetime.now(timezone(timedelta(hours=5))).isoformat(timespec="seconds")

    master = load_master()
    islands, census_names = build_islands(master)
    islands_by_id = {item["id"]: item for item in islands}
    resolver = IslandResolver(islands, master, MANUAL_ALIASES, census_names)

    aliases = []
    stops, access_edges = build_stops(master, islands, resolver, aliases)

    airports_df = pd.read_csv(AIRPORTS_CSV, encoding="utf-8-sig")
    airports = build_airports(master, airports_df, islands, resolver, aliases)
    airports.sort(key=lambda item: item["iata"])
    access_edges.extend(airport_access_edges(airports, islands, stops))

    excluded_air_routes = []
    air_services, included_pairs = build_air_services(airports, excluded_air_routes)
    ferry_services = build_ferry_services()
    villemale_ferry = build_villemale_ferry()

    health_facilities, excluded_health = build_health_facilities(resolver, islands, aliases)
    education_facilities, excluded_education, duplicate_education = build_education_facilities(
        resolver, islands, aliases
    )
    # The six contract categories do not cover preschools or Quran centres. Keep
    # them out of the served facility list (no dead rows) but account for every
    # one in report.excluded.
    education_zero_category = [
        facility for facility in education_facilities if not facility["categories"]
    ]
    education_facilities = [
        facility for facility in education_facilities if facility["categories"]
    ]
    intervention_facilities, service_meta, intervention_report, service_category_stats = (
        build_intervention_facilities(resolver, islands)
    )
    facilities = health_facilities + education_facilities + intervention_facilities

    # Deduplicate access edges deterministically but keep distinct parallel bases.
    unique_edges = {}
    for edge in access_edges:
        key = (edge["from"], edge["to"], edge["mode"], edge["basis"])
        unique_edges.setdefault(key, edge)
    access_edges = sorted(unique_edges.values(), key=lambda item: (item["from"], item["to"], item["mode"], item["basis"]))

    services = ferry_services + air_services + villemale_ferry
    services.sort(key=lambda item: item["id"])

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------
    category_definitions = [
        {
            "id": "health_any",
            "label": "Any public health facility",
            "definition": "Every named public health facility in the MHS/HEMS master.",
            "confidenceNote": "Facility locations are island-level (HMS master), not building coordinates.",
            "kind": "facility",
            "group": "Health facilities",
            "source": "data/external/health/_derived/public_health_facility_master.csv",
        },
        {
            "id": "health_hospital",
            "label": "Hospital (tier 1-3)",
            "definition": "Tiers 1_tertiary, 2_regional_hospital, 2_general_hospital, 2_hospital_other, 3_atoll_hospital, 3_atoll_hospital_small.",
            "confidenceNote": "Tier from the 2020 MHS facility master; unnamed placeholder rows excluded.",
            "kind": "facility",
            "group": "Health facilities",
            "source": "data/external/health/_derived/public_health_facility_master.csv",
        },
        {
            "id": "health_regional_tertiary",
            "label": "Regional or tertiary hospital",
            "definition": "Hospital tiers beginning 1_ (tertiary) or 2_ (regional/general).",
            "confidenceNote": "Derived from the tier field; island-level precision.",
            "kind": "facility",
            "group": "Health facilities",
            "source": "data/external/health/_derived/public_health_facility_master.csv",
        },
        {
            "id": "education_grade_11_12",
            "label": "School offering grade 11-12",
            "definition": "Education register rows with offers_grade_11_12 = true.",
            "confidenceNote": "Offering flag from the institution register; island-level.",
            "kind": "facility",
            "group": "Education",
            "source": "data/external/education/institutions_master.csv",
        },
        {
            "id": "education_higher_ed",
            "label": "Higher education campus/institute",
            "definition": "Campus/institute types excluding preschool, school, higher secondary school, institute (Quran centre) and institution total (all campuses).",
            "confidenceNote": "Aggregate all-campus totals and Quran centres excluded; island-level.",
            "kind": "facility",
            "group": "Education",
            "source": "data/external/education/institutions_master.csv",
        },
        {
            "id": "education_school",
            "label": "School",
            "definition": "Education register types 'school' and 'higher secondary school'.",
            "confidenceNote": "Preschools excluded; island-level.",
            "kind": "facility",
            "group": "Education",
            "source": "data/external/education/institutions_master.csv",
        },
    ]
    for category in category_definitions:
        members = [
            facility
            for facility in facilities
            if category["id"] in facility["categories"]
        ]
        category["facilityCount"] = len(members)
        category["islandCount"] = len({facility["islandId"] for facility in members})

    category_definitions.extend(intervention_category_definitions(service_category_stats))

    counts = {
        "islands": len(islands),
        "origins": sum(1 for island in islands if island["isOrigin"]),
        "stops": len(stops),
        "airports": len(airports),
        "ferryTrips": len(ferry_services),
        "airServices": len([service for service in services if service.get("mode") == "air"]),
        "facilities": len(facilities),
        "categories": len(category_definitions),
    }

    population_note = (
        "447,420 residents on the 191 inhabited administrative islands (2022 census). "
        "The four Greater Malé rows (Maale, Vilin'gili, Hulhumaale, Hulhule) are counted once "
        "from the 2022 city/ward split, not added on top of the census city total. "
        "Excluded from this origin scope: 1,399 harbour-area residents and 66,313 people in "
        "non-admin-island localities, for a republic total of 515,132."
    )

    assumptions = [
        {
            "id": "rtl_reference_day",
            "value": "The 102 RTL trips are the services recorded for reference day 2026-10-10.",
            "confidence": "source",
            "source": "data/team-kandu/rtl_trips.csv",
            "note": "RTL calibration is incomplete; missing journeys do not prove absence of transport.",
        },
        {
            "id": "rtl_single_time",
            "value": "RTL records one time per stop; it is used as both arrival and departure.",
            "confidence": "source",
            "source": "data/team-kandu/rtl_trips.csv",
        },
        {
            "id": "access_walk",
            "value": "Island/stop access is estimated at 4.5 km/h walking with a 1.25 detour factor.",
            "confidence": "assumption",
            "source": "MULTIMODAL_IMPLEMENTATION.md §5",
        },
        {
            "id": "access_local_transport",
            "value": "Same-island access beyond 1.5 km is estimated at 25 km/h local transport plus 5 minutes.",
            "confidence": "assumption",
            "source": "MULTIMODAL_IMPLEMENTATION.md §5",
        },
        {
            "id": "air_departure_generation",
            "value": "Domestic air departures are generated evenly in 06:00-18:00 at max(1, round(weekly/7)) per day; they are not observed schedules.",
            "confidence": "estimated",
            "source": "data/external/air/domestic_routes.csv",
            "note": "Weekly frequency is an estimate each way from the route table; MACL records do not establish schedules.",
        },
        {
            "id": "air_operating_only",
            "value": "Only domestic routes whose status contains 'operating' are included; 31 airport pairs plus 1 aggregate seaplane row excluded.",
            "confidence": "source",
            "source": "data/external/air/domestic_routes.csv",
        },
        {
            "id": "seaplane_excluded",
            "value": "Seaplane/resort water aerodromes are excluded from the resident accessibility network.",
            "confidence": "assumption",
            "source": "research/03_transport_network_and_methods.md",
        },
        {
            "id": "intervention_service_evidence",
            "value": (
                "Intervention service categories are taken solely from the diagnostics, "
                "specialist and dental evidence tables; they are not inferred from facility tier."
            ),
            "confidence": "source",
            "source": (
                "data/external/health/services/diagnostics/diagnostic_services.csv; "
                "data/external/health/services/specialist/specialist_services.csv; "
                "data/external/health/services/dental/dental_services.csv"
            ),
            "note": (
                "Resort/guest-only rows and islands that cannot be resolved are excluded "
                "from the served facility list and counted in meta.serviceData."
            ),
        },
        {
            "id": "speedboat_access",
            "value": "Airport-island speedboat access is estimated at 25 km/h plus 10 minutes boarding.",
            "confidence": "assumption",
            "source": "MULTIMODAL_IMPLEMENTATION.md §5",
        },
        {
            "id": "road_link_times",
            "value": "Addu, Laamu, Malé-Hulhulé-Hulhumalé link roads are modelled at 40 km/h plus 3 minutes; distances are centroid-derived with a 1.15 detour.",
            "confidence": "assumption",
            "source": "research/03_transport_network_and_methods.md",
        },
        {
            "id": "facilities_island_precision",
            "value": "Health and education facilities are island-level locations, not building coordinates or confirmed clinical services.",
            "confidence": "source",
            "source": "data/external/health, data/external/education",
        },
        {
            "id": "population_scope",
            "value": "Origin population is 447,420 on 191 inhabited islands; 1,399 harbour-area and 66,313 non-admin-island persons are omitted.",
            "confidence": "source",
            "source": "census 2022 crosswalk",
        },
        {
            "id": "villemale_ferry",
            "value": "Malé-Vilimaale ferry is modelled as a published frequency: 7 minutes, every 15 minutes, 06:00-22:00.",
            "confidence": "estimated",
            "source": "research/03_transport_network_and_methods.md",
        },
    ]

    origin_access = origin_access_summary(islands, access_edges, services)

    coverage_notes = [
        "RTL reference day 2026-10-10: 102 recorded trips on 49 routes; the calendar is not a full service calendar.",
        (
            f"{origin_access['withAccess']} of {origin_access['origins']} origin islands "
            f"({origin_access['populationWithAccess']:,} residents) have an incident access "
            f"edge or frequency service; {origin_access['withoutAccess']} origins "
            f"({origin_access['populationWithoutAccess']:,} residents) have no fixed "
            "access/frequency service in the reference-day network. This is a coverage "
            "statement, not proof that transport is absent."
        ),
        "Domestic air is an estimated frequency layer; generated departure times are not observed schedules.",
        "Seaplane and resort water-aerodrome services are outside the resident network.",
        "Airport-only islands are included as non-origin island nodes so airport access is explicit.",
        (
            "Facilities mapped to islands: "
            f"{len(health_facilities)}/{len(health_facilities) + len(excluded_health)} health rows and "
            f"{len(education_facilities)}/{len(education_facilities) + len(excluded_education) + len(education_zero_category) + len(duplicate_education)} education rows."
        ),
        (
            f"Intervention layer: {service_meta['rowsUsed']} of {service_meta['rowsRead']} "
            f"evidence rows used; {service_meta['rowsExcludedResort']} resort/guest-only and "
            f"{service_meta['rowsExcludedUnresolvedIsland']} unresolved-island rows excluded; "
            f"{len(intervention_facilities)} facilities across {len(service_category_stats)} categories."
        ),
    ]

    # ------------------------------------------------------------------
    # Ground-truth checks recorded in the report
    # ------------------------------------------------------------------
    airport_nodes = {f"airport:{airport['iata']}" for airport in airports}
    node_ids = {f"island:{island['id']}" for island in islands}
    node_ids |= {f"stop:{stop['id']}" for stop in stops}
    node_ids |= airport_nodes
    raw_stop_ids = {stop["id"] for stop in stops}

    unresolved_stop_refs = 0
    for service in ferry_services:
        for stop_time in service["stops"]:
            if stop_time["stopId"] not in raw_stop_ids:
                unresolved_stop_refs += 1

    checks = {
        "origins_191": counts["origins"] == 191,
        "population_447420": sum(
            island["population"] for island in islands if island["isOrigin"]
        )
        == 447_420,
        "node_islands_200": counts["islands"] == 200,
        "scheduled_stops_117": counts["stops"] == 117,
        "ferry_trips_102": counts["ferryTrips"] == 102,
        "airports_20": counts["airports"] == 20,
        "air_services_62_directed": counts["airServices"] == 62,
        "air_pairs_31": included_pairs == 31,
        "v1_facilities_501": len(
            [facility for facility in facilities if not facility.get("serviceCategories")]
        )
        == 501,
        "intervention_facilities_444": len(intervention_facilities) == 444,
        "categories_48": counts["categories"] == 48,
        "intervention_categories_42": len(service_category_stats) == 42,
        "intervention_facilities_categorised": all(
            facility["categories"]
            and set(facility["categories"]) == set(facility["serviceCategories"])
            and all(category.startswith("service:") for category in facility["categories"])
            for facility in intervention_facilities
        ),
        "intervention_evidence_categories_match": all(
            {item["category"] for item in facility["serviceEvidence"]}
            == set(facility["serviceCategories"])
            for facility in intervention_facilities
        ),
        "all_service_stop_ids_resolve": unresolved_stop_refs == 0,
        "all_access_edge_endpoints_resolve": all(
            edge["from"] in node_ids and edge["to"] in node_ids for edge in access_edges
        ),
        "every_airport_has_access_edge": all(
            any(
                edge["from"] == f"airport:{airport['iata']}"
                or edge["to"] == f"airport:{airport['iata']}"
                for edge in access_edges
            )
            for airport in airports
        ),
        "all_facility_islands_resolve": all(
            facility["islandId"] in islands_by_id for facility in facilities
        ),
        "all_served_facilities_categorised": all(
            bool(facility["categories"]) for facility in facilities
        ),
        "every_fuzzy_alias_unreviewed": all(
            alias["reviewed"] == "false"
            for alias in aliases
            if alias["method"] == "fuzzy"
        ),
    }
    if not all(checks.values()):
        failed = [name for name, value in checks.items() if not value]
        raise ValueError(f"invariant checks failed: {failed}")

    # Alias bookkeeping
    alias_counts_by_source = Counter(alias["source"] for alias in aliases)
    alias_counts_by_method = Counter(alias["method"] for alias in aliases)
    fuzzy_aliases = [alias for alias in aliases if alias["method"] == "fuzzy"]
    unresolved_aliases = [alias for alias in aliases if alias["method"] == "unresolved"]

    access_counts = Counter(edge["mode"] for edge in access_edges)
    category_counts = {
        category["id"]: {
            "facilities": category["facilityCount"],
            "islands": category["islandCount"],
        }
        for category in category_definitions
    }

    # ------------------------------------------------------------------
    # Write artifacts
    # ------------------------------------------------------------------
    network = {
        "meta": {
            "schemaVersion": SCHEMA_VERSION,
            "generatedAt": generated_at,
            "timezone": TIMEZONE,
            "referenceDay": REFERENCE_DAY,
            "serviceDayAssumption": (
                "All RTL trips are treated as one reference-day timetable; "
                "the actual weekly calendar is incomplete and not modelled."
            ),
            "population": {
                "origins": 447_420,
                "republic2022": 515_132,
                "originCount": 191,
                "note": population_note,
            },
            "assumptions": assumptions,
            "counts": counts,
            "routingDefaults": ROUTING_DEFAULTS,
            "excludedAirRoutes": sorted(
                excluded_air_routes, key=lambda item: (item["from"], item["to"], item["status"])
            ),
            "coverageNotes": coverage_notes,
            "serviceData": service_meta,
        },
        "islands": islands,
        "stops": stops,
        "airports": airports,
        "accessEdges": access_edges,
        "services": services,
        "facilities": facilities,
        "categories": category_definitions,
    }
    network_bytes = write_json(out_dir / "network.json", network, indent=1)

    geojson = build_geojson(islands)
    geojson_path = out_dir / "islands.geojson"
    geojson_bytes = write_json(geojson_path, geojson, indent=None)
    if geojson_bytes >= 2 * 1024 * 1024:
        raise ValueError(f"islands.geojson is {geojson_bytes} bytes, over the 2 MB budget")

    with open(out_dir / "aliases.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "source",
                "source_atoll",
                "source_name",
                "island_id",
                "island_name",
                "census_name",
                "method",
                "score",
                "reviewed",
            ]
        )
        for alias in aliases:
            writer.writerow(
                [
                    alias["source"],
                    alias["source_atoll"],
                    alias["source_name"],
                    alias["island_id"],
                    alias["island_name"],
                    census_names.get(alias["island_id"], ""),
                    alias["method"],
                    alias["score"],
                    alias["reviewed"],
                ]
            )

    report = {
        "generatedAt": generated_at,
        "referenceDay": REFERENCE_DAY,
        "files": {
            "networkJsonBytes": network_bytes,
            "islandsGeojsonBytes": geojson_bytes,
            "aliasesRows": len(aliases),
        },
        "counts": counts,
        "population": {
            "origins": 447_420,
            "republic2022": 515_132,
            "originCount": 191,
            "omittedHarbourArea": 1_399,
            "omittedNonAdminIsland": 66_313,
            "omittedTotal": 67_712,
            "reconciliation": {
                "originPopulation": 447_420,
                "harbourArea": 1_399,
                "nonAdminIsland": 66_313,
                "sum": 447_420 + 1_399 + 66_313,
                "republic2022": 515_132,
                "reconciles": 447_420 + 1_399 + 66_313 == 515_132,
            },
            "note": population_note,
        },
        "originAccess": origin_access,
        "canonicalNameOverrides": [
            {
                "islandId": pcode,
                "displayName": override["name"],
                "censusName": override["censusName"],
                "censusSource": "data/external/_derived/census2022_population_by_island.csv",
                "reason": override["reason"],
            }
            for pcode, override in sorted(DISPLAY_NAME_OVERRIDES.items())
        ],
        "categoryCounts": [
            {
                "id": category["id"],
                "label": category["label"],
                "facilityCount": category["facilityCount"],
                "islandCount": category["islandCount"],
            }
            for category in category_definitions
        ],
        "excludedAirRoutes": sorted(
            excluded_air_routes, key=lambda item: (item["from"], item["to"], item["status"])
        ),
        "air": {
            "operatingRows": 32,
            "airportPairsIncluded": included_pairs,
            "directedServices": counts["airServices"],
            "excludedRoutes": sorted(
                excluded_air_routes, key=lambda item: (item["from"], item["to"], item["status"])
            ),
        },
        "aliases": {
            "total": len(aliases),
            "bySource": dict(sorted(alias_counts_by_source.items())),
            "byMethod": dict(sorted(alias_counts_by_method.items())),
            "fuzzy": [
                {
                    "source": alias["source"],
                    "atoll": alias["source_atoll"],
                    "name": alias["source_name"],
                    "islandId": alias["island_id"],
                    "islandName": alias["island_name"],
                    "score": alias["score"],
                }
                for alias in fuzzy_aliases
            ],
            "unresolved": [
                {
                    "source": alias["source"],
                    "atoll": alias["source_atoll"],
                    "name": alias["source_name"],
                    "reason": alias.get("reason", ""),
                }
                for alias in unresolved_aliases
            ],
            "unresolvedBySource": dict(
                sorted(Counter(alias["source"] for alias in unresolved_aliases).items())
            ),
            "unresolvedByReason": dict(
                sorted(
                    Counter(
                        alias.get("reason", "") or "(no reason recorded)"
                        for alias in unresolved_aliases
                    ).items()
                )
            ),
            "manualOverrides": [
                {
                    "source": alias["source"],
                    "atoll": alias["source_atoll"],
                    "name": alias["source_name"],
                    "islandId": alias["island_id"],
                    "islandName": alias["island_name"],
                }
                for alias in aliases
                if alias["method"] == "manual"
            ],
        },
        "excluded": {
            "healthFacilities": excluded_health,
            "educationFacilities": excluded_education,
            "educationZeroCategoryFacilities": [
                {
                    "id": facility["id"],
                    "name": facility["name"],
                    "type": facility.get("type", ""),
                    "islandId": facility["islandId"],
                    "reason": "no contract category applies to this education facility type",
                }
                for facility in education_zero_category
            ],
            "educationDuplicateRows": duplicate_education,
        },
        "facilities": {
            "health": len(health_facilities),
            "education": len(education_facilities),
            "intervention": len(intervention_facilities),
            "total": len(facilities),
            "uncategorised": sum(1 for facility in facilities if not facility["categories"]),
            "excludedUncategorised": len(education_zero_category),
            "byCategory": category_counts,
        },
        "intervention": intervention_report,
        "serviceData": service_meta,
        "access": {
            "edges": len(access_edges),
            "byMode": dict(sorted(access_counts.items())),
            "airportsWithAccess": sum(
                1
                for airport in airports
                if any(
                    edge["from"] == f"airport:{airport['iata']}"
                    or edge["to"] == f"airport:{airport['iata']}"
                    for edge in access_edges
                )
            ),
        },
        "geojson": {
            "features": len(geojson["features"]),
            "bytes": geojson_bytes,
            "toleranceDegrees": GEOJSON_TOLERANCE,
        },
        "checks": checks,
        "assumptions": assumptions,
    }
    report_bytes = write_json(out_dir / "report.json", report, indent=2)

    public_written = {}
    if not args.skip_public:
        args.public_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out_dir / "network.json", args.public_dir / "multimodal.json")
        shutil.copyfile(out_dir / "islands.geojson", args.public_dir / "islands.geojson")
        public_written = {
            "multimodalJson": str((args.public_dir / "multimodal.json").relative_to(ROOT)),
            "islandsGeojson": str((args.public_dir / "islands.geojson").relative_to(ROOT)),
        }

    print(
        json.dumps(
            {
                "counts": counts,
                "aliases": {
                    "total": len(aliases),
                    "byMethod": dict(sorted(alias_counts_by_method.items())),
                },
                "bytes": {
                    "network": network_bytes,
                    "geojson": geojson_bytes,
                    "report": report_bytes,
                },
                "public": public_written,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
