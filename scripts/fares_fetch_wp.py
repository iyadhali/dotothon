"""Fetch WordPress posts by slug via the public REST API and save JSON + plain text.
Usage: python -I fares_fetch_wp.py <site_base> <out_dir> slug1 slug2 ..."""
import sys, json, re, html, time, urllib.request, urllib.parse, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
base, out = sys.argv[1].rstrip('/'), sys.argv[2]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
def txt(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</tr>|</h\d>", "\n", h)
    h = re.sub(r"(?i)</td>|</th>", " | ", h)
    h = re.sub(r"(?s)<[^>]+>", "", h)
    h = html.unescape(h)
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t\r]+", " ", h)).strip()
for slug in sys.argv[3:]:
    url = f"{base}/wp-json/wp/v2/posts?slug={urllib.parse.quote(slug)}&_fields=id,date,link,title,content"
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60))
    except Exception as e:
        print("FAIL", slug, e); continue
    if not d: print("EMPTY", slug); continue
    p = d[0]
    open(os.path.join(out, slug[:90] + ".json"), "w", encoding="utf-8").write(json.dumps(p, ensure_ascii=False))
    t = f"TITLE: {html.unescape(p['title']['rendered'])}\nDATE: {p['date']}\nURL: {p['link']}\n\n" + txt(p['content']['rendered'])
    open(os.path.join(out, slug[:90] + ".txt"), "w", encoding="utf-8").write(t)
    print("=" * 10, p['date'][:10], p['link']); print(t[:3500])
    time.sleep(1)
