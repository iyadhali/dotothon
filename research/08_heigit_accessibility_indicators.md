# 08 — HeiGIT "Maldives – Accessibility Indicators" (HDX)

**Source:** https://data.humdata.org/dataset/maldives-accessibility-indicators
**Publisher:** HeiGIT (Heidelberg Institute for Geoinformation Technology) · **Licence:** CC BY-SA
**Dataset date / last modified:** 25 Feb 2026 (metadata created 19 Dec 2025; update frequency 180 days)
**Related tool:** Open Access Lens — https://giscience.github.io/open-access-lens/#/
**Downloaded:** 2026-10-24 → `data\hdx-heigit-access\` (9 files, raw, untouched)
**Extracted:** `data\processed\heigit\` via `scripts\heigit_extract.py`
**Deeper profile:** see `02_data_profile_hdx_kandu.md` §A

---

## 1. Method (from HDX metadata)

- **Car-only travel isochrones** computed with openrouteservice on OpenStreetMap roads ("areas reachable within a given time or distance **by car**").
- Overlaid on **WorldPop** 100 m constrained population (top-down model, not census counts).
- Thresholds: **schools** by distance 5–50 km (5 km steps); **hospitals** and **primary healthcare** by time 10–120 min (10 min steps).
- Units: geoBoundaries ADM0 (country), ADM1 (atolls/cities), ADM2 (islands, partial).
- Sub-populations: total, school-age, under-5, adults, women of childbearing age, elderly.
- Publisher caveats: OSM completeness, WorldPop pixel-level error, standard road speeds, geoBoundaries ≠ official boundaries.

**Key implication for the Maldives:** there is no ferry, speedboat or air leg. An isochrone cannot leave an island's road network, so it effectively measures *"people living on the same island as a mapped facility."*

References cited by HeiGIT: Geldsetzer et al. 2020 (Lancet Healthy Longevity); Petricola et al. 2022 (IJ Health Geographics); Klipper, Zipf & Lautenbach 2021 (AGILE); Ruiz Sánchez et al. 2025 (AGILE).

## 2. Files

| Raw file (`data\hdx-heigit-access\`) | Content |
|---|---|
| `MDV_{category}_access.gpkg` | Isochrone polygons with population attributes; layers `adm0`, `adm1`, `adm2` |
| `MDV_{category}_access_long.csv` | One row per unit × range × population type |
| `MDV_{category}_access_wide.csv` | One row per unit × range, sub-populations as columns |

`category` ∈ `education`, `hospitals`, `primary_healthcare`.

| Extracted file (`data\processed\heigit\`) | Rows | Use |
|---|---|---|
| `heigit_access_long_all.csv` | 2,168 | All three categories in one table; adds `range_km` / `range_min` |
| `heigit_headline_adm0.csv` | 34 | National cumulative share curve per category |
| `heigit_unit_summary.csv` | per unit × category | Population share within 5/10/50 km (schools) and 10/30/60/120 min (health); HeiGIT-implied population |
| `heigit_coverage_matrix.csv` | per unit | Which categories each atoll/island appears in |
| `geojson\heigit_{category}_{adm0,adm1,adm2}.geojson` | 9 files | EPSG:4326 isochrone polygons, ready for QGIS or web maps |

## 3. Headline numbers (ADM0, total population)

| Service | Threshold | Population reached | Share |
|---|---|---|---|
| School | ≤ 5 km | 207,761 | **46.9%** |
| School | ≤ 50 km | 211,946 | **47.9%** |
| Hospital | ≤ 10 min | 200,318 | **45.2%** |
| Hospital | ≤ 120 min | 203,183 | **45.9%** |
| Primary healthcare | ≤ 10 min | 170,485 | **38.5%** |
| Primary healthcare | ≤ 120 min | 172,046 | **38.9%** |

The curves are almost flat: going from 10 to 120 minutes adds less than 1 percentage point. Beyond the home island, a car can't get anywhere new.

## 4. Atoll-level (ADM1) results

Atolls missing from a category are **omitted, not reported as 0%**. Of the 21 ADM1 units, education covers 10, hospitals 9, and primary healthcare 3.

| Atoll | School ≤ 5 km | Hospital ≤ 60 min | Primary HC ≤ 60 min | HeiGIT-implied pop |
|---|---|---|---|---|
| Malé (MV-MLE) | 99.0% | 99.5% | 99.5% | 162,016 |
| Kaafu (MV-26) | 90.1% | 76.8% | 76.6% | 7,773 |
| Alif Alif (MV-02) | 88.2% | 89.6% | 89.6% | 1,390 |
| Gaafu Dhaalu (MV-28) | — | 86.0% | — | 3,486 |
| Laamu (MV-05) | 29.5% | 65.9% | — | 8,777 |
| Haa Dhaalu (MV-23) | 42.2% | 42.2% | — | 11,840 |
| Noonu (MV-25) | 30.1% | — | — | 1,836 |
| Addu (MV-01) | 21.0% | 21.3% | — | 43,134 |
| Haa Alif (MV-07) | 9.1% | 9.1% | — | 12,145 |
| Raa (MV-13) | 5.3% | — | — | 41,623 |
| Thaa (MV-08) | 3.3% | 3.3% | — | 28,436 |
| *11 other atolls* | *absent* | *absent* | *absent* | — |

## 5. Data-quality issues

1. **Population misallocation (WorldPop):** HeiGIT puts 41.6k people in Raa (Census 2022: 17.6k) and 1.4k in Alif Alif (Census: 8.0k). The national base is about 443k. Use **Census 2022** (Team Kandu `observations.csv`, Yearbook table 3.3) for per-island denominators.
2. **Silent omission:** atolls with no reachable facility drop out instead of showing 0%. Any per-atoll comparison must left-join onto a full atoll list.
3. **OSM facility gaps:** many island schools and health centres are unmapped. The seed points are not the official facility list.
4. **Encoding:** "Malé" is stored as UTF-8. Read with `encoding="utf-8"`; Windows consoles show it garbled.

## 6. How to use it in the project

- **As the baseline and contrast:** *"A car-only global method says about 47% of Maldivians can reach a school and about 46% a hospital, and adding two hours of driving changes almost nothing. Our multi-modal model adds ferries, speedboats and flights and gives the real figure."* This speaks directly to the "innovative approach" and "policy relevance" judging criteria (see `01_datathon_context.md`).
- **Side-by-side map:** HeiGIT `adm1` GeoJSON shaded by share, against our multi-modal island-level results.
- **Replicability:** HeiGIT's pipeline (openrouteservice + WorldPop + geoBoundaries) is global. Positioning our model as a "sea- and air-aware extension" of that open method supports the scalability criterion.
- **Do not** use its population figures or its facility seeds without checking them against the census and the official Ministry of Education and Ministry of Health lists.

## 7. Reproduce

```
python -I scripts\heigit_extract.py data\hdx-heigit-access data\processed\heigit
```
