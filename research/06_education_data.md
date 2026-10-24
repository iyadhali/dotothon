# 06 – Education provider data (location, levels, capacity, student mobility)

Collected 2026-10-24 for the multi-modal accessibility project. Everything downloaded sits under
`data/external/education/<source>/`. The scripts that parse it are in `scripts/edu_*.py`; run each with
`python -I` (or `.venv/Scripts/python.exe -I` for the scripts that need pandas, openpyxl or pymupdf). OSM POIs and
census population counts are handled elsewhere and are not repeated here.

## Outputs to use first

| File | What it is |
|---|---|
| `data/external/education/institutions_master.csv` | 483 rows. Columns: institution, type, campus, island, atoll, levels_offered, enrolment, year, source_url, plus sector, atoll_code, teachers, enrolment_2025_moe_dir, highest_grade, offers_grade_11_12, notes. It holds (a) 203 higher-education/TVET rows from the Oct-2026 register (campuses, outreach centres and institute head offices; 99 have a stated island), (b) 12 institution-total rows with enrolment, (c) 261 schools from 2022-23 with grade range and enrolment (213 matched to the 2025 MoE directory for teachers and 2025 students), and (d) 7 directory schools that did not match. |
| `data/external/education/island_education_supply.csv` | 193 islands. For each: 2024 school enrolment, highest grade enrolled, whether grades 11-12 are on the island, and counts of HEI campuses and outreach centres. Use it as the destination layer for accessibility. |

**Key accessibility facts from the data**
- **Higher secondary is scarce.** Only **44 of 184 atoll islands** have any grade 11-12 enrolment (MoE 2024). Another 133 islands stop at grade 10.
- **Many students must move after grade 10.** 4,191 of 8,744 atoll grade 9-10 students (48%) attend school on an island with no grade 11-12. Across all atoll schools there are only 1,798 grade 11-12 students against 8,744 in grades 9-10.
- **Census 2022 shows the drain to Malé.** Malé residents attending Gr11-12 numbered 2,558, against 1,406 in all atolls. Tertiary attendance was 12,728 in Malé against about 8,400 in the atolls.
  - Among 16-19 year olds, 64% are studying in Malé against 47% in the atolls.
  - Education is the reason given by 43-53% of lifetime migrants to Malé from key atolls. For recent migrants (under 1 year) it is 23-39%.
- **Malé dominates higher-education supply.** Universities and colleges have 18 campuses in Malé City. Outside Malé, HEI campuses cluster in regional hubs: Kulhudhuffushi, Thinadhoo, Hithadhoo, L. Gan, Naifaru, Dhidhdhoo and Fuvahmulah.

---

## 1. Higher-education & TVET providers (campuses, levels)

### 1a. Register of Higher Education and Training Institutions ("Dhaftharu – Registered Colleges and Institutes"), Oct 2026
- **Source:** Ministry of Education, Higher Education & Skills Development (MoE). [PDF](https://www.moe.gov.mv/storage/files/resources/1791106952537-Dhaftharu-%20Registered%20Colleges%20and%20Institutes%20(1).pdf). It is linked from https://www.moe.gov.mv/en/reports-and-publications.
  - An earlier edition, dated 12 Aug 2025, came from the former MoHE. [PDF](https://mohe.gov.mv/images/resources/resources/Dhafutharu%20-%20%20Registered%20Colleges%20and%20Institutes%20as%20of%20-12-08-2025.pdf)
- **Files:**
  - `moe_registered_colleges/1791106952537-Dhaftharu-Registered_Colleges_and_Institutes.pdf`
  - Tidy: `moe_registered_colleges/registered_hei_campuses_2026.csv`, built by `scripts/edu_build_registry.py`. It has 203 rows, 119 institutions, and 99 rows with a location.
  - Older edition: `mohe_higher_education/Dhafutharu_-_Registered_Colleges_and_Institutes_as_of_-12-08-2025.pdf`
- **Granularity:** institution × campus/outreach centre × island.
- **Coverage:**
  - Universities: MNU (8 campuses/outreach centres) and IUM (7 campuses + 16 outreach centres).
  - 10 private colleges: Villa College (16 campuses), Clique, Cyryx, Mandhu, MAPS, Avid, MBS, MIANZ (6), Zikura and MIT.
  - 2 government colleges: Police (3) and CDSS (7).
  - 72 private institutes, 31 government institutes (including Maldives Polytechnic and the National Centre for the Holy Quran's 14 island centres) and 2 foreign institutes.
- **Key fields:** institution, category, sector, registration_no, campus, campus_type, atoll_code, atoll, island, location_stated.
- **Gaps:**
  - The Dhivehi text cannot be extracted, so the English columns were transcribed by hand. Check against the PDF before using.
  - Most institutes have no stated address. They are probably in Malé, but this is not confirmed.
  - The IUM main campus in Malé is not listed separately. A row was added for it and flagged.
  - Maldives Polytechnic has no campus list in the register, and no campus list was found online. News reports mention planned Fuvahmulah and GDh. Gadhdhoo campuses and TVET centres being built in HA Dhidhdhoo, R Alifushi, N Velidhoo, Kulhudhuffushi, Fuvahmulah and Sh Funadhoo.
  - No coordinates. Join on island name to the island gazetteer or OSM.
- **Licence:** a government publication with no explicit licence. Attribute MoE.

### 1b. Locally Available Higher Education Programmes as of 2025 (MoHE)
- **Source:** [PDF](https://mohe.gov.mv/images/resources/resources/Locally%20Available%20Programmes%20as%20of%202025.pdf), from https://mohe.gov.mv/resources.
- **Files:**
  - `mohe_higher_education/Locally_Available_Programmes_as_of_2025.pdf`
  - Tidy CSVs: `locally_available_programmes_2025.csv` (1,181 programmes) and `locally_available_programmes_2025_by_institution.csv` (30 institutions, with the MNQF levels each offers). Built by `scripts/edu_extract_mohe_programmes.py`.
- **Granularity:** institution × programme × MNQF level, for levels 5-10 (diploma and above).
- **Gaps:**
  - No campus attribution.
  - Certificate-level (MNQF 1-4) and TVET short courses are missing. Maldives Polytechnic shows only 21 programmes at levels 5-6.
- **Licence:** a government publication.

### 1c. MNU course catalogue by campus
- **Source:** https://courses.mnu.edu.mv/campus/{1..5}, covering Malé, Thinadhoo, Kulhudhuffushi, Gan and Hithadhoo.
- **Files:**
  - Scraper: `scripts/edu_mnu_courses.py`. The server returns intermittent HTTP 500s, so the script retries.
  - Output: `mnu_courses/mnu_courses_by_campus.csv`, 486 rows: Malé 214, Thinadhoo 73, Hithadhoo 72, Kulhudhuffushi 67, Gan 60. Raw HTML is in `mnu_courses/html/`.
- **Key fields:** campus, island, atoll, course_id, course, duration, mode, level_group. The MNQF level is inferred from the course title.
- **Gaps:**
  - Not every course listed runs every year.
  - The 3 outreach centres (R Ungoofaaru, HA Ihavandhoo, Dh Kudahuvadhoo) are not in the catalogue.
  - No enrolment figures.
- **Licence:** website content.

### 1d. Other institution websites checked
- Villa College campus pages (https://villacollege.edu.mv/campus) list 5 campuses (Hithadhoo, Kulhudhuffushi, L. Gan, Naifaru, QI/Malé), fewer than the 16 in the register, and give no per-campus programmes.
- polytechnic.edu.mv gives no campus list.
- tveta.gov.mv did not respond.
- The MQA site (mqa.gov.mv) has no downloadable register of institutions. The 2025 institutional audit report link is an empty template, so it was not kept.

## 2. Capacity – higher education

### 2a. MBS Statistical Yearbook 2022, education tables 7.24-7.31 (source: Ministry of Higher Education)
- **Source:** https://statisticsmaldives.gov.mv/yearbook/2022/. The files are XLSX and PDF.
- **Files:** `mbs_statistical_yearbook/yb2022/7.24-7.31.{xlsx,pdf}`. Tidy: `yb2022/hei_enrolment_by_institution_2019_2021.csv`, built by `scripts/edu_tidy_mbs_yearbook.py`.
- **Content:**
  - 7.27: number of HEIs, 2019-21.
  - 7.28: HEI staff by sex, nationality and FT/PT, 2019-21. In 2021 there were 1,695 staff.
  - **7.29: enrolment by institution, 2019, 2020 and 2021.** 2021 total 12,861: Villa 4,223, MI/MIANZ 2,496, MNU 2,376, Zikura 1,139, MAPS 1,000, MBS 671, Cyryx 494, Clique 387, Mandhu 75. IUM, Polytechnic and Avid appear only in 2020 and 2019.
  - 7.30: enrolment, graduates and dropout by field of study and sex.
  - 7.31: enrolment by MNQF level.
- **Granularity:** institution, national. **No campus or island split.**
- **Gaps:**
  - 2021 is the latest year with institution detail, and it omits IUM and Polytechnic.
  - The 2019 figures are fractional, apparently estimated from shares.
- **Licence:** MBS official statistics. Attribute "Maldives Bureau of Statistics".

### 2b. MoHE Statistics Booklet 2019-2023
- **Source:** [PDF](https://mohe.gov.mv/images/resources/resources/Statistics%20Booklet%202019-2023.pdf).
- **File:** `mohe_higher_education/Statistics_Booklet_2019-2023.pdf`
- **Content:**
  - National local enrolment: 27,421 (2019), 26,825 (2020), 26,733 (2021) and 29,016 (2022).
  - Academic staff: 869, 2,146, 1,867 and 2,395 for the same years.
  - Enrolment by MNQF level, field of study, loans and scholarships (1,693 scholarships, 2019-23), and spending of MVR 2.70 bn.
  - A list of 14 HEIs as of 30 Sep 2023.
- **Granularity:** national only.
- **Licence:** © MoHE. Dissemination is allowed for educational and policy use, not commercial use.

### 2c. MoHE Higher Education Statistics 2019 and the data-collection template
- **Files:** `mohe_higher_education/Higher_Education_Statistics_2019.pdf`, which includes a 2019 map of atolls with regional campuses, and `Higher_Education_Statistics_new_format_20.10.2019.xlsx`, which is the reporting template HEIs fill in (empty).
- **Also downloaded:**
  - `SCHOOL_LEAVERS_AND_THEIR_CAREER_CHOICES.pdf` (2020 survey). 6.8-7% of school leavers cite a lack of local higher education or training opportunities.
  - `National_Human_Capital_Needs_Assessment_Report.pdf`.

## 3. Schools – location, grade range, enrolment, teachers

### 3a. MoE School Statistics 2024 (data as of Nov 2024) – primary school source
- **Source:** [PDF](https://www.moe.gov.mv/storage/files/statistics/1782980847582-2024%20School%20Statistics.pdf). Earlier editions are in the same folder: 2023-24, 2022-23, 2021-22, 2020 and 2019.
- **Files:** `moe_school_statistics/1782980847582-2024 School Statistics.pdf`. Tidy CSVs sit next to it:
  - `..._island_enrolment_by_grade_wide.csv` and `_long.csv` (pages 22-37). These cover **184 atoll islands and 20 atoll totals × grades BN, N, LKG, UKG, GR1-GR12 × sex**. Derived fields: `highest_grade_enrolled`, `grade_9_10_enrolment`, `grade_11_12_enrolment`, `has_higher_secondary`. Every row sums to the PDF subtotal (`check_ok`). Built by `scripts/edu_extract_school_stats_islands.py`.
  - `..._atoll_enrolment_by_sector.csv` (page 12): schools and students by government, community and private sector × atoll.
  - `..._atoll_schools_teachers.csv` (page 38): schools by size, students, local and expat teachers, and pupil-teacher ratio × atoll. Nationally: 364 schools, 98,845 students and 11,534 teachers. Built by `scripts/edu_extract_school_stats_atoll.py`.
- **Gaps:**
  - The island tables cover atolls only. Greater Malé (Malé, Hulhumalé, Villimalé; 39,605 students, 44 schools) appears only as one total. Use 3c for Malé schools.
  - Enrolment is counted by island, not by school.
  - The 2023-24 edition is a scanned image and was not extracted. The 2022-23 and earlier PDFs were downloaded but not parsed.
- **Licence:** a government publication.

### 3b. MoE online school directory (government schools)
- **Source:** https://www.moe.gov.mv/en/schools and one page per school at `/en/schools/{id}`. Updated 23/05/2025. The figures are self-reported by schools.
- **Files:** `moe_school_directory/moe_school_directory.csv`, 220 schools; raw HTML is in `html/`. Built by `scripts/edu_moe_school_directory.py`.
- **Key fields:** school, atoll, atoll_code, island, opened date, status, students, teachers, govt_staff, address.
- **Totals:** 81,005 students and 9,952 teachers.
- **Gaps:**
  - No grade range.
  - Government schools only.
  - Island spellings vary.
  - One school (I'zzudhdheen) is temporarily closed.

### 3c. MBS Yearbook 2024 Table 7.2 – enrolment by SCHOOL × grade, 2022-23
- **Source:** https://statisticsmaldives.gov.mv/yearbook/2024/wp-content/uploads/sites/11/2024/11/7.2.xlsx
- **Files:** `mbs_statistical_yearbook/yb2024/7.2.xlsx`. Tidy: `yb2024/school_enrolment_by_grade_2022_23.csv`, 261 schools and preschools covering government, community and private, including Malé. 95,622 students. It records lowest and highest grade, and **44 schools offer Gr11-12**. Rows reconcile to the totals.
- **Gaps:** no sector column (inferred in the master file by matching to the directory), and spelling varies.

### 3d. MBS Yearbook 2023 Table 7.7 – enrolment by ISLAND × grade, 2021-22 (1 Jun 2022)
- **File:** `yb2023/7.7.xlsx`. Tidy: `yb2023/island_enrolment_by_grade_2021_22.csv`, 188 islands including Malé, Hulhumalé and Villimalé, plus 21 aggregate rows. Use it for time comparison.

### 3e. Other yearbook tables downloaded (raw, untidied)
- yb2025 (2023-24): 7.1-7.7, covering enrolment by level, sector, grade, schools and enrolment by locality, and schools/enrolment/teachers by atoll. Sheet "7.14" inside 7.2 and 7.5 is an empty template.
- yb2024: 7.1 and 7.3 (government teachers 2022-23); 7.15-7.22 (O/A-level exam results by atoll, 2019).
- yb2023: 7.8 and 7.9 (GER/NER 2006-22); 7.24 and 7.25 (technical education enrolment 2016-22).
- **Licence (MBS):** official statistics with attribution.

## 4. Student mobility

### 4a. Census 2022 education tables (MBS)
- **Source:** https://statisticsmaldives.gov.mv/census-2022/ (XLSX).
- **Files:** in `census2022_education_migration/`:
  - Raw: ED5-ED10, ED17, ED18, MG7, MG8 and MG13 (`.xlsx`).
  - Tidy, built by `scripts/edu_tidy_census2022.py`:
    - `census2022_ED18_attending_by_level_island.csv`: residents currently attending, by level × island. Levels: pre-school, primary, lower secondary, **higher secondary**, O/A-level classes, foundation, diploma, bachelor's, master's, PhD, certificate. Includes `tertiary_attending`.
    - `census2022_ED17_studying_by_age_island_long.csv`: population and currently-studying counts by age group × island. The 16-19 and 20-24 groups are the mobility signal. The source XLSX header shows the "2-5" and "6-12" age groups mangled into dates, corrected in the tidy file.
    - `census2022_MG13_male_residents_by_registered_island.csv`: Malé usual residents by island of registration. 157,254 in total, of whom 72,177 are registered in Malé. This gives a proxy for the diaspora from each island.
- **Gaps:**
  - No census table cross-tabulates reason for migration × island. Only the report-level tables below exist.
  - Attendance is counted at usual residence, so students who have moved show up in Malé.
- **Licence:** MBS official statistics.
- Census population tables (PP*) were deliberately not downloaded, since another agent covers them.

### 4b. Migration Report, Census 2022 (MBS, 2024)
- **Source:** [PDF](https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2024/02/Migration-Report-Census-2022.pdf). Also downloaded: `Migration-Summary.pdf` and `Migration-Census-2022.pdf`.
- **Tidy files:**
  - `census2022_reason_for_migration_to_male_by_atoll_pct.csv`: Tables 5.8 and 5.9, reason for migrating to Malé from HA, HDh, R, Th, GA, GDh and S, for all migrants and for migrants within the last year.
  - `census2022_reason_for_migration_by_destination_pct.csv`: Table 5.6 (Republic, Malé, atolls, admin islands; now vs 7 years ago) and Table 5.10 (Kulhudhuffushi, Fuvahmulah, Addu).
- **Key figures:**
  - Education drives 28-37% of migration to Malé.
  - Recent migration for education to Kulhudhuffushi is 34%, up from 15%. The report attributes this to the city's tertiary campuses.
  - The 10-14 age band surges among recent migrants because of migration for education.
- **Gaps:** only selected atolls, percentages only, and no island level.

### 4c. Dormitories and scholarships
- **No structured dataset was found.** From news and ministry sources:
  - MoHE plans student accommodation in R Dhuvaafaru, R Hulhudhuffaaru, GA Villingili and Fuvahmulah, announced Dec 2024 with a 5-year horizon.
  - MTCC is building a 32-room student hostel in HA Dhidhdhoo (2026).
  - MNU runs the Majeedhudheen Dhanaal hostel in Malé.
  - CHSE Malé and CHSE Hulhumalé are A-level-only government schools that draw atoll students.
- Scholarship and loan totals (national, by field and country) are in the MoHE Statistics Booklet (2b). There is no breakdown by student home island.

## Known gaps / next steps
1. **Campus-level enrolment and intake for HEIs is not published.** The yearbook gives only institution totals, latest 2021. The options are a data request to MoE Higher Education Division or MQA, or using the HEI reporting template.
2. **Maldives Polytechnic and TVET Authority centre locations and capacity** were not found online.
3. **Coordinates:** all files are keyed by atoll and island name, and spellings differ between sources (e.g. Fuvammulah/Fuvahmulah, Kurinbi/Kurinbee, Dhidhdhoo/Dhiddhoo). Join through a canonical island list with an alias table; `scripts/edu_island_supply.py` has a starter normaliser.
4. School grade ranges (2022-23) predate the 2023-24 "Atoll School" consolidations. The 2024 island tables give the current per-island picture.
5. A full transcription of the Dhivehi-only content in MoE Annual Report 2025 (`moe_annual_reports/Annual_Report_2025.pdf`) was not attempted.
