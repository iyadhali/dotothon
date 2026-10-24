"""Build key_figures.csv and value_of_time.json. Usage: python -I econ_build_key_figures.py <economics_dir>"""
import sys, csv, json
d = sys.argv[1]
HOURS = 173.0
INC = {'national': 5538, 'male': 7479, 'atolls': 3762}      # HIES2019 avg monthly per-capita income
EXPPC = {'national': 5439, 'male': 7177, 'atolls': 3860}    # HIES2019 monthly per-capita expenditure
MEDEXPDAY = 153.0                                           # national median exp/person/day 2019
EARNER_MED = {'national': 9600, 'male': 12313, 'atolls': 7000}
HHEXP = {'national': 28251, 'male': 37013, 'atolls': 20177}
GRP = {'health': {'national': 1402, 'male': 1498, 'atolls': 1295},
       'transport': {'national': 3091, 'male': 3192, 'atolls': 2980},
       'education': {'national': 1825, 'male': 2554, 'atolls': 1069}}
infl = {2020: -1.3697742556981, 2021: 0.543149688737012, 2022: 2.33054046477249,
        2023: 2.90372427754586, 2024: 1.41093527910134, 2025: 4.00578494118751}
f2025 = 1.0
for v in infl.values():
    f2025 *= 1 + v / 100
A2026 = 4.0
up = f2025 * (1 + A2026 / 100)
PPP2017 = 8.18050575256348
PPP2025 = 7.88991987219358
vot19 = {k: 0.3 * v / HOURS for k, v in INC.items()}
vot26 = {k: round(v * up, 2) for k, v in vot19.items()}
votw26 = {k: round(1.33 * v / HOURS * up, 1) for k, v in EARNER_MED.items()}
spl_usd = max(2.15, 1.15 + 0.5 * MEDEXPDAY / PPP2017)
spl_day19 = spl_usd * PPP2017
spl_mo19 = spl_day19 * 30.4
disc19 = {k: EXPPC[k] - spl_mo19 for k in EXPPC}
thr26 = {k: round(0.4 * disc19[k] * up) for k in disc19}
W = "https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2021/05/HIES2019-Expenditure.pdf"
HI = "https://statisticsmaldives.gov.mv/hies/ (Income-Indicator-HIES2019.xlsx, HIES2019-Expenditure-indicators.xlsx)"
WDI = "https://api.worldbank.org/v2/country/MDV/indicator/"
MW = "https://trade.gov.mv/wp-content/uploads/2023/05/minimum-wage-order-en-v01.pdf"
TV = "https://www.travelocity.com/Maldives-Guest-Houses.d109-aaGuestHouses.Travel-Guide-Accommodation"
rows = []


def add(*a):
    rows.append(a)


for g in ('male', 'atolls', 'national'):
    add("hies_avg_monthly_income_per_capita", INC[g], "MVR/month", 2019, g, HI, "Reported-income households")
    add("hies_median_monthly_income_per_capita", {'national': 4471, 'male': 6250, 'atolls': 3200}[g], "MVR/month", 2019, g, HI, "")
    add("hies_avg_monthly_income_per_household", {'national': 28746, 'male': 38596, 'atolls': 19633}[g], "MVR/month", 2019, g, HI, "")
    add("hies_household_size", {'national': 5.2, 'male': 5.1, 'atolls': 5.2}[g], "persons", 2019, g, HI, "")
    add("hies_monthly_expenditure_per_capita", EXPPC[g], "MVR/month", 2019, g, W, "")
    add("hies_median_monthly_income_per_earner", EARNER_MED[g], "MVR/month", 2019, g, HI, "Wage proxy: LFS 2024-25 publishes no earnings")
    add("hies_avg_monthly_income_per_earner", {'national': 11154, 'male': 14150, 'atolls': 8053}[g], "MVR/month", 2019, g, HI, "")
    for k in GRP:
        add("hies_spending_share_" + k, round(100 * GRP[k][g] / HHEXP[g], 2), "% of household expenditure", 2019, g, W,
            "Computed %d / %d MVR/household/month (group mean / mean total). Group means do not sum to total, so treat as upper bound; HIES report text gives lower shares (transport 9.9/8.4/12.3 national/Male/atolls; health ~3%%, education ~4%% national)" % (GRP[k][g], HHEXP[g]))
for g, v in (('national', 9.9), ('male', 8.4), ('atolls', 12.3)):
    add("hies_report_share_transport", v, "% of household expenditure", 2019, g, W, "As published in HIES2019 Expenditure report text (via research/11)")
add("hies_atoll_hh_expenditure_low", 15467, "MVR/month", 2019, "Raa (lowest)", W, "Per research/11; per-atoll income not in HIES indicator workbook")
add("hies_atoll_hh_expenditure_high", 24847, "MVR/month", 2019, "AA Dh (highest)", W, "Per research/11")
add("lfs_earnings_availability", "not published", "", 2025, "national", "https://statisticsmaldives.gov.mv/lfs/", "LFS 2024-25 report and annex tables contain employment only, no earnings; HIES 2019 income per earner used")
add("minimum_wage_private_small", 21.63, "MVR/hour (~4500/month)", 2022, "national", MW, "Order of 8 Nov 2021, effective 1 Jan 2022; micro enterprises exempt")
add("minimum_wage_private_medium", 33.65, "MVR/hour (~7000/month)", 2022, "national", MW, "")
add("minimum_wage_private_large", 38.46, "MVR/hour (~8000/month, derived)", 2022, "national", MW, "")
add("minimum_wage_public", 7000, "MVR/month (33.65/h)", 2022, "national", MW, "Permanent staff, >=30 h/week")
for y, v in infl.items():
    add("cpi_inflation_annual", round(v, 2), "%", y, "national", WDI + "FP.CPI.TOTL.ZG", "World Bank WDI; full MBS CPI table not retrieved")
add("cpi_uplift_2019_to_2025", round(f2025, 4), "factor", 2025, "national", WDI + "FP.CPI.TOTL.ZG", "Chained 2020-2025 annual inflation")
add("cpi_inflation_2026_assumed", A2026, "%", 2026, "national", "assumption", "LOW confidence. MBS ECPI (essentials, Male) Sep-2026 YoY is +7.79%, overstates headline")
add("cpi_uplift_2019_to_2026", round(up, 4), "factor", 2026, "national", "derived", "Inflate 2019 MVR to 2026 MVR")
add("mbs_ecpi_male_sep2026", 124.13, "index (Nov 2022=100)", 2026, "male", "https://statisticsmaldives.gov.mv/ecpi-september-2026/", "Essentials only (food, beverages, gas, personal care); YoY +7.79%, MoM +1.69%; not a headline CPI")
add("ppp_conversion_gdp", round(PPP2017, 3), "MVR per intl $", 2017, "national", WDI + "PA.NUS.PPP", "GDP PPP (PA.NUS.PRVT.PP not fetched); SPL base year")
add("ppp_conversion_gdp", 7.825, "MVR per intl $", 2019, "national", WDI + "PA.NUS.PPP", "")
add("ppp_conversion_gdp", round(PPP2025, 3), "MVR per intl $", 2025, "national", WDI + "PA.NUS.PPP", "Latest")
add("who_oop_share_of_che", 18.05, "% of current health expenditure", 2023, "national", "https://ghoapi.azureedge.net/api/GHED_OOPSCHE_SHA2011", "2022: 20.27; 2019: 17.46; 2016: 18.93")
add("who_catastrophic_oop_10pct", 10.27, "% of population", 2016, "national", "https://ghoapi.azureedge.net/api/FINPROTECTION_CATA_TOT_10_POP", "Old >10% threshold; 2009: 19.83; >25%: 4.07 (2016)")
add("aasandha_overseas_spend", 418e6, "MVR", 2025, "national", "research/05_healthcare_data.md", "Aasandha AR 2025; already in project data")
add("aasandha_inter_atoll_critical_patient_transport", 23.4e6, "MVR", 2025, "national", "research/05_healthcare_data.md", "Sea 19.9M, air 3.6M")
add("aasandha_patients_sent_abroad", 15535, "patients", 2024, "national", "research/05_healthcare_data.md", "")
add("lodging_male_guesthouse_low", 400, "MVR/night", 2026, "male", "https://amaldives.com/guesthouses/wind-stay", "LOW confidence. Aggregator snapshots USD ~26-46 cheapest Male guesthouse, x15.4")
add("lodging_male_guesthouse_typical", 700, "MVR/night", 2026, "male", TV, "LOW confidence. USD ~45-53 (Wind Stay from $40; Pine Lodge Hulhumale $53)")
add("lodging_male_guesthouse_high", 1300, "MVR/night", 2026, "male", TV, "LOW confidence. USD ~83 (LemonRock Comfort); mid-range up to USD 180 excluded")
add("rent_male_1bedroom_monthly", 8616, "MVR/month", 2020, "male", "https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2020/08/Rental-Survey-April-2020.pdf", "MBS Rental Survey Apr 2020; ~MVR 285/night long-let equivalent")
add("meals_per_day_estimate", 250, "MVR/day", 2026, "male", "derived from HIES", "LOW confidence. HIES Male per-capita food+restaurants ~MVR 62/day (2019, incl. children)")
for g in vot19:
    add("vot_nonwork", round(vot19[g], 2), "MVR/hour", 2019, g, "derived", "0.3 x per-capita income / 173h (TRN-15)")
for g in vot26:
    add("vot_nonwork", vot26[g], "MVR/hour", 2026, g, "derived", "2019 value x CPI uplift")
for g in votw26:
    add("vot_work", votw26[g], "MVR/hour", 2026, g, "derived", "1.33 x median income per earner / 173h x uplift")
add("societal_poverty_line", round(spl_mo19), "MVR/person/month", 2019, "national", "derived", "max(2.15, 1.15+0.5*median pc consumption) 2017 PPP$; median 153 MVR/day; PPP 8.18")
add("societal_poverty_line", round(spl_mo19 * up), "MVR/person/month", 2026, "national", "derived", "x CPI uplift")
for g, v in thr26.items():
    add("hardship_threshold_40pct_discretionary", v, "MVR/person (2026 prices)", 2026, g, "derived", "40% x (mean pc expenditure - SPL); mean used as median proxy; compare with travel-inclusive OOP")
with open(d + "/key_figures.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f)
    w.writerow("indicator,value,unit,year,geography,source_url,notes".split(","))
    w.writerows(rows)
vot = {
    "vot_mvr_per_hour": {"atolls": vot26['atolls'], "male": vot26['male'], "national": vot26['national'],
                         "confidence": "medium (TRN-15 formula and HIES inputs verified; 2026 inflation assumed)"},
    "vot_work_mvr_per_hour": dict(votw26, confidence="low-medium (HIES 2019 income per earner proxies wage; LFS 2024-25 has no earnings)"),
    "price_year": 2026,
    "method": "VoT_nonwork = 0.3 x HIES 2019 average monthly per-capita income / 173 h, inflated 2019->2026 by chained WDI inflation 2020-25 (x%.4f) plus assumed 4%% for 2026 (total x%.4f). 2019 values: atolls %.2f, Male %.2f, national %.2f MVR/h. Work VoT = 1.33 x median income per earner / 173 x uplift." % (f2025, up, vot19['atolls'], vot19['male'], vot19['national']),
    "cpi_uplift_2019_to_2026": round(up, 4),
    "cpi_uplift_2019_to_2025": round(f2025, 4),
    "lodging_mvr_per_night": {"low": 400, "typical": 700, "high": 1300, "confidence": "low (aggregator USD snapshots; no MVR patient-lodging tariff found); 0 if staying with relatives"},
    "meals_mvr_per_day": {"value": 250, "confidence": "low"},
    "hardship_threshold": {
        "definition": "SDG 3.8.2 (2026): OOP health spend > 40% of discretionary budget (per-capita consumption - SPL); extended with travel and lodging cash costs",
        "spl_mvr_per_person_month_2019": round(spl_mo19),
        "spl_mvr_per_person_month_2026": round(spl_mo19 * up),
        "discretionary_mvr_per_person_month_2026": {k: round(v * up) for k, v in disc19.items()},
        "threshold_40pct_mvr_per_person_2026": thr26,
        "threshold_40pct_mvr_per_household_2026": {'atolls': round(thr26['atolls'] * 5.2), 'male': round(thr26['male'] * 5.1), 'national': round(thr26['national'] * 5.2)},
        "ppp_factor_used": PPP2017,
        "confidence": "medium-low (mean not median expenditure; GDP not private-consumption PPP)"},
    "sources": [HI, W, MW, WDI + "FP.CPI.TOTL.ZG", WDI + "PA.NUS.PPP", "https://ghoapi.azureedge.net/api/GHED_OOPSCHE_SHA2011",
                "https://statisticsmaldives.gov.mv/mbs/wp-content/uploads/2020/08/Rental-Survey-April-2020.pdf", TV,
                "https://statisticsmaldives.gov.mv/ecpi-september-2026/"],
}
json.dump(vot, open(d + "/value_of_time.json", "w", encoding="utf8"), indent=1)
print(json.dumps(vot, indent=1)[:2600])
print(len(rows))
for r in rows:
    if r[0].startswith("hies_spending"):
        print(r[0], r[4], r[1])
