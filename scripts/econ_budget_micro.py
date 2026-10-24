"""Aggregate MoF 2026 Budget Micro Dataset (2024 actual, 2025 revised, 2026-28 budget).
Usage: python -I econ_budget_micro.py <mof_budget_dir>
Outputs in <dir>/derived/: budget_micro_long.parquet-like CSV aggregates.
"""
import sys, os, pandas as pd
d = sys.argv[1]
out = os.path.join(d, "derived"); os.makedirs(out, exist_ok=True)
df = pd.read_excel(os.path.join(d, "2026_Budget_Micro_Dataset.xlsx"), engine="openpyxl")
df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_") for c in df.columns]
df["year"] = df["time"].str[:4].astype(int)
df = df[df["account_type"].str.contains("Outflow", na=False)]
print(df.shape, df.columns.tolist())
keys = ["year", "category"]
def piv(g, name):
    p = g.groupby(g.columns.drop(["amount"]).tolist(), dropna=False)["amount"].sum().reset_index()
    p.to_csv(os.path.join(out, name), index=False)
    return p
# 1. Grants/subsidies/transfers by account (all government)
g = df[df["parent_account"].str.startswith(("228", "227"), na=False)][["year", "category", "account", "amount"]]
p = piv(g, "transfers_by_account.csv")
print(p.pivot_table(index="account", columns="year", values="amount", aggfunc="sum").div(1e6).round(1).to_string())
# 2. COFOG totals
g = df[["year", "category", "cofog", "amount"]]
piv(g, "cofog_totals.csv")
# 3. Selected organizations by program
sel = df["parent_aga"].str.contains("Higher Education|Social Protection|Health|Aasandha|Transport", case=False, na=False)
g = df[sel][["year", "category", "parent_aga", "organization", "sub_program_lv2", "account", "amount"]]
p = piv(g, "selected_agas_program_account.csv")
q = df[sel].groupby(["parent_aga", "sub_program_lv2", "year"])["amount"].sum().unstack("year").div(1e6).round(2)
print(q.to_string())
# 4. Health organizations (hospitals by island) totals
h = df[df["cofog"].str.startswith(("707",), na=False)].groupby(["organization", "year"])["amount"].sum().unstack("year")
h.to_csv(os.path.join(out, "health_cofog_by_organization.csv"))
# 5. Keyword search in program units (patient travel, evacuation, ambulance, dormitory, hostel, ferry)
kw = "evacuat|ambulance|patient|ticket|travel|ferry|transport|hostel|dormitor|accommodat|escort|medevac|scholar|degree|loan"
txt = df["unit_lv3"].fillna("") + " | " + df["sub_unit_activity_lv4"].fillna("")
m = txt.str.contains(kw, case=False)
k = df[m].assign(txt=txt[m]).groupby(["parent_aga", "txt", "year"])["amount"].sum().unstack("year").div(1e6).round(2)
k.to_csv(os.path.join(out, "keyword_units.csv"))
print(k.to_string())
# 6. NSPA + Aasandha detail by unit (Lv4) and account
n = df[df["parent_aga"].str.startswith("S41", na=False)]
nn = n.groupby(["sub_unit_activity_lv4", "account", "year"])["amount"].sum().unstack("year").div(1e6).round(2)
nn.to_csv(os.path.join(out, "nspa_units_accounts.csv"))
