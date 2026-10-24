#!/usr/bin/env python3
"""
Where should the next facility go, if the goal is to connect the most people?

This is a placement simulator, not a prediction: it answers one question on the network we
actually observe.

    If we added a <service type> on island X, how many more residents — and how many more
    children — would find themselves within two hours of that service?

Method (deliberately simple and stated in the UI):
  1. take the current travel time from every inhabited island to the nearest provider of that type;
  2. for each candidate island, the time to the new facility is just the travel time to that island;
  3. the new time is the better of the two, and anyone who moves from "over 2 h" (or "no route")
     to "within 2 h" is newly covered;
  4. rank candidates by newly covered residents, then children;
  5. repeat greedily for the next facility, on the network that already has the previous pick.

It is a greedy ranking, not an optimum — and it only knows the transport network we can see:
it does not model construction cost, land availability, staffing, or demand beyond population.

    python scripts/build_simulator.py               # all service types, k = 1..3
    python scripts/build_simulator.py --types hospital,school_higher_secondary
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from graph_core import build as build_graph, LAND_LINKS

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"
THRESHOLD_H = 2.0
KS = (1, 2, 3)

DEFAULT_TYPES = [
    "hospital",
    "school_higher_secondary",
    "college",
    "health_centre",
]


def norm(s) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def land_edges_for(spine: pd.DataFrame) -> list[tuple]:
    out, by_key = [], {(r.atoll_name, r.k): r.island_pcode for r in spine.itertuples()}
    for aa, a, ab, b, h in LAND_LINKS:
        pa, pb = by_key.get((aa, norm(a))), by_key.get((ab, norm(b)))
        if pa and pb:
            out.append((pa, pb, h))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", default=",".join(DEFAULT_TYPES))
    args = ap.parse_args()
    types = [t.strip() for t in args.types.split(",") if t.strip()]

    nodes = pd.read_csv(D / "sea_nodes.csv")
    edges = pd.read_csv(D / "sea_edges.csv")
    spine = pd.read_csv(ROOT / "data/external/island_spine.csv")
    spine["k"] = spine.island.map(norm)
    graph = build_graph(edges, nodes, land_edges_for(spine))

    attended = nodes[nodes.type == "inhabited"].copy().reset_index(drop=True)
    pop = attended.set_index("node_id").population.fillna(0).astype(int).to_dict()
    kids = attended.set_index("node_id").child_0_17.fillna(0).astype(int).to_dict()

    # travel time between two islands, on the same graph the app uses
    def hours(a: str, b: str) -> float:
        if a not in graph.comp or b not in graph.comp:
            return np.inf
        ca, cb = graph.comp[a], graph.comp[b]
        if ca == cb:
            return float(graph.offset.get(a, 0.0))
        return float(graph.dist[graph.idx[ca], graph.idx[cb]] + graph.offset.get(a, 0.0))

    rows = []
    for stype in types:
        providers = set(
            pd.read_csv(D / "services_placed.csv").query("service_type == @stype").node_id.dropna())
        if not providers:
            print(f"! no providers for {stype}, skipping")
            continue

        # current best time per island
        current = {i: graph.hours_to(i, providers)[0] for i in attended.node_id}
        candidates = [i for i in attended.node_id if i not in providers]

        for k in KS:
            best = None
            for c in candidates:
                newly_pop = newly_kids = newly_isl = 0
                gain = 0.0
                for i in attended.node_id:
                    if i in providers:
                        continue
                    old = current[i]
                    new = min(old, hours(i, c))
                    if new <= THRESHOLD_H and not old <= THRESHOLD_H:
                        newly_pop += pop.get(i, 0)
                        newly_kids += kids.get(i, 0)
                        newly_isl += 1
                    if np.isfinite(old) and new < old:
                        gain += pop.get(i, 0) * (old - new)
                score = (newly_pop, newly_kids)
                if best is None or score > best["score"]:
                    best = {"c": c, "pop": newly_pop, "kids": newly_kids, "isl": newly_isl,
                            "gain": gain, "score": score}
            if best is None:
                break

            c = best["c"]
            after = {i: min(current[i], hours(i, c)) for i in attended.node_id}
            covered = int(sum(1 for i, h in after.items() if h <= THRESHOLD_H))
            covered_pop = int(sum(pop.get(i, 0) for i, h in after.items() if h <= THRESHOLD_H))
            row = attended.set_index("node_id").loc[c]
            rows.append({
                "service_type": stype,
                "k": k,
                "node_id": c,
                "island": row["name"],
                "atoll": row["atoll"],
                "newly_within_2h": best["pop"],
                "children_newly": best["kids"],
                "islands_newly": best["isl"],
                "pop_weighted_gain": round(best["gain"], 1),
                "median_gain": round(float(np.median(
                    [current[i] - after[i] for i in attended.node_id
                     if np.isfinite(current[i]) and after[i] < current[i]] or [0])), 2),
                "coverage_after": covered,
                "population_after": covered_pop,
            })
            providers.add(c)
            candidates = [i for i in candidates if i != c]
            current = after

    out = pd.DataFrame(rows)
    out.to_csv(D / "placement.csv", index=False)
    print(f"wrote {D/'placement.csv'} — {len(out)} rows\n")
    for stype, g in out.groupby("service_type"):
        first = g[g.k == 1].iloc[0]
        print(f"{stype:28s} k=1 {first.island} ({first.atoll}) "
              f"+{int(first.newly_within_2h):,} people, +{int(first.children_newly):,} children, "
              f"coverage {int(first.coverage_after)}/187")


if __name__ == "__main__":
    main()
