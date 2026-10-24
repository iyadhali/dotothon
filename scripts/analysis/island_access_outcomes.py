#!/usr/bin/env python3
"""
Island accessibility -> demographic outcome analysis.

Joins the router's per-island best-of-day accessibility export
(`data/processed/multimodal/island_access_best.csv`, produced by
`web/scripts/export-accessibility.ts`) to census outcomes per island and reports
descriptive bands plus an OLS model.

Run from the repo root:

    python3 scripts/analysis/island_access_outcomes.py

Outputs:
    data/processed/multimodal/island_access_outcomes.csv   (one row per island)
    stdout: access-band tables and regression summaries

This is descriptive, not causal: accessibility is jointly determined with population
(the largest islands host the airports and ferry termini). The controls below are the
minimum needed to stop the comparison being a pure size story.
"""

from __future__ import annotations

import sys
from pathlib import Path

import difflib
import json
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DETAIL = ROOT / "data/processed/multimodal/island_access.csv"
BEST = ROOT / "data/processed/multimodal/island_access_best.csv"
MASTER = ROOT / "data/external/_derived/mdv_islands_master.csv"
EMP = ROOT / "data/external/mbs-census-2022/xlsx/2023-10_Island-Level-Indicator-Sheet-Emp.xlsx"
NETWORK = ROOT / "web/public/data/multimodal.json"
OUT = ROOT / "data/processed/multimodal/island_access_outcomes.csv"
OUT_SWING = ROOT / "data/processed/multimodal/island_access_departure_sensitivity.csv"
POPULATION_TOTAL = 447_420

CATEGORIES = [
    "health_hospital",
    "health_regional_tertiary",
    "education_grade_11_12",
    "service:emergency",
    "service:dialysis",
    "service:ct",
    "service:mri",
    "service:telemedicine",
]


def tidy_emp(path: Path) -> pd.DataFrame:
    """Island-Level-Indicator-Sheet-Emp: two-row block header, then one row per island."""
    raw = pd.read_excel(path, header=None)
    blocks: list[tuple[str | None, str]] = []
    current: str | None = None
    for col in range(raw.shape[1]):
        block = raw.iloc[3, col]
        sub = raw.iloc[4, col]
        if isinstance(block, str) and block.strip():
            current = block.strip()
        blocks.append((current, sub if isinstance(sub, str) else ""))

    cols = ["atoll", "island"] + [f"{b}__{s}" for b, s in blocks[2:]]
    body = raw.iloc[5:].copy()
    body.columns = cols
    body = body[body["island"].notna() & (body["island"] != "Administrative Islands")]
    return body


def normalize(value: object) -> str:
    return re.sub(r"[^a-z]", "", str(value).lower())


def match_emp_islands(emp: pd.DataFrame) -> pd.Series:
    """Map census island names to adm2 p-codes.

    Names differ by transliteration (Mundhoo/Mundoo), letter case in the atoll code
    (Adh/ADh) and one reviewed canonical override (Lamu Gamu is displayed as Gan).
    """
    islands = pd.DataFrame(json.loads(NETWORK.read_text())["islands"])
    islands["key"] = islands["name"].map(normalize)
    islands["atoll_key"] = islands["atoll"].str.upper()
    override = {"L|gamu": "MV015013"}  # report.json canonicalNameOverrides

    resolved: list[str | None] = []
    for _, row in emp.iterrows():
        key = f"{str(row['atoll']).upper()}|{normalize(row['island'])}"
        if key in override:
            resolved.append(override[key])
            continue
        pool = islands[islands["atoll_key"] == str(row["atoll"]).upper()]
        exact = pool[pool["key"] == normalize(row["island"])]
        if len(exact) == 1:
            resolved.append(exact.iloc[0]["id"])
            continue
        best = max(
            ((difflib.SequenceMatcher(None, normalize(row["island"]), k).ratio(), i) for i, k in zip(pool["id"], pool["key"])),
            default=(0.0, None),
        )
        resolved.append(best[1] if best[0] >= 0.8 else None)
    return pd.Series(resolved, index=emp.index, name="adm2_pcode")


def build_frame() -> pd.DataFrame:
    best = pd.read_csv(BEST)
    best = best[best.estimated_air == 1]
    acc = best.pivot_table(index="origin_island_id", columns="category", values="best_elapsed_minutes")
    acc = acc.reindex(columns=CATEGORIES)
    acc.columns = [c.replace("service:", "svc_").replace("health_", "health_").replace(":", "_") for c in acc.columns]

    master = pd.read_csv(MASTER, low_memory=False)
    frame = master[master["status"] == "inhabited"].copy()
    for col in ["pop2014", "pop2022", "yb_dist_to_male_km", "area_sqkm", "yb_land_area_ha"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.set_index("adm2_pcode")

    frame["growth_1422_pct"] = np.where(
        frame["pop2014"] > 0, (frame["pop2022"] - frame["pop2014"]) / frame["pop2014"] * 100, np.nan
    )

    emp = tidy_emp(EMP)
    emp["neet_15_24"] = pd.to_numeric(emp["NEET rate (15-24 years)__Total"], errors="coerce")
    emp["unemployment"] = pd.to_numeric(emp["Unemployment rate (%)__Total"], errors="coerce")
    emp["lfp_women"] = pd.to_numeric(emp["Labour force participation rate (%)__Women"], errors="coerce")
    emp["adm2_pcode"] = match_emp_islands(emp)
    emp = emp.dropna(subset=["adm2_pcode"]).drop_duplicates("adm2_pcode").set_index("adm2_pcode")

    out = frame.join(acc, how="left").join(emp[["neet_15_24", "unemployment", "lfp_women"]], how="left")
    print(f"census employment indicators joined: {out['neet_15_24'].notna().sum()}/{len(out)} islands")
    return out


def band(series: pd.Series, same_day: float = 1440) -> pd.Series:
    return pd.Series(
        np.where(series.isna(), "never_reachable_in_day", np.where(series > same_day, "next_day_only", "same_day")),
        index=series.index,
    )


def describe(df: pd.DataFrame, label: str, column: str) -> None:
    df = df.assign(band=band(df[column]))
    table = df.groupby("band").agg(
        islands=("pop2022", "size"),
        pop2022=("pop2022", "sum"),
        growth_median=("growth_1422_pct", "median"),
        growth_mean=("growth_1422_pct", "mean"),
        neet_median=("neet_15_24", "median"),
        dist_male_median=("yb_dist_to_male_km", "median"),
    )
    table["pop_share_pct"] = table["pop2022"] / df["pop2022"].sum() * 100
    print(f"\n=== {label} ===")
    print(table.round(2).to_string())


def ols(df: pd.DataFrame, y: str, terms: list[str]) -> None:
    """Tiny OLS with HC0 standard errors, prints coefficient table."""
    data = df[[y] + terms].replace([np.inf, -np.inf], np.nan).dropna()
    yv = data[y].to_numpy(float)
    X = np.column_stack([np.ones(len(data))] + [data[t].to_numpy(float) for t in terms])
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    resid = yv - X @ beta
    n, k = X.shape
    cov = np.linalg.pinv(X.T @ X) * (resid @ resid) / (n - k)
    se = np.sqrt(np.diag(cov))
    r2 = 1 - (resid @ resid) / ((yv - yv.mean()) @ (yv - yv.mean()))
    print(f"\n--- OLS: {y} (n={n}, R2={r2:.3f}) ---")
    for name, b, s in zip(["const"] + terms, beta, se):
        print(f"  {name:34s} {b:12.4f}  se {s:9.4f}  t {b / s if s else float('nan'):6.2f}")


def departure_sensitivity() -> None:
    """How much of "access" is really a property of the clock, not the network."""
    detail = pd.read_csv(DETAIL, low_memory=False)
    detail = detail[detail["estimated_air"] == 1]
    rows = []
    for category, group in detail.groupby("category"):
        by_hour = (
            group[group["status"] == "reachable"].groupby("departure_minute")["population"].sum() / POPULATION_TOTAL * 100
        )
        if by_hour.empty:
            continue
        rows.append(
            {
                "category": category,
                "earliest_pct": round(by_hour.min(), 2),
                "latest_pct": round(by_hour.max(), 2),
                "swing_pp": round(by_hour.max() - by_hour.min(), 2),
                **{f"pop_{int(m // 60):02d}h": round(v, 2) for m, v in by_hour.items()},
            }
        )
    table = pd.DataFrame(rows).sort_values("swing_pp", ascending=False)
    print("\n=== share of population with a same-day journey, by departure hour (air on) ===")
    print(table[["category", "earliest_pct", "latest_pct", "swing_pp"]].to_string(index=False))
    table.to_csv(OUT_SWING, index=False)
    print(f"wrote {len(table)} rows -> {OUT_SWING}")


def distance_gradient(frame: pd.DataFrame) -> pd.DataFrame:
    """Median growth 2014-22 by distance-to-Male quintile: the demographic gradient."""
    data = frame.dropna(subset=["growth_1422_pct", "yb_dist_to_male_km"]).copy()
    data["quintile"] = pd.qcut(
        data["yb_dist_to_male_km"], 5, labels=["Q1 nearest", "Q2", "Q3", "Q4", "Q5 furthest"]
    )
    table = data.groupby("quintile", observed=True).agg(
        islands=("growth_1422_pct", "size"),
        pop2022=("pop2022", "sum"),
        growth_median=("growth_1422_pct", "median"),
        dist_median=("yb_dist_to_male_km", "median"),
    )
    print("\n=== median growth 2014-22 by distance-to-Male quintile ===")
    print(table.round(2).to_string())
    return table


def coverage_gap(frame: pd.DataFrame, km: float = 100.0) -> pd.DataFrame:
    """Islands close to Male with no modelled hospital journey: a data gap, not isolation."""
    gap = frame["health_hospital"].isna() & (frame["yb_dist_to_male_km"] < km)
    print(f"\n=== modelled coverage gap (<{km:.0f} km from Male, no hospital journey) ===")
    print(
        f"{int(gap.sum())} islands, {frame.loc[gap, 'pop2022'].sum():,.0f} residents, "
        f"median growth 2014-22 {frame.loc[gap, 'growth_1422_pct'].median():.1f}%"
    )
    for label, subset in [
        ("all islands", frame),
        ("excluding coverage gap", frame[~gap]),
    ]:
        bands = subset.assign(band=band(subset["health_hospital"]))
        table = bands.groupby("band").agg(
            islands=("pop2022", "size"),
            pop=("pop2022", "sum"),
            growth_median=("growth_1422_pct", "median"),
            dist_median=("yb_dist_to_male_km", "median"),
        )
        print(f"\n  -- {label} --")
        print(table.round(2).to_string())
    return pd.DataFrame({"coverage_gap": gap})


def main() -> int:
    frame = build_frame()
    acc_cols = [c for c in frame.columns if c.startswith(("health_", "education_", "svc_"))]
    print(f"islands: {len(frame)} | population: {frame['pop2022'].sum():,.0f}")
    print(f"access columns: {acc_cols}")
    coverage = frame[acc_cols].notna().sum()
    print("\nislands reachable at all (best of day):")
    print(coverage.to_string())

    for label, column in [
        ("Hospital (tier 1-3)", "health_hospital"),
        ("Regional/tertiary hospital", "health_regional_tertiary"),
        ("School offering grade 11-12", "education_grade_11_12"),
        ("Emergency care", "svc_emergency"),
        ("MRI", "svc_mri"),
    ]:
        describe(frame, label, column)

    frame["log_pop2014"] = np.log(frame["pop2014"].clip(lower=1))
    frame["log_dist"] = np.log(frame["yb_dist_to_male_km"].clip(lower=0.1))
    # "no same-day journey" covers both never-reachable and next-day-only.
    frame["no_sameday_hosp"] = (band(frame["health_hospital"]) != "same_day").astype(float)
    frame["no_sameday_g1112"] = (band(frame["education_grade_11_12"]) != "same_day").astype(float)
    frame["atoll_capital"] = (
        frame["is_atoll_capital"].astype(str).str.strip().str.lower().isin(["true", "1", "yes", "y", "t"])
    ).astype(float)

    # The coverage gap must be excluded from the regressions: there, "no journey" measures a
    # missing timetable rather than isolation, so the dummy would load on "is a Kaafu guesthouse
    # island" instead of on access. See coverage_gap() and research/13 §2.3.
    gap = frame["health_hospital"].isna() & (frame["yb_dist_to_male_km"] < 100.0)
    est = frame[~gap]
    print(f"\nregression sample excludes {int(gap.sum())} coverage-gap islands -> n base {len(est)}")

    ols(est, "growth_1422_pct", ["log_pop2014", "log_dist", "no_sameday_hosp", "atoll_capital"])
    ols(est, "neet_15_24", ["log_pop2014", "log_dist", "no_sameday_hosp", "no_sameday_g1112"])
    ols(est, "unemployment", ["log_pop2014", "log_dist", "no_sameday_hosp", "no_sameday_g1112"])

    distance_gradient(frame)
    coverage_gap(frame)
    departure_sensitivity()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=True)
    print(f"\nwrote {len(frame)} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
