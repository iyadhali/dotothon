"""Build imaging rows (CT/MRI/mammography/endoscopy/X-ray/ultrasound) for Maldives diagnostics dataset.
Output: data/external/health/services/diagnostics/sources/imaging/rows.csv
Run: python -I scripts/imgfork_build_imaging_rows.py
"""
import csv, os

OUT = r"C:\Users\user\Music\Datathon\data\external\health\services\diagnostics\sources\imaging\rows.csv"
COLS = ["facility_name","operator_type","facility_type","island","atoll","service_category",
        "service_detail","evidence","source_url","source_date","confidence"]

# source shortcuts
IGMH_RAD = "https://www.igmh.gov.mv/en/departments/radiology"
IGMH_GI = "https://www.igmh.gov.mv/en/departments/gastroenterology"
DHARU = "https://edition.mv/news/10009"
HMH19 = "https://edition.mv/workshop/10344"
HMH26 = "https://edition.mv/news/53108"
HMH_MAMMO = "https://presidency.gov.mv/Press/Article/22430"
ADK_MRI = "https://edition.mv/news/27430"
ADK_3T = "https://atolltimes.mv/post/news/152"
ADK_MAMMO = "https://maldivesindependent.com/news-in-brief/adk-to-offer-mammography-and-digital-x-ray-services-13722"
ADK_CT = "https://adkhospital.com/en/page/news-and-events/launching-128-slice-ct-system"
ADK_RAD = "https://www.adkhospital.mv/departments/imaging-and-radiology"
ADK_GI = "https://www.adkhospital.mv/departments/gastroenterology"
TTH_RAD = "https://adhadhu.com/41525"
TTH_RAD2 = "https://www.treetophospital.com/specialities/radiology"
TTH_GI = "https://www.treetophospital.com/specialities/gastroenterology"
MEDICA = "https://medica.com.mv/service/radiology/"
CARETRUST = "https://caretrust.mv"
KRH_API = "https://siteapi.krh.gov.mv/api/v1/services"
KRH_CT19 = "https://avas.mv/en/71474"
URH_WP = "https://www.urh.gov.mv/?page_id=716"
URH_CT = "https://www.urh.gov.mv/?page_id=352"
URH_VP = "https://presidency.gov.mv/Press/Article/26171"
URH_MRI = "https://health.gov.mv/dv/news/ungoofaaru-reejanal-hospital-taarsharee-fenvarah-badhalu-kohdhehvaane-ministaru"
ASMH = "https://asmh.gov.mv/about-us"
ASMH_SVC = "https://asmh.gov.mv/services"
ASMH_RAAJJE = "https://raajje.mv/183308"
AEH = "https://aeh.gov.mv/storage/uploads/5b9a1902-7919-4068-be1c-a6cea60b9d0c/Diagnostic-&-Theraputic-Brochure1.pdf"
AEH2 = "https://aeh.gov.mv/storage/uploads/afefdabe-093e-4350-9e30-4006f318bca5/AEH-brochure1.pdf"
GAN_CT = "https://presidency.gov.mv/Press/Article/24045"
GAN_XR = "https://raajje.mv/116745"
MAMMO7 = "https://en.mmtv.mv/10677"
FUV_CT = "https://health.gov.mv/dv/news/fuvahmulaku-hospitalugai-seetee-skeynge-idhumai-rasmeekoh-fashaifi"
BAA_MAMMO = "https://en.mmtv.mv/5420"
BAA_MAMMO_MOH = "https://health.gov.mv/dv/news/uramatheege-kensaru-hurikan-dhenegathumah-kuraa-skeyning-memografeege-idhumai-batholhugai-fashaifi"
AR_IDX = "https://health.gov.mv/en/publications (facility annual report, local copy in data/external/health/moh_annual_reports)"
MHS2020 = "MoH Maldives Health Statistics 2020, section 1.1.6 Diagnostics (local copy data/external/health/moh_maldives_health_statistics/MHS2020_jjokopyg.pdf)"
NAH = "https://nah.gov.mv"
GA_XR = "https://edition.mv/news/54470"
MULI_STUDY = "https://ejhm.journals.ekb.eg/article_415897.html"
SENAHIYA = "https://psmnews.mv/en/53007"
IMDC = "https://imdctest.simdi.com/about.html"
MAAHARAA = "https://maaharaa.health.gov.mv/Public/Home/ListHealthCare"
MOH_XR_HC = "https://psmnews.mv/en/169657"

rows = []
def add(fac, op, ftype, island, atoll, cat, detail, evid, url, date, conf):
    rows.append(dict(zip(COLS, [fac, op, ftype, island, atoll, cat, detail, evid, url, date, conf])))

# ---------------- Greater Male ----------------
F = "Indira Gandhi Memorial Hospital (IGMH) / Dharumavantha Hospital"
add(F,"public","tertiary_hospital","Male","K","ct","128-slice CT and dual-source/dual-energy CT; 24/7 emergency imaging; CT-guided biopsy; dental cone-beam CT","IGMH Radiology dept page lists 128 slice CT and dual source CT for trauma, oncology, stroke, angiography",IGMH_RAD,"2026","high")
add(F,"public","tertiary_hospital","Male","K","mri","1.5T and 3.0T MRI (first public MRI installed Nov 2015)","IGMH Radiology page: MRI 1.5T and 3.0T; Maldives Independent 2015: IGMH set up first MRI",IGMH_RAD,"2026","high")
add(F,"public","tertiary_hospital","Male","K","mammography","2D and 3D digital mammography / breast tomosynthesis; screening & diagnostic; US-guided hook-wire localisation","IGMH Radiology page: Mammography 2D and 3D / Digital Breast Tomosynthesis",IGMH_RAD,"2026","high")
add(F,"public","tertiary_hospital","Male","K","ultrasound","Abdominal, pelvic, obstetric, vascular, small parts US; US-guided biopsy/drainage; also bone densitometry (DEXA)","IGMH Radiology page: Ultrasound real-time imaging; IGMH says five portable USG machines in use (2023)",IGMH_RAD,"2026","high")
add(F,"public","tertiary_hospital","Male","K","xray","Digital radiography, fluoroscopy, C-arm in OT, DEXA","IGMH Radiology page: Digital Radiography (X-Ray), Fluoroscopy, C-arm",IGMH_RAD,"2026","high")
add(F,"public","tertiary_hospital","Male","K","endoscopy","Diagnostic and therapeutic upper GI endoscopy (gastroenterology dept); endoscopy/colonoscopy/bronchoscopy suite on 7th floor of Dharumavantha tower","IGMH Gastroenterology page lists diagnostic & therapeutic upper GI endoscopy; Edition 2019: 7th floor endoscopy, colonoscopy, bronchoscopy",IGMH_GI,"2026","high")

F = "Vilimale' Hospital"
add(F,"public","hospital","Villimale","K","ultrasound","Weekly OPD ultrasound clinic staffed by IGMH radiology","IGMH Radiology page: 'Dedicated Ultrasound clinic in Villimale hospital - contributes weekly for OPD ultrasounds'",IGMH_RAD,"2026","high")
add(F,"public","hospital","Villimale","K","xray","General X-ray assumed at Grade-1 hospital (not directly confirmed)","Inferred from hospital tier (Hospital Grade 1, MHCC); not explicitly documented",MHS2020,"2020","low")

F = "Hulhumale' Hospital"
add(F,"public","tertiary_hospital","Hulhumale","K","mri","One MRI machine operating (radiology dept opened Apr 2019); second MRI being procured 2026","Edition 2019: MRI available with radiology dept opening; Edition Aug 2026: 'We currently have a machine that is in operation'",HMH26,"2026-08-03","high")
add(F,"public","tertiary_hospital","Hulhumale","K","mammography","Mammography launched 14 Oct 2019 (oncology dept anniversary)","President's Office: First Lady launches Mammography Services at Hulhumale Hospital",HMH_MAMMO,"2019-10-14","high")
add(F,"public","tertiary_hospital","Hulhumale","K","xray","Radiology department X-ray; new X-ray machines announced for installation","Radiology department inaugurated 2019; CEO said new MRI and X-ray machines to be installed (PSM, undated)",HMH19,"2019-04-28","high")
add(F,"public","tertiary_hospital","Hulhumale","K","ultrasound","Ultrasound in radiology/obstetric services (inferred from radiology dept + O&G/tertiary status)","Radiology dept operational since 2019; tertiary licence 2024",HMH19,"2019-04-28","medium")
add(F,"public","tertiary_hospital","Hulhumale","K","ct","CT announced as '2-3 weeks away' in Apr 2019; later reports say hospital 'making arrangements' to start CT; no launch confirmed","Edition 2019: mammography and CT 'might take a further 2-3 weeks'; no subsequent confirmation found",HMH19,"2019-04-28","low")

F = "ADK Hospital"
add(F,"private","private_hospital","Male","K","mri","3T Siemens MAGNETOM Lumina (Mar 2023), ~90 scans/day capacity; first MRI in Maldives (~2003)","Edition 2023: ADK introduces 3T MRI; ADK was first to install MRI in the Maldives",ADK_MRI,"2023-03-16","high")
add(F,"private","private_hospital","Male","K","ct","Siemens SOMATOM Definition AS 128-slice CT (CT angiography, cardiac, neuro, vascular)","ADK news: Launching of SOMATOM Definition AS 128 slice CT System (page now 404; seen via search snippet, ~2016)",ADK_CT,"2016-03","medium")
add(F,"private","private_hospital","Male","K","mammography","Mammography introduced 2010 (first in country)","Minivan/Maldives Independent 2010: ADK introduced mammography and digital x-ray services for the first time in the country",ADK_MAMMO,"2010-11-24","medium")
add(F,"private","private_hospital","Male","K","xray","Digital X-ray (since 2010); Imaging & Radiology dept with 4 radiologists","ADK Imaging and Radiology Department page lists consultant radiologists",ADK_RAD,"2026","high")
add(F,"private","private_hospital","Male","K","ultrasound","Ultrasound scanning in Imaging & Radiology dept","ADK Imaging and Radiology Department page (radiologists tagged 'Scan')",ADK_RAD,"2026","high")
add(F,"private","private_hospital","Male","K","endoscopy","Endoscopy, colonoscopy, therapeutic endoscopy (gastroenterology dept)","ADK Gastroenterology Department page: Endoscopy, Colonoscopy, Therapeutic Endoscopy",ADK_GI,"2026","high")

F = "Tree Top Hospital"
for cat, det in [("mri","MRI (popular, high demand)"),("ct","CT scans"),("mammography","Mammography"),
                 ("xray","X-ray and fluoroscopy; bone densitometry"),("ultrasound","Ultrasound")]:
    add(F,"private","private_hospital","Hulhumale","K",cat,det,"Adhadhu 2023: TTH radiology services include MRI, X-ray, Fluoroscopy, CT scans, Bone Densitometry, Ultrasound, Mammography; TTH radiology page",TTH_RAD,"2023-08-14","high")
add(F,"private","private_hospital","Hulhumale","K","endoscopy","Endoscopy and colonoscopy (gastroenterology)","TTH Gastroenterology page: 'presently offers ... Endoscopy, Colonoscopy'",TTH_GI,"2026","high")

F = "Medica Hospital"
add(F,"private","private_hospital","Male","K","xray","X-ray (radiology dept)","Medica radiology page: services offered X-ray, Ultrasound",MEDICA,"2024-09-02","high")
add(F,"private","private_hospital","Male","K","ultrasound","Ultrasound incl. antenatal, Doppler, breast US","Medica radiology page: services offered X-ray, Ultrasound; radiologist profile lists antenatal scan, arterial Doppler",MEDICA,"2024-09-02","high")

F = "Care Trust Multi Speciality Clinic"
add(F,"private","private_clinic","Male","K","xray","X-ray","Care Trust website: services range from laboratory services, X-ray, ultrasound imaging, doppler studies and ECHO",CARETRUST,"2026","high")
add(F,"private","private_clinic","Male","K","ultrasound","Ultrasound imaging, Doppler studies (radiologist on staff)","Care Trust website: X-ray, ultrasound imaging, doppler studies",CARETRUST,"2026","high")

F = "Senahiya Military Hospital"
add(F,"military","military_hospital","Male","K","xray","X-ray machine donated by India (MNDF hospital, open to public); CT/MRI announced as plans (2019) but not confirmed","PSM News: India donated an X-ray machine and an ultrasound machine to Senahiya (search snippet; psmnews blocked 403)",SENAHIYA,"","medium")
add(F,"military","military_hospital","Male","K","ultrasound","Ultrasound machine donated by India","PSM News: India donated X-ray and ultrasound machines to Senahiya (search snippet)",SENAHIYA,"","medium")

F = "Family Care Clinic and Scan Centre"
add(F,"private","private_clinic","Male","K","ultrasound","'Scan centre' in name; presumed ultrasound scanning (not verified)","Maaharaa licensed facility list: Family Care Clinic and Scan Centre, H. Azum, Ameenee Magu, Male'",MAAHARAA,"2026","low")

# ---------------- HA ----------------
F = "HA. Atoll Hospital (Dhidhoo)"
add(F,"public","atoll_hospital","Dhidhoo","HA","xray","3,126 X-rays taken in 2021; new building with CT room, X-ray room and USG room contracted Nov 2025 (6-month build)","HA Atoll Hospital Annual Report 2021: 'Total: 3126 X-Rays Taken'",AR_IDX,"2021","high")
add(F,"public","atoll_hospital","Dhidhoo","HA","ultrasound","1,168 antenatal scans in 2021; ~1,000 ultrasound scans 2022","HA Atoll Hospital Annual Report 2021 ('Scan Antenatal 1168') and HA Atoll Annual Report 2022 ('Ultrasound Scans')",AR_IDX,"2022","high")

# ---------------- HDh ----------------
F = "Kulhudhuffushi Regional Hospital"
add(F,"public","regional_hospital","Kulhudhuffushi","HDh","ct","CT since Oct 2019 (first CT outside Male region, with cardiac centre)","KRH services API lists 'CT Scan'; Avas 2019: KRH officially began CT scan and Cardiac Center services",KRH_API,"2026","high")
add(F,"public","regional_hospital","Kulhudhuffushi","HDh","mri","MRI scan services","KRH services API: 'Kulhudhuffushi Regional Hospital provides Magnetic Resonance Imaging (MRI) scans'; radiology team covers X-Ray, CT, MRI, Ultrasound",KRH_API,"2026","high")
add(F,"public","regional_hospital","Kulhudhuffushi","HDh","mammography","Mammography screening","KRH services API: 'Mammogram Services'",KRH_API,"2026","high")
add(F,"public","regional_hospital","Kulhudhuffushi","HDh","ultrasound","Ultrasound scan services","KRH services API: 'Ultrasound Scan Services'",KRH_API,"2026","high")
add(F,"public","regional_hospital","Kulhudhuffushi","HDh","xray","Digital X-ray","KRH services API: 'X-ray Service ... modern digital X-ray technology'",KRH_API,"2026","high")

# ---------------- Sh ----------------
F = "Sh. Atoll Hospital (Funadhoo)"
add(F,"public","atoll_hospital","Funadhoo","Sh","xray","General X-ray (atoll hospital tier); mammography being introduced 2026","MHS2020: X-ray and ultrasound available across most facilities incl. atoll hospitals; Minister Jul 2026: mammography work underway at Shaviyani Atoll Hospital",MHS2020,"2020","medium")
add(F,"public","atoll_hospital","Funadhoo","Sh","ultrasound","Ultrasound (atoll hospital tier)","MHS2020 tier statement",MHS2020,"2020","medium")
add("Sh. Milandhoo Health Centre","public","health_centre","Milandhoo","Sh","xray","X-ray service inaugurated at health centre (new hospital building under construction)","PSM News: Milandhoo health centre officially inaugurated X-ray services (search snippet; psmnews 403)",MOH_XR_HC,"","medium")

# ---------------- N ----------------
F = "Noonu Atoll Hospital (Manadhoo)"
add(F,"public","atoll_hospital","Manadhoo","N","xray","Radiology & imaging dept: X-ray","nah.gov.mv: 'Radiology & Imaging - X-ray, ultrasound, and diagnostic imaging'",NAH,"2026","high")
add(F,"public","atoll_hospital","Manadhoo","N","ultrasound","Radiology & imaging dept: ultrasound","nah.gov.mv: 'Radiology & Imaging - X-ray, ultrasound'",NAH,"2026","high")
add("N. Velidhoo Health Centre","public","health_centre","Velidhoo","N","xray","X-ray service introduced at health centre (Grade 4 HC)","PSM News: X-ray services introduced in Holhudhoo and Velidhoo of Noonu Atoll (search snippet)",MOH_XR_HC,"","medium")
add("N. Holhudhoo Health Centre","public","health_centre","Holhudhoo","N","xray","X-ray service introduced at health centre","PSM News: X-ray services introduced in Holhudhoo and Velidhoo (search snippet)",MOH_XR_HC,"","medium")

# ---------------- R ----------------
F = "Ungoofaaru Regional Hospital"
add(F,"public","regional_hospital","Ungoofaaru","R","ct","GE 128-slice CT; service since Oct 2021 (inaugurated Jan 2022)","URH CT Scan Service page: GE 128 Slice; President's Office Jan 2022: CT started Oct 2021, 45 patients by Dec 2021",URH_CT,"2023-07-27","high")
add(F,"public","regional_hospital","Ungoofaaru","R","mri","MRI service launched 12 Dec 2024 (step to tertiary status)","MoH news 12 Dec 2024: ceremony to start MRI service at Ungoofaaru Regional Hospital",URH_MRI,"2024-12-12","high")
add(F,"public","regional_hospital","Ungoofaaru","R","mammography","Digital mammography (since late 2021/Jan 2022)","URH Mammography Service page; President's Office Jan 2022: three patients had mammography",URH_VP,"2022-01-16","high")
add(F,"public","regional_hospital","Ungoofaaru","R","xray","Digital X-ray; OPG (dental panoramic) and RVG","URH Radiology page: X-ray, Ultrasonography (USG), CT scan, Mammography, OPG",URH_WP,"2023-08-14","high")
add(F,"public","regional_hospital","Ungoofaaru","R","ultrasound","Ultrasonography (USG) incl. antenatal","URH Radiology page lists Ultrasonography (USG)",URH_WP,"2023-08-14","high")

# ---------------- B ----------------
F = "B. Atoll Hospital (Eydhafushi)"
add(F,"public","atoll_hospital","Eydhafushi","B","mammography","Mammography launched 12 Aug 2025 by President (breast cancer screening room)","MoH/MMTV Aug 2025: mammography service launched at Baa Atoll Hospital; confirmed in Minister's Jul 2026 list",BAA_MAMMO,"2025-08-12","high")
add(F,"public","atoll_hospital","Eydhafushi","B","xray","X-ray service (exposures/patients charted in 2021 annual report)","Baa Atoll Hospital Annual Report 2021: 'X-ray Services in Baa Atoll Hospital in 2021'",AR_IDX,"2021","high")
add(F,"public","atoll_hospital","Eydhafushi","B","ultrasound","Ultrasound (atoll hospital tier)","MHS2020 tier statement",MHS2020,"2020","medium")

# ---------------- Lh ----------------
F = "Lh. Atoll Hospital (Naifaru)"
add(F,"public","atoll_hospital","Naifaru","Lh","xray","General X-ray (atoll hospital tier); being upgraded to tertiary (contract Apr 2025)","MHS2020 tier statement; MoH Apr 2025: Lh Atoll Hospital among hospitals contracted for tertiary upgrade",MHS2020,"2020","medium")
add(F,"public","atoll_hospital","Naifaru","Lh","ultrasound","Ultrasound (atoll hospital tier); 'scanning services' added as part of 2022 upgrade","PSM News (c.2022): scanning services among services sent with doctors for Naifaru upgrade (search snippet)",MHS2020,"2022","medium")

# ---------------- AA / ADh / V / F / Dh / Th (atoll hospitals; tier inference) ----------------
for fac, isl, at, grade in [("AA. Atoll Hospital (Rasdhoo)","Rasdhoo","AA","Grade 1"),
                            ("ADh. Atoll Hospital (Mahibadhoo)","Mahibadhoo","ADh","Grade 1"),
                            ("V. Atoll Hospital (Felidhoo)","Felidhoo","V","Grade 1"),
                            ("F. Atoll Hospital (Nilandhoo)","Nilandhoo","F","Grade 1"),
                            ("Th. Atoll Hospital (Veymandoo)","Veymandoo","Th","Grade 2")]:
    conf = "medium" if grade == "Grade 2" else "low"
    add(fac,"public","atoll_hospital",isl,at,"xray",f"General X-ray expected at atoll hospital (Hospital {grade}); not directly confirmed","MHS2020: ultrasound and X-ray services available across most facilities incl. atoll hospitals",MHS2020,"2020",conf)
    add(fac,"public","atoll_hospital",isl,at,"ultrasound",f"Ultrasound expected at atoll hospital (Hospital {grade}); not directly confirmed","MHS2020 tier statement",MHS2020,"2020",conf)

F = "Dh. Atoll Hospital (Kudahuvadhoo)"
add(F,"public","atoll_hospital","Kudahuvadhoo","Dh","xray","X-ray; radiographers in 2023 organogram","Dh Kudahuvadhoo Annual Report 2023 organogram lists 'Radiographers' and Diagnostic & Laboratory section",AR_IDX,"2023","medium")
add(F,"public","atoll_hospital","Kudahuvadhoo","Dh","ultrasound","Ultrasound (atoll hospital tier)","MHS2020 tier statement",MHS2020,"2020","medium")

# ---------------- M ----------------
F = "Muli Regional Hospital"
add(F,"public","regional_hospital","Muli","M","xray","X-ray: 1,808 X-ray studies over 10 months; sole imaging modality during radiologist absence; new 50-bed hospital under construction","EJHM 2025 retrospective study: 'X-ray as the only diagnostic modality in Muli Regional Hospital' while ultrasound machine broken",MULI_STUDY,"2025","high")
add(F,"public","regional_hospital","Muli","M","ultrasound","Ultrasound machine reported BROKEN during 2024/25 study period; radiology service introduced earlier","EJHM 2025: 'absence of a radiology doctor and breakdown of an ultrasound machine'",MULI_STUDY,"2025","medium")

# ---------------- L ----------------
F = "Gan Regional Hospital (L. Gan)"
add(F,"public","regional_hospital","Gan (Laamu)","L","ct","CT scan service inaugurated Dec 2020 by President Solih","President's Office 4 Dec 2020: inaugurated 'the CT scan service at Laamu Gan Regional Hospital'",GAN_CT,"2020-12-04","high")
add(F,"public","regional_hospital","Gan (Laamu)","L","xray","New digital X-ray unit inaugurated Apr 2022","Raajje 2022: New X-ray unit inaugurated at Gan Regional Hospital",GAN_XR,"2022-04-22","high")
add(F,"public","regional_hospital","Gan (Laamu)","L","mammography","Mammography at 'five regional hospitals' (Gan counted among the 5 regional hospitals by MoH)","Minister Jul 2026: mammography available in Greater Male, five regional hospitals, Fuvahmulah and Baa",MAMMO7,"2026-07-08","medium")
add(F,"public","regional_hospital","Gan (Laamu)","L","ultrasound","Ultrasound (regional hospital tier)","MHS2020: regional hospitals report ultrasound scans",MHS2020,"2020","medium")

# ---------------- GA ----------------
F = "GA. Atoll Hospital (Villingili)"
add(F,"public","atoll_hospital","Villingili (GA)","GA","xray","Conventional X-ray in use; digital X-ray delivered mid-2024 kept in storage >2 yrs pending electrical/structural works; mammography planned","Edition Sep 2026: digital x-ray in storage; 'a regular x-ray machine is used'",GA_XR,"2026-09-28","high")
add(F,"public","atoll_hospital","Villingili (GA)","GA","ultrasound","Ultrasound (atoll hospital tier)","MHS2020 tier statement",MHS2020,"2020","medium")

# ---------------- GDh ----------------
F = "Dr. Abdul Samad Memorial Hospital (Thinadhoo)"
add(F,"public","regional_hospital","Thinadhoo","GDh","ct","CT scan service (first installed under 2018-23 govt; re-launched late 2025/early 2026); MRI promised but not yet confirmed","ASMH website services: CT Scan Service; Raajje May 2026: CT 'already established under the previous administration'",ASMH_SVC,"2026","high")
add(F,"public","regional_hospital","Thinadhoo","GDh","mammography","Mammography service","ASMH About page: services include CT Scan Services, Mammography Services",ASMH,"2026","high")
add(F,"public","regional_hospital","Thinadhoo","GDh","xray","X-ray (resumed after machine repair, per PSM)","ASMH services: X-Ray Service",ASMH_SVC,"2026","high")
add(F,"public","regional_hospital","Thinadhoo","GDh","ultrasound","Ultrasound (radiologist on staff; regional tier)","ASMH doctors page lists a radiologist; MHS2020 regional hospitals report USG","https://asmh.gov.mv/doctors","2026","medium")

# ---------------- Gn ----------------
F = "Fuvahmulah Hospital"
add(F,"public","atoll_hospital","Fuvahmulah","Gn","ct","CT officially launched 4 Nov 2025 with stroke protocol (CT within 20 min); machine delivered Mar 2025; previously 75 CT referrals in 5 months to IGMH/AEH","MoH news 4 Nov 2025: CT scan service officially started at Fuvahmulah Hospital",FUV_CT,"2025-11-04","high")
add(F,"public","atoll_hospital","Fuvahmulah","Gn","mammography","Mammography (listed among 7 hospitals with service, Jul 2026)","Minister Geela Jul 2026: mammography in Greater Male, five regional hospitals, Fuvahmulah Hospital and Baa Atoll Hospital",MAMMO7,"2026-07-08","high")
add(F,"public","atoll_hospital","Fuvahmulah","Gn","xray","General X-ray (hospital grade 2)","MHS2020 tier statement",MHS2020,"2020","medium")
add(F,"public","atoll_hospital","Fuvahmulah","Gn","ultrasound","Ultrasound (hospital grade 2)","MHS2020 tier statement",MHS2020,"2020","medium")

# ---------------- S (Addu) ----------------
F = "Addu Equatorial Hospital (AEH)"
for cat, det in [("ct","Computed Tomography incl. neuro-angiography & peripheral angiography; CT since opening (Jan 2020); receives CT referrals from Fuvahmulah"),
                 ("mri","MRI (machine arrived Jun 2019; service listed at opening)"),
                 ("mammography","Mammography"),
                 ("ultrasound","Ultrasound & Doppler, portable ultrasound"),
                 ("xray","X-ray / portable X-ray, fluoroscopy, C-arm; tele-radiology; bone densitometry 'coming soon'"),
                 ("endoscopy","Endoscopy services (listed milestone at opening)")]:
    add(F,"public","regional_hospital","Hithadhoo","S",cat,det,"AEH Diagnostic & Therapeutic brochure: Radiology & Diagnostic Imaging (X-Ray, MRI, Fluoroscopy, Mammography, Ultrasound/Doppler, CT); AEH brochure milestones: Endoscopy, MRI, CT services started",AEH,"2023","high")

add("I.M.D.C Multi Speciality Hospital","private","private_hospital","Hithadhoo","S","xray","X-ray facility (only private hospital in Addu; website blocks scripted access 406)","IMDC about page: X-Ray facilities alongside laboratory, ICU, NICU (search snippet)",IMDC,"","medium")
add("F & C Medicare and Scan Center","private","private_clinic","Hithadhoo","S","ultrasound","'Scan center' in name; presumed ultrasound (not verified)","Maaharaa licensed facility list: F & C Medicare and Scan Center, Ehaaru, S. Hithadhoo",MAAHARAA,"2026","low")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
    w.writeheader(); w.writerows(rows)
print(len(rows), "rows ->", OUT)
from collections import Counter
print(Counter(r["service_category"] for r in rows))
print(Counter(r["confidence"] for r in rows))
