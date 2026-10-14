"""Infografía: ¿qué dotaciones acompañan a cada tipo de producto? (2015)

Explica con un ejemplo visual cómo se arma una celda (144 países en tres grupos según su tierra cultivable, cuántos tienen ventaja en primarios agropecuarios y la
diferencia), da la guía de colores, muestra el cuadro de bloques × dotaciones con los casos clave numerados, el tercio de Paraguay y el PIB per cápita de referencia.
Lee `data/model/bloques_dotaciones_2015.csv`, `bloques_pib_2015.csv` y `bloques_paises_2015.csv` (de `src.modelos.bloques_dotaciones`).
Todo se ubica en pulgadas desde la esquina inferior izquierda, para que los círculos sean redondos y los textos no se pisen.

Uso: uv run python -m src.figuras.bloques_infografia
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

from src.modelos.bloques_dotaciones import BLOQUES, DOTACIONES
from src.modelos.logit_nacional import MODELO, RAIZ

AZUL, NARANJA, NEUTRO, TINTA, GRIS = "#1f5f99", "#b5541c", "#eeeeee", "#1d1d1d", "#666666"
CMAP = LinearSegmentedColormap.from_list("div", [NARANJA, NEUTRO, AZUL])
W, H = 14.5, 18.3
FILAS = {  # bloque -> (nombre, ejemplos)
    "primarios_agropecuarios": ("Primarios agropecuarios", "soja, carne, cereales, frutas"),
    "minerales_y_energia": ("Minerales y energía", "petróleo, gas, carbón, metales"),
    "manufacturas_agropecuarias": ("Manufacturas agropecuarias", "alimentos procesados, aceites, cuero"),
    "manufacturas_de_minerales": ("Manufacturas de minerales", "química básica, cemento, vidrio"),
    "manufactura_liviana": ("Manufactura liviana", "textiles, confección, calzado, muebles"),
    "manufactura_pesada_media_tec": ("Pesada y tecnología media", "autos, maquinaria, acero, plásticos"),
    "manufactura_alta_tec": ("Alta tecnología", "electrónica, farmacéutica, aeronáutica"),
}
COLUMNAS = {
    "log_tierra": "Tierra\ncultivable", "log_agua": "Agua\ndulce", "l_petroleo": "Reservas\npetróleo", "l_gas": "Reservas\ngas", "l_carbon": "Reservas\ncarbón",
    "riqueza_mineral": "Reservas\nminerales", "hc": "Capital\nhumano", "log_capital_trabajador": "Capital por\ntrabajador", "menos_log_precio": "Electricidad\nbarata",
    "lpi": "Logística\n(LPI)", "pib_pc_ppa": "PIB per\ncápita",
}
GRUPOS_COLUMNAS = [("RECURSOS NATURALES", 0, 5), ("CAPACIDADES Y COSTOS", 6, 9), ("REFERENCIA", 10, 10)]
CASOS = [  # (número, celdas (bloque, dotación), trazo, mensaje)
    (1, [("primarios_agropecuarios", "log_tierra"), ("primarios_agropecuarios", "log_agua")], "-",
     "Más tierra y más agua dulce → más países con ventaja en primarios agropecuarios (+40 y +22 puntos)."),
    (2, [("minerales_y_energia", "l_petroleo"), ("minerales_y_energia", "l_gas")], "-",
     "Reservas de petróleo y gas → ventaja en minerales y energía (+52 y +50): el recurso explica su bloque."),
    (3, [("manufactura_pesada_media_tec", c) for c in ("hc", "log_capital_trabajador", "lpi")], "-",
     "Capital humano, capital por trabajador y logística → manufactura pesada (+45, +43 y +45), pero el ingreso hace lo mismo (+45)."),
    (4, [(b, c) for b in ("manufacturas_agropecuarias", "manufactura_liviana") for c in ("l_petroleo", "l_gas")], "-",
     "Naranja: con petróleo y gas se destaca menos en alimentos procesados y manufactura liviana (el petróleo domina las exportaciones)."),
    (5, [("manufactura_liviana", c) for c in ("hc", "log_capital_trabajador")], "--",
     "Manufactura liviana: sin patrón claro; tener poco capital por trabajador («trabajo abundante») no la explica por sí solo."),
]


class Lienzo:
    """Figura con utilidades para ubicar textos y formas en pulgadas desde la esquina inferior izquierda."""

    def __init__(self, w: float = W, h: float = H) -> None:
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=(w, h), facecolor="white")

    def t(self, x: float, y: float, s: str, **kw):
        kw.setdefault("color", TINTA)
        return self.fig.text(x / self.w, y / self.h, s, **kw)

    def caja(self, x: float, y: float, w: float, h: float, fc="#f6f6f6", ec="#d0d0d0", lw=1.0, r=0.1):
        self.fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw, transform=self.fig.dpi_scale_trans))

    def circulo(self, x: float, y: float, r: float, **kw):
        self.fig.add_artist(Circle((x, y), r, transform=self.fig.dpi_scale_trans, **kw))

    def linea(self, x0: float, y0: float, x1: float, y1: float, color="#999999", lw=1.2):
        self.fig.add_artist(plt.Line2D([x0 / self.w, x1 / self.w], [y0 / self.h, y1 / self.h], color=color, lw=lw, transform=self.fig.transFigure))

    def ejes(self, x: float, y: float, w: float, h: float):
        return self.fig.add_axes([x / self.w, y / self.h, w / self.w, h / self.h])


def seccion_ejemplo(L: Lienzo, tabla: pd.DataFrame, top: float, alto: float) -> None:
    yb, x0, ancho = top - alto, 0.35, W - 0.7
    L.caja(x0, yb, ancho, alto)
    f = tabla[(tabla.dotacion == "log_tierra") & (tabla.bloque == "primarios_agropecuarios")].iloc[0]
    n = int(f.n_bajo)
    L.t(0.6, yb + alto - 0.2, "Cómo se arma una celda — ejemplo: tierra cultivable × primarios agropecuarios", fontsize=13, fontweight="bold", va="top")
    L.t(0.6, yb + alto - 0.72, "Se ordenan los 144 países por su tierra cultivable por persona y se parten en tres grupos de 48.\n"
        "Cada punto es un país: lleno si tiene ventaja en ese bloque (RCA ≥ 1), vacío si no la tiene.", fontsize=10.8, va="top", linespacing=1.55)
    datos = [("1.er tercio: POCA tierra", f.pct_bajo), ("2.º tercio: tierra MEDIA", f.pct_medio), ("3.er tercio: MUCHA tierra", f.pct_alto)]
    for g, (titulo, pct) in enumerate(datos):
        k = round(pct / 100 * n)
        xg = 0.6 + g * 2.95
        L.t(xg, yb + 2.62, titulo, fontsize=11, fontweight="bold", va="center")
        for i in range(n):
            fila, col = divmod(i, 12)
            L.circulo(xg + 0.09 + col * 0.2, yb + 2.2 - fila * 0.2, 0.072, fc=AZUL if i < k else "white", ec=AZUL if i < k else "#b0b0b0", lw=1.1)
        L.t(xg, yb + 1.22, f"{k} de {n} = {pct:.0f} %", fontsize=13, fontweight="bold", color=AZUL, va="center")
    L.t(0.6, yb + 0.58, "La celda de la tabla es la diferencia entre el 3.º y el 1.er grupo:", fontsize=11, va="center")
    L.t(6.05, yb + 0.58, f"{f.pct_alto:.0f} % − {f.pct_bajo:.0f} % =", fontsize=15, fontweight="bold", va="center")
    L.caja(7.95, yb + 0.37, 1.4, 0.42, fc=CMAP(0.5 + f.dif_alto_bajo / 120), ec="none", r=0.07)
    L.t(8.65, yb + 0.58, f"+{f.dif_alto_bajo:.0f} puntos", fontsize=12.5, fontweight="bold", color="white", ha="center", va="center")
    L.t(0.6, yb + 0.2, "Son 40 puntos de diferencia entre dos porcentajes; no es un aumento del 40 %.", fontsize=9.6, color=GRIS, va="center")
    # guía de colores
    xk = 9.85
    L.linea(xk - 0.25, yb + 0.2, xk - 0.25, yb + alto - 0.2)
    L.t(xk, yb + alto - 0.2, "Cómo leer los colores", fontsize=13, fontweight="bold", va="top")
    ax = L.ejes(xk, yb + 2.68, 3.95, 0.3)
    ax.imshow(np.linspace(-1, 1, 256)[None, :], cmap=CMAP, aspect="auto")
    ax.axis("off")
    ax.set_zorder(10)
    L.t(xk, yb + 2.5, "NARANJA", fontsize=10.5, fontweight="bold", color=NARANJA, va="top")
    L.t(xk, yb + 2.27, "menos países con\nventaja entre los\nmás dotados", fontsize=9.6, color=NARANJA, va="top", linespacing=1.4)
    L.t(xk + 3.95, yb + 2.5, "AZUL", fontsize=10.5, fontweight="bold", color=AZUL, va="top", ha="right")
    L.t(xk + 3.95, yb + 2.27, "más países con\nventaja entre los\nmás dotados", fontsize=9.6, color=AZUL, va="top", ha="right", linespacing=1.4)
    L.t(xk + 1.975, yb + 2.4, "gris: sin\ndiferencia", fontsize=9.6, color=GRIS, va="top", ha="center", linespacing=1.4)
    L.t(xk, yb + 1.3, "•  junto al número: poco probable\n    que sea azar (p < 0,05).", fontsize=9.8, va="top", linespacing=1.45)
    L.t(xk, yb + 0.85, "Ventaja: el bloque pesa más en las\nexportaciones del país que en el\ncomercio mundial (RCA ≥ 1).", fontsize=9.8, color=GRIS, va="top", linespacing=1.45)


def cuadro(L: Lienzo, tabla: pd.DataFrame, pib: pd.Series, pry: pd.Series, top: float):
    fila, ancho_col, izq = 0.74, 0.79, 3.7
    alto, ancho = 7 * fila, 11 * ancho_col
    yb = top - alto
    ax = L.ejes(izq, yb, ancho, alto)
    m = tabla.pivot(index="bloque", columns="dotacion", values="dif_alto_bajo").reindex(index=BLOQUES, columns=list(DOTACIONES))
    p = tabla.pivot(index="bloque", columns="dotacion", values="p_fisher").reindex(index=BLOQUES, columns=list(DOTACIONES))
    ax.imshow(m.to_numpy(dtype=float), cmap=CMAP, vmin=-60, vmax=60, aspect="auto")
    ax.set_xticks(np.arange(-0.5, 11, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 7, 1), minor=True)
    ax.grid(which="minor", color="white", lw=2.2)
    ax.tick_params(which="both", length=0)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(7):
        for j in range(11):
            v = m.iat[i, j]
            v = 0.0 if abs(v) < 0.5 else v
            ax.text(j, i, f"{v:+.0f}" + ("•" if p.iat[i, j] < 0.05 else ""), ha="center", va="center", fontsize=11.5, fontweight="bold" if abs(v) >= 30 else "normal",
                    color="white" if abs(v) > 33 else TINTA)
    for i, b in enumerate(BLOQUES):
        nombre, ej = FILAS[b]
        yc = top - (i + 0.5) * fila
        L.t(izq - 0.12, yc + 0.11, nombre, ha="right", va="center", fontsize=11.2, fontweight="bold")
        L.t(izq - 0.12, yc - 0.15, ej, ha="right", va="center", fontsize=8.7, color=GRIS)
        L.t(izq + ancho + 0.2, yc, f"{pib[b] / 1000:.1f}", ha="left", va="center", fontsize=12, fontweight="bold")
    for j, c in enumerate(DOTACIONES):
        L.t(izq + (j + 0.5) * ancho_col, top + 0.07, COLUMNAS[c], ha="center", va="bottom", fontsize=8.9, linespacing=1.15)
    for nombre, a, b in GRUPOS_COLUMNAS:
        L.linea(izq + (a + 0.06) * ancho_col, top + 0.55, izq + (b + 0.94) * ancho_col, top + 0.55, color="#888888", lw=1.5)
        L.t(izq + (a + b + 1) / 2 * ancho_col, top + 0.6, nombre, ha="center", va="bottom", fontsize=9.4, fontweight="bold", color=GRIS)
    L.t(izq + ancho + 0.2, top + 0.07, "PIB per cápita\nmediano de los\npaíses con ventaja\n(miles de USD)", ha="left", va="bottom", fontsize=8.8, linespacing=1.2)
    yp = yb - 0.42
    L.t(izq - 0.12, yp, "Paraguay está en el tercio…", ha="right", va="center", fontsize=10.8, fontweight="bold")
    estilo = {"alto": ("#1d1d1d", "white", "ALTO"), "medio": ("#a3a3a3", "white", "MEDIO"), "bajo": ("#e4e4e4", "#333333", "BAJO")}
    for j, c in enumerate(DOTACIONES):
        fc, tc, txt = estilo[pry[f"tercil_{c}"]]
        L.caja(izq + j * ancho_col + 0.05, yp - 0.15, ancho_col - 0.1, 0.3, fc=fc, ec="none", r=0.06)
        L.t(izq + (j + 0.5) * ancho_col, yp, txt, ha="center", va="center", fontsize=8.8, fontweight="bold", color=tc)
    L.t(izq + ancho + 0.2, yp, "Paraguay: 14,4", ha="left", va="center", fontsize=11, fontweight="bold")
    return ax, yp - 0.15


def marcar_casos(ax) -> None:
    ib, jc = {b: i for i, b in enumerate(BLOQUES)}, {c: j for j, c in enumerate(DOTACIONES)}
    for n, celdas, trazo, _ in CASOS:
        for b, c in celdas:
            ax.add_patch(Rectangle((jc[c] - 0.47, ib[b] - 0.47), 0.94, 0.94, fill=False, ec=TINTA, lw=2.6, ls=trazo))
        b0, c0 = min(celdas, key=lambda bc: (ib[bc[0]], jc[bc[1]]))
        ax.text(jc[c0] - 0.5, ib[b0] - 0.5, str(n), ha="center", va="center", fontsize=10, fontweight="bold", color="white", zorder=10, clip_on=False,
                bbox={"boxstyle": "circle,pad=0.28", "fc": TINTA, "ec": "white", "lw": 1.5})


def seccion_lectura(L: Lienzo, top: float, alto: float) -> None:
    yb, x0, ancho = top - alto, 0.35, W - 0.7
    L.caja(x0, yb, ancho, alto)
    L.t(0.6, top - 0.2, "Qué se ve en la tabla (los números de los recuadros)", fontsize=13, fontweight="bold", va="top")
    for k, (n, _, _, msg) in enumerate(CASOS):
        y = top - 0.85 - k * 0.4
        L.circulo(0.78, y, 0.14, fc=TINTA, ec="none")
        L.t(0.78, y, str(n), fontsize=10.5, fontweight="bold", color="white", ha="center", va="center")
        L.t(1.1, y, msg, fontsize=11.2, va="center")
    L.linea(0.6, yb + 1.3, W - 0.6, yb + 1.3, color="#d0d0d0")
    L.t(0.6, yb + 0.65, "Paraguay: RCA de 13 en primarios agropecuarios (3.º del mundo); tierra, agua y electricidad barata en el tercio ALTO, poco de reservas.\n"
        "No tiene ventaja en manufactura pesada ni en alta tecnología:\nsu capital humano, su capital por trabajador y su logística están en el tercio MEDIO.",
        fontsize=10.8, fontweight="bold", color=AZUL, va="center", linespacing=1.55)


def main() -> None:
    tabla = pd.read_csv(MODELO / "bloques_dotaciones_2015.csv")
    pib = pd.read_csv(MODELO / "bloques_pib_2015.csv").set_index("bloque").pib_mediano_con
    pry = pd.read_csv(MODELO / "bloques_paises_2015.csv", index_col=0).loc["PRY"]
    L = Lienzo()
    L.t(0.35, H - 0.25, "¿Qué dotaciones acompañan a cada tipo de producto?", fontsize=23, fontweight="bold", va="top")
    L.t(0.35, H - 0.95, "144 países, 2015. Se compara la dotación de cada país (tierra, reservas, capital humano…) con los tipos de producto en los que tiene ventaja comparativa.\n"
        "Es una descripción, no una prueba de causas: las dotaciones y el ingreso suelen ir juntos.", fontsize=11.5, color=GRIS, va="top", linespacing=1.55)
    seccion_ejemplo(L, tabla, top=H - 1.75, alto=3.95)
    L.t(0.35, H - 6.0, "La tabla completa: cada celda se lee igual que el ejemplo (tercio más dotado menos tercio menos dotado, en puntos porcentuales)", fontsize=12.5,
        fontweight="bold", va="top")
    ax, base = cuadro(L, tabla, pib, pry, top=H - 7.2)
    marcar_casos(ax)
    seccion_lectura(L, top=base - 0.45, alto=4.0)
    y_pie = base - 0.45 - 4.0 - 0.12
    L.t(0.35, y_pie, "Fuentes: BACI (comercio), Banco Mundial (WDI), Penn World Table, USGS y Energy Institute (reservas), clasificación tecnológica de Lall (2000) llevada a HS4 (docs/clasificacion_lall.md).\n"
        "La versión que compara países del mismo nivel de ingreso, para separar dotación y desarrollo, está en bloques_dotaciones_2015_detalle.png (tiene pocos países por celda y es más ruidosa).",
        fontsize=8.8, color=GRIS, va="top", linespacing=1.5)
    destino = RAIZ / "docs" / "figuras" / "bloques_dotaciones_2015.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    L.fig.savefig(destino, dpi=130, facecolor="white")
    print(destino)


if __name__ == "__main__":
    main()
