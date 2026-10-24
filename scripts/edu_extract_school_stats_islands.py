"""Extract island-level enrolment-by-grade tables from MoE "School Statistics" PDFs.

The atoll pages ("Enrolment in <Atoll> Atoll Islands") list, per island, students by grade
(BN, N, LKG, UKG, GR1..GR12) and sex. Empty cells are blank in the PDF, so columns are
assigned by x-position against the M/F header row.

Outputs next to the source PDF:
  <stem>_island_enrolment_by_grade_wide.csv   one row per island
  <stem>_island_enrolment_by_grade_long.csv   island x grade x sex
  plus derived fields: highest_grade_offered, has_grade_11_12 (higher secondary available on island)

Usage: python -I scripts/edu_extract_school_stats_islands.py <pdf> <year_label>
"""
import csv
import re
import sys
from pathlib import Path

import pymupdf

GRADES = ["BN", "N", "LKG", "UKG"] + [f"GR{i}" for i in range(1, 13)]
NUM = re.compile(r"^[\d,]+(\.\d+)?$")


def rows_by_y(words, tol=3.0):
    rows = []
    for w in sorted(words, key=lambda w: (round(w[1], 1), w[0])):
        yc = (w[1] + w[3]) / 2
        for r in rows:
            if abs(r["y"] - yc) <= tol:
                r["w"].append(w)
                break
        else:
            rows.append({"y": yc, "w": [w]})
    for r in rows:
        r["w"].sort(key=lambda w: w[0])
    return sorted(rows, key=lambda r: r["y"])


def parse_block(rows, atoll, pno):
    hdr = None
    for r in rows:
        mf = [w for w in r["w"] if w[4] in ("M", "F")]
        if len(mf) >= 30:
            hdr = mf
            break
    if hdr is None:
        raise RuntimeError(f"no M/F header on page {pno} for {atoll}")
    centers = [((w[0] + w[2]) / 2, w[4]) for w in hdr]
    # expected: 16 grades x 2 + subtotal(2) + percentage(2) = 36
    labels = []
    for g in GRADES:
        labels += [f"{g}_M", f"{g}_F"]
    labels += ["subtotal_M", "subtotal_F", "pct_M", "pct_F"]
    if len(centers) != len(labels):
        raise RuntimeError(f"page {pno}: {len(centers)} M/F header cells, expected {len(labels)}")
    hdr_y = (hdr[0][1] + hdr[0][3]) / 2
    out = []
    for r in rows:
        if r["y"] <= hdr_y + 2:
            continue
        name_parts = [w[4] for w in r["w"] if not NUM.match(w[4].replace(" ", ""))]
        nums = [w for w in r["w"] if NUM.match(w[4])]
        if not nums:
            continue
        name = " ".join(name_parts).strip()
        if not name or name.lower() == "of" or name.lower().startswith(("student enrolment", "of ")):
            continue
        rec = {"atoll": atoll, "island": name, "page": pno}
        for w in nums:
            xc = (w[0] + w[2]) / 2
            j = min(range(len(centers)), key=lambda k: abs(centers[k][0] - xc))
            val = w[4].replace(",", "")
            if labels[j] in rec:  # collision -> keep both visible for QA
                rec[labels[j]] = str(rec[labels[j]]) + "|" + val
            else:
                rec[labels[j]] = val
        out.append(rec)
        if name.replace(" ", "").lower() == "atolltotal":
            break
    return out


def parse_page(page):
    """A page may hold 1+ atoll tables; split vertically at each title line."""
    words = page.get_text("words")
    rows = rows_by_y(words)
    titles = []
    for r in rows:
        line = " ".join(w[4] for w in r["w"])
        m = re.search(r"Enrolment in (.+?) Atoll Islands", line)
        if m:
            titles.append((r["y"], re.sub(r"\s+", " ", m.group(1)).strip()))
    if not titles:
        return []
    out = []
    for k, (y0, atoll) in enumerate(titles):
        y1 = titles[k + 1][0] if k + 1 < len(titles) else 1e9
        block = [r for r in rows if y0 <= r["y"] < y1]
        out += parse_block(block, atoll, page.number + 1)
    return out


def main():
    pdf = Path(sys.argv[1])
    year = sys.argv[2]
    doc = pymupdf.open(pdf)
    allrows = []
    for page in doc:
        allrows += parse_page(page)
    gcols = [f"{g}_{s}" for g in GRADES for s in ("M", "F")]
    problems = 0
    for r in allrows:
        tot = 0
        for c in gcols:
            v = r.get(c, "")
            if "|" in str(v):
                problems += 1
                print("COLLISION", r["atoll"], r["island"], c, v, file=sys.stderr)
                continue
            tot += int(v) if v else 0
            r[c] = int(v) if v else 0
        st = int(r.get("subtotal_M") or 0) + int(r.get("subtotal_F") or 0)
        r["total"] = tot
        r["check_ok"] = tot == st
        if tot != st:
            problems += 1
            print("SUMCHECK", r["atoll"], r["island"], tot, st, file=sys.stderr)
        offered = [g for g in GRADES if (r[f"{g}_M"] + r[f"{g}_F"]) > 0]
        hg = None
        for g in reversed(GRADES):
            if g in offered:
                hg = g
                break
        r["highest_grade_enrolled"] = hg
        r["grade_11_12_enrolment"] = sum(r[f"GR{i}_{s}"] for i in (11, 12) for s in "MF")
        r["grade_9_10_enrolment"] = sum(r[f"GR{i}_{s}"] for i in (9, 10) for s in "MF")
        r["has_higher_secondary"] = r["grade_11_12_enrolment"] > 0
        r["is_atoll_total"] = r["island"].replace(" ", "").lower() == "atolltotal"
        r["year"] = year
        r["source_pdf"] = pdf.name
    stem = pdf.stem.replace(" ", "_")
    wide = pdf.parent / f"{stem}_island_enrolment_by_grade_wide.csv"
    cols = (["year", "page", "atoll", "island", "is_atoll_total"] + gcols +
            ["subtotal_M", "subtotal_F", "total", "check_ok", "highest_grade_enrolled",
             "grade_9_10_enrolment", "grade_11_12_enrolment", "has_higher_secondary", "source_pdf"])
    with open(wide, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)
    long = pdf.parent / f"{stem}_island_enrolment_by_grade_long.csv"
    with open(long, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "atoll", "island", "grade", "sex", "students"])
        for r in allrows:
            if r["is_atoll_total"]:
                continue
            for g in GRADES:
                for s in "MF":
                    w.writerow([year, r["atoll"], r["island"], g, s, r[f"{g}_{s}"]])
    isl = [r for r in allrows if not r["is_atoll_total"]]
    print(f"{pdf.name}: {len(isl)} islands, {sum(r['total'] for r in isl)} students, "
          f"{sum(r['has_higher_secondary'] for r in isl)} with Gr11-12, problems={problems}")
    print("->", wide)


if __name__ == "__main__":
    main()
