"""Scrape Maldives National University course catalogue by campus (https://courses.mnu.edu.mv).

Writes data/external/education/mnu_courses/mnu_courses_by_campus.csv
(campus, island, atoll, course_id, course, duration, mode, level_group) and caches raw HTML.

Usage: python -I scripts/edu_mnu_courses.py
"""
import csv
import html as H
import re
import time
import urllib.request
from pathlib import Path

OUT = Path(r"C:\Users\user\Music\Datathon\data\external\education\mnu_courses")
RAW = OUT / "html"
RAW.mkdir(parents=True, exist_ok=True)
BASE = "https://courses.mnu.edu.mv"
CAMPUS = {1: ("Male' Campus", "Male'", "K"), 2: ("Thinadhoo Campus", "Thinadhoo", "GDh"),
          3: ("Kulhudhuffushi Campus", "Kulhudhuffushi", "HDh"), 4: ("Gan Campus", "Gan", "L"),
          5: ("Hithadhoo Campus", "Hithadhoo", "S")}
CARD = re.compile(r'<a href="/course/(\d+)"[^>]*>.*?<span id="headlessui-label-[^"]*"[^>]*>(.*?)</span>'
                  r'.*?<span id="headlessui-description-[^"]*"[^>]*><span[^>]*>(.*?)</span>(.*?)</a>', re.S)


def get(url, path):
    if path.exists() and path.stat().st_size > 1000:
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (datathon research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        s = r.read().decode("utf-8", errors="replace")
    path.write_text(s, encoding="utf-8")
    time.sleep(0.4)
    return s


def level(name):
    n = name.lower()
    for key, lab in (("doctor", "Doctorate (MNQF 10)"), ("phd", "Doctorate (MNQF 10)"),
                     ("master", "Master (MNQF 9)"), ("postgraduate", "Postgraduate cert/dip (MNQF 8)"),
                     ("graduate certificate", "Graduate cert (MNQF 8)"), ("graduate diploma", "Graduate dip (MNQF 8)"),
                     ("bachelor", "Bachelor (MNQF 7)"), ("associate degree", "Associate degree (MNQF 6)"),
                     ("advanced diploma", "Advanced diploma (MNQF 6)"), ("diploma", "Diploma (MNQF 5)"),
                     ("advanced certificate", "Advanced certificate (MNQF 4)"), ("foundation", "Foundation (MNQF 4)"),
                     ("certificate iv", "Certificate IV (MNQF 4)"), ("certificate iii", "Certificate III (MNQF 3)"),
                     ("certificate ii", "Certificate II (MNQF 2)"), ("certificate i", "Certificate I (MNQF 1)"),
                     ("certificate", "Certificate (MNQF 1-4)")):
        if key in n:
            return lab
    return "Other/short course"


def main():
    rows = []
    for cid, (cname, island, atoll) in CAMPUS.items():
        seen = set()
        page = 1
        while page < 40:
            s = get(f"{BASE}/campus/{cid}?page={page}", RAW / f"campus{cid}_p{page}.html")
            new = 0
            for m in CARD.finditer(s):
                course_id = m.group(1)
                if course_id in seen:
                    continue
                seen.add(course_id)
                new += 1
                name = H.unescape(re.sub(r"\s+", " ", m.group(2))).strip()
                dur = H.unescape(re.sub(r"<[^>]+>", "", m.group(3))).strip()
                modes = [H.unescape(x).strip() for x in re.findall(r"<span[^>]*>([^<]+)</span>", m.group(4))]
                rows.append(dict(institution="The Maldives National University", campus=cname, island=island,
                                 atoll=atoll, course_id=course_id, course=name, duration=dur,
                                 mode="; ".join(modes), level_group=level(name),
                                 source_url=f"{BASE}/course/{course_id}"))
            if new == 0:
                break
            page += 1
        print(cname, len(seen), "courses")
    with open(OUT / "mnu_courses_by_campus.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("total rows", len(rows))


if __name__ == "__main__":
    main()
