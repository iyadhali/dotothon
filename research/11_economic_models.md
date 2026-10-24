# 11 — Economic models to layer on the multi-modal accessibility model

Compiled 2026-10-24 for the Maldives Datathon 2026 project. The project measures land, sea and air travel time from every inhabited island to health facilities (by tier and specialty) and to higher-education campuses.
This file covers what economic layer to add, which formulas and parameters to use, what to show, and which Python tools fit.

**Evidence labels**
- **[V]** I read and verified the source this session; quoted numbers come from it.
- **[R]** The number comes from another research file in this folder, which cites its own source.
- **[K]** Standard literature cited from domain knowledge. The session's web-search budget ran out mid-task, so I could not open these again. The citations are well known, but check page numbers and exact figures before they go on a slide.
- **[A]** Assumption or default proposed for the hackathon. Expose it as a parameter and run a sensitivity test on it.

---

## 0. TL;DR: the recommended module ("Island Access Economics")

Five steps, each buildable in a few hours on top of the travel-time graph:

1. **Generalized cost (GC) per island–facility pair**, round trip, in MVR:
   `GC = fares + VoT × (IVT + 1.5 × (walk + wait + transfer) + 0.6 × schedule_delay) + nights × (lodging + food) + escort cost`.
   Use the World Bank TRN-15 defaults: **non-work VoT = 0.3 × household income per head per hour, and walk/wait = 1.5 × in-vehicle time (IVT)** [V].
2. **Accessibility** (four measures):
   - GC to the nearest facility of each tier;
   - same-day-return feasibility;
   - **E2SFCA** supply-to-demand ratios weighted by beds, doctors or seats;
   - **affordability**: round-trip cash cost as a % of monthly per-capita expenditure.
3. **Financial hardship incl. travel.** Find the share of people for whom one specialist round trip costs more than **40% of the monthly discretionary budget**. This threshold is the 2026 definition of SDG 3.8.2 [V], extended here to transport costs, which the official SDG indicator excludes.
4. **Equity.** Compute a Gini and concentration index of GC or access, Lorenz curves, and a Theil index split into between-atoll and within-atoll parts.
5. **Scenarios and optimisation.**
   - **p-median / MCLP** (spopt) to site a new dialysis, oncology or dental unit;
   - ferry-frequency and telemedicine what-ifs;
   - outputs: **ΔGC, person-hours saved, MVR per person-hour saved, and cost per person newly within same-day return**;
   - a rule-of-half benefit–cost ratio (BCR) at ADB discount rates.

**Three headline policy metrics:**
- **H1, "Same-day care":** % of people who can reach tier-X care (specialist, dialysis, surgery-capable hospital) and get home the same day. Add the Lancet 2-hour surgical-access metric as a companion.
- **H2, "Travel hardship":** % of atoll residents for whom one specialist trip costs more than 40% of the monthly discretionary budget. Also report the national **MVR cost per year of travelling for care**, and set it against Aasandha's MVR 23.4 M spent on moving critical patients [R].
- **H3, "Best next MVR":** a ranked list of interventions by MVR per person-hour saved, or by people brought within same-day reach per MVR 1 M.

---

## 1. Generalized cost of travel

### 1.1 Formula (per trip leg, then summed as a round trip)

```
GC_ij = F_ij                                   # cash: fares on all legs (ferry, speedboat, air, taxi/bus)
      + VoT_p × [ IVT_ij
                  + w_walk × walk_ij
                  + w_wait × wait_ij
                  + w_xfer × (transfer_time_ij + n_transfers × transfer_penalty)
                  + w_sd × SD_ij ]             # schedule delay (see 1.3)
      + N_ij × (L + M) × (1 + e)               # nights away × (lodging + meals) × (patient + escorts)
      + e × VoT_work × hours_lost_escort       # an accompanying adult loses work time
```

- **i** is the origin island and **j** the facility.
- **p** is the traveller type: adult non-work, working, child or patient.
- **e** is the number of escorts:
  - **1** for children, the elderly, maternity and dialysis [A];
  - **1** for overseas referrals, matching Aasandha practice, which pays the airfare of the patient and one caretaker [V, Suzana et al. 2015].

### 1.2 Weights for walking, waiting and transfers

| Component | Recommended weight (× IVT value) | Evidence |
|---|---|---|
| Walk / wait (non-work) | **1.5** | World Bank TRN-15, Table 2 "Base approach": "Walk/wait time modifier: 1.5 x value for IVT" [V] |
| Walk / wait (work trips) | 1.0 | TRN-15, Table 1 note 3: walking and waiting during work trips take the IVT value [V] |
| Range in the literature | 1.1 (Bangladesh, walking) to 2.0 (UK, walking) | TRN-15 citing IT Transport (2002) and Mackie et al. (2003) [V]. A UK meta-analysis puts walk at about 1.66 and wait at about 1.47 (Wardman 2004, *Transport Policy* 11:363–377) [K] |
| Transfer penalty | **15–30 IVT-minutes per transfer** on top of the weighted transfer wait [A, K] | Based on UK/EU practice, where a ferry-to-ferry or boat-to-plane interchange carries a heavy penalty. Use 20 min as the central value, and more when connecting means changing islands or terminals |
| Sea-state discomfort | optional ×1.2 on open-channel speedboat IVT [A] | TRN-15 says discomfort and stress are part of non-work time value [V] |

### 1.3 Infrequent ferries: schedule delay instead of half-headway

- **Half-headway waiting (H/2)** suits services that run every 15 minutes or so, where people arrive at random. It is wrong for RTL inter-island ferries that sail 1–3 times a day or a few times a week. On those services people **plan around the timetable**: they wait at home, not at the jetty, but they cannot travel when they want.
- The standard treatment is **schedule delay** (Vickrey 1969, *AER* 59(2); Small 1982, *AER* 72(3):467–479) [K]:
  - **SD** is the gap between the time a traveller wants to leave or arrive and the time the timetable allows.
  - Small (1982) estimated early schedule delay at about 0.6× and late schedule delay at about 2.4× the IVT value [K].
  - If desired departure times are spread evenly and the traveller takes the nearest sailing, **expected SD ≈ H/4**.
- **Recommended hackathon rule** [A]:
  - **H ≤ 30 min** (Malé–Hulhumalé–Villimalé, airport ferry): wait = H/2, weighted 1.5.
  - **30 min < H ≤ 24 h:** wait = terminal buffer (20 min for ferry, 60 min for domestic air), weighted 1.5. Add SD = H/4, weighted 0.6.
  - **Service not daily, or no feasible connection that day:** don't fold multi-day waits into SD. Count the **nights spent away** (§1.5). A three-times-a-week ferry is really a cost of overnight stays.
- **Best practice if time allows:** build a **time-expanded (timetable) graph**. Do not use a static graph with average waits.
  1. For each island, take a "ready to leave" time of 07:00 on a representative weekday.
  2. Compute the earliest arrival at each facility.
  3. Add the service duration (2–4 h for a specialist outpatient visit [A]).
  4. Compute the earliest possible arrival back home.
  5. `N_ij = number of nights away`. `same_day_ij = (N_ij == 0 and return ≤ 20:00)`.
- Doing this captures connection risk, Friday schedules, and the RTL **12-hour daytime-only service design** [R, 03_transport].

### 1.4 Value of time (VoT) for the Maldives

**Method (World Bank TRN-15, Mackie, Nellthorp & Laird 2005) [V]:**
- **Work time:** "Base approach Option 2: **1.33 × wage rate**", adjusted by the shadow wage rate.
- **Non-work time:**
  - **adults: 0.3 × household income (per head)** per hour;
  - **children: 0.15 ×**.
- TRN-15 also says non-work values must be inferred from behaviour. They rise with income, but less than proportionally. Where a country has no local study, they should be expressed as a share of household income.
- IT Transport (2002), the DFID study of least-developed countries [V], found Bangladesh non-work VoT to be **62% of work VoT**. TRN-15 also cites European non-work values of 10–42% of work values.
- The Netherlands range is 39% of the earnings rate for the lowest-income group and 22% for the highest (TRN-15 via search summary).

**Maldives inputs (HIES 2019, NBS) [V]:**

| Indicator (2019, MVR/month) | Republic | Malé | Atolls |
|---|---|---|---|
| Mean household expenditure | 28,251 | 37,013 | 20,177 |
| Median household expenditure | 24,932 | 35,026 | 17,154 |
| Household size | 5.2 | 5.1 | 5.2 |
| Mean per-capita expenditure | 5,439 | n/a | 3,860 (atoll mean) |
| Median per-capita expenditure | 4,648 (= MVR 153/day) | n/a | n/a |
| Atoll range, household expenditure | Raa 15,467 (lowest) to ADh 24,847 (highest) | | |
| Poorest-quintile household | n/a | 15,603 | 12,976 |
| Transport share of spending | 9.9% | 8.4% | **12.3%** |
| of which passenger transport services | 2.8% | 1.9% | **4.5%** |
| Housing, water and electricity group (household / per member) | 7,465 / 1,430 | **13,081 / 2,521** | 2,265 / 431 |

Source: https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2021/05/HIES2019-Expenditure.pdf

**Derived defaults** [A]:
- Expenditure stands in for income. Hours per month = 173 (40 h × 52 / 12).
- Inflate 2019 values to 2026 with the MBS CPI before final use. The values below are in 2019 MVR.

| Traveller | Formula | Atolls | Malé | Use |
|---|---|---|---|---|
| Adult, non-work | 0.3 × (per-capita income / 173) | **≈ MVR 6.7/h** | ≈ MVR 12.6/h | central case for patients and students |
| Child | 0.15 × … | ≈ MVR 3.3/h | ≈ MVR 6.3/h | paediatric trips |
| Work / escort losing a workday | 1.33 × wage/h | plug in the LFS mean wage. Example: MVR 10,000/month gives ≈ MVR 77/h | | escorts, civil servants |
| **Sensitivity band** | | **7 / 25 / 75 MVR/h** | | always show it |

**Note for the slides:**
- With a TRN-15 VoT, *time* costs come out small next to **fares and overnight stays**. That is a finding in its own right: in the Maldives, distance hurts mainly through cash and nights away, not through minutes.
- To compare "time" with "money", present GC in **hours-equivalent** (`GC / VoT`) as well as in MVR.

### 1.5 Overnight stays and indirect costs

| Item | Default [A] | How to firm it up |
|---|---|---|
| Lodging in Malé or a regional hub, L | MVR 600 per night (range 0–1,200). Use 0 if staying with relatives | Guesthouse rates. HIES shows housing costs per member in Malé are about **5.8× the atolls** (2,521 vs 431 MVR/month) [V] |
| Meals and incidentals, M | MVR 200 per person per day | HIES food spending per member is about MVR 1,250 per month (row alignment uncertain) [V/approx] |
| Lost earnings | 8 h × VoT_work for each employed traveller per day away | LFS wage |
| Escorts | e = 1 for under-15s, over-65s, maternity, dialysis and surgery | Aasandha rule for overseas referrals [V] |

**Evidence that overnight and travel costs dominate:**
- Suzana et al. (2015), *BMC Health Serv Res* 15:418, studied Maldivian medical travellers [V]:
  - **travel was 48% of the cost** of an overseas medical episode, and direct medical care was only 26%;
  - the median cost per patient was **USD 1,470** (USD 2,608 including caretakers);
  - **43% of these households faced catastrophic spending**, defined as health spending above 10% of household expenditure: South 62.7%, North 42%, Central 32.5%;
  - the most common stay was two weeks.
- HIES 2019 [V]:
  - **In the atolls, 53% of households with domestic travel spending had a medical reason for it.** In Malé the main reason was leisure.
  - **Transport is the largest single item in domestic medical-trip spending (about 51%).**
  - Mean household spending on domestic travel is MVR 2,485 (Republic), 1,497 (Malé) and **3,327 (atolls)** per month, among households reporting it. Table 9 is garbled in the PDF, so treat these as approximate.
- 03_transport [R]: inter-island travel cost about MRF 600 M in 2015, and about two-thirds of it was for medical purposes (PMC6010160).

---

## 2. Accessibility measures beyond the nearest facility

Write `c_ij` for GC (or time) and `d0` for a catchment threshold such as "same-day return" or 3 hours.

| Measure | Formula | Why it matters in the Maldives |
|---|---|---|
| **Nearest facility, by tier** | `A_i = min_j c_ij` for j in tier/specialty | Easy to explain. This is the baseline map |
| **Cumulative opportunities** | `A_i = Σ_j S_j · 1[c_ij ≤ d0]` | e.g. "specialist doctors reachable same-day". Geurs & van Wee 2004, *J Transp Geogr* 12:127–140 [K] |
| **Gravity / Hansen** | `A_i = Σ_j S_j · f(c_ij)`, with `f = exp(−β c)` or Gaussian | Hansen 1959, *JAIP* 25(2):73–76 [K]. Set β from the 03_transport distance-decay review, or from the half-life (e.g. access halves at 2 h) [A] |
| **2SFCA** | Step 1: `R_j = S_j / Σ_{k: c_kj ≤ d0} P_k`. Step 2: `A_i = Σ_{j: c_ij ≤ d0} R_j` | Gives **beds or doctors per 1,000 within reach** and so captures crowding (Luo & Wang 2003, *Env Plan B* 30:865–884 [K]). Capacity data: 2020 beds by tier and atoll; doctors per 10k by atoll (05_healthcare) [R] |
| **E2SFCA** | Same steps with zone weights `W_r` (e.g. 1.0, 0.68, 0.22) or a Gaussian decay inside d0 | Luo & Qi 2009, *Health & Place* 15:1100–1107 [K]. Use time bands such as < 1 h, 1–3 h, same day |
| **3SFCA / RAAM** | 3SFCA adds competition between facilities. RAAM uses an agent-choice equilibrium | Wan et al. 2012, *IJGIS* 26:1073 [K]; Saxon & Snow 2019, *Ann AAG* [V via pysal docs] |
| **Multi-modal 2SFCA (MM2SFCA)** | Split each island's population by modal access (e.g. share with air vs sea-only), with a separate catchment per mode | Mao & Nekorchuk 2013, *Health & Place* 24:115–122 [K]. **In the Maldives a GC-optimal path already picks the mode.** A cleaner variant takes the **logsum** across modes as `c_ij`: `c_ij = −(1/θ) ln Σ_m exp(−θ c_ijm)` [A] |
| **Affordability (cost-based)** | `Aff_i = cash_RT_ij / monthly per-capita expenditure_i`, and `Hardship_i = 1[cash_RT_ij > 0.4 × discretionary_i]` | Links access to SDG 3.8.2 (see §3.1) |

**Capacity (S_j) proxies available** [R]:
- **Health:**
  - inpatient beds by tier and atoll, 2020: 2,581 beds, 998 of them in Malé;
  - doctors per 10k by atoll, 2023;
  - IGMH: 537 beds and 464,783 outpatient visits in 2025;
  - dialysis units by island (news-derived).
- **Education:**
  - HEI enrolment by institution, 2021, with no campus split: total 12,861, of which Villa 4,223 and MNU 2,376;
  - MNU courses per campus (486 courses) as a seat proxy;
  - HEI campus counts per island.
- If capacity is missing, use tier-based defaults:
  - health centre = 1;
  - atoll hospital = 5;
  - regional hospital = 15;
  - tertiary = 50 "specialist-equivalents" [A].
- Document the defaults and run a sensitivity check.

**Choosing d0 for the Maldives** [A]:
- Emergency or obstetric: 2 h, which is the Lancet/EmONC convention.
- Specialist outpatient: same-day return.
- Dialysis: 30–60 min, because patients need three sessions a week.
- Tertiary education: "commutable daily" (≤ 1 h each way) versus "requires relocation".

---

## 3. Health economics

### 3.1 Catastrophic health expenditure and SDG 3.8.2, extended with travel

The definition changed in 2026. The current UN metadata (updated 2026-03-27) [V] defines **SDG 3.8.2** as:

> "Proportion of population with positive out-of-pocket household expenditures on health exceeding **40 per cent of household discretionary budget**."

- Discretionary budget = per-capita consumption − **societal poverty line (SPL)**.
- SPL = max($2.15; $1.15 + 0.5 × median per-capita consumption excluding out-of-pocket health spending), in 2017 PPP per day.
- **Out-of-pocket (OOP) spending is COICOP 06 only.** This covers medicines, outpatient, inpatient and other health services. **Transport to care is excluded.** The older 10% and 25% total-budget thresholds were superseded.
- Source: https://unstats.un.org/sdgs/metadata/files/Metadata-03-08-02.pdf

**Project innovation: a "travel-inclusive financial hardship" indicator.**
- Apply the 3.8.2 method with OOP = medical OOP + **travel and overnight cash costs**.
- This is defensible because Aasandha covers about 100% of public-facility care, so medical OOP is small for most islanders. The financial barrier that remains is **travel**.

**Back-of-envelope calibration** (2019 MVR, HIES) [A]:
- Median per-capita spending is MVR 153/day.
- 0.5 × median ≈ MVR 76.5. Add $1.15 PPP ≈ MVR 10. This needs the MVR/PPP-$ factor, so look it up in WDI.
- That gives SPL ≈ **MVR 87 per person per day ≈ MVR 2,640 per month**.
- For the average atoll resident (MVR 3,860 per month), the discretionary budget is ≈ **MVR 1,220 per person per month**.
- **The 40% threshold is ≈ MVR 490 per person, or ≈ MVR 2,540 for a household of 5.2.**
- In Raa, the lowest-spending atoll (2,974 per capita), the threshold falls to roughly **MVR 135 per person, or about MVR 700 per household**.
- **One round trip to Malé with an overnight stay and an escort clearly crosses this line in many atolls.** That is a strong, data-backed headline.
- Recompute in 2026 prices and with the correct PPP factor.

**Further references:**
- Wagstaff & van Doorslaer 2003, *Health Econ* 12:921–934 [K].
- Xu et al. 2003, *Lancet* 362:111–117, the 40% "capacity to pay" approach [K].
- World Bank equity note on Maldives health spending: OOP was **49% of total health expenditure in 2011** (search summary) [V-snippet]. https://documents1.worldbank.org/curated/en/884371468050349732/pdf/812480BRI0P12100Box037933B00PUBLIC0.pdf

### 3.2 Lancet Commission on Global Surgery: the 2-hour metric

Meara et al. 2015, *Lancet* 386:569–624 [K]. The six indicators and their 2030 targets:
1. **Access to timely essential surgery:** at least **80% of the population within 2 hours** of a facility that can perform the **bellwether procedures**: caesarean section, laparotomy and treatment of open fracture.
2. Specialist surgical, anaesthetic and obstetric workforce: at least 20 per 100,000.
3. Surgical volume: 5,000 procedures per 100,000.
4. Perioperative mortality: 100% of countries tracking it.
5. Protection against impoverishing expenditure: 100%.
6. Protection against catastrophic expenditure: 100%.

**Implementation:**
- Tag atoll, regional and tertiary hospitals that have an operating theatre and resident surgeon, obstetrician or gynaecologist (05_healthcare) as "bellwether-capable".
- Compute the % of population within 2 h by the *fastest emergency mode*, which is sea ambulance or air ambulance with a dispatch delay [R, 03_transport §speeds].
- Also compute it by scheduled public transport.
- The gap between the two is an **"emergency dependence" metric**: people who can reach surgery in time only by medevac.

**WHO/UNFPA EmONC norms (2009 handbook)** [K]: at least 5 EmONC facilities, including at least 1 comprehensive, per 500,000 people, and 2-hour access.

### 3.3 Cost of patient transfers and medevac

- **Aasandha data** [R, 05_healthcare]:
  - 4,079 emergency evacuations in 2023 and 4,426 in 2024;
  - inter-atoll transport of critical patients cost **MVR 23.4 M in 2025**: sea 19.9 M, air 3.6 M. Air was MVR 32.7 M in 2023;
  - evacuations per 1,000 residents in 2023: **GA 32.0, GDh 26.7, HA 21.2, Sh 20.5 … Kaafu 2.2, Malé 0.2**;
  - spending per capita in 2025: Malé about MVR 8,970 versus Kaafu outside Malé 592.
- **Implied average cost** ≈ MVR 23.4 M / ~4,400 ≈ **MVR 5,300 per evacuation**. This mixes years, so use it only to sanity-check the scale.
- **Model:** `Medevac_cost_i = r_evac,i × P_i × [p_sea × C_sea(dist_ij*) + p_air × C_air(dist_ij*)]`.
  - Calibrate `r_evac` to the atoll rates.
  - Set C_sea from charter speedboat rates. Fares of up to MVR 2,500 for a single maternity trip are reported [R].
  - Use the reported Aasandha totals as a calibration target.
- **Validation idea, which strengthens the technical-execution score:** check whether modelled GC or time to the nearest atoll or regional hospital correlates with the observed **evacuations per 1,000 by atoll**. A positive rank correlation is external validation of the accessibility model.

### 3.4 DALY / QALY-light options that fit a 10-hour hackathon

Avoid inventing clinical effect sizes. Rank the options as follows:

1. **Time and money burden in welfare units.** This is the safest option. Annual travel burden = Σ_s trips_s,i × GC_RT,s,i.
   - Get trip rates from outpatient visits per capita by atoll (2023: 1.9–8.8) [R].
   - Get specialist share from MoH: 1.24 M specialist visits out of 3.18 M [R].
   - Split between local and off-island visits using the facility tier available on the island [A].
2. **Cost-effectiveness denominators that need no DALYs:**
   - MVR per person newly within 2 h of bellwether surgery;
   - MVR per person newly within same-day specialist access;
   - MVR per avoided overnight stay;
   - MVR per person-hour saved.
3. **Dialysis case study** (strong human story, simple arithmetic):
   - 156 sessions a year × round-trip GC, compared with **relocating to a dialysis island** (rent at the HIES Malé housing differential plus lost livelihood).
   - Dialysis units cover about 11 islands, with 19 units across 9 atolls plus 2 original centres [R].
4. **Optional DALY step** (label it clearly as illustrative):
   - Take a literature relative risk for delayed emergency obstetric or trauma care beyond 2 h.
   - Multiply by births or injuries in the >2 h population and by DALYs per event.
   - Compare against WHO-CHOICE context, noting that GDP-per-capita thresholds are now discouraged (Bertram et al. 2016, *Bull WHO* 94:925–930) [K].

### 3.5 Equity metrics

| Metric | Formula / tool | Use |
|---|---|---|
| Gini of access (population-weighted) | PySAL `inequality.gini` or numpy | Headline inequality of GC or 2SFCA, health vs education |
| **Lorenz curve** | Cumulative population (sorted by access) vs cumulative access | One of the most persuasive charts |
| **Concentration index** | `CI = 2·cov_w(h_i, r_i)/μ_h`, where `r_i` is the fractional rank by per-capita expenditure (HIES atoll level) | Is poor access concentrated among the poor? O'Donnell et al. 2008, *Analyzing Health Equity Using Household Survey Data*, World Bank [K]; Wagstaff, Paci & van Doorslaer 1991 [K] |
| **Theil T decomposition** | Between-atoll + within-atoll parts (PySAL `inequality.theil.TheilD`) | Answers the policy question: is the gap **between** atolls (fix with regional hubs or air) or **within** them (fix with intra-atoll ferries)? |
| Spatial Gini / LISA hot spots | PySAL `esda` | Maps clusters of poor access |
| Palma-style ratio | Mean GC of the worst-off 10% of population ÷ best-off 40% | Easy to communicate |

---

## 4. Education economics

### 4.1 Cost of tertiary access for island students

The annual cost of attending campus k from island i is the smaller of commuting and relocating:

```
C_ik = min( commute: 2 × GC_ik × days_attend ,
            relocate: 12 × (rent_k + living_k − living_home) + trips_home × GC_RT_ik )
       + foregone_earnings × (1 − work_while_study_share)
       + fees − scholarship
```

- **Rent:** HIES housing costs per member are MVR 2,521 in Malé vs 431 in the atolls [V]. That is a ~MVR 2,000/month premium as a **lower bound**, because single students renting rooms pay more per person [A].
- **Fees:** the government Free First Degree scheme (2019) covers fees for a first degree at listed institutions [K, verify]. **Relocation and living costs remain, and they are the binding barrier.** This message is strong because it is precise.
- **Foregone earnings:** take the youth (18–24) median wage from the LFS and multiply by the employment probability [A].
- **Commutable vs relocation:** use the 2SFCA catchment of "≤ 1 h each way by scheduled transport". Only Malé, Hulhumalé, Villimalé and a few hub-adjacent islands (Addu link road, Kulhudhuffushi, Thinadhoo, Fuvahmulah, L. Gan) qualify [R, 06_education].
- **Supply concentration:** Malé has 18 HEI campuses. Outside Malé, campuses cluster in regional hubs, and MNU courses per campus run from Malé 214 to Gan 60 [R]. A course-weighted E2SFCA ("programmes reachable") is fairer than a campus count.

### 4.2 Returns to tertiary education

- The global private return to tertiary education is roughly **15% a year**. The Mincerian return is roughly **9% per year of schooling** (Psacharopoulos & Patrinos 2018, *Education Economics* 26(5):445–458) [K].
- **Use:** NPV of a degree = Σ_t (w_degree − w_secondary)_t / (1+r)^t − C_ik. Show how access cost C_ik **erodes the NPV for remote students**. Use the Maldives LFS wage by education if available. Otherwise apply the 15% return as a scenario [A].

### 4.3 Distance and enrolment

- **Literature:**
  - Frenette 2006, *Education Economics* 14(1):31–58, "Too far to go on?": students living beyond commuting distance of a university are much less likely to enrol, and the effect is concentrated in lower-income families [K].
  - Card 1995 used proximity to a college as an instrument for schooling [K].
  - Gibbons & Vignoles 2012, *Reg Sci Urban Econ* 42:98–113: distance affects *which* institution students choose more than *whether* they participate in England, where commuting is easy [K]. The Maldives sea gap is closer to Frenette's Canadian setting.
- **Hackathon test, which counts as innovation:** regress the island-level **share of 20–34-year-olds holding a degree or diploma** (Census 2022 attainment by island, if published) on **GC to the nearest programme-weighted campus**, controlling for atoll per-capita expenditure and island size.
  - A significant negative elasticity is a Maldives-specific "distance penalty" estimate.
  - Even a plain scatter with a lowess fit is persuasive.
  - Flag the result as correlational.

---

## 5. Investment and policy scenario modelling

### 5.1 Appraisal framework

- **Consumer surplus change (rule of half):** `ΔCS = ½ × Σ_ij (T⁰_ij + T¹_ij) × (GC⁰_ij − GC¹_ij)`.
  - This is standard practice in UK TAG and World Bank transport appraisal [K].
  - With fixed demand (T¹ = T⁰), it reduces to trips × ΔGC.
- **Discounting:** ADB *Guidelines for the Economic Analysis of Projects* (2017) use a **9% real rate as the general hurdle and 6% for social-sector and poverty-targeted projects** [K, verify]. Run a 20–30-year horizon and report NPV, BCR and EIRR.
- **Benefits:** traveller GC savings (fares, time, nights, escorts) + Aasandha transfer-cost savings + optional health benefits from §3.4.
- **Costs:**
  - capex: vessel, clinic, equipment, campus;
  - opex: crew, fuel, maintenance, specialist salaries.
  - A ferry's cost per vessel-hour can be derived from RTL subsidy figures, or from fuel burn × MGO price + crew [A].
- **Hackathon-friendly ratios:**
  - **MVR per person-hour saved** = annualised cost / Σ(trips × Δtime);
  - **"Marginal minute":** MVR per person-minute saved per year;
  - **cost per person newly within same-day reach** = annualised cost / ΔPop(same_day);
  - **cost per avoided night away**.

### 5.2 Intervention menu and how to model each on the graph

| Intervention | Graph edit | Key parameters |
|---|---|---|
| Higher ferry frequency / new RTL route | Add departures to the timetable graph. Don't divide times by frequency (04_build_feasibility rule) [R] | Vessel-hours added × cost per hour |
| Faster vessel / speedboat link | Change edge IVT using FollowMe GPS speeds | Fuel cost per km at the new speed |
| New atoll specialist clinic (dental, oncology outreach, dialysis) | Add a capacity node at an existing hospital | Capex + specialist cost. Use p-median / MCLP to choose the site |
| Telemedicine | Make a share τ of specialist **follow-up** trips GC ≈ 0, with a small connectivity cost | τ = 0.2–0.4 scenario [A]. Requires an on-island health centre |
| New airport / scheduled air route | Add an air edge with frequency, fare and check-in buffer (07_air_network) [R] | Fares are often much higher. GC may fall only for high-VoT or time-critical trips |
| New campus / outreach centre | Add an education node with seats | Fixed cost vs the relocation cost avoided per student |
| Fare subsidy (e.g. Greek-style "transport equivalent") | Lower F_ij | Fiscal cost = Δfare × trips. Track the change in hardship share |

### 5.3 Location-allocation for specialist units

- **p-median** (Hakimi 1964, *Oper Res* 12:450–459 [K]): minimise Σ_i w_i c_ij(x), where the weights `w_i = P_i × need rate` (e.g. CKD prevalence for dialysis, age 50+ for oncology screening) [A].
- **Maximal Covering Location Problem (MCLP)** (Church & ReVelle 1974, *Pap Reg Sci Assoc* 32:101–118 [K]): maximise the population within d0 (same day, or 1 h for dialysis) with p new units. This framing suits policy: "where should the next 2 dialysis units go?"
- **LSCP:** the minimum number of units needed for 100% coverage within d0, i.e. what universal same-day access would take.
- **Candidate sites** = existing atoll and regional hospitals, which have staff and power. **Cost matrix** = GC (or time) from the multi-modal model. Library: **spopt** (PySAL), whose models include LSCP, MCLP, P-Median, P-Center, P-Dispersion and Capacitated LSCP [V]. It is solved with PuLP and CBC.
- **Equity-aware option:** compare p-median (efficiency) with p-center (worst-off island). The trade-off curve between them makes a strong slide.

### 5.4 Archipelago and remote-area precedents (use for framing)

All [K]; verify details before quoting numbers.
- **Scotland:**
  - **Road Equivalent Tariff (RET)** on CalMac ferries was piloted for the Western Isles from 2008 and rolled out 2012–2015. It sets fares at roughly the cost of driving the same distance, and Transport Scotland's evaluations reported large traffic increases.
  - The **Islands (Scotland) Act 2018** requires "island communities impact assessments", which is island-proofing. This is a direct policy analogue for MBS and the ministries.
- **Norway:** ferry PSO contracts; the **"Ferry-free E39"** coastal-highway programme, appraised with standard CBA that monetises time and waiting savings; fare cuts and free ferries on low-traffic routes in recent years.
- **Faroe Islands:** subsea tunnels replaced ferries (Vágar 2002, Norðoy 2006, Eysturoy 2019/20, Sandoy 2023) with toll financing. Accessibility gains raised commuting and settlement retention.
- **Greece:** PSO ferry lines; the **"Transport Equivalent" (Metaforiko Isodynamo)** fare subsidy since about 2018, which sets island fares at the equivalent land-transport cost; and an air-ambulance (EKAB) service for small islands.
- **Philippines:** the **Strong Republic Nautical Highway / RoRo** policy (2003). ADB-supported studies reported large falls in passenger and cargo transport costs. GIS-based 2SFCA studies of health access are common.
- **Indonesia:** **Tol Laut** (subsidised "sea toll" shipping, 2015); **Nusantara Sehat** health-worker deployment to remote islands; floating hospitals.
- **Pacific (Fiji, Vanuatu, Solomons, Kiribati):** costly overseas-referral schemes; outer-island telehealth pilots; WHO Western Pacific "Healthy Islands" framing.
- **Canada (Nunavut) / Australia (Royal Flying Doctor Service):** medical travel takes a large share of territorial health budgets; RFDS economic evaluations monetise travel and time savings. These are useful analogues for the share of Aasandha spent on transfers.
- **Global gap:** global friction-surface maps of travel time to healthcare (Weiss et al. 2020, *Nature Medicine* 26:1835–1838 [K]) handle ferries and flights poorly in archipelagos. This project fills that gap, which supports the **innovation** score.

---

## 6. Concrete hackathon module

### 6.1 Data flow

```
islands (Census 2022 pop, age bands, atoll)  ─┐
facilities (tier, specialty, beds/doctors)   ─┤
campuses (programmes/seats)                  ─┤──► time-expanded multimodal graph (networkx/igraph)
timetables (RTL, airport ferry), FollowMe     ─┤        │  earliest arrival / return, legs, fares
speeds, air routes, Greater Malé road, fares ─┘        ▼
                                   OD table: i, j, IVT, walk, wait, transfers, SD, fare, nights
                                                       │
       params.yaml (VoT, weights, L, M, escorts, d0, rates)  ──►  GC_ij (MVR + hours-equivalent)
                                                       │
     ┌──────────────┬──────────────┬───────────────┬──┴───────────────┐
  nearest/same-day  E2SFCA (access) affordability /  equity (Gini, CI,  scenarios + spopt
  Lancet 2h          beds/docs/seats  hardship 40%    Theil, Lorenz)     (p-median/MCLP, BCR)
```

### 6.2 Parameter sheet (defaults; every row adjustable in the UI)

| Parameter | Default | Source |
|---|---|---|
| VoT non-work adult | MVR 6.7/h atolls, 12.6/h Malé (2019 MVR); sensitivity 7/25/75 | TRN-15 + HIES [V] |
| VoT child | 0.5 × adult | TRN-15 [V] |
| VoT work | 1.33 × LFS wage/h | TRN-15 [V] |
| Walk/wait weight | 1.5 | TRN-15 [V] |
| Schedule-delay weight | 0.6 | Small 1982 [K] |
| Transfer penalty | 20 IVT-min | [A] |
| Terminal buffer | 20 min ferry, 60 min domestic air | [A] |
| Same-day window | leave ≥ 07:00, home ≤ 20:00, 3 h at facility | [A]; RTL daytime-only design [R] |
| Lodging / meals | MVR 600 / 200 per person per night | [A] |
| Escorts | 1 for children, elderly, maternity, dialysis | Aasandha practice [V] |
| SPL / discretionary budget | ≈ MVR 2,640 per person per month (2019); atoll mean discretionary ≈ MVR 1,220 | SDG 3.8.2 method + HIES [V], PPP approx [A] |
| Hardship threshold | 40% of discretionary | SDG 3.8.2 (2026) [V] |
| Trip rates | outpatient visits per capita by atoll; specialist share 39% | MBS/MoH [R] |
| Evacuation rates | Aasandha per 1,000 by atoll, 2023 | [R] |
| Discount rate | 9% (6% social), 25 years | ADB 2017 [K] |
| FX | MVR 15.42 = USD 1 (peg) | [K] |

### 6.3 Outputs, maps and visuals

1. **Choropleth or bubble map of islands** with these layers:
   - GC (MVR) to specialist care;
   - hours-equivalent;
   - nights away;
   - same-day yes or no.
   Use a toggle between health tier and higher education.
2. **Hardship map:** cash cost of one specialist trip as a % of the discretionary budget, with islands above 40% highlighted.
3. **Lorenz curves:** access to health vs higher education vs the Malé baseline, with Gini and the between-atoll Theil share in the legend.
4. **E2SFCA map:** beds or doctors per 1,000 within reach. This shows crowding, not just distance.
5. **Scenario panel:** pick an intervention to get ΔGC, Δ same-day population, MVR per person-hour saved and BCR. Show the **p-median / MCLP optimal sites** for the next 1–3 dialysis or specialist units.
6. **Validation scatter:** modelled access vs Aasandha evacuations per 1,000 by atoll.
7. **Education:** campus-access GC vs degree attainment by island (if census attainment exists), plus the commute-vs-relocate split.

### 6.4 Minimal Python skeleton

```python
import numpy as np, pandas as pd, yaml
from access import Access           # PySAL access: 2SFCA/E2SFCA/3SFCA/RAAM
from spopt.locate import PMedian, MCLP
import pulp

P = yaml.safe_load(open("params.yaml"))

def gc(row, vot):
    t = (row.ivt_h + P["w_wait"]*(row.walk_h + row.wait_h + row.xfer_h)
         + P["w_sd"]*row.sd_h + row.n_xfer*P["xfer_pen_h"])
    stay = row.nights * (P["lodging"] + P["meals"]) * (1 + row.escorts)
    esc  = row.escorts * P["vot_work"] * min(8, row.hours_away)
    return row.fare_rt + vot*t + stay + esc

od["GC"]   = od.apply(lambda r: gc(r, vot_by_island[r.i]), axis=1)
od["GC_h"] = od.GC / od.i.map(vot_by_island)

# nearest, same-day, Lancet-2h
nearest = od[od.tier >= 3].groupby("i").GC.min()
same_day = od[od.tier >= 3].groupby("i").same_day.max()

# E2SFCA (Gaussian inside d0) via PySAL access, or ~15 lines of pandas
A = Access(demand_df=pop, demand_index="i", demand_value="pop",
           supply_df=fac, supply_index="j", supply_value="beds",
           cost_df=od, cost_origin="i", cost_dest="j", cost_name="GC_h")
A.enhanced_two_stage_fca(...)   # check the exact API name in the docs (also two_stage_fca with weight_fn)

# hardship: travel-inclusive SDG 3.8.2
disc = pce_island - SPL                    # per person per month
hard = (od_min_cash_rt_per_person > 0.4*disc.clip(lower=0)) | (disc <= 0)
H2 = np.average(hard, weights=pop)

# equity
def gini_w(x, w):                          # population-weighted Gini via Lorenz trapezoids
    o = np.argsort(x); x, w = np.asarray(x)[o], np.asarray(w)[o]
    cw  = np.concatenate([[0], np.cumsum(w) / w.sum()])
    cxw = np.concatenate([[0], np.cumsum(x * w) / np.sum(x * w)])
    return 1 - np.sum((cxw[1:] + cxw[:-1]) * np.diff(cw))

# location-allocation
cost = od.pivot(index="i", columns="cand_j", values="GC_h").values
pm = PMedian.from_cost_matrix(cost, weights=pop.values, p_facilities=2, name="dialysis")
pm = pm.solve(pulp.PULP_CBC_CMD(msg=False))
```

**Libraries:**
- **networkx** (prototyping, time-expanded Dijkstra) or **python-igraph** (10–100× faster shortest paths).
- **access** (PySAL) for FCA-family metrics [V].
- **spopt** for LSCP, MCLP, p-median and p-center [V].
- **inequality / esda** (PySAL) for Gini, Theil and LISA.
- **geopandas + folium/keplergl/pydeck** for maps.
- **pandana**: only for Greater Malé roads; overkill elsewhere.
- **r5py / OTP**: only if synthetic GTFS gets built. 03_transport recommends against it for the hackathon [R].
- **pulp** (CBC) as the MILP solver.

### 6.5 How this scores against the likely judging criteria (20% each)

| Criterion | What the economic layer adds |
|---|---|
| Policy relevance | Speaks in **MVR and SDG language** (3.8.2 hardship, Lancet 2 h, UHC), ties directly to Aasandha's transfer budget, and gives ranked investments with siting answers |
| Technical execution | Time-expanded GC, E2SFCA with real capacity data, MILP siting, and **external validation** against Aasandha evacuation rates |
| Presentation | Three headline numbers, a Lorenz curve, a hardship map and a scenario slider |
| Innovation | A travel-inclusive SDG 3.8.2 indicator; schedule-delay/overnight treatment of sparse ferries; a Maldives "distance penalty" for tertiary attainment |
| Replicability / scalability | YAML parameter sheet, open PySAL stack, works for any SIDS with timetables + census; MBS can update annually with HIES/LFS/CPI |

---

## 7. Gaps and caveats

- **Search budget:** the session-wide web-search limit ran out mid-task. Items marked [K] could not be re-opened this session. Spot-check the most-quoted ones before they go on slides: Meara 2015, Luo & Qi 2009, ADB discount rates, Free First Degree terms, and the Scotland RET results.
- **Prices:** HIES 2019 values are in 2019 MVR. Inflate them with the MBS CPI. A HIES 2024 release would supersede them if available.
- **PPP:** the SPL conversion uses an approximate PPP factor. Get the 2017 PPP private-consumption conversion factor for the Maldives from WDI.
- **Wages:** no Maldives wage figure was verified this session. Get it from LFS 2019/2023 (mean and youth monthly earnings).
- **Demand data:** there is no referral origin–destination matrix [R], so trip rates are modelled from atoll-level outpatient visits and tier availability.
- **Aasandha coverage:** coverage of domestic non-emergency travel is partial and has changed over time; the childbirth travel cut is one example [R]. Treat the share of cash GC borne by households as a scenario parameter.

## 8. Sources

**Verified this session [V]:**
- World Bank TRN-15, *Valuation of Time Savings* (Mackie, Nellthorp, Laird, Jan 2005): https://openknowledge.worldbank.org/entities/publication/7dc684c8-0af7-5f3e-90d5-9c6636ca37df ; full-text copy: https://assets.publishing.service.gov.uk/media/57a08ca6e5274a27b2001323/C21-trn-15-EENote2.pdf
- IT Transport (2002), *The Value of Time in Least Developed Countries*, DFID KaR R7785: https://assets.publishing.service.gov.uk/media/57a08d4340f0b64974001762/R7785.pdf
- NBS, *HIES 2019: Household Expenditure*: https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2021/05/HIES2019-Expenditure.pdf
- UN SDG metadata 3.8.2 (updated 2026-03-27): https://unstats.un.org/sdgs/metadata/files/Metadata-03-08-02.pdf
- Suzana M, Mills A, Tangcharoensathien V, Chongsuvivatwong V (2015), "The economic burden of overseas medical treatment: a cross sectional study of Maldivian medical travelers", *BMC Health Serv Res* 15:418: https://pmc.ncbi.nlm.nih.gov/articles/PMC4583732
- PySAL `access` docs (Saxon et al. 2020): https://pysal.org/access/
- PySAL `spopt` docs (Feng et al. 2022, *JOSS*, doi:10.21105/joss.03330): https://pysal.org/spopt/
- World Bank note on equity in Maldives health spending (search summary only): https://documents1.worldbank.org/curated/en/884371468050349732/pdf/812480BRI0P12100Box037933B00PUBLIC0.pdf
- Older HIES (2016) income gap, MVR 37,035 in Malé vs 18,358 in the atolls: https://maldivesindependent.com/society/survey-underscores-huge-income-gap-between-male-and-atolls-139188

**From other research files [R]:**
- `05_healthcare_data.md`: Aasandha spending, evacuations, beds and doctors.
- `06_education_data.md`: HEI campuses and enrolment.
- `03_transport_network_and_methods.md`: fares, Aasandha rules, medevac speeds; also https://mfr.mv/soes/how-aasandha-works , https://raajje.mv/21781 , https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6010160/

**Literature [K]:**
- Hansen 1959 *JAIP* 25:73–76.
- Luo & Wang 2003 *Env Plan B* 30:865–884.
- Luo & Qi 2009 *Health & Place* 15:1100–1107.
- Mao & Nekorchuk 2013 *Health & Place* 24:115–122.
- Wan, Zou & Sternberg 2012 *IJGIS* 26:1073–1089.
- Geurs & van Wee 2004 *J Transp Geogr* 12:127–140.
- Vickrey 1969 *AER* 59:251–260.
- Small 1982 *AER* 72:467–479.
- Wardman 2004 *Transport Policy* 11:363–377.
- Meara et al. 2015 *Lancet* 386:569–624.
- Wagstaff & van Doorslaer 2003 *Health Econ* 12:921–934.
- Xu et al. 2003 *Lancet* 362:111–117.
- O'Donnell et al. 2008, World Bank, *Analyzing Health Equity Using Household Survey Data*.
- Psacharopoulos & Patrinos 2018 *Educ Econ* 26:445–458.
- Frenette 2006 *Educ Econ* 14:31–58.
- Gibbons & Vignoles 2012 *RSUE* 42:98–113.
- Hakimi 1964 *Oper Res* 12:450–459.
- Church & ReVelle 1974 *PRSA* 32:101–118.
- Bertram et al. 2016 *Bull WHO* 94:925–930.
- Weiss et al. 2020 *Nat Med* 26:1835–1838.
- ADB 2017 *Guidelines for the Economic Analysis of Projects*: https://www.adb.org/documents/guidelines-economic-analysis-projects
- WHO/UNFPA/UNICEF/AMDD 2009 *Monitoring Emergency Obstetric Care*.
