"""Strip HTML to plain text. Usage: python -I html_to_text.py file.html [maxchars] [grep_regex]"""
import re, sys, html
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
t = re.sub(r"(?is)<(script|style|noscript|svg).*?</\1>", " ", t)
t = re.sub(r"(?s)<[^>]+>", "\n", t)
t = html.unescape(t)
t = re.sub(r"[ \t\r]+", " ", t)
t = re.sub(r"\n\s*\n+", "\n", t)
mx = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
if len(sys.argv) > 3:
    rx = re.compile(sys.argv[3], re.I)
    lines = t.split("\n")
    for i, l in enumerate(lines):
        if rx.search(l):
            print(i, l.strip()[:400])
else:
    print(t[:mx])
