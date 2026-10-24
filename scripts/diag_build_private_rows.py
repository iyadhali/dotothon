"""Build private-sector (and military) diagnostic service rows for the Maldives datathon.

Usage: python -I diag_build_private_rows.py <hems_diagnostic_staff_by_facility.csv> <out rows.csv>

Combines (1) manually curated evidence from websites / MoH lists, (2) MoH work-permit medical
facility list (Aug 2026) => basic serology + haematology, (3) HEMS professionals registry
(lab technologists, radiographers, radiologists, pathologists) for private/military establishments.
"""
import csv
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
staff_csv, out_csv = sys.argv[1], sys.argv[2]

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]

U_PCR_NOV22 = "https://health.gov.mv/storage/uploads/yXqPpMqB/pjdsnajt.pdf"
U_PCR_APR22 = "https://health.gov.mv/storage/uploads/6eY3pq3l/oe3e2dks.pdf"
U_AG_OCT22 = "https://health.gov.mv/storage/uploads/1VYx61oP/dr3keltp.pdf"
U_WP_2026 = "https://health.gov.mv/storage/uploads/kobdbDY8/it7zbg1p.pdf"
U_PVT_2026 = "https://health.gov.mv/storage/uploads/XqP13MoB/azlktiro.pdf"
U_HEMS = "https://hems.health.gov.mv/establishments"
U_AAS = "https://aasandha.mv/empanelled-facilities-local"
U_TTH_LAB = "https://www.treetophospital.com/lab-services"
U_TTH_FAC = "https://www.treetophospital.com/facilities"

rows = []


def add(name, op, ftype, island, atoll, cat, detail, evidence, url, date, conf):
    rows.append(dict(zip(COLS, [name, op, ftype, island, atoll, cat, detail, evidence, url, date, conf])))


# ---------------------------------------------------------------- 1. curated evidence
# ADK Hospital, Male
A = ("ADK Hospital", "private", "private_hospital", "Male", "K")
add(*A, "lab_advanced", "Full clinical lab: pathology & laboratory operations dept, consultant microbiologist; Aasandha-empanelled",
    "Departments list Pathology (Senior Consultant Pathologist, Head of Pathology and Laboratory Operations) and Microbiology (Consultant in Microbiology, clinical microbiology)",
    "https://adkhospital.com/departments/pathology", "2026", "high")
add(*A, "histopathology", "Histopathology, cytopathology, breast/surgical pathology reported in-house by 2 pathologists",
    "Pathology dept: 'Histopathology, Cytopathology, Laboratory Medicine'; 'Breast Pathology, Surgical Pathology'",
    "https://adkhospital.com/departments/pathology", "2026", "high")
add(*A, "pcr_molecular", "RT-PCR lab (COVID-19); fully automated Roche systems; ~2,000 tests/day incl. airport annex",
    "MoH 'Laboratories permitted for PCR testing' (private RT-PCR #1 ADK Hospital Laboratory, K.Male')",
    U_PCR_NOV22, "2022-11-07", "high")
add(*A, "endoscopy", "Upper GI endoscopy, colonoscopy, therapeutic endoscopy (gastroenterology dept)",
    "Gastroenterology dept: 'Endoscopy, Colonoscopy, Liver Disease, Therapeutic Endoscopy'",
    "https://adkhospital.com/departments/gastroenterology", "2026", "high")
add(*A, "xray", "Imaging & Radiology dept (4 consultant radiologists); CT/MRI detail covered by imaging stream",
    "Imaging and Radiology department with Senior Consultant/Consultant Radiologists",
    "https://adkhospital.com/departments/imaging-and-radiology", "2026", "high")
add(*A, "ultrasound", "Ultrasound by radiology dept",
    "Imaging and Radiology department with 4 radiologists ('Diagnostic Radiology ... Scan')",
    "https://adkhospital.com/departments/imaging-and-radiology", "2026", "high")
add("ADK Hospital Annex (Velana International Airport lab)", "private", "diagnostic_lab", "Hulhule", "K", "pcr_molecular",
    "Airport COVID-19 RT-PCR lab (ADK + LUX* + TMA), Roche automated; receives resort/island samples via ferry terminal; current status unknown",
    "Unveiled Dec 2020; listed as 'ADK Hospital Annex / Velanaa International Airport/ Hulhule' on MoH PCR list",
    "https://edition.mv/news/21140", "2022-11-07", "medium")

# Tree Top Hospital, Hulhumale
T = ("Tree Top Hospital", "private", "private_hospital", "Hulhumale", "K")
add(*T, "lab_advanced", "In-house catalogue: 100 biochemistry (incl. HbA1c), 19 haematology & haemostasis, 71 immunology & serology (TSH, PSA...), 30 microbiology (blood culture); plus 1,948 tests referred to Metropolis (India)",
    "Online test catalogue (2,421 tests); referral tests tagged 'METROPOLIS'; lab open 07:00-22:00",
    U_TTH_LAB, "2025-09", "high")
add(*T, "histopathology", "187 histopathology tests + gynae/non-gynae cytology in-house; IHC panels via Metropolis (India)",
    "Catalogue sections Histopathology (187), Gynaecology Cytology, Non Gynaecology Cytology",
    U_TTH_LAB, "2025-09", "high")
add(*T, "pcr_molecular", "12 molecular tests: COVID-19 RT-PCR, influenza A/B, dengue/zika/chikungunya RNA PCR, HPV PCR 16/18",
    "Catalogue section 'Molecular' (12 tests)", U_TTH_LAB, "2025-09", "high")
add(*T, "blood_bank", "Hospital transfusion lab: ABO/Rh, crossmatch, direct/indirect Coombs, Rh antibody titre, therapeutic phlebotomy",
    "Catalogue section 'Blood Bank' (6 tests)", U_TTH_LAB, "2025-09", "high")
for cat, det in [("mri", "MRI scanner"), ("ct", "CT scanner"), ("xray", "Digital X-ray, fluoroscopy, bone densitometry"),
                 ("ultrasound", "Ultrasound"), ("mammography", "Mammography"), ("endoscopy", "Endoscopy suite")]:
    add(*T, cat, det, "Facilities page 'Diagnostic & Imaging': MRI Scanner, CT Scanner, Digital X-Ray, Ultrasound, Mammography, Endoscopy Suite; radiology list (adhadhu.com 2023-08-14)",
        U_TTH_FAC, "2026", "high")
add("TTH Clinic Male' (Tree Top Hospital)", "private", "collection_centre", "Male", "K", "lab_basic",
    "Sample collection point for Tree Top Hospital lab (Hulhumale)", "'Laboratory Services: Diagnostic testing and sample collection services'",
    "https://www.treetophospital.com/tth-clinic-male", "2026", "high")

# Medica Hospital
M = ("Medica Hospital", "private", "private_hospital", "Male", "K")
add(*M, "xray", "X-ray (radiology dept, 2 radiologists)", "'Radiological services offered at Medica Hospital: X-ray, Ultrasound'",
    "https://medica.com.mv/service/radiology/", "2026", "high")
add(*M, "ultrasound", "Ultrasound incl. Doppler, obstetric, TVS, breast, thyroid, FNAC guidance",
    "Radiologist service list: antenatal scan, Doppler, breast, thyroid, transvaginal, whole abdomen, FNAC",
    "https://medica.com.mv/service/radiology/", "2026", "high")

# AMDC
AM = ("Azmi-Naeem Medical & Diagnostic Centre (AMDC)", "private", "private_clinic", "Male", "K")
add(*AM, "lab_advanced", "Channel partner of SRL Diagnostics (Mumbai, India): ~3,500 specialised tests by sample referral to India; COVID antigen testing permitted 2022",
    "'AMDC is the channel partner for the SRL ... access to a multitude of laboratorical investigations without having to leave the country'",
    "https://amdc.com.mv/service/srl-laboratory/", "2024", "high")
add(*AM, "ultrasound", "Ultrasound daily: Doppler, breast, KUB, pelvic, thyroid, TVS, NT, anomaly, transrectal, BPP",
    "'fully equipped with a high quality ultrasound scan machine and have doctors available every day to conduct scans'",
    "https://amdc.com.mv/service/ultra-sound-scanning/", "2024", "high")

# Medlab Diagnostics
ML = ("Medlab Diagnostics", "private", "diagnostic_lab", "Male", "K")
add(*ML, "lab_advanced", "Grade 1 private lab (Aasandha): haematology incl. coagulation, ferritin, G6PD, bone marrow; clinical chemistry; serology & immunology; microbiology; drugs-of-abuse (only private lab authorised); referral testing for hospitals and regional health centres; site sample collection; 2 outlets; 3-h TAT",
    "Services page test menu and 'Referral testing to other hospitals and regional health centers ... Site sample collection services'",
    "https://medlabdiagnostics.com/services", "2026", "high")
add(*ML, "histopathology", "Test menu lists 'Histopathology & Cytopathology' (in-house vs send-out not stated)",
    "Test Menu: HISTOPATHOLOGY & CYTOPATHOLOGY", "https://medlabdiagnostics.com/services", "2026", "medium")
add(*ML, "pcr_molecular", "COVID-19 RT-PCR (results in 24h)", "MoH PCR list private #4 Medlab Diagnostics/K.Male'", U_PCR_NOV22, "2022-11-07", "high")

# Mediflex
add("Mediflex Laboratories", "private", "diagnostic_lab", "Male", "K", "pcr_molecular",
    "RT-PCR lab opened 20 Dec 2020 (Medtech Maldives): 2x Thermo QuantStudio 5, KingFisher extraction, ~1,000 samples/day; collection across Greater Male' incl. airport, resort sampling kits",
    "Hotelier Maldives Jan 2021; MoH PCR list private #6", "https://hoteliermaldives.com/mediflex-laboratories/", "2022-11-07", "high")
add("Mediflex Scan Centre", "private", "private_clinic", "Male", "K", "ultrasound",
    "CLOSED per HEMS registry", "HEMS: Diagnostic Service Clinic, status Closed", U_HEMS, "2026", "low")

# Other PCR-permitted private labs (MoH lists 2022)
pcr = [
    ("RMLS Lab Services", "diagnostic_lab", "Hulhumale", "K", "RT-PCR and COVID antibody testing permitted; Lot 10059 New Hill (shared with Pearl Medical Centre Hulhumale)", "high"),
    ("Villa Bio Medicals Laboratory", "diagnostic_lab", "Nalaguraidhoo (Sun Island Resort)", "ADh", "RT-PCR lab on Sun Island Resort & Spa; Diagnostic Clinic licence still listed May 2026", "high"),
    ("Maafaru PCR Lab (Crystal Express)", "diagnostic_lab", "Maafaru", "N", "RT-PCR lab at Maafaru International Airport licensed to Crystal Express Maldives; likely COVID-era only", "medium"),
    ("Crystal Medicals", "private_clinic", "Male", "K", "RT-PCR permitted 2022", "medium"),
    ("Elite Medical Centre", "private_clinic", "Male", "K", "RT-PCR permitted 2022", "medium"),
    ("Maldives Diagnostic Centre", "diagnostic_lab", "Male", "K", "RT-PCR permitted 2022 (G. Velagala)", "medium"),
    ("Maldicare Clinic", "private_clinic", "Male", "K", "RT-PCR permitted 2022", "medium"),
    ("Mafhaa Diagnostic Centre", "diagnostic_lab", "Male", "K", "RT-PCR and COVID antigen permitted 2022", "medium"),
    ("Azmi-Naeem Medical & Diagnostic Centre (AMDC)", "private_clinic", "Male", "K", "RT-PCR permitted Nov 2022", "medium"),
    ("Southern Care Clinic", "private_clinic", "Hithadhoo", "S", "RT-PCR permitted Nov 2022 - only private PCR outside Greater Male' besides Villa Biomedicals/Maafaru", "medium"),
    ("Image Centre", "private_clinic", "Male", "K", "RT-PCR permitted Apr 2022 (dropped from Nov 2022 list)", "low"),
    ("Novalux Diagnostics", "diagnostic_lab", "Thulusdhoo", "K", "RT-PCR permitted 2022; HEMS shows Closed but MoH May-2026 list still shows Diagnostic Clinic licence", "low"),
    ("Huvadhoo PCR lab", "diagnostic_lab", "Thinadhoo", "GDh", "RT-PCR permitted 2022; CLOSED per HEMS registry", "low"),
    ("My Lab (Furaveri Resort)", "diagnostic_lab", "Furaveri (resort)", "R", "RT-PCR permitted 2022; CLOSED per HEMS registry", "low"),
    ("My Lab Dharavandhoo", "diagnostic_lab", "Dharavandhoo", "B", "RT-PCR permitted 2022; CLOSED per HEMS registry", "low"),
]
for n, ft, isl, at, det, conf in pcr:
    add(n, "private", ft, isl, at, "pcr_molecular", det, "MoH 'Laboratories permitted for PCR testing' (private RT-PCR list)",
        U_PCR_NOV22 if "Apr 2022" not in det else U_PCR_APR22, "2022-11-07" if "Apr 2022" not in det else "2022-04-07", conf)

# Senahiya
add("Senahiya Military Hospital", "military", "military_hospital", "Male", "K", "lab_basic",
    "MNDF hospital lab; COVID antibody and antigen testing permitted; work-permit medicals; Aasandha-empanelled",
    "MoH antibody/antigen testing list Oct 2022 (Senahiya Hospitals / K.Male'); MoH work-permit list 2026", U_AG_OCT22, "2022-10-17", "high")

# Island private hospitals / clinics
add("I.M.D.C Multi Speciality Hospital", "private", "private_hospital", "Hithadhoo", "S", "lab_basic",
    "30-bed private hospital: 'state of the art laboratory'; work-permit medicals; Aasandha", "IMDC site: 'houses a state of the art laboratory, X-Ray facilities, ... ICU, NICU'; home page lists 'Laboratory', 'Diagnostic Centre'",
    "https://imdc.com.mv/", "2026", "high")
add("I.M.D.C Multi Speciality Hospital", "private", "private_hospital", "Hithadhoo", "S", "xray",
    "X-ray facilities", "IMDC 'About': 'X-Ray facilities'", "https://imdctest.simdi.com/about.html", "2026", "medium")
add("AIMS Diagnostic Care", "private", "private_clinic", "Feydhoo", "S", "lab_basic",
    "Laboratory services; applied for COVID testing 2020 (36 samples/h) but refused; work-permit medicals; Aasandha", "Directory profile: 'X-ray Services, Scan Services, Laboratory Services'; edition.mv 2020",
    "https://village.ai/company/aimsmv", "2024", "medium")
add("AIMS Diagnostic Care", "private", "private_clinic", "Feydhoo", "S", "xray", "X-ray services", "Directory profile lists 'X-ray Services'", "https://village.ai/company/aimsmv", "2024", "medium")
add("AIMS Diagnostic Care", "private", "private_clinic", "Feydhoo", "S", "ultrasound", "'Scan services' (assumed ultrasound)", "Directory profile lists 'Scan Services'", "https://village.ai/company/aimsmv", "2024", "low")
add("F & C Medicare and Scan Center", "private", "private_clinic", "Hithadhoo", "S", "ultrasound",
    "Clinic with scan centre (ultrasound assumed from name)", "MoH private facility list: 'F & C Medicare and Scan Center', Ehaaru, S. Hithadhoo", U_PVT_2026, "2026-05-05", "low")
add("Family Care Clinic and Scan Centre", "private", "private_clinic", "Male", "K", "ultrasound",
    "Scan centre (ultrasound assumed from name); work-permit medicals", "MoH private facility list / work-permit list", U_PVT_2026, "2026-05-05", "low")
add("Care Trust Multi Speciality Clinic", "private", "private_hospital", "Hulhumale", "K", "lab_basic",
    "Laboratory services; advanced prenatal, genetic & cancer testing (likely referred); work-permit medicals", "'Our services ranges from laboratory services, X-ray, ultrasound imaging, doppler studies and ECHO'",
    "https://caretrust.mv/", "2026", "high")
add("Care Trust Multi Speciality Clinic", "private", "private_hospital", "Hulhumale", "K", "xray", "X-ray", "Website services list", "https://caretrust.mv/", "2026", "high")
add("Care Trust Multi Speciality Clinic", "private", "private_hospital", "Hulhumale", "K", "ultrasound", "Ultrasound, Doppler, fetal medicine (radiologist + FMF-certified fetal medicine specialist)", "Website services list", "https://caretrust.mv/", "2026", "high")
add("Clinica Maldives", "private", "private_clinic", "Male", "K", "lab_basic",
    "Integrated laboratory diagnostics (Male' and Hulhumale centres), resort/occupational screening; partner Nawaloka Hospital (Sri Lanka)",
    "'integrated laboratory diagnostics, occupational health screenings'", "https://clinica.mv/", "2026", "high")
add("Gynova", "private", "private_clinic", "Kulhudhuffushi", "HDh", "ultrasound",
    "Women's clinic; radiologist specialising in obstetric & gynaecological ultrasound", "Website doctor profile 'Radiologist ... obstetric and gynaecological ultrasounds'", "https://gynova.mv/", "2026", "high")
add("Medicrest Clinic and Diagnostics", "private", "private_clinic", "Velidhoo", "N", "lab_basic",
    "Clinic & diagnostics (lab services inferred from name; licensed Sept 2023)", "MoH private facility list: Dhoodhaari Imaaraaiyy, N. Velidhoo", U_PVT_2026, "2026-05-05", "low")
for n, isl, at in [("Lab Maldives", "Hulhumale", "K"), ("MVDX Diagnostics", "Male", "K"),
                   ("Resort Medical and Laboratory Services (Island Health Solutions)", "Male", "K"),
                   ("Maldives Diagnostic Centre", "Male", "K"), ("Mafhaa Diagnostic Centre", "Male", "K"),
                   ("Mediflex Laboratories", "Male", "K"), ("Villa Bio Medicals Laboratory", "Nalaguraidhoo (Sun Island Resort)", "ADh")]:
    add(n, "private", "diagnostic_lab", isl, at, "lab_basic", "Licensed Diagnostic Clinic (laboratory) - test menu not published",
        "MoH 'Operating Private Health Facilities' - Diagnostic Clinic section", U_PVT_2026, "2026-05-05", "medium")

# Resort clinics permitted for COVID antigen RDT (POC only)
for n, isl, at in [("Rangali Clinic (Conrad Maldives)", "Rangali (resort)", "ADh"), ("Vommuli Clinic (St. Regis)", "Vommuli (resort)", "Dh"),
                   ("Pullman Maldives Maamutaa Resort Clinic", "Maamutaa (resort)", "GA"), ("Athuruga Medical Clinic", "Athurugau (resort)", "ADh"),
                   ("Sandies Bathala Infirmary", "Bathalaa (resort)", "AA"), ("Ouch (W Maldives)", "Fesdhoo (resort)", "AA"),
                   ("Thundufushi Medical Clinic", "Thundufushi (resort)", "ADh"), ("Eve Clinic", "Male", "K")]:
    add(n, "private", "private_clinic", isl, at, "lab_basic", "Point-of-care only: COVID-19 antigen RDT permitted",
        "MoH 'Laboratories permitted for COVID-19 antigen testing'", U_AG_OCT22, "2022-10-17", "low")

# ---------------------------------------------------------------- 2. work-permit medical facilities (private)
WP = [("ADK Hospital", "Male", "K"), ("AMDC Clinic", "Male", "K"), ("Medica Hospital", "Male", "K"), ("Pearl Medical Centre", "Male", "K"),
      ("AIMS Diagnostic Care", "Feydhoo", "S"), ("I.M.D.C Multi Speciality Hospital", "Hithadhoo", "S"), ("Tree Top Hospital", "Hulhumale", "K"),
      ("Elite Medical Centre", "Male", "K"), ("Senahiya Military Hospital", "Male", "K"), ("Pearl Medical Centre Hulhumale", "Hulhumale", "K"),
      ("Care Trust Multi Speciality Clinic", "Hulhumale", "K"), ("Maldicare Clinic", "Male", "K"), ("Pro Care Clinic and Dental Centre", "Mahibadhoo", "ADh"),
      ("Image Centre", "Male", "K"), ("Hussain Abdul Samad Memorial Clinic", "Dhangethi", "ADh"), ("Southern Care Clinic", "Hithadhoo", "S"),
      ("Synergy Care", "Hulhumale", "K"), ("Mednova Medical Center", "Male", "K"), ("Thasalli Medical Care", "Male", "K"),
      ("Dr. Usama's Clinic", "Male", "K"), ("Naifaru Medical Center", "Naifaru", "Lh"), ("Eve Clinic", "Male", "K"), ("Clinica Maldives", "Male", "K"),
      ("Central Clinic", "Male", "K"), ("Advance Medical Clinic", "Male", "K"), ("Maldives Diagnostic Centre", "Male", "K"),
      ("Faruvaa Clinic", "Male", "K"), ("Crystal Medicals", "Male", "K"), ("Star Medical", "Male", "K"),
      ("Dharavandhoo Medical Center", "Dharavandhoo", "B"), ("My Care Medical Centre", "Male", "K"), ("AMG Clinic", "Meedhoo", "R"),
      ("Rx Medicare", "Hulhumale", "K"), ("Advance Diagnostic Center", "Eydhafushi", "B"), ("Family Care Clinic and Scan Centre", "Male", "K"),
      ("Vital Care", "Male", "K"), ("Vitalcare Huvadhoo", "Thinadhoo", "GDh"), ("My Medical Center", "Male", "K"), ("Point Medical Care", "Male", "K"),
      ("Life Wellness Clinic", "Hulhumale", "K"), ("Life Care Medical", "Hulhumale", "K"), ("Well Care Medicals", "Male", "K"),
      ("Eve Clinic Vinares", "Hulhumale", "K"), ("Pulse Medical and Diagnostics", "Male", "K"), ("Careone Dental & Clinic", "Male", "K"),
      ("Farook Healthcare", "Fuvahmulah", "Gn"), ("Oagaa Medical Centre", "Male", "K")]
have_lab = {(r["facility_name"], "lab") for r in rows if r["service_category"] in ("lab_basic", "lab_advanced")}
for n, isl, at in WP:
    if (n, "lab") in have_lab:
        continue
    op = "military" if "Senahiya" in n else "private"
    ft = "private_hospital" if "Hospital" in n else ("military_hospital" if op == "military" else "private_clinic")
    add(n, op, ft, isl, at, "lab_basic",
        "Approved for expatriate work-permit medicals: Hb, total count, blood group, VDRL, HBsAg, HIV, HCV + chest X-ray report (tests may be outsourced)",
        "MoH 'Health facilities permitted for work permit medical issuance' (private list), 9 Aug 2026; form MOH-QA/F/17/67-4",
        U_WP_2026, "2026-08-09", "medium")

# ---------------------------------------------------------------- 3. HEMS professionals (private + military)
ISLAND_FIX = {  # establishment_id -> (facility name, island, atoll) for private/military facilities whose island HEMS lacks
    "827": ("ADK Hospital", "Male", "K"), "362": ("Tree Top Hospital", "Hulhumale", "K"), "459": ("Medica Hospital", "Male", "K"),
    "782": ("I.M.D.C Multi Speciality Hospital", "Hithadhoo", "S"), "420": ("Care Trust Multi Speciality Clinic", "Hulhumale", "K"),
    "327": ("Senahiya Military Hospital", "Male", "K"), "272": ("Senahiya Northern", "Maafilaafushi", "Lh"),
    "1223": ("Advance Hospital", "", ""), "432": ("AIMS Diagnostic Care", "Feydhoo", "S"), "828": ("Azmi-Naeem Medical & Diagnostic Centre (AMDC)", "Male", "K"),
    "340": ("Advance Diagnostic Center", "Eydhafushi", "B"), "457": ("F & C Medicare and Scan Center", "Hithadhoo", "S"),
    "806": ("F & C Medicare", "Maradhoo-Feydhoo", "S"), "277": ("F&C Medicare, Meedhoo", "Meedhoo", "S"),
    "777": ("Family Care Clinic and Scan Centre", "Male", "K"), "223": ("Mafhaa Diagnostic Centre", "Male", "K"),
    "218": ("Maldives Diagnostic Centre", "Male", "K"), "274": ("Mediflex Laboratories", "Male", "K"), "695": ("Medlab Diagnostics", "Male", "K"),
    "125": ("MVDX Diagnostics", "Male", "K"), "338": ("Resort Medical and Laboratory Services (Island Health Solutions)", "Male", "K"),
    "279": ("RMLS Lab Services", "Hulhumale", "K"), "256": ("Villa Bio Medicals Laboratory", "Nalaguraidhoo (Sun Island Resort)", "ADh"),
    "858": ("Pulse Medical and Diagnostics", "Male", "K"), "1460": ("Zen Medi Clinic", "Kulhudhuffushi", "HDh"),
    "1354": ("Thilafushi General Clinic", "Thilafushi", "K"), "9": ("WTE Medical Clinic", "Thilafushi", "K"),
    "42": ("Dharavandhoo Medical Center", "Dharavandhoo", "B"), "153": ("Naifaru Medical Center", "Naifaru", "Lh"),
    "520": ("Pearl Medical Centre", "Male", "K"), "314": ("Pearl Medical Centre Hulhumale", "Hulhumale", "K"),
    "235": ("Farook Healthcare", "Fuvahmulah", "Gn"), "176": ("Farook Healthcare Villingili", "Villingili", "GA"),
    "236": ("Fuvahmulah Medical Centre", "Fuvahmulah", "Gn"), "884": ("Gynova", "Kulhudhuffushi", "HDh"),
    "90": ("Haajy Medical Clinic", "Kulhudhuffushi", "HDh"), "869": ("Island Polyclinic", "Hanimaadhoo", "HDh"),
    "221": ("Southern Care Clinic", "Hithadhoo", "S"), "434": ("Pro Care Clinic and Dental Centre", "Mahibadhoo", "ADh"),
    "335": ("Hussain Abdul Samad Memorial Clinic", "Dhangethi", "ADh"), "128": ("AMG Clinic", "Meedhoo", "R"),
    "11": ("Omni Care Clinic", "Thulhaadhoo", "B"), "208": ("Revive Medical Centre", "Hoarafushi", "HA"),
    "917": ("Pulse Point Medical Center", "Ihavandhoo", "HA"), "54": ("Modern Medical Centre", "Fonadhoo", "L"),
    "824": ("Abuharee Medical Centre", "Hithadhoo", "S"), "1258": ("CAREMORE MEDICALS", "Hithadhoo", "S"),
    "771": ("Maandhoo Medical Centre", "Maandhoo", "L"), "230": ("Maamigili Clinic", "Maamigili", "R"),
    "164": ("Vitalcare Huvadhoo", "Thinadhoo", "GDh"), "275": ("Vital Care Kulhudhuffushi", "Kulhudhuffushi", "HDh"),
    "523": ("Vital Care", "Male", "K"), "35": ("NU Hospitals Clinic", "Hulhumale", "K"), "775": ("Image Centre", "Male", "K"),
    "814": ("Maldicare Clinic", "Male", "K"), "354": ("Elite Medical Centre", "Male", "K"), "402": ("Crystal Medicals", "Male", "K"),
    "201": ("Hiyaa Medical Center", "Hulhumale", "K"), "29": ("Pine Tree Medic Care Sh. Funadhoo", "Funadhoo", "Sh"),
    "261": ("Aahiyans Medical Clinic", "Hinnavaru", "Lh"), "88": ("Master Medical and Dental Care Centre", "Gadhdhoo", "GDh"),
    "64": ("Master Medical and Dental Care Centre", "Gadhdhoo", "GDh"), "89": ("Healing Care Medical Center", "Kulhudhuffushi", "HDh"),
    "93": ("Olive Medical Centre", "Thinadhoo", "GDh"),
}
if os.path.exists(staff_csv):
    staff = list(csv.DictReader(open(staff_csv, encoding="utf-8")))
    for s in staff:
        if s["sector"] == "public" and "MNDF" not in s["name"].upper() and "Senahiya" not in s["name"]:
            continue
        if s["status"].lower() != "operating":
            continue
        lab = int(s["lab_tech"]) ; path = int(s["pathologist"]); micro = int(s["microbiologist"])
        rg = int(s["radiographer"]); rl = int(s["radiologist"]); gi = int(s["gastro_endoscopy"])
        if not any([lab, path, micro, rg, rl, gi]):
            continue
        name, isl, at = ISLAND_FIX.get(s["establishment_id"], (s["name"], s["island"], s["atoll_code"]))
        op = "military" if "Senahiya" in s["name"] or "MNDF" in s["name"].upper() else "private"
        lvl = s["level"]
        ft = ("military_hospital" if op == "military" and "Hospital" in lvl else
              "private_hospital" if "Hospital" in lvl else "diagnostic_lab" if "Diagnostic" in lvl else "private_clinic")
        ev = f"HEMS professionals registry: {lab} lab technologist/technician, {path} pathologist/haematologist, {micro} microbiologist, {rg} radiographer, {rl} radiologist, {gi} gastroenterologist ({s['diag_titles']})"
        url = f"https://hems.health.gov.mv/establishments/{s['establishment_id']}/professionals"
        if lab or path or micro:
            adv = path > 0 or micro > 0 or lab >= 4
            add(name, op, ft, isl, at, "lab_advanced" if adv else "lab_basic",
                f"Licensed lab staff on register ({lab} lab tech{'s' if lab != 1 else ''}{', pathologist' if path else ''}{', microbiologist' if micro else ''}); test menu not verified",
                ev, url, "2026-10", "medium" if adv or lab >= 2 else "low")
        if path:
            add(name, op, ft, isl, at, "histopathology", "Pathologist on staff (histopathology capacity likely; send-out not excluded)", ev, url, "2026-10", "low")
        if rg:
            add(name, op, ft, isl, at, "xray", f"{rg} radiographer(s) registered", ev, url, "2026-10", "medium")
        if rl:
            add(name, op, ft, isl, at, "ultrasound", f"{rl} radiologist(s) registered (ultrasound reporting)", ev, url, "2026-10", "medium")
        if gi:
            add(name, op, ft, isl, at, "endoscopy", f"{gi} gastroenterologist(s) registered (endoscopy likely)", ev, url, "2026-10", "low")
else:
    print("WARNING: no HEMS staff summary found; skipping HEMS-derived rows")

# ---------------------------------------------------------------- dedupe: keep best confidence per facility x category, merge evidence
rank = {"high": 3, "medium": 2, "low": 1}
best = {}
for r in rows:
    key = (r["facility_name"].lower().replace("'", "").replace(".", "").strip(), r["service_category"])
    if key not in best:
        best[key] = r
        continue
    b = best[key]
    if rank[r["confidence"]] > rank[b["confidence"]]:
        r = dict(r)
        r["evidence"] = r["evidence"] + " | also: " + b["evidence"][:200]
        best[key] = r
    else:
        if len(b["evidence"]) < 900:
            b["evidence"] = b["evidence"] + " | also: " + r["evidence"][:200]
out = sorted(best.values(), key=lambda r: (r["atoll"], r["island"], r["facility_name"], r["service_category"]))
with open(out_csv, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    w.writerows(out)
print("rows:", len(out))
