# Criteria map — every deliverable, and the criterion it earns

Rule for the rest of the day: **nothing gets built unless it moves a criterion.** If a feature
cannot be named against a row below, it does not go in the repo. This file is the audit trail for
that rule.

Scoring reminder: each criterion is **1–5**, contribution = `score / 5 × weight × 100`. Technical,
Impact and Scalability are 50 of the 100 points; **Impact + Scalability also break ties.**

## Where each artifact scores

| Artifact | Criterion | What it does for the score |
|---|---|---|
| `docs/findings.md` + `data/derived/priority_gaps.csv` | **Impact 15 %** | named user, named decision, 28-island table ranked by children with the school island and km to it |
| `make refresh` + `scripts/check_outputs.py` | **Scalability 15 %** | proves the pipeline runs on new data and that 13 published numbers still hold |
| `scripts/build_sea_network.py` (GPS → stays → crossings) | **Innovation 10 %** *and* **Technical 20 %** | the method itself: the network is observed, not published |
| Django app (`web/`) | **Technical 20 %**, **Clarity 5 %** | live demo, offline, one screen that answers the question — **not** the innovation |
| `scripts/build_school_provision.py`, grade totals reconciled to 5,105 | **Data Utilization 15 %** | official MoE table, used correctly, self-checking |
| `scripts/build_island_spine.py`, area r = 0.9996 vs OCHA | **Data Utilization 15 %** | two independent sources agree — the join is validated, not assumed |
| `data/derived/island_access.csv` | **Relevance 10 %**, Impact | 187 real islands, not a sample; the answer is in hours and children |
| Limits section in README + `docs/findings.md` | **Technical 20 %** | judges score "results hold up, with limits named" |
| `REVIEW.md` | Teamwork 10 %, Clarity 5 % | shows the review discipline and the decisions behind the build |

## What we deliberately do **not** build

Each of these would cost time and move no criterion — several would actively hurt the Innovation
score by making this look like a dashboard project.

- **No login, no database, no admin panel.** `DATABASES = {}` on purpose.
- **No fares page.** No fare data was supplied; inventing one would fail Data Utilization.
- **No live API calls.** Everything is precomputed; venue wifi cannot break the demo.
- **No animation, 3D, or choropleth-by-default.** The circle map is readable in a projector shot;
  a choropleth of 186 islands at national zoom is not.
- **No second dashboard.** The app is the demo surface for one method, not a product.

## Risk to the score, and who owns it

| Risk | Criterion at stake | Mitigation |
|---|---|---|
| Judge clicks Addu → Malé and sees "no observed journey" | Technical 20 % | say the sentence before they do: *that is the air gap*; or ship the air layer |
| Judge reads the app as "another dashboard" | Innovation 10 % | slide 2 opens with the GPS-reconstruction, not the app |
| FollowMe alone carries the model | Data Utilization 15 % | say plainly that MTCC/MACL/Avas are context, and name the one cross-check we do have |
| Only one team member can explain the code | Teamwork 10 %, Technical 20 % | second speaker on the pipeline and on the limits |
| Stale number in slides vs app | Technical 20 % | `make check` before the deck is exported |
