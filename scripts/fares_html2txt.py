"""Convert saved HTML fare sources to plain text and grep fare-related lines.

Usage: python -I fares_html2txt.py <file.html> [regex]
Writes <file>.txt next to the input and prints matching lines with context.
"""
import html
import re
import sys
from pathlib import Path

DEFAULT_RX = r"(MVR|Rf|USD|US\$|\$\s?\d|laari|fare|price|ticket|rufiyaa|charter|per hour)"


def to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(p|div|li|tr|h\d|td|th)>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    lines = [re.sub(r"[ \t\xa0]+", " ", l).strip() for l in raw.splitlines()]
    return "\n".join(l for l in lines if l)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    src = Path(sys.argv[1])
    rx = re.compile(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_RX, re.I)
    txt = to_text(src.read_text(encoding="utf-8", errors="replace"))
    out = src.with_suffix(".txt")
    out.write_text(txt, encoding="utf-8")
    for i, line in enumerate(txt.splitlines()):
        if rx.search(line):
            print(f"{i}: {line[:400]}")


if __name__ == "__main__":
    main()
