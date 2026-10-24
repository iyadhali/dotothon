"""Fetch gazette notice pages by id; save html; print date, office, title, first body text."""
import sys, re, html, os, urllib.request, time
sys.stdout.reconfigure(encoding='utf-8')
OUT = r"C:\Users\user\Music\Datathon\data\external\health\services\diagnostics\sources\public_hospital_labs\gazette\notices"
os.makedirs(OUT, exist_ok=True)
nchars = 700
for nid in sys.argv[1:]:
    if nid.startswith('-n'): nchars = int(nid[2:]); continue
    fp = os.path.join(OUT, f"{nid}.html")
    if not os.path.exists(fp):
        req = urllib.request.Request(f"https://www.gazette.gov.mv/iulaan/{nid}", headers={"User-Agent": "Mozilla/5.0 Chrome/124.0"})
        try:
            s = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'ignore')
        except Exception as e:
            print(nid, "ERR", e); continue
        open(fp, "w", encoding="utf-8").write(s); time.sleep(0.5)
    s = open(fp, encoding="utf-8").read()
    t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', s)
    t = html.unescape(re.sub(r'<[^>]+>', '\n', t)); t = re.sub(r'[ \t\xa0]+', ' ', t); t = re.sub(r'\n\s*\n+', '\n', t)
    a = t.find('އާންމު އިޢުލާން'); body = t[a+15:]
    b = body.find('ހޯދާ'); body = body[:b] if b > 0 else body
    pub = re.search(r'(?:Published date|ޕަބްލިޝްކުރި ތާރީޚު)\s*:?\s*\n?\s*([^\n]+)', t)
    print("=====", nid, "|", pub.group(1).strip() if pub else '')
    print(body.strip()[:nchars])
