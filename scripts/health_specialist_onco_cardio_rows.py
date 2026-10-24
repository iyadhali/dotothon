"""Build partial CSV of oncology / cardiology / hospital-department evidence rows
(hand-curated from saved sources in data/external/health/services/specialist/sources/hospitals_onco_cardio).

Usage: python -I health_specialist_onco_cardio_rows.py <OUT_CSV>
"""
import csv
import sys

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]

ACC = "2026-10-24"  # access date for undated web pages

# ---- sources ----
IGMH = "https://www.igmh.gov.mv/en/"
MCGH = "https://mcgh.gov.mv/specialities"
ED = "https://edition.mv/news/"
URH = "https://www.urh.gov.mv/?page_id="
AEH_DOC = "https://aeh.gov.mv/doctors"
ASMH_DOC = "https://asmh.gov.mv/doctors"
ADK = "https://www.adkhospital.com/departments"
TT = "https://www.treetophospital.com/specialities"
KRH_AR = "https://health.gov.mv/storage/uploads/0wNN3bwA/ldoamukt.pdf"
URH_AR = "https://health.gov.mv/storage/uploads/Ko2x5PYQ/7qsqjacp.pdf"
F_AR = "https://health.gov.mv/storage/uploads/rovPBeYj/z0xftjvr.pdf"
DH_AR = "https://health.gov.mv/storage/uploads/Ko2xMrYQ/zpszm3fr.pdf"
HA_AR22 = "https://health.gov.mv/storage/uploads/Arovx2Yj/bvtns64j.pdf"
HA_AR21 = "https://health.gov.mv/storage/uploads/Ejo6VWor/4mjffjag.pdf"
MV_URH = "https://maldivesvoice.mv/2611"
PSM_ATOLL_CHEMO = "https://psmnews.mv/en/132621"
MV_2984 = "https://maldivesvoice.mv/2984"

rows = []


def add(fac, op, ftype, isl, atoll, cat, detail, ev, url, date, conf):
    rows.append(dict(zip(COLS, [fac, op, ftype, isl, atoll, cat, detail, ev, url, date, conf])))


# ======================= IGMH (Male') =======================
F, O, T, I, A = "Indira Gandhi Memorial Hospital (IGMH)", "public", "tertiary_hospital", "Male'", "MLE"
add(F, O, T, I, A, "oncology", "National Cancer Centre: onco-surgery OPD, medical oncologist OPD, day-care chemotherapy units, immunotherapy, hormone therapy, cancer surgery, inpatient oncology ward, palliative/end-of-life care, weekly tumour board. NO radiotherapy (not available anywhere in Maldives).",
    "IGMH NCC page: 'offers cancer screening, diagnostic evaluation, chemotherapy, and advanced oncological surgical procedures'; NCC established 2023 with dedicated ward", IGMH + "centres/national-cancer-centre", ACC, "high")
add(F, O, T, I, A, "oncology", "8-bed oncology ward opened Aug 2023 (chemotherapy under one roof)",
    "'The newly inaugurated ward features eight beds'", "https://adhadhu.com/41684", "2023-08-17", "high")
add(F, O, T, I, A, "cardiology", "National Cardiac Centre / National Centre for Cardiovascular Sciences: cath lab since 2016 (angiography, angioplasty), run by ~5 Maldivian cardiologists since Nov 2025 (previously Meditrina Hospital, India); upgrade to bi-plane planned; paediatric cardiology clinic",
    "'Cath lab services at IGMH began being offered at the Cardiac Center ... currently being offered by Maldivian doctors at IGMH'", ED + "53108", "2026-08-03", "high")
add(F, O, T, I, A, "icu", "Critical Care Department: medical ICU, surgical ICU, post-operative critical care, ventilator support; neurosurgical ICU planned",
    "IGMH Critical Care Department page", IGMH + "departments/critical-care-department", ACC, "high")
add(F, O, T, I, A, "nicu", "18-bed NICU (incl. 2 observation) in Hiyala Wing and Dharumavantha Hospital; ~80 neonatal admissions/month; ROP eye treatment for premature babies",
    "'Our NICU has 18 beds, including 2 observation beds'", IGMH + "departments/paediatrics-neonatology", ACC, "high")
add(F, O, T, I, A, "paediatrics", "Paediatrics & Neonatology dept (0-16 y); 32-bed paediatric ward (2021); subspecialty clinics incl. paediatric cardiology, high-risk follow-up; national paediatric referral centre",
    "IGMH dept page; 'hospital's 32 bed pediatric ward was currently full'", IGMH + "departments/paediatrics-neonatology", ACC, "high")
add(F, O, T, I, A, "maternity", "Obstetrics & Gynaecology: labour unit, high-risk pregnancy inpatient care, emergency operative obstetrics, prenatal diagnosis (amnio/CVS), Villimale' ANC; gynaecological oncology",
    "IGMH O&G page lists 'Labour unit - inductions & deliveries, Obstetric emergency services'", IGMH + "departments/obstetrics-gynecology", ACC, "high")
add(F, O, T, I, A, "emergency", "Trauma & Emergency dept, 24/7 triage/resuscitation; national trauma referral",
    "'providing 24-hour emergency medical services for all acute, critical, and life-threatening conditions'", IGMH + "departments/trauma-emergency", ACC, "high")
add(F, O, T, I, A, "surgery", "General surgery, neurosurgery (National Centre for Neurosciences & Stroke, Feb 2026), urology, plastic surgery, oncosurgery, hybrid OT",
    "IGMH departments list; MCGH specialities list", IGMH + "departments/surgery", ACC, "high")
add(F, O, T, I, A, "orthopaedics", "Orthopaedics & Trauma Surgery, 24/7 emergency trauma + elective",
    "'The department offers 24/7 emergency trauma services alongside specialized elective orthopedic care'", IGMH + "departments/orthopedics-trauma-surgery", ACC, "high")
add(F, O, T, I, A, "ophthalmology", "Ophthalmology: retina & glaucoma clinics, ROP, lasers (PRP, YAG), cataract surgery",
    "IGMH Ophthalmology page", IGMH + "departments/ophthalmology", ACC, "high")
add(F, O, T, I, A, "ent", "ENT / head & neck surgery: endoscopy, otoendoscopy, surgery; speech pathology & audiology dept",
    "IGMH ENT page", IGMH + "departments/ent", ACC, "high")
add(F, O, T, I, A, "dermatology", "Dermatology (5 dermatologists), STI and leprosy services; weekly outreach to Villimale' Hospital",
    "'Our Team includes five Dermatologists'", IGMH + "departments/dermatology", ACC, "high")
add(F, O, T, I, A, "ncd_diabetes", "National Diabetes Centre + Endocrinology dept (endocrinologists, diabetes clinic, day-care endocrine tests)",
    "IGMH National Diabetes Centre page", IGMH + "centres/national-diabets-centre", ACC, "high")
add(F, O, T, I, A, "psychiatry", "National Centre for Mental Health: national tertiary psychiatric referral centre (OPD, inpatient, emergency, psychology, FPU)",
    "'NCMH is the national tertiary centre for mental health care'", IGMH + "centres/national-centre-for-mental-health", ACC, "high")
add(F, O, T, I, A, "physiotherapy", "Physiotherapy & Physical Rehabilitation: MSK, neuro-rehab, cardiopulmonary physio, inpatient + outpatient",
    "IGMH physiotherapy page", IGMH + "departments/physiotherapy-physical-rehabilitation", ACC, "high")
add(F, O, T, I, A, "fertility", "National Fertility Centre: IVF, ICSI, IUI, onco-fertility/gamete preservation",
    "IGMH National Fertility Centre page", IGMH + "centres/national-fertility-centre", ACC, "high")

# Dharumavantha Hospital (MCGH, Male')
F, T = "Dharumavantha Hospital (MCGH)", "tertiary_hospital"
add(F, O, T, I, A, "cardiology", "Cardiology and paediatric cardiology listed; second cath lab + bi-plane hybrid OT being established (planned 2026)",
    "MCGH specialities page lists DH for Cardiology, Paediatric Cardiology; 'additional cardiac catheterization laboratory (cath lab) in Dharumavantha Hospital'", ED + "53108", "2026-08-03", "medium")
add(F, O, T, I, A, "oncology", "Surgical oncology listed (MCGH specialities)", "MCGH specialities: Surgical Oncology - DH, IGMH", MCGH, ACC, "medium")
add(F, O, T, I, A, "nicu", "Part of IGMH 18-bed NICU located at DH", "'Located in both the Hiyala Wing and Dharumavantha Hospital (DH)'", IGMH + "departments/paediatrics-neonatology", ACC, "high")
add(F, O, T, I, A, "maternity", "Obstetrics & Gynecology (MCGH specialities)", "MCGH specialities: Obstetrics & Gynecology - DH, HMH, IGMH", MCGH, ACC, "medium")

# ======================= Hulhumale' Hospital =======================
F, T, I = "Hulhumale' Hospital (MCGH)", "tertiary_hospital", "Hulhumale'"
add(F, O, T, I, A, "oncology", "Government chemotherapy/oncology service since Oct 2017 (day-care chemo, ~5 oncology beds; 9 cancer beds shared with IGMH per 2026); breast cancer surgery introduced 2026; supports atoll chemo units (Lh, ASMH, KRH)",
    "Minister: 'chemotherapy is available at IGMH and Hulhumale' Hospital, and those hospitals have 9 beds'", ED + "51911", "2026-06-23", "high")
add(F, O, T, I, A, "icu", "10-bed ICU opened Nov 2024", "'A ten-bed ICU was opened'", ED + "37524", "2024-11-16", "high")
add(F, O, T, I, A, "nicu", "14-bed NICU (phototherapy, newborn intensive care)", "'a 14-bed neonatal intensive care unit (NICU)'", "https://en.mmtv.mv/10912", "2026-07-21", "high")
add(F, O, T, I, A, "surgery", "4-theatre OT complex (orthopaedic, eye, women's health, general surgery) opened Nov 2024", "'Four operating theatres were inaugurated'", ED + "37524", "2024-11-16", "high")
add(F, O, T, I, A, "cardiology", "Cardiology listed; GE Vivid E95 cardiovascular ultrasound (echo) from Feb 2026; no cath lab", "'Hulhumale' Hospital has launched the services of the latest Cardiovascular Ultrasound Scan System'", ED + "48752", "2026-03-02", "high")
add(F, O, T, I, A, "ophthalmology", "Ophthalmology introduced 2026 (glaucoma treatment)", "'they recently introduced breast cancer surgery and ophthalmology services'", ED + "53772", "2026-08-29", "high")
add(F, O, T, I, A, "maternity", "Obstetrics & Gynecology (MCGH specialities); women's health OT", "MCGH specialities list HMH for Obstetrics & Gynecology", MCGH, ACC, "medium")
add(F, O, T, I, A, "paediatrics", "Paediatrics (no super-specialists; complex cases to IGMH)", "MCGH specialities list HMH for Paediatrics; 2021: 'lacks super-specialists'", ED + "23640", "2021-12-30", "medium")
add(F, O, T, I, A, "orthopaedics", "Orthopaedics + orthopaedic OT", "MCGH specialities list HMH for Orthopedics", MCGH, ACC, "medium")
add(F, O, T, I, A, "psychiatry", "Psychiatry OPD (MCGH specialities)", "MCGH specialities list HMH for Psychiatry", MCGH, ACC, "medium")
add(F, O, T, I, A, "dermatology", "Dermatology (MCGH specialities)", "MCGH specialities list HMH for Dermatology", MCGH, ACC, "medium")
add(F, O, T, I, A, "emergency", "Emergency department (expanding to 14 ER beds)", "'plans to increase the ER bed capacity to 14'", ED + "37524", "2024-11-16", "high")
add(F, O, T, I, A, "physiotherapy", "Physiotherapy (MCGH specialities)", "MCGH specialities list HMH for Physiotherapy", MCGH, ACC, "medium")

# ======================= Villimale' Hospital =======================
F, T, I = "Villimale' Hospital (MCGH)", "hospital", "Villimale'"
add(F, O, T, I, A, "dermatology", "visiting/periodic: IGMH dermatologist clinic once a week", "'Our doctors visits Vilimale' Hospital once a week'", IGMH + "departments/dermatology", ACC, "high")
add(F, O, T, I, A, "maternity", "Antenatal clinic run by IGMH O&G (no labour room evidence)", "IGMH O&G services list 'Villimale' ANC'", IGMH + "departments/obstetrics-gynecology", ACC, "medium")

# ======================= ADK Hospital (private, Male') =======================
F, O, T, I = "ADK Hospital", "private", "tertiary_hospital", "Male'"
add(F, O, T, I, A, "cardiology", "Cardiology + cardiac catheterisation lab (HITECC, opened Mar 2018), coronary angiography/angioplasty, echo, 5-bed CCU; cardiothoracic & vascular surgery (first bypass in Maldives 2018)",
    "ADK cardiology page lists 'Coronary angiography and angioplasty', 'ECHO'; departments include 'Cardiac thoracic and Vascular Surgery'", ADK + "/cardiology", ACC, "high")
add(F, O, T, I, A, "oncology", "Oncology dept (consultant oncologist): medical oncology/chemotherapy, immunotherapy, targeted therapy. Page lists 'Radiation Oncology' as a heading but no radiotherapy machine exists in Maldives",
    "ADK oncology page", ADK + "/oncology", ACC, "medium")
for cat, det in [("maternity", "Obstetrics & Gynaecology / maternity services"), ("paediatrics", "Paediatrics incl. paediatric neurology & paediatric gastroenterology"),
                 ("psychiatry", "Psychiatry"), ("ophthalmology", "Ophthalmology"), ("ent", "ENT"), ("orthopaedics", "Orthopaedics"),
                 ("dermatology", "Dermatology"), ("ncd_diabetes", "Endocrinology"), ("emergency", "24h emergency care / urgent care"),
                 ("hyperbaric", "Hyperbaric Treatment Unit (monoplace HBOT chambers)")]:
    add(F, O, T, I, A, cat, det, "ADK Departments & Specialties page", ADK, ACC, "high")

# ======================= Tree Top Hospital (private, Hulhumale') =======================
F, T, I = "Tree Top Hospital", "tertiary_hospital", "Hulhumale'"
add(F, O, T, I, A, "cardiology", "Cardiology with cath lab & diagnostics centre (since 2018); renal angioplasty", "'State of the art Catheterization Lab & Diagnostics Centre'", "https://www.treetophospital.com", ACC, "high")
add(F, O, T, I, A, "oncology", "Oncology: chemotherapy, immunotherapy, targeted & hormone therapy, cancer surgery, chemo ports, tumour board; cervical/breast screening packages; no radiotherapy", "Tree Top oncology page 'Available treatments: Chemotherapy, Immunotherapy...'", TT + "/oncology", ACC, "high")
add(F, O, T, I, A, "icu", "ICU managed by intensivists", "'our ICU is managed by highly trained and specialized Intensivists'", TT + "/intensive-care-medicine", ACC, "high")
add(F, O, T, I, A, "nicu", "Fully equipped NICU incl. ventilation", "'We offer a fully equipped neonatal unit (NICU)'", TT + "/neonatology", ACC, "high")
for cat, det in [("maternity", "Obstetrics & gynaecology; Women & Child Centre"), ("paediatrics", "Paediatrics + paediatric surgery"), ("psychiatry", "Psychiatry and psychology"),
                 ("ophthalmology", "Ophthalmology (cataract/glaucoma surgery)"), ("ent", "Otorhinolaryngology (ENT) + audiology"),
                 ("orthopaedics", "Orthopedics, trauma surgery and sports injuries"), ("dermatology", "Dermatology / dermaesthetics"),
                 ("ncd_diabetes", "Endocrinology"), ("emergency", "24/7 Accident & Emergency"), ("physiotherapy", "Rehabilitative centre; home physiotherapy"),
                 ("fertility", "Fertility Centre (IUI/IVF)"), ("surgery", "General surgery, neurosurgery, urology, OMFS (6 theatres)")]:
    add(F, O, T, I, A, cat, det, "Tree Top specialities list (35+ specialties)", TT, ACC, "high")

# ======================= Medica Hospital (private, Male') =======================
F, T, I = "Medica Hospital", "hospital", "Male'"
for cat in ["cardiology", "dermatology", "ent", "maternity", "surgery", "orthopaedics", "ophthalmology", "physiotherapy", "paediatrics", "geriatrics"]:
    det = {"maternity": "Gynecology", "surgery": "General surgery, plastic surgery, urology", "paediatrics": "Pediatric care"}.get(cat, cat.capitalize())
    add(F, O, T, I, A, cat, det, "Medica website services menu", "https://medica.com.mv", ACC, "medium")

# ======================= Care Trust (private, Hulhumale') =======================
F, T, I = "Care Trust Multispecialty Clinic", "specialist_clinic", "Hulhumale'"
add(F, O, T, I, A, "cardiology", "Paediatric cardiology; echocardiogram; doppler", "Care Trust home: 'PEDIATRIC CARDIOLOGY', 'ECHO cardiogram'", "https://caretrust.mv", ACC, "medium")
add(F, O, T, I, A, "maternity", "Fetal medicine & perinatology, prenatal screening, reproductive medicine, gynaecologist", "Care Trust services list", "https://caretrust.mv", ACC, "medium")
add(F, O, T, I, A, "dermatology", "Dermatologist; skin care", "Care Trust doctors list", "https://caretrust.mv", ACC, "medium")

# ======================= Kulhudhuffushi RH (HDh) =======================
F, O, T, I, A = "Kulhudhuffushi Regional Hospital", "public", "regional_hospital", "Kulhudhuffushi", "HDh"
add(F, O, T, I, A, "oncology", "Chemotherapy unit (biosafety cabinets, trained nurses) since 2023, set up with Hulhumale' Hospital; sessions timed to ferry schedule, free",
    "'By 2023, chemotherapy services had been further expanded to ... Kulhudhuffushi Regional Hospital'", MV_URH, "2026-01-25", "high")
add(F, O, T, I, A, "icu", "ICU and CCU ward (nursing ward with ward manager)", "2023 approved org chart: 'ICU and CCU Ward'", KRH_AR, "2023", "high")
add(F, O, T, I, A, "surgery", "OT Unit; consultant surgeons x3, plastic surgery sub-specialist post", "2023 org chart: 'OT Unit', 'Consultant in Surgery x 3'", KRH_AR, "2023", "high")
add(F, O, T, I, A, "emergency", "Accident & Trauma services unit; emergency medicine consultant post", "2023 org chart: 'Accident and Trauma Services Unit'", KRH_AR, "2023", "high")
add(F, O, T, I, A, "psychiatry", "Psychiatry & isolation ward; psychiatry specialist posts x2", "2023 org chart: 'Psychiatry & Isolation ward'", KRH_AR, "2023", "high")
add(F, O, T, I, A, "cardiology", "Cardiology sub-specialist post (approved structure; filling not confirmed); CCU", "2023 org chart: 'Consultant / (Sub) Specialist in Cardiology'", KRH_AR, "2023", "low")
for cat, det in [("ent", "Consultant in ENT x2 (approved posts)"), ("dermatology", "Dermatology specialist posts x2"), ("ophthalmology", "Consultant in Ophthalmology x2"),
                 ("orthopaedics", "Consultant in Orthopaedics x3"), ("maternity", "Consultant in Gynaecology x5"), ("paediatrics", "Paediatrics specialists x5"),
                 ("nicu", "Neonatology specialist post (neonatal unit implied)"), ("physiotherapy", "Senior physiotherapist + physiotherapists x2 + occupational therapist")]:
    add(F, O, T, I, A, cat, det + " - approved org structure 2023", "KRH 2023 annual report org chart (Clinical / Allied Health departments)", KRH_AR, "2023", "medium" if cat != "nicu" else "low")

# ======================= Ungoofaaru RH (R) =======================
F, I, A = "Ungoofaaru Regional Hospital", "Ungoofaaru", "R"
add(F, O, T, I, A, "oncology", "Chemotherapy room (2 chairs) launched Jan 2026 with IGMH Oncology Dept; no resident oncologist; 58 Raa patients on cancer treatment",
    "'Chemotherapy services have been launched at Ungoofaaru Regional Hospital'", MV_URH, "2026-01-25", "high")
add(F, O, T, I, A, "icu", "ICU (Internal Medicine dept) + 'ICU and NICU Unit' nursing unit", "URH Internal Medicine page 'specialized focus on Intensive Care Unit (ICU) care'; 2023 org chart 'ICU And NICU Unit'", URH + "613", ACC, "high")
add(F, O, T, I, A, "nicu", "NICU within Paediatrics dept", "URH departments: Pediatrics 'specialized focus on Neonatal Intensive Care'", URH + "494", ACC, "high")
add(F, O, T, I, A, "cardiology", "Consultant sub-specialist in cardiology on staff", "URH doctors list: 'Consultant Subspecialist in Cardilology'", URH + "486", ACC, "high")
add(F, O, T, I, A, "psychiatry", "Psychiatry dept with psychologists; individual/group therapy", "URH Psychiatry department page", URH + "616", ACC, "high")
add(F, O, T, I, A, "surgery", "Operation theatre service; surgery dept; anaesthesiologist", "URH services: 'Operation Theatre Service'", URH + "290", ACC, "high")
add(F, O, T, I, A, "oncology", "Mammography (breast cancer screening)", "URH services: 'Mammography Service'", URH + "290", ACC, "high")
for cat, det, c in [("ophthalmology", "Consultant ophthalmologist", "high"), ("dermatology", "Consultant dermatologist", "high"), ("ent", "ENT department", "high"),
                    ("maternity", "Obstetrics & Gynaecology dept; midwifery unit", "high"), ("orthopaedics", "Orthopaedics dept", "high"),
                    ("paediatrics", "Paediatrics dept", "high"), ("physiotherapy", "Physiotherapy services", "medium"), ("emergency", "ER unit; accidents & trauma unit (2023 org chart)", "high"),
                    ("geriatrics", "Geriatric care within Internal Medicine", "low")]:
    add(F, O, T, I, A, cat, det, "URH website departments/doctors/services pages", URH + "494", ACC, c)

# ======================= ASMH Thinadhoo (GDh) =======================
F, I, A = "Dr. Abdul Samad Memorial Hospital (ASMH)", "Thinadhoo", "GDh"
add(F, O, T, I, A, "oncology", "Chemotherapy launched 7-8 May 2023 with Hulhumale' Hospital support", "'launched chemotherapy service for cancer patients'", "https://atolltimes.mv/post/news/3569", "2023-05-08", "high")
add(F, O, T, I, A, "oncology", "Mammography service (breast cancer screening)", "ASMH services: 'Mammography Service'", "https://asmh.gov.mv/services", ACC, "high")
add(F, O, T, I, A, "surgery", "Operation theatre; surgeons x2, anaesthetists x2; laparoscopic abdominal surgery (2023)", "ASMH services 'Operation Theatre Service'; doctors list", ASMH_DOC, ACC, "high")
for cat, det in [("maternity", "Gynaecologists x3"), ("paediatrics", "Paediatricians x3"), ("orthopaedics", "Orthopaedicians x2"), ("ent", "ENT specialists x2"),
                 ("dermatology", "Dermatologists x2"), ("ophthalmology", "Ophthalmologist x1"), ("psychiatry", "Psychiatrists x2")]:
    add(F, O, T, I, A, cat, det, "ASMH doctors page (specialists list)", ASMH_DOC, ACC, "high")

# ======================= Addu Equatorial Hospital (S) =======================
F, T, I, A = "Addu Equatorial Hospital (AEH)", "tertiary_hospital", "Hithadhoo", "S"
add(F, O, T, I, A, "cardiology", "Cath lab (installed Oct 2023, operational 28 Jan 2026, run with IGMH National Cardiac Centre): angiography, angioplasty; first primary PCI outside Male' + ICD & permanent pacemaker (visiting NCC team 31 Mar-2 Apr 2026)",
    "'The Cardiac Catheterization Laboratory (Cath Lab) at Equatorial Hospital ... operated in collaboration with IGMH'", ED + "47736", "2026-01-25", "high")
add(F, O, T, I, A, "visiting_specialist", "visiting/periodic: IGMH National Cardiac Centre interventional team visits for PCI/pacemaker/ICD cases", "'doctors who specialize in such operations will make the trip from Male' to AEH once such cases present'", ED + "49650", "2026-04-03", "high")
add(F, O, T, I, A, "cardiology", "CIED (pacemaker/ICD) follow-up clinic opened Jul 2026 with NCCS; 2 cardiologists on staff", "'A Cardiac Implantable Electronic Device (CIED) Follow-up Clinic has been opened at Addu Equatorial Hospital'", ED + "52331", "2026-07-09", "high")
add(F, O, T, I, A, "oncology", "Chemotherapy (one of first atoll hospitals offering it); no medical oncologist listed", "psmnews (via search snippet): chemo 'offered at Addu City, Laamu Atoll Hospital, ASMH, Thaa Atoll Hospital and KRH' (psmnews blocked 403)", PSM_ATOLL_CHEMO, "", "medium")
add(F, O, T, I, A, "icu", "ICU (transferred from Hithadhoo Regional Hospital)", "search summary of psmnews/AEH: 'Emergency, ICU and inpatient services were the last to move over'", "https://psmnews.mv/en/62519", "", "medium")
add(F, O, T, I, A, "ncd_diabetes", "Hiyfahi Clinic: NCD clinic (diabetes, hypertension, dyslipidaemia) since 14 Nov 2022; endocrinologist on staff", "AEH Hiyfahi Clinic page", "https://aeh.gov.mv/our-services/hiyfahi-clinic", ACC, "high")
add(F, O, T, I, A, "paediatrics", "Southern Child Development Centre (developmental/behavioural, since Apr 2021); paediatricians x2", "AEH SCDC page", "https://aeh.gov.mv/our-services/southern-child-development-center", ACC, "high")
add(F, O, T, I, A, "telemedicine", "Tele-consultation request service", "AEH 'Request a Tele-Consultation' page", "https://aeh.gov.mv/for-patients-and-visitors/request-a-tele-consultation", "2023-12-03", "medium")
add(F, O, T, I, A, "emergency", "24/7 Accident & Emergency; emergency medicine specialist", "AEH homepage 'AEH offers 24/7 emergency services'", "https://aeh.gov.mv", ACC, "high")
for cat, det in [("maternity", "Obstetrics & Gynaecology x4"), ("ent", "ENT x3"), ("orthopaedics", "Orthopaedics & trauma surgery x3 (first joint replacement 2018)"),
                 ("surgery", "General surgery x3, urology, anaesthesiology x3"), ("psychiatry", "Psychiatry x2"), ("ophthalmology", "Ophthalmology x2"),
                 ("dermatology", "Dermatology x2"), ("nephrology", "Nephrologist x1")]:
    add(F, O, T, I, A, cat, det, "AEH Find-a-doctor pages 1-8 (specialty counts)", AEH_DOC, ACC, "high")

# IMDC Addu (private)
F, O, T = "I.M.D.C Multi Speciality Hospital", "private", "hospital"
for cat, det in [("surgery", "Operating theatre"), ("emergency", "24/7 emergency dept + ambulance"), ("paediatrics", "Paediatrics"), ("maternity", "Gynecology"),
                 ("dermatology", "Dermatology"), ("ent", "ENT; visiting cochlear implant programme"), ("physiotherapy", "Physiotherapy"),
                 ("visiting_specialist", "visiting/periodic: visiting specialists incl. orthopaedics and ENT/cochlear implant surgeon")]:
    add(F, O, T, "Hithadhoo", A, cat, det, "IMDC website services list (island inferred from MoH surgery data listing IMDC under S. Atoll)", "https://www.imdc.com.mv", ACC, "medium")

# ======================= Other atoll hospitals (chemo / screening / depts) =======================
O = "public"
add("Lhaviyani Atoll Hospital", O, "atoll_hospital", "Naifaru", "Lh", "oncology", "Chemotherapy since Dec 2020 (first outside Greater Male'), dedicated oncology ward/beds, with Hulhumale' Hospital", "'Lhaviyani Atoll Hospital, Naifaru, unveiled its chemotherapy services'", ED + "20982", "2020-12-16", "high")
add("Gan Regional Hospital (Laamu Atoll Hospital)", O, "regional_hospital", "Gan", "L", "oncology", "Chemotherapy (expanded during COVID-19)", "psmnews snippet lists 'Laamu Atoll Hospital' among chemo providers (psmnews blocked 403)", PSM_ATOLL_CHEMO, "", "medium")
add("Thaa Atoll Hospital", O, "atoll_hospital", "Veymandoo", "Th", "oncology", "Chemotherapy (expanded during COVID-19)", "psmnews snippet lists 'Thaa Atoll Hospital' among chemo providers (psmnews blocked 403)", PSM_ATOLL_CHEMO, "", "medium")
add("Baa Atoll Hospital", O, "atoll_hospital", "Eydhafushi", "B", "oncology", "Mammography / breast cancer screening room launched Aug 2025", "'Mammography was launched at Baa Atoll Hospital'", "https://en.mmtv.mv/5420", "2025-08-12", "high")
add("Fuvahmulah Hospital", O, "regional_hospital", "Fuvahmulah", "Gn", "oncology", "Mammography breast cancer screening", "Minister: 'mammography screening ... available at five regional hospitals, as well as Fuvahmulah City Hospital and Baa Atoll Hospital'", MV_2984, "2026-06-23", "medium")
F, I, A = "Haa Alifu Atoll Hospital", "Dhidhdhoo", "HA"
add(F, O, "atoll_hospital", I, A, "icu", "ICU ward census reported 2022", "HA Atoll 2022 annual report: 'ICU Census'", HA_AR22, "2022", "medium")
add(F, O, "atoll_hospital", I, A, "nicu", "NICU census reported 2022", "HA Atoll 2022 annual report: 'NICU' census", HA_AR22, "2022", "medium")
add(F, O, "atoll_hospital", I, A, "maternity", "O&G ward; deliveries & caesareans; gynae OPD", "2022 'Obstetrics & Gynaecology Census'; 2021 'Delivery & Cesarean'", HA_AR22, "2022", "medium")
add(F, O, "atoll_hospital", I, A, "paediatrics", "Paediatrics ward + OPD", "2022 'Paediatrics Census'; 2021 OPD 'Pediatrics'", HA_AR22, "2022", "medium")
add(F, O, "atoll_hospital", I, A, "ent", "ENT OPD", "2021 OPD by specialty incl. 'ENT'", HA_AR21, "2021", "medium")
add(F, O, "atoll_hospital", I, A, "orthopaedics", "Orthopaedics OPD", "2021 OPD by specialty incl. 'Orthopedics'", HA_AR21, "2021", "medium")
F, I, A = "Faafu Atoll Hospital", "Nilandhoo", "F"
for cat, det in [("maternity", "Obstetrics & gynaecology unit, gynae ward"), ("paediatrics", "General paediatrics / paediatric unit"), ("surgery", "Surgery unit & surgical ward"),
                 ("orthopaedics", "Orthopaedics"), ("emergency", "Accident & trauma / emergency response unit")]:
    add(F, O, "atoll_hospital", I, A, cat, det, "F. Nilandhoo 2023 annual report org chart (Specialists)", F_AR, "2023", "medium")
F, I, A = "Dhaalu Atoll Hospital", "Kudahuvadhoo", "Dh"
for cat, det in [("maternity", "Gynaecology"), ("orthopaedics", "Orthopedics"), ("surgery", "Surgery"), ("emergency", "Emergency")]:
    add(F, O, "atoll_hospital", I, A, cat, det, "Dh. Kudahuvadhoo 2023 annual report org chart", DH_AR, "2023", "medium")
add("Vaavu Atoll Hospital", O, "atoll_hospital", "Felidhoo", "V", "maternity", "LIMITED: normal delivery only, no operation theatre / no caesarean; no births in 14 years; C-section planned with new Grade-1 hospital building",
    "'there has been ... a lack of an operation theater'; 'cesarean services cannot be offered from the hospital'", ED + "53397", "2026-08-13", "high")

# ======================= NGO / visiting =======================
add("Tiny Hearts of Maldives", "ngo", "ngo", "Male'", "MLE", "visiting_specialist", "visiting/periodic: annual 'Care for Tiny Hearts' camp with visiting paediatric cardiologists (consultations, echo, fetal heart screening)", "'free consultations with visiting Pediatric Cardiologists, echocardiography sessions, and fetal screenings'", ED + "9559", "2019-03-11", "medium")
add("Cancer Society of Maldives", "ngo", "ngo", "Hithadhoo", "S", "visiting_specialist", "visiting/periodic: breast cancer screening camp with volunteer doctors from Singapore (Feb 2014), planned annually in a different atoll", "'CMS conducted a breast cancer screening at Addu City with the help of voluntary doctors from Singapore'", "https://minivannewsarchive.com/?p=90649", "2014-10", "medium")
for isl in ["Dhangethi", "Dhigurah", "Fenfushi", "Maamigili", "Dhidhdhoo"]:
    add("Cancer Society of Maldives", "ngo", "ngo", isl, "ADh", "visiting_specialist", "visiting/periodic: multi-island cancer awareness & free screening programme (breast, oral, colorectal, cervical, prostate)", "World Cancer Day activity listing 'Cancer awareness & screening program ADh Atoll' (year not shown)", "https://www.worldcancerday.org/activities/cancer-awareness-screening-program-adh-atoll", "", "low")
add("Cancer Society of Maldives", "ngo", "ngo", "", "N", "visiting_specialist", "visiting/periodic: cancer awareness & screening programme in Noonu Atoll (Nov 2023, with BML)", "raajje.mv: separate cancer awareness and screening programmes in Noonu Atoll", "https://raajje.mv/145169", "2023-11-17", "low")

# ======================= Planned (not operational) =======================
add("Hulhumale' Phase 2 tertiary/cancer hospital + Diagnostic Centre for Oncology Services (DCOS)", "public", "planned", "Hulhumale'", "MLE", "oncology", "PLANNED - NOT OPERATIONAL: radiotherapy, PET-CT, 25-bed cancer unit; basic services targeted by 2028 (earlier L. Gan cancer hospital plan cancelled)", "'A dedicated space for Diagnostic Centre for Oncology Services (DCOS) ... where PET Scans, radiation therapy ... will be provided'", ED + "53132", "2026-08-04", "high")

with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows")
