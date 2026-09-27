# -*- coding: utf-8 -*-
import pymupdf, json, os, re, sys, io
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import BUILD, DOCS  # noqa: E402
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
DST = DOCS
TMP = BUILD
fallos = []

# --- 1. el banco: las 408 preguntas y sus 5 opciones deben ser extraibles ---
d = pymupdf.open(os.path.join(DST, "01-Banco-de-Preguntas.pdf"))
full = "\n".join(p.get_text() for p in d)
print("01 banco: %d paginas, %d caracteres extraibles" % (d.page_count, len(full)))
bank = json.load(open(os.path.join(TMP, "bank.json"), encoding="utf-8"))
ids_ok = 0
for b in bank:
    if re.search(r"(?m)^%d\.\s" % b["id"], full):
        ids_ok += 1
print("  preguntas localizables en el PDF: %d/%d" % (ids_ok, len(bank)))
if ids_ok != len(bank):
    faltan = [b["id"] for b in bank if not re.search(r"(?m)^%d\.\s" % b["id"], full)]
    fallos.append("faltan preguntas en el PDF: %s" % faltan[:20])
marcadores = len(re.findall(r"(?m)^[A-E]\)\s", full))
print("  opciones A-E halladas: %d (esperado %d)" % (marcadores, len(bank) * 5))
if marcadores != len(bank) * 5:
    fallos.append("opciones incompletas: %d de %d" % (marcadores, len(bank) * 5))
d.close()

# --- 2. clave general ---
d = pymupdf.open(os.path.join(DST, "02-Clave-General.pdf"))
t = "\n".join(p.get_text() for p in d)
clave = json.load(open(os.path.join(TMP, "final_answers.json"), encoding="utf-8"))["answers"]
mal = 0
for b in bank:
    exp = "%d.%s" % (b["id"], b["respuesta"])
    if exp not in t.replace(" ", "") and exp not in t:
        mal += 1
print("02 clave general: %d paginas | entradas no encontradas: %d" % (d.page_count, mal))
if mal > 0:
    fallos.append("clave general con %d entradas ausentes" % mal)
if "P42" not in t and "42.A" not in t.replace(" ", ""):
    print("  (aviso: no se ve la entrada 42)")
d.close()

# --- 3. clave por forma: 1000 entradas ---
d = pymupdf.open(os.path.join(DST, "03-Clave-por-Forma.pdf"))
t3 = "".join(p.get_text() for p in d)
forms = json.load(open(os.path.join(TMP, "forms.json"), encoding="utf-8"))
flat = re.sub(r"\s+", "", t3)
n = sum(1 for f in forms for q in f["preguntas"] if ("%d.%s" % (q["pos"], "ABCDE"[q["correcta"]])) in flat)
print("03 clave por forma: %d paginas | entradas halladas: %d/1000" % (d.page_count, n))
if n != 1000:
    fallos.append("clave por forma con %d/1000 entradas" % n)
print("  formas nombradas: %d/20" % len(re.findall(r"Forma \d+", t3)))
d.close()

# --- 4. que no haya texto fuera del area util (desbordes) ---
for f in sorted(os.listdir(DST)):
    if not f.endswith(".pdf"):
        continue
    doc = pymupdf.open(os.path.join(DST, f))
    fuera = 0
    for p in doc:
        for b in p.get_text("blocks"):
            x0, y0, x1, y1 = b[:4]
            if x0 < 40 or x1 > 560 or y0 < 20 or y1 > 830:
                fuera += 1
    print("%-30s bloques fuera de margen: %d" % (f, fuera))
    if fuera > 0:
        fallos.append("%s: %d bloques fuera del area util" % (f, fuera))
    doc.close()

print()
if fallos:
    print("PROBLEMAS:")
    for x in fallos:
        print("  -", x)
    sys.exit(1)
print("PDFs OK: texto extraible, completo y dentro de margins.")
