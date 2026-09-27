# -*- coding: utf-8 -*-
"""Mock de Google Apps Script para probar la ruta del ranking sin Sheets.

    GET  /exec                  -> {"ok":true,"top":[...]}   (con CORS)
    GET  /exec?accion=ping      -> {"ok":true,"via":"mock",...}
    POST /exec                  -> 204  (el navegador lo ve opaco por no-cors)

Los nombres llevan HTML a proposito, para comprobar que el sitio lo escapa.
"""
import json, sys, io, pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

TOP = [
    {"nombre": "Ana Quispe", "forma": 3, "aciertos": 48, "total": 50, "pct": 96, "fecha": "2026-09-20"},
    {"nombre": "Luis <b>Torres</b>", "forma": 12, "aciertos": 45, "total": 50, "pct": 90, "fecha": "2026-09-21"},
    {"nombre": "María Ñañake", "forma": 7, "aciertos": 44, "total": 50, "pct": 88, "fecha": "2026-09-22"},
    {"nombre": "Pedro \"El Chato\"", "forma": 1, "aciertos": 30, "total": 50, "pct": 60, "fecha": "2026-09-23"},
]


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if q.get("accion", [""])[0] == "ping":
            guardados = len(TOP) + self._posts()
            body = json.dumps({
                "ok": True, "hoja": "Resultados", "via": "mock",
                "hojaExiste": True, "resultados": guardados
            }, ensure_ascii=False).encode("utf-8")
        else:
            body = json.dumps({"ok": True, "top": TOP}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _posts(self):
        f = pathlib.Path(__file__).resolve().parent / "mock_post.txt"
        try:
            return len([x for x in f.read_text(encoding="utf-8").splitlines() if x.strip()])
        except OSError:
            return 0

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        crudo = self.rfile.read(n).decode("utf-8", "replace")
        salida = pathlib.Path(__file__).resolve().parent / "mock_post.txt"
        with salida.open("a", encoding="utf-8") as f:
            f.write(crudo + "\n")
        self.send_response(204)
        self._cors()
        self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8732), H).serve_forever()
