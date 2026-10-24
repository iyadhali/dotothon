"""List all tables (title + PDF/XLS links) from MBS Statistical Yearbook pages.

Usage: python -I health_yearbook_list.py <html_file> [<html_file> ...]
Prints TSV: file, title, pdf, xls  (only rows matching health-ish keywords unless --all)
"""
import html
import re
import sys

KW = re.compile(r"health|hospital|medical|patient|disease|death|mortal|birth|"
                r"insurance|aasandha|dhamana|immuni|tuberc|malaria|dengue|"
                r"bed|doctor|nurse|pharmac|disab|nutrition|infant|maternal|"
                r"causes|ambulance|evacuat|referr", re.I)


def parse(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    items = re.split(r'class="[^"]*(?:table-item|list-group-item|card-body)[^"]*"', txt)[1:]
    for it in items:
        m = re.search(r'<(?:span|p) class="(?:fw-semibold|me-2|fs-sm)">(.*?)</(?:span|p)>', it, re.S)
        if not m:
            continue
        title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
        pdf = re.search(r'href="([^"]+\.pdf)"', it[:3000])
        xls = re.search(r'href="([^"]+\.xlsx?)"', it[:3000])
        yield title, pdf.group(1) if pdf else "", xls.group(1) if xls else ""


if __name__ == "__main__":
    show_all = "--all" in sys.argv
    for f in [a for a in sys.argv[1:] if a != "--all"]:
        for t, p, x in parse(f):
            if show_all or KW.search(t):
                print(f"{f}\t{t}\t{p}\t{x}")
