"""List article links+titles from news tag pages. Usage: python -I diag_imaging_tags.py OUTDIR url1 url2... (prints /post/ or /NNNN links)"""
import re,sys,html,os,urllib.request
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for u in sys.argv[2:]:
    p=os.path.join(out,re.sub(r'[^A-Za-z0-9]+','_',u.split('://')[1])[:120]+'.html')
    try:
        if not os.path.exists(p):
            d=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read(); open(p,'wb').write(d)
        s=open(p,encoding='utf-8',errors='ignore').read()
    except Exception as e:
        print('##',u,'ERR',e); continue
    print('##',u)
    seen=set()
    for href,inner in re.findall(r'<a[^>]+href="([^"]*(?:/post/[a-z]+/\d+|/en/\d+|mv/\d+)[^"]*)"[^>]*>(.*?)</a>',s,re.S):
        txt=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',inner))).strip()
        if href in seen or len(txt)<12: continue
        seen.add(href); print('  ',href,'|',txt[:140])
