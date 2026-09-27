# -*- coding: utf-8 -*-
"""Validacion estatica del sitio: referencias JS->HTML, delimitadores, cobertura de clave."""
import json, re, os, sys, io
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import ROOT  # noqa: E402
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJ = ROOT
html = open(os.path.join(PROJ, "index.html"), encoding="utf-8").read()
js = open(os.path.join(PROJ, "assets", "app.js"), encoding="utf-8").read()
css = open(os.path.join(PROJ, "assets", "style.css"), encoding="utf-8").read()
forms = json.load(open(os.path.join(PROJ, "data", "forms.json"), encoding="utf-8"))
clave = json.load(open(os.path.join(PROJ, "data", "clave.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(PROJ, "data", "meta.json"), encoding="utf-8"))

fallos = []

# --- 1) ids que el JS busca ---
ids_html = set(re.findall(r'\bid="([^"]+)"', html))
refs = set(re.findall(r'\$\("#([A-Za-z0-9_]+)"\)', js))
faltan = sorted(refs - ids_html)
print("ids en HTML:", len(ids_html), "| referenciados por JS:", len(refs))
if faltan:
    fallos.append("JS busca ids que no existen en el HTML: " + ", ".join(faltan))
else:
    print("  -> todas las referencias JS->HTML resuelven")

# --- 2) delimitadores ---
for nom, txt in (("app.js", js), ("style.css", css)):
    for a, b in (("{", "}"), ("(", ")"), ("[", "]")):
        if txt.count(a) != txt.count(b):
            fallos.append("%s desbalanceado: %s%s = %d vs %d" % (nom, a, b, txt.count(a), txt.count(b)))
    print("  %s delimitadores: %s" % (nom, "OK" if not any(f.startswith(nom) for f in fallos) else "REVISAR"))

# --- 3) html: etiquetas balanceadas (aprox) ---
for tag in ("section", "div", "main", "header", "footer", "button", "p", "label", "table"):
    ab = len(re.findall(r"<%s[\s>]" % tag, html))
    ce = len(re.findall(r"</%s>" % tag, html))
    if ab != ce:
        fallos.append("HTML <%s>: %d abren, %d cierran" % (tag, ab, ce))
print("  HTML etiquetas principales: %s" % ("OK" if not any("HTML <" in f for f in fallos) else "REVISAR"))

# --- 4) cobertura de la clave ---
if len(forms) != len(clave):
    fallos.append("forms=%d pero clave=%d" % (len(forms), len(clave)))
for f in forms:
    k = clave.get(str(f["id"]))
    if not k:
        fallos.append("sin clave para la Forma %d" % f["id"]); continue
    if len(k) != len(f["preguntas"]):
        fallos.append("Forma %d: clave con %d entradas, preguntas %d" % (f["id"], len(k), len(f["preguntas"])))
    for p in f["preguntas"]:
        c = k.get(str(p["pos"]))
        if c is None or not (0 <= c < len(p["opciones"])):
            fallos.append("Forma %d pos %d: clave invalida %r" % (f["id"], p["pos"], c))
        if len(p["opciones"]) != 5:
            fallos.append("Forma %d pos %d: %d opciones" % (f["id"], p["pos"], len(p["opciones"])))
print("  cobertura de clave: %s" % ("OK" if not any("clave" in f or "Forma" in f for f in fallos) else "REVISAR"))

# --- 5) ningun campo de respuesta filtrado al cliente ---
claves_p = set()
for f in forms:
    for p in f["preguntas"]:
        claves_p |= set(p.keys())
if claves_p & {"correcta", "correcto", "respuesta", "solucion", "answer"}:
    fallos.append("forms.json expone el campo de respuesta: " + ", ".join(sorted(claves_p & {"correcta", "correcto", "respuesta", "solucion", "answer"})))
else:
    print("  campos por pregunta:", sorted(claves_p))
    print("  forms.json NO expone respuestas: OK")

# --- 6) pos continuos 1..50 ---
for f in forms:
    ps = [p["pos"] for p in f["preguntas"]]
    if ps != list(range(1, 51)):
        fallos.append("Forma %d: posiciones no correlativas" % f["id"])
print("  posiciones 1..50 en las 20 formas: %s" % ("OK" if not any("posiciones" in x for x in fallos) else "REVISAR"))

# --- 7) archivos referenciados por el HTML existen ---
for src in re.findall(r'(?:src|href)="([^"]+)"', html):
    if src.startswith("http"): continue
    if not os.path.exists(os.path.join(PROJ, src.replace("/", os.sep))):
        fallos.append("el HTML apunta a un archivo inexistente: " + src)
print("  assets referenciados: %s" % ("OK" if not any("inexistente" in x for x in fallos) else "REVISAR"))

print()
if fallos:
    print("PROBLEMAS (%d):" % len(fallos))
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("TODO OK — Formas: %d | preguntas distintas: %d | topicos: %d"
      % (len(forms), meta["preguntasDistintas"], len(meta["topicos"])))
