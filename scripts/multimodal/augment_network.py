#!/usr/bin/env python3
"""Add two gap-filling sea layers to the prepared network (run after build_network.py).

1. MTCC public ferry trips (2023 all-atolls timetable, recovered from the Wayback Machine;
   data/external/ferry_timetables/supplementary_trips.csv) for the atolls the RTL snapshot
   does not cover at all: Kaafu, Alif Alif, Alif Dhaalu, Vaavu, Meemu and Lhaviyani. Every
   trip is added with its published running days (`days`), so the router can apply the
   weekday calendar; no MTCC route runs on Friday.
2. Observed boat links from FollowMe GPS (data/processed/followme/observed_sea_links.csv):
   regular island-to-island boat traffic touching an island the RTL network cannot reach,
   added as estimated-frequency `sea` services under one route id so the whole layer can be
   switched off. These are observed movements of any tracked boat, not a public timetable.

3. Gap fixes (research/18_data_gaps.md):
   - T6: domestic air services with fewer than 7 weekly flights run on that many weekdays
     (`days`) instead of daily, removing the generated-departure inflation.
   - T5: observed boat departures are placed at the hours boats were seen leaving (FollowMe
     departure-hour histogram), and links with no weekend traffic do not run Fri/Sat.
   - T4: RTL trips with no trip back between the same two islands get an inferred return
     (reverse stop order after a 30-minute turnaround), id prefix `inferred:`, switchable.
4. Build manifest: `meta.build.id` is a content hash of the network; fares and extras record
   it so the database build can refuse mismatched artifacts.

Idempotent: earlier MTCC/observed/inferred entries are removed and air departures regenerated
from the weekly frequency. Writes the browser copy and, when present,
data/processed/multimodal/network.json.
"""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_NETWORK = ROOT / "web" / "public" / "data" / "multimodal.json"
PROCESSED_NETWORK = ROOT / "data" / "processed" / "multimodal" / "network.json"
MTCC_CSV = ROOT / "data" / "external" / "ferry_timetables" / "supplementary_trips.csv"
OBSERVED_CSV = ROOT / "data" / "processed" / "followme" / "observed_sea_links.csv"

MTCC_ATOLLS = {"AA", "ADh", "K", "V", "M", "Lh"}  # no scheduled RTL stop in the snapshot
ATOLL_CODES = {"Ha": "HA", "Ga": "GA", "Gdh": "GDh", "Hdh": "HDh"}
MALE_NAMES = {"male", "malé", "maale"}
JETTY_WALK_MIN = 5
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
OBSERVED_ROUTE_ID = "observed-boats"
MAX_OBSERVED_DEPARTURES = 12
TURNAROUND_MIN = 30
WEEK = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]


def norm(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", text)


def minutes(hhmm: str) -> int | None:
    hhmm = (hhmm or "").strip()
    if not re.fullmatch(r"\d{1,2}:\d{2}", hhmm):
        return None
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


class IslandIndex:
    def __init__(self, islands: list[dict]):
        self.by_atoll: dict[str, dict[str, dict]] = {}
        for island in islands:
            self.by_atoll.setdefault(island["atoll"], {})[norm(island["name"])] = island
        self.male = next((i for i in islands if norm(i["name"]) == "maale"), None)

    def find(self, name: str, atoll: str) -> dict | None:
        if norm(name) in {norm(n) for n in MALE_NAMES}:
            return self.male
        names = self.by_atoll.get(ATOLL_CODES.get(atoll, atoll), {})
        key = norm(name)
        if key in names:
            return names[key]
        close = difflib.get_close_matches(key, list(names), n=1, cutoff=0.85)
        return names[close[0]] if close else None


def strip_previous(network: dict) -> None:
    network["services"] = [
        s for s in network["services"]
        if not (s["id"].startswith("mtcc:") or s["id"].startswith("observed:") or s["id"].startswith("inferred:"))
    ]
    network["stops"] = [s for s in network["stops"] if not s["id"].startswith("MTCC:")]
    network["accessEdges"] = [
        e for e in network["accessEdges"]
        if not (e["from"].startswith("stop:MTCC:") or e["to"].startswith("stop:MTCC:"))
    ]
    network["meta"]["assumptions"] = [
        a for a in network["meta"].get("assumptions", [])
        if a.get("id") not in {"mtcc_2023_trips", "observed_boat_links", "air_weekday_calendar", "inferred_returns"}
    ]


def add_mtcc(network: dict, index: IslandIndex, weekday: str) -> dict:
    rows = list(csv.DictReader(MTCC_CSV.open(encoding="utf-8")))
    trips: dict[str, list[dict]] = {}
    for row in rows:
        trips.setdefault(row["trip_id"], []).append(row)

    route_atolls: dict[str, set[str]] = {}
    for row in rows:
        route_atolls.setdefault(row["route_code"], set()).add(ATOLL_CODES.get(row["atoll"], row["atoll"]))

    stops: dict[str, dict] = {}
    services, unmatched, skipped_day = [], set(), 0
    for trip_id, trip_rows in trips.items():
        first = trip_rows[0]
        if not route_atolls[first["route_code"]] <= MTCC_ATOLLS:
            continue
        days = [d.strip() for d in first["days_of_week"].split(",") if d.strip()]
        if weekday not in days:
            skipped_day += 1  # still added; counted for the reference-day summary
        stop_times = []
        for row in sorted(trip_rows, key=lambda r: int(r["stop_sequence"])):
            island = index.find(row["island_name"], row["atoll"])
            arrival, departure = minutes(row["arrival_hhmm"]), minutes(row["departure_hhmm"])
            if island is None:
                unmatched.add(f"{row['island_name']} ({row['atoll']})")
                continue
            if arrival is None and departure is None:
                continue
            arrival = arrival if arrival is not None else departure
            departure = departure if departure is not None else arrival
            stop_id = f"MTCC:{island['id']}"
            stops.setdefault(stop_id, {
                "id": stop_id, "code": island["id"], "name": island["name"], "islandId": island["id"],
                "lat": island["lat"], "lon": island["lon"], "scheduled": True,
            })
            if stop_times and stop_times[-1]["stopId"] == stop_id:
                continue
            stop_times.append({"stopId": stop_id, "name": island["name"], "sequence": len(stop_times) + 1,
                               "arrival": arrival, "departure": max(arrival, departure)})
        # Times must not run backwards along the trip.
        if len(stop_times) < 2 or any(b["arrival"] < a["departure"] for a, b in zip(stop_times, stop_times[1:])):
            continue
        services.append({
            "id": f"mtcc:{trip_id}", "kind": "timetabled", "mode": "ferry", "operator": "MTCC",
            "routeId": first["route_code"], "routeCode": first["route_code"].replace("MTCC-", "MTCC "),
            "zone": first["zone"], "confidence": "verified_timetable",
            "calendar": f"MTCC 2023 timetable; runs {first['days_of_week']}",
            "source": "data/external/ferry_timetables/supplementary_trips.csv", "stops": stop_times,
            "days": days,
        })

    network["stops"].extend(stops.values())
    for stop in stops.values():
        network["accessEdges"].append({
            "from": f"island:{stop['islandId']}", "to": f"stop:{stop['id']}", "mode": "walk",
            "minutes": JETTY_WALK_MIN, "confidence": "estimated_access",
            "basis": "island to MTCC jetty (island-level location)", "distanceKm": 0.3,
        })
    network["services"].extend(services)
    network["meta"]["assumptions"].append({
        "id": "mtcc_2023_trips",
        "value": f"{len(services)} MTCC trips from the 2023 all-atolls timetable, with their running days, in atolls with no RTL coverage (AA, ADh, K, V, M, Lh); {len(services) - skipped_day} run on {weekday}s.",
        "confidence": "source",
        "source": "data/external/ferry_timetables/supplementary_trips.csv",
        "note": "Timetable dated 2023 (Wayback copy of mtcc.mv PDF); services may have changed since.",
    })
    return {"trips": len(services), "stops": len(stops), "unmatched": sorted(unmatched), "otherDays": skipped_day}


def add_observed(network: dict) -> dict:
    island_ids = {i["id"] for i in network["islands"]}
    timetabled_pairs = set()
    for service in network["services"]:
        if service["kind"] != "timetabled":
            continue
        isl = [s["stopId"] for s in service["stops"]]
        stop_island = {s["id"]: s["islandId"] for s in network["stops"]}
        islands = [stop_island.get(sid) for sid in isl]
        for a, b in zip(islands, islands[1:]):
            timetabled_pairs.add((a, b))

    added = 0
    with OBSERVED_CSV.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["touches_no_access_origin"] != "True" or row["rtl_served"] == "True":
                continue
            a, b = row["from_island_id"], row["to_island_id"]
            if a not in island_ids or b not in island_ids or (a, b) in timetabled_pairs:
                continue
            per_day = max(1, min(MAX_OBSERVED_DEPARTURES, round(float(row["trips_per_day"]))))
            start = int(round(float(row["first_dep_hour_p10"]) * 60))
            end = int(round(float(row["last_dep_hour_p90"]) * 60))
            start, end = max(300, min(start, 1260)), max(300, min(max(end, start), 1320))
            departures = observed_departures(row.get("dep_hour_hist", ""), per_day, start, end)
            weekend = float(row.get("tpd_weekend") or 0)
            days = None if weekend >= 0.5 else [d for d in WEEK if d not in ("Fri", "Sat")]
            network["services"].append({
                "id": f"observed:{a}-{b}", "kind": "frequency", "mode": "sea", "routeId": OBSERVED_ROUTE_ID,
                "label": f"Observed boats {row['from_name']} → {row['to_name']}",
                "fromNode": f"island:{a}", "toNode": f"island:{b}",
                "weeklyFrequency": round(float(row["trips_per_day"]) * 7, 1), "departuresPerDay": len(departures),
                "operatingWindow": {"start": start, "end": end}, "blockMinutes": max(1, round(float(row["median_min"]))),
                "departures": departures, "confidence": "estimated_frequency",
                "status": "observed boat traffic (FollowMe GPS, Aug 2025); not a public timetable",
                "source": "data/processed/followme/observed_sea_links.csv",
                **({"days": days} if days else {}),
            })
            added += 1
    network["meta"]["assumptions"].append({
        "id": "observed_boat_links",
        "value": f"{added} regular boat links observed in FollowMe GPS (Aug 2025) are added as estimated sea services where an island has no RTL/MTCC service.",
        "confidence": "estimated",
        "source": "data/processed/followme/observed_sea_links.csv",
        "note": "Any tracked boat (public, private, fishing). Departures sit at the busiest observed departure hours; links with no weekend traffic do not run Fri/Sat. Switch off with route 'observed-boats'.",
    })
    return {"links": added}


def observed_departures(hist_text: str, per_day: int, start: int, end: int) -> list[int]:
    """Departures at the busiest observed hours (FollowMe histogram), within the observed window."""
    try:
        hist = {int(h): int(c) for h, c in json.loads(hist_text or "{}").items()}
    except (ValueError, TypeError):
        hist = {}
    hours = sorted(
        (h for h in hist if start <= h * 60 + 30 <= max(end, start + 60)),
        key=lambda h: (-hist[h], h),
    )[:per_day]
    if not hours:  # no histogram: fall back to an even spread over the window
        step = (end - start) / per_day if per_day > 1 else 0
        return sorted({int(start + step * k) for k in range(per_day)})
    return sorted(h * 60 + 30 for h in hours)


def fix_air_calendar(network: dict) -> int:
    """Air services: departures per day from weekly frequency; < 7 a week run on chosen weekdays."""
    changed = 0
    for service in network["services"]:
        if service["mode"] != "air" or service["kind"] != "frequency":
            continue
        weekly = float(service.get("weeklyFrequency") or 0)
        window = service.get("operatingWindow") or {"start": 360, "end": 1080}
        per_day = max(1, round(weekly / 7))
        step = (window["end"] - window["start"]) / per_day
        service["departures"] = [int(window["start"] + step * (k + 0.5)) for k in range(per_day)]
        service["departuresPerDay"] = per_day
        if weekly < 7:
            count = max(1, round(weekly))
            # Spread the flying days across the week, deterministically.
            service["days"] = [WEEK[int(i * 7 / count)] for i in range(count)]
            changed += 1
        else:
            service.pop("days", None)
    network["meta"]["assumptions"].append({
        "id": "air_weekday_calendar",
        "value": f"{changed} domestic air services with fewer than 7 estimated weekly flights run on that many weekdays instead of daily.",
        "confidence": "estimated",
        "source": "data/external/air/domestic_routes.csv",
        "note": "Removes the departure inflation from rounding weekly frequency up to daily (research/18_data_gaps.md T6).",
    })
    return changed


def add_inferred_returns(network: dict) -> int:
    """RTL trips with no trip back between the same two islands get a mirrored return trip."""
    stop_island = {stop["id"]: stop["islandId"] for stop in network["stops"]}
    rtl = [s for s in network["services"] if s["kind"] == "timetabled" and s.get("operator") == "RTL"]
    pairs = {(stop_island.get(t["stops"][0]["stopId"]), stop_island.get(t["stops"][-1]["stopId"])) for t in rtl}
    added = []
    for trip in rtl:
        first = stop_island.get(trip["stops"][0]["stopId"])
        last = stop_island.get(trip["stops"][-1]["stopId"])
        if (last, first) in pairs:
            continue
        stops = trip["stops"]
        clock = stops[-1]["arrival"] + TURNAROUND_MIN
        mirrored = []
        for index, stop in enumerate(reversed(stops)):
            if index > 0:
                prev = stops[len(stops) - index]
                gap = prev["arrival"] - stop["departure"]
                clock += max(1, gap)
            mirrored.append({"stopId": stop["stopId"], "name": stop["name"], "sequence": index + 1, "arrival": clock, "departure": clock})
        added.append({
            **{k: v for k, v in trip.items() if k != "stops"},
            "id": f"inferred:{trip['id']}",
            "calendar": "inferred return: reverse stop order after a 30-minute turnaround",
            "source": f"{trip.get('source', '')} (inferred return)",
            "stops": mirrored,
        })
    network["services"].extend(added)
    network["meta"]["assumptions"].append({
        "id": "inferred_returns",
        "value": f"{len(added)} RTL trips recorded in one direction only get an inferred return trip (reverse stops, {TURNAROUND_MIN}-minute turnaround).",
        "confidence": "assumption",
        "source": "data/team-kandu/rtl_trips.csv",
        "note": "Evidence layer 'inferred'; switch off in the Data menu (research/18_data_gaps.md T4).",
    })
    return len(added)


def stamp_build(network: dict) -> str:
    """Content hash of the network (without the build block) as a shared build id."""
    network["meta"].pop("build", None)
    digest = hashlib.sha256(json.dumps(network, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    network["meta"]["build"] = {"id": digest, "script": "scripts/multimodal/augment_network.py"}
    return digest


def main() -> None:
    network = json.loads(WEB_NETWORK.read_text(encoding="utf-8"))
    strip_previous(network)
    weekday = WEEKDAYS[date.fromisoformat(network["meta"]["referenceDay"]).weekday()]
    index = IslandIndex(network["islands"])
    mtcc = add_mtcc(network, index, weekday)
    observed = add_observed(network)
    inferred = add_inferred_returns(network)
    air_days = fix_air_calendar(network)
    counts = network["meta"].setdefault("counts", {})
    counts["stops"] = len(network["stops"])
    counts["ferryTrips"] = sum(1 for s in network["services"] if s["kind"] == "timetabled")
    counts["observedSeaLinks"] = observed["links"]
    counts["accessEdges"] = len(network["accessEdges"])
    counts["services"] = len(network["services"])
    counts["inferredReturns"] = inferred
    build_id = stamp_build(network)
    text = json.dumps(network, indent=1) + "\n"  # same layout as build_network.py output
    WEB_NETWORK.write_text(text, encoding="utf-8")
    if PROCESSED_NETWORK.parent.exists():
        PROCESSED_NETWORK.write_text(text, encoding="utf-8")
    print(f"MTCC: {mtcc['trips']} trips, {mtcc['stops']} stops; {mtcc['otherDays']} do not run on {weekday}s")
    if mtcc["unmatched"]:
        print("  unmatched MTCC islands:", ", ".join(mtcc["unmatched"]))
    print(f"Observed boat links: {observed['links']}; inferred returns: {inferred}; air services on weekdays: {air_days}")
    print(f"build id {build_id}")


if __name__ == "__main__":
    main()
