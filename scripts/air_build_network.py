"""Build the AIR network dataset for the Maldives multi-modal travel-time model.

Inputs (all local, downloaded by curl into data/external/air/<source>/):
  ourairports/airports.csv, runways.csv           OurAirports (iso_country=MV)
  velana_fis/fis_flights_parsed.csv               Velana FIS snapshots (air_parse_fis.py)
  tma/atolls/*.html                               TMA "resorts we fly to" pages
  ../_derived/yb2025_t10.14_resorts.csv           MBS yearbook 2025 resort list (dist to Velana)
  ../_derived/census2022_to_codab_crosswalk.csv   inhabited islands -> COD-AB pcodes
  ../hdx-cod-ab/extracted/mdv_adminpoints.geojson island points
  ../osm-overpass/islands_20261024.geojson        OSM island points (fallback geocoder)

Outputs (data/external/air/):
  airports.csv, domestic_routes.csv, seaplane_destinations.csv, airport_catchment.csv,
  block_time_calibration.csv

Usage: python -I air_build_network.py <repo_data_dir>
"""
import csv
import glob
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
DATA = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\user\Music\Datathon\data"
AIR = os.path.join(DATA, "external", "air")
EXT = os.path.join(DATA, "external")
AS_OF = "2026-10-24"


def hav(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def norm(s):
    s = (s or "").lower()
    s = s.replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------------------------
# 1. Island gazetteer (COD-AB admin points, OSM islands fallback)
# --------------------------------------------------------------------------------------
ATOLL_NAME = {
    "HA": "Haa Alifu", "HDh": "Haa Dhaalu", "Sh": "Shaviyani", "N": "Noonu", "R": "Raa",
    "B": "Baa", "Lh": "Lhaviyani", "K": "Kaafu", "AA": "Alifu Alifu", "ADh": "Alifu Dhaalu",
    "V": "Vaavu", "M": "Meemu", "F": "Faafu", "Dh": "Dhaalu", "Th": "Thaa", "L": "Laamu",
    "GA": "Gaafu Alifu", "GDh": "Gaafu Dhaalu", "Gn": "Gnaviyani", "S": "Seenu (Addu City)",
    "MLE": "Male' City",
}
NAME_TO_ATOLL = {v.split(" (")[0]: k for k, v in ATOLL_NAME.items()}
NAME_TO_ATOLL["Seenu"] = "S"
NAME_TO_ATOLL["Addu City"] = "S"
NAME_TO_ATOLL["Male City"] = "MLE"
NAME_TO_ATOLL["Malé City"] = "MLE"

pts = json.load(open(os.path.join(EXT, "hdx-cod-ab", "extracted", "mdv_adminpoints.geojson"), encoding="utf-8"))
ISL = []  # (name, atoll_code, lat, lon, pcode)
for f in pts["features"]:
    p = f["properties"]
    if p.get("admin_level") == 2:
        ac = NAME_TO_ATOLL.get(p.get("adm1_name"), p.get("adm1_name"))
        ISL.append((p["name"], ac, p["y_coord"], p["x_coord"], p["adm2_pcode"]))
PCODE = {i[4]: i for i in ISL}
osm = json.load(open(os.path.join(EXT, "osm-overpass", "islands_20261024.geojson"), encoding="utf-8"))
OSM = [(f["properties"].get("name") or "", f["properties"]["rep_lat"], f["properties"]["rep_lon"]) for f in osm["features"]]


ATOLL_CENTRE = {}
for _ac in {i[1] for i in ISL}:
    _p = [i for i in ISL if i[1] == _ac]
    ATOLL_CENTRE[_ac] = (sum(i[2] for i in _p) / len(_p), sum(i[3] for i in _p) / len(_p))


def geocode(name, atoll=None, near=None):
    """Return (lat, lon, method). Exact (normalised) name match only, restricted to the atoll when given."""
    n = norm(name)
    cands = [i for i in ISL if norm(i[0]) == n and (atoll is None or i[1] == atoll)]
    if cands:
        if near and len(cands) > 1:
            cands.sort(key=lambda i: hav(near[0], near[1], i[2], i[3]))
        return cands[0][2], cands[0][3], "cod-ab_adminpoint"
    o = [x for x in OSM if norm(x[0]) == n]
    if atoll in ATOLL_CENTRE:
        c = ATOLL_CENTRE[atoll]
        o = [x for x in o if hav(c[0], c[1], x[1], x[2]) < 60]
    if o:
        if near:
            o.sort(key=lambda x: hav(near[0], near[1], x[1], x[2]))
        return o[0][1], o[0][2], "osm_island_point"
    return None, None, "not_found"


# --------------------------------------------------------------------------------------
# 2. Airports
# --------------------------------------------------------------------------------------
oa = {r["iata_code"] or r["ident"]: r for r in csv.DictReader(open(os.path.join(AIR, "ourairports", "airports.csv"), encoding="utf-8"))
      if r["iso_country"] == "MV"}
U = {
    "oa": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    "wl": "https://en.wikipedia.org/wiki/List_of_airports_in_the_Maldives",
    "md": "https://maldivian.aero/destinations/",
}
# iata, icao, name, island, atoll, type, operator, runway_m, surface, opened, status, notes, extra sources
A = [
    ("MLE", "VRMM", "Velana International Airport", "Hulhule", "K", "international", "Maldives Airports Company Ltd (MACL)", 3400, "asphalt",
     "1966-04-12", "operational", "Runway 18/36 3400x60 m operational 2022-10-06 (old runway now taxiway); new international terminal July 2025; waterdrome seaplane terminal 2022-10-06 with 4 water runways (TMA/Maldivian/Manta seaplane hub). Domestic terminal T2.",
     "https://en.wikipedia.org/wiki/Velana_International_Airport"),
    ("GAN", "VRMG", "Gan International Airport", "Gan", "S", "international", "Addu International Airport Pvt Ltd (state)", 2651, "concrete",
     "RAF base to 1976; civil since", "operational", "Runway 10/28 reported 2651x45 m (2010 source); Wikipedia infobox now says 3600 m and OurAirports 3658 m (12000 ft) - conflicting, verify with AIP. TMA seaplane base for Addu/Huvadhu resorts. Intl: SriLankan (CMB).",
     "https://en.wikipedia.org/wiki/Gan_International_Airport"),
    ("HAQ", "VRMH", "Hanimaadhoo International Airport", "Hanimaadhoo", "HDh", "international", "Regional Airports Co. / MACL (redevelopment)", 2460, "asphalt",
     "domestic (pre-2012); intl 2012-02-02; redeveloped 2025", "operational (expanded)", "Old runway 1220x30 m; Indian EXIM-funded redevelopment: new runway ~2.46 km (some reports 2.7 km), new terminal (1.3 M pax/yr) opened late 2025; further 700 m extension announced.",
     "https://atolltimes.mv/post/business/14023"),
    ("NMF", "VRDA", "Maafaru International Airport", "Maafaru", "N", "international", "Island Aviation Services (Maldivian)", 2200, "asphalt",
     "2019-12-01", "operational", "Runway 2200x40 m per Wikipedia (OurAirports lists 9350 ft); UAE (ADFD) funded; serves Noonu resorts.",
     "https://en.wikipedia.org/wiki/Maafaru_International_Airport"),
    ("VAM", "VRMV", "Villa International Airport Maamigili", "Maamigili", "ADh", "international", "Villa Group (Villa Air)", 1800, "concrete",
     "2011-10-01", "operational", "Domestic opening 2011, international standard 2013; Villa Air hub; serves South Ari resorts (speedboat).",
     "https://en.wikipedia.org/wiki/Villa_International_Airport_Maamigili"),
    ("DRV", "VRMD", "Dharavandhoo Airport", "Dharavandhoo", "B", "domestic", "Island Aviation Services", 1189, "asphalt",
     "2012-10-17", "operational", "Baa Atoll UNESCO biosphere; flights began 2012-10-15.", "https://en.wikipedia.org/wiki/Dharavandhoo_Airport"),
    ("FVM", "VRMR", "Fuvahmulah Airport", "Fuvahmulah", "Gn", "domestic", "Regional Airports Co. (assumed)", 1200, "asphalt",
     "2011-11 (sched. flights 2011-11-10/11)", "operational", "OurAirports ICAO VRMF; Wikipedia/SKYbrary use VRMR. Single-island atoll (Fuvahmulah City).",
     "https://maldivesindependent.com/news-in-brief/scheduled-flights-commence-to-fuvahmulah-airport-28095"),
    ("RUL", "VRQM", "Maavarulu Airport", "Maavarulu", "GDh", "domestic", "Regional Airports Co.", 1200, "asphalt",
     "2020-07-04", "operational", "Often served via Kaadedhdhoo.", "https://en.wikipedia.org/wiki/Maavarulu_Airport"),
    ("IFU", "VREI", "Ifuru Airport", "Ifuru", "R", "domestic", "Island Aviation Services", 1200, "asphalt",
     "2015-05-29", "operational", "Only operational airport in Raa (Alifushi under construction).", "https://en.wikipedia.org/wiki/Ifuru_Airport"),
    ("KDM", "VRMT", "Kaadedhdhoo Airport", "Kaadedhdhoo", "GDh", "domestic", "Regional Airports Co.", 1220, "bitumen",
     "1993-12-10", "operational", "3.7 NM south of Thinadhoo (GDh capital).", "https://en.wikipedia.org/wiki/Kaadedhdhoo_Airport"),
    ("KDO", "VRMK", "Kadhdhoo Airport", "Kadhdhoo", "L", "domestic", "MACL", 1220, "bitumen",
     "1986-04-06 (runway completed)", "operational", "Laamu link road connects Kadhdhoo-Fonadhoo-Gan(L) and neighbours by road.", "https://en.wikipedia.org/wiki/Kadhdhoo_Airport"),
    ("GKK", "VRMO", "Kooddoo Airport", "Kooddoo", "GA", "domestic", "Pristine Island Maldives (private)", 1800, "asphalt",
     "2012-09-10", "operational", "Maldivian suspended flights in 2024 after runway damage; service observed again in 2026 FIS data.", "https://en.wikipedia.org/wiki/Kooddoo_Airport"),
    ("DDD", "VRMU", "Dhaalu Airport", "Kudahuvadhoo", "Dh", "domestic (intl-capable)", "Dhaalu Airport Holdings (Reollo Investments)", 1800, "asphalt",
     "2017-06-01", "operational", "Manta Air hub until Sept 2026 (Manta exiting domestic ops); Maldivian flights Q2 230x/30x observed Oct 2026.", "https://en.wikipedia.org/wiki/Dhaalu_Airport"),
    ("TMF", "VRNT", "Thimarafushi Airport", "Thimarafushi", "Th", "domestic", "Island Aviation Services", 1200, "asphalt",
     "2013-09-03", "operational", "", "https://en.wikipedia.org/wiki/Thimarafushi_Airport"),
    ("HDK", "VRBK", "Kulhudhuffushi Airport", "Kulhudhuffushi", "HDh", "domestic", "Regional Airports Co.", 1220, "asphalt",
     "2018-09-21 (commercial ops 2019-08-09)", "operational", "", "https://en.wikipedia.org/wiki/Kulhudhuffushi_Airport"),
    ("LMV", "VRGD", "Madivaru Airport", "Madivaru", "Lh", "domestic", "Island Aviation Services", 1200, "asphalt",
     "2022-02-18", "operational", "Built by Kuredu Holdings; ICAO per Wikipedia (blank in OurAirports).", "https://www.connectingtravel.com/news/maldives-opens-its-second-airport-in-lhaviyani-atoll"),
    ("FND", "VRCF", "Funadhoo Airport", "Funadhoo", "Sh", "domestic", "Regional Airports Co.", 1200, "asphalt",
     "2020-02-03", "operational", "", "https://en.wikipedia.org/wiki/Funadhoo_Airport"),
    ("HRF", "VRAH", "Hoarafushi Airport", "Hoarafushi", "HA", "domestic", "Regional Airports Co.", 1200, "asphalt",
     "2020-11-17", "operational", "", "https://en.wikipedia.org/wiki/Hoarafushi_Airport"),
    ("FMT", "VRQF", "Faresmaathodaa Airport", "Fares-Maathodaa", "GDh", "domestic", "Regional Airports Co. (assumed)", 1200, "asphalt",
     "2023-03-15", "operational (low frequency)", "Test flight 2023-03-13; served via Kaadedhdhoo.", "https://mfr.mv/public-sector/test-flights-to-be-conducted-at-fares-maathodaa-airport"),
    ("MUM", "VRKM", "Muli Airport", "Muli", "M", "domestic", "Regional Airports Co.", 1200, "asphalt",
     "2025-05-20 (first commercial flight 2025-05-24)", "operational", "Runway 1200x30 m (Wikipedia says 1500 m). FIS also used code MUV in June 2026.", "https://maldivian.aero/media/2025/05/20/maldivian-inaugurates-direct-flights-to-meemu-muli.html"),
]
# planned / under construction: island, atoll, status, notes, source
P = [
    ("Villingili (GA) International Airport", "Villingili", "GA", "planned (construction start expected late Nov 2026)", 2200,
     "International airport with 2.2 km runway + transit hotel; MoU Feb 2024; contractor being finalised Oct 2026.", "https://en.mmtv.mv/12775"),
    ("Makunudhoo Airport", "Makunudhoo", "HDh", "under construction", None,
     "MTCC; reclamation finished; shore protection paused July 2026 after resident complaints.", "https://edition.mv/news/52442"),
    ("Alifushi Airport", "Alifushi", "R", "under construction", 1200,
     "MTCC; 750-day contract; 1200 m runway, terminal, fire station.", "https://avas.mv/en/120820"),
    ("Magoodhoo Airport", "Magoodhoo", "F", "under construction (behind schedule)", 1800,
     "MTCC; runway revised 1500->1800 m; target ops Sept 2026 not confirmed; works reported stalled Feb 2026.", "https://raajje.mv/170960"),
    ("Bileffahi Airport", "Bileffahi", "Sh", "under construction (announced; 30 months)", None,
     "MACL; 36 ha reclamation in 8 months; operational within 30 months (announced 2026-10-14).", "https://en.mmtv.mv/6419"),
    ("Vilufushi Airport", "Vilufushi", "Th", "under construction (reclamation)", None,
     "Listed as construction started (Mar 2024 presidential resolution); reclamation contracted.", "https://edition.mv/news/32600"),
    ("Thulhaadhoo Airport", "Thulhaadhoo", "B", "planned (reclamation contracted)", None,
     "Reclamation contracted to Capital Marine (with Vilufushi).", "https://psmnews.mv/en/123454"),
    ("Nilandhoo (F) Airport", "Nilandhoo", "F", "planned / reportedly under construction", None,
     "Presidential resolution Mar 2024; reported as competing with nearby Magoodhoo.", "https://edition.mv/news/32600"),
    ("Dhidhdhoo Airport", "Dhidhdhoo", "HA", "planned (presidential resolution 2024)", None, "", "https://edition.mv/news/32600"),
    ("Dhiguveli Airport", "Dhiguvelidhoomairah", "Sh", "planned (presidential resolution 2024)", None, "Island name as reported 'Dhiguveli'; geocoded to closest COD-AB name.", "https://edition.mv/news/32600"),
    ("Milandhoo Airport", "Milandhoo", "Sh", "planned (presidential resolution 2024)", None, "", "https://edition.mv/news/32600"),
    ("Vihafaru Airport", "Vihafaru", "N", "planned (presidential resolution 2024)", None, "Island not found in gazetteer - coordinates missing.", "https://edition.mv/news/32600"),
    ("Fainu Airport", "Fainu", "R", "planned (presidential resolution 2024)", None, "", "https://edition.mv/news/32600"),
    ("Mathiveri Airport", "Mathiveri", "AA", "planned (presidential resolution 2024)", None, "", "https://edition.mv/news/32600"),
    ("Maalhendhoo (GA) Airport", "Maalhendhoo", "GA", "planned (presidential resolution 2024)", None, "Reported as Gaafu Alif; gazetteer only has N. Maalhendhoo.", "https://edition.mv/news/32600"),
    ("Guraidhoo (Th) Airport", "Guraidhoo", "Th", "planned (presidential resolution 2024)", None, "", "https://edition.mv/news/32600"),
]
FALLBACK = {"Villingili": (0.7564, 73.4355), "Bileffahi": (6.3361, 72.9719), "Dhidhdhoo": (6.8872, 73.1142)}  # approx. island centres (manual, from maps)

rw = defaultdict(list)
for r in csv.DictReader(open(os.path.join(AIR, "ourairports", "runways.csv"), encoding="utf-8")):
    rw[r["airport_ident"]].append(r)

air_rows = []
APT = {}
for (iata, icao, name, island, atoll, typ, op, rlen, surf, opened, status, notes, src) in A:
    o = oa.get(iata)
    lat = float(o["latitude_deg"]) if o else None
    lon = float(o["longitude_deg"]) if o else None
    oa_len = ""
    if o and rw.get(o["ident"]):
        ft = rw[o["ident"]][0]["length_ft"]
        oa_len = str(round(float(ft) * 0.3048)) if ft else ""
    APT[iata] = (lat, lon)
    air_rows.append(dict(iata=iata, icao=icao, name=name, island=island, atoll_code=atoll, atoll_name=ATOLL_NAME[atoll],
                         lat=round(lat, 6), lon=round(lon, 6), coord_source="OurAirports", type=typ, operator=op,
                         runway_length_m=rlen, runway_length_m_ourairports=oa_len, runway_surface=surf, opened=opened,
                         status=status, scheduled_service_2026_10="", notes=notes,
                         sources=";".join([U["oa"], U["wl"], src])))
for (name, island, atoll, status, rlen, notes, src) in P:
    lat, lon, how = geocode(island, atoll)
    if lat is None and island in FALLBACK:
        lat, lon = FALLBACK[island]
        how = "manual_approx"
    air_rows.append(dict(iata="", icao="", name=name, island=island, atoll_code=atoll, atoll_name=ATOLL_NAME[atoll],
                         lat=round(lat, 5) if lat else "", lon=round(lon, 5) if lon else "", coord_source=how + " (island centre)",
                         type="domestic (planned)" if "Villingili" not in name else "international (planned)", operator="",
                         runway_length_m=rlen or "", runway_length_m_ourairports="", runway_surface="", opened="",
                         status=status, scheduled_service_2026_10="none", notes=notes, sources=src))
# seaplane bases / water aerodromes known to OurAirports
for k, o in oa.items():
    if o["type"] == "seaplane_base":
        _la, _lo = float(o["latitude_deg"]), float(o["longitude_deg"])
        _ac = min([k for k in ATOLL_CENTRE if k in ATOLL_NAME and k != "MLE"], key=lambda k: hav(_la, _lo, *ATOLL_CENTRE[k]))
        air_rows.append(dict(iata="", icao="", name=o["name"], island=o["municipality"], atoll_code=_ac,
                             atoll_name=ATOLL_NAME.get(_ac, _ac) + " (nearest atoll centre)",
                             lat=round(float(o["latitude_deg"]), 6), lon=round(float(o["longitude_deg"]), 6), coord_source="OurAirports",
                             type="seaplane_base (resort water aerodrome)", operator="resort / TMA-Maldivian-Manta", runway_length_m="",
                             runway_length_m_ourairports="", runway_surface="water", opened="", status="operational (unverified)",
                             scheduled_service_2026_10="on-demand seaplane", notes="OurAirports ident " + o["ident"] +
                             "; most of ~70+ resort water aerodromes are not in OurAirports - see seaplane_destinations.csv",
                             sources=U["oa"]))
air_rows.append(dict(iata="", icao="", name="Velana Waterdrome / Noovilu Seaplane Terminal", island="Hulhule", atoll_code="K",
                     atoll_name=ATOLL_NAME["K"], lat=4.2010, lon=73.5230, coord_source="approx (west lagoon of Hulhule)",
                     type="seaplane_base (hub)", operator="MACL; TMA, Maldivian, Manta Air", runway_length_m=1190,
                     runway_length_m_ourairports="", runway_surface="water (4 water runways)", opened="2022-10-06",
                     status="operational", scheduled_service_2026_10="seaplane hub",
                     notes="Main seaplane hub (~300 daily movements avg, up to 600 peak).",
                     sources="https://en.wikipedia.org/wiki/Velana_International_Airport"))

# --------------------------------------------------------------------------------------
# 3. Domestic routes from Velana FIS snapshots
# --------------------------------------------------------------------------------------
CITY = {"male": "MLE", "maafaru": "NMF", "madivaru": "LMV", "thimarafushi": "TMF", "kadhdhoo": "KDO", "kooddoo": "GKK",
        "kaadehdhoo": "KDM", "kaadedhdhoo": "KDM", "maavarulu": "RUL", "ifuru": "IFU", "dharavandhoo": "DRV",
        "funadhoo": "FND", "hanimaadhoo": "HAQ", "kulhudhuffushi": "HDK", "muli": "MUM", "fuvahmulah": "FVM",
        "faresmaathodaa": "FMT", "faresmathoda": "FMT", "gan": "GAN", "hoarafushi": "HRF", "kudahuvadhoo": "DDD",
        "maamigili": "VAM"}
FIX = {"MUV": "MUM"}
fis = [r for r in csv.DictReader(open(os.path.join(AIR, "velana_fis", "fis_flights_parsed.csv"), encoding="utf-8"))
       if r["category"] == "domestic" and r["originCode"] != r["destinationCode"]]


def tmin(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def routing(r):
    o, d = FIX.get(r["originCode"], r["originCode"]), FIX.get(r["destinationCode"], r["destinationCode"])
    via = [CITY.get(norm(v).split(" ")[0], "?" + v) for v in r["viaRoutes"].split("|") if v]
    return [o] + via + [d]


# coverage window per date (domestic departures+arrivals observed)
cov = defaultdict(list)
for r in fis:
    cov[r["date"]].append(tmin(r["scheduledTime"]))
SEASON = {"2026-06-17": "2026-06", "2026-06-18": "2026-06", "2026-07-11": "2026-07", "2026-07-12": "2026-07", "2026-07-13": "2026-07"}
season_of = lambda d: SEASON.get(d, d[:7])
# a date is usable for frequency if it covers at least 08:00-23:00 (domestic)
usable = sorted(d for d, ts in cov.items() if min(ts) <= 8 * 60 + 30 and max(ts) >= 22 * 60)
print("usable dates:", usable, {d: (min(t) // 60, max(t) // 60, len(t)) for d, t in sorted(cov.items())})

# legs from departures (out of MLE) and arrivals (into MLE)
leg_obs = defaultdict(lambda: defaultdict(int))  # (airline, o, d) -> date -> count
leg_meta = defaultdict(lambda: {"routings": set(), "flights": set(), "code": ""})
for r in fis:
    seq = routing(r)
    for a, b in zip(seq, seq[1:]):
        k = (r["airline"], a, b)
        leg_obs[k][r["date"]] += 1
        leg_meta[k]["routings"].add("-".join(seq))
        leg_meta[k]["flights"].add(r["flightNumber"])
        leg_meta[k]["code"] = r["airlineCode"]

# block times from round-trip pairs (dep N from MLE nonstop, arr N+1 to MLE nonstop, same date)
TURN = 25
deps = {(r["date"], r["flightNumber"]): r for r in fis if r["type"] == "departure" and not r["viaRoutes"]}
arrs = {(r["date"], r["flightNumber"]): r for r in fis if r["type"] == "arrival" and not r["viaRoutes"]}
rt = defaultdict(list)
for (dt, fn), r in deps.items():
    al, num = fn.split(" ")
    nxt = f"{al} {int(num) + 1:0{len(num)}d}"
    a = arrs.get((dt, nxt))
    if a and FIX.get(a["originCode"], a["originCode"]) == FIX.get(r["destinationCode"], r["destinationCode"]):
        x = tmin(a["scheduledTime"]) - tmin(r["scheduledTime"])
        if 0 < x < 300:
            rt[FIX.get(r["destinationCode"], r["destinationCode"])].append((x, fn, dt))
cal = []
for d, xs in sorted(rt.items()):
    med = statistics.median([x[0] for x in xs])
    dist = hav(*APT["MLE"], *APT[d])
    cal.append(dict(dest=d, distance_km=round(dist, 1), n_pairs=len(xs), median_roundtrip_min=med,
                    block_est_min=round((med - TURN) / 2), pairs=";".join(f"{fn}@{dt}:{x}" for x, fn, dt in xs)))
# least squares block = a + b*dist
X = [c["distance_km"] for c in cal]
Y = [c["block_est_min"] for c in cal]
n = len(X)
mx, my = sum(X) / n, sum(Y) / n
b = sum((x - mx) * (y - my) for x, y in zip(X, Y)) / sum((x - mx) ** 2 for x in X)
a = my - b * mx
print(f"block model: block = {a:.1f} + {b:.4f}*km  (n={n}); implied cruise {60 / b:.0f} km/h")


def model_block(dist):
    """ESTIMATED block time (min): linear fit on FIS round trips; short hops (<100 km) use 15 + 0.2*km."""
    return round(15 + 0.2 * dist) if dist < 100 else round(a + b * dist)


for c in cal:
    c["model_block_min"] = model_block(c["distance_km"])
with open(os.path.join(AIR, "block_time_calibration.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(cal[0].keys()))
    w.writeheader()
    w.writerows(cal)
OBS_BLOCK = {c["dest"]: c["block_est_min"] for c in cal}

AC = {"Maldivian": "ATR 72-600 / ATR 42-600 / Dash 8-300 (fleet-level, not flight-specific)",
      "Villa Air": "ATR 72-500 / ATR 72-600 (fleet-level)", "Manta Air": "ATR 72-600 (fleet-level)"}
SRC_FIS = "https://www.fis.com.mv/api/flights (live) + Wayback snapshots of https://fis.com.mv/"
routes = []
for (al, o, d), byd in sorted(leg_obs.items()):
    dates = sorted(byd)
    seasons = sorted({season_of(x) for x in dates})
    latest = seasons[-1]
    cur_usable = [x for x in usable if season_of(x) == latest]
    cur_all = [x for x in dates if season_of(x) == latest]
    if cur_usable:
        daily = [byd.get(x, 0) for x in cur_usable]
        wk = max(1, round(statistics.mean(daily) * 7))
        meth = f"ESTIMATED: mean daily legs on {len(cur_usable)} near-complete FIS day(s) {','.join(cur_usable)} x7"
    else:
        daily = [byd[x] for x in cur_all]
        wk = max(1, round(statistics.mean(daily) * 7))
        meth = f"ESTIMATED (weak): only partial-day FIS coverage {','.join(cur_all)}; mean x7, likely undercount"
    dist = hav(*APT[o], *APT[d]) if o in APT and d in APT else None
    key = d if o == "MLE" else (o if d == "MLE" else None)
    if key and key in OBS_BLOCK and all("-".join([o, d]) in rr or True for rr in leg_meta[(al, o, d)]["routings"]):
        bt, bm = OBS_BLOCK[key], "derived: FIS round-trip (dep N / arr N+1) minus 25 min turn, /2"
    else:
        bt, bm = (model_block(dist) if dist else ""), "ESTIMATED: distance model (27.1+0.125*km; <100 km: 15+0.2*km)"
    status = "operating"
    if al == "Manta Air":
        status = "ceased/ceasing Sept 2026 (Manta exiting domestic ATR ops)"
    elif latest < "2026-10":
        status = f"observed {latest} only; not seen in Oct 2026 snapshots (may be seasonal/irregular)"
    routes.append(dict(origin_iata=o, dest_iata=d, airline=al, airline_code=leg_meta[(al, o, d)]["code"],
                       service="nonstop" if all(len(rr.split("-")) == 2 for rr in leg_meta[(al, o, d)]["routings"]) else "leg of multi-stop routing(s)",
                       routings="; ".join(sorted(leg_meta[(al, o, d)]["routings"])),
                       flight_numbers=" ".join(sorted(leg_meta[(al, o, d)]["flights"])),
                       weekly_frequency=wk, weekly_frequency_method=meth,
                       daily_counts_by_date=";".join(f"{x}:{byd[x]}" for x in dates),
                       block_time_min=bt, block_time_method=bm,
                       distance_km=round(dist, 1) if dist else "", aircraft_type=AC.get(al, ""),
                       status=status, season=latest, source_url=SRC_FIS, as_of_date=AS_OF,
                       estimated="yes"))
# manual rows from secondary sources
routes.append(dict(origin_iata="MLE", dest_iata="DRV", airline="Villa Air", airline_code="VP", service="nonstop", routings="MLE-DRV",
                   flight_numbers="", weekly_frequency="", weekly_frequency_method="not observed; Wikipedia lists 'resuming soon'",
                   daily_counts_by_date="", block_time_min=model_block(hav(*APT["MLE"], *APT["DRV"])), block_time_method="ESTIMATED: distance model",
                   distance_km=round(hav(*APT["MLE"], *APT["DRV"]), 1), aircraft_type=AC["Villa Air"], status="suspended / resuming (unconfirmed)",
                   season="", source_url="https://en.wikipedia.org/wiki/Villa_Air", as_of_date=AS_OF, estimated="yes"))
routes.append(dict(origin_iata="MLE", dest_iata="SEAPLANE", airline="Trans Maldivian Airways / Maldivian Seaplane / Manta Air",
                   airline_code="TMW/Q2/NR", service="on-demand seaplane", routings="see seaplane_destinations.csv",
                   flight_numbers="", weekly_frequency="", weekly_frequency_method="on demand (resort transfers, daylight only)",
                   daily_counts_by_date="", block_time_min="", block_time_method="see seaplane_destinations.csv",
                   distance_km="", aircraft_type="DHC-6 Twin Otter floatplane", status="operating", season="",
                   source_url="https://www.transmaldivian.com/maldives-resorts/", as_of_date=AS_OF, estimated="yes"))
with open(os.path.join(AIR, "domestic_legs_directed.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(routes[0].keys()))
    w.writeheader()
    w.writerows(routes)

# undirected airline x airport-pair edge list (FIS 'via' ordering is ambiguous, so legs are symmetrised)
und = {}
for r in routes:
    if r["dest_iata"] == "SEAPLANE":
        continue
    pair = tuple(sorted([r["origin_iata"], r["dest_iata"]], key=lambda x: (x != "MLE", x)))
    k = (r["airline"],) + pair
    e = und.setdefault(k, dict(origin_iata=pair[0], dest_iata=pair[1], airline=r["airline"], airline_code=r["airline_code"],
                                weekly_frequency_each_way=0, weekly_frequency_method="", block_time_min=r["block_time_min"],
                                block_time_method=r["block_time_method"], distance_km=r["distance_km"], aircraft_type=r["aircraft_type"],
                                service=set(), routings=set(), flight_numbers=set(), directions_observed=set(), status=r["status"],
                                season=r["season"], source_url=r["source_url"], as_of_date=r["as_of_date"], estimated="yes"))
    if r["weekly_frequency"] != "":
        e["weekly_frequency_each_way"] = max(e["weekly_frequency_each_way"], r["weekly_frequency"])
        e["weekly_frequency_method"] = r["weekly_frequency_method"] + "; max of the two directions"
    else:
        e["weekly_frequency_each_way"] = ""
        e["weekly_frequency_method"] = r["weekly_frequency_method"]
    e["service"].add(r["service"])
    e["routings"].update(r["routings"].split("; "))
    e["flight_numbers"].update(r["flight_numbers"].split())
    e["directions_observed"].add(f"{r['origin_iata']}>{r['dest_iata']}")
    if r["season"] > e["season"]:
        e["season"], e["status"] = r["season"], r["status"]
# recompute each-way weekly frequency per undirected pair from per-date leg counts:
#   MLE pairs: max of the two directions (early-morning arrivals are often outside the FIS window)
#   outstation pairs: (dir1 + dir2) / 2, because each rotation is listed on both the departure and the arrival
#   board and the 'via' order is ambiguous, so the two records = one leg each way.
for (al, x, y), e in und.items():
    if e["weekly_frequency_each_way"] == "":
        continue
    d1, d2 = leg_obs.get((al, x, y), {}), leg_obs.get((al, y, x), {})
    dates = sorted(set(d1) | set(d2))
    latest = max(season_of(d) for d in dates)
    cur = [d for d in usable if season_of(d) == latest] or [d for d in dates if season_of(d) == latest]
    if x == "MLE":
        daily = [max(d1.get(d, 0), d2.get(d, 0)) for d in cur]
        rule = "max of directions"
    else:
        daily = [(d1.get(d, 0) + d2.get(d, 0)) / 2 for d in cur]
        rule = "(dir1+dir2)/2"
    e["weekly_frequency_each_way"] = max(1, round(statistics.mean(daily) * 7))
    weak = "" if set(cur) <= set(usable) else " (weak: partial-day coverage only)"
    e["weekly_frequency_method"] = (f"ESTIMATED{weak}: mean daily legs each way [{rule}] on FIS day(s) {','.join(cur)} x7; "
                                    "Oct-2026 days miss departures before ~08:00 (possible undercount)")
    e["daily_legs_by_date"] = ";".join(f"{d}:{d1.get(d, 0)}/{d2.get(d, 0)}" for d in dates)
out = []
for e in und.values():
    e.setdefault("daily_legs_by_date", "")
    for f in ("service", "routings", "flight_numbers", "directions_observed"):
        e[f] = "; ".join(sorted(e[f]))
    out.append(e)
out.sort(key=lambda e: (e["status"] != "operating", e["airline"], e["origin_iata"] != "MLE", e["origin_iata"], e["dest_iata"]))
out.append(dict(origin_iata="MLE", dest_iata="(resort water aerodromes)", airline="Trans Maldivian Airways / Maldivian Seaplane / Manta Air",
                airline_code="TMW/Q2/NR", weekly_frequency_each_way="", weekly_frequency_method="on demand, daylight only",
                block_time_min="", block_time_method="see seaplane_destinations.csv (8 + km/4.5)", distance_km="",
                aircraft_type="DHC-6 Twin Otter floatplane", service="on-demand seaplane", routings="", flight_numbers="",
                directions_observed="", daily_legs_by_date="", status="operating", season="", source_url="https://www.transmaldivian.com/maldives-resorts/",
                as_of_date=AS_OF, estimated="yes"))
with open(os.path.join(AIR, "domestic_routes.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

# scheduled-service summary per airport for airports.csv
srv = defaultdict(lambda: defaultdict(list))
for e in out:
    if e["status"] == "operating" and e["weekly_frequency_each_way"] not in ("", None):
        for x, other in ((e["origin_iata"], e["dest_iata"]), (e["dest_iata"], e["origin_iata"])):
            srv[x][e["airline"]].append(f"{other} {e['weekly_frequency_each_way']}/wk")
for row in air_rows:
    if row["iata"] in srv:
        row["scheduled_service_2026_10"] = "; ".join(f"{k}: " + ", ".join(v) for k, v in srv[row["iata"]].items()) + " (est. each way)"
with open(os.path.join(AIR, "airports.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(air_rows[0].keys()))
    w.writeheader()
    w.writerows(air_rows)

# --------------------------------------------------------------------------------------
# 4. Seaplane destinations
# --------------------------------------------------------------------------------------
res = list(csv.DictReader(open(os.path.join(EXT, "_derived", "yb2025_t10.14_resorts.csv"), encoding="utf-8")))
tma = {}
TMA_ATOLL = {"baa": "B", "dhaalu": "Dh", "faafu": "F", "gaafu-alifu": "GA", "laamu": "L", "lhaviyani": "Lh", "meemu-atoll": "M",
             "noonu": "N", "north-ari": "AA", "north-male": "K", "raa-atoll": "R", "shaviyani": "Sh", "south-ari-atoll": "ADh",
             "south-male": "K", "vaavu": "V"}
for p in glob.glob(os.path.join(AIR, "tma", "atolls", "resorts-*.html")):
    slug_at = os.path.basename(p)[8:-5]
    if slug_at not in TMA_ATOLL:
        continue
    t = open(p, encoding="utf-8", errors="ignore").read()
    for s in set(re.findall(r"https://www.transmaldivian.com/resorts/([a-z0-9-]+)/", t)):
        if slug_at != "meemu-atoll" and s in ("cinnamon-hakuraa-huraa-maldives", "medhufushi-island-resort"):
            continue  # footer/sidebar links repeated on every page
        tma[s] = TMA_ATOLL[slug_at]
STOP = {"maldives", "resort", "island", "spa", "the", "and", "at", "by", "of", "private", "islands", "villas", "retreat", "hotel", "a", "s"}


def toks(s):
    return {w for w in norm(s).split() if w not in STOP and len(w) > 2}


# other operators from Wikipedia (Maldivian seaplane) and Manta news/Wikipedia: (name tokens, atoll)
MALDIVIAN_SP = [("Anantara Kihavah", "B"), ("Four Seasons Private Island Voavah", "B"), ("Dreamland Hirundhoo", "B"),
                ("Vakkaru", "B"), ("Doores Island Retreat", "Dh"), ("Kandima", "Dh"), ("Maagau", "Dh"), ("Niyama", "Dh"),
                ("Robinson Noonu Orivaru", "N"), ("Kudafushi", "R"), ("Maalifushi COMO", "Th")]
MANTA_SP = [("Soneva Fushi", "B"), ("Dhigufaru", "B"), ("Nika", "AA"), ("Anantara Kihavah", "B"), ("Kandima", "Dh"),
            ("Niyama", "Dh"), ("Riu Atoll", "Dh")]
OA_SP = {o["name"]: (float(o["latitude_deg"]), float(o["longitude_deg"])) for o in oa.values() if o["type"] == "seaplane_base"}

sp_rows = []
used_tma = set()
# one-to-one scored assignment TMA slug <-> MBS resort (name tokens +1, island-name tokens +2)
cand = []
for ri, r in enumerate(res):
    at = r["atoll_abbr"] if r["atoll_abbr"] in ATOLL_NAME else ""
    for s_, sa in tma.items():
        if not (sa == at or (sa in ("AA", "ADh") and at in ("AA", "ADh"))):
            continue
        st = toks(s_.replace("-", " "))
        sc = len(toks(r["resort"]) & st) + 2 * len(toks(r["island"]) & st)
        if sc >= 1:
            cand.append((sc, ri, s_))
TMA_MATCH = {}
for sc, ri, s_ in sorted(cand, reverse=True):
    if ri in TMA_MATCH or s_ in used_tma:
        continue
    TMA_MATCH[ri] = s_
    used_tma.add(s_)
for ri, r in enumerate(res):
    at = r["atoll_abbr"] if r["atoll_abbr"] in ATOLL_NAME else ""
    rt_ = toks(r["resort"]) | toks(r["island"])
    ops, srcs = [], []
    if ri in TMA_MATCH:
        ops.append("TMA")
        srcs.append("https://www.transmaldivian.com/resorts/" + TMA_MATCH[ri] + "/")
    for nm, sa in MALDIVIAN_SP:
        if sa == at and len(toks(nm) & rt_) >= 1 and not (nm.startswith("Four Seasons") and "voavah" not in norm(r["island"])):
            ops.append("Maldivian Seaplane")
            srcs.append("https://en.wikipedia.org/wiki/Maldivian_(airline)")
            break
    for nm, sa in MANTA_SP:
        if sa == at and len(toks(nm) & rt_) >= 1:
            ops.append("Manta Air")
            srcs.append("https://en.wikipedia.org/wiki/Manta_Air ; https://mantaair.mv/news/")
            break
    try:
        dkm = float(r["dist_airport_km"])
    except ValueError:
        dkm = None
    lat = lon = None
    how = ""
    for n_, (la, lo) in OA_SP.items():
        if toks(n_) & toks(r["island"]) or len(toks(n_) & toks(r["resort"])) >= 2:
            lat, lon, how = la, lo, "OurAirports seaplane base"
            break
    if lat is None:
        lat, lon, how = geocode(r["island"], at or None)
    dflag = ""
    if lat is not None:
        dcalc = hav(*APT["MLE"], lat, lon)
        if dkm is None:
            dflag = f"MBS distance missing; used straight-line {dcalc:.0f} km"
            dkm = round(dcalc, 1)
        elif abs(dcalc - dkm) > max(15, 0.4 * dcalc):
            if at != "K" and dkm < 20:
                dflag = f"MBS distance {dkm} implausible for atoll {at}; used straight-line {dcalc:.0f} km"
                dkm = round(dcalc, 1)
            else:
                dflag = f"coordinates ({how}) disagree with MBS distance (straight-line {dcalc:.0f} km) - coordinates dropped"
                lat = lon = None
                how = ""
    if dkm is not None and at not in ("K", "") and dkm < 20 and lat is None:
        dflag = f"MBS distance {dkm} km implausible for atoll {at}; no coordinates to correct it"
        dkm = None
    est = round(8 + dkm / 4.5) if dkm else ""
    if dkm and dkm > 350:
        est = ""
        dflag = (dflag + "; " if dflag else "") + "beyond routine seaplane range from Velana: domestic flight (TMA also has a seaplane base at Gan for Addu/Huvadhu)"
    if ops:
        mode = "seaplane (listed operator)"
    elif at == "K" or (dkm and dkm <= 45):
        mode = "speedboat from Velana (inferred)"
    elif at in ("ADh",) and dkm and dkm < 110:
        mode = "seaplane or domestic flight to VAM + speedboat (inferred)"
    elif at in ("GA", "GDh", "S", "L", "HA", "HDh", "Th", "Dh", "B", "N", "Lh", "Sh", "R", "M"):
        mode = "domestic flight + speedboat, or seaplane (operator not confirmed)"
    else:
        mode = "seaplane or speedboat (operator not confirmed)"
    sp_rows.append(dict(resort=r["resort"], island=r["island"], atoll_code=at, atoll_name=ATOLL_NAME.get(at, ""),
                        operating_2024=r["operating_in_latest_year"], beds_2024=r["beds_2024"],
                        dist_from_velana_km=r["dist_airport_km"], dist_used_km=dkm if dkm is not None else "", dist_flag=dflag, est_seaplane_min_from_velana=est if ("seaplane" in mode) else "",
                        est_seaplane_min_method="ESTIMATED: 8 + km/4.5 (Twin Otter ~270 km/h + taxi); calibrated to TMA 20-60 min, Baa 30-35, Ari 20-30, HA ~70",
                        seaplane_operators="; ".join(ops), access_mode=mode, lat=round(lat, 5) if lat else "",
                        lon=round(lon, 5) if lon else "", coord_source=how, operator_sources=" ".join(srcs),
                        resort_source="MBS Statistical Yearbook 2025 table 10.14 (data/external/_derived/yb2025_t10.14_resorts.csv)"))
for s, sa in tma.items():
    if s not in used_tma:
        sp_rows.append(dict(resort=s.replace("-", " ").title(), island="", atoll_code=sa, atoll_name=ATOLL_NAME[sa], operating_2024="",
                            beds_2024="", dist_from_velana_km="", dist_used_km="", dist_flag="", est_seaplane_min_from_velana="", est_seaplane_min_method="",
                            seaplane_operators="TMA", access_mode="seaplane (listed operator); not matched to MBS resort list",
                            lat="", lon="", coord_source="", operator_sources="https://www.transmaldivian.com/resorts/" + s + "/",
                            resort_source="TMA website"))
with open(os.path.join(AIR, "seaplane_destinations.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(sp_rows[0].keys()))
    w.writeheader()
    w.writerows(sp_rows)

# --------------------------------------------------------------------------------------
# 5. Airport catchment of inhabited islands (straight-line nearest operational airport)
# --------------------------------------------------------------------------------------
NOTES = {
    "S": "Addu City: Gan-Feydhoo-Maradhoo-Hithadhoo linked by causeway/link road; Meedhoo/Hulhudhoo by road link or ferry",
    "L": "Laamu link road joins Kadhdhoo, Fonadhoo, Maandhoo, Gan(L) etc.",
    "Gn": "single-island atoll; airport on island",
    "MLE": "Greater Male: Male-Hulhumale via Sinamale bridge; Villimale by ferry",
}
cw = list(csv.DictReader(open(os.path.join(EXT, "_derived", "census2022_to_codab_crosswalk.csv"), encoding="utf-8")))
oper = [r["iata"] for r in air_rows if r["iata"] and r["status"].startswith("operational")]
APT_ATOLL = {r["iata"]: r["atoll_code"] for r in air_rows if r["iata"]}
APT_ISL = {norm(r["island"]): r["iata"] for r in air_rows if r["iata"]}
cat = []
seen = set()
POPSUM = defaultdict(float)
for r in cw:
    if r["adm2_pcode"]:
        POPSUM[r["adm2_pcode"]] += float(r["pop2022"] or 0)
for r in cw:
    if not r["adm2_pcode"] or r["adm2_pcode"] not in PCODE:
        continue
    if r["atoll_abbr"] == "MLE" and r["adm2_pcode"] in seen:
        continue
    seen.add(r["adm2_pcode"])
    nm, ac, la, lo, pc = PCODE[r["adm2_pcode"]]
    ds = sorted((hav(la, lo, *APT[i]), i) for i in oper)
    d1, a1 = ds[0]
    d2, a2 = ds[1]
    on_island = APT_ISL.get(norm(r["census_island"]))
    mode = "airport on island" if on_island else ("road/causeway (Addu/Laamu link)" if r["atoll_abbr"] in ("S",) or
                                                    (r["atoll_abbr"] == "L" and d1 < 25) else "speedboat/ferry transfer")
    if r["atoll_abbr"] == "MLE" or (r["atoll_abbr"] == "K" and a1 == "MLE"):
        mode = "Greater Male / Kaafu: road, ferry or speedboat to Velana"
    # practical airport: rule-based (no airport in AA/V/K/F -> Velana by speedboat/ferry; prefer same-atoll airport if not much farther)
    at_ = r["atoll_abbr"]
    same = [(d, i) for d, i in ds if APT_ATOLL.get(i) == at_]
    if at_ in ("AA", "V", "K", "MLE", "F"):
        prac, why = "MLE", "no airport in atoll; speedboat/ferry to Male/Velana (RTL/MTCC ferries, private speedboats)"
    elif at_ == "ADh" and a1 != "VAM" or (at_ == "ADh" and d1 > 25):
        prac, why = "MLE", "speedboat/ferry to Male (VAM alternative: Villa Air only flies VAM-MLE)"
    elif same and same[0][0] <= 1.3 * d1 + 5:
        prac, why = same[0][1], ("airport on island" if on_island else "same-atoll airport by speedboat/ferry")
    else:
        prac, why = a1, "nearest airport (other atoll)"
    if at_ in ("S", "Gn"):
        why = NOTES[at_]
    isl_name = f"{r['atoll_abbr']}. {r['census_island']}" if r["atoll_abbr"] != "MLE" else f"MLE. {PCODE[r['adm2_pcode']][0]} (census wards aggregated)"
    cat.append(dict(island=isl_name, atoll_code=r["atoll_abbr"], pop2022=int(POPSUM[r["adm2_pcode"]]),
                    adm2_pcode=pc, lat=round(la, 5), lon=round(lo, 5), nearest_airport=a1, dist_km=round(d1, 1),
                    same_atoll=("yes" if APT_ATOLL.get(a1) == r["atoll_abbr"] else "no"),
                    second_airport=a2, second_dist_km=round(d2, 1), practical_airport=prac,
                    practical_dist_km=round(hav(la, lo, *APT[prac]), 1), practical_reason=why, access_mode_inferred=mode,
                    note=NOTES.get(r["atoll_abbr"], ""),
                    method="straight-line nearest operational airport (COD-AB island point); sea-route distance and ferry/speedboat availability not modelled"))
with open(os.path.join(AIR, "airport_catchment.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(cat[0].keys()))
    w.writeheader()
    w.writerows(cat)

# --------------------------------------------------------------------------------------
# 6. Validation vs MBS yearbook aircraft movements 2024 (team-kandu observations.csv, table 11.17)
# --------------------------------------------------------------------------------------
GEO = {"ADh. Maamigili": "VAM", "B. Dharavandhoo": "DRV", "Dh. Kudahuvadhoo": "DDD", "Faresmaathoda": "FMT", "Funadhoo": "FND",
       "GA. Koodoo": "GKK", "GDh. Kaadedhdhoo": "KDM", "Gan International Airport": "GAN", "Gn. Fuvahmulah": "FVM",
       "Hanimaadhoo International Airport": "HAQ", "Hoarafushi": "HRF", "Kulhudhufushi": "HDK", "L. Kadhdhoo": "KDO",
       "Maavurlu": "RUL", "Madivaru": "LMV", "Raa. Ifuru": "IFU", "Th. Thimarafushi": "TMF", "Velana International Airport": "MLE"}
mov = defaultdict(float)
obs_p = os.path.join(DATA, "team-kandu", "observations.csv")
for r in csv.DictReader(open(obs_p, encoding="utf-8")):
    if r["metric"] == "aircraft_movements" and r["period"] == "month" and r["date"][:4] == "2024" and r["geo"] in GEO:
        mov[GEO[r["geo"]]] += float(r["value"] or 0)
est = defaultdict(float)
for e in out:
    if e["status"] == "operating" and e["weekly_frequency_each_way"] not in ("", None):
        for x in (e["origin_iata"], e["dest_iata"]):
            est[x] += e["weekly_frequency_each_way"] * 2 * 52  # dep + arr per week each way
val = []
for i in sorted(set(mov) | set(est)):
    if i.startswith("("):
        continue
    val.append(dict(iata=i, mbs_aircraft_movements_2024=int(mov.get(i, 0)) or "",
                    est_scheduled_movements_per_year_2026=int(est.get(i, 0)) or "",
                    ratio_est_to_mbs=round(est[i] / mov[i], 2) if mov.get(i) and est.get(i) else "",
                    note="MBS counts all movements (scheduled, charter, private, international, MLE incl. seaplanes?)"))
with open(os.path.join(AIR, "validation_movements_vs_mbs2024.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(val[0].keys()))
    w.writeheader()
    w.writerows(val)

print("airports:", len(air_rows), "routes:", len(routes), "seaplane rows:", len(sp_rows), "catchment islands:", len(cat))
