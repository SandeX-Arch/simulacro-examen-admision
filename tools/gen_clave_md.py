# -*- coding: utf-8 -*-
"""Genera CLAVE_RESPUESTAS.md a partir de bank.json (el tema de cada pregunta ya
esta verificado, asi que no hay que duplicar el mapa de areas)."""
import json, sys, io, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _paths import BANK, FINAL_ANSWERS  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OUT = pathlib.Path(__file__).resolve().parent.parent.parent / "CLAVE_RESPUESTAS.md"

bank = json.load(open(BANK, encoding="utf-8"))
clave = json.load(open(FINAL_ANSWERS, encoding="utf-8"))
A = {int(k): v for k, v in clave["answers"].items()}
U = {int(k): v for k, v in clave["unresolved"].items()}

by_t = collections.OrderedDict()
for b in sorted(bank, key=lambda x: x["id"]):
    by_t.setdefault(b["topico"], []).append(b)

L = []
L.append("# Clave de Respuestas")
L.append("")
L.append("Extraida de la tabla RESPUESTAS del valotario original (73 paginas escaneadas, OCR).\n")
L.append("## Resumen\n")
L.append("| Dato | Valor |")
L.append("|---|---|")
L.append("| Preguntas en el valotario | 1000 |")
L.append("| Clave recuperada | %d |" % len(A))
L.append("| Sin alternativa (son \"Resolver\") | %d (P%s) |"
         % (len(U), ", P".join(str(k) for k in sorted(U))))
L.append("| Preguntas usadas en el simulacro | %d |" % len(bank))
L.append("| Temas | %d |" % len(by_t))
L.append("")
L.append("> **Aviso:** la clave impresa en el libro parece tener errores. Se detectaron al menos")
L.append("> tres al cotejar con las preguntas: **P42** (marca A, esperable D), **P67** (marca D,")
L.append("> esperable A) y **P80** (marca A, esperable C). Contrasta con el original.\n")
L.append("> El OCR perdio acentos y tildes en casi todo el texto, y se descartaron 92 preguntas")
L.append("> ilegibles o sin alternativa. Ver `README.md` para el detalle.\n")
L.append("---\n")
L.append("## Clave por tema\n")
for t, items in by_t.items():
    L.append("### %s  (P%d-P%d, %d preguntas)\n" % (t, items[0]["id"], items[-1]["id"], len(items)))
    L.append("| P | R | P | R | P | R | P | R | P | R |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    fila = []
    for b in items:
        fila.append("%d | %s" % (b["id"], b["respuesta"]))
        if len(fila) == 10:
            L.append("| " + " | ".join(fila) + " |")
            fila = []
    if fila:
        while len(fila) < 10:
            fila.append(" | ")
        L.append("| " + " | ".join(fila) + " |")
    L.append("")

L.append("---\n")
L.append("## Preguntas del valotario sin alternativa\n")
L.append("En el original no son de opcion multiple, por eso no entran al simulacro:\n")
L.append("| P | Texto en el original |")
L.append("|---|---|")
for k in sorted(U):
    L.append("| %d | %s |" % (k, U[k].get("near") or U[k].get("reocr") or "?"))
L.append("")

L.append("---\n")
L.append("## Abreviaturas\n")
L.append("P = numero de pregunta en el valotario · R = alternativa correcta (A-E)\n")

OUT.write_text("\n".join(L), encoding="utf-8")
print("CLAVE_RESPUESTAS.md actualizado: %d preguntas, %d temas, %d sin alternativa"
      % (len(bank), len(by_t), len(U)))
print("  ->", OUT)
print("  entradas con letra vacia:", sum(1 for v in A.values() if not str(v).strip()))
