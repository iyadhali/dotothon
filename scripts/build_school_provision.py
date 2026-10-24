#!/usr/bin/env python3
"""
Extract per-island school provision and enrolment from the MoE "School Statistics 2024" PDF.

Source: https://education.gov.mv/storage/files/statistics/1782980847582-2024%20School%20Statistics.pdf
        (Ministry of Education, School Statistics 2024 — pages 22-37 hold the per-atoll tables)

Each atoll table has one row per island and, per grade (BN, N, LKG, UKG, GR1..GR12), the number
of male and female students enrolled. That makes it the authoritative answer to "does island X
actually teach grade 11-12, and to how many students?" — which is what the accessibility model
needs, and it is stronger than a scraped school list.

Extraction is positional: pdfplumber words are binned onto the x positions of the header M/F
pairs. Every island row is then validated — the sum of its grade cells must equal its printed
sub-total. Rows that fail are reported, not silently kept.

Output: data/derived/island_school_provision.csv
"""
from __future__ import annotations

import collections
import re
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "external" / "schoolstats2024.pdf"
OUT = ROOT / "data" / "derived" / "island_school_provision.csv"

GR = ["BN", "N", "LKG", "UKG"] + [f"GR{i}" for i in range(1, 13)]
TAIL = ["SUBT", "PCT"]
GRADES = GR


def lines_of(page):
    L = collections.defaultdict(list)
    for w in page.extract_words():
        L[round(w["top"], 0)].append(w)
    return {k: sorted(v, key=lambda w: w["x0"]) for k, v in L.items()}


def header_columns(row) -> tuple[list, list]:
    """Build x positions and (label, sex) metadata from a row of M/F header tokens."""
    pairs = [(row[i]["x0"], row[i + 1]["x0"]) for i in range(0, min(len(row), 36), 2)]
    labels = GR + TAIL
    xs, meta = [], []
    for lab, (xm, xf) in zip(labels, pairs):
        xs += [xm, xf]
        meta += [(lab, "M"), (lab, "F")]
    return xs, meta


def parse_page(page):
    """Bin *characters* onto the header columns.

    Word-level extraction merges adjacent numbers once enrolment passes 3 digits
    ("1,1201,1101,355"), which silently corrupts exactly the largest islands. Characters
    carry their own x position, so binning chars into column bands avoids that merge.
    """
    import bisect

    L = lines_of(page)
    tops = sorted(L)
    raw_heads = [t for t in tops if any(w["text"] in ("M", "F") for w in L[t])
                 and sum(1 for w in L[t] if w["text"] in ("M", "F")) >= 2]
    heads = []
    for t in raw_heads:                      # some pages split the M/F row over two lines
        if heads and t - heads[-1] <= 3:
            L[heads[-1]] = sorted(L[heads[-1]] + L[t], key=lambda w: w["x0"])
        elif sum(1 for w in L[t] if w["text"] in ("M", "F")) >= 30 or not heads:
            heads.append(t)
            continue
        else:
            heads.append(t)
    heads = [h for h in heads if sum(1 for w in L[h] if w["text"] in ("M", "F")) >= 30]
    sections = [t for t in tops if any(w["text"].startswith("Enrolment") for w in L[t])]
    chars = page.chars
    out = []
    for h in heads:
        body_end = next((t for t in tops if t > h and t in heads), max(tops) + 1)
        xs, meta = header_columns(L[h])
        bounds = [-1e9] + [(xs[i] + xs[i + 1]) / 2 for i in range(len(xs) - 1)] + [1e9]
        first_col_x = min(xs)
        atoll = ""
        for sec in sections:
            if sec < h:
                txt = " ".join(w["text"] for w in L[sec])
                m = re.search(r"Enrolment in (.+?) (?:Atoll )?Islands", txt)
                if m:
                    atoll = m.group(1).strip()
        for t in tops:
            if not (h < t < body_end):
                continue
            row = L[t]
            if not row:
                continue
            name = row[0]["text"]
            if not re.fullmatch(r"[A-Za-z'’\.\- ]{3,40}", name) or name == "Island":
                continue
            is_region = name == "Atoll" or "total" in name.lower()
            if name.lower().startswith(("pre", "sub", "enrolment", "student")):
                continue
            # characters on this row, right of the island-name column
            band = [c for c in chars if abs(c["top"] - t) <= 5 and c["x0"] >= first_col_x - 6]
            cell = {}
            for sex_i in range(2):
                pass
            for c in band:
                if not (c["text"].isdigit() or c["text"] == ","):
                    continue
                j = bisect.bisect_right(bounds, c["x0"]) - 1
                if 0 <= j < len(meta):
                    lab, sex = meta[j]
                    cell.setdefault(f"{lab}_{sex}", []).append((c["x0"], c["text"]))
            cell = {k: int("".join(t_ for _, t_ in sorted(v)).replace(",", "")) for k, v in cell.items()}
            if not cell:
                continue
            grade_sum = sum(v for k, v in cell.items() if k.split("_")[0] in GRADES)
            subtotal = cell.get("SUBT_M", 0) + cell.get("SUBT_F", 0)
            rec = dict(atoll=atoll, island=name, grade_sum=grade_sum, subtotal=subtotal,
                       check_ok=(grade_sum == subtotal), is_region_total=is_region)

            def g(a, b):
                return sum(cell.get(f"GR{i}_{s}", 0) for i in range(a, b + 1) for s in "MF")

            def anyg(a, b):
                return any(cell.get(f"GR{i}_{s}", 0) for i in range(a, b + 1) for s in "MF")

            rec.update(
                enrolled_total=subtotal,
                pre_primary=sum(cell.get(f"{k}_{s}", 0) for k in ("BN", "N", "LKG", "UKG") for s in "MF"),
                primary=g(1, 6), lower_secondary=g(7, 10), higher_secondary=g(11, 12),
                is_preschool=any(cell.get(f"LKG_{s}", 0) for s in "MF"),
                is_primary=anyg(1, 6), is_lower_secondary=anyg(7, 10), is_higher_secondary=anyg(11, 12),
                gr11=g(11, 11), gr12=g(12, 12),
            )
            out.append(rec)
    return out


def main() -> None:
    rows = []
    with pdfplumber.open(PDF) as pdf:
        for i in range(21, 37):  # pages 22-37
            rows += [dict(page=i + 1, **r) for r in parse_page(pdf.pages[i])]
    df = pd.DataFrame(rows)
    # keep only rows whose grade cells sum to their printed sub-total, with a plausible size
    reg = df[df.is_region_total].copy()
    df = df[~df.is_region_total]
    keep = df.check_ok & df.grade_sum.gt(0) & df.grade_sum.lt(45000)
    dropped = int((~keep).sum())
    df = df[keep].drop_duplicates(["atoll", "island"], keep="first").reset_index(drop=True)

    # Greater Malé (Malé, Hulhumalé, Villingili) is published only as a region total on p.37:
    # its per-island columns sit too close together for character binning. Use the region row,
    # which does state grade 11-12 enrolment, and label it as a region aggregate.
    male = reg[reg.enrolled_total == reg.enrolled_total.max()]
    if len(male):
        m = male.iloc[0]
        df = pd.concat([df, pd.DataFrame([dict(
            page=int(m.page), atoll="Greater Malé", island="Malé City (region total)",
            grade_sum=int(m.grade_sum), subtotal=int(m.subtotal), check_ok=True,
            enrolled_total=int(m.enrolled_total), pre_primary=int(m.pre_primary),
            primary=int(m.primary), lower_secondary=int(m.lower_secondary),
            higher_secondary=int(m.higher_secondary), is_preschool=True, is_primary=True,
            is_lower_secondary=True, is_higher_secondary=bool(m.higher_secondary > 0),
            gr11=int(m.gr11), gr12=int(m.gr12), is_region_total=True)])], ignore_index=True)
        print(f"added Greater Malé region row: {int(m.enrolled_total):,} students, "
              f"Gr11 {int(m.gr11)}, Gr12 {int(m.gr12)}")
    df.to_csv(OUT, index=False)
    print(f"dropped {dropped} rows (failed sum check / implausible / duplicate)")

    ok = int(df.check_ok.sum())
    print(f"island rows {len(df)} | internal sum check {ok}/{len(df)} pass")
    bad = df[~df.check_ok]
    if len(bad):
        print("  rows failing the sum check (kept, flagged):")
        print(bad[["atoll", "island", "grade_sum", "subtotal"]].to_string(index=False))
    print(f"\ntotal enrolment in table: {int(df.enrolled_total.sum()):,}")
    print(f"islands with any enrolment: {len(df)}")
    for col, lab in [("is_primary", "primary (Gr 1-6)"), ("is_lower_secondary", "lower secondary (Gr 7-10)"),
                     ("is_higher_secondary", "higher secondary (Gr 11-12)")]:
        sub = df[df[col]]
        print(f"  {lab:<28} {len(sub):>4} islands | {int(sub.label.sum()) if False else int(sub.enrolled_total.sum()):>7,} students")
    print(f"\nhigher-secondary providers ({int(df.is_higher_secondary.sum())}):")
    print(df[df.is_higher_secondary].sort_values("gr11", ascending=False)
          .head(20)[["atoll", "island", "gr11", "gr12", "enrolled_total"]].to_string(index=False))
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
