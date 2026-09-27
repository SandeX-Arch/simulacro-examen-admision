# Simulacro de Examen de Admisión

Simulador de examen de admisión construido a partir de un valotario impreso de 1000 preguntas.
20 formas de 50 preguntas, ranking compartido en Google Sheets y despliegue estático en GitHub Pages.

- **Banco:** 408 preguntas verificadas en 16 temas
- **Formas:** 20 × 50 = 1000 apariciones
- **Sin repetidas:** ninguna pregunta aparece dos veces dentro de una misma forma
- **PDFs de texto real:** se pueden buscar, copiar y imprimir (no son imágenes)

---

## Cómo usarlo

1. Abre la página (GitHub Pages).
2. Elige tu forma (1 a 20).
3. Escribe tu nombre y documento.
4. Responde las 50 preguntas. Puedes marcar las que quieras revisar y usar el mapa de preguntas.
5. Entrega y mira tu puntaje, tu desglose por tema y el ranking.

Atajos de teclado: `1`–`5` para responder, `←` / `→` para moverte.

Si recargas la página a mitad de examen, aparece un botón **Continuar** con el avance guardado
en el navegador.

---

## Estructura

```
index.html              interfaz (3 vistas: inicio, examen, resultado)
assets/style.css        estilos, paleta sobria
assets/app.js           lógica del cliente, sin dependencias
data/forms.json         las 20 formas con sus 1000 preguntas (SIN respuestas)
data/clave.json         clave de respuestas, separada a propósito
data/meta.json          temas y estadísticas
data/config.js          aquí se pega la URL de Google Apps Script
code/Code.gs            backend de Google Sheets
docs/                   PDFs generados
tools/                  scripts de extracción y generación
```

`data/forms.json` no contiene el campo de respuesta. La clave está en `data/clave.json` porque
el navegador necesita la clave para calificar en el momento; **esto no es un examen a prueba de
trampas**. Para un examen real, elije la clave desde el servidor.

---

## Habilitar el ranking compartido (Google Sheets)

El sitio funciona sin esto: guarda el resultado solo en el navegador y muestra el ranking como
"no configurado".

1. Crea un Google Sheet nuevo.
2. Menú **Extensiones → Apps Script**.
3. Borra el contenido de `Code.gs` y pega el archivo de `code/Code.gs` de este repositorio.
4. **Implementar → Nueva aplicación web**
   - Ejecutar como: **Yo**
   - Quién tiene acceso: **Cualquiera**
5. Copia la URL que termina en `/exec`.
6. Pégala en `data/config.js`:
   ```js
   window.APP_CONFIG = { sheetsApiUrl: "https://script.google.com/macros/s/TU_ID/exec" };
   ```
7. Sube el cambio a GitHub (tarda unos minutos en reflejarse en Pages).

La hoja `Resultados` se crea sola con las columnas: Fecha, Nombre, Documento, Correo, Forma,
Aciertos, Total, Porcentaje.

> Si el ranking no carga, revisa que el Web App esté en "Cualquiera". También puedes probarlo
> con `?api=TU_URL` en la barra de direcciones sin tocar el repositorio.

---

## Los PDFs

| Archivo | Contenido |
|---|---|
| `docs/01-Banco-de-Preguntas.pdf` | Las 408 preguntas con sus 5 opciones, agrupadas por tema (50 págs) |
| `docs/02-Clave-General.pdf` | Clave de las 408 preguntas |
| `docs/03-Clave-por-Forma.pdf` | Las 20 formas × 50 respuestas |

Las preguntas se identifican por su número original del valotario (P1 … P1000), así que puedes
cruzar cualquier pregunta con el libro físico.

---

## Procedencia y límites del contenido

Todo el texto viene de OCR sobre un PDF escaneado. Esto tiene consecuencias que conviene conocer:

- **Faltan acentos y tildes.** El OCR los perdió en casi todo el texto ("Cual" en vez de "Cuál").
- **La clave impresa parece tener errores.** Se detectaron al menos tres: P42, P67 y P80.
  Contrasta con el libro original.
- **Se descartaron 92 de las 1000 preguntas** por ilegibilidad o por no ser de opción múltiple:

| Rango | Motivo |
|---|---|
| 201–220 Analogías | La tabla de 3 columnas se leyó con las filas intercaladas; se perdería el orden |
| 251–265 Plan de redacción | El OCR destroys las etiquetas romanas (I/II indistinguibles), las opciones quedan sin sentido |
| 856–858 Química | En el original dicen "Resolver": son abiertas, sin alternativa |
| 92 restantes | Enunciado u opción ilegible, o el bloque se derramó sobre la pregunta siguiente |

- Quedan **16 temas**: Psicología, Economía Política, Historia del Perú, Historia Universal,
  Filosofía, Ética y Cívica, Geografía, Comprensión Lectora, Sinónimos, Antónimos,
  Términos Excluidos, Etimologías, Morfología y Sintaxis, Conectores Lógicos, Química y Biología.

**Úsalo como simulacro, no como fuente oficial.**

### Reparto de las 408 preguntas en las 20 formas

Con 408 preguntas y 1000 slots no se puede cumplir "cada pregunta exactamente dos veces"
(harían falta 500). Se repartió lo más parejo posible:

- 224 preguntas aparecen **2 veces**
- 184 preguntas aparecen **3 veces**
- dentro de cada forma, las 50 son siempre distintas

---

## Regenerar los datos

```bash
pip install pymupdf rapidocr-onnxruntime opencv-python-headless numpy
python tools/parse_final.py    # clave de respuestas -> final_answers.json
python tools/parse_bank.py     # OCR + clave -> bank.json
python tools/make_forms.py     # bank.json -> forms.json (20 formas)
python tools/export_web.py     # -> data/forms.json, data/clave.json, data/meta.json
python tools/gen_pdfs.py       # -> docs/*.pdf
```

Comprobaciones:

```bash
python tools/verify_forms.py   # 1000/1000 respuestas correctas tras el barajado
python tools/verify_pdfs.py    # texto extraíble, sin desbordes
python tools/validate_web.py   # referencias JS->HTML, cobertura de la clave
```

---

## Licencia y datos

El contenido de las preguntas pertenece a la editorial del valotario original; este repositorio
solo contiene la extracción y el simulador.
