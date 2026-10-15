"""Figura de oportunidades de Paraguay: puntuación del modelo (cercanía) contra complejidad de los productos candidatos.

Panel A: complejidad intrínseca (PCI del Atlas). Panel B: complejidad relativa (salto respecto de los productos presentes más próximos). Tamaño del punto = ganancia de complejidad (COG).

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
COLORES_REL = {"cercano y sube": "#2a7f62", "cercano y no sube": "#d08c1f", "lejano y sube": "#3a6ea5", "lejano y no sube": "#b8c2c8"}
SALIDA = RAIZ / "docs" / "figuras" / "oportunidades_PRY_2024.png"


def corto(s: str, n: int = 30) -> str:
    s = str(s).split(":")[0]
    return s if len(s) <= n else s[: n - 1] + "…"


def panel(ax, d: pd.DataFrame, y: str, cuad: str, colores: dict[str, str], umbral_y: float, etiqueta_y: str, titulo: str, principal: str) -> None:
    corte = d.puntaje.quantile(CUANTIL_CERCANO)
    for nombre, col in colores.items():
        g = d[d[cuad] == nombre]
        ax.scatter(g.puntaje, g[y], s=12 + 220 * g.cog.clip(lower=0), color=col, alpha=0.7, edgecolor="white", linewidth=0.5, label=f"{nombre} ({len(g)})")
    ax.axvline(corte, color="#555", lw=0.8, ls="--")
    ax.axhline(umbral_y, color="#555", lw=0.8, ls="--")
    desplazamientos = [(8, 14), (10, -22), (-80, 18), (12, 36), (14, -38), (-96, -6)]
    for r, dx in zip(d[d[cuad] == principal].nlargest(6, "puntaje").itertuples(), desplazamientos, strict=False):
        ax.annotate(corto(r.nombre, 26), (r.puntaje, getattr(r, y)), xytext=dx, textcoords="offset points", fontsize=7.5, arrowprops={"arrowstyle": "-", "color": "#888", "lw": 0.6})
    ax.set_xlabel("Cercanía: puntuación del modelo (densidad + propensión del producto)")
    ax.set_ylabel(etiqueta_y)
    ax.set_title(titulo, loc="left", fontsize=11)
    ax.legend(frameon=False, loc="upper right", fontsize=8, markerscale=0.6)
    ax.spines[["top", "right"]].set_visible(False)


def main() -> None:
    d = pd.read_csv(MODELO / "oportunidades_PRY_2024.csv", dtype={"hs4": str})
    fig, (a, b) = plt.subplots(1, 2, figsize=(16, 7))
    panel(a, d, "pci", "cuadrante", COLORES, PCI_COMPLEJO, "Complejidad del producto (PCI, Atlas)", "A. Complejidad intrínseca", "cercano y complejo")
    panel(b, d, "salto", "cuadrante_relativo", COLORES_REL, 0.0, "Salto de complejidad frente a lo que Paraguay ya hace cerca", "B. Complejidad relativa (peldaño)", "cercano y sube")
    fig.suptitle("Paraguay 2024: productos candidatos según cercanía y complejidad (tamaño = ganancia de complejidad, COG)", x=0.01, ha="left", fontsize=12)
    fig.tight_layout()
    fig.savefig(SALIDA, dpi=140)
    print(SALIDA)


if __name__ == "__main__":
    main()
