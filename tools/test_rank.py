# -*- coding: utf-8 -*-
"""Prueba de la ruta del RANKING contra el mock de Apps Script.
Verifica: carga de la tabla, escape de HTML, envio del resultado al hacer entrega."""
import json, os, sys, io, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SITE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8731/index.html"
API = "http://127.0.0.1:8732/exec"
POST = r"C:\Users\musky\AppData\Local\Temp\opencode\mock_post.txt"
if os.path.exists(POST):
    os.remove(POST)

fallos = []
opt = Options()
for a in ("--headless=new", "--disable-gpu", "--no-sandbox", "--window-size=1280,900"):
    opt.add_argument(a)
drv = webdriver.Edge(options=opt)
try:
    drv.get(SITE + "?api=" + API)
    time.sleep(2.0)

    # --- 1. la tabla del ranking se pintó ---
    filas = drv.find_elements(By.CSS_SELECTOR, "#rankBody table.rank-t tbody tr")
    print("filas del ranking:", len(filas))
    if len(filas) != 4:
        fallos.append("se esperaban 4 filas, hay %d" % len(filas))
    estado = drv.find_element(By.ID, "rankState").text
    print("estado:", estado)
    if "participante" not in estado:
        fallos.append("el estado del ranking no cuadra: %r" % estado)

    # --- 2. el HTML del nombre viene escapado (no inyecta <b>) ---
    crudo = drv.find_element(By.ID, "rankBody").get_attribute("innerHTML")
    if "<b>Torres</b>" in crudo:
        fallos.append("el nombre del ranking se inyecta como HTML sin escapar")
    else:
        print("escapado de HTML: OK")
    if "&lt;b&gt;Torres&lt;/b&gt;" not in crudo:
        fallos.append("no se encontro el texto escapado esperado")

    # --- 3. puntaje mostrado ---
    p = filas[0].find_element(By.CSS_SELECTOR, "td.p").text
    print("primer lugar:", filas[0].text.replace("\n", " | "))
    if "48/50" not in p or "96%" not in p:
        fallos.append("el puntaje no se formatea bien: %r" % p)

    # --- 4. entregar un intento y ver que se POSTea ---
    drv.find_elements(By.CSS_SELECTOR, ".fbtn")[0].click()
    drv.find_element(By.ID, "inNombre").send_keys("Post De Prueba")
    drv.find_element(By.ID, "inDoc").send_keys("99999999")
    drv.find_element(By.ID, "btnComenzar").click()
    time.sleep(1.0)
    # contestar 3 preguntas DISTINTAS y entregar (debe avisar que faltan)
    for i in range(3):
        drv.find_elements(By.CSS_SELECTOR, ".pal")[i].click()
        drv.find_elements(By.CSS_SELECTOR, "#qOpts .opt")[i].click()
    drv.find_element(By.ID, "btnEntregar").click()
    time.sleep(0.4)
    if drv.find_element(By.ID, "avisoEntrega").is_displayed():
        print("aviso de preguntas faltantes: OK")
    else:
        fallos.append("no aviso que faltan preguntas al entregar incompleto")
    aviso = drv.find_element(By.ID, "faltan").text
    if aviso.strip() != "47":
        fallos.append("faltan dice %r, se esperaba 47" % aviso)

    # forzar entrega contestando el resto
    clave = json.load(open(r"C:\Users\musky\OneDrive\Documentos\SIMULACROS\examen-admision\data\clave.json",
                          encoding="utf-8"))["1"]
    forms = json.load(open(r"C:\Users\musky\OneDrive\Documentos\SIMULACROS\examen-admision\data\forms.json",
                           encoding="utf-8"))
    pregs = [f for f in forms if f["id"] == 1][0]["preguntas"]
    for q in pregs:
        drv.find_elements(By.CSS_SELECTOR, ".pal")[q["pos"] - 1].click()
        drv.find_elements(By.CSS_SELECTOR, "#qOpts .opt")[clave[str(q["pos"])]].click()
    drv.find_element(By.ID, "btnEntregar").click()
    time.sleep(1.6)

    if not drv.find_element(By.ID, "viewResultado").is_displayed():
        fallos.append("no se llego a la vista de resultado")
    msg = drv.find_element(By.ID, "resEnvio").text
    print("mensaje de envio:", msg)
    if "Enviando" in msg or "No se pudo" in msg:
        fallos.append("el envio no se completo: %r" % msg)

    # el mock guardo lo que recibio
    if not os.path.exists(POST):
        fallos.append("el backend no recibio ningun POST")
    else:
        lineas = [l for l in open(POST, encoding="utf-8").read().splitlines() if l.strip()]
        print("POSTs recibidas:", len(lineas))
        if not lineas:
            fallos.append("no se registro el POST")
        else:
            d = json.loads(lineas[-1])
            print("  payload:", json.dumps(d, ensure_ascii=False))
            for k, v in (("nombre", "Post De Prueba"), ("documento", "99999999"), ("forma", 1),
                         ("aciertos", 50), ("total", 50)):
                if d.get(k) != v:
                    fallos.append("payload %s = %r, se esperaba %r" % (k, d.get(k), v))

    # el ranking se refresca solo
    time.sleep(3.0)
    filas2 = drv.find_elements(By.CSS_SELECTOR, "#rankBody table.rank-t tbody tr")
    print("filas tras refrescar:", len(filas2))
finally:
    drv.quit()

print()
if fallos:
    print("FALLOS (%d):" % len(fallos))
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("RANKING OK: carga, escape, formateo, POST y refresco.")
