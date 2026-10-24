#!/usr/bin/env python3
"""Build the HeiGIT accessibility baseline JSON (contract section 10.4).

This copies only the values published in the processed HeiGIT tables.  No
interpolation, smoothing or re-estimation is performed: where the source table
has no value, the output field is null.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEADLINE_CSV = ROOT / "data" / "processed" / "heigit" / "heigit_headline_adm0.csv"
UNITS_CSV = ROOT / "data" / "processed" / "heigit" / "heigit_unit_summary.csv"
DEFAULT_OUT = ROOT / "web" / "public" / "data" / "heigit-baseline.json"

SOURCE = "HeiGIT accessibility indicators, Maldives baseline (data/processed/heigit)"
METHOD = (
    "Values copied directly from the HeiGIT headline (national) and unit summary "
    "tables; no interpolation or re-estimation."
)
WARNING = (
    "Baseline context only. Population shares describe modelled access within a "
    "distance or travel-time threshold; they are not observed journeys and should "
    "not be used as demand or service-quality measurements."
)


def number(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def read_rows(path: Path):
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def threshold_label(row: dict) -> str:
    if str(row.get("range_type", "")).strip() == "distance":
        value = number(row.get("range_km"))
        return f"{value:g} km" if value is not None else ""
    value = number(row.get("range_min"))
    return f"{value:g} min" if value is not None else ""


def build_payload(headline_path: Path, units_path: Path) -> dict:
    national = []
    for row in read_rows(headline_path):
        threshold = threshold_label(row)
        share = number(row.get("population_share"))
        population = number(row.get("population"))
        if not threshold or share is None:
            continue
        national.append(
            {
                "category": str(row.get("category", "")).strip(),
                "threshold": threshold,
                "share": share,
                "population": int(round(population)) if population is not None else None,
            }
        )

    units = []
    for row in read_rows(units_path):
        units.append(
            {
                "admLevel": str(row.get("admin_level", "")).strip(),
                "name": str(row.get("name", "")).strip(),
                "category": str(row.get("category", "")).strip(),
                "within5km": number(row.get("share_within_5km")),
            }
        )

    if not national:
        raise ValueError(f"no national rows found in {headline_path}")
    if not units:
        raise ValueError(f"no unit rows found in {units_path}")

    return {
        "source": SOURCE,
        "method": METHOD,
        "warning": WARNING,
        "national": national,
        "units": units,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headline", type=Path, default=HEADLINE_CSV)
    parser.add_argument("--units", type=Path, default=UNITS_CSV)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    payload = build_payload(args.headline, args.units)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "out": str(args.out),
                "national": len(payload["national"]),
                "units": len(payload["units"]),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
