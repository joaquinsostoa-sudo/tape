"""Reconstruye las tablas de data/clean y los puentes a partir de data/raw, en orden.

Uso: `uv run python -m src.reconstruir_todo`. Si falta un archivo de entrada (p. ej. un archivo manual que
no se descarga solo), el paso se salta y se informa cuál falta; los demás siguen.
Las descargas automáticas son aparte: `uv run python -m src.descargas.todas`.
"""
from __future__ import annotations

import importlib

PASOS = [
    "src.limpieza.bcp_pib33",
    "src.limpieza.bcp_cra",
    "src.limpieza.cnaep_ciiu",
    "src.limpieza.industrias_mic",
    "src.limpieza.aneaes",
    "src.limpieza.mic_ciudades",
    "src.limpieza.can_distrito",
    "src.limpieza.mic_red_electrica",
    "src.limpieza.mic_rutas",
    "src.limpieza.mic_polos",
    "src.limpieza.mic_aduanas",
    "src.limpieza.mic_salud",
    "src.puentes.clasificaciones_locales",
    "src.puentes.taxonomia_tape",
    "src.puentes.cnaep_sector",
    "src.puentes.mic_sector",
    "src.puentes.geoprocesar_industrias",
    "src.puentes.industrias_distrito_sector",
    "src.puentes.subestaciones_distrito",
    "src.puentes.rutas_distrito",
    "src.puentes.aduanas_distrito",
    "src.puentes.salud_distrito",
    "src.puentes.hs_sector",
    "src.puentes.doc_taxonomia",
]


def main() -> None:
    faltan: list[str] = []
    fallos: list[str] = []
    for nombre in PASOS:
        print(f"=== {nombre}")
        try:
            importlib.import_module(nombre).main()
        except FileNotFoundError as e:
            faltan.append(f"{nombre}: falta {e.filename}")
            print(f"  SALTADO: falta {e.filename}")
        except Exception as e:  # noqa: BLE001  (p. ej. un límite administrativo ausente lo reporta pyogrio)
            fallos.append(f"{nombre}: {type(e).__name__}: {e}")
            print(f"  FALLÓ: {type(e).__name__}: {e}")
    print("\nRESUMEN:", "todo reconstruido" if not (faltan or fallos) else "revisar lo de abajo")
    for f in faltan:
        print(" - falta entrada:", f)
    for f in fallos:
        print(" - falló:", f)
    if fallos:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
