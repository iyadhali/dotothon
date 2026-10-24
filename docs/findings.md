# Findings and the decision they support

*This is the Impact artifact (15 %, and one half of the first tie-break). It exists to answer the
two questions judges ask: **who benefits**, and **what could they do differently**.*

## The finding in one paragraph

Of the Maldives' 187 inhabited islands, **44 teach grade 11–12**. On the network that boats
actually sailed in August 2025, **159 islands — 427,538 people — can reach one of those schools
within two hours**, and **28 islands cannot**. Those 28 hold **21,281 residents and 6,758 children
aged 0–17**. Nationally the consequence is visible: 91.9 % of primary-age children are in school,
but only **29.9 %** of 16–17-year-olds are enrolled in grades 11–12. The barrier is not a missing
school; it is the last connection between an island and the school that already exists.

## Who this is for

| User | What they do with it |
|---|---|
| **Planning & Research Division, Ministry of Education** — the unit that publishes the *School Statistics* series used here | decides where a boarding/hostel place or a transport subsidy buys the most enrolment, because the gap table is ranked by children, not islands |
| **MTCC / RTL route planning** | sees which pairs are *almost* connected: every gap row names the school island and the kilometres between them |
| **Island councils of the 28** | can put a specific, costed ask to the ministry instead of a general complaint |

## The decision table (top of the 28, ranked by children affected)

| Island | Atoll | Population | Children 0–17 | Hours now | Nearest grade 11–12 | km apart | If direct |
|---|---|---:|---:|---:|---|---:|---:|
| Gan | Laamu | 4,815 | 1,457 | 2.16 | Fonadhoo | 9.3 | 0.75 h |
| Gaafaru | Kaafu | 1,294 | 503 | 3.02 | Malé City | 62.4 | 2.18 h |
| Baarah | Haa Alifu | 1,141 | 406 | 2.17 | Hanimaadhoo | 8.6 | 0.73 h |
| Fenfushi | Alifu Dhaalu | 1,000 | 333 | 2.19 | Mahibadhoo | 36.1 | 1.48 h |
| Kelaa | Haa Alifu | 1,115 | 327 | 4.98 | Dhihdhoo | 13.4 | 0.86 h |
| Isdhoo | Laamu | 929 | 309 | 3.40 | Fonadhoo | 33.3 | 1.40 h |

Median saving if the nearest school were reachable directly: **1.51 hours each way**, which is the
difference between a same-day return and an overnight stay. Full table:
`data/derived/priority_gaps.csv` (sortable, every row reproducible).

The pattern that matters: **the biggest gaps are not the most remote islands, they are the ones
beside a school.** Gan sits 9.3 km from Fonadhoo, which teaches grade 11–12, and still takes 2.16 h
because the connection runs the wrong way round the atoll. That is a scheduling decision, not a
capital-works decision — and it is exactly the kind of finding a route planner can act on next
quarter.

## What we are *not* claiming

- **"No observed route" ≠ no service.** Two islands (Nadellaa, GDh; Muraidhoo, HA) had no tracked
  crossing in August 2025. They are reported as a data gap, never as a cut-off.
- **The "if direct" column is a scenario**, not an observation: straight-line distance at 20 knots
  plus a 0.5 h connection. It prices a hypothetical link; it does not claim anyone sails it.
- **One month of GPS.** Seasonal routes and monsoon cancellations are invisible.
- **No fares.** The supplied data has none, so affordability — which the original challenge card
  claimed — is deliberately absent from this analysis rather than guessed at.

## How to reproduce

```bash
python scripts/build_reachability.py     # writes data/derived/priority_gaps.csv
```

Every number above comes from that one command, over data in `data/external/` and `data/`.
