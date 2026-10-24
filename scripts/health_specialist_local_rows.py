"""Build specialist-service rows from LOCAL already-downloaded MoH sources:
  * MoH Surgery data 2022 & 2023 (Table 1.7: surgeries by atoll and facility type)
  * English-language organograms / census charts in hospital annual reports (2021-2023)

Writes rows in the specialist_services.csv schema.
Usage: python -I health_specialist_local_rows.py <OUT_CSV> [MHS2020_T1-16_workforce_by_atoll_profession_tidy.csv]
"""
import csv
import sys

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]

SURG22 = "https://health.gov.mv/storage/uploads/roOjr2qP/fg4ihibj.xlsx"
SURG23 = "https://health.gov.mv/storage/uploads/eY3GzxY3/2om420vh.xlsx"

# atoll -> (facility name, facility_type, island)
ATOLL_HOSP = {
    "HA": ("Haa Alifu Atoll Hospital", "atoll_hospital", "Dhidhdhoo"),
    "HDh": ("Kulhudhuffushi Regional Hospital", "regional_hospital", "Kulhudhuffushi"),
    "Sh": ("Shaviyani Atoll Hospital", "atoll_hospital", "Funadhoo"),
    "N": ("Noonu Atoll Hospital", "atoll_hospital", "Manadhoo"),
    "R": ("Ungoofaaru Regional Hospital", "regional_hospital", "Ungoofaaru"),
    "B": ("Baa Atoll Hospital", "atoll_hospital", "Eydhafushi"),
    "Lh": ("Lhaviyani Atoll Hospital", "atoll_hospital", "Naifaru"),
    "AA": ("Alifu Alifu Atoll Hospital", "atoll_hospital", "Rasdhoo"),
    "ADh": ("Alifu Dhaalu Atoll Hospital", "atoll_hospital", "Mahibadhoo"),
    "V": ("Vaavu Atoll Hospital", "atoll_hospital", "Felidhoo"),
    "M": ("Muli Regional Hospital", "regional_hospital", "Muli"),
    "F": ("Faafu Atoll Hospital", "atoll_hospital", "Nilandhoo"),
    "Dh": ("Dhaalu Atoll Hospital", "atoll_hospital", "Kudahuvadhoo"),
    "Th": ("Thaa Atoll Hospital", "atoll_hospital", "Veymandoo"),
    "L": ("Gan Regional Hospital", "regional_hospital", "Gan"),
    "GA": ("Gaafu Alifu Atoll Hospital", "atoll_hospital", "Villingili"),
    "GDh": ("Dr. Abdul Samad Memorial Hospital", "regional_hospital", "Thinadhoo"),
    "Gn": ("Fuvahmulah Hospital", "atoll_hospital", "Fuvahmulah"),
}

# Table 1.7 (major, minor) at atoll/regional hospital
S23 = {"AA": (14, 3), "ADh": (6, 47), "B": (52, 69), "Dh": (62, 35), "F": (35, 78), "GA": (37, 49),
       "GDh": (134, 222), "Gn": (61, 126), "HA": (61, 35), "HDh": (451, 302), "L": (156, 147),
       "Lh": (64, 539), "M": (31, 30), "N": (10, 14), "R": (183, 117), "Sh": (73, 68), "Th": (30, 58)}
S22 = {"AA": (7, 13), "ADh": (12, 44), "B": (33, 65), "Dh": (22, 23), "F": (64, 64), "GA": (38, 69),
       "GDh": (113, 178), "Gn": (66, 81), "HA": (38, 58), "HDh": (493, 325), "L": (119, 103),
       "Lh": (53, 68), "M": (15, 17), "N": (18, 34), "R": (216, 207), "Sh": (88, 100), "Th": (30, 51)}

rows = []


def add(**kw):
    r = {c: "" for c in COLS}
    r.update(kw)
    rows.append(r)


for at, (name, ftype, isl) in ATOLL_HOSP.items():
    if at in S23:
        mj, mn = S23[at]
        mj2, mn2 = S22[at]
        add(facility_name=name, operator_type="public", facility_type=ftype, island=isl, atoll=at,
            service_category="surgery",
            service_detail=f"operating theatre in use; {mj} major + {mn} minor surgeries in 2023 ({mj2}+{mn2} in 2022)",
            evidence=f"MoH Surgery data Table 1.7: atoll/regional hospital in {at} reported {mj} major / {mn} minor surgeries 2023",
            source_url=SURG23, source_date="2023",
            confidence="high" if mj >= 20 else "medium")
# Vaavu: zero surgeries both years
add(facility_name="Vaavu Atoll Hospital", operator_type="public", facility_type="atoll_hospital",
    island="Felidhoo", atoll="V", service_category="surgery",
    service_detail="NO surgery recorded 2022 or 2023 (gap; Vaavu absent from Table 1.7)",
    evidence="MoH Surgery data 2022/2023 Table 1.7 lists no surgeries for Vaavu; V surgery rate 0 per 1000 in 2023",
    source_url=SURG23, source_date="2023", confidence="medium")
# Addu
add(facility_name="Addu Equatorial Hospital", operator_type="public", facility_type="tertiary_hospital",
    island="Hithadhoo", atoll="S", service_category="surgery",
    service_detail="tertiary operating theatres; 490 major + 469 minor surgeries 2023 (332+353 in 2022)",
    evidence="MoH Surgery data Table 1.7/1.10: AEH classed Tertiary Hospital; S atoll tertiary 490 major/469 minor 2023",
    source_url=SURG23, source_date="2023", confidence="high")
add(facility_name="I.M.D.C Multi Speciality Hospital", operator_type="private", facility_type="private_hospital",
    island="Hithadhoo", atoll="S", service_category="surgery",
    service_detail="private hospital theatre; 8 major + 64 minor surgeries 2023",
    evidence="MoH Surgery data Table 1.7/1.10: IMDC 'Other hospital' S atoll 8 major/64 minor 2023",
    source_url=SURG23, source_date="2023", confidence="medium")
# Greater Male'
for name, op, ft, isl in [("Indira Gandhi Memorial Hospital (IGMH)", "public", "tertiary_hospital", "Male'"),
                          ("ADK Hospital", "private", "tertiary_hospital", "Male'"),
                          ("Tree Top Hospital", "private", "tertiary_hospital", "Hulhumale'")]:
    add(facility_name=name, operator_type=op, facility_type=ft, island=isl, atoll="MLE",
        service_category="surgery",
        service_detail="tertiary multi-speciality surgery (general, O&G, ortho, cardiothoracic, neuro, ENT, eye, urology, GI); Male' tertiary total 7705 major + 5971 minor 2023",
        evidence="MoH Surgery data 2023 Table 1.7/1.10: classed Tertiary Hospital; neurosurgery/GI surgery only in Greater Male' private+public",
        source_url=SURG23, source_date="2023", confidence="high")
for name, op, ft, isl in [("Hulhumale' Hospital", "public", "hospital", "Hulhumale'"),
                          ("Medica Hospital", "private", "private_hospital", "Male'"),
                          ("Senahiya Military Hospital", "military", "hospital", "Male'"),
                          ("Villimale' Hospital", "public", "hospital", "Villimale'")]:
    add(facility_name=name, operator_type=op, facility_type=ft, island=isl, atoll="MLE",
        service_category="surgery",
        service_detail="operating theatre; Greater Male' 'other hospitals' group 873 major + 1614 minor 2023",
        evidence="MoH Surgery data 2023 Table 1.10 lists facility as reporting surgeries ('Other hospital')",
        source_url=SURG23, source_date="2023", confidence="high")

# ---- annual report organograms (English pages) ----
KRH = "https://health.gov.mv/storage/uploads/0wNN3bwA/ldoamukt.pdf"
krh_units = [
    ("dialysis", "Dialysis Ward (nursing unit); nephrology consultant post"),
    ("icu", "ICU and CCU Ward"),
    ("surgery", "OT Unit; consultants in surgery x3, anaesthesiology x4, plastic surgery sub-specialist post"),
    ("psychiatry", "Psychiatry & Isolation ward; psychiatry specialist posts x2; clinical psychologist; counsellors x2"),
    ("emergency", "Accident and Trauma unit; consultants in emergency medicine x3; paramedics/EMTs"),
    ("orthopaedics", "Orthopedic Unit; consultants in orthopaedics x3"),
    ("maternity", "Gynae ward; consultants in gynaecology x5"),
    ("paediatrics", "Paediatric ward; paediatric specialist posts x5"),
    ("nicu", "neonatology specialist post (organogram)"),
    ("cardiology", "cardiology (sub)specialist post in organogram"),
    ("ent", "consultants in ENT x2"),
    ("ophthalmology", "consultants in ophthalmology x2; optometrist"),
    ("dermatology", "dermatology specialist posts x2"),
    ("ncd_diabetes", "internal medicine consultants x3; endocrinology, nephrology, rheumatology, neurology, pulmonology, urology posts; dietician"),
    ("physiotherapy", "senior physiotherapist + physiotherapists x2; speech therapists x2; occupational therapist"),
]
for cat, det in krh_units:
    add(facility_name="Kulhudhuffushi Regional Hospital", operator_type="public", facility_type="regional_hospital",
        island="Kulhudhuffushi", atoll="HDh", service_category=cat,
        service_detail=det + " (approved organogram v2.0, 21.07.2022 - posts may be partly vacant)",
        evidence="KRH Annual Report 2023 organogram: " + det[:120],
        source_url=KRH, source_date="2023", confidence="medium")

URH = "https://health.gov.mv/storage/uploads/Ko2x5PYQ/7qsqjacp.pdf"
for cat, det in [("dialysis", "Dialysis Unit"), ("maternity", "Midwifery Unit; Gynecology Unit"),
                 ("emergency", "Accidents and Trauma Unit; ER Unit"), ("icu", "ICU and NICU Unit"),
                 ("nicu", "ICU and NICU Unit"), ("surgery", "OT Unit; Surgical Unit"),
                 ("psychiatry", "Psychiatrist Unit"), ("paediatrics", "Pediatrics Unit"),
                 ("orthopaedics", "Orthopedician Unit"), ("ncd_diabetes", "Non Communicable Diseases Unit (public health)"),
                 ("physiotherapy", "Therapeutic Unit (diagnostic & therapeutic section)")]:
    add(facility_name="Ungoofaaru Regional Hospital", operator_type="public", facility_type="regional_hospital",
        island="Ungoofaaru", atoll="R", service_category=cat, service_detail=det + " (organogram 2023)",
        evidence="URH Annual Report 2023 organisational chart lists " + det,
        source_url=URH, source_date="2023", confidence="medium")

DH = "https://health.gov.mv/storage/uploads/Ko2xMrYQ/zpszm3fr.pdf"
for cat, det in [("ncd_diabetes", "consultant in internal medicine"), ("paediatrics", "consultant in paediatrics"),
                 ("surgery", "consultant in surgery; consultant in anaesthesiology"),
                 ("ophthalmology", "consultant in ophthalmology"), ("orthopaedics", "consultant in orthopaedics"),
                 ("maternity", "consultant in gynaecology"), ("emergency", "emergency response section; ambulance")]:
    add(facility_name="Dhaalu Atoll Hospital", operator_type="public", facility_type="atoll_hospital",
        island="Kudahuvadhoo", atoll="Dh", service_category=cat, service_detail=det + " (organogram post 2023)",
        evidence="Dh Atoll Hospital Annual Report 2023 organogram lists " + det,
        source_url=DH, source_date="2023", confidence="medium")

FH = "https://health.gov.mv/storage/uploads/rovPBeYj/z0xftjvr.pdf"
for cat, det in [("paediatrics", "consultants in general paediatrics; Pediatric Unit (nursing)"),
                 ("maternity", "consultant in obstetrics & gynecology; GYNAE ward"),
                 ("surgery", "consultant in surgery; consultant in anaesthesiology; surgical ward"),
                 ("orthopaedics", "consultant in orthopaedics"),
                 ("emergency", "Accident & Trauma service; emergency response unit"),
                 ("ncd_diabetes", "Non-Communicable Disease public health unit")]:
    add(facility_name="Faafu Atoll Hospital", operator_type="public", facility_type="atoll_hospital",
        island="Nilandhoo", atoll="F", service_category=cat, service_detail=det + " (organogram 2023)",
        evidence="F Atoll Hospital Annual Report 2023 organogram lists " + det,
        source_url=FH, source_date="2023", confidence="medium")

HA = "https://health.gov.mv/storage/uploads/Arovx2Yj/bvtns64j.pdf"
for cat, det in [("icu", "ICU census reported 2022"), ("nicu", "NICU census reported 2022"),
                 ("maternity", "Obstetrics & Gynaecology census; Gynae OPD"),
                 ("paediatrics", "Paediatrics census; paediatrics OPD"), ("ent", "ENT OPD clinic 2021"),
                 ("orthopaedics", "Orthopaedics OPD 2021"), ("ncd_diabetes", "Internal medicine OPD 2021"),
                 ("thalassaemia", "thalassaemia cases followed (transfusion/screening statistics) 2021-22")]:
    add(facility_name="Haa Alifu Atoll Hospital", operator_type="public", facility_type="atoll_hospital",
        island="Dhidhdhoo", atoll="HA", service_category=cat, service_detail=det,
        evidence="HA Atoll Hospital annual report charts: " + det + "; referrals mainly to IGMH and KRH",
        source_url=HA, source_date="2022", confidence="medium")

add(facility_name="Gaafu Alifu Atoll Hospital", operator_type="public", facility_type="atoll_hospital",
    island="Villingili", atoll="GA", service_category="physiotherapy",
    service_detail="physiotherapy sessions counted in 2022 service statistics",
    evidence="GA Atoll Annual Report 2022 service chart: Lab, cross-match, transfusion, X-ray, Physiotherapy",
    source_url="https://health.gov.mv/storage/uploads/6eY3WxY3/9w5s4p1m.pdf", source_date="2022", confidence="medium")


# ---- MHS 2020 Table 1-16: public-sector specialists by atoll (=> at the atoll/regional hospital) ----
MHS20 = "https://health.gov.mv/storage/uploads/79qgJ9YD/jjokopyg.pdf"
WF = sys.argv[2] if len(sys.argv) > 2 else None
PROF_CAT = {"Obstetricians and Gynaecologists": "maternity", "Pediatricians": "paediatrics",
            "Surgeons": "surgery", "Orthopedic Doctors": "orthopaedics",
            "Internal medicine (Physicians)": "ncd_diabetes",
            "ENT Doctors (Otorhinolaryngologists)": "ent", "Ophthalmologists": "ophthalmology",
            "Dermatologists": "dermatology", "Psychiatrists": "psychiatry", "Psychologists": "psychiatry",
            "Physiotherapists": "physiotherapy", "Speech Pathologists": "physiotherapy",
            "Cardiologists": "cardiology", "Urologists": "urology", "Pulmonologists": "pulmonology",
            "Anesthesiology": "surgery", "Nephrologist": "nephrology"}
if WF:
    from collections import defaultdict
    agg = defaultdict(list)
    for x in csv.DictReader(open(WF, encoding="utf-8")):
        a, prof = x["atoll_code"], x["profession"]
        if a not in ATOLL_HOSP and a != "S":
            continue
        if prof in PROF_CAT and x["total"] not in ("", "0"):
            agg[(a, PROF_CAT[prof])].append(f"{x['total']} {prof}")
    for (a, cat), specs in sorted(agg.items()):
        if a == "S":
            name, ftype, isl = "Addu Equatorial Hospital", "tertiary_hospital", "Hithadhoo"
        else:
            name, ftype, isl = ATOLL_HOSP[a]
        det = "; ".join(specs)
        if cat == "ncd_diabetes":
            det = "internal medicine physician(s) (NCD/diabetes management): " + det
        add(facility_name=name, operator_type="public", facility_type=ftype, island=isl, atoll=a,
            service_category=cat,
            service_detail=f"public-sector specialists posted in {a} atoll in 2020 (atoll's referral hospital): {det}",
            evidence=f"Maldives Health Statistics 2020, Table 1-16 workforce by atoll & category: {det}",
            source_url=MHS20, source_date="2020", confidence="medium")

with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows")
