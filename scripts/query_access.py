#!/usr/bin/env python3
"""
Query the accessibility model.

    python scripts/query_access.py --from Fuvahmulah
    python scripts/query_access.py --from "Baarah" --atoll "Haa Alifu"
    python scripts/query_access.py --from Malé --to Kulhudhuffushi

Answers the two questions in the pitch:
  * where is a given island's nearest grade 11-12 school / university campus, and how long
  * can a person get from island A to island B, and how long does the best route take
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def pick(df, name, atoll=None):
    k = norm(name)
    m = df[df.k == k]
    if atoll:
        m = m[m.atoll.map(norm) == norm(atoll)]
    if m.empty:
        m = df[df.k.str.startswith(k[:6])]
    return m.iloc[0] if len(m) else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--atoll")
    ap.add_argument("--to", dest="dst")
    a = ap.parse_args()

    acc = pd.read_csv(D / "island_access.csv")
    pairs = pd.read_csv(D / "island_pairs.csv")
    acc["k"] = acc.island.map(norm)

    src = pick(acc, a.src, a.atoll)
    if src is None:
        raise SystemExit(f"island not found: {a.src}")

    kids = "" if pd.isna(src.child_0_17) else f", children 0-17 {int(src.child_0_17):,}"
    print(f"{src.island} ({src.atoll}) — population {int(src.population):,}{kids}")
    print(f"  own schools: primary={src.has_own_higher_secondary or '-'} "
          f"lower-secondary={bool(src.has_own_lower_secondary)} "
          f"higher-secondary={bool(src.has_own_higher_secondary)}")

    def fmt(h):
        if pd.isna(h):
            return "no route found in the observed network"
        return f"{h:.2f} h ({int(h * 60)} min)"

    print(f"  nearest grade 11-12 school : {fmt(src.hours_to_hs)}")
    print(f"  nearest university campus  : {fmt(src.hours_to_campus)}")
    print(f"  islands reachable          : {int(src.islands_reachable)}")
    print(f"  grade 11-12 within 2 h     : {int(src.hs_within_2h)} islands")

    if a.dst:
        dst = pick(acc, a.dst)
        if dst is None:
            raise SystemExit(f"island not found: {a.dst}")
        r = pairs[(pairs.from_id == src.node_id) & (pairs.to_id == dst.node_id)]
        if r.empty:
            print(f"\n{src.island} -> {dst.island}: no route within 2 sailings")
        else:
            row = r.iloc[0]
            print(f"\n{src.island} -> {dst.island}: {fmt(row.best_hours)}, "
                  f"{int(row.hops)} sailing(s), atoll {dst.atoll}")


if __name__ == "__main__":
    main()
