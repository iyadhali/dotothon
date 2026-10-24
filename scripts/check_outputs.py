#!/usr/bin/env python3
"""
Assert that the numbers published in the README, the slides and the app still hold.

Run before every submission (`make check`). Each line is a claim we make in public, so a failure
here means a number somewhere is stale — not that the assertion is wrong.

Exit code 1 on the first failure.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data" / "derived"
E = ROOT / "data" / "external"

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


def main() -> None:
    spine = pd.read_csv(E / "island_spine.csv")
    check("island spine has 187 rows", len(spine) == 187, f"{len(spine)}")
    check("island spine has no unmatched island",
          bool(spine.matched.fillna(False).all()), f"{int((~spine.matched.fillna(False)).sum())} unmatched")

    prov = pd.read_csv(D / "island_school_provision.csv")
    hs = int(prov.gr11.sum() + prov.gr12.sum())
    check("grade 11-12 enrolment equals the published national total",
          hs == 5105, f"{hs} vs 5,105")
    check("44 islands teach grade 11-12",
          int(prov.loc[~prov.is_region_total, "is_higher_secondary"].sum()) == 44,
          str(int(prov.loc[~prov.is_region_total, "is_higher_secondary"].sum())))

    edges = pd.read_csv(D / "sea_edges.csv")
    check("observed sea edges in a plausible band", 4000 <= len(edges) <= 8000, f"{len(edges)}")
    check("no crossing implies an impossible speed",
          bool(edges.med_knots.between(0.5, 55).all()), "0.5-55 kn")

    acc = pd.read_csv(D / "island_access.csv")
    check("187 inhabited islands scored", len(acc) == 187, f"{len(acc)}")
    w2 = int((acc.hours_to_hs <= 2).sum())
    check("159 islands within two hours", w2 == 159, f"{w2}")
    pop = int(acc.loc[acc.hours_to_hs <= 2, "population"].sum())
    check("427,538 residents within two hours", pop == 427538, f"{pop:,}")
    none = int(acc.hours_to_hs.isna().sum())
    check("2 islands with no observed route", none == 2, f"{none}")

    gaps = pd.read_csv(D / "priority_gaps.csv")
    check("28 priority-gap islands", len(gaps) == 28, f"{len(gaps)}")
    check("6,758 children in those islands", int(gaps.child_0_17.sum()) == 6758,
          f"{int(gaps.child_0_17.sum()):,}")
    check("every gap row names a school island", bool(gaps.nearest_hs.notna().all()),
          f"{int(gaps.nearest_hs.isna().sum())} missing")

    svc = pd.read_csv(D / "service_access.csv")
    reg = pd.read_csv(E.parent / "services.csv")
    check("services register is non-trivial", len(reg) >= 500, f"{len(reg)} services")
    check("every service is attached to an island",
          bool(pd.read_csv(D / "services_placed.csv").node_id.notna().all()), "")
    hosp = svc[svc.service_type == "hospital"]
    n2 = int((hosp.hours <= 2).sum())
    check("35 islands reach a hospital within two hours", n2 == 35, f"{n2}")
    hc = svc[svc.service_type == "health_centre"]
    check("186 islands reach a health centre within two hours",
          int((hc.hours <= 2).sum()) == 186, f"{int((hc.hours <= 2).sum())}")
    hp = int(hosp.loc[hosp.hours <= 2, "population"].sum())
    check("274,015 people reach a hospital within two hours", hp == 274015, f"{hp:,}")

    if failures:
        print(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
        sys.exit(1)
    print("\nall checks passed")


if __name__ == "__main__":
    main()
