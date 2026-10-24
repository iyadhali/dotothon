"""Scrape the MoH Health Establishment Management System (HEMS) public registry.

https://hems.health.gov.mv/establishments  (paginated, 15 rows/page)

Outputs (in OUT_DIR):
  raw_pages/page_NNN.html            raw HTML as downloaded
  hems_establishments.csv            one row per establishment, tidy
  hems_professionals_by_facility.csv counts of registered practising professionals by
                                      profession per facility (aggregated; NO personal names kept)

Usage: python -I health_hems_scrape.py <OUT_DIR> [--professionals]
"""
import csv
import html
import json
import os
import re
import sys
import time
import urllib.request

BASE = "https://hems.health.gov.mv"
UA = {"User-Agent": "Mozilla/5.0 (datathon research; contact hello@looth.xyz)"}

ATOLL_PREFIX = {
    # normalised prefix -> (atoll code used by MBS, atoll name)
    "HA": ("HA", "Haa Alif"), "HDH": ("HDh", "Haa Dhaalu"), "SH": ("Sh", "Shaviyani"),
    "N": ("N", "Noonu"), "R": ("R", "Raa"), "B": ("B", "Baa"), "LH": ("Lh", "Lhaviyani"),
    "K": ("K", "Kaafu"), "AA": ("AA", "Alif Alif"), "ADH": ("ADh", "Alif Dhaal"),
    "V": ("V", "Vaavu"), "M": ("M", "Meemu"), "F": ("F", "Faafu"), "DH": ("Dh", "Dhaalu"),
    "TH": ("Th", "Thaa"), "L": ("L", "Laamu"), "GA": ("GA", "Gaafu Alif"),
    "GDH": ("GDh", "Gaafu Dhaalu"), "GN": ("Gn", "Gnaviyani"), "S": ("S", "Seenu/Addu"),
}


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            print("retry", url, e, file=sys.stderr)
            time.sleep(2 + 3 * i)
    raise RuntimeError(url)


def cf_decode(hexstr):
    """Decode Cloudflare email obfuscation (data-cfemail)."""
    key = int(hexstr[:2], 16)
    return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))


def clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def guess_atoll(name):
    """Pull atoll prefix like 'A.A.', 'AA.', 'A,Dh.', 'HDh.', 'GA.' from the facility name."""
    m = re.match(r"^\s*([A-Za-z]{1,2}(?:[\.,\s]{0,2}[A-Za-z]{1,2})?)[\.,]\s*(\S.*)$", name)
    if not m:
        return "", "", ""
    raw = re.sub(r"[^A-Za-z]", "", m.group(1)).upper()
    if raw in ATOLL_PREFIX:
        code, aname = ATOLL_PREFIX[raw]
        rest = m.group(2)
        island = re.split(r"\s+(?:Health|Atoll|Regional|Hospital|Medical|Clinic)", rest)[0]
        return code, aname, island.strip(" .,")
    return "", "", ""


def parse_page(txt):
    rows = []
    for m in re.finditer(r'<tr\s+class="est-row[^"]*"\s+onclick="toggleProfessionals\(this,\s*(\d+)\)"\s*>(.*?)</tr>',
                         txt, re.S):
        eid, body = m.group(1), m.group(2)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", body, re.S)
        name = clean(re.search(r'<div class="est-name">\s*<span>(.*?)</span>', body, re.S).group(1))
        st = re.search(r'data-test="est-status">(.*?)</span>', body, re.S)
        em = re.search(r'data-cfemail="([0-9a-f]+)"', body)
        web = re.search(r'href="(http[^"]+)"[^>]*class="est-link"', tds[8]) if len(tds) > 8 else None
        code, aname, island = guess_atoll(name)
        rows.append({
            "establishment_id": eid,
            "name": name,
            "status": clean(st.group(1)) if st else "",
            "owner": clean(tds[1]),
            "level": clean(tds[2]),
            "reg_no": clean(tds[3]),
            "license_no": clean(tds[4]),
            "contact": clean(tds[5]),
            "email": cf_decode(em.group(1)) if em else "",
            "n_professionals": clean(tds[7]),
            "website": web.group(1) if web else "",
            "atoll_code_guess": code,
            "atoll_name_guess": aname,
            "island_guess": island,
        })
    return rows


def main():
    out = sys.argv[1]
    want_pros = "--professionals" in sys.argv
    os.makedirs(os.path.join(out, "raw_pages"), exist_ok=True)
    first = get(f"{BASE}/establishments?page=1")
    last = max(int(x) for x in re.findall(r"establishments\?page=(\d+)", first))
    allrows = []
    for p in range(1, last + 1):
        txt = first if p == 1 else get(f"{BASE}/establishments?page={p}")
        open(os.path.join(out, "raw_pages", f"page_{p:03d}.html"), "w", encoding="utf-8").write(txt)
        rows = parse_page(txt)
        print(f"page {p}/{last}: {len(rows)} rows", file=sys.stderr)
        allrows += rows
        time.sleep(0.5)
    # de-duplicate (desktop table only is parsed, but be safe)
    seen, uniq = set(), []
    for r in allrows:
        if r["establishment_id"] not in seen:
            seen.add(r["establishment_id"])
            uniq.append(r)
    with open(os.path.join(out, "hems_establishments.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(uniq[0].keys()))
        w.writeheader()
        w.writerows(uniq)
    print(f"wrote {len(uniq)} establishments", file=sys.stderr)

    if want_pros:
        prow = []
        for r in uniq:
            try:
                n = int(r["n_professionals"] or 0)
            except ValueError:
                n = 0
            if n == 0:
                continue
            data = json.loads(get(f"{BASE}/establishments/{r['establishment_id']}/professionals"))
            items = data if isinstance(data, list) else data.get("data", data.get("professionals", []))
            counts = {}
            for it in items:
                prof = (it.get("profession") or it.get("profession_name") or "")
                if isinstance(prof, dict):
                    prof = prof.get("name", "")
                spec = (it.get("speciality") or it.get("speciality_name") or "")
                if isinstance(spec, dict):
                    spec = spec.get("name", "")
                key = (str(prof).strip(), str(spec).strip())
                counts[key] = counts.get(key, 0) + 1
            for (prof, spec), c in counts.items():
                prow.append({"establishment_id": r["establishment_id"], "name": r["name"],
                             "level": r["level"], "profession": prof, "speciality": spec, "count": c})
            time.sleep(0.3)
        with open(os.path.join(out, "hems_professionals_by_facility.csv"), "w", newline="",
                  encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["establishment_id", "name", "level", "profession",
                                              "speciality", "count"])
            w.writeheader()
            w.writerows(prow)
        print(f"wrote {len(prow)} profession-count rows", file=sys.stderr)


if __name__ == "__main__":
    main()
