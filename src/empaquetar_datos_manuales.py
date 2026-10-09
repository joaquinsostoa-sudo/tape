"""Arma TAPE_datos_manuales.zip: los archivos de data/raw/ que NO se bajan con `src.descargas.todas`.

Uso: `uv run python -m src.empaquetar_datos_manuales` (deja el zip junto a la carpeta del repositorio).
Quedan fuera los README y manifiestos (ya están en Git), los `.txt` derivados y las copias previas
(`ephc/2022_sitio_previo/`). La lista de carpetas es la tabla de `docs/COLABORACION.md`.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
DESTINO = RAIZ.parent / "TAPE_datos_manuales.zip"
MANUALES = ["aneaes", "bcp_credito", "bcp_cuentas_nacionales", "bcp_cuentas_regionales", "censo_agropecuario",
            "ephc", "mec_escuelas", "mic_mapa", "mic_maquila", "mip_cepal_oit", "pwt"]
EXCLUIR_NOMBRES = {"README.md", "MANIFEST.json"}
EXCLUIR_EXTENSIONES = {".part", ".txt"}
EXCLUIR_CARPETAS = {"2022_sitio_previo"}
LEEME = """TAPE - datos manuales
=====================
Descomprimir ESTE zip en la raiz del repositorio TAPE (la carpeta que contiene data/, src/, docs/).
Los archivos quedan en data/raw/<fuente>/. Despues:

    uv run python -m src.descargas.todas     (BACI, Atlas, WDI, concordancias, limites y SIMEL: baja ~4 GB)
    uv run python -m src.reconstruir_todo
    uv run pytest

Detalle de cada archivo y de su origen: docs/COLABORACION.md y el README de cada carpeta data/raw/<fuente>/.
No contiene datos personales (el registro de titulos del MEC no esta incluido).
Atencion: los JSON de data/raw/mic_mapa/ vienen de un visor publico del MIC sin licencia declarada;
son datos provisorios de uso interno.
"""


def seleccionar(raw: Path = RAW, carpetas: list[str] = MANUALES) -> list[Path]:
    """Archivos a empaquetar, en orden estable."""
    salida = []
    for carpeta in carpetas:
        for f in sorted((raw / carpeta).rglob("*")):
            rel = f.relative_to(raw / carpeta)
            if not f.is_file() or f.name in EXCLUIR_NOMBRES or f.suffix in EXCLUIR_EXTENSIONES:
                continue
            if EXCLUIR_CARPETAS & set(rel.parts):
                continue
            salida.append(f)
    return salida


def main() -> None:
    archivos = seleccionar()
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in archivos:
            z.write(f, f.relative_to(RAIZ).as_posix())
        z.writestr("LEEME.txt", LEEME)
    with zipfile.ZipFile(DESTINO) as z:
        malo = z.testzip()
    print(f"{DESTINO} ({DESTINO.stat().st_size / 1e6:.1f} MB), {len(archivos)} archivos; "
          f"integridad: {malo or 'ok'}")


if __name__ == "__main__":
    main()
