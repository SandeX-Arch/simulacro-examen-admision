# -*- coding: utf-8 -*-
"""Genera PDFs de TEXTO real (buscables, no imagenes) del simulacro."""
import json, os, re, sys, io
import pymupdf
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import BUILD, DOCS  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TMP = BUILD
DST = DOCS
# Fuentes base-14 (WinAnsiEncoding): el texto extraido es identico al escrito, cosa que
# NO ocurre con una TTF embebida (los parentesis y guiones se extraen como glifos PUA
# y rompen el buscar/copiar en el PDF).
FONT, FONTB = "helv", "hebo"
os.makedirs(DST, exist_ok=True)

W, H = 595.0, 842.0
ML, MR, MT, MB = 48.0, 48.0, 56.0, 46.0
TW = W - ML - MR

TRANS = {"\u2192": "->", "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
         "\u201c": '"', "\u201d": '"', "\u00a0": " ", "\u2026": "...",
         "\u2265": ">=", "\u2264": "<=", "\u00b7": "-", "\u2212": "-", "\u2260": "!=",
         "\u2190": "<-", "\u03b1": "alpha", "\u03b2": "beta", "\u2011": "-"}
FU = pymupdf.Font("helv")


def sane(s):
    s = "" if s is None else str(s)
    for a, b in TRANS.items():
        s = s.replace(a, b)
    s = "".join(c if ord(c) < 256 else "?" for c in s)
    return re.sub(r"\s+", " ", s).strip()


def wrap(txt, size, ancho):
    out, cur = [], ""
    for w in txt.split(" "):
        t = (cur + " " + w).strip()
        if FU.text_length(t, fontsize=size) <= ancho or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out or [""]


class Doc:
    def __init__(self, titulo):
        self.d = pymupdf.open()
        self.titulo = sane(titulo)
        self.y = MT
        self.paginas = 0
        self._page()

    def _page(self):
        self.paginas += 1
        p = self.d.new_page(width=W, height=H)
        if self.paginas > 1:
            p.insert_text((ML, 30), self.titulo, fontname=FONTB,
                          fontsize=8, color=(0.56, 0.55, 0.52))
            p.insert_text((W - MR - 40, 30), str(self.paginas), fontname=FONT,
                          fontsize=8, color=(0.56, 0.55, 0.52))
            p.draw_line(pymupdf.Point(ML, 36), pymupdf.Point(W - MR, 36),
                        color=(0.90, 0.89, 0.86), width=0.6)
        self.y = MT
        return p

    def espacio(self, h=6):
        if self.y + h > H - MB:
            self._page()
        self.y += h

    def texto(self, txt, size=9.5, bold=False, color=(0.23, 0.23, 0.22),
              x=ML, ancho=None, gap=3.0, leading=None):
        txt = sane(txt)
        if not txt:
            return
        ancho = ancho or (W - MR - x)
        leading = leading or size * 1.45
        lines = wrap(txt, size, ancho)
        nm = FONTB if bold else FONT
        for ln in lines:
            if self.y + leading > H - MB:
                self._page()
            self.d[-1].insert_text((x, self.y), ln, fontname=nm,
                                   fontsize=size, color=color)
            self.y += leading
        self.y += gap

    def regla(self, color=(0.90, 0.89, 0.86)):
        self.d[-1].draw_line(pymupdf.Point(ML, self.y - 2), pymupdf.Point(W - MR, self.y - 2),
                             color=color, width=0.6)
        self.y += 8

    def guardar(self, ruta):
        self.d.set_metadata({"title": self.titulo, "author": "Simulacro de Admision",
                             "subject": "Banco de preguntas y claves", "keywords": "simulacro, admision"})
        try:
            self.d.subset_fonts()          # recorta la fuente embebida -> archivos mucho mas chicos
        except Exception as e:
            print("  (subset_fonts no disponible: %s)" % e)
        self.d.save(ruta, garbage=4, deflate=True, clean=True)
        n = self.d.page_count
        self.d.close()
        kb = os.path.getsize(ruta) / 1024
        print("%-30s %3d paginas  %7.1f KB" % (os.path.basename(ruta), n, kb))


AZUL = (0.24, 0.33, 0.39)
GRIS = (0.45, 0.44, 0.41)
ROJO = (0.55, 0.40, 0.34)

# ------------------------------------------------------------------ 1. banco
bank = json.load(open(os.path.join(TMP, "bank.json"), encoding="utf-8"))
by_t = {}
for b in bank:
    by_t.setdefault(b["topico"], []).append(b)
orden = sorted(by_t, key=lambda t: by_t[t][0]["id"])

d = Doc("Simulacro de Admision - Banco de Preguntas")
d.texto("Banco de Preguntas", 20, True, AZUL, gap=6)
d.texto("%d preguntas en %d temas, ordenadas por el numero original del valotario."
        % (len(bank), len(orden)), 9.5, color=GRIS)
d.texto("PDF de texto real: se puede buscar, seleccionar y copiar. Las respuestas correctas "
        "estan en el PDF de claves.", 9, color=GRIS)
d.regla()
for t in orden:
    it = by_t[t]
    d.espacio(8)
    d.texto("%s   P%d-P%d  (%d)" % (t, it[0]["id"], it[-1]["id"], len(it)), 12.5, True, AZUL, gap=5)
    for b in it:
        d.texto("%d.  %s" % (b["id"], b["pregunta"]), 9.5, gap=2.5)
        for k in "ABCDE":
            d.texto("%s)  %s" % (k, b["opciones"][k]), 9, color=(0.28, 0.28, 0.26),
                    x=ML + 13, ancho=TW - 13, gap=0.6, leading=12.6)
        d.espacio(4)
d.guardar(os.path.join(DST, "01-Banco-de-Preguntas.pdf"))

# ------------------------------------------------------------------ 2. clave general
d = Doc("Simulacro de Admision - Clave General")
d.texto("Clave General de Respuestas", 20, True, AZUL, gap=6)
d.texto("%d preguntas con su alternativa correcta, segun la tabla RESPUESTAS del valotario."
        % len(bank), 9.5, color=GRIS)
d.texto("Atencion: la clave impresa en el original parece tener errores en algunas preguntas "
        "(p. ej. P42, P67, P80). Contrastala antes de tomarla como fuente oficial.",
        9, color=ROJO)
d.regla()
for t in orden:
    it = by_t[t]
    d.espacio(8)
    d.texto(t, 12, True, AZUL, gap=5)
    linea = []
    for b in it:
        linea.append("%d.%s" % (b["id"], b["respuesta"]))
        if len(linea) == 10:
            d.texto("     ".join(linea), 9.5, gap=2.5)
            linea = []
    if linea:
        d.texto("     ".join(linea), 9.5, gap=2.5)
d.guardar(os.path.join(DST, "02-Clave-General.pdf"))

# ------------------------------------------------------------------ 3. clave por forma
forms = json.load(open(os.path.join(TMP, "forms.json"), encoding="utf-8"))
d = Doc("Simulacro de Admision - Clave por Forma")
d.texto("Clave por Forma", 20, True, AZUL, gap=6)
d.texto("20 formas x 50 preguntas = 1000 apariciones. Ninguna pregunta se repite dentro de una "
        "misma forma.", 9.5, color=GRIS)
d.texto("El orden de las opciones se baraja en cada aparicion, por lo que la letra cambia entre "
        "formas aunque el contenido sea el mismo.", 9, color=GRIS)
d.regla()
for f in forms:
    d.texto(f["nombre"], 12.5, True, AZUL, gap=5)
    for ini in range(0, 50, 25):
        trozo = f["preguntas"][ini:ini + 25]
        d.texto("     ".join("%d.%s" % (q["pos"], "ABCDE"[q["correcta"]]) for q in trozo),
                9, gap=2.5)
    d.espacio(7)
d.guardar(os.path.join(DST, "03-Clave-por-Forma.pdf"))
