"""Convert saved HTML files to plain text (stdout, UTF-8). Usage: python -I diag_html2txt.py file.html [maxchars] [grep_regex]"""
import html
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
path = sys.argv[1]
maxc = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
pat = sys.argv[3] if len(sys.argv) > 3 else None
s = open(path, encoding="utf-8", errors="ignore").read()
s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S | re.I)
t = html.unescape(re.sub(r"<[^>]+>", " ", s))
t = re.sub(r"\s+", " ", t)
if pat:
    for m in re.finditer(r".{0,250}(?:%s).{0,250}" % pat, t, flags=re.I):
        print("...", m.group(0))
else:
    print(t[:maxc])
