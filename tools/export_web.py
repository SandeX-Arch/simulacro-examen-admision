# -*- coding: utf-8 -*-
"""Exporta el proyecto web: separa preguntas (forms.json) de la clave (clave.json)
para que el navegador no descargue las respuestas junto con el examen."""
import json, os, sys, io, collections
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import BUILD, ROOT  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
TMP = BUILD
PROJ = ROOT
forms = json.load(open(os.path.join(TMP, "forms.json"), encoding="utf-8"))
bank = {b["id"]: b for b in json.load(open(os.path.join(TMP, "bank.json"), encoding="utf-8"))}

publico, clave = [], {}
for f in forms:
    ps = []
    for p in f["preguntas"]:
        ps.append({
            "pos": p["pos"],
            "id": p["id"],
            "topico": p["topico"],
            "pregunta": p["pregunta"],
            "opciones": p["opciones"],
        })
    publico.append({"id": f["id"], "nombre": f["nombre"], "preguntas": ps})
    clave[str(f["id"])] = {str(p["pos"]): p["correcta"] for p in f["preguntas"]}

topicos = collections.Counter(b["topico"] for b in bank.values())
meta = {
    "titulo": "Simulacro de Examen de Admision",
    "fuente": "Valotario de preguntas - 1000 preguntas",
    "formas": len(forms),
    "porForma": 50,
    "preguntasDistintas": len(bank),
    "topicos": [{"nombre": t, "n": n} for t, n in sorted(topicos.items())],
    "excluidas": [
        "Analogias (201-220): tabla de 3 columnas mal leida por el OCR",
        "Plan de Redaccion (251-265): etiquetas romanas I/II indistinguibles",
        "Quimica 856-858: son 'Resolver', no tienen alternativa",
    ],
}

os.makedirs(os.path.join(PROJ, "data"), exist_ok=True)
for name, obj in (("forms.json", publico), ("clave.json", clave), ("meta.json", meta)):
    p = os.path.join(PROJ, "data", name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
    print("%-12s %8.1f KB" % (name, os.path.getsize(p) / 1024))

print("\nFormas:", len(publico), "| slots:", sum(len(f['preguntas']) for f in publico))
print("Clave: %d formas" % len(clave))
print("ninguna 'correcta' en forms.json:",
      not any("correcta" in p for f in publico for p in f["preguntas"]))
