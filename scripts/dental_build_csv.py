"""Build data/external/health/services/dental/dental_services.csv

Combines:
  1. HEMS (MoH Health Establishment Management System) per-facility dental professional counts
     (sources/hems/hems_dental_counts.csv) -> mostly private facilities (+ Tree Top, KRH)
  2. HEMS dental-named establishments with zero professionals listed (moh_hems_registry)
  3. Aasandha empanelled-facility list (provider -> island) used to locate private facilities
  4. Manually curated rows (public hospitals / health centres / outreach / news evidence) in
     sources/manual_rows*.csv (same columns as output)

Usage: python -I dental_build_csv.py <DENTAL_DIR> <HEMS_TIDY_CSV>
"""
import csv
import difflib
import os
import re
import sys

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]
ACCESS = "2026-10-24"

ATOLL_FROM_PREFIX = {"k": "K", "aa": "AA", "adh": "ADh", "ha": "HA", "hdh": "HDh", "sh": "Sh", "n": "N",
                     "r": "R", "b": "B", "lh": "Lh", "v": "V", "m": "M", "f": "F", "dh": "Dh",
                     "th": "Th", "l": "L", "ga": "GA", "gdh": "GDh", "gn": "Gn", "s": "S"}

# Manual location overrides for HEMS facilities not resolvable via Aasandha
# eid -> (island, atoll, how, confidence_cap)
MANUAL_LOC = {
    "459": ("Malé", "K", "MoH work-permit list 'Medica, Male''; registry address M. Dhahana, Fareedhee Magu, K. Male'", "high"),
    "202": ("Alifushi", "R", "MoH private facility registry (23.07.2026) address: Flooniyaage, R. Alifushi", "high"),
    "29": ("Funadhoo", "Sh", "MoH private facility registry (23.07.2026) address: Sea Star, Sh. Funadhoo", "high"),
    "277": ("Meedhoo (Addu)", "S", "MoH private facility registry (23.07.2026) address: Mirihaana, S. Meedhoo", "high"),
    "1478": ("Hulhumalé (unverified)", "K", "not in registry; same contact number as Care Trust Multi Speciality Clinic (Hulhumalé); registered 2026", "low"),
    "1442": ("Milandhoo", "Sh", "MoH private facility registry (23.07.2026) address: Bilaalu-aage, Sh. Milandhoo (licensed May 2026)", "high"),
    "1223": ("Malé", "K", "MoH private facility registry (23.07.2026) address: Ma. Neem Flower, K. Male' (hospital licensed June 2026)", "high"),
    "1042": ("Malé", "K", "MoH private facility registry (23.07.2026) address: M. Gadhdhaduge (Maafannu ward, Malé; licensed Feb 2026)", "medium"),
    "126": ("Ellaidhoo (resort island)", "AA", "MoH private facility registry (23.07.2026) address: Ellaidhoo, Alif Alif Atoll (Cinnamon resort clinic; serves resort guests/staff, not a local community)", "medium"),
    "1463": ("Hulhumalé", "K", "MoH private facility registry (23.07.2026) address: Lot 10119, Halaveli Magu, Hulhumale", "high"),
    "1142": ("Malé", "K", "MoH private facility registry (23.07.2026) address: M. Haagiri, Male'", "high"),
    "54": ("Fonadhoo", "L", "MoH private facility registry (23.07.2026) address: Fehifarudhaage, L. Fonadhoo", "high"),
    "7": ("Malé", "K", "MoH private facility registry (23.07.2026) address: H. Rasmaadhooge, Abadhah Fehi Magu, Male'", "high"),
    "93": ("Thinadhoo", "GDh", "MoH private facility registry (23.07.2026) address: Alidhoadhi, Gdh. Thinadhoo", "high"),
    "917": ("Ihavandhoo", "HA", "MoH private facility registry (23.07.2026) address: Fulmoon, Ha. Ihavandhoo", "high"),
    "165": ("Malé", "K", "MoH private facility registry (23.07.2026) address: M. Sailaa, Izzuddeen Magu, Male'", "high"),
    "526": ("Malé", "K", "MoH private facility registry (23.07.2026) address: G. Nashaathu Villa, Nirolhu Magu (Malé)", "high"),
    "163": ("Malé", "K", "MoH private facility registry (23.07.2026) address: Ma. Meyvaagasdhoshuge (Malé)", "high"),
    "64": ("Gadhdhoo", "GDh", "MoH private facility registry (23.07.2026) address: Jihaadh, Gdh. Gadhdhoo (owner Dent Care Maldives; shares contact with Master Dental Care chain)", "high"),
}

SPEC_MAP = [
    (r"orthodon", "orthodontics"),
    (r"maxillofacial", "oral and maxillofacial surgery"),
    (r"pedodon|paediatric dent|pediatric dent|pedodontics", "paediatric dentistry"),
    (r"endodon|conservati", "endodontics"),
    (r"periodon", "periodontics"),
    (r"prosthodon", "prosthodontics"),
    (r"implant", "implantology"),
    (r"oral medicine", "oral medicine and radiology"),
    (r"dentist|dentistry", "general dentistry"),
]


def norm(s):
    s = s.lower().replace("centre", "center").replace("&", "and").replace("\xa0", " ")
    return re.sub(r"[^a-z0-9 ]", "", s)


def parse_island(s):
    s = s.replace("\xa0", " ").strip()
    m = re.match(r"^([A-Za-z]+)\.\s*(.*)$", s)
    if not m:
        return s, ""
    pre, isl = m.group(1).lower(), m.group(2).strip()
    isl = {"Male'": "Malé", "Hulhumale'": "Hulhumalé", "Villimale": "Villimalé",
           "MaradhooFeydhoo": "Maradhoo-Feydhoo"}.get(isl, isl)
    return isl, ATOLL_FROM_PREFIX.get(pre, pre.upper())


def spec_of(prof):
    p = prof.lower()
    for pat, lab in SPEC_MAP:
        if re.search(pat, p):
            return lab
    return None


def ftype(level, name):
    n = name.lower()
    if "hospital" in level.lower():
        return "private hospital"
    if "dent" in n:
        return "dental clinic"
    return "private clinic"


def main():
    ddir, hems_tidy = sys.argv[1], sys.argv[2]
    src = os.path.join(ddir, "sources")
    aas = list(csv.DictReader(open(os.path.join(src, "aasandha", "aasandha_empanelled_local.csv"), encoding="utf-8")))
    an = [norm(a["provider"]) for a in aas]
    dent = list(csv.DictReader(open(os.path.join(src, "hems", "hems_dental_counts.csv"), encoding="utf-8")))
    tidy = {r["establishment_id"]: r for r in csv.DictReader(open(hems_tidy, encoding="utf-8"))}

    # group professions per establishment, skip ambiguous 'Medicine/Dentistry'
    fac = {}
    for r in dent:
        if r["profession"] == "Medicine/Dentistry":
            continue
        f = fac.setdefault(r["establishment_id"], {"row": r, "spec": {}})
        lab = spec_of(r["profession"])
        if lab:
            f["spec"].setdefault(lab, []).append(f"{r['count']} {r['profession']}")
    # dental-named establishments with nobody listed
    for eid, t in tidy.items():
        if eid in fac:
            continue
        if re.search(r"dent", t["name"], re.I):
            fac[eid] = {"row": {"establishment_id": eid, "name": t["name"], "sector": t["sector"],
                                "level": t["level"], "atoll_code": t["atoll_code"], "island": t["island"],
                                "status": t["status"]}, "spec": {}}

    out = []
    for eid, f in fac.items():
        r = f["row"]
        name = r["name"].strip()
        t = tidy.get(eid, {})
        isl, atl, how, cap = "", "", "", "high"
        if r.get("island"):
            isl, atl, how = r["island"].replace("'", "é").replace("Hulhumaleé", "Hulhumalé"), r["atoll_code"], "HEMS name prefix"
        if not isl:
            m = difflib.get_close_matches(norm(name), an, n=1, cutoff=0.82)
            if m:
                a = aas[an.index(m[0])]
                isl, atl = parse_island(a["island"])
                how = f"Aasandha empanelled list: '{a['provider']}' at {a['island']}"
        if eid in MANUAL_LOC:
            isl, atl, how, cap = MANUAL_LOC[eid]
        sector = r.get("sector") or t.get("sector", "private")
        op = "public" if sector == "public" else "private"
        if "senahiya" in name.lower():
            op = "military"
        ft = "regional hospital" if "Regional Hospital" in name else ftype(r.get("level", ""), name)
        url = f"https://hems.health.gov.mv/establishments/{eid}/professionals"
        reg = t.get("reg_no", "")
        if f["spec"]:
            for lab, items in f["spec"].items():
                conf = cap if isl else "low"
                ev = (f"HEMS lists {'; '.join(items)} at this establishment (reg {reg}); location: {how}")
                out.append([name, op, ft, isl or "unknown", atl, "dental", lab, ev, url, ACCESS, conf])
        else:
            ev = (f"HEMS-registered {r.get('level','')} with dental name (reg {reg}; status {t.get('status','')}); "
                  f"no practitioners listed in HEMS; location: {how or 'not found'}")
            conf = "medium" if isl and "unknown" not in isl and cap != "low" else "low"
            out.append([name, op, ft, isl or "unknown", atl, "dental", "general dentistry (registered dental clinic; staffing not listed)",
                        ev, url, ACCESS, conf])

    for fn in sorted(os.listdir(src)):
        if fn.startswith("manual_rows") and fn.endswith(".csv"):
            for r in csv.DictReader(open(os.path.join(src, fn), encoding="utf-8")):
                out.append([(r.get(c) or "").strip() for c in COLS])
    # de-duplicate exact facility x service x island
    rank = {"high": 3, "medium": 2, "low": 1}
    seen, final = {}, []
    for r in out:
        k = (norm(r[0]), r[3].lower(), r[6].lower())
        if k in seen:
            f = seen[k]
            if r[7] and r[7] not in f[7]:
                f[7] = f[7] + " || " + r[7]
            if r[8] and r[8] not in f[8]:
                f[8] = f[8] + " | " + r[8]
            if r[9] and r[9] > f[9]:
                f[9] = r[9]
            if rank.get(r[10], 0) > rank.get(f[10], 0):
                f[10] = r[10]
            continue
        seen[k] = r
        final.append(r)
    final.sort(key=lambda r: (r[4] or "zz", r[3], r[0], r[6]))
    with open(os.path.join(ddir, "dental_services.csv"), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(COLS)
        w.writerows(final)
    print(f"wrote {len(final)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
