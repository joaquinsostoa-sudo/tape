"""World Development Indicators por la API del Banco Mundial (un JSON por indicador y página)."""
from __future__ import annotations

import json
import time

import requests

from .comun import CABECERAS, RAW, anotar, sha256_archivo

INDICADORES = {
    "SE.TER.ENRR": "Matrícula terciaria (% bruto)",
    "SE.SEC.ENRR": "Matrícula secundaria (% bruto)",
    "FS.AST.PRVT.GD.ZS": "Crédito interno al sector privado (% PIB)",
    "FS.AST.DOMS.GD.ZS": "Crédito interno del sector financiero (% PIB)",
    "EG.USE.ELEC.KH.PC": "Consumo eléctrico (kWh per cápita)",
    "EG.ELC.ACCS.ZS": "Acceso a electricidad (% población)",
    "NE.TRD.GNFS.ZS": "Comercio (% PIB)",
    "LP.LPI.OVRL.XQ": "Índice de desempeño logístico (LPI), general",
    "NV.IND.MANF.ZS": "Valor agregado manufacturero (% PIB)",
    "IT.NET.USER.ZS": "Usuarios de internet (% población)",
    "AG.LND.ARBL.HA.PC": "Tierra arable (ha per cápita)",
    "NY.GDP.PCAP.PP.KD": "PIB per cápita, PPA (USD 2021)",
    "SP.POP.TOTL": "Población total",
}
BASE = "https://api.worldbank.org/v2/country/all/indicator"


def main() -> None:
    carpeta = RAW / "wdi"
    carpeta.mkdir(parents=True, exist_ok=True)
    for codigo in INDICADORES:
        pagina = 1
        while True:
            url = f"{BASE}/{codigo}?format=json&per_page=20000&date=1990:2025&page={pagina}"
            r = requests.get(url, headers=CABECERAS, timeout=120)
            r.raise_for_status()
            datos = r.json()
            destino = carpeta / f"wdi_{codigo}_p{pagina}.json"
            destino.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
            anotar(destino, url, destino.stat().st_size, sha256_archivo(destino))
            meta = datos[0]
            print(f"{codigo} p{pagina}/{meta['pages']} filas={meta['total']} actualizado={meta['lastupdated']}")
            if pagina >= int(meta["pages"]):
                break
            pagina += 1
            time.sleep(1)
        time.sleep(1)


if __name__ == "__main__":
    main()
