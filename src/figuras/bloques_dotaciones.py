"""Figura: diferencia en el % de países con ventaja (RCA ≥ 1) entre el tercil alto y el bajo de cada dotación, por bloque de productos (2015).

Dos paneles: sin controles y dentro de terciles de ingreso (arriba contra abajo de la mediana). Azul = más países con ventaja entre los más dotados;
naranja = menos; gris claro = cerca de cero. Se marca con un punto la diferencia con p de Fisher < 0,05 (solo el panel sin controles). Bajo cada columna, el tercil de Paraguay.

Uso: uv run python -m src.figuras.bloques_dotaciones
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from src.modelos.bloques_dotaciones import BLOQUES, DOTACIONES
from src.modelos.logit_nacional import MODELO, RAIZ

ETIQUETAS_BLOQUES = {
    "primarios_agropecuarios": "Primarios agropecuarios", "minerales_y_energia": "Minerales y energía", "manufacturas_agropecuarias": "Manufacturas agropecuarias",
    "manufacturas_de_minerales": "Manufacturas de minerales", "manufactura_liviana": "Manufactura liviana",
    "manufactura_pesada_media_tec": "Manufactura pesada y tec. media", "manufactura_alta_tec": "Manufactura de alta tecnología",
}
ETIQUETAS_DOT = {
    "log_tierra": "Tierra\ncultivable", "log_agua": "Agua\ndulce", "l_petroleo": "Reservas\npetróleo", "l_gas": "Reservas\ngas", "l_carbon": "Reservas\ncarbón",
    "riqueza_mineral": "Reservas\nminerales", "hc": "Capital\nhumano", "log_capital_trabajador": "Capital por\ntrabajador", "menos_log_precio": "Electricidad\nbarata",
    "lpi": "Logística\n(LPI)", "pib_pc_ppa": "PIB per cápita\n(referencia)",
}
COLOR_POS, COLOR_NEG, NEUTRO = "#1f5f99", "#b5541c", "#eeeeee"


def dibujar(ax, tabla: pd.DataFrame, valor: str, titulo: str, marcar: bool, paraguay: pd.Series | None) -> None:
    m = tabla.pivot(index="bloque", columns="dotacion", values=valor).reindex(index=BLOQUES, columns=list(DOTACIONES))
    p = tabla.pivot(index="bloque", columns="dotacion", values="p_fisher").reindex(index=BLOQUES, columns=list(DOTACIONES))
    cmap = LinearSegmentedColormap.from_list("div", [COLOR_NEG, NEUTRO, COLOR_POS])
    ax.imshow(m.to_numpy(dtype=float), cmap=cmap, vmin=-60, vmax=60, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m.iat[i, j]
            if np.isnan(v):
                continue
            v = 0.0 if abs(v) < 0.5 else v  # evita el «-0»
            ax.text(j, i, f"{v:+.0f}" + ("•" if marcar and p.iat[i, j] < 0.05 else ""), ha="center", va="center", fontsize=8.5,
                    color="white" if abs(v) > 35 else "#222222")
    ax.set_yticks(range(len(BLOQUES)), [ETIQUETAS_BLOQUES[b] for b in BLOQUES], fontsize=9)
    etiquetas = [ETIQUETAS_DOT[c] + (f"\nPRY: {paraguay[f'tercil_{c}']}" if paraguay is not None else "") for c in DOTACIONES]
    ax.set_xticks(range(len(DOTACIONES)), etiquetas, fontsize=8)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    ax.set_title(titulo, fontsize=10, loc="left", pad=38)
    for s in ax.spines.values():
        s.set_visible(False)


def main() -> None:
    tabla = pd.read_csv(MODELO / "bloques_dotaciones_2015.csv")
    pry = pd.read_csv(MODELO / "bloques_paises_2015.csv", index_col=0).loc["PRY"]
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 9.2))
    dibujar(axes[0], tabla, "dif_alto_bajo", "Sin controles: puntos porcentuales de diferencia entre el tercil alto y el bajo de cada dotación (• = p < 0,05)", True, pry)
    dibujar(axes[1], tabla, "dif_dentro_de_ingreso", "Dentro de terciles de ingreso: diferencia entre países por encima y por debajo de la mediana de la dotación", False, None)
    fig.suptitle("¿Qué proporción de países tiene ventaja comparativa en cada bloque de productos, según su dotación? (2015, 144 países)", fontsize=11.5, x=0.01, ha="left", y=0.995)
    fig.text(0.01, 0.005, "Ventaja = RCA del bloque ≥ 1. Bloques: clasificación tecnológica de Lall (2000) llevada a HS4. Azul: más países con ventaja entre los más dotados; naranja: menos. "
             "Descriptivo, sin causalidad.", fontsize=7.8, color="#444444")
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    destino = RAIZ / "docs" / "figuras" / "bloques_dotaciones_2015.png"
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=140)
    print(destino)


if __name__ == "__main__":
    main()
