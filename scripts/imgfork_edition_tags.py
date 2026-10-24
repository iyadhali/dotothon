"""(imaging fork) List article links+titles from edition.mv topic pages. Usage: python -I imgfork_edition_tags.py OUTDIR tag1 tag2..."""
import re,sys,html,os,urllib.request
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
for tag in sys.argv[2:]:
    u=f'https://edition.mv/{tag}'
    p=os.path.join(out,f'edition_tag_{tag}.html')
    try:
        if not os.path.exists(p):
            d=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read(); open(p,'wb').write(d)
        s=open(p,encoding='utf-8',errors='ignore').read()
    except Exception as e:
        print('##',u,'ERR',e); continue
    print('##',u)
    seen=set()
    for href,inner in re.findall(r'<a[^>]+href="(?:https://edition\.mv)?(/[a-z_]+/\d+)[^"]*"[^>]*>(.*?)</a>',s,re.S):
        txt=re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',inner))).strip()
        if href in seen or len(txt)<15: continue
        seen.add(href); print('  ',href,'|',txt[:150])
