#!/usr/bin/env python3
"""
Project the pipeline's CSV artifacts into SQLite — the platform's queryable system of record.

Every table is dropped and rebuilt, so the database is never edited by hand: it is a projection
of data/derived/*.csv plus data/services.csv. The web app reads it; the pipeline owns it.

    python scripts/build_database.py              # rebuild data/platform.sqlite
    python scripts/build_database.py --inspect    # rebuild, then print row counts and size
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"
OUT = ROOT / "data" / "platform.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

from graph_core import LAND_LINKS  # noqa: E402  (same road links the travel model uses)


def norm(s) -> str:
    import re
    return re.sub(r"[^a-z]", "", str(s).lower())


def put(df: pd.DataFrame, table: str, con) -> None:
    """Insert one artifact, naming the table if SQLite refuses it."""
    try:
        df.to_sql(table, con, if_exists="append", index=False)
    except Exception as exc:
        raise SystemExit(f"failed to load {table} ({len(df)} rows): {exc}") from exc


def read(name: str) -> pd.DataFrame:
    path = D / name
    if not path.exists():
        print(f"! missing {path.name} — run the pipeline first")
        return pd.DataFrame()
    return pd.read_csv(path)


def record_run(con, stamp: dict) -> None:
    """Persist the last ingest run and its stages, so the app can show provenance from the DB."""
    last = stamp.get("last_run")
    finished = last if isinstance(last, str) else (last or {}).get("finished")
    con.execute("delete from ingest_stage")
    con.execute("delete from ingest_run")
    con.execute(
        "insert into ingest_run (run_id, started, finished, seconds, trigger, stages) values (1,?,?,?,?,?)",
        (finished, finished, None, "cli",
         ",".join(k for k, v in (stamp.get("stages") or {}).items() if v == "run")))
    for stage, value in (stamp.get("stages") or {}).items():
        status = "ok" if value == "run" else "skipped"
        con.execute("insert into ingest_stage (run_id, stage, status, seconds, detail) values (1,?,?,?,?)",
                    (stage, status, 0.0, None if status == "ok" else f"fingerprint {value}"))


def main() -> None:
    if not SCHEMA.exists():
        raise SystemExit(f"no schema at {SCHEMA}")
    if OUT.exists():
        OUT.unlink()

    con = sqlite3.connect(OUT)
    con.executescript(SCHEMA.read_text())

    # ---------------------------------------------------------------- the network -------------
    nodes = read("sea_nodes.csv")
    acc = read("island_access.csv")
    spine = pd.read_csv(ROOT / "data/external/island_spine.csv")
    spine["k"] = spine.island.map(norm)

    islands = nodes.rename(columns={"node_id": "node_id", "name": "name"}).copy()
    islands = islands.merge(
        acc[["node_id", "has_own_higher_secondary", "has_own_lower_secondary", "hours_to_hs",
             "hours_to_lower_sec", "hours_to_campus", "islands_reachable", "sea_neighbours"]],
        on="node_id", how="left")
    # island_access carries the filled child count (Malé's is imputed at the national share);
    # sea_nodes leaves it NULL, so prefer the filled series and fall back to the raw one
    filled_kids = acc.set_index("node_id").child_0_17.to_dict()
    islands["child_0_17"] = islands.node_id.map(filled_kids).fillna(islands.child_0_17)
    area = spine.set_index("island_pcode").area_km2.to_dict()
    islands["area_km2"] = islands.node_id.map(area)
    islands["has_higher_secondary"] = islands.has_own_higher_secondary.fillna(0).astype(int)
    islands["has_lower_secondary"] = islands.has_own_lower_secondary.fillna(0).astype(int)
    islands.loc[islands.type != "inhabited", ["has_higher_secondary", "has_lower_secondary"]] = 0
    cols = ["node_id", "name", "atoll", "type", "lat", "lon", "population", "child_0_17",
            "area_km2", "has_higher_secondary", "has_lower_secondary", "hours_to_hs",
            "hours_to_lower_sec", "hours_to_campus", "islands_reachable", "sea_neighbours"]
    put(islands[cols], "island", con)

    edges = read("sea_edges.csv")
    put(edges, "sea_edge", con)

    land = []
    by_key = {(r.atoll_name, r.k): r.island_pcode for r in spine.itertuples()}
    for aa, a, ab, b, h in LAND_LINKS:
        pa, pb = by_key.get((aa, norm(a))), by_key.get((ab, norm(b)))
        if pa and pb:
            land.append({"a": pa, "b": pb, "hours": h, "note": "causeway (model assumption)"})
    put(pd.DataFrame(land), "land_edge", con)

    # ---------------------------------------------------------------- services ----------------
    services = read("services_placed.csv")
    put(services[[
        "service_id", "category", "service_type", "name", "atoll", "island", "node_id",
        "lat", "lon", "source", "notes", "added_at"]], "service", con)

    put(read("service_access.csv"), "service_access", con)
    put(read("service_summary.csv"), "service_summary", con)

    gaps = read("priority_gaps.csv")
    if len(gaps):
        put(gaps[["node_id", "island", "atoll", "population", "child_0_17", "hours_now",
                  "nearest_hs_id", "nearest_hs", "distance_km", "hours_if_direct", "hours_saved"]],
            "priority_gaps", con)

    placement = read("placement.csv")
    if len(placement):
        put(placement, "placement", con)

    # ---------------------------------------------------------------- provenance --------------
    manifest_path = D / "source_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        rows = [{
            "id": k, "files": v.get("files", 0), "bytes": v.get("bytes", 0),
            "fingerprint": v.get("fingerprint"), "latest_mtime": v.get("latest_mtime"),
            "first_seen": v.get("first_seen"), "last_seen": v.get("last_seen"),
        } for k, v in manifest.get("sources", {}).items()]
        if rows:
            put(pd.DataFrame(rows), "dataset", con)

    built = datetime.now(timezone.utc).isoformat(timespec="seconds")
    pd.DataFrame([
        {"key": "built_at", "value": built},
        {"key": "islands", "value": str(len(islands))},
        {"key": "services", "value": str(len(services))},
        {"key": "edges", "value": str(len(edges))},
    ]).to_sql("meta", con, if_exists="append", index=False)
    stamp_path = D / ".ingest.json"
    if stamp_path.exists():
        try:
            record_run(con, json.loads(stamp_path.read_text()))
        except Exception as exc:                 # provenance is a nicety, never the build
            print(f"! could not record the ingest run: {exc}")
    con.commit()

    counts = {t: con.execute(f"select count(*) from {t}").fetchone()[0]
              for t in ["island", "sea_edge", "land_edge", "service", "service_access",
                        "service_summary", "priority_gaps", "placement", "dataset", "meta"]}
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size/1e6:.2f} MB)")
    print("  " + "  ".join(f"{k}={v:,}" for k, v in counts.items()))
    con.close()

    if "--inspect" in sys.argv:
        con = sqlite3.connect(OUT)
        for t in counts:
            print(f"\n{t}:")
            for row in con.execute(f"select * from {t} limit 3"):
                print("   ", row)
        con.close()


if __name__ == "__main__":
    main()
