"""Strip HTML to text and print paragraphs containing keywords. Usage: python -I diag_html2text.py file.html [kw1|kw2]"""
import sys, re, html
s = open(sys.argv[1], encoding='utf-8', errors='ignore').read()
s = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', s)
title = re.search(r'(?is)<title>(.*?)</title>', s)
date = re.findall(r'(?i)"datePublished"\s*:\s*"([^"]+)"|article:published_time"\s+content="([^"]+)"', s)
s = re.sub(r'(?i)<(br|/p|/div|/h\d|/li)[^>]*>', '\n', s)
t = html.unescape(re.sub(r'<[^>]+>', ' ', s))
lines = [re.sub(r'\s+', ' ', l).strip() for l in t.split('\n')]
lines = [l for l in lines if len(l) > 40]
print('TITLE:', title.group(1).strip() if title else None, '| DATE:', date[:1])
kw = sys.argv[2] if len(sys.argv) > 2 else None
for l in lines:
    if kw is None or re.search(kw, l, re.I):
        print('-', l[:700])
