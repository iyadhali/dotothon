#!/usr/bin/env python3
"""
Watch the four supplied datasets and re-run the pipeline automatically when anything changes.

    python scripts/watch_data.py            # poll every 10 s, run ingest on change
    python scripts/watch_data.py --every 5  # poll faster
    python scripts/watch_data.py --once     # single check, ingest if stale, exit (for cron/CI)

It watches the same groups that `scripts/ingest.py` fingerprints, so "what changed" and "what to
rebuild" cannot drift apart. Nothing is tracked in git and nothing is copied: a new file dropped
into `data/FollowMe_september_2025/` (or over any existing CSV) is picked up in place.

Output also goes to `data/derived/ingest.log` so an unattended run leaves a trail.
"""
from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "derived" / "ingest.log"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest import fingerprint, source_files            # noqa: E402


def snapshot() -> dict[str, str]:
    return {name: fingerprint(paths) for name, paths in source_files().items()}


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(line + "\n")


def ingest() -> bool:
    log("change detected — running ingest")
    t0 = time.time()
    proc = subprocess.run([sys.executable, "scripts/ingest.py"], cwd=ROOT)
    ok = proc.returncode == 0
    log(f"ingest {'finished' if ok else 'FAILED'} in {time.time() - t0:.0f}s")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=float, default=10.0, help="poll interval in seconds")
    ap.add_argument("--once", action="store_true", help="check once, ingest if needed, exit")
    args = ap.parse_args()

    seen = snapshot()
    log(f"watching {sum(1 for v in seen.values() if v)} source groups every {args.every:g}s")

    if args.once:
        ingest()
        return

    stop = False

    def handle(_sig, _frm):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGTERM, handle)

    while not stop:
        time.sleep(args.every)
        now = snapshot()
        changed = [k for k in now if now[k] != seen.get(k)]
        if not changed:
            continue
        log(f"changed: {', '.join(changed)}")
        time.sleep(2)                      # let a copy finish writing
        seen = snapshot()                  # re-read so we do not ingest a half-written file twice
        ingest()
        seen = snapshot()                  # fold in anything that landed during the ingest
    log("watcher stopped")


if __name__ == "__main__":
    main()
