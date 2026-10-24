#!/usr/bin/env python3
"""
Absorb whatever is dropped in `data/incoming/` into the SQLite system of record.

The pipeline knows nine sources. A new file must not be lost just because no stage understands it
yet, so this script registers every file it sees and keeps the records it can parse:

  * every file gets a row in `source_file` (sha256 over the bytes, size, row count, kind, stage);
  * a file whose name maps to a known source is copied to that source's location and tagged with
    the stage that consumes it, so the next ingest rebuilds that part of the model;
  * a file nobody consumes yet is parsed (csv/xlsx/json) and its records land in `raw_record` as
    JSON, which makes it queryable immediately.

    python scripts/absorb_incoming.py            # absorb, report, move nothing twice
    python scripts/absorb_incoming.py --dry-run  # report only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INCOMING = ROOT / "data" / "incoming"
# the landing zone is deliberately a *separate* database from the one the app serves:
# raw bytes never reach the serving path, only what a stage has processed does
DB = ROOT / "data" / "landing.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"
MAX_ROWS = 50_000          # a runaway file should not silently bloat the database

# filename fragment -> (kind, destination, stage that consumes it)
KNOWN = [
    ("services", "services", ROOT / "data" / "services.csv", "services"),
    ("mtcc", "mtcc", ROOT / "data" / "MTCC.xlsx", "normalise"),
    ("macl", "macl", ROOT / "data" / "MACL", "normalise"),
    ("avas", "avas", ROOT / "data" / "Avas_Ride", "normalise"),
    ("followme", "followme", None, "sea"),
    ("census", "census", ROOT / "data" / "external", "spine"),
    ("moh", "moh", ROOT / "data" / "external", "services"),
    ("moe", "moe", ROOT / "data" / "external", "provision"),
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(path: Path) -> tuple[str, str | None]:
    name = path.name.lower()
    for fragment, kind, _dest, stage in KNOWN:
        if fragment in name:
            return kind, stage
    return "raw", None


def parse(path: Path) -> pd.DataFrame | None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix in {".xlsx", ".xlsm"}:
            return pd.read_excel(path)
        if suffix == ".json":
            data = json.loads(path.read_text())
            return pd.json_normalize(data if isinstance(data, list) else [data])
    except Exception as exc:
        print(f"! could not parse {path.name}: {exc}")
    return None


def ensure_schema(con) -> None:
    con.executescript(SCHEMA.read_text())      # idempotent: CREATE ... IF NOT EXISTS


LANDING_SCHEMA = """
create table if not exists source_file (
    path text primary key, sha256 text not null, bytes integer, rows integer,
    kind text, stage text, first_seen text, last_seen text);
create table if not exists raw_record (
    source_file text not null, row_no integer not null, payload text,
    primary key (source_file, row_no));
create table if not exists intake_log (
    logged_at text, path text, action text, detail text);
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    INCOMING.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in INCOMING.rglob("*") if p.is_file() and not p.name.startswith("."))
    if not files:
        print("nothing in data/incoming/")
        return

    con = sqlite3.connect(DB)
    con.executescript(LANDING_SCHEMA)
    ensure_schema(con)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report = []

    for path in files:
        rel = str(path.relative_to(ROOT))
        digest = sha256_of(path)
        known = con.execute("select sha256, first_seen from source_file where path = ?", (rel,)).fetchone()
        if known and known[0] == digest:
            print(f"· {path.name}: unchanged since {known[1]}")
            continue

        kind, stage = classify(path)
        frame = parse(path)
        rows = None if frame is None else int(len(frame))
        report.append((path, rel, digest, kind, stage, rows))

        if args.dry_run:
            continue

        con.execute(
            "insert into source_file (path, sha256, bytes, rows, kind, stage, first_seen, last_seen) "
            "values (?,?,?,?,?,?,?,?) on conflict(path) do update set "
            "sha256=excluded.sha256, bytes=excluded.bytes, rows=excluded.rows, kind=excluded.kind, "
            "stage=excluded.stage, last_seen=excluded.last_seen",
            (rel, digest, path.stat().st_size, rows, kind, stage, known[1] if known else now, now))

        if kind == "raw" and frame is not None:
            con.execute("delete from raw_record where source_file = ?", (rel,))
            payloads = [
                (rel, i, json.dumps({str(k): (None if pd.isna(v) else v.item() if hasattr(v, "item") else v)
                                     for k, v in row.items()}, default=str))
                for i, row in enumerate(frame.head(MAX_ROWS).to_dict("records"))
            ]
            con.executemany("insert or replace into raw_record (source_file, row_no, payload) "
                            "values (?,?,?)", payloads)
        con.commit()

    if args.dry_run:
        print("dry run — nothing written")
    else:
        con.execute("insert into data_change (changed_at, table_name, inserted, updated, deleted, note) "
                    "values (?,?,?,?,?,?)",
                    (now, "source_file", len(report), 0, 0, "absorbed from data/incoming"))
        con.commit()

    for path, rel, _digest, kind, stage, rows in report:
        where = f"{rows:,} rows" if rows is not None else "unparsed"
        print(f"+ {path.name:32} kind={kind:9} stage={stage or '—':10} {where}")
    print(f"{len(report)} new file(s) registered in source_file")
    con.close()


if __name__ == "__main__":
    main()
