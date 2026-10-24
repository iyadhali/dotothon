# 05 — Maldives healthcare data (facilities, capacity, utilisation, morbidity)

Compiled 2026-10-24 for the Maldives Datathon 2026 project on multi-modal access to health and education services by island. OSM health POIs and census population are handled in other workstreams and are not repeated here. The exception is the 2022 census resident population by atoll, which MoH prints inside its HR workbook; it is used here only as a denominator.

All downloads are under `C:\Users\user\Music\Datathon\data\external\health\<source>\`. Scripts are in `C:\Users\user\Music\Datathon\scripts\health_*.py`. All Python was run with `python -I`.

**What this gives you for access analysis:**

1. An island-level list of public facilities with tier and grade: 187 facilities in 2020, cross-walked to the live 2026 MoH licence registry.
2. Atoll-level capacity: beds (2020) and staff per 10k (2023).
3. Atoll-level utilisation: outpatient visits per capita (2023), admissions (2020) and emergency evacuations per 1,000 (2023).
4. Island-level surveillance cases (2025) and island-level Aasandha spending (2014–2024).

---

## 1. Dataset inventory

Granularity codes: **I** = island, **F** = facility, **A** = atoll (20 atolls + Malé), **R** = DHS region (6), **N** = national.

### 1.1 MBS Statistical Yearbook, health and social-protection chapters (XLSX). Best source.

- **Source:** https://statisticsmaldives.gov.mv/yearbook/2026/ (and the /2025/, /2024/ and /2021/ editions)
- **Licence:** Maldives Bureau of Statistics. Free public release; no explicit licence, so cite "Statistical Yearbook of Maldives, MBS".
- **Folder:** `mbs_statistical_yearbook\yb2026\`, `yb2025\`, `yb2024\`, `yb2021\`. `MANIFEST.tsv` holds the title, URL and local file for each table. The lister is `health_yearbook_list.py`.

| Table (yearbook) | Content | Years | Gran. | Original source |
|---|---|---|---|---|
| 6.1 (2026) | Medical staff by category (allied, admin, doctors/dentists, nurses) × Malé/Atolls × sex | 2022, 2023 | Malé vs atolls | MoH |
| 6.2 (2026) | Health personnel local vs expatriate × public/private | 2022, 2023 | N | MoH |
| **6.3 (2026)** | **Outpatient visits by atoll × sex** | 2022, 2023 | **A** | MoH |
| **6.3 (2021)** | **Outpatient, inpatient and inpatient beds per government hospital tier per atoll** (IGMH, ADK, Tree Top, Hulhumalé, Villimalé, Senahiya, Medica, Dhamanaveshi, then each atoll split into hospital vs health centres) | 2020 | **F/A** | MoH |
| 6.5 / 6.6 | Dhamanaveshi outpatient care; IGMH beds, outpatients, inpatients, bed-days, length of stay, occupancy | 2010–2025 | F | IGMH |
| 6.7 | IGMH surgical interventions by type | 2010–2025 | F | IGMH |
| 6.9 / 6.10 | IGMH outpatients and inpatients by specialty × sex | 2025 (sheets go back to 2024) | F | IGMH |
| 6.11 | Thalassaemia registered cases, Malé vs atolls | 2010–2025 | Malé vs atolls | NTC |
| **6.17** | **Reported cases: ARI, viral fever, diarrhoea, measles, scrub typhus, dengue, typhoid (<5 / ≥5)** | 2025 | **A** | HPA |
| **6.18** | **Same diseases by island** (about 200 islands) | 2025; 2017 copy in `yb2024\6.18.xlsx` | **I** | HPA |
| 6.19 | Monthly reported cases | 2025 | N | HPA |
| 6.20 (2024) | Immunisation coverage by island | 2015 | I | HPA |
| 3.10 / 3.11 / 3.12 (pdf) / 3.14 | Births and deaths by locality; deaths by age × sex × Malé/Atolls | 2022–2025 | Malé vs atolls | Civil registration |
| 18.22 / 18.23 | Aasandha spending by institution type (hospital, pharmacy, clinic, airfare, **emergency evacuation air / sea**), by atoll | 2025 | A | Aasandha |
| 18.24 | Aasandha spending by service, including **inter-atoll transport of critical patients (sea / air)** and dialysis | 2014–2025 | N | Aasandha |
| 18.25 | Aasandha spending by atoll | 2014–2025 | A | Aasandha |
| **18.26** (2025, 2024) | **Aasandha spending by island** | 2014–2024 | **I** | Aasandha |
| 18.27 | Emergency evacuations; patients sent abroad; empanelled hospitals and pharmacies | 2018–2024 | N | Aasandha |
| **18.28** | **Emergency evacuations, empanelled facilities and pharmacies by atoll** | 2023 | **A** | Aasandha |

**Gaps:**
- Labels are provisional.
- 6.4 and 6.16 are not published in 2026.
- 2021 T6.3 has its *Inpatient* and *Outpatient* column headers swapped in the source. This is fixed in `_derived\mbs_T6-3_2021yb_hospital_beds_2020_tidy.csv`.
- IGMH beds conflict for 2020: 587 in 2021 T6.3 versus 423 end-of-year in T6.6.

### 1.2 MoH Health Establishment Management System (HEMS): live licence registry

- **Source:** https://hems.health.gov.mv/establishments (41 pages), scraped 2026-10-24 with `health_hems_scrape.py`.
- **Licence:** public MoH registry; terms not stated.
- **Folder:** `moh_hems_registry\`
  - `raw_pages\` (HTML)
  - `hems_establishments.csv`: 601 rows. Fields: name, status, owner, level, reg_no, license_no, contact, email, n_professionals.
  - `hems_facilities_tidy.csv`: adds sector, tier, atoll_code, island and location_source. Built with `health_hems_tidy.py`.
- **Content:**
  - 601 establishments: 584 open, 17 closed.
  - 193 government. By licence level: Tertiary 4 (IGMH, Hulhumalé, Dharumavantha, Addu Equatorial); Hospital Grade 3 = 4 (Kulhudhuffushi, Ungoofaaru, L. Gan, Dr Abdul Samad Memorial/GDh Thinadhoo); Grade 2 = 9; Grade 1 = 6.
  - Government health centres: Grade 4 = 12, Grade 3 = 55, Grade 2 = 37, Grade 1 = 60.
  - Private: 2 tertiary (ADK, Tree Top), 4 general hospitals (Advance, Care Trust, IMDC Addu, Medica), Eye Care, and about 390 clinics.
- **Granularity:** F. For public facilities the island comes from the facility name, plus a curated lookup for hospitals. That lookup matches MoH's work-permit facility list (`moh_workpermit_facility_list\`).
- **Gaps:**
  - No coordinates, beds or services.
  - Private and resort clinic names usually carry no island.
  - The professional count is 0 for almost all government facilities, so it cannot be used for staffing.
  - Four small government clinics have no island.

### 1.3 Maldives Health Statistics (MoH annual), PDFs plus extracted CSVs

- **Folder:** `moh_maldives_health_statistics\`
- **Files:**
  - `MHS2020_jjokopyg.pdf`: https://health.gov.mv/storage/uploads/79qgJ9YD/jjokopyg.pdf, 400+ pages, published Dec 2021.
  - MHS 2015-16, MHS 2013, Health Profile 2019. Full text is in the `.txt` files next to them.
- **Licence:** © Ministry of Health. Excerpts may be used for research with acknowledgement.
- **Tidy CSVs extracted** (`health_mhs2020_facilities.py`, `health_pdf_coord_table.py`, `health_mhs2020_tidy.py`):
  - `MHS2020_T1-14_public_facilities_by_island.csv`: **187 public facilities with atoll, island, category (Tertiary / Regional / Atoll Hospital / Health Center) and grade 1–4.** **I**
  - `MHS2020_T1-16_workforce_by_atoll_profession_tidy.csv`: workforce by atoll × profession (about 25 cadres: GPs, specialists by type, nurses, community health workers, lab, pharmacy) × local/expat × sex, 2020. **A**
  - `MHS2020_T3-14_admissions_by_atoll_sex_group_tidy.csv`: admissions by atoll × sex × GBD group, 2020. **A**
  - `MHS2020_T3-11_inpatients_by_GBD_subgroup_sex.csv`: national admissions by GBD sub-group. N
  - `MHS2020_T4-8_top20_causes_of_death_GBD.csv` and `..._T4-9_..._ICD.csv`: top 20 causes of death, all / female / male. N
- **Also in the 2020 PDF but not extracted:**
  - Table 1-2: facilities by NSP zone.
  - Fig 1-6: outpatients by atoll.
  - Fig 1-7: beds (3,720 facility beds; 2,581 inpatient beds).
  - Table 3-15: admissions by facility tier.
  - Table 4-15: NCD deaths by atoll.
  - Table 5-7: surveillance diseases by atoll.
- **Gaps:**
  - MHS 2021 is only on a SharePoint link that now returns an error.
  - MHS 2017-2019 (`moh_statistics_publications\`) is a scanned PDF with no text layer.

### 1.4 MoH statistics releases, 2022–2026 (XLSX plus snapshot PDFs)

- **Source:** health.gov.mv publications, category "Statistics" / "Maldives Health Statistics 2022-2023". Index: `moh_statistics_publications\moh_publications_index.tsv`. Lister and downloader: `health_moh_publications.py`.
- **Licence:** as for MoH above.

| File | Content | Gran. |
|---|---|---|
| `Maldives_Outpatient_Visits_Snapshot_2022_2023__9u6sa3ct.xlsx` (2022) and `__ifntvx26.xlsx` (2023) | OP visits per 1,000 by atoll; by consultation type and **33 specialties**; by age, nationality, public vs private; list of facilities covered | A / N |
| `Human_resources_data_2022_and_2023__fdfkh08a.xlsx` (2022) and `__5dvltwmw.xlsx` (2023) | **Health personnel per 10,000 by atoll** (total, allied, community health workers, dentists, doctors, midwives, nurses); headcount by atoll × facility type (atoll/regional hospital, health centre, tertiary); facility list with type | **A** |
| `Surgery_data_2022/2023*.xlsx` + snapshot PDFs | Surgeries by specialty, urgency, facility type, public vs private | N / tier |
| `Quarterly_Vital_Statistics_2022…2026*.xlsx` | Births and deaths by place of occurrence × usual residence (atoll), age, sex | A |
| `Human_Resource_Data_Snapshot_2025`, `Human_resource_snapshot_2026` (PDF) | HR snapshot infographics | N |

### 1.5 MoH facility and agency annual reports, 2021–2025 (raw)

- **Folder:** `moh_annual_reports\` (200 PDFs, 556 MB; index in `moh_annual_reports_index.tsv`; text dumps in `_text\`).
- **Content:** island health centre, atoll hospital, regional hospital, HPA and MoH annual reports.
- **Gaps:** mostly in Dhivehi and/or scanned, so text extraction is unusable. They are kept for manual reading only, for example referral or ambulance tables for one atoll.

### 1.6 DHS Maldives 2016-17

- **Folder:** `dhs_maldives_2016_17\`
- **Files:**
  - `MDHS_2016-17_FR349.pdf`: https://dhsprogram.com/pubs/pdf/FR349/FR349.pdf
  - API pulls in `raw_json\` and flattened CSVs: `dhs_MV2016_subnational.csv` (11,977 rows) and `dhs_MV2016_national.csv` (3,022 rows). Built with `health_dhs_tidy.py`.
- **Licence:** DHS Program. Free with citation; microdata need registration (not requested).
- **Granularity:** API is **R** (Malé, North, North Central, Central, South Central, South). The report PDF has **atoll** rows for a few tables. Extracted:
  - `MDHS_T15-1_hypertension_diabetes_by_atoll.csv`: self-reported hypertension and diabetes, women and men 15-49.
  - `MDHS_T15-4_other_NCD_diagnosis_by_atoll.csv`: heart attack, stroke, renal failure, cancer, COPD/asthma.
- **Key access fields (region level):** "Problems in accessing health care: distance to health facility" (women 15-49) ranges from 27.6% (North Central) to 37.5% (South). "Getting money" ranges from 16% to 22%.

### 1.7 WHO STEPS NCD risk-factor survey 2020-21

- **Folder:** `who_steps_maldives_2020\`
- **Files:**
  - `Maldives_STEPS_report_2020-2021.pdf`: from https://extranet.who.int/ncdsmicrodata/index.php/catalog/997
  - `STEPS_Instrument_V3.1.pdf`
  - `MDVSTEPS1/3.xlsx`: ODK questionnaire forms, **not data**.
  - `STEPS_2020-21_key_indicators_factsheet.csv`: transcribed from the fact sheet.
- **Licence:** WHO. Report public; microdata by request.
- **Granularity:** N only (sample was Greater Malé plus 5 atoll regions). Fieldwork Dec 2020 – Dec 2021, n = 3,233.

### 1.8 WHO Global Health Observatory and World Bank WDI (API, national)

- **Folders:** `who_gho\` (`who_gho_maldives_long.csv`, 1,624 rows, 21 indicators) and `worldbank_wdi\` (`worldbank_wdi_maldives_health_long.csv`, 280 rows, 14 indicators). Built with `health_api_pull.py`.
- **Licences:** WHO GHO CC BY-NC-SA 3.0 IGO; World Bank CC BY 4.0.
- **Indicators:** beds per 10k, doctors, nurses, dentists, pharmacists, raised blood pressure and glucose, diabetes, obesity, tobacco, NCD mortality 30–70, UHC index, out-of-pocket share, life expectancy, maternal mortality, under-5 and neonatal mortality, cause-of-death shares. All **N**.

### 1.9 Derived (built here)

Folder `_derived\`. Builders: `health_build_atoll_summary.py` and `health_facility_master.py`.

- **`health_atoll_summary.csv`**: one row per atoll plus Malé. Fields:
  - population (2022 census, resident)
  - top tier and number of hospitals / health centres (2020)
  - inpatient beds 2020 and beds per 1,000
  - outpatients, inpatients and admissions (2020)
  - outpatient visits 2023 and per capita
  - emergency evacuations 2023 and per 1,000
  - Aasandha empanelled facilities
  - Aasandha spending per capita, 2025
  - staff per 10k 2023, in 7 cadres
- **`public_health_facility_master.csv`**: the 187 MHS-2020 island facilities (category and grade) joined to the HEMS 2026 licence. 183 matched; 10 are HEMS-only, mostly Malé hospitals plus Dharumavantha.
- Tidy copies of yearbook tables:
  - `mbs_T6-3_2021yb_hospital_beds_2020_tidy.csv`
  - `mbs_T6-3_2026yb_outpatients_by_atoll_tidy.csv`
  - `mbs_T18-28_aasandha_evac_by_atoll_2023_tidy.csv`
  - `mbs_T18-25_aasandha_expenditure_by_atoll_tidy.csv` (long format)

---

## 2. Key facts

### Facility network and tiers

- **2020 (MHS T1-2):** 430 facilities.
  - 190 public: 166 health centres, 22 hospitals, 2 clinics.
  - 240 private, including 92 resort clinics, 86 allopathic clinics and 6 hospitals.
  - 46% of all facilities are in NSP Zone 3 (Malé region).
- **Referral hierarchy (NSP zones, MHS Fig 1-3):**
  - Kulhudhuffushi RH covers the north.
  - Ungoofaaru (Raa) RH covers north-central.
  - IGMH / Centre for Mental Health covers the centre.
  - Gan (Laamu) RH, ASMH (GDh Thinadhoo) and Addu Equatorial (S Hithadhoo) cover the south.
  - Every other atoll has one atoll hospital on its capital island: HA Dhidhoo, Sh Funadhoo, N Manadhoo, B Eydhafushi, Lh Naifaru, AA Rasdhoo, ADh Mahibadhoo, V Felidhoo, M Muli, F Nilandhoo, Dh Kudahuvadhoo, Th Veymandoo, GA Villingili, Gn Fuvahmulah. Kaafu has health centres only.
- **Dialysis (news only, no dataset):** 19 units across 9 atolls plus the 2 original centres (Oct 2025). Vaavu, Faafu and Dhaalu were still pending; Dh Atoll Hospital opened Jan 2026. About 11 islands had dialysis by 2026.

### Capacity

**Inpatient beds, 2020 (MBS 2021 T6.3; ÷ 2022 census population).**
- 2,581 inpatient beds: Malé 998, atolls 1,583.
- Beds per 1,000:

| Group | Beds per 1,000 |
|---|---|
| Malé region | 4.7 |
| **Highest:** Meemu | 11.0 |
| Laamu | 9.9 |
| Thaa | 9.6 |
| Faafu | 9.0 |
| GDh | 7.2 |
| **Lowest:** Kaafu (excl. Malé) | 1.6 |
| Baa | 3.5 |
| Dhaalu | 4.1 |
| HDh | 4.1 |
| Lhaviyani | 4.1 |

- WHO: 45.6 beds per 10k in 2021.
- IGMH, 2025: 537 beds, 464,783 outpatients, 15,509 inpatients, average stay of about 5.6 days, occupancy 45.9%.

**Workforce, 2023 (MBS T6.1/6.2).**
- 11,955 staff: Malé 5,042, atolls 6,913.
- Doctors and dentists: 1,516, of whom **911 (60%) are expatriates**.
- Nurses: 3,716, of whom 1,346 are expatriates.
- Doctors per 10k (MoH HR 2023):

| Group | Doctors per 10k |
|---|---|
| **Lowest:** Kaafu (excl. Malé) | 4.6 |
| ADh | 15.8 |
| Baa | 16.9 |
| Lhaviyani | 17.3 |
| **Highest:** Vaavu | 43.8 |
| Faafu | 37.1 |
| GDh | 35.0 |

  These ratios are inflated in small atolls with a fixed hospital establishment.

### Utilisation

**Outpatient visits, 2023 (MoH snapshot).** 3,183,577 visits:

| Consultation type | Visits | Share |
|---|---|---|
| General medicine incl. casualty / emergency | 1,824,077 | 57% |
| Specialists | 1,241,591 | |
| Dentistry | 88,148 | |
| Allied health | 29,761 | |

**Top 10 specialist consultation types, 2023 (no diagnosis-level outpatient data are published):**

| Rank | Specialty | Visits |
|---|---|---|
| 1 | Internal medicine | 187,890 |
| 2 | O&G (other 126,491 + antenatal 52,693) | 179,184 |
| 3 | Paediatrics | 149,864 |
| 4 | Orthopaedics | 147,352 |
| 5 | General surgery | 97,066 |
| 6 | ENT | 82,733 |
| 7 | Dermatology | 78,575 |
| 8 | Ophthalmology | 76,673 |
| 9 | Cardiology | 34,770 |
| 10 | Psychiatry | 33,319 |

**Outpatient visits per capita, 2023 (atolls):** highest in GDh (8.8), Faafu (8.5), Laamu (8.2) and Thaa (7.6); lowest in Kaafu outside Malé (1.9), Vaavu (3.8) and Noonu (4.3). Kaafu residents mostly use Malé facilities.

**HPA notifiable "reasons for consultation", 2025 (MBS T6.17; atoll and island level):**

| Condition | Cases |
|---|---|
| Acute respiratory infection | 371,794 (69,178 under age 5) |
| Viral fever | 133,821 |
| Diarrhoea | 53,671 |
| Dengue | 2,611 |
| Typhoid | 35 |
| Scrub typhus | 28 |
| Measles | 0 |

**Top causes of admission, 2020 (MHS T3-11).** 41,800 admissions. Excluding 5,725 not categorised and 4,028 ill-defined:

| Rank | Cause | Admissions |
|---|---|---|
| 1 | Maternal conditions | 8,551 |
| 2 | Cardiovascular | 2,785 |
| 3 | Genitourinary | 2,690 |
| 4 | Injuries | 2,476 |
| 5 | Digestive | 2,464 |
| 6 | Perinatal | 2,285 |
| 7 | Infectious and parasitic | 1,444 |
| 8 | Endocrine | 1,231 |
| 9 | Respiratory diseases | 1,227 |
| 10 | Respiratory infections | 1,124 |

**Top causes of death, 2020 (MHS T4-8, GBD sub-groups; 1,278 deaths):**

| Rank | Cause | Deaths (share) |
|---|---|---|
| 1 | Other cardiovascular | 166 (13%) |
| 2 | Cerebrovascular | 105 (8%) |
| 3 | Ischaemic heart disease | 102 (8%) |
| 4 | Other respiratory | 80 |
| 5 | Lower respiratory infections | 68 |
| 6 | COPD | 58 |
| 7 | Other infectious | 48 |
| 8 | COVID-19 | 48 |
| 9 | Hypertensive heart disease | 29 |
| 10 | Other malignant neoplasms | 26 |

- Deaths in 2025: 1,399 (Malé 830, atolls 569).
- World Bank, 2021: NCDs cause 77% of deaths.

### NCD prevalence

- **STEPS 2020-21, ages 18–69:**

| Indicator | Prevalence |
|---|---|
| Raised blood pressure | 27.4% (M 24.0, F 31.4) |
| Hypertensives not on medication | 67.5% |
| Raised fasting glucose or on medication | 8.7% |
| Obese | 18.1% |
| Overweight | 52.5% |
| Current smokers | 23.1% (M 35.6%) |
| Insufficient physical activity | 45.8% |

- **DHS 2016-17, self-reported hypertension, women 15–49, by atoll:** from 1.4% (Gn) to 9.9% (AA).

### Referrals, evacuations and overseas treatment (Aasandha)

- **Emergency evacuations:** 3,727 in 2018, 4,079 in 2023, 4,426 in 2024.
- **Patients sent abroad:** 5,588 in 2018, 13,170 in 2023, 15,535 in 2024.
- **Evacuations per 1,000 residents, 2023:**

| Atoll | Evacuations per 1,000 |
|---|---|
| GA | 32.0 |
| GDh | 26.7 |
| HA | 21.2 |
| Sh | 20.5 |
| Kaafu | 2.2 |
| Malé | 0.2 |

- **Aasandha spending 2025:** MVR 3.26 bn in total, including:
  - overseas: MVR 418 M
  - inter-atoll transport of critical patients: MVR 23.4 M (sea 19.9 M, air 3.6 M; air was 32.7 M in 2023)
  - dialysis: MVR 13.0 M
- **Spending per capita, 2025:** Malé about MVR 8,970; S Addu 6,934; HDh 5,747; Kaafu outside Malé 592.

### Ambulances and sea ambulances

There is no dataset. News reports say MNDF runs the sea-ambulance service, that MoH plans to procure 13 sea ambulances for the atolls, and that Japan funded one USD 3.6 M sea ambulance. MEMS (Maldives Emergency Medical Services) is licensed in HEMS as an area-specific centre in Malé.

---

## 3. Main gaps and suggested work-arounds

1. **No island-level bed, specialist, ICU or maternity inventory after 2020.**
   - Use MHS 2020 T1-14 grade plus 2021 T6.3 beds per tier per atoll.
   - Treat HEMS licence level as the 2026 tier.
   - MoH's facility grading standard defines services by grade; it was not downloaded.
2. **No diagnosis-level outpatient data.** Use specialty mix (national) and HPA notifiable diseases (island level, 2025).
3. **No referral origin–destination matrix.** Only Aasandha evacuation counts by atoll (2023) and spending by atoll and island exist. Facility annual reports (Dhivehi, scanned) may hold atoll referral counts.
4. **No coordinates in MoH sources.** Join `public_health_facility_master.csv` to the OSM POIs from the other workstream on atoll + island name.
5. **Ambulance, sea-ambulance and dialysis counts** come only from news; no official table was found. The web-search budget ran out before more searching could be done.
6. **Mixed years** (beds 2020, staff 2023, population 2022). All yearbook health tables are flagged "provisional".
