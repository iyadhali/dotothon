"""Build data/external/education/institutions_master.csv from the tidy per-source CSVs.

Rows:
  * higher-education / TVET campuses from the MoE/MoHE register (Oct 2026), with
    levels offered (MNU: per campus from courses.mnu.edu.mv; others: institution-level from
    MoHE "Locally Available Programmes 2025") and an extra institution-total row carrying
    enrolment from MBS Statistical Yearbook 2022 Table 7.29 (latest year available per institution);
  * schools from MBS Yearbook 2024 Table 7.2 (school x grade enrolment 2022-23), enriched with
    MoE school directory (May 2025) students/teachers for government schools where matched;
    unmatched directory schools are appended.

Columns: institution, type, campus, island, atoll, levels_offered, enrolment, year, source_url,
         + sector, atoll_code, teachers, enrolment_2025_moe_dir, highest_grade, offers_grade_11_12, notes

Usage: python -I scripts/edu_build_master.py
"""
import csv
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

E = Path(r"C:\Users\user\Music\Datathon\data\external\education")
ATOLL = {"HA": "Haa Alifu", "HDh": "Haa Dhaalu", "Sh": "Shaviyani", "N": "Noonu", "R": "Raa", "B": "Baa",
         "Lh": "Lhaviyani", "K": "Kaafu", "AA": "Alifu Alifu", "ADh": "Alifu Dhaalu", "V": "Vaavu",
         "M": "Meemu", "F": "Faafu", "Dh": "Dhaalu", "Th": "Thaa", "L": "Laamu", "GA": "Gaafu Alifu",
         "GDh": "Gaafu Dhaalu", "Gn": "Gnaviyani", "S": "Seenu", "Sn": "Seenu", "K-Male": "Male' City",
         "Male city": "Male' City"}
ATOLL_CI = {k.lower(): v for k, v in ATOLL.items()}
NAME2CODE = {v: k for k, v in ATOLL.items() if k not in ("Sn", "Male city")}
NAME2CODE["Male' City"] = "K-Male"

# register name -> (MoHE programmes-list name, MBS enrolment name)
HEI_MAP = {
    "The Maldives National University": ("Maldives National University", "Maldives National University"),
    "Islamic University of Maldives": ("Islamic University of Maldives", "Islamic University of Maldives"),
    "Villa College": ("Villa College", "Villa College"),
    "Clique College": ("Clique College", "Clique College"),
    "Cyryx College": ("Cyryx College", "Cyryx College"),
    "Mandhu College": ("Mandhu College", "Mandhu College"),
    "MAPS College": ("Maps College", "MAPS College"),
    "Avid College": ("Avid College", "Avid College"),
    "Maldives Business School": ("Maldives Business School", "Maldives Business School"),
    "MIANZ College (formerly MI College)": ("Mianz International College", "MI College"),
    "Zikura International College": ("Zikura International College", "Zikura International College"),
    "Maldives Institute of Technology": ("Maldives Institute of Technology", None),
    "Maldives Polytechnic": ("Maldives Polytechnic", "Maldives Polytechnic"),
    "Eupheus Collegiate": ("Eupheus Collegiate", None),
    "NES Institute": ("NES Institute", None),
    "Island Institute of Tertiary Education": ("Island Institute of Tertiary Education", None),
    "ILM Institute for Islamic Studies": ("ILM Institute For Islamic Studies", None),
    "Institute of Quran and Sunnah": ("Institute of Quran and Sunnah", None),
    "Zaad Academy": ("Zaad Academy", None),
    "Dhives Institute": ("Dhives Institute", None),
    "Maldives National Institute of Sports": ("Maldives National institute of Sports", None),
    "Port Training Centre": ("Port Training Centre", None),
    "Maldives Media Institute": ("Maldives Media Institute", None),
    "Civil Service Training Institute": ("Civil Service Training Institute", None),
    "Institute for Correctional Studies": ("Institute for Correctional Studies", None),
    "Centre for Customs and Excise Studies": ("Centre for Customs and excise Studies", None),
    "Evove Academy": ("Evove Academy", None),
    "Institute of Quranic Studies": ("Institute of Quranic Studies", None),
    "Shafia Institute of Health - ADK Hospital": ("Shafia Institute of Health, ADK Hospital", None),
}
MNU_LEVEL = {"Doctorate": 10, "Master": 9, "Postgraduate": 8, "Graduate": 8, "Bachelor": 7, "Associate": 6,
             "Advanced diploma": 6, "Diploma": 5, "Advanced certificate": 4, "Foundation": 4,
             "Certificate IV": 4, "Certificate III": 3, "Certificate II": 2, "Certificate I ": 1}


def read(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[’'`.\-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def school_key(s):
    s = norm(s)
    s = re.sub(r"^(ha|hdh|sh|n|r|b|lh|k|aa|adh|v|m|f|dh|th|l|ga|gdh|gn|s|noonu|seenu|raa|baa|laamu|thaa|"
               r"faafu|dhaalu|meemu|vaavu|kaafu|shaviyani|lhaviyani|gnaviyani)\s+", "", s)
    s = re.sub(r"\b(haa alifu|haa dhaalu|alifu alifu|alifu dhaalu|gaafu alifu|gaafu dhaalu|shaviyani|noonu|raa|baa|"
               r"lhaviyani|kaafu|vaavu|meemu|faafu|dhaalu|thaa|laamu|gnaviyani|seenu|ha|hdh|sh|lh|aa|adh|ga|gdh|gn)"
               r"\s+atoll\b", "atoll", s)
    s = re.sub(r"\b(school|the)\b", " ", s)
    s = s.replace("madharusathul", "madrasathul")
    return re.sub(r"\s+", " ", s).strip()


def island_key(s):
    s = norm(s)
    s = re.sub(r"\b(city)\b", "", s).replace("vilimale", "villimale").replace("hulhumale", "hulhumale")
    return s.replace(" ", "")


def mnu_levels():
    lv = defaultdict(set)
    for r in read(E / "mnu_courses" / "mnu_courses_by_campus.csv"):
        m = re.search(r"MNQF (\d+)", r["level_group"])
        if m:
            lv[r["island"]].add(int(m.group(1)))
        elif "MNQF 1-4" in r["level_group"]:
            lv[r["island"]].add(4)  # generic certificate; treat as <= 4
    return lv


def main():
    out = []
    reg = read(E / "moe_registered_colleges" / "registered_hei_campuses_2026.csv")
    prog = defaultdict(set)
    for r in read(E / "mohe_higher_education" / "locally_available_programmes_2025.csv"):
        if r["mnqf_level"]:
            prog[r["institution"]].add(int(r["mnqf_level"]))
    enr = {}
    for r in read(E / "mbs_statistical_yearbook" / "yb2022" / "hei_enrolment_by_institution_2019_2021.csv"):
        k = r["institution"]
        if k not in enr or int(r["year"]) > int(enr[k]["year"]):
            enr[k] = r
    mnu = mnu_levels()
    src_prog = "https://mohe.gov.mv/images/resources/resources/Locally%20Available%20Programmes%20as%20of%202025.pdf"
    src_enr = "https://statisticsmaldives.gov.mv/yearbook/2022/wp-content/uploads/sites/9/2023/03/7.29.xlsx"
    seen_inst = []
    for r in reg:
        inst = r["institution"]
        pname, ename = HEI_MAP.get(inst, (None, None))
        levels, note = "", ""
        if inst == "The Maldives National University" and r["island"] in mnu:
            levels = "MNQF " + ",".join(str(x) for x in sorted(mnu[r["island"]]))
            note = "levels from MNU course catalogue for this campus (courses.mnu.edu.mv)"
        elif pname and pname in prog:
            levels = "MNQF " + ",".join(str(x) for x in sorted(prog[pname]))
            note = "institution-level programme levels (MoHE list covers MNQF 5+; campus offer not specified)"
        if not r["location_stated"] == "True":
            note = (note + "; " if note else "") + "location not stated in register"
        typ = {"University": "university campus", "College": "college campus"}.get(r["category"], "institute")
        if inst == "Maldives Polytechnic":
            typ = "TVET institute"
        if r["campus_type"] == "outreach centre":
            typ += " (outreach centre)"
        if r["campus_type"] == "quran centre (gofi)":
            typ = "institute (Quran centre)"
        out.append(dict(institution=inst, type=typ, campus=r["campus"], island=r["island"], atoll=r["atoll"],
                        levels_offered=levels, enrolment="", year="2026 (register)", source_url=r["source_url"],
                        sector=r["sector"], atoll_code=r["atoll_code"], teachers="", enrolment_2025_moe_dir="",
                        highest_grade="", offers_grade_11_12="", notes=note))
        if inst not in seen_inst:
            seen_inst.append(inst)
    # institution-total rows with enrolment
    for inst in seen_inst:
        pname, ename = HEI_MAP.get(inst, (None, None))
        if ename and ename in enr:
            e = enr[ename]
            lv = "MNQF " + ",".join(str(x) for x in sorted(prog.get(pname, []))) if pname in prog else ""
            cat = next(r for r in reg if r["institution"] == inst)
            out.append(dict(institution=inst, type="institution total (all campuses)", campus="ALL",
                            island="", atoll="", levels_offered=lv, enrolment=e["enrolment"], year=e["year"],
                            source_url=src_enr, sector=cat["sector"], atoll_code="", teachers="",
                            enrolment_2025_moe_dir="", highest_grade="", offers_grade_11_12="",
                            notes="enrolment from Ministry of Higher Education via MBS Yearbook 2022 T7.29; "
                                  "no campus split published"))

    # ---- schools
    sch = read(E / "mbs_statistical_yearbook" / "yb2024" / "school_enrolment_by_grade_2022_23.csv")
    moe = read(E / "moe_school_directory" / "moe_school_directory.csv")
    # greedy matching within atoll: name similarity (+ island similarity)
    def atoll_of_sch(x):
        return ATOLL_CI.get(x["atoll_label"].lower(), x["atoll_label"])

    def atoll_of_moe(m):
        return "Male' City" if "Male" in (m["atoll"] or "") else m["atoll"]

    pairs = []
    for i, x in enumerate(sch):
        for m in moe:
            if atoll_of_moe(m) != atoll_of_sch(x):
                continue
            ns = SequenceMatcher(None, school_key(x["school"]), school_key(m["school"])).ratio()
            isim = SequenceMatcher(None, island_key(x["island"]), island_key(m["island"] or "")).ratio()
            male_city = atoll_of_sch(x) == "Male' City"  # island sim is meaningless inside Male' City
            if ns >= 0.8 or (not male_city and ns >= 0.55 and isim >= 0.6):
                pairs.append((ns + 0.2 * isim, i, m["moe_school_id"], ns))
    pairs.sort(reverse=True)
    match, used = {}, set()
    moe_by_id = {m["moe_school_id"]: m for m in moe}
    for sc, i, mid, ns in pairs:
        if i in match or mid in used:
            continue
        match[i] = (moe_by_id[mid], ns)
        used.add(mid)
    src_sch = "https://statisticsmaldives.gov.mv/yearbook/2024/wp-content/uploads/sites/11/2024/11/7.2.xlsx"
    for i, s in enumerate(sch):
        best, score = match.get(i, (None, 0.0))
        name = s["school"]
        is_pre = bool(re.search(r"pre[\s-]?school|preschool|kindergarten|nursery", name, re.I)) or s["lowest_grade"] in ("BN", "N") and s["highest_grade"] in ("N", "LKG", "UKG")
        typ = "preschool" if is_pre or s["highest_grade"] in ("LKG", "UKG", "N", "BN") else "school"
        if s["highest_grade"] == "GR12" and s["lowest_grade"] == "GR11":
            typ = "higher secondary school"
        atoll_name = ATOLL_CI.get(s["atoll_label"].lower(), s["atoll_label"])
        out.append(dict(
            institution=name, type=typ, campus="", island=s["island"], atoll=atoll_name,
            levels_offered=f"{s['lowest_grade']}-{s['highest_grade']}" if s["lowest_grade"] else "",
            enrolment=s["total"], year="2022-2023", source_url=src_sch,
            sector="government" if best else "private/community or unmatched government",
            atoll_code=NAME2CODE.get(atoll_name, s["atoll_code"]),
            teachers=best["teachers"] if best else "", enrolment_2025_moe_dir=best["students"] if best else "",
            highest_grade=s["highest_grade"], offers_grade_11_12=s["offers_higher_secondary"],
            notes=(f"matched MoE directory id {best['moe_school_id']} ({best['school']}, score {score:.2f})"
                   if best else "")))
    for m in moe:
        if m["moe_school_id"] in used:
            continue
        atoll_name = "Male' City" if "Male" in (m["atoll"] or "") else m["atoll"]
        out.append(dict(
            institution=m["school"], type="school", campus="", island=m["island"], atoll=atoll_name,
            levels_offered="", enrolment=m["students"], year="2025 (MoE directory, updated 23/05/2025)",
            source_url=m["source_url"], sector="government", atoll_code=NAME2CODE.get(atoll_name, m["atoll_code"]),
            teachers=m["teachers"], enrolment_2025_moe_dir=m["students"], highest_grade="", offers_grade_11_12="",
            notes="MoE directory school not matched to 2022-23 school table" +
                  ("; temporarily closed" if m["status"] != "open" else "")))
    cols = ["institution", "type", "campus", "island", "atoll", "levels_offered", "enrolment", "year", "source_url",
            "sector", "atoll_code", "teachers", "enrolment_2025_moe_dir", "highest_grade", "offers_grade_11_12", "notes"]
    f = E / "institutions_master.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    n_s = sum(1 for r in out if r["year"] == "2022-2023")
    n_m = sum(1 for r in out if r["year"] == "2022-2023" and r["sector"] == "government")
    print(f"{f}: {len(out)} rows; schools(2022-23)={n_s}, matched to MoE directory={n_m}, "
          f"unmatched directory rows={sum(1 for r in out if r['year'].startswith('2025'))}")


if __name__ == "__main__":
    main()
