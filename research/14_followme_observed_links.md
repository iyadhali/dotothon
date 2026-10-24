# 14. Observed sea links from FollowMe GPS trips (Aug 2025)

Purpose: fill the router's biggest coverage gap (islands with `no_origin_access`) with **observed** boat movements, and cross-check the RTL ferry timetable.

Scripts: `scripts/followme_links_build.py` (build), `scripts/followme_links_stats.py` (summary tables).
Outputs (in `data/processed/followme/`):
- `observed_sea_links.csv` - 481 regular directed island-pair links (the filtered product).
- `observed_sea_links_all_candidates.csv` - all 2,309 directed pairs with at least one trip, unfiltered. It has the same columns as the main file.
- `observed_links_noaccess_coverage.csv` - per no-access island: covered or not.

The main file has the requested columns plus `trips`, `tpd_weekday`, `tpd_weekend`, `top_vessel_share`, `detour`, `od_kmh` and `dep_hour_hist` (a JSON map of local hour to trip count).

## Method

1. **Input**: `fm_trips.parquet`, 110,074 moving trips from 1,655 trackers. Timestamps are treated as UTC and shifted +5 h to local time, which puts the departure peak at roughly 07-09 local.
2. **Gazetteer**: the 200 islands in `multimodal.json` (191 inhabited plus 9 airport islands) and the 117 RTL stop coordinates mapped to their islands. Resorts and uninhabited islands are absent, so resort-only trips drop out when snapping.
3. **Snap**: trip origin (`o_lat/o_lon`) and destination (`d_lat/d_lon`) go to the nearest gazetteer point within **1.5 km**. The radius is 3 km for islands with population above 8,000 (Malé, Hulhumalé, Addu cities and similar), because their centroid is far from the harbour.
   - 70,345 origins and 70,209 destinations snapped.
   - 51,364 trips snapped at both ends.
   - 6,222 were same-island loops, which are dropped.
   - 45,063 inter-island trips remain after also dropping trips over 600 min.
4. **Aggregate** per directed pair (A to B):
   - trips/day = trips / 31, plus weekday (Sun-Thu) and weekend (Fri-Sat) means;
   - active days, distinct vessels (IMEI), median and p80 duration;
   - median OD distance, departure p10 and p90 hour (local), and an hourly histogram.
   - **Speed class** is `fast` if median OD speed is at least 25 km/h, otherwise `slow`.
5. **Regular passenger-type filter** (all must hold):
   - at least 0.5 trips/day (16 or more trips in 31 days);
   - active on at least 10 distinct days;
   - at least 2 vessels, and no single vessel above 80% of the trips (excludes private shuttles);
   - median detour at most 1.6 (excludes fishing loops and wandering tracks);
   - median OD distance at least 1.5 km.
   - Result: **481 directed links**, 426 fast and 55 slow. Median 1.13 trips/day, median 10 vessels per link.
6. **No-access flag**: `touches_no_access_origin` is true if either end is a `no_origin_access` island in the router output (67 islands, 63,749 people).
7. **RTL comparison**: each RTL stop maps to its island. The RTL duration is the median `shortest_minutes` over `rtl_connections.csv` rows for that island pair (reverse direction used if needed). `rtl_served` means the pair appears in RTL.

## Coverage of no-access islands

- **58 of 67** no-access islands, **58,064 of 63,749 people (91%)**, have at least one regular observed link. With the looser rule (5 or more trips, 2 or more vessels) it is 65 of 67 (62,429 people).
- 215 regular links touch a no-access island, and none of them is in the RTL network (consistent with the gap).
- By atoll, covered / no-access: Alif Alif 8/8, Alif Dhaalu 7/9, Kaafu 9/9, Meemu 6/7, Vaavu 5/5, Thaa 5/5, Raa/Baa/Noonu/Lhaviyani/Haa Dhaalu all complete. Haa Alifu 0/4 and Gaafu Alifu 2/3 are the weak spots.
- Still uncovered under the strict filter: Baarah (1,141), Kelaa (1,115), Dhaandhoo (1,044), Dhigurah (761), Filladhoo (559), Vashafaru (476), Mandhoo (418), Raimandhoo (171) and Gaadhoo* (0).
  - Baarah, Kelaa and Vashafaru have thinner traffic (they pass the looser rule, not the strict one).
  - North Haa Alifu is largely invisible in this data.
- **Important**: a link is only useful to the router if it reaches a network node.
  - 41 covered islands (46,358 people) link directly to at least one island that already has RTL/air access.
  - 17 covered islands (about 12,000 people) link only to other no-access islands (for example the Alif Alif cluster Mathiveri, Bodufolhudhoo, Feridhoo, Maalhos and Himandhoo, or the Thaa cluster Vilufushi, Madifushi and Dhiyamigili). They need a second hop, so the router should add the links to the graph and let transitive routing decide.
- Kaafu islands link to the Malé area directly. The biggest are Maafushi to Malé (about 8 trips/day each way, 30 min), Thulusdhoo to Hulhulé (17/day) and Himmafushi to Malé.

## Validation against RTL

220 of the regular links connect pairs that RTL also serves; 124 distinct island pairs are matched in both sets.

| Metric | Value |
|---|---|
| Median ratio, observed / RTL duration | **0.65** (p10 0.37, p25 0.49, p75 0.84, p90 1.00) |
| Within +/-25% of RTL | 32% |
| Observed shorter than RTL by more than half | 28% |
| Ratio at least 1 (observed slower) | 10% |
| Correlation, durations (Pearson) | 0.74 raw, 0.80 on logs |
| Median absolute difference | 7.3 min |
| Ratio, fast links (n=200) | 0.63 |
| Ratio, slow links (n=20) | 0.87 |

Median ratio by distance (n links): 0-5 km 0.55 (54), 5-10 km 0.63 (77), 10-20 km 0.66 (66), 20-40 km 0.87 (18), 40 km or more 0.98 (5).

Reading: observed durations track the RTL timetable well in rank order, but FollowMe is **systematically about 35% faster**. The gap is largest on short hops.
- RTL stop-to-stop times include dwell and loading, and RTL pairs are served by slower public ferries, while the GPS trips include many speedboats.
- Fixed per-trip overheads (docking, manoeuvring) weigh more on short hops.
- RTL times for the longest links (40 km or more) match the GPS times almost exactly (0.98).
- Use the observed durations for links RTL does not serve as **speedboat-class** times. For ferry-class service, scale up or add the RTL-style dwell, for example about 1.5x for hops under 20 km.

## Caveats

- **Vessel type is unknown.** Private speedboats, resort and guesthouse transfers, dive boats and fishing boats are mixed with public ferries. A link here means boats move between the islands, not that a scheduled or affordable public service exists. The vessel-count, top-share and detour filters reduce but do not remove this.
- The data is **August 2025 (tourist high season), not October 2026**. Services may have changed. Trips/day is a boat-movement count, not a timetable.
- Trip extraction is crude (the `fm_trips` method). Trips are split at stops and some journeys with intermediate calls are cut, so durations can be shorter than a full ferry run.
- Snapping uses centroids and stop points. Close neighbours are ambiguous: Malé, Hulhulé, Hulhumalé and Vilingili sit within a few km, and the nearest point wins. The many "Hulhulé" links are in practice the airport ferry terminal (plausible), but some Hulhumalé traffic may be attributed to Hulhulé. Large islands may still miss trips whose harbour is more than 3 km from the centroid.
- A tracker's own movement implies two or more people may be aboard, not passenger counts. No capacity, fare or schedule is inferred.
- Weekday split uses Maldives weekend Fri-Sat. The weekend/weekday ratio is a median of about 0.84.
- RTL durations come from `rtl_connections.csv` `shortest_minutes`. Where several stops share an island the median is used.
- Coverage is by trips with GPS-equipped vessels. Absence of a link (for example north Haa Alifu) is not proof of no transport.
