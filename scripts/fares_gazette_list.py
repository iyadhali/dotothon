"""Parse saved gazette.gov.mv /iulaan listing pages: print id, office, title.

Usage: python -I fares_gazette_list.py <listing.html> [<listing.html> ...]
"""
import html
import re
import sys


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for path in sys.argv[1:]:
        s = open(path, encoding="utf-8", errors="replace").read()
        m = re.search(r"ޖުމްލަ (\d+)", s)
        print(f"## {path} total={m.group(1) if m else None}")
        seen = set()
        for m in re.finditer(
            r'href="(?:https://www\.gazette\.gov\.mv)?/iulaan/(\d+)"[^>]*>(.*?)</a>', s, re.S
        ):
            t = re.sub(r"<[^>]+>", " ", m.group(2))
            t = html.unescape(re.sub(r"\s+", " ", t)).strip()
            if t and m.group(1) not in seen:
                seen.add(m.group(1))
                print(m.group(1), t[:160])


if __name__ == "__main__":
    main()
