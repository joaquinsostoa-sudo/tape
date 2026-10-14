"""Arma la página HTML de la herramienta (una sola archivo, datos embebidos) a partir de `plantilla.html` y del JSON de `exportar_pry`.

Uso: uv run python -m src.herramienta.construir_pagina
"""
from __future__ import annotations

from pathlib import Path

from src.herramienta.exportar_pry import SALIDA

PLANTILLA = Path(__file__).with_name("plantilla.html")
PAGINA = SALIDA.with_suffix(".html")


def construir(plantilla: str, datos: str) -> str:
    """Inserta el JSON en la plantilla; `</` se escapa para que los datos no cierren el elemento script."""
    return plantilla.replace("__DATOS__", datos.replace("</", r"<\/"))


def main() -> None:
    PAGINA.write_text(construir(PLANTILLA.read_text(encoding="utf-8"), SALIDA.read_text(encoding="utf-8")), encoding="utf-8")
    print(PAGINA, f"{PAGINA.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
