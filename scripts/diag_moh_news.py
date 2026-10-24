"""Crawl health.gov.mv news / press-release listings; save slugs+titles. Usage: python -I diag_moh_news.py OUTDIR section maxpages"""
import sys, re, html, time, urllib.request, csv, os
out, sec, maxp = sys.argv[1], sys.argv[2], int(sys.argv[3])
UA = {'User-Agent': 'Mozilla/5.0 (research)'}
rows, seen = [], set()
for p in range(1, maxp + 1):
    url = f'https://health.gov.mv/en/{sec}?page={p}'
    try:
        s = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8', 'ignore')
    except Exception as e:
        print('fail', url, e, file=sys.stderr); break
    new = 0
    for u, txt in re.findall(r'href="(https://health.gov.mv/en/' + sec + r'/[^"?]+)"[^>]*>(.*?)</a>', s, re.S):
        txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(txt))).strip()
        if u in seen: continue
        seen.add(u); new += 1; rows.append((u, txt[:300], p))
    if new == 0: break
    time.sleep(0.5)
with open(os.path.join(out, f'moh_{sec}.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['url', 'title', 'page']); w.writerows(rows)
print(sec, 'pages', p, 'items', len(rows))
