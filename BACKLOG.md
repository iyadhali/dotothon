# Backlog

Open work items for the Island Access Atlas, highest priority first. Each item lists what is wrong today and what "done" means.

## 1. Fix evidence switching, transfer rules, calendars and fare applicability — **done (24 Oct)**

- [x] **Evidence:** the evidence layers are RTL 2026, MTCC 2023, observed boats, estimated flights and the Malé ferry (`web/shared/routing/evidence.ts`).
  - Each can be switched off from the "Data" menu.
  - Every journey row shows the evidence it used (verified vs estimated tags).
  - Precedence is structural: MTCC only where RTL has no stop, and observed boats only where no timetable serves the pair.
- [~] **Transfer rules:** made explicit in the UI:
  - 15 min ferry boarding
  - 45 min air check-in (60 min at Velana)
  - 10 min change of mode
  - same-vehicle stops are not re-boarded
  
  Per-jetty minimum connection times are still open.
- [x] **Calendars:**
  - Day-of-week picker.
  - All 30 MTCC 2023 trips carry their published `days`; none run on Friday, so the router drops them on other days.
  - RTL, flights and observed boats have no published calendar and are treated as daily (flagged).
- [x] **Fares:**
  - Traveller selector: adult resident, 65+ or disabled (RTL and Malé ferries free), student (Malé ferry free), and approved emergency (MVR 0, Aasandha pays).
  - Observed-boat legs are priced at the RTL tariff and flagged as estimated.
  - Return trips are still priced as two one-ways.
- Tests: 3 new router tests (calendar, concessions, evidence); 53/53 pass.

## 2. Make map classifications and fallback stories consistent — **done (24 Oct)**

- [x] One classification module (`web/app/utils/classify.ts`) sets the classes, labels and colours for the minimal map, the fallback map, the legend and the store.
- [x] Token-free SVG fallback (`FallbackMap.vue`) with the same props and all three stories. It is used automatically when Mapbox or WebGL fails, and can be forced with `?map=svg`.
- [x] Wording is unified everywhere: "No transport data" and "No same-day trip". This covers the KPI strip, bands, the intervention panel and the access panel.

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
