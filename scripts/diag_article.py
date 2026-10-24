"""Print main article paragraphs (<p> text > 60 chars) from a saved news HTML file, plus date hints."""
import sys, re, html
sys.stdout.reconfigure(encoding='utf-8')
for fp in sys.argv[1:]:
    s = open(fp, encoding='utf-8', errors='ignore').read()
    title = re.search(r'<title>(.*?)</title>', s, re.S)
    dates = re.findall(r'(?:datePublished|article:published_time)["\']?\s*(?:content=)?[:=]?\s*["\']([^"\']+)', s)
    print("#####", fp.split('/')[-1], "|", html.unescape(title.group(1).strip()) if title else '', "|", dates[:1])
    ps = re.findall(r'(?is)<p[^>]*>(.*?)</p>', s)
    for p in ps:
        t = html.unescape(re.sub(r'<[^>]+>', '', p)).strip()
        if len(t) > 60: print(" -", t)
