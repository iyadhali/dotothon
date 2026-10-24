# Speaker notes — Implementation & Demo

Maldives Datathon 2026 · A Team · all figures below pass `make check` (27/27).

Two slides are empty inside the deck: **slide 4 (Implementation)** has five stage labels and icons,
**slide 5 (Demo)** has one word. This file is the speech for both, plus the numbers and the Q&A.

---

## 0. The frame — say this before slide 4

> 187 inhabited islands. 44 of them teach grade 11–12.
> We rebuilt the sea network from a month of vessel GPS — **not from the timetable** — and asked
> which islands cannot reach one of those schools in two hours.
> Thirty-three cannot. 32,584 people, **9,591 children**.

This buys you the room: one question, one method, one number. Everything after it is evidence.

**The sound bite to repeat:**
> The biggest gaps are not the most remote islands — they are the ones next door. That makes this a
> scheduling decision, not a capital-works decision.

---

## 1. Slide 4 — Implementation

The five boxes on the slide, in order. Speak ~20 seconds each; do not read the boxes.

### 1. Data Exploration
- Four operator datasets were supplied; **none of them contains a school, a population or a facility**.
- Only **FollowMe** covers the whole archipelago: 31 days, **17.4 M points, 1,328 devices**.
- So the spine comes from public open data: **Census 2022** (population, children), **OCHA**
  boundaries, **MoE** statistics, **MoH** register, MNU campuses.
- **12 sources**, every one fingerprinted with sha256, so we always know which input produced which
  table.

> *"We started by finding out what the supplied data could not tell us."*

### 2. Geo-spatial preparation
- Census joined to **1,556 OCHA island polygons** → **187 inhabited islands, 448,819 residents**.
- Validation, not assumption: our computed island areas agree with OCHA's at **r = 0.9996**.
- GPS stays are snapped to the nearest island centroid within **6 km**.

### 3. POI mapping & network construction — *this is the innovation, slow down here*
- **A stay** = five or more consecutive polls at or below 2 knots. **Two stays** = one trip.
- 17.4 M points → **5,789 observed crossings**, each with a real, measured duration.
- **1,303 crossings dropped** because the implied speed was physically impossible (outside 0.5–55 kn).
- **572 facilities** placed on islands: 412 education (183 primary, 181 lower secondary, **44 upper
  secondary**, 4 campuses), 160 health (155 health centres, 5 hospitals).
- **No edge is invented.** No boat in the month → the pair is reported as *not connected*, never
  bridged on an assumption.

> *"This is the difference: the network we model is the one boats actually sailed."*

### 4. Accessibility analysis
- One weighted graph, one Dijkstra per service type. Cost = **observed median crossing time** per
  leg + **1 h connection penalty**, capped at **five sailings** (long chains are real itineraries).
- 44 islands teach grade 11–12; **5,105 students** in grades 11–12 — reconciles exactly to the
  published national total.
- **154 islands / 416,235 people within 2 h. 33 islands / 32,584 people / 9,591 children beyond.**
- Same graph, different destinations: **30 islands reach a hospital** within 2 h (262,712 people,
  48,768 children, median **4.79 h**) versus **183** for a health centre.

### 5. Data visualization
- Django + HTMX + Leaflet, **all vendored** — no CDN, no map tiles, no network calls. Runs offline.
- It reads **one SQLite file** that is the system of record: upserts by natural key, prunes what
  disappeared, writes one `data_change` row per touched table. Second run prints `nothing changed`.
- Map answers *"what can this island reach?"*; simulator answers *"where would the next build help
  the most people?"*

### If asked "is this a one-off analysis?" (Technical / Scalability)
- Nine stages, one command. `make ingest` fingerprints every source and rebuilds **only the stale
  stages**; `make watch` reacts in seconds (measured: **6 s** from drop to rebuilt tables).
- `make check` re-asserts **27 published numbers** after every rebuild — 27/27 today.
- New data is queryable before any stage understands it: unknown files land in `raw_record`.

---

## 2. Slide 5 — Demo (3 minutes, live)

Have open: `http://127.0.0.1:8000/` (map) and `http://127.0.0.1:8000/simulator/` in a second tab.
Fallback screenshots: `docs/app-desktop.png`, `docs/app-journey.png`, `docs/app-network.png`,
`docs/build-page.png`, `docs/build-page-crossings.png`.

**0:00 — Map, default view**
> 187 islands. Circle size is population, colour is hours to the nearest grade 11–12 school.
> Green is under two hours, red is over eight.

**0:15 — Click Gan (Laamu)**
- Card: **4,815 residents, 1,457 children, 7 sea links**; **1 of 6 service types on the island —
  it has a regional hospital, and not one grade 11–12 place.**
- Journey to Fonadhoo: **2.16 h = 1.16 h sailing + 1 h waiting**, via Bodufinolhu, **9.3 km apart**.
> *"Next door — and still two hours. The connection runs the wrong way round the atoll."*

**0:45 — Change "Colour the map by" to Hospital**
> Same network, sharper gap: 30 islands, 262,712 people, 48,768 children within two hours.
> The median island is 4.79 hours from a hospital.

**1:05 — Toggle "show the 2,076 observed links"**
> Every line is a crossing a tracked vessel actually made — pairs seen at least twice.
> There is no timetable in this model.

**1:20 — Scroll to "33 islands beyond two hours"**
> Ranked by children, with the school island and the kilometres to it. Median saving if that link
> were direct: 1.51 hours each way — a same-day return instead of an overnight stay.
> Seven islands had no tracked crossing at all; five are joined to Addu by causeway, and we say so
> rather than inventing a road link.

**1:50 — `/simulator/`, hospital tab (default)**
> Today: 30 islands, 262,712 people, 48,768 children. Build at Kulhudhuffushi:
> **+33,399 people, +11,855 children, +19 islands inside two hours — coverage 30 → 49 islands.**
> Pick a second site and it re-scores the country after the first build (Un'goofaaru: +23,713).

**2:25 — Scroll to "Where should we build connectivity?"**
> One new crossing at a time, 60 km limit. Fuvahmulah–Hithadhoo: 51 km, 1.9 h →
> **9,177 people and 2,761 children inside two hours.** Fuvahmulah has zero observed sea links
> today — that is the data gap this prices, not a claim that no boat exists.

**2:45 — Close**
> One SQLite file, no network calls, runs on venue wifi. Drop next month's GPS into `data/` and
> `make ingest` rebuilds the map, the register and the simulator; `make check` tells you if any
> published number moved.

**Demo failure drill:** if the app misbehaves, jump to `docs/app-desktop.png` and keep talking — the
numbers are all in this file. Do not debug on stage.

---

## 3. Numbers card (memorise these six)

| | |
|---|---|
| Islands / people | 187 · 448,819 |
| Grade 11–12 | 44 islands · 5,105 students |
| Within 2 h | 154 islands · 416,235 people |
| **Beyond 2 h** | **33 islands · 32,584 people · 9,591 children** |
| Hospital within 2 h | 30 islands · 262,712 people · 48,768 children · median 4.79 h |
| Enrolment | **91.9 % primary vs 29.9 % in grades 11–12** |

Supporting: 17.4 M GPS points · 1,328 devices · 5,789 crossings · 1,303 rejected · 572 facilities
· 2,076 links drawn · 27 checks · r = 0.9996 · 6 s rebuild.

---

## 4. What each sentence earns

| Criterion | The line that earns it |
|---|---|
| Technical 20 % | "live, offline, every number re-derivable, 27/27 checks, limits named in the app" |
| Impact 15 % | "MoE Planning & Research decides where a boarding place or subsidy buys the most enrolment; 33-island table ranked by children" |
| Scalability 15 % | "`make ingest` rebuilds only stale stages; a dropped file updates the app in 6 seconds; no server, no migrations" |
| Data Utilization 15 % | "12 sources; 4 organiser + 8 public; school totals reconcile to 5,105; island areas r = 0.9996" |
| Innovation 10 % | "the network is observed from GPS, not copied from a timetable; accessibility is population-weighted hours, not island counts" |
| Relevance 10 % | "post-16 education and health access across 187 islands — the defining Maldivian transport problem" |
| Clarity 5 % | "one question, one map, one simulator" |
| Teamwork 10 % | two speakers: implementation (pipeline) + demo (app), roles named on the slide |

---

## 5. Q&A — the eight questions we will get

**1. Why 33?**
Seven islands had no tracked crossing in the month; 26 had a route but over two hours. 7 + 26 = 33.

**2. Addu and Fuvahmulah come back "not connected". Is that right?**
Not connected *on the observed sea network*. Five Addu islands are physically joined to Hithadhoo by
causeway and Fuvahmulah had no tracked crossing in August 2025. We don't invent a road or air edge.
Counted with Addu's road link, the gap is 28 islands, 21,281 residents, 6,758 children. Air is the
named next step: Malé → Kulhudhuffushi is 7.7 h by sea against ~50 min by air.

**3. The title says multi-modal, but this is sea only.**
The graph is mode-agnostic — edges carry a mode and the schema already has a land-edge table. Only
the sea layer is *observed*, so it's the only one we ship; road and air need data we did not have.
The app footer says "network: sea crossings only" on purpose.

**4. Isn't this another dashboard?**
The dashboard is the demo surface. The contribution is the method: reconstructing the network from
GPS and turning it into population-weighted hours — a judge can rerun it from `make`.

**5. 1,328 devices can't be the whole fleet.**
Correct — a device is not a vessel and small dhoni traffic is under-sampled. That is why absence is
reported as a data gap, never a cut-off. We publish what the network can prove, not what it assumes.

**6. One month of GPS — what about seasonality?**
August 2025 only; monsoon cancellations and seasonal routes are invisible. That is exactly why the
pipeline exists: the next month's folder reruns the slow stage and nothing else.

**7. Fares and affordability?**
No inter-island fare table was supplied. The only price data is a Greater Malé airport-transfer
matrix (six zones, MVR 30–120). We deliberately do not model affordability rather than guess it.

**8. How do we know the numbers are right?**
Three independent checks: grade 11–12 enrolment reconciles to the published 5,105; island areas
agree with OCHA at r = 0.9996; 1,303 physically impossible crossings were rejected. `make check`
asserts all 27 published figures on every rebuild.

**9. Why 5,789 crossings but 2,076 links on the map?**
5,789 are directed observed crossings across all 1,134 snapped island nodes (journeys can transfer
on resort or airport jetties). The map draws one undirected line per pair seen **at least twice** —
a single trip is as likely to be GPS noise as a route.

---

## 6. Pre-flight — fix or check these before you walk on

1. **Slide 3 uses other people's numbers** (48 %, 43–53 % migration, ~47 % HeiGIT land-only). Label
   it "what is already known" and put **our** finding on slide 4–5: 44 islands, 33 beyond 2 h, 9,591
   children, 29.9 % vs 91.9 %. Otherwise the deck and the demo disagree in front of a judge.
2. **Say the multi-modal caveat once, early.** Better you say it than a judge finds it.
3. **Two speakers** — Teamwork is 10 % and the rubric explicitly asks for several members speaking.
4. **Run `make check` and open both pages** five minutes before. Keep the screenshot fallback open.
5. **Don't quote 8.5 h** for Malé → Kulhudhuffushi (stale README line); the live model says **7.68 h**.
6. **Rehearse the two scrolls** — the gap table and the crossing table are below the fold.
7. If the simulator summary says **4 hospital facilities**, it is counting provider *islands* (Malé
   has two hospitals). Say **"five hospitals on four islands"**.

---

## 7. Slide 6 — Impact & Limitations

### Impact — five claims, each with a number and an actor

- **Named decision, named user.** The Ministry of Education's planning team (and the Ministry of
  Health for the hospital layer) can act on the 33-island table: where one boarding place, transport
  subsidy or re-timed sailing keeps the most children in school. The output is a ranked list of
  places, not a dashboard to read.
- **The gap is big, concentrated and measurable.** 33 of 187 islands — about 18 % — hold 32,584
  residents and 9,591 children. Nationally the transition cliff is 91.9 % (primary) against 29.9 %
  (grades 11–12).
- **Provision is not the blocker; the journey is.** 44 islands already teach grade 11–12, and their
  5,105 students reconcile exactly to the published national total. The binding constraint is
  whether a child can reach one of them and come home the same day.
- **Most of it is fixable without building anything.** 26 of the 33 already have a route, just
  slower than two hours. The median island would save 1.51 h each way on a direct link — twice a
  day, that is the difference between a daily commute and a boarding place.
- **The counterfactuals are priced.** A hospital at Kulhudhuffushi puts 11,855 more children inside
  two hours (coverage 30 → 49 islands); one 51 km Fuvahmulah–Hithadhoo link does the same for 2,761
  children. Both are checkable in the simulator in thirty seconds.
- **One platform, six services.** The same graph answers hospital (30 islands / 262,712 people /
  48,768 children, median 4.79 h), health centre (183 / 422,593), college (45 / 294,469, median
  3.47 h) and lower secondary (185 / 446,239). Education is where the gap is sharpest, not the only
  place the method applies.

### Limitations — state them before the judges do, each with the fix

- **One month of GPS (August 2025).** Monsoon cancellations and seasonal routes are invisible. The
  fix is mechanical: next month's folder into `data/`, `make ingest`, ~4-minute slow stage, 6 s to
  updated tables.
- **Absence is not proof.** "No observed route" means no tracked vessel crossed in the month. Seven
  islands qualify: five are Addu's causeway islands, plus Muraidhoo (Haa Alifu) and Nadellaa (Gaafu
  Dhaalu). Counted with Addu's road link, the gap is 28 islands / 21,281 residents / 6,758 children.
- **Sea only.** The graph is mode-agnostic and the schema has a land-edge table, but air and road are
  not observed, so we ship neither. 14 domestic airports are the next layer; today Malé →
  Kulhudhuffushi is 7.68 h by sea against ~50 min by air. The deck title says "multi-modal"; the app
  footer says "sea crossings only" — say the second one out loud.
- **1,328 devices is not the fleet.** A device is not a vessel, and small dhoni traffic is
  under-sampled, so counts are a floor rather than a census. The cross-checks — 5,105 students
  reconciled, island areas r = 0.9996 — keep the network honest.
- **No fares.** The only supplied price table is the Greater Malé airport-transfer matrix (six zones,
  MVR 30–120). Affordability is a real barrier we do not model rather than guess.
- **Timing assumptions are choices, not facts.** One hour per connection, median observed leg time,
  maximum five sailings; no timetables, no waiting-time distribution, no capacity or school-quality
  data. It measures *opportunity*, not attendance.

### The two closing lines

> What we can defend: every number tonight is re-derivable from this repo with `make`.
> What we do not claim: that transport alone raises enrolment, or that no boat exists where none was
> tracked.
