"""Turn aggregated HEMS professional-by-speciality counts into specialist_services rows.

Location: from hems_facilities_tidy (public facilities), facility name, or contact clues
(atoll landline prefix 6xx, Male' 3xx, email); otherwise Greater Male' assumed (low confidence).

Usage: python -I health_hems_specialist_rows.py <hems_facilities_tidy.csv> <hems_professionals_by_speciality.csv> <OUT_CSV> [aasandha_empanelled_local.csv]

If the Aasandha empanelled-provider list (with islands) is given, private facilities are
geolocated by fuzzy name match against it (overrides the phone-prefix heuristic).
"""
import difflib
import csv
import re
import sys
from collections import defaultdict

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]
SRC = "https://hems.health.gov.mv/establishments (per-facility /professionals JSON)"
DATE = "2026-10-24"

# (category, regex) - first match wins; None = ignore (dental/lab/imaging/general/other agents)
MAP = [
    (None, r"dent|orthodon|endodon|periodon|prosthodon|pedodon|implant|oral|maxillofac|crown"),
    (None, r"laborator|lab tech|patholog|radiolog|radiograph|radiodiag|neuroradiol|sonograph|embryol|biotech|biomedical|forensic"),
    (None, r"nurse|midwife|medical officer|general practi|medical practitioner|pharm|hijam|beys|ayurved|community health|primary health|family health|public health|^$|^a medical"),
    ("oncology", r"oncolog|radiotherap|breast cancer|haematolog|hematolog"),
    ("dialysis", r"nephrolog"),
    ("cardiology", r"cardi"),
    ("nicu", r"neonatol|perinatol"),
    ("paediatrics", r"paediat|pediat|peadiat|developmental"),
    ("maternity", r"obstet|gyn"),
    ("psychiatry", r"psychiat|psycholog|psyclog|psychhol|counsel"),
    ("ophthalmology", r"ophthal|opthal|optomet|glaucoma"),
    ("ent", r"otorhino|oto-rhino|otolaryng|\bent\b"),
    ("dermatology", r"dermat"),
    ("orthopaedics", r"orthop|traumatolog"),
    ("physiotherapy", r"physio|occupational|speech|physical medicine|podiatr"),
    ("icu", r"critical care|intensive care|respiratory therap"),
    ("emergency", r"emergency"),
    ("ncd_diabetes", r"endocrin|diabet|dietit|physician|physian|internal medicine|general medicine|rheumat|pulmonolog|neurolog|gastroenterolog"),
    ("surgery", r"surg|urolog|anaesth|anesth|operation theatre"),
]

# establishment_id -> (island, atoll, operator_type, facility_type, confidence-of-location)
LOC = {
    "612": ("Kulhudhuffushi", "HDh", "public", "regional_hospital", "high"),
    "728": ("Dharavandhoo", "B", "public", "health_centre", "high"),
    "782": ("Hithadhoo", "S", "private", "private_hospital", "high"),
    "827": ("Male'", "MLE", "private", "tertiary_hospital", "high"),
    "362": ("Hulhumale'", "MLE", "private", "tertiary_hospital", "high"),
    "459": ("Male'", "MLE", "private", "private_hospital", "high"),
    "1223": ("Male'", "MLE", "private", "private_hospital", "low"),
    "420": ("Male'", "MLE", "private", "private_hospital", "low"),
    "807": ("Male'", "MLE", "private", "eye_hospital", "high"),
    "397": ("Male'", "MLE", "private", "eye_clinic", "medium"),
    "1395": ("Hithadhoo", "S", "private", "eye_clinic", "low"),
    "1392": ("Kulhudhuffushi", "HDh", "private", "eye_clinic", "high"),
    "1393": ("Gan", "L", "private", "eye_clinic", "high"),  # Aasandha: Eye Care Opticals - Laamu Branch, L. Gan
    "522": ("Male'", "MLE", "private", "eye_clinic", "medium"),
    "451": ("Male'", "MLE", "private", "eye_clinic", "medium"),
    "345": ("Hulhumale'", "MLE", "private", "eye_clinic", "high"),
    "275": ("Kulhudhuffushi", "HDh", "private", "private_clinic", "high"),
    "164": ("Thinadhoo", "GDh", "private", "private_clinic", "low"),
    "42": ("Dharavandhoo", "B", "private", "private_clinic", "high"),
    "153": ("Naifaru", "Lh", "private", "private_clinic", "high"),
    "236": ("Fuvahmulah", "Gn", "private", "private_clinic", "high"),
    "235": ("Fuvahmulah", "Gn", "private", "private_clinic", "medium"),
    "176": ("Villingili", "GA", "private", "private_clinic", "low"),
    "29": ("Funadhoo", "Sh", "private", "private_clinic", "high"),
    "432": ("Hithadhoo", "S", "private", "private_clinic", "low"),
    "90": ("Kulhudhuffushi", "HDh", "private", "private_clinic", "low"),
    "335": ("Dhangethi", "ADh", "private", "private_clinic", "medium"),
    "954": ("Dhidhdhoo", "HA", "private", "physio_rehab_clinic", "high"),
    "1627": ("Thulusdhoo", "K", "private", "physio_rehab_clinic", "high"),
    "33": ("Hulhumale'", "MLE", "private", "therapy_clinic", "high"),
    "314": ("Hulhumale'", "MLE", "private", "private_clinic", "high"),
    "35": ("Hulhumale'", "MLE", "private", "private_clinic", "low"),
    "201": ("Hulhumale'", "MLE", "private", "private_clinic", "low"),
    "886": ("Hulhumale'", "MLE", "private", "private_clinic", "low"),
    "818": ("Male'", "MLE", "ngo", "family_planning_clinic", "medium"),
}
SKIP = {"772", "419", "517", "64"}  # police detention clinics; dental centres with a visiting cardiologist


AAS_BAD = {"Advance Hospital", "CyMa Care Hulhumale'", "Child Development Clinic",
           "SafeSpace Psychological Clinic", "Vision Care Optical and Eye Clinic"}
PFX = {"aa": "AA", "adh": "ADh", "gdh": "GDh", "hdh": "HDh", "ha": "HA", "sh": "Sh", "lh": "Lh",
       "ga": "GA", "gn": "Gn", "th": "Th", "dh": "Dh", "k": "K", "s": "S", "l": "L", "b": "B",
       "r": "R", "n": "N", "m": "M", "f": "F", "v": "V"}
ISL = {"Dhagethi": "Dhangethi", "Male'": "Male'", "Hulhumale'": "Hulhumale'"}


def nk(s):
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    s = re.sub(r"(pvt|ltd|private|limited|the|medical|clinic|centre|center|and|services|care)", " ", s)
    return " ".join(s.split())


def load_aas(path):
    out = {}
    for a in csv.DictReader(open(path, encoding="utf-8")):
        isl = ISL.get(a["island"].strip(), a["island"].strip())
        at = PFX.get(a["atoll_prefix"].strip().lower(), a["atoll_prefix"].strip())
        if isl in ("Male'", "Hulhumale'", "Villimale'", "Vilimale'"):
            at = "MLE"
        out[nk(a["provider_name"])] = (isl, at, a["provider_name"], a["island_raw"])
    return out


def main():
    aas = load_aas(sys.argv[4]) if len(sys.argv) > 4 else {}
    tidy = {r["establishment_id"]: r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))}
    pros = list(csv.DictReader(open(sys.argv[2], encoding="utf-8")))
    agg = defaultdict(lambda: defaultdict(list))
    for p in pros:
        eid = p["establishment_id"]
        if eid in SKIP:
            continue
        spec = p["profession_or_speciality"].strip()
        cat = "?"
        for c, rx in MAP:
            if re.search(rx, spec, re.I):
                cat = c
                break
        if cat is None or cat == "?":
            continue
        agg[eid][cat].append(f"{p['count']} {spec}")
    rows = []
    for eid, cats in agg.items():
        t = tidy.get(eid, {})
        name = t.get("name", "")
        lvl = t.get("level", "")
        am = None
        if aas and name not in AAS_BAD:
            mm = difflib.get_close_matches(nk(name), list(aas), n=1, cutoff=0.75)
            am = aas[mm[0]] if mm else None
        if eid in LOC and not (am and LOC[eid][4] == "low"):
            isl, at, op, ft, lc = LOC[eid]
        elif am and not t.get("island"):
            isl, at = am[0], am[1]
            op = "ngo" if eid == "818" else "private"
            ft = {"General Clinic": "private_clinic", "Therapeutic Service Clinic": "therapy_clinic",
                  "Area Specific Clinic": "specialist_clinic", "General Hospital": "private_hospital",
                  "Tertiary Hospital": "tertiary_hospital", "Area Specific Hospital": "eye_hospital"}.get(lvl, lvl.lower().replace(" ", "_"))
            lc = "aas"
        elif t.get("island"):
            isl, at = t["island"], t["atoll_code"]
            op = "public" if t.get("sector") == "public" else "private"
            ft, lc = lvl.lower().replace(" ", "_"), "high"
        else:
            m = "hulhumale" in name.lower()
            contact = t.get("contact", "")
            if re.search(r"(?<!\d)335\d{4}(?!\d)", contact):
                m = True
            isl, at, op = ("Hulhumale'" if m else "Male'"), "MLE", "private"
            male_landline = re.search(r"(?<!\d)3\d{6}(?!\d)", contact)
            ft = {"General Clinic": "private_clinic", "Therapeutic Service Clinic": "therapy_clinic",
                  "Area Specific Clinic": "specialist_clinic", "General Hospital": "private_hospital"}.get(lvl, lvl.lower().replace(" ", "_"))
            lc = "medium" if male_landline else "low"
        for cat, specs in cats.items():
            n = sum(int(s.split()[0]) for s in specs)
            det = "; ".join(specs)
            if cat == "ncd_diabetes":
                det = "internal-medicine/medical specialists: " + det
            if lc == "aas":
                det += f" [island from Aasandha empanelled list: {am[2]}, {am[3]}]"
            if lc == "low":
                det += " [location inferred - Greater Male' assumed or from phone/email clue]"
            elif eid not in LOC and not t.get("island"):
                det += " [location from Male'-region landline in HEMS contact]"
            conf = {"high": "high", "medium": "medium", "low": "low", "aas": "high"}[lc]
            if conf == "high" and n == 1 and cat in ("ncd_diabetes",):
                conf = "medium"
            rows.append({"facility_name": name, "operator_type": op, "facility_type": ft,
                         "island": isl, "atoll": at, "service_category": cat,
                         "service_detail": det[:300],
                         "evidence": f"HEMS public registry lists {n} registered practitioner(s) in this field at the establishment ({lvl})",
                         "source_url": SRC, "source_date": DATE, "confidence": conf})
    with open(sys.argv[3], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "rows from", len(agg), "facilities")


if __name__ == "__main__":
    main()
