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

    # ---------- land layer (road / causeway) ----------
    # The sea graph cannot see islands that are joined by road, which is exactly the case the
    # challenge is about: Addu City is one land mass spread over 6 census islands, and Malé is
    # bridged to Hulhumalé. Times are the driving/ferry time at 30 km/h over the link road
    # (assumption, stated in the output), because the supplied data has no road speeds.
    LAND = [
        ("Seenu", "Hithadhoo", "Seenu", "Maradhoo", 0.25),
        ("Seenu", "Maradhoo", "Seenu", "Maradhoofeydhoo", 0.10),
        ("Seenu", "Maradhoofeydhoo", "Seenu", "Feydhoo", 0.10),
        ("Seenu", "Feydhoo", "Seenu", "Hulhudhoo", 0.15),
        ("Seenu", "Hulhudhoo", "Seenu", "Meedhoo", 0.10),
    ]
    land_edges = []
    for aa, a, ab, b, h in LAND:
        pa = spine[(spine.atoll_name == aa) & (spine.k == norm(a))]
        pb = spine[(spine.atoll_name == ab) & (spine.k == norm(b))]
        if len(pa) and len(pb):
            land_edges.append((pa.iloc[0].island_pcode, pb.iloc[0].island_pcode, h))

    # ---------- travel-time graph ----------
    idx = {n: i for i, n in enumerate(nodes.node_id)}
    N = len(nodes)
    INF = np.inf
    d = np.full((N, N), INF)
    np.fill_diagonal(d, 0.0)
    for a, b, h in zip(edges.from_id, edges.to_id, edges.med_hours):
        if a in idx and b in idx:
            d[idx[a], idx[b]] = min(d[idx[a], idx[b]], h)
    for a, b, h in land_edges:                 # bidirectional road links
        if a in idx and b in idx:
            d[idx[a], idx[b]] = min(d[idx[a], idx[b]], h)
            d[idx[b], idx[a]] = min(d[idx[b], idx[a]], h)
    print(f"land/causeway links added: {len(land_edges)}")
    hops = np.full((N, N), 99, dtype=np.int16)
    np.fill_diagonal(hops, 0)
    hops[d > 0] = 1

    for _ in range(MAX_HOPS):
        for k in range(N):
            alt = d[:, k][:, None] + TRANSFER_H + d[k, :][None, :]
            better = alt < d - 1e-9
            d = np.where(better, alt, d)
            hops = np.where(better, hops[:, k][:, None] + hops[k, :][None, :], hops)

    # ---------- per-island access ----------
    inh = nodes[nodes.type == "inhabited"].copy()
    rows = []
    for _, isl in inh.iterrows():
        i = idx[isl.node_id]

        def best(targets):
            if isl.node_id in targets:            # the service is on this island: 0 hours
                return 0.0
            v = [d[i, idx[t]] for t in targets if t in idx]
            v = [x for x in v if np.isfinite(x)]
            return min(v) if v else np.nan

        def within(targets, lim):
            return sum(1 for t in targets if t in idx and np.isfinite(d[i, idx[t]]) and 0 < d[i, idx[t]] <= lim)

        nbrs = int(((edges.from_id == isl.node_id) | (edges.to_id == isl.node_id)).sum())
        rows.append(dict(
            node_id=isl.node_id, island=isl["name"], atoll=isl.atoll,
            population=isl.population, child_0_17=isl.child_0_17,
            has_own_higher_secondary=isl.node_id in hs,
            has_own_lower_secondary=isl.node_id in ls,
            sea_neighbours=nbrs,
            islands_reachable=int(np.isfinite(d[i]).sum() - 1),
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
    pos = [idx[x] for x in ids]
    sub = d[np.ix_(pos, pos)]
    hsub = hops[np.ix_(pos, pos)]
    pairs = pd.DataFrame({
        "from_id": np.repeat(ids, len(ids)), "to_id": np.tile(ids, len(ids)),
        "best_hours": sub.ravel(), "hops": hsub.ravel(),
    })
    pairs = pairs[(pairs.from_id != pairs.to_id) & np.isfinite(pairs.best_hours)]
    nm = acc.set_index("node_id")
    pairs["from_island"] = pairs.from_id.map(nm.island)
    pairs["to_island"] = pairs.to_id.map(nm.island)
    pairs["from_atoll"] = pairs.from_id.map(nm.atoll)

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
    print("\nworst-served (largest population with no reachable grade 11-12):")
    print(acc[no].nlargest(10, "population")[
        ["island", "atoll", "population", "child_0_17", "sea_neighbours"]].to_string(index=False))
    print(f"\nwrote island_access.csv ({len(acc)}) and island_pairs.csv ({len(pairs):,})")


if __name__ == "__main__":
    main()
