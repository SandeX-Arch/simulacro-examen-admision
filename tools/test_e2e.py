# -*- coding: utf-8 -*-
"""Prueba end-to-end con Selenium: recorre una Forma completa respondiendo bien
todas las preguntas y exige 50/50. Verifica tambien el guardado en localStorage."""
import json, sys, io, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
URL = "http://127.0.0.1:8731/index.html"
DATA = r"C:\Users\musky\OneDrive\Documentos\SIMULACROS\examen-admision\data"
FORMA = 7

clave = json.load(open(DATA + r"\clave.json", encoding="utf-8"))[str(FORMA)]
forms = json.load(open(DATA + r"\forms.json", encoding="utf-8"))
pregs = [f for f in forms if f["id"] == FORMA][0]["preguntas"]

opt = Options()
opt.add_argument("--headless=new")
opt.add_argument("--disable-gpu")
opt.add_argument("--no-sandbox")
opt.add_argument("--window-size=1280,900")
drv = webdriver.Edge(options=opt)
fallos = []

try:
    drv.get(URL)
    time.sleep(1.2)

    # --- 1. selector de formas ---
    botones = drv.find_elements(By.CSS_SELECTOR, ".fbtn")
    print("formas en el selector:", len(botones))
    if len(botones) != 20:
        fallos.append("se esperaban 20 botones de forma")

    # --- 2. datos + commencing ---
    botones[FORMA - 1].click()
    drv.find_element(By.ID, "inNombre").send_keys("Participante Prueba")
    drv.find_element(By.ID, "inDoc").send_keys("12345678")
    btn = drv.find_element(By.ID, "btnComenzar")
    if btn.get_attribute("disabled"):
        fallos.append("el boton Comenzar sigue deshabilitado")
    btn.click()
    time.sleep(1.0)

    if not drv.find_element(By.ID, "viewExamen").is_displayed():
        fallos.append("no se muestra la vista de examen")
    print("vista examen visible:", drv.find_element(By.ID, "viewExamen").is_displayed())
    print("encabezado:", drv.find_element(By.ID, "exForma").text, "|",
          drv.find_element(By.ID, "qNum").text)

    # --- 3. responder las 50 correctamente ---
    for p in pregs:
        pos = p["pos"]
        # navegar por la paleta hasta la posicion correcta
        pal = drv.find_elements(By.CSS_SELECTOR, ".pal")
        pal[pos - 1].click()
        time.sleep(0.02)
        num = drv.find_element(By.ID, "qNum").text.upper()
        if ("PREGUNTA %d " % pos) not in num:
            fallos.append("la paleta llevo a %s en vez de la %d" % (num, pos))
        opts = drv.find_elements(By.CSS_SELECTOR, "#qOpts .opt")
        if len(opts) != 5:
            fallos.append("pos %d: %d opciones" % (pos, len(opts)))
        opts[clave[str(pos)]].click()
        time.sleep(0.02)

    prog = drv.find_element(By.ID, "progTxt").text
    print("progreso final:", prog)
    if prog.strip() != "50 / 50":
        fallos.append("el progreso no llegó a 50/50: %r" % prog)

    # --- 4. entregar ---
    drv.find_element(By.ID, "btnEntregar").click()
    time.sleep(1.0)
    if not drv.find_element(By.ID, "viewResultado").is_displayed():
        fallos.append("no se muestra la vista de resultado")
    puntaje = drv.find_element(By.ID, "puntaje").text
    print("puntaje obtenido:", puntaje, "(esperado 50)")
    if puntaje.strip() != "50":
        fallos.append("puntaje %r, se esperaba 50" % puntaje)

    barras = drv.find_elements(By.CSS_SELECTOR, "#resTema .tema")
    print("desglose por tema:", len(barras), "filas")
    if not barras:
        fallos.append("el desglose por tema salio vacio")
    suma_temas = sum(int(t.find_element(By.CSS_SELECTOR, ".tn").text.split("/")[0]) for t in barras)
    if suma_temas != 50:
        fallos.append("las filas por tema suman %d, no 50" % suma_temas)

    # --- 5. historial en localStorage ---
    hist = drv.execute_script("return JSON.parse(localStorage.getItem('simu_v1_historial')||'[]')")
    print("historial guardado:", json.dumps(hist, ensure_ascii=False)[:150])
    if not hist or hist[-1]["aciertos"] != 50:
        fallos.append("el historial no registro el intento")

    # --- 6. el progreso se limpio tras entregar ---
    prog2 = drv.execute_script("return localStorage.getItem('simu_v1_progreso')")
    if prog2:
        fallos.append("el progreso quedo en localStorage tras entregar")

    # --- 7. captura de pantalla del resultado ---
    drv.save_screenshot(r"C:\Users\musky\AppData\Local\Temp\opencode\shot_resultado.png")

    # --- 8. vuelta al inicio y estado limpio ---
    drv.find_element(By.ID, "btnOtra").click()
    time.sleep(0.6)
    if not drv.find_element(By.ID, "viewInicio").is_displayed():
        fallos.append("no se vuelve al inicio")
    drv.save_screenshot(r"C:\Users\musky\AppData\Local\Temp\opencode\shot_inicio.png")
    drv.find_element(By.CSS_SELECTOR, ".fbtn").click()
    drv.find_element(By.ID, "inNombre").send_keys("X")
    drv.find_element(By.ID, "inDoc").send_keys("1")
    drv.find_element(By.ID, "btnComenzar").click()
    time.sleep(0.8)
    drv.save_screenshot(r"C:\Users\musky\AppData\Local\Temp\opencode\shot_examen.png")

finally:
    drv.quit()

print()
if fallos:
    print("FALLOS (%d):" % len(fallos))
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("E2E OK: 50/50, desglose correcto, historial y reinicio limpios.")
