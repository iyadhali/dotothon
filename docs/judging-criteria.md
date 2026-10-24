# Judging criteria — the actual rubric (recorded 24 Oct 2026)

This supersedes the summary in the team briefing. Keep it open while building the slides.

## Mechanics

- Each judge scores **eight criteria from 1 to 5**; the weighted total is **out of 100**.
  Contribution of a criterion = `score / 5 × weight × 100`.
- **Technical execution, Impact and Scalability carry 50 of the 100 points.**
- 1 = weak (a mock-up, or nothing anyone could act on) · 3 = solid · 5 = excellent · 2 and 4 allowed.
- Tie-break order: **higher average of Impact + Scalability**, then **higher Technical execution**, then judges' vote.

## The eight criteria

| Criterion | Weight | What judges look for |
|---|---|---|
| **Relevance to the theme** | 10 % | Does the project tackle a real transport and mobility question for the Maldives? |
| **Data Utilization** | 15 % | Is the data right for the question, used correctly and properly sourced? **Only organiser-provided datasets, self-collected data shared with organisers, and publicly open data are allowed.** |
| **Innovation** | 10 % | Is the question, method or product original, beyond a standard set of charts? **A platform, app or dashboard is not innovative on its own** — judges look at what is new in the idea, the method, or the way it is used. |
| **Technical execution** | 20 % | Does the demo work live? Can you explain how it works and why you chose it? Do the results hold up, with limits named? |
| **Impact** | 15 % | Would the findings help real decision-makers? Who benefits, and what could they do differently? |
| **Scalability and implementation readiness** | 15 % | Can it be built out after the datathon? Does it work with updated data, on tools others can maintain, for a named user, with a realistic plan? |
| **Clarity of presentation** | 5 % | Clear story, readable visuals, on time, direct answers in Q&A |
| **Teamwork** | 10 % | Did the whole team contribute? Clear roles, several members speaking, collaboration visible |

## Three things in this rubric our project must answer for

1. **"A dashboard is not innovative."** Our innovation is the *method*: the ferry network is
   reconstructed from 17.4 M GPS points instead of copied from a timetable, and accessibility is
   expressed as population-weighted hours rather than island counts. The Django app is the demo
   surface for that method — never the pitch itself.
2. **Data must be allowed.** Every source we use is either organiser-provided (FollowMe, MTCC,
   MACL, Avas) or publicly open (MBS Census 2022, MoE School Statistics 2024, OCHA boundaries,
   MNU campus list). No scraping of private data, no personal data.
3. **Impact and Scalability are the tie-breakers.** They are worth 30 points *and* decide a tie.

## Self-assessment — where we stand

Scores are our own honest guess at what a judge would write today, updated after actions 1–2 landed
(`docs/findings.md`, `make check`). Was 76.0 before them.
`contribution = score / 5 × weight × 100`.

| Criterion | Weight | Score | Points | Evidence we can point at | Gap |
|---|---|---|---|---|---|
| Relevance | 10 % | 5 | 10.0 | island-to-island access to post-16 education is a live Maldivian policy question; 187 islands, not a toy sample | — |
| Data Utilization | 15 % | 4 | 12.0 | 4 organiser datasets + 3 public sources; school table reconciles to the published 5,105 students; island areas match OCHA at r = 0.9996 | **FollowMe carries the model; MTCC, MACL and Avas are only context.** Add one cross-validation (see action 4) |
| Innovation | 10 % | 4 | 8.0 | observed network from GPS; 1,303 physically impossible crossings rejected; road links added because boats cannot see a causeway | must be *stated* as the innovation, or a judge reads it as "another dashboard" and scores 2 |
| Technical execution | 20 % | 4 | 16.0 | live demo, runs offline, pipeline re-runnable, limits named in-app and in the README | **three capital routes return "no observed journey"** (Addu, Fuvahmulah, Thinadhoo) — correct, but reads as a bug. Air layer fixes it |
| Impact | 15 % | 4 | 12.0 | `docs/findings.md`: named user (MoE Planning & Research), 28-island decision table ranked by children, named schools and km; NER 29.9 % vs 91.9 % | boarding/subsidy costing not modelled |
| Scalability & readiness | 15 % | 4 | 12.0 | `Makefile` with `make refresh GPS=…`; `make check` asserts 13 published numbers; one command per stage | no hosted instance; maintainer note still thin |
| Clarity | 5 % | 4 | 4.0 | one question, one map, one number | 8-slide story not built yet |
| Teamwork | 10 % | 4 | 8.0 | five cleanly separable stages | needs two speakers minimum and a visible split of roles |
| **Total** | | | **82.0** | after actions 1 and 2 (Impact 3→4, Scalability 3→4) |

## The five actions, ranked by points at stake

1. **Name the decision-maker and ship one decision output (Impact, 15 %, first tie-break).**
   User: the Planning and Research Division at the Ministry of Education — the unit that publishes
   the School Statistics we already parse — plus MTCC/RTL route scheduling. Deliverable: a table of
   the **28 islands beyond 2 h**, with population, children, hours, and *the specific link whose
   addition would fix each*. **Done — see `docs/findings.md` and `data/derived/priority_gaps.csv`.**
2. **Prove the model refreshes (Scalability, 15 %, first tie-break).**
   `make refresh GPS=/path/to/next-month` now exists, and `make check` asserts the published
   numbers after every rebuild. Still to demonstrate: the same pipeline run on a one-week subset.
3. **Add the air layer (Technical, 20 %).** 14 domestic airports; the three failing capital routes
   become reachable, and "unreachable" stops being a false negative in front of a judge.
4. **Cross-validate FollowMe against MTCC (Data Utilization, 15 %).** MTCC reports monthly
   ridership on 8 ferry routes; we observe crossings on those same routes. If observed crossing
   volume tracks reported ridership, we have used two organiser datasets to check each other —
   the strongest possible answer to "is the data used correctly?"
5. **Write the 8-slide story with the method as the hero.** Slide 2 must say: the network is
   reconstructed from GPS, not read from a timetable, and that is why the answer differs from the
   RTL route map.
