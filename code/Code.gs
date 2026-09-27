/**
 * Simulacro de Admisión — backend en Google Sheets + Apps Script
 *
 * Crea un Google Sheet nuevo y pega este archivo en
 *   Extensiones > Apps Script > Code.gs
 *Luego: Implementar > Nueva aplicación web > Ejecutar como: Yo
 *      > Quién tiene acceso: Cualquiera   > Implementar
 * Copia la URL /exec y pégala en data/config.js del sitio.
 *
 * Hoja "Resultados" (se crea sola). Columnas:
 *   A Fecha | B Nombre | C Documento | D Correo | E Forma | F Aciertos | G Total | H Porcentaje
 */

var HOJA = 'Resultados';
var MAX_Filas = 5000;

function doGet(e) {
  try {
    responder({ ok: true, top: topN(50) });
  } catch (err) {
    responder({ ok: false, error: String(err) });
  }
}

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    if (!d.nombre || !d.documento || !d.forma) {
      responder({ ok: false, error: 'faltan datos' });
      return;
    }
    var lock = LockService.getScriptLock();
    lock.waitLock(10000);
    try {
      var fila = [
        new Date(),
        String(d.nombre).slice(0, 60),
        String(d.documento).slice(0, 20),
        String(d.correo || '').slice(0, 80),
        Number(d.forma),
        Number(d.aciertos),
        Number(d.total),
        Math.round(Number(d.aciertos) / Number(d.total) * 100)
      ];
      var ss = SpreadsheetApp.getActiveSpreadsheet();
      var sh = ss.getSheetByName(HOJA) || ss.insertSheet(HOJA);
      if (sh.getLastRow() === 0) sh.appendRow(['Fecha', 'Nombre', 'Documento', 'Correo', 'Forma', 'Aciertos', 'Total', 'Porcentaje']);
      sh.appendRow(fila);
      if (sh.getLastRow() > MAX_Filas) sh.deleteRows(2, sh.getLastRow() - MAX_Filas);
      responder({ ok: true });
    } finally {
      lock.releaseLock();
    }
  } catch (err) {
    responder({ ok: false, error: String(err) });
  }
}

/** Top N por porcentaje y luego por aciertos. */
function topN(n) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(HOJA);
  if (!sh) return [];
  var v = sh.getDataRange().getValues();
  var out = [];
  for (var i = 1; i < v.length; i++) {
    var r = v[i];
    if (!r[1]) continue;
    out.push({
      nombre: r[1],
      forma: r[4],
      aciertos: r[5],
      total: r[6],
      pct: r[7],
      fecha: r[0]
    });
  }
  out.sort(function (a, b) {
    if (b.pct !== a.pct) return b.pct - a.pct;
    if (b.aciertos !== a.aciertos) return b.aciertos - a.aciertos;
    return new Date(a.fecha) - new Date(b.fecha);
  });
  return out.slice(0, n);
}

/** Un Web App público de Apps Script responde con CORS abierto para ContentService. */
function responder(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
