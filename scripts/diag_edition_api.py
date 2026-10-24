"""Pull all article headlines for edition.mv tags via the site's tag-listing API.
Usage: python -I diag_edition_api.py OUTCSV tag1 tag2 ..."""
import sys, json, time, urllib.request, csv
UA = {'User-Agent': 'Mozilla/5.0 (research)'}
out = sys.argv[1]; rows = {}
for tag in sys.argv[2:]:
    page = 1
    while True:
        url = f'https://edge-api.edition.mv/api/edition/tags/{tag}/articles?per_page=100&page={page}'
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception as e:
            print('fail', url, e, file=sys.stderr); break
        for a in d.get('data', []):
            rows[a['id']] = (a['id'], tag, (a.get('headline') or '').replace('\n', ' '), (a.get('summary') or '').replace('\n', ' '), a.get('published_at') or a.get('created_at') or '')
        if not d.get('next_page_url'): break
        page += 1; time.sleep(0.5)
    print(tag, 'done', len(rows), file=sys.stderr)
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['id', 'tag', 'headline', 'summary', 'date']); w.writerows(rows.values())
