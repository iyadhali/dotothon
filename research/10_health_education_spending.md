# 10. Household income, spending and cost parameters (health and education access)

Outputs: `data/external/economics/key_figures.csv`, `value_of_time.json`. Built by `scripts/econ_build_key_figures.py` (inputs dumped by `econ_dump_hies.py`, `econ_dump_lfs.py`). Prices are MVR; "2026" means inflated from 2019 with the factor below.

## 1. Headline parameters (2026 MVR)

| Parameter | Atolls | Malé | National | Confidence |
|---|---|---|---|---|
| Non-work VoT (MVR/h) = 0.3 x per-capita income / 173 h | 7.47 | 14.86 | 11.00 | medium |
| Work VoT (MVR/h) = 1.33 x median income per earner / 173 h | 61.6 | 108.4 | 84.5 | low-medium |
| 40% hardship threshold, per person per month | 572 | 2,092 | 1,295 | medium-low |
| Same, per household (5.2 / 5.1 persons) | 2,974 | 10,669 | 6,734 | medium-low |

- Lodging per night in Malé: low 400, typical 700, high 1,300 (low confidence). Use 0 when staying with relatives.
- Meals: about 250 per day (low confidence).
- CPI uplift 2019 to 2025 = 1.1014 (chained WDI inflation); 2019 to 2026 = 1.1454 (assumes 4% for 2026).
- The 2019 VoT values are 6.52 (atolls), 12.97 (Malé) and 9.60 (national). They are slightly different from research/11 (6.7 / 12.6), which used expenditure; here per-capita income is used as the brief specifies.

## 2. HIES 2019 (MBS) [verified, local files in `mbs_hies2019/`]

| Indicator | National | Malé | Atolls |
|---|---|---|---|
| Average income per capita (MVR/month) | 5,538 | 7,479 | 3,762 |
| Median income per capita | 4,471 | 6,250 | 3,200 |
| Average income per household | 28,746 | 38,596 | 19,633 |
| Household size | 5.2 | 5.1 | 5.2 |
| Median income per earner | 9,600 | 12,313 | 7,000 |
| Average expenditure per capita | 5,439 | 7,177 | 3,860 |
| Health, transport, education: group mean as % of mean household expenditure | 5.0 / 10.9 / 6.5 | 4.1 / 8.6 / 6.9 | 6.4 / 14.8 / 5.3 |

- Per-atoll income is not in the indicator workbook. Only the expenditure range is available (Raa 15,467 to AA Dh 24,847 per household per month).
- Caveat on shares: the group means in the workbook do not sum to the mean total, and the report text shows lower shares (transport 9.9 / 8.4 / 12.3; health about 3%; education about 4% nationally). The health and education shares in the CSV are therefore upper bounds. Resolving them needs the HIES tables (app.statisticsmaldives.gov.mv/hies-data/), which were not tried.

## 3. Wages

- LFS 2024-25 (released Oct 2025, revised report May 2026) was downloaded to `wages_income/`. Its report and Annex 2 tables cover employment only and have no earnings. LFS therefore gives no wage figure.
- Proxy: HIES 2019 median monthly income per earner (see table above). No later wage source was found.
- Minimum wage (Order of 8 Nov 2021, effective 1 Jan 2022; `wages_income/minimum_wage_order`): small enterprises MVR 21.63/h (about 4,500/month), medium 33.65/h (about 7,000), large 38.46/h (about 8,000, derived), micro enterprises exempt, public sector 7,000/month. No later replacement order was found; this is not confirmed.

## 4. Prices

- WDI annual inflation (FP.CPI.TOTL.ZG): 2020 -1.37%, 2021 0.54%, 2022 2.33%, 2023 2.90%, 2024 1.41%, 2025 4.01%.
- 2026 inflation is assumed at 4% (low confidence). The MBS Essential Commodities Price Index for Malé (base Nov 2022 = 100) was 124.13 in Sep 2026, up 7.79% year on year. It covers only food, beverages, gas and personal care, so it overstates headline CPI. The MBS headline CPI tables were not located.
- PPP conversion (PA.NUS.PPP, GDP basis): 2017 8.18, 2019 7.83, 2025 7.89 MVR per international dollar. The private-consumption PPP (PA.NUS.PRVT.PP) was not fetched.
- Social poverty line (SDG 3.8.2) calculation: median consumption of MVR 153 per day gives 1.15 + 0.5 x 153/8.18 = USD 10.5 (2017 PPP), or about MVR 2,612 per month in 2019 and 2,991 in 2026. This agrees with the estimate of about 2,640 in research/11.
- Threshold = 40% x (mean per-capita expenditure - SPL). Mean stands in for the per-person distribution, so it is an approximation. Travel costs are added to out-of-pocket spending, which goes beyond the official indicator.

## 5. Health financing

- WHO GHED out-of-pocket share of current health expenditure: 18.05% (2023), 20.27% (2022), 17.46% (2019); it was 63% in 2000.
- Catastrophic spending above 10% of the household budget: 7.3% (2004), 19.8% (2009), 10.3% (2016). Above 25%: 4.1% (2016). These are the old SDG 3.8.2 definitions, and no later year exists in GHO.
- Aasandha 2025 (already in research/05, not duplicated): overseas treatment MVR 418 M; inter-atoll critical-patient transport MVR 23.4 M; 15,535 patients sent abroad (2024). Patient-travel or escort spending separate from these was not found.

## 6. Lodging evidence (low confidence)

- No MVR tariff for patient lodging was found. Aggregator snapshots (Travelocity, operator site) show Malé guesthouses from about USD 26-46, Hulhumalé about USD 53, and USD 83 for a higher guesthouse. At MVR 15.4 per USD this gives 400 / 700 / 1,300.
- MBS Rental Survey April 2020: a 1-bedroom flat in Malé averaged MVR 8,616 a month (about MVR 285 a night over a month); 2-bedroom 14,217.
- research/11 assumed 600 for lodging and 200 for meals; the new values are close to those.

## 7. Failed or incomplete sources

- World Bank API through curl and WebFetch timed out. The existing local WDI/GHED downloads were used instead.
- statisticsmaldives.gov.mv/consumer-price-index/ returned 404, so no headline CPI index. health.gov.mv and aasandha.mv were not re-fetched (data already local).
- Google search pages, tradingeconomics and TripAdvisor (403) and Wikipedia gave no usable wage or lodging figures.
- LFS 2024-25 has no earnings. Student lodging and patient-travel news were not found; the `news_patient_travel` and `mohe_higher_ed` folders are still empty.

## 8. Gaps to close

1. A Maldives wage by atoll or region (the LFS microdata or a Statistical Yearbook labour table, or the MIRA/Pension Office data).
2. The headline MBS CPI for 2020-2026, to replace the assumed 4% for 2026.
3. The private-consumption PPP factor.
4. HIES 2019 health and education shares from the table-level data.
5. An MVR tariff for patient accommodation (for example NSPA or a hostel for patients) and ferry or dhoni escort fares.
