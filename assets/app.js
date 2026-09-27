/* Simulacro de Admisión — lógica del cliente (sin dependencias) */
(function () {
  "use strict";

  var CFG = window.APP_CONFIG || {};
  var LS = "simu_v1_";
  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };

  var S = {
    vista: "inicio",
    forma: null,
    preguntas: [],
    clave: {},
    indice: 0,
    resp: {},        // pos -> 0..4
    marcadas: {},    // pos -> true
    datos: {},
    meta: null,
    resultado: null
  };

  /* ---------------- datos ---------------- */
  function cargar(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error(url + " -> " + r.status);
      return r.json();
    });
  }

  /* ---------------- vistas ---------------- */
  function ver(v) {
    S.vista = v;
    $("#viewInicio").hidden = v !== "inicio";
    $("#viewExamen").hidden = v !== "examen";
    $("#viewResultado").hidden = v !== "resultado";
    $("#btnSalir").hidden = v === "inicio";
    window.scrollTo(0, 0);
  }

  /* ---------------- inicio ---------------- */
  function pintarFormas(formas) {
    var g = $("#gridFormas");
    g.innerHTML = "";
    formas.forEach(function (f) {
      var b = document.createElement("button");
      b.className = "fbtn";
      b.type = "button";
      b.textContent = f.id;
      b.setAttribute("aria-pressed", "false");
      b.setAttribute("aria-label", f.nombre);
      b.addEventListener("click", function () {
        S.forma = f.id;
        $$(".fbtn").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        b.setAttribute("aria-pressed", "true");
        $("#elegida").innerHTML = "Forma seleccionada: <b>" + f.nombre + "</b>";
        $("#btnComenzar").disabled = false;
      });
      g.appendChild(b);
    });
  }

  function leerDatos() {
    return {
      nombre: $("#inNombre").value.trim(),
      documento: $("#inDoc").value.trim(),
      correo: $("#inMail").value.trim()
    };
  }

  /* ---------------- examen ---------------- */
  function pintarPregunta() {
    var p = S.preguntas[S.indice];
    $("#exForma").textContent = "Forma " + S.forma;
    $("#qNum").textContent = "Pregunta " + p.pos + " de " + S.preguntas.length;
    $("#qTopico").textContent = p.topico;
    $("#qStem").textContent = p.pregunta;

    var cont = $("#qOpts");
    cont.innerHTML = "";
    p.opciones.forEach(function (txt, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "opt";
      b.setAttribute("aria-pressed", S.resp[p.pos] === i ? "true" : "false");
      var k = document.createElement("span");
      k.className = "k";
      k.textContent = "ABCDE".charAt(i);
      var t = document.createElement("span");
      t.textContent = txt;
      b.appendChild(k); b.appendChild(t);
      b.addEventListener("click", function () {
        S.resp[p.pos] = i;
        persistir();
        pintarPregunta();
      });
      cont.appendChild(b);
    });

    var hechas = Object.keys(S.resp).length;
    var total = S.preguntas.length;
    $("#progFill").style.width = (hechas / total * 100) + "%";
    $("#progTxt").textContent = hechas + " / " + total;

    $("#btnPrev").disabled = S.indice === 0;
    var ultimo = S.indice === total - 1;
    $("#btnNext").textContent = ultimo ? "Última →" : "Siguiente →";
    var mk = S.marcadas[p.pos];
    $("#btnMarcar").textContent = mk ? "Quitar marca" : "Marcar";
    $("#btnMarcar").classList.toggle("btn-primary", !!mk);

    pintarPaleta();
  }

  function pintarPaleta() {
    var p = $("#paleta");
    p.innerHTML = "";
    S.preguntas.forEach(function (q, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "pal";
      b.textContent = q.pos;
      if (S.resp[q.pos] !== undefined) b.classList.add("done");
      if (S.marcadas[q.pos]) b.classList.add("mark");
      if (i === S.indice) b.classList.add("cur");
      b.addEventListener("click", function () { S.indice = i; pintarPregunta(); });
      p.appendChild(b);
    });
  }

  /* ---------------- resultado ---------------- */
  function calificar() {
    var k = S.clave[S.forma] || {};
    var porTema = {}, aciertos = 0, detalle = [];
    S.preguntas.forEach(function (p) {
      var c = k[String(p.pos)];
      var r = S.resp[p.pos];
      var ok = r !== undefined && r === c;
      if (ok) aciertos++;
      if (!porTema[p.topico]) porTema[p.topico] = { ok: 0, tot: 0 };
      porTema[p.topico].tot++;
      if (ok) porTema[p.topico].ok++;
      detalle.push({ pos: p.pos, id: p.id, topico: p.topico, elegida: r, correcta: c, ok: ok });
    });
    return { aciertos: aciertos, total: S.preguntas.length, porTema: porTema, detalle: detalle };
  }

  function pintarResultado(res) {
    var pct = Math.round(res.aciertos / res.total * 100);
    $("#resForma").textContent = S.preguntas.length + " preguntas · Forma " + S.forma;
    $("#puntaje").textContent = res.aciertos;
    $("#resNombre").textContent = S.datos.nombre;
    $("#resBar").firstElementChild.style.width = pct + "%";
    $("#resMsg").textContent = pct + "% de aciertos (" + res.aciertos + " de " + res.total + ")";
    $("#puntaje").nextElementSibling.textContent = "/ " + res.total;

    var t = $("#resTema");
    t.innerHTML = "";
    Object.keys(res.porTema).sort(function (a, b) {
      var x = res.porTema[a].ok / res.porTema[a].tot, y = res.porTema[b].ok / res.porTema[b].tot;
      return x - y;
    }).forEach(function (nombre) {
      var d = res.porTema[nombre];
      var p = Math.round(d.ok / d.tot * 100);
      var row = document.createElement("div");
      row.className = "tema";
      var a = document.createElement("div"); a.textContent = nombre;
      var bar = document.createElement("div"); bar.className = "tb";
      var fill = document.createElement("i"); fill.style.width = p + "%";
      bar.appendChild(fill);
      var n = document.createElement("div"); n.className = "tn";
      n.textContent = d.ok + "/" + d.tot;
      row.appendChild(a); row.appendChild(bar); row.appendChild(n);
      t.appendChild(row);
    });
  }

  function guardarLocal(res) {
    try {
      var ls = JSON.parse(localStorage.getItem(LS + "historial") || "[]");
      ls.push({ forma: S.forma, datos: S.datos, aciertos: res.aciertos, total: res.total, fecha: new Date().toISOString() });
      localStorage.setItem(LS + "historial", JSON.stringify(ls.slice(-50)));
    } catch (e) { /* modo privado: se ignora */ }
  }

  function enviar(res) {
    var out = $("#resEnvio");
    var url = apiUrl();
    out.textContent = "";
    if (!url) {
      out.textContent = "Ranking compartido no configurado: el resultado se guardó solo en este navegador.";
      return;
    }
    out.textContent = "Enviando resultado…";
    // no-cors + text/plain: Apps Script no expone CORS para POST, y text/plain
    // es un content-type "simple" (no dispara preflight).
    fetch(url, {
      method: "POST",
      mode: "no-cors",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({
        nombre: S.datos.nombre,
        documento: S.datos.documento,
        correo: S.datos.correo,
        forma: S.forma,
        aciertos: res.aciertos,
        total: res.total
      })
    }).then(function () {
      out.textContent = "Resultado enviado. El ranking se actualiza en unos segundos.";
      setTimeout(cargarRanking, 2500);
    }).catch(function () {
      out.textContent = "No se pudo enviar el resultado (sin conexión). Quedó guardado en este navegador.";
    });
  }

  function entregar(forzar) {
    var total = S.preguntas.length;
    var hechas = Object.keys(S.resp).length;
    if (!forzar && hechas < total) {
      $("#faltan").textContent = total - hechas;
      $("#avisoEntrega").hidden = false;
      return;
    }
    $("#avisoEntrega").hidden = true;
    S.resultado = calificar();
    guardarLocal(S.resultado);
    pintarResultado(S.resultado);
    ver("resultado");
    enviar(S.resultado);
    try { localStorage.removeItem(LS + "progreso"); } catch (e) {}
  }

  /* ---------------- configuracion del backend ---------------- */
  function apiGuardada() {
    try { return (localStorage.getItem(LS + "api") || "").trim(); } catch (e) { return ""; }
  }

  function apiUrl() {
    var q = (new URLSearchParams(location.search).get("api") || "").trim();
    if (q) return q;                                  // override de ad-hoc (?api=...)
    if (apiGuardada()) return apiGuardada();         // lo que guardo el admin en este navegador
    return (CFG.sheetsApiUrl || "").trim();          // data/config.js
  }

  function mostrarPanelOwner(forzar) {
    $("#panelOwner").hidden = forzar ? false : !!apiUrl();
  }

  // Solo se aceptan URLs con forma de Web App de Apps Script. Se admite localhost
  // para poder probar el backend en local sin desplegarlo.
  var RE_URL = /^(https:\/\/script\.google(usercontent)?\.com\/macros\/s\/[^/]+\/exec|https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\/.*)$/;

  function urlValida(u) {
    return RE_URL.test(String(u || "").trim());
  }

  function mensaje(txt, tipo) {
    var m = $("#apiMsg");
    m.textContent = txt;
    m.className = "small " + (tipo || "");
  }

  function probarApi(url) {
    if (!urlValida(url)) {
      mensaje("Esa URL no tiene la forma de un Web App de Apps Script (debe terminar en /exec).", "warn");
      return false;
    }
    mensaje("Comprobando…");
    fetch(url + (String(url).indexOf("?") < 0 ? "?" : "&") + "accion=ping", { cache: "no-cache" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.ok) {
          mensaje("Conectado. Hoja \"" + j.hoja + "\", resultados guardados: " + j.resultados + ".", "ok");
        } else {
          mensaje("El script respondió con error: " + (j && j.error ? j.error : "respuesta vacía"), "warn");
        }
      })
      .catch(function () {
        mensaje("No se pudo contactar el script. Revisa que el acceso sea \"Cualquiera\".", "warn");
      });
    return true;
  }

  function cablearOwner() {
    $("#btnCopiarGs").addEventListener("click", function () {
      fetch("code/Code.gs", { cache: "no-cache" })
        .then(function (r) { return r.text(); })
        .then(function (t) {
          $("#gsCode").value = t;
          $("#gsCode").select();
          var ok = false;
          try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
          mensaje(ok ? "Código copiado. Pégalo en Apps Script." : "No se pudo copiar: selecciona el texto y pulsa Ctrl+C.", ok ? "ok" : "warn");
        })
        .catch(function () {
          mensaje("No se pudo cargar code/Code.gs. Ábrelo desde el enlace de GitHub.", "warn");
        });
    });

    $("#btnProbar").addEventListener("click", function () { probarApi($("#inApi").value); });

    $("#btnGuardarApi").addEventListener("click", function () {
      var u = $("#inApi").value.trim();
      if (!urlValida(u)) {
        mensaje("Esa URL no parece un Web App de Apps Script, así que no se guardó. Debe ser https://script.google.com/macros/s/.../exec", "warn");
        return;
      }
      try { localStorage.setItem(LS + "api", u); } catch (e) {}
      $("#inApi").value = "";
      mostrarPanelOwner();
      cargarRanking();
      mensaje("Ranking activado en este navegador.", "ok");
    });

    // si ya habia una URL guardada, laShows para poder corregirla
    $("#inApi").value = apiGuardada();
  }

  /* ---------------- ranking ---------------- */
  function pintarRanking(filas) {
    var b = $("#rankBody"), st = $("#rankState");
    if (!filas || !filas.length) {
      st.textContent = "sin datos"; st.className = "pill off";
      b.innerHTML = '<p class="rank-note">Todavía no hay resultados registrados.</p>';
      return;
    }
    st.textContent = filas.length + " participante" + (filas.length === 1 ? "" : "s");
    var h = '<table class="rank-t"><thead><tr><th>#</th><th>Participante</th><th>Forma</th><th>Puntaje</th></tr></thead><tbody>';
    filas.forEach(function (f, i) {
      var pct = f.total ? Math.round(f.aciertos / f.total * 100) : 0;
      h += "<tr><td class='n'>" + (i + 1) + "</td><td>" + esc(f.nombre) +
           "</td><td class='muted'>" + esc(String(f.forma)) + "</td><td class='p'>" +
           esc(String(f.aciertos)) + "/" + esc(String(f.total)) + " · " + pct + "%</td></tr>";
    });
    b.innerHTML = h + "</tbody></table>";
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function cargarRanking() {
    var url = apiUrl();
    mostrarPanelOwner();
    if (!url) {
      $("#rankState").textContent = "no configurado";
      $("#rankState").className = "pill off";
      $("#rankBody").innerHTML = '<p class="rank-note">El ranking compartido se habilita conectando el Web App de Google Apps Script.</p>';
      return;
    }
    $("#rankState").textContent = "cargando…";
    fetch(url, { cache: "no-cache" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.ok === false) throw new Error(j.error || 'el script devolvio un error');
        pintarRanking(j && j.top);
      })
      .catch(function (e) {
        $("#rankState").textContent = "sin conexión";
        $("#rankState").className = "pill off";
        $("#rankBody").innerHTML = '<p class="rank-note">No se pudo consultar el ranking (' + esc(e.message) + ').</p>';
        // si hay una URL guardada pero no responde, reopening panel para poder corregirla
        if (apiUrl()) mostrarPanelOwner(true);
      });
  }

  /* ---------------- persistencia ---------------- */
  function persistir() {
    try {
      localStorage.setItem(LS + "progreso", JSON.stringify({
        forma: S.forma, indice: S.indice, resp: S.resp, marcadas: S.marcadas, datos: S.datos
      }));
    } catch (e) {}
  }

  function recuperar() {
    try {
      var raw = localStorage.getItem(LS + "progreso");
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  function ofrecerContinuar() {
    var g = $("#gridFormas");
    var prev = document.createElement("div");
    prev.className = "rank-note";
    prev.style.marginTop = "12px";
    var r = recuperar();
    if (r && r.forma) {
      prev.innerHTML = "Hay un examen en pausa (Forma " + esc(String(r.forma)) + ", " +
        Object.keys(r.resp || {}).length + " respondidas). <button id='btnSeguir' class='btn btn-ghost' style='margin-left:8px'>Continuar</button>";
    } else {
      prev.innerHTML = "";
    }
    g.parentNode.insertBefore(prev, g.nextSibling);
    if (r && r.forma) {
      prev.querySelector("#btnSeguir").addEventListener("click", function () { empezar(r.forma, r); });
    }
  }

  /* ---------------- arranque de examen ---------------- */
  function empezar(forma, prev) {
    return Promise.all([cargar("data/forms.json"), cargar("data/clave.json")]).then(function (r) {
      var formas = r[0], claves = r[1];
      var f = formas.filter(function (x) { return x.id === Number(forma); })[0];
      if (!f) throw new Error("Forma no encontrada");
      S.forma = f.id;
      S.preguntas = f.preguntas;
      S.clave = claves;
      S.indice = 0;
      S.resp = {}; S.marcadas = {};
      if (prev) { S.indice = prev.indice || 0; S.resp = prev.resp || {}; S.marcadas = prev.marcadas || {}; S.datos = prev.datos || {}; }
      else { S.datos = leerDatos(); }
      $("#inNombre").value = S.datos.nombre || "";
      $("#inDoc").value = S.datos.documento || "";
      $("#inMail").value = S.datos.correo || "";
      $("#exNombre").textContent = S.datos.nombre;
      ver("examen");
      pintarPregunta();
    }).catch(function (e) {
      alert("No se pudo cargar el examen: " + e.message);
    });
  }

  /* ---------------- init ---------------- */
  function init() {
    cablearOwner();

    $("#btnComenzar").addEventListener("click", function () {
      S.datos = leerDatos();
      if (!S.datos.nombre || !S.datos.documento) {
        $("#avisoDatos").hidden = false;
        return;
      }
      $("#avisoDatos").hidden = true;
      empezar(S.forma);
    });

    $("#btnPrev").addEventListener("click", function () {
      if (S.indice > 0) { S.indice--; pintarPregunta(); }
    });
    $("#btnNext").addEventListener("click", function () {
      if (S.indice < S.preguntas.length - 1) { S.indice++; pintarPregunta(); }
    });
    $("#btnMarcar").addEventListener("click", function () {
      var pos = S.preguntas[S.indice].pos;
      if (S.marcadas[pos]) delete S.marcadas[pos]; else S.marcadas[pos] = true;
      persistir(); pintarPregunta();
    });
    $("#btnEntregar").addEventListener("click", function () { entregar(false); });
    $("#btnSalir").addEventListener("click", function () {
      if (S.vista === "examen" && !confirm("¿Salir del examen? Se guardará el avance.")) return;
      ver("inicio");
    });
    $("#btnRevisar").addEventListener("click", function () {
      S.indice = 0; ver("examen"); pintarPregunta();
    });
    $("#btnOtra").addEventListener("click", function () {
      S.forma = null; S.resp = {}; S.marcadas = {}; S.preguntas = [];
      $$(".fbtn").forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
      $("#elegida").innerHTML = "Forma seleccionada: <b>—</b>";
      $("#btnComenzar").disabled = true;
      ver("inicio");
      cargarRanking();
    });

    document.addEventListener("keydown", function (e) {
      if (S.vista !== "examen") return;
      if (e.key === "ArrowRight") { $("#btnNext").click(); }
      else if (e.key === "ArrowLeft") { $("#btnPrev").click(); }
      else if (/^[1-5]$/.test(e.key)) {
        var b = $$("#qOpts .opt")[Number(e.key) - 1];
        if (b) b.click();
      }
    });

    Promise.all([cargar("data/forms.json"), cargar("data/meta.json")]).then(function (r) {
      S.meta = r[1];
      pintarFormas(r[0]);
      $("#fTotal").textContent = r[1].preguntasDistintas;
      $("#brandSub").textContent = r[0].length + " formas · " + r[1].porForma + " preguntas";
      ofrecerContinuar();
    }).catch(function (e) {
      $("#rankBody").innerHTML = '<p class="rank-note">No se pudieron cargar los datos del examen (' + esc(e.message) + ").</p>";
    });

    cargarRanking();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
