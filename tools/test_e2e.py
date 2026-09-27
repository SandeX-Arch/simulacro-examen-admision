# -*- coding: utf-8 -*-
"""Prueba end-to-end del examen: recorre una Forma completa respondiendo bien todas
las preguntas y exige 50/50. Verifica tambien el desglose, el historial y el reinicio.

    python tools/test_e2e.py [url]      (por defecto http://127.0.0.1:8731/index.html)
"""
import json, sys, io, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _paths import DATA  # noqa: E402
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8731/index.html"
FORMA = 7

clave = json.load(open(DATA / "clave.json", encoding="utf-8"))[str(FORMA)]
forms = json.load(open(DATA / "forms.json", encoding="utf-8"))
pregs = [f for f in forms if f["id"] == FORMA][0]["preguntas"]

opt = Options()
for a in ("--headless=new", "--disable-gpu", "--no-sandbox", "--window-size=1280,900"):
    opt.add_argument(a)
drv = webdriver.Edge(options=opt)
fallos = []

try:
    drv.get(URL)
    time.sleep(1.5)

    # --- 1. selector de formas ---
    botones = drv.find_elements(By.CSS_SELECTOR, ".fbtn")
    print("formas en el selector:", len(botones))
    if len(botones) != 20:
        fallos.append("se esperaban 20 botones de forma")

    # --- 2. datos + comenzar ---
    botones[FORMA - 1].click()
    drv.find_element(By.ID, "inNombre").send_keys("Participante Prueba")
    btn = drv.find_element(By.ID, "btnComenzar")
    if btn.get_attribute("disabled"):
        fallos.append("el boton Comenzar sigue deshabilitado")
    btn.click()
    time.sleep(1.2)

    if not drv.find_element(By.ID, "viewExamen").is_displayed():
        fallos.append("no se muestra la vista de examen")
    print("vista examen visible:", drv.find_element(By.ID, "viewExamen").is_displayed())
    print("encabezado:", drv.find_element(By.ID, "exForma").text, "|",
          drv.find_element(By.ID, "qNum").text)

    # --- 3. las 50, respondiendo bien ---
    for p in pregs:
        pos = p["pos"]
        drv.find_elements(By.CSS_SELECTOR, ".pal")[pos - 1].click()
        num = drv.find_element(By.ID, "qNum").text.upper()
        if ("PREGUNTA %d " % pos) not in num:
            fallos.append("la paleta llevo a %s en vez de la %d" % (num, pos))
        opts = drv.find_elements(By.CSS_SELECTOR, "#qOpts .opt")
        if len(opts) != 5:
            fallos.append("pos %d: %d opciones" % (pos, len(opts)))
        opts[clave[str(pos)]].click()

    prog = drv.find_element(By.ID, "progTxt").text
    print("progreso final:", prog)
    if prog.strip() != "50 / 50":
        fallos.append("el progreso no llegó a 50/50: %r" % prog)

    # --- 4. entregar ---
    drv.find_element(By.ID, "btnEntregar").click()
    time.sleep(1.2)
    if not drv.find_element(By.ID, "viewResultado").is_displayed():
        fallos.append("no se muestra la vista de resultado")
    puntaje = drv.find_element(By.ID, "puntaje").text
    print("puntaje obtenido:", puntaje, "(esperado 50)")
    if puntaje.strip() != "50":
        fallos.append("puntaje %r, se esperaba 50" % puntaje)

    filas = drv.find_elements(By.CSS_SELECTOR, "#resTema .tema")
    print("desglose por tema:", len(filas), "filas")
    if not filas:
        fallos.append("el desglose por tema salio vacio")
    suma = sum(int(t.find_element(By.CSS_SELECTOR, ".tn").text.split("/")[0]) for t in filas)
    if suma != 50:
        fallos.append("las filas por tema suman %d, no 50" % suma)

    # --- 5. historial y limpieza ---
    hist = drv.execute_script("return JSON.parse(localStorage.getItem('simu_v1_historial')||'[]')")
    print("historial guardado:", json.dumps(hist, ensure_ascii=False)[:140])
    if not hist or hist[-1]["aciertos"] != 50:
        fallos.append("el historial no registro el intento")
    if drv.execute_script("return localStorage.getItem('simu_v1_progreso')"):
        fallos.append("el progreso quedo en localStorage tras entregar")

    # --- 6. volver al inicio y arrancar otra forma ---
    drv.find_element(By.ID, "btnOtra").click()
    time.sleep(0.8)
    if not drv.find_element(By.ID, "viewInicio").is_displayed():
        fallos.append("no se vuelve al inicio")
    drv.find_element(By.CSS_SELECTOR, ".fbtn").click()
    drv.find_element(By.ID, "inNombre").send_keys("X")
    drv.find_element(By.ID, "btnComenzar").click()
    time.sleep(1.0)
    if drv.find_element(By.ID, "exForma").text.strip() != "Examen 1":
        fallos.append("la segunda forma no arranco en el Examen 1")
finally:
    drv.quit()

print()
if fallos:
    print("FALLOS (%d):" % len(fallos))
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("E2E OK: 50/50, desglose correcto, historial y reinicio limpios.")
