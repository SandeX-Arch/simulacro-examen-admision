# -*- coding: utf-8 -*-
"""Rutas compartidas por los scripts de tools/.

Todo es relativo a la raiz del repositorio, asi que el pipeline se puede
ejecutar desde cualquier maquina. El PDF original se indica por entorno:

    set VALOTARIO_PDF=C:\\ruta\\al\\valotario.pdf
"""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DATA = ROOT / "data"
DOCS = ROOT / "docs"
BUILD = ROOT / "build"          # intermedios: OCR, clave, banco, formas

# PDF escaneado original (no se versiona: son decenas de MB)
DEFAULT_PDF = r"C:\Users\musky\OneDrive\Documentos\SIMULACROS\Scan2026-08-27_163257.pdf"
VALOTARIO_PDF = pathlib.Path(os.environ.get("VALOTARIO_PDF", DEFAULT_PDF))

OCR_CLEAN = BUILD / "ocr_clean.txt"
OCR_FULL = BUILD / "ocr_full.txt"
KEYPAGES = BUILD / "keypages.txt"
FINAL_ANSWERS = BUILD / "final_answers.json"
BANK = BUILD / "bank.json"
FORMS = BUILD / "forms.json"

for _d in (DATA, DOCS, BUILD):
    _d.mkdir(parents=True, exist_ok=True)
