# 09c Specialist health services by island (Maldives)

_Datathon 2026 research note. Compiled 2026-10-24. Output dataset: `data/external/health/services/specialist/specialist_services.csv`, with **787 rows** covering **270 facility-island units** on **45 islands** (42 outside Greater Male')._

Scope: where specialised services exist, island by island, across public, private, NGO and military operators. This note does not cover dental services, labs/imaging, or facility tiers, beds and morbidity; other notes handle those.

## 1. Method

1. **Local MoH data that was already in the repo, re-mined for specialties**
   - *MoH Surgery data 2022 and 2023* (Table 1.7 surgeries by atoll and facility type; Table 1.10 facility list). These give evidence of a working operating theatre for each atoll or regional hospital.
   - *Maldives Health Statistics 2020*, Table 1-16: public-sector specialists by atoll and profession. In each atoll these specialists sit at the atoll or regional hospital.
   - English organograms and census charts in hospital annual reports: Kulhudhuffushi RH 2023, Ungoofaaru RH 2023, Dh Kudahuvadhoo 2023, F Nilandhoo 2023, HA 2021/2022 and GA 2022. Most other annual reports use legacy, non-Unicode Thaana fonts, so their text extraction is garbage and they were skipped.
2. **HEMS public registry (new pull).** `hems.health.gov.mv/establishments/<id>/professionals` lists the registered practitioners at each establishment, with profession and specialty. All 601 establishments were pulled by `scripts/health_hems_specialists.py`. Names were dropped and only counts per specialty per facility were kept (`sources/hems/hems_professionals_by_speciality.csv`, 1,391 rows). The coverage is mostly **private-sector**: public hospitals list few or no staff there.
3. **Geolocation of private facilities.**
   - The Aasandha local empanelled-provider list (763 providers, each with its island; `sources/visiting_tele_eye/aasandha_empanelled_local.csv`) was fuzzy-matched to HEMS names.
   - Where that failed, the Male'-region landline prefix (3xxxxxx) was used.
   - Anything still unresolved was assumed to be in Greater Male' and given **low** confidence.
4. **Web and news research.** This was done by 4 parallel workstreams:
   - dialysis, thalassaemia and NCD
   - oncology, cardiology and hospital departments
   - mental health, drug rehab, physiotherapy and sports
   - visiting camps, telemedicine and eye care

   Sources included MoH news, hospital and MCGH pages (mcgh.gov.mv/specialities), NDA, edition.mv, sun.mv, atolltimes.mv, avas.mv, maldivesvoice.mv, corporatemaldives.com and clinic websites. Raw captures are under `sources/<topic>/`.
5. **Merge.** `scripts/health_specialist_merge.py` does the following:
   - normalises atoll codes (census abbreviations, with **MLE** for Male', Hulhumale' and Villimale') and categories
   - de-duplicates on facility x island x category, keeping the highest-confidence and most recent row
   - appends other distinct details after `|| also:` and keeps up to 3 source URLs
   - geofixes blank islands from the HEMS/Aasandha match

   Visiting-camp rows are kept one per event. Rows describing *not-yet-operational / planned / gap* items stay in the CSV, flagged in `service_detail`, and are excluded from the matrix.

The partial files are in `sources/_partial/`:

| Partial file | Rows |
|---|---|
| hems_registry | 414 |
| local_reports_surgery | 189 |
| hospitals_onco_cardio | 172 |
| visiting_tele_eye | 157 |
| mental_rehab_physio_sports | 112 |
| dialysis_thal_ncd | 44 |
| extra_manual | 5 |

Together they hold 1,093 input rows, which merge to 787.

**Confidence:** 503 high, 204 medium, 80 low. **Operators:** 496 private, 269 public, 19 NGO, 3 military (Senahiya).

**Categories (rows):**

| Category | Rows |
|---|---|
| ncd_diabetes | 85 |
| maternity | 65 |
| psychiatry | 62 |
| physiotherapy | 57 |
| paediatrics | 57 |
| surgery | 53 |
| ophthalmology | 53 |
| orthopaedics | 47 |
| ent | 44 |
| visiting_specialist | 41 |
| dermatology | 39 |
| dialysis | 33 |
| cardiology | 31 |
| developmental_therapy | 19 |
| icu | 18 |
| oncology | 16 |
| drug_rehab | 12 |
| emergency | 11 |
| nicu | 8 |
| telemedicine | 8 |
| thalassaemia | 5 |
| geriatrics | 5 |
| nephrology | 4 |
| sports_medicine | 3 |
| fertility, pulmonology, rheumatology, urology, gastroenterology | 2 each |
| hyperbaric | 1 |

The categories after the core list are extra snake_case categories, used where the core list did not fit.

### Caveats (read before modelling)
- **Rows show presence, not capacity.** One row means "evidence the service exists". It does not tell you about hours, staffing levels or waiting times.
- **Private atoll polyclinics** (for example Vital Care Kulhudhuffushi, AIMS Feydhoo, Pine Tree Funadhoo) register specialists who often visit periodically rather than reside on the island.
- **MHS 2020 rows (medium confidence)** describe posts in 2020. Organogram rows describe *approved* posts, some of which may be vacant.
- **Ophthalmology** includes optical/optometry-only outlets, which are labelled in `service_detail`. Filter on "Ophthalmologist" when you need a doctor.
- **Physician rows mapped to `ncd_diabetes`** mean internal-medicine physicians who manage NCDs, not necessarily a dedicated NCD clinic.
- **54 Greater-Male' private rows have an assumed or inferred location**, and a few more are only inferred from a Male' landline number. All of them are flagged in `service_detail`.

## 2. Sources

**Used, with key files:**
- MoH Surgery data 2022 (`health.gov.mv/storage/uploads/roOjr2qP/fg4ihibj.xlsx`) and 2023 (`.../eY3GzxY3/2om420vh.xlsx`).
- Maldives Health Statistics 2020 (`.../79qgJ9YD/jjokopyg.pdf`).
- Hospital annual reports on health.gov.mv: KRH 2023 (`0wNN3bwA/ldoamukt.pdf`), URH 2023 (`Ko2x5PYQ/7qsqjacp.pdf`), Dh 2023 (`Ko2xMrYQ/zpszm3fr.pdf`), F 2023 (`rovPBeYj/z0xftjvr.pdf`), HA 2022 (`Arovx2Yj/bvtns64j.pdf`) and GA 2022 (`6eY3WxY3/9w5s4p1m.pdf`).
- National Mental Health Department annual reports 2024 and 2025, NDA annual reports 2021 and 2022, and the Dhamanaveshi 2024 report (read with pymupdf).
- HEMS public registry, pulled 2026-10-24.
- Aasandha local empanelled list (aasandha.mv).
- MCGH specialities page (mcgh.gov.mv/specialities).
- NDA website (centres list).
- Hospital pages for ADK, Tree Top (where reachable), Medica, EyeCare and the AEH doctor list.
- News on edition.mv, sun.mv, atolltimes.mv, avas.mv, corporatemaldives.com, maldivesvoice.mv and raajje.mv. Psmnews.mv was used through search snippets only. Key items:
  - atolltimes.mv/post/news/16462 and edition.mv/news/52305 (Jul 2026): overseas cancer referrals and chemotherapy availability
  - maldivesvoice.mv/2984 (Jun 2026): cancer plan, 2028 target, mammography sites
  - maldivesvoice.mv/1585: Dharumavantha tertiary upgrade
  - edition.mv/news/54795: Kulhudhuffushi Manas Hub
  - edition.mv/news/49111: Maafushi physiotherapy
- Thalassaemia master plan PDF; PMC paper on dialysis.

**Failed or limited:**
- **403:** psmnews.mv / cms.psmnews.mv, see.mv, mbs.gov.mv, mhsgmv.org and the Dhiraagu press release.
- **Unreachable or empty:** treetophospital.com, hmh.mv, male-optical.com, senahiya.mv, vmh.gov.mv, journey.org.mv, bulbulmaldives.com, cymacare.com.mv, back.raajje.mv (DNS), krh.gov.mv and Hulhumale' hospital pages (JavaScript shells), mrh.gov.mv ("coming soon"), and the IGMH cardiac page.
- **Other errors:** igmh.gov.mv (404 on several pages), imdc.com.mv (406), the UICC page (406), vitalcare.com.mv (526), journals.lww.com (402) and the Thalassaemia Society and Diabetes Society websites (do not resolve).
- **HEMS establishment detail pages** need a login, so the registry gives no addresses; the professionals JSON is public.
- **The session's shared WebSearch budget (200 calls) ran out mid-task.** As a result, ENT, cleft-lip and paediatric-cardiology camp searches, sports medicine, elderly care, and Gan, Muli and Fuvahmulah department details are under-searched.
- **Most MoH and atoll annual reports** use legacy Thaana fonts, so their text is unextractable.

## 3. Island x specialty matrix

Key:
- ● = at least one active row with high or medium confidence
- ○ = low-confidence evidence only
- Not-operational, planned and gap rows are excluded
- `n` = number of core specialties present, not counting visiting camps

Generated by `scripts/health_specialist_matrix_md.py`. The full per-category counts are in `sources/island_specialty_matrix.csv`.

| Atoll | Island | Dial | Onc | Card | ICU | NICU | O&G | Paed | Surg | Orth | ENT | Eye | Derm | Psy | Phys | NCD | Thal | Drug | ER | Tele | Visit | n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MLE | Greater Male' (Male'/Hulhumale'/Villimale') | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | 19 |
| HA | Dhidhdhoo |  |  |  | ● | ● | ● | ● | ● | ● | ● |  |  |  | ● | ● | ● |  |  |  | ● | 10 |
| HA | Ihavandhoo | ● |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 |
| HDh | Hanimaadhoo |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  | ○ |  |  |  | 2 |
| HDh | Kulhudhuffushi | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |  |  | ● | ● | ● | 17 |
| Sh | Funadhoo | ● |  |  |  |  | ● | ● | ● | ● | ● |  |  | ● |  | ● |  |  |  |  | ● | 8 |
| Sh | Komandoo | ● |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 |
| N | Manadhoo | ● |  |  |  |  | ● | ● | ● |  |  |  |  |  |  | ● |  |  |  |  |  | 5 |
| N | Velidhoo | ● |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 |
| R | Meedhoo |  |  |  |  |  |  |  |  |  |  |  |  |  | ● | ● |  |  |  |  |  | 2 |
| R | Ungoofaaru | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |  |  | ● |  | ● | 16 |
| B | Dharavandhoo | ● |  |  |  |  | ● |  |  |  | ● |  |  |  |  | ● |  |  |  |  |  | 4 |
| B | Eydhafushi | ● | ● |  | ● |  | ● | ● | ● | ● |  |  |  |  | ● | ● |  |  |  |  |  | 9 |
| B | Thulhaadhoo |  |  |  | ● |  |  |  |  |  |  |  |  |  |  | ● |  |  |  |  |  | 2 |
| Lh | Naifaru | ● | ● |  |  |  | ● | ● | ● | ● |  | ● |  | ● | ● | ● |  |  |  |  |  | 10 |
| K | Gulhifalhu |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  | 1 |
| K | Guraidhoo |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  |  |  |  | ● | 1 |
| K | Himmafushi |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  | 1 |
| K | Huraa |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ○ |  |  |  |  | ● | 1 |
| K | Kaashidhoo |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ● | 0 |
| K | Maafushi |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  |  |  |  | 1 |
| K | Thulusdhoo |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  |  |  |  | 1 |
| AA | Rasdhoo | ● |  |  |  |  | ● | ● | ● |  |  |  |  |  |  | ● |  |  |  |  |  | 5 |
| ADh | Dhangethi |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  |  | ○ | 1 |
| ADh | Dhidhdhoo |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ○ | 0 |
| ADh | Dhigurah |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ○ | 0 |
| ADh | Fenfushi |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ○ | 0 |
| ADh | Maamigili |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ○ | 0 |
| ADh | Mahibadhoo | ● |  |  |  |  | ● | ● | ● | ● |  | ● |  | ● |  |  |  |  |  |  |  | 7 |
| V | Felidhoo |  |  |  |  |  | ● | ● |  |  |  |  |  |  |  |  |  |  |  |  |  | 2 |
| M | Dhiggaru |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  |  |  | 1 |
| M | Muli | ● |  |  |  |  | ● | ● | ● |  |  |  |  |  | ● | ● |  |  |  |  | ● | 6 |
| F | Nilandhoo |  |  |  |  |  | ● | ● | ● | ● |  |  |  |  |  | ● |  |  | ● | ● | ● | 7 |
| Dh | Kudahuvadhoo | ● |  |  |  |  | ● | ● | ● | ● |  | ● |  |  |  | ● |  |  | ● |  | ● | 8 |
| Th | Veymandoo | ● | ● |  |  |  | ● | ● | ● |  |  |  |  |  |  | ● |  |  |  |  | ● | 6 |
| L | Gan | ● | ● |  |  |  | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |  |  |  |  | ● | 12 |
| GA | Villingili | ● |  |  |  |  | ● | ● | ● | ● |  |  |  |  | ● | ● |  | ● |  |  | ● | 8 |
| GDh | Thinadhoo | ● | ● | ● |  |  | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |  | ● |  | ○ | ● | 15 |
| Gn | Fuvahmulah | ● | ● |  |  |  | ● | ● | ● | ● |  | ● | ● |  | ● | ● |  | ● |  |  |  | 11 |
| S | Feydhoo |  |  |  |  |  | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ○ |  |  |  |  | 11 |
| S | Hithadhoo | ● | ● | ● | ● |  | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | 18 |
| S | Hulhudhoo |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  | 1 |
| S | Maradhoo |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | ● |  |  |  |  | 1 |

**Reading the matrix:**
- **Greater Male'** has everything. Hithadhoo (S) with 18, Kulhudhuffushi (HDh) with 17, Ungoofaaru (R) with 16 and Thinadhoo (GDh) with 15 are the only near-comprehensive atoll hubs, followed by Gan (L) with 12, Fuvahmulah (Gn) and Feydhoo (S, private AIMS) with 11 each, and Dhidhdhoo (HA) and Naifaru (Lh) with 10 each.
- **Most atoll hospitals** (AA Rasdhoo, ADh Mahibadhoo, N Manadhoo, Th Veymandoo, M Muli, Dh Kudahuvadhoo, F Nilandhoo, GA Villingili, B Eydhafushi) offer O&G, paediatrics, general surgery with anaesthesia, internal medicine, and now dialysis. Few have anything beyond that.
- **Non-capital islands** show up mainly for 2025–26 dialysis units: Ihavandhoo, Velidhoo, Dharavandhoo and Komandoo.

Surgical activity at atoll and regional hospitals, as major / minor operations (MoH Surgery data):

| Hospital | 2023 | 2022 |
|---|---|---|
| Kulhudhuffushi RH | 451 / 302 | 493 / 325 |
| Ungoofaaru RH | 183 / 117 | — |
| Gan RH | 156 / 147 | — |
| ASMH Thinadhoo | 134 / 222 | — |
| Addu Equatorial Hospital (tertiary) | 490 / 469 | — |
| AA Rasdhoo | 14 / 3 | — |
| N Manadhoo | 10 / 14 | — |
| Vaavu (Felidhoo) | **0 / 0** | **0 / 0** |

## 4. Specialties that exist ONLY (or essentially only) in Greater Male'

| Service | Where it exists | Nearest exception outside Greater Male' |
|---|---|---|
| **Radiotherapy** | **Nowhere in the Maldives.** Patients go abroad under Aasandha (15 Indian and 2 Sri Lankan partner hospitals). A Hulhumale' Phase 2 cancer hospital with radiotherapy and PET-CT is planned, with basic services targeted for 2028. | none |
| Medical oncology clinics, PET, onco-surgery | IGMH National Cancer Centre, Hulhumale' Hospital (oncology since 2017, ~5 beds), ADK, Tree Top, MIOT | Chemotherapy *administration* has been decentralised to Naifaru (Dec 2020), Thinadhoo (2023), Kulhudhuffushi (2023), Ungoofaaru (Jan 2026, 2 chairs) and probably Veymandoo. These run under Hulhumale' Hospital or IGMH protocols, with no resident oncologist. |
| Cardiac cath lab / PCI | IGMH (2016), ADK (2018), Tree Top (2018); Dharumavantha second lab planned | **Addu Equatorial Hospital**, operational 28 Jan 2026 and run by IGMH. It is the only one outside Male'. |
| Cardiothoracic and open-heart surgery, neurosurgery, GI/bariatric surgery | IGMH, ADK, Tree Top and Male' private hospitals. All 188 GI surgeries in 2023 were private and in Male'. | none (AIMS Feydhoo registers a neurosurgeon) |
| IVF / fertility | IGMH National Fertility Centre (Dharumavantha), Tree Top | none |
| Inpatient psychiatry | IGMH National Centre for Mental Health (9 beds); residential care at the K. Guraidhoo HPSN | Ungoofaaru RH: 4-bed unit, the only one in the atolls |
| National thalassaemia centre (transfusion and chelation) | Hulhumale' (moved to Orange Hiyaa in May 2025) | Local transfusion is documented only at Hithadhoo (S) and Dhidhdhoo (HA). 293 patients were followed on their home islands in 2023, but the sites are undocumented. |
| Paediatric cardiology and neurology, PM&R, gastroenterology/endoscopy, neurology, interventional radiology | Male' and Hulhumale' private and tertiary | a few visiting specialists at atoll polyclinics |
| Hyperbaric medicine (clinical) | ADK hyperbaric unit | resort chambers, e.g. Bandos (K), not mapped |
| Sports medicine | **No sports-medicine physician registered anywhere.** Only Tree Top's sports-injury orthopaedics and rehab, and Wellcare Physiotherapy & Sports Rehabilitation (both Hulhumale'). No Ministry of Sports medical unit was found. | none |
| Geriatric medicine | No dedicated department anywhere; only IGMH geriatric physiotherapy, Medica and Tree Top rehab | Guraidhoo HPSN (residential) |
| 24/7 nephrology | IGMH, Hulhumale', Tree Top, NU | Addu (nephrologist), KRH (1 nephrologist) |

## 5. Decentralised services (count of islands outside Greater Male')

| Service | Islands | Details |
|---|---|---|
| **Dialysis** | 20 operational | Fuvahmulah (Dec 2019); Eydhafushi (Nov 2022); Naifaru (2022/23); Kulhudhuffushi, Ungoofaaru, Thinadhoo, Gan and Hithadhoo (all pre-2024); Manadhoo (pre-2025); Ihavandhoo (Feb 2025); Velidhoo (Apr 2025); Veymandoo, Muli and Villingili (Apr 2025); Funadhoo (2025); Dharavandhoo and Rasdhoo (Aug 2025); Mahibadhoo (Oct 2025); Kudahuvadhoo (early 2026); Komandoo (about Apr 2026). **Not yet:** Nilandhoo (F; equipment ready, no water system) and Felidhoo (V). Kaafu has no unit and relies on Male'. |
| **O&G / maternity specialists** | 21 | Every atoll or regional hospital. Vaavu has normal delivery only, with no theatre or caesarean. |
| Paediatrics | 20 | |
| Surgery (operating theatre in use) | 19 hospital islands, plus Feydhoo (private) | |
| Orthopaedics | 15 | |
| Physiotherapy | 16 | Includes the new Maafushi service (Mar 2026), Bluspan branches in Dhidhdhoo and Thulusdhoo, and Fuvahmulah. |
| Psychiatry / mental health | 10 | Psychiatrists are posted **only at the 5 regional hospitals**: Kulhudhuffushi, Ungoofaaru, Gan, Thinadhoo and Hithadhoo. The others are psychologists in private clinics (Funadhoo, Naifaru, Mahibadhoo, Feydhoo), the Kulhudhuffushi Manas Hub youth centre (Oct 2026), or the Guraidhoo HPSN. |
| ICU | 6 | Kulhudhuffushi (ICU + CCU), Ungoofaaru (ICU + NICU), Hithadhoo (AEH), Dhidhdhoo (HA ICU census), Eydhafushi (B) and the private Omni Care in Thulhaadhoo (critical-care physician). |
| **NICU** | 3 | Kulhudhuffushi, Ungoofaaru and Dhidhdhoo. **None was found in the south**: no NICU evidence at AEH or ASMH. |
| Cardiology (cardiologist on site) | 4 | Hithadhoo, Kulhudhuffushi, Ungoofaaru and Thinadhoo (private Vitalcare). |
| ENT | 9 | |
| Ophthalmology | 10 | Ophthalmologists are at the EyeCare branches in Kulhudhuffushi, Gan and Hithadhoo, at AIMS Feydhoo, at Pro Care Mahibadhoo, and at the regional hospitals. Fuvahmulah, Ungoofaaru, Thinadhoo and Naifaru have optical outlets. |
| Dermatology | 7 | |
| Drug rehabilitation (NDA) | 8 | K Himmafushi (residential, about 80 patients; 500-bed new building begun Sep 2026), GA Villingili, GDh Thinadhoo, Gn Fuvahmulah, S Hithadhoo, S Hulhudhoo (Vilunu), K Gulhifalhu (remand detox) and HDh Hanimaadhoo (2021 listing only, low confidence). Inside Greater Male' there are also the Male' Gagan Clinic (methadone) and Community Service Centre, and the Hulhumale' halfway house. |
| Breast-cancer screening (mammography) | 7 | Male' region; 5 regional hospitals (Ungoofaaru and Thinadhoo confirmed; Kulhudhuffushi, Gan and Hithadhoo inferred); Fuvahmulah; Baa (Eydhafushi, Aug 2025). The government decided in 2026 to roll out cervical-cancer testing in all atolls. |
| Telemedicine | 4 | **Nascent.** The 2025 pilot links IGMH with KRH and Faafu Atoll Hospital (Nilandhoo) for cardiac, renal and stroke follow-up. AEH has a tele-consultation request service. Thinadhoo had a historic 2010 unit. Hulhumale' Hospital offers online mental-health consultations, there is the national 1677 helpline, and Tree Top provides app teleconsults. |

## 6. Visiting / periodic specialist provision

Visiting camps are **frequent but irregular, and mostly private or donor-led**:
- **Tree Top Hospital:** 18 multi-specialty CSR camps by June 2026, about 3–4 a year, each seeing 300–500 patients. Sites: Villingili (GA), Thinadhoo and Gan (2024); Veymandoo, Kudahuvadhoo, Dhidhdhoo and Muli (2025); Funadhoo and Gan (2026).
- **MCGH (public):** specialist surgical camps in 2025 at Kulhudhuffushi, Ungoofaaru, Addu and Laamu, with 969 patients and 86 surgeries.
- **Others:**
  - Sri Lankan High Commission camp at Nilandhoo (Dec 2025)
  - Vital Care camps with island councils in K Kaashidhoo, Huraa and Guraidhoo
  - Ungoofaaru psychiatry outreach
  - A 2018 MoH camp with Pakistani specialists across 8 hospitals
  - ADK camps (2018)
  - Indian forces / Senahiya camps (2014)
  - Cancer Society screening in Noonu
  - Diabetes Society island screening

There is **no evidence of a regular MoH specialist rotation**. A nephrologist from Addu visits Fuvahmulah quarterly.

## 7. Referral pathways (as evidenced)
1. **Island health centre** (primary care, midwife, GP; tele-advice) to **atoll hospital**: O&G, paediatrics, general surgery, internal medicine and, increasingly, dialysis and physiotherapy.
2. **Atoll hospital** to **regional hub**. The hubs are KRH (north: HA, HDh, Sh, N), URH (north-central: R, B, Lh), Muli (central; thin), Gan RH (L, Th), ASMH Thinadhoo (GA, GDh) and AEH Hithadhoo (S, Gn). For example, the HA Atoll Hospital referred 51 cases to IGMH and 42 to KRH in 2022.
3. **To Greater Male' tertiary care** (IGMH/Dharumavantha, Hulhumale', ADK, Tree Top, Senahiya) for cath lab care (until AEH in 2026), neurosurgery, cardiothoracic surgery, NICU for the south, inpatient psychiatry, oncology diagnosis and treatment planning, IVF and thalassaemia.
4. **Overseas (Aasandha):** radiotherapy, PET, most complex oncology and neurology care. Amrita Hospital (Kochi) is the main destination. There were 1,638 cancer patients abroad in 2023, 1,996 in 2024 and more than 2,000 in 2025. Only 39 went abroad for chemotherapy alone.
5. **Reverse flows:** chemotherapy and dialysis now return patients to their atolls, using Hulhumale' Hospital or IGMH protocols and devolved units. Telemedicine pilots and the AEH cath lab are run by IGMH.

## 8. Gaps (for the accessibility model)
- **Vaavu (Felidhoo):** no surgery in 2022–23, no caesarean, no births in 14 years, and no dialysis. **Faafu:** dialysis is installed but not running. **Kaafu (non-Male' islands):** no hospital, and services sit in Male'; Maafushi physiotherapy was added in 2026.
- **The south has no NICU and no inpatient psychiatry.** In the whole country, the only inpatient psychiatric beds are at IGMH and Ungoofaaru.
- **There are no psychiatrists in 15 of the 20 atolls.** Child development centres exist only in Hulhumale' and Hithadhoo, with therapy staff at KRH.
- **ICU** exists essentially at the regional hubs only. Muli RH (a Grade 1 regional hospital) shows little beyond the basic specialties.
- **Cardiology** outside Male' is limited to Hithadhoo (cath lab), Kulhudhuffushi and Ungoofaaru.
- **Oncology:** radiotherapy is absent nationally. The planned regional cancer services in Addu, HDh, Lh, R and GDh are not yet implemented, and the Auditor General (2026) found the Hulhumale' cancer-centre agreement not fully implemented.
- **Sports medicine and geriatric medicine** are absent as specialties.
- **Thalassaemia:** island transfusion sites are undocumented.
- **Evidence gaps to close later:**
  - department lists for Gan RH, Muli RH, Fuvahmulah and AA/ADh/N/Th atoll hospitals (beyond MHS 2020 posts)
  - public specialist staffing in 2024–26, since public staff are largely missing from HEMS
  - island locations for the 54 Male'-assumed or inferred private-clinic rows
  - the ENT, cleft and paediatric-cardiology camp record

## 9. Reproduce
Paths are relative to `data/external/health/services/specialist/` unless given in full.
```
python -I scripts/health_hems_specialists.py data/external/health/moh_hems_registry/hems_establishments.csv sources/hems/hems_professionals_by_speciality.csv
python -I scripts/health_hems_specialist_rows.py data/external/health/moh_hems_registry/hems_facilities_tidy.csv sources/hems/hems_professionals_by_speciality.csv sources/_partial/hems_registry.csv sources/visiting_tele_eye/aasandha_empanelled_local.csv
python -I scripts/health_specialist_local_rows.py sources/_partial/local_reports_surgery.csv data/external/health/moh_maldives_health_statistics/MHS2020_T1-16_workforce_by_atoll_profession_tidy.csv
# fork builders: health_specialist_dialysis_thal_ncd_rows.py, health_specialist_onco_cardio_rows.py,
#                health_specialist_mental_rehab_rows.py, health_specialist_vte_build.py (+ health_aasandha_empanelled.py)
python -I scripts/health_specialist_merge.py sources/_partial specialist_services.csv sources/island_specialty_matrix.csv
python -I scripts/health_specialist_matrix_md.py specialist_services.csv > sources/island_specialty_matrix.md
```
