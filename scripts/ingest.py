#!/usr/bin/env python3
"""
Ingest pipeline: fingerprint the four supplied datasets, rebuild only what changed, and write a
manifest that proves what the numbers were built from.

    python scripts/ingest.py                 # incremental: run only the stale stages
    python scripts/ingest.py --dry-run       # say what would run, touch nothing
    python scripts/ingest.py --force         # rebuild everything
    python scripts/ingest.py --only sea      # one stage

Staleness is decided by a **fingerprint** of each source group (path + size + mtime of every
file), not by content hashing: FollowMe alone is 1.8 GB, and re-reading it to decide whether to
re-read it would defeat the purpose. The fingerprint is recorded in `data/derived/.ingest.json`,
so the next run knows exactly which inputs produced which outputs.

New data is dropped in the same way it was delivered, or into `data/incoming/` when it is a new
dataset rather than a replacement: anything left there is registered in `source_file` and, if no
stage understands it yet, its records are kept in `raw_record`:

    data/incoming/<anything>.csv|xlsx|json   absorbed into SQLite, queryable immediately

New data is dropped in the same way it was delivered:
    data/FollowMe_<month>/   any new folder matching data/FollowMe* is picked up automatically
    data/MTCC.xlsx           overwrite
    data/MACL/*.csv          overwrite
    data/Avas_Ride/*.csv     overwrite
`scripts/watch_data.py` polls for that and calls this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = DATA / "derived"
STAMP = DERIVED / ".ingest.json"

# source group -> files that belong to it. Missing groups are simply skipped.
def source_files() -> dict[str, list[Path]]:
    followme_dirs = sorted(d for d in DATA.glob("FollowMe*") if d.is_dir())
    # newest drop wins: the folder name carries the month, and mtime breaks ties
    followme = []
    if followme_dirs:
        latest = max(followme_dirs, key=lambda d: (d.name, d.stat().st_mtime))
        followme = sorted(latest.glob("*.csv"))
    return {
        "followme": followme,
        "mtcc": [DATA / "MTCC.xlsx"],
        "macl": sorted((DATA / "MACL").glob("*.csv")),
        "avas": sorted((DATA / "Avas_Ride").glob("*.csv")),
        "census": sorted((DATA / "external").glob("census2022_*.xlsx")),
        "boundaries": sorted((DATA / "external").glob("mdv_admin*.geojson")),
        "moe": sorted((DATA / "external").glob("schoolstats*.pdf")),
        "moh": sorted((DATA / "external").glob("moh_health_facilities*")),
        "services": [DATA / "services.csv"],      # hand-edited, or added through the app
        # anything dropped here is absorbed into SQLite even if no stage understands it yet
        "incoming": sorted(p for p in (DATA / "incoming").rglob("*")
                           if p.is_file() and not p.name.startswith(".")),
    }


def fingerprint(paths: list[Path]) -> str:
    """Stable hash of (relative path, size, mtime) for a group of files."""
    h = hashlib.sha256()
    for p in sorted(paths):
        if not p.exists():
            continue
        st = p.stat()
        h.update(f"{p.relative_to(ROOT)}|{st.st_size}|{st.st_mtime_ns}".encode())
    return h.hexdigest()[:16] if paths else ""


def describe(paths: list[Path]) -> dict:
    files = [p for p in paths if p.exists()]
    return {
        "files": len(files),
        "bytes": sum(p.stat().st_size for p in files),
        "fingerprint": fingerprint(files),
        "latest_mtime": datetime.fromtimestamp(
            max((p.stat().st_mtime for p in files), default=0), tz=timezone.utc
        ).strftime("%Y-%m-%d %H:%M"),
    }


# ---------------------------------------------------------------------------------------------
# stages: name -> (python script, extra args, the source groups that invalidate it)
STAGES: list[tuple[str, list[str], tuple[str, ...]]] = [
    ("spine", ["scripts/build_island_spine.py"], ("census", "boundaries")),
    ("normalise", ["scripts/normalise_sources.py"], ("mtcc", "macl", "avas")),
    ("sea", ["scripts/build_sea_network.py"], ("followme",)),
    ("provision", ["scripts/build_school_provision.py"], ("moe",)),
    ("reachability", ["scripts/build_reachability.py"], ("spine", "sea", "provision")),
    # the register is the source of truth; seed it once, then rebuild access from whatever it holds
    ("services", ["scripts/seed_services.py", "--if-missing"], ("services", "moh")),
    ("service_access", ["scripts/build_service_access.py"], ("services", "moh", "sea")),
    ("simulator", ["scripts/build_simulator.py"], ("service_access", "sea", "services")),
    ("incoming", ["scripts/absorb_incoming.py"], ("incoming",)),
    ("database", ["scripts/build_database.py"], ("simulator", "service_access", "reachability", "incoming")),
    ("web", ["web/build_web_data.py"], ("service_access", "sea", "provision")),
    ("check", ["scripts/check_outputs.py"], ()),          # always last, always cheap
]

OUTPUTS = {
    "spine": ["island_spine.csv"],
    "normalise": ["macl_monthly.csv", "avas_daily.csv", "mtcc_ferry_monthly.csv"],
    "sea": ["sea_edges.csv", "sea_nodes.csv"],
    "provision": ["island_school_provision.csv"],
    "reachability": ["island_access.csv", "island_pairs.csv", "priority_gaps.csv"],
    "services": ["services_placed.csv"],
    "service_access": ["service_access.csv", "service_summary.csv"],
    "simulator": ["placement.csv"],
    "database": ["platform.sqlite"],
    "web": ["islands_points.json"],
}


def load_stamp() -> dict:
    if STAMP.exists():
        try:
            return json.loads(STAMP.read_text())
        except json.JSONDecodeError:
            pass
    return {"sources": {}, "stages": {}}


def save_stamp(stamp: dict) -> None:
    STAMP.write_text(json.dumps(stamp, indent=2, sort_keys=True))


OUTPUT_DIRS = [DERIVED, DATA / "external", ROOT / "web/access/static/access"]


def missing_outputs(stage_name: str) -> list[str]:
    """An output counts as present if it exists in any of the directories we write to."""
    return [o for o in OUTPUTS.get(stage_name, [])
            if not any((d / o).exists() for d in OUTPUT_DIRS)]


def plan(sources: dict, stamp: dict, force: bool) -> list[tuple[str, str]]:
    """Return [(stage, reason)] for everything that needs to run."""
    todo: list[tuple[str, str]] = []
    changed_sources = {name
                       for name, meta in sources.items()
                       if meta["fingerprint"] and meta["fingerprint"] != stamp["sources"].get(name)}
    produced: dict[str, str] = {}

    for name, script, deps in STAGES:
        if force:
            todo.append((name, "--force"))
            produced[name] = sources.get(name, {}).get("fingerprint", "forced")
            continue
        reasons = []
        for dep in deps:
            if dep in changed_sources:
                reasons.append(f"{dep} changed")
            elif dep in produced:
                reasons.append(f"{dep} rebuilt")
        missing = missing_outputs(name)
        if missing:
            reasons.append("missing " + ", ".join(missing))
        if deps and not reasons:
            continue
        if not deps:
            reasons.append("always")
        todo.append((name, ", ".join(dict.fromkeys(reasons))))
        produced[name] = reasons[0]
    return todo


def run(stage: str, script: list[str]) -> float:
    t0 = time.time()
    print(f"\n▶ {stage}: {' '.join(script)}", flush=True)
    proc = subprocess.run([sys.executable, *script], cwd=ROOT)
    if proc.returncode != 0:
        raise SystemExit(f"stage '{stage}' failed with exit code {proc.returncode}")
    return time.time() - t0


def write_manifest(sources: dict, ran: dict) -> None:
    rows = {
        "mtcc_bus_monthly.csv": (DERIVED / "mtcc_bus_monthly.csv"),
        "mtcc_bus_daily.csv": (DERIVED / "mtcc_bus_daily.csv"),
        "mtcc_ferry_monthly.csv": (DERIVED / "mtcc_ferry_monthly.csv"),
        "macl_monthly.csv": (DERIVED / "macl_monthly.csv"),
        "avas_daily.csv": (DERIVED / "avas_daily.csv"),
        "sea_edges.csv": (DERIVED / "sea_edges.csv"),
        "island_access.csv": (DERIVED / "island_access.csv"),
        "priority_gaps.csv": (DERIVED / "priority_gaps.csv"),
    }
    counts = {}
    for name, path in rows.items():
        if path.exists():
            with path.open("rb") as fh:
                counts[name] = sum(1 for _ in fh) - 1     # minus header
    manifest = {
        "generated_at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "sources": sources,
        "derived_rows": counts,
        "stages_run": ran,
    }
    (DERIVED / "source_manifest.json").write_text(json.dumps(manifest, indent=2))

    lines = ["# Source manifest", "",
             f"Generated {manifest['generated_at']} by `scripts/ingest.py`.", "",
             "| source | files | size | last touched | fingerprint |",
             "|---|---:|---:|---|---|"]
    for name, meta in sources.items():
        if not meta["files"]:
            continue
        mb = meta["bytes"] / 1e6
        size = f"{mb:,.0f} MB" if mb >= 1 else f"{meta['bytes'] / 1e3:,.0f} kB"
        lines.append(f"| {name} | {meta['files']} | {size} | {meta['latest_mtime']} | "
                     f"`{meta['fingerprint']}` |")
    lines += ["", "Derived tables:", "", "| table | rows |", "|---|---:|"]
    for name, n in counts.items():
        lines.append(f"| `{name}` | {n:,} |")
    (DERIVED / "source_manifest.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rebuild every stage")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    ap.add_argument("--only", action="append", default=[], help="run just these stages")
    args = ap.parse_args()

    DERIVED.mkdir(parents=True, exist_ok=True)
    stamp = load_stamp()
    files = source_files()
    sources = {name: describe(paths) for name, paths in files.items()}

    missing = [name for name, meta in sources.items() if not meta["files"]]
    todo = plan(sources, stamp, args.force)
    if args.only:
        todo = [t for t in todo if t[0] in args.only] or [(n, "--only") for n in args.only]

    print("sources")
    for name, meta in sources.items():
        flag = "missing" if not meta["files"] else (
            "new" if meta["fingerprint"] != stamp["sources"].get(name) else "unchanged")
        print(f"  {name:<11} {meta['files']:>3} files  {meta['bytes'] / 1e6:>8,.1f} MB  {flag}")

    if not todo:
        print("\nnothing to do — every output is newer than its inputs")
        if not args.dry_run:
            write_manifest(sources, {})
        return

    print("\nplan")
    for name, reason in todo:
        print(f"  {name:<13} because {reason}")
    if args.dry_run:
        return

    ran: dict[str, float] = {}
    for name, script, _deps in STAGES:
        if name not in [t[0] for t in todo]:
            continue
        ran[name] = round(run(name, script), 1)
        stamp["stages"][name] = sources.get(name, {}).get("fingerprint", "run")
    stamp["sources"] = {k: v["fingerprint"] for k, v in sources.items() if v["fingerprint"]}
    stamp["last_run"] = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    save_stamp(stamp)
    write_manifest(sources, ran)

    print(f"\n✓ ingest complete in {sum(ran.values()):.0f}s — stages: "
          + ", ".join(f"{k} {v:.0f}s" for k, v in ran.items()))
    print(f"  manifest: {DERIVED / 'source_manifest.md'}")


if __name__ == "__main__":
    main()
