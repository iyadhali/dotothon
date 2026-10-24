"""Fetch URLs, save raw HTML, print title + date-ish + keyword excerpts. Usage: python -I diag_fetch.py OUTDIR url1 url2 ..."""
import re,sys,html,os,urllib.request,ssl
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
KW=r'(CT[ -]?scan|\bCT\b|MRI|[Mm]ammo|[Ee]ndoscop|[Cc]olonoscop|X-?[Rr]ay|[Uu]ltraso|USG|[Rr]adiolog|[Ii]maging|[Ss]onograph|[Ll]aborator|[Ff]luoroscop|scanner)'
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
for u in sys.argv[2:]:
    slug=re.sub(r'[^A-Za-z0-9]+','_',u.split('://',1)[-1])[:120]+'.html'
    p=os.path.join(out,slug)
    try:
        if not os.path.exists(p):
            req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'})
            data=urllib.request.urlopen(req,timeout=30,context=ctx).read()
            open(p,'wb').write(data)
        s=open(p,encoding='utf-8',errors='ignore').read()
    except Exception as e:
        print('#####',u,'ERROR',e); continue
    title=re.search(r'<title[^>]*>(.*?)</title>',s,re.S)
    dates=re.findall(r'"datePublished"\s*:\s*"([^"]+)"|article:published_time"\s+content="([^"]+)"',s)
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S)
    t=html.unescape(re.sub(r'<[^>]+>',' ',t)); t=re.sub(r'\s+',' ',t)
    print('#####',u,'|',html.unescape(title.group(1).strip()) if title else '','|',dates[:1],'| len',len(t))
    seen=0; last=-1000
    for m in re.finditer(KW,t):
        if m.start()-last<250: continue
        last=m.start(); print('  ..',t[max(0,m.start()-200):m.start()+250]); seen+=1
        if seen>=int(os.environ.get('NX','6')): break
