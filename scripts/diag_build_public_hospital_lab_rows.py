"""Build rows.csv for stream D (public hospital laboratory capacity, Maldives).

Evidence was collected manually from hospital websites, gazette.gov.mv notices (tenders /
vacancies), news and MoH annual reports; raw copies are saved next to the output under
data/external/health/services/diagnostics/sources/public_hospital_labs/.
Run: python -I scripts/diag_build_public_hospital_lab_rows.py
"""
import csv
import os

OUT = r"C:\Users\user\Music\Datathon\data\external\health\services\diagnostics\sources\public_hospital_labs\rows.csv"
COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]

G = "https://www.gazette.gov.mv/iulaan/"

# facility key -> (facility_name, operator_type, facility_type, island, atoll)
F = {
    "IGMH": ("Indira Gandhi Memorial Hospital (IGMH)", "public", "tertiary_hospital", "Male", "K"),
    "HMH": ("Hulhumale Hospital", "public", "tertiary_hospital", "Hulhumale", "K"),
    "DH": ("Dharumavantha Hospital", "public", "tertiary_hospital", "Male", "K"),
    "VMH": ("Villimale Hospital", "public", "hospital", "Villimale", "K"),
    "SMH": ("Senahiya Military Hospital", "military", "hospital", "Male", "K"),
    "KRH": ("Kulhudhuffushi Regional Hospital", "public", "regional_hospital", "Kulhudhuffushi", "HDh"),
    "URH": ("Ungoofaaru Regional Hospital", "public", "regional_hospital", "Ungoofaaru", "R"),
    "MRH": ("Muli Regional Hospital", "public", "regional_hospital", "Muli", "M"),
    "GRH": ("Gan Regional Hospital", "public", "regional_hospital", "Gan", "L"),
    "ASMH": ("Dr. Abdul Samad Memorial Hospital (Thinadhoo)", "public", "regional_hospital", "Thinadhoo", "GDh"),
    "AEH": ("Addu Equatorial Hospital", "public", "tertiary_hospital", "Hithadhoo", "S"),
    "HAAH": ("HA. Atoll Hospital (Dhidhoo)", "public", "atoll_hospital", "Dhidhoo", "HA"),
    "SHAH": ("Sh. Atoll Hospital (Funadhoo)", "public", "atoll_hospital", "Funadhoo", "Sh"),
    "NAH": ("N. Atoll Hospital (Manadhoo)", "public", "atoll_hospital", "Manadhoo", "N"),
    "BAH": ("B. Atoll Hospital (Eydhafushi)", "public", "atoll_hospital", "Eydhafushi", "B"),
    "LHAH": ("Lh. Atoll Hospital (Naifaru)", "public", "atoll_hospital", "Naifaru", "Lh"),
    "AAAH": ("AA. Atoll Hospital (Rasdhoo)", "public", "atoll_hospital", "Rasdhoo", "AA"),
    "ADHAH": ("ADh. Atoll Hospital (Mahibadhoo)", "public", "atoll_hospital", "Mahibadhoo", "ADh"),
    "VAH": ("V. Atoll Hospital (Felidhoo)", "public", "atoll_hospital", "Felidhoo", "V"),
    "FAH": ("F. Atoll Hospital (Nilandhoo)", "public", "atoll_hospital", "Nilandhoo", "F"),
    "DHAH": ("Dh. Atoll Hospital (Kudahuvadhoo)", "public", "atoll_hospital", "Kudahuvadhoo", "Dh"),
    "THAH": ("Th. Atoll Hospital (Veymandoo)", "public", "atoll_hospital", "Veymandoo", "Th"),
    "GAAH": ("GA. Atoll Hospital (Villingili)", "public", "atoll_hospital", "Villingili", "GA"),
    "GNH": ("Fuvahmulah Hospital", "public", "atoll_hospital", "Fuvahmulah", "Gn"),
}

ROWS = []


def add(fac, cat, detail, evidence, url, date, conf):
    name, op, ftype, island, atoll = F[fac]
    ROWS.append(dict(zip(COLS, [name, op, ftype, island, atoll, cat, detail, evidence, url, date, conf])))


# ---------------------------------------------------------------- Male / tertiary
IGMH_LAB = "https://www.igmh.gov.mv/en/departments/laboratory-medicine"
add("IGMH", "lab_basic", "24/7 emergency & inpatient lab; OPD 07:30-22:00 daily",
    "IGMH Laboratory Medicine page: OPD daily 07:30-22:00; emergency & inpatient 24/7", IGMH_LAB, "2026", "high")
add("IGMH", "lab_advanced",
    "National reference-level lab: clinical chemistry, haematology, immunology, microbiology, clinical pathology, "
    "molecular diagnostics/PCR, allergy testing, newborn screening; first Total Laboratory Automation in Maldives; "
    "consultant biochemist; refers highly specialised tests to accredited international reference lab (Aasandha-covered; "
    "historically SRL India); 'samples sent abroad' collection window daily",
    "'largest and most advanced medical laboratory in the Maldives'; first TLA system; services list incl. Clinical "
    "Chemistry, Microbiology, Immunology, Molecular Diagnostics; sample referral abroad", IGMH_LAB, "2026", "high")
add("IGMH", "histopathology",
    "Histopathology & cytopathology section with 4 pathology consultants; new tissue processor and automated IHC/ISH "
    "system procured 2025",
    "Lab page lists 'Histopathology & Cytopathology'; gazette tenders: tissue processor for IGMH lab (06 Oct 2025, "
    "iulaan 362719) and automatic IHC/ISH system (10 Dec 2025, iulaan 371353)", IGMH_LAB + " ; " + G + "362719 ; " + G + "371353",
    "2025-12-10", "high")
add("IGMH", "blood_bank", "Hospital blood bank services within IGMH laboratory (MCGH; MBS adjacent)",
    "Lab page services list includes 'Blood Bank Services'", IGMH_LAB, "2026", "high")

add("HMH", "lab_basic", "Hospital laboratory; phlebotomists and lab technologists recruited 2024-2026; Phase II "
    "(Hiyaa Tower) clinic has a lab collection/testing facility",
    "Gazette vacancies: Laboratory Technologist (18 Aug 2026, iulaan 408035); fully automated urine analyser tender "
    "(18 Feb 2016, iulaan 41189)", G + "408035 ; " + G + "41189", "2026-08-18", "high")
add("HMH", "lab_advanced",
    "Specialist-led lab: medical laboratory specialists in haematology and in microbiology & immunology, immuno-haematology/transfusion "
    "specialist, clinical haematology consultants (national thalassaemia/haematology hub; MRI T2* iron studies 2024)",
    "Gazette 30 Sep 2026: 'Medical Laboratory Specialist in Microbiology and Immunology' (iulaan 414574) and '... in Hematology' (iulaan 414577); 'Medical Laboratory "
    "Specialist in Immuno Hematology / Transfusion Medicine' (13 Jul 2026, iulaan 402523); Consultant in Clinical "
    "Hematology (2025-2026)", G + "414574 ; " + G + "414577 ; " + G + "402523 ; " + G + "382360", "2026-09-30", "medium")
add("HMH", "histopathology",
    "Pathology consultant posts; MoH QA official stated histopathology available at tertiary hospitals",
    "Gazette: Consultant in Pathology (06 May 2024 iulaan 288515; 04 Oct 2026 iulaan 415296); PSM News: "
    "'histopathology services are now available at tertiary hospitals'", G + "288515 ; " + G + "415296 ; https://cms.psmnews.mv/en/100078",
    "2026-10-04", "medium")

add("DH", "lab_basic", "Tertiary hospital in Male City Group of Hospitals (MCGH) sharing group lab network with IGMH",
    "Inaugurated as tertiary-level hospital Nov 2024 under MCGH; IGMH network page lists DH", "https://maldivesvoice.mv/1585",
    "2024-11", "medium")
add("DH", "lab_advanced", "Specialised haematology service for MCGH (clinical + lab haematology); routine advanced "
    "tests presumably processed by IGMH group lab",
    "Presidency blog 8 Jul 2025: 'Dharumavantha Hospital signed an agreement to provide Haematology services to the "
    "Male' City Group of Hospitals'",
    "https://blogs.presidency.gov.mv/daily-blogs/at-igmhmv-dharumavantha-hospital-signs-hematology-service-agreement-with-mcgh",
    "2025-07-08", "low")

add("VMH", "lab_basic", "Hospital Grade 1 laboratory (MCGH network); continuous lab technologist/technician recruitment",
    "Gazette: Vili Male' Hospital 'MEDICAL LABORATORY TECHNOLOGIST (CONTRACT)' (31 Jul 2025, iulaan 353374); "
    "Senior MLT posts (2025, iulaan 338079)", G + "353374 ; " + G + "338079", "2025-07-31", "high")
add("VMH", "lab_advanced", "Medical laboratory specialist in microbiology & immunology post (suggests culture/serology "
    "capacity, possibly shared within MCGH)", "Gazette 26 Feb 2025: Vilimale Hospital vacancy 'Medical Laboratory "
    "Specialist in Microbiology and Immunology' (iulaan 330075)", G + "330075", "2025-02-26", "low")
add("SMH", "lab_basic", "Military general hospital (MNDF); lab presumed for a general hospital - no public test list found",
    "Listed as General Hospital in MoH HEMS registry; no lab evidence found online", "https://hems.health.gov.mv", "2026", "low")

# ---------------------------------------------------------------- Regional hospitals
KRH_API = "https://siteapi.krh.gov.mv/api/v1/services"
add("KRH", "lab_basic", "24/7 emergency/inpatient lab; 12 lab staff listed; hub for HDh health-centre samples (Hirimaradhoo, Naivaadhoo, Kurinbi 2020; atoll-wide 2022)",
    "KRH website: Laboratory Service supports emergency and inpatient services 24/7; Diagnostic Laboratory staff list (12); "
    "gazette: transport of lab samples from HDh health centres to KRH (06 Jun 2022, iulaan 195387; 2020 iulaan 125707)",
    KRH_API + " ; https://siteapi.krh.gov.mv/api/v1/diagnostic-therapy ; " + G + "195387", "2026", "high")
add("KRH", "lab_advanced",
    "Clinical chemistry (LFT/RFT/lipids), haematology + coagulation, microbiology culture & sensitivity, automated blood "
    "culture, immunology & serology, HPLC (HbA1c / Hb variants), thalassaemia & DNA testing; consultant haematologist "
    "and pathologist posts",
    "KRH site lists Clinical Chemistry, Hematology incl. coagulation, Microbiology culture & sensitivity, Immunology & "
    "Serology, 'Thalassemia and DNA testing'; gazette tenders: automated microbiology analyser + automated blood culture "
    "analyser (15 Apr 2024, iulaan 285307), HPLC analyser (18 Feb 2024, iulaan 278616); Raajje 2022: MRI, CT, "
    "thalassemia DNA testing introduced",
    KRH_API + " ; " + G + "285307 ; " + G + "278616 ; https://raajje.mv/114382", "2024-04-15", "high")
add("KRH", "histopathology", "Histopathology & cytology listed; pathology consultant / specialist registrar posts",
    "KRH site: 'Histopathology & Cytology - tissue and cell examinations'; 2023 annual report org chart: Consultant in "
    "Pathology; gazette: Specialist Registrar in Pathology (28 May 2025, iulaan 343814)",
    KRH_API + " ; " + G + "343814", "2025-05-28", "high")
add("KRH", "blood_bank", "Hospital blood bank: screening, storage, cross-match, voluntary donation drives",
    "KRH site 'Blood bank service'; blood bank centrifuge tender (2022, iulaan 186880)", KRH_API + " ; " + G + "186880", "2026", "high")
add("KRH", "xray", "Digital X-ray", "KRH site services list: X-ray Service", KRH_API, "2026", "high")
add("KRH", "ultrasound", "Ultrasound scan services", "KRH site services list: Ultrasound Scan Services", KRH_API, "2026", "high")
add("KRH", "ct", "CT scan", "KRH site services list: CT Scan; Raajje 2022", KRH_API + " ; https://raajje.mv/114382", "2026", "high")
add("KRH", "mri", "MRI scan", "KRH site services list: MRI Scan Services; Raajje 2022", KRH_API + " ; https://raajje.mv/114382", "2026", "high")
add("KRH", "mammography", "Mammography screening", "KRH site services list: Mammogram Services", KRH_API, "2026", "high")

URH_LAB = "https://www.urh.gov.mv/?page_id=332"
add("URH", "lab_basic", "Hospital lab serving R atoll; lab technologists recruited for URH and its health centres",
    "Repeated gazette vacancies for Medical Laboratory Technologist 'to work under URH and health centers under URH' "
    "(2022-2026)", URH_LAB + " ; " + G + "375203", "2026-01-05", "high")
add("URH", "lab_advanced",
    "Haematology (CBC, automated haematology analyser), automated coagulation analyser, clinical chemistry panels, "
    "microbiology incl. automated microbiology urine analyser, immunology & serology",
    "URH Laboratory Service page lists Hematology, Clinical Chemistry, Microbiology, Immunology and Serology; gazette "
    "reagent-rental tenders: automated haematology analyser (04 Aug 2024, iulaan 302119), automated coagulation analyser "
    "(17 Aug 2024 iulaan 304146; 12 Jul 2026 iulaan 402172), automated microbiology urine analyser (17 Aug 2024 iulaan "
    "304144; 12 Jul 2026 iulaan 402184)",
    URH_LAB + " ; " + G + "302119 ; " + G + "304146 ; " + G + "402184", "2026-07-12", "high")
add("URH", "histopathology", "Website claims histopathology & cytology and molecular diagnostics with pathologists; "
    "not corroborated by tenders/news (may be generic web copy)",
    "URH Laboratory Service page: 'Histopathology and Cytology ... staffed by laboratory scientists, technicians, and "
    "pathologists'", URH_LAB, "2023-08-12", "medium")
add("URH", "xray", "Digital X-ray, OPG", "URH Radiology page", "https://www.urh.gov.mv/?page_id=716", "2023-08-14", "high")
add("URH", "ultrasound", "Ultrasonography incl. obstetric, Doppler/vascular", "URH Radiology page",
    "https://www.urh.gov.mv/?page_id=716", "2023-08-14", "high")
add("URH", "ct", "GE 128-slice CT", "URH CT Scan Service page", "https://urh.gov.mv/?page_id=352", "2023-07-29", "high")
add("URH", "mammography", "Digital mammography (screening & diagnostic)", "URH Mammography Service page",
    "https://urh.gov.mv/?page_id=357", "2023-07-27", "high")

GRH_SRC = "https://psmnews.mv/en/58736"
add("GRH", "lab_basic", "Regional lab, avg >50 tests/day (2019); maintains lab network of L atoll health centres",
    "PSM News 2019: regional hospital in Laamu runs >50 tests/day; other Laamu labs ~12/day; gazette: equipment for "
    "labs maintained by GRH (13 Mar 2023, iulaan 232840)", GRH_SRC + " ; " + G + "232840", "2023-03-13", "high")
add("GRH", "lab_advanced", "Automated biochemistry analyser (LFT/RFT/lipids etc.) and haematology analyser on "
    "reagent-rental; no evidence found for hormones, microbiology culture or histopathology",
    "Gazette: automated biochemistry analyser 3-yr rental (11 May 2023, iulaan 240397); haematology analyser 3-yr rental "
    "(16 May 2023, iulaan 240976)", G + "240397 ; " + G + "240976", "2023-05-16", "medium")

ASMH = "https://asmh.gov.mv/services"
add("ASMH", "lab_basic", "Regional hospital lab (GDh) staffed by lab scientists & technicians; GDh had 21 public lab "
    "staff in 2020 (largest outside Male/HDh)",
    "ASMH website services: 'Laboratory Services ... laboratory scientists, technicians'; gazette MLT recruitment "
    "(09 Jul 2026, iulaan 401965); MHS 2020 workforce table", ASMH + " ; " + G + "401965", "2026-07-09", "high")
add("ASMH", "lab_advanced", "Likely automated chemistry/haematology given staffing and CT/dialysis services; specific "
    "panels (hormones, culture) not confirmed online",
    "Indirect: lab scientists on staff; dialysis unit (requires RFT/electrolytes); MHS 2020: 21 lab staff in GDh",
    ASMH, "2026", "medium")
add("ASMH", "xray", "Digital X-ray", "ASMH website services list: X-Ray Service", ASMH, "2026", "high")
add("ASMH", "ct", "CT scan", "ASMH website services list: CT Scan Service", ASMH, "2026", "high")
add("ASMH", "mammography", "Mammography", "ASMH website services list: Mammography Service", ASMH, "2026", "high")

add("MRH", "lab_basic", "Hospital lab (M atoll hub, with M. Dhiggaru HC lab as secondary hub); 6 public lab staff in M (2020)",
    "Gazette 13 Jan 2021: MRH tender to carry samples from islands without lab (M. Raiymandhoo HC -> M. Dhiggaru HC); "
    "MHS 2020 workforce", G + "141727", "2021-01-13", "medium")

AEH_BRO = "https://aeh.gov.mv/storage/uploads/5b9a1902-7919-4068-be1c-a6cea60b9d0c/Diagnostic-&-Theraputic-Brochure1.pdf"
AEH_LAB = "https://aeh.gov.mv/our-services/laboratory-medicine"
add("AEH", "lab_basic", "Lab open 08:00-22:00 daily, emergency 24/7; thalassaemia screening Sat-Thu",
    "AEH Laboratory Medicine page (updated 07 Oct 2024)", AEH_LAB, "2024-10-07", "high")
add("AEH", "lab_advanced",
    "Haematology & blood bank, biochemistry & immunology (automated immunology analyser), automated HbA1c "
    "(glycohaemoglobin) analyser, microbiology & serology (automated microbiology analyser), allergy testing analyser, "
    "automated urine analyser, molecular diagnostics; outsources some tests via a 'referral laboratory service' contract",
    "AEH Diagnostic & Therapeutic brochure (2023) lists Hematology & blood bank, Biochemistry & immunology, Microbiology "
    "& Serology, Molecular diagnostics; gazette: HbA1c + immunohaematology analysers (23 Feb 2023, iulaan 230303), "
    "immunology analyser (16 Jan 2023, iulaan 224254), microbiology analyser (2023-2026, iulaan 403489), allergy testing "
    "analyser (16 Nov 2023, iulaan 264281), referral laboratory service tender (28 Feb 2024, iulaan 280481)",
    AEH_BRO + " ; " + G + "230303 ; " + G + "224254 ; " + G + "403489 ; " + G + "280481", "2026-07-20", "high")
add("AEH", "histopathology", "Histopathology & cytology with resident pathologist (tissue samples processed)",
    "AEH brochure: 'Histopathology & Cytology'; lab page: team includes 'a pathologist' testing 'blood, urine, stool, "
    "tissues'", AEH_BRO + " ; " + AEH_LAB, "2024-10-07", "high")
add("AEH", "blood_bank", "Hospital blood bank / transfusion", "AEH brochure: 'Hematology & blood bank'; 'Blood transfusion' "
    "clinical service", AEH_BRO, "2023", "high")
add("AEH", "xray", "X-ray / portable X-ray, fluoroscopy", "AEH brochure radiology list", AEH_BRO, "2023", "high")
add("AEH", "ultrasound", "Ultrasound & Doppler, portable US", "AEH brochure radiology list", AEH_BRO, "2023", "high")
add("AEH", "ct", "CT (since 19 Jan 2019), neuro/peripheral angiography", "AEH brochure: CT scan services started 19 Jan 2019",
    AEH_BRO, "2023", "high")
add("AEH", "mri", "MRI (since 19 Jan 2019)", "AEH brochure: MRI scan services started 19 Jan 2019", AEH_BRO, "2023", "high")
add("AEH", "mammography", "Mammography", "AEH brochure radiology list", AEH_BRO, "2023", "high")
add("AEH", "endoscopy", "Endoscopy (since 19 Jan 2019)", "AEH brochure: Endoscopy services started 19th Jan 2019",
    "https://aeh.gov.mv/storage/uploads/afefdabe-093e-4350-9e30-4006f318bca5/AEH-brochure1.pdf", "2023", "high")

# ---------------------------------------------------------------- Atoll hospitals
add("HAAH", "lab_basic", "Hospital lab (inpatient & outpatient lab statistics); hub for HA Utheemu, Maarandhoo, Vashafaru samples (2020-2021)",
    "HA Atoll Hospital annual report 2022 charts 'Lab_Inpatients / Lab_Outpatients'; gazette: samples from HA Utheemu/"
    "Maarandhoo/Vashafaru HCs to HA Atoll Hospital lab (2020-2021, iulaan 156127, 160056, 165707)",
    "https://health.gov.mv/en/publications (HA Atoll Annual Report 2022) ; " + G + "160056 ; " + G + "165707", "2022", "high")
add("HAAH", "blood_bank", "Blood transfusion services", "HA Atoll Hospital annual report 2022: 'Blood Transfusion Services'",
    "https://health.gov.mv/en/publications (HA Atoll Annual Report 2022)", "2022", "medium")
add("HAAH", "xray", "X-ray", "HA Atoll annual report 2021/2022: 'X-Rays Taken'",
    "https://health.gov.mv/en/publications (HA Atoll Annual Report 2022)", "2022", "high")
add("HAAH", "ultrasound", "Ultrasound incl. antenatal scans (~1000/yr)", "HA Atoll annual report 2022: 'Ultrasound Scans'; 2021: 'Scan Antenatal'",
    "https://health.gov.mv/en/publications (HA Atoll Annual Report 2022)", "2022", "high")

add("SHAH", "lab_basic", "Hospital lab (hub for Sh 'mobile laboratory' sample network); lab renovation 2026",
    "Gazette: Sh Atoll Hospital laboratory renovation (25 Jun 2026, iulaan 399172); mobile laboratory set-up tenders "
    "(2020-2021, iulaan 132394/157772); MLT for Sh Atoll Hospital (iulaan 387862)", G + "399172 ; " + G + "157772",
    "2026-06-25", "high")
add("NAH", "lab_basic", "Hospital lab; senior lab technician posts", "Gazette: N. Atoll Hospital A2 sheet Senior Medical "
    "Laboratory Technician (iulaan 283962); MLT/Senior MLT vacancies (iulaan 303580, 321145)", G + "283962 ; " + G + "321145",
    "2024", "medium")
add("BAH", "lab_basic", "Hospital lab (~10,000 investigations/yr scale chart 2021); B atoll sample network to Kendhoo HC lab",
    "B Atoll Hospital annual report 2021: 'Laboratory services in Baa Atoll Hospital 2021' chart; gazette sample "
    "transport tenders (2020-2021, iulaan 156064)", "https://health.gov.mv/en/publications (Annual Report 2021 B Atoll Hospital) ; " + G + "156064",
    "2021", "high")
add("BAH", "xray", "X-ray (~900 exposures/yr scale)", "B Atoll Hospital annual report 2021: 'X-ray Services in Baa Atoll Hospital in 2021'",
    "https://health.gov.mv/en/publications (Annual Report 2021 B Atoll Hospital)", "2021", "high")
add("LHAH", "lab_basic", "Hospital lab (Lh sample network also uses Kurendhoo HC lab for Olhuvelifushi)", "Gazette: Lh. Atoll Hospital Medical Laboratory Technologist recruitment "
    "(14 Sep 2026, iulaan 412169)", G + "412169", "2026-09-14", "medium")
add("AAAH", "lab_basic", "Hospital lab receiving samples from AA. Ukulhas HC (2020); AA lab network also uses Mathiveri HC lab",
    "Gazette 22 Jul 2020: samples from AA. Ukulhas HC to AA Atoll Hospital (iulaan 131787); lab technician recruitment "
    "(15 Oct 2024, iulaan 312113)", G + "131787 ; " + G + "312113", "2024-10-15", "high")
add("ADHAH", "lab_basic", "Hospital lab; hub for ADh Kunburudhoo, Mandhoo, Hangnaameedhoo, Omadhoo samples",
    "Gazette 2020-2021: samples from ADh HCs brought to 'ADh. Atoll Hospital laboratory' (iulaan 154051, 131815); MLT "
    "screening (26 Dec 2025, iulaan 374012)", G + "154051 ; " + G + "374012", "2025-12-26", "high")
add("VAH", "lab_basic", "Hospital lab; hub for V Fulidhoo, Thinadhoo, Keyodhoo, Rakeedhoo samples",
    "Gazette 26 May 2021: samples from V atoll HCs to 'V. Atoll Hospital laboratory' (iulaan 152533)", G + "152533",
    "2021-05-26", "high")
add("FAH", "lab_basic", "Hospital lab since 7 Apr 2002; hub for F. Dharanboodhoo samples",
    "Wikipedia (Faafu Atoll Hospital): laboratory services began 7 April 2002; gazette: samples F. Dharanboodhoo HC -> "
    "F. Atoll Hospital (2020-2021, iulaan 151274); MLT recruitment 2026 (iulaan 417463)",
    "https://en.wikipedia.org/wiki/Faafu_Atoll_Hospital ; " + G + "151274 ; " + G + "417463", "2026-10-15", "high")
add("DHAH", "lab_basic", "Hospital lab ('Diagnostic and Laboratory Services' unit); hub for Dh Maaenboodhoo, "
    "Rinbudhoo, Hulhudheli samples",
    "Gazette 24 Sep 2020: samples from Dh HCs to Dh. Atoll Hospital (iulaan 134193/134194); 2023 annual report org chart "
    "lists Diagnostic and Laboratory Services", G + "134193 ; " + G + "134194", "2023", "high")
add("GAAH", "lab_basic", "Hospital lab (lab investigations counted)", "GA Atoll annual report 2022 activity chart: "
    "'Lab investigation, Cross Match, Blood transfusion, X ray'", "https://health.gov.mv/en/publications (Ga Atoll Annual Report 2022)",
    "2022", "high")
add("GAAH", "blood_bank", "Cross-match & transfusion", "GA Atoll annual report 2022: 'Cross Match', 'Blood tranfusion'",
    "https://health.gov.mv/en/publications (Ga Atoll Annual Report 2022)", "2022", "medium")
add("GAAH", "xray", "X-ray", "GA Atoll annual report 2022: 'X ray'", "https://health.gov.mv/en/publications (Ga Atoll Annual Report 2022)",
    "2022", "medium")
add("GNH", "lab_basic", "Hospital lab; senior MLT and MLT posts", "Gazette: Fuvahmulah Hospital Senior Medical Laboratory "
    "Technologist screening (14 Jan 2026, iulaan 376551); senior MLT vacancy (iulaan 408739)", G + "376551 ; " + G + "408739",
    "2026-01-14", "medium")
add("THAH", "lab_basic", "Atoll hospital lab; hub for Th. Kinbidhoo and Th. Omadhoo samples (mobile-lab scheme, 2020)",
    "Gazette 06 Feb 2020 (Th. Atoll Hospital, Veymandoo): samples from Kinbidhoo HC and Omadhoo HC to Th. Atoll Hospital; "
    "Kandoodhoo/Vandhoo -> Hirilandhoo HC, Gaadhiffushi -> Thimarafushi HC, Dhiyamigili -> Madifushi HC (iulaan 125753)",
    G + "125753", "2020-02-06", "high")
add("URH", "pcr_molecular", "PCR lab set up at URH (COVID-19 era)", "Gazette 14 Jun 2021: works to establish a PCR lab at "
    "Ungoofaaru Regional Hospital (iulaan 154010)", G + "154010", "2021-06-14", "medium")
add("LHAH", "pcr_molecular", "PCR lab set up at Lh. Atoll Hospital (COVID-19 era)", "Gazette 04 Jul 2021 & 14 Nov 2021: works "
    "to establish PCR lab at Lh. Atoll Hospital (iulaan 155627, 169617)", G + "155627 ; " + G + "169617", "2021-11-14", "medium")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(ROWS)
    print(len(ROWS), "rows ->", OUT)
