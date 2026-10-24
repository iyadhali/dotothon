"""Build data/external/fares/air_fares.csv: Maldives domestic air, seaplane and air-ambulance fares.

Inputs (read-only):
  data/external/air/airports.csv, data/external/air/domestic_routes.csv
  Observed fares are hand-coded below from sources saved in data/external/fares/air_sources/
Outputs:
  data/external/fares/air_fares.csv
  data/external/fares/air_fares_model.json  (regression coefficients and ratios)

Run: python -I scripts/fares_build_air.py
"""
import csv, json, math, os, sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AIR = os.path.join(ROOT, "data", "external", "air")
OUT = os.path.join(ROOT, "data", "external", "fares")
USD = 15.42  # MVR per USD (task convention; official peg-band rate)

COLS = ["mode", "operator", "origin", "origin_atoll", "destination", "destination_atoll", "fare_amount",
        "currency", "fare_mvr", "fare_type", "trip_type", "distance_km", "duration_min", "source_url",
        "source_date", "confidence", "notes"]

# ---------------------------------------------------------------- reference data
airports = {}
for r in csv.DictReader(open(os.path.join(AIR, "airports.csv"), encoding="utf-8")):
    if r["iata"]:
        airports[r["iata"]] = dict(atoll=r["atoll_name"], lat=float(r["lat"]), lon=float(r["lon"]))

routes = OrderedDict()  # (o,d) -> dict ; first operating airline wins
for r in csv.DictReader(open(os.path.join(AIR, "domestic_routes.csv"), encoding="utf-8")):
    o, d = r["origin_iata"], r["dest_iata"]
    if o not in airports or d not in airports:
        continue
    key = (o, d)
    if key in routes:
        continue
    if r["airline"] == "Manta Air" or "suspended" in r["status"]:
        continue  # ceased / suspended operators (kept out of current-fare grid)
    routes[key] = dict(airline=r["airline"], km=float(r["distance_km"]),
                       block=int(float(r["block_time_min"])) if r["block_time_min"] else None,
                       status=r["status"])


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def km(o, d):
    if (o, d) in routes: return routes[(o, d)]["km"]
    if (d, o) in routes: return routes[(d, o)]["km"]
    a, b = airports[o], airports[d]
    return round(hav(a["lat"], a["lon"], b["lat"], b["lon"]), 1)


def block(o, d):
    for k in ((o, d), (d, o)):
        if k in routes and routes[k]["block"]: return routes[k]["block"]
    x = km(o, d)  # same distance model as domestic_routes.csv
    return round(15 + 0.2 * x) if x < 100 else round(27.1 + 0.125 * x)


def atoll(code):
    return airports[code]["atoll"] if code in airports else ""


# excess baggage, MVR per kg (Maldivian baggage-policy page, fetched 2026-10-24)
EXCESS = {}
for dests, rate in [("HAQ HRF HDK", 56), ("IFU NMF LMV MUM", 50), ("FND KDO", 56), ("DRV TMF", 44),
                    ("GKK KDM RUL FMT", 68), ("FVM", 77), ("GAN", 80)]:
    for x in dests.split(): EXCESS[("MLE", x)] = rate
for a, b, rate in [("FVM", "KDM", 30), ("FVM", "KDO", 30), ("GAN", "GKK", 30), ("GAN", "KDM", 30), ("GAN", "KDO", 40),
                   ("IFU", "HAQ", 30), ("IFU", "NMF", 30), ("HAQ", "LMV", 30), ("KDO", "KDM", 30), ("LMV", "IFU", 30),
                   ("LMV", "NMF", 30), ("KDM", "GKK", 30), ("NMF", "HDK", 30)]:
    EXCESS[(a, b)] = rate


def bag_note(o, d):
    r = EXCESS.get((o, d)) or EXCESS.get((d, o))
    return f"excess baggage MVR {r}/kg (Maldivian)" if r else ""


# ---------------------------------------------------------------- sources
S = dict(
    promo24="https://maldivian.aero/assets/files/Press%20Statement%20-%20Promotional%20Fares_14_03_2024%281%29.pdf",
    promo24cm="https://corporatemaldives.com/maldivian-launches-promotional-fares-across-domestic-routes/",
    lmv24="https://corporatemaldives.com/maldivian-slashes-prices-for-madivaru-flights/",
    mum25="https://corporatemaldives.com/maldivian-expands-domestic-network-with-muli-route/",
    ddd26="https://corporatemaldives.com/maldivian-expands-domestic-network-with-kudahuvadhoo-route/",
    south26="https://en.mmtv.mv/7891",
    cut19="https://corporatemaldives.com/air-fares-of-maldivian-decreased-by-25-30/",
    cut19mi="https://maldivesindependent.com/business/domestic-airfare-reduced-as-pledged-143339",
    cut19pr="https://maldivian.aero/media/2019/01/02/fare-reduction-on-all-local-sectors.html",
    roadha19="https://corporatemaldives.com/roadha-promotional-fares-available-at-maldivian/",
    mfr23="https://mfr.mv/travel-and-tourism/increasing-fares-for-domestic-airline-travel",
    ooredoo24="https://maldivian.aero/assets/files/Press%20Release%20-%20Ooredoo%20Fun%20Run%20(for%20Maldivian%20website)%20(1).pdf",
    thoddoo26="https://corporatemaldives.com/maldivian-to-launch-scheduled-seaplane-service-to-thoddoo-enhancing-local-tourism-access/",
    velidhoo26="https://corporatemaldives.com/maldivian-seaplane-expands-network-with-velidhoo-route/",
    lux="https://luxatolls.com/atolls/",
    luxidx="https://luxatolls.com/maldives-pricing-index/",
    amal="https://amaldives.com/plan-your-trip/maldives-budget-travel-complete-guide-2026",
    av26="https://www.aviatorsmaldives.com/post/20565",
    atolltr="https://atolltransfer.com/how-to-choose-maldives-transfer (saved by sea/land task: data/external/fares/sea_land_sources/atolltransfer_*.txt)",
    tmafaq="https://www.transmaldivian.com/faq/",
    tmacom="https://transmaldivian.com/local-community/",
    aasandha="https://aasandha.mv (scheme page; saved data/external/economics/aasandha_nspa/html/aasandha-scheme.html)",
    yb1824="https://statisticsmaldives.gov.mv/yearbook/2026/wp-content/uploads/sites/13/2026/09/18.24.xlsx",
    amb25="https://corporatemaldives.com/one-year-on-maldivians-air-ambulance-service-supports-931-patients/",
    mfrAas="https://mfr.mv/soes/how-aasandha-works",
)

rows = []


def add(mode, op, o, d, amt, cur, ftype, trip, src, sdate, conf, notes, dist=None, dur=None, oat=None, dat=None):
    mvr = round(amt * USD) if cur == "USD" else round(amt)
    if dist is None and o in airports and d in airports: dist = km(o, d)
    if dur is None and o in airports and d in airports: dur = block(o, d)
    rows.append(OrderedDict(mode=mode, operator=op, origin=o, origin_atoll=oat if oat is not None else atoll(o),
                            destination=d, destination_atoll=dat if dat is not None else atoll(d),
                            fare_amount=amt, currency=cur, fare_mvr=mvr, fare_type=ftype, trip_type=trip,
                            distance_km=dist if dist is not None else "", duration_min=dur if dur is not None else "",
                            source_url=src, source_date=sdate, confidence=conf, notes=notes))


# ---------------------------------------------------------------- observed: Maldivian local (MVR) one-way, lowest/promo bucket
PROMO24 = {"GAN": 1222, "FVM": 1155, "RUL": 1133, "FMT": 1133, "HRF": 1133, "KDM": 1333, "GKK": 1111,
           "HDK": 1111, "HAQ": 1111, "TMF": 1111, "KDO": 1055, "FND": 1055, "NMF": 999, "IFU": 999}
# NB: in the PDF table the MLE-KDM / KDM-MLE rows carry MVR 1,333 (also in the Dhivehi table); Corporate Maldives'
# transcription lists Kaadedhdhoo at MVR 1,133. The official table's route codes take precedence.
obs_promo = {}  # (o,d) -> (amount, src, date, conf, note)
for d, f in PROMO24.items():
    obs_promo[("MLE", d)] = (f, S["promo24"], "2024-03-14", "high",
                             "Maldivian promotional (lowest-bucket) local fare, effective 17 Mar 2024, website/app only, selected flights; fares frozen since (minister, Oct 2026)")
obs_promo[("MLE", "KDM")] = (1333, S["promo24"], "2024-03-14", "high",
                             "Maldivian promotional (lowest-bucket) local fare, effective 17 Mar 2024; PDF route rows MLE-KDM = 1,333 (Corporate Maldives transcribes 1,133); fares frozen since")
obs_promo[("MLE", "LMV")] = (949, S["lmv24"], "2024-01-20", "medium",
                             "online-only reduced fare, down from MVR 1,377; promo fare 'already effective' per 14 Mar 2024 release")
obs_promo[("MLE", "DDD")] = (1111, S["ddd26"], "2026-09-14", "medium",
                             "launch promotional fare 'from MVR 1,111' for new Maldivian MLE-DDD daily service (17 Sep 2026)")
# south regional 'lower fares' from 1 Feb 2026 (one-way, MVR)
SOUTH26 = {("GAN", "FVM"): 500, ("FVM", "KDM"): 650, ("FVM", "GKK"): 650, ("GAN", "KDM"): 900, ("GAN", "GKK"): 900}
obs_south = {k: (v, S["south26"], "2026-01-22", "medium",
                 "southern-region lower fare effective 1 Feb 2026 (Maldivian connectivity initiative); one-way")
             for k, v in SOUTH26.items()}

# observed 'regular' local one-way
obs_regular = {
    ("MLE", "LMV"): (1377, S["lmv24"], "2024-01-20", "medium", "previous standard one-way fare before Jan 2024 cut"),
    ("MLE", "MUM"): (1377, S["mum25"], "2025-05-11", "medium", "launch fare 'begins at MVR 1,377 one way' (lowest published, weekly service)"),
    ("MLE", "FVM"): (1600, S["mfr23"], "2023-04-17", "low",
                     "MFR: MLE-FVM went from <=MVR 999 to >=MVR 1,500, then +MVR 100-200; 1,600 = mid estimate of 2023 regular fare; frozen since"),
}

# ---------------------------------------------------------------- models
def ols(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs); sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx; a = my - b * mx
    ss_res = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys)); ss_tot = sum((y - my) ** 2 for y in ys)
    return a, b, 1 - ss_res / ss_tot if ss_tot else float("nan"), n


trunk = [(km(o, d), v[0]) for (o, d), v in obs_promo.items()]
A1, B1, R21, N1 = ols([x for x, _ in trunk], [y for _, y in trunk])
south = [(km(o, d), v[0]) for (o, d), v in obs_south.items()]
A2, B2, R22, N2 = ols([x for x, _ in south], [y for _, y in south])

# regular / promo ratio: LMV 1377/949 ; FVM 1600/1155 ; 2019 high/low return buckets (10 routes)
CUT19 = {"HAQ": (1610, 2226), "IFU": (1500, 2056), "DRV": (1098, 1562), "DDD": (1500, 2056), "TMF": (1610, 2226),
         "KDO": (1610, 2226), "GKK": (1652, 2442), "KDM": (1652, 2442), "FVM": (1698, 2598), "GAN": (1698, 2666)}
ratios = [1377 / 949, 1600 / 1155] + [hi / lo for lo, hi in CUT19.values()]
R_REG = round(sum(ratios) / len(ratios), 3)

# foreigner (USD, flight-only) anchors - LuxAtolls Oct 2026 atoll guides, return midpoints
FOR_ANCH = {("MLE", "GAN"): (250, "200-300"), ("MLE", "HAQ"): (300, "250-350")}


def promo_est(o, d):
    x = km(o, d)
    if o == "MLE" or d == "MLE":
        return round(A1 + B1 * x), "trunk"
    return round(A2 + B2 * x), "regional"


def promo(o, d):
    for k in ((o, d), (d, o)):
        if k in obs_promo: return obs_promo[k][0], True
        if k in obs_south: return obs_south[k][0], True
    return promo_est(o, d)[0], False


f_ratios = []
for (o, d), (usd_ret, _) in FOR_ANCH.items():
    p, _ = promo(o, d)
    f_ratios.append((usd_ret / 2 * USD) / (p * R_REG))
R_FOR = round(sum(f_ratios) / len(f_ratios), 3)

model = dict(
    trunk_model=dict(desc="local lowest/promo one-way MVR = a + b*km, Male-trunk routes (Maldivian, 2024-2026)",
                     a=round(A1, 1), b=round(B1, 3), r2=round(R21, 3), n=N1,
                     points={f"{o}-{d}": [km(o, d), v[0]] for (o, d), v in obs_promo.items()}),
    regional_model=dict(desc="local one-way MVR = a + b*km, inter-atoll regional legs (south, Feb 2026)",
                        a=round(A2, 1), b=round(B2, 3), r2=round(R22, 3), n=N2,
                        points={f"{o}-{d}": [km(o, d), v[0]] for (o, d), v in obs_south.items()}),
    regular_to_promo_ratio=dict(value=R_REG, inputs=[round(r, 3) for r in ratios]),
    foreigner_to_local_regular_ratio=dict(value=R_FOR, inputs=[round(r, 3) for r in f_ratios],
                                          anchors="LuxAtolls flight-only return midpoints MLE-GAN USD250, MLE-HAQ USD300"),
    usd_mvr=USD,
)
print(json.dumps(model, indent=1))

# ---------------------------------------------------------------- current grid (2026-10) per operating route
SDATE_EST = "2026-10-24"
for (o, d), info in routes.items():
    op = info["airline"]
    bn = bag_note(o, d)
    # 1) local lowest one-way
    hit = obs_promo.get((o, d)) or obs_south.get((o, d)) or obs_promo.get((d, o)) or obs_south.get((d, o))
    if hit:
        amt, src, sd, cf, nt = hit
        add("domestic_air", op, o, d, amt, "MVR", "local", "one_way", src, sd, cf, "; ".join(x for x in [nt, bn] if x))
        p_low = amt
    else:
        p_low, which = promo_est(o, d)
        mdl = (f"trunk model {A1:.0f}+{B1:.3f}*km" if which == "trunk" else f"regional model {A2:.0f}+{B2:.3f}*km")
        extra = ""
        if op == "Villa Air":
            extra = "Villa Air local fare not published; Maldivian-based model applied"
        if (o, d) == ("MLE", "DRV"):
            extra = "DRV promo fare 'already effective' Mar 2024 but amount not published; 2019 return MVR 1,098-1,562 (cheapest route)"
        add("domestic_air", op, o, d, p_low, "MVR", "local", "one_way", "model: see research/12_air_fares.md",
            SDATE_EST, "low", "; ".join(x for x in ["estimated", f"lowest-bucket local one-way via {mdl}", extra, bn] if x))
    # 2) local regular one-way
    reg = obs_regular.get((o, d)) or obs_regular.get((d, o))
    if reg:
        amt, src, sd, cf, nt = reg
        add("domestic_air", op, o, d, amt, "MVR", "local", "one_way", src, sd, cf, "; ".join(x for x in ["regular fare", nt, bn] if x))
        p_reg = amt
    else:
        p_reg = round(p_low * R_REG / 5) * 5
        add("domestic_air", op, o, d, p_reg, "MVR", "local", "one_way", "model: see research/12_air_fares.md", SDATE_EST, "low",
            "; ".join(x for x in [f"estimated; typical/regular local one-way = lowest x {R_REG}", bn] if x))
    # 3) local return (regular)
    add("domestic_air", op, o, d, 2 * p_reg, "MVR", "local", "return", "model: see research/12_air_fares.md", SDATE_EST, "low",
        "estimated; 2 x regular one-way (Maldivian prices returns as two one-ways; cf. MLE-KDO special return MVR 2,488 in 2024)")
    # 4) foreigner one-way & return (USD)
    usd_ow = round(p_reg * R_FOR / USD)
    if (o, d) == ("MLE", "VAM"):
        add("domestic_air", op, o, d, 110, "USD", "foreigner", "one_way", S["amal"], "2026", "low",
            "travel-blog range USD 100-120 one-way MLE-Maamigili (Villa Air), midpoint")
    else:
        add("domestic_air", op, o, d, usd_ow, "USD", "foreigner", "one_way", "model: see research/12_air_fares.md", SDATE_EST, "low",
            f"estimated; foreigner fare = local regular x {R_FOR} (anchored on LuxAtolls MLE-GAN/HAQ); tourists pay USD; "
            "Apr 2026 fuel rise added USD 33/sector on MLE-GAN/FVM; Nov 2025 FIT fares -15%; cabinet ordered tourist-fare cut review Aug 2026")
    anch = FOR_ANCH.get((o, d))
    if anch:
        add("domestic_air", op, o, d, anch[0], "USD", "foreigner", "return", S["lux"], "2026-10-22", "low",
            f"LuxAtolls atoll guide: 'around ${anch[1]} return' flight-only, midpoint")
    elif (o, d) == ("MLE", "VAM"):
        add("domestic_air", op, o, d, 220, "USD", "foreigner", "return", S["amal"], "2026", "low", "2 x USD 110 one-way (blog range 100-120)")
    else:
        add("domestic_air", op, o, d, 2 * usd_ow, "USD", "foreigner", "return", "model: see research/12_air_fares.md", SDATE_EST, "low",
            "estimated; 2 x foreigner one-way")

# ---------------------------------------------------------------- foreigner bundles (flight + speedboat), LuxAtolls Oct 2026
BUNDLES = [("DRV", "Baa", 375, "300-450", "domestic flight to Dharavandhoo + 10-30 min speedboat"),
           ("DDD", "Dhaalu", None, "", ""),
           ("IFU", "Raa", 350, "300-400", "domestic flight to Ifuru + speedboat"),
           ("NMF", "Noonu", 400, "350-450", "domestic flight to Maafaru + speedboat"),
           ("VAM", "Alifu Dhaalu", 350, "300-400", "domestic flight to Maamigili + speedboat"),
           ("TMF", "Thaa", 400, "350-450", "domestic flight to Thimarafushi + 20-40 min speedboat"),
           ("KDO", "Laamu", 400, "350-450", "domestic flight to Kadhdhoo + short speedboat"),
           ("GKK", "Gaafu Alifu", 450, "400-500", "domestic flight to Kooddoo + 10-40 min speedboat"),
           ("KDM", "Gaafu Dhaalu", 450, "400-500", "domestic flight to Kaadedhdhoo + 10-30 min speedboat"),
           ("HAQ", "Haa Alifu", 400, "350-450", "domestic flight to Hanimaadhoo + 20-60 min speedboat north to HA resorts")]
for code, at, amt, rng, desc in BUNDLES:
    if amt is None: continue
    op = "Villa Air" if code == "VAM" else "Maldivian"
    add("domestic_air", op, "MLE", code, amt, "USD", "foreigner", "return", S["lux"], "2026-10-22", "low",
        f"resort-transfer bundle 'roughly ${rng} return' per adult ({desc}); includes speedboat - upper bound for flight-only fare; destination atoll of resorts: {at}")

# ---------------------------------------------------------------- historical local fares (2019-2024)
for d, (lo, hi) in CUT19.items():
    add("domestic_air", "Maldivian", "MLE", d, lo, "MVR", "subsidised", "return", S["cut19mi"], "2019-01-10", "high",
        "2019 govt-pledged 25-30% fare cut (state subsidy MVR 35m in 2019); lowest bucket (~15,000 seats/month); historical")
    add("domestic_air", "Maldivian", "MLE", d, hi, "MVR", "subsidised", "return", S["cut19"], "2019-01-10", "high",
        "2019 govt-pledged fare cut; highest bucket; historical")
add("domestic_air", "Maldivian", "MLE", "HAQ", 2800, "MVR", "local", "return", S["cut19mi"], "2018-12", "medium",
    "pre-cut highest return fare (~MVR 2,800); historical")
add("domestic_air", "Maldivian", "MLE", "GAN", 3500, "MVR", "local", "return", S["cut19mi"], "2018-12", "medium",
    "pre-cut highest return fare (~MVR 3,500); historical")
ROADHA = {"DRV": 999, "DDD": 1388, "IFU": 1338, "HAQ": 1477, "TMF": 1477, "KDO": 1477, "GKK": 1515, "KDM": 1515, "GAN": 1544, "FVM": 1544}
for d, f in ROADHA.items():
    add("domestic_air", "Maldivian", "MLE", d, f, "MVR", "local", "return", S["roadha19"], "2019-04-18", "medium",
        "Ramadan 2019 promotional return fare (travel 5-28 May 2019, buy 3 days ahead); historical")
add("domestic_air", "Maldivian", "MLE", "FVM", 999, "MVR", "local", "one_way", S["mfr23"], "2023-04-17", "low",
    "MFR: fare was 'MVR 999 and below' before recent increases (c. 2019-2021); historical")
add("domestic_air", "Maldivian", "MLE", "FVM", 1500, "MVR", "local", "one_way", S["mfr23"], "2023-04-17", "medium",
    "MFR: fare rose to 'MVR 1,500 and above', then a further MVR 100-200 increase (jet fuel MVR 12->22/litre)")
add("domestic_air", "Maldivian", "MLE", "KDO", 2488, "MVR", "local", "return", S["ooredoo24"], "2024-06-27", "high",
    "event special return fare (Ooredoo Fun Run Laamu, travel 4-7 Jul 2024)")

# ---------------------------------------------------------------- patient / subsidised domestic carriage
add("domestic_air", "Maldivian", "ALL", "MLE", 0, "MVR", "patient", "one_way", S["aasandha"], "2025", "medium",
    "Aasandha (state health insurance) pays all transport for approved emergency cases; Maldivian-Aasandha carriage agreement since 2015 (Villa Air since 2022). Non-emergency domestic travel to see a doctor is NOT generally covered (patient pays local fare)",
    dist="", dur="", oat="various", dat="Kaafu")

# ---------------------------------------------------------------- seaplane
add("seaplane", "Maldivian (seaplane)", "MLE", "Thoddoo", 799, "MVR", "local", "one_way", S["thoddoo26"], "2026-02-05", "medium",
    "scheduled seaplane (Thu/Sat, ~20 min); promotional fare for Maldivians; started 12 Feb 2026",
    dist=round(hav(4.1918, 73.5291, 4.4380, 72.9600), 1), dur=20, dat="Alifu Alifu")
add("seaplane", "Maldivian (seaplane)", "MLE", "Velidhoo", 999, "MVR", "local", "one_way", S["velidhoo26"], "2025-12-04", "medium",
    "scheduled seaplane (Wed/Fri) from 23 Jan 2026; promotional one-way fare for local passengers",
    dist=round(hav(4.1918, 73.5291, 5.6650, 73.2730), 1), dur=45, dat="Noonu")
# resort transfers (TMA / Manta / Maldivian seaplane), USD per adult return, LuxAtolls atoll guides Oct 2026
ATOLL_REF = {  # atoll -> (lat, lon, ref description)
    "Baa": (5.15, 73.06, "atoll centre"), "Dhaalu": (2.85, 72.95, "atoll centre"), "Faafu": (3.08, 72.97, "Magoodhoo"),
    "Lhaviyani": (5.33, 73.50, "atoll centre"), "Meemu": (2.95, 73.55, "atoll centre"), "Noonu": (5.80, 73.32, "Orivaru area"),
    "Alifu Alifu": (4.10, 72.85, "North Ari centre"), "Raa": (5.55, 72.98, "atoll centre"), "Shaviyani": (6.25, 73.10, "atoll centre"),
    "Alifu Dhaalu": (3.62, 72.83, "South Ari centre"), "Thaa": (2.35, 73.20, "atoll centre"), "Vaavu": (3.50, 73.48, "atoll centre"),
    "Haa Alifu": (6.95, 72.95, "atoll north")}
SEA = [("Baa", 525, "450-600", 35), ("Dhaalu", 500, "450-550", 35), ("Faafu", 450, "400-500", 35),
       ("Lhaviyani", 525, "450-600", 38), ("Meemu", 500, "450-550", 45), ("Noonu", 575, "500-650", 43),
       ("Alifu Alifu", 450, "400-500", 23), ("Raa", 550, "500-600", 43), ("Shaviyani", 575, "500-650", 55),
       ("Alifu Dhaalu", 475, "400-550", 30), ("Thaa", 600, "550-650", 60), ("Vaavu", 450, "400-500", 25),
       ("Haa Alifu", 600, "600+", 90)]
for at, amt, rng, dur in SEA:
    la, lo, ref = ATOLL_REF[at]
    add("seaplane", "TMA / Manta Air / Maldivian seaplane", "MLE", "(resort water aerodromes)", amt, "USD", "foreigner", "return",
        S["lux"], "2026-10-22", "low",
        f"resort seaplane transfer, per adult return, LuxAtolls range ${rng} (midpoint); daylight only; distance to {ref} (approx.)",
        dist=round(hav(4.1918, 73.5291, la, lo), 1), dur=dur, dat=at)
add("seaplane", "TMA / Manta Air / Maldivian seaplane", "MLE", "(resort water aerodromes)", 617, "USD", "foreigner", "return",
    S["luxidx"], "2026-10-22", "medium",
    "portfolio average of 76 seaplane-transfer resorts (min $332, max $1,950) per adult return; LuxAtolls Pricing Index",
    dist="", dur="", dat="various")
add("seaplane", "TMA / Manta Air / Maldivian seaplane", "MLE", "(resort water aerodromes)", 290, "USD", "foreigner", "one_way",
    S["atolltr"], "2025", "low", "shared seaplane seat via resort: 'from 290 to 900 USD per person' (lower bound); upper bound USD 900",
    dist="", dur="", dat="various")
add("seaplane", "private charter (various)", "MLE", "(resort water aerodromes)", 2600, "USD", "charter", "one_way",
    S["atolltr"], "2025", "low", "private seaplane charter 'from 2,600 to 16,000 USD' per aircraft (lower bound)", dist="", dur="", dat="various")
add("seaplane", "private charter (various)", "MLE", "(resort water aerodromes)", 16000, "USD", "charter", "one_way",
    S["atolltr"], "2025", "low", "private seaplane charter upper bound per aircraft", dist="", dur="", dat="various")
add("seaplane", "Trans Maldivian Airways", "(TMA destinations)", "MLE", 0, "USD", "patient", "one_way", S["tmacom"], "2026", "medium",
    "TMA flies Thalassaemia-affected children and a parent to Male free of charge (CSR). TMA baggage 20 kg + 5 kg hand; excess USD 5/kg",
    dist="", dur="", oat="various", dat="Kaafu")

# ---------------------------------------------------------------- air ambulance
add("air_ambulance", "Maldivian (IASL) air ambulance - MoH/NSPA/Aasandha", "ALL", "MLE", 0, "MVR", "patient", "one_way",
    S["amb25"], "2025-03-19", "high",
    "free at point of use: state air ambulance since 1 Mar 2024 (Dash 8-200 + DHC-6 seaplane, 24/7, 15 medics); 787 flights / 931 patients in year 1; funded by govt (MoH, NSPA, Aasandha); destination = nearest tertiary hospital (often Male)",
    dist="", dur="", oat="various", dat="Kaafu")
# implied cost per air evacuation from Aasandha spend (Statistical Yearbook 2026 T18.24)
air_spend_2023 = 32683397
evac_2023 = 4079
air_share = 31 / 339  # charters per evacuation in a PSM-reported period (research/03 note)
est_air_evacs = evac_2023 * air_share
cost_per = round(air_spend_2023 / est_air_evacs, -3)
add("air_ambulance", "charter (Maldivian / Manta / Villa) paid by Aasandha", "ALL", "MLE", cost_per, "MVR", "charter", "one_way",
    S["yb1824"], "2023", "low",
    f"estimated system cost per air medevac: Aasandha air-evac spend 2023 MVR {air_spend_2023:,} / ~{est_air_evacs:.0f} air evacs "
    f"({evac_2023} evacuations x 31/339 air share); paid by Aasandha, not patient. Air spend fell to MVR 17.3m (2024) and 3.6m (2025) as the state air ambulance took over",
    dist="", dur="", oat="various", dat="Kaafu")
sea_spend_2023 = 22032841
add("air_ambulance", "reference: sea ambulance / speedboat evac paid by Aasandha", "ALL", "(nearest referral hospital)",
    round(sea_spend_2023 / (evac_2023 - est_air_evacs), -2), "MVR", "patient", "one_way", S["yb1824"], "2023", "low",
    f"estimated average Aasandha cost per sea evacuation 2023 (MVR {sea_spend_2023:,} / ~{evac_2023 - est_air_evacs:.0f}); context for air vs sea; patient pays 0",
    dist="", dur="", oat="various", dat="various")

# ---------------------------------------------------------------- write
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "air_fares.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader()
    for r in rows: w.writerow(r)
json.dump(model, open(os.path.join(OUT, "air_fares_model.json"), "w", encoding="utf-8"), indent=1)
print(f"wrote {len(rows)} rows; routes in grid: {len(routes)}")
from collections import Counter
print(Counter((r['mode'], r['fare_type'], r['confidence']) for r in rows))
