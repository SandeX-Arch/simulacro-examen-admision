# -*- coding: utf-8 -*-
"""Verificacion independiente: en cada aparicion, la opcion marcada como correcta
debe ser EXACTAMENTE el texto que el banco define como correcto."""
import json, sys, io, collections, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _paths import BUILD, FORMS  # noqa: E402
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

bank = {b["id"]: b for b in json.load(open(BUILD / "bank.json", encoding="utf-8"))}
forms = json.load(open(FORMS, encoding="utf-8"))

errores, total, por_letra = [], 0, collections.Counter()
vacias = 0
for f in forms:
    for p in f["preguntas"]:
        total += 1
        b = bank[p["id"]]
        correcto = b["opciones"][b["respuesta"]]
        elegido = p["opciones"][p["correcta"]]
        if correcto != elegido:
            errores.append((f["id"], p["pos"], p["id"], correcto, elegido))
        por_letra[chr(65 + p["correcta"])] += 1
        for o in p["opciones"]:
            if not o.strip() or o.strip().lower() in ("n.a.", "-", "ilegible en el original"):
                vacias += 1
        # el conjunto de opciones debe ser el mismo, solo reordenado
        if sorted(p["opciones"]) != sorted(b["opciones"].values()):
            errores.append((f["id"], p["pos"], p["id"], "conjunto de opciones distinto", ""))

print("apariciones verificadas:", total)
print("respuestas correctas coinciden con el banco:", total - len(errores), "/", total)
print("opciones vacias/degeneradas:", vacias)
print("reparticion de la letra correcta:", dict(sorted(por_letra.items())))
if errores:
    print("\nERRORES (%d):" % len(errores))
    for e in errores[:15]:
        print("  ", e)
else:
    print("\nOK: ninguna discrepancia.")

# ninguna pregunta puede repetirse dentro de una misma Forma
dup = [(f["id"], q) for f in forms for q, c in collections.Counter(p["id"] for p in f["preguntas"]).items() if c > 1]
print("duplicados dentro de una Forma:", dup if dup else "ninguno")
