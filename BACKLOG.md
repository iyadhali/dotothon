# Backlog

Open work items for the Island Access Atlas, highest priority first. Each item lists what is wrong today and what "done" means.

## 1. Fix evidence switching, transfer rules, calendars and fare applicability

- **Now:**
  - Evidence types sit in one network without explicit precedence. These are the RTL 2026 snapshot, MTCC 2023 trips, observed FollowMe boat links and estimated air.
  - Transfers use flat penalties.
  - Every trip is assumed to run on the reference day.
  - Fares are full resident fares on every leg.
- **Done when:**
  - [ ] Per-route evidence precedence is defined (RTL > MTCC > observed boats > estimated), with a user switch. Results label which evidence each journey used.
  - [ ] Transfer rules are realistic: minimum connection time per mode and jetty-to-airport links. No same-vehicle double counting.
  - [ ] Service calendars by weekday. MTCC `days_of_week` is honoured, there is no Friday service, and a day-of-week picker replaces the single reference day.
  - [ ] Fares apply correctly: concessions (65+, under 3, disabled, students), Aasandha-covered emergency trips, return vs one-way pricing, and observed-boat legs flagged as estimated.

## 2. Make map classifications and fallback stories consistent

- **Now:** the minimal map, `/details`, the schematic fallback and the Mapbox view classify islands slightly differently (bands, "no transport data", underserved classes). The fallback map does not show the Underserved and Where-to-build stories.
- **Done when:**
  - [ ] One shared classification function feeds every view and legend.
  - [ ] The schematic or static fallback renders the same three stories when Mapbox or WebGL is unavailable.
  - [ ] Wording is consistent everywhere: "No transport data" vs "No same-day trip".

## 3. Require version-matched artifact validation and QGIS exports

- **Now:**
  - `augment_network.py`, `build_fares.py`, `build_extras.py` and `build-db.ts` can drift. Expected counts are hand-edited.
  - The QGIS export predates the augmented network.
- **Done when:**
  - [ ] Every prepared artifact carries a shared build id or content hash: `multimodal.json`, `fares.json`, `extras/*`, the SQLite file and the QGIS layers.
  - [ ] `db:check` and CI fail on a mismatch.
  - [ ] Expected counts are derived from the manifest, not hard-coded.
  - [ ] `export_qgis.py` is re-run on the augmented network and its outputs are validated against the same build id.
  - [ ] The layers are opened once in desktop QGIS.

## 4. Build one verified appointment / care-episode pilot

- **Now:** journeys are one-way to the nearest listed facility, with a fixed 2-hour appointment and a modelled return.
- **Done when:**
  - [ ] One real pathway is modelled end to end and checked with the facility and operator. For example, dialysis three times a week from one atoll island, or a specialist referral to IGMH. The check covers:
    - departure, wait, appointment slot and return
    - overnight stay and escort
    - cost to the household
  - [ ] Results are compared with Aasandha or patient-reported travel for that pathway.
  - [ ] The approach is documented so it can be repeated for other pathways (see `research/17_care_delivery_and_appointment_coordination.md`).
