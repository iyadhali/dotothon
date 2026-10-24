"""Build a tidy campus-level CSV from the MoE/MoHE "Register of Higher Education and Training
Institutions in Maldives" (Dhaftharu - Registered Colleges and Institutes), Oct 2026 edition.

The PDF's English columns were transcribed (Dhivehi glyphs are not extractable); see
data/external/education/moe_registered_colleges/1791106952537-Dhaftharu-Registered_Colleges_and_Institutes.pdf

Output: data/external/education/moe_registered_colleges/registered_hei_campuses_2026.csv

Usage: python -I scripts/edu_build_registry.py
"""
import csv
from pathlib import Path

OUT = Path(r"C:\Users\user\Music\Datathon\data\external\education\moe_registered_colleges")
SRC = ("https://www.moe.gov.mv/storage/files/resources/"
       "1791106952537-Dhaftharu-%20Registered%20Colleges%20and%20Institutes%20(1).pdf")
ATOLL = {"HA": "Haa Alifu", "HDh": "Haa Dhaalu", "Sh": "Shaviyani", "N": "Noonu", "R": "Raa", "B": "Baa",
         "Lh": "Lhaviyani", "K": "Kaafu", "AA": "Alifu Alifu", "ADh": "Alifu Dhaalu", "V": "Vaavu",
         "M": "Meemu", "F": "Faafu", "Dh": "Dhaalu", "Th": "Thaa", "L": "Laamu", "GA": "Gaafu Alifu",
         "GDh": "Gaafu Dhaalu", "Gn": "Gnaviyani", "S": "Seenu", "": ""}

# (institution, category, sector, registration_no, [(campus, atoll_code, island), ...])
U = "University"; C = "College"; I = "Institute"
DATA = [
    ("The Maldives National University", U, "Public", "", [
        ("Kulhudhuffushi Campus", "HDh", "Kulhudhuffushi"), ("Male' Campus", "K", "Male'"),
        ("Gan Campus", "L", "Gan"), ("Thinadhoo Campus", "GDh", "Thinadhoo"), ("Hithadhoo Campus", "S", "Hithadhoo"),
        ("Ungoofaaru Outreach Centre", "R", "Ungoofaaru"), ("Ihavandhoo Outreach Centre", "HA", "Ihavandhoo"),
        ("Kudahuvadhoo Outreach Centre", "Dh", "Kudahuvadhoo")]),
    ("Islamic University of Maldives", U, "Public", "", [
        ("Male' Main Campus (not listed separately in register)", "K", "Male'"),
        ("Naifaru IUM Campus", "Lh", "Naifaru"), ("Fuvahmulah IUM Campus", "Gn", "Fuvahmulah"),
        ("Meedhoo IUM Campus (Addu)", "S", "Meedhoo"), ("Fonadhoo IUM Campus", "L", "Fonadhoo"),
        ("Ungoofaaru IUM Campus", "R", "Ungoofaaru"), ("Thinadhoo IUM Campus", "GDh", "Thinadhoo"),
        ("Maradhoo-Feydhoo IUM Campus (Addu)", "S", "Maradhoo-Feydhoo"),
        ("Hulhudhuffaaru Outreach Centre", "R", "Hulhudhuffaaru"), ("Maamigili Outreach Centre", "ADh", "Maamigili"),
        ("Dhidhdhoo Outreach Centre", "HA", "Dhidhdhoo"), ("Kulhudhuffushi Outreach Centre", "HDh", "Kulhudhuffushi"),
        ("Kudahuvadhoo Outreach Centre", "Dh", "Kudahuvadhoo"), ("Maafaru Outreach Centre", "N", "Maafaru"),
        ("Maafushi Outreach Centre", "K", "Maafushi"), ("Manadhoo Outreach Centre", "N", "Manadhoo"),
        ("Funadhoo Outreach Centre", "Sh", "Funadhoo"), ("Hoadehdhoo Outreach Centre", "GDh", "Hoadedhdhoo"),
        ("Gemanafushi Outreach Centre", "GA", "Gemanafushi"), ("Madaveli Outreach Centre", "GDh", "Madaveli"),
        ("Vaadhoo Outreach Centre", "GDh", "Vaadhoo"), ("Keyodhoo Outreach Centre", "V", "Keyodhoo"),
        ("Eydhafushi Outreach Centre", "B", "Eydhafushi"), ("Hithadhoo Outreach Centre", "S", "Hithadhoo")]),
    ("Villa College", C, "Private", "475-PP/B/2023/01", [
        ("QI Campus (Main Campus)", "K", "Male'"), ("Naifaru Campus", "Lh", "Naifaru"),
        ("Kulhudhuffushi Campus", "HDh", "Kulhudhuffushi"), ("Meedhoo Campus", "R", "Meedhoo"),
        ("Mahibadhoo Campus", "ADh", "Mahibadhoo"), ("Gan Campus", "L", "Gan"), ("Hithadhoo Campus", "S", "Hithadhoo"),
        ("Eydhafushi Campus", "B", "Eydhafushi"), ("Kudahuvadhoo Campus", "Dh", "Kudahuvadhoo"),
        ("Muli Campus", "M", "Muli"), ("Villingili Campus", "GA", "Villingili"), ("Dhihdhoo Campus", "HA", "Dhidhdhoo"),
        ("Nilandhoo Campus", "F", "Nilandhoo"), ("Ungoofaaru Campus", "R", "Ungoofaaru"),
        ("Veymandoo Campus", "Th", "Veymandoo"), ("Thinadhoo Campus", "GDh", "Thinadhoo")]),
    ("Clique College", C, "Private", "475-PP/B/2023/02", [("Main Campus", "K", "Male'")]),
    ("Cyryx College", C, "Private", "475-PP/B/2023/04", [("Main Campus", "K", "Male'"), ("Galolhu Campus", "K", "Male'")]),
    ("Mandhu College", C, "Private", "166/A-5/2013/03", [("Main Campus", "K", "Male'")]),
    ("MAPS College", C, "Private", "475-PP/B/2022/02", [("Main Campus", "K", "Male'")]),
    ("Avid College", C, "Private", "475-PP/B/2023/05", [
        ("Diamond Campus", "K", "Male'"), ("Ruby Campus", "K", "Male'"), ("Thinadhoo Campus", "GDh", "Thinadhoo")]),
    ("Maldives Business School", C, "Private", "475-PP/B/2022/03", [("Main Campus", "K", "Male'")]),
    ("MIANZ College (formerly MI College)", C, "Private", "475-PP/B/2024/01", [
        ("Main Campus", "K", "Male'"), ("Kulhudhuffushi Campus", "HDh", "Kulhudhuffushi"),
        ("Hulhumale' Campus", "K", "Hulhumale'"), ("Addu Campus", "S", "Addu City (island not stated)"),
        ("Dhuvaafaru Campus", "R", "Dhuvaafaru"), ("Fuvahmulah Campus", "Gn", "Fuvahmulah")]),
    ("Zikura International College", C, "Private", "475-PP/B/2022/01", [("Male' Campus", "K", "Male'")]),
    ("Maldives Institute of Technology", C, "Private", "475-PP/B/2023/03", [
        ("MIT Main Campus", "K", "Male'"), ("MIT Hulhumale' Campus", "K", "Hulhumale'"),
        ("MIT Refrigeration and Air-conditioning Lab Campus", "K", "Male'"), ("MIT Annex Engineering Campus", "K", "Male'")]),
    ("National College of Policing and Law Enforcement", C, "Public", "475-PP/B-171/2024/02", [
        ("Hithadhoo Campus (Main Campus)", "S", "Hithadhoo"), ("Male' Campus", "K", "Male'"), ("Vaanee Campus", "Dh", "Vaanee")]),
    ("College of Defence and Security Studies", C, "Public", "475-PP/B-28/2025/01", [
        ("Main Campus", "K", "Male'"), ("Maafilaafushi Campus", "Lh", "Maafilaafushi"), ("Girifushi Campus", "K", "Girifushi"),
        ("Kahdhoo Campus", "L", "Kahdhoo"), ("Villimale' Campus", "K", "Villimale'"), ("Kihaadhoo Campus", "B", "Kihaadhoo"),
        ("Gan Campus", "S", "Gan")]),
    # Government institutes
    ("Maldives Polytechnic", I, "Public (TVET)", "166-DHE/A-1/2010/49", [("Main (location not stated in register)", "", "")]),
    ("Maldives National Institute of Sports", I, "Public", "475-PP/A-141/2024/02", [("", "", "")]),
    ("Centre for Customs and Excise Studies", I, "Public", "475-PP/A-14/2023/04", [("", "", "")]),
    ("Institute of Maldives Immigration", I, "Public", "475-PP/A-94/2024/09", [("", "", "")]),
    ("National Institute of Education", I, "Public", "475-PP/A-451/2023/08", [("", "", "")]),
    ("National Centre for the Holy Quran", I, "Public", "475-PP/A-160/2024/08", [
        ("Main", "", ""), ("Dhihdhoo Gofi", "HA", "Dhidhdhoo"), ("Utheemu Gofi", "HA", "Utheemu"),
        ("Uligamu Gofi", "HA", "Uligamu"), ("Vaikaradhoo Gofi", "HDh", "Vaikaradhoo"), ("Maduvvaree Gofi", "R", "Maduvvaree"),
        ("Rasmaadhoo Gofi", "R", "Rasmaadhoo"), ("Hinnavaru Gofi", "Lh", "Hinnavaru"), ("Huraa Gofi", "K", "Huraa"),
        ("Himmafushi Gofi", "K", "Himmafushi"), ("Maafushi Gofi", "K", "Maafushi"),
        ("Hulhumale' (Phase 1) Gofi", "K", "Hulhumale'"), ("Veymandoo Gofi", "Th", "Veymandoo"),
        ("Dhandhoo Gofi", "GA", "Dhaandhoo"), ("Hithadhoo Gofi", "S", "Hithadhoo")]),
    ("Civil Service Training Institute", I, "Public", "475-PP/A-188/2023/01", [("", "", "")]),
    ("Maldives Monetary Authority Training Institute", I, "Public", "475-PP/A-98/2024/04", [("", "", "")]),
    ("Port Training Centre", I, "Public", "475-PP/A-113/2024/01", [("", "", "")]),
    ("Marine Research and Higher Education Centre (Univ. Milano-Bicocca)", I, "Public/foreign outpost",
     "166/A-6/2016/08", [("MaRHE Centre", "F", "Magoodhoo")]),
    ("Aviation Institute of Maldives", I, "Public", "475-PP/A-116/2022/01", [("", "", "")]),
    ("Maldives Fisheries Training Institute", I, "Public", "475-PP/A-30/2023/05", [("", "", "")]),
    ("Institute for Correctional Studies", I, "Public", "475-PP/A-167/2024/07", [("", "", "")]),
    ("National Institute for Research and Addiction Studies", I, "Public", "475-PP/A-434/2024/03", [("", "", "")]),
    ("Maldives Media Institute", I, "Public", "475-PP/A-PSM/2023/10", [("", "", "")]),
    ("Foreign Service Institute of Maldives", I, "Public", "475-PP/A-25/2023/09", [("", "", "")]),
    ("Maldives Tax Academy", I, "Public", "475-PP/A-220/2024/11", [("", "", "")]),
    ("Institute of Audit and Assurance", I, "Public", "475-PP/A-7/2024/10", [("", "", "")]),
    ("National Healthcare Academy", I, "Public", "475-PP/A-13/2022/04", [("", "", "")]),
    ("Public Finance Institute", I, "Public", "475-PP/A-13/2022/03", [("", "", "")]),
    ("Maldivian Aviation Academy", I, "Public", "475-PP/A-IAS/2025/04", [("", "", "")]),
    ("Maldives Institute for Local Governance", I, "Public", "475-PP/A-221/2022/02", [("", "", "")]),
    ("STO Training Institute", I, "Public (SOE)", "475-PP/A-60/2023/03", [("", "", "")]),
    ("Fenaka Institute for Training and Research", I, "Public (SOE)", "475-PP/A-FNK/2023/06", [("", "", "")]),
    ("Maldives National Anti-Corruption Academy", I, "Public", "475-PP/A-123/2023/02", [("", "", "")]),
    ("BCC Training Institute", I, "Public (SOE)", "475-PP/A-101/2023/07", [("", "", "")]),
    ("HDC Training Institute", I, "Public (SOE)", "475-PP/A-161/2024/12", [("", "", "")]),
    ("National Statistical Capacity Development & Research Centre", I, "Public", "475-PP/A-457/2024/13", [("", "", "")]),
    ("Prosecutor General's Academy", I, "Public", "475-PP/A-196/2025/01", [("", "", "")]),
    ("BML Academy", I, "Public (SOE)", "475-PP/A-BML/2025/02", [("", "", "")]),
    ("Future Institute", I, "Public (SOE)", "475-PP/A-TMC/2025/03", [("", "", "")]),
    # Foreign institutes
    ("Institute of Islamic & Arabic Sciences in Maldives", I, "Foreign", "475-PP/D/2025/01", [("", "", "")]),
    ("Zenith Aviation Academy", I, "Foreign", "475-PP/I/2025/01", [("", "", "")]),
]
# Private institutes (registered; the register gives outreach centres only where they exist)
PRIVATE_INST = [
    ("Centre for Information Technology Management", "475-PP/A/2024/07"),
    ("The Language Learning Centre", "22-ER/7/T-10/2000/30"), ("Institute of Logic and Technology", "475-PP/A/2023/16"),
    ("Astral Institute", "475-PP/A/2022/11"), ("Ixcel Institute for Professional Studies", "475-PP/A/2024/03"),
    ("Bina Institute of Higher Education", "475-PP/A/2023/02"), ("Manfaa Institute for Training", "475-PP/A/2023/10"),
    ("Everyone's Institute of Higher Education", "475-PP/A/2022/17"),
    ("Shafia Institute of Health - ADK Hospital", "475-PP/A/2022/31"), ("Maldives Music and Art Centre", "475-PP/A/2024/06"),
    ("Island Institute of Tertiary Education", "475-PP/A/2022/32"),
    ("Efes Institute of Cake Decorations and Art", "475-PP/A/2022/33"), ("Civeng Training Centre", "475-PP/A/2022/23"),
    ("Male' Fitness Academy", "475-PP/A/2023/15"), ("Absolute Academy", "475-PP/A/2022/39"),
    ("Gage Training Institute", "475-PP/A/2023/04"), ("Excel Learning Center", "475-PP/A/2022/36"),
    ("Haf Tailors Training Centre", "475-PP/A/2023/01"), ("Islanders Institute of Applied Sciences", "475-PP/A/2022/12"),
    ("Institute of Quranic Studies", "475-PP/A/2023/07"), ("Institute of Professional Education", "475-PP/A/2025/02"),
    ("Eupheus Collegiate", "475-PP/A/2022/03"), ("Kazu Institute", "475-PP/A/2024/08"),
    ("Institute of Quran and Sunnah", "475-PP/A/2022/18"), ("Hulhumale' Sports School", "475-PP/A/2024/10"),
    ("ILM Institute for Islamic Studies", "475-PP/A/2022/16"), ("Maldives Training Institute", "475-PP/A/2023/13"),
    ("Horizon International Academy", "475-PP/A/2022/26"),
    ("Academy of International Maritime and Management Studies", "475/PP/A/2022/27"),
    ("Dhives Institute", "475-PP/A/2023/06"), ("Maldives Institute of Nautical Sciences", "475-PP/A/2024/02"),
    ("Maldives Capacity Development and Governance Institute", "475-PP/A/2022/09"), ("Uyoon Institute", "475-PP/A/2022/13"),
    ("NES Institute", "475-PP/A/2022/26"), ("Markazu Noon", "475-PP/A/2024/09"),
    ("Technical and Vocational Education Centre", "475-PP/A/2023/12"), ("Dhaarul Quran Wassunnah", "475-PP/A/2022/10"),
    ("Ahmadhiyya Career Training Institute", "475/PP/A/2022/34"), ("Zaad Academy", "475-PP/A/2022/14"),
    ("Utiz Career Tech Institute", "475-PP/A/2022/20"), ("The Circle Academy", "475-PP/A/2022/05"),
    ("Thireehaa Institute", "475-PP/A/2022/30"), ("Modern Institute for Management and Science", "475-PP/A/2022/15"),
    ("Enfold Academy", "475-PP/A/2023/11"), ("UMYR Institute", "475-PP/A/2022/06"),
    ("Mathiveri Learning Centre", "475-PP/A/2023/03"), ("Festivo Institute of Art and Design", "475-PP/A/2023/09"),
    ("Academy of Ta'allam al' Quran", "475-PP/A/2022/38"), ("Institute for Applied Learning", "475-PP/A/2022/29"),
    ("Institute of Exercise & Sports", "475-PP/A/2022/08"), ("Riyan Training Institute", "475-PP/A/2024/01"),
    ("JLS Training Institute Maldives", "475-PP/A/2022/01"), ("Maritime Training Institute", "475-PP/A/2022/19"),
    ("Akuru Institute", "475-PP/A/2022/21"), ("Institute of Accounting and Business Studies", "475-PP/A/2022/25"),
    ("AICCET Training Center", "475-PP/A/2022/35"), ("Evove Academy", "475-PP/A/2023/05"),
    ("Institute for Quran and Islam", "475-PP/A/2023/08"), ("Rawdah Institute", "475-PP/A/2023/14"),
    ("Sustainable Development and Research Institute", "475-PP/A/2024/04"), ("Dharaja Academy", "475-PP/A/2024/05"),
    ("Maldivian Academy of Diving", "475-PP/A/2024/11"), ("Ocean Warriors Institute", "475-PP/A/2025/01"),
    ("ABC Academy", "475-PP/A/2025/10"), ("Bright Shine Institute", "475-PP/A/2025/03"),
    ("Alimas Institute", "475-PP/A/2025/04"), ("Ilaaj Institute", "475-PP/A/2025/05"),
    ("FEA Academy Maldives", "475-PP/A/2025/06"), ("A-Focus Academy", "475-PP/A/2025/07"),
    ("The Maldives Academy of Tourism and Hospitality", "475-PP/A/2025/08"), ("Faragu Academy", "475-PP/A/2025/09"),
    ("Sun Siyam Academy", "22-PP/A/2026/1"),
]
OUTREACH = {  # private institutes with outreach centres listed in the register
    "Island Institute of Tertiary Education": [("Villingili Outreach Centre", "GA", "Villingili"),
                                               ("Kulhudhuffushi Outreach Centre", "HDh", "Kulhudhuffushi")],
    "Eupheus Collegiate": [("Kulhudhuffushi Outreach Centre", "HDh", "Kulhudhuffushi"),
                           ("Maamigili Outreach Centre", "ADh", "Maamigili"), ("Landhoo Outreach Centre", "N", "Landhoo")],
    "ILM Institute for Islamic Studies": [("Hulhumale' Outreach Centre", "K", "Hulhumale'")],
}


def main():
    rows = []
    for inst, cat, sector, reg, campuses in DATA:
        for campus, a, isl in campuses:
            rows.append(dict(institution=inst, category=cat, sector=sector, registration_no=reg,
                             campus=campus or "(no campus listed)", campus_type=(
                                 "outreach centre" if "Outreach" in campus else
                                 "quran centre (gofi)" if "Gofi" in campus else
                                 "main campus" if ("Main" in campus or (campus.startswith("Male'") and cat != I)) else
                                 "campus" if campus else "not stated"),
                             atoll_code=a, atoll=ATOLL.get(a, a), island=isl,
                             location_stated=bool(isl), source_url=SRC))
    for inst, reg in PRIVATE_INST:
        rows.append(dict(institution=inst, category=I, sector="Private", registration_no=reg,
                         campus="(head office; location not stated in register)", campus_type="not stated",
                         atoll_code="", atoll="", island="", location_stated=False, source_url=SRC))
        for campus, a, isl in OUTREACH.get(inst, []):
            rows.append(dict(institution=inst, category=I, sector="Private", registration_no=reg, campus=campus,
                             campus_type="outreach centre", atoll_code=a, atoll=ATOLL[a], island=isl,
                             location_stated=True, source_url=SRC))
    f = OUT / "registered_hei_campuses_2026.csv"
    with open(f, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f, len(rows), "rows;", len({r['institution'] for r in rows}), "institutions;",
          sum(r["location_stated"] for r in rows), "with location")


if __name__ == "__main__":
    main()
