"""Parse RTL ferry fare tables published in the Maldives Government Gazette.

Inputs : saved gazette.gov.mv/iulaan/<id> HTML pages (tables are inline HTML).
         data/external/_derived/mdv_islands_master.csv (island centroids).
Output : CSV of origin/destination fares (one-way + return) with great-circle km.

Usage:
  python -I fares_parse_gazette_rtl.py <gazette_dir> <islands_master.csv> <out.csv> [--debug ID]
"""
import csv
import difflib
import html
import math
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------- Thaana
CONS = {
    "ހ": "h", "ށ": "sh", "ނ": "n", "ރ": "r", "ބ": "b",
    "ޅ": "lh", "ކ": "k", "އ": "", "ވ": "v", "މ": "m",
    "ފ": "f", "ދ": "dh", "ތ": "th", "ލ": "l", "ގ": "g",
    "ޏ": "gn", "ސ": "s", "ޑ": "d", "ޒ": "z", "ޓ": "t",
    "ޔ": "y", "ޕ": "p", "ޖ": "j", "ޗ": "ch", "ޘ": "th",
    "ޙ": "h", "ޚ": "kh", "ޛ": "dh", "ޜ": "z", "ޝ": "sh",
    "ޞ": "s", "ޟ": "dh", "ޠ": "t", "ޡ": "z", "ޢ": "",
    "ޣ": "gh", "ޤ": "q", "ޥ": "w", "ޱ": "n",
}
VOW = {
    "ަ": "a", "ާ": "aa", "ި": "i", "ީ": "ee", "ު": "u",
    "ޫ": "oo", "ެ": "e", "ޭ": "ey", "ޮ": "o", "ޯ": "oa",
    "ް": "",  # sukun
}


def translit(s: str) -> str:
    out = []
    chars = list(s)
    for i, ch in enumerate(chars):
        if ch in CONS:
            nxt = chars[i + 1] if i + 1 < len(chars) else ""
            if ch == "އ" and nxt == "ް":  # alif+sukun -> geminate / h
                out.append("h")
            else:
                out.append(CONS[ch])
        elif ch in VOW:
            out.append(VOW[ch])
        else:
            out.append(ch)
    t = "".join(out).strip()
    return t[:1].upper() + t[1:]


def has_thaana(s: str) -> bool:
    return any("ހ" <= c <= "޿" for c in s)


# ---------------------------------------------------------------- atolls
ATOLL_TH = {
    "ހއ": "HA", "ހދ": "HDh", "ށ": "Sh", "ނ": "N", "ރ": "R", "ބ": "B", "ޅ": "Lh",
    "ކ": "K", "އއ": "AA", "އދ": "ADh", "ވ": "V", "މ": "M", "ފ": "F", "ދ": "Dh",
    "ތ": "Th", "ލ": "L", "ގއ": "GA", "ގދ": "GDh", "ޏ": "Gn", "ސ": "S",
    "ގ.އ": "GA", "ގ.ދ": "GDh", "ހ.އ": "HA", "ހ.ދ": "HDh", "އ.އ": "AA", "އ.ދ": "ADh",
}
ATOLL_EN = {
    "ha": "HA", "hdh": "HDh", "sh": "Sh", "n": "N", "r": "R", "b": "B", "lh": "Lh",
    "k": "K", "aa": "AA", "adh": "ADh", "v": "V", "m": "M", "f": "F", "dh": "Dh",
    "th": "Th", "l": "L", "ga": "GA", "gdh": "GDh", "gn": "Gn", "s": "S",
}
ATOLL_NAME = {
    "HA": "Haa Alifu", "HDh": "Haa Dhaalu", "Sh": "Shaviyani", "N": "Noonu", "R": "Raa",
    "B": "Baa", "Lh": "Lhaviyani", "K": "Kaafu", "AA": "Alifu Alifu", "ADh": "Alifu Dhaalu",
    "V": "Vaavu", "M": "Meemu", "F": "Faafu", "Dh": "Dhaalu", "Th": "Thaa", "L": "Laamu",
    "GA": "Gaafu Alifu", "GDh": "Gaafu Dhaalu", "Gn": "Gnaviyani", "S": "Seenu",
}


def atoll_code(s: str) -> str:
    s = s.strip().strip(".").strip()
    if has_thaana(s):
        k = s.replace(" ", "")
        return ATOLL_TH.get(k, ATOLL_TH.get(k.replace(".", ""), ""))
    return ATOLL_EN.get(s.lower().replace(".", "").replace(" ", ""), "")


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("n'", "")
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z]", "", s)
    s = s.replace("ee", "i").replace("oo", "u").replace("aa", "a")
    s = s.replace("th", "t").replace("dh", "d").replace("sh", "s").replace("lh", "l").replace("gn", "n")
    s = re.sub(r"(.)\1+", r"\1", s)
    s = s.replace("hd", "d").replace("hf", "f").replace("hk", "k").replace("ht", "t")
    s = re.sub(r"(.)\1+", r"\1", s)
    return s


# ---------------------------------------------------------------- islands
class Islands:
    def __init__(self, path: str):
        self.by_atoll = {}
        for r in csv.DictReader(open(path, encoding="utf-8")):
            if r["status"] not in ("inhabited", "airport", "resort", "industrial"):
                pass
            try:
                lat, lon = float(r["center_lat"]), float(r["center_lon"])
            except ValueError:
                continue
            rec = (r["adm2_name"], norm_name(r["adm2_name"]), lat, lon, r["status"])
            self.by_atoll.setdefault(r["adm1_name"], []).append(rec)

    def match(self, atoll: str, name: str):
        cands = self.by_atoll.get(ATOLL_NAME.get(atoll, ""), [])
        if atoll in ("K",):
            cands = cands + self.by_atoll.get("Male", [])
        key = norm_name(name)
        exact = [c for c in cands if c[1] == key]
        if exact:
            exact.sort(key=lambda c: c[4] != "inhabited")
            return exact[0], "exact"
        keys = [c[1] for c in cands]
        best = difflib.get_close_matches(key, keys, n=1, cutoff=0.72)
        if best:
            pool = [c for c in cands if c[1] == best[0]]
            pool.sort(key=lambda c: c[4] != "inhabited")
            return pool[0], "fuzzy"
        return None, "none"


def haversine(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[2], a[3], b[2], b[3]))
    d = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(d))


# ---------------------------------------------------------------- HTML tables
class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._row, self._cell, self._depth = [], None, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tables.append([])
        elif tag == "tr" and self.tables:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None and self.tables:
            if any(self._row):
                self.tables[-1].append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


NUM = re.compile(r"^\d{1,4}(\.\d+)?$")


def pub_date(txt: str) -> str:
    months = {"ޖަނަވަރީ": 1, "ފެބުރުއަރީ": 2, "ފެބުރުވަރީ": 2, "މާރިޗު": 3, "މާޗް": 3,
              "އޭޕްރީލް": 4, "އޭޕްރިލް": 4, "މޭ": 5, "ޖޫން": 6, "އޮގަސްޓް": 8, "އޮކްޓޯބަރު": 10,
              "ޖުލައި": 7, "އޮގަސްޓު": 8, "ސެޕްޓެންބަރު": 9, "އޮކްޓޫބަރު": 10, "ނޮވެންބަރު": 11,
              "ޑިސެންބަރު": 12}
    m = re.search(r"ޕަބްލިޝްކުރި ތާރީޚު:\s*(\d{1,2})\s+(\S+)\s+(\d{4})", txt)
    if not m:
        return ""
    mo = months.get(m.group(2), 0)
    return f"{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}" if mo else f"{m.group(3)}"


def split_atoll_island(cell: str):
    """'ޅ. ހިންނަވަރު' or 'G.Dh Thinadhoo' -> (atoll_code, island)."""
    cell = cell.strip()
    if has_thaana(cell):
        m = re.match(r"^([ހ-޿]{1,4}(?:\.[ހ-޿])?)\s*\.\s*(.+)$", cell)
        if m:
            return atoll_code(m.group(1)), m.group(2).strip()
    else:
        m = re.match(r"^([A-Za-z]{1,3}(?:\.[A-Za-z]{1,2})?)[.\s]+(.+)$", cell)
        if m and atoll_code(m.group(1)):
            return atoll_code(m.group(1)), m.group(2).strip()
    return "", cell


def parse_notice(path: Path, debug=False):
    raw = path.read_text(encoding="utf-8", errors="replace")
    txt = re.sub(r"<[^>]+>", "\n", raw)
    txt = html.unescape(txt)
    date = pub_date(txt)
    cancelled = "ބާތިލް ކުރެވިފައެވެ" in txt
    tp = TableParser()
    tp.feed(raw)
    out = []
    for t in tp.tables:
        # header orientation: return-before-oneway (old RTL layout) ?
        head = " ".join(" ".join(r) for r in t[:3])
        i_ret, i_one = head.find("ދެކޮޅު"), head.find("އެއްކޮޅު")
        ret_first = i_ret != -1 and i_one != -1 and i_ret < i_one
        for row in t:
            if debug:
                print(row)
            cells = [c for c in row if c != ""]
            nums = [c for c in cells if NUM.match(c)]
            texts = [c for c in cells if not NUM.match(c)]
            if len(nums) < 2 or not texts:
                continue
            # drop running index '#'
            if len(cells) >= 7 and NUM.match(cells[0]):
                cells = cells[1:]
                nums = [c for c in cells if NUM.match(c)]
                texts = [c for c in cells if not NUM.match(c)]
            fares = [float(x) for x in nums[-2:]] if not ret_first else [float(x) for x in nums[:2]]
            one, ret = (fares[1], fares[0]) if ret_first else (fares[0], fares[1])
            if len(texts) >= 4:
                o_at, o_is, d_at, d_is = atoll_code(texts[0]), texts[1], atoll_code(texts[2]), texts[3]
            elif len(texts) == 2:
                a, b = split_atoll_island(texts[0]), split_atoll_island(texts[1])
                (o_at, o_is), (d_at, d_is) = (b, a) if ret_first else (a, b)
            else:
                continue
            if not o_at or not d_at:
                continue
            out.append(dict(o_at=o_at, o_is=o_is, d_at=d_at, d_is=d_is, one=one, ret=ret,
                            date=date, cancelled=cancelled))
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    gdir, master, outp = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    dbg = sys.argv[sys.argv.index("--debug") + 1] if "--debug" in sys.argv else None
    isl = Islands(master)
    rows, unmatched = [], set()
    files = sorted(gdir.glob("iulaan_*.html"))
    for f in files:
        gid = f.stem.split("_")[1]
        if dbg and gid != dbg:
            continue
        recs = parse_notice(f, debug=bool(dbg))
        for r in recs:
            res = []
            for at, name in ((r["o_at"], r["o_is"]), (r["d_at"], r["d_is"])):
                first = re.split(r"\s*/\s*", name)[0]
                lat_name = translit(first) if has_thaana(first) else first
                m, how = isl.match(at, lat_name)
                if not m:
                    unmatched.add((at, name, lat_name))
                res.append((lat_name, m, how))
            (on, om, oh), (dn, dm, dh) = res
            km = round(haversine(om, dm), 2) if om and dm else ""
            if on == "Hulhumeedhoo" or (om and om[0] == "Hulhudhoo" and r["o_at"] == "S"):
                on, om = "Hulhumeedhoo", (("Hulhumeedhoo",) + tuple(om[1:])) if om else None
            if dn == "Hulhumeedhoo" or (dm and dm[0] == "Hulhudhoo" and r["d_at"] == "S"):
                dn, dm = "Hulhumeedhoo", (("Hulhumeedhoo",) + tuple(dm[1:])) if dm else None
            rows.append({
                "gazette_id": gid, "pub_date": r["date"], "cancelled": r["cancelled"],
                "origin_atoll": r["o_at"], "origin_raw": r["o_is"],
                "origin": om[0] if om else on, "origin_match": oh,
                "destination_atoll": r["d_at"], "destination_raw": r["d_is"],
                "destination": dm[0] if dm else dn, "destination_match": dh,
                "one_way_mvr": r["one"], "return_mvr": r["ret"], "gc_km": km,
            })
        print(f"{gid}: {len(recs)} rows")
    if dbg:
        return
    with open(outp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {outp}")
    for u in sorted(unmatched):
        print("UNMATCHED", u)


if __name__ == "__main__":
    main()
