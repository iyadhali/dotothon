#!/usr/bin/env python3
"""Build small curated analysis tables for the SQLite serving DB.

Reads local research datasets (data/ is gitignored) and writes committed JSON
tables to web/public/data/extras/. Each file: {"meta": {...}, "records": [...]}.
Missing sources are skipped with a warning. Run from anywhere:

    python scripts/multimodal/build_extras.py
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
OUT = WEB / "public" / "data" / "extras"
TODAY = dt.date.today().isoformat()
sizes: dict[str, int] = {}


def warn(msg: str) -> None:
    print(f"WARN  {msg}", file=sys.stderr)


def clean(v):
    """JSON-safe scalar: NaN -> None, numpy -> python, repair mojibake."""
    if v is None:
        return None
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return int(v) if v.is_integer() and abs(v) < 1e15 else round(v, 4)
    if isinstance(v, str):
        if "Ã" in v or "â€" in v:
            try:
                v = v.encode("cp1252").decode("utf8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass
        return v
    return v


def network_build_id() -> str | None:
    """Build id stamped by augment_network.py, so build-db can reject stale extras."""
    path = WEB / "public" / "data" / "multimodal.json"
    if not path.exists():
        return None
    return (json.loads(path.read_text(encoding="utf8")).get("meta", {}).get("build") or {}).get("id")


def write(name: str, records: list, sources: list[str], notes: list[str], extra: dict | None = None) -> None:
    meta = {
        "table": name,
        "generatedAt": TODAY,
        "networkBuildId": network_build_id(),
        "rowCount": len(records),
        "sources": sources,
        "notes": notes,
        **(extra or {}),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.json"
    path.write_text(
        json.dumps({"meta": meta, "records": records}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf8",
    )
    sizes[name] = path.stat().st_size
    print(f"wrote {name}: {len(records)} rows, {sizes[name] / 1024:.0f} KiB")


def need(*paths: str) -> bool:
    missing = [p for p in paths if not (ROOT / p).exists()]
    for p in missing:
        warn(f"missing source {p}")
    return not missing


def read_csv(rel: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / rel, encoding="utf8")


def recs(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    return [{c: clean(r[c]) for c in cols} for r in df.to_dict("records")]


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def load_network() -> dict | None:
    p = WEB / "public" / "data" / "multimodal.json"
    if not p.exists():
        warn("missing web/public/data/multimodal.json")
        return None
    return json.loads(p.read_text(encoding="utf8"))


def fares() -> None:
    p = WEB / "public" / "data" / "fares.json"
    if p.exists() and need("data/external/fares/air_fares.csv"):
        f = json.loads(p.read_text(encoding="utf8"))
        df = read_csv("data/external/fares/air_fares.csv")
        df = df[(df["mode"] == "domestic_air") & (df["trip_type"] == "one_way")]
        src: dict[str, list] = {}
        for r in df.to_dict("records"):
            src.setdefault(f"{r['origin']}-{r['destination']}", []).append(r)
        records = []
        for pair, v in sorted(f["airRoutes"].items()):
            o, d = pair.split("-")
            url = next((str(c["source_url"]) for c in src.get(pair, []) if str(c["source_url"]).startswith("http")), None)
            records.append({
                "pair": pair, "origin": o, "destination": d,
                "resident_one_way_mvr": clean(v.get("mvr")),
                "lowest_mvr": clean(v.get("lowestMvr")),
                "confidence": clean(v.get("confidence")),
                "basis": clean(v.get("basis")),
                "source_url": url or clean(v.get("source")),
            })
        write("fares_air", records,
              ["web/public/data/fares.json", "data/external/fares/air_fares.csv"],
              ["Resident one-way regular fare per airport pair (MVR); lowest = cheapest observed/modelled.",
               "source_url is a published URL when one exists, else the model reference."],
              {"usdMvr": f.get("usdMvr")})
    else:
        warn("skipping fares_air")
    sp = ROOT / "data/external/fares/sea_land_fares_model.json"
    if sp.exists():
        m = json.loads(sp.read_text(encoding="utf8"))
        records = []
        for mode, v in m.items():
            if not isinstance(v, dict):
                continue
            ols = v.get("ols") or {}
            a = v.get("a_mvr", ols.get("a_mvr"))
            b = v.get("b_mvr_per_km", ols.get("b_mvr_per_km"))
            n = v.get("n", ols.get("n"))
            r2 = v.get("r2", ols.get("r2"))
            if a is None and b is None:
                continue
            records.append({"mode": mode, "a_mvr": clean(a), "b_mvr_per_km": clean(b), "n": clean(n),
                            "r2": clean(r2), "thin": 1 if v.get("thin") else 0})
        write("fare_models", records, ["data/external/fares/sea_land_fares_model.json"],
              ["fare = a + b * great-circle km (MVR, resident one-way). thin=1 means few observations."])
    else:
        warn("missing data/external/fares/sea_land_fares_model.json; skipping fare_models")


def profile(net: dict) -> None:
    ok = need("data/external/education/island_education_supply.csv",
              "data/external/health/_derived/health_atoll_summary.csv")
    edu = hs = None
    if ok:
        edu = read_csv("data/external/education/island_education_supply.csv")
        hs = read_csv("data/external/health/_derived/health_atoll_summary.csv")
    islands = net["islands"]
    edu_by: dict = {}
    unmatched_edu: list[str] = []
    pending: list = []
    if edu is not None:
        name_map = {}
        for i in islands:
            name_map[(norm(i.get("atollName")), norm(i["name"]))] = i["id"]
        for r in edu.to_dict("records"):
            a = norm(r["atoll"]).replace("city", "")
            iid = name_map.get((a, norm(r["island"])))
            if iid:
                edu_by[iid] = r
            else:
                pending.append(r)
        # fuzzy fallback within the same atoll (apostrophe / spelling variants), unclaimed islands only
        for r in pending:
            a = norm(r["atoll"]).replace("city", "")
            pool = {n: iid for (at, n), iid in name_map.items() if at == a and iid not in edu_by}
            hit = difflib.get_close_matches(norm(r["island"]), list(pool), n=1, cutoff=0.85)
            if hit:
                edu_by[pool[hit[0]]] = r
            else:
                unmatched_edu.append(f"{r['atoll']}/{r['island']}")
    hs_by: dict = {}
    unmatched_hs: list[str] = []
    if hs is not None:
        codes = {i.get("atoll") for i in islands}
        for r in hs.to_dict("records"):
            code = "MLE" if norm(r["atoll"]) == "male" else str(r["atoll"])
            if code in codes:
                hs_by[code] = r
            else:
                unmatched_hs.append(str(r["atoll"]))
    records = []
    for i in islands:
        e = edu_by.get(i["id"])
        h = hs_by.get(i.get("atoll"))
        records.append({
            "island_id": i["id"], "name": i["name"], "atoll_code": i.get("atoll"),
            "atoll_name": i.get("atollName"), "population": clean(i.get("population")),
            "highest_grade": clean(e["highest_grade_enrolled_2024"]) if e else None,
            "school_enrolment": clean(e["school_enrolment_2024"]) if e else None,
            "higher_secondary_on_island": (1 if str(e["higher_secondary_on_island"]).lower() == "true" else 0) if e else None,
            "hei_campuses": clean(e["hei_campuses"]) if e else None,
            "beds_per_1000": clean(h["inpatient_beds_per_1000"]) if h else None,
            "staff_per_10k": clean(h["hr2023_total_number_of_health_personnel_per10k"]) if h else None,
            "evacuations_per_1000": clean(h["evacuations_per_1000_2023"]) if h else None,
            "aasandha_per_person_mvr": clean(h["aasandha_exp_per_capita_2025_mvr"]) if h else None,
        })
    ne = sum(r["school_enrolment"] is not None for r in records)
    notes = [
        "Education joined on normalised (atoll name, island name); health capacity joined on atoll code (Male' atoll row -> MLE).",
        f"Islands with an education row matched: {ne} of {len(records)}; others are uninhabited or absent from the MoE register.",
        f"Education rows not matched to an island ({len(unmatched_edu)}): {', '.join(unmatched_edu[:40])}",
        f"Health atoll rows not matched ({len(unmatched_hs)}): {', '.join(unmatched_hs) or 'none'}",
        "staff_per_10k = hr2023 total health personnel per 10k; null where the HR survey has no value.",
    ]
    for n in notes[1:]:
        print("note:", n[:240])
    write("island_profile", records,
          ["web/public/data/multimodal.json", "data/external/education/island_education_supply.csv",
           "data/external/health/_derived/health_atoll_summary.csv"], notes)


def health_facilities(net: dict | None) -> None:
    rel = "data/external/health/_derived/public_health_facility_master.csv"
    if not need(rel):
        return
    df = read_csv(rel)
    lookup = {}
    if net:
        for i in net["islands"]:
            lookup[(i.get("atoll"), norm(i["name"]))] = i["id"]
    records, un = [], []
    for k, r in enumerate(df.to_dict("records")):
        ac = clean(r["atoll_code"])
        iid = lookup.get((ac, norm(r["island"])))
        if iid is None and ac:
            pool = {n: v for (a, n), v in lookup.items() if a == ac}
            hit = difflib.get_close_matches(norm(r["island"]), list(pool), n=1, cutoff=0.85)
            iid = pool[hit[0]] if hit else None
        if iid is None:
            un.append(f"{r['atoll_code']}/{r['island']}")
        records.append({
            "facility_key": k,
            "name": clean(r["hems_name"]) or f"{r['island']} ({r['mhs2020_category']})",
            "island": clean(r["island"]), "atoll_code": clean(r["atoll_code"]), "island_id": iid,
            "tier": clean(r["tier"]), "grade": clean(r["mhs2020_grade"]),
            "type": clean(r["mhs2020_category"]), "level_2026": clean(r["hems_level_2026"]),
            "owner": clean(r["hems_owner"]),
        })
    write("health_facilities", records, [rel],
          ["facility_key is the row order of the source CSV.",
           f"island_id is null where (atoll code, island name) did not match multimodal.json islands ({len(un)}): {', '.join(un[:40])}"])


def economics() -> None:
    vp = ROOT / "data/external/economics/value_of_time.json"
    kp = ROOT / "data/external/economics/key_figures.csv"
    records: list[dict] = []
    if vp.exists():
        v = json.loads(vp.read_text(encoding="utf8"))

        def flat(prefix: str, d: dict) -> None:
            for k, x in d.items():
                path = f"{prefix}.{k}" if prefix else k
                if isinstance(x, dict):
                    flat(path, x)
                elif isinstance(x, (int, float)) and not isinstance(x, bool):
                    records.append({"kind": "value_of_time", "key": path, "value": clean(x), "unit": None,
                                    "year": clean(v.get("price_year")), "geography": None, "note": None,
                                    "source_url": None})
                elif isinstance(x, str) and k in ("method", "confidence", "definition"):
                    records.append({"kind": "value_of_time", "key": path, "value": None, "unit": None,
                                    "year": clean(v.get("price_year")), "geography": None, "note": clean(x),
                                    "source_url": None})

        flat("", {k: x for k, x in v.items() if k != "sources"})
    else:
        warn("missing value_of_time.json")
    if kp.exists():
        df = pd.read_csv(kp, encoding="utf8")
        for r in df.to_dict("records"):
            val = clean(r["value"])
            if isinstance(val, str):
                try:
                    val = float(val.replace(",", ""))
                    val = int(val) if val.is_integer() else val
                except ValueError:
                    pass
            num = val if isinstance(val, (int, float)) else None
            note = clean(r["notes"])
            if num is None and val is not None:
                note = f"{val}; {note}" if note else str(val)
            records.append({"kind": "key_figure", "key": clean(r["indicator"]), "value": num,
                            "unit": clean(r["unit"]), "year": clean(r["year"]),
                            "geography": clean(r["geography"]), "note": note,
                            "source_url": clean(r["source_url"])})
    else:
        warn("missing key_figures.csv")
    if records:
        write("economics", records,
              ["data/external/economics/value_of_time.json", "data/external/economics/key_figures.csv"],
              ["kind=value_of_time rows are flattened leaves of value_of_time.json (dotted key path); "
               "kind=key_figure rows mirror key_figures.csv (indicator repeats across geography/year)."])


def sea_links() -> None:
    rel = "data/processed/followme/observed_sea_links.csv"
    if not need(rel):
        return
    df = read_csv(rel)
    cols = ["from_island_id", "to_island_id", "from_name", "to_name", "trips_per_day", "active_days", "vessels",
            "median_min", "p80_min", "distance_km", "speed_class", "first_dep_hour_p10", "last_dep_hour_p90",
            "rtl_served"]
    records = recs(df, cols)
    for r in records:
        r["rtl_served"] = 1 if str(r["rtl_served"]).lower() == "true" else 0
    write("observed_sea_links", records, [rel],
          ["Observed (vessel-tracking) directed island-to-island links; core columns only (histograms dropped)."])


def validation() -> None:
    rel = "data/processed/validation/atoll_access_vs_outcomes.csv"
    if not need(rel):
        return
    df = read_csv(rel)
    cols = list(df.columns)
    records = recs(df, cols)
    for r in records:
        r["is_greater_male"] = 1 if str(r.get("is_greater_male")).lower() == "true" else 0
        r["atoll_code"] = r.pop("key")
    write("validation_atoll", records, [rel],
          ["Model access metrics vs observed health/education outcomes per atoll (atoll_code = source 'key')."])


def island_access(net: dict | None) -> None:
    if not net:
        return
    script = WEB / "scripts" / "export-accessibility.ts"
    if not script.exists():
        warn("missing export-accessibility.ts")
        return
    tmp = Path(tempfile.mkdtemp(prefix="iaa-access-"))
    out = tmp / "island_access.csv"
    try:
        subprocess.run(["node", "--experimental-strip-types", str(script), "--out", str(out)],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        warn(f"accessibility export failed: {exc}")
        return
    df = pd.read_csv(out)
    best = pd.read_csv(tmp / "island_access_best.csv")
    best = best[["origin_island_id", "category", "estimated_air", "best_elapsed_minutes"]]
    df = df[df["departure_minute"].isin([360, 480, 840])]
    df = df.merge(best, on=["origin_island_id", "category", "estimated_air"], how="left")
    cols = ["origin_island_id", "category", "departure_minute", "estimated_air", "status", "elapsed_minutes",
            "modes", "destination_island_id", "best_elapsed_minutes"]
    df = df.sort_values(["origin_island_id", "category", "estimated_air", "departure_minute"])
    records = [{k: v for k, v in r.items() if v is not None} for r in recs(df, cols)]
    write("island_access", records,
          ["web/scripts/export-accessibility.ts (router over web/public/data/multimodal.json)"],
          ["Departures 06:00 (360), 08:00 (480), 14:00 (840). estimated_air 0 = scheduled/observed services only, "
           "1 = include estimated air.",
           "best_elapsed_minutes = best over 05:00-18:00 hourly departures for the same origin/category/air setting."],
          {"referenceDay": net["meta"].get("referenceDay")})


def main() -> int:
    net = load_network()
    fares()
    if net:
        profile(net)
    health_facilities(net)
    economics()
    sea_links()
    validation()
    island_access(net)
    total = sum(sizes.values())
    print(f"total {total / 1024 / 1024:.2f} MiB")
    if total > 3 * 1024 * 1024:
        warn("extras exceed 3 MB budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
