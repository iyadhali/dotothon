#!/usr/bin/env python3
"""
The travel-time graph, in one place.

Islands joined by road are contracted into a single node, because a causeway is not a sailing and
must not spend the two-sailing budget; each island keeps its road-time offset inside that node.
Everything downstream — school access, hospital access, any new service category — reads from the
same graph, so adding a service never means re-deriving the network.

    graph = build(edges, nodes)
    graph.hours_to(node_id, provider_ids)     # best time to reach any provider
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRANSFER_H = 1.0      # waiting for the next sailing
MAX_HOPS = 2          # sailings per journey

# Road/causeway links the boat data cannot see. Addu City is one land mass spread over six census
# islands; times are driving at 30 km/h over the link road (stated assumption, no road speeds in
# the supplied data). (atoll_a, island_a, atoll_b, island_b, hours)


@dataclass
class Graph:
    nodes: pd.DataFrame
    comp: dict[str, str]           # island -> contracted node id
    offset: dict[str, float]       # island -> road minutes/hours to its contracted node
    idx: dict[str, int]
    dist: np.ndarray
    hops: np.ndarray

    def hours_to(self, island: str, providers: set[str]) -> tuple[float, str | None]:
        """(hours, provider island) for the nearest provider, or (inf, None)."""
        if island in providers:
            return 0.0, island
        if island not in self.comp:
            return np.inf, None
        base = self.offset.get(island, 0.0)
        ci = self.idx[self.comp[island]]
        best, who = np.inf, None
        for p in providers:
            if p not in self.comp:
                continue
            if self.comp[p] == self.comp[island]:
                d = 0.0
            else:
                d = self.dist[ci, self.idx[self.comp[p]]]
            if np.isfinite(d) and base + d < best:
                best, who = base + d, p
        return best, who


def build(edges: pd.DataFrame, nodes: pd.DataFrame,
          transfer_h: float = TRANSFER_H, max_hops: int = MAX_HOPS) -> Graph:
    parent = {n: n for n in nodes.node_id}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    land_edges: list[tuple] = []          # no road links exist in the base data
    for a, b, _h in land_edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comp = {n: find(n) for n in nodes.node_id}

    land_adj: dict[str, list] = {}
    for a, b, h in land_edges:
        land_adj.setdefault(a, []).append((b, h))
        land_adj.setdefault(b, []).append((a, h))
    offset: dict[str, float] = {}
    for n in nodes.node_id:
        if comp[n] != n or n in offset:
            continue
        offset[n] = 0.0
        stack = [(n, 0.0)]
        while stack:
            u, du = stack.pop()
            for v, h in land_adj.get(u, []):
                if v not in offset or du + h < offset[v] - 1e-9:
                    offset[v] = du + h
                    stack.append((v, du + h))
    offset = {n: offset.get(n, 0.0) for n in nodes.node_id}

    reps = sorted({comp[n] for n in nodes.node_id})
    idx = {r: i for i, r in enumerate(reps)}
    n = len(reps)
    dist = np.full((n, n), np.inf)
    np.fill_diagonal(dist, 0.0)
    for a, b, h in zip(edges.from_id, edges.to_id, edges.med_hours):
        if a in comp and b in comp:
            i, j = idx[comp[a]], idx[comp[b]]
            if i != j:
                dist[i, j] = min(dist[i, j], h)

    hops = np.full((n, n), 99, dtype=np.int16)
    np.fill_diagonal(hops, 0)
    hops[np.isfinite(dist) & (dist > 0)] = 1
    for _ in range(max_hops):
        for k in range(n):
            alt = dist[:, k][:, None] + transfer_h + dist[k, :][None, :]
            better = alt < dist - 1e-9
            dist = np.where(better, alt, dist)
            hops = np.where(better, hops[:, k][:, None] + hops[k, :][None, :], hops)

    return Graph(nodes=nodes, comp=comp, offset=offset, idx=idx, dist=dist, hops=hops)
