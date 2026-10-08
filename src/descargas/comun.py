"""Descarga reproducible a data/raw/<fuente>/: idempotente y con manifiesto (URL, fecha, tamaño, sha256)."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw"
CABECERAS = {"User-Agent": "TAPE-LabDE/0.1 (investigacion academica)"}
DATAVERSE = "https://dataverse.harvard.edu"


def sha256_archivo(ruta: Path, bloque: int = 1 << 20) -> str:
    """SHA-256 de un archivo, leído por bloques."""
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        while chunk := f.read(bloque):
            h.update(chunk)
    return h.hexdigest()


def tamano_remoto(url: str) -> int | None:
    """Tamaño en bytes según HEAD, o None si el servidor no lo informa."""
    try:
        r = requests.head(url, headers=CABECERAS, allow_redirects=True, timeout=60)
        return int(r.headers["Content-Length"]) if r.ok and "Content-Length" in r.headers else None
    except requests.RequestException:
        return None


def ya_descargado(destino: Path, esperado: int | None) -> bool:
    """True si el archivo existe y (cuando se conoce) su tamaño coincide con el remoto."""
    return destino.exists() and (esperado is None or destino.stat().st_size == esperado)


def anotar(destino: Path, url: str, nbytes: int, sha: str) -> None:
    carpeta = RAW / destino.relative_to(RAW).parts[0]
    ruta = carpeta / "MANIFEST.json"
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    datos[str(destino.relative_to(carpeta)).replace("\\", "/")] = {
        "url": url, "fecha_utc": datetime.now(UTC).strftime("%Y-%m-%d"),
        "bytes": nbytes, "sha256": sha,
    }
    ruta.write_text(json.dumps(datos, indent=1, ensure_ascii=False), encoding="utf-8")


def descargar(url: str, fuente: str, nombre: str, *, reintentos: int = 3) -> Path:
    """Baja `url` a data/raw/<fuente>/<nombre> (con subcarpetas si `nombre` las trae)."""
    destino = RAW / fuente / nombre
    destino.parent.mkdir(parents=True, exist_ok=True)
    if ya_descargado(destino, tamano_remoto(url)):
        print(f"ya estaba: {fuente}/{nombre}")
        return destino
    for intento in range(1, reintentos + 1):
        parcial = destino.with_name(destino.name + ".part")
        try:
            with requests.get(url, headers=CABECERAS, stream=True, timeout=120) as r:
                r.raise_for_status()
                with parcial.open("wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            parcial.replace(destino)
            break
        except requests.RequestException as e:
            print(f"intento {intento} falló para {nombre}: {e}")
            if intento == reintentos:
                raise
            time.sleep(5 * intento)
    sha = sha256_archivo(destino)
    anotar(destino, url, destino.stat().st_size, sha)
    print(f"bajado: {fuente}/{nombre} ({destino.stat().st_size / 1e6:.1f} MB)")
    return destino


def archivos_dataverse(respuesta: dict) -> dict[str, int]:
    """Del JSON de la API de Dataverse: {nombre de archivo: id} de la última versión."""
    return {f["dataFile"]["filename"]: f["dataFile"]["id"] for f in respuesta["data"]["files"]}


def listar_dataverse(doi: str) -> dict[str, int]:
    r = requests.get(
        f"{DATAVERSE}/api/datasets/:persistentId/versions/:latest",
        params={"persistentId": doi}, headers=CABECERAS, timeout=60)
    r.raise_for_status()
    return archivos_dataverse(r.json())


def descargar_dataverse(doi: str, fuente: str, subcarpeta: str = "", solo: list[str] | None = None) -> None:
    """Baja los archivos de un dataset de Dataverse (todos, o solo los nombres de `solo`)."""
    archivos = listar_dataverse(doi)
    faltan = set(solo or []) - set(archivos)
    if faltan:
        raise FileNotFoundError(f"{doi}: no están {sorted(faltan)}")
    for nombre, fid in archivos.items():
        if solo is None or nombre in solo:
            descargar(f"{DATAVERSE}/api/access/datafile/{fid}", fuente, f"{subcarpeta}{nombre}")
