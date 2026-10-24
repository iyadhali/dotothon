#!/usr/bin/env python3
"""Export the multimodal network as QGIS-ready GeoJSON layers (contract §10.5).

Standard library only.  Layers are derived from the processed network artifact
so QGIS sees exactly the same facilities, services and access edges as the web
application.

Outputs (default data/processed/multimodal/qgis/):
  islands.geojson       simplified island polygons (byte copy)
  facilities.geojson    island-centroid points for every served facility
  ferry_routes.geojson  LineStrings for each recorded RTL ferry trip
  air_routes.geojson    LineStrings for each operating domestic air pair
  access_edges.geojson  LineStrings for walk/road/speedboat access edges
  access_style.qml      categorized style for access mode
  README.md             provenance and layer notes
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROCESSED = ROOT / "data" / "processed" / "multimodal"
DEFAULT_OUT = DEFAULT_PROCESSED / "qgis"

ACCESS_COLORS = {
    "walk": "#1b9e77",
    "road": "#d95f02",
    "speedboat": "#7570b3",
    "ferry_transfer": "#e7298a",
}
ACCESS_LABELS = {
    "walk": "Walk",
    "road": "Road",
    "speedboat": "Speedboat",
    "ferry_transfer": "Ferry transfer",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> int:
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def point_feature(properties: dict, lon: float, lat: float) -> dict:
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
    }


def line_feature(properties: dict, coordinates: list[list[float]]) -> dict:
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": "LineString", "coordinates": coordinates},
    }


def collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def build_qml() -> str:
    categories = []
    symbols = []
    for index, mode in enumerate(sorted(ACCESS_COLORS)):
        categories.append(
            f'    <category value="{mode}" symbol="{index}" type="string" '
            f'label="{ACCESS_LABELS[mode]}"/>'
        )
        color = ACCESS_COLORS[mode]
        symbols.append(
            f"""    <symbol type="line" name="{index}" alpha="1" clip_to_extent="1" force_rhr="0">
      <layer class="SimpleLine" locked="0" enabled="1" pass="0">
        <prop k="line_color" v="{color}"/>
        <prop k="line_style" v="solid"/>
        <prop k="line_width" v="0.8"/>
        <prop k="line_width_unit" v="MM"/>
        <prop k="capstyle" v="square"/>
        <prop k="joinstyle" v="bevel"/>
      </layer>
    </symbol>"""
        )
    return "\n".join(
        [
            "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>",
            '<qgis version="3.34.0-Prizren" styleCategories="Symbology">',
            '  <renderer-v2 type="categorizedSymbol" attr="mode" symbollevels="0" '
            'forceraster="0" enableorderby="0" referencescale="-1">',
            "    <categories>",
            *categories,
            "    </categories>",
            "    <symbols>",
            *symbols,
            "    </symbols>",
            "  </renderer-v2>",
            "</qgis>",
            "",
        ]
    )


def export(processed_dir: Path, out_dir: Path) -> dict:
    network = load_json(processed_dir / "network.json")
    islands_geojson_path = processed_dir / "islands.geojson"
    if not islands_geojson_path.exists():
        raise FileNotFoundError(f"missing {islands_geojson_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(islands_geojson_path, out_dir / "islands.geojson")

    islands = {item["id"]: item for item in network["islands"]}
    island_coords = {
        island_id: [float(item["lon"]), float(item["lat"])]
        for island_id, item in islands.items()
    }
    stop_coords = {
        stop["id"]: [float(stop["lon"]), float(stop["lat"])] for stop in network["stops"]
    }
    airport_coords = {
        airport["iata"]: [float(airport["lon"]), float(airport["lat"])]
        for airport in network["airports"]
    }
    node_coords = {}
    node_coords.update({f"island:{key}": value for key, value in island_coords.items()})
    node_coords.update({f"stop:{key}": value for key, value in stop_coords.items()})
    node_coords.update({f"airport:{key}": value for key, value in airport_coords.items()})

    facility_features = []
    for facility in sorted(network["facilities"], key=lambda item: item["id"]):
        lon, lat = island_coords[facility["islandId"]]
        properties = {
            "id": facility["id"],
            "name": facility["name"],
            "islandId": facility["islandId"],
            "kind": facility["kind"],
            "categories": ";".join(facility["categories"]),
            "precision": facility["precision"],
            "reviewed": bool(facility.get("reviewed", False)),
            "source": facility.get("source", ""),
        }
        if facility.get("serviceCategories"):
            properties["serviceCategories"] = ";".join(facility["serviceCategories"])
            properties["serviceEvidenceCount"] = len(facility.get("serviceEvidence", []))
            properties["userAdded"] = bool(facility.get("userAdded", False))
        if facility.get("sourceDate"):
            properties["sourceDate"] = facility["sourceDate"]
        facility_features.append(point_feature(properties, lon, lat))

    ferry_features = []
    for service in sorted(network["services"], key=lambda item: item["id"]):
        if service.get("kind") != "timetabled":
            continue
        coordinates = [
            stop_coords[stop_time["stopId"]]
            for stop_time in service["stops"]
            if stop_time["stopId"] in stop_coords
        ]
        if len(coordinates) < 2:
            continue
        ferry_features.append(
            line_feature(
                {
                    "id": service["id"],
                    "routeId": service.get("routeId", ""),
                    "routeCode": service.get("routeCode", ""),
                    "operator": service.get("operator", ""),
                    "zone": service.get("zone", ""),
                    "stops": len(coordinates),
                    "confidence": service.get("confidence", ""),
                },
                coordinates,
            )
        )

    pairs = {}
    for service in network["services"]:
        if service.get("kind") != "frequency" or service.get("mode") != "air":
            continue
        key = tuple(sorted((service["fromAirport"], service["toAirport"])))
        pairs.setdefault(key, []).append(service)
    air_features = []
    for pair in sorted(pairs):
        services = pairs[pair]
        first = sorted(services, key=lambda item: item["id"])[0]
        coordinates = [airport_coords[pair[0]], airport_coords[pair[1]]]
        airlines = sorted({service.get("airline", "") for service in services if service.get("airline")})
        air_features.append(
            line_feature(
                {
                    "pair": f"{pair[0]}-{pair[1]}",
                    "fromAirport": pair[0],
                    "toAirport": pair[1],
                    "airlines": ";".join(airlines),
                    "blockMinutes": first.get("blockMinutes", 0),
                    "weeklyFrequency": max(
                        service.get("weeklyFrequency", 0) for service in services
                    ),
                    "directedServices": len(services),
                    "confidence": "estimated_frequency",
                },
                coordinates,
            )
        )

    access_features = []
    for edge in sorted(
        network["accessEdges"],
        key=lambda item: (item["from"], item["to"], item["mode"], item["basis"]),
    ):
        start = node_coords.get(edge["from"])
        end = node_coords.get(edge["to"])
        if start is None or end is None:
            continue
        properties = {
            "from": edge["from"],
            "to": edge["to"],
            "mode": edge["mode"],
            "minutes": edge["minutes"],
            "confidence": edge["confidence"],
            "basis": edge["basis"],
            "assumed": bool(edge.get("assumed", False)),
        }
        if edge.get("distanceKm") is not None:
            properties["distanceKm"] = edge["distanceKm"]
        access_features.append(line_feature(properties, [start, end]))

    files = {
        "islands.geojson": None,
        "facilities.geojson": write_json(out_dir / "facilities.geojson", collection(facility_features)),
        "ferry_routes.geojson": write_json(out_dir / "ferry_routes.geojson", collection(ferry_features)),
        "air_routes.geojson": write_json(out_dir / "air_routes.geojson", collection(air_features)),
        "access_edges.geojson": write_json(out_dir / "access_edges.geojson", collection(access_features)),
    }
    files["islands.geojson"] = (out_dir / "islands.geojson").stat().st_size
    (out_dir / "access_style.qml").write_text(build_qml(), encoding="utf-8")

    readme = f"""# Multimodal Maldives QGIS export

Generated from `data/processed/multimodal/network.json` and `islands.geojson`.
CRS: EPSG:4326 (WGS 84). Coordinates are island centroids for facilities and
island access, not building locations.

Layers:
- `islands.geojson` — {len(network["islands"])} node islands (inhabited + airport-only).
- `facilities.geojson` — {len(facility_features)} island-precision facilities
  ({sum(1 for item in network["facilities"] if item.get("serviceCategories"))} intervention layer).
- `ferry_routes.geojson` — {len(ferry_features)} recorded RTL trips.
- `air_routes.geojson` — {len(air_features)} operating domestic airport pairs
  (directed services are collapsed to one line per pair).
- `access_edges.geojson` — {len(access_features)} same-island, link-road and
  airport speedboat access edges.
- `access_style.qml` — categorized line style by `mode`.

Caveats: RTL records one reference day, not a full calendar. Domestic air
departures are estimated frequencies, not observed schedules. Seaplane and
resort water-aerodrome services are excluded. Facility categories are
island-level evidence, not confirmed clinical services.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    return {
        "out": str(out_dir),
        "files": files,
        "counts": {
            "facilities": len(facility_features),
            "ferryRoutes": len(ferry_features),
            "airPairs": len(air_features),
            "accessEdges": len(access_features),
        },
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    summary = export(args.processed_dir, args.out_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
