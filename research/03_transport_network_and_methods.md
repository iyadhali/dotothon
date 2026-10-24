# 03 — Transport network parameters & accessibility methods (land / sea / air)

**Purpose:** realistic parameters and supplementary schedule facts for a multi-modal travel-time network across Maldivian islands, used to compute accessibility to schools, tertiary education, and hospitals.
**Compiled:** 2026-10-24 from web sources (WebSearch/WebFetch, plus curl for open catalogues). Every number has a source URL. Values marked **[derived]** are my own arithmetic from sourced times and distances. Values marked **[assumption]** are modelling defaults with no direct source.
**Related files:** `08_heigit_accessibility_indicators.md` (HeiGIT car-only baseline), `MULTI_MODAL_ACCESSIBILITY_PLAN.md`.

> **Data-access caveats found while researching**
> - The official MTCC ferry timetable PDF (55 pages, "CTN-Ferry-All-Atolls-16.7.23", valid from Apr 2023) is at `https://mtcc.mv/wp-content/uploads/2022/01/CTN-Ferry-All-Atolls-16.7.23.pdf`, but mtcc.mv returns **HTTP 403 to scripted requests**. Download it by hand in a browser if needed. (URL from https://therestlessbeans.com/maldives-public-ferries/)
> - Current RTL schedules are only shown in the RTL app and the rtl.mv web portal, which is a JavaScript app. There is **no open data export and no GTFS**.
> - **No Maldives GTFS feed exists** in the Mobility Database catalogue. I checked the full `feeds_v2.csv` (https://files.mobilitydatabase.org/feeds_v2.csv, 2026-10-24) and found zero rows for country code MV.
> - Several psmnews.mv pages also return 403. Their facts are quoted here from search-result snippets.

---

## 1. Sea transport

### 1.1 Operators and network structure

| Item | Fact | Source |
|---|---|---|
| Operator | MTCC Plc (state-majority). It runs public ferries, Greater Malé buses, and the **Raajje Transport Link (RTL)** high-speed ferry network. | https://asocialnomad.com/maldives/public-ferry-maldives/ ; https://blogs.presidency.gov.mv/daily-blogs/rtl-ferry-network-expands-to-laamu-atoll |
| Policy origin | Integrated National Public Ferry Network, announced 2021. It serves all administrative islands, has separate passenger and cargo networks, uses the **6 regions of the National Spatial Plan 2020–2040**, and defines three link types: **commute, non-commute and highway links**. | https://presidency.gov.mv/Press/Article/24237 ; https://edition.mv/news/21501 |
| Design rule | The network design specifies a **12-hour, daytime-only service**, a minimum vessel speed (figure not published), automated ticketing and real-time monitoring. | https://mfr.mv/governance/the-integrated-national-public-ferry-network |
| RTL zones (Sep 2025) | Zone 1: HA, HDh, Sh · Zone 2: N, R, B, Lh · Zone 4: Th · Zone 5: GA, GDh · Zone 6: Fuvahmulah + Addu. At that date service had not started in 8 atolls. | https://atolltimes.mv/post/news/13581 |
| RTL coverage (Apr 2026) | **15 atolls**. Laamu was added on 1 Apr 2026 with 2 routes. | https://blogs.presidency.gov.mv/daily-blogs/rtl-ferry-network-expands-to-laamu-atoll |
| Rollout dates | HDh 12 Jun 2022, HA 3 Jul 2022, Sh 30 Aug 2022 · Lh (2023) · GA/GDh 13 Jul 2023 (9 routes, 6 ferries) · Addu/Fuvahmulah Aug 2023 (2 routes, 7 days/week, also the "highway link" from Zone 6 to Zone 5) · Faafu/Dhaalu (network then 14 routes) · Thaa 24 Sep 2025 (5 routes, 2 ferries, 6 days/week) · Laamu Apr 2026 | https://edition.mv/bjp/25062 ; https://adhadhu.com/40056 ; https://atolltimes.mv/post/news/5113 ; https://atolltimes.mv/post/news/13581 |
| Fleet | Zone 1 has 17 Gulf Craft high-speed ferries. A further 65 × 50-pax Al-Shaali ferries were contracted (~USD 34.6 M) for phases 2–3. India granted funds for 12 more. One report gave "81 islands, 9 atolls, 26 ferries", which is now outdated. | psmnews snippets via search; https://edition.mv/business/27602 ; https://edition.mv/news/41335 |
| Vessel | 50 passengers, air-conditioned, toilet, space for wheelchairs and stretchers. **This matters for patient transfers.** | https://edition.mv/business/27602 ; https://adhadhu.com/40056 |
| Legacy MTCC ferries | These are the routes in Kaafu, Ari, Vaavu and other atolls not yet on RTL. They are numbered by zone (e.g. 303, 305, 306, 308, 309). **No service on Fridays** except the airport ferry. Tickets are cash, bought at the counter or on board. | https://asocialnomad.com/maldives/public-ferry-maldives/ ; https://therestlessbeans.com/maldives-public-ferries/ |

### 1.2 Vessel speeds

| Vessel class | Speed | Evidence | Source |
|---|---|---|---|
| RTL high-speed ferry (Gulf Craft, Zone 1) | **Rated 30–50 kn**, "three times faster than the previously used ferries" | MTCC/PSM report | psmnews.mv/en/108547 (search snippet: https://cms.psmnews.mv/en/108547) |
| RTL effect, Huvadhu | A council president said trips fell **from 5 h to 2 h** (≈2.5×) | news | psmnews snippet (search, see §1.1 sources) |
| Legacy MTCC ferry (dhoni-type launch) | **≈8–10 kn effective, including stops** [derived]. Malé→Maafushi (~26 km straight line, 2 intermediate stops) takes 15:00→16:40 = 100 min, about 8.4 kn. Malé→Ukulhas (~72 km) takes 09:00→13:05 = 245 min, about 9.5 kn. One blog quotes "12–20 kn", which looks too high against these timetables. | timetable excerpts | https://therestlessbeans.com/maldives-public-ferries/ |
| Engine dhoni (generic) | ~7–8 kn cruise. One 22 m charter dhoni: 8 kn at half load, 14.8 kn max | charter spec | https://arconyachts.com/en/shipyards/fairline/charters/fairline-dhoni-stella |
| Shared/private speedboat | **≈25–30 kn effective on open water** [derived]. Malé→Dhangethi (~88 km straight line) takes 90–105 min, about 27–31 kn. Malé/airport→Maafushi (~26 km) takes 40–45 min, about 19 kn including harbour manoeuvring. Charter boats are rated up to 40 kn top speed. | operator timetables | https://amaldives.com/islands/dhangethi ; https://12go.com/en/ferry/male/maafushi/ ; https://surf-shop-maldives.odoo.com/surf-trips |
| Sea ambulance | 19 m vessel with life support (Japan grant, USD 3.6 M). The MNDF Coast Guard also moves patients. | | https://www.mv.emb-japan.go.jp/itpr_ja/11_000001_00261.html |

### 1.3 Sample schedules and travel times (supplementary schedule data)

| Route | Service | Days / frequency | Times / duration | Source |
|---|---|---|---|---|
| Malé ↔ Hulhulé (airport ferry) | MTCC | Daily incl. Friday. Every 15 min 06:00–19:00, every 30 min 19:00–24:00 | ~10 min; MVR 15 (20 early morning) | https://therestlessbeans.com/maldives-public-ferries/ |
| Malé ↔ Villimalé | MTCC | ~every 15 min in daytime (5–10 min historically at peak) | ~7 min; ~MVR 3.25 | https://minivannewsarchive.com/?p=18743 ; https://wanderlog.com/place/details/43100/villingili-ferry-terminal ; https://raajje.mv/80332 |
| Malé → Himmafushi (308, continues to Huraa/Thulusdhoo/Dhiffushi) | MTCC | Daily except Friday, 1/day each way | 14:30→15:10 (40 min) | https://therestlessbeans.com/maldives-public-ferries/ |
| Malé → Gulhi → Guraidhoo → Maafushi (309) | MTCC | Daily except Friday, 1/day each way | 15:00→16:40 (100 min); return 07:25→09:05 | same |
| Malé → Maafushi → Fulidhoo (306) | MTCC | Sun/Tue/Thu out, Sat/Mon/Wed back | 10:00 → Maafushi 11:30 → Fulidhoo 13:20 | same |
| Malé → Ukulhas → Thoddoo (303) | MTCC | Mon/Thu out, Sun/Wed back | 09:00 → 13:05 → 16:20 | same |
| Malé → Mahibadhoo (305) | MTCC | a few days per week | dep 08:30 | same |
| Malé → Dhangethi (shared speedboat) | private | 2/day (Fri adjusted) | 10:45 & 16:00; 90–120 min | https://amaldives.com/islands/dhangethi |
| Malé → Dhigurah (shared speedboat) | private | 1/day | 16:00; ~90 min | https://www.bluewaterdivetravel.com/node/6771 |
| Malé → Thulusdhoo (shared speedboat) | private | ~4/day | 09:20, 12:20, 16:30, 22:15 | search result (asocialnomad) |
| Malé → Guraidhoo (speedboat) | private | 3/day each way | ~45 min | https://en.wikipedia.org/wiki/Guraidhoo_(Kaafu_Atoll) |
| Malé → Meemu (RTL) | MTCC | 2/week planned | — | psmnews snippet (Male'–Meemu agreement) |
| Kulhudhuffushi residents | RTL | Residents asked for ferry times to match flights at Hanimaadhoo, showing **intermodal timing is a real friction** | — | psmnews snippet (search) |

### 1.4 Fares

| Service | Fare | Source |
|---|---|---|
| Legacy MTCC ferries | MVR 20–53 (e.g. Malé–Thulusdhoo MVR 22, to Vaavu MVR 53), about USD 1.4–3.4 | https://asocialnomad.com/maldives/public-ferry-maldives/ ; https://therestlessbeans.com/maldives-public-ferries/ |
| RTL within atoll (Lh) | USD 2–8 | psmnews snippet |
| RTL Villingili (GA) ↔ Thinadhoo (GDh) highway | USD 10 | psmnews snippet |
| RTL Fuvahmulah ↔ Vaadhoo / Hulhumeedhoo / Feydhoo | USD 16 | https://www.psmnews.mv/en/126992 (snippet) |
| RTL Vaadhoo ↔ Hulhumeedhoo | USD 32 | same |
| RTL Hulhumeedhoo ↔ Feydhoo | USD 4 | same |
| RTL free riders | NSPA-registered persons with disabilities; children under 3 on lap | https://atolltimes.mv/post/news/5113 |
| Shared speedboat | USD 20–75 one way (Maafushi ~25, Fulidhoo ~50, distant ~75) | https://therestlessbeans.com/maldives-public-ferries/ |
| Private charter | ~USD 150–300+; boat fares up to **MVR 2,500** reported for an island-to-Kulhudhuffushi trip for childbirth | https://amaldives.com/plan-your-trip/maldives-public-ferry-guide-2026 ; https://raajje.mv/21781 |

### 1.5 Boarding and terminal overheads

- Legacy ferry: buy at the counter on the day; guides advise **arriving 30–45 min early**. Missing a 1/day ferry means waiting until the next day or chartering. (https://amaldives.com/plan-your-trip/maldives-public-ferry-guide-2026)
- RTL: tickets via app or website, seat reservation, so a **~15 min** pre-departure buffer is reasonable **[assumption]**.
- Shared speedboats: timetables are geared to international flights. After about 20:00 most shared boats stop and private transfers carry a 20–30% night surcharge. (https://pickyourtrail.com/blog/maldives-speedboat-guide)
- Empirical ferry waiting (Norway, 10,952 travellers): with an **average headway of 52 min, the average terminal wait was 15 min**, below half the headway. Wait rises concavely with headway. Capacity denials caused about 20% of waiting. Hanssen, Jørgensen & Larsen (2020), *Transportation* 47(4). (https://ideas.repec.org/a/kap/transp/v47y2020i4d10.1007_s11116-019-09979-5.html ; https://nordopen.nord.no/nord-xmlui/handle/11250/2583719)

---

## 2. Air

### 2.1 Airports (20)

| Airport | Island (atoll) | IATA | Type |
|---|---|---|---|
| Velana Intl | Hulhulé (Kaafu/Malé) | MLE | Intl (main hub) |
| Gan Intl | Gan (Addu) | GAN | Intl (minor) |
| Hanimaadhoo Intl | Hanimaadhoo (HDh) | HAQ | Intl (minor) |
| Maafaru Intl | Maafaru (N) | NMF | Intl (minor) |
| Villa Intl Maamigili | Maamigili (ADh) | VAM | Intl (minor, mostly domestic traffic) |
| Dharavandhoo | B | DRV | Domestic |
| Fuvahmulah | Gn | FVM | Domestic |
| Maavarulu | GDh | RUL | Domestic |
| Ifuru | R | IFU | Domestic |
| Kaadedhdhoo | GDh | KDM | Domestic |
| Kadhdhoo | L | KDO | Domestic |
| Kooddoo | GA | GKK | Domestic |
| Dhaalu (Kudahuvadhoo) | Dh | DDD | Domestic |
| Thimarafushi | Th | TMF | Domestic |
| Kulhudhuffushi | HDh | HDK | Domestic |
| Madivaru | Lh | LMV | Domestic |
| Funadhoo | Sh | FND | Domestic |
| Hoarafushi | HA | HRF | Domestic |
| Faresmaathodaa | GDh | FMT | Domestic |
| Muli | M | MUM | Domestic (no scheduled service flagged on Wikipedia) |

Source: https://en.wikipedia.org/wiki/List_of_airports_in_the_Maldives . The Wikipedia page itself notes it relies on a single source. Runways are about 1,200–1,220 m at the newer domestic airports (Kulhudhuffushi, Funadhoo, Ifuru), which suits turboprops. (https://www.aircharterservice.com/about-us/news-features/blog/your-guide-to-airports-in-the-maldives)

**Modelling note:** several airports sit on uninhabited or airport-only islands (e.g. Kooddoo, Kaadedhdhoo, Kadhdhoo, Hulhulé, Gan-Addu is road-linked). Each needs an explicit **airport↔town access edge** (road or speedboat). Example: Kaadedhdhoo passengers "often transfer by speedboat" (aircharterservice, above).

### 2.2 Airlines

| Airline | Domestic network | Fleet (2026) | Source |
|---|---|---|---|
| **Maldivian** (Island Aviation, state) | Widest network: DRV, FMT, FND, FVM, GAN, HAQ, HRF, IFU, KDM, KDO, GKK, HDK, NMF, RUL, LMV, TMF, MUM | ATR 42-600 ×3, ATR 72-600 ×2, Dash 8-300 ×2 (being phased out), DHC-6 Twin Otter seaplanes ×11. Dash 8-200 used as **air ambulance (MEMS)** | https://en.wikipedia.org/wiki/Maldivian_(airline) |
| **Manta Air** | Hub at Dhaalu (DDD). Serves DRV (2–3/day since 2019), IFU, LMV, GKK; also seaplanes. ATR 72-600s | | https://hoteliermaldives.com/manta-air-expands-flight-schedule-for-eid-al-fitr/ ; https://www.ch-aviation.com/news/83595-maldives-manta-air-launches-seaplane-operations |
| **Villa Air / Flyme** | Essentially MLE↔VAM (Maamigili). DRV "resuming soon" | ATR 72-500 ×1, ATR 72-600 ×1, DHC-6 ×2 | https://en.wikipedia.org/wiki/Villa_Air |
| **Trans Maldivian Airways (TMA)** | Seaplanes to ~80 **resorts**. Bases at Velana and Gan. Scheduled domestic service ended in 2009 | ~65 DHC-6 Twin Otters, the world's largest seaplane fleet | https://en.wikipedia.org/wiki/Trans_Maldivian_Airways ; https://transmaldivian.com/twin-otter/ |

### 2.3 Typical block times from Malé (MLE) and observed daily frequency

| To | Atoll | Block time | Flights listed on sample day |
|---|---|---|---|
| VAM | ADh | 25–30 min | 3 |
| LMV | Lh | ~25 min | — |
| DRV | B | 30–40 min | 1 |
| DDD | Dh | 35–45 min | 5 |
| IFU | R | 40–50 min | 2 |
| NMF / HAQ / TMF | N / HDh / Th | 45–55 min | 1 / 2 / 0 |
| FND / KDO | Sh / L | 50–60 min | 1 / 2 |
| HDK | HDh | 50–55 min | 1 |
| HRF / GKK | HA / GA | 55–65 min | 1 / 3 |
| KDM / RUL | GDh | 60–70 min | 2 / 0 |
| FVM | Gn | 60–75 min | 3 |
| GAN | Addu | 70–90 min | 2 |

Sources: https://resortlife.travel/maldives-domestic-flights (live board, 59 domestic movements that day). LMV time is from https://www.aircharterservice.com/about-us/news-features/blog/your-guide-to-airports-in-the-maldives . Use the datathon **MACL** dataset for real frequencies where possible.

Implied block speed [derived]: MLE–GAN is about 480 km in about 80 min, roughly 360 km/h. For pairs without a published time, use **300 km/h great-circle plus 10 min taxi**, which is conservative for ATR and Dash 8.

### 2.4 Overheads

- Check-in: guides advise arriving **60–90 min** before domestic departures. Velana's own guidance is 2 h (https://resortlife.travel/maldives-domestic-flights ; https://velana.macl.aero/guide/departure). Maldivian's city check-in closes 90 min before departure (psmnews.mv/en/38548 via search).
- Baggage: 20 kg checked + 5–7 kg cabin on Maldivian domestic economy. (https://maldives-magazine.com/general-info/maldives-domestic-flights-booking-baggage-allowance-tips.htm)
- **Seaplanes fly daylight only.** Operators give windows of about 06:00–15:30 to 06:00–18:00, and arrivals after mid-afternoon overnight in Malé. (https://constancehotels.com/en/seaplane-constance-halaveli-maldives-booking-conditions ; https://www.centarahotelsresorts.com/the-centara-collection/cirm/sea-plane-transfer ; https://www.fourseasons.com/maldiveslg/getting-here.mobile/)
- DHC-6 cruise is 145 kn (Series 300 reference) and 170 KTAS max cruise for the 300-G on wheels. Float drag lowers it, so use **~140 kn** for seaplanes [assumption]. (https://www.islesofscilly-travel.co.uk/wp-content/uploads/2016/10/skybus-seating-plans.pdf ; https://dehavilland.com/wp-content/uploads/2025/09/DHC-6-Twin-Otter-Classic-300-G_Brochure_V4_DIGITAL.pdf)
- **Recommendation:** leave seaplanes out of the resident accessibility network. They serve resorts, are mostly chartered, and fly in daylight only. Include them, if at all, only as an emergency or charter scenario.

---

## 3. Land

### 3.1 Inter-island road links

| Link | Islands joined | Length | Status | Source |
|---|---|---|---|---|
| **Sinamalé Bridge** | Malé ↔ Hulhulé (airport) ↔ Hulhumalé (by road across Hulhulé) | **1.39 km**, 20.3 m wide | Open since 30 Aug 2018 | https://en.wikipedia.org/wiki/Sinamal%C3%A9_Bridge ; https://edition.mv/news/43821 |
| **Thilamalé Bridge** (Greater Malé Connectivity Project) | Malé ↔ Villingili ↔ Gulhifalhu ↔ Thilafushi | **6.74 km** (≈3.6 km over water, 3 navigation spans of 140 m) | **Under construction.** 76.1% complete (Aug 2026). The Malé–Villingili deck was joined in late Aug 2026. Opening target **21 Dec 2027**. Do not include in the 2026 baseline; use it as a "2028 scenario" | https://en.wikipedia.org/wiki/Thilamal%C3%A9_Bridge ; https://standard.mv/?p=19536 ; https://standard.mv/president-muizzu-walks-across-newly-connected-male-villingili-section-of-thilamale-bridge/ |
| **Addu Link Road** | Hithadhoo ↔ Maradhoo ↔ Maradhoo-Feydhoo ↔ Feydhoo ↔ Gan | Quoted as 12.3–16 km. Rebuild covers 12.3 km existing plus 5.5 km new | Open. Reconstruction contract MVR 829.8 M (RDC, 3 y 9 m); survey began early 2026 | https://edition.mv/news/40402 ; https://edition.mv/news/47945 ; https://en.mmtv.mv/3804 |
| (Addu, not road-linked) | Hulhumeedhoo (Hulhudhoo+Meedhoo, one island) and Addu Villingili are **not** road-linked to Gan. RTL charges USD 4 for Hulhumeedhoo↔Feydhoo | — | — | §1.4 |
| **Laamu Link Road** | Fonadhoo ↔ Kadhdhoo (airport) ↔ Maandhoo ↔ Gan | **~15 km** (EIA 14.9 km; AidData 15.1 km; MNU cites ~18 km of causeways) | Open since Nov 2016 (Chinese grant) | https://china.aiddata.org/projects/38034 ; https://saruna.mnu.edu.mv/items/0a94c739-3163-4d98-9040-29180f7f17d6 ; https://mnu.edu.mv/gan |
| Hulhulé ↔ Hulhumalé | Link road/causeway on the reclaimed land | short | Open; Malé's only 4-lane road corridor | https://maldivesindependent.com/society/five-injured-in-highway-accidents-142357 |

### 3.2 Urban speeds and buses

| Item | Fact | Source |
|---|---|---|
| Sinamalé Bridge speed limit | 25–50 km/h | https://raajje.mv/40271 ; https://raajje.mv/46373 |
| Highway (bridge / Hulhumalé road) vs Malé | "Speed limit on the highway is 50 km/h, **double the limit in the capital**", which implies **~25 km/h in Malé** | https://raajje.mv/46373 (Dec 2018) |
| Congestion | 64% of the 390,000 m² road area in Greater Malé is occupied by vehicles. Over 65% of Malé's land area is taken by vehicles. Heavy reliance on two-wheelers | https://uncrd.un.org/sites/uncrd.un.org//files/16th-est_cr_maldives-ppt.pdf (MoTCA, Dec 2024) |
| RTL buses (Greater Malé) | 46 buses and 8 routes (2022); later 12 routes and 105 buses in the MTCC fleet. **West Malé → Hulhumalé Phase II: 15 min peak / 20 min off-peak** (~10 km, ≈30–40 km/h [derived]) | https://edition.mv/business/24980 ; psmnews snippets |
| Bus headway and fare | Typically every 15–20 min. Airport routes: R3 60 min, R4 30 min, R9 30 min (24/7). MVR 5 urban, MVR 10–15 airport routes. No service ~11:30–13:00 on Fridays (prayer) | https://booking.resortlife.travel/content/content.aspx?id=11461 ; https://www.cestee.com/airport/male-mle/transport ; search summary |
| Policy targets | Public transport to cater for 80% of demand by 2027; ridership +40% by 2030; 50% e-buses | https://uncrd.un.org/sites/uncrd.un.org//files/16th-est_cr_maldives-ppt.pdf |

**On-island travel outside Greater Malé:** most inhabited islands are under 2 km long, so walking at 4.5 km/h (≤25 min) or motorbike is enough. Large exceptions are Fuvahmulah (~4.5 km), Addu, Laamu and Kulhudhuffushi; use a motorbike or taxi at 25–35 km/h there [assumption].

---

## 4. Methodology

### 4.1 HeiGIT / openrouteservice "Accessibility Indicators" (baseline to beat)

- HDX dataset "Maldives – Accessibility Indicators" (HeiGIT, CC BY-SA, last modified 2026-02-25): https://data.humdata.org/dataset/maldives-accessibility-indicators . It is already downloaded and profiled in `08_heigit_accessibility_indicators.md`.
- Method: **isochrones "reachable … by car"** from openrouteservice on OSM roads, overlaid on WorldPop 100 m. Hospitals and primary healthcare use 10–120 min bands; schools use **distance** bands of 5–50 km. Results are aggregated by geoBoundaries ADM0–ADM4. (HDX metadata; https://heigit.org/global-data-on-healthcare-and-education-accessibility-with-openaccesslens/)
- Stated limitations: **motorized travel only**, no public or non-motorized transport, standard road speeds, and dependence on OSM completeness. (same)
- ORS has **no ferry profile**. Ferries in OSM are only used when they are routable for the profile (e.g. not `motor_vehicle=no`), and ferry avoidance needs `avoid_features: ["ferries"]`. (https://ask.openrouteservice.org/t/route-wont-take-ferry/461 ; https://ask.openrouteservice.org/t/isochrone-call-on-premise-server-avoid-features-ferries-issue/3940)
- **Why it fails in the Maldives:** in the HeiGIT output the hospital share goes from 45.2% at ≤10 min to only 45.9% at ≤120 min. Isochrones cannot leave the home island, so the indicator effectively means "lives on the same island as a facility". This is our core motivation. Methods references: Geldsetzer et al. 2020 (*Lancet Healthy Longevity*); Petricola et al. 2022 (https://doi.org/10.1186/s12942-022-00315-2).

### 4.2 Timetable-based tools (r5py / OpenTripPlanner)

- **r5py** (Python wrapper of Conveyal R5) computes travel-time matrices from an OSM `.pbf` plus one or more GTFS feeds. Ferries are ordinary transit routes (GTFS `route_type = 4`). (https://sumogis.readthedocs.io/en/latest/lessons/L2/r5py_demo.html ; https://transit.land/documentation/datastore/routes-and-route-stop-patterns.html)
- **OpenTripPlanner** supports per-mode slack: `boardSlackForMode` / `alightSlackForMode` with keys including `FERRY` and `AIRPLANE`. The docs' example is AIRPLANE board 35 min and alight 15 min, and `transferSlack` defaults to 2 min. (https://docs.opentripplanner.org/en/latest/RouteRequest/)
- **Blocker:** no GTFS exists for the Maldives (see the data-access caveats at the top). With these tools you would have to **synthesize GTFS** from `MTCC.xlsx` and MACL. GTFS `frequencies.txt` can express "n departures per day" where exact times are unknown. Every ferry stop must snap to OSM walkable ways on its island; check stop-linking on small islands. For a hackathon this costs more than it returns. **Recommended: a custom generalized-cost graph in networkx or igraph (§4.4)**, with r5py or OTP left as stretch goals.

### 4.3 World Bank, ADB and government transport documents

- I found **no World Bank Maldives inter-island accessibility study**. MTCC says the World Bank reviewed RTL and found it met international standards, but I could not locate that study (psmnews.mv/en/112632). World Bank "interisland connectivity" projects returned in searches concern the **Comoros** (P179109). It is a useful analogue for SIDS ferry projects, not Maldives data.
- ADB: "Sustaining Harbor Operation and Maintenance in Maldives" (2018, Kulhudhuffushi harbour) https://www.adb.org/publications/harbor-operation-maintenance-maldives . An ADB country diagnostic named an **inadequate inter-atoll transport network as the #1 binding constraint** on growth (via https://see.mv/31706).
- Government: no document titled "National Transport Policy" was found online. The closest policy documents are: Strategic Action Plan 2019–2023 and National Spatial Plan 2020–2040, which make an integrated national transport service a national priority (https://edition.mv/news/21501); the MoTCA urban transport presentation (Dec 2024, UNCRD link above); and Civil Aviation "Flight Plan 2020–2025" (https://see.mv/63429). The Maldives Transport Authority was abolished and its functions moved to the Ministry (psmnews.mv/en/95409).
- Island accessibility literature: on Greek Aegean islands, accessibility depends on available modal options more than on distance (Island Studies Journal 2014, https://doaj.org/article/9dddcb6c4cdb41e0b79d8a86b3714a2e). Norwegian ferry waiting-time evidence is in §1.5.

### 4.4 Recommended graph design (hackathon-ready)

**Nodes**
1. `island` nodes: one per inhabited island (~187), placed at the harbour if known, else the centroid. Attributes: population (census 2022), atoll, and service flags (school / higher-secondary / tertiary campus / health centre / atoll / regional / tertiary hospital).
2. `airport` nodes: the 20 airports in §2.1.
3. Optional `stop` nodes for Greater Malé (Malé, Villimalé, Hulhumalé Ph I/II, Hulhulé) to resolve the bus, bridge and ferry options.

**Edges** (directed, weight = generalized minutes)

| Edge type | Built from | In-vehicle time | Added overhead |
|---|---|---|---|
| `road` | linked islands (Greater Malé, Addu, Laamu) and airport↔town on road-linked islands | distance ÷ road speed (§5) | 0–5 min parking/pick-up |
| `bus` | RTL Greater Malé routes | published 15–20 min Malé↔Hulhumalé | wait = headway/2 |
| `ferry_rtl` | RTL routes (MTCC.xlsx / RTL app) | route distance × 1.15 detour ÷ 25 kn | board 15 min + wait |
| `ferry_legacy` | MTCC routes (MTCC.xlsx / CTN PDF) | distance × 1.15 ÷ 9 kn, or use timetable durations directly | board 30 min + wait |
| `speedboat_shared` | known private routes from Malé/airport (§1.3) | distance × 1.15 ÷ 25 kn | board 20 min + wait |
| `speedboat_charter` | *scenario only*: any island pair in the same atoll within 60 km, plus the nearest hub | distance × 1.15 ÷ 25 kn | dispatch 45 min, no headway |
| `air` | MACL flight pairs | published block time (§2.3), else great-circle ÷ 300 km/h + 10 | check-in 60 min (MLE) / 45 min (outer), egress 15 min, + wait |
| `access` | island↔its airport (speedboat or road) | as above | — |

**Waiting rule.** For headway H in minutes, using the daytime service span of 12 h from the ferry network design:
- `wait = min(H/2, cap)`, with cap = 30 min for urban modes (bus, airport and Villimalé ferries).
- For **infrequent services (≤ a few departures/day)** half-headway is not meaningful: a 3/week ferry gives a 28 h "wait". Report two scenarios:
  - **A. Planned trip:** wait = 0. The traveller times arrival to the schedule, so only boarding buffers apply. Add a separate **service-frequency indicator** (departures per week on the best path).
  - **B. Unplanned / on-demand:** wait = H/2 capped at 12 h. Exclude Friday for legacy MTCC ferries.
- Optionally use the empirical concave form instead. In Norway, H ≈ 52 min gave an observed wait of ≈15 min, about 0.3·H. Use `wait ≈ 2·√H` minutes as a smooth alternative [assumption calibrated to that point: 2·√52 ≈ 14].

**Transfer penalty.** Add **+10 min per mode change** at the same harbour or airport and **+5 min** pure disutility per boarding after the first. Use +20–30 min when the change needs a road or speedboat hop between an airport island and a harbour island.

**Scenarios to compute**
1. Car-only (replicates HeiGIT, the sanity check).
2. Public scheduled transport, planned trip (A).
3. Public scheduled transport with waits (B), including a Friday variant.
4. **Emergency/health:** charter speedboat or sea ambulance plus Maldivian air ambulance (Dash 8, operating since 2 Mar 2024) to the nearest regional or tertiary hospital, with dispatch overhead.
5. 2028 network: Thilamalé bridge open, plus new RTL zones.

**Algorithm.** Multi-source Dijkstra from all facility nodes of a given tier on the reversed graph (networkx `multi_source_dijkstra`), giving travel time from each island to the nearest facility. Weight by island population for "% of population within 30/60/120/240 min" and "same-day return feasible". Report the dominant mode chain per island.

---

## 5. Ready-to-use parameter table

| Mode | Speed (effective) | Wait / transfer overhead | Main source(s) |
|---|---|---|---|
| Walk (on-island) | 4.5 km/h | — | [assumption]; islands mostly <2 km |
| Motorbike/car, Malé city | 15–20 km/h | +3 min parking | Malé limit ~25 km/h (https://raajje.mv/46373) |
| Car, bridge / Hulhumalé / Addu & Laamu link roads | 35–40 km/h | +3 min | 50 km/h limit (https://raajje.mv/46373 ; https://raajje.mv/40271) |
| RTL bus, Greater Malé | ~30 km/h (Malé W↔Hulhumalé Ph II 15–20 min) | wait = ½ headway (15–20 min → 8–10 min); airport routes 30–60 min headway | https://edition.mv/business/24980 ; https://booking.resortlife.travel/content/content.aspx?id=11461 |
| Urban shuttle ferry (Malé↔Villimalé, Malé↔Hulhulé) | fixed 7–10 min | wait 5–8 min + 5 min boarding | https://therestlessbeans.com/maldives-public-ferries/ ; https://wanderlog.com/place/details/43100/villingili-ferry-terminal |
| Legacy MTCC ferry (dhoni-type) | **9 kn ≈ 17 km/h** (8–10 kn incl. stops) | board 30 min; 1/day to 2–3/week; no Friday service; wait per scenario A/B | [derived] from https://therestlessbeans.com/maldives-public-ferries/ ; https://amaldives.com/plan-your-trip/maldives-public-ferry-guide-2026 |
| RTL high-speed ferry | **25 kn ≈ 46 km/h** effective (rated 30–50 kn) | board 15 min; daily, 6–7 days/week; wait per scenario | psmnews.mv/en/108547 ; https://atolltimes.mv/post/news/13581 |
| Shared speedboat (private) | **25 kn ≈ 46 km/h** (open water 27–31 kn; short harbour hops ~19 kn) | board 20 min; 1–4 departures/day | [derived] from https://amaldives.com/islands/dhangethi ; https://12go.com/en/ferry/male/maafushi/ |
| Charter speedboat / sea ambulance | 25 kn | dispatch 30–60 min [assumption]; no headway | https://mfr.mv/soes/how-aasandha-works ; https://www.mv.emb-japan.go.jp/itpr_ja/11_000001_00261.html |
| Domestic flight (ATR/Dash 8) | published block times (25–90 min from MLE); fallback 300 km/h + 10 min | check-in 60 min MLE / 45 min outer; egress 15 min; wait = ½ headway (1–5 flights/day) or scenario A | https://resortlife.travel/maldives-domestic-flights ; https://velana.macl.aero/guide/departure |
| Air ambulance (Maldivian Dash 8, MEMS) | 300 km/h | dispatch 60–120 min [assumption] | https://mfr.mv/public-sector/maldives-achieves-healthcare-milestone-with-launch-of-first-air-ambulance-service |
| Seaplane (resort/charter only) | ~140 kn ≈ 260 km/h | daylight only (~06:00–15:30/18:00); check-in 60 min | https://constancehotels.com/en/seaplane-constance-halaveli-maldives-booking-conditions ; DHC-6 specs above |
| Mode change (same terminal) | — | +10 min, plus +5 min per extra boarding | [assumption]; OTP default transferSlack 2 min + mode slack (https://docs.opentripplanner.org/en/latest/RouteRequest/) |
| Airport island ↔ town hop | by road or speedboat speed | +20–30 min | [assumption] |

Detour factor: multiply straight-line sea distances by **1.15–1.3** to account for reef passes and channels [assumption]. Check against timetable durations where available.

---

## 6. Education and health system facts

### 6.1 Tertiary education locations

| Institution | Campuses (island, atoll) | Source |
|---|---|---|
| **Maldives National University (MNU)** | Main campus **Malé** (several sites); **Kulhudhuffushi** (HDh, northernmost, est. 1987); **Gan** (Laamu); **Hithadhoo** (Addu); **Thinadhoo** (GDh). Also **>15 outreach centres** (locations not published on the about page). Serves more than half of the country's tertiary students | https://mnu.edu.mv/about-us/ ; https://courses.mnu.edu.mv/campus/3 |
| **Villa College** (private) | 9 campuses: QI Campus (Malé), Knowledge Village, Lakeside (both Greater Malé area, location not stated on page), **Fuvahmulah**, **Addu**, **Hithadhoo** (Addu), **Mahibadhoo** (ADh), **Kulhudhuffushi** (HDh), **Naifaru** (Lh), plus **Laamu Gan** (opened 2019). Learning centres in N, R, K, ADh, L atolls | https://villacollege.edu.mv/campus ; https://villacollege.edu.mv/news/villa-college-gan-campus-officially-inaugurated |
| **Islamic University of Maldives (IUM)** | Main campus Malé. 6 **temporary** atoll campuses in operation; **11 permanent campuses** planned (10 contracts awarded). These include **Manadhoo** (N, under construction, first permanent atoll campus), **Funadhoo** (Sh, land handed over Apr 2026), **Naifaru** and **Hinnavaru** (Lh). Learning centres have run in Lh | https://blogs.presidency.gov.mv/daily-blogs/land-secured-for-new-islamic-university-campus-in-funadhoo ; psmnews.mv/en/178756, /182341, /176711 (snippets) |
| **Maldives Polytechnic** | Malé. Planned campuses in **Fuvahmulah** and **Gadhdhoo** (GDh). Temporary courses have run in Dhidhdhoo, Kulhudhuffushi, Fonadhoo, Manadhoo, Kudahuvadhoo, Gadhdhoo | https://cms.psmnews.mv/en/62366 ; psmnews.mv/en/64676 |

**Tertiary nodes for the model:** Malé/Hulhumalé (all institutions), Kulhudhuffushi (MNU, Villa), Naifaru (Villa, IUM), Manadhoo (IUM, opening), Mahibadhoo (Villa), Laamu Gan (MNU, Villa), Thinadhoo (MNU), Fuvahmulah (Villa, Polytechnic planned), Addu Hithadhoo (MNU, Villa). Weight Malé higher, since full degree programmes concentrate there.

### 6.2 Health system tiers and hospitals

- **Three tiers.** (1) Island-level primary health centres, present on every inhabited island however small. (2) Atoll and regional hospitals with specialists, at least one atoll hospital per atoll. (3) Tertiary referral hospitals. (MoH, quoted in search results from https://health.gov.mv/en/ministry-of-health ; UN https://maldives.un.org/en/download/55967/102366)
- **Counts** (MoH Health Statistics 2021, as shown in an ADB forum slide, Jul 2025): tertiary 3 referral hospitals; **regional 6 (+5 being upgraded to tertiary)**; **atoll hospitals 13**; **island-level facilities 164**; 5 hospitals in Malé; 3,720 beds (1,309 Greater Malé, 2,411 atolls). (https://events.development.asia/system/files/ps26-ms-shaina-uhc.pdf)
- **Current MoH list of tertiary hospitals (6):** government IGMH (Malé), Dharumavantha (Malé), Hulhumalé Hospital, Addu Equatorial Hospital (Hithadhoo); private ADK (Malé) and Treetop (Hulhumalé). (search result from health.gov.mv; also https://health.gov.mv/en/news/moaldivs-neshanal-yunivaasal-helthu-kavareyj-foaramyooechsee-foaram-miadhu-fashaifi)
- **Regional hospitals** (Maamaaraa facility directory): **Kulhudhuffushi RH** (HDh), **Ungoofaaru RH** (R), **Muli RH** (M), **Gan RH** (L, listed as AH), **Dr. Abdul Samad Memorial, Thinadhoo** (GDh). AEH (Addu) completes the 6. Planned tertiary upgrades: Kulhudhuffushi, Ungoofaaru, Gan, Thinadhoo, AEH. (https://maaharaa.health.gov.mv/Public/Home/ListHealthCare ; https://www.psmnews.mv/en/77726)
- **Atoll hospitals** (Maamaaraa): Dhidhdhoo (HA), Funadhoo (Sh), Manadhoo (N), Naifaru (Lh), Eydhafushi (B), Rasdhoo (AA), Mahibadhoo (ADh), Nilandhoo (F), Kudahuvadhoo (Dh), Veymandoo (Th), Villingili (GA), Fuvahmulah (Gn). Greater Malé also has Villimalé Hospital and Senahiya (military), plus private Medica and IMDC (Addu). New hospitals near completion: Hoarafushi (HA), Kendhikulhudhoo (N), Dhuvaafaru (R), Thulhaadhoo (B), Hinnavaru (Lh), Guraidhoo (K). (https://maaharaa.health.gov.mv/Public/Home/ListHealthCare ; psmnews.mv/en/174494 snippet)

### 6.3 How students and patients travel now

- **Malé dependency.** About **50% of Malé-area residents come from other atolls** (Census 2022, cited by MoTCA). (https://uncrd.un.org/sites/uncrd.un.org//files/16th-est_cr_maldives-ppt.pdf)
- **Students.** **4,443 requests to transfer** into Malé schools in 2020–2024, and **>1,500 island-to-Malé transfers** at the start of the 2026 year. Malé had 38 schools while atoll schools fell from 338 to 238 (2016–2020). Some students must move islands for higher-secondary (A-level) years. UNICEF/MoE (2015) studied children migrating to Malé without parents. (https://maldivesindependent.com/morning-brief/new-academic-year-begins-with-unabated-migration-to-capital-9786 ; https://www.idea.int/publications/catalogue/html/absent-voters-maldives-challenges-and-prospects-enfranchisement ; https://www.unicef.org/maldives/reports/assessment-situation-students-who-migrate-mal%C3%A9-education ; https://www.eenet.org.uk/blog-how-geospatial-data-is-transforming-education-in-remote-maldivian-islands/)
- **Patients and Aasandha.**
  - Universal insurance gives 100% cost coverage in public facilities (ADB slide above).
  - Aasandha **covers emergency medical transport**. The mode depends on condition, distance and availability. If no sea ambulance is available, a private speedboat can be hired with prior Aasandha approval.
  - Overseas referrals get economy air tickets; in 2019 Aasandha spent MVR 74 M on air tickets out of MVR 2.4 bn total. (https://mfr.mv/soes/how-aasandha-works)
  - Aasandha also ran an inter-island transfer service for chemotherapy, dialysis, transfusion and labour, with 339 emergency evacuations and 31 charter flights in one reported period. (https://www.psmnews.mv/en/69237 snippet)
  - Coverage for travel off-island for **childbirth was cut** once an island got a resident gynaecologist, leaving families with boat fares up to MVR 2,500. (https://raajje.mv/21781)
- **Transfer system.** MoH SOP: land and sea transfers exist, but before 2024 there was no structured air transfer for critical patients and charters were inconsistent. (https://maaharaa.health.gov.mv/Public/Home/GetFile/72b210c7-bb18-4906-9a01-5cf8c0ffe5e2) Maldivian's air ambulance started on **2 Mar 2024** (first flight Kulhudhuffushi→Malé, 15 staff). (https://mfr.mv/public-sector/maldives-achieves-healthcare-milestone-with-launch-of-first-air-ambulance-service) A high-profile case: a sea ambulance took a child to Kooddoo, then a charter flight to Malé after a technical fault on the planned flight. This led to a presidential review of medevac processes. (search snippet, Deccan Herald via foreignpolicy link)
- **Cost burden.** Inter-island travel cost about MRF 600 M in 2015, and **about two-thirds of it was for medical purposes**. Rural travellers bear a disproportionate cost. (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4583732/ ; https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6010160/)

---

## 7. Open gaps and next steps

1. Get the **CTN ferry timetable PDF** and RTL route lists by hand in a browser (403 to scripts). Cross-check them against the datathon `MTCC.xlsx`.
2. Use **MACL** for real flight frequencies and pair list, and keep the §2.3 block times as a fallback.
3. Pull OSM `route=ferry` ways for the Maldives via Overpass to get route geometry and `duration` tags. Overpass rate-limited my attempt with HTTP 429; retry later with: `[out:json];area["ISO3166-1"="MV"][admin_level=2]->.a;(way["route"="ferry"](area.a);relation["route"="ferry"](area.a););out geom;`
4. No published RTL in-service speed exists. Calibrate the 25 kn assumption against 2–3 RTL timetable durations from the app.
5. Locations of MNU outreach centres and IUM temporary campuses are unpublished. Treat them as secondary tertiary nodes, or omit them.
