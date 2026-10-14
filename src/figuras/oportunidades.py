"""Figura de oportunidades de Paraguay: cercanía (densidad) contra complejidad (PCI) de los productos candidatos, con el tamaño dado por la ganancia de complejidad (COG).

Uso: uv run python -m src.figuras.oportunidades
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.modelos.logit_nacional import MODELO, RAIZ
from src.modelos.oportunidades import CUANTIL_CERCANO, PCI_COMPLEJO

COLORES = {"cercano y complejo": "#2a7f62", "cercano y simple": "#d08c1f", "lejano y complejo": "#3a6ea5", "lejano y simple": "#b8c2c8"}
SALIDA = RAIZ / "docs" / "figuras" / "oportunidades_PRY_2024.png"


def corto(s: str, n: int = 30) -> str:
    s = str(s).split(":")[0]
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> None:
    d = pd.read_csv(MODELO / "oportunidades_PRY_2024.csv", dtype={"hs4": str})
    corte = d.densidad.quantile(CUANTIL_CERCANO)
    fig, ax = plt.subplots(figsize=(11.5, 7.8))
    for cuad, col in COLORES.items():
        g = d[d.cuadrante == cuad]
        ax.scatter(g.densidad, g.pci, s=14 + 260 * g.cog.clip(lower=0), color=col, alpha=0.7, edgecolor="white", linewidth=0.5, label=f"{cuad} ({len(g)})")
    ax.axvline(corte, color="#555", lw=0.8, ls="--")
    ax.axhline(PCI_COMPLEJO, color="#555", lw=0.8, ls="--")
    desplazamientos = [(8, 16), (10, -22), (-72, 22), (12, 40), (14, -40), (-90, -8)]  # evita que se pisen las etiquetas del racimo
    for r, dx in zip(d[d.cuadrante == "cercano y complejo"].nlargest(6, "puntaje").itertuples(), desplazamientos, strict=False):
        ax.annotate(corto(r.nombre), (r.densidad, r.pci), xytext=dx, textcoords="offset points", fontsize=8, arrowprops={"arrowstyle": "-", "color": "#888", "lw": 0.6})
    ax.set_xlabel("Cercanía a lo que Paraguay ya exporta (densidad)")
    ax.set_ylabel("Complejidad del producto (PCI, Atlas)")
    ax.set_title("Paraguay 2024: productos candidatos según cercanía y complejidad\ntamaño del punto = ganancia de complejidad (COG)", loc="left", fontsize=12)
    ax.legend(frameon=False, loc="lower right", markerscale=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(SALIDA, dpi=150)
    print(SALIDA)


if __name__ == "__main__":
    main()
