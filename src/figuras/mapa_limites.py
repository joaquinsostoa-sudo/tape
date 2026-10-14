"""Figura del mapa de límites de Paraguay: densidad contra déficit ponderado de los productos cercanos no exportados, según su estado.

Uso: uv run python -m src.figuras.mapa_limites
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.modelos.logit_nacional import CLEAN, MODELO, RAIZ

COLORES = {"compatible": "#2a7f62", "déficit alto": "#d08c1f", "límite duro": "#b3392f", "sin dato confiable de reservas": "#7f7f7f"}
SALIDA = RAIZ / "docs" / "figuras" / "mapa_limites_PRY_2019.png"


def nombres() -> pd.Series:
    b = pd.read_csv(CLEAN / "puente_hs92_sector.csv", dtype=str)
    b["hs4"] = b.hs92.str[:4]
    b["v"] = pd.to_numeric(b.valor_mundial, errors="coerce").fillna(0)
    return b.sort_values("v", ascending=False).drop_duplicates("hs4").set_index("hs4").descripcion.str.split(":").str[0].str.slice(0, 28)


def main() -> None:
    t = pd.read_csv(MODELO / "mapa_limites_especifico_PRY_2019.csv", dtype={"hs4": str})
    q = t[t.cercano_no_exportado].copy()
    q["nombre"] = q.hs4.map(nombres())
    fig, ax = plt.subplots(figsize=(11, 7.5))
    for est, col in COLORES.items():
        g = q[q.estado == est]
        ax.scatter(g.deficit_ponderado, g.densidad, s=34, color=col, label=f"{est} ({len(g)})", alpha=0.85, edgecolor="white", linewidth=0.5)
    for r in q[q.estado == "compatible"].nlargest(10, "densidad").itertuples():
        ax.annotate(r.nombre, (r.deficit_ponderado, r.densidad), xytext=(5, 3), textcoords="offset points", fontsize=8)
    for r in q[q.estado.isin(["límite duro", "sin dato confiable de reservas"])].nlargest(6, "densidad").itertuples():
        ax.annotate(r.nombre, (r.deficit_ponderado, r.densidad), xytext=(5, -9), textcoords="offset points", fontsize=8, color="#555")
    ax.set_xlabel("Déficit ponderado por relevancia (puntos de percentil; menor = más compatible)")
    ax.set_ylabel("Densidad (cercanía a lo que ya exporta)")
    ax.set_title("Paraguay 2019: productos cercanos que todavía no exporta\nsegún su compatibilidad de dotaciones", loc="left", fontsize=12)
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(SALIDA, dpi=150)
    print(SALIDA)


if __name__ == "__main__":
    main()
