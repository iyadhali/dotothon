# 5-Minute Presentation — Talking Points

**Project:** Multi-Modal Accessibility to Key Services in the Maldives
**Theme:** *Mapping Mobility through Data: Innovating Transport Insights for a Connected Maldives* (MBS, 24 Oct 2026)
**Runtime target:** ~5:00 (including Q&A)

## Slide 1 — Title (0:00–0:15) — 15s

**Say:**
“Good evening. We’re [Team Name], and this is Multi-Modal Accessibility to Key Services in the Maldives. Our question is simple: how long — and at what cost — does it take someone on each inhabited island to reach a school, a university, or a hospital, when you combine land, sea, and air travel?”

**Anchor facts:**

- 26 atolls; ~200 inhabited islands.
- Services are concentrated in Malé and a few regional hubs.

**Transition:** “Why does that matter? Because the standard picture is incomplete.”

## Slide 2 — Problem (0:15–0:45) — 30s

**Say:**
“Access is deeply uneven. Many islands don’t just face long distances — they face infeasible links: long travel times, multiple transfers, and unreliable schedules. The standard global datasets route by car only. HeiGIT/HDX reports about 47% of people can reach a school, and extending the drive from 10 to 120 minutes adds less than one percentage point — because a car cannot leave its island. HeiGIT leaves out 11 of 21 atolls entirely.”

**Key numbers:**

- ~47% school access under car-only routing.
- Coverage stays flat at ~46–48%.
- 11 of 21 atolls missing.

**Transition:** “So we changed the question.”

## Slide 3 — Feasibility (0:45–1:15) — 30s

**Say:**
“The question isn’t just ‘is the service nearby?’ It’s ‘is the link workable?’ Can a student realistically reach a university and return — given travel time, transfers, and schedule frequency? Two examples. Education: only 44 of 184 atoll islands teach grades 11–12, and 48% of atoll grade 9–10 students live on islands without them. Education accounts for 43–53% of migration to Malé from the key atolls. Health: in 2024, Aasandha recorded 4,426 emergency evacuations and 15,535 patients sent abroad.”

**Key numbers:**

- 44/184 atoll islands teach grades 11–12.
- 48% of atoll grade 9–10 students live on islands without them.
- 43–53% of migration to Malé from key atolls is education-related.
- 4,426 emergency evacuations; 15,535 patients abroad (2024).

**Transition:** “To measure that, we built a multi-modal network.”

## Slide 4 — Data & Method (1:15–2:15) — 60s

**Say:**
“Our network has 191 inhabited islands from Census 2022, plus airports, harbours, and facility islands as nodes.
For sea, we use the RTL fast-ferry timetable — 149 stops and 102 daily trips — with speeds measured from FollowMe boat GPS: about 110,000 trips; speedboats around 43 km/h, slow boats around 13 km/h.
For air, 20 operating airports and 40 domestic routes, with flight times and weekly frequencies.
For land, Greater Malé road times from Avas — about 85 seconds per km plus 71 seconds — plus the Addu and Laamu link roads.
Transfers include waiting time of half the interval between departures, plus boarding and check-in.
Destinations are schools by highest grade taught, higher-education campuses, and health facilities by level of care and specialty.
Outputs: travel time and cost to the nearest service, population beyond time thresholds, which modes reach which islands, and capacity-weighted access using 2SFCA.”

**Caveats to name:**

- MTCC passenger counts are synthetic — only route codes are real.
- MACL covers international flights at Velana only, with anonymised codes — it does not establish domestic flight schedules.
- Avas trip times look like booking-time estimates.
- FollowMe has no vessel type, plus GPS glitches and duplicate rows.
- Island names vary — join on atoll code + normalised island name.
- Low-frequency ferry waiting should use the actual timetable, not automatically half the interval.

**Transition:** “Here’s what we found.”

## Slide 5 — Demo & Results (2:15–3:35) — 80s

**Say:**
“We prepared the routes and layers for QGIS and set up a Mapbox view. The web app is a Nuxt + Nuxt UI + Mapbox GL JS starter — it already has the Maldives map component, and it’s ready for the facilities-atlas and simulator layers.
The analysis gives us travel time and cost per island, population beyond thresholds, mode reach, and capacity-weighted access.
The headline findings: car-only models miss most of the country; HeiGIT’s coverage stays flat at about 46–48%; the Grade 10 cliff; and health access depends on transfers — 4,426 emergency evacuations and 15,535 patients abroad in 2024.
We also built scenario testing: generalized cost = fare + value of time + overnight stays; affordability as a share of income; and what-if analysis for new routes or clinics.”

**Limits to state:**

- The web deliverable is currently a scaffold; the facilities atlas, timetable router, and transport simulator are planned.
- MTCC passenger counts are synthetic; they are not observed demand.
- MACL’s released records do not establish domestic flight schedules.
- Missing journeys do not prove absence of transport.
- Facility locations are island-level, not verified building coordinates.

**Transition:** “Who does this help?”

## Slide 6 — Impact (3:35–4:10) — 35s

**Say:**
“Real decision-makers: transport planners, the education and health ministries, and atoll councils. They could prioritise ferry and flight routes, place clinics and schools where they’re needed, and target subsidies to islands with large populations beyond time thresholds. The value isn’t a single map — it’s scenario testing: what happens if we add a route, a clinic, or a subsidy?”

**Transition:** “Of course, with that comes limitations.”

## Slide 7 — Limitations (4:10–4:30) — 20s

**Say:**
“Our biggest limitation is data completeness. As more verified data becomes available, it plugs in cleanly — new routes, updated timetables, or better facility locations will refine the results without rebuilding from scratch.”

**Key points to hit:**

- **Single limitation:** Data completeness (schedules, facility coordinates, fares).
- **Approach:** Explicit assumptions, not hard-coded guesses.
- **Future-ready:** Extensible model — add more verified data as it becomes available to improve accuracy over time.

**Transition:** “With those in mind, here’s our path forward.”

## Slide 8 — Close & Next (4:30–4:50) — 20s

## Slide 9 — Q&A (4:50–5:00) — 10s

---

## Judging criteria coverage

| Criterion | Weight | Where it’s covered |
|---|---|---|
| Relevance to theme | 10% | Slides 1–3: real Maldives transport/mobility question |
| Data Utilization | 15% | Slide 4: sources, joins, and intentional caveats |
| Innovation | 10% | Slides 3–5: feasibility framing, multi-modal + 2SFCA + scenarios |
| Technical execution | 20% | Slides 4, 5 & 7: network, QGIS/Mapbox, live demo, and clearly named limits |
| Impact | 15% | Slide 6: decision-makers and scenario testing |
| Scalability & implementation readiness | 15% | Slides 7 & 8: data readiness, pilot corridor, and maintainable tools |
| Clarity | 5% | Whole deck: timed story, light slides, explicit limitations |
| Teamwork | 10% | Split speaking roles across slides |
