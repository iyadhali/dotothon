"""Parse Aasandha empanelled-facilities HTML pages (2-col table). Usage: python -I diag_parse_aasandha.py out.csv in1.html [in2.html ...]"""
import csv, html, re, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = set()
for p in sys.argv[2:]:
    s = open(p, encoding="utf-8", errors="ignore").read()
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", s, flags=re.S):
        c = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", r, flags=re.S)]
        if len(c) >= 2:
            rows.add(tuple(c[:2]))
with open(sys.argv[1], "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["provider", "island"])
    for r in sorted(rows):
        w.writerow(r)
print(len(rows))
