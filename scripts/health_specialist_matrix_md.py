"""Print a markdown island x specialty matrix from specialist_services.csv.
Usage: python -I health_specialist_matrix_md.py <specialist_services.csv>
 ● = at least one high/medium-confidence active row; ○ = only low-confidence; v = visiting/camp only
"""
import csv
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
NOT_ACTIVE = re.compile(r"^(no |not yet|planned|proposed|under construction)|not (yet )?operational|\bgap\b", re.I)
COLS = [("dialysis", "Dial"), ("oncology", "Onc"), ("cardiology", "Card"), ("icu", "ICU"), ("nicu", "NICU"),
        ("maternity", "O&G"), ("paediatrics", "Paed"), ("surgery", "Surg"), ("orthopaedics", "Orth"),
        ("ent", "ENT"), ("ophthalmology", "Eye"), ("dermatology", "Derm"), ("psychiatry", "Psy"),
        ("physiotherapy", "Phys"), ("ncd_diabetes", "NCD"), ("thalassaemia", "Thal"),
        ("drug_rehab", "Drug"), ("emergency", "ER"), ("telemedicine", "Tele"),
        ("visiting_specialist", "Visit")]
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
m = defaultdict(lambda: defaultdict(str))
for r in rows:
    if not r["island"] or NOT_ACTIVE.search(r["service_detail"]):
        continue
    isl = ("Greater Male' (Male'/Hulhumale'/Villimale')", "MLE") if r["atoll"] == "MLE" else (r["island"], r["atoll"])
    c = r["service_category"]
    vis = "visiting/periodic" in r["service_detail"].lower() or c == "visiting_specialist"
    mark = "v" if vis and c != "visiting_specialist" else ("●" if r["confidence"] in ("high", "medium") else "○")
    cur = m[isl][c]
    rank = {"": 0, "v": 1, "○": 2, "●": 3}
    if rank[mark] > rank[cur]:
        m[isl][c] = mark
order = ["MLE", "HA", "HDh", "Sh", "N", "R", "B", "Lh", "K", "AA", "ADh", "V", "M", "F", "Dh", "Th", "L", "GA", "GDh", "Gn", "S"]
keys = sorted(m, key=lambda k: (order.index(k[1]) if k[1] in order else 99, k[0]))
print("| Atoll | Island | " + " | ".join(h for _, h in COLS) + " | n |")
print("|---|---|" + "---|" * (len(COLS) + 1))
for k in keys:
    n = sum(1 for c, _ in COLS if m[k][c] in ("●", "○") and c != "visiting_specialist")
    print(f"| {k[1]} | {k[0]} | " + " | ".join(m[k][c] for c, _ in COLS) + f" | {n} |")
