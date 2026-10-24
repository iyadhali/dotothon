"""Tidy Maldives Census 2022 island population tables and build a crosswalk to the HDX COD-AB island polygons.

Usage:
  python -I census_island_join.py <external_dir>
Reads:
  <ext>/mbs-census-2022/xlsx/2023-07_P3.xlsx   (pop by place of enumeration 2022 & 2014, by island)
  <ext>/mbs-census-2022/xlsx/2023-07_P5.xlsx   (pop by island and sex 2022)
  <ext>/mbs-census-2022/xlsx/2023-08_MG12.xlsx (usual resident pop by island 2022)
  <ext>/hdx-cod-ab/extracted/mdv_admin2.geojson
Writes (to <ext>/_derived/):
  census2022_population_by_island.csv
  census2022_to_codab_crosswalk.csv
  islands_codab_with_census2022.gpkg  (all 1,556 COD-AB islands + census columns where matched)
"""
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd
import geopandas as gpd
from rapidfuzz import fuzz, process

sys.stdout.reconfigure(encoding="utf-8")
EXT = Path(sys.argv[1])
X = EXT / "mbs-census-2022" / "xlsx"
OUT = EXT / "_derived"
OUT.mkdir(exist_ok=True)

# census atoll abbreviation -> COD-AB adm1 pcode / official atoll letter code
ATOLL = {
    "HA": ("MV001", "Haa Alifu"), "HDh": ("MV002", "Haa Dhaalu"), "Sh": ("MV003", "Shaviyani"),
    "N": ("MV004", "Noonu"), "R": ("MV006", "Raa"), "B": ("MV007", "Baa"),
    "Lh": ("MV005", "Lhaviyani"), "K": ("MV009", "Kaafu"), "AA": ("MV008", "Alifu Alifu"),
    "ADh": ("MV020", "Alifu Dhaalu"), "V": ("MV010", "Vaavu"), "M": ("MV013", "Meemu"),
    "F": ("MV011", "Faafu"), "Dh": ("MV012", "Dhaalu"), "Th": ("MV014", "Thaa"), "L": ("MV015", "Laamu"),
    "GA": ("MV016", "Gaafu Alifu"), "GDh": ("MV017", "Gaafu Dhaalu"), "Gn": ("MV018", "Gnaviyani"),
    "S": ("MV019", "Seenu"), "MLE": ("MV021", "Male"),
}
ATOLL_NORM = {re.sub(r"[^a-z]", "", k.lower()): k for k in ATOLL}


def norm_name(s: str) -> str:
    """Aggressive transliteration-insensitive key for Dhivehi island names."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("n'", "")  # COD-AB marks nasal n with n' (Ban'didhoo); census drops it (Badidhoo)
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z]", "", s)
    s = s.replace("ee", "i").replace("oo", "u").replace("aa", "a")
    s = s.replace("th", "t").replace("dh", "d").replace("sh", "s").replace("lh", "l").replace("gn", "n")
    s = re.sub(r"(.)\1+", r"\1", s)          # collapse doubled letters (Villi/Vili, hdh/dh ...)
    s = s.replace("hd", "d").replace("hf", "f").replace("hk", "k").replace("ht", "t")  # ih-dhoo / idh-dhoo
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


def read_table(path, ncols, names, header_rows=6):
    df = pd.read_excel(path, header=None, skiprows=header_rows)
    df = df.iloc[:, :ncols]
    df.columns = names
    return df


def tidy():
    p3 = read_table(X / "2023-07_P3.xlsx", 11,
                    ["atoll_abbr", "island", "pop2022", "pop2022_mdv", "pop2022_foreign",
                     "pop2014", "pop2014_mdv", "pop2014_foreign", "growth_pop", "growth_mdv", "growth_foreign"])
    p5 = read_table(X / "2023-07_P5.xlsx", 12,
                    ["atoll_abbr", "island", "pop2022_chk", "pop2022_female", "pop2022_male",
                     "mdv_chk", "mdv_female", "mdv_male", "for_chk", "foreign_female", "foreign_male", "sex_ratio_mdv"],
                    header_rows=5)
    mg = read_table(X / "2023-08_MG12.xlsx", 5,
                    ["atoll_abbr", "island", "usual_res_2022", "usual_res_2022_mdv", "usual_res_2022_foreign"])

    def clean(df, section_markers):
        df = df.copy()
        df["atoll_abbr"] = df["atoll_abbr"].fillna("").astype(str).str.strip()
        df["island"] = df["island"].fillna("").astype(str).str.strip()
        # Maale wards appear with blank atoll before the 'Admin islands' header row
        out, in_male = [], False
        for _, r in df.iterrows():
            isl = r["island"]
            if isl in ("Maale",):
                in_male = True
                out.append({**r, "atoll_abbr": "MLE", "level": "city_total"})
                continue
            if any(isl.startswith(m) for m in section_markers):
                in_male = False
                continue
            if r["atoll_abbr"]:
                out.append({**r, "level": "island"})
            elif in_male and isl not in ("", "nan", "None"):
                out.append({**r, "atoll_abbr": "MLE", "level": "male_ward"})
        return pd.DataFrame(out)

    markers = ("Admin islands", "Atolls (Admin", "Non-admin", "Non-Admin", "Republic", "Resorts", "Industrial", "Source", "*")
    p3c, p5c, mgc = clean(p3, markers), clean(p5, markers), clean(mg, markers)
    key = ["atoll_abbr", "island"]
    df = p3c.merge(p5c.drop(columns=["level", "pop2022_chk", "mdv_chk", "for_chk"]), on=key, how="outer") \
            .merge(mgc.drop(columns=["level"]), on=key, how="outer")
    canon = {k.lower(): k for k in ATOLL}
    df["atoll_abbr"] = df["atoll_abbr"].map(lambda a: canon.get(str(a).lower(), a))
    df = df[~df["atoll_abbr"].astype(str).str.startswith("*")]
    df["atoll_pcode"] = df["atoll_abbr"].map(lambda a: ATOLL.get(a, (None, None))[0])
    df["atoll_name"] = df["atoll_abbr"].map(lambda a: ATOLL.get(a, (None, None))[1])
    df["name_key"] = df["island"].map(norm_name)
    df["join_key"] = df["atoll_pcode"].fillna("") + "|" + df["name_key"]
    num = [c for c in df.columns if c.startswith(("pop", "growth", "mdv_", "foreign_", "usual", "sex_"))]
    df[num] = df[num].apply(pd.to_numeric, errors="coerce")
    df = df[["atoll_abbr", "atoll_pcode", "atoll_name", "island", "level", "name_key", "join_key"] + num]
    df.to_csv(OUT / "census2022_population_by_island.csv", index=False, encoding="utf-8")
    return df


# Census localities that map to a different/combined COD-AB polygon (manual overrides, verified by name)
MANUAL = {
    # Male city: wards Henveiru/Galolhu/Machchangolhi/Maafannu are all on Male island
    ("MLE", "Henveiru"): "Male", ("MLE", "Galolhu"): "Male", ("MLE", "Machchangolhi"): "Male",
    ("MLE", "Maafannu"): "Male", ("MLE", "Vilimaale"): "Vilin'gili",
    ("L", "Gamu"): "Gan",
    ("MLE", "Hulhumaale Phase 1"): "Hulhumaale", ("MLE", "Hulhumaale Phase 2"): "Hulhumaale",
    ("MLE", "Hulhule"): "Hulhule",
}


def crosswalk(census):
    isl = gpd.read_file(EXT / "hdx-cod-ab" / "extracted" / "mdv_admin2.geojson")
    isl["name_key"] = isl["adm2_name"].map(norm_name)
    rows = []
    for _, r in census[census.level.isin(["island", "male_ward"])].iterrows():
        cand = isl[isl.adm1_pcode == r.atoll_pcode] if r.atoll_pcode != "MV021" else             isl[isl.adm1_pcode.isin(["MV021", "MV009"])].sort_values("adm1_pcode", ascending=False)
        target = MANUAL.get((r.atoll_abbr, r.island))
        method, score, hit = None, None, None
        if target is not None:
            m = cand[cand.adm2_name.map(norm_name) == norm_name(target)]
            if len(m):
                hit, method, score = m.iloc[0], "manual", 100
        if hit is None:
            m = cand[cand.name_key == r.name_key]
            if len(m) == 1:
                hit, method, score = m.iloc[0], "exact_key", 100
            elif len(m) > 1:  # same name twice in an atoll -> take the largest island (inhabited ones are usually larger)
                hit, method, score = m.sort_values("area_sqkm", ascending=False).iloc[0], "exact_key_largest_of_dupes", 100
        if hit is None and r.name_key:
            # hyphenated census names (e.g. Fares-Maathodaa, Maradhoo-Feydhoo) -> try each part
            parts = [norm_name(p) for p in re.split(r"[-/]", r.island) if p.strip()]
            for p in parts:
                m = cand[cand.name_key == p]
                if len(m):
                    hit, method, score = m.sort_values("area_sqkm", ascending=False).iloc[0], "hyphen_part", 95
                    break
        if hit is None and r.name_key:
            best = process.extractOne(r.name_key, cand.name_key.tolist(), scorer=fuzz.ratio)
            if best and best[1] >= 80:
                hit, method, score = cand.iloc[best[2]], "fuzzy", round(best[1], 1)
        rows.append({
            "atoll_abbr": r.atoll_abbr, "census_island": r.island, "census_level": r.level,
            "census_join_key": r.join_key, "pop2022": r.pop2022,
            "adm2_pcode": None if hit is None else hit.adm2_pcode,
            "adm2_name": None if hit is None else hit.adm2_name,
            "adm1_pcode": r.atoll_pcode, "match_method": method or "UNMATCHED", "match_score": score,
        })
    cw = pd.DataFrame(rows)
    cw.to_csv(OUT / "census2022_to_codab_crosswalk.csv", index=False, encoding="utf-8")

    # aggregate to polygon (Male wards -> Male island etc.)
    agg = census.merge(cw[["census_island", "atoll_abbr", "adm2_pcode", "match_method"]],
                       left_on=["island", "atoll_abbr"], right_on=["census_island", "atoll_abbr"], how="inner")
    agg = agg[agg.adm2_pcode.notna()]
    sumcols = ["pop2022", "pop2022_mdv", "pop2022_foreign", "pop2014", "pop2022_female", "pop2022_male",
               "usual_res_2022", "usual_res_2022_mdv", "usual_res_2022_foreign"]
    g = agg.groupby("adm2_pcode").agg({**{c: "sum" for c in sumcols},
                                        "island": lambda s: "; ".join(s), "match_method": "first"}) \
           .rename(columns={"island": "census_localities"}).reset_index()
    g["inhabited_census2022"] = True
    out = isl.merge(g, on="adm2_pcode", how="left")
    out["inhabited_census2022"] = out["inhabited_census2022"].fillna(False).astype(bool)
    out.drop(columns=["name_key"]).to_file(OUT / "islands_codab_with_census2022.gpkg", layer="islands", driver="GPKG")
    print("census rows:", len(census), " island/ward rows:", len(cw))
    print(cw.match_method.value_counts().to_string())
    print("UNMATCHED:\n", cw[cw.match_method == "UNMATCHED"][["atoll_abbr", "census_island", "census_join_key"]].to_string())
    print("fuzzy/hyphen:\n", cw[cw.match_method.isin(["fuzzy", "hyphen_part", "exact_key_largest_of_dupes"])]
          [["atoll_abbr", "census_island", "adm2_name", "adm2_pcode", "match_method", "match_score"]].to_string())
    print("polygons with census pop:", int(out.inhabited_census2022.sum()), " pop matched:",
          int(out.pop2022.sum()), " of census island+ward total:", int(census[census.level != 'city_total'].pop2022.sum()))


if __name__ == "__main__":
    c = tidy()
    crosswalk(c)
