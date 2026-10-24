"""Build rows.csv for the PCR/molecular + blood bank + thalassaemia stream (diagnostics research).

Evidence was gathered manually from saved sources in
data/external/health/services/diagnostics/sources/pcr_bloodbank/ (see source_url per row).
Run: python -I scripts/diag_pcr_bloodbank_rows.py
"""
import csv
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'external', 'health',
                   'services', 'diagnostics', 'sources', 'pcr_bloodbank', 'rows.csv')

HEADER = ['facility_name', 'operator_type', 'facility_type', 'island', 'atoll', 'service_category',
          'service_detail', 'evidence', 'source_url', 'source_date', 'confidence']

E17690 = 'https://edition.mv/news/17690'
E21268 = 'https://edition.mv/news/21268'
UN114067 = 'https://maldives.un.org/en/node/114067'

R = []


def add(*a):
    assert len(a) == len(HEADER), a
    R.append(dict(zip(HEADER, a)))


IGMH = 'Indira Gandhi Memorial Hospital (IGMH)'
KRH = 'Kulhudhuffushi Regional Hospital'
AEH = 'Addu Equatorial Hospital (Hithadhoo Regional Hospital)'

# ---------------- PCR / molecular ----------------
add(IGMH, 'public', 'tertiary_hospital', 'Male', 'K', 'pcr_molecular',
    'RT-PCR (national COVID-19 reference testing lab 2020-22); current PCR diagnostics and molecular diagnostics section; refers highly specialised tests abroad',
    'IGMH Laboratory page (2026): "Specialized services such as allergy testing, PCR diagnostics, and newborn screening"; sections incl. Molecular Diagnostics. WHO 2020: IGMH was main COVID-19 RT-PCR lab (~700 samples/day) and trained atoll lab technicians.',
    'https://www.igmh.gov.mv/en/departments/laboratory-medicine', '2026', 'high')
add('Maldives Police Service Forensic Laboratory', 'public', 'forensic_lab', 'Male', 'K', 'pcr_molecular',
    'RT-PCR (forensic DNA lab repurposed for COVID-19 testing 2020-22; tourist PCR from Sept 2020)',
    'WHO: Police Forensic Services lab strengthened for RT-PCR testing; HPA added Police Lab to traveller PCR list (2020).',
    'https://raajje.mv/84928', '2020-09', 'medium')
add('Hulhumale Hospital', 'public', 'tertiary_hospital', 'Hulhumale', 'K', 'pcr_molecular',
    'COVID-19 RT-PCR launched 12 Sept 2020 (target 200 samples/day); listed among 13 PCR-permitted labs (2021); MoH 2022 list permits antibody/antigen testing',
    'HEOC: PCR facilities to be set up at MFDA and Hulhumale Hospital; Hulhumale Hospital announced PCR testing launched 12 Sept (3rd facility in Greater Male). MoH Oct 2022 list of labs permitted for COVID antibody & antigen tests includes Hulhumale Hospital.',
    'https://psmnews.mv/en/74538', '2020-09', 'medium')
add('ADK Hospital', 'private', 'private_hospital', 'Male', 'K', 'pcr_molecular',
    'RT-PCR (Roche LightCycler 480 / MagNa Pure); COVID-19 PCR for public & tourists from 2020; capacity up to 2,000 tests/day incl. airport lab',
    'Edition 2020-12-24: ADK capacity 2,000 PCR tests/day with VIA lab; PCR price cut to MVR1,000 locals. HPA Aug 2020 traveller PCR list includes ADK (MVR1,500).',
    'https://edition.mv/news/21140', '2020-12-24', 'medium')
add('ADK PCR Laboratory, Velana International Airport', 'private', 'diagnostic_lab', 'Hulhule', 'K', 'pcr_molecular',
    'Fully automated COVID-19 RT-PCR lab (Roche LightCycler 480, MagNa Pure) set up by ADK with LUX* and TMA; sample drop-off at airport ferry terminal for resort/island samples',
    'ADK Hospital teamed up with LUX* Resorts and TMA to develop a COVID-19 testing laboratory in VIA, unveiled 23 Dec 2020; will test samples collected from resorts and islands. Current status not confirmed.',
    'https://raajje.mv/92695', '2020-12', 'low')
add('Maafaru Airport PCR Laboratory (ADK/Soneva)', 'private', 'diagnostic_lab', 'Maafaru', 'N', 'pcr_molecular',
    'COVID-19 RT-PCR lab (Roche LightCycler 96, 700 tests/day) at Maafaru International Airport, operated by ADK Hospitals, funded by Soneva & Velaa; also served local population',
    'Edition 2020-07-13: testing facility at Maafaru International Airport inaugurated; operated by ADK Hospitals; first Maldivian airport with a PCR lab. Pandemic-era; current status unknown.',
    'https://edition.mv/news/17871', '2020-07-13', 'low')
add('Tree Top Hospital', 'private', 'private_hospital', 'Hulhumale', 'K', 'pcr_molecular',
    'COVID-19 RT-PCR testing 2020-22 (results within 12 h); also permitted for COVID antibody testing (2022)',
    'Edition 2020-10-21: TTH reduced PCR test pricing, increased PCR capacity. HPA Aug 2020 traveller list included TTH; MoH 2022 antibody-testing permitted list includes Tree Top.',
    'https://edition.mv/news/19885', '2020-10-21', 'medium')
add('Medlab Diagnostics', 'private', 'diagnostic_lab', 'Male', 'K', 'pcr_molecular',
    'COVID-19 PCR testing (listed among government-permitted PCR labs 2021-22); also COVID antibody testing permitted (2022)',
    'Travel operator list of 13 PCR-permitted labs includes "Medlab" (Male); MoH Oct 2022 list includes "Medlab Diagnostics / K.Male" for antibody testing.',
    'https://www.atolltransfer.com/pcrtestbooking', '2022', 'low')
add('Mediflex Laboratories', 'private', 'diagnostic_lab', 'Male', 'K', 'pcr_molecular',
    'COVID-19 PCR testing (listed among PCR-permitted labs 2021-22); antibody testing permitted (2022)',
    'Travel operator list of PCR labs includes "Mediflex" (Male); MoH Oct 2022 list includes "Medflex Laboratories / K.Male" (antibody testing).',
    'https://www.atolltransfer.com/pcrtestbooking', '2022', 'low')
add(KRH, 'public', 'regional_hospital', 'Kulhudhuffushi', 'HDh', 'pcr_molecular',
    'RT-PCR (WHO-funded, installed by Wavelength; 72 samples/day at launch 5 Jul 2020); GeneXpert; now offers "Thalassemia and DNA testing"',
    'Edition 2020-07-05: KRH commenced COVID-19 PCR tests, 2nd location outside Male. KRH services API (2026) lists "Thalassemia and DNA testing" service.',
    E17690, '2020-07-05', 'high')
add(AEH, 'public', 'regional_hospital', 'Hithadhoo', 'S', 'pcr_molecular',
    'BioFire FilmArray POC PCR (24 tests/day) from 21 Jun 2020, then PCR machine; current lab lists Molecular diagnostics',
    'First COVID-19 test outside Male conducted at AEH on 21 Jun 2020 (BioFire). AEH Diagnostic & Therapeutic brochure (2023) lists "Molecular diagnostics" under Clinical Laboratory Medicine.',
    'https://aeh.gov.mv/storage/uploads/5b9a1902-7919-4068-be1c-a6cea60b9d0c/Diagnostic-&-Theraputic-Brochure1.pdf', '2023', 'high')
add('Dharavandhoo Health Centre', 'public', 'health_centre', 'Dharavandhoo', 'B', 'pcr_molecular',
    'COVID-19 PCR lab in an extension of the health centre (96 samples/hour), funded by The Nautilus & Milaidhoo resorts; HEMS lists a private "My Lab Dharavandhoo" diagnostic clinic (now closed)',
    'PCR lab at Dharavandhoo Health Centre inaugurated 10 Nov 2020 by Health Minister, services from 12 Nov 2020; follows HPA guidelines. HEMS registry: "My Lab Dharavandhoo" - Diagnostic Service Clinic - Closed.',
    'https://psmnews.mv/en/77636', '2020-11', 'medium')
add('Dh. Atoll Hospital (Kudahuvadhoo)', 'public', 'atoll_hospital', 'Kudahuvadhoo', 'Dh', 'pcr_molecular',
    'PCR machines donated by Kandima resort (Jul 2020), to be operationalised Jan 2021; can also test dengue',
    'Edition 2021-01-01: Kandima announced PCR machines donated to Kudahuvadhoo would be operationalised in January 2021. Operation not independently confirmed.',
    E21268, '2021-01-01', 'low')
add('Fuvahmulah Hospital', 'public', 'atoll_hospital', 'Fuvahmulah', 'Gn', 'pcr_molecular',
    'COVID-19 POC molecular machine (Jul 2021) and World Bank-funded PCR machine pledged by end-Sept 2021',
    'President (Jul 2021): technicians to install POC machine within a week; PCR machine funded by World Bank grant to be installed in Fuvahmulah by end Sept 2021. Installation not confirmed in sources found.',
    'https://raajje.mv/103020', '2021-07', 'low')
# GeneXpert (cartridge-based RT-PCR) sites, used for TB and COVID-19
for fac, ftype, isl, atl in [
        ('Sh. Atoll Hospital (Funadhoo)', 'atoll_hospital', 'Funadhoo', 'Sh'),
        ('Ungoofaaru Regional Hospital', 'regional_hospital', 'Ungoofaaru', 'R'),
        ('B. Atoll Hospital (Eydhafushi)', 'atoll_hospital', 'Eydhafushi', 'B'),
        ('Gan Regional Hospital', 'regional_hospital', 'Gan', 'L'),
        ('GA. Atoll Hospital (Villingili)', 'atoll_hospital', 'Villingili', 'GA'),
        ('Dr. Abdul Samad Memorial Hospital (Thinadhoo)', 'regional_hospital', 'Thinadhoo', 'GDh')]:
    extra = ''
    conf = 'medium'
    url = E21268
    if isl == 'Ungoofaaru':
        extra = ' URH laboratory page lists Molecular Diagnostics.'
        conf = 'high'
        url = 'https://urh.gov.mv/?page_id=332'
    if isl == 'Gan':
        extra = ' 2020 Gan COVID facility included a separate COVID-19 lab (48 tests/day).'
    if isl == 'Villingili':
        extra = ' HEOC (2020) also planned WHO-supplied PCR machine for GA Villingili.'
    add(fac, 'public', ftype, isl, atl, 'pcr_molecular',
        'GeneXpert cartridge RT-PCR (TB diagnosis; SARS-CoV-2 cartridges from Jul 2020)',
        'UN/WHO 2020: GeneXpert machines (one 4-module, six 2-module) mainly used for TB; SARS-CoV-2 cartridges enable testing in Sh. Atoll Hospital, Ungoofaaru RH, Baa Atoll Hospital, GA Atoll Hospital and Dr ASMH, and add capacity at KRH and Gan RH. Edition 2021-01-01 confirms GeneXpert COVID testing in these six hospitals.' + extra,
        url, '2021-01-01' if url == E21268 else '2026', conf)
add('Lh. Atoll Hospital (Naifaru)', 'public', 'atoll_hospital', 'Naifaru', 'Lh', 'pcr_molecular',
    'WHO-supplied COVID-19 testing machine planned (2020)',
    'HEOC spokesperson Dr Nazla: testing arrangements to be made in GA Villingili, Fuvahmulah City and Lh Naifaru with machines obtained through WHO. Not confirmed operational.',
    'https://psmnews.mv/en/74723', '2020-09', 'low')
add('Maldives Food and Drug Authority - National Health Laboratory', 'public', 'public_health_lab', 'Male', 'K', 'pcr_molecular',
    'PCR testing capacity planned at MFDA lab (2020)',
    'HEOC 2020: "PCR testing facilities will soon be established in MFDA and Hulhumale Hospital." Not confirmed operational for clinical PCR.',
    'https://psmnews.mv/en/74538', '2020-09', 'low')
add('Huvadhoo PCR Lab', 'private', 'diagnostic_lab', '', 'GDh', 'pcr_molecular',
    'Private COVID-19 PCR lab (Diagnostic Service Clinic) in Huvadhoo atoll; island not stated; now closed',
    'MoH HEMS registry: "Huvadhoo PCR lab" - private - Diagnostic Service Clinic - status Closed. Island/atoll (GA or GDh) not given.',
    'https://hems.health.gov.mv/', '2026', 'low')
add('AIMS Diagnostic Care', 'private', 'private_clinic', '', 'S', 'pcr_molecular',
    'Private clinic in Addu City planned COVID-19 testing (36 samples/hour) in 2020; island within Addu not stated',
    'Edition 2020-05-30: Addu City private clinic AIMS Diagnostic Care preparing to start COVID-19 testing, 36 samples/hour. HEMS: AIMS Diagnostic Care operating (General Clinic).',
    'https://edition.mv/news/16944', '2020-05-30', 'low')

# ---------------- Blood bank / transfusion ----------------
add('Maldivian Blood Services (MBS) / National Thalassaemia Centre', 'public', 'blood_service', 'Hulhumale', 'K', 'blood_bank',
    'National blood service: donor collection (Sun-Thu 08:00-20:00), screening, storage, issue; transfusion centre for ~650 thalassaemia patients (~220 packs/week); relocated to Orange Hiyaa, Hulhumale (formerly Male); under Male City Group of Hospitals',
    'Edition 2026-01-22: donations at Orange Hiyaa in Hulhumale. Edition 2025-11: Thalassemia Centre needs 220 blood packs/week; standards for blood bank being developed. MBS obtains much blood from camps (incl. resorts).',
    'https://edition.mv/news/47686', '2026-01-22', 'high')
add(IGMH, 'public', 'tertiary_hospital', 'Male', 'K', 'blood_bank',
    'Hospital blood bank (grouping, cross-match, component issue) within IGMH Laboratory Medicine',
    'IGMH Laboratory page lists "Blood Bank Services" among lab sections (with Clinical Chemistry, Microbiology, Haematology, Immunology, Histopathology, Molecular Diagnostics).',
    'https://www.igmh.gov.mv/en/departments/laboratory-medicine', '2026', 'high')
add(KRH, 'public', 'regional_hospital', 'Kulhudhuffushi', 'HDh', 'blood_bank',
    'Hospital blood bank: screening, storage, cross-matching; voluntary donor recruitment; rare groups sometimes sourced by flying donors from Male',
    'KRH services (2026): "every unit of blood is properly screened, stored, and cross-matched". Edition 2026-02-12: family sought AB- donors from Male to KRH after appealing to HA, HDh, Sh, N, R atolls.',
    'https://siteapi.krh.gov.mv/api/v1/services', '2026', 'high')
add(AEH, 'public', 'regional_hospital', 'Hithadhoo', 'S', 'blood_bank',
    'Hospital blood bank (Haematology & blood bank section), 24/7 emergency lab',
    'AEH Diagnostic & Therapeutic brochure: Clinical Laboratory Medicine - "Hematology & blood bank", Biochemistry & immunology, Microbiology, Molecular diagnostics, Histopathology & Cytology.',
    'https://aeh.gov.mv/storage/uploads/5b9a1902-7919-4068-be1c-a6cea60b9d0c/Diagnostic-&-Theraputic-Brochure1.pdf', '2023', 'high')
add('Dr. Abdul Samad Memorial Hospital (Thinadhoo)', 'public', 'regional_hospital', 'Thinadhoo', 'GDh', 'blood_bank',
    'Hospital blood bank with online donor registration ("Give Blood")',
    'ASMH website "Become a Blood Donor" form: "I consent to the blood bank storing my details for the purpose of donor registration and contact."',
    'https://asmh.gov.mv/giveblood', '2026', 'high')
add('GA. Atoll Hospital (Villingili)', 'public', 'atoll_hospital', 'Villingili', 'GA', 'blood_bank',
    'Cross-match and blood transfusion service (walking-donor model likely)',
    'GA Atoll annual report 2022 (statistics chart): "Lab investigation, Cross Match, Blood tranfusion, X ray, Physiotheraphy".',
    'https://health.gov.mv/storage/uploads/6eY3WxY3/9w5s4p1m.pdf', '2022', 'medium')
add('HA. Atoll Hospital (Dhidhoo)', 'public', 'atoll_hospital', 'Dhidhoo', 'HA', 'blood_bank',
    'Blood transfusion service (thalassaemia, anaemia, pregnancy cases; ~55 transfusions/yr)',
    'HA Atoll Hospital annual reports 2021 & 2022: "Blood Transfusion Services" / "Blood Service" chart by Thalassemia, Anaemic and Pregnancy cases (Total: 55).',
    'https://health.gov.mv/storage/uploads/Arovx2Yj/bvtns64j.pdf', '2022', 'medium')
add('R. Maduvvari Health Centre', 'public', 'health_centre', 'Maduvvari', 'R', 'blood_bank',
    'Cross-match and blood transfusion at health-centre level (thalassaemia/anaemia/pregnancy); >13,000 lab investigations in 2023',
    'Maduvvari HC annual report 2023: "Blood Transfusion" chart with X Matches, Anemia, Pregnancy, Thalasemia counts (23/15/6/2) and "Laboratory investigation Statistics" (13,113).',
    'https://health.gov.mv/storage/uploads/DqKeMWwO/60dkvjzq.pdf', '2023', 'medium')

# ---------------- Thalassaemia screening / specialised haematology (lab_advanced) ----------------
add('Maldivian Blood Services (MBS) / National Thalassaemia Centre', 'public', 'blood_service', 'Hulhumale', 'K', 'lab_advanced',
    'Thalassaemia carrier screening (national programme incl. all Grade 10 students since Feb 2024), haematology, HLA typing & BMT work-up tests (from Aug 2025, visiting doctors); BMT cross-match samples collected locally, tested in India',
    'Edition 2026-05: haematology services, HLA typing and specialised bone-marrow-transplant tests began in August; Edition 2024-02-04: Thalassemia Screening Programme launched (MoH, MoE, MBS) for all Grade 10 students; Edition 2024-05-10: BMT cross-match samples extracted locally, tested in India.',
    'https://edition.mv/news/50750', '2026-05', 'high')
add(AEH, 'public', 'regional_hospital', 'Hithadhoo', 'S', 'lab_advanced',
    'Thalassaemia screening clinic (Sat-Thu 09:00-13:00) plus pathologist-led lab',
    'AEH Laboratory Medicine page: "Thalassemia screening Saturday to Thursday 09:00am to 01:00pm"; staff include a pathologist.',
    'https://aeh.gov.mv/our-services/laboratory-medicine', '2026', 'high')
add(KRH, 'public', 'regional_hospital', 'Kulhudhuffushi', 'HDh', 'lab_advanced',
    'Thalassaemia carrier/patient testing and DNA testing',
    'KRH services API: "Thalassemia and DNA testing - helps identify carriers and patients with thalassemia". Raajje headline: "Kulhudhuffushi Hospital launches thalassemia testing".',
    'https://siteapi.krh.gov.mv/api/v1/services', '2026', 'high')

with open(OUT, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=HEADER)
    w.writeheader()
    w.writerows(R)
print(len(R), 'rows ->', os.path.normpath(OUT))
