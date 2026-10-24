# 07 — Air network (domestic flights, seaplanes, airport catchments)

As of 2026-10-24. All outputs are in `data/external/air/`. Raw downloads are in one subfolder per source. Scripts are in `scripts/air_*.py`/`.sh`.

## 1. Deliverables

| File | Rows | What it is |
|---|---|---|
| `airports.csv` | 48 | 20 operational airports (5 international, 15 domestic), 16 planned or under-construction airports, 11 resort seaplane bases from OurAirports, and the Velana waterdrome. Columns: IATA, ICAO, name, island, atoll, lat/lon, type, operator, runway (curated and OurAirports), opening date, status, est. scheduled service Oct-2026, notes, sources |
| `domestic_routes.csv` | 40 | **Main edge list.** One row per undirected airport pair per airline. Columns: est. weekly frequency each way, block time (min), distance, aircraft, routings, flight numbers, per-date leg counts, status, source, as-of date. Every value is flagged `estimated=yes` and carries a method note |
| `domestic_legs_directed.csv` | 69 | Directed legs as parsed from the Velana FIS (before symmetrising) |
| `block_time_calibration.csv` | 16 | Round-trip pairs (dep N / arr N+1) used to derive block times for each MLE route |
| `seaplane_destinations.csv` | 187 | 180 MBS-listed resorts plus 7 TMA resorts not in the MBS list. Columns: operator(s) (TMA / Maldivian Seaplane / Manta), distance from Velana, est. seaplane minutes, inferred access mode, coordinates where reliable |
| `airport_catchment.csv` | 191 | Every inhabited census island, with its nearest operational airport (straight line), second airport, and a rule-based "practical" airport plus reason |
| `validation_movements_vs_mbs2024.csv` | 20 | Estimated scheduled movements vs MBS Yearbook 2024 aircraft movements (from team-kandu `observations.csv`, table 11.17) |

Scripts:
- `scripts/air_parse_fis.py`: parses Velana FIS JSON/HTML into `velana_fis/fis_flights_parsed.csv`.
- `scripts/air_build_network.py`: builds all of the files above.
- `scripts/air_poll_fis.sh`: poller. One run was left polling `fis.com.mv/api/flights` every 15 min into `velana_fis/live/`. Run it for at least 7 days, then re-run the two Python scripts to replace the estimates with an observed weekly timetable.

## 2. Sources and what each gave

| Source (folder) | Used for | Notes |
|---|---|---|
| OurAirports `airports.csv`, `runways.csv` (`ourairports/`) | Coordinates, ICAO, runway lengths, 11 seaplane bases | 31 MV records. Some ICAO codes missing or different (LMV blank; FVM = VRMF vs VRMR in Wikipedia/SKYbrary) |
| Wikipedia wikitext (`wikipedia/`): List of airports, 20 airport pages, Maldivian, Manta Air, Villa Air, TMA | Opening dates, operators, runways, seaplane resort lists, fleets | Manta Air page (Sept 2026): Manta is **ceasing domestic ATR flights** to focus on seaplanes. Fuvahmulah/Faresmaathodaa pages were rate-limited, so news sources were used instead |
| **Velana FIS** `https://www.fis.com.mv/api/flights` plus 5 Wayback snapshots (`velana_fis/`) | **Domestic schedule:** flight numbers, routings ("via"), scheduled times | Live JSON is open (no key). It covers about 2 h ago to tomorrow (domestic: today only). Wayback Next.js pages with embedded JSON exist for 2026-06-17, 07-11, 07-12, 07-13 and 10-15. Days usable for frequency: 07-11 (Sat), 07-13 (Mon), 10-15 (Thu), 10-24 (Sat) |
| maldivian.aero (`maldivian/`) | Network list (26 codes in the booking widget, 19 domestic incl. MLE) | Booking engine sits behind Cloudflare Turnstile and a proof-of-work script. Not scraped; no public timetable PDF |
| TMA website (`tma/atolls/`) | 78 resorts TMA flies to, by atoll | WP REST portfolio endpoint is empty; atoll pages were parsed |
| mantaair.mv (`manta/`) | (little) | No destination list on the site. Manta seaplane resorts are taken from Wikipedia and news (Soneva Fushi 2026; Dhigufaru and Nika exclusive from Nov 2024; Kihavah, Kandima, Niyama, Riu at the 2019 launch) |
| MBS Yearbook 2025 T10.14 (`../_derived/yb2025_t10.14_resorts.csv`, built by another agent) | Resort list, island, **official distance from Velana** | Used as the seaplane base list and as the distance input |
| COD-AB admin points and census crosswalk (`../hdx-cod-ab`, `../_derived`) | Island coordinates and population for catchments and planned airports | |
| News: atolltimes, edition.mv, mmtv, avas, raajje, psmnews, mfr.mv, maldivesindependent | Hanimaadhoo expansion, Muli opening, Faresmaathodaa, Madivaru, Fuvahmulah, Ifuru dates, planned airports | URLs in `airports.csv:sources` |
| team-kandu `maldivian_destinations.csv` | Cross-check of Maldivian codes | All 19 domestic codes match `airports.csv` |
| MACL `Airport traffic_Dataset_27092026.csv` | Code alignment only | **International movements at MLE only** (regions South Asia, Middle East, etc.). Carrier, route and aircraft codes are anonymised (`Carrier_008`, `Route_0175`), so it cannot be joined to IATA codes and holds no domestic data |
| FlightConnections, flight.info, flightmapper | Not usable | Cloudflare challenge or empty response. Search snippets gave published MLE–GAN 1:10 to 1:35 and MLE–DRV about 0:40, which agree with the FIS-derived block times |

## 3. Summary table: operational airports

Frequencies and block times are **estimates** (see §4).

| IATA | ICAO | Airport (island, atoll) | Type | Runway m | Opened | Status | MLE link: airline, est. flights/wk each way, block min | Practical catchment: islands / pop 2022 |
|---|---|---|---|---|---|---|---|---|
| MLE | VRMM | Velana Intl (Hulhulé, K) | international hub | 3400 | 1966-04-12 | operational; new runway 2022, new terminal 2025, waterdrome 2022 | hub | 36 / 248,043 (Greater Malé + K, AA, V, F, north ADh) |
| GAN | VRMG | Gan Intl (Gan, S/Addu) | international | 2651* | RAF to 1976 | operational | Maldivian 18/wk, 102 min | 6 / 25,062 |
| HAQ | VRMH | Hanimaadhoo Intl (HDh) | international | ~2460 (new) | intl 2012; rebuilt 2025 | operational (expanded) | Maldivian 21/wk, 62 min | 8 / 7,649 |
| NMF | VRDA | Maafaru Intl (N) | international | 2200 | 2019-12-01 | operational | Maldivian 7/wk, 48 min (some via LMV) | 13 / 12,503 |
| VAM | VRMV | Villa Intl Maamigili (ADh) | international | 1800 | 2011-10-01 | operational | Villa Air 14/wk, 41 min | 5 / 5,636 |
| DRV | VRMD | Dharavandhoo (B) | domestic | 1189 | 2012-10-17 | operational | Maldivian 14/wk, 40 min (rotations with IFU) | 13 / 10,631 |
| FVM | VRMR | Fuvahmulah (Gn) | domestic | 1200 | 2011-11 | operational | Maldivian 18/wk, 88 min | 1 / 9,177 |
| RUL | VRQM | Maavarulu (GDh) | domestic | 1200 | 2020-07-04 | operational | Maldivian 7/wk, 82 min (with KDM) | 3 / 3,351 |
| IFU | VREI | Ifuru (R) | domestic | 1200 | 2015-05-29 | operational | Maldivian 14/wk, 49 min (with DRV) | 15 / 17,581 |
| KDM | VRMT | Kaadedhdhoo (GDh) | domestic | 1220 | 1993-12-10 | operational | Maldivian 14/wk, 72 min | 3 / 8,321 |
| KDO | VRMK | Kadhdhoo (L) | domestic | 1220 | 1986 | operational | Maldivian 18/wk, 52 min | 12 / 14,699 |
| GKK | VRMO | Kooddoo (GA) | domestic | 1800 | 2012-09-10 | operational (suspended 2024, resumed) | Maldivian 24/wk, 68 min | 7 / 7,253 |
| DDD | VRMU | Dhaalu (Kudahuvadhoo, Dh) | domestic | 1800 | 2017-06-01 | operational; Manta → Maldivian handover 2026 | Maldivian 28/wk, 48 min (Manta 28/wk in Jul, ceased) | 6 / 6,637 |
| TMF | VRNT | Thimarafushi (Th) | domestic | 1200 | 2013-09-03 | operational | Maldivian 4/wk direct + via KDO, 58 min | 13 / 10,260 |
| HDK | VRBK | Kulhudhuffushi (HDh) | domestic | 1220 | 2018-09-21 | operational | Maldivian 14/wk, 60 min (with HAQ/FND) | 13 / 20,269 |
| LMV | VRGD | Madivaru (Lh) | domestic | 1200 | 2022-02-18 | operational | Maldivian 4/wk, 42 min (with NMF) | 4 / 8,992 |
| FND | VRCF | Funadhoo (Sh) | domestic | 1200 | 2020-02-03 | operational | Maldivian 7/wk, 68 min | 11 / 11,542 |
| HRF | VRAH | Hoarafushi (HA) | domestic | 1200 | 2020-11-17 | operational | Maldivian 4/wk, 72 min (+ via FND) | 9 / 11,301 |
| FMT | VRQF | Faresmaathodaa (GDh) | domestic | 1200 | 2023-03-15 | operational, low frequency | Maldivian ~4/wk via KDM, 83 min | 5 / 3,023 |
| MUM | VRKM | Muli (M) | domestic | 1200 | 2025-05-20 | operational | Maldivian 7/wk, 48 min (with KDO) | 8 / 5,490 |

\* Gan runway sources conflict: 2651 m (2010 source), 3600 m (Wikipedia infobox), 3658 m (OurAirports). Verify against the AIP.

Outstation-to-outstation edges, from multi-stop rotations: DRV–IFU (21/wk), HAQ–HDK (7), KDM–RUL (7), LMV–NMF (7), KDO–TMF (5), KDO–MUM (4), GKK–KDO (4), FMT–KDM (4), FND–HDK, FND–HRF, GAN–GKK, GKK–KDM (about 2 each). July-only legs: FVM–GKK, FVM–KDM, FVM–KDO, GAN–KDM, KDM–MUM.

**Planned or under construction (in `airports.csv`, with island-centre coordinates):**
- Under construction: Makunudhoo (HDh, MTCC, works paused Jul-2026), Alifushi (R, 1200 m), Magoodhoo (F, 1800 m, behind its Sept-2026 target), Bileffahi (Sh, MACL, 30 months from Oct-2026), Vilufushi (Th, reclamation).
- Planned, contracts or start dates set: Villingili GA International (2.2 km, start expected late Nov-2026), Thulhaadhoo (B).
- Planned by presidential resolution (Mar-2024): Dhidhdhoo HA, Dhiguveli Sh, Milandhoo Sh, Vihafaru N, Fainu R, Mathiveri AA, Nilandhoo F, Maalhendhoo GA, Guraidhoo Th.
- Hanimaadhoo expansion is done: new runway of about 2.46 km and terminal opened in 2025. A further 700 m extension has been announced.

## 4. Methods (and why everything is marked estimated)

**Weekly frequency.** The FIS lists every domestic movement at MLE with flight number, scheduled time and "via" stops. On each usable day I counted legs per airport pair and multiplied the mean daily count by 7.
- For pairs involving MLE, I took the max of the two directions, because early-morning returns are often outside the window.
- For outstation pairs, I used (dir1 + dir2)/2, because each rotation appears on both the departure and the arrival board.
- The current season uses the two October days (Thu 15th, Sat 24th). Both start at about 08:00, so pre-08:00 departures (05:00–07:59, seen in July on IFU/DRV/GKK/KDM rotations) are missing and some routes are **undercounted by about 1 flight/day**. Day-of-week variation is only partly captured.
- If a pair was seen in only one of the two days, its estimate falls to about 4/wk.

**"Via" ambiguity.** The FIS gives destination plus via stop, but the ordering is inconsistent between boards. For example, Q2 132 is listed as "Maafaru via Madivaru" outbound and "Madivaru via Maafaru" inbound. Edges are therefore undirected, and a rotation's outstations are both credited with an MLE edge.

**Block time.** For nonstop routes I used `(arr(N+1) − dep(N) − 25 min turn) / 2` from the FIS (16 routes, up to 15 pairs each). Example values: MLE–DRV 40, DDD 48, HAQ 62, KDO 52, GKK 68, KDM 72, FVM 88, GAN 102 min. These match published durations (DRV about 40 min; GAN 70–95 min, flightmapper 1:35).
- For other legs I used a fitted model: `block = 27.1 + 0.125·km`, implied about 480 km/h block speed. Legs under 100 km use `15 + 0.2·km`.
- Treat ±10 min as the uncertainty. The model ignores airline-specific turn times; for example, Manta MLE–DDD round trips were 120–150 min.

**Aircraft.** The FIS gives no aircraft type, so fleet-level types are given:
- Maldivian: ATR 72-600, ATR 42-600, Dash 8-300.
- Villa Air: ATR 72-500/600.
- Manta: ATR 72-600.

**Validation against MBS 2024 movements.** Ratio of estimated scheduled movements to MBS movements: DRV 0.87, FVM 1.09, KDM 0.80, LMV 0.91, HDK 1.16, DDD 0.78.
- Higher ratios: IFU, RUL, TMF, KDO, FND and FMT come out 2.4–5×. This is consistent with Maldivian network growth in 2025–26 and the via double-crediting.
- Lower ratios: GAN 0.12 and HAQ 0.41, because MBS includes international, charter and (at GAN) TMA seaplane movements.
- MUM and NMF have no 2024 MBS data. The MBS MLE figure (695k) is clearly not aircraft movements.

## 5. Seaplanes

- **Operators:**
  - TMA (Trans Maldivian Airways): about 60+ DHC-6 floatplanes. Hubs are the Velana waterdrome (Noovilu terminal) and Gan.
  - Maldivian Seaplane: 11 resorts listed on Wikipedia (Kihavah, Voavah, Hirundhoo, Vakkaru, Doores, Kandima, Maagau, Niyama, Robinson Noonu, Kudafushi, Maalifushi), plus the inhabited islands Kamadhoo, Fulhadhoo and Velidhoo.
  - Manta Air: shifting to seaplane-only. Soneva Fushi, Dhigufaru, Nika, Kihavah, Kandima, Niyama and Riu (historical).
- **Coverage:** `seaplane_destinations.csv` gives 90 resorts with a named seaplane operator (83 matched to MBS, 7 TMA-only new resorts). Another 53 are reached by speedboat (Kaafu, or ≤45 km), and 44 have an unconfirmed mode (domestic flight plus speedboat, or seaplane).
- **Typical seaplane time from Velana:** estimated as `8 + km/4.5` (Twin Otter at about 270 km/h plus taxi). This is calibrated to TMA's own "20–60 min" range and guide figures: Ari 20–30, Baa 30–35, Haa Alifu about 70. Median by atoll for operator-listed resorts:

| Atoll | K | V | AA | ADh | B | F | M | Lh | R | Dh | N | Sh | Th | L |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| median min | 17 | 19 | 21 | 28 | 35 | 35 | 37 | 37 | 43 | 43 | 49 | 58 | 66 | 66 |

- Resorts more than 350 km away (GA, GDh, Addu) are left without a time; they are reached by domestic flight, and TMA's Gan base serves Addu and Huvadhu.
- Seaplanes fly in **daylight only**, on demand, and carry resort guests only. Treat them as a tourism layer, not public transport for residents.

## 6. Airport catchments (qualitative and rule-based)

`airport_catchment.csv` assigns each of the 191 inhabited islands (pop 2022) to a **practical airport** with these rules:
- AA, V, K, F and northern ADh go to MLE, reached by ferry or speedboat. There is no airport in those atolls; Mathiveri, Magoodhoo and Nilandhoo F are planned.
- Otherwise an island goes to its same-atoll airport, if that is no more than 1.3 × nearest + 5 km away.
- Otherwise it goes to the nearest airport.

Highlights by airport:
- **GAN:** all of Addu City (Hithadhoo, Maradhoo, Feydhoo, Meedhoo, Hulhudhoo) by link road or causeway.
- **KDO:** Laamu via the link road (Fonadhoo, Gan, Maandhoo, Maavah, Isdhoo, Kalaidhoo).
- **HDK:** Kulhudhuffushi, which is also the hub for northern Sh islands.
- **HAQ / HRF:** they split Haa Alifu.
- **IFU:** all of Raa (Ungoofaaru, Dhuvaafaru, Alifushi).
- **DRV:** all of Baa (Eydhafushi, Thulhaadhoo, Kendhoo, Goidhoo, Fulhadhoo).
- **NMF:** all of Noonu.
- **LMV:** Naifaru, Hinnavaru, Kurendhoo.
- **FND:** most of Shaviyani.
- **MUM:** Meemu.
- **DDD:** Dhaalu.
- **TMF:** all of Thaa.
- **KDM / RUL / FMT:** they share GDh (Thinadhoo and Madaveli go to KDM).
- **GKK:** Villingili GA and its neighbours.
- **VAM:** southern ADh (Maamigili, Fenfushi, Dhigurah, Dhangethi).
- **FVM:** single-island Fuvahmulah.

Distances are straight-line; there is no sea-route or ferry timetable yet. Join these with the sea layer (team-kandu RTL/MTCC ferries) for the access legs.

## 7. Gaps and caveats

1. **No full weekly timetable.** Frequencies are extrapolated from 2 October days and 2 July days. Fix: run `air_poll_fis.sh` for at least 7 days. The live API is open and covers all domestic airlines at MLE.
2. **Outstation-only flights are invisible.** Flights that never touch MLE (for example GAN–GKK–KDM shuttles) only appear when part of an MLE rotation. Inter-outstation frequencies are therefore lower bounds.
3. **Manta Air is in transition (Sept 2026).** Domestic ATR flights on MLE–DDD and DRV have ceased; Maldivian took over DDD. Its rows are kept with `status=ceased`.
4. **Villa Air:** only MLE–VAM is operated, 2×/day. DRV is "resuming soon" (unconfirmed).
5. **Runway and opening conflicts:** Gan runway, Maafaru runway (2200 vs 2850 m), Muli runway (1200 vs 1500 m), FVM ICAO code. Fuvahmulah's "2002" opening date on Wikipedia is wrong; it opened in Nov 2011.
6. **Seaplane operators are partial.** The TMA list comes from its 2026 website. Maldivian and Manta lists come from Wikipedia and news and may be dated. Resort coordinates are missing for about 63 rows (not in the gazetteer, or failed a distance cross-check against MBS).
7. **The MACL dataset is international-only and anonymised.** It is not usable for domestic edges.
8. **International spokes from regional airports** (GAN–CMB SriLankan; HAQ, NMF, VAM and DDD intl-capable) are not in the domestic edge list.
