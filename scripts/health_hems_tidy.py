"""Build a tidy facility master list from the scraped HEMS registry.

Adds atoll code / island / service tier using (a) the atoll prefix embedded in the name
("Haa Alifu X Health Centre", "GDh. X Health Centre", "A.A X ..."), and (b) a hand-curated
lookup for hospitals whose names carry no island (marked location_source='curated').

Usage: python -I health_hems_tidy.py <hems_establishments.csv> <out.csv>
"""
import csv
import re
import sys

ATOLLS = [  # (regex on name prefix, MBS atoll code, atoll name)
    (r"haa\s+alifu?|h\.?\s*a\b\.?", "HA", "Haa Alif"),
    (r"haa\s+dhaalu|h\.?\s*dh\b\.?", "HDh", "Haa Dhaalu"),
    (r"shaviyani|sh\b\.?", "Sh", "Shaviyani"),
    (r"noonu|n\b\.", "N", "Noonu"),
    (r"raa|r\b\.", "R", "Raa"),
    (r"baa|b\b\.", "B", "Baa"),
    (r"lhaviyani|lh\b\.?", "Lh", "Lhaviyani"),
    (r"kaafu|k\b\.?", "K", "Kaafu"),
    (r"alifu\s+alifu|a\.?\s*a\b\.?", "AA", "Alif Alif"),
    (r"alifu\s+dhaalu|a[\.,]?\s*dh\b\.?", "ADh", "Alif Dhaal"),
    (r"vaavu|v\b\.", "V", "Vaavu"),
    (r"meemu|m\b\.", "M", "Meemu"),
    (r"faafu|f\b\.?", "F", "Faafu"),
    (r"dhaalu|dh\b\.?", "Dh", "Dhaalu"),
    (r"thaa|th\b\.?", "Th", "Thaa"),
    (r"laamu|l\b\.?", "L", "Laamu"),
    (r"gaafu\s+alifu?|g\.?\s*a\b\.?", "GA", "Gaafu Alif"),
    (r"gaafu\s+dhaalu|g\.?\s*dh\b\.?", "GDh", "Gaafu Dhaalu"),
    (r"gnaviyani|gn\b\.?", "Gn", "Gnaviyani"),
    (r"seenu|addu|s\b\.", "S", "Seenu (Addu)"),
]
# order matters: longer / two-letter codes must be tried before single letters
ORDER = ["HA", "HDh", "Sh", "Lh", "AA", "ADh", "GA", "GDh", "Gn", "Th", "Dh",
         "N", "R", "B", "K", "V", "M", "F", "L", "S"]
ATOLLS.sort(key=lambda a: ORDER.index(a[1]))

# Curated locations for facilities whose names do not include the island.
# Sources: MoH hospital naming conventions / facility websites; verify before publication.
CURATED = {
    "Indhira Gandhi Memorial Hospital": ("K", "Male'"),
    "ADK Hospital": ("K", "Male'"),
    "Tree Top Hospital": ("K", "Hulhumale'"),
    "Hulhumale' Hospital": ("K", "Hulhumale'"),
    "Vilimale' Hospital": ("K", "Villimale'"),
    "Dharumavantha Hospital": ("K", "Male'"),
    "Senahiya Military Hospital": ("K", "Male'"),
    "Maldives Emergency Medical Services": ("K", "Male'"),
    "Huraa Health Center": ("K", "Huraa"),
    "Addu Equatorial Hospital": ("S", "Hithadhoo"),
    "Gan Regional Hospital": ("L", "Gan"),
    "Dr. Abdul Samad Memorial Hospital": ("GDh", "Thinadhoo"),
    "Fuvammulah Hospital": ("Gn", "Fuvahmulah"),
    "Kulhudhuffushi Regional Hospital": ("HDh", "Kulhudhuffushi"),
    "Un'goofaaru Regional Hospital": ("R", "Ungoofaaru"),
    "Muli Regional Hospital": ("M", "Muli"),
    "Haa Alifu Atoll Hospital": ("HA", "Dhidhoo"),
    "Shaviyani Atoll Hospital": ("Sh", "Funadhoo"),
    "Noonu Atoll hospital": ("N", "Manadhoo"),
    "Baa Atoll Hospital": ("B", "Eydhafushi"),
    "Lhaviyani Atoll Hospital": ("Lh", "Naifaru"),
    "Alifu Alifu Atoll Hospital": ("AA", "Rasdhoo"),
    "Alifu Dhaalu Atoll Hospital": ("ADh", "Mahibadhoo"),
    "Vaavu Atoll Hospital": ("V", "Felidhoo"),
    "Faafu Atoll Hospital": ("F", "Nilandhoo"),
    "Dhaalu Atoll Hospital": ("Dh", "Kudahuvadhoo"),
    "Thaa Atoll Hospital": ("Th", "Veymandoo"),
    "Gaafu Alifu Atoll Hospital": ("GA", "Villingili"),
    "Amina Dhiyo Health Centre": ("HA", "Ihavandhoo"),
    # by elimination: MHS 2020 lists HA Baarah + HA Ihavandhoo HCs; HEMS names only these two
    "Amina Rehendhi Health Centre": ("HA", "Baarah"),
    "I.M.D.C Multi Speciality Hospital": ("S", "Hithadhoo"),
    "M.C.S. Medical Center 2": ("", ""),  # prison clinic, island not stated
}

TIER = {
    "Tertiary Hospital": "1_tertiary",
    "Hospital Grade 3": "2_regional_hospital",
    "General Hospital": "2_general_hospital",
    "Hospital Grade 2": "3_atoll_hospital",
    "Hospital Grade 1": "3_atoll_hospital_small",
    "Health Centre Grade 4": "4_health_centre_g4",
    "Health Centre Grade 3": "4_health_centre_g3",
    "Health Centre Grade 2": "5_health_centre_g2",
    "Health Centre Grade 1": "5_health_centre_g1",
}


def locate(name):
    if name in CURATED:
        a, isl = CURATED[name]
        return a, isl, "curated"
    n = name.strip()
    for rx, code, _ in ATOLLS:
        m = re.match(rf"^\s*(?:{rx})[\s\.,]*(.+)$", n, re.I)
        if m:
            rest = m.group(1)
            isl = re.split(r"\s+(?:Health|Heath|Atoll|Regional|Hospital|Medical|Clinic)\b", rest, flags=re.I)[0]
            isl = isl.strip(" .,")
            if isl and isl[0].isupper():
                return code, isl, "name_prefix"
    return "", "", ""


def main():
    src, out = sys.argv[1], sys.argv[2]
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    name_of = {a[1]: a[2] for a in ATOLLS}
    res = []
    for r in rows:
        public = ("GOV" in r["reg_no"]) or r["owner"].lower().startswith("ministry")
        code, isl, how = locate(r["name"])
        res.append({
            "establishment_id": r["establishment_id"], "name": r["name"], "status": r["status"],
            "sector": "public" if public else "private", "owner": r["owner"], "level": r["level"],
            "tier": TIER.get(r["level"], "other_clinic"),
            "atoll_code": code, "atoll_name": name_of.get(code, ""), "island": isl,
            "location_source": how, "reg_no": r["reg_no"], "license_no": r["license_no"],
            "contact": r["contact"], "n_professionals_listed": r["n_professionals"],
        })
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0].keys()))
        w.writeheader()
        w.writerows(res)
    pub = [x for x in res if x["sector"] == "public"]
    print(f"{len(res)} rows; public {len(pub)}; public unlocated:",
          [x["name"] for x in pub if not x["atoll_code"]])


if __name__ == "__main__":
    main()
