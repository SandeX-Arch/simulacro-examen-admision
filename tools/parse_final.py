import os, re, json, statistics
import numpy as np, cv2, pymupdf
from rapidocr_onnxruntime import RapidOCR
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import FINAL_ANSWERS, VALOTARIO_PDF  # noqa: E402

SRC = KEYPAGES
PDF = VALOTARIO_PDF
OUTJSON = FINAL_ANSWERS
SC = 200 / 72.0
FIRST = {5: 1, 19: 101, 33: 301, 38: 501, 42: 561,
         48: 621, 55: 681, 61: 741, 67: 801, 73: 901}

rows_by_page = {}
cur = None
for line in open(SRC, encoding="utf-8"):
    line = line.rstrip("\n")
    m = re.match(r"########## PAGINA (\d+) ##########", line)
    if m:
        cur = int(m.group(1)); rows_by_page[cur] = []; continue
    if cur is None:
        continue
    ym = re.match(r"y=\s*([\d.]+)\s*\|(.*)", line)
    if not ym:
        continue
    y = float(ym.group(1))
    cells = []
    for part in ym.group(2).split("||"):
        mm = re.match(r"\s*x=\s*([\d.]+):(.*)", part)
        if mm:
            cells.append((float(mm.group(1)), mm.group(2).strip()))
    ints = [x for x, t in cells if re.fullmatch(r"\d{1,4}", t)]
    if len(ints) >= 3:
        rows_by_page[cur].append((y, cells, ints))

doc = pymupdf.open(PDF)
ocr = RapidOCR()
_cc = {}

def reocr(page, x, y):
    k = (page, round(x / 5), round(y / 5))
    if k in _cc:
        return _cc[k]
    clip = pymupdf.Rect((x - 50) / SC, (y - 30) / SC, (x + 50) / SC, (y + 30) / SC)
    pix = doc[page - 1].get_pixmap(dpi=600, clip=clip)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.copyMakeBorder(img, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=(255,) * 3)
    r, _ = ocr(img)
    t = " ".join(s for _, s, _ in r) if r else ""
    _cc[k] = t.strip()
    return _cc[k]

def norm(t):
    t = t.strip().strip("'\".,()[]:;-")
    t = re.sub(r"^[^a-zA-Z]+", "", t)
    return t[:1].lower()

LETTERS = set("abcde")   # conjunto, no cadena: "" in "abcde" es True (bug)
answers, unresolved = {}, {}
for page, first in FIRST.items():
    rows = sorted(rows_by_page[page], key=lambda r: r[0])
    # split into contiguous runs (gap > 120px), keep the largest = the key table
    runs, cur_run = [], [rows[0]]
    for r in rows[1:]:
        if r[0] - cur_run[-1][0] > 120:
            runs.append(cur_run); cur_run = [r]
        else:
            cur_run.append(r)
    runs.append(cur_run)
    run = max(runs, key=len)
    nrows = len(run)
    ncol = int(statistics.mode(len(r[2]) for r in run))
    numxs = sorted(x for r in run for x, t in r[1] if re.fullmatch(r"\d{1,4}", t))
    # cluster number x positions (tolerance 120px)
    clusters = []
    for x in numxs:
        if clusters and x - clusters[-1][-1] < 120:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    cen = [statistics.mean(c) for c in clusters]
    if len(cen) > ncol:
        # keep the ncol clusters that best fit an arithmetic progression
        diffs = [b - a for a, b in zip(cen, cen[1:]) if b - a > 0]
        step = statistics.median(diffs) if diffs else 200.0
        best, bestscore = None, -1
        for s in range(len(cen)):
            for k in range(ncol):
                grp = []
                for j in range(ncol):
                    target = cen[s] + j * step
                    cand = min(cen, key=lambda c: abs(c - target))
                    if cand not in grp:
                        grp.append(cand)
                score = sum(1 for g in grp if min(abs(g - (cen[s] + j * step))
                                                 for j in range(ncol)) < 60)
                if len(grp) == ncol and score > bestscore:
                    bestscore, best = score, grp
        cen = sorted(best) if best else cen[:ncol]
    colx = cen[:ncol]
    print(f"page {page}: rows={nrows} cols={len(colx)} total={nrows*len(colx)}")
    for ci, nx in enumerate(colx):
        base = first + ci * nrows
        for ri, (y, cells, ints) in enumerate(run):
            qn = base + ri
            lo = nx
            hi = colx[ci + 1] if ci + 1 < len(colx) else 1e9
            cand = [(x, t) for x, t in cells if lo < x < hi and not re.fullmatch(r"\d{1,4}", t)]
            letter = norm(cand[0][1]) if cand else ""
            if letter not in LETTERS:
                letter = norm(reocr(page, nx + 126, y))
            if letter in LETTERS:
                answers[qn] = letter.upper()
            else:
                unresolved[qn] = {"page": page, "x": round(nx), "y": round(y),
                                  "near": cand[0][1] if cand else None,
                                  "reocr": reocr(page, nx + 126, y)}

json.dump({"answers": answers, "unresolved": unresolved},
          open(OUTJSON, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("\nRESUELTAS:", len(answers), "/1000")
print("SIN RESOLVER:", sorted(unresolved))
for k in sorted(unresolved):
    print("  ", k, unresolved[k])
