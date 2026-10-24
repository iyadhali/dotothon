"""Search gazette.gov.mv iulaan by keyword; output TSV of id, date, office, title. Saves raw result pages."""
import sys, re, html, time, urllib.request, urllib.parse, os
sys.stdout.reconfigure(encoding='utf-8')
OUT = r"C:\Users\user\Music\Datathon\data\external\health\services\diagnostics\sources\public_hospital_labs\gazette"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'ignore')
q = sys.argv[1]; maxpages = int(sys.argv[2]) if len(sys.argv) > 2 else 5
office = sys.argv[3] if len(sys.argv) > 3 else ""
seen = set()
for p in range(1, maxpages + 1):
    url = "https://www.gazette.gov.mv/iulaan?" + urllib.parse.urlencode({"q": q, "page": p, **({"office": office} if office else {})})
    try:
        s = get(url)
    except Exception as e:
        print("ERR", e); break
    open(os.path.join(OUT, f"search_{office}_{abs(hash(q))%10**6}_{re.sub(r'[^A-Za-z0-9]+','_',q)}_p{p}.html"), "w", encoding="utf-8").write(s)
    if p == 1:
        m = re.search(r'ޖުމްލަ\s*(\d+)', s); print("#total", m.group(1) if m else '?')
    items = s.split('class="col-md-12 bordered items')[1:]
    if not items: break
    newc = 0
    for it in items:
        m = re.search(r'iulaan/(\d+)" title="view details">([^<]*)</a>', it)
        if not m or m.group(1) in seen: continue
        seen.add(m.group(1)); newc += 1
        typ = re.search(r'class="iulaan-type"[^>]*>\s*([^<]*?)\s*</a>', it)
        off = re.search(r'class="iulaan-office"[^>]*>\s*([^<]*?)\s*</a>', it, re.S)
        dt = re.search(r'Date:\s*([^<]*?)\s*</div>', it, re.S)
        print("	".join([m.group(1), (dt.group(1).strip() if dt else ''), (off.group(1).strip() if off else ''), (typ.group(1).strip() if typ else ''), html.unescape(m.group(2).strip())]))
    if not newc: break
    time.sleep(1)
