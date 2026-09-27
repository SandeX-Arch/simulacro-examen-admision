/**
 * Simulacro de Admisión — backend en Google Sheets + Apps Script
 * =============================================================
 *
 * CÓMO MONTARLO (no necesitas editar nada, solo pegar y publicar)
 *   1. Crea un Google Sheet nuevo.
 *   2. Con el Sheet abierto: menu Extensiones > Apps Script.
 *   3. Borra lo que haya en Code.gs y pega TODO este archivo. Guarda.
 *   4. Menu Implementar > Nueva aplicacion web
 *        - Ejecutar como:      Yo
 *        - Quien tiene acceso: Cualquiera  (o "Cualquier persona")
 *      Acepta los avisos de permiso.
 *   5. Copia la URL que termina en /exec.
 *   6. En el sitio, despliega el panel "Conectar el ranking compartido", pega
 *      esa URL y pulsa "Guardar y activar".
 *
 *   Para que lo usen todos sin configurar nada, pega la URL en data/config.js
 *   del repositorio y sube el cambio.
 *
 *   La hoja "Resultados" se crea sola con estas columnas, con el titulo fijo:
 *   Fecha | Nombre | Forma | Aciertos | Total | Porcentaje
 *
 *   Si da error de hoja, pega el ID del Sheet (esta en su URL, entre /d/ y /edit)
 *   en SPREADSHEET_ID.
 */

// ------------------------------------------------------------------ CONFIG
// Dejalo vacio si el script esta ligado a un Sheet (lo normal: Apps Script se
// abrio desde el propio Sheet). Solo rellenalo si da error de hoja.
var SPREADSHEET_ID = '';
var HOJA = 'Resultados';
var MAX_FILAS = 20000;
var TOP_N = 50;

// ------------------------------------------------------------------ HELPERS
var _ultimaRuta = '';   // como se localizo el Sheet, para el diagnostico

/** Localiza el Sheet valga como este: ID explicito, hoja activa o hoja madre del script. */
function ss() {
  if (SPREADSHEET_ID) {
    _ultimaRuta = 'SPREADSHEET_ID';
    return SpreadsheetApp.openById(String(SPREADSHEET_ID).trim());
  }
  var act = SpreadsheetApp.getActiveSpreadsheet();
  if (act) { _ultimaRuta = 'hoja activa'; return act; }

  // script independiente: buscar la hoja de la que cuelga el archivo .gs
  var padres = SpreadsheetApp.getActive().getFile().getParents();
  for (var i = 0; i < padres.length; i++) {
    if (padres[i].getMimeType() === 'application/vnd.google-apps.spreadsheet') {
      _ultimaRuta = 'hoja madre del script';
      return SpreadsheetApp.openById(padres[i].getId());
    }
  }
  throw new Error('No se encontro la hoja. Abre el ID del Sheet (esta en su URL, ' +
    'entre /d/ y /edit) y pegalo en SPREADSHEET_ID.');
}

function tabla() {
  var libro = ss();
  var hoja = libro.getSheetByName(HOJA);
  if (!hoja) {
    hoja = libro.insertSheet(HOJA);
    hoja.appendRow(['Fecha', 'Nombre', 'Forma', 'Aciertos', 'Total', 'Porcentaje']);
    hoja.setFrozenRows(1);
    hoja.getRange(1, 1, 1, 6).setFontWeight('bold');
    hoja.getRange('A:A').setNumberFormat('dd/mm/yyyy hh:mm');
  }
  return hoja;
}

function limpio(v, n) {
  // quita caracteres de control (saltos de linea, tabs), NO espacios ni signos
  return String(v == null ? '' : v).replace(/[\x00-\x1F\x7F]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, n || 60);
}

function num(v) {
  var n = Number(v);
  return isFinite(n) ? n : 0;
}

// ------------------------------------------------------------------ ENDPOINTS
/** GET /exec            -> ranking
 *  GET /exec?accion=ping -> diagnostico                      */
function doGet(e) {
  try {
    var accion = (e && e.parameter && e.parameter.accion) || '';
    if (accion === 'ping') {
      var h = ss().getSheetByName(HOJA);
      return json({
        ok: true,
        hoja: h ? HOJA : '(se creara al primer envio)',
        via: _ultimaRuta,
        hojaExiste: !!h,
        resultados: h ? Math.max(0, h.getLastRow() - 1) : 0
      });
    }
    return json({ ok: true, top: top(TOP_N) });
  } catch (err) {
    return json({ ok: false, error: String(err && err.message || err) });
  }
}

/** POST /exec  con cuerpo JSON plano: {nombre, forma, aciertos, total} */
function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    var d = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (!limpio(d.nombre, 40) || !num(d.forma)) {
      return json({ ok: false, error: 'faltan el nombre o la forma' });
    }
    var total = num(d.total) || 50;
    var aciertos = num(d.aciertos);
    if (aciertos > total) aciertos = total;
    if (aciertos < 0) aciertos = 0;

    var hoja = tabla();
    hoja.appendRow([
      new Date(),
      limpio(d.nombre, 40),
      num(d.forma),
      aciertos,
      total,
      Math.round(aciertos / total * 100)
    ]);

    var excess = hoja.getLastRow() - 1 - MAX_FILAS;
    if (excess > 0) hoja.deleteRows(2, excess);   // conserva la cabecera

    return json({ ok: true, guardadas: hoja.getLastRow() - 1 });
  } catch (err) {
    return json({ ok: false, error: String(err && err.message || err) });
  } finally {
    lock.releaseLock();
  }
}

/** Top N por porcentaje, luego aciertos, luego fecha (el primero que lo hizo gana). */
function top(n) {
  var hoja = ss().getSheetByName(HOJA);
  if (!hoja || hoja.getLastRow() < 2) return [];
  var v = hoja.getRange(2, 1, hoja.getLastRow() - 1, 6).getValues();
  var out = [];
  for (var i = 0; i < v.length; i++) {
    var r = v[i];
    if (!r[1]) continue;
    out.push({
      nombre: r[1], forma: r[2],
      aciertos: r[3], total: r[4], pct: r[5], fecha: r[0]
    });
  }
  out.sort(function (a, b) {
    if (b.pct !== a.pct) return b.pct - a.pct;
    if (b.aciertos !== a.aciertos) return b.aciertos - a.aciertos;
    return new Date(a.fecha) - new Date(b.fecha);
  });
  return out.slice(0, n || TOP_N);
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
