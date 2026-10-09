"""SIMEL (MTESS/INE/OIT): tablas del Observatorio Laboral vía su API SDMX abierta (141 tablas, ver docs/simel_tablas.md).

Se bajan solo las tablas útiles para TAPE: establecimientos y puestos inscritos (registro administrativo),
formación profesional (SINAFOCAL, SNPP) e informalidad por departamento. Salida: data/raw/simel/<id>.csv.
Licencia por confirmar en el portal.
"""
from __future__ import annotations

import requests

from .comun import CABECERAS, RAW, anotar, sha256_archivo

API = "https://sdmx.simel.mtess.gov.py/rest"
AGENCIA = "PY110"
FORMATO_CSV = "application/vnd.sdmx.data+csv;version=1.0.0"
TABLAS = [
    "DF_ESTNB_TIPEST_ECO", "DF_ESTNB_AREAREF_TIPEST", "DF_PUESTONB_TIPEST_ECO", "DF_PUESTONB_AREAREF_TIPEST",
    "DF_AFSINANB_AREAREF_ECO", "DF_AFSNPPNB_FLIAPRO", "DF_MATRNB_AREAREF_SEXO", "DF_CERSNPP_AREAREF_SEXO",
    "DF_INFORNAC_AREAREF", "DF_INFORPRIV_AREAREF",
]


def url_datos(tabla: str, version: str = "1.0") -> str:
    """URL de la API SDMX para todos los datos de una tabla."""
    return f"{API}/data/{AGENCIA},{tabla},{version}/all"


def descargar_tabla(tabla: str) -> None:
    destino = RAW / "simel" / f"{tabla}.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        print(f"ya estaba: simel/{destino.name}")
        return
    url = url_datos(tabla)
    r = requests.get(url, headers={**CABECERAS, "Accept": FORMATO_CSV}, timeout=180)
    r.raise_for_status()
    if "csv" not in r.headers.get("Content-Type", "").lower():
        raise RuntimeError(f"{url} no devolvió CSV ({r.headers.get('Content-Type')})")
    destino.write_bytes(r.content)
    anotar(destino, url, len(r.content), sha256_archivo(destino))
    print(f"bajado: simel/{destino.name} ({len(r.content) / 1e3:.0f} KB)")


def main() -> None:
    for tabla in TABLAS:
        descargar_tabla(tabla)


if __name__ == "__main__":
    main()
