# Maldives Datathon 2026: Context Research

Researched 2026-10-24 using WebFetch/WebSearch, plus a read of the dataset files already downloaded to `C:\Users\user\Music\Datathon\data\`.
Labels: **[CONFIRMED]** means an official 2026 source states it. **[2025 PRECEDENT]** means it comes from the 2025 edition's rules and was not restated for 2026. **[UNCONFIRMED]** means I could not verify it.

---

## 0. Headline facts (read first)

| Item | Finding | Source |
|---|---|---|
| Competition day | **2026-10-24 (TODAY)**, Male', 09:00 to 22:00 [CONFIRMED] | https://www.datathon.stats.gov.mv/ |
| Format | Prep phase (webinars/workshops), then an in-person **10-hour** hacking day in Male'. Teams may also take part virtually. [CONFIRMED] | https://www.datathon.stats.gov.mv/faq |
| Team size | **3 to 5 members** [CONFIRMED] | https://www.datathon.stats.gov.mv/faq |
| Registration | Closed **27 September 2026** [CONFIRMED] | https://www.datathon.stats.gov.mv/faq |
| Prize pool | **60,000 on winning the competition, plus 40,000 after delivering the advancement per MBS requirements.** The site gives no currency; MVR is likely. This implies the winner is expected to keep developing the solution for MBS afterwards. | https://www.datathon.stats.gov.mv/ |
| Judging criteria for 2026 | **Not published.** The Judges page says "Judges will be announced soon." [UNCONFIRMED] | https://www.datathon.stats.gov.mv/judges |
| Mentors for 2026 | **Not published.** The page says "Mentors will be announced soon." | https://www.datathon.stats.gov.mv/mentors |
| Submission portal/format for 2026 | **Not published anywhere online.** Expect instructions on the day. [UNCONFIRMED] | Checked all pages of https://www.datathon.stats.gov.mv/ |
| Data warning | **The MTCC dataset is synthetic.** Its README sheet says "all passenger figures are randomly generated and are not actual MTCC / RTL data." | `data\MTCC\MTCC.xlsx`, README sheet (from https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases/tag/v1.0) |

---

## 1. Theme, problem statement, scope, expected outputs

**Theme:** "Mapping Mobility through Data: Innovating Transport Insights for a Connected Maldives." [CONFIRMED] Source: https://www.datathon.stats.gov.mv/

**There are no separate tracks.** The site and the official presentation list one theme with a broad scope. (The 2024/25 edition had a Youth track for ages 15 to 24 and an Open track. No 2026 page mentions tracks.) Sources: https://www.datathon.stats.gov.mv/about and https://statisticsmaldives.gov.mv/maldives-datathon/

**Key objective** (official presentation, slide 3): "to develop and showcase data-driven, tech-enabled solutions that strengthen transport data systems through innovative methods, enhancing transport planning, monitoring, and sustainability."
Source: Datathon 2026 Presentation PDF, https://www.datathon.stats.gov.mv/storage/resources/01M4VH26KZH0TTS6EDVSMF3PZQ.pdf (linked from https://www.datathon.stats.gov.mv/resources)

**Purpose / problem statement** (presentation slide 4, FAQ):
- Strengthen transport statistics by finding new ways to improve the **quality, accessibility and utility of transport data**.
- "In the Greater Malé area transport related data is often fragmented, siloed, or outdated, limiting the ability of planners and decision makers to respond effectively to congestion, emissions, and infrastructure needs."
- The FAQ adds that MBS wants to modernise national statistics using GIS, big data, real-time analytics and visualisation.

**Focus of the event** (slide 5): partnerships with the research and technical community; use of official statistics by young people and to support policy; smart cities, sustainable transport and climate resilience; **integrating GIS into national statistical systems**; **"big data for statistics"**; collaboration between statisticians, geospatial experts and technologists.

**Scope ("includes, but is not limited to")** (slides 6 to 8, and the FAQ):
- Earth Observation and satellite data to map and monitor transport infrastructure and activity
- ML/AI/computer vision on imagery and transport datasets
- Movement patterns across **road, marine and pedestrian** systems
- **Inter-island transport flows** and connectivity challenges
- Participatory mapping and mobile-based data collection
- OpenStreetMap and other open data to fill gaps
- **Dashboards, interactive maps or data portals for policymakers**
- Accessible tools for planning, investment and emergency response
- Modelling traffic flows and marine transport patterns to **forecast demand or congestion**
- Suggesting better routes or interventions from historical and real-time data
- Strategies to **reduce the carbon footprint** of urban mobility
- Open-data innovation in the statistical community
- The FAQ adds that solutions should also be applicable outside the study area, which suggests scalability or replicability matters.

**SDG framing in the deck** (slides 10 to 12), which judges may reward:
- SDG 3.6.1 (road traffic deaths)
- SDG 9.1.1 (rural population within 2 km of an all-season road)
- **SDG 9.1.2 (passenger and freight volumes by mode)**
- **SDG 11.2.1 (convenient access to public transport by sex, age and disability)**
- SDG 7, 13 and 8 linkages
- The deck also links the NSDS: https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2021/11/NSDS-Maldives.pdf

**Call to action** (slide 16): "A connected nation starts with understanding how its people move… Data gives us the visibility; our solution gives policy makers and operators the leverage to act on it." Closing line: "Better Data, Better Lives!"

**Expected deliverable type:**
- The About page says participants will create "interactive dashboards, data visualizations, and analytical tools that offer actionable insights." That text appears to be carried over from 2025. Source: https://www.datathon.stats.gov.mv/about
- The scope list explicitly names dashboards, interactive maps, data portals, forecasting models and route or intervention proposals.
- **The exact 2026 submission package (slides, code repo, report) is not stated online. [UNCONFIRMED]**
- 2025 precedent: submissions were "[e.g., reports, presentations, code repositories]" (placeholder text), code had to be "well-documented and understandable", and each team got a **7-minute presentation plus 5-minute Q&A**. Source: https://statisticsmaldives.gov.mv/maldives-datathon/
- The safest plan is a live dashboard or map, a short slide deck, and a documented code repo.

---

## 2. Judging, rules, timeline, submission

### Judging criteria
- **2026: not published. [UNCONFIRMED]** The Judges page says "Judges will be announced soon." Source: https://www.datathon.stats.gov.mv/judges
- **[2025 PRECEDENT]** Five criteria, each scored 1 to 5 and weighted **20%** (25 raw points, 100 weighted). Source: https://statisticsmaldives.gov.mv/maldives-datathon/

| # | Criterion (2025) | Weight |
|---|---|---|
| 1 | Relevance for Specific Policy Use | 20% |
| 2 | Technical Execution (also called "Methodological Soundness" on the same page) | 20% |
| 3 | Communication and Presentation | 20% |
| 4 | Innovative Approach | 20% |
| 5 | Replicability and Scalability | 20% |

- The 2025 rules also summarise judging as "relevance, data use, innovation, execution, clarity, impact." That page has internal inconsistencies: a 1 to 10 band for Technical Execution, and a sample weighting that sums to 84. Source: https://statisticsmaldives.gov.mv/maldives-datathon/
- The 2026 FAQ's line about applying solutions outside the study area matches the 2025 "Replicability and Scalability" criterion, so the rubric is probably similar. **This is an inference, not confirmed.**

### Rules
| Rule | 2026 status | 2025 precedent |
|---|---|---|
| Team size | 3 to 5 [CONFIRMED, FAQ] | 3 to 5; members can change up to 24 hours before the start |
| In-person or virtual | Both allowed [CONFIRMED, FAQ] | Virtual teams need a stable connection |
| Eligibility | Not stated. About page: "You don't need to be an expert" | Maldivians and foreign residents. Youth track 15 to 24, Open track any age |
| External data | **Effectively encouraged.** The deck lists international open sources (UNCTAD TnT, ICAO country-pair, Transport Data Commons, data.transportation.gov, awesome-public-datasets, OSM/Overpass) and the scope names EO/satellite and OSM. No explicit 2026 rule found. | "Teams may use public datasets or gather new data, with proper citation." Private or IP-restricted data is prohibited. |
| IP / licensing | Not stated for 2026. **The 40,000 "advancement" tranche suggests MBS expects the winning solution to be developed further for MBS. Terms unconfirmed.** | "Rights to final products belong to the respective teams." Teams bring their own equipment and licences. |
| Conduct | The Code of Conduct link on the site points to "#" (no page) | Professional conduct required. Disqualification for rule breaches or missing the final presentation. |

Sources: https://www.datathon.stats.gov.mv/faq, https://www.datathon.stats.gov.mv/about, the presentation PDF (slide 14), and https://statisticsmaldives.gov.mv/maldives-datathon/

### Timeline
| Date | Event | Source |
|---|---|---|
| (pre-Oct) | "Datathon 2026 - Pre Information Session" (heading only, no date or recording link) | https://www.datathon.stats.gov.mv/resources |
| 2026-09-27 | Registration closed | https://www.datathon.stats.gov.mv/faq |
| 2026-09-27 | MACL file is dated 27092026 (filename) | `data\MACL\MACL\Airport traffic_Dataset_27092026.csv` |
| 2026-10-14 | Dataset repo created; release v1.0 published with MACL and FollowMe | https://github.com/mbs-datathon/maldives-datathon-2026-datasets/commits/main and https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases |
| 2026-10-21 | Avas Ride, MTCC and Team Kandu shared datasets added | https://github.com/mbs-datathon/maldives-datathon-2026-datasets/commits/main |
| **2026-10-24** | **Competition day, 09:00 to 22:00, Male' (10 hours of hacking)** | https://www.datathon.stats.gov.mv/ and /faq |
| Submission deadline | **Not published. [UNCONFIRMED]** In 2025 work had to be submitted by the end of the event, with presentations to judges. | https://statisticsmaldives.gov.mv/maldives-datathon/ |

### Submission format and location
- **Not published online. [UNCONFIRMED]** There is no submission portal on the site, and the GitHub repo is for data distribution only (0 issues, no discussions). Ask the organisers on the day.
- Contact: info@stats.gov.mv, +960 3008400, Maldives Bureau of Statistics, Dar Al Eiman Building, Majeedhee Magu, 20345, Male'. Source: https://www.datathon.stats.gov.mv/contact

---

## 3. Dataset documentation

Repo: https://github.com/mbs-datathon/maldives-datathon-2026-datasets
- The release notes for v1.0 only name the four zips. There are no data dictionaries in the release notes, and no issues or discussions exist. Sources: https://github.com/mbs-datathon/maldives-datathon-2026-datasets/releases/tag/v1.0 and https://github.com/mbs-datathon/maldives-datathon-2026-datasets/issues
- Documentation ships **inside the zips**. I read it from the local copies.
- The README lists these sizes: MACL 3.25 MB, FollowMe 440.04 MB, Avas Ride 12.79 MB, MTCC 53 KB.

The presentation (slide 13) lists "Transport Data Sources from Maldives" as a guide: Followme App, Avas App, Maldives Police Services camera data, MTCC Bus Passenger data, MTCC Ferry Passenger data, MACL Flight Passenger data, MPL Vessel data, and the Statistical Yearbook transport chapter. **Only FollowMe, Avas, MTCC and MACL were released.** Police camera and MPL vessel data were not released. Resources also link the yearbook: https://statisticsmaldives.gov.mv/yearbook/2026/

### MACL: `MACL\MACL\Airport traffic_Dataset_27092026.csv` plus `Metadata.csv`
- **What's in it:** flight-level passenger records. My local profile counted 168,959 rows, with departure dates from 2012-01-01 to 2026-07-31. Flight types are SCHEDULED (167,151) and CHARTER (1,808).
- **Columns (from Metadata.csv):**
  - Identity and schedule: record_id, flight_type, dep_date, arrival_date
  - Anonymised codes: carrier_code (e.g. "Carrier_008"), route_code ("Route_0175"), aircraft_type_code ("Type_014")
  - region (destination region), aircraft_category (Narrowbody/Widebody)
  - Passenger counts: arr / transit / dep, each split into adults / children / infants
  - ata and atd (HH:MM)
- **Regions:** South Asia, Middle East, Southeast Asia, Europe, East Asia, Central Asia & CIS, Africa, Other. This looks like **international traffic at Velana International Airport only**; no domestic or seaplane rows are evident.
- **Interpretation [UNCONFIRMED]:**
  - Each row has both arrival and departure passengers plus ata and atd. That suggests one row is a **turnaround** (arrival plus departure of the same aircraft).
  - About 16.1k rows in 2025, times 2, is about 32k movements. MACL reported 34,868 international flights in 2025 (https://edition.mv/business/47702, https://hoteliermaldives.com/maldives-main-airport-records-7-increase-in-passenger-traffic-in-2025/). The slide 9 key indicator is 34,786.
  - Dates are M/D/YYYY in the CSV, although the metadata says YYYY-MM-DD.
  - 2020 shows the COVID drop (4,463 rows).

### FollowMe: `FollowMe\FollowMe_august_2025\1.csv … 31.csv` plus `Summary of the available data.txt`
- **What's in it:** raw GPS pings from tracking devices for **August 2025**, one file per day. About 1.8 GB unzipped.
- **Data dictionary (verbatim from the bundled txt):**
  - poll_id: unique database row id
  - imei: tracking device IMEI/serial
  - timestamp: time saved in the database
  - device_date: time the device collected the reading
  - latitude, longitude
  - **speed: "Speed of the boat"**
  - heading: heading/bearing
  - **network: 1 = Dhiraagu, 2 = Ooredoo**
  - cellid: mobile cell id
  - gsm_level: signal level
- The same schema is shown as a sample on presentation slide 13.
- **Interpretation:**
  - The dictionary says "Speed of the boat", and FollowMe markets itself mainly as a vessel tracker, so most devices are probably **boats (inter-island marine traffic)**. FollowMe also tracks vehicles, so expect a mix.
  - Speed units are not documented (likely km/h or knots). [UNCONFIRMED]
  - device_date can be rounded or stale compared with timestamp (sample: device_date 00:00:00 vs timestamp 00:00:26).
  - Speed 0 with heading 0 rows are likely parked or idle devices.

### Avas Ride: `Avas_Ride\avas_rides_aug_sep_2026.csv` plus `car_fare_matrix.csv`
- **What's in it:** ride requests from **2026-08-01 to 2026-09-30**, 371,788 rows. There is no bundled dictionary.
- **Columns:** date_started, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, distance_km, time_sec, status.
- **Status values:** payment_completed (320,140), ride_expired (27,247), ride_completed (24,401). "ride_expired" is probably an unmatched request, which is useful as a **demand-supply gap** signal. [UNCONFIRMED]
- **car_fare_matrix.csv:** zone-to-zone car fares for "Male City", with zones Male, Hulhumale Phase 1, Velana International Airport, Hulhumale Phase 2, Sea Plane and Domestic Terminal. Example: Male to Hulhumale Phase 2 is 100.0, and an intra-zone trip is 30.0. Currency is presumably MVR. [UNCONFIRMED]

### MTCC: `MTCC\MTCC.xlsx` (sheets README, bus_monthly, bus_daily, ferry_monthly)
- **bus_monthly:** Jan 2023 to Dec 2025, Greater Male' routes. Examples: R1 Hulhumale Ph1 to Male (West Park), R2 Hulhumale Ph1 to Male (Carnival), R3 Male (West Park) to Velana Airport, R4 Hulhumale Ph1 to Velana Airport. Columns are paid_pax, foc_pax and total_pax. FOC means free of charge: people over 65, persons with disabilities and infants.
- **bus_daily:** calendar 2025 for R1, R2 and R4. The README notes "Fridays are low-demand days."
- **ferry_monthly:** RTL zone, atoll, route_id and passengers (no FOC). Example: RTL Zone 01, Haa Alifu, routes H1, S1C1 and so on.
- **CRITICAL, from the README sheet:** "Route names and codes are real; **all passenger figures are randomly generated and are not actual MTCC / RTL data.**"
  - Only a subset of routes is included.
  - Built-in patterns: seasonality, slow growth, Friday dip, ferry zones that start at different dates (Zone 05 from Jul 2023, Noonu from Jul 2024), occasional disruption dips.
  - **Do not present MTCC figures as real findings.** Use them only for method or prototype demos, and say so.

### Team-shared datasets
- `team-shared-datasets/Team_Kandu.zip` has 14 CSVs, added 2026-10-21. The folder README says only "additional datasets shared by participating teams… Please review any accompanying documentation."
- Local extract (`data\team-kandu\`): rtl_bus_routes/stops/departures, rtl_routes/stops/trips/connections/unscheduled, odi_connections, maldivian_destinations, mma_series, observations, parse_log, qa_flags. These look like a parsed RTL timetable plus some other series.
- Provenance and accuracy are **unverified** (made by a team, not by MBS).
- Source: https://github.com/mbs-datathon/maldives-datathon-2026-datasets/tree/main/team-shared-datasets

---

## 4. Organiser guidance, FAQs, webinars, mentors, prizes

- **FAQ (4 entries):** what a datathon is; purpose; scope; structure (prep webinars and workshops, then the in-person event; teams of 3 to 5; in-person or virtual; registration closes 27 Sep 2026; 10-hour competition on 24 Oct 2026). Source: https://www.datathon.stats.gov.mv/faq
- **Resources:**
  1. "Datathon 2026 - Pre Information Session" (heading only; no recording or slides linked)
  2. the Datathon 2026 Presentation PDF (17 slides, summarised above)
  3. the 2026 Statistical Yearbook, Geography and Transport: https://statisticsmaldives.gov.mv/yearbook/2026/
  - Source: https://www.datathon.stats.gov.mv/resources
- **Suggested reading in the deck (slide 15):**
  - ITF-OECD "Big Data and Transport": https://www.itf-oecd.org/sites/default/files/docs/15cpb_bigdata_0.pdf
  - Urbano et al. 2025: https://www.sciencedirect.com/science/article/pii/S2210539525000136
  - Beeharry et al.: https://www.researchgate.net/publication/317368854
  - Iliashenko et al. 2021: https://www.researchgate.net/publication/349744184
- **Key indicators in the deck (slide 9):**
  - International flight movements 2025: 34,786
  - Domestic flight movements 2025: 214,237 (likely includes seaplanes)
  - VIA passenger arrivals 2025: 2,699,225
  - Registered vehicles 2024: 16,153 (this figure looks low for the Maldives; verify against the yearbook) [UNCONFIRMED]
- **Mentors and judges (2026):** "will be announced soon." Sources: https://www.datathon.stats.gov.mv/mentors and https://www.datathon.stats.gov.mv/judges
- **Prizes:** 60,000 on winning and 40,000 after delivering the advancement per MBS requirements (no currency stated). Source: https://www.datathon.stats.gov.mv/
  - Precedent: the 2024/25 edition awarded MVR 80,000 to one best solution. Source: https://statisticsmaldives.gov.mv/maldives-datathon/
- **Past winner (2025, "Shaping the future of work"):** SQL no Jutsu, "Education Improved with Data". 7 teams took part. 2025 partners were Women in Tech, MPAO, Dhiraagu, UNFPA and ILO. Source: https://www.datathon.stats.gov.mv/honours
- **Webinars:** the FAQ mentions a prep phase of webinars and workshops, but no recordings or dates are posted. [UNCONFIRMED]

---

## 5. Data providers: who they are and what the data means

### MACL: Maldives Airports Company Limited
- 100% government-owned. Operator and developer of **Velana International Airport (VIA)** in Hulhulé, next to Male'. Founded 1966.
- Facilities: a 3,400 m runway, the **Noovilu Seaplane Terminal** ("world's largest seaplane hub"), cargo facilities, and regional aerodromes (not named on the homepage).
- Source: https://www.macl.aero/
- 2025 traffic as reported by MACL:
  - 8.28M passengers in total: 5.38M international, 1.17M domestic, 1.73M seaplane
  - 249,214 air traffic movements: 34,868 international, 28,348 domestic, 185,998 seaplane
  - Sources: https://edition.mv/business/47702 and https://hoteliermaldives.com/maldives-main-airport-records-7-increase-in-passenger-traffic-in-2025/
- **Interpretation:** the MACL dataset covers international flights at VIA (tourist and expatriate gateway flows by origin region). Seaplane and domestic movements dominate total movements, but they **are not** in the released file.

### MTCC: Maldives Transport and Contracting Company PLC
- Listed public company, incorporated around 1980/81. **Government owns about 64.2%.**
  - Sources: https://finance.gov.mv/public-enterprises and https://edition.mv/mtcc/19095
  - SOE Gateway shows a conflicting 48%: https://soegateway.finance.gov.mv/soe/mtcc
- Largest civil and marine contractor in the country. Runs public transport by land and sea under the **RTL (Raajje Transport Link)** brand.
- Ferry services date from 2001 (Male' to Villingili). A 2021 agreement with the government created the nationwide RTL ferry network, organised in **zones by atoll**.
- MTCC took over the Greater Male' urban bus services (Male', Hulhumalé, airport) from Maldives Ports Limited in 2021.
- Sources: https://informinvestor.cmda.gov.mv/storage/uploads/NQoQd1qv/omqkkdtv.pdf (MTCC annual report, via search summary), https://edition.mv/news/267 (2016 ferry mandate) and https://raajje.mv/107333
- **Interpretation:**
  - Bus routes R1 to R4 link Male', Hulhumalé Phase 1 and VIA across the Sinamalé Bridge and Hulhulé.
  - Ferry routes connect islands within atoll zones.
  - The FOC share (over 65, PWD, infants) links to **SDG 11.2.1** (inclusive access).
  - **The released numbers are synthetic** (see section 3).

### FollowMe: FollowMe Maldives Pvt Ltd
- Maldivian real-time GPS tracking service: "Your Instant Tracking Solution… Start Monitoring your Vessels & Vehicles." It offers personal and asset tracking, iOS and Android apps, a Developer API and TV portals for boats and vehicles. Device models T711 and T366 appear on the site.
- Source: https://followme.mv
- The app store listing ("FollowMe Vessel Tracker") gives location updates up to every 10 seconds, with developer FollowMe Maldives Pvt Ltd. Source (third party): https://justuseapp.com/en/app/1225632920/followme-vessel-tracker/contact
- **Interpretation:**
  - The dataset is GPS telemetry from privately owned tracker devices, mainly on **boats** (speedboats, dhonis, launches) plus some vehicles.
  - It is good for mapping inter-island marine routes, vessel speeds, harbour dwell times and connectivity.
  - It covers only FollowMe subscribers, so it is a sample and not the full fleet.
  - SIMs on Dhiraagu or Ooredoo cell networks mean coverage gaps at sea are likely.

### Avas Ride / Avas App: AVAS Enterprises Private Limited
- Ride-hailing app linking riders with taxis, private cars, luxury cars and vans in **Male' and Hulhumalé**. Riders book immediately or in advance; the app has a wallet and live driver tracking.
- Source: App Store listing https://apps.apple.com/us/app/-/id1447876849 (seller AVAS ENTERPRISES PRIVATE LIMITED, avasride.com)
- Launched 2019 in Male'. Described as the largest taxi service provider in the Maldives, with about 2,500 vehicles listed. Rebranded to **Avas App** in April 2024, adding motorcycles, pickups and a payment gateway. Source: https://adhadhu.com/article/52267 (8 Apr 2024)
- **Interpretation:**
  - Ride origin-destination pairs within Greater Male' (Male', Hulhumalé Ph1/Ph2, VIA, seaplane and domestic terminals).
  - Useful for road OD flows, peak hours, trip lengths and speeds (distance_km / time_sec) as a congestion proxy, unmet demand ("ride_expired") and comparison with the RTL bus routes.
  - Avas users are a sample of taxi or ride-hail demand only.

---

## 6. Items I could not confirm
1. 2026 judging criteria and weights (not published; the 2025 rubric is the best proxy).
2. 2026 submission format, portal and exact deadline time on 24 Oct.
3. 2026 rules on IP/licensing, external data, eligibility and code of conduct (the Code of Conduct link is a placeholder "#").
4. Prize currency (MVR assumed) and what "advancement per MBS requirements" involves.
5. Webinar recordings, the information session date or content, and mentor or judge names.
6. Units for FollowMe `speed`; the meaning of Avas `status` values and the fare-matrix currency; whether one MACL row equals one turnaround.
7. The "Registered vehicles 16,153 (2024)" key indicator on slide 9.
