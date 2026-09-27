# -*- coding: utf-8 -*-
"""Prueba del panel 'Conectar ranking':
 - aparece cuando no hay URL configurada
 - el boton de copiar carga code/Code.gs
 - una URL invalida se rechaza
 - guardar una URL buena activa el ranking y guarda en localStorage
 - al recargar, el panel desaparece
"""
import json, os, sys, io, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SITE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8731/index.html"
BUENA = "http://127.0.0.1:8732/exec"       # el mock acepta cualquier ruta /exec
fallos = []

opt = Options()
for a in ("--headless=new", "--disable-gpu", "--no-sandbox", "--window-size=1280,900"):
    opt.add_argument(a)
drv = webdriver.Edge(options=opt)


def panel_visible():
    return drv.find_element(By.ID, "panelOwner").is_displayed()


try:
    # ---------- 1. sin configurar: el panel esta visible ----------
    drv.get(SITE)
    time.sleep(1.8)
    if not panel_visible():
        fallos.append("el panel del admin no aparece sin URL configurada")
    else:
        print("panel visible sin configurar: OK")
    if drv.find_element(By.ID, "rankState").text != "no configurado":
        fallos.append("el estado del ranking no dice 'no configurado'")

    # abrir el <details> (viene plegado para no molestar al participante)
    drv.find_element(By.CSS_SELECTOR, "details.owner > summary").click()
    time.sleep(0.4)
    if not drv.find_element(By.ID, "btnCopiarGs").is_displayed():
        fallos.append("el summary no despliega el panel")
    else:
        print("summary despliega el panel: OK")

    # ---------- 2. cargar el codigo de Apps Script ----------
    drv.find_element(By.ID, "btnCopiarGs").click()
    time.sleep(1.2)
    cod = drv.find_element(By.ID, "gsCode").get_attribute("value")
    print("code/Code.gs cargado: %d caracteres" % len(cod))
    if len(cod) < 800:
        fallos.append("el codigo de Apps Script no se cargo (solo %d chars)" % len(cod))
    for marca in ("function doGet", "function doPost", "function top", "SPREADSHEET_ID"):
        if marca not in cod:
            fallos.append("al codigo le falta %r" % marca)
    if "HACK" in cod or "posicion" in cod:
        fallos.append("el codigo contiene restos sospechosos")

    # ---------- 3. URL invalida: debe advertir y NO guardar ----------
    campo = drv.find_element(By.ID, "inApi")
    campo.clear()
    campo.send_keys("https://ejemplo.com/no-es-apps-script")
    drv.find_element(By.ID, "btnProbar").click()
    time.sleep(0.8)
    m = drv.find_element(By.ID, "apiMsg").text
    print("aviso de URL invalida:", m[:70])
    if "forma de un Web App" not in m:
        fallos.append("no aviso que la URL no tiene forma de /exec")

    # ---------- 3b. "Guardar" tampoco debe aceptar una URL invalida ----------
    drv.find_element(By.ID, "btnGuardarApi").click()
    time.sleep(0.6)
    if drv.execute_script("return localStorage.getItem('simu_v1_api')"):
        fallos.append("GUARDO una URL invalida (no debio)")
    else:
        print("guardar rechaza URL invalida: OK")
    if not panel_visible():
        fallos.append("el panel se oculto pese a no haber guardado nada")
    else:
        print("panel sigue visible tras rechazo: OK")

    # ---------- 4. guardar la URL buena ----------
    campo = drv.find_element(By.ID, "inApi")
    campo.clear()
    campo.send_keys(BUENA)
    drv.find_element(By.ID, "btnGuardarApi").click()
    time.sleep(2.0)
    guardada = drv.execute_script("return localStorage.getItem('simu_v1_api')")
    print("URL guardada:", guardada)
    if guardada != BUENA:
        fallos.append("no guardo la URL: %r" % guardada)
    if panel_visible():
        fallos.append("el panel sigue visible despues de activar el ranking")
    else:
        print("panel oculto tras activar: OK")
    filas = drv.find_elements(By.CSS_SELECTOR, "#rankBody table.rank-t tbody tr")
    print("filas del ranking tras activar:", len(filas))
    if len(filas) != 4:
        fallos.append("el ranking no cargo tras guardar la URL (%d filas)" % len(filas))

    # ---------- 5. tras recargar, el panel no vuelve ----------
    drv.get(SITE)
    time.sleep(2.0)
    if panel_visible():
        fallos.append("el panel reaparece tras recargar (deberia quedar oculto)")
    else:
        print("panel oculto tras recargar: OK")
    if drv.execute_script("return localStorage.getItem('simu_v1_api')") != BUENA:
        fallos.append("la URL no persistio tras recargar")

    # ---------- 6. ?api= manda sobre localStorage ----------
    drv.get(SITE + "?api=" + BUENA)
    time.sleep(1.8)
    if panel_visible():
        fallos.append("con ?api= el panel deberia quedar oculto")
    print("?api= respetado: OK")

    # ---------- 7. limpiar ----------
    drv.execute_script("localStorage.removeItem('simu_v1_api')")
finally:
    drv.quit()

print()
if fallos:
    print("FALLOS (%d):" % len(fallos))
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("PANEL OK: aparece, carga codigo, valida, guarda, activa y se oculta.")
