# -*- coding: utf-8 -*-
"""Parser v2 - recupera opciones con marcadores danados por el OCR."""
import re, json, unicodedata, sys
from collections import Counter
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from _paths import BANK, FINAL_ANSWERS, OCR_CLEAN  # noqa: E402

OCR = OCR_CLEAN
KEY = FINAL_ANSWERS
OUT = BANK
BLOCKS = [
    ("Humanidades", "Psicologia",            1,  15),
    ("Humanidades", "Economia Politica",    16,  30),
    ("Humanidades", "Historia del Peru",    31,  50),
    ("Humanidades", "Historia Universal",   51,  65),
    ("Humanidades", "Filosofia",           66,  75),
    ("Humanidades", "Etica y Civica",       76,  90),
    ("Humanidades", "Geografia",            91, 100),
    ("Razonamiento Verbal", "Comprension Lectora", 101, 160),
    ("Razonamiento Verbal", "Sinonimos",           161, 180),
    ("Razonamiento Verbal", "Antonimos",           181, 200),
    ("Razonamiento Verbal", "Analogias",           201, 220),
    ("Razonamiento Verbal", "Terminos Excluidos",  221, 235),
    ("Razonamiento Verbal", "Etimologias",          236, 250),
    ("Razonamiento Verbal", "Plan de Redaccion",   251, 265),
    ("Razonamiento Verbal", "Morfologia y Sintaxis",266, 290),
    ("Razonamiento Verbal", "Conectores Logicos",  291, 300),
    ("Quimica", "Quimica",              801, 900),
    ("Biologia", "Biologia",            901, 1000),
]
def locate(n):
    for area, top, lo, hi in BLOCKS:
        if lo <= n <= hi:
            return area, top
    return None, None

WORD_STEM = {"Sinonimos": "syn", "Antonimos": "ant", "Terminos Excluidos": "excl"}
# Plan de Redaccion se EXCLUYE: el OCR destruye las etiquetas romanas (I/II indistinguibles
# entre "1", "Il", "ll", "1l") y las secuencias de las opciones ("I-II-III-IV" -> "1-1-1I-IV").
# No se puede reconstruir con confianza -> se descarta para no generar respuestas incorrectas.
DROP_TOPICS = {"Plan de Redaccion", "Analogias"}
BADCHARS = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]')
# senales de que el bloque se derramo sobre la pregunta siguiente
SPILL_OPT = re.compile(r'(?<![A-Za-z0-9])[eEdDcCbBaA]\s*(?:[iIl|]\s*)?[\)\.\uFF09]\s*(?=[A-Za-zÁ-Ž0-9])')
SPILL_NUM = re.compile(r'(?<![A-Za-z0-9])\d{1,4}\s*[\.\)]\s')
TRAIL = re.compile(r'[\s,;:\-\.\)\]]+$')

def descontaminar(t):
    """Corta el texto de opcion en el punto donde empieza otra pregunta."""
    cuts = []
    for rx in (SPILL_OPT, SPILL_NUM):
        m = rx.search(t)
        if m:
            cuts.append(m.start())
    if cuts:
        t = t[:min(cuts)]
    t = TRAIL.sub('', t)
    # "ayudo a los mas necesitados" colgado al final ->Recorta comas sueltas
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def fix_spaces(s):
    s = unicodedata.normalize('NFC', s)
    s = re.sub(r'(?<=[a-záéíóúñü])(?=[A-ZÁÉÍÓÚÑÜ])', ' ', s)
    s = re.sub(r'(?<=[a-zñ])(?=[áéíóúÁÉÍÓÚ])', ' ', s)
    s = re.sub(r'(?<=[áéíóúÁÉÍÓÚ])(?=[a-zñ])', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.replace(' ,', ',').replace(' .', '.').replace('( ', '(').replace(' )', ')')
    s = re.sub(r'\s*:\s*', ' : ', s)
    return s.strip()

def legible(t):
    """True si el texto tiene contenido usable (letras O digitos)."""
    core = BADCHARS.sub(' ', t)
    return bool(re.search(r'[A-Za-z0-9Á-žá-ž]', core))

# Marcador de opcion: letra a-e + ) o .   (incluye ) de ancho completo, basura "di)",
# y NEGATIVA para no anidarse cuando lo sigue es otro marcador ("a) a) ...").
MARK = (r'([eEdDcCbBaA])\s*(?:[iIl|]\s*)?[\)\.\uFF09\uFF0E]\s*'
        r'(?![eEdDcCbBaA]\s*(?:[iIl|]\s*)?[\)\.\uFF09\uFF0E])')

def find_markers(block):
    """Devuelve lista de (inicio, fin, letra) usando regex laxa dentro de ventanas plausibles."""
    cands = []
    for m in re.finditer(MARK, block):
        after = block[m.end():m.end() + 40]
        # el texto de la opcion suele empezar con letra, digito o signo
        if after and (after[0].isalnum() or after[0] in '"“(-–'):
            cands.append((m.start(), m.end(), m.group(1).lower()))
    return cands

def build(block):
    """Intenta extraer (stem, {letra:texto}, calidad)."""
    ms = find_markers(block)
    if len(ms) < 4:
        return None
    letters = [m[2] for m in ms]

    def slice_opts(idxs):
        stem = block[:ms[idxs[0]][0]].strip()
        opts, used = {}, []
        for j, i in enumerate(idxs):
            end = ms[idxs[j + 1]][0] if j + 1 < len(idxs) else len(block)
            txt = block[ms[i][1]:end].strip()
            opts[ms[i][2]] = (txt, i)
            used.append(ms[i][2])
        return stem, opts

    # A) 5 marcadores consecutivos -> permutation de a..e
    for i in range(len(ms) - 4):
        win = letters[i:i + 5]
        if len(set(win)) == 5 and set(win) == set('abcde'):
            stem, opts = slice_opts(list(range(i, i + 5)))
            return stem, {k: v[0] for k, v in opts.items()}, 'ok'

    # B) 5 marcadores, 4 letras distintas -> una repetida (OCR duplico la letra)
    if len(ms) >= 5 and len(set(letters)) == 4:
        counts = Counter(letters)
        dup = [l for l, c in counts.items() if c > 1]
        missing = [l for l in 'abcde' if l not in counts]
        if len(missing) == 1:
            miss = missing[0]
            i5 = None
            for i in range(len(ms) - 4):
                win = letters[i:i + 5]
                if win[0] == dup[0] and set(win) == set(letters):
                    i5 = i; break
            if i5 is None:
                for i in range(len(ms) - 4):
                    if set(letters[i:i + 5]) == set(letters):
                        i5 = i; break
            if i5 is not None:
                idxs = list(range(i5, i5 + 5))
                stem, opts = slice_opts(idxs)
                # el primer marcador es el duplicado -> really es la que falta
                new = {}
                for k, (txt, i) in opts.items():
                    if i == i5 and letters.count(dup[0]) > 1 and k == dup[0]:
                        new[miss] = txt
                    else:
                        new[k] = txt
                if len(new) == 5:
                    return stem, new, 'dup'

    # C) 4 marcadores con 4 letras distintas -> falta una; se recupera del hueco
    if len(ms) >= 4:
        for i in range(len(ms) - 3):
            win = letters[i:i + 4]
            if len(set(win)) == 4:
                missing = [l for l in 'abcde' if l not in win]
                if len(missing) != 1:
                    continue
                miss = missing[0]
                stem, opts = slice_opts(list(range(i, i + 4)))
                # el texto de la letra faltante quedo entre la opcion previa y la siguiente
                # (o antes del primer marcador / despues del ultimo)
                pos = [j for j, (t, _) in enumerate(opts.values())]
                # reconstruye: el hueco esta justo despues de la opcion que precede
                # en el orden alfabetico-impreso, usando posicion en el bloque
                first_i = i
                if first_i == 0:
                    lost = stem          # iba antes del primer marcador
                    stem = ''
                else:
                    prev = ms[first_i - 1]
                    nxt = ms[first_i + 4] if first_i + 4 < len(ms) else None
                    lost = block[prev[1]: nxt[0] if nxt else len(block)].strip()
                if lost:
                    opts[miss] = (lost, -1)
                    return stem, {k: v[0] for k, v in opts.items()}, 'miss'
    return None

key = {int(k): v for k, v in json.load(open(KEY, encoding="utf-8"))["answers"].items()}
lines = open(OCR, encoding="utf-8").read().split('\n')

# lineas que cortan el bloque: cierre de seccion, texto de lectura, clave, etc.
STOP = re.compile(
    r'^(RESPUESTAS\b|Oraciones\s*eliminadas|Oracioneseliminadas|'
    r'Texto\s*\d*|Lectura|'
    r'HUMANIDADES|RAZONAMIENTO\w*|ALGEBRA|ARITMETICA|GEOMETRIA|FiSICA|TRIGONOMETRIA|QUIMICA|BIOLOGIA|'
    r'Psicologia|Economia\w*|Historia\w*|Filosofia|Etica\w*|Geografia|'
    r'Comprension\w*|Sinonimos|Antonimos|Analogias|Terminos\w*|Etimologias|'
    r'Plan de\w*|Morfologia\w*|Conectores\w*|Quimica\w*|Biologia)$', re.I)

recs = []
for ln in lines:
    s = ln.strip()
    m = re.match(r'^===== PAGINA (\d+)', s)
    if m:
        continue
    if not s or re.fullmatch(r'[\u4e00-\u9fff]{1,3}', s) or s.lower() == 'l':
        continue
    if STOP.match(s):
        if recs:
            recs[-1][1].append('__STOP__')
        continue
    qm = re.match(r'^(\d{1,4})\s*[\.\)]\s*(.*)$', s)
    if qm:
        n = int(qm.group(1))
        if 1 <= n <= 1000 and locate(n)[0]:
            recs.append((n, [qm.group(2)]))
            continue
    if recs and len(recs[-1][1]) < 30:
        if s.isdigit():          # numero de pagina suelto
            recs[-1][1].append('__STOP__')
            continue
        recs[-1][1].append(s)

bank, rejects, quality = [], [], Counter()
seen = set()
for n, ls in recs:
    if n in seen:
        continue
    seen.add(n)
    if '__STOP__' in ls:
        ls = ls[:ls.index('__STOP__')]
    area, top = locate(n)
    if top in DROP_TOPICS:
        rejects.append((n, 'topico descartado por OCR no confiable', top)); continue
    block = ' '.join(ls)
    r = build(block)
    if not r:
        rejects.append((n, 'no parseable', block[:100])); continue
    stem, opts, q = r
    quality[q] += 1

    # 1) descontaminar cada opcion
    opts = {k: descontaminar(v) for k, v in opts.items()}
    stem = descontaminar(stem)

    # 1b) Conectores Logicos: las opciones son parejas "X - Y"; si hay frase de mas, se corta
    if top == "Conectores Logicos":
        def solo_par(v):
            m = re.match(r'^\s*(.+?)\s*-\s*(.+)$', v)
            if not m:
                return v
            der = ' '.join(m.group(2).split()[:2])
            return f"{m.group(1).strip()} - {der}".strip(' ,')
        opts = {k: solo_par(v) for k, v in opts.items()}

    # 1) stem autogenerado para temas de palabra suelta
    w = WORD_STEM.get(top)
    if w and len(stem) < 40 and re.fullmatch(r'[A-Za-zÁ-Žá-ž\.\- ]{2,40}', stem or ''):
        base = fix_spaces(stem).strip(' .')
        if not base:
            rejects.append((n, 'stem vacio', block[:80])); continue
        if w == 'syn':
            stem = f'¿Cuál es el SINÓNIMO de «{base}»?'
        elif w == 'ant':
            stem = f'¿Cuál es el ANTÓNIMO de «{base}»?'
        else:
            stem = f'¿Cuál de las siguientes alternativas NO es sinónimo de «{base}»?'
        q = 'auto'
    else:
        stem = fix_spaces(stem)

    opts = {k.upper(): fix_spaces(v) for k, v in opts.items()}
    if len(opts) != 5 or set(opts) != set('ABCDE'):
        rejects.append((n, 'no son 5 opciones', str(sorted(opts)))); continue
    if len(stem) < 8 or not re.search(r'[A-Za-zÁ-Žá-ž]{3}', stem):
        rejects.append((n, 'stem invalido', stem[:80])); continue
    ans = key.get(n)
    if not ans:
        rejects.append((n, 'sin clave', stem[:60])); continue
    bad = [k for k, v in opts.items() if not legible(v)]
    if ans in bad:
        rejects.append((n, 'la respuesta es ilegible', opts.get(ans, '')[:60])); continue
    # si la opcion correcta quedo contaminada o vacia -> no es confiable
    if not opts.get(ans, '').strip():
        rejects.append((n, 'opcion correcta vacia', stem[:60])); continue
    for k in bad:
        opts[k] = '[ilegible en el original]'
    if any(BADCHARS.search(v) for v in opts.values()):
        rejects.append((n, 'opciones con caracteres CJK', str(opts)[:90])); continue
    # ninguna opcion debe quedar con markers colgantes
    if any(SPILL_OPT.search(v) for v in opts.values()):
        rejects.append((n, 'opciones con marcadores colgantes', str(opts)[:90])); continue
    # varianza de longitud: si una opcion es 5x mas larga que otra, hay contaminacion
    lens = [len(v) for v in opts.values() if v]
    if lens and max(lens) > 6 * max(1, sorted(lens)[len(lens) // 2]):
        rejects.append((n, 'opciones desbalanceadas', str({k: len(v) for k, v in opts.items()}))); continue

    bank.append({"id": n, "area": area, "topico": top, "pregunta": stem,
                 "opciones": opts, "respuesta": ans, "q": q})

json.dump(bank, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"PARSEADAS {len(bank)} / 500   rechazadas {len(rejects)}")
print("calidad:", dict(quality))
print("\npor topico:")
tot = {}
for area, top, lo, hi in BLOCKS:
    tot[top] = hi - lo + 1
for top, c in Counter(b['topico'] for b in bank).most_common():
    print(f"  {top:<26} {c:>4} / {tot[top]}")
print("\nrechazos (motivo):", dict(Counter(r[1] for r in rejects)))
print("\nmuestra de rechazos:")
for r in rejects[:20]:
    print("  ", r[0], r[1], '|', r[2][:85])
print("->", OUT)

