# 13 — What the data can answer next, and where machine learning actually pays

Status: analysis note, 24 October 2026. Companion to `research/03_transport_network_and_methods.md`,
`research/11_economic_models.md` and `MULTIMODAL_DATA_READINESS_PLAN.md`.
Every number below is either cited to a note/source or reproducible with the commands in §8.

---

## 0. TL;DR

Five things the data already says, and five things worth doing next.

**What the data says**

1. **"72% reach a hospital" is not a property of the Maldives — it is a property of the clock.**
   Holding the network fixed and only moving the departure hour, the share of residents with a
   same-day journey swings by **19 pp for hospitals (66.4% at 18:00 → 85.4% at 05:00)** and
   **25 pp for emergency care (55.7% → 81.1%)**. Reporting one snapshot number throws away the
   finding that matters most for policy.
2. **Distance to Malé is the dominant demographic gradient.** Median island population change
   2014–2022 falls from **+19.8%** in the nearest distance quintile to **+2.7%** in the furthest;
   the regression coefficient on log distance is **−10.9 pp per log-km (t = −4.29, n = 162)**.
   Growth, not decline, is what remoteness predicts at island level.
3. **Our own blind spot is the fastest-growing part of the country.** 25 islands within 100 km of
   Malé have no modelled hospital journey at all — **29,462 residents, median growth +20.6%**.
   This is the missing RTL Zone 3 / Kaafu coverage, i.e. a *data* gap. Reading it as isolation
   inverts the result: with the gap included, "never reaches a hospital" islands appear to grow
   *faster* (13.6% vs 9.2%); with the gap removed the difference disappears (8.9% vs 9.2%).
4. **The grade-10 cliff shows up in youth labour outcomes.** Islands without same-day access to a
   school teaching grades 11–12 have **+5.6 pp higher NEET among 15–24-year-olds** (t = 2.05,
   n = 159), controlling for population size and distance. Correlational, but it is the first
   island-level link between the education finding and an economic outcome.
5. **Air is not the lever it looks like.** Turning the estimated air layer on moves the 08:00
   hospital figure by **+1.0 pp (322,715 → 327,354 residents)**. Air matters for a handful of
   islands and for specific services (emergency +7.1 pp), not for national coverage.

**What to do next**

| Priority | Action | Why now |
|---|---|---|
| 1 | Report access as a **distribution over the day**, not a snapshot | Already computable, changes the headline, no new data |
| 2 | Close the **Kaafu / Zone 3 coverage gap** | 29,462 residents in the model's blind spot, and the fastest-growing islands |
| 3 | Add **arrival-time reliability** (FIS delays/cancellations, ferry no-shows) as a first-class output | 28 cancellations and 14 delays already observable in 318 domestic flight records |
| 4 | Publish **per-island accessibility CSVs** so the analysis is reusable | `scripts/analysis/island_access_outcomes.py` now does this |
| 5 | Acquire **one demand dataset** (Aasandha island-level claims or HEMS transfer logs) | Everything about "smarter decisions" is blocked on demand, not on map layers |

**Where ML is worth the effort** (detail in §5): learning sea-link travel times from 110,074
observed vessel trips (M1), inferring origin–destination demand from 17.46M GPS rows (M2), and
forecasting airport activity from a 15-year monthly panel (M3). Everything else is better served
by optimisation or careful econometrics than by a model.

---

## 1. What we actually hold

Graded by *what decision it can support*, not by file count.

| Dataset | Volume | Granularity | Readiness | Honest limitation |
|---|---|---|---|---|
| `data/processed/multimodal/multimodal.json` | 200 islands, 117 stops, 20 airports, 166 services, 945 facilities, 48 categories | node/edge | **Ready** | island-level facility locations; no calendars; air frequencies estimated |
| Census 2022 (`data/external/mbs-census-2022/xlsx/`) | 75 tables incl. **MG4 21×21 atoll OD matrix**, P3 island population 2014→2022, ED17 studying-by-age-by-island, EC3 labour force by island, per-island indicator sheets | island / atoll | **Ready** | provisional; 2022 vintage |
| `data/team-kandu/observations.csv` | 9,196 rows, 10 metrics | island × month | **Ready** | heterogeneous coverage per metric |
| ↳ `aircraft_movements` | **2,410 rows, 19 airports, monthly 2011-01 → 2025-12** | airport × month | **Ready** | real panel; spelling variants (`Kulhudhufushi` vs `Kuludhufushi`) |
| ↳ `passengers` | 3,678 rows, 21 airports, monthly 2015 → 2025 | airport × month | **Ready** | some airports start late |
| ↳ `registered_population` | 600 rows, 202 islands, 2023/2024/2025 | island × year | **Ready** | registration ≠ residence |
| `data/external/_derived/mdv_islands_master.csv` | 1,556 islands × 57 cols | island | **Ready** | joins already reviewed |
| FollowMe GPS | **17,462,749 rows × 11 cols, 1,776 devices, 31 days, 1.8 GB** | device × timestamp | **Ready (heavy)** | no nulls; `speed` is in **knots** (undocumented, geometrically verified); `device_date` is the authoritative clock, `timestamp` drifts to 2026-10 in 0.85% of rows; timezone unverified |
| ↳ `data/processed/followme/fm_trips.parquet` | **110,074 trips × 32 cols, 1,655 devices** | device × trip | **Ready** | duration p50 16.1 min, 7.0 km, detour p50 1.09; only **18.0%** of trips have both endpoints within 1 km of an RTL stop |
| Avas Ride | **371,788 rides × 8 cols**, 2026-08-01 → 09-30 | ride | **Ready (thin, urban)** | Greater Malé only; times are routing-engine estimates (constant ~38 km/h, 300 s floor); every OD pair is unique → must bin to ~1.1 km (19×19, 272 cells) |
| MACL traffic | **168,959 rows**, 2012-01 → 2026-07 (175 months) | aircraft movement at Velana | **Ready (MLE only)** | dates are **MM/DD/YYYY** despite ISO metadata; carriers/routes pseudonymised; **no seat capacity**; excludes all domestic airports |
| Velana FIS arrivals/departures | **963 rows, 12 dates, 318 domestic** | flight | **Ready (thin)** | 12 scraped dates, not a continuous feed |
| `data/external/air/domestic_routes.csv` | 40 routes | route | **Estimated** | every row carries `estimated=yes` |
| RTL network (`data/team-kandu/rtl_*.csv`) | 49 routes, 149 stops, 390 stop-times | stop/route | **Partial** | no calendars; Zone 3 absent; no GTFS exists for the Maldives |
| MTCC (`data/MTCC/MTCC.xlsx`) | 4 sheets, 2023-01 → 2025-12 | route × month | **Join key only** | README verbatim: *"Route names and codes are real; all passenger figures are randomly generated and are not actual MTCC / RTL data."* |
| Aasandha / HIES / budget | PDFs + derived CSVs | national / programme | **Context only** | no island-level claims; annual totals only |
| HeiGIT HDX baseline | adm0/adm1/adm2 | polygon | **Comparison only** | isochrones cannot leave the home island |

**The structural gap.** The network tells us what is *possible*; nothing in the repo tells us what
people *actually do*. There is no island-level origin–destination demand, no ridership, no
referral flow, no vehicle capacity. Every proposal below is therefore split into
"descriptive, ready now" and "needs demand data".

### 1.1 Data traps — read before modelling anything

Every one of these was found by inspection, and each silently produces plausible-looking wrong
answers. They belong in the repo, not just in someone's head.

| Trap | File | What is actually true |
|---|---|---|
| **Dates are US format** | `data/MACL/MACL/Airport traffic_Dataset_27092026.csv` | `dep_date` is **MM/DD/YYYY** although `Metadata.csv` claims ISO. Parsing as ISO silently scatters 102,304 of 168,959 rows across the wrong months. |
| **Speed is knots** | `data/FollowMe/FollowMe_august_2025/*.csv` | Undocumented. Verified geometrically (implied km/h ÷ reported = 1.925 over 2.0 M fix pairs, vs 1.852 for knots). Reading it as km/h makes every vessel 1.85× too fast. |
| **Two clocks** | same | `device_date` is authoritative (0 rows outside August); `timestamp` drifts to 2026-10-08 in 0.847% of rows. Median gap 2 s. |
| **Timezone unverified** | same | Diurnal minimum lands at 19:00–23:00 and peak at 02:00–12:00 — implausible as local time, consistent with UTC (local = UTC+5). Confirm before any hour-of-day feature. |
| **Duplicate device-timestamps** | same | 158,086 duplicate `(imei, timestamp)` pairs (0.905%) despite zero duplicate rows. Dedupe before segmentation. |
| **Ride times are engine estimates** | `data/Avas_Ride/avas_rides_aug_sep_2026.csv` | Implied speed is 38.1 km/h with SD ≈ 3, flat across all hours (36.7–39.1) and across statuses; `time_sec` has a hard 300 s floor. Expired rides are statistically identical to completed ones. There is **no** congestion or travel-time signal here. |
| **Every OD pair is unique** | same | 371,788 rides, 371,788 distinct coordinate pairs. Any OD matrix must be binned (~1.1 km → 19×19, 272 cells, top-50 = 82.5% of rides). |
| **Passenger counts are synthetic** | `data/MTCC/MTCC.xlsx` | Stated in the workbook's own README sheet. Route names, zones and atolls are real; every `paid_pax`/`foc_pax`/`total_pax`/`passengers` value is generated. The Friday −39% dip is an artefact of that generator. |
| **Carriers and routes are pseudonymised** | MACL | `carrier_code`, `route_code`, `aircraft_type_code` are `Carrier_###`/`Route_####`/`Type_###`. Only `region` (8 values) and `aircraft_category` (3 values) are real. No airport codes, no seat capacity, no load factor. |
| **GPS sample ≠ population** | FollowMe | 1,776 devices against 447,420 residents ≈ 0.4%, non-random (smartphone, telecom subscriber, urban-skewed). Usable for relative pattern and edge calibration; never as a population count. |
| **Stop labels cover 18%** | `data/processed/followme/fm_trips.parquet` | Only 19,856 of 110,074 trips have both endpoints within 1 km of an RTL stop. `o_km` p50 is 65.3 km. Route-OD learning is limited by the catalogue, not by the GPS. |

---

## 2. Findings available now

### 2.1 Access is a function of the clock

Same network, same day, only the departure hour changes (air on, share of 447,420 residents with a
same-day journey):

| Service | 05:00 | 08:00 | 12:00 | 18:00 | Swing |
|---|---|---|---|---|---|
| Emergency care | 81.1% | 70.5% | 63.1% | 55.7% | **25.4 pp** |
| Regional/tertiary hospital | 80.4% | 70.1% | 66.4% | 58.0% | 22.5 pp |
| MRI | 80.4% | 74.4% | 64.3% | 54.6% | 25.8 pp |
| Hospital (tier 1–3) | 85.4% | 73.2% | 71.3% | 66.4% | 19.1 pp |
| Grade 11–12 school | 89.1% | 81.8% | 80.0% | 72.4% | 16.7 pp |

Why: **28 of the 102 ferry trips have already departed by 08:00**, so a fixed 08:00 departure
measures the timetable, not the network. Report the curve, and report the *worst* hour as the
service guarantee. This is free — no new data, one chart.

### 2.2 Distance is the demographic gradient

Median island population change 2014–2022 by distance-to-Malé quintile:

| Quintile | Islands | 2022 population | Median growth |
|---|---|---|---|
| Q1 nearest | 38 | 249,130 | **+19.8%** |
| Q2 | 37 | 38,016 | +11.7% |
| Q3 | 37 | 36,855 | +13.6% |
| Q4 | 37 | 48,972 | +6.3% |
| Q5 furthest | 38 | 69,669 | **+2.7%** |

OLS on 162 islands (excluding the coverage gap, §2.3), `growth ~ log(pop2014) + log(distance) +
no_same_day_hospital + atoll_capital`: **log distance = −10.9 pp, se 2.54, t = −4.29, R² = 0.120**.
The accessibility dummy is *not* significant once distance is in (−0.73 pp, t = −0.15), nor is the
atoll-capital dummy (+7.4 pp, t = 1.04) — a warning that raw access indicators proxy for geography
unless the network adds information beyond it.

### 2.3 The blind spot is the boom zone

25 islands inside 100 km of Malé have no modelled hospital journey: **29,462 residents, median
growth +20.6%** — the fastest-growing group in the country (Maafushi +47.8%, Thulusdhoo +27.9%,
Huraa +27.2%, Thoddoo +25.4%). These are guesthouse islands served by scheduled speedboats and
local ferries that are not in the RTL extract (Zone 3 / Kaafu).

| Sample | "Never reaches hospital" | "Same day" |
|---|---|---|
| All islands | 69 islands, 65,143 people, **+13.6%** growth | 122 islands, 382,277 people, +9.2% |
| Excluding coverage gap | 44 islands, 35,681 people, **+8.9%** | 122 islands, 382,277 people, +9.2% |

The first row is a data artefact that reads as a finding. The second row says access does not
predict growth *conditional on distance* — which is the honest answer and the one to report.

### 2.4 Education cliff → youth labour market

`NEET 15–24 ~ log(pop) + log(distance) + no_same_day_hospital + no_same_day_grade_11_12`
on 159 islands: **no grade 11–12 access = +5.6 pp NEET** (se 2.75, t = 2.05); log distance
= +3.9 pp per log-km (t = 2.42). Direction matches the mechanism in `research/06_education_data.md`
— a student who cannot continue at grade 11 either leaves (out-migration) or stops (NEET).
Treat as suggestive; NEET is measured in 2022 on the same islands, so reverse causality is live.

### 2.5 Air is narrow, not broad

08:00, air off → on: hospital **+4,639 residents (+1.0 pp)**; emergency **+31,973 (+7.1 pp)**;
grade 11–12 **+2,798 (+0.6 pp)**. Air is a service-specific lever (emergency, dialysis, oncology),
not a coverage lever. The "estimated air" toggle should stay visibly flagged, and the pitch should
not claim air transforms national coverage.

### 2.6 Reliability is measurable today

The Velana FIS extract holds **318 domestic flight records across 12 dates**, all with both
scheduled and estimated times: 28 cancelled, 14 delayed, 825 on-time, and 45/37 landed/departed.
That is not enough to train a delay model — but it *is* enough to fit the distributions that a
reliability scenario needs (a cancellation probability of roughly 1-in-11 legs in the sample, with
wide uncertainty given 12 days). Pair it with the "28 of 102 trips gone by 08:00" structure and
reliability becomes a first-class output instead of a caveat.

---

## 3. The demand hole

Everything a planner wants next is blocked on the same missing object:

> "If we add/move/upgrade service X, how many people use it, what does it cost, and who benefits?"

Currently answerable: *who becomes reachable* (population-weighted, by mode, by hour).
Not answerable: *how many will travel*, *at what fare*, *with what load*, *and whether the ferry
has space*. `MULTIMODAL_DATA_READINESS_PLAN.md` already names the missing inputs: real OD data,
vehicle capacities, fleet assignments, turnaround constraints, observed delays.

The cheapest path to a demand proxy is not a new map layer — it is **Aasandha's island-level
claim and transfer records** (which already exist inside the annual reports as aggregates:
4,426 emergency evacuations and 15,535 patients treated abroad in 2024) or **HEMS transfer logs**.
One island-level referral table would unlock §5 M6, cost-benefit work in
`research/11_economic_models.md`, and a defensible demand model.

---

## 4. Data to acquire next, ranked

| # | Data | Decision it unlocks | Effort | Note |
|---|---|---|---|---|
| 1 | **RTL Zone 3 / Kaafu + Vaavu timetables** (published PDFs, board photos, operator email) | Fixes the blind spot affecting 29,462 residents | Low | Highest value per hour of work |
| 2 | **Service calendars** (weekday/Friday/holiday exceptions) | Real reachability; today every trip is assumed to run | Medium | Without it, "weekday" and "Friday" numbers are guesses |
| 3 | **Aasandha island-level claims / HEMS transfer log** | Demand, cost, equity — the whole decision layer | High (FOI) | Even a one-year extract is transformative |
| 4 | **Ferry & flight capacity (seats, fleet, turnaround)** | Load, queueing, "is the boat full?" | Medium | Operator request |
| 5 | **Sea state / wave height by month** | Weather-adjusted reliability for small vessels | Low | MMS or ERA5 reanalysis; makes "sea route fails in monsoon" testable |
| 6 | **Facility coordinates + opening hours** | Sub-island access; the model is island-level today | Medium | Only where a registry actually publishes them |
| 7 | **RTL in-service speed calibration** (2–3 app timetables vs GPS) | Removes a silent assumption in every edge | Low | Compare against FollowMe vessel tracks |

Items 1, 2, 5 and 7 are cheap and each removes a documented assumption. Item 3 is expensive and
the only one that changes what questions can be asked.

---

## 5. Where ML pays — and where it doesn't

Ranked by *decision value ÷ feasibility*. Each card states the decision, the target, the labels we
actually hold, the baseline to beat, and the way this fails.

### M1 — Learn sea-link travel times where no timetable exists  ★ highest value
- **Decision:** is this island connected in practice, and how long does the crossing really take?
- **Labels:** **110,074 vessel trips in Aug 2025 from 1,655 vessels** (median 16.1 min, 7.0 km; detour
  ratio median 1.09, p95 1.83) — observed, not modelled. Derived from 17,462,749 raw pings.
- **Target:** trip duration / effective speed as a function of great-circle distance, vessel class,
  time of day, month.
- **Features:** distance, detour geometry, vessel type, hour, monsoon month, operator.
- **Model:** gradient-boosted regression with a per-vessel random effect; start with a
  distance-only linear baseline (`27.1 + 0.125·km` already exists in `research/07_air_network.md`
  for air — the sea equivalent does not).
- **Baseline to beat:** constant 25 kn ÷ 1.15 detour (the current assumption everywhere).
- **Why it pays:** every one of the 153 access edges and 49 sea routes inherits this number. A 10%
  error in effective speed moves the 60-minute population threshold more than adding the air layer
  did (+4,639).
- **Two binding limits, stated up front:** (1) only **18.0%** of trips touch an RTL stop, so the
  learnable subset is the dense corridors (Malé–Hulhumalé, Addu, Laamu) and the result must be
  extrapolated along distance, not claimed per route; (2) the fast/medium/slow classes are
  **self-defined from speed**, so there is no ground-truth vessel label — do not report a classifier.
- **How it fails:** trips are a biased sample of the *actual* network (only vessels carrying FollowMe
  devices); slow vessels are under-represented; no ground truth for the true OD; timezone of the
  hour-of-day feature is unverified.
- **Effort:** 2–3 days. **Readiness: high.**

### M2 — Infer demand: origin–destination trips from GPS  ★ highest ceiling
- **Decision:** where does travel actually go, and by which mode?
- **Labels:** none — unsupervised. **17,462,749 rows, 11 columns, 1,776 devices, 31 days, 1.8 GB.**
- **Pipeline:** dedupe 158,086 `(imei, timestamp)` pairs → stop detection (dwell clustering) → trip
  segmentation → OD assignment to island polygons → mode classification (land/sea/air) from speed
  and geometry.
- **Baseline to beat:** no demand estimate at all; for validation, compare inferred ferry legs
  against the 102 known trips and the RTL stop pairs in `rtl_connections.csv`.
- **Why it pays:** it is the only route from "reachable" to "used", and it would let the 2SFCA and
  p-median work in `research/11_economic_models.md` run on observed rather than assumed demand.
- **How it fails:** 1,776 devices over 447,420 residents ≈ 0.4% penetration, non-random
  (smartphone, Dhiraagu/Ooredoo subscriber, urban-skewed). Fine for *relative* patterns and for
  calibrating network edges; not a population estimate. Must be reported as a device panel, never
  as "the Maldives travels X times". Also: 7.34% of consecutive fixes imply >60 km/h and 0.186%
  imply >100 km/h, so a smoothing/outlier stage is mandatory before segmentation.
- **Effort:** 1–2 weeks. **Readiness: medium** (data present, labels absent).

### M3 — Forecast airport activity and route viability
- **Decision:** which domestic air links are sustainable; where to add frequency.
- **Two independent panels, both real and both underused:**
  - `data/team-kandu/observations.csv` — **2,410 airport-months of aircraft movements, 19 airports,
    2011-01 → 2025-12** (Velana/Gan/Hanimaadhoo 288 months each; Kaadedhdhoo and Kadhdhoo 168;
    Fuvahmulah 159; Dharavandhoo 147; down to Faresmaathoda at 22), plus 3,678 airport-months of
    passengers.
  - `data/MACL/MACL/Airport traffic_Dataset_27092026.csv` — **168,959 movements at Velana only,
    2012-01 → 2026-07 (175 months)**, with real `region` (8 values) and `aircraft_category`
    (widebody/narrowbody/turboprop) and passenger counts.
- **Target:** monthly movements/passengers per airport; then a route-level load proxy.
- **Model:** seasonal naive / ETS baseline, then gradient boosting on pooled panel with
  airport fixed effects and holiday/season features. Pooling is what makes 288 months per major
  airport usable.
- **Baseline to beat:** seasonal naive — this is the test that decides whether ML earns its place.
- **Why it pays:** directly supports the "16 planned airports" question and the estimated
  frequency table (all 40 routes are `estimated=yes`).
- **How it fails:** route level is not in either panel (MACL carriers/routes are pseudonymised);
  MACL is Velana-only and has **no seat capacity or load factor**, so "demand" means passengers
  carried, not demand; COVID is a structural break inside the series (2020-04: 19 movements vs
  1,266 in 2020-01); airport opening/closing creates zeros that are not demand zeros.
- **Effort:** 3–5 days. **Readiness: high.**

### M4 — Urban ride-demand forecasting (Malé / Hulhumalé only)
- **Decision:** where to stage vehicles, and how much capacity a corridor needs.
- **Labels:** **371,788 Avas rides, 2026-08-01 → 09-30 (61 days, no gaps)**, 6,095 rides/day,
  pickup/dropoff coordinates, `status` in {payment_completed 86.1%, ride_expired 7.3%,
  ride_completed 6.6%}.
- **Binnable signal:** at ~1.1 km the Greater Malé bbox resolves to **19×19 zones / 272 OD cells**,
  top-50 = 82.5% of rides. Hour peaks at 16:00–18:00, trough 02:00–04:00; Saturday highest,
  Friday lowest. 83.7% of rides cross the harbour.
- **Target:** rides per zone-hour; OD flow matrix.
- **Model:** Poisson/negative-binomial GLM with hour, weekday, zone fixed effects — then a boosted
  tree if it beats the GLM out of sample.
- **Baseline to beat:** historical zone-hour mean.
- **Why it pays:** it is the only *observed* behavioural dataset in the repo, and the only place
  where a real demand model can be validated end-to-end.
- **How it fails:** two months, no year; the road network only covers Malé/Hulhumalé (Addu, Laamu,
  Sinamalé); **no fare, no driver id, no wait time, no cancellation reason, no polyline**; and
  `distance_km`/`time_sec` are routing-engine estimates at booking (constant ~38 km/h, 300 s floor),
  so speed-based features are circular. It also says nothing about inter-island travel, which is
  the actual project question.
- **Effort:** 3–5 days. **Readiness: medium.** Value: demonstrative more than decisive.

### M5 — Fill the service matrix with uncertainty, not point estimates
- **Decision:** which "no service here" cells are real absences and which are unverified?
- **Labels:** 945 facilities × 48 categories, built from 1,405 intervention rows with 1,279
  evidence items. Roughly a quarter of specialist rows are tier-inferred.
- **Target:** P(service available | facility type, tier, atoll, population, nearest hospital).
- **Model:** hierarchical logistic / matrix completion with partial pooling by atoll and facility
  tier. Output a probability and an interval, not a yes/no.
- **Why it pays:** prevents the classic error of reading "absent from the registry" as "absent in
  reality" — the same error §2.3 catches at network level.
- **How it fails:** labels are the registry, so the model learns the registry's own gaps. Only
  useful if some cells are audited (the `reviewed` flag exists for exactly this).
- **Effort:** 2–3 days. **Readiness: medium.**

### M6 — Accessibility → outcome models for targeting (not prediction)
- **Decision:** which islands to prioritise, and what to expect if nothing changes.
- **Labels:** 191 islands; growth 2014–2022, NEET, unemployment, registered population 2023–2025.
- **Model:** regularised regression / causal-inference design (distance as instrument for access),
  never a black-box predictor on 191 rows.
- **Why it pays:** it converts the atlas from "here is a map" into "here is where the cost lands".
- **How it fails:** n = 191, endogeneity (access and population are jointly determined), and
  2022 outcomes coincide with the 2022 census inputs — leakage if features are not lagged.
- **Effort:** already prototyped (§8). **Readiness: high for description, low for prediction.**

### M7 — Timetable optimisation with a learned surrogate
- **Decision:** where to move a departure to gain the most reachability per hour of vessel time.
- **Method:** this is an optimisation problem first (p-median / MCLP already specified in
  `research/11_economic_models.md`), with ML only as a fast surrogate for the router so the search
  is cheap.
- **Why it pays:** §2.1 shows the swing is 19–25 pp; schedule is a lever the state already controls
  and costs no new infrastructure.
- **How it fails:** if the surrogate is trained on a biased 102-trip network, it will confidently
  optimise a wrong network.
- **Effort:** 1 week after M2. **Readiness: low-medium.**

### What not to do
- **Do not train on MTCC passenger counts.** The workbook says they are randomly generated.
- **Do not fit deep models on 191 islands.** Use regularisation and report uncertainty.
- **Do not present device-panel inferences as population estimates.** 1,776 devices ≠ 447,420 people.
- **Do not predict accessibility from accessibility.** The router already computes it exactly;
  ML belongs on the inputs (edge times, frequencies, reliability), not the output.
- **Do not use 2022 census values as features to predict 2022 outcomes.** Lag everything or use
  the 2014 panel.

### Validation protocol (applies to all of the above)
1. Always report a naive baseline (seasonal naive for time series, distance-only for edges,
   HeiGIT for national coverage).
2. Group cross-validation by **atoll**, not by island — neighbouring islands share boats and
   facilities, so random folds leak.
3. Temporal split for anything with dates: train ≤2023, test 2024–2025.
4. Keep verified and estimated inputs in separate columns so a reviewer can rerun without the
   estimated layer.

---

## 6. Answering the question directly

**"What else can we do?"** — Four things, in order of value:

1. **Turn the snapshot into a service-quality story.** Report reachability as a curve across the
   day and the week (§2.1), with the worst hour as the guarantee. Cheapest, highest-impact change.
2. **Fix the Kaafu/Zone 3 hole** (§2.3) and re-run every national number. 29,462 residents sit in
   the blind spot, and they are the fastest-growing islands.
3. **Add reliability**: cancellations, delays, missed connections, "no boat today". The FIS extract
   and the timetable structure make the first version possible now (§2.6).
4. **Move from reachability to cost**: fares (3,058 parsed gazette rows), value of time (MVR 6.7/h
   atolls), out-of-pocket + escort + overnight costs. `research/11_economic_models.md` already
   specifies the generalised-cost formula; the atlas has never shown it.

**"Where can we use ML?"** — M1, M2 and M3 are the three that change decisions. M1 makes the
network credible. M2 creates the demand data the project is missing. M3 makes air planning
empirical. M4–M7 are worth doing only after one of those three lands.

---

## 7. Roadmap

| Horizon | Work | Output |
|---|---|---|
| **This week** | Departure-sensitivity curve in the UI; coverage-gap flag on every metric; per-island CSV export | New headline, honest caveats, reusable data |
| **2–3 weeks** | M1 sea-link durations from FollowMe; M3 airport forecast with seasonal-naive baseline | Network credibility + one forecast that beats a baseline |
| **4–6 weeks** | M2 OD inference; reliability layer; generalised cost in MVR | Demand proxy, reliability, cost — the three missing decision inputs |
| **Beyond** | Aasandha/HEMS extraction; capacity-constrained simulation; timetable optimisation (M7) | Operational decision support |

---

## 8. Reproduce

```bash
# 1. per-island accessibility from the router (writes two CSVs)
node --experimental-strip-types web/scripts/export-accessibility.ts

# 2. join to census outcomes; prints the §2.1 swing table, the §2.2 distance gradient,
#    the §2.3 coverage gap and the regressions (which exclude the coverage gap)
python3 scripts/analysis/island_access_outcomes.py
```

Outputs, all under `data/processed/multimodal/`:

- `island_access.csv` — 64,176 rows: origin × category × departure hour × air setting
- `island_access_best.csv` — best journey found anywhere in the operating day, per origin and category
- `island_access_outcomes.csv` — 191 islands: accessibility + growth + NEET/unemployment
- `island_access_departure_sensitivity.csv` — the §2.1 table

Sanity check: air-off 08:00 hospital reachability reproduces `VALIDATION.md` exactly —
322,715 / 447,420 = 72.128%.
