# 09b - Laboratory and diagnostic services by island (Maldives)

Companion data: `data/external/health/services/diagnostics/diagnostic_services.csv` (396 rows, one per facility x service category; schema: facility_name, operator_type, facility_type, island, atoll, service_category, service_detail, evidence, source_url, source_date, confidence).
Built by `scripts/diag_merge_rows.py` from five stream files in `data/external/health/services/diagnostics/sources/<stream>/rows.csv` (plus per-stream builder scripts in `scripts/`).

## 1. Method

1. Five parallel streams: (A) PCR/molecular, public health lab, blood banks, thalassaemia; (B) imaging (CT/MRI/mammography/endoscopy/X-ray/USG); (C) private labs and diagnostic centres, with HEMS registry staffing as a weak locator; (D) public hospital laboratories; (E) island health-centre labs/X-ray.
2. Sources: hospital websites and APIs (IGMH, Kulhudhuffushi, Ungoofaaru, Addu Equatorial, Thinadhoo, Tree Top, ADK), MoH news (health.gov.mv, Dhivehi listing crawled), edition.mv, avas.mv, raajje.mv, atolltimes.mv, mmtv, MoH policy documents, HHFA 2022/23, MHS 2020, HEMS and Maaharaa facility registries, Aasandha provider list (762 providers).
3. Merge: normalise atoll/island/hospital names, de-duplicate on facility x category (highest confidence kept, other evidence appended), then add tier-inferred rows for public atoll/regional hospitals from HHFA 2022/23 aggregate rates (lab_advanced and lab_basic "medium", X-ray and USG "low"; these are flagged `HHFA` in evidence and are NOT facility-confirmed).
4. Confidence: high = operator/official source or explicit news that service operates (136 rows); medium = indirect, older, or tier-inferred with an aggregate statistic (171); low = registry-only, planned, or weak inference (89).
5. Resort clinics/labs are kept in the CSV with the resort named in `island` (e.g. Sun Island Resort PCR lab); they serve guests, not residents, and should be excluded from resident-access analysis.

Row counts by category: lab_basic 150, ultrasound 68, xray 56, pcr_molecular 38, lab_advanced 29, mammography 11, ct 10, endoscopy 10, blood_bank 9, histopathology 8, mri 7.

## 2. Sources (including failed ones)

Worked: IGMH lab page and 2025 service charter; Kulhudhuffushi RH site API; Ungoofaaru RH site; AEH brochures; ASMH pages; Tree Top lab catalogue (2,421 tests, 1,948 referred to Metropolis India); ADK site; MoH PDFs (National Policy on Health Laboratories 2020, National Standards for Medical Laboratories, Quality Standards Maldives Healthcare, National Minimum Requirement for Facility Equipment 2025, HHFA 2022/23); MHS 2020 (diagnostics section 1.1.6, workforce by atoll); eMTCT validation report 2018; raajje.mv 64532 (mobile labs, Oct 2019); avas.mv (Innamaadhoo lab, Jan 2020); edition.mv (health-centre labs 2019-2026); MoH news crawl; presidency pledges; MoH approved private PCR list (Nov 2022) and work-permit medicals clinic list (Aug 2026); HEMS (601 establishments); Maaharaa (558 facilities).

Failed / blocked / not usable:
- psmnews.mv, cms.psmnews.mv, see.mv, travelpulse: HTTP 403 (used search snippets only, rows marked medium).
- mbs.gov.mv 403; hpa.gov.mv 502 (nothing on the National Public Health Laboratory); presidency.gov.mv listings 500; imdc.com.mv and vmh.gov.mv 406; ghsindex.org PDF 403; old.health.gov.mv and the "Approved PCR labs 19.06.2022" PDF not retrievable.
- About 92 of 176 MoH facility annual-report PDFs are Dhivehi in a non-Unicode font or image-only and no OCR is installed, so they yielded only scattered English fragments (e.g. B Atoll Hospital 2021 lab/X-ray charts, Ga Atoll 2022 lab/cross-match, HA 2022 USG/X-ray, L Fonadhoo 2023 lab statistics, R Maduvvari 2023 lab statistics). MBS annual reports 2021/2022/2024 are scanned.
- The shared WebSearch budget (200) ran out part-way, so coverage of Hulhumale CT, Senahiya, the 2026 CT rollout, Advance Diagnostic Center (Eydhafushi), F&C Medicare (Addu) and Medicrest (Velidhoo) is thin.
- Websites for Mediflex, Villa Biomedicals, MVDX, Novalux, Family Care, AIMS, Senahiya, Eye Care returned nothing usable.

## 3. Summary by atoll (confirmed or medium+ evidence; resorts excluded)

lab_adv/histo = advanced lab or histopathology at high confidence only (tier-inferred hospital FBC/RFT/LFT rows are NOT counted here). Blank "-" = no evidence found, not proof of absence.

| Atoll | Adv. lab / histopathology (high) | CT | MRI | Mammography | Blood bank / transfusion | PCR / molecular |
|---|---|---|---|---|---|---|
| K (Male, Hulhumale) | Male, Hulhumale | Male, Hulhumale | Male, Hulhumale | Male, Hulhumale | Male, Hulhumale | Male, Hulhumale |
| HA | - | - | - | - | Dhidhoo (cross-match) | - |
| HDh | Kulhudhuffushi | Kulhudhuffushi | Kulhudhuffushi | Kulhudhuffushi | Kulhudhuffushi | Kulhudhuffushi |
| Sh | - | - | - | - | - | Funadhoo (GeneXpert) |
| N | - | - | - | - | - | Maafaru (airport private lab) |
| R | Ungoofaaru | Ungoofaaru | Ungoofaaru | Ungoofaaru | Maduvvari HC (cross-match) | Ungoofaaru |
| B | - | - | - | Eydhafushi | - | Dharavandhoo, Eydhafushi |
| Lh | - | - | - | - | - | Naifaru |
| AA, ADh, V, M, F, Dh, Th | - | - | - | - | - | - (ADh: private PCR at Sun Island resort only) |
| L | - | Gan | - | Gan (medium) | - | Gan |
| GA | - | - | - | - | Villingili | Villingili |
| GDh | - | Thinadhoo | - | Thinadhoo | Thinadhoo | Thinadhoo |
| Gn | - | Fuvahmulah (Nov 2025) | - | Fuvahmulah | - | - (planned) |
| S (Addu) | Hithadhoo | Hithadhoo | Hithadhoo | Hithadhoo | Hithadhoo | Hithadhoo |

Key reading:
- CT exists on 8 islands: Male, Hulhumale (Tree Top; Hulhumale Hospital CT unconfirmed), Kulhudhuffushi (2019), Hithadhoo (2019/20), Gan (Dec 2020), Ungoofaaru (2021), Thinadhoo (relaunched 2025/26), Fuvahmulah (Nov 2025).
- MRI on 5 locations only: Male (IGMH, ADK), Hulhumale (Hulhumale Hospital, Tree Top), Kulhudhuffushi, Ungoofaaru (Dec 2024), Hithadhoo. This matches HHFA 2022/23 (MRI only in Male, HDh, S at assessment time).
- Endoscopy only at IGMH, ADK, Tree Top, Addu Equatorial (no atoll/regional endoscopy found).
- Full histopathology: IGMH, ADK, Hulhumale Hospital, Addu Equatorial, Kulhudhuffushi (high/medium); Ungoofaaru website claim (medium). Elsewhere specimens go to Male or abroad.
- Full-service in-country lab "hubs" outside Greater Male: Kulhudhuffushi, Ungoofaaru, Addu Equatorial, plus Gan, Thinadhoo and Fuvahmulah (partial; biochemistry/haematology and blood banks, no confirmed histopathology).
- Atoll hospitals in AA, ADh, V, M, F, Dh, Th, Lh, B, N, Sh, HA, GA have only tier-inferred routine biochemistry/haematology (HHFA: 100% of 23 hospitals do FBC, RFT, LFT, lipids) with no evidence of hormones, tumour markers, culture or histopathology.
- Advanced private labs (hormones, tumour markers, culture, send-out to India) are essentially Male/Hulhumale only: Tree Top, ADK, Medlab, Mediflex, AMDC (SRL partner). Private islands outside K: IMDC and AIMS Diagnostic Care (Addu); small clinics in Eydhafushi, Naifaru, Thinadhoo, Fuvahmulah, Mahibadhoo, Dharavandhoo, Dhangethi, Meedhoo (R) with basic blood tests plus X-ray.

## 4. Tier standards (what each level is supposed to provide)

- Facility grades (Quality Standards): HCG1-3 (health centres), HG1-3 (atoll/regional hospitals), Tertiary. Dedicated lab and radiology infrastructure expected from HCG1 up; imaging equipment (mobile X-ray, X-ray, USG) from HG1 up; pathologist and radiologist posts at HG3 and Tertiary; breast screening and lab cancer diagnosis from HCG3. Tertiary care "includes super-specialities and advanced diagnostic services; IGMH is the only government facility providing this" (Quality Standards, 2020s).
- Lab categories (National Standards for Medical Laboratories): Cat 1 = confirmatory tests plus screening in biochemistry, microbiology, haematology, pathology (BSL2/3); Cat 2 = screening/initial tests without confirmation; Cat 3 = point-of-care only. National Policy on Health Laboratories 2020 designates L-I, L-II, L-III tiers by hospital beds/function and proposes IGMH as apex National Reference Lab with 4-5 Regional Reference Labs.
- eMTCT report 2018: island health centres do basic haematology and rapid tests (HIV TriDot, syphilis SD Bioline) and refer samples; atoll hospitals do a variety of haematology, serology, urine and stool culture; confirmatory HIV testing at IGMH.
- Equipment standard 2025 Annex 4 lists the full lab (haematology analyser, coagulation, biochemistry and HbA1c analysers) and radiology (X-ray, CT, MRI, USG, mammography, DEXA) set, but does not map items to tiers.
- Reality (HHFA 2022/23, 188 facilities): hospitals 100% FBC/blood group/renal/liver/lipid; health centres about 50% have the same tests; culture and sensitivity 65% of hospitals and 3% of HCs; imaging in hospitals: USG 83%, X-ray 91%, mammography 22%, CT 30%, MRI 17%; health centres essentially none (USG 4%, X-ray 1%). 24-hour lab: 41% of facilities. MHS 2020: CT/MRI not done in any health centre or atoll hospital in 2020.
- Coverage trend: about 90 islands had a lab in Oct 2019; 76 still had none in late 2023; from 2024 point-of-care testing; Jan 2026 the minister pledged a physical lab and technologist on every island by end-2026 (60 foreign lab technicians recruited). 15 health centres were in a lab-construction tender in May 2026 (R Fainu, N Kudafari/Fodhdhoo, B Kudarikilu/Dhonfanu, M Raiymandhoo, L Mundoo/Kunahandhoo, Sh Goidhoo, HA Muraidhoo, HDh Kumundhoo/Naivaadhoo, Th Omadhoo/Gaadhiffushi, ADh Dhidhdhoo). A China lab-equipment grant (Mar 2024) covers 13+ further health centres (status unverified, low confidence in CSV).

## 5. Referral of samples and patients from islands without labs

- Policy (Lab Policy 2020): tests not done at a lower level are referred to the next higher level or the centre; "transportation of infectious samples between islands through courier service by sea/air is not streamlined, and therefore patients are directly referred to the central laboratory"; networking of health-centre labs to atoll/regional labs "is not streamlined". Samples not testable in-country are sent abroad (Aasandha-funded); Tree Top refers 1,948 of its 2,421 catalogue tests to Metropolis (India); bone-marrow-transplant cross-match goes to India; DHL was contracted historically for overseas shipment.
- Practice: islands without a lab collect samples at the health centre and send them by boat with the next transport to the atoll hospital or nearest lab (Laamu mobile-lab scheme: Mundoo and Dhanbidhoo samples to Maabaidhoo; Kunahandhoo and Maamendhoo to L. Hithadhoo). Innamaadhoo (R) residents previously travelled 20 min by speedboat or 1 h by ferry to Ungoofaaru before their own lab opened (Jan 2020).
- COVID-era: WHO funded sample-collection and referral carriers; islands/resorts shipped swabs to the nearest PCR lab; GeneXpert at 7-8 regional/atoll hospitals; peak about 13 government-permitted PCR labs.
- Imaging referral: Kulhudhuffushi made 74 urgent CT/cardiac referrals to Male in the year before its CT; Fuvahmulah referred 75 CT cases to IGMH/AEH in 5 months before its scanner. Muli RH ultrasound was broken with no radiologist (2025); GA Villingili digital X-ray sat in storage over 2 years; Maamigili (ADh) X-ray delivered but idle for lack of radiographers.
- Blood: atoll supply depends on local donors; blood banks at Kulhudhuffushi, Thinadhoo, Addu; cross-match/transfusion at Villingili, Dhidhoo, Maduvvari. A 2026 Kulhudhuffushi case required AB-negative donors flown from Male. National service is Maldivian Blood Services (Hulhumale; thalassaemia programme, about 650 patients, about 220 packs/week).

## 6. Gaps and cautions

- No published island-by-island list of tests; the CSV is a best-effort evidence compilation. "-" in the table means "no evidence found", especially for AA, ADh, V, M, F, Dh, Th, Lh, Sh, N, HA hospitals where only tier-inference exists.
- Tier-inferred rows (source = HHFA aggregate) are not facility-confirmed: use `confidence` and the `HHFA` marker in evidence to filter. About 25 HEMS-staffing-derived private rows have island set to Male/Hulhumale by assumption (low).
- Hulhumale Hospital CT, Fuvahmulah/Dh Kudahuvadhoo PCR, Naifaru and Villingili PCR are announced but not confirmed operational. Planned (not in CSV): CT in 15 islands and MRI at all tertiary hospitals (presidential pledge 2025), HA Dhidhoo CT/X-ray/USG building, mammography at Sh/HA/GA hospitals, MRI at Thinadhoo, Hulhumale Hospital 250-bed extension with MRI/endoscopy.
- Blood bank coverage for other atoll hospitals (B, Lh, N, Sh, AA, ADh, V, M, F, Dh, Th) is incomplete; many probably hold cross-match capability only.
- Equipment functionality changes quickly (breakdowns, staff shortages); dates in `source_date` should be respected.
- Potentially useful follow-up: OCR the Dhivehi annual reports (92 files), request the MoH "approved PCR labs" list and the L-I/II/III laboratory designation list, and the Maaharaa licensed-laboratory register detail.
