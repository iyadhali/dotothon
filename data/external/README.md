# External geospatial base layers: Maldives Datathon 2026

These are the base layers for the multi-modal (land/sea/air) accessibility analysis of schools, higher education and health services, by inhabited island.

- **Downloaded:** 2026-10-24. OSM snapshot `osm_base` is about 2026-10-24T05:00Z.
- **CRS:** every vector file is **EPSG:4326 (WGS 84 lon/lat)**; the rasters are EPSG:4326 at 3 arc-seconds. For distances and buffers, reproject to **EPSG:32643 (WGS 84 / UTM 43N)**, which covers the whole archipelago.
- **Scripts:** `C:\Users\user\Music\Datathon\scripts\` (not inside the data folders).
- **Python:** isolated venv at `C:\Users\user\Music\Datathon\.venv` (geopandas, pyogrio/GDAL 3.12, rasterio, rapidfuzz). Run it with `python -I`.

| Script | What it does |
|---|---|
| `osm_fetch.py <out_dir> [layer…]` | Overpass queries, then converts to GeoJSON (raw JSON kept in `osm-overpass/raw/`) |
| `census_island_join.py <external_dir>` | Tidies Census 2022 island tables and builds the census↔COD-AB crosswalk |
| `yearbook_tidy.py <yb_dir> <out_dir>` | Tidies MBS Yearbook 2025 tables 1.5, 10.14 and 10.15 |
| `build_island_status.py <external_dir>` | Builds the island master layer (status, population, resorts, airports) |
| `osm_to_gpkg.py <osm_dir> <stamp>` | Packs the OSM GeoJSONs into one GPKG, split by geometry family |
| `inspect_vec.py`, `inventory_external.py` | Quick summaries and file inventory |

---

## 0. Start here: `_derived/` (built by the scripts above from the sources below)

| File | Rows | Description |
|---|---|---|
| `_derived/mdv_islands_master.gpkg` → layer `islands` (polygons), `island_points` (representative points) | 1,556 | All COD-AB islands. Adds Census 2022 population (place of enumeration and usual residence, by sex and nationality, plus 2014), `inhabited_census2022`, resort names and 2024 beds (MBS/MoT list), airport names and IATA codes (OurAirports), OSM island id and name, OSM industrial-landuse share, atoll-capital flag, yearbook land area and distance to Malé. Also `status`, `join_key` and `worldpop2022_sum` (WorldPop 2022 constrained, zonal sum with all_touched; correlation with census pop2022 r = 0.996). |
| `_derived/mdv_islands_master.csv` | 1,556 | The same attributes plus `lon`/`lat` of the representative point. |
| `_derived/islands_codab_with_census2022.gpkg` | 1,556 | COD-AB islands with census columns only. |
| `_derived/census2022_population_by_island.csv` | 200 | Tidy merge of Census 2022 tables P3 (2022/2014 pop and growth), P5 (sex) and MG12 (usual residents). Covers 187 admin islands, the Malé wards and the Malé city total. |
| `_derived/census2022_to_codab_crosswalk.csv` | 196 | Census locality → `adm2_pcode`, with `match_method` (exact_key / manual / fuzzy) and score. |
| `_derived/yb2025_t1.5_island_area_pop_distance.csv` | 189 | Inhabited islands: land area (ha), population 2022, density, distance to Malé (km), atoll-capital flag. |
| `_derived/yb2025_t10.14_resorts.csv` | 180 | Resorts: name, atoll, island, opening year, beds 2024, distance to the airport. |
| `_derived/yb2025_resorts_to_codab_crosswalk.csv` | 180 | Resort → `adm2_pcode` (173 matched). |
| `_derived/yb2025_t10.15_tourist_establishments_by_island.csv` | 205 | Resorts, hotels and guesthouses (count and beds) by island, Dec 2024. |

`status` values in the master layer (priority order):

| Status | Islands |
|---|---|
| `inhabited` (Census 2022 admin islands, including Malé, Hulhumalé, Vilimalé and Hulhulé) | 191 |
| `resort` (operating in 2024) | 165 |
| `resort_closed_or_planned` | 7 |
| `airport` (non-inhabited island with an airport within 1 km) | 9 |
| `resort_osm_hint` | 5 |
| `industrial_osm_hint` (at least 25 % of the island covered by OSM landuse=industrial/port, e.g. Thilafushi) | 2 |
| `uninhabited_or_unknown` | 1,177 |

Census population matched to polygons totals 447,420 of 448,819 island+ward residents. The only unmatched row is "Harbours (Malé, Hulhumalé & Vilimalé)" (1,399 people living on boats). Resort and industrial islands appear in the census only as aggregates (resorts 52,210; industrial islands 12,656 usual residents), so they have no island-level population.

---

## 1. Islands and administrative boundaries

### `hdx-cod-ab/` : OCHA COD-AB Maldives v02 (recommended island layer)

- **Source:** https://data.humdata.org/dataset/cod-ab-mdv (Government of Maldives / OCHA ROAP; valid from 2024-10-22, reviewed 2025-10-30)
- **Licence:** CC BY-IGO
- **Files:** `mdv_admin_boundaries.geojson.zip`, unzipped into `extracted/`; `mdv_admin_boundaries.xlsx` (attribute tables); `hdx_package_metadata.json`

| Layer | Features | Notes |
|---|---|---|
| `mdv_admin0` | 1 | Country |
| `mdv_admin1` | 21 | Atolls plus Malé City; `adm1_pcode` MV001–MV021 |
| `mdv_admin2` | **1,556** | **Island polygons**: `adm2_name`, `adm2_pcode` (e.g. MV001001), `adm1_name`/`adm1_pcode`, `area_sqkm`, `center_lat`/`center_lon` |
| `mdv_adminpoints` | 1,578 | Label points |
| `mdv_adminlines` | 1,679 | |
| `mdv_atolllines` | 29 | |

- **Gaps:** there is no inhabited/resort/industrial attribute (see `_derived`). Dhivehi names are only at admin0. The 1,556 polygons include sandbanks and reclaimed land, some named `LDxxxx`; the official count is about 1,192 islands. Hulhulé (MV009052) belongs to Kaafu, not Malé City.

**Atoll pcodes:**

| Census abbr. | pcode | Atoll | Census abbr. | pcode | Atoll |
|---|---|---|---|---|---|
| HA | MV001 | Haa Alifu | V | MV010 | Vaavu |
| HDh | MV002 | Haa Dhaalu | F | MV011 | Faafu |
| Sh | MV003 | Shaviyani | Dh | MV012 | Dhaalu |
| N | MV004 | Noonu | M | MV013 | Meemu |
| Lh | MV005 | Lhaviyani | Th | MV014 | Thaa |
| R | MV006 | Raa | L | MV015 | Laamu |
| B | MV007 | Baa | GA | MV016 | Gaafu Alifu |
| AA | MV008 | Alifu Alifu | GDh | MV017 | Gaafu Dhaalu |
| K | MV009 | Kaafu | Gn | MV018 | Gnaviyani |
| ADh | MV020 | Alifu Dhaalu | S | MV019 | Seenu (Addu) |
| (Malé City) | MV021 | Malé | | | |

### `geoboundaries/` : geoBoundaries (wmgeolab, commit 9469f09)

- **Source:** https://www.geoboundaries.org/api/current/gbOpen/MDV/ALL/ and `/gbHumanitarian/MDV/ALL/` (API metadata JSON saved alongside)

| File | Features | Source | Licence |
|---|---|---|---|
| `gbOpen-MDV-ADM0.geojson` | 1 | Sentinel-2 LULC 2021 (detailed coastline) | CC BY 4.0 |
| `gbOpen-MDV-ADM1.geojson` | 21 | OSM/Wambacher 2017 | ODbL |
| `gbOpen-MDV-ADM2.geojson` | 21 | Gov./OCHA 2017 | CC BY 3.0 IGO |
| `gbHumanitarian-MDV-ADM0..ADM3.geojson` | 1 / 5 / 21 / **210** | Gov./HDX 2010 | CC BY 3.0 IGO |

- ADM3 contains 210 polygons of (older) inhabited islands. They have names only, no codes, and use 2010 spellings such as "Thurakunu".
- **Gap:** the data is older than COD-AB v02; use it only as a cross-check.

### `hdx-kontur-boundaries/` : Kontur Boundaries MV 2023-06-28

- **Source:** https://data.humdata.org/dataset/kontur-boundaries-maldives
- **Licence:** ODbL (per HDX)
- **Files:** `kontur_boundaries_MV_20230628.gpkg` (and the `.gz`). 29 features: country, atolls and Malé wards, each with a Kontur population estimate. Atoll level only.

### `osm-overpass/islands_20261024.geojson` and `admin_boundaries_20261024.geojson` (see section 3)

- `islands`: 921 OSM `place=island|islet` features (900 polygons, 1 multipolygon, 20 points); 688 named, 520 with wikidata. Tagging is inconsistent (`landuse`, `tourism`), and there is **no inhabited/resort flag**.
- `admin_boundaries`: 29 relations (21 atolls at admin_level 4, plus Malé city and ward levels).

---

## 2. Population

### `mbs-census-2022/` : Maldives Population and Housing Census 2022 (Maldives Bureau of Statistics)

- **Source page:** https://statisticsmaldives.gov.mv/census-2022/ (snapshot saved as `census-2022-page_snapshot.html`; URL list in `xlsx_urls.txt`)
- **Licence:** MBS official statistics, free to use with attribution ("Source: Maldives Population and Housing Census 2022, MBS"). No explicit open licence is stated.
- **Files:** `xlsx/`, 75 XLSX tables named `<upload yyyy-mm>_<table>.xlsx`, plus `2023-03_Table-P5.pdf`.

**Key island-level tables** (use the `2023-07_*` final versions; `2023-03_*` are provisional):

| Table | Content | Rows |
|---|---|---|
| `2023-07_P3.xlsx` | Resident population by place of enumeration and island, 2022 vs 2014, with growth | 187 admin islands + 9 Malé localities |
| `2023-07_P5.xlsx` | Population by island and sex (Maldivian/foreign) | |
| `2023-08_MG12.xlsx` | **Usual-resident** population by island and nationality | |
| `2023-08_MG10.xlsx` | Enumerated vs usual residence by island | |
| `2023-07_H2.xlsx`, `2023-07_H4.xlsx` | Households and population by living quarters, by island | |
| `2023-09_ED17.xlsx`, `2023-09_ED18.xlsx` | School attendance by level, by island (useful demand side: school-age population) | |
| `2023-07_P6.xlsx` | 5-year age groups by locality | atoll level |
| `2023-09_Island-Level-Indicator-Sheet-Population.xlsx` | Island indicator sheet | |

- National total 515,132: Malé 211,908; admin islands 236,911; non-admin (resorts and industrial) 66,313.
- **Gaps:** resort and industrial island populations exist only as aggregates. "Place of enumeration" counts people where they were on census night, which inflates Malé; MG12 "usual residence" differs. Island names use MBS spellings (see the join notes below). Laamu Gaadhoo was uninhabited in 2022.

### `mbs-yearbook-2025-geo-tourism/` : MBS Statistical Yearbook 2025, chapter 1 (table 1.5) and chapter 10 (tourism)

- **Source:** https://statisticsmaldives.gov.mv/yearbook/2025/ (tourism tables are hosted under `/yearbook/2016/wp-content/uploads/sites/2/2025/07/`)
- **Licence:** MBS, attribution.
- **Files:** `yb_1.1`–`yb_1.5.xlsx` and `yb_10.1`–`yb_10.15.xlsx`
  - **1.5**: population, land area (ha), density and distance to Malé for 189 inhabited localities.
  - **10.14**: all 180 resorts with island, opening year, beds 2007–2024 and distance to the airport (source: Ministry of Tourism).
  - **10.15**: tourist establishments by island, Dec 2024.
- Tidy versions are in `_derived/`.

### `hdx-cod-ps/` : COD-PS Maldives 2022 (UNFPA/MBS)

- **Source:** https://data.humdata.org/dataset/cod-ps-mdv
- **Licence:** CC BY-IGO
- **Files:** `mdv_admpop_2022.xlsx`, `mdv_admpop_adm1_2022.csv`. 21 atoll rows with sex and 5-year age bands, joinable on `ADM1_PCODE` to COD-AB. **Atoll level only.**

### `worldpop/` : WorldPop 100 m population rasters

- **Source:** https://hub.worldpop.org/ (API JSON saved)
- **Licence:** CC BY 4.0 (`licence.txt`)
- **Files:**

| File | Size | Grid | Total population |
|---|---|---|---|
| `mdv_pop_2022_CN_100m_R2025A_v1.tif` (Global2 R2025A **constrained**, alpha version) | 0.36 MB | 1344×9372 px, EPSG:4326, nodata −99999 | 523,069 |
| `mdv_pop_2025_CN_100m_R2025A_v1.tif` | 0.36 MB | same | 528,754 |
| `mdv_ppp_2020_UNadj.tif` (Global 2000–2020 unconstrained, UN-adjusted) | 0.34 MB | 1347×9373 px | 540,542 |

- Other years (2015–2030 R2025A; 2000–2020) are available at the same URL patterns.
- **Use:** intra-island population distribution, for example the walk or ride distance to a school within Malé or Hulhumalé. Island totals should come from the census.

---

## 3. OSM points of interest and networks: `osm-overpass/`

- **Source:** OpenStreetMap via the Overpass API (https://overpass-api.de/api/interpreter), bbox `-1.0,72.4,7.3,74.0`, queried 2026-10-24.
- **Licence:** **ODbL 1.0**, © OpenStreetMap contributors.
- **Format:** one GeoJSON per layer, named `<layer>_20261024.geojson`. Each feature has every OSM tag plus `osm_type`, `osm_id`, `osm_url`, `geom_type`, `rep_lon`/`rep_lat` (a representative point, handy for polygon POIs). Closed ways and multipolygons become Polygons; highways stay LineStrings. Raw Overpass JSON is in `raw/`; the run log is `fetch_log.txt`.

**Recommended format:** `osm_maldives_20261024.gpkg`, which holds all layers split by geometry family (`<layer>_pt`, `_ln`, `_pl`), with columns present in fewer than 1 % of features dropped. The GeoJSONs keep every tag.

| Layer (`<layer>_20261024.geojson`) | Features | Query / content | Main tag counts |
|---|---|---|---|
| `islands` | 921 (901 pl, 20 pt) | `place=island\|islet` | islet 830, island 91; 688 named |
| `admin_boundaries` | 29 | `boundary=administrative` relations | admin_level 4 (atolls): 21; Malé levels 8/9: 7 |
| `places_settlements` | 41 pt | `place=city…locality` nodes | town 23, locality 9, village 7, city 1 |
| `education` | 397 (71 pt, 321 pl, 5 ln) | `amenity=school\|university\|college\|kindergarten\|language_school\|training`, `building=school\|university\|college` | amenity: school 121, kindergarten 26, university 14, college 13. A further 183 have only `building=school` (often the same campus mapped twice: amenity point + building). 182 named. |
| `health` | 251 (121 pt, 129 pl) | `amenity=hospital\|clinic\|doctors\|dentist\|pharmacy`, any `healthcare=*`, `building=hospital` | hospital 63, clinic 19, doctors 18, pharmacy 73, dentist 4 |
| `sea_transport` | 3,790 (109 pt, 2,980 ln, 701 pl) | `amenity=ferry_terminal`, `harbour=*`, `leisure=marina`, `landuse=harbour`, `man_made=pier\|quay\|jetty` | ferry_terminal 69, marina 127, landuse=harbour 61, harbour=yes 22, pier 3,517 (mostly resort and villa jetties), quay 14 |
| `ferry_routes` | 110 ln | `route=ferry` ways | 94 named. Not a timetable: use MTCC/RTL data for schedules. |
| `air_transport` | 95 (11 pt, 32 ln, 52 pl) | `aeroway=aerodrome\|heliport\|helipad\|airstrip\|runway\|terminal\|seaplane_base\|water_runway`, `seaplane=*` | aerodrome 26, runway 32, terminal 32, helipad 5. Seaplane platforms are barely mapped. |
| `roads` | 14,290 (14,286 ln) | all `highway=*` ways, whole country | residential 8,116, footway 1,805, path 1,731, service 1,380, track 453, unclassified 248, tertiary 198, secondary 103; 2,034 named |
| `landuse_resort_industrial` | 919 | `tourism=resort\|hotel\|guest_house`, `leisure=resort`, `landuse=industrial\|military\|port` | tourism=hotel 539 (resorts are mostly tagged as hotels), guest_house 260, leisure=resort 24, landuse=industrial 88, military 8 |

**Coverage checks** (point-in-polygon against the 191 census-inhabited islands, 100 m buffer):

| Feature | Inhabited islands covered |
|---|---|
| OSM schools (`amenity` or `building=school`) | **70 / 191** |
| OSM hospitals, clinics and doctors | **55 / 191** |
| Drivable roads (excluding footway, path and steps) | **186 / 191** |

Greater Malé drivable road length (OSM):

| Island | km |
|---|---|
| Malé | ~61 |
| Hulhumalé | ~83 |
| Vilimalé | ~7 |
| Hulhulé (airport) | ~24 |

**OSM is not enough for the service destinations.** Use the official lists in section 4 (MoE school directory, HEMS registry, higher-ed register) as the authoritative destination set. OSM is good for roads, harbours and jetties, ferry routes and airports, and for placing facilities within Greater Malé.

**Related OSM-derived products:**

### `healthsites-io/` : healthsites.io Maldives (via HDX)

- **Source:** https://data.humdata.org/dataset/maldives-healthsites
- **Licence:** ODbL
- **Files:** `maldives_healthsites.geojson` (174 features: 106 points, 68 polygons) and `.csv`. OSM-derived, with extra fields (`operator`, `beds`, `speciality`).

### `heigit-road-surface/` : HeiGIT Mapillary/OSM road surface

- **Source:** https://data.humdata.org/dataset/maldives-road-surface-data (2024-11)
- **Licence:** ODbL
- **Files:** `heigit_mdv_roadsurface_lines.gpkg`, 12,837 road lines with paved/unpaved prediction.

---

## 4. Official facility lists

These folders were produced by parallel helper processes in this session; see the files themselves for details.

| File | Rows | Content |
|---|---|---|
| `higher-ed-campuses/higher_ed_campuses_by_island.csv` | 203 | Rows hand-built from the **MoE Register of Higher Education and Training Institutions** (PDF saved alongside, https://www.moe.gov.mv/storage/files/resources/1791106952537-Dhaftharu-%20Registered%20Colleges%20and%20Institutes%20(1).pdf). Covers 32 university campuses (MNU, IUM, etc.), 46 college campuses and 125 institutes. 99 rows have an island (51 distinct atoll+island pairs); 104 institute rows have no stated location (most likely Malé). 5 inferred locations are flagged in `notes`. © MoE, all rights reserved. |
| `moe-school-statistics-2024/island_enrolment_2024.csv` | 208 | MoE **2024 School Statistics** (Nov 2024; PDF saved alongside, https://www.moe.gov.mv/storage/files/statistics/1782980847582-2024%20School%20Statistics.pdf). Enrolment by grade and sex for 187 islands plus 21 atoll totals (98,845 students). Island aggregates, not per school. Malé is reported as "Greater Malé Region". Seenu shows only 4 island rows. |
| `education/moe_school_directory/moe_school_directory.csv` | 220 | **MoE school directory** (https://www.moe.gov.mv/en/schools/<id>): school, atoll, island, opening date, status, students, teachers. |
| `education/` (other) | | MoE School Statistics PDFs 2019–2024, MBS yearbook chapter 7 (education), MoE registered colleges, annual reports |
| `health/moh_hems_registry/hems_facilities_tidy.csv` | 601 | **Ministry of Health HEMS facility registry**: name, status, public/private, owner, level (e.g. "Health Centre Grade 3"), tier, atoll, island, registration and licence numbers. |
| `health/` (other) | | MBS yearbook health and Aasandha tables (`MANIFEST.tsv`), MoH Maldives Health Statistics, WHO GHO, World Bank WDI |
| `air/` | | Airline (Maldivian, Manta), TMA, Velana FIS flight scrapes, Wikipedia airport pages and a second OurAirports copy |

All official lists are **island-level only (no coordinates)**. To place them on the map, join them to `_derived/mdv_islands_master.gpkg` on atoll code + normalised island name (below), then use the island point or the matching OSM POI.

---

## 5. Airports: `ourairports/`

- **Source:** https://davidmegginson.github.io/ourairports-data/airports.csv and `runways.csv`
- **Licence:** Public Domain (OurAirports)
- **Files:**
  - `airports_world.csv`, `runways_world.csv`: full downloads.
  - **`airports_MV.csv` / `airports_MV.geojson`**: 31 rows (3 large: MLE, GAN, HAQ; 4 medium: NMF, KDO, KDM, VAM; 13 small; 11 seaplane bases), with lat/lon, IATA/ICAO codes, `scheduled_service` and municipality.
  - `runways_MV.csv`: 11 rows.
- **Gaps:** the seaplane-base list is very incomplete. TMA and Manta serve more than 100 resort lagoons; use `osm-overpass/air_transport` and the resort list for those. Some domestic airports have `scheduled_service=no` although they are served. Check against `air/` (Maldivian destinations).

---

## 6. Joining population and facilities to islands

Dhivehi→Latin transliterations vary widely between sources, for example:

- Thuraakunu / Thurakunu
- Kun'burudhoo / Kuburudhoo / Kunburudhoo / Kumburudhoo
- Vilin'gili / Villingili / Vilimaale / Villimale'
- Dhidhdhoo / Dhihdhoo
- Bileiydhoo / Biledhdhoo / Bilehdhoo
- Hoarafushi / Huvarafushi
- Fares-Maathodaa / Faresmaathodaa / Maathodaa
- Malé / Male' / Maale

Island names are also **not unique nationally**. There are several Hulhudhoo, Maafushi, Viligili and Fenfushi islands, so **never join on name alone**.

**Recommended join key:** `join_key = adm1_pcode + "|" + norm(island_name)`. It is stored in `_derived/mdv_islands_master.*`; `norm()` is `census_island_join.norm_name`.

**Step 1: get the atoll pcode.** Map the source's atoll code or name to the COD-AB `adm1_pcode` using the table in section 1. Sources write the same atoll in several ways:

- HA, H.A., Haa Alif, North Thiladhunmathi → MV001
- ADh, A.Dh., Alif Dhaal, South Ari → MV020
- K, Kaafu, North/South Malé Atoll → MV009
- Malé City → MV021 (plus Hulhulé in MV009)

**Step 2: normalise the island name with `norm_name()`.** It applies these rules in order:

1. ASCII-fold and lower-case the name.
2. Drop COD-AB's nasal marker `n'`, so `Ban'didhoo` becomes `Badidhoo`.
3. Strip punctuation, spaces and parenthesised parts.
4. Collapse long vowels: `aa→a`, `ee→i`, `oo→u`.
5. Drop the aspiration `h` in digraphs: `th→t`, `dh→d`, `sh→s`, `lh→l`, `gn→n`.
6. Collapse doubled letters (`Villingili` = `Viligili`).
7. Remove the pre-consonant `h` in `hd`, `hf`, `hk` and `ht` (`Dhihdhoo` = `Dhidhdhoo`).

**Step 3: match within the atoll only, in this order:**

1. **Manual overrides.** For Malé wards: Henveiru, Galolhu, Machchangolhi and Maafannu → Maale (MV021001); Vilimaale → Vilin'gili (MV021002); Hulhumaale Phase 1 and 2 → Hulhumaale (MV021003); Hulhule → MV009052. For Laamu: "Gamu" (census) = Gan (MV015013).
2. **Exact normalised key.** When there are duplicates, take the largest polygon.
3. **Hyphen and "and" parts** ("Maafushi and Kedhigandu").
4. **Fuzzy match** (rapidfuzz ratio ≥ 80–85) within the atoll. Review every fuzzy match manually (they are listed in the crosswalk CSVs).

**Results:**

| Source | Matched | Notes |
|---|---|---|
| Census 2022 | 195/196 | 176 exact, 9 manual, 9 fuzzy, 1 exact-of-duplicates. The only unmatched row is the boat-dwelling "Harbours" population. |
| Yearbook 1.5 | 189/189 | Addu "Meedho" (a yearbook typo) is matched manually |
| Resorts | 173/180 | |

**Notes and pitfalls:**

- Addu City (Seenu) is reported per island (Hithadhoo, Maradhoo, Maradhoo-Feydhoo, Feydhoo, Hulhudhoo, Meedhoo), but the islands are causeway-linked. Treat them as one land network.
- Fuvahmulah is a single island and city.
- Hulhumalé Phase 1 and Phase 2 are one COD-AB polygon.
- For the census use P3 or P5 (enumerated) or MG12 (usual residence) consistently. MG12 is better for "population served"; P3 has the 2014 comparison.
- The MoE enrolment, school directory and HEMS lists use Dhivehi-style names with curly apostrophes (`Kan’duhulhudhoo`). Replace `’` with `'` before applying `norm_name`.
- Join OSM POIs to islands **spatially** (point-in-polygon against `mdv_islands_master/islands`, buffered about 50 m for harbours and jetties that sit just offshore), not by name.

---

## 7. Known gaps and caveats

1. **Island status beyond inhabited and resort is weak.** No official list of industrial islands (fish plants, Thilafushi, Gulhifalhu, etc.), airport-only islands or agricultural or picnic islands was found. The OSM landuse hints flag only 2 industrial islands; Felivaru (Lh) has only 17 % industrial cover and stays `uninhabited_or_unknown`. Census industrial and resort population (12,656 + 52,210) is aggregate only.
2. **COD-AB has 1,556 polygons against the official ~1,192 islands.** It includes sandbanks, lagoon reclamations (e.g. `LD1509` = Hoarafushi airport) and finolhu islands. Filter by `status`/`area_sqkm` for display.
3. **Seven resorts are unmatched to polygons** (Bandos, Emboodhoofalhu ×3, Kudavillingili, a lagoon-only project, and one row with no island). Fuzzy matches such as `Maadhoo Finolhu → Medhufinolhu` need checking.
4. **The higher-ed register lacks locations** for 104 institute rows. The MoE school directory has 220 schools, but the 2024 statistics count 187 islands with enrolment; reconcile the two. Neither has coordinates.
5. **OSM POI completeness is low outside Greater Malé** (see the coverage checks). Tags are messy: building-only schools, resort jetties tagged `man_made=pier`, and seaplane platforms largely unmapped.
6. **There are no inter-island travel times here.** Sea and air connectivity must come from the datathon datasets (MTCC, MACL, RTL in `../team-kandu`, Avas/FollowMe). OSM `ferry_routes` is only geometry.
7. **WorldPop R2025A is an alpha release.** It has a 2022 total of 523k against the census 515k and puts population on resort islands. Use it only for intra-island distribution.
8. **Licences:**

    | Licence | Datasets |
    |---|---|
    | ODbL | OSM, healthsites, HeiGIT, Kontur, geoBoundaries ADM1 |
    | CC BY-IGO | COD-AB, COD-PS |
    | CC BY 4.0 | WorldPop, geoBoundaries ADM0 |
    | Public domain | OurAirports |
    | Attribution only, no open licence stated | MBS census and yearbook |
    | All rights reserved | MoE PDFs |

    ODbL requires attribution ("© OpenStreetMap contributors"), and derivative databases must be shared alike.
9. **WorldPop sizes are tiny** (about 0.35 MB each). Further years can be fetched from the same URL pattern (`.../R2025A/<year>/MDV/v1/100m/constrained/mdv_pop_<year>_CN_100m_R2025A_v1.tif`).
10. **Not attempted or blocked:** an official Ministry of Tourism resort registry with coordinates (yearbook 10.14 used instead), the Aasandha provider network list, and ium.edu.mv (TLS error).
