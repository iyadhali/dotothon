"""Extract readable text from saved HTML news pages (diagnostics research, PCR/blood bank stream)."""
import sys, re, html
for p in sys.argv[1:]:
    s = open(p, encoding='utf-8', errors='ignore').read()
    s = re.sub(r'(?is)<(script|style|noscript|svg).*?</\1>', ' ', s)
    t = re.search(r'(?is)<title>(.*?)</title>', s)
    s = re.sub(r'(?is)<br\s*/?>|</p>|</h\d>|</li>|</div>', '\n', s)
    s = re.sub(r'(?s)<[^>]+>', ' ', s)
    s = html.unescape(s)
    lines = [re.sub(r'[ \t]+', ' ', l).strip() for l in s.splitlines()]
    lines = [l for l in lines if len(l) > 40]
    out = p.rsplit('.', 1)[0] + '.txt'
    open(out, 'w', encoding='utf-8').write((t.group(1).strip() if t else '') + '\n' + '\n'.join(lines))
