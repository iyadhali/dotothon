"""Extract headline/date/body text from a saved Maldives Independent (Next.js) article HTML.
Usage: python -I fares_mi_text.py file.html [file2.html ...]  -> prints and writes file.txt"""
import re, sys, json, html
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
for fn in sys.argv[1:]:
    t = open(fn, encoding="utf-8", errors="replace").read()
    out = []
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
    for ld in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
        try:
            d = json.loads(ld)
            if isinstance(d, dict) and d.get("@type") == "NewsArticle":
                out.append(f"HEADLINE: {d.get('headline')}\nDATE: {d.get('datePublished')}\nURL: {d.get('url')}\nDESC: {d.get('description')}")
                if d.get("articleBody"): out.append(d["articleBody"])
                break
        except Exception:
            pass
    if len(out) < 2:
        chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', t, re.S)
        s = "".join(chunks)
        try:
            s = json.loads('"' + s.replace('\n', '\n') + '"')
        except Exception:
            s = s.encode("utf-8", "ignore").decode("unicode_escape", "ignore")
        # body paragraphs appear as "text":"..." blocks and T-chunks with html
        paras = re.findall(r'"text":"(.{40,}?)"(?=[,}])', s)
        paras += re.findall(r'<p>(.*?)</p>', s, re.S)
        seen = set()
        for p in paras:
            p = html.unescape(re.sub(r"<[^>]+>", "", p)).replace("&nbsp;", " ").strip()
            if p and p not in seen:
                seen.add(p); out.append(p)
    txt = "\n".join(out)
    open(fn.rsplit(".", 1)[0] + ".txt", "w", encoding="utf-8").write(txt)
    print("=" * 8, fn); print(txt[:4000])
