#!/usr/bin/env python3
"""Build the browser fare table (web/public/data/fares.json) for journey cost estimates.

Air: per airport pair, the typical resident one-way fare from data/external/fares/air_fares.csv
(regular-fare rows, else the lowest promotional fare x the published regular/promo ratio),
with the lowest promotional fare kept for context. Pairs with no row fall back to the
distance model in air_fares_model.json.

Sea and road: data/external/fares/sea_land_fares_model.json when present. A mode without
data is left out, so the app reports that leg's fare as unknown instead of guessing.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FARES = ROOT / "data" / "external" / "fares"
DEFAULT_OUT = ROOT / "web" / "public" / "data" / "fares.json"
NETWORK = ROOT / "web" / "public" / "data" / "multimodal.json"
CONF = {"high": "sourced", "medium": "sourced", "low": "estimated"}
SEA_DETOUR = 1.1  # FollowMe: boat tracks are about 1.1x straight-line distance (research/04)


def air_routes(rows: list[dict], ratio: float) -> dict:
    by_pair: dict[str, dict] = {}
    for row in rows:
        if row["mode"] != "domestic_air" or row["fare_type"] != "local" or row["trip_type"] != "one_way":
            continue
        if row["source_date"][:4] < "2024":
            continue
        pair = "-".join(sorted([row["origin"], row["destination"]]))
        notes = row["notes"].lower()
        entry = by_pair.setdefault(pair, {"regular": [], "lowest": []})
        kind = "regular" if ("regular" in notes or "typical" in notes) else "lowest"
        entry[kind].append(row)

    out = {}
    for pair, entry in sorted(by_pair.items()):
        newest = lambda rs: max(rs, key=lambda r: (r["source_date"], r["confidence"] != "low"))
        lowest = min((float(r["fare_mvr"]) for r in entry["lowest"]), default=None)
        if entry["regular"]:
            row = newest(entry["regular"])
            mvr, confidence = float(row["fare_mvr"]), CONF.get(row["confidence"], "estimated")
            basis = "Resident one-way, regular fare" if confidence == "sourced" else "Resident one-way, regular fare (estimated)"
            source = row["source_url"]
        elif lowest is not None:
            row = newest(entry["lowest"])
            mvr, confidence = lowest * ratio, "estimated"
            basis = f"Resident one-way, lowest fare x {ratio:.2f} regular/promo ratio"
            source = row["source_url"]
        else:
            continue
        item = {"mvr": round(mvr), "basis": basis, "confidence": confidence, "source": source}
        if lowest is not None and round(lowest) < round(mvr):
            item["lowestMvr"] = round(lowest)
        out[pair] = item
    return out


def model(block: dict | None, basis: str) -> dict | None:
    """Accept {a_mvr, b_mvr_per_km} or a flat {median_mvr|flat_mvr|fare_mvr} block."""
    if not block:
        return None
    if "a_mvr" in block:
        a, b = float(block["a_mvr"]), float(block.get("b_mvr_per_km", 0) or 0)
    else:
        flat = next((block[k] for k in ("flat_mvr", "median_mvr", "fare_mvr", "mvr") if k in block), None)
        if flat is None:
            return None
        a, b = float(flat), 0.0
    thin = bool(block.get("thin")) or int(block.get("n", 0) or 0) < 3
    return {
        "aMvr": round(a, 2),
        "bMvrPerKm": round(b, 3),
        "basis": block.get("basis") or basis,
        "confidence": "assumption" if thin else "estimated",
        "source": "data/external/fares/sea_land_fares_model.json",
    }


def first(sea: dict, *keys: str) -> dict | None:
    for key in keys:
        if isinstance(sea.get(key), dict):
            return sea[key]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = list(csv.DictReader((FARES / "air_fares.csv").open(encoding="utf-8")))
    air_model = json.loads((FARES / "air_fares_model.json").read_text(encoding="utf-8"))
    ratio = float(air_model["regular_to_promo_ratio"]["value"])
    trunk = air_model["trunk_model"]

    table = {
        "schemaVersion": 1,
        "currency": "MVR",
        "usdMvr": float(air_model.get("usd_mvr", 15.42)),
        "generatedAt": date.today().isoformat(),
        "airRoutes": air_routes(rows, ratio),
        "airModel": {
            "aMvr": round(trunk["a"] * ratio, 2),
            "bMvrPerKm": round(trunk["b"] * ratio, 3),
            "basis": "Resident one-way, distance model (no published fare for this pair)",
            "confidence": "estimated",
            "source": "data/external/fares/air_fares_model.json",
        },
        "seaDetour": SEA_DETOUR,
        "notes": [
            "Non-emergency resident fares, MVR. Approved emergency transport is paid by Aasandha.",
            "Air fares are Maldivian resident fares (2024-2026); estimated rows are labelled.",
        ],
    }

    sea_path = FARES / "sea_land_fares_model.json"
    if sea_path.exists():
        sea = json.loads(sea_path.read_text(encoding="utf-8"))
        source = "data/external/fares/sea_land_fares_model.json"
        rtl = sea.get("fast_ferry_rtl")
        if rtl and "a_mvr" in rtl:
            # A fit to the official RTL gazette step tariff (35/50/65/70/100/125 by great-circle km).
            table["ferry"] = {
                "aMvr": round(float(rtl["a_mvr"]), 2),
                "bMvrPerKm": round(float(rtl["b_mvr_per_km"]), 3),
                "basis": f"RTL resident one-way, gazette tariff fit (n={rtl.get('n')}, r²={rtl.get('r2')})",
                "confidence": "sourced" if int(rtl.get("n", 0)) >= 100 and float(rtl.get("r2") or 0) >= 0.8 else "estimated",
                "source": source,
            }
        male = sea.get("greater_male") or {}
        if "villimale_ferry_mvr" in male:
            # The network's frequency ferries are the Malé–Vilimalé shuttle (both directions).
            network = json.loads(NETWORK.read_text(encoding="utf-8"))
            table["serviceFares"] = {
                service["id"]: {
                    "aMvr": float(male["villimale_ferry_mvr"]),
                    "bMvrPerKm": 0.0,
                    "basis": "Malé–Vilimalé ferry, flat fare",
                    "confidence": "sourced",
                    "source": source,
                }
                for service in network["services"]
                if service["kind"] == "frequency" and service["mode"] == "ferry"
            }
        taxi = male.get("taxi") or {}
        points = [(2.5, taxi.get("male_airport")), (7.5, taxi.get("male_hm1")), (10.5, taxi.get("male_hm2"))]
        points = [(km, float(mvr)) for km, mvr in points if mvr is not None]
        if len(points) >= 2:
            # Least-squares line through the regulated Greater Malé taxi fares (approx. road km).
            n = len(points)
            mx = sum(km for km, _ in points) / n
            my = sum(mvr for _, mvr in points) / n
            b = sum((km - mx) * (mvr - my) for km, mvr in points) / sum((km - mx) ** 2 for km, _ in points)
            table["road"] = {
                "aMvr": round(my - b * mx, 2),
                "bMvrPerKm": round(b, 3),
                "basis": "Taxi, fit to the regulated Greater Malé fares (gazette 2024)",
                "confidence": "estimated",
                "source": source,
            }
        # No resident scheduled-speedboat tariff exists (tourist USD prices only), so
        # speedboat legs stay unpriced rather than using tourist fares.
        table["notes"].append("Sea and road fares from data/external/fares/sea_land_fares_model.json.")
        table["notes"].append(
            "Free ferry and bus travel applies to people aged 65+, children under 3, disabled people "
            "and (Greater Malé) students; this estimate is the full resident fare."
        )
    else:
        table["notes"].append("No sea/road fare data yet: those legs are reported as unknown.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(table, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out} — {len(table['airRoutes'])} air pairs; modes: "
          + ", ".join(k for k in ("ferry", "serviceFares", "speedboat", "road") if k in table))


if __name__ == "__main__":
    main()
