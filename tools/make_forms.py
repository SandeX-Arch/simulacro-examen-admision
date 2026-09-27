# -*- coding: utf-8 -*-
"""Genera 20 Formas de 50 preguntas a partir de bank.json.
Garantias:
  - ningun qid se repite dentro de una misma Forma
  - cada pregunta aparece 2 o 3 veces (1000 slots / 408 preguntas)
  - los temas quedan repartidos, no agrupados
  - el orden de opciones se baraja por aparicion y se recalcula la letra correcta
"""
import json, random, sys, io, collections
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import BANK, FORMS  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BANK = BANK
OUT = FORMS
NFORMAS = 20
POR_FORMA = 50
SHUFFLE_OPCIONES = True
SEED = 20260926

bank = json.load(open(BANK, encoding="utf-8"))
byid = {b["id"]: b for b in bank}
ids = sorted(byid)
n = len(ids)
total = NFORMAS * POR_FORMA
base, extra = divmod(total, n)          # 2, 184
uso = {q: base for q in ids}

# el reparto de la "tercera vuelta" se hace round-robin entre temas, para que
# ningun tema quede penalizado
por_topico = collections.defaultdict(list)
for q in ids:
    por_topico[byid[q]["topico"]].append(q)
orden_topicos = sorted(por_topico, key=lambda t: -len(por_topico[t]))
ronda, i = 0, 0
while extra > 0:
    t = orden_topicos[ronda % len(orden_topicos)]
    cand = [q for q in por_topico[t] if uso[q] == base]
    if cand:
        uso[cand[i % len(cand)]] += 1
        extra -= 1
        i += 1
    ronda += 1
    if ronda > 500000:
        raise SystemExit("no se pudo repartir")

# asignar cada aparicion a formas distintas, con strides coprimos
formas = [[] for _ in range(NFORMAS)]
for idx, q in enumerate(ids):
    k = uso[q]
    start = (idx * 7) % NFORMAS
    picked = []
    for j in range(k):
        f = (start + j * 6) % NFORMAS
        while f in picked:
            f = (f + 1) % NFORMAS
        picked.append(f)
    for f in picked:
        formas[f].append(q)

# reajustar a exactamente 50 por forma
def reequilibrar():
    for _ in range(100000):
        grande = max(range(NFORMAS), key=lambda f: len(formas[f]))
        if len(formas[grande]) <= POR_FORMA:
            return
        for f in range(NFORMAS):
            if len(formas[f]) >= POR_FORMA:
                continue
            for pos in range(len(formas[grande]) - 1, -1, -1):
                q = formas[grande][pos]
                if q not in formas[f]:
                    formas[grande].pop(pos)
                    formas[f].append(q)
                    break
            else:
                continue
            break
        else:
            raise SystemExit("atasco en el reparto")
reequilibrar()

rng = random.Random(SEED)
salida = []
for f, qids in enumerate(formas, start=1):
    assert len(qids) == POR_FORMA, (f, len(qids))
    assert len(set(qids)) == POR_FORMA, ("repetida dentro de la forma", f)
    # intercalar temas: orden por "capa" para que no haya rafagas del mismo tema
    por_t = collections.defaultdict(list)
    for q in qids:
        por_t[byid[q]["topico"]].append(q)
    for v in por_t.values():
        rng.shuffle(v)
    orden, pendientes = [], collections.Counter({t: 0 for t in por_t})
    while len(orden) < POR_FORMA:
        cand = [t for t in por_t if pendientes[t] < len(por_t[t])]
        t = min(cand, key=lambda t: (pendientes[t], rng.random()))
        orden.append(por_t[t][pendientes[t]])
        pendientes[t] += 1

    preguntas = []
    for pos, q in enumerate(orden):
        b = byid[q]
        letras = list("ABCDE")
        ops = [b["opciones"][k] for k in letras]
        corr = letras.index(b["respuesta"])
        if SHUFFLE_OPCIONES:
            p = rng.randrange(5)
            ops = ops[p:] + ops[:p]
            corr = (corr - p) % 5
        preguntas.append({
            "pos": pos + 1,
            "id": q,
            "topico": b["topico"],
            "pregunta": b["pregunta"],
            "opciones": ops,
            "correcta": corr,
        })
    salida.append({
        "id": f,
        "nombre": "Forma %d" % f,
        "preguntas": preguntas,
    })

# ---- verificaciones ----
cuenta = collections.Counter(p["id"] for f in salida for p in f["preguntas"])
assert len(cuenta) == n, "se perdieron preguntas"
print("Formas:", len(salida), "| preguntas por forma:", POR_FORMA)
print("slots:", sum(len(f["preguntas"]) for f in salida))
print("preguntas distintas:", len(cuenta))
print("apariciones por pregunta: min=%d max=%d" % (min(cuenta.values()), max(cuenta.values())))
print("distribucion:", dict(collections.Counter(cuenta.values())))
print("repetidas dentro de una forma: 0 (verificado)")
print("\ntemas por forma (min-max):")
for t in orden_topicos:
    xs = [sum(1 for p in f["preguntas"] if p["topico"] == t) for f in salida]
    print("  %-26s %2d-%2d  (total %d)" % (t, min(xs), max(xs), sum(xs)))

json.dump(salida, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n->", OUT)
