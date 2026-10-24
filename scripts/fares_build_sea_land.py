"""Build sea_land_fares.csv and sea_land_fares_model.json from downloaded sources. Run: python -I fares_build_sea_land.py"""
import csv, json, math, statistics as st, collections
B = r"C:/Users/user/Music/Datathon/data/"
S = B + "external/fares/sea_land_sources/"
OUT = B + "external/fares/"
FX = 15.42
COLS = "mode,operator,origin,origin_atoll,destination,destination_atoll,fare_amount,currency,fare_mvr,fare_type,trip_type,distance_km,duration_min,source_url,source_date,confidence,notes".split(",")
rows = []


def add(mode, op, o, oa, d, da, amt, cur, ftype, trip, km="", dur="", url="", date="", conf="medium", notes=""):
    mvr = round(amt * FX, 2) if cur == "USD" else amt
    rows.append(dict(mode=mode, operator=op, origin=o, origin_atoll=oa, destination=d, destination_atoll=da,
                     fare_amount=amt, currency=cur, fare_mvr=mvr, fare_type=ftype, trip_type=trip, distance_km=km,
                     duration_min=dur, source_url=url, source_date=date, confidence=conf, notes=notes))


# ---------- 1. RTL gazette fares (official, MVR) ----------
g = list(csv.DictReader(open(S + "rtl_gazette_fares_parsed.csv", encoding="utf-8")))
best = {}
for x in g:
    if x["cancelled"] != "False" or not x["one_way_mvr"]:
        continue
    k = (x["origin"], x["origin_atoll"], x["destination"], x["destination_atoll"])
    if k not in best or x["pub_date"] > best[k]["pub_date"]:
        best[k] = x
gaz = list(best.values())
HW = {"198739", "207576", "259922", "369391", "382053"}


def is_hw(x):
    """Highway Link (inter-zone) tariff: dedicated notices; the 55 MVR Hulhumeedhoo-Feydhoo row in 259922 is an ordinary intra-atoll hop."""
    return x["gazette_id"] in HW and not (x["gazette_id"] == "259922" and float(x["one_way_mvr"]) == 55)


for x in gaz:
    exact = x["origin_match"] == "exact" and x["destination_match"] == "exact"
    inter = is_hw(x)
    url = "https://www.gazette.gov.mv/iulaan/" + x["gazette_id"]
    km = x["gc_km"]
    for trip, v in (("one_way", x["one_way_mvr"]), ("return", x["return_mvr"])):
        if not v:
            continue
        add("fast_ferry_rtl", "MTCC / Raajje Transport Link", x["origin"], x["origin_atoll"], x["destination"], x["destination_atoll"],
            float(v), "MVR", "flat", trip, km, "", url, x["pub_date"], "high" if exact else "medium",
            f"Gazette notice IUL {x['gazette_id']}: {trip} MVR {float(v):g} "
            f"({'inter-zone Highway Link tariff' if inter else 'standard island-to-island tariff'}); single tariff, no local/foreigner split in notice; "
            f"distance = great-circle km (sea route longer); name match {'exact' if exact else 'fuzzy'}")

# ---------- 2. Greater Male taxi (gazette 2024-05, 290173) ----------
T = "https://www.gazette.gov.mv/iulaan/290173"
zk = {}
for r in csv.DictReader(open(S + "avas_zone_pair_distances.csv")):
    zk[(r["from_zone"], r["to_zone"])] = (r["median_km"], r["median_min"], r["n_rides"])
Z = {"M": "Male", "H1": "Hulhumale Phase 1", "H2": "Hulhumale Phase 2", "A": "Velana International Airport"}
tax = [("M", "M", 30, 45), ("M", "H1", 85, 130), ("M", "H2", 100, 155), ("M", "A", 70, 110), ("H1", "M", 85, 130),
       ("H1", "H2", 40, 60), ("H1", "A", 80, 125), ("H2", "M", 100, 155), ("H2", "H1", 40, 60), ("H2", "A", 85, 130),
       ("A", "M", 70, 110), ("A", "H1", 80, 125), ("A", "H2", 85, 130), ("H1", "H1", 30, 45), ("H2", "H2", 30, 45)]
for a, b, f6, f10 in tax:
    km, mn, n = zk.get((Z[a], Z[b]), ("", "", ""))
    for lab, f in (("under-6-seat car", f6), ("7-10 seat vehicle", f10)):
        add("taxi", "Taxi (Ministry of Transport fixed fare)", Z[a], "K", Z[b], "K", f, "MVR", "flat", "per_trip", km, mn, T, "2024-05-14",
            "high", f"Gazette IUL 472/1/2024/58 (effective 20 May 2024) {lab}: MVR {f}; distance/time = Avas Ride median of {n} rides; "
            "extras: +MVR10 (small)/+15 (large) for domestic terminal, +5 per bag beyond 3")
add("taxi", "Taxi (Transport Authority)", "Male", "K", "Hulhumale (Phase 1)", "K", 40, "MVR", "flat", "per_trip", "", "",
    "https://corporatemaldives.com/government-fixed-a-maximum-price-that-can-be-charged-for-a-taxi-journey-from-male-to-hulhumale/",
    "2018-09-11", "medium", "Historical 2018 cap 'From Male' to Hulhumale' and vice versa- MVR 40'; superseded (2019: 75, 2022/2024: 85)")
add("taxi", "Taxi (Transport Authority)", "Male", "K", "Hulhumale (Phase 1)", "K", 75, "MVR", "flat", "per_trip", "", "",
    "https://corporatemaldives.com/ministry-of-transport-and-civil-aviation-unveils-the-permitted-taxi-applications-and-taxi-fares/",
    "2019-08-03", "medium", "Historical 2019 fare 'MVR 75 for each trip between Male' and Hulhumale'' (gazette IUL 202-M/1/2019/67); superseded")

# ---------- 3. Ride-hailing (Avas Ride matrix) ----------
M = list(csv.reader(open(B + "Avas_Ride/car_fare_matrix.csv", encoding="utf-8")))
hdr = M[0][2:]
for r in M[1:]:
    o = r[1]
    for d, v in zip(hdr, r[2:]):
        km, mn, n = zk.get((o, d), ("", "", ""))
        add("ride_hailing", "Avas Ride", o, "K", d, "K", float(v), "MVR", "flat", "per_trip", km, mn,
            "local file: data/Avas_Ride/car_fare_matrix.csv", "", "medium",
            f"Avas Ride zone fare matrix (from {o} to {d}); equals regulated taxi tariff where zones overlap (e.g. Male->HM1 85, Male->VIA 70); "
            + (f"distance/time = median of {n} Avas rides" if km else "no ride distance for this pair (Sea Plane / Domestic Terminal zones)"))

# ---------- 4. Buses ----------
CM = "https://corporatemaldives.com/"


def bus(o, d, f, url, date, conf, note, op="MTCC / RTL bus"):
    add("bus", op, o, "K", d, "K", f, "MVR", "flat", "one_way", "", "", url, date, conf, note)


bus("Male (city minibus)", "Male (city minibus)", 7, CM + "mtcc-begins-charging-for-rtl-minibus-services/", "2022-10-04", "high",
    "'the fare for minibus service will be MVR 7' from 3 Oct 2022; QR ticket valid 7 days")
bus("Male (city minibus)", "Male (city minibus)", 7, "https://atolltimes.mv/post/news/647", "2022-10", "high",
    "'The price of a bus token is MVR 7'; 'passengers will have to pay MVR 7 per trip'")
bus("Male (R10 Orchid)", "Male (R10 Orchid)", 7, "https://therestlessbeans.com/maldives-public-ferries/", "2023-05-09", "medium", "R10 Orchid route 'costs 7 MVR for a single ticket'")
bus("Hulhumale Phase 1 (R2)", "Male ferry terminal (Carnival)", 10, "https://therestlessbeans.com/maldives-public-ferries/", "2023-05-09", "medium", "R2 'costs 10 MVR for a single ticket'")
bus("Hulhumale Phase 2 (R8)", "Male ferry terminal (Carnival)", 15, "https://therestlessbeans.com/maldives-public-ferries/", "2023-05-09", "medium", "R8 'costs 15 MVR for a single ticket'")
bus("Male (West Park, R3)", "Velana International Airport", 10, "https://www.cestee.com/airport/male-mle/transport", "2023-12-31", "medium", "R3 'Price - 10 mvr', 25 min")
bus("Hulhumale Phase 1 (R4)", "Velana International Airport", 10, "https://www.cestee.com/airport/male-mle/transport", "2023-12-31", "medium", "R4 'Price - 10 mvr', 20 min")
bus("Hulhumale Phase 2 (R9)", "Velana International Airport", 15, "https://www.cestee.com/airport/male-mle/transport", "2023-12-31", "medium", "R9 'Price - 15 mvr', 25 min")
bus("Male", "Hulhumale", 10, CM + "10-rufiyaa-fare-for-male-hulhumale-bus/", "2018-12-25", "medium",
    "Historical MPL fare 'a bus fare of MVR 10' from 1 Jan 2019 (TouchLink card)", op="Maldives Ports Ltd bus")
bus("Villimale", "Villimale", 5, "https://atolltimes.mv/post/news/2695", "2023-01-20", "high", "'The service charges MVR 5 per person' (Villimale RTL bus)")
add("bus", "Villimale council buggy", "Villimale", "K", "Villimale", "K", 2, "MVR", "flat", "one_way", "", "", "https://atolltimes.mv/post/news/2695", "2023-03-08", "medium",
    "Buggy 'MVR 2 per person'; private hire 4-seat MVR 6, 6-seat MVR 10, 12-seat MVR 15")
for who, txt, url, dt in [
        ("senior", "people aged 65+ ride free with ID", CM + "mtcc-begins-charging-for-rtl-minibus-services/", "2022-10-04"),
        ("student", "school students in uniform ride free", CM + "mtcc-begins-charging-for-rtl-minibus-services/", "2022-10-04"),
        ("disabled", "people with special needs ride free with NSPA card", CM + "mtcc-begins-charging-for-rtl-minibus-services/", "2022-10-04"),
        ("student", "university/college students ride free with student ID (bus and ferry)", CM + "mtcc-expands-free-travel-concessions-for-higher-education-students/", "2023-09-02")]:
    add("bus", "MTCC / RTL bus", "Greater Male", "K", "Greater Male", "K", 0, "MVR", who, "one_way", "", "", url, dt, "high", f"Concession: {txt}")
for who, txt in [("senior", "aged 65+ and children under 3 travel free with ID"), ("disabled", "persons with special needs free with NSPA card"),
                 ("student", "school children in uniform and college/university students free with student card")]:
    add("fast_ferry_rtl", "MTCC / RTL", "Greater Male (QR ticketing)", "K", "Greater Male", "K", 0, "MVR", who, "one_way", "", "",
        CM + "mtcc-launches-new-ticketing-system-for-greater-male-ferry-services/", "2023-10-16", "high",
        f"Concession (article text): {txt}. Atoll Times (c. Jul 2026) says free RTL ferry currently for persons with disabilities and the elderly; free travel for regular medical patients only proposed")

# ---------- 5. Public ferries (MTCC, pre-RTL / Greater Male / Kaafu) ----------
RB = "https://therestlessbeans.com/maldives-public-ferries/"


def fer(o, oa, d, da, f, url, date, conf, note, km="", dur="", trip="one_way"):
    add("ferry_public", "MTCC", o, oa, d, da, f, "MVR", "flat", trip, km, dur, url, date, conf, note)


fer("Velana International Airport", "K", "Male", "K", 15, RB, "2023-05-09", "high", "'15 MVR per trip (20 MVR first thing in the morning)', 10 min; also cestee.com 'Price - 15 mvr / 1 usd'", dur=10)
fer("Velana International Airport", "K", "Male", "K", 20, RB, "2023-05-09", "medium", "Early-morning fare 'MVR 20' (00:00-05:59)", dur=10)
fer("Male", "K", "Hulhumale", "K", 10, "https://en.wikivoyage.org/wiki/Mal%C3%A9", "", "medium", "Wikivoyage: 'MTCC ferries run between Male and Hulhumale ... (MVR10, 20min)'", dur=20)
fer("Male", "K", "Villimale", "K", 3, "https://en.wikivoyage.org/wiki/Mal%C3%A9", "", "low", "Wikivoyage: Villimale ferry 'costing Rf 3 each way' (undated, possibly dated); atolltransfer.com lists 'Mrf 3/25'", dur=10)
fer("Male", "K", "Thulusdhoo", "K", 22, "https://asocialnomad.com/maldives/public-ferry-maldives/", "2024-01-02", "medium", "'Male to Thulusdhoo 22 MVR'")
fer("Male", "K", "Dhiffushi", "K", 22, "https://asocialnomad.com/maldives/male-to-dhiffushi/", "2024-01-02", "medium", "'Tickets from Male to Dhiffushi on the public ferry cost 22MVR per person'; 2.5 h", dur=150)
fer("Male", "K", "Maafushi", "K", 53, "https://therestlessbeans.com/maafushi-maldives/", "2023-05-05", "medium",
    "'306 MTCC Male to Maafushi public ferry costs 53 MVR per person' (90 min). NOTE asocialnomad.com male-to-maafushi says 22 MVR, which conflicts and looks copied from the Dhiffushi page", dur=90)
fer("Maafushi", "K", "Fulidhoo", "V", 53, "https://asocialnomad.com/maldives/maafushi-to-fulidhoo/", "2024-01-02", "medium", "'Tickets from Maafushi to Fulidhoo on the public ferry cost 53 MVR per person'")
fer("Male", "K", "Vaavu atoll (Fulidhoo)", "V", 53, RB, "2023-05-09", "low", "'most we paid was 53 MVR (3.43 USD) to the Vaavu Atoll'; 'lowest we paid ... 22 MVR to North Male Atoll'")
TL = CM + "mtcc-commences-launch-ferry-services-between-thaa-and-laamu-atolls/"
fer("Veymandoo", "Th", "Thimarafushi", "Th", 75, TL, "2020-12-29", "high", "'one-way ticket ... between Veymandoo and Thimarafushi is MVR 75, which a round trip will cost MVR 150' (MTCC launch ferry, pre-RTL)")
fer("Veymandoo", "Th", "Thimarafushi", "Th", 150, TL, "2020-12-29", "high", "Return MVR 150", trip="return")
fer("Thimarafushi", "Th", "Gan", "L", 250, TL, "2020-12-29", "high", "'between Thimarafushi and L. Gan is set at MVR 250, and a two-way ticket is MVR 400'")
fer("Thimarafushi", "Th", "Gan", "L", 400, TL, "2020-12-29", "high", "Return MVR 400", trip="return")
AM = "https://amaldives.com/plan-your-trip/maldives-public-ferry-guide-2026"
for lab, lo, hi in [("short routes (Male-Hulhumale/Villingili)", 0.5, 1.0), ("medium routes (Male-Maafushi/Gulhi/Guraidhoo)", 2.0, 3.0),
                    ("longer routes (Male-Rasdhoo/Ukulhas/Thoddoo/Fulidhoo)", 4.0, 6.0)]:
    add("ferry_public", "MTCC", "Male", "K", lab, "", round((lo + hi) / 2, 2), "USD", "foreigner", "one_way", "", "", AM, "2026-05-26", "low",
        f"Blog 'Estimated 2026': ${lo}-{hi} USD per person one-way; row = midpoint of quoted range (estimate, not a tariff)")


# ---------- 6. Scheduled speedboats (tourist, USD) ----------
def sp(o, oa, d, da, f, url, date, conf, note, dur=""):
    add("speedboat_scheduled", "Guesthouse / private operators", o, oa, d, da, f, "USD", "foreigner", "one_way", "", dur, url, date, conf, note)


sp("Male / airport", "K", "Maafushi", "K", 25, "https://therestlessbeans.com/maafushi-maldives/", "2023-05-05", "medium", "'speedboat costs about 25 USD per person each way and takes about 45 minutes'", 45)
sp("Male / airport", "K", "Maafushi", "K", 30, "https://amaldives.com/plan-your-trip/maldives-budget-travel-complete-guide-2026", "2026-05-26", "low", "'trip to Maafushi by shared speedboat ... around $30 per person' (30-45 min); route range $25-50")
sp("Male / airport", "K", "Maafushi", "K", 40, "https://asocialnomad.com/maldives/male-to-maafushi/", "2024-01-02", "low", "'from US$25 (usually more like US$40) upwards'")
sp("Male / airport", "K", "Thulusdhoo", "K", 30, "https://asocialnomad.com/maldives/male-to-thulusdhoo/", "2024-02-13", "medium", "'The cost of the speedboat from Male to Thulusdhoo is U$30 per person'")
sp("Male airport", "K", "Dhiffushi", "K", 50, "https://asocialnomad.com/maldives/male-to-dhiffushi/", "2024-01-02", "low", "'around US$50 per person upwards'")
sp("Male / airport", "K", "Fulidhoo", "V", 50, RB, "2023-05-09", "low", "'speedboat ... about 50 USD per person'")
sp("Male", "K", "Rasdhoo/Ukulhas/Thoddoo", "A", 50, AM, "2026-05-26", "low", "'Shared Speedboat (Male to Rasdhoo/Ukulhas/Thoddoo): $40 - $60 USD per person, one-way'; row = midpoint")
sp("Male", "K", "Maafushi (range)", "K", 32.5, AM, "2026-05-26", "low", "'Shared Speedboat (Male to Maafushi): $25 - $40 USD'; row = midpoint")
sp("Male airport", "K", "Guesthouse islands (generic)", "K", 30, "https://www.atolltransfer.com/faq", "", "low", "'Price starts from USD30 per person per way (scheduled speedboat)'; generic floor, not a specific route")
add("speedboat_scheduled", "MTCC (airport express)", "Male", "K", "Velana International Airport", "K", 1.5, "USD", "foreigner", "one_way", "", "", "https://www.atolltransfer.com/faq", "", "low",
    "'Speed Boat Ferry to airport is organized by MTCC and the price is USD1.5' (Airport Express)")

# ---------- 7. Charter ----------
RJ = "https://raajje.mv/21781"


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return round(2 * 6371 * math.asin(math.sqrt(x)), 2)


KM_MK = hav(6.28180, 73.24251, 6.61791, 73.06470)
KM_MF = hav(6.28180, 73.24251, 6.14896, 73.28789)
add("speedboat_charter", "Private speedboat (patient/resident)", "Milandhoo", "Sh", "Kulhudhuffushi", "HDh", 2500, "MVR", "local", "per_trip", KM_MK, "", RJ, "", "medium",
    "Raajje.mv: 'Travelling by speed boat ... to Kulhudhuffushi costs up to MVR 2,500' (upper bound; context: women travelling for labour care). Distance = great-circle from rtl_stops.csv")
add("speedboat_charter", "Private speedboat (patient/resident)", "Milandhoo", "Sh", "Funadhoo", "Sh", 1200, "MVR", "local", "per_trip", KM_MF, "", RJ, "", "medium",
    "Raajje.mv: 'travelling to Funadhoo can cost up to MVR 1,200' (upper bound). Distance = great-circle from rtl_stops.csv")
add("speedboat_charter", "Atoll Transfer (tourist)", "1 nautical mile", "", "(rate)", "", 12, "USD", "foreigner", "per_trip", 1.852, "", "https://www.atolltransfer.com/faq", "", "low",
    "'USD12 per noticale mile (private speedboat)': UNIT = per nautical mile (1 nm = 1.852 km), about MVR 99.9/km; tourist price list")
add("speedboat_charter", "Private operators (tourist)", "Male area", "K", "Local islands (generic)", "", 225, "USD", "foreigner", "per_trip", "", "", AM, "2026-05-26", "low",
    "'Private Speedboat ... Starts from $150 - $300+ USD per trip, one-way'; row = midpoint of quoted range")
add("speedboat_charter", "Atoll Transfer (tourist)", "Kaafu/Alif resorts", "", "Other atolls", "", 95, "USD", "foreigner", "per_trip", "", "", "https://www.atolltransfer.com/scheduled-speed-boat", "", "low",
    "'Private airport transfers are available at USD 95++ to USD1600'; row = lower bound only")

# ---------- 8. Sea ambulance ----------
add("sea_ambulance", "Government / MNDF / Aasandha", "(island)", "", "(hospital)", "", 0, "MVR", "local", "per_trip", "", "", "https://mfr.mv/soes/how-aasandha-works", "", "low",
    "No tariff published. Aasandha 'covers medical transportation costs of emergency cases'; 'If a sea ambulance is unavailable, private speed boats may be hired where cost of hiring must be approved by Aasandha'. 0 = patient out-of-pocket under scheme (policy statement, not a price)")

with open(OUT + "sea_land_fares.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)


# ---------- MODELS ----------
def ols(p):
    n = len(p)
    mx = sum(a for a, _ in p) / n
    my = sum(b for _, b in p) / n
    sxx = sum((a - mx) ** 2 for a, _ in p)
    if sxx == 0:
        return None
    b = sum((a - mx) * (y - my) for a, y in p) / sxx
    a0 = my - b * mx
    ss = sum((y - (a0 + b * x)) ** 2 for x, y in p)
    tt = sum((y - my) ** 2 for _, y in p)
    return dict(a_mvr=round(a0, 2), b_mvr_per_km=round(b, 3), n=n, r2=round(1 - ss / tt, 3) if tt else None)


R = {}
intra = [(float(x["gc_km"]), float(x["one_way_mvr"])) for x in gaz if not is_hw(x)]
inter = [(float(x["gc_km"]), float(x["one_way_mvr"])) for x in gaz if is_hw(x)]
m = ols(intra)
m.update(local_one_way=True, thin=False,
         unit="MVR one-way vs great-circle km (RTL official gazette tariffs 2022-2026; directed pairs de-duplicated, cancelled notices excluded)")
tiers = collections.defaultdict(list)
for km, f in intra:
    tiers[f].append(km)
m["points"] = {f"{int(f)}": dict(km_min=round(min(v), 1), km_max=round(max(v), 1), km_median=round(st.median(v), 1), n=len(v)) for f, v in sorted(tiers.items())}
m["return_note"] = "Return fare is about 1.8x one-way (35->65, 50->90, 70->130, 100->200 in HDh notice)"
m["use"] = "fare = a + b*km, or snap to the step tariff (35/50/65/70/100/125); steps are the true structure"
R["fast_ferry_rtl"] = m
hl = collections.defaultdict(list)
for km, f in inter:
    hl[f].append(km)
R["fast_ferry_rtl_highway_link"] = dict(
    thin=False, local_one_way=True, n=len(inter), median_mvr=st.median(f for _, f in inter), min_mvr=min(f for _, f in inter),
    max_mvr=max(f for _, f in inter), ols=ols(inter),
    points={f"{int(f)}": dict(n=len(v), km_min=round(min(v), 1), km_max=round(max(v), 1)) for f, v in sorted(hl.items())},
    note="Inter-zone 'Highway Link' tariffs are nearly distance-independent (MVR 130-170 north/central; southern Fuvahmulah/Addu/Huvadhoo links 250 and 490)")
fp = {"Male-Hulhumale": 10, "airport-Male": 15, "Male-Dhiffushi": 22, "Male-Thulusdhoo": 22, "Male-Maafushi": 53,
      "Maafushi-Fulidhoo": 53, "Veymandoo-Thimarafushi (2020)": 75, "Thimarafushi-Gan (2020)": 250}
R["ferry_public"] = dict(thin=True, local_one_way=True, n=len(fp), median_mvr=st.median(fp.values()), points=fp,
                         note="No distances for the Kaafu points so no regression. Greater Male harbour hops MVR 3-15; Kaafu/Vaavu islands MVR 22-53; superseded by RTL tariff where RTL runs. Use fast_ferry_rtl for atolls.")
sps = {"Maafushi": 25, "Maafushi (alt source)": 30, "Thulusdhoo": 30, "Dhiffushi": 50, "Fulidhoo": 50, "Rasdhoo/Ukulhas/Thoddoo": 50}
R["speedboat_scheduled"] = dict(thin=True, local_one_way=False, fare_type="foreigner_usd", n=len(sps), median_usd=st.median(sps.values()),
                                median_mvr=round(st.median(sps.values()) * FX, 1), range_usd=[25, 60], points_usd=sps,
                                note="Tourist USD prices; no local scheduled-speedboat tariff found. Do not use for local cost.")
cp = [(KM_MF, 1200), (KM_MK, 2500)]
two = ols(cp)
R["speedboat_charter"] = dict(
    thin=True, local_one_way=True, n=2, r2=None, a_mvr=two["a_mvr"], b_mvr_per_km=two["b_mvr_per_km"],
    points={"Milandhoo-Funadhoo (gc km %.1f, 'up to')" % KM_MF: 1200, "Milandhoo-Kulhudhuffushi (gc km %.1f, 'up to')" % KM_MK: 2500},
    tourist_rate_mvr_per_km=round(12 * FX / 1.852, 1), tourist_private_usd_per_trip=[150, 300],
    note="a,b from two resident quotes only (n=2, upper-bound quotes), r2 undefined. Tourist per-nm rate ~MVR 100/km is ~2x the local slope. Order of magnitude only.")
R["dhoni_charter"] = dict(thin=True, n=0, note="No numeric dhoni charter fare found. Thinadhoo council launch-hire rule (gazette IUL 415/415/2026/69) PDF has figures 262.50, 300.00, 3000.00 but text is Dhivehi-garbled, labels unknown; not used.")
R["sea_ambulance"] = dict(thin=True, n=0, patient_cost_mvr=0, note="No tariff. Aasandha covers emergency transfer; private speedboat hire needs Aasandha pre-approval. Assume MVR 0 to patient (policy); for system-cost views use speedboat_charter.")
am = {}
for r in M[1:]:
    for d, v in zip(hdr, r[2:]):
        am[(r[1], d)] = float(v)
vals = list(am.values())
R["greater_male"] = dict(
    taxi=dict(flat_within_zone_mvr=30, flat_within_zone_7_10_seat_mvr=45, male_hm1=85, male_hm2=100, male_airport=70, hm1_hm2=40, hm1_airport=80, hm2_airport=85,
              large_vehicle_multiplier_approx=1.5, source="Gazette IUL 472/1/2024/58 (20 May 2024)", note="Official fixed fare; over-charging reported"),
    bus=dict(male_minibus_mvr=7, villimale_bus_mvr=5, hulhumale_routes_mvr=[10, 15], airport_routes_mvr=[10, 15],
             free_for=["65+", "under 3", "school students in uniform", "university students with ID", "NSPA special needs card"]),
    airport_ferry_mvr=15, male_hulhumale_ferry_mvr=10, villimale_ferry_mvr=3,
    ride_hailing_avas=dict(min_mvr=min(vals), max_mvr=max(vals), within_zone_mvr=30, zone_matrix={f"{a}->{b}": v for (a, b), v in am.items()},
                           note="Avas matrix mirrors the regulated taxi tariff; Sea Plane / Domestic Terminal pairs add 10-40."))
R["concessions"] = dict(
    bus=dict(senior_65_plus="free (ID)", child_under_3="free", school_student_uniform="free", university_student="free with ID since Sep 2023", disabled="free with NSPA card"),
    rtl_ferry_greater_male=dict(senior_65_plus="free", child_under_3="free", student_school_uniform_and_university="free", disabled="free with NSPA card"),
    rtl_ferry_atolls=dict(status="Atoll Times (c. Jul 2026): free RTL ferry currently for persons with disabilities and the elderly; free travel for regular-medical-treatment patients (plus assistant, via NSPA/BML card) only under discussion"),
    villimale_buggy="free for students in uniform, under 6, 65+, NSPA-registered disabled",
    aasandha="covers emergency medical transport",
    note="Concessions are zero-fare, not percentage discounts. No half-fare scheme found. Student exemption is uniform/ID based, so a school-trip demo can assume MVR 0 for the student on public bus/Greater Male ferry; atoll RTL student exemption not confirmed.")
R["meta"] = dict(fx_mvr_per_usd=FX, rows=len(rows), built_by="scripts/fares_build_sea_land.py")
json.dump(R, open(OUT + "sea_land_fares_model.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(len(rows), collections.Counter(r["mode"] for r in rows))
print(json.dumps({k: R[k] for k in ("fast_ferry_rtl", "fast_ferry_rtl_highway_link", "speedboat_charter")}, indent=1)[:3000])
