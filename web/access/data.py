"""
Data access layer for the accessibility explorer.

The pipeline writes `data/platform.sqlite` (see `db/schema.sql` and `scripts/build_database.py`)
and this module reads it. The views the app queries are named after the pipeline stages —
`sea_nodes`, `sea_edges`, `island_access`, `services_placed` — so any number on screen can be
traced back to the stage that produced it. The graph is still loaded into memory once: 187
islands and 5,789 crossings are small, and a live query per route would be slower, not simpler.
"""
from __future__ import annotations

import heapq
import re
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"
DB = ROOT / "data" / "platform.sqlite"
SPINE = ROOT / "data" / "external" / "island_spine.csv"


def db_frame(sql: str, params: tuple = ()) -> pd.DataFrame:
    """One query against the platform database, read-only."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()

TRANSFER_H = 1.0       # waiting for the next sailing
MAX_HOPS = 2           # a journey needing three sailings is reported as not accessible

# Addu City is one land mass across six census islands, joined by the Addu link road; the boat
# data cannot see roads, so those legs are added explicitly (30 km/h assumption). Names are
# resolved at load time — typing raw pcodes is how you end up "connecting" the wrong atoll,
# because Hithadhoo, Feydhoo, Meedhoo and Hulhudhoo all exist in more than one atoll.

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
        nodes = db_frame("select * from sea_nodes")
        acc = db_frame("select * from island_access")
        # keep the Census-derived child count (Malé's is imputed at the national share) under a
        # separate name, because sea_nodes.csv has no children for the hand-added Malé row
        acc = acc.rename(columns={"child_0_17": "kids_census"})
        acc = acc.drop(columns=[c for c in ("island", "atoll", "population", "lat", "lon")
                                if c in acc.columns])
        self.nodes = nodes.merge(acc, on="node_id", how="left")
        self.by_id = self.nodes.set_index("node_id", drop=False)
        self.inhabited = self.nodes[self.nodes.type == "inhabited"].copy()
        # services register (education + health) and the per-island access table built from it
        self.services = db_frame("select * from services_placed")
        self.svc_access = db_frame("select * from service_access")
        self.service_summary = db_frame("select * from service_summary")
        self.hs_ids = set(self.inhabited.loc[self.inhabited.has_own_higher_secondary.fillna(False),
                                             "node_id"])
        self.ls_ids = set(self.inhabited.loc[self.inhabited.has_own_lower_secondary.fillna(False),
                                             "node_id"])

        self.adj: dict[str, list[Edge]] = {}
        best: dict[tuple[str, str], Edge] = {}
        for r in db_frame("select * from sea_edges").itertuples():
            for a, b in ((r.from_id, r.to_id), (r.to_id, r.from_id)):
                if not self._known(a) or not self._known(b):
                    continue
                if (a, b) not in best or r.med_hours < best[(a, b)].hours:
                    best[(a, b)] = Edge(a, b, float(r.med_hours), float(r.med_km),
                                        float(r.med_knots), int(r.trips))
        for (a, b), e in best.items():
            self.adj.setdefault(a, []).append(e)
        self.n_edges = len(best)

        self.nearest_hs = self._multi_source(self.hs_ids)
        campus_ids = {i for i in (self._pid(a, n) for a, n in CAMPUSES) if i}
        self.nearest_campus = self._multi_source(campus_ids)

        gaps_path = DERIVED / "priority_gaps.csv"
        self.gaps = [] if not gaps_path.exists() else [
            {k: (None if pd.isna(v) else v) for k, v in r._asdict().items()}
            for r in db_frame("select * from priority_gaps").itertuples()
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
                ns = sails + (1 if e.kind == "sea" else 0)   # air and road legs do not use the sailing budget
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
            "services": self.services_on(node_id),
            "access": self.service_access_for(node_id),
            "links": [{"to": self.name_of(e.b), "to_id": e.b, "hours": round(e.hours, 2),
                       "trips": e.trips, "kind": e.kind,
                       "knots": None if e.knots is None else round(e.knots, 1)} for e in links],
        }

    def services_on(self, node_id: str) -> list[dict]:
        rows = self.services[self.services.node_id == node_id]
        return [{"name": r.name, "category": r.category, "type": r.service_type,
                 "source": r.source} for r in rows.itertuples()]

    @property
    def provider_ids(self) -> dict:
        if not hasattr(self, "_provider_ids"):
            self._provider_ids = {(r.node_id, r.service_type): r.provider_node
                                  for r in self.svc_access.itertuples()
                                  if isinstance(r.provider_node, str)}
        return self._provider_ids

    def service_access_for(self, node_id: str) -> dict:
        """Hours to the nearest provider of each service type, plus who provides it."""
        rows = self.svc_access[self.svc_access.node_id == node_id]
        out = {}
        for r in rows.itertuples():
            out[r.service_type] = {
                "category": r.category,
                "local": bool(r.has_local),
                "hours": None if pd.isna(r.hours) else round(float(r.hours), 2),
                "place": r.provider_island if isinstance(r.provider_island, str) else None,
                "name": r.provider_name if isinstance(r.provider_name, str) else None,
                "provider_id": self.provider_ids.get((node_id, r.service_type)),
            }
        return out

    def service_types(self) -> list[dict]:
        """The categories and types actually present in the register, for the pickers."""
        out = []
        for (cat, t), g in self.svc_access.groupby(["category", "service_type"]):
            out.append({"category": cat, "type": t, "islands": int(g.has_local.sum()),
                        "n": int(g.n_providers.iloc[0])})
        return sorted(out, key=lambda d: (d["category"], -d["n"]))

    def band_population(self) -> list[dict]:
        """People and children in each travel-time band, for the stacked bar."""
        rows = db_frame("""
            select case
                     when hours_to_hs is null then 'unknown'
                     when hours_to_hs = 0 then 'own'
                     when hours_to_hs <= 2 then 'under2'
                     when hours_to_hs <= 4 then 'under4'
                     when hours_to_hs <= 8 then 'under8'
                     else 'over8' end as band,
                   sum(population) as people, sum(child_0_17) as kids
            from island_access group by band""")
        order = ["own", "under2", "under4", "under8", "over8", "unknown"]
        got = {r.band: (int(r.people or 0), int(r.kids or 0)) for r in rows.itertuples()}
        total = sum(v[0] for v in got.values()) or 1
        label = {"own": "on the island", "under2": "under 2 h", "under4": "2–4 h",
                 "under8": "4–8 h", "over8": "over 8 h", "unknown": "no route"}
        return [{"band": b, "label": label[b], "people": got.get(b, (0, 0))[0],
                 "kids": got.get(b, (0, 0))[1],
                 "share": round(100 * got.get(b, (0, 0))[0] / total, 1)}
                for b in order if got.get(b, (0, 0))[0]]

    def summary_rows(self) -> list[dict]:
        """Per service type: facilities, coverage and median travel time."""
        return db_frame("select * from service_summary order by category, service_type").to_dict("records")

    # ---------------------------------------------------------------- simulator ----------
    def placement(self, service_type: str) -> pd.DataFrame:
        """Greedy picks 1..k for one service type, best first."""
        return db_frame("select * from placement where service_type = ? order by k",
                        (service_type,))

    def placement_types(self) -> list[dict]:
        rows = db_frame("""
            select p.service_type, s.category, count(*) as picks
            from placement p join service_summary s on s.service_type = p.service_type
            group by p.service_type, s.category order by s.category, p.service_type""")
        return rows.to_dict("records")

    def access_now(self, service_type: str) -> dict:
        """Today's picture for one service type, for the before/after comparison."""
        row = db_frame("select * from service_summary where service_type = ?", (service_type,))
        if row.empty:
            return {}
        r = row.iloc[0]
        return {"facilities": int(r.n_facilities),
                "islands_local": int(r.islands_with_local),
                "islands_2h": int(r.islands_within_2h),
                "people_2h": int(r.population_within_2h),
                "children_2h": int(r.children_within_2h),
                "median_hours": None if pd.isna(r.median_hours) else float(r.median_hours)}

    def map_hours(self, service_type: str) -> dict:
        """{node_id: hours} for one service type, for the simulator map."""
        df = db_frame("select node_id, hours from service_access where service_type = ?",
                      (service_type,))
        return {r.node_id: (None if pd.isna(r.hours) else float(r.hours))
                for r in df.itertuples()}

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


def data_version() -> tuple:
    """Cheap fingerprint of the database: any rebuild replaces the file, so the next request
    picks up new data without restarting the server (no manual cache clear needed)."""
    if not DB.exists():
        return ("missing",)
    st = DB.stat()
    return (DB.name, st.st_mtime_ns, st.st_size)


@lru_cache(maxsize=2)
def _model_for(version: tuple) -> Model:
    return Model()


def model() -> Model:
    """Always the model for the current data on disk."""
    return _model_for(data_version())


# --- widgets ---------------------------------------------------------------------------------
# Every number below is a query over the same tables the pages use; nothing is hard-coded.

def coverage_by_atoll() -> list[dict]:
    """Islands and people per atoll, split by whether grade 11-12 is within two hours."""
    df = db_frame("""
        select atoll,
               count(*) as islands,
               sum(population) as population,
               sum(case when hours_to_hs is not null and hours_to_hs <= 2 then 1 else 0 end) as within2,
               sum(case when hours_to_hs is null or hours_to_hs > 2 then 1 else 0 end) as beyond
        from island_access group by atoll""")
    df["share"] = (df.within2 / df.islands * 100).round(0)
    return df.sort_values(["beyond", "population"], ascending=[False, False]).to_dict("records")


def service_gap_by_atoll(service_type: str = "hospital", limit: int = 6) -> list[dict]:
    """Which atolls hold the people who live more than two hours from this service type."""
    df = db_frame("""
        select atoll,
               sum(case when hours is null or hours > 2 then population else 0 end) as people_beyond,
               sum(case when hours is null or hours > 2 then child_0_17 else 0 end) as children_beyond
        from service_access where service_type = ? group by atoll
        having people_beyond > 0 order by people_beyond desc limit ?""", (service_type, limit))
    return df.to_dict("records")


def journey_split(hours: float, wait: float) -> dict:
    """Sailing time vs waiting time, for the journey card's little bar."""
    moving = max(0.0, hours - wait)
    return {"moving": round(moving, 2), "waiting": round(wait, 2),
            "moving_pct": round(100 * moving / hours) if hours else 0}
