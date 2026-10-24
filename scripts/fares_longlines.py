"""Print long text lines (article body) from an HTML file. Usage: python -I fares_longlines.py file.html [minlen]"""
import re, sys, html
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
t = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", t)
t = re.sub(r"(?s)<[^>]+>", "\n", t)
t = html.unescape(t)
t = re.sub(r"[ \t\r]+", " ", t)
mn = int(sys.argv[2]) if len(sys.argv) > 2 else 80
seen=set()
for l in t.split("\n"):
    l=l.strip()
    if len(l)>=mn and l not in seen:
        seen.add(l); print("-", l[:1500])
