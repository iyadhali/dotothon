"""Build health-centre diagnostic rows CSV (stream E: island health centres).
Usage: python -I diag_build_hc_rows.py HEMS_CSV OUT_CSV
Evidence collected from news (edition.mv, avas.mv, psmnews.mv via search snippets), AEH website,
MoH news (Dhivehi), MFDA, Wikipedia island articles and MoH facility annual reports."""
import csv
import sys
import collections

hems_csv, out_csv = sys.argv[1], sys.argv[2]
grade = {}
for r in csv.DictReader(open(hems_csv, encoding='utf-8')):
    if r['atoll_code'] and r['island'] and ('Health Centre' in r['level'] or 'Hospital' in r['level']):
        grade[(r['atoll_code'], r['island'])] = r['level'].replace('Health Centre Grade ', 'HC Grade ')

U = dict(
    avas_inna='https://avas.mv/en/77028',
    aeh_hmhc='https://aeh.gov.mv/health-centres/hulhumeedhoo-health-centre',
    ed_thak='https://edition.mv/news/13020',
    ed_land='https://edition.mv/news/15240',
    ed_kandu='https://edition.mv/news/12900',
    psm_laamu='https://psmnews.mv/en/58736',
    mmtv_xray='https://en.mmtv.mv/2861',
    psm_xray='https://psmnews.mv/en/169657',
    psm_uth='https://psmnews.mv/en/177216',
    ed_noom='https://edition.mv/news/45041',
    ed_tender='https://edition.mv/news/51277',
    mfda_china='https://mfda.gov.mv/en/news/signed-agreement-with-chinese-government-for-procurement-of-laboratory-equipments-for-17-islands',
    moh_thul='https://health.gov.mv/dv/news/maale-atholhu-ihee-marukazuge-voadaai-leboataree-maraamaathu-kurumah-fahu-alun-hulhuvaifi',
    wiki_hulhu='https://en.wikipedia.org/wiki/Hulhudhuffaaru',
    wiki_kendhoo='https://en.wikipedia.org/wiki/Kendhoo',
    wiki_koman='https://en.wikipedia.org/wiki/Komandoo_(Shaviyani_Atoll)',
    wiki_mahi='https://en.wikipedia.org/wiki/Mahibadhoo',
    ar_fonadhoo='https://health.gov.mv/storage/uploads/QoQQO1ov/68yabesg.pdf',
    ar_maduvvari='https://health.gov.mv/storage/uploads/DqKeMWwO/60dkvjzq.pdf',
    ar_kolhufushi='https://health.gov.mv/storage/uploads/RwXeZNYW/da2cvbbm.pdf',
    ar_madifushi='https://health.gov.mv/storage/uploads/JYkjO3wR/gbgevkjf.pdf',
    ar_kinbidhoo='https://health.gov.mv/storage/uploads/XqPjpLwB/4cecc2qv.pdf',
    ar_makunudhoo='https://health.gov.mv/storage/uploads/8qe8Z3YP/6gt7ijq2.pdf',
    ar_vilufushi='https://health.gov.mv/storage/uploads/aVw5kPq1/fatlsokq.pdf',
)
rows = []


def add(atoll, island, cat, detail, evidence, src, date, conf, op='public', ftype='health_centre', name=None):
    g = grade.get((atoll, island), '')
    if name is None:
        name = f'{atoll}. {island} Health Centre'
    d = (g + '; ' if g and ftype == 'health_centre' else '') + detail
    rows.append([name, op, ftype, island, atoll, cat, d, evidence, U.get(src, src), date, conf])


# --- explicit lab openings / listings ---
add('R', 'Innamaadhoo', 'lab_basic', 'Laboratory opened Jan 2020 (built by island council with companies); previously residents used Ungoofaaru Regional Hospital lab',
    'Avas: "The laboratory service is officially initiated in R.Innamaadhoo Health Centre"; "In Raa Atoll there are 8 Health Centres that provide laboratory services"', 'avas_inna', '2020-01-25', 'high')
add('S', 'Hulhumeedhoo', 'lab_basic', 'Lab since 27 Jun 2003; 2 medical laboratory technologists; largest HC in Maldives (20 beds, 24h)',
    'AEH page: "Laboratory services began on June 27, 2003" ... "two medical laboratory technologists"', 'aeh_hmhc', '2024', 'high')
add('S', 'Hulhumeedhoo', 'xray', 'X-ray service in HMHC extension building inaugurated 15 Dec 2022 (with ENT, ophthalmology, dental, dialysis, physio)',
    'AEH page: extension building to introduce "... X-ray Services, Dialysis and Physiotherapy Services"; inaugurated 15 Dec 2022', 'aeh_hmhc', '2022-12-15', 'high')
add('HA', 'Thakandhoo', 'lab_basic', 'Laboratory inaugurated Oct 2019; previously travelled to Dhidhoo or Kulhudhuffushi',
    'Edition: "inaugurated the Laboratory at the Health Centre in Thakandhoo, Haa Alif Atoll"', 'ed_thak', '2019-10-20', 'high')
for isl in ['Ihavandhoo', 'Hoarafushi', 'Baarah', 'Thuraakunu', 'Kelaa', 'Filladhoo', 'Uligan']:
    add('HA', isl, 'lab_basic', 'Listed among 8 HA islands with laboratory services (2019)',
        'Edition: "A total of eight islands now provide laboratory services in Haa Alif Atoll, including Ihavandhoo, Hoarafushi, Baarah, Thuraakunu, Kelaa, Filladhoo and Uligamu"', 'ed_thak', '2019-10-20', 'high')
add('N', 'Landhoo', 'lab_basic', 'Laboratory services inaugurated Feb 2020 (supports thalassaemia patients of Landhoo, Maalhendhoo, Maafaru); previously used N Atoll Hospital (Manadhoo)',
    'Edition: "inaugurated laboratory services at Landhoo Health Centre, Noonu Atoll"', 'ed_land', '2020-02-29', 'high')
for isl in ['Velidhoo', 'Kendhikulhudhoo', 'Holhudhoo']:
    add('N', isl, 'lab_basic', 'Listed among Noonu islands with laboratory services (2020)',
        'Edition: "In addition to Landhoo, islands from which laboratory services are available include Manadhoo, Velidhoo, Kendhikulhudhoo and Holhudhoo"', 'ed_land', '2020-02-29', 'high')
add('GA', 'Kanduhulhudhoo', 'lab_basic', 'Laboratory services since 22 Sep 2019 (inaugurated 12 Oct 2019); previously travelled to Gemanafushi or Gadhdhoo',
    'Edition: "officially inaugurated laboratory services in the health centre at Kanduhulhudhoo, Gaafu Alif Atoll"', 'ed_kandu', '2019-10-13', 'high')
for isl in ['Gemanafushi', 'Dhaandhoo', 'Dhevvadhoo', 'Kolamaafushi']:
    add('GA', isl, 'lab_basic', 'Listed among GA facilities providing laboratory services (2019)',
        'Edition: "laboratory services the atoll are provided in Gaafu Alif Atoll Hospital, Gemanafushi Health Centre, Daandhoo Health Centre, Dhevvadhoo Health Centre and Kolamaafushi Health Centre"', 'ed_kandu', '2019-10-13', 'high')
for isl in ['Maabaidhoo', 'Hithadhoo']:
    add('L', isl, 'lab_basic', 'Laamu lab hub for 2019 mobile-lab/sample scheme: samples from Mundoo & Dhanbidhoo -> Maabaidhoo; Kunahandhoo & Maamendhoo -> L. Hithadhoo',
        'PSM (via search snippet; site returns 403 to scripts): "Laboratory services are available in Gan, Hithadhoo and Maabaidhoo in Laamu Atoll"', 'psm_laamu', '2019-10', 'medium')
add('Sh', 'Noomaraa', 'lab_basic', 'Existing lab to be upgraded so all essential tests can be done on-island (President, Oct 2025); also on 2024 China lab-equipment list',
    'Edition: "the existing laboratory in Noomaraa will be upgraded with necessary facilities"', 'ed_noom', '2025-10-13', 'high')
add('K', 'Thulusdhoo', 'lab_basic', "Male' Atoll (Kaafu) Health Centre; ward and laboratory renovated/enlarged and reopened Jun 2024",
    'MoH news (Dhivehi): K. Thulusdhoo Maale Atoll Health Centre "ward and laboratory reopened after repair" (lab enlarged, AC installed)', 'moh_thul', '2024-06-05', 'high')
for isl in ['Utheemu', 'Vashafaru']:
    add('HA', isl, 'lab_basic', 'Lab launched under 2024-26 national lab expansion (reported as 15th and 16th islands to get the service); date approximate',
        'PSM (search snippet; 403 to scripts): labs launched in Utheemu and Vashafaru, the 15th and 16th islands to receive the service', 'psm_uth', '2026', 'medium')
# --- X-ray at health centres ---
for isl in ['Holhudhoo', 'Velidhoo']:
    add('N', isl, 'xray', "X-ray service launched 2025 during Health Minister Nazim's Noonu tour (one of 4 islands in 2025 X-ray plan)",
        "PSM (search snippet): X-ray services were launched at both islands' health centres; MMTV: plan for X-ray in Holhudhoo, Velidhoo, Milandhoo, Maamigili", 'psm_xray', '2025', 'medium')
add('Sh', 'Milandhoo', 'xray', 'X-ray service officially opened 2025 ("fourth island to gain X-ray since current government took office"); HC being rebuilt as hospital (works started Oct 2025)',
    'PSM (search snippet): X-ray services officially opened at Milandhoo health centre', 'psm_xray', '2025', 'medium')
add('ADh', 'Maamigili', 'xray', 'X-ray machine delivered under 2025 plan but reported not operational for months due to lack of radiographers; residents go to Mahibadhoo or Male',
    'MMTV: X-ray planned at Maamigili; Sun (via search summary): machine uninstalled ~4 months for lack of technicians', 'mmtv_xray', '2025', 'low')
# --- Wikipedia / annual reports ---
add('R', 'Hulhudhuffaaru', 'lab_basic', '24h HC; lab among listed services',
    'Wikipedia: services include "... Antenatal & Postnatal Clinic, Laboratory service, Home Visits and Ambulance service"', 'wiki_hulhu', '2025', 'medium')
add('B', 'Kendhoo', 'lab_basic', '16h HC; lab for general investigations',
    'Wikipedia: "The Health centre also provides laboratory services for general investigations"', 'wiki_kendhoo', '2025', 'medium')
add('Sh', 'Komandoo', 'lab_basic', 'Lab investigations; blood transfusion and ECG also listed',
    'Wikipedia: "Services provided by the Health Center include blood transfusion, E.C.G, laboratory investigations and family planning"', 'wiki_koman', '2025', 'medium')
add('L', 'Fonadhoo', 'lab_basic', 'Monthly inpatient & outpatient laboratory activity charted for 2023',
    'Annual Report L. Fonadhoo 2023: "LABORATORY SERVICES DURING THE YEAR 2023" (Laboratory 2023 Inpatient / Outpatient)', 'ar_fonadhoo', '2023', 'high')
add('R', 'Maduvvari', 'lab_basic', 'Laboratory investigation statistics 2023 (OP and IP investigations; chart values ~13.1k and ~9.3k)',
    'Annual Report R. Maduvvari 2023: "Laboratory investigation Statistics ... OP investigation IP investigation"', 'ar_maduvvari', '2023', 'high')
add('Th', 'Vilufushi', 'lab_basic', 'Tests reported 2021: blood sugar, cholesterol, blood tests, sputum, stool, urine',
    'Annual Report Th. Vilufushi 2021 table: "Total Lab Test / Blood Sugar / Cholesterol / Blood Test / Sputum / Stool / Urine Tested"', 'ar_vilufushi', '2021', 'high')
add('M', 'Kolhufushi', 'lab_basic', 'Laboratory unit in 2023 organogram',
    'Annual Report M. Kolhufushi 2023 org chart lists "Laboratory"', 'ar_kolhufushi', '2023', 'medium')
add('Th', 'Madifushi', 'lab_basic', 'Registered nurse assigned to laboratory (2023)',
    'Annual Report Th. Madifushi 2023 staff list: "REG. NURSE LABORATORY"', 'ar_madifushi', '2023', 'medium')
add('Th', 'Kinbidhoo', 'lab_basic', 'Laboratory post in 2023 staff list',
    'Annual Report Th. Kinbidhoo 2023 staff list: "LABORATORY"', 'ar_kinbidhoo', '2023', 'medium')
add('HDh', 'Makunudhoo', 'lab_basic', 'Lab technologist on staff (2023)',
    'Annual Report HDh. Makunudhoo 2023 org chart: "Lab Technologist"', 'ar_makunudhoo', '2023', 'medium')
# --- islands with POC only (no physical lab) as of May 2026 ---
tender = [('R', 'Fainu'), ('N', 'Kudafari'), ('N', 'Fodhdhoo'), ('B', 'Kudarikilu'), ('B', 'Dhonfanu'), ('M', 'Raiymandhoo'),
          ('L', 'Mundoo'), ('L', 'Kunahandhoo'), ('Sh', 'Goidhoo'), ('HA', 'Muraidhoo'), ('HDh', 'Kumundhoo'), ('HDh', 'Naivaadhoo'),
          ('Th', 'Omadhoo'), ('Th', 'Gaadhiffushi'), ('ADh', 'Dhidhdhoo')]
china = [('N', 'Fodhdhoo'), ('GDh', 'Hoadedhdhoo'), ('HA', 'Muraidhoo'), ('HA', 'Maarandhoo'), ('B', 'Goidhoo'), ('B', 'Dhonfanu'),
         ('B', 'Kihaadhoo'), ('Th', 'Dhiyamigili'), ('GA', 'Maamendhoo'), ('GA', 'Nilandhoo'), ('Sh', 'Noomaraa'), ('Lh', 'Olhuvelifushi'),
         ('ADh', 'Hangnaameedhoo'), ('V', 'Keyodhoo'), ('K', 'Gaafaru'), ('N', 'Maalhendhoo'), ('AA', 'Maalhos')]
tset, cset = set(tender), set(china)
for a, i in tender:
    extra = '; also on 2024 China lab-equipment grant list' if (a, i) in cset else ''
    add(a, i, 'lab_basic', 'Point-of-care basic testing only - no physical laboratory as of May 2026; lab building tendered under 76-island lab programme' + extra,
        'Edition: Ministry "opened bids for the construction of laboratories in 15 islands with existing health centres" (lists this island); Minister (edition.mv/news/47709): islands lacking labs got basic testing "under point of care"',
        'ed_tender', '2026-05-26', 'medium')
for a, i in china:
    if (a, i) in tset or (a, i) == ('Sh', 'Noomaraa'):
        continue
    add(a, i, 'lab_basic', 'Lab equipment allocated under China grant (Letter of Exchange 28 Mar 2024; first 17 of 72 islands); island lacked a lab in 2023 - basic POC testing since 2024; physical-lab status unverified',
        'MFDA/MoH: "17 health centres in the country will receive laboratory equipment" (lists this HC)', 'mfda_china', '2024-03-28', 'low')
# --- private clinic on an outer island ---
pc = 'Pro Care Clinic and Dental Centre (Mahibadhoo)'
add('ADh', 'Mahibadhoo', 'lab_basic', 'Private clinic: lab investigations, occasional specialist consultations',
    'Wikipedia (Mahibadhoo): Procare Clinic "facilities including x-ray, laboratory investigations"; Maaharaa registry lists Pro Care Clinic and Dental Centre, ADh. Mahibadhoo',
    'wiki_mahi', '2025', 'medium', op='private', ftype='private_clinic', name=pc)
add('ADh', 'Mahibadhoo', 'xray', 'Private clinic X-ray', 'Wikipedia (Mahibadhoo): Procare Clinic "facilities including x-ray"',
    'wiki_mahi', '2025', 'medium', op='private', ftype='private_clinic', name=pc)

seen, out = set(), []
for r in rows:
    k = (r[0], r[5])
    if k in seen:
        continue
    seen.add(k)
    out.append(r)
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['facility_name', 'operator_type', 'facility_type', 'island', 'atoll', 'service_category', 'service_detail',
                'evidence', 'source_url', 'source_date', 'confidence'])
    w.writerows(out)
print(len(out), collections.Counter(r[5] for r in out), collections.Counter(r[10] for r in out))
