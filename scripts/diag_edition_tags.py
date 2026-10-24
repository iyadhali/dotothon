"""Crawl edition.mv tag listing pages and collect (id, title, date). Usage: python -I diag_edition_tags.py OUTDIR tag maxpages"""
import sys, re, html, time, urllib.request, csv, os
out, tag, maxp = sys.argv[1], sys.argv[2], int(sys.argv[3])
UA = {'User-Agent': 'Mozilla/5.0 (research)'}
rows, seen = [], set()
for p in range(1, maxp + 1):
    url = f'https://edition.mv/{tag}?page={p}'
    try:
        s = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'ignore')
    except Exception as e:
        print('fail', url, e, file=sys.stderr); break
    new = 0
    for i, txt in re.findall(r'href="/(?:news|features|business)/(\d+)[^"]*"[^>]*>(.*?)</a>', s, re.S):
        txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(txt))).strip()
        if i in seen or not txt: continue
        seen.add(i); new += 1; rows.append((i, txt[:200], p))
    if new == 0: break
    time.sleep(0.7)
with open(os.path.join(out, f'edition_tag_{tag}.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['id', 'title', 'page']); w.writerows(rows)
print(tag, 'pages', p, 'articles', len(rows))
