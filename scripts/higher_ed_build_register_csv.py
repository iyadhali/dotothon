"""Build a tidy CSV of higher-education campuses / outreach centres by island from the
Ministry of Education (Higher Education) "Register of Higher Education and Training
Institutions in Maldives" PDF (hand transcribed from the English column of the PDF;
see scripts/higher_ed_dump_register.py for the text dump used).

Source PDF:
https://www.moe.gov.mv/storage/files/resources/1791106952537-Dhaftharu-%20Registered%20Colleges%20and%20Institutes%20(1).pdf
(linked from https://www.moe.gov.mv/en/reports-and-publications)

Usage: python -I scripts/higher_ed_build_register_csv.py <out_csv>
"""
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")

SRC = ("https://www.moe.gov.mv/storage/files/resources/"
       "1791106952537-Dhaftharu-%20Registered%20Colleges%20and%20Institutes%20(1).pdf")
MNU = "https://mnu.edu.mv/"

ATOLLS = {
    "HA": "Haa Alifu", "HDh": "Haa Dhaalu", "Sh": "Shaviyani", "N": "Noonu", "R": "Raa",
    "B": "Baa", "Lh": "Lhaviyani", "K": "Kaafu", "AA": "Alifu Alifu", "ADh": "Alifu Dhaalu",
    "V": "Vaavu", "M": "Meemu", "F": "Faafu", "Dh": "Dhaalu", "Th": "Thaa", "L": "Laamu",
    "GA": "Gaafu Alifu", "GDh": "Gaafu Dhaalu", "Gn": "Gnaviyani", "S": "Seenu",
}
# Malé City islands are administratively Kaafu (K.) in the register's notation
MALE_CITY = {"Malé", "Hulhumalé", "Vilimalé"}
# island spellings normalised here -> spelling used in the register
AS_WRITTEN = {
    "Malé": "Male'", "Hulhumalé": "Hulhumale'", "Vilimalé": "Villimale'",
    "Hulhudhuffaaru": "Hulhudhuhfaaru", "Dhidhdhoo": "Dhihdhoo", "Kulhudhuffushi": "Kulhudhuhfushi / Kulhudhuffushi",
    "Hoadedhdhoo": "Hoadehdhoo", "Maduvvari": "Maduvaree", "Rasmaadhoo": "Rasmadhoo",
    "Himmafushi": "Hinmafushi", "Dhaandhoo": "Dhandhoo", "Maradhoo-Feydhoo": "Maradhoo Feydhoo",
    "Meedhoo": "Meedhoo (Addu Meedhoo for S.)",
}

# (institution, institution_type, campus_name, campus_type, atoll_code, island,
#  registration_number, page, notes)
U, PC, GC, PI, GI, FI = ("university", "private_college", "government_college",
                         "private_institute", "government_institute", "foreign_institute")
ROWS = []


def add(inst, itype, campus, ctype, ac, island, reg, page, notes=""):
    ROWS.append((inst, itype, campus, ctype, ac, island, reg, page, notes))


# ---- Universities (pp.1-3); registration number shown as '-' in register
mnu = "Maldives National University"
add(mnu, U, "Male' Campus", "main_campus", "K", "Malé", "", 1,
    "Main campus; register lists campuses under the university without a 'main' flag")
for ac, isl in [("HDh", "Kulhudhuffushi"), ("L", "Gan"), ("GDh", "Thinadhoo"), ("S", "Hithadhoo")]:
    add(mnu, U, f"{ac}. {isl} Campus", "campus", ac, isl, "", 1)
for ac, isl in [("R", "Ungoofaaru"), ("HA", "Ihavandhoo"), ("Dh", "Kudahuvadhoo")]:
    add(mnu, U, f"{ac}. {isl} Outreach Centre", "outreach_centre", ac, isl, "", 1)

ium = "Islamic University of Maldives"
add(ium, U, "Male' (main campus)", "main_campus", "K", "Malé", "", 2,
    "Main campus not itemised in register; IUM HQ is in Malé (added for completeness)")
for ac, isl, nm in [("Lh", "Naifaru", "Lh. Naifaru IUM Campus"),
                    ("Gn", "Fuvahmulah", "Gn. Fuvahmulah IUM Campus"),
                    ("S", "Meedhoo", "Addu Meedhoo IUM Campus"),
                    ("L", "Fonadhoo", "L. Fonadhoo IUM Campus"),
                    ("R", "Ungoofaaru", "R. Ungoofaaru IUM Campus"),
                    ("GDh", "Thinadhoo", "GDh. Thinadhoo IUM Campus"),
                    ("S", "Maradhoo-Feydhoo", "Maradhoo Feydhoo IUM Campus")]:
    add(ium, U, nm, "campus", ac, isl, "", 2)
for ac, isl, pg in [("R", "Hulhudhuffaaru", 2), ("ADh", "Maamigili", 2), ("HA", "Dhidhdhoo", 2),
                    ("HDh", "Kulhudhuffushi", 2), ("Dh", "Kudahuvadhoo", 2), ("N", "Maafaru", 2),
                    ("K", "Maafushi", 2), ("N", "Manadhoo", 2), ("Sh", "Funadhoo", 2),
                    ("GDh", "Hoadedhdhoo", 2), ("GA", "Gemanafushi", 2), ("GDh", "Madaveli", 3),
                    ("GDh", "Vaadhoo", 3), ("V", "Keyodhoo", 3), ("B", "Eydhafushi", 3),
                    ("S", "Hithadhoo", 3)]:
    add(ium, U, f"{ac}. {isl} Outreach Centre", "outreach_centre", ac, isl, "", pg)

# ---- Private colleges (pp.4-6)
vc = "Villa College"
add(vc, PC, "QI Campus (Main Campus)", "main_campus", "K", "Malé", "475-PP/B/2023/01", 4)
for ac, isl, pg in [("Lh", "Naifaru", 4), ("HDh", "Kulhudhuffushi", 4), ("R", "Meedhoo", 4),
                    ("ADh", "Mahibadhoo", 4), ("L", "Gan", 4), ("S", "Hithadhoo", 4),
                    ("B", "Eydhafushi", 4), ("Dh", "Kudahuvadhoo", 4), ("M", "Muli", 4),
                    ("GA", "Villingili", 4), ("HA", "Dhidhdhoo", 4), ("F", "Nilandhoo", 4),
                    ("R", "Ungoofaaru", 5), ("Th", "Veymandoo", 5), ("GDh", "Thinadhoo", 5)]:
    add(vc, PC, f"{isl} Campus", "campus", ac, isl, "475-PP/B/2023/01", pg)
add("Clique College", PC, "Main Campus", "main_campus", "K", "Malé", "475-PP/B/2023/02", 5)
add("Cyryx College", PC, "Main Campus", "main_campus", "K", "Malé", "475-PP/B/2023/04", 5)
add("Cyryx College", PC, "Galolhu Campus", "campus", "K", "Malé", "475-PP/B/2023/04", 5)
add("Mandhu College", PC, "Main Campus", "main_campus", "K", "Malé", "166/A-5/2013/03", 5)
add("MAPS College", PC, "Main Campus", "main_campus", "K", "Malé", "475-PP/B/2022/02", 5)
add("Avid College", PC, "Diamond Campus", "main_campus", "K", "Malé", "475-PP/B/2023/05", 5)
add("Avid College", PC, "Ruby Campus", "campus", "K", "Malé", "475-PP/B/2023/05", 5)
add("Avid College", PC, "Thinadhoo Campus", "campus", "GDh", "Thinadhoo", "475-PP/B/2023/05", 5)
add("Maldives Business School", PC, "Main Campus", "main_campus", "K", "Malé", "475-PP/B/2022/03", 5)
mz = "MIANZ College"
add(mz, PC, "Main Campus", "main_campus", "K", "Malé", "475-PP/B/2024/01", 5)
add(mz, PC, "Kulhudhuhfushi Campus", "campus", "HDh", "Kulhudhuffushi", "475-PP/B/2024/01", 5)
add(mz, PC, "Hulhumale' Campus", "campus", "K", "Hulhumalé", "475-PP/B/2024/01", 5,
    "Register gives location as 'K. Male''; campus name indicates Hulhumalé")
add(mz, PC, "Addu Campus", "campus", "S", "Hithadhoo", "475-PP/B/2024/01", 6,
    "Register gives 'Addu City' only; island assumed Hithadhoo (Addu City capital) - verify")
add(mz, PC, "Dhuvaafaru Campus", "campus", "R", "Dhuvaafaru", "475-PP/B/2024/01", 6)
add(mz, PC, "Fuvahmulah Campus", "campus", "Gn", "Fuvahmulah", "475-PP/B/2024/01", 6)
add("Zikura International College", PC, "Male' Campus", "main_campus", "K", "Malé", "475-PP/B/2022/01", 6)
mit = "Maldives Institute of Technology"
add(mit, PC, "MIT Main Campus", "main_campus", "K", "Malé", "475-PP/B/2023/03", 6)
add(mit, PC, "MIT Hulhumale' Campus", "campus", "K", "Hulhumalé", "475-PP/B/2023/03", 6)
add(mit, PC, "MIT Refrigeration and Air conditioning Lab Campus", "campus", "K", "Malé", "475-PP/B/2023/03", 6)
add(mit, PC, "MIT Annex Engineering Campus", "campus", "K", "Malé", "475-PP/B/2023/03", 6)

# ---- Government colleges (p.7)
nc = "National College of Policing and Law Enforcement"
add(nc, GC, "Hithadhoo Campus (Main Campus)", "main_campus", "S", "Hithadhoo", "475-PP/B-171/2024/02", 7,
    "Register gives 'Addu City'; campus name says Hithadhoo")
add(nc, GC, "Male' Campus", "campus", "K", "Malé", "475-PP/B-171/2024/02", 7)
add(nc, GC, "Vaanee Campus", "campus", "Dh", "Vaanee", "475-PP/B-171/2024/02", 7)
cd = "College of Defence and Security Studies"
add(cd, GC, "Main Campus", "main_campus", "K", "Malé", "475-PP/B-28/2025/01", 7)
for ac, isl in [("Lh", "Maafilaafushi"), ("K", "Girifushi"), ("L", "Kahdhoo"),
                ("K", "Vilimalé"), ("B", "Kihaadhoo"), ("S", "Gan")]:
    note = "Military/training island; not an inhabited island" if isl in ("Girifushi",) else ""
    add(cd, GC, f"{isl} Campus", "campus", ac, isl, "475-PP/B-28/2025/01", 7, note)

# ---- Private institutes (pp.8-13): (name, reg, page, [(ac, island, centre_name)])
NOLOC = ("Location of main premises not stated in register "
         "(most private institutes are Malé-based) - island left blank")
PRIV = [
    ("Centre for Information Technology Management", "475-PP/A/2024/07", 8),
    ("The Language Learning Centre", "22-ER/7/T-10/2000/30", 8),
    ("Institute of Logic and Technology", "475-PP/A/2023/16", 8),
    ("Astral Institute", "475-PP/A/2022/11", 8),
    ("Ixcel Institute for Professional Studies", "475-PP/A/2024/03", 8),
    ("Bina Institute of Higher Education", "475-PP/A/2023/02", 8),
    ("Manfaa Institute for Training", "475-PP/A/2023/10", 8),
    ("Everyone's institute of Higher Education", "475-PP/A/2022/17", 8),
    ("Shafia Institute of Health-ADK hospital", "475-PP/A/2022/31", 8),
    ("Maldives Music and Art Centre", "475-PP/A/2024/06", 8),
    ("Island Institute of Tertiary Education", "475-PP/A/2022/32", 8),
    ("Efes Institute of Cake Decorations and Art", "475-PP/A/2022/33", 9),
    ("Civeng Training Centre", "475-PP/A/2022/23", 9),
    ("Male' Fitness Academy", "475-PP/A/2023/15", 9),
    ("Absolute Academy", "475-PP/A/2022/39", 9),
    ("Gage training Institute", "475-PP/A/2023/04", 9),
    ("Excel Learning Center", "475-PP/A/2022/36", 9),
    ("Haf Tailors Training Centre", "475-PP/A/2023/01", 9),
    ("Islanders Institute of Applied Sciences", "475-PP/A/2022/12", 9),
    ("Institute of Quranic Studies", "475-PP/A/2023/07", 9),
    ("Institute of professional Education", "475-PP/A/2025/02", 9),
    ("Eupheus Collegiate", "475-PP/A/2022/03", 9),
    ("Kazu Institute", "475-PP/A/2024/08", 10),
    ("Institute of Quran and Sunnah", "475-PP/A/2022/18", 10),
    ("Hulhumale' Sports School", "475-PP/A/2024/10", 10),
    ("ILM Institute for Islamic Studies", "475-PP/A/2022/16", 10),
    ("Maldives Training Institute", "475-PP/A/2023/13", 10),
    ("Horizon International Academy", "475-PP/A/2022/26", 10),
    ("Academy of International Maritime and Management Studies", "475/PP/A/2022/27", 10),
    ("Dhives Institute", "475-PP/A/2023/06", 10),
    ("Maldives Institute of Nautical Sciences", "475-PP/A/2024/02", 10),
    ("Maldives Capacity Development and Governance Institute", "475-PP/A/2022/09", 10),
    ("Uyoon Institute", "475-PP/A/2022/13", 10),
    ("NES Institute", "475-PP/A/2022/26", 11),
    ("Markazu Noon", "475-PP/A/2024/09", 11),
    ("Technical and Vocational Education Centre", "475-PP/A/2023/12", 11),
    ("Dhaarul Quran Wassunnah", "475-PP/A/2022/10", 11),
    ("Ahmadhiyya Career Training Institute", "475/PP/A/2022/34", 11),
    ("Zaad Academy", "475-PP/A/2022/14", 11),
    ("Utiz Career tech Institute", "475-PP/A/2022/20", 11),
    ("The Circle Academy", "475-PP/A/2022/05", 11),
    ("Thireehaa Institute", "475-PP/A/2022/30", 11),
    ("Modern Institute for Management and science", "475-PP/A/2022/15", 11),
    ("Enfold Academy", "475-PP/A/2023/11", 11),
    ("UMYR Institute", "475-PP/A/2022/06", 11),
    ("Mathiveri Learning Centre", "475-PP/A/2023/03", 11),
    ("Festivo Institute of Art and Design", "475-PP/A/2023/09", 11),
    ("Academy of Ta'allam al' Quran", "475-PP/A/2022/38", 11),
    ("Institute for Applied Learning", "475-PP/A/2022/29", 11),
    ("Institute of Exercise & sports", "475-PP/A/2022/08", 12),
    ("Riyan Training Institute", "475-PP/A/2024/01", 12),
    ("JLS Training Institute Maldives", "475-PP/A/2022/01", 12),
    ("Maritime Training Institute", "475-PP/A/2022/19", 12),
    ("Akuru Institute", "475-PP/A/2022/21", 12),
    ("Institute of Accounting and Business Studies", "475-PP/A/2022/25", 12),
    ("AICCET Training Center", "475-PP/A/2022/35", 12),
    ("Evove Academy", "475-PP/A/2023/05", 12),
    ("Institute for Quran and Islam", "475-PP/A/2023/08", 12),
    ("Rawdah Institute", "475-PP/A/2023/14", 12),
    ("Sustainable Development and Research Institute", "475-PP/A/2024/04", 12),
    ("Dharaja Academy", "475-PP/A/2024/05", 12),
    ("Maldivian Academy of Diving", "475-PP/A/2024/11", 12),
    ("Ocean Warriors Institute", "475-PP/A/2025/01", 12),
    ("ABC Academy", "475-PP/A/2025/10", 12),
    ("Bright Shine Institute", "475-PP/A/2025/03", 13),
    ("Alimas Institute", "475-PP/A/2025/04", 13),
    ("Ilaaj Institute", "475-PP/A/2025/05", 13),
    ("FEA Academy Maldives", "475-PP/A/2025/06", 13),
    ("A - Focus Academy", "475-PP/A/2025/07", 13),
    ("The Maldives Academy of Tourism and Hospitality", "475-PP/A/2025/08", 13),
    ("Faragu Academy", "475-PP/A/2025/09", 13),
    ("Sun Siyam Academy", "22-PP/A/2026/1", 13),
]
PRIV_OC = {
    "Island Institute of Tertiary Education": [("GA", "Villingili", 8), ("HDh", "Kulhudhuffushi", 9)],
    "Eupheus Collegiate": [("HDh", "Kulhudhuffushi", 9), ("ADh", "Maamigili", 10), ("N", "Landhoo", 10)],
    "ILM Institute for Islamic Studies": [("K", "Hulhumalé", 10)],
}
for name, reg, pg in PRIV:
    hint = ""
    island = ""
    ac = ""
    if name == "Hulhumale' Sports School":
        ac, island, hint = "K", "Hulhumalé", "Island inferred from institution name, not stated in register"
    add(name, PI, "Main premises", "main_premises", ac, island, reg, pg, hint or NOLOC)
    for oac, oisl, opg in PRIV_OC.get(name, []):
        add(name, PI, f"{oac}. {oisl} Outreach Centre", "outreach_centre", oac, oisl, reg, opg)

# ---- Government institutes (pp.14-19)
GOV = [
    ("Maldives Polytechnic", "166-DHE/A-1/2010/49", 14),
    ("Maldives National Institute of Sports", "475-PP/A-141/2024/02", 14),
    ("Centre for Customs and excise studies", "475-PP/A-14/2023/04", 14),
    ("Institute of Maldives Immigration", "475-PP/A-94/2024/09", 14),
    ("National Institute of Education", "475-PP/A-451/2023/08", 14),
    ("National Centre for the Holy Quran", "475-PP/A-160/2024/08", 14),
    ("Civil Service Training Institute", "475-PP/A-188/2023/01", 16),
    ("Maldives Monetary Authority Training Institute", "475-PP/A-98/2024/04", 16),
    ("Port Training Centre", "475-PP/A-113/2024/01", 16),
    ("Marine Research and Higher Education Centre (outpost of University of Milano-Bicocca)", "166/A-6/2016/08", 17),
    ("Aviation Institute of Maldives", "475-PP/A-116/2022/01", 17),
    ("Maldives Fisheries Training Institute", "475-PP/A-30/2023/05", 17),
    ("Institute for Correctional Studies", "475-PP/A-167/2024/07", 17),
    ("National Institute for Research and Addiction Studies", "475-PP/A-434/2024/03", 17),
    ("Maldives Media Institute", "475-PP/A-PSM/2023/10", 17),
    ("The Foreign Service Institute of Maldives", "475-PP/A-25/2023/09", 17),
    ("Maldives Tax Academy", "475-PP/A-220/2024/11", 17),
    ("Institute of Audit and Assurance", "475-PP/A-7/2024/10", 17),
    ("National Healthcare Academy", "475-PP/A-13/2022/04", 18),
    ("Public Finance Institute", "475-PP/A-13/2022/03", 18),
    ("Maldivian Aviation Academy", "475-PP/A-IAS/2025/04", 18),
    ("Maldives Institute for local governance", "475-PP/A-221/2022/02", 18),
    ("STO training institute", "475-PP/A-60/2023/03", 18),
    ("Fenaka Institute for Training and Research", "475-PP/A-FNK/2023/06", 18),
    ("Maldives National Anti-Corruption Academy", "475-PP/A-123/2023/02", 18),
    ("BCC Training Institute", "475-PP/A-101/2023/07", 18),
    ("HDC Training Institute", "475-PP/A-161/2024/12", 18),
    ("National Statistical Capacity Development & Research Centre", "475-PP/A-457/2024/13", 18),
    ("Prosecutor General's Academy", "475-PP/A-196/2025/01", 18),
    ("BML Academy", "475-PP/A-BML/2025/02", 19),
    ("Future Institute", "475-PP/A-TMC/2025/03", 19),
]
GOFI = [("HA", "Dhidhdhoo", 14), ("HA", "Utheemu", 14), ("HA", "Uligamu", 14),
        ("HDh", "Vaikaradhoo", 15), ("R", "Maduvvari", 15), ("R", "Rasmaadhoo", 15),
        ("Lh", "Hinnavaru", 15), ("K", "Huraa", 15), ("K", "Himmafushi", 15), ("K", "Maafushi", 15),
        ("K", "Hulhumalé", 16), ("Th", "Veymandoo", 16), ("GA", "Dhaandhoo", 16), ("S", "Hithadhoo", 16)]
for name, reg, pg in GOV:
    note = NOLOC.replace("private institutes", "government institutes")
    if name == "Maldives Polytechnic":
        note += ("; register lists no outreach centres for Maldives Polytechnic (main campus is in Malé; "
                 "former regional RYVTC sites e.g. HDh. Kulhudhuffushi, S. Hithadhoo not listed)")
    if name.startswith("Marine Research"):
        note = "MaRHE Centre is on Dh. Magoodhoo (not stated in register; from general knowledge - verify)"
    add(name, GI, "Main premises", "main_premises", "", "", reg, pg, note)
    if name == "National Centre for the Holy Quran":
        for ac, isl, gpg in GOFI:
            extra = "Hulhumalé (Phase 1)" if isl == "Hulhumalé" else ""
            add(name, GI, f"National Centre for the Holy Quran - {ac}. {isl} Gofi", "branch_gofi",
                ac, isl, reg, gpg, extra)

# ---- Foreign institutes (p.20)
add("Institute of Islamic & Arabic Sciences in Maldives", FI, "Main premises", "main_premises", "", "",
    "475-PP/D/2025/01", 20, NOLOC.replace("private institutes", "institutes"))
add("Zenith Aviation Academy", FI, "Main premises", "main_premises", "", "",
    "475-PP/I/2025/01", 20, NOLOC.replace("private institutes", "institutes"))

out = sys.argv[1]
cols = ["institution", "institution_type", "campus_name", "campus_type", "atoll_code", "atoll",
        "island", "island_as_in_register", "male_city", "registration_number", "location_stated_in_register",
        "source_url", "source_page", "notes"]
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(cols)
    for inst, itype, campus, ctype, ac, island, reg, page, notes in ROWS:
        stated = "yes" if island else "no"
        if any(k in notes for k in ("inferred", "not itemised", "not stated in register", "assumed", "campus name")):
            stated = "inferred"
        if not island:
            stated = "no"
        w.writerow([inst, itype, campus, ctype, ac, ATOLLS.get(ac, ""), island, AS_WRITTEN.get(island, island),
                    "yes" if island in MALE_CITY else ("no" if island else ""),
                    reg, stated, SRC, page, notes])
print(len(ROWS), "rows ->", out)
