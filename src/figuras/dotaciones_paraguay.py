"""Figura de control de la tarea 1.5: posición de Paraguay (percentil) en cada capa de dotaciones, 2000-2022.

Percentil entre los países con dato en ese año. Colores: las cuatro primeras posiciones de la paleta categórica
validada de la guía de visualización (validate_palette: pasa; contraste bajo en verde y amarillo, por eso cada línea
lleva etiqueta directa y los datos están en data/clean/dotaciones_cortes.csv).
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.limpieza.dotaciones import CAPAS, RAIZ, SALIDA

SALIDA_PNG = RAIZ / "docs" / "figuras" / "dotaciones_paraguay.png"
ETIQUETAS = {"capital_humano": "Capital humano", "credito": "Crédito privado", "energia": "Energía (precio bajo)",
             "logistica": "Logística (LPI)"}
COLORES = {"capital_humano": "#2a78d6", "credito": "#eb6834", "energia": "#1baf7a", "logistica": "#eda100"}
TINTA, TINTA_SUAVE, FONDO = "#0b0b0b", "#52514e", "#fcfcfb"


def dibujar(df: pd.DataFrame, destino=SALIDA_PNG) -> None:
    py = df[(df.iso3 == "PRY") & df.anio.between(2000, 2022)]
    fig, ax = plt.subplots(figsize=(9.2, 5.2), dpi=130, facecolor=FONDO)
    ax.set_facecolor(FONDO)
    ax.axhline(50, color="#c9c8c2", lw=1, ls=(0, (4, 3)), zorder=1)
    ax.text(2000.1, 51.5, "mediana de los países", fontsize=8.5, color=TINTA_SUAVE, va="bottom")
    finales = {}
    for capa in CAPAS:
        s = py.dropna(subset=[f"pct_{capa}"])
        ax.plot(s.anio, 100 * s[f"pct_{capa}"], color=COLORES[capa], lw=2, marker="o", ms=4, zorder=3,
                label=ETIQUETAS[capa])
        u = s.iloc[-1]
        finales[capa] = (u.anio, 100 * u[f"pct_{capa}"])
    # etiquetas directas al final de cada línea, separadas al menos 5 puntos de percentil para que no se pisen
    previo = -99.0
    for capa, (x, y) in sorted(finales.items(), key=lambda kv: kv[1][1]):
        ya = max(y, previo + 5.0)
        ax.annotate(ETIQUETAS[capa], (x, y), xytext=(x + 0.5, ya), textcoords="data", fontsize=9, color=TINTA,
                    va="center", arrowprops={"arrowstyle": "-", "color": "#b5b4ad", "lw": 0.7, "shrinkA": 0, "shrinkB": 3})
        previo = ya
    ax.set_ylim(0, 100)
    ax.set_xlim(1999.5, 2026.5)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100"], color=TINTA_SUAVE, fontsize=9)
    ax.set_xticks(range(2000, 2023, 2))
    ax.tick_params(axis="x", colors=TINTA_SUAVE, labelsize=9, length=0)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", color="#e7e6e1", lw=0.8, zorder=0)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    ax.set_ylabel("Percentil entre países con dato (100 = el mejor)", color=TINTA_SUAVE, fontsize=9)
    fig.suptitle("Paraguay tiene energía barata y está cerca de la mitad en las otras tres dotaciones", x=0.06, ha="left",
                 fontsize=13, fontweight="bold", color=TINTA, y=0.975)
    ax.set_title("Percentil por capa (100 = mejor). Energía: precio de la electricidad 2014-2019 aplicado a todos los años "
                 "(100 = el más barato).\nCapital humano: PWT, hasta 2019. Logística: LPI desde 2007, con la edición "
                 "arrastrada hasta la siguiente (los saltos son cambios de edición).",
                 loc="left", fontsize=8, color=TINTA_SUAVE, pad=8)
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=TINTA, ncol=2)
    fig.text(0.06, 0.012, "Fuentes: Penn World Table 10.01, WDI y Doing Business (Banco Mundial). Tarea 1.5 de TAPE (LabDE).",
             fontsize=8, color=TINTA_SUAVE)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, facecolor=FONDO)
    plt.close(fig)


def main() -> None:
    dibujar(pd.read_parquet(SALIDA))
    print("figura:", SALIDA_PNG)


if __name__ == "__main__":
    main()
