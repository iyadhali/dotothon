# Multi-Modal Accessibility Plan

## Objective

Display the accessibility (in terms of travel distance/time) of key services such as universities and schools to the population living on various islands, considering land, sea, and air transport modes, and visualize the results in QGIS.

## Datasets Available

* **MACL (Airport Traffic)** - Flight routes, schedules/traffic data. Useful for air connectivity between atolls/islands with airports.
* **MTCC.xlsx** - Ferry/scheduled sea transport data (bus/ferry routes with passenger data). Core for inter-island sea connectivity across atolls.
* **FollowMe / Avas Ride** - Land transport/ride-hailing data. Useful for first/last-mile connectivity, particularly in Greater Male' region.
* **Team-shared datasets** - May contain POIs (schools, universities), island boundaries, population data, or additional transport data.
* **HeiGIT/OpenAccessLens Maldives Risk Assessment Indicators** - Can be used as a baseline for comparison (access to education/healthcare indicators).

## Methodology

1. **Define study area \& population** - Use island-level population data (from census/MBS datasets or team-shared data). Focus on residential islands and their populations.
2. **Identify key services (destinations)** - Map locations of universities and schools. Prioritize tertiary education (universities) as it has the widest catchment and most transport dependency.
3. **Build multi-modal transport network** - Model the combined network with nodes (islands, ports, airports, bus stops) and edges weighted by travel distance/time for each mode:

   * **Land**: Utilize FollowMe/Avas Ride data for road-based travel where available
   * **Sea**: Utilize MTCC ferry routes and schedules for inter-island sea transport
   * **Air**: Utilize MACL flight data for air links between islands/atolls
4. **Account for transfers** - Include transfer times between modes (e.g., island to port, port to ferry, etc.)
5. **Calculate accessibility** - For each origin island (with population), compute shortest travel time/distance to the nearest university/school via the best multi-modal route.
6. **Classify accessibility** - Group islands by accessibility levels (e.g., very accessible, moderately accessible, poorly accessible) based on travel time thresholds.
7. **Visualize in QGIS** - Create thematic maps showing accessibility by island, with population overlays to highlight underserved areas with large populations.

## Key Metrics

* **Travel time to nearest service** (minutes/hours) via multi-modal network
* **Travel distance** (km) to nearest service
* **Population affected** - Number of people on islands with limited access (beyond threshold)
* **Mode breakdown** - Which mode combination provides access to different islands
* **Accessibility gaps** - Islands with no reasonable access or longest travel times

## Implementation Steps

1. **Data exploration** - Analyze all datasets to understand structure, coverage, routes, and temporal aspects.
2. **Geospatial preparation** - Get island boundaries, coordinates (ports, airports), and build a spatial dataset of all nodes.
3. **POI mapping** - Locate universities and schools (extract from OSM, team-shared datasets, or available sources).
4. **Network construction** - Build multi-modal graph with appropriate edge weights (travel times/distances).
5. **Accessibility analysis** - Compute multi-modal shortest-path travel times/distances from each inhabited island to nearest key services.
6. **QGIS visualization** - Symbolize islands by accessibility class, add population data, create clear maps showing underserved areas.
7. **Analysis \& interpretation** - Identify patterns and gaps, especially for islands far from Male' or regional hubs.

## Feasibility Notes

* Leverages actual datathon datasets (MACL, MTCC, FollowMe/Avas) - well-suited for this challenge
* Aligns with HeiGIT/OpenAccessLens methodology which is proven for archipelagic contexts
* Focused scope (universities and schools) makes it achievable within hackathon timeframe
* Results are highly visual and impactful for policymakers
* Multi-modal approach is necessary given Maldives' geography

