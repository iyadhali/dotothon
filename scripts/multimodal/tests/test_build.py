#!/usr/bin/env python3
"""Invariant tests for the multimodal network artifacts (contract §5)."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "multimodal" / "build_network.py"
PROCESSED = ROOT / "data" / "processed" / "multimodal"
NETWORK_PATH = PROCESSED / "network.json"
GEOJSON_PATH = PROCESSED / "islands.geojson"
ALIASES_PATH = PROCESSED / "aliases.csv"
REPORT_PATH = PROCESSED / "report.json"
PUBLIC_NETWORK_PATH = ROOT / "web" / "public" / "data" / "multimodal.json"
PUBLIC_GEOJSON_PATH = ROOT / "web" / "public" / "data" / "islands.geojson"

MASTER_CSV = ROOT / "data" / "external" / "_derived" / "mdv_islands_master.csv"
CROSSWALK_CSV = ROOT / "data" / "external" / "_derived" / "census2022_to_codab_crosswalk.csv"
CENSUS_CSV = ROOT / "data" / "external" / "_derived" / "census2022_population_by_island.csv"
STOPS_CSV = ROOT / "data" / "team-kandu" / "rtl_stops.csv"
TRIPS_CSV = ROOT / "data" / "team-kandu" / "rtl_trips.csv"
ROUTES_CSV = ROOT / "data" / "team-kandu" / "rtl_routes.csv"
AIRPORTS_CSV = ROOT / "data" / "external" / "air" / "airports.csv"
AIR_ROUTES_CSV = ROOT / "data" / "external" / "air" / "domestic_routes.csv"
HEALTH_CSV = (
    ROOT / "data" / "external" / "health" / "_derived" / "public_health_facility_master.csv"
)
EDUCATION_CSV = ROOT / "data" / "external" / "education" / "institutions_master.csv"
DIAGNOSTIC_CSV = (
    ROOT / "data" / "external" / "health" / "services" / "diagnostics" / "diagnostic_services.csv"
)
SPECIALIST_CSV = (
    ROOT / "data" / "external" / "health" / "services" / "specialist" / "specialist_services.csv"
)
DENTAL_CSV = (
    ROOT / "data" / "external" / "health" / "services" / "dental" / "dental_services.csv"
)
HDX_HEADLINE_CSV = ROOT / "data" / "processed" / "heigit" / "heigit_headline_adm0.csv"
HDX_UNITS_CSV = ROOT / "data" / "processed" / "heigit" / "heigit_unit_summary.csv"
HDX_JSON = ROOT / "web" / "public" / "data" / "heigit-baseline.json"
QGIS_DIR = PROCESSED / "qgis"
GEOJSON_SRC = (
    ROOT / "data" / "external" / "hdx-cod-ab" / "extracted" / "mdv_admin2.geojson"
)
BUILD_INPUTS = (
    MASTER_CSV,
    CROSSWALK_CSV,
    CENSUS_CSV,
    STOPS_CSV,
    TRIPS_CSV,
    ROUTES_CSV,
    AIRPORTS_CSV,
    AIR_ROUTES_CSV,
    HEALTH_CSV,
    EDUCATION_CSV,
    DIAGNOSTIC_CSV,
    SPECIALIST_CSV,
    DENTAL_CSV,
    GEOJSON_SRC,
)
DATA_AVAILABLE = all(path.exists() for path in BUILD_INPUTS)
INTERVENTION_AVAILABLE = all(
    path.exists() for path in (DIAGNOSTIC_CSV, SPECIALIST_CSV, DENTAL_CSV)
)
HDX_AVAILABLE = HDX_JSON.exists() and HDX_HEADLINE_CSV.exists() and HDX_UNITS_CSV.exists()
QGIS_AVAILABLE = (
    QGIS_DIR.exists()
    and NETWORK_PATH.exists()
    and (QGIS_DIR / "facilities.geojson").exists()
    and (QGIS_DIR / "ferry_routes.geojson").exists()
    and (QGIS_DIR / "air_routes.geojson").exists()
    and (QGIS_DIR / "access_edges.geojson").exists()
    and (QGIS_DIR / "access_style.qml").exists()
)
SERVICE_CATEGORY_GROUP = {
    "Diagnostics & procedures",
    "Specialist services",
    "Dental",
}
TRIPS_AVAILABLE = STOPS_CSV.exists() and TRIPS_CSV.exists()
AIR_ROUTES_AVAILABLE = AIR_ROUTES_CSV.exists()
PUBLIC_COPIES_AVAILABLE = PUBLIC_NETWORK_PATH.exists() and PUBLIC_GEOJSON_PATH.exists()

FIXED_GENERATED_AT = "2026-10-10T00:00:00+05:00"
CATEGORY_IDS = {
    "health_any",
    "health_hospital",
    "health_regional_tertiary",
    "education_grade_11_12",
    "education_higher_ed",
    "education_school",
}
HOSPITAL_TIERS = {
    "1_tertiary",
    "2_regional_hospital",
    "2_general_hospital",
    "2_hospital_other",
    "3_atoll_hospital",
    "3_atoll_hospital_small",
}
HIGHER_ED_TYPES = {
    "college campus",
    "university campus",
    "university campus (outreach centre)",
    "institute",
    "institute (outreach centre)",
    "TVET institute",
}


def reject_constant(value):
    raise ValueError(f"non-finite JSON constant: {value}")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def assert_finite(value, where="root"):
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise AssertionError(f"non-finite number at {where}")
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_finite(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_finite(item, f"{where}[{index}]")


def assert_no_nan(value, where="root"):
    if isinstance(value, float) and math.isnan(value):
        raise AssertionError(f"NaN at {where}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert_no_nan(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_nan(item, f"{where}[{index}]")


class ArtifactTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path in (NETWORK_PATH, GEOJSON_PATH, ALIASES_PATH, REPORT_PATH):
            if not path.exists():
                raise unittest.SkipTest(
                    f"{path} missing; run python3 scripts/multimodal/build_network.py"
                )
        cls.network = load_json(NETWORK_PATH)
        cls.report = load_json(REPORT_PATH)
        cls.geojson = load_json(GEOJSON_PATH)
        with open(ALIASES_PATH, encoding="utf-8", newline="") as handle:
            cls.alias_rows = list(csv.DictReader(handle))
        cls.islands = {island["id"]: island for island in cls.network["islands"]}
        cls.stops = {stop["id"]: stop for stop in cls.network["stops"]}
        cls.airports = {airport["iata"]: airport for airport in cls.network["airports"]}
        cls.categories = {category["id"]: category for category in cls.network["categories"]}
        cls.facilities = {facility["id"]: facility for facility in cls.network["facilities"]}


class TestMetadataAndSchema(ArtifactTestCase):
    def test_meta(self):
        meta = self.network["meta"]
        self.assertEqual(meta["schemaVersion"], 1)
        self.assertEqual(meta["timezone"], "Indian/Maldives")
        self.assertEqual(meta["referenceDay"], "2026-10-10")
        self.assertEqual(meta["population"]["origins"], 447_420)
        self.assertEqual(meta["population"]["republic2022"], 515_132)
        self.assertEqual(meta["population"]["originCount"], 191)
        self.assertIn("1,399", meta["population"]["note"])
        self.assertIn("66,313", meta["population"]["note"])
        self.assertIn("515,132", meta["population"]["note"])
        self.assertEqual(
            meta["routingDefaults"],
            {
                "ferryBoardMinutes": 15,
                "ferryAlightMinutes": 2,
                "airBoardMinutes": 45,
                "airBoardMinutesMle": 60,
                "airAlightMinutes": 15,
                "transferPenaltyMinutes": 10,
                "additionalBoardPenaltyMinutes": 5,
                "maxJourneyMinutes": 1440,
            },
        )
        self.assertEqual(meta["serviceData"]["rowsRead"], 1405)
        self.assertEqual(meta["serviceData"]["rowsExcludedResort"], 12)
        self.assertEqual(meta["serviceData"]["rowsExcludedUnresolvedIsland"], 7)
        self.assertEqual(meta["serviceData"]["categories"], 42)
        self.assertEqual(meta["serviceData"]["facilities"], 444)
        assumption_ids = {assumption["id"] for assumption in meta["assumptions"]}
        self.assertIn("intervention_service_evidence", assumption_ids)
        self.assertIn("air_departure_generation", assumption_ids)
        self.assertIn("population_scope", assumption_ids)
        self.assertTrue(
            all(
                assumption["confidence"] in {"source", "assumption", "estimated"}
                for assumption in meta["assumptions"]
            )
        )

    def test_counts_match_arrays(self):
        counts = self.network["meta"]["counts"]
        self.assertEqual(counts["islands"], len(self.network["islands"]))
        self.assertEqual(counts["origins"], sum(1 for island in self.network["islands"] if island["isOrigin"]))
        self.assertEqual(counts["stops"], len(self.network["stops"]))
        self.assertEqual(counts["airports"], len(self.network["airports"]))
        self.assertEqual(
            counts["ferryTrips"],
            sum(1 for service in self.network["services"] if service["kind"] == "timetabled"),
        )
        self.assertEqual(
            counts["airServices"],
            sum(1 for service in self.network["services"] if service.get("mode") == "air"),
        )
        self.assertEqual(counts["facilities"], len(self.network["facilities"]))
        self.assertEqual(counts["categories"], len(self.network["categories"]))
        self.assertEqual(counts["islands"], 200)
        self.assertEqual(counts["origins"], 191)
        self.assertEqual(counts["stops"], 117)
        self.assertEqual(counts["airports"], 20)
        self.assertEqual(counts["ferryTrips"], 102)
        self.assertEqual(counts["airServices"], 62)
        self.assertEqual(counts["facilities"], 945)
        self.assertEqual(counts["categories"], 48)

    def test_ids_are_unique_and_well_formed(self):
        for label, items in (
            ("island", self.network["islands"]),
            ("stop", self.network["stops"]),
            ("airport", self.network["airports"]),
            ("service", self.network["services"]),
            ("facility", self.network["facilities"]),
            ("category", self.network["categories"]),
        ):
            ids = [item["id"] for item in items]
            self.assertEqual(len(ids), len(set(ids)), f"duplicate {label} ids")
        for stop in self.network["stops"]:
            self.assertTrue(stop["id"].startswith("RTL:"), stop["id"])
            self.assertEqual(stop["id"], f"RTL:{stop['code']}")
        for airport in self.network["airports"]:
            self.assertEqual(airport["id"], airport["iata"])
            self.assertEqual(len(airport["iata"]), 3)

    def test_no_nan_or_infinity(self):
        assert_finite(self.network)
        assert_no_nan(self.network)
        assert_finite(self.geojson)
        assert_no_nan(self.geojson)
        assert_finite(self.report)
        assert_no_nan(self.report)


class TestPopulationAndIslands(ArtifactTestCase):
    def test_origin_population_exactly_447420(self):
        origins = [island for island in self.network["islands"] if island["isOrigin"]]
        self.assertEqual(len(origins), 191)
        self.assertEqual(sum(island["population"] for island in origins), 447_420)
        self.assertTrue(all(island["status"] == "inhabited" for island in origins))

    def test_greater_male_rows(self):
        expected = {
            "MV021001": ("Maale", 137_238),
            "MV021002": ("Vilin'gili", 6_755),
            "MV021003": ("Hulhumaale", 65_714),
            "MV009052": ("Hulhule", 802),
        }
        for island_id, (name, population) in expected.items():
            island = self.islands[island_id]
            self.assertEqual(island["name"], name)
            self.assertEqual(island["population"], population)
            self.assertTrue(island["isOrigin"])

    def test_airport_only_islands_are_non_origin_nodes(self):
        airport_islands = [island for island in self.network["islands"] if island["status"] == "airport"]
        self.assertEqual(len(airport_islands), 9)
        for island in airport_islands:
            self.assertFalse(island["isOrigin"])
            self.assertEqual(island["population"], 0)

    def test_every_origin_has_coordinates(self):
        for island in self.network["islands"]:
            self.assertIsInstance(island["lat"], float)
            self.assertIsInstance(island["lon"], float)
            self.assertTrue(72.0 < island["lon"] < 74.0, island["id"])
            self.assertTrue(-1.0 < island["lat"] < 8.0, island["id"])


class TestStopsAndFerry(ArtifactTestCase):
    def test_scheduled_stops(self):
        self.assertEqual(len(self.network["stops"]), 117)
        self.assertTrue(all(stop["scheduled"] is True for stop in self.network["stops"]))
        self.assertTrue(all(stop["islandId"] in self.islands for stop in self.network["stops"]))

    @unittest.skipUnless(TRIPS_AVAILABLE, "RTL source CSVs not present")
    def test_ferry_trips_reconstruct_rtl_trips(self):
        trips_path = TRIPS_CSV
        stops_path = STOPS_CSV
        with open(stops_path, encoding="utf-8-sig", newline="") as handle:
            stop_rows = list(csv.DictReader(handle))
        code_by_name = {row["name"]: row["code"] for row in stop_rows}

        with open(trips_path, encoding="utf-8-sig", newline="") as handle:
            trip_rows = list(csv.DictReader(handle))
        expected = defaultdict(list)
        for row in trip_rows:
            key = f"ferry:{int(row['route_id'])}:{int(row['trip'])}"
            hour, minute = row["time"].split(":")
            expected[key].append(
                (
                    int(row["order"]),
                    f"RTL:{code_by_name[row['stop']]}",
                    row["stop"],
                    int(hour) * 60 + int(minute),
                )
            )

        services = {
            service["id"]: service
            for service in self.network["services"]
            if service["kind"] == "timetabled"
        }
        self.assertEqual(len(services), 102)
        self.assertEqual(set(services), set(expected))
        for service_id, service in services.items():
            rows = sorted(expected[service_id])
            self.assertEqual([stop["sequence"] for stop in service["stops"]], [row[0] for row in rows])
            self.assertEqual([stop["stopId"] for stop in service["stops"]], [row[1] for row in rows])
            self.assertEqual([stop["name"] for stop in service["stops"]], [row[2] for row in rows])
            self.assertEqual([stop["arrival"] for stop in service["stops"]], [row[3] for row in rows])
            self.assertEqual([stop["departure"] for stop in service["stops"]], [row[3] for row in rows])
            self.assertEqual(service["confidence"], "verified_timetable")
            self.assertEqual(service["calendar"], "reference_day_all_recorded_trips")
            self.assertEqual(service["source"], "data/team-kandu/rtl_trips.csv")

    def test_route_259_direction_and_single_recorded_time(self):
        service = next(
            item for item in self.network["services"] if item["id"] == "ferry:259:1"
        )
        self.assertEqual(
            [stop["stopId"] for stop in service["stops"]],
            ["RTL:207", "RTL:208", "RTL:209"],
        )
        self.assertEqual([stop["arrival"] for stop in service["stops"]], [905, 915, 930])
        self.assertTrue(
            all(stop["arrival"] == stop["departure"] for stop in service["stops"])
        )

    def test_every_timetabled_stop_is_referenced(self):
        referenced = {
            stop["stopId"]
            for service in self.network["services"]
            if service["kind"] == "timetabled"
            for stop in service["stops"]
        }
        self.assertEqual(referenced, set(self.stops))
        self.assertEqual(len(referenced), 117)


class TestAccessEdges(ArtifactTestCase):
    def test_endpoints_and_modes(self):
        node_ids = {f"island:{island['id']}" for island in self.network["islands"]}
        node_ids |= {f"stop:{stop['id']}" for stop in self.network["stops"]}
        node_ids |= {f"airport:{airport['iata']}" for airport in self.network["airports"]}
        self.assertEqual(len(self.network["accessEdges"]), 153)
        for edge in self.network["accessEdges"]:
            self.assertIn(edge["from"], node_ids)
            self.assertIn(edge["to"], node_ids)
            self.assertIn(edge["mode"], {"walk", "road", "speedboat", "ferry_transfer"})
            self.assertIn(
                edge["confidence"],
                {"verified_timetable", "estimated_frequency", "estimated_access", "assumption"},
            )
            self.assertGreater(edge["minutes"], 0)
            self.assertTrue(edge["basis"])

    def test_no_access_edge_crosses_water(self):
        node_island = {}
        for island in self.network["islands"]:
            node_island[f"island:{island['id']}"] = island["id"]
        for stop in self.network["stops"]:
            node_island[f"stop:{stop['id']}"] = stop["islandId"]
        for airport in self.network["airports"]:
            node_island[f"airport:{airport['iata']}"] = airport["islandId"]

        allowed_bases = ("Hulhumeedhoo", "Hoarafushi")
        for edge in self.network["accessEdges"]:
            source_island = node_island[edge["from"]]
            target_island = node_island[edge["to"]]
            if source_island == target_island:
                continue
            if edge["mode"] in {"road", "speedboat"}:
                continue
            if edge["mode"] == "walk" and any(
                marker in edge["basis"] for marker in allowed_bases
            ):
                continue
            self.fail(
                f"walk edge crosses islands: {edge['from']} ({source_island}) -> "
                f"{edge['to']} ({target_island})"
            )

    def test_every_airport_has_access(self):
        for airport in self.network["airports"]:
            node = f"airport:{airport['iata']}"
            incident = [
                edge
                for edge in self.network["accessEdges"]
                if edge["from"] == node or edge["to"] == node
            ]
            self.assertTrue(incident, f"{airport['iata']} has no access edge")

    def test_airport_access_paths_and_link_roads(self):
        adjacency = defaultdict(set)
        for edge in self.network["accessEdges"]:
            adjacency[edge["from"]].add(edge["to"])
            adjacency[edge["to"]].add(edge["from"])
        for service in self.network["services"]:
            if service["kind"] == "timetabled":
                nodes = [f"stop:{stop['stopId']}" for stop in service["stops"]]
                for left, right in zip(nodes, nodes[1:]):
                    adjacency[left].add(right)
                    adjacency[right].add(left)
            else:
                adjacency[service["fromNode"]].add(service["toNode"])
                adjacency[service["toNode"]].add(service["fromNode"])

        origin_nodes = {
            f"island:{island['id']}"
            for island in self.network["islands"]
            if island["isOrigin"]
        }
        for airport in self.network["airports"]:
            start = f"airport:{airport['iata']}"
            seen = {start}
            stack = [start]
            while stack:
                current = stack.pop()
                for neighbour in adjacency[current]:
                    if neighbour not in seen:
                        seen.add(neighbour)
                        stack.append(neighbour)
            self.assertTrue(
                seen & origin_nodes, f"airport {airport['iata']} cannot reach an origin"
            )

        def bases_contain(text):
            return [
                edge
                for edge in self.network["accessEdges"]
                if text in edge["basis"]
            ]

        self.assertTrue(bases_contain("Sinamalé Bridge"))
        self.assertTrue(bases_contain("Hulhulé to Hulhumalé"))
        self.assertEqual(len(bases_contain("Addu Link Road")), 4)
        self.assertEqual(len(bases_contain("Laamu Link Road")), 2)
        self.assertTrue(bases_contain("Hoarafushi town"))
        self.assertTrue(bases_contain("Naifaru"))
        self.assertTrue(bases_contain("Faresmaathodaa town"))

    def test_stop_access_rules(self):
        stop_edges = [
            edge
            for edge in self.network["accessEdges"]
            if edge["from"].startswith("island:") and edge["to"].startswith("stop:")
        ]
        self.assertEqual(len(stop_edges), 118)  # 117 stops + combined Hulhumeedhoo second edge
        long_edges = [edge for edge in stop_edges if edge["distanceKm"] and edge["distanceKm"] > 1.5]
        self.assertTrue(long_edges)
        for edge in long_edges:
            self.assertEqual(edge["mode"], "road")
            self.assertTrue(edge.get("assumed"))
            self.assertIn("25 km/h", edge["basis"])


class TestAirServices(ArtifactTestCase):
    def test_directed_services_and_reverse_pairs(self):
        air = [service for service in self.network["services"] if service.get("mode") == "air"]
        self.assertEqual(len(air), 62)
        by_id = {service["id"]: service for service in air}
        pairs = set()
        for service in air:
            origin = service["fromAirport"]
            destination = service["toAirport"]
            self.assertEqual(service["fromNode"], f"airport:{origin}")
            self.assertEqual(service["toNode"], f"airport:{destination}")
            self.assertIn(origin, self.airports)
            self.assertIn(destination, self.airports)
            reverse = by_id[f"air:{destination}-{origin}"]
            self.assertEqual(reverse["weeklyFrequency"], service["weeklyFrequency"])
            self.assertEqual(reverse["blockMinutes"], service["blockMinutes"])
            self.assertEqual(reverse["departures"], service["departures"])
            pairs.add(tuple(sorted((origin, destination))))
        self.assertEqual(len(pairs), 31)

    def test_departure_generation(self):
        for service in self.network["services"]:
            if service.get("mode") != "air":
                continue
            weekly = service["weeklyFrequency"]
            per_day = max(1, round(weekly / 7))
            self.assertEqual(service["departuresPerDay"], per_day)
            self.assertEqual(len(service["departures"]), per_day)
            self.assertEqual(service["departures"], sorted(set(service["departures"])))
            self.assertTrue(all(360 <= minute <= 1080 for minute in service["departures"]))
            self.assertEqual(service["operatingWindow"], {"start": 360, "end": 1080})
            self.assertEqual(service["confidence"], "estimated_frequency")

    @unittest.skipUnless(AIR_ROUTES_AVAILABLE, "domestic_routes.csv not present")
    def test_source_frequencies_and_exclusions(self):
        routes_path = AIR_ROUTES_CSV
        with open(routes_path, encoding="utf-8-sig", newline="") as handle:
            routes = list(csv.DictReader(handle))
        operating = [row for row in routes if "operating" in row["status"].lower()]
        self.assertEqual(len(operating), 32)
        air = {
            (service["fromAirport"], service["toAirport"]): service
            for service in self.network["services"]
            if service.get("mode") == "air"
        }
        for row in operating:
            if len(row["dest_iata"].strip()) != 3:
                continue
            origin = row["origin_iata"].strip()
            destination = row["dest_iata"].strip()
            service = air[(origin, destination)]
            self.assertEqual(service["blockMinutes"], int(round(float(row["block_time_min"]))))
            self.assertEqual(
                service["weeklyFrequency"], int(round(float(row["weekly_frequency_each_way"])))
            )

        excluded = self.network["meta"]["excludedAirRoutes"]
        self.assertEqual(len(excluded), 9)
        seaplane = [
            route for route in excluded if route["to"] == "(resort water aerodromes)"
        ]
        self.assertEqual(len(seaplane), 1)
        self.assertIn("seaplane", seaplane[0]["reason"])
        self.assertTrue(any("ceased" in route["reason"] for route in excluded))
        self.assertTrue(any("suspended" in route["reason"] for route in excluded))
        self.assertTrue(any("July 2026" in route["reason"] for route in excluded))
        self.assertEqual(self.report["air"]["airportPairsIncluded"], 31)


class TestFacilities(ArtifactTestCase):
    def test_counts_and_categories(self):
        health = [facility for facility in self.network["facilities"] if facility["kind"] == "health"]
        education = [facility for facility in self.network["facilities"] if facility["kind"] == "education"]
        intervention = [
            facility
            for facility in self.network["facilities"]
            if facility.get("serviceCategories")
        ]
        self.assertEqual(len(health), 633)
        self.assertEqual(len(education), 312)
        self.assertEqual(len(intervention), 444)
        self.assertEqual(len(self.network["facilities"]), 945)
        self.assertEqual(
            {category["id"] for category in self.network["categories"]} - {
                category["id"] for category in self.network["categories"] if category.get("kind") == "intervention"
            },
            CATEGORY_IDS,
        )
        service_categories = {
            category["id"]
            for category in self.network["categories"]
            if category.get("kind") == "intervention"
        }
        self.assertEqual(len(service_categories), 42)
        self.assertTrue(all(category.startswith("service:") for category in service_categories))
        expected = {
            "health_any": (189, 186),
            "health_hospital": (24, 22),
            "health_regional_tertiary": (10, 8),
            "education_grade_11_12": (44, 40),
            "education_higher_ed": (81, 40),
            "education_school": (231, 185),
        }
        for category_id, (facility_count, island_count) in expected.items():
            category = self.categories[category_id]
            self.assertEqual(category["facilityCount"], facility_count)
            self.assertEqual(category["islandCount"], island_count)
            members = [
                facility
                for facility in self.network["facilities"]
                if category_id in facility["categories"]
            ]
            self.assertEqual(len(members), facility_count)
            self.assertEqual(len({facility["islandId"] for facility in members}), island_count)

    def test_facility_rules(self):
        for facility in self.network["facilities"]:
            self.assertIn(facility["islandId"], self.islands)
            self.assertTrue(facility["categories"], facility["id"])
            self.assertEqual(facility["precision"], "island")
            self.assertIsInstance(facility["reviewed"], bool)
            if facility.get("serviceCategories"):
                self.assertEqual(facility["serviceCategories"], facility["categories"])
                self.assertTrue(
                    all(category.startswith("service:") for category in facility["categories"])
                )
                self.assertFalse(facility["userAdded"])
                self.assertTrue(facility["serviceEvidence"])
                self.assertEqual(
                    {item["category"] for item in facility["serviceEvidence"]},
                    set(facility["serviceCategories"]),
                )
                continue
            self.assertTrue(set(facility["categories"]).issubset(CATEGORY_IDS))
            if facility["kind"] == "health":
                self.assertIn("health_any", facility["categories"])
                tier = facility.get("tier", "")
                if tier in HOSPITAL_TIERS:
                    self.assertIn("health_hospital", facility["categories"])
                else:
                    self.assertNotIn("health_hospital", facility["categories"])
                if tier.startswith(("1_", "2_")):
                    self.assertIn("health_regional_tertiary", facility["categories"])
                else:
                    self.assertNotIn("health_regional_tertiary", facility["categories"])
            else:
                self.assertEqual(facility["kind"], "education")
                self.assertIn(facility["type"], HIGHER_ED_TYPES | {"school", "higher secondary school", "preschool"})
                if facility["type"] in {"school", "higher secondary school"}:
                    self.assertIn("education_school", facility["categories"])

    def test_unresolved_rows_counted_not_dropped(self):
        health_excluded = self.report["excluded"]["healthFacilities"]
        education_excluded = self.report["excluded"]["educationFacilities"]
        self.assertEqual(len(health_excluded), 8)
        self.assertEqual(len(education_excluded), 120)
        zero_category = self.report["excluded"]["educationZeroCategoryFacilities"]
        self.assertEqual(len(zero_category), 50)
        self.assertEqual(
            Counter(item["type"] for item in zero_category),
            Counter({"preschool": 36, "institute (Quran centre)": 14}),
        )
        served = [f for f in self.network["facilities"] if f["kind"] == "education"]
        self.assertEqual(
            len(served) + len(education_excluded) + len(zero_category) + 1, 483
        )
        self.assertEqual(len(self.report["excluded"]["educationDuplicateRows"]), 1)
        by_source = self.report["aliases"]["bySource"]
        self.assertEqual(by_source["health"], 197)
        self.assertEqual(by_source["education"], 483)


class TestAliases(ArtifactTestCase):
    def test_csv_shape_and_counts(self):
        with open(ALIASES_PATH, encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(
                reader.fieldnames,
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
                ],
            )
        self.assertEqual(len(self.alias_rows), 818)
        by_source = Counter(row["source"] for row in self.alias_rows)
        self.assertEqual(
            by_source,
            Counter({"education": 483, "health": 197, "rtl_stops": 118, "airports": 20}),
        )
        by_method = Counter(row["method"] for row in self.alias_rows)
        self.assertEqual(
            by_method,
            Counter({"exact": 512, "manual": 122, "unresolved": 128, "fuzzy": 56}),
        )

    def test_fuzzy_rows_are_reviewable_and_reviewed_false(self):
        for row in self.alias_rows:
            self.assertIn(row["method"], {"exact", "fuzzy", "manual", "unresolved"})
            self.assertIn(row["reviewed"], {"true", "false"})
            if row["method"] == "fuzzy":
                self.assertEqual(row["reviewed"], "false")
                score = float(row["score"])
                self.assertGreaterEqual(score, 0.8)
                self.assertLessEqual(score, 1.0)
            elif row["method"] in {"exact", "manual"}:
                self.assertEqual(row["reviewed"], "true")
                self.assertEqual(row["score"], "1.000")
            else:
                self.assertEqual(row["reviewed"], "false")
                self.assertEqual(row["score"], "")
                self.assertEqual(row["island_id"], "")

    def test_alias_islands_exist(self):
        for row in self.alias_rows:
            if row["island_id"]:
                self.assertIn(row["island_id"], self.islands, row)

    def test_known_manual_joins(self):
        def find(source, atoll, name):
            return [
                row
                for row in self.alias_rows
                if row["source"] == source
                and row["source_atoll"] == atoll
                and row["source_name"] == name
            ]

        self.assertEqual(find("rtl_stops", "L", "Gan")[0]["island_id"], "MV015013")
        self.assertEqual(find("rtl_stops", "GDh", "Kaadehdhoo")[0]["island_id"], "MV017013")
        self.assertEqual(find("rtl_stops", "GA", "Kooddoo")[0]["island_id"], "MV016054")
        hulhumeedhoo = find("rtl_stops", "S", "Hulhumeedhoo")
        self.assertEqual(
            {row["island_id"] for row in hulhumeedhoo}, {"MV019006", "MV019001"}
        )
        fmt = find("airports", "GDh", "Fares-Maathodaa")
        self.assertEqual(fmt[0]["island_id"], "MV017141")
        self.assertEqual(fmt[0]["island_name"], "Maarehaa")
        self.assertEqual(self.airports["FMT"]["islandId"], "MV017141")
        self.assertEqual(find("airports", "HA", "Hoarafushi")[0]["island_id"], "MV001031")


class TestGeoJSON(ArtifactTestCase):
    def test_features(self):
        self.assertEqual(self.geojson["type"], "FeatureCollection")
        self.assertEqual(len(self.geojson["features"]), 200)
        self.assertEqual(
            {feature["properties"]["islandId"] for feature in self.geojson["features"]},
            set(self.islands),
        )
        self.assertTrue(GEOJSON_PATH.stat().st_size < 2 * 1024 * 1024)

    def test_properties_and_coordinates(self):
        expected_keys = {
            "islandId",
            "name",
            "atoll",
            "population",
            "status",
            "isOrigin",
            "lat",
            "lon",
        }
        for feature in self.geojson["features"]:
            properties = feature["properties"]
            self.assertEqual(set(properties), expected_keys)
            self.assertIsInstance(properties["isOrigin"], bool)
            geometry = feature["geometry"]
            self.assertIn(geometry["type"], {"Polygon", "MultiPolygon"})
            polygons = (
                [geometry["coordinates"]]
                if geometry["type"] == "Polygon"
                else geometry["coordinates"]
            )
            for polygon in polygons:
                for ring in polygon:
                    self.assertGreaterEqual(len(ring), 4)
                    self.assertEqual(ring[0], ring[-1])
                    for longitude, latitude in ring:
                        self.assertEqual(round(longitude, 5), longitude)
                        self.assertEqual(round(latitude, 5), latitude)
                        self.assertTrue(72.0 < longitude < 74.0)
                        self.assertTrue(-1.0 < latitude < 8.0)


class TestReportConsistency(ArtifactTestCase):
    def test_report_matches_network(self):
        self.assertEqual(self.report["counts"], self.network["meta"]["counts"])
        self.assertTrue(all(self.report["checks"].values()))
        self.assertEqual(self.report["population"]["omittedHarbourArea"], 1_399)
        self.assertEqual(self.report["population"]["omittedNonAdminIsland"], 66_313)
        self.assertEqual(self.report["population"]["omittedTotal"], 67_712)
        self.assertEqual(self.report["aliases"]["total"], 818)
        self.assertEqual(len(self.report["aliases"]["fuzzy"]), 56)
        self.assertEqual(len(self.report["aliases"]["unresolved"]), 128)
        self.assertEqual(self.report["access"]["airportsWithAccess"], 20)
        self.assertEqual(self.report["access"]["byMode"], {"road": 13, "speedboat": 2, "walk": 138})

    @unittest.skipUnless(PUBLIC_COPIES_AVAILABLE, "public copies not present")
    def test_public_copies_are_byte_identical(self):
        self.assertEqual(NETWORK_PATH.read_bytes(), PUBLIC_NETWORK_PATH.read_bytes())
        self.assertEqual(GEOJSON_PATH.read_bytes(), PUBLIC_GEOJSON_PATH.read_bytes())


@unittest.skipUnless(DATA_AVAILABLE, "source datasets not present")
class TestDeterminism(ArtifactTestCase):
    def run_build(self, out_dir: Path):
        command = [
            sys.executable,
            str(SCRIPT),
            "--generated-at",
            FIXED_GENERATED_AT,
            "--out-dir",
            str(out_dir),
            "--skip-public",
        ]
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_two_runs_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_dir = Path(first)
            second_dir = Path(second)
            self.run_build(first_dir)
            self.run_build(second_dir)
            for filename in ("network.json", "islands.geojson", "aliases.csv", "report.json"):
                self.assertEqual(
                    (first_dir / filename).read_bytes(),
                    (second_dir / filename).read_bytes(),
                    f"{filename} is not deterministic",
                )
            network = load_json(first_dir / "network.json")
            self.assertEqual(network["meta"]["generatedAt"], FIXED_GENERATED_AT)


class TestCoverageAndCanonicalNames(ArtifactTestCase):
    def test_laamu_gan_uses_transport_name_and_keeps_census_name(self):
        gan = self.islands["MV015013"]
        self.assertEqual(gan["name"], "Gan")
        self.assertEqual(gan["atoll"], "L")
        override = self.report["canonicalNameOverrides"][0]
        self.assertEqual(override["islandId"], "MV015013")
        self.assertEqual(override["displayName"], "Gan")
        self.assertEqual(override["censusName"], "Gamu")
        rows = [row for row in self.alias_rows if row["island_id"] == "MV015013"]
        self.assertTrue(rows)
        self.assertTrue(all(row["census_name"] == "Gamu" for row in rows))

    def test_origin_access_coverage(self):
        coverage = self.report["originAccess"]
        self.assertEqual(coverage["origins"], 191)
        self.assertEqual(coverage["withAccess"], 124)
        self.assertEqual(coverage["withoutAccess"], 67)
        self.assertEqual(coverage["populationWithAccess"], 383_671)
        self.assertEqual(coverage["populationWithoutAccess"], 63_749)
        self.assertEqual(
            coverage["populationWithAccess"] + coverage["populationWithoutAccess"],
            447_420,
        )
        self.assertEqual(
            coverage["withAccess"],
            coverage["withAccessViaAccessEdge"] + coverage["withAccessViaFrequencyOnly"],
        )
        self.assertEqual(coverage["withAccessViaFrequencyOnly"], 1)

        # Recompute the headline from the served graph.
        origins = {
            island["id"]: island
            for island in self.network["islands"]
            if island["isOrigin"]
        }
        incident = set()
        for edge in self.network["accessEdges"]:
            for endpoint in (edge["from"], edge["to"]):
                if endpoint.startswith("island:"):
                    incident.add(endpoint.split(":", 1)[1])
        for service in self.network["services"]:
            if service["kind"] != "frequency":
                continue
            for endpoint in (service["fromNode"], service["toNode"]):
                if endpoint.startswith("island:"):
                    incident.add(endpoint.split(":", 1)[1])
        covered = set(origins) & incident
        self.assertEqual(len(covered), 124)
        self.assertEqual(len(set(origins) - incident), 67)
        self.assertEqual(
            sum(origins[island_id]["population"] for island_id in covered), 383_671
        )
        self.assertEqual(sum(island["population"] for island in origins.values()), 447_420)

        by_atoll = {item["atoll"]: item for item in coverage["byAtoll"]}
        self.assertEqual(
            sum(item["origins"] for item in by_atoll.values()), 191
        )
        self.assertEqual(
            sum(item["withoutAccess"] for item in by_atoll.values()), 67
        )
        self.assertEqual(
            sum(item["populationWithoutAccess"] for item in by_atoll.values()), 63_749
        )
        self.assertIn("124 of 191", self.network["meta"]["coverageNotes"][1])


class TestInterventionLayer(ArtifactTestCase):
    def test_metadata_and_report(self):
        meta = self.network["meta"]["serviceData"]
        report = self.report["intervention"]
        self.assertEqual(meta["rowsRead"], 1405)
        self.assertEqual(meta["rowsUsed"], 1386)
        self.assertEqual(meta["rowsExcludedResort"], 12)
        self.assertEqual(meta["rowsExcludedUnresolvedIsland"], 7)
        self.assertEqual(meta["facilities"], 444)
        self.assertEqual(meta["categories"], 42)
        self.assertEqual(report["rowsRead"], meta["rowsRead"])
        self.assertEqual(report["rowsUsed"], 1386)
        self.assertEqual(report["facilities"], 444)
        self.assertEqual(report["categories"], 42)
        self.assertEqual(report["evidenceItems"], 1279)
        self.assertEqual(report["duplicateEvidenceRowsMerged"], 107)
        self.assertEqual(report["bySourceFile"], {"dental": 222, "diagnostics": 396, "specialist": 787})

    def test_resort_rows_excluded_and_counted(self):
        report = self.report["intervention"]
        self.assertEqual(len(report["resortRows"]), 12)
        self.assertEqual(
            Counter(item["source"] for item in report["resortRows"]),
            Counter({"diagnostics": 10, "dental": 2}),
        )
        self.assertTrue(
            all(
                "resort" in item["island"].lower() or "guest" in item["island"].lower()
                for item in report["resortRows"]
            )
        )

    def test_unresolved_islands_excluded_and_counted(self):
        report = self.report["intervention"]
        self.assertEqual(len(report["unresolvedRows"]), 7)
        self.assertEqual(len(report["unresolvedGroups"]), 4)
        groups = {
            (item["source"], item["atoll"], item["island"]): item["rows"]
            for item in report["unresolvedGroups"]
        }
        self.assertEqual(groups[("dental", "K", "Hulhumalé (unverified)")], 2)
        self.assertEqual(groups[("specialist", "", "")], 3)
        self.assertEqual(groups[("specialist", "K", "Gulhifalhu")], 1)
        self.assertEqual(groups[("specialist", "N", "")], 1)
        for item in report["unresolvedRows"]:
            self.assertIn("no matching island", item["reason"])

    def test_duplicate_evidence_merged_to_one_row_per_category(self):
        intervention = [
            facility
            for facility in self.network["facilities"]
            if facility.get("serviceCategories")
        ]
        self.assertEqual(len(intervention), 444)
        for facility in intervention:
            categories = [item["category"] for item in facility["serviceEvidence"]]
            self.assertEqual(len(categories), len(set(categories)), facility["id"])
            self.assertEqual(set(categories), set(facility["serviceCategories"]))
            self.assertEqual(len(facility["categories"]), len(set(facility["categories"])))
        dental = [
            facility
            for facility in intervention
            if "service:dental" in facility["serviceCategories"]
        ]
        self.assertEqual(len(dental), 112)
        self.assertTrue(
            all(
                len(
                    [
                        item
                        for item in facility["serviceEvidence"]
                        if item["category"] == "service:dental"
                    ]
                )
                == 1
                for facility in dental
            )
        )

    def test_intervention_facility_contract(self):
        intervention = [
            facility
            for facility in self.network["facilities"]
            if facility.get("serviceCategories")
        ]
        for facility in intervention:
            self.assertTrue(facility["id"].startswith("health:service:"), facility["id"])
            self.assertEqual(facility["kind"], "health")
            self.assertEqual(facility["precision"], "island")
            self.assertIs(facility["userAdded"], False)
            self.assertTrue(facility["reviewed"])
            self.assertIn(facility["islandId"], self.islands)
            self.assertTrue(facility.get("source"))
            for evidence in facility["serviceEvidence"]:
                self.assertTrue(evidence["category"].startswith("service:"))
                self.assertIn(evidence["confidence"], {"high", "medium", "low", ""})
                self.assertTrue(evidence["source"].endswith(".csv"))
                self.assertTrue(evidence["detail"])
            self.assertNotIn("health_any", facility["categories"])
            self.assertNotIn("health_hospital", facility["categories"])

    def test_intervention_category_definitions(self):
        definitions = [
            category
            for category in self.network["categories"]
            if category.get("kind") == "intervention"
        ]
        self.assertEqual(len(definitions), 42)
        self.assertEqual(
            {category["group"] for category in definitions}, SERVICE_CATEGORY_GROUP
        )
        for category in definitions:
            self.assertTrue(category["id"].startswith("service:"))
            self.assertTrue(category["source"].endswith(".csv"))
            self.assertIn("evidence rows", category["confidenceNote"])
            members = [
                facility
                for facility in self.network["facilities"]
                if category["id"] in facility["categories"]
            ]
            self.assertEqual(category["facilityCount"], len(members))
            self.assertEqual(
                category["islandCount"], len({facility["islandId"] for facility in members})
            )


@unittest.skipUnless(HDX_AVAILABLE, "HeiGIT baseline inputs/output not present")
class TestHDXBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = load_json(HDX_JSON)

    def test_schema_and_counts(self):
        payload = self.payload
        self.assertEqual(set(payload), {"source", "method", "warning", "national", "units"})
        self.assertTrue(payload["source"])
        self.assertTrue(payload["method"])
        self.assertTrue(payload["warning"])
        self.assertEqual(len(payload["national"]), 34)
        self.assertEqual(len(payload["units"]), 43)

    def test_national_rows_preserve_source_values(self):
        for row in self.payload["national"]:
            self.assertEqual(
                set(row), {"category", "threshold", "share", "population"}
            )
            self.assertIn(row["category"], {"education", "hospitals", "primary_healthcare"})
            self.assertTrue(row["threshold"].endswith((" km", " min")))
            self.assertGreaterEqual(row["share"], 0)
            self.assertLessEqual(row["share"], 100)
            self.assertIsInstance(row["population"], int)
        first = self.payload["national"][0]
        self.assertEqual(
            (first["category"], first["threshold"], first["share"], first["population"]),
            ("education", "5 km", 46.92, 207761),
        )

    def test_unit_rows(self):
        for row in self.payload["units"]:
            self.assertEqual(set(row), {"admLevel", "name", "category", "within5km"})
            self.assertIn(row["admLevel"], {"ADM1", "ADM2"})
            self.assertTrue(row["name"])
            self.assertIn(row["category"], {"education", "hospitals", "primary_healthcare"})
            if row["within5km"] is not None:
                self.assertGreaterEqual(row["within5km"], 0)
                self.assertLessEqual(row["within5km"], 100)


@unittest.skipUnless(QGIS_AVAILABLE, "QGIS export not present")
class TestQGISExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.network = load_json(NETWORK_PATH)
        cls.islands = {item["id"]: item for item in cls.network["islands"]}

    def read_features(self, name):
        return load_json(QGIS_DIR / name)["features"]

    def test_files_and_island_copy(self):
        expected = {
            "islands.geojson",
            "facilities.geojson",
            "ferry_routes.geojson",
            "air_routes.geojson",
            "access_edges.geojson",
            "access_style.qml",
            "README.md",
        }
        self.assertTrue(expected.issubset({path.name for path in QGIS_DIR.iterdir()}))
        self.assertEqual(
            (QGIS_DIR / "islands.geojson").read_bytes(), GEOJSON_PATH.read_bytes()
        )

    def test_facility_points_match_island_centroids(self):
        features = self.read_features("facilities.geojson")
        self.assertEqual(len(features), len(self.network["facilities"]))
        for feature in features:
            properties = feature["properties"]
            island = self.islands[properties["islandId"]]
            self.assertEqual(feature["geometry"]["type"], "Point")
            self.assertEqual(feature["geometry"]["coordinates"], [island["lon"], island["lat"]])
            self.assertIn("categories", properties)

    def test_route_and_access_layers(self):
        ferries = self.read_features("ferry_routes.geojson")
        air = self.read_features("air_routes.geojson")
        access = self.read_features("access_edges.geojson")
        self.assertEqual(len(ferries), 102)
        self.assertEqual(len(air), 31)
        self.assertEqual(len(access), 153)
        self.assertTrue(all(feature["geometry"]["type"] == "LineString" for feature in ferries + air + access))
        air_pairs = {feature["properties"]["pair"] for feature in air}
        self.assertEqual(len(air_pairs), 31)

    def test_access_style(self):
        qml = (QGIS_DIR / "access_style.qml").read_text(encoding="utf-8")
        self.assertIn("categorizedSymbol", qml)
        for mode in ("walk", "road", "speedboat"):
            self.assertIn(f'value="{mode}"', qml)
        readme = (QGIS_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("EPSG:4326", readme)


class TestAliasNormalisationFixture(unittest.TestCase):
    """Data-independent tests for the normalisation/resolution rules."""

    @classmethod
    def setUpClass(cls):
        if not SCRIPT.exists():
            raise unittest.SkipTest(f"{SCRIPT} missing")
        try:
            import pandas as pd
        except ImportError:
            raise unittest.SkipTest("pandas is not installed")
        spec = importlib.util.spec_from_file_location(
            "multimodal_build_network_for_tests", SCRIPT
        )
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except ImportError as error:
            raise unittest.SkipTest(f"build module dependencies missing: {error}")
        cls.module = module
        cls.pd = pd

    def make_resolver(self, manual=None):
        islands = [
            {"id": "MV012002", "name": "Badidhoo", "atoll": "Dh"},
            {"id": "MV012003", "name": "Ribudhoo", "atoll": "Dh"},
            {"id": "MV019004", "name": "Feydhoo", "atoll": "S"},
            {"id": "MV019006", "name": "Feydhoo", "atoll": "S"},
        ]
        master = self.pd.DataFrame(
            {
                "adm2_name": ["Ban'didhoo", "Rin'budhoo", "Feydhoo", "Feydhoo"],
                "adm2_name1": [None, None, None, None],
                "adm2_name2": [None, None, None, None],
                "adm2_name3": [None, None, None, None],
                "adm2_ref_name": [None, None, None, None],
            },
            index=["MV012002", "MV012003", "MV019004", "MV019006"],
        )
        return self.module.IslandResolver(
            islands, master, manual or {}, {"MV012002": "Badidhoo", "MV012003": "Ribudhoo"}
        )

    def test_norm_and_phonetic_elision(self):
        module = self.module
        self.assertEqual(module.norm("B.Dharavandhoo"), "bdharavandhoo")
        self.assertEqual(module.norm("Ban'didhoo"), "bandidhoo")
        self.assertEqual(module.norm("Maaen'boodhoo"), "maaenboodhoo")
        self.assertEqual(
            module.phonetic("Bandidhoo"), module.phonetic("Badidhoo")
        )
        self.assertEqual(module.phonetic("Kondey"), module.phonetic("Kodey"))
        self.assertNotEqual(module.phonetic("Maafushi"), module.phonetic("Mahibadhoo"))

    def test_atoll_normalisation(self):
        module = self.module
        self.assertEqual(module.normalise_atoll("K-Male"), "MLE")
        self.assertEqual(module.normalise_atoll("Male' City"), "MLE")
        self.assertEqual(module.normalise_atoll("gdh"), "GDh")
        self.assertEqual(module.normalise_atoll("HA"), "HA")

    def test_exact_fuzzy_manual_and_ambiguous(self):
        resolver = self.make_resolver()
        exact = resolver.resolve("test", "Dh", "Bandidhoo")
        self.assertEqual((exact["method"], exact["island_ids"]), ("exact", ["MV012002"]))
        fuzzy = resolver.resolve("test", "Dh", "Badidho")
        self.assertEqual((fuzzy["method"], fuzzy["island_ids"]), ("fuzzy", ["MV012002"]))
        self.assertGreaterEqual(fuzzy["score"], 0.8)
        missing = resolver.resolve("test", "S", "Bandidhoo")
        self.assertEqual(missing["method"], "unresolved")
        ambiguous = resolver.resolve("test", "S", "Feydhoo")
        self.assertEqual(ambiguous["method"], "unresolved")
        self.assertEqual(ambiguous["reason"], "ambiguous exact name within atoll")

        manual = self.make_resolver({("test", "Dh", "custom"): "MV012003"})
        resolved = manual.resolve("test", "Dh", "Custom")
        self.assertEqual((resolved["method"], resolved["island_ids"]), ("manual", ["MV012003"]))


if __name__ == "__main__":
    unittest.main()
