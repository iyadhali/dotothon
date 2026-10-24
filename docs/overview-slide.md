# Overview slide — key points

Maldives Datathon 2026 · A Team · all numbers verified with `make check`

## Key points and their summary

| # | Key point | Summary |
|---|---|---|
| 1 | **44 of 187 inhabited islands teach grade 11–12.** | Upper secondary is a journey, not a neighbourhood school. |
| 2 | **The network is observed, not published** — 17.4 M GPS points, 5,789 crossings boats actually sailed. | We measured the sea network instead of copying the timetable. |
| 3 | **154 islands reach a school within 2 h; 28 do not** — 32,584 residents, 9,591 children. | Twenty-eight islands, 9,591 children, more than two hours from grade 11–12. |
| 4 | **The biggest gaps are next door** — Gan is 9.3 km from Fonadhoo and still takes 2.16 h; fixing links saves 1.51 h median. | A scheduling problem, not a capital-works problem. |
| 5 | **91.9 % primary enrolment vs 29.9 % in grades 11–12**; only 30 islands reach a hospital within 2 h. | The last connection is the barrier — for school and for health. |

**One line:** 187 islands, 44 schools, 17.4 million GPS points — and 9,591 children more than two
hours from grade 11–12.

**Visual:** full-bleed crop of the map from `docs/app-desktop.png`.

---

## What we have done

| # | Workstream | Summary |
|---|---|---|
| 1 | **Built the island spine** — Census 2022 ⋈ OCHA boundaries | 187 inhabited islands, 448,819 residents; island areas reconcile to OCHA at r = 0.9996 |
| 2 | **Rebuilt the sea network from GPS** — 17.4 M points → stays → crossings | 5,789 observed directed crossings; 1,303 impossible-speed trips rejected; no road or air links invented — an unobserved pair is reported as not connected |
| 3 | **Parsed the need** — MoE School Statistics 2024, MoH register | 44 islands teach grade 11–12 (5,105 students, reconciles to the national total); 572 facilities registered |
| 4 | **Modelled reachability and shipped the decision table** | Hours from all 187 islands to school, college, health centre, hospital; 28 gap islands ranked by children, each with the link that would fix it |
| 5 | **Built the platform and the app** — SQLite system of record, Django + HTMX + Leaflet | 13 tables + 4 views, audit log, app reads the database only; one map that runs offline |
| 6 | **Made it automatic and verifiable** — `make ingest` / `make watch` / `make check` | New data rebuilds only stale stages (6 s), provenance recorded, 27 assertions re-test every published number |

**One line:** from 17.4 million raw GPS points to a 28-island decision table, a working map, and a
pipeline that rebuilds itself when the next month of data arrives.

