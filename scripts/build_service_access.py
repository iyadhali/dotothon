#!/usr/bin/env python3
"""
Turn the services register into an answer to "which islands can reach this service?"

Reads
  data/services.csv                the register (seeded, then hand-edited or added in the app)
  data/derived/sea_edges.csv       observed crossings
  data/derived/sea_nodes.csv       island nodes
  data/external/island_spine.csv   Census population
  data/derived/island_school_provision.csv  (not required, kept for join consistency)

Writes
  data/derived/service_access.csv    one row per island × service category × service type:
                                     has it locally, hours to the nearest, which island provides it
  data/derived/service_summary.csv   national roll-up per service type, for the header and docs

A service belongs to an island, so accessibility is computed on the same travel-time graph the
education model uses — one network, any number of service categories.

    python scripts/build_service_access.py
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path

import pandas as pd

from graph_core import build as build_graph, LAND_LINKS

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"
SERVICES = ROOT / "data" / "services.csv"


def norm(s) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def land_edges_for(spine: pd.DataFrame) -> list[tuple]:
    out = []
    for aa, a, ab, b, h in LAND_LINKS:
        pa = spine[(spine.atoll_name == aa) & (spine.island.map(norm) == norm(a))]
        pb = spine[(spine.atoll_name == ab) & (spine.island.map(norm) == norm(b))]
        if len(pa) and len(pb):
            out.append((pa.iloc[0].island_pcode, pb.iloc[0].island_pcode, h))
    return out


def main() -> None:
    if not SERVICES.exists():
        raise SystemExit("no data/services.csv — run scripts/seed_services.py first")

    services = pd.read_csv(SERVICES)
    nodes = pd.read_csv(D / "sea_nodes.csv")
    spine = pd.read_csv(ROOT / "data/external/island_spine.csv")
    spine["k"] = spine.island.map(norm)

    # ---------- attach every service to a node ----------
    def to_node(r):
        if r.atoll == "Male (city)":
            return "MLE"
        cand = spine[(spine.atoll_name == r.atoll) & (spine.k == norm(r.island))]
        if len(cand):
            return cand.iloc[0].island_pcode
        near = difflib.get_close_matches(norm(r.island), spine.k.tolist(), n=1, cutoff=0.8)
        return spine[spine.k == near[0]].iloc[0].island_pcode if near else None

    services["node_id"] = services.apply(to_node, axis=1)
    missing = services[services.node_id.isna()]
    if len(missing):
        print(f"! {len(missing)} services could not be attached to an island:")
        print(missing[["name", "atoll", "island"]].head(10).to_string(index=False))
    placed = services.dropna(subset=["node_id"])
    placed.to_csv(D / "services_placed.csv", index=False)

    # ---------- graph ----------
    edges = pd.read_csv(D / "sea_edges.csv")
    graph = build_graph(edges, nodes, land_edges_for(spine))
    print(f"graph: {len(nodes)} islands -> {len(graph.idx)} places")

    inhabited = nodes[nodes.type == "inhabited"].copy()
    # demography comes from island_access.csv, which already carries Malé's city population and
    # its imputed children; the spine keys Malé as "MV", so using it directly would drop 211,908
    # residents from every national total.
    demo = pd.read_csv(D / "island_access.csv").set_index("node_id")
    population = demo.population.to_dict()
    kids = demo.child_0_17.to_dict()

    # ---------- access per island x service type ----------
    rows = []
    for (category, stype), group in placed.groupby(["category", "service_type"]):
        providers = set(group.node_id)
        names = group.groupby("node_id").name.first().to_dict()
        for isl in inhabited.itertuples():
            hours, who = graph.hours_to(isl.node_id, providers)
            rows.append(dict(
                node_id=isl.node_id, island=isl.name, atoll=isl.atoll,
                category=category, service_type=stype,
                n_providers=len(providers),
                has_local=isl.node_id in providers,
                hours=None if hours == float("inf") else round(float(hours), 2),
                provider_island=(nodes.set_index("node_id").name.get(who) if who else None),
                provider_name=(names.get(who) if who else None),
                population=int(population.get(isl.node_id, 0) or 0),
                child_0_17=int(kids.get(isl.node_id, 0) or 0),
            ))
    access = pd.DataFrame(rows)
    access.to_csv(D / "service_access.csv", index=False)

    # ---------- national roll-up ----------
    summary = (access.groupby(["category", "service_type"])
               .apply(lambda g: pd.Series({
                   "n_facilities": int(g.n_providers.iloc[0]),
                   "islands_with_local": int(g.has_local.sum()),
                   "islands_within_2h": int((g.hours.notna() & (g.hours <= 2)).sum()),
                   "islands_unreachable": int(g.hours.isna().sum()),
                   "population_within_2h": int(g.loc[g.hours.notna() & (g.hours <= 2), "population"].sum()),
                   "children_within_2h": int(g.loc[g.hours.notna() & (g.hours <= 2), "child_0_17"].sum()),
                   "median_hours": round(float(g.hours.median()), 2) if g.hours.notna().any() else None,
               }), include_groups=False)
               .reset_index())
    summary.to_csv(D / "service_summary.csv", index=False)

    print(f"\nservices attached to islands: {len(placed)} / {len(services)}")
    print(summary.to_string(index=False))
    print(f"\nwrote {D/'service_access.csv'} ({len(access):,} rows) and {D/'service_summary.csv'}")


if __name__ == "__main__":
    main()
