"""Figura de la ficha de brechas de Paraguay para un producto (prototipo): trayectoria de Paraguay, quiénes producen hoy y en qué dotaciones está por debajo.

Usa `src.modelos.ficha_brechas`. Un punto de percentil es la posición de un país entre los países D8 del año (0 = el menos dotado, 100 = el más dotado).

Uso: uv run python -m src.figuras.ficha_brechas
"""
from __future__ import annotations

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.figuras.bloques_infografia import AZUL, GRIS, NARANJA, TINTA, Lienzo
from src.modelos.ficha_brechas import PRODUCTOS, ficha, trayectoria
from src.modelos.logit_nacional import CLEAN, MODELO, RAIZ, calcular_rca

W, H = 14.5, 11.9
NOMBRES = {"8544": "Arneses y cables aislados (HS 8544)", "2207": "Etanol (HS 2207)"}
NOTAS = {
    "8544": "Los arneses son ensamblaje intensivo en mano de obra y entraron con el régimen de maquila: ni los salarios ni el régimen están en las dotaciones. "
            "HS 8544 reúne los arneses (HS 854430) con otros cables aislados.",
    "2207": "El biodiesel no se puede separar a 4 dígitos (HS92), así que la ficha solo cubre el etanol (HS 2207). "
            "La tierra y el agua son recursos de las materias primas (caña, maíz); entre los países que producen etanol no son un requisito.",
}


def color_brecha(v: float) -> str:
    return NARANJA if v >= 10 else (AZUL if v <= -10 else GRIS)


def texto_brecha(v: float) -> str:
    if np.isnan(v):
        return "sin dato"
    return f"falta {v:.0f}" if v >= 10 else (f"sobra {-v:.0f}" if v <= -10 else "similar")


def dibujar(hs4: str, anio: int, expo: pd.DataFrame, dot: pd.DataFrame, pob: pd.DataFrame) -> str:
    f = ficha(expo, dot, pob, hs4, anio)
    tab = f["tabla"]
    L = Lienzo(W, H)
    L.t(0.35, H - 0.25, f"Ficha de brechas: {NOMBRES[hs4]}", fontsize=22, fontweight="bold", va="top")
    L.t(0.35, H - 0.85, f"¿En qué dotaciones está Paraguay por debajo de los países que ya producen esto? ({anio}; prototipo descriptivo, no una predicción)",
        fontsize=11.5, color=GRIS, va="top")
    # A. trayectoria de Paraguay
    top_a, alto_a = H - 1.35, 2.75
    L.caja(0.35, top_a - alto_a, 7.0, alto_a)
    L.t(0.6, top_a - 0.18, "Paraguay en este producto", fontsize=12.5, fontweight="bold", va="top")
    tr = trayectoria(expo, hs4)
    ax = L.ejes(0.75, top_a - alto_a + 0.55, 6.4, 1.6)
    ax.set_zorder(10)
    ax.patch.set_alpha(0)
    ax.bar(range(len(tr)), tr.exportaciones / 1000, color=[AZUL if r >= 1 else "#c9c9c9" for r in tr.rca], width=0.68)
    ymax = max(tr.exportaciones.max() / 1000, 1)
    for i, v in enumerate(tr.exportaciones / 1000):
        ax.text(i, v + ymax * 0.03, f"{v:,.0f}".replace(",", "."), ha="center", va="bottom", fontsize=8.6, color=TINTA)
    ax.set_xticks(range(len(tr)), [str(a) for a in tr.anio], fontsize=9)
    ax.set_yticks([])
    ax.set_ylim(0, ymax * 1.22)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    L.t(0.6, top_a - alto_a + 0.2, "Exportaciones, en millones de USD. Barra azul: Paraguay tiene ventaja (RCA ≥ 1); gris: todavía no.", fontsize=9, color=GRIS, va="center")
    # B. quién produce
    L.caja(7.55, top_a - alto_a, W - 7.9, alto_a)
    L.t(7.8, top_a - 0.18, f"Quién produce hoy ({anio})", fontsize=12.5, fontweight="bold", va="top")
    rca = calcular_rca(expo)
    r = rca[(rca.anio == anio) & (rca.hs4 == hs4) & rca.iso3.isin(f["productores"])].nlargest(10, "rca")
    L.t(7.8, top_a - 0.62, f"{f['n_productores']} países con ventaja sostenida (RCA ≥ 1). Los que más destacan:", fontsize=10.2, va="top")
    for i, (iso, v) in enumerate(zip(r.iso3, r.rca, strict=True)):
        col, fila = divmod(i, 5)
        L.t(7.85 + col * 3.1, top_a - 0.92 - fila * 0.24, f"{iso}   RCA {v:.1f}".replace(".", ","), fontsize=10, va="top")
    dens = f"{f['densidad']:.2f}".replace(".", ",")
    L.t(7.8, top_a - alto_a + 0.3, f"Cercanía de Paraguay al producto (densidad): {dens}; supera a la del {f['densidad_percentil']:.0f} % de los\n"
        f"productos que todavía no tiene. Referencias: {f['n_productores']} productores, {f['n_peers']} de ingreso parecido\n"
        f"y {f['n_vecinos']} productos vecinos. Confianza: {f['confianza']}.", fontsize=9.4, color=GRIS, va="center", linespacing=1.5)
    # C. brechas
    top_c, alto_c = top_a - alto_a - 0.25, 6.05
    L.caja(0.35, top_c - alto_c, W - 0.7, alto_c)
    L.t(0.6, top_c - 0.18, "Posición de Paraguay frente a quienes producen (percentil entre los países: 0 = el menos dotado, 100 = el más dotado)", fontsize=12.5, fontweight="bold", va="top")
    x0, ancho, y_top, fila_h = 3.55, 6.0, top_c - 1.8, 0.46
    ax = L.ejes(x0, y_top - fila_h * len(tab), ancho, fila_h * len(tab))
    ax.set_zorder(10)
    ax.patch.set_alpha(0)
    ax.set_xlim(0, 100)
    ax.set_ylim(len(tab), 0)
    for v in (0, 25, 50, 75, 100):
        ax.axvline(v, color="#e2e2e2", lw=1, zorder=0)
    for i, fila in tab.iterrows():
        ax.plot([fila.paraguay, fila.productores], [i + 0.5, i + 0.5], color="#d4d4d4", lw=3, zorder=1, solid_capstyle="round")
        ax.scatter(fila.vecindad, i + 0.5, marker="^", s=70, facecolor="white", edgecolor=TINTA, lw=1.4, zorder=3)
        ax.scatter(fila.productores_ingreso_parecido, i + 0.5, marker="s", s=62, color="#8a8a8a", zorder=3)
        ax.scatter(fila.productores, i + 0.5, marker="D", s=70, color=TINTA, zorder=4)
        ax.scatter(fila.paraguay, i + 0.5, marker="o", s=150, color=AZUL, edgecolor="white", lw=1.5, zorder=5)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100], ["0", "25", "50", "75", "100"], fontsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    columnas = (("brecha_productores", x0 + ancho + 0.3, "frente a todos\nlos productores"),
                ("brecha_productores_ingreso_parecido", x0 + ancho + 1.9, "frente a productores\nde ingreso parecido"),
                ("brecha_vecindad", x0 + ancho + 3.5, "frente a los\nproductos vecinos"))
    for i, fila in tab.iterrows():
        yc = y_top - (i + 0.5) * fila_h
        L.t(x0 - 0.15, yc, fila.dotacion, ha="right", va="center", fontsize=11, fontweight="bold" if i < len(tab) - 1 else "normal", color=TINTA if i < len(tab) - 1 else GRIS)
        for campo, xx, _ in columnas:
            L.t(xx, yc, texto_brecha(fila[campo]), fontsize=11, fontweight="bold", color=color_brecha(fila[campo]), va="center")
    for _, xx, t in columnas:
        L.t(xx, y_top + 0.08, t, fontsize=9.3, color=GRIS, va="bottom", linespacing=1.3)
    L.t(x0 + ancho + 0.3, y_top + 0.62, "Brecha de Paraguay (puntos de percentil)", fontsize=10.2, fontweight="bold", va="bottom")
    yl = top_c - 0.75
    for xx, marcador, txt, rel, borde in ((x0, "o", "Paraguay", AZUL, AZUL), (x0 + 1.45, "D", "productores", TINTA, TINTA),
                                         (x0 + 3.0, "s", "productores de ingreso parecido", "#8a8a8a", "#8a8a8a"), (x0 + 5.85, "^", "productos vecinos", "white", TINTA)):
        L.fig.add_artist(plt.Line2D([xx / W], [yl / H], marker=marcador, markersize=9, linestyle="none", transform=L.fig.transFigure,
                                    markerfacecolor=rel, markeredgecolor=borde, markeredgewidth=1.4))
        L.t(xx + 0.17, yl, txt, fontsize=9.8, va="center")
    L.t(0.6, top_c - alto_c + 0.45, "Cómo leerlo: «falta 24» = Paraguay está 24 puntos de percentil por debajo de la mediana de los productores en esa dotación; «sobra» = está por encima (no es algo que le falte).\n"
        "Con ingreso parecido se compara con productores del mismo tercio de PIB per cápita que Paraguay, para separar la dotación del desarrollo general.",
        fontsize=9.8, va="center", linespacing=1.5)
    limites = ("Límites: " + NOTAS[hs4] + " Es un benchmark descriptivo: el backtest no mostró que las dotaciones predigan qué producto nuevo aparece; "
               "«falta» significa «está por debajo de los productores», no «con más de esto produciría».")
    L.t(0.35, top_c - alto_c - 0.18, "\n".join(textwrap.wrap(limites, 195)), fontsize=9, color=GRIS, va="top", linespacing=1.5)
    destino = RAIZ / "docs" / "figuras" / f"ficha_brechas_{hs4}.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    L.fig.savefig(destino, dpi=130, facecolor="white")
    return str(destino)


def main() -> None:
    expo = pd.read_parquet(MODELO / "exportaciones_hs4.parquet")
    dot = pd.read_parquet(CLEAN / "dotaciones.parquet")
    pob = pd.read_csv(CLEAN / "poblacion_pais.csv")
    for hs4 in PRODUCTOS:
        print(dibujar(hs4, 2015, expo, dot, pob))


if __name__ == "__main__":
    main()
