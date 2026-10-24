#!/usr/bin/env python3
"""
Reconcile the pipeline's artifacts into SQLite — the platform's system of record.

The database is upserted, not replaced: every table has a natural key, rows are inserted or
updated on that key, rows that no longer exist are pruned, and every table's counts are written
to `data_change`. Running this twice in a row changes nothing the second time.

    python scripts/build_database.py             # reconcile (idempotent)
    python scripts/build_database.py --rebuild   # throw the file away and start clean
    python scripts/build_database.py --inspect   # reconcile, then print a sample of each table
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

from graph_core import LAND_LINKS  # noqa: E402  (the same road links the travel model uses)


def norm(s) -> str:
    import re
    return re.sub(r"[^a-z]", "", str(s).lower())


def read(name: str) -> pd.DataFrame:
    path = D / name
    if not path.exists():
        print(f"! missing {path.name} — run the pipeline first")
        return pd.DataFrame()
    return pd.read_csv(path)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """SQLite cannot take NaN/NaT, and a float column turns None straight back into NaN.

    Casting to object first is what makes the None survive, which is also why the reconciler
    compares cleanly: string columns come back from SQLite as None, not as nan.
    """
    return df.astype(object).where(pd.notna(df), None)


def _keyset(con, table: str, keys: list[str]) -> set:
    try:
        return set(con.execute(f"select {','.join(keys)} from {table}"))
    except sqlite3.OperationalError:
        return set()


def upsert(con, table: str, df: pd.DataFrame, keys: list[str], note: str = "") -> tuple[int, int, int]:
    """Insert-or-update on the natural key, then delete rows the source no longer has.

    Returns (inserted, updated, deleted). Reconciles rather than appends, so the table always
    equals the artifact it was built from.
    """
    if df is None or df.empty:
        return (0, 0, 0)
    df = _clean(df[list(dict.fromkeys(keys + [c for c in df.columns if c not in keys]))])
    cols = list(df.columns)
    incoming = [tuple(r) for r in df[cols].itertuples(index=False, name=None)]
    live = _keyset(con, table, keys)

    key_idx = [cols.index(k) for k in keys]
    new_keys = {tuple(r[i] for i in key_idx) for r in incoming}
    inserted = len(new_keys - live)

    # count a row as updated only when its values actually differ, so a no-op build reports zero
    existing = {}
    if live:
        try:
            for row in con.execute(f"select {','.join(cols)} from {table}"):
                existing[tuple(row[i] for i in key_idx)] = tuple(row)
        except sqlite3.OperationalError:
            existing = {}
    updated = sum(1 for r in incoming
                  if (k := tuple(r[i] for i in key_idx)) in existing and existing[k] != r)

    sets = ",".join(f"{c}=excluded.{c}" for c in cols if c not in keys)
    action = f"do update set {sets}" if sets else "do nothing"
    sql = (f"insert into {table} ({','.join(cols)}) values ({','.join('?' * len(cols))}) "
           f"on conflict({','.join(keys)}) {action}")
    try:
        con.executemany(sql, incoming)
    except Exception as exc:
        raise SystemExit(f"failed to load {table} ({len(df)} rows): {exc}") from exc

    stale = live - new_keys
    if stale:
        if len(keys) == 1:
            con.executemany(f"delete from {table} where {keys[0]} = ?", [(k[0],) for k in stale])
        else:
            where = " and ".join(f"{k} = ?" for k in keys)
            con.executemany(f"delete from {table} where {where}", list(stale))

    inserted_total, updated_total, deleted_total = inserted, updated, len(stale)
    if inserted_total or updated_total or deleted_total:
        con.execute(
            "insert into data_change (changed_at, table_name, inserted, updated, deleted, note) "
            "values (?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), table, inserted_total,
             updated_total, deleted_total, note or None))
    return (inserted_total, updated_total, deleted_total)


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


def build_islands() -> pd.DataFrame:
    nodes = read("sea_nodes.csv")
    acc = read("island_access.csv")
    spine = pd.read_csv(ROOT / "data/external/island_spine.csv")
    spine["k"] = spine.island.map(norm)

    islands = nodes.copy()
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
    return islands[cols]


def build_land_edges() -> pd.DataFrame:
    spine = pd.read_csv(ROOT / "data/external/island_spine.csv")
    by_key = {(r.atoll_name, norm(r.island)): r.island_pcode for r in spine.itertuples()}
    rows = []
    for aa, a, ab, b, h in LAND_LINKS:
        pa, pb = by_key.get((aa, norm(a))), by_key.get((ab, norm(b)))
        if pa and pb:
            rows.append({"a": pa, "b": pb, "hours": h, "note": "causeway (model assumption)"})
    return pd.DataFrame(rows)


def build_dataset(con) -> pd.DataFrame:
    """Logical source rows from the manifest, plus a per-file row for everything on disk."""
    manifest_path = D / "source_manifest.json"
    if not manifest_path.exists():
        return pd.DataFrame()
    manifest = json.loads(manifest_path.read_text())
    return pd.DataFrame([{
        "id": k, "files": v.get("files", 0), "bytes": v.get("bytes", 0),
        "fingerprint": v.get("fingerprint"), "latest_mtime": v.get("latest_mtime"),
        "first_seen": v.get("first_seen"), "last_seen": v.get("last_seen"),
    } for k, v in manifest.get("sources", {}).items()])


KEYS = {
    "island": ["node_id"], "sea_edge": ["from_id", "to_id"], "land_edge": ["a", "b"],
    "service": ["service_id"], "service_access": ["node_id", "service_type"],
    "service_summary": ["category", "service_type"], "priority_gaps": ["node_id"],
    "placement": ["service_type", "k"],
    "air_edge": ["a", "b"], "dataset": ["id"], "meta": ["key"],
}


def migrate(con) -> None:
    """Give an older database file the keys this version upserts on.

    The schema is applied with IF NOT EXISTS, so an existing table is never altered in place; when
    a table's primary key does not match the natural key we drop it and let the schema recreate it
    empty. The reconciler fills it back in the same run, so nothing is lost.
    """
    fixed = []
    for table, keys in KEYS.items():
        info = con.execute(f"pragma table_info({table})").fetchall()
        if not info:
            continue                                    # not created yet: the schema will do it
        pk = [row[1] for row in sorted(info, key=lambda r: r[5]) if row[5]]
        if pk != keys:
            con.execute(f"drop table if exists {table}")
            con.executescript(SCHEMA.read_text())
            fixed.append(f"{table}({','.join(pk) or 'no key'} -> {','.join(keys)})")
    if fixed:
        print("migrated: " + "; ".join(fixed))


def main() -> None:
    if not SCHEMA.exists():
        raise SystemExit(f"no schema at {SCHEMA}")
    if "--rebuild" in sys.argv and OUT.exists():
        OUT.unlink()
        print(f"--rebuild: removed {OUT.relative_to(ROOT)}")

    con = sqlite3.connect(OUT)
    con.executescript(SCHEMA.read_text())        # idempotent: CREATE ... IF NOT EXISTS
    con.execute("PRAGMA foreign_keys = OFF")     # reconciliation order is not the FK order
    migrate(con)

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    changes: dict[str, tuple[int, int, int]] = {}

    # ---------------------------------------------------------------- the network -------------
    changes["island"] = upsert(con, "island", build_islands(), ["node_id"], "sea_nodes + island_access")
    changes["sea_edge"] = upsert(con, "sea_edge", read("sea_edges.csv"), ["from_id", "to_id"],
                                 "median observed crossing per island pair")
    changes["land_edge"] = upsert(con, "land_edge", build_land_edges(), ["a", "b"], "causeway model links")

    # ---------------------------------------------------------------- services ----------------
    services = read("services_placed.csv")
    if len(services):
        changes["service"] = upsert(con, "service", services[[
            "service_id", "category", "service_type", "name", "atoll", "island", "node_id",
            "lat", "lon", "source", "notes", "added_at"]], ["service_id"], "the facility register")

    changes["service_access"] = upsert(con, "service_access", read("service_access.csv"),
                                       ["node_id", "service_type"], "multi-source Dijkstra")
    changes["service_summary"] = upsert(con, "service_summary", read("service_summary.csv"),
                                        ["category", "service_type"], "national roll-up")

    gaps = read("priority_gaps.csv")
    if len(gaps):
        changes["priority_gaps"] = upsert(con, "priority_gaps", gaps[[
            "node_id", "island", "atoll", "population", "child_0_17", "hours_now",
            "nearest_hs_id", "nearest_hs", "distance_km", "hours_if_direct", "hours_saved"]],
            ["node_id"], "islands beyond two hours")

    placement = read("placement.csv")
    if len(placement):
        changes["placement"] = upsert(con, "placement", placement, ["service_type", "k"],
                                      "greedy placement ranking")

    # ---------------------------------------------------------------- provenance --------------
    dataset = build_dataset(con)
    if len(dataset):
        changes["dataset"] = upsert(con, "dataset", dataset, ["id"], "source manifest")

    meta_rows = pd.DataFrame([
        {"key": "built_at", "value": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        {"key": "islands", "value": str(int(con.execute("select count(*) from island").fetchone()[0]))},
        {"key": "services", "value": str(int(con.execute("select count(*) from service").fetchone()[0]))},
        {"key": "edges", "value": str(int(con.execute("select count(*) from sea_edge").fetchone()[0]))},
        {"key": "reconciled", "value": started},
    ])
    upsert(con, "meta", meta_rows, ["key"], "build stamp")

    stamp_path = D / ".ingest.json"
    if stamp_path.exists():
        try:
            record_run(con, json.loads(stamp_path.read_text()))
        except Exception as exc:                 # provenance is a nicety, never the build
            print(f"! could not record the ingest run: {exc}")

    con.commit()
    touched = {k: v for k, v in changes.items() if any(v)}
    counts = {t: con.execute(f"select count(*) from {t}").fetchone()[0]
              for t in ["island", "sea_edge", "land_edge", "service", "service_access",
                        "service_summary", "priority_gaps", "placement", "dataset", "meta",
                        "air_edge", "data_change"]}
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size/1e6:.2f} MB)")
    print("  " + "  ".join(f"{k}={v:,}" for k, v in counts.items()))
    if touched:
        for table, (i, u, d) in touched.items():
            print(f"  {table:16} +{i:<5} ~{u:<5} -{d:<5}")
    else:
        print("  nothing changed — the database already matched the artifacts")
    con.close()

    if "--inspect" in sys.argv:
        con = sqlite3.connect(OUT)
        for t in ["island", "service", "sea_edge", "air_edge", "data_change"]:
            print(f"\n{t}:")
            for row in con.execute(f"select * from {t} limit 3"):
                print("   ", row)
        con.close()


if __name__ == "__main__":
    main()
