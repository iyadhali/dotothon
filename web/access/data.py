"""
Data access layer for the accessibility explorer.

Everything is loaded once from the CSVs produced by scripts/build_*.py and kept in memory:
187 islands and 5,789 observed sea edges are small enough that a database would be overhead,
not architecture. No models, no migrations — this app is a read-only view over the pipeline.
"""
from __future__ import annotations

import heapq
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"
SPINE = ROOT / "data" / "external" / "island_spine.csv"

TRANSFER_H = 1.0       # waiting for the next sailing
MAX_HOPS = 2           # a journey needing three sailings is reported as not accessible

# Addu City is one land mass across six census islands, joined by the Addu link road; the boat
# data cannot see roads, so those legs are added explicitly (30 km/h assumption). Names are
# resolved at load time — typing raw pcodes is how you end up "connecting" the wrong atoll,
# because Hithadhoo, Feydhoo, Meedhoo and Hulhudhoo all exist in more than one atoll.
LAND_LINKS = [
    ("Seenu", "Hithadhoo", "Seenu", "Maradhoo", 0.25),
    ("Seenu", "Maradhoo", "Seenu", "Maradhoofeydhoo", 0.10),
    ("Seenu", "Maradhoofeydhoo", "Seenu", "Feydhoo", 0.10),
    ("Seenu", "Feydhoo", "Seenu", "Hulhudhoo", 0.15),
    ("Seenu", "Hulhudhoo", "Seenu", "Meedhoo", 0.10),
]

CAMPUSES = [("Male", "Malé City"), ("Haa Dhaalu", "Kulhudhuffushi"),
            ("Gaafu Dhaalu", "Thinadhoo"), ("Seenu", "Hithadhoo")]  # Gan campus sits on Addu


@dataclass
class Edge:
    a: str
    b: str
    hours: float
    km: float | None = None
    knots: float | None = None
    trips: int | None = None
    kind: str = "sea"


def norm(s: str) -> str:
    return re.sub(r"[^a-z]", "", str(s).lower())


def band_of(hours, own: bool) -> str:
    """Colour band shared by the map and the table, so one legend explains both."""
    if hours is None or (isinstance(hours, float) and hours != hours):
        return "unknown"
    if own or hours == 0:
        return "own"
    if hours <= 2:
        return "under2"
    if hours <= 4:
        return "under4"
    if hours <= 8:
        return "under8"
    return "over8"


class Model:
    """The whole dataset, in memory: 1,134 island nodes, 5,789 sea edges, 5 road edges.

    Graph nodes are *all* islands, because a journey can transfer at an airport island or a
    resort jetty that nobody lives on. Only the 187 inhabited ones are offered in the UI.
    """

    def __init__(self) -> None:
        nodes = pd.read_csv(DERIVED / "sea_nodes.csv")
        acc = pd.read_csv(DERIVED / "island_access.csv")
        # keep the Census-derived child count (Malé's is imputed at the national share) under a
        # separate name, because sea_nodes.csv has no children for the hand-added Malé row
        acc = acc.rename(columns={"child_0_17": "kids_census"})
        acc = acc.drop(columns=[c for c in ("island", "atoll", "population", "lat", "lon")
                                if c in acc.columns])
        self.nodes = nodes.merge(acc, on="node_id", how="left")
        self.by_id = self.nodes.set_index("node_id", drop=False)
        self.inhabited = self.nodes[self.nodes.type == "inhabited"].copy()
        self.hs_ids = set(self.inhabited.loc[self.inhabited.has_own_higher_secondary.fillna(False),
                                             "node_id"])
        self.ls_ids = set(self.inhabited.loc[self.inhabited.has_own_lower_secondary.fillna(False),
                                             "node_id"])

        self.adj: dict[str, list[Edge]] = {}
        best: dict[tuple[str, str], Edge] = {}
        for r in pd.read_csv(DERIVED / "sea_edges.csv").itertuples():
            for a, b in ((r.from_id, r.to_id), (r.to_id, r.from_id)):
                if not self._known(a) or not self._known(b):
                    continue
                if (a, b) not in best or r.med_hours < best[(a, b)].hours:
                    best[(a, b)] = Edge(a, b, float(r.med_hours), float(r.med_km),
                                        float(r.med_knots), int(r.trips))
        for aa, an, ab, bn, h in LAND_LINKS:
            a, b = self._pid(aa, an), self._pid(ab, bn)
            if a and b:
                for x, y in ((a, b), (b, a)):
                    best[(x, y)] = Edge(x, y, h, None, None, None, "land")
        for (a, b), e in best.items():
            self.adj.setdefault(a, []).append(e)
        self.n_edges = len(best)

        self.nearest_hs = self._multi_source(self.hs_ids)
        campus_ids = {i for i in (self._pid(a, n) for a, n in CAMPUSES) if i}
        self.nearest_campus = self._multi_source(campus_ids)

        gaps_path = DERIVED / "priority_gaps.csv"
        self.gaps = [] if not gaps_path.exists() else [
            {k: (None if pd.isna(v) else v) for k, v in r._asdict().items()}
            for r in pd.read_csv(gaps_path).itertuples()
        ]

        self.atolls = sorted(self.inhabited.atoll.dropna().unique().tolist())
        self.picker = [{"node_id": r.node_id, "island": r.name, "atoll": r.atoll}
                       for r in self.inhabited.sort_values(["atoll", "name"]).itertuples()]

    # ---------- graph plumbing ----------
    def _known(self, i: str) -> bool:
        return i in self.by_id.index

    def _pid(self, atoll: str, name: str) -> str | None:
        """Resolve (atoll, island) to a node id — the atoll disambiguates the 37 duplicate names."""
        m = self.by_id[(self.by_id.atoll == atoll) & (self.by_id.name.map(norm) == norm(name))]
        return None if not len(m) else str(m.iloc[0].node_id)

    def _multi_source(self, sources: set[str]) -> dict[str, tuple[float, str]]:
        """Nearest provider of a service for every node: (hours, provider island id)."""
        dist: dict[str, tuple[float, str]] = {s: (0.0, s) for s in sources if s in self.by_id.index}
        pq = [(0.0, s, s) for s in dist]
        heapq.heapify(pq)
        while pq:
            d, node, prov = heapq.heappop(pq)
            if d > dist.get(node, (1e18, ""))[0]:
                continue
            for e in self.adj.get(node, []):
                nd = d + e.hours
                if nd < dist.get(e.b, (1e18, ""))[0] - 1e-9:
                    dist[e.b] = (nd, prov)
                    heapq.heappush(pq, (nd, e.b, prov))
        return dist

    def route(self, src: str, dst: str):
        """Best journey as (legs, total_hours).

        Two rules keep the model honest:
          * the hop budget counts *sailings*, not legs — an Addu causeway is one road with six
            villages on it, so road links must not eat the allowance;
          * the 1 h connection penalty applies only when the mode changes or a new sailing
            starts, never between two consecutive road legs.
        """
        if src == dst:
            return [], 0.0
        start = (0.0, src, 0, None)          # (cost, node, sailings used, last mode)
        pq = [start]
        seen = {(src, 0, None): 0.0}
        prev: dict[tuple, tuple[tuple, Edge]] = {}
        done = None
        while pq:
            cost, node, sails, mode = heapq.heappop(pq)
            if seen.get((node, sails, mode), 1e18) < cost - 1e-9:
                continue
            if node == dst:
                done = (node, sails, mode)
                break
            for e in self.adj.get(node, []):
                ns = sails + (1 if e.kind == "sea" else 0)
                if ns > MAX_HOPS:
                    continue
                connects = mode is not None and not (mode == "land" and e.kind == "land")
                nc = cost + e.hours + (TRANSFER_H if connects else 0.0)
                key = (e.b, ns, e.kind)
                if nc < seen.get(key, 1e18) - 1e-9:
                    seen[key] = nc
                    prev[key] = ((node, sails, mode), e)
                    heapq.heappush(pq, (nc, e.b, ns, e.kind))
        if done is None:
            return None, None
        legs = []
        cur = done
        while cur in prev:
            parent, e = prev[cur]
            legs.append(e)
            cur = parent
        legs.reverse()
        return legs, seen[done]

    # ---------- views helpers ----------
    def name_of(self, node_id: str) -> str:
        try:
            return str(self.by_id.loc[node_id, "name"])
        except KeyError:
            return node_id

    def card(self, node_id: str) -> dict | None:
        if node_id not in self.inhabited.node_id.values:
            return None
        r = self.by_id.loc[node_id]
        links = sorted(self.adj.get(node_id, []),
                       key=lambda e: (-1e9 if e.kind == "land" else -(e.trips or 0)))[:4]
        hs_h, hs_prov = self.nearest_hs.get(node_id, (None, None))
        ca_h, ca_prov = self.nearest_campus.get(node_id, (None, None))
        return {
            "id": node_id, "name": r["name"], "atoll": r.atoll,
            "population": int(r.population),
            "kids": int(r.kids_census if pd.notna(r.kids_census) else r.child_0_17 or 0),
            "own_hs": bool(r.has_own_higher_secondary),
            "own_ls": bool(r.has_own_lower_secondary),
            "reach": int(r.islands_reachable), "nbrs": int(r.sea_neighbours),
            "hs_hours": None if hs_h is None else round(hs_h, 2),
            "hs_place": None if hs_prov is None else self.name_of(hs_prov),
            "campus_hours": None if ca_h is None else round(ca_h, 2),
            "campus_place": None if ca_prov is None else self.name_of(ca_prov),
            "links": [{"to": self.name_of(e.b), "to_id": e.b, "hours": round(e.hours, 2),
                       "trips": e.trips, "kind": e.kind,
                       "knots": None if e.knots is None else round(e.knots, 1)} for e in links],
        }

    def ranked(self, atoll: str = "", band: str = "", limit: int = 400) -> list[dict]:
        df = self.inhabited.copy()
        df["hs_hours_n"] = df.hours_to_hs.fillna(99)
        if atoll:
            df = df[df.atoll == atoll]
        if band == "none":
            df = df[df.hours_to_hs.isna()]
        elif band == "over2":
            df = df[df.hs_hours_n > 2]
        elif band == "over4":
            df = df[df.hs_hours_n > 4]
        elif band == "own":
            df = df[df.has_own_higher_secondary.fillna(False)]
        df = df.sort_values(["hs_hours_n", "population"], ascending=[False, False])
        return [{"id": r.node_id, "name": r.name, "atoll": r.atoll,
                 "pop": int(r.population),
                 "kids": int(r.kids_census if pd.notna(r.kids_census) else (r.child_0_17 or 0)),
                 "hours": None if pd.isna(r.hours_to_hs) else round(float(r.hours_to_hs), 2),
                 "own": bool(r.has_own_higher_secondary),
                 "band": band_of(r.hours_to_hs, bool(r.has_own_higher_secondary))}
                for r in df.head(limit).itertuples()]

    def stats(self) -> dict:
        i = self.inhabited
        no = i.hours_to_hs.isna()
        return {
            "islands": len(i),
            "population": int(i.population.sum()),
            "kids": int(i.kids_census.fillna(0).sum()),
            "hs_islands": int(i.has_own_higher_secondary.fillna(False).sum()),
            "within2_islands": int((i.hours_to_hs <= 2).sum()),
            "within2_pop": int(i.loc[i.hours_to_hs <= 2, "population"].sum()),
            "beyond2_pop": int(i.loc[i.hours_to_hs > 2, "population"].sum()),
            "no_service": int(no.sum()),
            "no_service_pop": int(i.loc[no, "population"].sum()),
            "edges": self.n_edges,
        }


@lru_cache(maxsize=1)
def model() -> Model:
    return Model()
