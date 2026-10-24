# 13. Sea and land transport fares (Maldives)

Outputs: `data/external/fares/sea_land_fares.csv` (4,304 rows), `sea_land_fares_model.json`. Build script: `scripts/fares_build_sea_land.py` (re-runnable, `python -I`). FX 15.42 MVR/USD. No WebSearch used; no new downloads were needed.

## Sources used
| Source | Used for | Quality |
|---|---|---|
| Gazette (gazette.gov.mv) RTL tariff notices, parsed in `rtl_gazette_fares_parsed.csv` (20 notices 2022-06 to 2026-04; 3 cancelled/replaced notices excluded) | fast_ferry_rtl one-way and return fares with great-circle km, ~2,300 island pairs | Official, high |
| Gazette IUL 472/1/2024/58 (20 May 2024) | Greater Male taxi tariff, 2 vehicle classes | Official, high |
| `Avas_Ride/car_fare_matrix.csv`, `avas_zone_pair_distances.csv` | ride-hailing zone fares, observed ride km/min | Good; matrix equals the regulated taxi tariff |
| corporatemaldives.com, atolltimes.mv | bus fares, concessions, 2020 Thaa-Laamu MTCC ferry fares, historic taxi caps | Press, high/medium |
| therestlessbeans.com, asocialnomad.com, cestee.com, wikivoyage | MTCC public ferry, bus and speedboat prices (2023-24) | Travel blogs, medium/low, conflicts noted |
| amaldives.com (2026), atolltransfer.com | tourist USD ranges for ferry, speedboat, private charter | Marketing/estimates, low |
| raajje.mv 21781 | resident speedboat charter quotes (Milandhoo) | One article, "up to" figures, medium |
| mfr.mv Aasandha explainer | sea ambulance / emergency transfer policy | Policy only, no price |

## Sources that failed or were not usable
- `rtl_routes.csv` / `rtl_stops.csv` have no fare columns (only route, zone, stops, trips/day; stops have lat/lon, used for two charter distances). RTL fares come from the gazette instead; route codes like Z2R18 are not in the gazette tables, so join by island name.
- Gazette PDF for Thinadhoo council launch hire (IUL 415/415/2026/69, `doc_400097_286844`): Dhivehi text is garbled in the extract and `pdftoppm` is not installed, so the figures 262.50 / 300.00 / 3000.00 could not be labelled. Not used. This is the only lead for a dhoni/launch charter tariff.
- Hawks private speedboat article: no price. atolltimes pages on taxis/EV buses/road law: no fares beyond those used. Seaplane/air ambulance articles: out of scope (air).
- The `q_*.html` gazette search pages, sitemaps and PDFs were not mined further.

## Models (see JSON for full detail)
| Mode | Model | n | r2 | Note |
|---|---|---|---|---|
| fast_ferry_rtl (island to island, standard tariff) | one-way MVR = 33.8 + 1.79 x great-circle km | 1,837 directed pairs | 0.87 | True structure is a step tariff: 35 (1.5-10 km), 50 (7.5-18.5), 65 (12-33), 70 (17-30), 100 (26-64), 125 (35-71). Prefer snapping to the tier by km (medians 5, 11, 16, 22, 32, 47 km). Return is about 1.8x one-way. Intercept is large, so the line overstates very short hops (<5 km). |
| fast_ferry_rtl_highway_link (inter-zone) | roughly flat: median 150, range 130-170 north/central; 250 and 490 southern | 256 | 0.17 | Not distance driven; use median or the explicit tier. |
| ferry_public (old MTCC) | thin, median MVR 22 | 8 points | n/a | Harbour hops 3-15, Kaafu islands 22-53; no km, no regression. |
| speedboat_scheduled | thin, median USD 30 (MVR ~460) | 6 | n/a | Foreigner USD prices only. |
| speedboat_charter | resident: 438 + 48.8 x km (thin, from two "up to" quotes); tourist per-nm USD 12 (~MVR 100/km) | 2 (+ rate) | undefined | Order of magnitude only. |
| dhoni_charter | none | 0 | n/a | Gap. |
| sea_ambulance | none; assume MVR 0 to patient | 0 | n/a | Policy, not tariff. |
| bus | Greater Male flat 7 (city minibus), 10-15 (Hulhumale/airport routes), 5 (Villimale) | 15 rows | n/a | |
| taxi | fixed tariff, see zone table | 32 rows | n/a | |
| ride_hailing | MVR 30-120 by zone pair | 36 | n/a | |

### Greater Male
- Taxi (May 2024): within Male / Hulhumale: 30 (45 for 7-10 seat). Male-HM1 85, Male-HM2 100, Male-airport 70, HM1-HM2 40, HM1-airport 80, HM2-airport 85. 7-10 seaters: 130 / 155 / 110 / 60 / 125 / 130. Domestic terminal +10 (+15 large); +5 per bag beyond 3. Fares are routinely exceeded in practice (press reports).
- Ride-hailing (Avas matrix): MVR 30 to 120. Same as the regulated taxi tariff; Sea Plane and Domestic Terminal pairs cost 10-40 more. Median observed ride: Male-HM1 8.3 km / 12.7 min, Male-airport 4.5 km / 8.3 min.
- Bus: MVR 7 city minibus (Oct 2022), 10 for R2/R3/R4, 15 for R8/R9, 5 Villimale.
- Ferry: airport-Male 15 (20 at night), Male-Hulhumale 10, Villimale 3 (older source). A state-run EV taxi service was due to start in 2026; its fares had not been announced in the sources.

## Concessions
Zero fare, not percentage discounts. Buses and Greater Male ferries: free for age 65+, under 3, school students in uniform, university students with ID (since Sep 2023) and people with an NSPA special-needs card. For atoll RTL ferries Atoll Times (c. Jul 2026) only confirms free travel for people with disabilities and the elderly; free travel for regular-treatment patients (plus one assistant) is proposed, not in force. No evidence of student exemption on atoll RTL ferries. Aasandha covers emergency medical transfer.

## Gaps
- Sea ambulance and dhoni charter prices: none. Resident speedboat charter: two upper-bound quotes from one island.
- No local vs foreigner split in RTL gazette tariffs (single price list). Foreigner speedboat prices are tourist USD quotes, not tariffs.
- Distances are great-circle; sea routes are longer. About 35% of gazette CSV rows (1,474 of 4,189) involve a fuzzy island-name match and are marked confidence medium.
- Most blog fares are 2023-24; the 22 vs 53 MVR Male-Maafushi conflict is unresolved (53 favoured).
- RTL route code (Z2R18 etc.) to island pair mapping is not in any fare file.
- Reported inflation after a 2026 oil shock (petrol and diesel reported to have more than doubled) may mean current fares differ from the 2022-2025 gazettes; no 2026 re-tariff found except new zone notices (Feb-Apr 2026) at the old tiers.

## What a demo should assume (labelled assumptions)
1. **Atoll island to hospital/school by RTL ferry (local)**: use the step tariff by great-circle km (assumption: do not inflate distance for sea routes, since the tiers and regression are on the great-circle basis). One-way MVR 35 / 50 / 65 / 70 / 100 / 125; return = 1.8x. Different-zone Highway Link: MVR 150 (130-170). Confidence high where a gazette pair exists, medium for the regression.
2. **Student in uniform / senior / disabled**: MVR 0 on Greater Male bus and ferry (high); on atoll RTL ferry assume 0 for senior and disabled (medium), full fare for students (assumption, unconfirmed).
3. **Where no RTL service (emergency, off-schedule, night)**: resident speedboat charter, MVR 438 + 49/km (low confidence; about MVR 1,200 at 15 km, 2,500 at 42 km). Label as "up to" quotes.
4. **Sea ambulance**: patient cost MVR 0 (Aasandha policy); real cost approximate to a charter.
5. **Greater Male**: bus 7-15, taxi per tariff table, ride-hailing per Avas matrix (30 within zone, 85 Male-HM1, 70 Male-airport).
6. **Old MTCC ferries (Kaafu/Vaavu, Thaa-Laamu)**: 22-53 MVR as reference only; prefer RTL tiers.
7. **Tourists**: scheduled speedboat USD 25-50, private USD 150-300 per trip; irrelevant for local household cost.
