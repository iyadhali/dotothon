# 12 · Domestic air, seaplane and air-ambulance fares (Maldives)

Researched 2026-10-24. Output files:
- `data/external/fares/air_fares.csv`: 248 rows with the exact column set requested.
- `data/external/fares/air_fares_model.json`: regression coefficients and ratios.
- Build script: `scripts/fares_build_air.py`, run with `python -I`.
- Raw sources: `data/external/fares/air_sources/`.

**Bottom line.** Maldivian publishes **no fare table**. Fares exist only inside its booking engine, which was deliberately not scraped. Local fares are well documented through official press releases and news. They come in two layers:
- a **lowest/promo bucket**: about MVR 950–1,350 one-way on Malé trunk routes (official, March 2024);
- a **regular level**: about 1.43× the promo bucket, so MVR 1,400–1,900 one-way.

Government policy has **frozen local fares since about late 2023**. **Tourist (USD) fares are the weakest part of the data.** No official tariff was found, so they are estimated and every row is marked `confidence=low`.

## 1. How to use the CSV

The `source_date` column separates the current grid (2023–2026) from the historical rows (2018–2019).

| block | rows | what it is |
|---|---|---|
| Current grid | 36 operating routes × 5 rows = 180 | For every non-ceased route in `air/domestic_routes.csv`: (1) local one-way at the lowest/promo bucket, (2) local one-way at the regular level, (3) local return, (4) foreigner one-way (USD), (5) foreigner return. Observed values are used where found; otherwise `confidence=low, notes="estimated"`. |
| Foreigner bundles | 9 | LuxAtolls resort-transfer prices (flight plus speedboat, USD return per adult). These are an upper bound for the flight-only fare. |
| Historical | 35 | Jan 2019 subsidised fare cut (lowest and highest bucket, 10 routes), pre-2019 levels, Ramadan 2019 promo, MFR 2023 levels, a 2024 event fare. |
| Seaplane | 20 | Maldivian scheduled seaplane fares for locals (Thoddoo, Velidhoo); TMA/Manta resort-transfer prices by atoll; charter range; TMA free Thalassaemia flights. |
| Patient / air ambulance | 4 | Patient pays 0 (Aasandha / state air ambulance). Estimated system cost per air and per sea medevac. |

Conversion: USD × 15.42 = `fare_mvr`. MVR fares are recorded as MVR.

## 2. Sources

### Used

| Source | Content | Confidence |
|---|---|---|
| Maldivian press statement PDF, 14 Mar 2024 (`air_sources/maldivian_media/ps_promo_fares_2024-03-14.pdf/.txt`) | Promo one-way local fares for 14 Malé routes: GAN 1,222; FVM 1,155; RUL/FMT/HRF 1,133; **KDM 1,333**; GKK/HDK/HAQ/TMF 1,111; KDO/FND 1,055; NMF/IFU 999. DRV and LMV promos were "already effective". | high |
| Corporate Maldives (WordPress REST API; `air_sources/corporatemaldives/`) | Same 2024 list, though it transcribes KDM as 1,133 (the PDF route rows say 1,333). LMV 1,377→949 (Jan 2024). MUM from 1,377 (May 2025). DDD from 1,111 (Sep 2026). Thoddoo seaplane 799 and Velidhoo seaplane 999 for locals. 2019 25–30% cut table. Ramadan 2019 promo. FIT fares −15% from Nov 2025. Minister (Jun and Oct 2026): local fares not raised in about 3 years; President blocked 3 proposed increases; tourist fares raised Apr 2026. Cabinet (Aug 2026) ordered IASL to cut tourist fares. Jet fuel USD 1.19→1.69→1.44/L (2026). Air-ambulance articles. Aasandha rules. | medium |
| MMTV `en.mmtv.mv/7891` (22 Jan 2026) | Southern regional one-way fares from 1 Feb 2026: GAN–FVM 500; FVM–KDM/GKK 650; GAN–KDM/GKK 900. | medium |
| Maldives Independent (sitemap → article; `air_sources/maldivesindependent/`) | 2019 cut details: about 15,000 seats/month in the lowest bucket; HAQ return was about 2,800 and GAN about 3,500 before the cut. Apr 2026: foreigner fares +USD 33 per sector on GAN and FVM. 2010 fuel and insurance surcharge of MVR 220. | medium |
| Aviators Maldives post 20565 (Apr 2026) | Tourist fare rise of +USD 33/sector (GAN, FVM) after MACL jet fuel rose 42%. | medium |
| MFR, 17 Apr 2023 | MLE–FVM went from ≤MVR 999 to ≥MVR 1,500, then +100–200. Jet fuel MVR 12→22/L. 2019 subsidy was MVR 35 m and IAS still lost MVR 126 m. No subsidy since 2019. | medium |
| Maldivian website pages (baggage, high-volume baggage, FAQ, child rules, refund) | Excess baggage per kg by sector (below). Surfbag charges in USD. MVR payment allowed only for locals and expatriates with ID. | high |
| Villa Air baggage page (embedded JSON) | 20 kg checked + 5 kg cabin. Excess **MVR 25/kg for Maldivians vs USD 5/kg for foreigners** (3.1×). | high |
| TMA FAQ and community page | Seaplane allowance 20 + 5 kg, excess USD 5/kg. Free flights for Thalassaemia children plus a parent. | high |
| LuxAtolls atoll guides and Pricing Index (Oct 2026; `air_sources/luxatolls/`) | Tourist transfer prices by atoll (seaplane and domestic+boat). Flight-only MLE–GAN $200–300 return, MLE–HAQ $250–350 return. Seaplane average $617 return (76 resorts, range $332–1,950). | low–medium |
| aMaldives budget guide 2026; atolltransfer.com (sea/land task files) | MLE–VAM $100–120 one-way. Domestic flights $90–150 one-way. Domestic plane transfer $110–285 per way. Shared seaplane seat $290–900. Private seaplane $2,600–16,000. | low |
| MBS Statistical Yearbook 2026 T18.22/18.24, 2025 T18.27 (`data/external/health/mbs_statistical_yearbook/`) | Aasandha spending on air and sea evacuation 2020–2025, evacuation counts, overseas airfare. | high |
| Aasandha scheme page; MFR "How Aasandha works" | Aasandha pays "all transportation fees of emergency cases" and economy tickets for overseas referrals. No reimbursement if the patient hires transport privately. | high |

### Failed or not used
- **WebSearch** worked once, then the session's shared search budget was exhausted. All later discovery went through site navigation: WordPress REST search on corporatemaldives.com and hoteliermaldives.com, the Maldives Independent sitemap, and the Maldivian news archive.
- **see.mv** (3 articles on fares) returned 403 to both curl and WebFetch, so they were skipped. **sun.mv** and **psmnews.mv** search returned 403.
- **Maldivian booking engine:** not queried, by policy. **Flight meta-search route pages** (Kayak, Skyscanner and similar) were blocked by the permission classifier and not accessed.
- Maldivian `downloads/` has no fare sheet. Villa Air, Manta Air and TMA publish no fares (TMA sells through resorts only).
- Wikivoyage atoll pages returned Wikimedia errors (rate-limited). The Maldives page has no fares.
- atolltimes search is JavaScript-only. The edition.mv sitemap has no slugs. The Maldives Independent WordPress API returns 404 (the site is Next.js; its text was taken from the page payload).
- Aasandha annual reports on disk are mostly Dhivehi, and no per-flight cost was extractable.

## 3. Fare-per-km model (used for routes with no observed fare)

**Trunk model (Malé ↔ outer airport, local lowest-bucket one-way):**
- `fare_MVR = 940 + 0.537 × km`, n = 16, R² = 0.56.
- Fitted on the 2024 promo table plus LMV (2024) and DDD (2026). The distances are great-circle values from `domestic_routes.csv`.
- The curve is very flat: 142 km costs MVR 949 and 545 km costs MVR 1,222. So **fare per km tapers from about MVR 6.7/km (LMV) to MVR 2.2/km (GAN)**. Pricing is close to zone-flat, with a large fixed component.

**Regional model (inter-atoll legs not touching Malé):**
- `fare_MVR = 267 + 4.02 × km`, n = 5, R² = 0.85, fitted on the Feb 2026 southern fares.
- It is applied to the northern and central short legs (HAQ–HDK, LMV–NMF, DRV–IFU, FND–HDK/HRF, KDO–TMF/MUM, KDM–RUL/MUM, FMT–KDM, GKK–KDO/KDM, FVM–KDO). **Low confidence:** those legs may not have received the 2026 reduction.

**Regular vs lowest bucket:**
- The regular local fare is **1.434 × the lowest bucket** (mean of 12 ratios).
- Inputs: LMV 1,377/949; FVM about 1,600/1,155; and the 2019 highest/lowest bucket pairs for 10 routes, which range from 1.37 to 1.57.

**Foreigner vs local:**
- The foreigner fare is estimated at **1.28 × the local regular fare**. This rests on two LuxAtolls flight-only anchors: GAN gives 1.10 and HAQ gives 1.45.
- That works out to roughly **1.6–2.1× the cheapest local promo fare**.
- Estimated tourist one-way fares come out at about USD 115–160 on Malé trunk routes, and about USD 230–320 return.
- Cross-checks:
  - LuxAtolls flight+boat bundles are $300–500 return.
  - Blog figures are $90–150 one-way.
  - Villa Air prices foreigners' excess baggage at 3.1× the local rate, which suggests the true gap may be larger on some routes.
- Treat foreigner rows as **order-of-magnitude** values.

**Duration:** `block_time_min` comes from `domestic_routes.csv`. For pairs missing there, the same distance model is used (15 + 0.2·km under 100 km; otherwise 27.1 + 0.125·km).

## 4. Local vs foreigner gap, and subsidies

**Two-tier pricing is explicit.**
- Locals and resident expatriates can pay in MVR with ID. Tourists are priced in USD (Maldivian high-volume-baggage page; Villa Air baggage tiers).
- Corporate rates for resorts and guesthouses also exist (Sep 2025).

**Divergence in 2025–2026.**
- Local fares have been held flat for about 3 years by presidential instruction: three proposed increases were blocked. The minister has said domestic fares are "not set above cost" (Jun and Oct 2026).
- Tourist fares were cut about 15% (FIT, from Nov 2025), then raised in **Apr 2026** (+USD 33 per sector on GAN and FVM after jet fuel rose 42%). In **Aug 2026** the cabinet ordered IASL to review and reduce them.
- The local freeze is therefore an **implicit subsidy**: an SOE absorbs the losses, plus cross-subsidy from tourist fares. It is not a line-item subsidy.

**Explicit subsidy in 2019.**
- The government paid MVR 35 m to fund the 25–30% cut of Jan 2019. About 15,000 seats/month were offered in the lowest bucket. These rows have `fare_type=subsidised`.
- IAS still lost MVR 126 m. With no subsidy after 2019, fares crept up through 2022–23 as jet fuel went from MVR 12 to 22/L.

**Regional "lower fares" from Feb 2026.** The southern MVR 500–900 fares fall under the government-led South Connectivity initiative.

**Student and senior discounts:** none published or found. Child and infant rules exist, but no percentages were found. Lounge and Premium Economy add-ons exist (Premium Economy from Apr 2025 gives 25 kg baggage and does not affect economy fares).

**Patients.**
- Aasandha pays all transport for approved **emergency** evacuations (sea or air) and economy tickets for overseas referrals. Maldivian has carried Aasandha passengers under an agreement since 2015, Villa Air since 2022.
- Non-emergency domestic trips to a doctor are paid by the patient at the normal local fare. Childbirth travel cover was cut where islands have a resident gynaecologist (see `research/03`).
- The state **air ambulance** (from 1 Mar 2024) is free at the point of use. It is funded jointly by MoH, NSPA and Aasandha, and carried 931 patients on 787 flights in its first year. It was extended to Thailand and the UAE in Nov 2025. NSPA medical welfare moved to Aasandha on 1 Jun 2026.

## 5. Baggage (Maldivian)
- Cabin allowance is 5–7 kg. The free checked allowance is not stated on the site: atolltransfer quotes 20 kg, and Premium Economy gets 25 kg.
- Excess baggage per kg, by sector:
  - MLE–GAN 80; FVM 77
  - MLE–GKK/KDM/RUL/FMT 68
  - MLE–HAQ/HRF/HDK/FND/KDO 56
  - MLE–IFU/NMF/LMV/MUM 50
  - MLE–DRV/TMF 44
  - GAN–KDO 40
  - other inter-atoll legs 30
  - All figures are MVR plus tax.
- Villa Air: 20 kg checked, excess MVR 25/kg for locals and USD 5/kg for foreigners.
- Seaplanes (TMA): 20 + 5 kg, excess USD 5/kg.

## 6. Fare timeline

| date | event |
|---|---|
| 2010 | +MVR 50 on GAN/HAQ/KDO/KDM plus an MVR 220 insurance and fuel surcharge |
| pre-2019 | Highest return fares: HAQ about MVR 2,800, GAN about MVR 3,500 |
| 10 Jan 2019 | 25–30% subsidised cut. Return fares MVR 1,098–1,562 (DRV) up to 1,698–2,666 (GAN) |
| 2021–23 | Fares rise (MLE–FVM goes from ≤999 to ≥1,500 one-way, then +100–200). Fuel MVR 12→22/L |
| Jan–Mar 2024 | Promo buckets: LMV 949 (from 1,377); 14 routes at MVR 999–1,333 |
| Apr 2024 | Throughfares: up to 5% off domestic+international tickets |
| 2023–Oct 2026 | Local fares frozen |
| Nov 2025 | FIT (tourist) fares −15% |
| Feb 2026 | Southern regional fares MVR 500–900 |
| Mar–Apr 2026 | Jet fuel USD 1.19→1.69→1.44/L; tourist fares +USD 33/sector (GAN, FVM) |
| Aug 2026 | Cabinet orders a tourist-fare reduction |
| Sep 2026 | MLE–DDD launched from MVR 1,111 (Manta Air leaves domestic) |

**Currency note.** The task rate is 15.42 MVR/USD (official). Parallel-market dollars cost more (often MVR 17–20 in 2023–25), so USD fares cost locals more than 15.42 implies.

## 7. Seaplanes and medevac costs

**Seaplanes (context).**
- Resort transfers are sold only through resorts. Per adult return:
  - North Ari and Vaavu: $400–500
  - Baa and Lhaviyani: $450–600
  - Raa: $500–600
  - Noonu and Shaviyani: $500–650
  - Thaa: $550–650
  - Haa Alifu: $600+
  - Portfolio average: $617
- Private charters cost $2,600–16,000.
- Maldivian runs scheduled seaplane services to local islands at local fares: Thoddoo MVR 799, Velidhoo MVR 999 (promo), Fulhadhoo (fare not published).
- Manta Air left domestic ATR flying in Sep 2026 to focus on seaplanes.

**Medevac and who pays.**
- Aasandha's inter-atoll critical-patient transport spending, by air / by sea (MVR m):

  | year | air | sea |
  |---|---|---|
  | 2020 | 38.0 | 20.8 |
  | 2021 | 26.0 | 21.0 |
  | 2022 | 24.4 | 23.1 |
  | 2023 | 32.7 | 22.0 |
  | 2024 | 17.3 | 19.1 |
  | 2025 | 3.6 | 19.9 |

- The collapse in air spending after 2024 matches the start of the state air ambulance, which appears to be funded outside Aasandha's claims budget.
- Evacuation counts: 4,079 (2023) and 4,426 (2024).
- Estimated cost per air medevac: **about MVR 88k** (2023 air spend ÷ ~373 air evacuations, assuming the 31/339 charter share from a PSM report). Average sea evacuation: **about MVR 5.9k**. Both are low-confidence estimates.
- The patient pays nothing for approved emergencies. Self-hired transport is not reimbursed.

## 8. Gaps / next steps
1. **Tourist USD fare per route.** No official sheet found. The best fix is a dated manual check of the Maldivian booking site by a person, or an airline or MoTCA fare circular. One parliamentary or SOE committee document would replace all the estimates.
2. **Regular local fares by route.** Only LMV, MUM and FVM are observed. The rest are promo × 1.434.
3. **Villa Air (VAM) local fare, and Manta's former DDD/DRV fares:** not found.
4. **Inter-atoll fares in the north and centre** (HAQ–HDK, LMV–NMF, DRV–IFU and others): estimated from the 2026 southern regional model.
5. **Student, senior and disability concessions:** none documented. Child fare percentage unknown.
6. **Air-ambulance unit cost and budget line:** not published. Look at the MoH budget or the NSPA–IASL agreement. The figure above is an estimate.
7. The 2024 promo buckets apply only to selected flights and limited seats. Effective average fares paid are higher. Island Aviation passenger revenue per passenger would calibrate this; the PCB/SOE quarterly reports have revenue but no passenger counts.
