#!/usr/bin/env python3
"""
The data behind the Build page: where a new facility would add the most coverage, and where a
new sea crossing would connect the most people.

Two questions, one model — the same travel-time graph the rest of the app serves:

  1. Placement. For every inhabited island, the travel time to it from every other inhabited
     island. Add a facility there and an island is covered if either its current provider or the
     new one is within two hours. That is enough for the page to rank candidates, and to re-rank
     them greedily after the user builds one — without the browser ever knowing the graph.

  2. Connectivity. A crossing that does not exist today, drawn between two inhabited islands that
     are not directly connected, no more than 60 km apart. Its time is the great-circle distance
     at 20 knots plus half an hour to connect — the same "if direct" assumption the findings note
     uses, so the two pages agree. For each candidate the script measures what changes when that
     single edge is added: travel time is re-derived exactly from the graph's all-pairs closure
     (the new crossing may sit anywhere in a chain, and each junction it creates costs the usual
     transfer hour), so every island's new time is exact, not estimated.

Both rankings are greedy and stated as such in the UI. They know the observed network and the
census, and nothing else: no construction cost, no land, no staffing, no demand model.

    python scripts/build_placement.py
    python scripts/build_placement.py --link-km 50 --link-keep 30

Writes data/derived/travel_time.csv and data/derived/link_candidates.csv.
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from graph_core import build as build_graph

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"
THRESHOLD_H = 2.0
DEFAULT_TYPES = ["hospital", "school_higher_secondary", "college", "health_centre"]
KNOTS = 20.0                    # assumed cruising speed of a new scheduled crossing
CONNECT_H = 0.5                 # getting to the jetty and away again, same as findings.md
KM_PER_H = KNOTS * 1.852
EARTH_KM = 6371.0088


def norm(s) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def haversine(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_KM * math.asin(math.sqrt(a))


def direct_matrix(edges: pd.DataFrame, comp: dict, idx: dict) -> np.ndarray:
    """One sailing, no transfer: the only other leg a two-sailing route may use."""
    n = len(idx)
    d1 = np.full((n, n), np.inf)
    np.fill_diagonal(d1, 0.0)
    for r in edges.itertuples():
        ca, cb = comp.get(r.from_id), comp.get(r.to_id)
        if ca is None or cb is None or ca == cb:
            continue
        i, j = idx[ca], idx[cb]
        if r.med_hours < d1[i, j]:
            d1[i, j] = d1[j, i] = float(r.med_hours)
    return d1


def hours_after_link(base: np.ndarray, w: float, dist: np.ndarray, isl_comp: np.ndarray,
                     offset: np.ndarray, ca: int, cb: int, p: int) -> np.ndarray:
    """Travel time to provider component `p` if one crossing a-b of `w` hours is added.

    `dist` is the graph's all-pairs closure, so a journey may use the new crossing anywhere in a
    chain: prefix to the near end, the crossing, then the far side's best remaining route. The two
    bracket terms are the transfer costs at the junctions -- a junction costs an hour only when a
    sailing continues on either side of it.
    """
    far = dist[cb, p]
    back = dist[ca, p]
    via_a = dist[isl_comp, ca] + w + far + (dist[isl_comp, ca] > 0) + (far > 0)
    via_b = dist[isl_comp, cb] + w + back + (dist[isl_comp, cb] > 0) + (back > 0)
    return np.minimum(base, offset + np.minimum(via_a, via_b))
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--link-km", type=float, default=60.0, help="longest new crossing to consider")
    ap.add_argument("--link-keep", type=int, default=25, help="rows kept per service type")
    ap.add_argument("--types", default=",".join(DEFAULT_TYPES),
                    help="service types to score (comma separated)")
    args = ap.parse_args()

    nodes = pd.read_csv(D / "sea_nodes.csv")
    edges = pd.read_csv(D / "sea_edges.csv")
    graph = build_graph(edges, nodes)

    acc = pd.read_csv(D / "island_access.csv")
    acc = acc.set_index("node_id")
    islands = list(acc.index)
    isl_comp = np.array([graph.idx[graph.comp[i]] for i in islands])
    offset = np.array([float(graph.offset.get(i, 0.0)) for i in islands])
    pop = acc.population.fillna(0).astype(int).to_numpy()
    kids = acc.child_0_17.fillna(0).astype(int).to_numpy()
    name = acc.island.to_dict()
    atoll = acc.atoll.to_dict()
    lat = acc.lat.astype(float).to_numpy()
    lon = acc.lon.astype(float).to_numpy()

    # ---- 1. travel time between inhabited islands ------------------------------------------
    dist = graph.dist
    src = graph.idx
    rows = []
    for i, ii in enumerate(islands):
        ci = isl_comp[i]
        for j, jj in enumerate(islands):
            cj = isl_comp[j]
            if i == j:
                h = 0.0
            elif ci == cj:
                h = float(offset[i])       # same road island-group: no sailing needed
            else:
                h = float(offset[i] + dist[ci, cj])
            if not math.isfinite(h):
                h = None
            rows.append((ii, jj, None if h is None else round(h, 3)))
    travel = pd.DataFrame(rows, columns=["from_id", "to_id", "hours"])
    travel.to_csv(D / "travel_time.csv", index=False)
    print(f"wrote {D/'travel_time.csv'} — {len(travel):,} rows, "
          f"{travel.hours.notna().sum():,} reachable")

    # the matrix must reproduce the access table the rest of the app shows
    services = pd.read_csv(D / "services_placed.csv")
    access = pd.read_csv(D / "service_access.csv")
    prov = {t: sorted(set(g.node_id.dropna())) for t, g in services.groupby("service_type")}
    types = [t.strip() for t in args.types.split(",") if t.strip() in prov]
    prov = {t: prov[t] for t in types}
    if not prov:
        raise SystemExit("no service types to score")
    bad = 0
    mat = travel.pivot(index="from_id", columns="to_id", values="hours").loc[islands, islands]
    mat = mat.astype(float)
    for stype, providers in prov.items():
        cols = [islands.index(p) for p in providers if p in acc.index]
        if not cols:
            continue
        best = mat.iloc[:, cols].min(axis=1)
        ref = access[access.service_type == stype].set_index("node_id").hours.reindex(islands)
        delta = (best - ref).abs()
        bad += int((delta > 0.011).sum()
                   + (best.isna() != ref.isna()).sum())
    print(f"travel matrix vs service_access.csv: {bad} mismatches")
    if bad:
        raise SystemExit("refusing to publish a matrix that disagrees with the access table")

    # ---- 2. new crossings ------------------------------------------------------------------
    exists = set()
    for r in edges.itertuples():
        exists.add((r.from_id, r.to_id))
        exists.add((r.to_id, r.from_id))
    direct = direct_matrix(edges, graph.comp, graph.idx)
    prov_comps = {t: sorted({graph.idx[graph.comp[p]] for p in ps if p in graph.comp})
                  for t, ps in prov.items()}

    current = {}
    for stype, pcs in prov_comps.items():
        cur = np.full(len(islands), np.inf)
        for p in pcs:
            cur = np.minimum(cur, offset + dist[isl_comp, p])
        current[stype] = cur
    covered_now = {t: np.isfinite(c) & (c <= THRESHOLD_H) for t, c in current.items()}

    candidates = []
    for i in range(len(islands)):
        for j in range(i + 1, len(islands)):
            if isl_comp[i] == isl_comp[j]:
                continue
            if (islands[i], islands[j]) in exists:
                continue
            km = haversine(lat[i], lon[i], lat[j], lon[j])
            if km > args.link_km:
                continue
            candidates.append((i, j, km, km / KM_PER_H + CONNECT_H))
    print(f"{len(candidates):,} unpublished island pairs within {args.link_km:.0f} km")

    per_type = {}
    for stype, pcs in prov_comps.items():
        cur = current[stype]
        already = covered_now[stype]
        scored = []
        for (i, j, km, w) in candidates:
            after = None
            for p in pcs:
                base = offset + dist[isl_comp, p]
                h = hours_after_link(base, w, dist, isl_comp, offset, isl_comp[i],
                                     isl_comp[j], p)
                after = h if after is None else np.minimum(after, h)
            # a crossing can only make things better; never let a numerical edge undo that
            after = np.minimum(after, cur)
            newly = np.isfinite(after) & (after <= THRESHOLD_H) & ~already
            if not newly.any():
                continue
            after_cov = np.isfinite(after) & (after <= THRESHOLD_H)
            both = np.isfinite(cur) & np.isfinite(after)
            saved = np.zeros_like(cur)
            saved[both] = np.maximum(0.0, cur[both] - after[both])
            scored.append({
                "service_type": stype,
                "a_id": islands[i], "a_island": name[islands[i]], "a_atoll": atoll[islands[i]],
                "b_id": islands[j], "b_island": name[islands[j]], "b_atoll": atoll[islands[j]],
                "km": round(km, 1),
                "hours_if_direct": round(w, 2),
                "newly_islands": int(newly.sum()),
                "newly_people": int(pop[newly].sum()),
                "newly_children": int(kids[newly].sum()),
                "newly_ids": "|".join(islands[k] for k in np.flatnonzero(newly)),
                "coverage_after": int(after_cov.sum()),
                "population_after": int(pop[after_cov].sum()),
                "islands_saved": int((saved >= 0.5).sum()),
                "people_saved": int(pop[saved >= 0.5].sum()),
                "person_hours_saved": int((pop * saved).sum()),
            })
        scored.sort(key=lambda r: (-r["newly_people"], -r["person_hours_saved"]))
        per_type[stype] = scored[: args.link_keep]

    # one crossing can help several services; say how many, without repeating the row
    helped = {}
    for stype, rows_ in per_type.items():
        for r in rows_:
            key = (r["a_id"], r["b_id"])
            helped[key] = helped.get(key, 0) + 1
    out = pd.DataFrame([{**r, "types_helped": helped[(r["a_id"], r["b_id"])], "rank": n + 1}
                        for stype, rows_ in per_type.items() for n, r in enumerate(rows_)])
    out = out[["service_type", "rank", "a_id", "a_island", "a_atoll", "b_id", "b_island",
               "b_atoll", "km", "hours_if_direct", "newly_islands", "newly_people",
               "newly_children", "newly_ids", "coverage_after", "population_after",
               "islands_saved", "people_saved", "person_hours_saved", "types_helped"]]
    out.to_csv(D / "link_candidates.csv", index=False)
    print(f"wrote {D/'link_candidates.csv'} — {len(out)} rows")
    for stype, g in out.groupby("service_type"):
        best = g.iloc[0]
        print(f"  {stype:26s} {best.a_island}–{best.b_island} {best.km:.1f} km "
              f"{best.hours_if_direct:.2f} h → +{best.newly_people:,} people / "
              f"+{best.newly_islands} islands")


if __name__ == "__main__":
    main()
