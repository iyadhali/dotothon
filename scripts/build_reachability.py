#!/usr/bin/env python3
"""
Answer the question the pitch asks: from island A, can a student reach a school that teaches
grade 11-12 (or a university campus) — and how long does it take?

Inputs
  data/derived/sea_edges.csv              observed crossings (build_sea_network.py)
  data/derived/sea_nodes.csv              island nodes + Census population
  data/derived/island_school_provision.csv per-island enrolment by grade (build_school_provision.py)
  data/external/island_spine.csv          Census 2022 population

Outputs
  data/derived/island_access.csv     one row per inhabited island
  data/derived/island_pairs.csv      travel time between every pair of inhabited islands

Model
  Edge = observed median crossing time. Transfer = 1.0 h waiting. Paths via Floyd-Warshall on a
  hop-budgeted graph, so a journey needing 3 or more sailings is reported as *not accessible*
  rather than silently given a huge number.

Known limitation, stated in the output
  Greater Malé (Malé, Hulhumalé, Villingili) is added as a full-service hub by hand: the MoE
  School Statistics 2024 table for that region has its cells merged in the PDF text layer, so
  the per-grade split could not be extracted. Malé has grade 1-12 schools and the main MNU
  campus, so the hub assumption is safe — but it is an assumption and is flagged as such.
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"
TRANSFER_H = 1.0
MAX_HOPS = 2
MALE_ID = "MLE"


def norm(s) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def resolve(spine: pd.DataFrame, atoll: str, island: str):
    cand = spine[spine.atoll_name == atoll]
    if cand.empty:
        return None
    e = cand[cand.k == norm(island)]
    if len(e):
        return e.iloc[0].island_pcode
    b = difflib.get_close_matches(norm(island), cand.k.tolist(), n=1, cutoff=0.75)
    return cand[cand.k == b[0]].iloc[0].island_pcode if b else None


def main() -> None:
    edges = pd.read_csv(D / "sea_edges.csv")
    nodes = pd.read_csv(D / "sea_nodes.csv")
    spine = pd.read_csv(ROOT / "data/external/island_spine.csv")
    prov = pd.read_csv(D / "island_school_provision.csv")
    spine["k"] = spine.island.map(norm)

    # ---------- service flags ----------
    prov["pcode"] = [MALE_ID if a == "Greater Malé" else resolve(spine, a, i)
                     for a, i in zip(prov.atoll, prov.island)]
    print(f"provision rows matched to islands: {prov.pcode.notna().sum()} / {len(prov)}")
    hs = set(prov.loc[prov.is_higher_secondary, "pcode"].dropna())
    ls = set(prov.loc[prov.is_lower_secondary, "pcode"].dropna())
    hs.add(MALE_ID); ls.add(MALE_ID)          # Greater Malé = full-service hub (flagged)
    # MNU campuses: Malé (main), Kulhudhuffushi (HDh), Thinadhoo (GDh), Hithadhoo (Seenu). The
    # "Gan" campus stands on the Addu land mass next to Hithadhoo, so Hithadhoo covers it.
    # Resolved WITH the atoll, never by name alone: Gan, Hithadhoo and Thinadhoo each exist in
    # two or more atolls, and a bare name match silently picked the Laamu ones.
    campus = {MALE_ID}
    for atoll, name in (("Haa Dhaalu", "Kulhudhuffushi"), ("Gaafu Dhaalu", "Thinadhoo"),
                        ("Seenu", "Hithadhoo")):
        pid = resolve(spine, atoll, name)
        if pid is None:
            print(f"  ! campus not resolved: {atoll} / {name}")
        else:
            campus.add(pid)
    print(f"islands with grade 11-12: {len(hs)} | with grade 7-10: {len(ls)} | with a campus: {len(campus)}")

    # ---------- travel-time graph (shared with every other service layer) ----------
    from graph_core import build as build_graph

    graph = build_graph(edges, nodes)
    comp, offset, idx = graph.comp, graph.offset, graph.idx
    d, hops = graph.dist, graph.hops
    print(f"road links 0 (none in the base data) | {len(nodes)} islands")

    # ---------- per-island access ----------
    inh = nodes[nodes.type == "inhabited"].copy()
    rows = []
    for _, isl in inh.iterrows():
        base = offset[isl.node_id]
        ci = idx[comp[isl.node_id]]

        def best(targets):
            if isl.node_id in targets:            # the service is on this island: 0 hours
                return 0.0
            v = []
            for t in targets:
                if t not in comp:
                    continue
                v.append(base + (0.0 if comp[t] == comp[isl.node_id] else d[ci, idx[comp[t]]]))
            v = [x for x in v if np.isfinite(x)]
            return min(v) if v else np.nan

        def within(targets, lim):
            out = 0
            for t in targets:
                h = best([t])
                if np.isfinite(h) and 0 < h <= lim:
                    out += 1
            return out

        nbrs = int(((edges.from_id == isl.node_id) | (edges.to_id == isl.node_id)).sum())
        rows.append(dict(
            node_id=isl.node_id, island=isl["name"], atoll=isl.atoll,
            population=isl.population, child_0_17=isl.child_0_17,
            lat=isl.lat, lon=isl.lon,
            has_own_higher_secondary=isl.node_id in hs,
            has_own_lower_secondary=isl.node_id in ls,
            sea_neighbours=nbrs,
            islands_reachable=int(np.isfinite(d[ci]).sum() - 1),
            hours_to_hs=best(hs), hours_to_lower_sec=best(ls), hours_to_campus=best(campus),
            hs_within_2h=within(hs, 2.0), hs_within_4h=within(hs, 4.0),
            campus_within_4h=within(campus, 4.0),
        ))
    acc = pd.DataFrame(rows)
    # Malé has no per-island Census row, so its child count is imputed at the national
    # share of children (73,754 / 448,819 = 16.4 % of residents).
    share = 73754 / 448819
    acc["child_0_17"] = acc.child_0_17.fillna(acc.population * share).round().astype(int)

    # ---------- island x island ----------
    ids = acc.node_id.tolist()
    pos = [idx[comp[x]] for x in ids]
    sub = d[np.ix_(pos, pos)].copy()
    hsub = hops[np.ix_(pos, pos)].copy()
    for a_i, x in enumerate(ids):            # islands inside one road component: road time
        for b_i, y in enumerate(ids):
            if x != y and comp[x] == comp[y]:
                sub[a_i, b_i] = offset[x] + offset[y]
                hsub[a_i, b_i] = 0
    pairs = pd.DataFrame({
        "from_id": np.repeat(ids, len(ids)), "to_id": np.tile(ids, len(ids)),
        "best_hours": sub.ravel(), "hops": hsub.ravel(),
    })
    pairs = pairs[(pairs.from_id != pairs.to_id) & np.isfinite(pairs.best_hours)]
    nm = acc.set_index("node_id")
    pairs["from_island"] = pairs.from_id.map(nm.island)
    pairs["to_island"] = pairs.to_id.map(nm.island)
    pairs["from_atoll"] = pairs.from_id.map(nm.atoll)

    # ---------- priority gaps: the decision output (Impact criterion) ----------
    # For every island that cannot reach grade 11-12 within 2 h, name the higher-secondary island
    # it would most sensibly be connected to, and price the single link that would fix it.
    # The scenario time is a distance estimate at 20 knots plus a 0.5 h connection — labelled a
    # scenario, never presented as an observation.
    lat = acc.set_index("node_id").lat.to_dict()
    lon = acc.set_index("node_id").lon.to_dict()
    name = acc.set_index("node_id").island.to_dict()
    hs_nodes = sorted(hs & set(acc.node_id))

    def haversine_km(a, b):
        import math
        la1, lo1, la2, lo2 = map(math.radians, (lat[a], lon[a], lat[b], lon[b]))
        h = (math.sin((la2 - la1) / 2) ** 2
             + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
        return 2 * 6371.0088 * math.asin(math.sqrt(h))

    SCENARIO_KNOTS = 20.0
    gaps = []
    for r in acc.itertuples():
        hours = r.hours_to_hs
        if pd.notna(hours) and hours <= 2.0:
            continue                       # already within the policy threshold
        best_node, best_km = None, None
        for h in hs_nodes:
            if h == r.node_id:
                continue
            try:
                km = haversine_km(r.node_id, h)
            except KeyError:
                continue
            if best_km is None or km < best_km:
                best_node, best_km = h, km
        scenario = None if best_km is None else round(best_km / (SCENARIO_KNOTS * 1.852) + 0.5, 2)
        gaps.append(dict(
            node_id=r.node_id, island=r.island, atoll=r.atoll,
            population=int(r.population), child_0_17=int(r.child_0_17),
            hours_now=None if pd.isna(hours) else round(float(hours), 2),
            nearest_hs_id=best_node, nearest_hs=name.get(best_node, ""),
            distance_km=None if best_km is None else round(best_km, 1),
            hours_if_direct=scenario,
            hours_saved=None if (scenario is None or pd.isna(hours)) else round(float(hours) - scenario, 2),
        ))
    gaps = pd.DataFrame(gaps).sort_values(["child_0_17"], ascending=False)
    gaps.to_csv(D / "priority_gaps.csv", index=False)

    acc.to_csv(D / "island_access.csv", index=False)
    pairs.to_csv(D / "island_pairs.csv", index=False)

    # ---------- report ----------
    no = acc.hours_to_hs.isna()
    print("\n" + "=" * 70)
    print(f"inhabited islands {len(acc)} | population {int(acc.population.sum()):,} "
          f"| children 0-17 {int(acc.child_0_17.sum()):,}")
    print(f"islands with their own grade 11-12: {int(acc.has_own_higher_secondary.sum())}")
    reg = prov[prov.is_region_total]
    isl = prov[~prov.is_region_total]
    print(f"provision table reconciles: Gr11+12 {int(prov.gr11.sum() + prov.gr12.sum()):,} "
          f"vs national 5,105 | all students {int(prov.enrolled_total.sum()):,} vs 98,845")
    print(f"islands with NO reachable grade 11-12 (<=2 sailings): {int(no.sum())} "
          f"| {int(acc[no].population.sum()):,} people | {int(acc[no].child_0_17.sum()):,} children")
    for lim in (2, 4, 8):
        m = ~no & (acc.hours_to_hs <= lim)
        print(f"  can reach grade 11-12 within {lim:>2} h: {int(m.sum()):>3} islands, "
              f"{int(acc[m].population.sum()):>7,} people")
    print(f"\npriority gaps (beyond 2 h): {len(gaps)} islands, "
          f"{int(gaps.population.sum()):,} people, {int(gaps.child_0_17.sum()):,} children")
    print(gaps.head(10)[["island", "atoll", "population", "child_0_17", "hours_now",
                          "nearest_hs", "distance_km", "hours_if_direct"]].to_string(index=False))
    print("\nworst-served (largest population with no reachable grade 11-12):")
    print(acc[no].nlargest(10, "population")[
        ["island", "atoll", "population", "child_0_17", "sea_neighbours"]].to_string(index=False))
    print(f"\nwrote island_access.csv ({len(acc)}) and island_pairs.csv ({len(pairs):,})")


if __name__ == "__main__":
    main()
