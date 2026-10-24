"""External validation: modelled access vs observed outcomes (atoll + island level)."""
import sys, re, json, os
import numpy as np, pandas as pd, openpyxl
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\user\Music\Datathon"
SCR = r"C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Music-Datathon\d458dfe7-195f-4f46-88be-e1f23eed6bc0\scratchpad"
OUT = ROOT + r"\data\processed\validation"
os.makedirs(OUT, exist_ok=True)
GM = {"Maale", "Hulhumaale", "Hulhule", "Vilin'gili"}

isl = pd.DataFrame(json.load(open(ROOT + r"\web\public\data\multimodal.json", encoding="utf-8"))["islands"])
isl = isl[isl.isOrigin].copy()
isl["gm"] = isl.name.isin(GM)
acc = pd.read_csv(SCR + r"\island_access.csv")
best = pd.read_csv(SCR + r"\island_access_best.csv")

CATS = {"hosp": "health_hospital", "reg": "health_regional_tertiary", "g1112": "education_grade_11_12"}


def island_table(air):
    rows = isl[["id", "name", "atoll", "population", "gm"]].rename(columns={"id": "origin_island_id"}).copy()
    for k, c in CATS.items():
        a = acc[(acc.category == c) & (acc.estimated_air == air)]
        nod = a.groupby("origin_island_id").status.agg(lambda s: (s == "no_origin_access").all())
        b = best[(best.category == c) & (best.estimated_air == air)].set_index("origin_island_id").best_elapsed_minutes
        rows[f"{k}_min"] = rows.origin_island_id.map(b)
        rows[f"{k}_nodata"] = rows.origin_island_id.map(nod).fillna(True)
        rows.loc[rows[f"{k}_min"].notna(), f"{k}_nodata"] = False
        rows[f"{k}_noroute"] = rows[f"{k}_min"].isna() & ~rows[f"{k}_nodata"]
    return rows


def agg(rows, key):
    out = []
    for g, d in rows.groupby(key):
        r = {key: g, "pop_model": d.population.sum(), "n_islands": len(d)}
        w = d.population
        for k in CATS:
            nod = d[f"{k}_nodata"]; nr = d[f"{k}_noroute"]; ok = d[f"{k}_min"].notna()
            r[f"{k}_pct_nodata"] = 100 * w[nod].sum() / w.sum()
            cov = w[~nod].sum()
            r[f"{k}_pct_noroute_of_covered"] = 100 * w[nr].sum() / cov if cov > 0 else np.nan
            r[f"{k}_pct_noroute_of_total"] = 100 * w[nr].sum() / w.sum()
            r[f"{k}_min_reachable"] = np.average(d.loc[ok, f"{k}_min"], weights=w[ok]) if ok.any() else np.nan
            m = d.loc[~nod, f"{k}_min"].fillna(1440)
            r[f"{k}_min_penalised"] = np.average(m, weights=w[~nod]) if cov > 0 else np.nan
        out.append(r)
    return pd.DataFrame(out)


H = pd.read_csv(ROOT + r"\data\external\health\_derived\health_atoll_summary.csv")
H["key"] = H.atoll.replace({"Male'": "MLE"})
H = H[["key", "pop2022_resident", "evacuations_per_1000_2023", "op_visits_per_capita_2023",
       "aasandha_exp_per_capita_2025_mvr", "inpatient_beds_per_1000"]]

E = ROOT + "\\data\\external\\education\\census2022_education_migration\\"
ed17 = pd.read_csv(E + "census2022_ED17_studying_by_age_island_long.csv")
ed17 = ed17[ed17.island.notna()].copy(); ed17["key"] = ed17.atoll.str.upper()
a1619 = ed17[ed17.age_group == "16-19"].groupby("key")[["resident_maldivian_pop", "currently_studying"]].sum()
a1619["pct_16_19_studying"] = 100 * a1619.currently_studying / a1619.resident_maldivian_pop
tot = ed17.groupby("key").resident_maldivian_pop.sum().rename("maldivian_pop_all_ages")
ed18 = pd.read_csv(E + "census2022_ED18_attending_by_level_island.csv")
ed18 = ed18[ed18.row_type == "island"].copy(); ed18["key"] = ed18.atoll.str.upper()
hs = ed18.groupby("key").higher_secondary_g11_12.sum().rename("hs_attending_residents")
mg = pd.read_csv(E + "census2022_MG13_male_residents_by_registered_island.csv")
mg["key"] = mg.registered_atoll.str.upper()
mgs = mg.groupby("key").male_residents_both.sum().rename("registered_here_living_in_male")
EDU = a1619.join(tot).join(hs).join(mgs)
EDU["male_resident_per_1000_pop"] = 1000 * EDU.registered_here_living_in_male / EDU.maldivian_pop_all_ages
EDU["g11_12_per_100_16_19"] = 100 * EDU.hs_attending_residents / EDU.resident_maldivian_pop
EDU = EDU.reset_index()
_m = {c.upper(): c for c in isl.atoll.unique()}
EDU["key"] = EDU.key.map(lambda k: _m.get(str(k).upper(), k))


def build(air):
    t = island_table(air)
    t["grp"] = np.where(t.gm, "MLE", t.atoll)
    A = agg(t, "grp").rename(columns={"grp": "key"})
    A["estimated_air"] = air
    A = A.merge(H, on="key", how="left").merge(EDU.drop(columns=["resident_maldivian_pop", "currently_studying"]), on="key", how="left")
    return A, t


A0, T0 = build(0)
A1, T1 = build(1)
atoll = pd.concat([A0, A1], ignore_index=True)
atoll["is_greater_male"] = atoll.key == "MLE"
atoll.to_csv(OUT + r"\atoll_access_vs_outcomes.csv", index=False)
T0.to_csv(OUT + r"\island_access_modelled.csv", index=False)


def sp(x, y):
    d = pd.concat([x, y], axis=1).dropna()
    if len(d) < 4 or d.iloc[:, 0].nunique() < 3 or d.iloc[:, 1].nunique() < 3:
        return len(d), np.nan, np.nan
    r, p = spearmanr(d.iloc[:, 0], d.iloc[:, 1])
    return len(d), r, p


HEALTH_X = {"hosp_min_reachable": "Hospital (tier 1-3): mean best-of-day minutes, reachable pop",
            "hosp_min_penalised": "Hospital: mean minutes, no-route = 1440",
            "hosp_pct_noroute_of_covered": "Hospital: % covered pop with no same-day route",
            "reg_min_reachable": "Regional/tertiary: mean best-of-day minutes, reachable pop",
            "reg_min_penalised": "Regional/tertiary: mean minutes, no-route = 1440",
            "reg_pct_noroute_of_covered": "Regional/tertiary: % covered pop with no same-day route",
            "hosp_pct_nodata": "% pop with no transport data coverage"}
HEALTH_Y = {"evacuations_per_1000_2023": "Emergency evacuations per 1,000 (2023)",
            "op_visits_per_capita_2023": "Outpatient visits per person (2023)",
            "aasandha_exp_per_capita_2025_mvr": "Aasandha spend per person (MVR, 2025)"}
EDU_X = {"g1112_min_reachable": "Grade 11-12: mean best-of-day minutes, reachable pop",
         "g1112_min_penalised": "Grade 11-12: mean minutes, no-route = 1440",
         "g1112_pct_noroute_of_covered": "Grade 11-12: % covered pop with no same-day route",
         "g1112_pct_nodata": "% pop with no transport data coverage"}
EDU_Y = {"pct_16_19_studying": "% of 16-19 yr olds in education (census 2022)",
         "male_resident_per_1000_pop": "Registered-here residents living in Male' per 1,000 (census 2022)",
         "g11_12_per_100_16_19": "Residents attending Gr 11-12 per 100 aged 16-19"}

res = []
for air, A in [(0, A0), (1, A1)]:
    for label, sub in [("20 atolls (excl Greater Male)", A[A.key != "MLE"]), ("21 incl Greater Male", A)]:
        for xs, ys, dom in [(HEALTH_X, HEALTH_Y, "health"), (EDU_X, EDU_Y, "education")]:
            if dom == "education" and label.startswith("21"):
                continue
            for x in xs:
                for y in ys:
                    n, r, p = sp(sub[x], sub[y])
                    res.append(dict(domain=dom, estimated_air=air, sample=label, x=x, y=y, n=n, spearman_rho=r, p_value=p))
for air, A in [(0, A0), (1, A1)]:
    sub = A[(A.key != "MLE") & (A.hosp_pct_nodata <= 35)]
    for xs, ys, dom in [(HEALTH_X, HEALTH_Y, "health"), (EDU_X, EDU_Y, "education")]:
        for x in xs:
            if x.endswith("pct_nodata"): continue
            for y in ys:
                n, r, p = sp(sub[x], sub[y])
                res.append(dict(domain=dom, estimated_air=air, sample="atolls with <=35% pop uncovered (excl Greater Male)", x=x, y=y, n=n, spearman_rho=r, p_value=p))
R = pd.DataFrame(res)
R.to_csv(OUT + r"\validation_correlations.csv", index=False)


def scatter(df, x, y, xl, yl, fname, extra="", label_col="key"):
    d = df[[x, y, label_col]].dropna()
    n, r, p = sp(d[x], d[y])
    fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=130)
    ax.scatter(d[x], d[y], s=42, color="#1f6f8b", edgecolor="white", zorder=3)
    if len(d) <= 40:
        for _, row in d.iterrows():
            ax.annotate(row[label_col], (row[x], row[y]), fontsize=7, xytext=(3, 3), textcoords="offset points", color="#444")
    ax.set_xlabel(xl, fontsize=8); ax.set_ylabel(yl, fontsize=8)
    ax.set_title(f"Spearman rho = {r:+.2f}, p = {p:.3f}, n = {n}{extra}", fontsize=9)
    ax.grid(alpha=.25); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(OUT + "\\" + fname); plt.close(fig)


for x in ["hosp_min_reachable", "hosp_pct_noroute_of_covered", "reg_min_reachable", "reg_pct_noroute_of_covered", "hosp_pct_nodata"]:
    for y in HEALTH_Y:
        scatter(A0[A0.key != "MLE"], x, y, HEALTH_X[x], HEALTH_Y[y], f"atoll_{x}__{y}.png", ", 20 atolls excl Greater Male")
for x in ["g1112_min_reachable", "g1112_pct_noroute_of_covered"]:
    for y in EDU_Y:
        scatter(A0[A0.key != "MLE"], x, y, EDU_X[x], EDU_Y[y], f"atoll_edu_{x}__{y}.png", ", 20 atolls")

# ---------- island level: Aasandha 2024 ----------
wb = openpyxl.load_workbook(ROOT + r"\data\external\health\mbs_statistical_yearbook\yb2025\18.26.xlsx", data_only=True)
rows = list(wb.active.iter_rows(values_only=True))[4:]
recs, cur = [], None
for r in rows:
    nm = r[0]
    if nm is None:
        continue
    nm = str(nm).strip()
    if nm in ("Republic", "Atolls", "Male'"):
        cur = None; continue
    m = re.search(r"\(([A-Za-z]+)\)\s*$", nm)
    if m:
        cur = m.group(1); continue
    if cur and not nm.startswith(("Note", "Source")) and not re.match(r"^\d_/", nm):
        recs.append((cur, re.sub(r"\s*\d_/\s*$", "", nm), r[10]))
AI = pd.DataFrame(recs, columns=["atoll_code", "island_raw", "v24"])
AI["atoll_u"] = AI.atoll_code.str.upper()


def norm(s):
    s = s.lower().replace("'", "")
    for a, b in [("aa", "a"), ("oo", "o"), ("ee", "e"), ("dh", "d"), ("th", "t"), ("ii", "i")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z]", "", s)


T0["atoll_u"] = T0.atoll.str.upper(); T0["nm"] = T0.name.map(norm)
AI["nm"] = AI.island_raw.map(norm)
AI["aasandha_2024_mvr"] = pd.to_numeric(AI.v24, errors="coerce")
import difflib
def fuzzy_fix(t, src_names):
    t = t.copy(); fixed = 0
    for i, r in t.iterrows():
        pool = src_names.get(r.atoll_u, [])
        if r.nm not in pool:
            m = difflib.get_close_matches(r.nm, pool, n=1, cutoff=0.8)
            if m: t.at[i, "nm"] = m[0]; fixed += 1
    print("fuzzy-matched", fixed); return t
_pool = AI.groupby("atoll_u").nm.apply(list).to_dict()
T0f = fuzzy_fix(T0, _pool)
J = T0f[~T0f.gm].merge(AI[["atoll_u", "nm", "island_raw", "aasandha_2024_mvr"]].drop_duplicates(["atoll_u", "nm"]), on=["atoll_u", "nm"], how="left")
J["aasandha_per_person_2024"] = J.aasandha_2024_mvr / J.population
J.to_csv(OUT + r"\island_aasandha_vs_access.csv", index=False)
print("island parse:", len(AI), "model islands:", len(J), "matched:", J.aasandha_2024_mvr.notna().sum())
print("unmatched model:", J[J.aasandha_2024_mvr.isna()][["atoll", "name"]].values.tolist()[:40])

isl_res = []
Jd = J[J.aasandha_per_person_2024 > 0]
for lab, d in [("all matched islands, Aasandha>0", Jd),
               ("excl islands with on-island hospital (min>0)", Jd[Jd.hosp_min > 0]),
               ("islands with a hospital route (reachable)", Jd[Jd.hosp_min.notna()])]:
    for x in ["hosp_min", "reg_min"]:
        n, r, p = sp(d[x], d.aasandha_per_person_2024)
        isl_res.append(dict(sample=lab, x=x, y="aasandha_per_person_2024", n=n, spearman_rho=r, p_value=p))
d = Jd[~Jd.hosp_nodata]
n, r, p = sp(d.hosp_noroute.astype(float), d.aasandha_per_person_2024)
isl_res.append(dict(sample="covered islands: no-route=1 vs route=0", x="hosp_noroute", y="aasandha_per_person_2024", n=n, spearman_rho=r, p_value=p))

ed = ed17[ed17.age_group == "16-19"][["atoll", "island", "resident_maldivian_pop", "currently_studying", "pct_studying"]].copy()
ed["atoll_u"] = ed.atoll.str.upper(); ed["nm"] = ed.island.map(norm)
T0e = fuzzy_fix(T0, ed.groupby("atoll_u").nm.apply(list).to_dict())
JE = T0e[~T0e.gm].merge(ed.drop_duplicates(["atoll_u", "nm"]), on=["atoll_u", "nm"], how="left")
JE.to_csv(OUT + r"\island_edu_vs_access.csv", index=False)
print("edu island matched:", JE.pct_studying.notna().sum(), "of", len(JE))
for lab, d in [("islands with >=20 aged 16-19", JE[JE.resident_maldivian_pop >= 20]),
               ("same, excl on-island gr 11-12 (min>0)", JE[(JE.resident_maldivian_pop >= 20) & (JE.g1112_min > 0)])]:
    n, r, p = sp(d.g1112_min, d.pct_studying)
    isl_res.append(dict(sample=lab, x="g1112_min", y="pct_16_19_studying", n=n, spearman_rho=r, p_value=p))
    d2 = d[~d.g1112_noroute & ~d.g1112_nodata]
IR = pd.DataFrame(isl_res)
IR.to_csv(OUT + r"\validation_island_correlations.csv", index=False)

scatter(Jd[Jd.hosp_min.notna()], "hosp_min", "aasandha_per_person_2024", "Modelled min to hospital (tier 1-3), best of day",
        "Aasandha spend per person 2024 (MVR)", "island_hosp_min__aasandha_pp.png", ", islands excl Greater Male", label_col="name")
d = JE[(JE.resident_maldivian_pop >= 20) & JE.g1112_min.notna()]
scatter(d, "g1112_min", "pct_studying", "Modelled min to grade 11-12, best of day", "% aged 16-19 in education",
        "island_g1112_min__pct_16_19_studying.png", ", islands >=20 aged 16-19", label_col="name")

pd.set_option("display.width", 250, "display.max_columns", 50, "display.max_rows", 300)
print(A0[["key", "pop_model", "hosp_min_reachable", "hosp_pct_noroute_of_covered", "hosp_pct_nodata", "reg_min_reachable",
          "reg_pct_noroute_of_covered", "g1112_min_reachable", "g1112_pct_noroute_of_covered"]].round(1).to_string())
print(R[(R.estimated_air == 0) & R["sample"].str.startswith("atolls")].round(3).to_string())
print(R[(R.estimated_air == 0) & R["sample"].str.startswith("20")].round(3).to_string())
print(IR.round(3).to_string())
