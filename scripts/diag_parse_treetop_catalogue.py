"""Parse the Tree Top Hospital lab test catalogue embedded in the saved /lab-services HTML.
Usage: python -I diag_parse_treetop_catalogue.py <tth_lab-services.html> <out.csv>"""
import collections
import csv
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8", errors="ignore").read()
pat = re.compile(
    r'\{"id":(\d+),"section":"([^"]*)","tthcode":"([^"]*)","tth_test_description":"((?:[^"\\]|\\.)*)"'
)
seen = {}
for m in pat.finditer(s):
    seen[m.group(1)] = (m.group(1), m.group(2).replace("\\u0026", "&"), m.group(3), m.group(4))
print("tests:", len(seen))
print(collections.Counter(v[1] for v in seen.values()).most_common())
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "section", "code", "test"])
    for v in seen.values():
        w.writerow(v)
for v in seen.values():
    if v[1] in ("Molecular", "Blood Bank"):
        print(v[1], "|", v[3])
ref = " ".join(v[3] for v in seen.values() if v[1] == "Referral Laboratory")
print("referral labs:", collections.Counter(re.findall(r"\(([A-Z][A-Z ]{2,20}?)\s*-\s*[A-Z0-9]", ref)).most_common(8))
