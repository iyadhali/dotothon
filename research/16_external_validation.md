# 16 - External validation of the modelled access scores

Question: do the modelled minutes (same-day, one-way, best departure of the day, reference-day timetable of 2026-10-10) line up with outcomes the model never saw? Short answer: **weakly and only conditionally.** The headline "worse access means more evacuations" does not hold at atoll level. Two checks do hold, but each depends on a sub-sample or on whether the island hosts the facility itself.

Script: `scripts/validate_access_outcomes.py`. Outputs are in `data/processed/validation/`:
- `atoll_access_vs_outcomes.csv`: atoll table, modelled access + outcomes, `estimated_air` = 0 (timetabled) and 1 (with estimated air).
- `validation_correlations.csv` (all atoll Spearman tests) and `validation_island_correlations.csv`.
- `island_aasandha_vs_access.csv` and `island_edu_vs_access.csv`: island joins.
- Scatter PNGs: `atoll_<access>__<outcome>.png` (15 health, 6 education), `island_hosp_min__aasandha_pp.png`, `island_g1112_min__pct_16_19_studying.png`.

## Method

- **Access (per atoll, population-weighted by 2022 resident population of origin islands):**
  - `*_min_reachable`: mean best-of-day elapsed minutes over people who have a same-day route (0 = facility on the island).
  - `*_pct_noroute_of_covered`: % of people with transport data but no same-day route.
  - `hosp_pct_nodata`: % of people on islands with no transport coverage in the model (`no_origin_access` at every hour). 64 of 191 islands.
  - `*_min_penalised`: unreachable counted as 1,440 min (covered islands only).
  - Categories: `health_hospital` (tier 1-3), `health_regional_tertiary`, `education_grade_11_12`. Headline uses `estimated_air = 0`.
- **Greater Male** (Maale, Hulhumaale, Hulhule, Vilin'gili; Hulhule moved out of K) is a separate 21st unit matched to the "Male'" outcome row. "Without" = 20 atolls; "with" = 21. K atoll has 100% no-data after removing Hulhule, so health n is 19 without and 20 with.
- **Outcomes:** evacuations per 1,000 (2023), outpatient visits per person (2023), Aasandha spend per person (2025) from `health_atoll_summary.csv`. Island Aasandha spend 2024 from yearbook Table 18.26 divided by 2022 population (183 of 187 islands matched; 114 have non-zero spend). Education: share of 16-19 year olds studying, Gr 11-12 attendees per 100 aged 16-19, and Malé residents registered on each atoll per 1,000 (census 2022 ED17, ED18, MG13). The reason-for-migration table covers only 7 atolls, so out-migration for education cannot be isolated; MG13 (all reasons, where education is ~45%) is the proxy.
- Spearman rho, two-sided p, n shown. No multiple-comparison correction. About 150 tests were run, so a few p < 0.05 are expected by chance.

## Results

### Health, atoll level (20 atolls excl Greater Male; headline air = 0)

| Access metric | Evacuations /1,000 (expect +) | Outpatient visits /person (expect -) | Aasandha /person |
|---|---|---|---|
| Hospital mean min (reachable), n=19 | +0.28 (p=0.25) | +0.19 (p=0.43) | +0.19 (p=0.43) |
| Hospital % no same-day route, n=19 | -0.02 (p=0.95) | +0.06 (p=0.81) | +0.07 (p=0.78) |
| Regional/tertiary % no route, n=17 | -0.36 (p=0.16) | -0.36 (p=0.16) | **-0.60 (p=0.010)** |
| Regional/tertiary mean min (reachable), n=11 | +0.39 (p=0.24) | -0.29 (p=0.39) | -0.36 (p=0.29) |
| % pop with no data, n=20 | -0.28 (p=0.23) | **-0.68 (p=0.001)** | **-0.77 (p<0.001)** |

Adding Greater Male (n=20-21) changes nothing material: hospital minutes vs evacuations +0.31 (p=0.18); regional % no route vs Aasandha -0.64 (p=0.004). Malé has 0.17 evacuations per 1,000, so it is a legitimate low-need anchor but does not rescue the hospital result.

Reading:
1. **Evacuations: direction is right for hospital minutes (+0.28) and regional minutes (+0.39) but not significant** with n=11-19. Using "% with no route" it is flat or reversed. Not validated.
2. **Outpatient visits: no association** with hospital access. The only strong correlation is with *data coverage* (-0.68), which is a modelling gap, not an access effect (see caveat 1).
3. **Aasandha spend per person falls where regional access is worse** (rho -0.60, n=17, p=0.010; -0.76 among well-covered atolls). Plausible mechanism is suppressed utilisation (people who cannot get to care do not claim). But this sign was not pre-registered and it weakens a lot with estimated air (-0.31, p=0.23).
4. **Coverage-restricted sensitivity** (atolls with <=35% of people uncovered, n=13): hospital minutes vs Aasandha -0.63 (p=0.022) and vs outpatient visits -0.48 (p=0.09); evacuations +0.08 (p=0.79). Better access goes with more recorded care use, evacuations stay null.

### Island level (excl Greater Male)

| Test | n | rho | p |
|---|---|---|---|
| Hospital minutes vs Aasandha per person 2024, all matched islands | 114 | -0.38 | <0.001 |
| Same, **excluding islands that host a hospital** | 96 | +0.02 | 0.81 |
| Regional/tertiary minutes vs Aasandha per person | 68 | -0.23 | 0.06 |

The island-level negative correlation is almost entirely a **billing-location effect**: Aasandha spend is booked where care is delivered, so hospital islands show high spend per resident. Once hospital islands are removed there is no relationship. We do **not** claim island-level validation for health.

### Education

| Test | n | rho | p |
|---|---|---|---|
| Atoll: Gr 11-12 min (reachable) vs % 16-19 studying, all 20 atolls | 19 | +0.01 | 0.98 |
| Atoll: Gr 11-12 min (penalised) vs % 16-19 studying | 19 | -0.25 | 0.31 |
| Atoll: Gr 11-12 min vs Malé residents per 1,000 registered | 19 | +0.03 | 0.90 |
| Atoll, well-covered atolls only: Gr 11-12 min vs % 16-19 studying | 13 | **-0.74** | 0.004 |
| Atoll, well-covered only: Gr 11-12 min vs Gr 11-12 attendees per 100 aged 16-19 | 13 | -0.65 | 0.015 |
| Island: Gr 11-12 min vs % 16-19 studying (>=20 aged 16-19) | 95 | -0.52 | <0.001 |
| Island, excluding islands with Gr 11-12 on site | 58 | -0.21 | 0.12 |

The pattern is the same as health: the full-sample test is null at atoll level; the sign is right once data-gap atolls are dropped or at island level, but at island level most of the signal is "school on the island or not". Out-migration to Malé (all reasons) shows **no relationship** with modelled access (rho ~0). That is not surprising: it is dominated by jobs and family, and people who already left are not "residents" in the denominator.

## Caveats

1. **Data coverage confounds everything.** 64 of 191 islands have no transport coverage. Atoll "mean minutes among reachable" in AA, M, V and Lh covers only the host island (0 min). Atolls with most missing coverage (AA 84%, M 83%, V 69%) are small, low-spend atolls, so the strong "no data" correlations (-0.68, -0.77) are spurious for validation purposes and should not be sold as findings.
2. **Ecological fallacy.** Atoll rho says nothing about individuals; evacuations are triggered by case severity, not just distance, and atoll hospitals differ in capability (tier mix is in the data).
3. **Small n.** 11-19 atolls, so only |rho| > ~0.45-0.55 reaches p < 0.05. Absence of significance here is low power, not proof of no effect. 150-odd tests, no correction; the -0.60 and -0.74 results are exploratory.
4. **Reference-day timetable** (2026-10-10, one weekday) vs outcomes aggregated over 2023-2025 and census 2022. Estimated-air sensitivity changes several coefficients by 0.1-0.3, i.e. results are not robust to the air assumption.
5. **Outcome definitions.** Evacuations are counted by origin atoll (Aasandha-funded only). Aasandha spend is booked at facility and in MVR, so it reflects prices and facility mix. Outpatient visits are government facility counts. 16-19 "studying" counts studying anywhere, including those who moved to Malé to study, which is the opposite direction to what the model is expected to predict for stay-at-home teens.
6. Population weights are 2022 census residents on admin islands; resort and non-admin populations are excluded.

## Slide-ready lines

1. **"Where the model says it is farther to a hospital, Aasandha claims per person are lower"**: rho -0.63 (n=13 well-covered atolls, p=0.02); also -0.60 for regional/tertiary no-route share (n=17, p=0.01). Chart: `atoll_reg_pct_noroute_of_covered__aasandha_exp_per_capita_2025_mvr.png`.
2. **"Longer modelled trips to Gr 11-12 go with fewer 16-19 year olds in school"**: rho -0.74 (n=13 atolls with good coverage, p=0.004); island level -0.52 (n=95). Chart: `atoll_edu_g1112_min_reachable__pct_16_19_studying.png`, plus `island_g1112_min__pct_16_19_studying.png`.
3. **"Honest limit"**: emergency evacuations per 1,000 correlate +0.28 with modelled hospital minutes (n=19, p=0.25): right direction, not significant. We say so, and the model is not claiming to predict evacuations. Chart: `atoll_hosp_min_reachable__evacuations_per_1000_2023.png`.

Suggested one-line framing for judges: "External checks agree in sign on education and on care use, are inconclusive on evacuations, and the biggest weakness they expose is our own transport-data coverage gap."
