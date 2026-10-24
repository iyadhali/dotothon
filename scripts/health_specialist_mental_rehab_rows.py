"""Write curated rows (mental health, drug rehab, geriatrics, physio/rehab, developmental
therapy, sports medicine) for the specialist-services dataset.

Rows were compiled by hand from: MoH HEMS public registry (aggregated professional counts),
MoH/NMHD/NDA annual reports, the Central & Regional Mental Health Services Development Plan
2022-2025, the National Mental Health Strategic Action Plan 2025-2029, Maldives Health
Statistics 2020 (workforce by atoll), hospital and clinic websites, NDA website, and news.

Usage: python -I health_specialist_mental_rehab_rows.py <OUT_CSV>
"""
import csv
import sys

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]

MI = "https://maldivesindependent.com/society/where-to-turn-a-guide-to-the-maldives-mental-health-support-system-and-the-plan-to-rebuild-it-8a78"
SAP = "https://health.gov.mv/storage/uploads/7wzEkvoW/bwjwjfot.pdf"
CRP = "https://health.gov.mv/storage/uploads/NAq7Loeg/opbcrit8.pdf"
MHS20 = "https://health.gov.mv/storage/uploads/79qgJ9YD/jjokopyg.pdf"
HEMS = "https://hems.health.gov.mv/establishments"
KRH23 = "https://health.gov.mv/storage/uploads/0wNN3bwA/ldoamukt.pdf"
URH23 = "https://health.gov.mv/storage/uploads/Ko2x5PYQ/7qsqjacp.pdf"
NMHD25 = "https://health.gov.mv/storage/uploads/rY4V33oB/bhe2r3pj.pdf"
NDA21 = "https://health.gov.mv/storage/uploads/yXqP4LqB/7e5wjavc.pdf"
NDA22 = "https://health.gov.mv/storage/uploads/9kobrEo8/zxb0kwaw.pdf"
NDAC = "https://nda.gov.mv/en/centers"
DHAM24 = "https://health.gov.mv/storage/uploads/Aq7X2doe/8wrxp0qn.pdf"
GA22 = "https://health.gov.mv/storage/uploads/6eY3WxY3/9w5s4p1m.pdf"
HMH_MHC = "https://hmh.gov.mv/hospital/services/mhc"
HMH_CDC = "https://hmh.gov.mv/hospital/services/cdc"
HMH_DMRC = "https://hmh.gov.mv/hospital/services/dmrc"
IGMH_PT = "https://www.igmh.gov.mv/en/departments/physiotherapy-physical-rehabilitation"
IGMH = "https://www.igmh.gov.mv/"
TTH_RC = "https://www.treetophospital.com/specialities/rehabilitative-centre"
TTH_OR = "https://www.treetophospital.com/specialities/orthopedics,-trauma-surgery-and-sports-injuries"
HD = "2026-10-24"  # HEMS pull date

R = []


def add(*a):
    assert len(a) == len(COLS), a
    R.append(dict(zip(COLS, a)))


# ---------------- PUBLIC: Greater Male' ----------------
add("Indira Gandhi Memorial Hospital (IGMH) - National Centre for Mental Health", "public", "tertiary_hospital",
    "Male'", "MLE", "psychiatry",
    "National Centre for Mental Health (est. 25 Mar 2019): psychiatry OPD, psychology, social work, OT; 9-bed inpatient psychiatry unit (2022); central referral point",
    "CMH est. 25 Mar 2019 with 4 psychiatrists, 5 psychologists; 9-bed inpatient unit opened 2022; IGMH waitlist ~1,300 (May 2026)",
    MI, "2026-05-05", "high")
add("Indira Gandhi Memorial Hospital (IGMH)", "public", "tertiary_hospital", "Male'", "MLE", "physiotherapy",
    "Physiotherapy & Physical Rehabilitation dept (IP/OP): musculoskeletal, neuro, cardiopulmonary, ortho/post-surgical, paediatric and geriatric physiotherapy; ~18 physios + OT; separate Speech Pathology & Audiology dept",
    "IGMH departments page lists Physiotherapy & Physical Rehabilitation with staff list",
    IGMH_PT, "2026", "high")
add("Indira Gandhi Memorial Hospital (IGMH)", "public", "tertiary_hospital", "Male'", "MLE", "geriatrics",
    "Geriatric physiotherapy within IGMH physio dept (no dedicated geriatric medicine department listed)",
    "Physio dept services list includes 'Geriatric Physiotherapy'", IGMH_PT, "2026", "medium")
add("Hulhumale' Hospital - Mental Health Centre", "public", "tertiary_hospital", "Hulhumale'", "MLE", "psychiatry",
    "Mental Health Centre: psychiatric consultation, psychotherapy (CBT/DBT), family/group therapy, home-based treatment, elderly mental health; outpatient only; 1 psychiatrist + 2 psychologists via Cadabams (India)",
    "HMH service page; MI guide: outpatient only, waitlist ~10 (May 2026)", HMH_MHC, "2026", "high")
add("Hulhumale' Hospital - Mental Health Centre", "public", "tertiary_hospital", "Hulhumale'", "MLE", "telemedicine",
    "Online (tele-) mental health consultations offered for patients outside Greater Male'",
    "HMH MHC page: 'online consultations for patients outside greater Male''", HMH_MHC, "2026", "high")
add("Hulhumale' Hospital - Child Development Centre", "public", "tertiary_hospital", "Hulhumale'", "MLE", "developmental_therapy",
    "Child Development Centre (opened 2021): developmental paediatrician, multidisciplinary assessment/intervention for developmental delay, autism (PDD), CP, learning disorders; children <15",
    "HMH CDC page; NMH SAP 2025-2029: CDC opened in Hulhumale Hospital in 2021", HMH_CDC, "2026", "high")
add("Hulhumale' Hospital - Disability Management & Rehabilitation Centre (DMRC)", "public", "tertiary_hospital", "Hulhumale'", "MLE", "physiotherapy",
    "DMRC: physiotherapy (electrotherapy, neuro-, cardio-, post-burn rehab), speech therapy, occupational therapy, psychosocial support, skills programme for PWDs",
    "HMH DMRC service page", HMH_DMRC, "2026", "high")
add("Dhamanaveshi (Urban Primary Health Centre) - Mental Health Unit", "public", "primary_care_centre", "Male'", "MLE", "psychiatry",
    "Mental health unit: counselling sessions, mental health home visits (primary-level, not psychiatrist-led)",
    "Dhamanaveshi Annual Report 2024 (Dhivehi): mental health unit, counselling service statistics, MH home visits", DHAM24, "2024", "medium")
add("National Mental Health Department - 1677 National Mental Health Helpline", "public", "helpline", "Male'", "MLE", "telemedicine",
    "24h national mental health helpline 1677 (psychological first aid, crisis management) launched 21 Feb 2024; national coverage incl. all atolls",
    "NMHD Annual Report 2025; MI guide: 2,032 calls by Dec 2024", NMHD25, "2025", "high")
add("Home for People with Special Needs (HPSN)", "public", "residential_care_facility", "Guraidhoo", "K", "psychiatry",
    "Only residential facility for people with severe mental illness; 212 residents (Dec 2024), 178 with mental illness; transferred to MoH (NMHD residential section) Sept 2024; no structured rehab programme",
    "NMH SAP 2025-2029 and NMHD Annual Report 2025", SAP, "2025-02", "high")
add("Home for People with Special Needs (HPSN)", "public", "residential_care_facility", "Guraidhoo", "K", "geriatrics",
    "Residential care incl. frail elderly / geriatric residents (only state long-term residential care facility); new mental health hospital planned on Guraidhoo",
    "Plan 2022-25: residents include frail elderly; HRCM 2009: 46 geriatric patients", CRP, "2022", "medium")
add("Tree Top Hospital - Rehabilitative Centre", "private", "tertiary_hospital", "Hulhumale'", "MLE", "physiotherapy",
    "Rehabilitative Centre: physiotherapy, speech & occupational therapy, audiology; neuro, cardiothoracic, paediatric (CP, autism), geriatric conditions; 14 physios registered in HEMS",
    "TTH Rehabilitative Centre page; HEMS: 14 physiotherapists", TTH_RC, "2026", "high")
add("Tree Top Hospital", "private", "tertiary_hospital", "Hulhumale'", "MLE", "sports_medicine",
    "Orthopaedics, Trauma Surgery and Sports Injuries specialty + sports injury rehab in Rehabilitative Centre (no registered sports-medicine physician found in HEMS)",
    "TTH specialty page 'Orthopedics, Trauma Surgery and Sports Injuries'", TTH_OR, "2026", "medium")
add("Tree Top Hospital", "private", "tertiary_hospital", "Hulhumale'", "MLE", "psychiatry",
    "Psychiatry consultation (1 psychiatrist, 1 psychologist registered)", "HEMS public professional list (aggregated)", HEMS, HD, "medium")
add("Tree Top Hospital", "private", "tertiary_hospital", "Hulhumale'", "MLE", "geriatrics",
    "Geriatric rehabilitation in Rehabilitative Centre; hospital announced home care services", "TTH rehab page lists 'Geriatric conditions'; news item on home care services",
    TTH_RC, "2026", "low")
add("TTH Clinic (Tree Top Hospital Male' City clinic)", "private", "general_clinic", "Male'", "MLE", "physiotherapy",
    "Large outpatient physiotherapy service (19 physiotherapists registered)", "HEMS public professional list; TTH site: 'TTH Clinic Male' City outpatient services'", HEMS, HD, "medium")
add("ADK Hospital", "private", "tertiary_hospital", "Male'", "MLE", "psychiatry",
    "Psychiatry consultation (1 psychiatrist registered)", "HEMS public professional list (aggregated)", HEMS, HD, "medium")
add("Care Trust Multi Speciality Clinic", "private", "specialist_clinic", "Hulhumale'", "MLE", "psychiatry",
    "Psychiatry consultation (1 psychiatrist registered)", "HEMS; clinic site address Reethigas Magu, Hulhumale'", HEMS, HD, "medium")

# ---------------- PUBLIC: regional / atoll hospitals ----------------
add("Ungoofaaru Regional Hospital", "public", "regional_hospital", "Ungoofaaru", "R", "psychiatry",
    "Only atoll-level inpatient psychiatric unit: 4-bed mental health centre, 2 psychiatrists + 1 psychologist; 'Psychiatrist Unit' in org chart",
    "NMH SAP 2025-2029: 'only Ungoofaaru Regional Hospital has established a four bed-mental health center'; MI guide 2026", SAP, "2025-02", "high")
add("Ungoofaaru Regional Hospital", "public", "regional_hospital", "Ungoofaaru", "R", "visiting_specialist",
    "Psychiatry outreach visits to islands in the northern-central region (periodic/visiting)",
    "NMH SAP: 'they conduct outreach visits to the islands in the region'", SAP, "2025-02", "medium")
add("Ungoofaaru Regional Hospital", "public", "regional_hospital", "Ungoofaaru", "R", "physiotherapy",
    "Physiotherapy (2 physiotherapists in R atoll public workforce 2020; 'Therapeutic Unit' in 2023 org chart); speech therapist",
    "MHS 2020 T1.16 workforce by atoll: R physiotherapists=2; Plan 2022-25: 1 speech therapist", MHS20, "2020", "medium")
add("Kulhudhuffushi Regional Hospital", "public", "regional_hospital", "Kulhudhuffushi", "HDh", "psychiatry",
    "Psychiatry consultants (2 psychiatrists), 'Psychiatry & Isolation ward', clinical psychologist, 2 counsellors in structure; consultations, limited MDT",
    "KRH Annual Report 2023 org chart; MHS2020: HDh psychiatrists=2; MI 2026 lists KRH among regional hospitals with psychiatrists", KRH23, "2023", "high")
add("Kulhudhuffushi Regional Hospital", "public", "regional_hospital", "Kulhudhuffushi", "HDh", "physiotherapy",
    "Physiotherapy section (senior physio + 2 physiotherapists + assistant), occupational therapist, 2 speech therapists",
    "KRH Annual Report 2023 org chart; HEMS: 2 SLPs + 1 OT registered; MHS2020 HDh physios=3", KRH23, "2023", "high")
add("Kulhudhuffushi Regional Hospital", "public", "regional_hospital", "Kulhudhuffushi", "HDh", "developmental_therapy",
    "Child development / therapy services (OT, speech therapy, clinical psychologist); listed with CDC capacity for regional child mental health",
    "NMH SAP 2025-2029 baseline lists CDC services in Addu and Kulhudhuffushi; KRH org chart", SAP, "2025-02", "medium")
add("Addu Equatorial Hospital", "public", "tertiary_hospital", "Hithadhoo", "S", "psychiatry",
    "Psychiatry consultations (2 psychiatrists 2020), clinical psychologist, psychologist, assistant psychologist; no inpatient psychiatric unit",
    "MHS2020: S psychiatrists=2; Plan 2022-25 table; MI 2026 lists AEH with psychiatrists", CRP, "2022", "high")
add("Addu Equatorial Hospital - Child Development Centre", "public", "tertiary_hospital", "Hithadhoo", "S", "developmental_therapy",
    "Child Development Centre opened 2022 for children <15 with developmental / mental health needs (MDT); orthotist",
    "NMH SAP 2025-2029: CDC opened in Addu Equatorial Hospital in 2022", SAP, "2025-02", "high")
add("Addu Equatorial Hospital", "public", "tertiary_hospital", "Hithadhoo", "S", "physiotherapy",
    "Physiotherapy (3 physiotherapists in S atoll public workforce 2020)", "MHS 2020 T1.16: S physiotherapists=3", MHS20, "2020", "medium")
add("Dr. Abdul Samad Memorial Hospital (ASMH)", "public", "regional_hospital", "Thinadhoo", "GDh", "psychiatry",
    "Psychiatry consultations (2 psychiatrists per 2021 HR baseline)", "Plan 2022-25 & NMH SAP 2025-29 tables; MI 2026", SAP, "2025-02", "high")
add("Dr. Abdul Samad Memorial Hospital (ASMH)", "public", "regional_hospital", "Thinadhoo", "GDh", "physiotherapy",
    "Physiotherapy (3 physiotherapists in GDh public workforce 2020)", "MHS 2020 T1.16: GDh physiotherapists=3", MHS20, "2020", "medium")
add("Gan Regional Hospital", "public", "regional_hospital", "Gan", "L", "psychiatry",
    "Psychiatry consultations (2 psychiatrists; 1 psychologist 2020; counsellor)", "MHS2020: L psychiatrists=2, psychologists=1; Plan 2022-25; MI 2026", MHS20, "2020", "high")
add("Gan Regional Hospital", "public", "regional_hospital", "Gan", "L", "physiotherapy",
    "Physiotherapy (1 physiotherapist in L public workforce 2020)", "MHS 2020 T1.16: L physiotherapists=1", MHS20, "2020", "medium")
add("Gaafu Alifu Atoll Hospital", "public", "atoll_hospital", "Villingili", "GA", "physiotherapy",
    "Physiotherapy service (1 physiotherapist 2020; physiotherapy listed among services 2022)", "MHS2020 GA physios=1; GA Atoll Annual Report 2022 service table lists 'Physiotheraphy'", GA22, "2022", "medium")
add("Fuvahmulah Hospital", "public", "atoll_hospital", "Fuvahmulah", "Gn", "physiotherapy",
    "Physiotherapy (1 physiotherapist in Gn public workforce 2020)", "MHS 2020 T1.16: Gn physiotherapists=1", MHS20, "2020", "medium")
add("Haa Alifu Atoll Hospital", "public", "atoll_hospital", "Dhidhdhoo", "HA", "physiotherapy",
    "Physiotherapy (1 physiotherapist in HA public workforce 2020)", "MHS 2020 T1.16: HA physiotherapists=1", MHS20, "2020", "medium")
add("Lhaviyani Atoll Hospital", "public", "atoll_hospital", "Naifaru", "Lh", "physiotherapy",
    "Physiotherapy (1 physiotherapist in Lh public workforce 2020)", "MHS 2020 T1.16: Lh physiotherapists=1", MHS20, "2020", "medium")
add("Muli Regional Hospital", "public", "regional_hospital", "Muli", "M", "physiotherapy",
    "Physiotherapy (2 physiotherapists in M public workforce 2020)", "MHS 2020 T1.16: M physiotherapists=2", MHS20, "2020", "medium")

# ---------------- DRUG REHABILITATION (NDA + NGO) ----------------
NDA_ROWS = [
    ("Drug Treatment and Rehabilitation Centre (DTRC) Himmafushi", "residential_rehab_centre", "Himmafushi", "K",
     "Residential rehab (Therapeutic Community model) since 1997, detox and clinical services; designed for 174, ~80 patients due to dilapidation; new 500-bed building (USD5m) foundation laid Sept 2026",
     NDAC, "2026", "high"),
    ("NDA Community Service Centre", "community_rehab_centre", "Male'", "MLE",
     "After-care and direct community treatment programmes (3-6 month community treatment)", NDAC, "2026", "high"),
    ("NDA Gagan Clinic", "outpatient_clinic", "Male'", "MLE",
     "Outpatient detox/withdrawal management consultations, Methadone Maintenance Treatment (MMT), psychiatric consultation", NDAC, "2026", "high"),
    ("NDA Halfway House Hulhumale'", "semi_residential_centre", "Hulhumale'", "MLE",
     "Semi-residential treatment and community reintegration for men and women 18+ (women's section opened 2022)", NDAC, "2026", "high"),
    ("NDA Outpatient Community Rehabilitation Centre - Dhagena", "community_rehab_centre", "Villingili", "GA",
     "Outpatient community rehab for the region; detox for self-referred clients; family support (est. 2021)", NDAC, "2026", "high"),
    ("NDA Drug Detoxification and Community Rehabilitation Centre - Thinadhoo", "detox_rehab_centre", "Thinadhoo", "GDh",
     "Detoxification and community rehabilitation for the southern region", NDAC, "2026", "high"),
    ("NDA Drug Detoxification and Community Rehabilitation Centre - Fuvahmulah", "detox_rehab_centre", "Fuvahmulah", "Gn",
     "Drug treatment, detoxification and community rehabilitation", NDAC, "2026", "high"),
    ("NDA Drug Detoxification and Community Rehabilitation Centre - Hithadhoo", "detox_rehab_centre", "Hithadhoo", "S",
     "Detox and community rehab; methadone treatment started 2022; moved into former Hithadhoo hospital building", NDAC, "2026", "high"),
    ("NDA Vilunu Centre", "residential_rehab_centre", "Hulhudhoo", "S",
     "Treatment/rehabilitation centre built with Government of India grant, opened 2022 (S. Hulhudhoo/Hulhumeedhoo)", NDAC, "2026", "high"),
]
for name, ftype, isl, at, det, url, dt, conf in NDA_ROWS:
    add(name, "public", ftype, isl, at, "drug_rehab", det, "NDA website treatment centres list (9 centres); NDA annual reports 2021-22", url, dt, conf)
add("NDA Gagan Clinic", "public", "outpatient_clinic", "Male'", "MLE", "psychiatry",
    "Psychiatric consultation for substance-use clients", "NDA centres page: services incl. 'Psychiatric consultation'", NDAC, "2026", "high")
add("Drug Offender Remand Centre (with detox facility)", "public", "remand_detox_centre", "Gulhifalhu", "K", "drug_rehab",
    "First drug offender remand centre (opened 2021) with detoxification; 2022 decision to run as central detox centre; not on current NDA centre list (status uncertain)",
    "NDA Annual Reports 2021 & 2022 (Dhivehi)", NDA22, "2022", "medium")
add("NDA Drug Detoxification and Community Rehabilitation Centre - Hanimaadhoo", "public", "detox_rehab_centre", "Hanimaadhoo", "HDh", "drug_rehab",
    "Listed among NDA centres in 2021 annual report; NOT on 2026 NDA website list - may be closed/inactive",
    "NDA Annual Report 2021 contents: centre (HDh. Hanimaadhoo)", NDA21, "2021", "low")
add("Journey (NGO)", "ngo", "ngo_centre", "Male'", "MLE", "drug_rehab",
    "Recovery support NGO (est. 2005): peer/group counselling, aftercare for recovering users, daily outreach, prevention (RISE programme on 13 islands)",
    "Wikipedia: Journey (NGO), address G. Greenge, Male'", "https://en.wikipedia.org/wiki/Journey_(NGO)", "2020", "medium")

# ---------------- NGO disability / developmental ----------------
add("Care Society", "ngo", "ngo_centre", "Male'", "MLE", "developmental_therapy",
    "Care Development Centre, Care Therapy & Rehabilitation Services for persons with disabilities; offices Male' (Sosun Villa) and Hulhumale'",
    "caresociety.org.mv: development centres, therapy and rehabilitation services", "https://caresociety.org.mv/", "2026", "high")
add("Care Society", "ngo", "ngo_centre", "Hulhumale'", "MLE", "physiotherapy",
    "Therapy & rehabilitation services for PWDs (Hulhumale' premises H1-G-04/05)", "caresociety.org.mv address & programmes", "https://caresociety.org.mv/", "2026", "medium")
add("Care Society - Community Based Rehabilitation Programme", "ngo", "outreach_programme", "", "", "visiting_specialist",
    "Community-based rehabilitation (CBR) & outreach programme in islands (periodic; ~30 CBR/outreach activities 2023-25); islands not itemised",
    "caresociety.org.mv: 'Community Based Rehabilitation Program', '30 CRB & outreach program'", "https://caresociety.org.mv/", "2025", "low")
add("Maldives Autism Association", "ngo", "ngo_centre", "Male'", "MLE", "developmental_therapy",
    "Services for children with neurodevelopmental conditions (autism); island assumed Male' (not verified)",
    "NMH SAP 2025-29: 'Maldives Autism Association and Care Society ... provide services for children with neurodevelopmental challenges'", SAP, "2025-02", "low")

# ---------------- PRIVATE clinics (HEMS public registry, aggregated counts) ----------------
# (name, facility_type, island, atoll, category, detail, confidence)
P = [
    ("Institute For Counselling And Psychotherapy (ICP)", "therapeutic_clinic", "Male'", "MLE", "psychiatry", "Private psychological services: assessment, psychotherapy, behaviour therapy (est. 2015); address Bodufungandu Magu, Male'", "high"),
    ("Institute Of Mental Well Being", "specialist_clinic", "Male'", "MLE", "psychiatry", "Private mental health clinic (landline 333-xxxx Male'); cited by MI as fast private access", "medium"),
    ("VCare Counselling and Psychotherapy Centre", "therapeutic_clinic", "Male'", "MLE", "psychiatry", "Counselling/psychotherapy (12 counsellors/psychologists registered); Villa College; Aasandha full coverage", "medium"),
    ("Faruvaa Clinic", "general_clinic", "Male'", "MLE", "psychiatry", "2 psychiatrists registered; Husnuheenaa Magu, Galolhu", "medium"),
    ("Elite Medical Center", "general_clinic", "Male'", "MLE", "psychiatry", "1 psychiatrist + 7 psychologists/counsellors; Aasandha full coverage for MH", "medium"),
    ("Eve Clinic", "general_clinic", "Male'", "MLE", "psychiatry", "2 psychiatrists + 5 psychologists; also physio/OT/speech; Aasandha full coverage for MH", "medium"),
    ("Pulse Medical and Diagnostics", "general_clinic", "Male'", "MLE", "psychiatry", "1 psychiatrist + 1 psychologist registered", "medium"),
    ("Family Care Clinic and Scan Center", "general_clinic", "Male'", "MLE", "psychiatry", "1 psychiatrist + 4 psychologists/counsellors registered", "medium"),
    ("Thasalli Medical Care", "general_clinic", "Male'", "MLE", "psychiatry", "1 psychiatrist registered", "medium"),
    ("Spectrum Child Development Center", "general_clinic", "Male'", "MLE", "developmental_therapy", "Developmental paediatrician, 9 psychologists, 5 OT/speech, physio; autism & developmental delay; Alhige Buruzu Magu, Male'", "high"),
    ("Knowhub", "therapeutic_clinic", "Male'", "MLE", "developmental_therapy", "OT/speech (3), psychologists (2), physio (1)", "medium"),
    ("Azmi Naeem Medical and Diagnostic Centre (AMDC)", "general_clinic", "Male'", "MLE", "physiotherapy", "4 physiotherapists; site lists physiotherapy/rehab & psychiatry; Shaariuvarudhee, Male'", "medium"),
    ("Physio Solutions", "therapeutic_clinic", "Male'", "MLE", "physiotherapy", "Private physiotherapy clinic (2 physios; landline 3314455)", "medium"),
    ("TotalPhysio", "therapeutic_clinic", "Male'", "MLE", "physiotherapy", "Private physiotherapy clinic (2 physios; landline 3301704)", "medium"),
    ("Pain Clinic (Medius)", "general_clinic", "Male'", "MLE", "physiotherapy", "Pain management with physiotherapy; Haveeree Hingun, Male'", "medium"),
    ("Pine Tree Medic Care Sh. Funadhoo", "general_clinic", "Funadhoo", "Sh", "psychiatry", "2 psychologists/counsellors registered at Funadhoo branch (psychological services, not psychiatrist)", "medium"),
    ("Fuvahmulah Medical Centre", "general_clinic", "Fuvahmulah", "Gn", "physiotherapy", "2 physiotherapists registered", "medium"),
    ("Bluspan Care Dhidhdhoo", "therapeutic_clinic", "Dhidhdhoo", "HA", "physiotherapy", "Branch of Blue Span physio group: 1 physio + 2 OT/speech therapists", "high"),
    ("Bluspan Care Thulusdhoo", "therapeutic_clinic", "Thulusdhoo", "K", "physiotherapy", "Branch of Blue Span physio group: 1 physio + 2 OT/speech therapists", "high"),
    ("AIMS Diagnostic Care", "general_clinic", "Hithadhoo", "S", "psychiatry", "1 psychiatrist + 2 psychologists (Addu landline 689-xxxx; island within Addu not verified)", "low"),
    ("AIMS Diagnostic Care", "general_clinic", "Hithadhoo", "S", "physiotherapy", "2 physiotherapists (Addu landline; island within Addu not verified)", "low"),
    ("CyMa Care Hulhumale'", "therapeutic_clinic", "Hulhumale'", "MLE", "developmental_therapy", "OT/speech (3), psychologist (1)", "medium"),
    ("Physio & Autism Clinic - Hulhumale'", "therapeutic_clinic", "Hulhumale'", "MLE", "physiotherapy", "Physio and autism therapy clinic", "medium"),
]
for name, ft, isl, at, cat, det, conf in P:
    add(name, "private", ft, isl, at, cat, det + "; source HEMS public registry (aggregated counts)", "HEMS registry listing / professional counts", HEMS, HD, conf)

# Private clinics whose island is not published in HEMS (most likely Greater Male')
U = [
    ("CyMa Care", "developmental_therapy", "9 psychologists + 7 OT/speech; Aasandha full coverage for MH"),
    ("Blyss Multi-Specialty Therapy Centre", "psychiatry", "1 psychiatrist + 11 psychologists/counsellors"),
    ("Central Medical Center", "psychiatry", "12 psychologists/counsellors"),
    ("Eve Clinic West Park", "psychiatry", "1 psychiatrist + 15 psychologists; 9 physios"),
    ("Eve Clinic Vinares", "psychiatry", "1 psychiatrist + 6 psychologists; 3 physios"),
    ("Shifaa Medical", "psychiatry", "2 psychiatrists + 1 psychologist"),
    ("D.S.M Clinic", "psychiatry", "1 psychiatrist + 1 psychologist"),
    ("Pro Care Clinic & Dental Centre", "psychiatry", "1 psychiatrist"),
    ("Kulunu Medical Clinic", "psychiatry", "3 psychologists; Aasandha full coverage for MH"),
    ("Mednova Medical Center", "psychiatry", "1 psychologist + OT/speech; Aasandha full coverage for MH"),
    ("Mindcare Clinic", "psychiatry", "Psychological services"),
    ("Mipstar Clinic", "psychiatry", "Psychological services (Maldives Institute for Psychological Services Training & Research)"),
    ("Nafsu Psychological Services", "psychiatry", "3 psychologists/counsellors"),
    ("SafeSpace Psychological Clinic", "psychiatry", "Psychological clinic"),
    ("Zen Medi Clinic", "psychiatry", "3 psychologists/counsellors"),
    ("MIOT Rehab Centre - Maldives", "physiotherapy", "Specialist in Physical Medicine & Rehabilitation (only PM&R specialist in registry), 2 physios, 2 OT/speech, 1 psychiatrist"),
    ("Wellcare Physiotherapy & Sports Rehabilitation", "sports_medicine", "Sports rehabilitation physiotherapy clinic (2 physiotherapists; no sports-medicine physician)"),
    ("Wellcare Physiotherapy & Sports Rehabilitation", "physiotherapy", "2 physiotherapists"),
    ("Moving Cure", "physiotherapy", "1 physiotherapist + 1 psychiatrist"),
    ("Recovery Room", "physiotherapy", "3 physiotherapists"),
    ("HEAL Physio and Wellness Clinic", "physiotherapy", "2 physiotherapists"),
    ("Physio Cure", "physiotherapy", "Physiotherapy clinic"),
    ("Physio Clinic (Blue Span)", "physiotherapy", "Physiotherapy clinic (Blue Span group HQ)"),
    ("Island Polyclinic", "physiotherapy", "2 physiotherapists"),
    ("Magey Physio", "physiotherapy", "Physiotherapy clinic"),
    ("Bulbul Therapy Center", "developmental_therapy", "4 OT/speech + 3 psychologists"),
    ("Bulbul Multi Rehab Clinic", "developmental_therapy", "OT/speech + psychologist"),
    ("Alai Clinic", "developmental_therapy", "6 psychologists + OT/speech"),
    ("Alai Play and Learn Therapy Center", "developmental_therapy", "5 psychologists + OT/speech"),
    ("Child Development Clinic", "developmental_therapy", "11 OT/speech + 3 psychologists"),
    ("Great Minds", "developmental_therapy", "Occupational, speech therapy, special education, early intervention"),
    ("Early Intervention Therapy Centre", "developmental_therapy", "Early intervention therapy (Blue Span group)"),
    ("Bliss Care", "developmental_therapy", "OT/speech (2), physio, psychologist"),
    ("Kulhelama Therapy", "developmental_therapy", "Speech/OT therapy"),
    ("Huvadhoo Therapy Clinic", "developmental_therapy", "Therapy clinic (name suggests Huvadhoo atoll, island unverified)"),
]
for name, cat, det in U:
    add(name, "private", "therapeutic_or_general_clinic", "", "", cat,
        det + "; island NOT published in HEMS public list (likely Greater Male')",
        "HEMS registry listing / professional counts (aggregated)", HEMS, HD, "low")

# ---------------- Sports medicine: negative/structural evidence ----------------
add("Ministry of Youth Empowerment, Sports and Fitness", "public", "ministry", "Male'", "MLE", "sports_medicine",
    "No sports medicine unit/clinic found on ministry website departments (Sports Dept, Projects, MNIS, COS); no 'sports medicine' speciality among registered professionals in HEMS - treat as GAP",
    "sports.gov.mv departments pages reviewed; HEMS speciality list", "https://sports.gov.mv/dv/departments", "2026-10", "low")

with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(R)
print(len(R), "rows ->", sys.argv[1])
