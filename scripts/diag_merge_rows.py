"""Merge per-stream diagnostic-service rows into the final diagnostic_services.csv.

Inputs : data/external/health/services/diagnostics/sources/<stream>/rows.csv
Output : data/external/health/services/diagnostics/diagnostic_services.csv

Steps
1. read every stream's rows.csv (same 11-column schema)
2. normalise atoll codes, island names, public-hospital facility names, categories
3. de-duplicate on (facility_key, service_category): keep the highest-confidence row,
   append other sources' evidence/URLs into the evidence field
4. add HHFA-2022/23-inferred rows for public hospitals lacking lab/X-ray/USG rows
   (HHFA: 100% of 23 hospitals offer FBC, renal & liver function; 91% X-ray; 83% USG)
Run: python -I scripts/diag_merge_rows.py
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/external/health/services/diagnostics"
SRC = BASE / "sources"
OUT = BASE / "diagnostic_services.csv"
STREAMS = ["public_hospital_labs", "imaging", "pcr_bloodbank", "private_labs", "health_centres", "extra"]
COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]
CATS = ["lab_basic", "lab_advanced", "blood_bank", "pcr_molecular", "histopathology", "xray",
        "ultrasound", "ct", "mri", "mammography", "endoscopy"]
ATOLLS = ["HA", "HDh", "Sh", "N", "R", "B", "Lh", "K", "AA", "ADh", "V", "M", "F", "Dh", "Th", "L",
          "GA", "GDh", "Gn", "S"]
ATOLL_ALIASES = {a.lower(): a for a in ATOLLS}
ATOLL_ALIASES.update({
    "haa alifu": "HA", "haa alif": "HA", "haa dhaalu": "HDh", "haa dhaal": "HDh", "hdh.": "HDh",
    "shaviyani": "Sh", "noonu": "N", "raa": "R", "baa": "B", "lhaviyani": "Lh", "kaafu": "K",
    "male": "K", "male'": "K", "male city": "K", "alifu alifu": "AA", "alif alif": "AA",
    "alifu dhaalu": "ADh", "alif dhaal": "ADh", "a.dh": "ADh", "vaavu": "V", "meemu": "M",
    "faafu": "F", "dhaalu": "Dh", "thaa": "Th", "laamu": "L", "gaafu alifu": "GA", "gaafu alif": "GA",
    "gaafu dhaalu": "GDh", "gaafu dhaal": "GDh", "gnaviyani": "Gn", "fuvahmulah": "Gn",
    "seenu": "S", "addu": "S", "addu city": "S", "gdh": "GDh", "ga": "GA", "hdh": "HDh",
})
RANK = {"high": 3, "medium": 2, "low": 1}

# canonical public / major hospitals keyed by (atoll, island)
HOSPITALS = {
    ("K", "Male"): None,  # several facilities in Male - not keyed by island
    ("S", "Hithadhoo"): ("Addu Equatorial Hospital (Hithadhoo)", "public", "tertiary_hospital"),
    ("HDh", "Kulhudhuffushi"): ("Kulhudhuffushi Regional Hospital", "public", "regional_hospital"),
    ("R", "Ungoofaaru"): ("Ungoofaaru Regional Hospital", "public", "regional_hospital"),
    ("L", "Gan"): ("Gan Regional Hospital", "public", "regional_hospital"),
    ("GDh", "Thinadhoo"): ("Dr. Abdul Samad Memorial Hospital (Thinadhoo)", "public", "regional_hospital"),
    ("M", "Muli"): ("Muli Regional Hospital", "public", "regional_hospital"),
    ("Gn", "Fuvahmulah"): ("Fuvahmulah Hospital", "public", "atoll_hospital"),
    ("HA", "Dhidhoo"): ("HA. Atoll Hospital (Dhidhoo)", "public", "atoll_hospital"),
    ("Sh", "Funadhoo"): ("Sh. Atoll Hospital (Funadhoo)", "public", "atoll_hospital"),
    ("N", "Manadhoo"): ("N. Atoll Hospital (Manadhoo)", "public", "atoll_hospital"),
    ("B", "Eydhafushi"): ("B. Atoll Hospital (Eydhafushi)", "public", "atoll_hospital"),
    ("Lh", "Naifaru"): ("Lh. Atoll Hospital (Naifaru)", "public", "atoll_hospital"),
    ("AA", "Rasdhoo"): ("AA. Atoll Hospital (Rasdhoo)", "public", "atoll_hospital"),
    ("ADh", "Mahibadhoo"): ("ADh. Atoll Hospital (Mahibadhoo)", "public", "atoll_hospital"),
    ("V", "Felidhoo"): ("V. Atoll Hospital (Felidhoo)", "public", "atoll_hospital"),
    ("F", "Nilandhoo"): ("F. Atoll Hospital (Nilandhoo)", "public", "atoll_hospital"),
    ("Dh", "Kudahuvadhoo"): ("Dh. Atoll Hospital (Kudahuvadhoo)", "public", "atoll_hospital"),
    ("Th", "Veymandoo"): ("Th. Atoll Hospital (Veymandoo)", "public", "atoll_hospital"),
    ("GA", "Villingili"): ("GA. Atoll Hospital (Villingili)", "public", "atoll_hospital"),
    ("K", "Villimale"): ("Villimale Hospital", "public", "hospital"),
}
ISLAND_ALIASES = {
    "male'": "Male", "malé": "Male", "male": "Male", "hulhumale'": "Hulhumale", "hulhumalé": "Hulhumale",
    "hulhumale": "Hulhumale", "vilimale": "Villimale", "vilimale'": "Villimale", "villimale'": "Villimale",
    "villingili (male)": "Villimale", "fuvammulah": "Fuvahmulah", "fuvahmulaku": "Fuvahmulah",
    "foammulah": "Fuvahmulah", "un'goofaaru": "Ungoofaaru", "ungoofaru": "Ungoofaaru",
    "kulhudhufushi": "Kulhudhuffushi", "kulhudhuffushi city": "Kulhudhuffushi",
    "veymandu": "Veymandoo", "viligili": "Villingili", "vilingili": "Villingili",
    "maduvvaree": "Maduvvari", "naifaru": "Naifaru", "mahibadhu": "Mahibadhoo",
    "gan (laamu)": "Gan", "villingili (ga)": "Villingili",
    "male/hulhumale (island not stated in hems)": "Male", "hulhule": "Hulhumale",
    "thinadhoo city": "Thinadhoo", "hithadhoo (addu)": "Hithadhoo", "hithadhoo, addu": "Hithadhoo",
}
# Male-based facilities: name pattern -> canonical
MALE_NAMES = [
    (r"\bigmh\b|indira gandhi|indhira gandhi", ("Indira Gandhi Memorial Hospital (IGMH)", "public", "tertiary_hospital", "Male")),
    (r"dharumavantha", ("Dharumavantha Hospital", "public", "tertiary_hospital", "Male")),
    (r"senahiya", ("Senahiya Military Hospital", "military", "military_hospital", "Male")),
    (r"^adk hospital|^adk$|^a\.?d\.?k\.? hospital", ("ADK Hospital", "private", "private_hospital", "Male")),
    (r"tree ?top", ("Tree Top Hospital", "private", "private_hospital", "Hulhumale")),
    (r"^hulhumale'? hospital|^hulhumal[eé] hospital", ("Hulhumale Hospital", "public", "tertiary_hospital", "Hulhumale")),
]


def ascii_fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def norm_atoll(a):
    a = (a or "").strip().rstrip(".")
    if not a:
        return ""
    return ATOLL_ALIASES.get(a.lower(), ATOLL_ALIASES.get(ascii_fold(a).lower(), a))


def norm_island(i):
    i = (i or "").strip()
    if not i:
        return ""
    key = i.lower()
    if key in ISLAND_ALIASES:
        return ISLAND_ALIASES[key]
    f = ascii_fold(i)
    return ISLAND_ALIASES.get(f.lower(), f)


NAME_ISLAND_FIX = {"huvadhoo pcr lab": ("Thinadhoo", "GDh"), "aims diagnostic care": ("Feydhoo", "S")}


def canon(row):
    fix = NAME_ISLAND_FIX.get(row["facility_name"].strip().lower())
    if fix and not row["island"].strip():
        row["island"], row["atoll"] = fix
    row["atoll"] = norm_atoll(row["atoll"])
    row["island"] = norm_island(row["island"])
    if row["island"] in ("Male", "Hulhumale", "Villimale") and not row["atoll"]:
        row["atoll"] = "K"
    name = row["facility_name"].strip()
    low = ascii_fold(name).lower()
    for pat, (cname, op, ft, isl) in MALE_NAMES:
        if re.search(pat, low):
            row.update(facility_name=cname, operator_type=op, facility_type=ft, island=isl, atoll="K")
            return row
    key = (row["atoll"], row["island"])
    is_public_hosp = row["operator_type"] == "public" and (
        "hospital" in low or row["facility_type"] in ("regional_hospital", "atoll_hospital", "tertiary_hospital", "hospital"))
    if key in HOSPITALS and HOSPITALS[key] and is_public_hosp and "health cent" not in low:
        cname, op, ft = HOSPITALS[key]
        row.update(facility_name=cname, operator_type=op, facility_type=ft)
    row["facility_name"] = re.sub(r"\s+", " ", row["facility_name"]).strip()
    return row


def fkey(row):
    n = ascii_fold(row["facility_name"]).lower()
    n = re.sub(r"[^a-z0-9]+", " ", n).strip()
    return (n, row["island"].lower(), row["service_category"])


def main():
    rows, bad = [], []
    for s in STREAMS:
        p = SRC / s / "rows.csv"
        if not p.exists():
            print("missing", p)
            continue
        with open(p, encoding="utf-8-sig", newline="") as fh:
            rd = csv.DictReader(fh)
            miss = [c for c in COLS if c not in (rd.fieldnames or [])]
            if miss:
                print("schema problem", p, miss)
            n = 0
            for r in rd:
                r = {c: (r.get(c) or "").strip() for c in COLS}
                r["_stream"] = s
                r["service_category"] = r["service_category"].lower()
                r["confidence"] = r["confidence"].lower()
                if r["service_category"] not in CATS:
                    bad.append((s, r["facility_name"], r["service_category"]))
                    continue
                if r["confidence"] not in RANK:
                    r["confidence"] = "low"
                rows.append(canon(r))
                n += 1
            print(f"{s}: {n} rows")
    if bad:
        print("dropped (bad category):", len(bad), bad[:10])

    merged = {}
    for r in rows:
        k = fkey(r)
        if k not in merged:
            merged[k] = dict(r, _extra=[])
            continue
        cur = merged[k]
        better = (RANK[r["confidence"]], r["source_date"]) > (RANK[cur["confidence"]], cur["source_date"])
        keep, other = (r, cur) if better else (cur, r)
        extra = cur["_extra"]
        if better:
            merged[k] = dict(r, _extra=extra)
            keep = merged[k]
        if other["source_url"] and other["source_url"] != keep["source_url"]:
            extra.append(f"{other['evidence'][:200]} [{other['source_url']}]")
        for f in ("operator_type", "facility_type", "atoll", "service_detail", "source_date"):
            if not keep[f] and other[f]:
                keep[f] = other[f]

    # HHFA inference for public hospitals
    hhfa = "https://health.gov.mv/storage/uploads/9qgDbRoD/vseyvs18.pdf"
    have = {(k[0], k[2]) for k in merged}
    hosp_list = [v for v in HOSPITALS.values() if v]
    hosp_list += [("Indira Gandhi Memorial Hospital (IGMH)", "public", "tertiary_hospital"),
                  ("Hulhumale Hospital", "public", "tertiary_hospital")]
    island_of = {v[0]: k for k, v in HOSPITALS.items() if v}
    island_of["Indira Gandhi Memorial Hospital (IGMH)"] = ("K", "Male")
    island_of["Hulhumale Hospital"] = ("K", "Hulhumale")
    inferred = 0
    for name, op, ft in hosp_list:
        nk = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
        atoll, island = island_of[name]
        for cat, pct, det in [
            ("lab_basic", "100%", "Basic haematology/biochemistry, blood grouping, glucose, urine tests (inferred)"),
            ("lab_advanced", "100%", "FBC, renal & liver function, lipid profile, electrolytes (inferred from HHFA aggregate; specific test menu unverified)"),
            ("xray", "91%", "X-ray (inferred; 91% of hospitals)"),
            ("ultrasound", "83%", "Ultrasound (inferred; 83% of hospitals)"),
        ]:
            if (nk, cat) in have:
                continue
            conf = "medium" if cat in ("lab_basic", "lab_advanced") else "low"
            merged[(nk, island.lower(), cat)] = {
                "facility_name": name, "operator_type": op, "facility_type": ft, "island": island,
                "atoll": atoll, "service_category": cat, "service_detail": det,
                "evidence": f"HHFA Maldives 2022/23 Table 13/11: {pct} of the 23 hospitals assessed offer this; facility-specific confirmation not found",
                "source_url": hhfa, "source_date": "2023", "confidence": conf, "_extra": [], "_stream": "inferred_hhfa"}
            inferred += 1
    print("HHFA-inferred rows added:", inferred)

    out = []
    for r in merged.values():
        ev = r["evidence"]
        if r["_extra"]:
            ev = ev + " | ALSO: " + " | ".join(r["_extra"][:3])
        r["evidence"] = ev[:1500]
        out.append({c: r[c] for c in COLS})
    order = {c: i for i, c in enumerate(CATS)}
    aorder = {a: i for i, a in enumerate(ATOLLS)}
    out.sort(key=lambda r: (aorder.get(r["atoll"], 99), r["island"], r["facility_name"], order[r["service_category"]]))
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(out)
    print("wrote", OUT, len(out), "rows")
    unknown = sorted({r["atoll"] for r in out if r["atoll"] not in ATOLLS})
    if unknown:
        print("non-standard atoll values:", unknown)


if __name__ == "__main__":
    sys.exit(main())
