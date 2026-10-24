"""Merge partial specialist-service CSVs into the final specialist_services.csv.

* validates/normalises operator_type, atoll codes, service_category, confidence
* de-duplicates facility x island x service_category (except visiting_specialist rows,
  which are kept per event), keeping the highest-confidence / most recent row,
  appending distinct details from the other rows ('|| also:') and up to 3 source URLs.
* prints an island x specialty matrix summary.

Usage: python -I health_specialist_merge.py <partial_dir> <out_csv> [matrix_csv]
"""
import csv
import glob
import os
import re
import sys
import unicodedata
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COLS = ["facility_name", "operator_type", "facility_type", "island", "atoll", "service_category",
        "service_detail", "evidence", "source_url", "source_date", "confidence"]
ATOLLS = {"HA", "HDh", "Sh", "N", "R", "B", "Lh", "K", "AA", "ADh", "V", "M", "F", "Dh", "Th", "L",
          "GA", "GDh", "Gn", "S", "MLE"}
ATOLL_FIX = {a.lower(): a for a in ATOLLS}
ATOLL_FIX.update({"male": "MLE", "male'": "MLE", "malé": "MLE", "male city": "MLE", "k.": "K",
                  "addu": "S", "seenu": "S", "fuvahmulah": "Gn", "gnaviyani": "Gn", "kaafu": "K",
                  "haa alifu": "HA", "haa dhaalu": "HDh", "shaviyani": "Sh", "noonu": "N", "raa": "R",
                  "baa": "B", "lhaviyani": "Lh", "alifu alifu": "AA", "alifu dhaalu": "ADh",
                  "vaavu": "V", "meemu": "M", "faafu": "F", "dhaalu": "Dh", "thaa": "Th", "laamu": "L",
                  "gaafu alifu": "GA", "gaafu dhaalu": "GDh", "mle": "MLE", "national": "",
                  "nationwide": "", "multiple": "", "": ""})
ISLAND_FIX = {"male": "Male'", "malé": "Male'", "male'": "Male'", "hulhumale": "Hulhumale'",
              "hulhumalé": "Hulhumale'", "hulhumale'": "Hulhumale'", "villimale": "Villimale'",
              "vilimale": "Villimale'", "villimalé": "Villimale'", "villimale'": "Villimale'",
              "vilimale'": "Villimale'", "villingili (male)": "Villimale'", "hulhule": "Hulhule'",
              "hulhulé": "Hulhule'", "addu (hithadhoo)": "Hithadhoo", "kulhudhuffushi city": "Kulhudhuffushi",
              "fuvahmulah city": "Fuvahmulah", "fuvammulah": "Fuvahmulah", "un'goofaaru": "Ungoofaaru",
              "thinadhoo (gdh)": "Thinadhoo", "gan (laamu)": "Gan", "eydhafushi (b)": "Eydhafushi",
              "dhidhdhoo": "Dhidhdhoo", "dhidhoo": "Dhidhdhoo", "hdh. kulhudhuffushi": "Kulhudhuffushi"}
CATS = {"oncology", "sports_medicine", "physiotherapy", "dialysis", "cardiology", "maternity",
        "paediatrics", "nicu", "psychiatry", "ophthalmology", "ent", "orthopaedics", "dermatology",
        "ncd_diabetes", "icu", "emergency", "surgery", "thalassaemia", "drug_rehab", "geriatrics",
        "visiting_specialist", "telemedicine",
        # extra snake_case categories used where none of the core list fits
        "nephrology", "developmental_therapy", "gastroenterology", "rheumatology", "pulmonology",
        "neurology", "urology", "fertility", "hyperbaric"}
CAT_FIX = {"obstetrics": "maternity", "obgyn": "maternity", "gynaecology": "maternity",
           "obstetrics_gynaecology": "maternity", "labour_room": "maternity", "pediatrics": "paediatrics",
           "mental_health": "psychiatry", "eye": "ophthalmology", "eye_care": "ophthalmology",
           "diabetes": "ncd_diabetes", "ncd": "ncd_diabetes",
           "endocrinology": "ncd_diabetes", "rehabilitation": "physiotherapy", "rehab": "physiotherapy",
           "orthopedics": "orthopaedics", "trauma": "emergency", "cancer": "oncology",
           "cancer_screening": "oncology", "palliative_care": "oncology", "elderly_care": "geriatrics",
           "drug_rehabilitation": "drug_rehab", "ccu": "icu", "hdu": "icu", "picu": "icu",
           "visiting": "visiting_specialist", "telehealth": "telemedicine"}
CONF_RANK = {"high": 3, "medium": 2, "low": 1}
NOT_ACTIVE = re.compile(r"^(no |not yet|planned|proposed|under construction)|not (yet )?operational|\bgap\b", re.I)


def key(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(the|hospital|regional|atoll|centre|center|clinic|unit|pvt|ltd|private|limited)\b", " ", s)
    return " ".join(s.split())


def norm(r, src):
    r = {c: (r.get(c) or "").strip() for c in COLS}
    a = r["atoll"]
    r["atoll"] = ATOLL_FIX.get(a.lower(), a) if a not in ATOLLS else a
    isl = r["island"]
    r["island"] = ISLAND_FIX.get(isl.lower(), isl)
    if r["island"] in ("Male'", "Hulhumale'", "Villimale'", "Hulhule'"):
        r["atoll"] = "MLE"
    c = r["service_category"].lower().replace(" ", "_").replace("-", "_")
    r["service_category"] = CAT_FIX.get(c, c)
    r["operator_type"] = r["operator_type"].lower()
    if r["operator_type"] in ("government", "state", "soe"):
        r["operator_type"] = "public"
    if r["operator_type"] in ("mndf",):
        r["operator_type"] = "military"
    if r["operator_type"] in ("charity", "ngo/charity", "international_ngo"):
        r["operator_type"] = "ngo"
    r["confidence"] = r["confidence"].lower() if r["confidence"].lower() in CONF_RANK else "low"
    r["_src"] = os.path.basename(src)
    return r


def main():
    pdir, out = sys.argv[1], sys.argv[2]
    mout = sys.argv[3] if len(sys.argv) > 3 else None
    rows = []
    for f in sorted(glob.glob(os.path.join(pdir, "*.csv"))):
        with open(f, encoding="utf-8-sig", newline="") as fh:
            rd = csv.DictReader(fh)
            missing = [c for c in COLS if c not in (rd.fieldnames or [])]
            if missing:
                print("WARN", f, "missing cols", missing)
            n = 0
            for r in rd:
                if not (r.get("facility_name") or "").strip():
                    continue
                rows.append(norm(r, f))
                n += 1
            print(f"{os.path.basename(f)}: {n} rows")
    # geofix: rows with blank island (or HEMS-derived rows) inherit the island of the same
    # facility from the HEMS+Aasandha-located rows (hems_registry.csv)
    geo = {}
    for r in rows:
        if r["_src"] == "hems_registry.csv" and r["island"] and r["confidence"] == "high":
            geo.setdefault(key(r["facility_name"]), (r["island"], r["atoll"]))
    nfix = 0
    for r in rows:
        g = geo.get(key(r["facility_name"]))
        if g and r["_src"] != "hems_registry.csv" and (not r["island"] or "HEMS" in r["evidence"] + r["service_detail"] + r["source_url"]):
            if (r["island"], r["atoll"]) != g:
                r["island"], r["atoll"] = g
                if "island NOT published" in r["service_detail"]:
                    r["service_detail"] = r["service_detail"].replace("island NOT published in HEMS public list", "island from Aasandha empanelled list")
                    if r["confidence"] == "low":
                        r["confidence"] = "medium"
                nfix += 1
    print("geofixed rows:", nfix)
    nm = 0
    for r in rows:
        if r["island"] == "(multiple islands)":
            r["island"] = ""
        if not r["island"] and not r["atoll"] and re.search(r"likely Greater Mal", r["service_detail"]) and "Huvadhoo" not in r["facility_name"]:
            r["island"], r["atoll"] = "Male'", "MLE"
            r["service_detail"] += " [island assumed Male' (Greater Male') - unverified]"
            r["confidence"] = "low"
            nm += 1
    print("assumed Greater Male' rows:", nm)
    bad_cat = defaultdict(int)
    bad_atoll = defaultdict(int)
    for r in rows:
        if r["service_category"] not in CATS:
            bad_cat[r["service_category"]] += 1
        if r["atoll"] not in ATOLLS:
            bad_atoll[r["atoll"]] += 1
        if r["operator_type"] not in ("public", "private", "ngo", "military"):
            print("WARN operator", r["operator_type"], r["facility_name"])
    print("non-standard categories:", dict(bad_cat))
    print("non-standard atolls:", dict(bad_atoll))

    groups = {}
    order = []
    for r in rows:
        if r["service_category"] == "visiting_specialist":
            k = (key(r["facility_name"]), r["island"].lower(), r["service_category"],
                 key(r["service_detail"])[:60], r["source_date"][:7])
        else:
            k = (key(r["facility_name"]), r["island"].lower(), r["service_category"])
        if k not in groups:
            groups[k] = [r]
            order.append(k)
        else:
            groups[k].append(r)
    final = []
    for k in order:
        g = groups[k]
        g.sort(key=lambda x: (CONF_RANK[x["confidence"]], x["source_date"]), reverse=True)
        best = dict(g[0])
        urls = []
        for x in g:
            for u in x["source_url"].split(" ; "):
                u = u.strip()
                if u and u not in urls:
                    urls.append(u)
        best["source_url"] = " ; ".join(urls[:3])
        extra = []
        for x in g[1:]:
            d = x["service_detail"].strip()
            if d and key(d)[:50] != key(best["service_detail"])[:50] and d[:100] not in extra:
                extra.append(d[:140])
        if extra:
            best["service_detail"] = (best["service_detail"] + " || also: " + " | ".join(extra))[:600]
        final.append(best)
    final.sort(key=lambda x: (x["atoll"] != "MLE", x["atoll"], x["island"], x["facility_name"],
                              x["service_category"]))
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(final)
    print(f"input {len(rows)} -> final {len(final)} rows -> {out}")

    # matrix: island x category (permanent only, i.e. excl. visiting rows and 'NO ' gap rows)
    mat = defaultdict(lambda: defaultdict(int))
    for r in final:
        if NOT_ACTIVE.search(r["service_detail"]):
            continue
        if not r["island"]:
            continue
        isl = f"{r['atoll']}|{r['island']}"
        mat[isl][r["service_category"]] += 1
    cats = sorted(CATS)
    if mout:
        with open(mout, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["atoll", "island", "n_categories"] + cats)
            for isl in sorted(mat):
                a, i = isl.split("|", 1)
                w.writerow([a, i, sum(1 for c in cats if mat[isl][c])] + [mat[isl][c] for c in cats])
        print("matrix ->", mout)
    by_cat = defaultdict(set)
    for isl, d in mat.items():
        for c, v in d.items():
            if v:
                by_cat[c].add(isl)
    for c in cats:
        nm = sum(1 for i in by_cat[c] if i.startswith("MLE|"))
        print(f"{c:22s} islands={len(by_cat[c]):3d} (GreaterMale={nm})  {sorted(i.split('|')[1] for i in by_cat[c] if not i.startswith('MLE|'))}")


if __name__ == "__main__":
    main()
