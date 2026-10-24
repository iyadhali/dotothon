# 18. Data gaps register: Island Access Atlas

Compiled 24 October 2026. Audience: datathon judges, and the follow-on development work with MBS (Maldives Bureau of Statistics) and the transport, health and education agencies.

Scope: every data gap that limits what the Atlas can claim about multi-modal travel time and cost from inhabited islands to health and education services. Each gap states what is missing, the evidence (counts computed from the prepared files), the effect on results, what the project already does about it, and who could close it.

## How to read this register

- **Computed** figures were recomputed on 24 Oct 2026 from `web/public/data/multimodal.json` (200 islands, 191 origins, 163 stops, 132 timetabled ferry trips, 154 observed-boat links, 62 air services, 199 access edges, 945 facilities, 48 categories), `web/public/data/fares.json` and `web/public/data/extras/island_access.json` (13,752 rows: 191 origins x 12 categories x departures 06:00/08:00/14:00 x estimated air off/on). Where a figure comes from a note it is cited by path.
- **Population denominator:** 447,420 residents on 191 inhabited administrative islands (Census 2022). Greater Malé (Malé, Vilin'gili, Hulhumalé) is 209,707 of those (46.9%), and the facility is on the island, so those residents add a trivial zero-minute result. **Outside Greater Malé there are 237,713 residents (53.1%).** Where it matters, both are shown. "Outside Greater Malé" here means every origin whose atoll code is not `MLE`; it therefore includes Hulhulé (802 residents), and can differ by about 1 percentage point from the "atoll residents" figures in `VALIDATION.md`.
- **Severity** is the project's judgement of how much the gap can move a headline number: **H** (can move a headline by 5 points or more, or blocks a claim), **M** (moves sub-groups or specific services), **L** (bounded or cosmetic).
- Direction: "optimistic" means the model overstates access; "pessimistic" means it understates it.

## 0. Summary

| # | Gap | Sev. | Direction | Size of effect |
|---|---|---|---|---|
| T1 | RTL is a single-day snapshot (Saturday 10 Oct 2026) with no calendar | H | unknown, mostly optimistic | 102 of 132 timetabled trips (77.3%) carry no running days; MTCC trips that do run 0 trips on Friday and 19 to 21 per day Sat to Thu |
| T2 | Zone 3 and Malé links only from a 2023 MTCC timetable | H | unknown | 44 islands / 52,783 residents (outside Greater Malé) have MTCC but no RTL stop; 12 islands / 12,022 depend on MTCC alone |
| T5 | Observed FollowMe boats stand in for timetables | H | optimistic | Hospital access 95.6% at 06:00 vs 81.3% at 08:00 vs 73.6% at 14:00. Switching the layer off removes 4.4 points (19,585 residents) |
| T6 | Air frequencies are estimates from 4 days of boards | M | optimistic (+15.9% departures) | Air adds +10.4 points for MRI at 08:00 and +8.1 for regional/tertiary hospital at 06:00 |
| D3 | No referral or patient-flow O-D, no observed demand | H | not applicable | Blocks demand weighting, 2SFCA and cost-benefit |
| F3 | No capacity, hours or appointments | H | optimistic | "Reachable" means reachable island, not served patient |
| P1 | Origin universe excludes 67,712 people (13.1% of the republic) | M | pessimistic for coverage of the republic | 66,313 non-admin plus 1,399 harbour residents |
| C1 | No resident speedboat tariff; air fares 91.7% estimated | M | unknown | Boat legs of observed links priced at RTL tariff |
| V1 | Only weak external validation | H | not applicable | Evacuations rho = +0.28, p = 0.25 (n = 19) |

Everything below is the evidence for these rows and for the smaller gaps behind them.

---

## 1. Transport supply

### T1. RTL timetable is one day, with no service calendar

- **Missing:** weekday, Friday, holiday and seasonal calendar; validity dates; per-trip direction pairing.
- **Evidence:**
  - `data/team-kandu/rtl_trips.csv` is the 2026-10-10 scrape (a Saturday; `fetched_at` 2026-10-10). Its 102 trips on 49 routes (390 stop-times) are 77.3% of the 132 timetabled trips in `multimodal.json`; none has a `days` field. `meta.serviceDayAssumption`: "All RTL trips are treated as one reference-day timetable".
  - Trips per route: 6 routes have 1 trip, 39 have 2, 3 have 4, 1 has 6. RTL records one time per stop, so arrival equals departure at every one of the 102 trips (dwell is zero by construction).
  - The 30 MTCC trips that do carry days show how much a calendar matters: 0 of 30 run on Friday; trips running per day are Sat 21, Sun 20, Mon 19, Tue 21, Wed 20, Thu 19. Only 14 of 30 (46.7%) run all six days Sat to Thu; the other 16 run on 1 to 3 days.
  - The router repeats the reference day on the next day regardless of days (`research/18_current_implementation_critical_review.md` finding 3: Rasdhoo to Thoddoo is offered on a Sunday although the stored calendar says Saturday and Tuesday).
- **Effect:** the figures are "what a Saturday looks like", not a weekly average. If RTL runs fewer trips on Friday, hospital access that day is lower than the 81.3% quoted (no number is possible without the calendar). Departure time is already a larger driver than anything else we can measure: hospital reachable at 06:00 / 08:00 / 14:00 is 95.6% / 81.3% / 73.6% of all residents and 91.6% / 64.9% / 50.3% outside Greater Malé (air on, computed from `island_access.json`).
- **Mitigation:** the day-of-week picker uses published `days` for MTCC trips; RTL, air and observed boats are flagged "treated as daily"; headline text says "reference day"; quote 08:00 figures.
- **Closes it:** RTL/MTCC GTFS-style export with `calendar.txt` and `calendar_dates.txt` (see section 7, ask 1). `research/02_data_profile_hdx_kandu.md` estimates the RTL files are about 80% of a GTFS feed already.

### T2. Zone 3 and Malé links exist only as a 2023 timetable

- **Missing:** current RTL (or MTCC) timetable for Kaafu, Alif Alif, Alif Dhaalu, Vaavu and Meemu; any Malé-bound ferry from RTL.
- **Evidence:**
  - `rtl_stops.csv` has no stops in K, AA, ADh, V or M (Zone 3). Routes: Zones 1, 2, 4, 5, 6 only (`research/02`).
  - Gap filled from the MTCC all-atolls PDF dated 16 Jul 2023, effective 29 Apr 2023, recovered from the Wayback Machine because mtcc.mv returned 403 (`research/15_ferry_timetable_gaps.md`). It is 3.5 years older than the reference day. In the network: 30 MTCC trips on 15 routes (28 Zone 3, 2 Zone 2), 46 stop ids. Three stop rows are low confidence (102 Ihavandhoo arrival illegible; Kandoodhoo/Buruni days assumed); 406/407 day groups assumed to both run.
  - Dependence: 44 origin islands (52,783 residents, excluding Greater Malé) have an MTCC stop but no RTL stop; 12 of them (12,022) have no observed-boat link either, so MTCC is the only surface evidence.
  - Before the MTCC and observed layers were added, 67 of 191 origins (63,749 residents) had no transport data (`VALIDATION.md` s3); after, 6 islands (4,335 residents) remain.
  - Outside the files entirely: Malé-Villingili and Hulhumalé city ferries (separate MTCC network), Addu intra-atoll and Fuvahmulah services (`research/15`). The Malé-Vilimalé ferry is modelled as 7 min every 15 min, 06:00 to 22:00, confidence "estimated" (`meta.assumptions.villemale_ferry`).
- **Effect:** direction unknown. The 2023 PDF probably misses later changes. The Aug 2025 observed data show much denser traffic than the PDF lists on the Kaafu corridors (for example Maafushi to Malé about 8 trips a day each way, `research/14`), which would make the timetable pessimistic there; but observed boats include private traffic (T5).
- **Mitigation:** evidence layers are switchable (RTL 2026, MTCC 2023, observed boats, estimated flights); MTCC applies only where RTL has no stop; each journey row shows the evidence it used; tests cover the calendar.
- **Closes it:** current RTL Zone 3 and MTCC timetable with calendar (ask 1); route map to join MTCC route numbers (101 to 607) with RTL codes (Z2R3 and so on), which are not mapped one-to-one today.

### T3. 61 unscheduled RTL routes

- **Missing:** times for routes that have a stop sequence only.
- **Evidence:** `rtl_unscheduled.csv` has 61 rows (Zone 1: 34, Zone 2: 19, Zones 4 to 6: 8); one is an `ERROR` duplicate of S2C5, leaving 60 usable. 38 of the 60 (63.3%) match a single MTCC trip by island set (MTCC times are proxies, not the RTL service); 22 (36.7%) do not match: old or variant codes, spelling (Bileyfahi, Bileffahi), Z2R5 Manadhoo-Kudafari, Z6 Fuvahmulah-Vaadhoo, Z5R2 Dhevvadhoo-Villingili (`research/15`). 32 of 149 RTL stops (21.5%) are marked `scheduled = no`, including all 7 Lhaviyani stops (`research/02`). In the prepared network every one of the 163 stops (117 RTL + 46 MTCC) is scheduled: the 32 unscheduled RTL stops are absent as stops.
- **Effect:** pessimistic where nothing else serves the island (some of these islands are rescued by observed boats), neutral elsewhere. Not quantifiable in people without the unscheduled routes' timings.
- **Mitigation:** none beyond the MTCC layer (30 trips). The 38 matched routes have only MTCC proxy times; the other 22 have no times at all.
- **Closes it:** RTL times for the 60 routes, or confirmation that they are inactive.

### T4. One-direction trip records

- **Missing:** the return leg of some recorded trips.
- **Evidence (computed):** 6 of 49 RTL routes (12.2%) have no trip in the reverse direction; 19 of 615 directed island pairs (3.1%) lack a reverse pair. 7 islands (7,445 residents) have no bidirectional RTL pair: Maalhos (Baa, 572), Dharavandhoo (Baa, 997), and Raa's Maduvvari (1,760), Iguraidhoo (1,278), Fainu (423), Meedhoo (1,872) and Kinolhas (543). Example: the Baa pilot corridor `Z2R18` is one trip Dharavandhoo to Maalhos to Eydhafushi at 15:05; Maalhos has one departure and one arrival and no return, and Dharavandhoo is reached from no one. Disabling Z2R18 removes only its 572 residents (Maalhos) from the hospital figure (327,354 to 326,782 in the earlier network, `VALIDATION.md` s3.1).
- **Effect:** one-way access to a facility is unchanged; the same-day return and round-trip cost in the island access report are wrong by the missing leg (the panel falls back to a night away at default MVR 950). Whether these are real loop services or scrape gaps cannot be told from the file; `meta.assumptions.rtl_reference_day` says "missing journeys do not prove absence of transport".
- **Mitigation:** direction and full stop order are preserved by the router; return trips are searched; unknown cost shown as "+".
- **Closes it:** the RTL operator's full-direction trip table for the seven islands (ask 1).

### T5. Observed FollowMe boats used as service

- **Missing:** vessel type, operator, tariff, seat capacity, passenger eligibility, timetable.
- **Evidence:**
  - `data/processed/followme/observed_sea_links.csv` -> 154 links in `multimodal.json` (`VALIDATION.md` s5a and the review quote 162; the prepared artefact has 154, see M2). Source: FollowMe August 2025, 110,074 inferred trips from 1,655 trackers, 17.46 M GPS fixes; Aug is tourist high season. The tracker feed has no vessel type; 669 of 1,776 devices are fast (at least 18 kn) and make 76k of the 110k trips (69%) (`research/04`).
  - Filters (`research/14`): at least 0.5 trips/day, 10 active days, 2 vessels, no vessel over 80% of trips, detour at most 1.6. They reduce but do not remove private shuttles, resort and guesthouse transfers and fishing boats.
  - Departures are generated, not observed: 273 per day across 154 links (mean 1.77; 105 links, 68.2%, have one departure a day), spread evenly over the observed hours (median window 7.2 h; 67 of 273 generated departures, 24.5%, before 08:00). Median block time 24 min.
  - Coverage: links touch 72 origin islands; 20 non-Greater-Malé islands (15,210 residents) depend on observed boats alone (no RTL, no MTCC). 58 of the 67 islands that had no transport data (58,064 of 63,749 people, 91%) got at least one link; Haa Alifu 0 of 4 and Gaafu Alifu 2 of 3 stay weak.
  - Durations versus RTL (124 island pairs in both): observed trips are a median 0.65 of RTL timetable time (p10 0.37, p90 1.00), rank correlation 0.80; the ratio is 0.55 on 0 to 5 km hops, 0.98 at 40 km or more.
- **Effect: optimistic, and time-of-day dependent.** Even spacing puts boats at 06:00-07:59 that may not exist, which is why 06:00 gives 95.6% for the hospital and 08:00 gives 81.3% (`VALIDATION.md` s5a). Layer sensitivity at 08:00, hospital tier 1 to 3: 363,648 reachable (81.28%) with the layer; 344,063 (76.90%) with observed boats off, a drop of 19,585 residents or 4.38 points; 339,424 (75.86%) with observed boats and estimated air off (`research/18_current_implementation_critical_review.md`). Timetable-only before augmentation: 327,354 (73.2%). Ferry-class vessels would be slower than the observed medians (ratio 0.65), so the observed durations are speedboat-class and optimistic for a public ferry user.
- **Mitigation:** the layer is an independent switch (`observed-boats`), labelled "any tracked boat (public, private, fishing)", priced at the RTL tariff and flagged estimated; the 08:00 figure is the quoted one.
- **Closes it:** operator timetables (RTL, MTCC, island-council boats, licensed speedboat operators) for the 154 links, or a vessel-class label from FollowMe (ask 3).

### T6. Domestic air: estimated frequencies from four days of boards

- **Missing:** an observed weekly timetable, seat capacity, load factors, bookable availability.
- **Evidence:**
  - Frequencies come from the Velana FIS departure/arrival board on four days: two days in July and two in October (Thu 15 and Sat 24 Oct 2026), by `research/07_air_network.md`. Both October days start about 08:00, so flights between 05:00 and 07:59 are missing and routes may be undercounted by about 1 flight a day. Outstation-to-outstation flights that never touch Malé are invisible; "via" ordering is inconsistent between boards, so edges are undirected.
  - Network: 62 directed services on 31 airport pairs (Maldivian 60, Villa Air 2), all `estimated_frequency`, all spread evenly across 06:00-18:00. Estimated weekly total 616; generated departures `max(1, round(weekly/7))` per day give 714 a week, 15.9% more. For the 24 services (38.7%) estimated at fewer than 7 a week (82 a week in total) the generator produces 168, 2.05 times as many; for example FND-HDK at 2 a week becomes daily.
  - Manta Air left domestic ATR flying in Sep 2026; MLE-DDD and DRV rows are `ceased` and excluded, as are five July-only routes (FVM-GKK, FVM-KDM, FVM-KDO, GAN-KDM, KDM-MUM) (`meta.excludedAirRoutes`).
  - The 4-day estimate scores 0.78 to 1.16 of MBS 2024 movements for DRV, FVM, KDM, LMV, HDK, DDD, but 2.4x to 5x for IFU, RUL, TMF, KDO, FND and FMT (network growth plus double-crediting) and 0.12 for GAN (`research/07`).
- **Effect: optimistic in frequency, mixed in timing.** Air matters most for services held by few facilities: at 08:00 (all residents, air off to on) hospital 80.3% to 81.3%; regional/tertiary hospital 73.2% to 79.3%; CT 72.5% to 79.3%; MRI 68.9% to 79.3%; dialysis 83.1% to 83.7%. At 06:00 the regional/tertiary gain is 84.5% to 92.6% (+8.1 points). Outside Greater Malé at 08:00 the regional/tertiary figure is 49.6% air off and 61.1% air on (11.5 points). Air fares carry 91.7% estimated values (C2).
- **Mitigation:** air is estimated-labelled and toggleable; verified vs estimated reachable counts are reported separately (for example 320,799 verified / 6,555 estimated at 08:00 in the pre-augmentation network).
- **Closes it:** Maldivian/Villa schedules, or 7 or more days of the open FIS API polled with `scripts/air_poll_fis.sh` (the script exists; the poll was not completed); MACL domestic data (ask 5).

### T7. No speedboat or launch schedules or fares

- **Evidence:** the MTCC PDF and the RTL files list public ferries only. Scheduled speedboat prices are six thin USD tourist quotes (median USD 30, about MVR 460); resident speedboat charter has two "up to" quotes (MVR 438 + 48.8 per km); dhoni charter has none; a Thinadhoo council launch tariff (IUL 415/415/2026/69) could not be read (garbled Dhivehi) (`research/13_sea_land_fares.md`). Airport speedboat transfers at Maarehaa and similar are two assumed edges at 25 km/h + 10 min (`accessEdges`, confidence "assumption").
- **Effect:** the fast vessels that FollowMe sees (69% of trips) and that residents plausibly use, especially in Kaafu, Vaavu and Meemu, are in the model only as observed links at RTL prices. Fares for speedboat legs are unknown (cost shown as "+"); times are likely to be optimistic for a resident without a charter.
- **Closes it:** licensed passenger-speedboat register with routes, timetables and tariffs (MoTCA / Transport Authority; ask 3).

### T8. Seaplanes excluded

- **Evidence:** by design (`meta.assumptions.seaplane_excluded`). 187 seaplane-destination rows (180 MBS resorts + 7 TMA); 90 resorts have a named operator (`research/07`). Maldivian Seaplane also serves inhabited islands at local fares (Thoddoo MVR 799, Velidhoo 999; Kamadhoo and Fulhadhoo listed). Those four islands hold 4,649 residents (Thoddoo 1,924, Velidhoo 1,832, Kamadhoo 552, Fulhadhoo 341).
- **Effect:** small and pessimistic: at most 1.0% of the origin universe, and Thoddoo has MTCC and observed links in any case. Time-critical care is not affected because seaplanes fly daylight only.
- **Closes it:** Maldivian seaplane schedule and resident-fare sheet for the four islands.

### T9. No road network inside islands

- **Evidence:** access edges: 199, of which walk 184 (181 `estimated_access`, 3 `assumption`), road 13 (Addu, Laamu, Sinamalé, Hulhulé-Hulhumalé at 40 km/h plus 3 min, centroid-derived distances with a 1.15 detour) and speedboat 2. Walk is 4.5 km/h with a 1.25 detour; local transport 25 km/h plus 5 min beyond 1.5 km. Facilities are island-level points, so every facility on an island is at the same place. OSM has drivable roads on 186 of 191 inhabited islands (Malé about 61 km, Hulhumalé about 83) but they are not used for routing. Avas ride times are routing-engine estimates at about 38.7 km/h with no peak effect (`research/04`).
- **Effect:** on most islands (under 2 km across) the effect is a few minutes. It is unbounded in Malé, Hulhumalé, Addu, Fuvahmulah and Kulhudhuffushi, where the "0 minutes" for a facility on the island hides the walk, wait and congestion. Optimistic.
- **Closes it:** facility building coordinates (F1) plus OSM roads for the cities; peak-hour speeds for Greater Malé from Avas (ask 8).

### T10. No sea-ambulance or medevac network

- **Evidence:** no dataset. News says MNDF runs sea ambulance, MoH plans 13 sea ambulances and Japan funded one (USD 3.6 M); MEMS is licensed in Malé (`research/05_healthcare_data.md` s2). Aasandha recorded 4,426 emergency evacuations and 15,535 patients sent abroad in 2024; estimated cost per air medevac about MVR 88k and per sea medevac about MVR 5.9k, both low confidence (`research/12`). The router fare class "approved emergency" sets MVR 0 but still routes on public timetables.
- **Effect:** for urgent conditions the actual access path (air ambulance, sea ambulance, charter) is outside the model, so emergency access is **pessimistic** on time (public timetable is slower than an ambulance) and **unmeasured** on capacity. For routine care the model is an optimistic upper bound. The headline should not be read as emergency readiness.
- **Closes it:** MNDF / NDMA / MEMS ambulance dispatch logs and asset register (ask 6).

---

## 2. Facilities

### F1. Island-level locations only

- **Evidence:** all 945 facilities have `precision = "island"`. No coordinates in MoH HEMS (601 establishments), MoE directory (220 schools) or higher-education register (203 rows) (`data/external/README.md` s4). OSM coverage of listed facilities on inhabited islands: schools 70 of 191, hospitals/clinics/doctors 55 of 191.
- **Effect:** within-island travel is a single assumed value. Neutral for small islands, optimistic in large ones (T9).
- **Closes it:** MoH and MoE facility coordinates (ask 4); OSM can place facilities inside Greater Malé.

### F2. Tiers from 2020 MHS; specialist and diagnostic claims of mixed confidence

- **Evidence:**
  - Tier source: `public_health_facility_master.csv` (2020 MHS tier mapped to the 2026 HEMS licence level). `health_hospital` = 24 facilities on 22 islands; `health_regional_tertiary` = 10 on 8 islands; 189 base health facilities on 186 islands (164 health centres, 13 atoll hospitals, 6 regional, 3 tertiary, others). 11 health rows are marked `reviewed = false`.
  - Intervention layer: 1,405 evidence rows read, 1,386 used; 444 facilities, 1,279 evidence items on 108 islands in 42 categories. Confidence: high 732 (57.2%), medium 385 (30.1%), low 162 (12.7%). Source dates: 188 items (14.7%) are dated 2022 or earlier and 11 have no date; the 895 items dated 2026 are probably retrieval dates rather than service dates.
  - Low-confidence shares by category (from `categories[].confidenceNote`): endoscopy 6 of 10 low, ultrasound 29 of 68 (42.6%), visiting specialist 13 of 39 (33.3%), X-ray 16 of 56 (28.6%), PCR 10 of 36 (27.8%), developmental therapy 7 of 18.
  - Thin categories: 15 of 42 categories exist on 5 or fewer islands (MRI 5, hyperbaric 1, fertility 2, urology 2, and so on), so one wrong claim moves the result.
  - Tier-inferred rows (HHFA 2022/23 aggregate rates, not facility-confirmed): lab_advanced and lab_basic medium, X-ray and ultrasound low (`research/09b_lab_diagnostic_services.md`). 54 Greater Malé private rows in the specialist table have assumed or inferred locations (`research/09c_specialist_services.md`); about 25 diagnostic rows likewise.
  - Source completeness: lab coverage trend (about 90 islands with a lab in Oct 2019, 76 with none in late 2023; Jan 2026 pledge of a lab on every island by end-2026). Blank cells in the research matrices mean "no evidence found", not proof of absence.
- **Effect:** the high-confidence core of 732 claims is robust. Service-specific access numbers (CT, MRI, dialysis, oncology) depend on 7 to 33 claims each and mix confidences. Direction is mixed: claims may be stale (optimistic) and the absence of evidence may hide a real service (pessimistic).
- **Mitigation:** every claim keeps confidence, source and date and is shown in the evidence panel; resort/guest-only rows (12) and unresolved islands (7) excluded; not inferred from tier.
- **Closes it:** the MoH facility service registry (services by facility with date) and the Health Facility Assessment microdata (ask 4).

### F3. No capacity, hours or appointment availability

- **Evidence:** no bed, specialist, ICU or maternity inventory after 2020 (`research/05` s3): 2,581 inpatient beds in 2020 (Malé 998, atolls 1,583), 1.6 to 11.0 beds per 1,000 across atolls, staff only to atoll level (2023, 11,955 staff). The HEMS professional count is 0 for almost all government facilities. IGMH 2025: 537 beds, occupancy 45.9%. Education: enrolment by island only (MoE 2024, 98,845 students, 187 islands plus 21 atoll totals), school directory 220 government schools with students and teachers but no grade range; campus-level higher-education enrolment not published (`research/06`). No facility opening hours or appointment slots anywhere.
- **Effect:** optimistic. "Reachable" is the nearest listed island, not a patient who is seen. A health centre and a regional hospital count the same in `health_any`. Cannot rank sites by capacity; the "Recommended sites" story is a greedy population-coverage screen (`research/18_current_implementation_critical_review.md`).
- **Closes it:** facility-level beds and staff by cadre (MoH), campus enrolment (MoE/MoHE/MQA), appointment-slot and roster extracts for one pilot pathway (ask 4 and 10).

### F4. Higher-education register partly without islands

- **Evidence:** `data/external/higher-ed-campuses/higher_ed_campuses_by_island.csv`: 203 rows; 99 have an island, 104 (51.2%) have none (mostly institutes, most likely Malé); 5 inferred locations flagged in notes. The network holds 81 higher-education facilities on 40 islands, of which 22 are in Greater Malé. 32 education rows are `reviewed = false`. Maldives Polytechnic and TVET centre locations and capacity were not found (`research/06`).
- **Effect:** probably small for the headline (unplaced rows are mostly Malé-based and Malé is already served), but the share of residents outside Malé within reach of any post-secondary provider is unmeasured for institutes. Optimistic if unplaced institutes are in fact only in Malé and we count none, pessimistic otherwise.
- **Closes it:** MoE/MoHE register with campus addresses; TVET Authority centre list (ask 4).

### F5. Education facility mapping and denominators

- **Evidence:** 312 of 483 education rows mapped (64.6%); base exclusions 120 rows (104 blank, 12 aggregate, 4 no-match) plus 50 zero-category rows (36 preschool, 14 Quran centre). Grade 11 to 12: 44 of 184 atoll islands teach those grades; the 40 islands carrying them in the network include Malé's wards. 179 of 200 islands have an education supply row (`island_profile`). School grade ranges are from 2022-23 and predate the 2023-24 "Atoll School" consolidations (`research/06`). The education figures use all residents as the denominator (Grade 11-12: 89.7% at 08:00), not the 16 to 19 cohort (Census ED17/ED18 have it by island but are not used).
- **Effect:** the education share counts everyone; the cohort share would differ by island (young-age structure varies). Direction unknown. The shortfall in grade ranges is a possible optimistic bias for consolidated schools.
- **Closes it:** current MoE school list with grade range per school and school-age population by island (Census ED17/ED18 already local, needs wiring).

### F6. Private facility placement assumptions

- **Evidence:** private and resort clinic names usually carry no island in HEMS; unresolved private specialist and diagnostic rows were assumed to be in Greater Malé at low confidence (54 specialist rows, about 25 diagnostic rows). The Aasandha empanelled list (763 local providers with island) was fuzzy-matched to HEMS names (`research/09c`). Private atoll polyclinics often list visiting rather than resident specialists.
- **Effect:** concentrates private capacity in Malé, which is correct for most but not all; pessimistic for the few misplaced atoll clinics. Not decision-critical for Greater Malé residents.
- **Closes it:** HEMS licence address field (MoH), or Aasandha empanelment list with island (ask 4, 7).

---

## 3. Population and demand

### P1. Origin universe is 447,420 of 515,132

- **Evidence:** 447,420 on 191 inhabited administrative islands; excluded 66,313 (non-administrative localities, mainly resort and industrial islands: resorts 52,210; industrial islands 12,656) and 1,399 harbour-area residents. 447,420 + 66,313 + 1,399 = 515,132. The excluded 67,712 are 13.1% of the republic. Resort workers and industrial-island workers have no island-level population (census aggregates only). The origin set is Census 2022 (place of enumeration) and the reference day is October 2026, so four years of growth and the Malé enumeration inflation are not adjusted. `observations` table 3.3 has registered population for 2023 to 2025 but is not used.
- **Effect:** coverage percentages are for residents of administrative islands. Anyone who works on a resort or industrial island (the non-administrative localities are 12.9% of the republic's population) is outside the denominator but within the health system. Neutral to small on percentages; large on absolute headcounts. Population is total residents (Maldivian and foreign); the share of migrant workers who use public ferries or Aasandha is unknown.
- **Mitigation:** exclusions are stated in `meta.population.note`, `VALIDATION.md` and `data/external/README.md`.
- **Closes it:** MBS Census 2022 island-by-nationality tables (P5, MG12 already local, wiring needed) and a staff-headcount list for resorts and industrial islands from Ministry of Tourism / MIRA (ask 9).

### P2. Resort and industrial islands

- **Evidence:** 165 operating resorts plus 7 closed or planned (status in the master layer), 2 OSM-hinted industrial islands; no official industrial-island list (`data/external/README.md` s7). Staff clinics, seaplane and speedboat transfers on those islands are out of scope.
- **Effect:** none on residents' access; removes a sizeable demand segment.

### D3. No observed demand

- **Evidence:** MTCC passenger counts are randomly generated per the workbook's own README (all `paid_pax`, `foc_pax`, `total_pax`, `passengers` values); only route names and codes are real, and only 3 of 8 MTCC ferry codes match RTL directly (H1, S1C1, Z5R5) (`research/04`). MACL covers international turnarounds at Velana only, with anonymised carrier and route codes and no seat capacity. FollowMe trips are boat movements, not passengers. The synthetic dataset has a Friday dip of 39% that is an artefact of the generator (`research/13_data_opportunities_and_ml.md`).
- **Effect:** no queueing, seat availability, "is the boat full" or load factor; route importance weights cannot be set. 2SFCA, optimiser and cost-benefit were not built. Counts are not used.
- **Closes it:** RTL/MTCC real ticket counts by route and day, ferry and flight capacities (ask 2, 5).

### D4. No referral or patient-flow O-D

- **Evidence:** only Aasandha atoll-level evacuation counts (2023: 4,079; 2024: 4,426) and Aasandha spend by atoll and island exist; no origin-destination matrix of patient moves (`research/05` s3, item 3). Island Aasandha spend is booked where care is delivered (billing-location effect), so it cannot stand in for origin demand (`research/16_external_validation.md`).
- **Effect:** the model has no revealed preference. Nearest-facility is assumed; actual referral patterns (to IGMH, ADK, regional hospitals, abroad: 15,535 patients in 2024) may differ. Affects every service-specific claim.
- **Closes it:** Aasandha or HEMS referral extract with origin island, destination facility and mode, even for one year (ask 2). This is the single most valuable data request.

---

## 4. Costs

### C1. Sea and road fares

- **Evidence (`data/external/fares/sea_land_fares_model.json`, `web/public/data/fares.json`):**
  - RTL ferry fare = 33.82 + 1.794 x great-circle km, fitted to the gazette step tariff (n = 1,837 directed pairs, r2 = 0.872; 20 gazette notices 2022-06 to 2026-04). The true tariff is a step function (MVR 35, 50, 65, 70, 100, 125 by distance band); the intercept overstates short hops (for example 42.8 vs the MVR 35 step at 5 km, +22%); return is about 1.8 times one-way. About 35% of gazette rows (1,474 of 4,189) used a fuzzy island-name match. Inter-zone Highway Link fares are flat (median 150, range 130 to 170, r2 = 0.17).
  - The same RTL regression is applied to MTCC services and to observed-boat legs: Fulidhoo to Maafushi shows MVR 88 labelled "sourced" while the local MTCC source lists MVR 53 for that pair (finding 4 in `research/18_current_implementation_critical_review.md`). Concessions: Greater Malé ferries and buses are free for 65+ and students; atoll RTL is confirmed free only for the elderly and disabled; regular-treatment patient exemption is proposed, not in force.
  - No 2026 re-tariff found. A 2026 oil shock (petrol and diesel reported more than doubled) is unmodelled.
  - No resident speedboat tariff (T7); dhoni charter none; sea ambulance none (patient pays MVR 0 by policy).
  - Taxi: Greater Malé regulated tariff (fit MVR 59.9 + 3.673 per km, confidence estimated); regulated fares are "routinely exceeded in practice".
- **Effect:** cash cost for a typical one-way atoll ferry is MVR 35 to 125, so the short-hop intercept error is modest (about +22% at 5 km). The MTCC fare is overstated by 66% in the example above (88 vs 53). Unknown fares appear as "+", they are not zero.
- **Closes it:** RTL tariff by route code (ask 7), MTCC current fare sheet, MoTCA speedboat tariffs.

### C2. Air fares

- **Evidence:** 36 airport-pair fares in `fares.json`: 33 labelled estimated regular fares (91.7%), 2 sourced, 1 derived from the lowest fare x 1.43. Promo fares are official only for 14 Malé routes (Maldivian press release, 14 Mar 2024); regular = 1.434 x promo (mean of 12 ratios); only LMV, MUM and FVM have observed regular fares. Short northern legs use a 2026 southern regional model and are low confidence. Local fares were frozen for about 3 years by presidential instruction. Promo buckets apply to selected flights and limited seats, so average fares paid are higher. Distance model for pairs without a fare: 1,348.25 + 0.77 per km (`fares.json.airModel`).
- **Effect:** a typical Malé trunk resident fare is MVR 1,400 to 1,900, so a +-10% error on a pair is MVR 140 to 190 per leg; the order of magnitude is right. Optimistic if a resident cannot get the regular price.
- **Closes it:** Maldivian/Villa resident fare circulars; Island Aviation revenue per passenger (ask 5).

### C3. Value of time

- **Evidence (`data/external/economics/value_of_time.json`):** non-work VoT = 0.3 x HIES 2019 mean monthly per-capita income / 173 h, inflated 2019 to 2026 by x1.1454: chained WDI CPI for 2020 to 2025 (x1.1014) plus an assumed 4% for 2026. Result MVR 7.47/h (atolls), 14.86 (Malé), 11.0 (national), "medium" confidence. Work VoT (national 84.5, atolls 61.6, Malé 108.4 per hour) is low-medium: income per earner proxies wage because the 2024-25 labour force survey has no earnings. The September 2026 ECPI release is listed as a source, but the uplift is not recomputed from it.
- **Effect:** the 4% 2026 assumption is a 3.8% shift in VoT (1.1454 against 1.1014). VoT is small next to cash fares: a 4 h ferry trip is worth about MVR 30 at the atoll rate against MVR 35 to 125 cash, so ranking by generalised cost is dominated by cash and lodging, not by time. A 2019 income base is 7 years old.
- **Closes it:** HIES 2025/26 or the latest household income and expenditure results (ask 9).

### C4. Lodging and meals

- **Evidence:** MVR 400 / 700 / 1,300 per night (low / typical / high) from aggregator USD snapshots; no MVR patient-lodging tariff found; 0 if staying with relatives; meals MVR 250 per day (low). Default night away MVR 950 = 700 + 250.
- **Effect:** when a same-day return is impossible, this one value dominates the household cost. The plausible range is MVR 650 (-32%) to 1,550 (+63%) per night against a default of 950; in the T4 islands every trip needing a night away inherits that uncertainty. MVR 950 is about 8 to 27 times a one-way atoll ferry fare of MVR 35 to 125.
- **Closes it:** patient hostel and guesthouse rates from Aasandha / NSPA patient-accommodation policy and island guesthouse registers (ask 9).

---

## 5. Validation

### V1. What was validated

| Check | Result | Source |
|---|---|---|
| Observed FollowMe trips vs RTL timetable duration (124 island pairs in both) | median observed / RTL = 0.65 (p10 0.37, p90 1.00); Pearson 0.74 raw, 0.80 on logs; within +-25% of RTL in 32% of pairs; observed shorter by more than half in 28%; median absolute difference 7.3 min | `research/14_followme_observed_links.md` |
| Estimated air movements vs MBS Yearbook 2024 | 0.78 to 1.16 for DRV, FVM, KDM, LMV, HDK, DDD; 2.4 to 5x for IFU, RUL, TMF, KDO, FND, FMT; 0.12 GAN | `research/07_air_network.md` |
| Router logic | 48 to 53 routing tests depending on the document (calendar, concession and evidence included); pipeline tests with 17 skipped without local CSVs; pilot table in `VALIDATION.md` s4 | `VALIDATION.md` |
| Atoll access vs Aasandha spend per person | rho = -0.60, p = 0.010 (regional/tertiary no-route share, n = 17); hospital minutes vs Aasandha -0.63, p = 0.022 (n = 13 well-covered atolls) | `research/16_external_validation.md` |
| Atoll Grade 11-12 minutes vs share of 16 to 19 year olds studying | rho = -0.74, p = 0.004 (n = 13 well-covered atolls); island level -0.52 (n = 95), but -0.21, p = 0.12 once islands with a school are excluded | `research/16` |
| Emergency evacuations vs hospital minutes | rho = +0.28, p = 0.25 (n = 19): right sign, not significant | `research/16` |

### V2. What cannot be validated yet

- **Timetables against operators:** no operator confirmation for any single RTL, MTCC or air trip beyond one amaldives.com cross-check of the Malé-Maafushi 309 timetable (matches the PDF exactly; `research/15`).
- **Observed boats as public service:** link existence is observed; passenger eligibility, price and schedule are not.
- **Access against revealed patient behaviour:** no referral O-D (D4). The island-level Aasandha correlation (rho -0.38, n = 114) vanishes once hospital islands are removed (rho +0.02, p = 0.81, n = 96), a billing-location effect; we do not claim island-level health validation.
- **Evacuations:** not predicted. Atoll data coverage confounds everything: the strongest coefficients with "% population with no data" (rho = -0.68 and -0.77) are modelling gaps and are not findings. About 150 tests were run without correction, and with n of 11 to 19 only coefficients with |rho| above about 0.45 to 0.55 reach p < 0.05.
- **Pipeline defect:** `scripts/validate_access_outcomes.py:182` reads index 10 of the island Aasandha workbook and labels it 2024, but the review found index 10 is 2023 and 2024 is index 11; `scripts/analysis/island_access_outcomes.py:169` calls a homoskedastic covariance HC0. The island-level Aasandha figures should be rerun before they are cited (`research/18_current_implementation_critical_review.md` finding 9).
- **Weekly pattern and seasonality:** one Saturday, plus August 2025 boats. No monsoon or sea-state reliability data; an unchanged assumption in every sea edge.
- **Mapbox basemap rendering and the QGIS export** were not visually verified (`VALIDATION.md`).
- **Sensitivity to 2023 data:** no test compares MTCC 2023 timetable results with a current one, because no current one exists.

### V3. Metadata drift (M2)

- Counts differ across documents: README and `VALIDATION.md` s2 quote 117 stops, 102 trips; `VALIDATION.md` s5a quotes 21 MTCC trips and 162 observed links; the prepared `multimodal.json` contains 163 stops, 132 timetabled trips (102 RTL, 30 MTCC) and 154 observed links. The QGIS export still reflects the older 153 access edges and 102 ferry routes. See `BACKLOG.md` item 3 (shared build id and manifest-derived counts).

---

## 6. Gaps ranked by effect on the headline

| Rank | Gap | What moves | Evidence for size |
|---|---|---|---|
| 1 | T5 observed boats and T1 reference-day timing | The hospital headline between 73.6% (14:00) and 95.6% (06:00), and 4.4 points by layer | `island_access.json`, review sensitivity |
| 2 | D4/D3 no referral O-D, no observed demand | Cannot weight, rank or validate; blocks cost-benefit | 15,535 patients abroad and 4,426 evacuations are unlocated |
| 3 | F3 no capacity, hours or appointments | "Reachable" becomes "served" only with it | 24 hospital facilities on 22 islands treated as identical |
| 4 | T2 Zone 3 / Malé links (2023 PDF) | 52,783 residents on islands with MTCC but no RTL; 12,022 on MTCC alone | `multimodal.json` |
| 5 | T6 estimated air | +8.1 points regional/tertiary at 06:00; +10.4 MRI at 08:00 | `island_access.json` |
| 6 | P1 origin universe | 67,712 people (13.1%) outside the denominator | `meta.population` |
| 7 | F2 service-claim confidence | 162 low plus 385 medium of 1,279 claims | `categories[].confidenceNote` |
| 8 | C1/C4 fare and lodging uncertainty | Night-away cost -32% to +63%; MTCC fare up to 66% off | `fares.json`, `value_of_time.json` |
| 9 | T7/T10 speedboats and ambulance | Unpriced fast mode; emergency path not modelled | `research/13`, `research/05` |
| 10 | T9/F1 island-level location | Constant intra-island time | `accessEdges` |

---

## 6a. Gaps reduced in the app with data already in hand (24 Oct, evening)

| Gap | Change | Effect |
|---|---|---|
| T6 air inflation | Air services with fewer than 7 estimated weekly flights fly only on that many weekdays (`days`), using the router's weekday calendar. | Generated departures go from +15.9% to +1.9% over the estimated weekly frequency (24 of 62 services). |
| T5 observed boats | Departures are placed at the busiest hours seen in the FollowMe departure histogram, not spread evenly. Links with under 0.5 weekend trips a day do not run Fri/Sat. | Fewer early-morning boats that were never observed; 06:00 results become less optimistic. |
| T4 one-direction trips | RTL trips with no trip back between the same two islands get an inferred return (reverse stops, 30-min turnaround). Evidence layer "Inferred return", switchable off in the Data menu. | 2 trips added: Eydhafushi → Maalhos → Dharavandhoo and Maduvvari → Ungoofaaru. Maalhos now has a trip home. |
| V3 metadata drift | `meta.build.id` (content hash) is stamped on the network; `fares.json` and every `extras/*.json` record `networkBuildId`; `build-db` rejects extras built from a different network. Expected stops, access edges and services come from the network's own `meta.counts`, not hand-edited numbers. | Stale artifacts now fail the database build instead of drifting silently. |
| Transparency | "Data limits" panel in the app: each main gap, what the app does about it, and the data needed. | Judges see the limits next to the results. |

Re-run order: `augment_network.py` → `build_fares.py` → `build_extras.py` → `npm run db:build`.

## 7. Top 10 data asks

Effort: S = a few days, M = weeks, L = months or a formal data-sharing agreement.

| # | Gap closed | Owner / agency | Format wanted | Effort | Impact on results |
|---|---|---|---|---|---|
| 1 | T1, T2, T3, T4: current ferry timetable with calendar, Zone 3, unscheduled routes, both directions | RTL (Regional Transport Ltd), MTCC | GTFS export (`stops`, `routes`, `trips`, `stop_times`, `calendar`, `calendar_dates`); the existing `rtl_*.csv` already maps to it | S to M | Removes the largest assumption; turns "reference day" into weekday and Friday figures; replaces 3.5-year-old MTCC data for 52,783 residents |
| 2 | D3, D4: referral and patient-flow O-D, with Aasandha emergency transfers | Aasandha / NSPA, MoH (HEMS) | CSV: year, origin island, destination facility, service, mode, count (even one year; suppress cells under 5) | L | Enables demand weighting, 2SFCA, validation of the model beyond atoll correlations, cost-benefit |
| 3 | T5, T7: passenger-boat register and speedboat schedules and tariffs | MoTCA / Transport Authority, island councils, MNDF coast guard (vessel registry) | CSV: vessel class, licence, route, days, departure times, tariff | M | Replaces or labels the 154 observed links; fixes optimistic 06:00 to 08:00 behaviour; unlocks speedboat fares |
| 4 | F1, F2, F3, F4: facility registry with coordinates, services, beds, staff, hours | MoH (HEMS and facility grading), MoE (school directory), MoHE / MQA | CSV or GeoJSON: facility id, coordinates, grade, services with date, beds, staff by cadre, opening hours; campus list with island and enrolment | M | Moves "reachable island" to "reachable service"; resolves 162 low and 385 medium claims; places 104 unplaced campus rows |
| 5 | T6, D3: domestic air schedules, capacity and load | MACL, Maldivian, Villa Air, Island Aviation | Weekly schedule (flight number, days, STD/STA), seats, domestic movements and passengers by airport | S to M | Removes the +15.9% departure inflation and the pre-08:00 gap; MACL domestic data covers what the anonymised file lacks |
| 6 | T10: sea-ambulance and air-ambulance assets and dispatch log | MNDF, NDMA, MEMS, MoH | Asset list by atoll; response-time log (origin, destination, mode, time) | M | Adds the emergency path; separates emergency from routine access |
| 7 | C1: ferry tariff by route code and current fare sheet | RTL, MTCC, MoTCA | CSV: route code, island pair, fare, concession rule, valid-from | S | Retires the regression (r2 = 0.87) and the MTCC mislabel; fixes short-hop overstatement |
| 8 | T9: intra-island roads and peak travel times | MBS / Land Survey, MNDF, Avas, island councils; OSM community | Road GeoJSON for cities; hourly speeds | M | Replaces constant island access; fixes 'zero minutes' in the cities |
| 9 | P1, C3, C4: population and prices | MBS (Census 2022 tables, HIES latest, ECPI), Ministry of Tourism, NSPA | MBS tables by island, nationality and age; HIES 2025/26; patient lodging rates | S to M | Updates VoT (removes the assumed 4% CPI), cohort denominators for education, resort and industrial staff |
| 10 | Pilot pathway for the appointment model (BACKLOG item 4) | One regional hospital and its operator (for example dialysis from one atoll) | One month of slots, roster, no-show, transport used, and cost | M | Turns the 2-hour appointment and night-away conventions into measured values |

---

## 8. What we can still claim confidently

1. **Car-only models miss the sea.** The HDX/HeiGIT benchmark finds 46.92% of people within 5 km of a school and 45.24% within 10 min of a hospital, rising only to 45.89% at 120 min, because isochrones never leave the island; 11 of 21 atolls are absent from its education table and 12 from its hospital table. The multimodal model shows what is added. This does not depend on any gap above.
2. **Structure, not level.** Only 44 of 184 atoll islands teach grades 11 and 12, and the facility tiers (3 tertiary, 6 regional, 13 atoll hospitals) are concentrated in a few hubs. The ordering of links is better supported than their level: observed and timetable durations agree in rank (0.80) although observed times are 35% shorter.
3. **Time of day matters more than any layer choice.** Hospital reach moves 22 points between 06:00 and 14:00 (95.6% to 73.6%) with the same network. Quoting a single clock time without a range is not supportable.
4. **Outside Greater Malé the picture is much worse than the national figure suggests.** 64.9% of 237,713 residents can reach a hospital tier 1 to 3 by an 08:00 departure (91.6% at 06:00, 50.3% at 14:00); regional/tertiary 61.1%. These are optimistic upper bounds on a one-way, one-day basis. We can say "at most", not "exactly".
5. **Lower bound on the gap.** The timetable-only network (RTL plus estimated air, before augmentation) gave 73.2% hospital reach and left 63,749 residents (14.2%) without transport data. We can state this lower bound without any observed-boat assumption; the augmented figure of 81.3% is an upper-central estimate.
6. **The data holes themselves are findings.** 64 islands outside Greater Malé (67,993 residents, 15.2% of the origin universe) have no RTL stop and rest on 2023 or observed evidence; 6 islands (4,335 residents) have no transport data at all; 7 islands have no return leg. This is where the next data effort pays most.
7. **Methodological honesty.** Missing coverage is never shown as zero access; filters are shown as `not_selected`; every layer is labelled and switchable; and the external validation is reported with its failure (evacuations, p = 0.25) as well as its two supportive results.

What we cannot claim: weekly or seasonal access; capacity-adjusted or appointment-adjusted access; the number of people actually served or referred; affordability beyond order of magnitude; emergency readiness; cost-benefit of any new route or clinic.

---

## Appendix A. How the numbers were computed

- Island and service counts, routes-with-no-reverse, residents by evidence layer, air frequency inflation, MTCC trips per weekday and observed-boat statistics: counted directly from `web/public/data/multimodal.json` (services, stops, islands, accessEdges, facilities, categories) with Python (`.venv\Scripts\python.exe -I`).
- Reach by departure time, air flag, category and Greater Malé split: `web/public/data/extras/island_access.json` joined to island population in `multimodal.json`; "reachable" means status `reachable` (one-way, nearest listed facility, no same-day-return test); `no_origin_access` residents (4,335 for hospital) are counted as not reachable, as in `VALIDATION.md`.
- Fares, VoT and lodging: `web/public/data/fares.json`, `data/external/economics/value_of_time.json`.
- All other figures are quoted from the cited research notes and `VALIDATION.md`. Where this register recomputed a number that also appears elsewhere, small differences (for example air-off hospital 80.3% here against 80.2% in `VALIDATION.md`) are rounding or denominator definitions.
