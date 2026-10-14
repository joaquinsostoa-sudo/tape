"""Reservas probadas de petróleo, gas y carbón por país (Energy Institute, Statistical Review of World Energy), republicadas por Our World in Data.

Insumo de la dotación de recursos naturales (prueba de corte transversal, `docs/resultado_presente.md`). Una dotación física, no una renta:
las rentas de recursos de WDI son valor de producción y serían circulares con las exportaciones. Los minerales (USGS, Mineral Commodity
Summaries) no se bajan solos: ScienceBase bloquea el acceso automático; ver `data/raw/usgs_mcs/README.md`.
Licencia: CC BY 4.0 de Our World in Data; los datos de origen son del Energy Institute (confirmar condiciones de reutilización antes de publicar).
"""
from .comun import descargar

BASE = "https://ourworldindata.org/grapher"
ARCHIVOS = {  # nombre local -> identificador del gráfico de Our World in Data
    "petroleo_reservas_probadas.csv": "oil-proved-reserves",
    "gas_reservas_probadas.csv": "natural-gas-proved-reserves",
    "carbon_reservas_probadas.csv": "coal-proved-reserves",
}


def main() -> None:
    for nombre, grafico in ARCHIVOS.items():
        try:
            descargar(f"{BASE}/{grafico}.csv?v=1&csvType=full&useColumnShortNames=true", "reservas_energia", nombre)
        except Exception as e:  # noqa: BLE001  (un gráfico puede no existir: se informa y se sigue)
            print(f"no se pudo bajar {nombre}: {e}")


if __name__ == "__main__":
    main()
