"""Figura del ejemplo de aplicación del capital humano: base contra formación específica para una industria que exige y una que no.

Cada punto es un distrito (tamaño = población). Eje horizontal: base (percentil del índice v2 a 30 km). Eje vertical: formación específica del sector (percentil del pool de graduados a 30 km).
Los distritos que hoy tienen la industria (mapa MIC) van marcados. Para la industria que exige, importa estar arriba a la derecha; para la que no exige, solo importa el eje horizontal.
Uso: uv run python -m src.figuras.ejemplo_ch
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from ..puentes.taxonomia_tape import RAIZ

SALIDA = RAIZ / "docs" / "figuras" / "ejemplo_ch_S40_S09.png"
GRIS = "#9aa3ad"
AZUL = "#1f5fbf"
TINTA = "#1d2733"
DESPLAZAMIENTO = {"Asunción": (-52, 4), "San Lorenzo": (6, -15), "Itauguá": (6, -17)}  # puntos de pantalla para que las etiquetas no se superpongan
ETIQUETAS = {"ASUNCION": "Asunción", "CIUDAD DEL ESTE": "Ciudad del Este", "ENCARNACION": "Encarnación", "CONCEPCION": "Concepción",
             "SAN LORENZO": "San Lorenzo", "VILLARRICA": "Villarrica", "PEDRO JUAN CABALLERO": "P. J. Caballero", "ITAUGUA": "Itauguá"}


def panel(ax, d: pd.DataFrame, titulo: str, exige: bool, ub: float, ue: float) -> None:
    d = d.dropna(subset=["p_base", "p_especifico"]).copy()
    hoy = d["industrias_hoy"] > 0
    tam = 12 + 280 * (d["poblacion"] / d["poblacion"].max()) ** 0.5
    ax.scatter(d.loc[~hoy, "p_base"], d.loc[~hoy, "p_especifico"], s=tam[~hoy], c=GRIS, alpha=0.55, linewidths=0)
    ax.scatter(d.loc[hoy, "p_base"], d.loc[hoy, "p_especifico"], s=tam[hoy], c=AZUL, alpha=0.9, edgecolors="white", linewidths=0.8)
    ax.axvline(ub, color=TINTA, lw=0.8, ls=":")
    ax.text(ub + 1, 3, "umbral de base", fontsize=7.5, color=TINTA)
    if exige:
        ax.axhline(ue, color=TINTA, lw=0.8, ls=":")
        ax.text(1, ue + 1.5, "umbral de formación específica", fontsize=7.5, color=TINTA)
        ax.text(ub + 2, ue + 14, "LISTA", fontsize=9, color=TINTA, weight="bold")
    else:
        ax.text(ub + 2, 96, "LISTA: solo cuenta la base", fontsize=8.5, color=TINTA, weight="bold")
    for _, r in d.iterrows():
        e = ETIQUETAS.get(str(r["distrito"]).upper())
        if e:
            ax.annotate(e, (r["p_base"], r["p_especifico"]), xytext=DESPLAZAMIENTO.get(e, (5, -9)), textcoords="offset points", fontsize=8, color=TINTA)
    ax.set_xlim(-3, 104)
    ax.set_ylim(-3, 104)
    ax.set_xlabel("Base de capital humano (percentil entre distritos)", fontsize=9)
    ax.set_title(titulo, fontsize=10.5, loc="left", color=TINTA)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.grid(color="#e6e9ee", lw=0.6)
    ax.set_axisbelow(True)


def main() -> None:
    a = pd.read_csv(RAIZ / "data" / "model" / "ejemplo_diagnostico_S40.csv")
    b = pd.read_csv(RAIZ / "data" / "model" / "ejemplo_diagnostico_S09.csv")
    fig, ejes = plt.subplots(1, 2, figsize=(12.5, 5.6), sharey=True)
    panel(ejes[0], a, "Electrónica y equipo eléctrico: EXIGE formación específica (NBER 0,44)", True, a["umbral_base"].iloc[0], a["umbral_especifico"].iloc[0])
    panel(ejes[1], b, "Frigoríficos: NO exige formación específica (NBER 0,16)", False, b["umbral_base"].iloc[0], b["umbral_especifico"].iloc[0])
    ejes[0].set_ylabel("Formación específica del sector (percentil del pool de graduados)", fontsize=9)
    fig.text(0.01, 0.005, "Azul: distritos con la industria hoy (mapa MIC). Tamaño = población. Pool a 30 km, sede principal. Umbrales: percentil 10 de los distritos que hoy tienen la industria (D31). Ilustración, no una predicción.",
             fontsize=8, color=TINTA)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SALIDA, dpi=140)
    print(SALIDA)


if __name__ == "__main__":
    main()
