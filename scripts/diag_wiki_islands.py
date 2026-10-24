"""Fetch wikitext of Maldives island/health-facility Wikipedia articles and grep for lab/imaging mentions.
Usage: python -I diag_wiki_islands.py OUTDIR"""
import json, sys, os, re, time, urllib.request, urllib.parse
OUT = sys.argv[1]
UA = {'User-Agent': 'DatathonResearch/1.0 (research; see project README)'}
API = 'https://en.wikipedia.org/w/api.php?'
def get(params):
    params['format'] = 'json'
    req = urllib.request.Request(API + urllib.parse.urlencode(params), headers=UA)
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            time.sleep(2)
    return {}
seen_cats, pages = set(), set()
def walk(cat, depth):
    if cat in seen_cats or depth < 0: return
    seen_cats.add(cat)
    cont = {}
    while True:
        d = get(dict(action='query', list='categorymembers', cmtitle=cat, cmlimit='500', **cont))
        for m in d.get('query', {}).get('categorymembers', []):
            if m['ns'] == 14: walk(m['title'], depth - 1)
            elif m['ns'] == 0: pages.add(m['title'])
        if 'continue' in d: cont = {'cmcontinue': d['continue']['cmcontinue']}
        else: break
for c in ['Category:Islands of the Maldives', 'Category:Hospitals in the Maldives', 'Category:Inhabited islands of the Maldives', 'Category:Populated places in the Maldives']:
    walk(c, 2)
pages = sorted(pages)
print('pages', len(pages), file=sys.stderr)
texts = {}
for i in range(0, len(pages), 40):
    d = get(dict(action='query', prop='revisions', rvprop='content', rvslots='main', titles='|'.join(pages[i:i+40])))
    for p in d.get('query', {}).get('pages', {}).values():
        try: texts[p['title']] = p['revisions'][0]['slots']['main']['*']
        except Exception: pass
    time.sleep(0.5)
json.dump(texts, open(os.path.join(OUT, 'wiki_texts.json'), 'w', encoding='utf-8'), ensure_ascii=False)
kw = re.compile(r'laborator|\blab\b|x-ray|xray|x ray|ultrasound|ultra sound|\bUSG\b|scan|radiolog|blood bank|PCR', re.I)
with open(os.path.join(OUT, 'wiki_hits.txt'), 'w', encoding='utf-8') as f:
    for t, s in sorted(texts.items()):
        hits = [re.sub(r'\s+', ' ', x).strip() for x in re.split(r'(?<=[.!?])\s+|\n', s) if kw.search(x)]
        if hits:
            f.write('### ' + t + '\n' + '\n'.join('- ' + h[:500] for h in hits) + '\n')
print('texts', len(texts), file=sys.stderr)
