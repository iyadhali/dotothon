"""Extract text from a folder of PDFs (PyMuPDF) and report lines mentioning dental terms.

Usage: python -I dental_grep_pdfs.py <PDF_DIR> <OUT_TXT> [<TEXT_CACHE_DIR>]
Writes one block per PDF: filename, page, line (with 1 line of context).
"""
import os
import re
import site
import sys

sys.path.append(site.getusersitepackages())
import pymupdf as fitz  # noqa: E402

PAT = re.compile(r"dent|oral health|orthodon|tooth|teeth|scaling|extraction|ދަތް", re.I)


def main():
    src, out = sys.argv[1], sys.argv[2]
    cache = sys.argv[3] if len(sys.argv) > 3 else None
    if cache:
        os.makedirs(cache, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for fn in sorted(os.listdir(src)):
            if not fn.lower().endswith(".pdf"):
                continue
            try:
                d = fitz.open(os.path.join(src, fn))
            except Exception as e:  # noqa: BLE001
                f.write(f"##### {fn} OPEN-FAIL {e}\n")
                continue
            hits, ntext = [], 0
            alltxt = []
            for i, p in enumerate(d):
                t = p.get_text()
                ntext += len(t.strip())
                alltxt.append(f"--- page {i+1}\n{t}")
                lines = t.splitlines()
                for j, ln in enumerate(lines):
                    if PAT.search(ln) and not re.search(r"accident|incident|independ|resident|student|dentif|precedent|evident|confident", ln, re.I):
                        ctx = " / ".join(x.strip() for x in lines[max(0, j - 1):j + 2])
                        hits.append(f"  p{i+1}: {ctx[:300]}")
            if cache:
                open(os.path.join(cache, fn[:-4] + ".txt"), "w", encoding="utf-8").write("\n".join(alltxt))
            f.write(f"##### {fn} pages={d.page_count} textchars={ntext} hits={len(hits)}\n")
            f.write("\n".join(hits[:80]) + ("\n" if hits else ""))
    print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
