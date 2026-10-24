"""Generic coordinate-based table extractor for text PDFs (PyMuPDF words).

For each page, finds the header line that contains the given header tokens (in order),
uses their x-centres as column anchors, and assigns every numeric/dash token on later lines
to the nearest anchor. Text to the left of the first anchor is the row label; its x-indent is
kept so hierarchical tables (atoll -> profession) can be rebuilt.

Usage:
  python -I health_pdf_coord_table.py <pdf> <p1-p2> "<tok1,tok2,...>" "<name1,name2,...>" <out.csv>
          [--stop "<regex>"] [--parent-indent-max X] [--carry]
[--anchors "x1,x2,..."] [--tol PT]  manual column x-centres (implies --carry)
--carry reuses the previous page's column anchors on continuation pages without a header.
Rows whose label indent <= parent-indent-max are treated as parent rows (e.g. atoll), and
child rows inherit the latest parent label in column 'parent'.
"""
import csv
import re
import site
import sys
from collections import defaultdict

sys.path.append(site.getusersitepackages())
import fitz  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOL = 3.0  # y-tolerance (pt) for words on the same line
NUM = re.compile(r"^-?[\d,]+(\.\d+)?%?$|^-$|^–$")


def main():
    pdf, prange, toks, names, out = sys.argv[1:6]
    opts = sys.argv[6:]
    stop = None
    pim = None
    if "--stop" in opts:
        stop = re.compile(opts[opts.index("--stop") + 1], re.I)
    if "--parent-indent-max" in opts:
        pim = float(opts[opts.index("--parent-indent-max") + 1])
    toks = toks.split(",")
    names = names.split(",")
    a, b = (prange.split("-") + [prange])[:2]
    doc = fitz.open(pdf)
    rows = []
    parent = ""
    stopped = False
    global TOL
    if "--tol" in opts:
        TOL = float(opts[opts.index("--tol") + 1])
    carry = "--carry" in opts
    prev_anchors = None
    fixed = None
    if "--anchors" in opts:  # manual x-centres, comma separated; header tokens ignored
        fixed = [float(x) for x in opts[opts.index("--anchors") + 1].split(",")]
        carry = True
        prev_anchors = fixed
    for pn in range(int(a), int(b) + 1):
        if stopped:
            break
        lines = defaultdict(list)
        keys = []
        for w in sorted(doc[pn - 1].get_text("words"), key=lambda w: w[3]):
            k = next((k for k in keys if abs(k - w[3]) <= TOL), None)
            if k is None:
                k = w[3]
                keys.append(k)
            lines[k].append(w)
        anchors = prev_anchors if carry else None
        for y in sorted(lines):
            ws = sorted(lines[y], key=lambda w: w[0])
            txt = [w[4] for w in ws]
            line_txt = " ".join(txt)
            # header detection: tokens appear in order
            idx, pos = 0, []
            for w in ws:
                if idx < len(toks) and w[4] == toks[idx]:
                    pos.append((w[0] + w[2]) / 2)
                    idx += 1
            if idx == len(toks) and fixed is None:
                anchors = prev_anchors = pos
                continue
            if anchors is None:
                continue
            if carry and ws[0][1] < 70:  # running page header
                continue
            if stop and stop.search(line_txt):
                stopped = True
                break
            first_anchor = min(anchors) - 25
            label_ws = [w for w in ws if w[2] < first_anchor or not NUM.match(w[4])]
            val_ws = [w for w in ws if w not in label_ws]
            if not val_ws:
                continue
            label = " ".join(w[4] for w in label_ws)
            if not label:
                continue
            indent = round(label_ws[0][0]) if label_ws else None
            rec = {"page": pn, "parent": "", "label": label, "indent": indent}
            for n in names:
                rec[n] = ""
            for w in val_ws:
                xc = (w[0] + w[2]) / 2
                k = min(range(len(anchors)), key=lambda i: abs(anchors[i] - xc))
                v = w[4].replace(",", "")
                rec[names[k]] = "" if v in ("-", "–") else v
            if pim is not None and indent is not None and indent <= pim:
                parent = label
            rec["parent"] = parent
            rows.append(rec)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["page", "parent", "label", "indent"] + names)
        w.writeheader()
        w.writerows(rows)
    print("wrote", len(rows), "rows ->", out)


if __name__ == "__main__":
    main()
