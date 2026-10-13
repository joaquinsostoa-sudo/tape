# Logit nacional con capas: primera corrida provisoria (2026-10-13)

**Provisorio.** Es la primera versión de la tarea 1.9 (`src/modelos/logit_nacional.py`). Los coeficientes son **asociaciones dentro de la muestra**, no causalidad ni predicción. No se usan para decidir qué capas entran al modelo final.

## Cómo se hizo
- **Datos:** `rca_matrix` de la base de Ever (foto de lectura, HS6, con todas las exportaciones de BACI), agregada a HS4 y recalculada sin la energía de Itaipú/Yacyretá (HS4 2716). Se usaron exportaciones de 1995 a 2020.
- **Modelo (D2 c):** `Pr(E=1) = Λ(α_ct + γ_pt + β d + Σ_k θ_k r_k a_k + Σ_k λ_k d r_k a_k)`. Efectos fijos de país-ventana y producto-ventana. Errores agrupados por país (`LogitEfectosFijos.errores_agrupados`).
- **Entrada (D7):** `RCA_t0 < 0,5` y `RCA_t0+5 ≥ 1`, un solo año. Ventanas 2000, 2005, 2010 y 2015. **El panel incluye los productos que el país no exportaba (RCA = 0)**: son el 22 % de las filas, con una tasa de entrada de 1,2 % (contra 2,6 % en los que ya exportaban algo).
- **Muestra (D8):** 112, 128, 141 y 144 países por ventana. **Se pierden países al exigir las cuatro capas**: quedan 61, 93, 114 y 119 (falta crédito en 46 de los 112 países de 2000, y capital humano en 12 a 18). Paraguay está en las cuatro ventanas.
- **Presencia (D13)** y densidad (D3): con la muestra D8 de cada ventana.
- **Capas:** energía (intensidad energética × precio de la electricidad), capital humano (habilidades × `hc`), crédito (intensidad de capital × crédito/PIB) y logística (**menos** log valor/peso × LPI). r en logaritmo (salvo habilidades) y estandarizado; a re-estandarizado entre los países de la muestra.
- **Se descartaron** las filas de países-ventana y productos-ventana sin ninguna entrada (28 % de las filas): no aportan a las pendientes y causan separación perfecta. Quedan 230.643 filas y 7.411 entradas, 126 países y 1.095 productos.

## Resultados (todas las ventanas)
| Variable | Coeficiente | Error agrupado | p |
|---|---|---|---|
| Densidad (d) | 1,15 | 0,06 | <0,001 |
| Energía (r·a) | 0,017 | 0,032 | 0,60 |
| **Capital humano (r·a)** | **0,089** | 0,018 | <0,001 |
| Crédito (r·a) | 0,011 | 0,018 | 0,54 |
| **Logística (r·a)** | **−0,085** | 0,029 | 0,005 |

Con la densidad sola, el coeficiente de densidad es 1,18 (0,06). Las interacciones con la densidad (λ) no son significativas (la de logística, +0,029, p = 0,059).

## Lo que se ve
1. **La densidad predice las entradas** en las cuatro ventanas (coeficiente 0,98 a 1,31), como se esperaba.
2. **Capital humano es robusto:** la interacción habilidades × capital humano da 0,087 a 0,091 en todas las submuestras, siempre significativa. Los productos que exigen más habilidades entran más en países con más capital humano.
3. **Energía y crédito no se distinguen de cero.** El precio de la electricidad solo existe para 2014-2019 (anacrónico antes). Crédito y capital humano están correlacionados con la logística (0,65 a 0,72 entre las dotaciones).
4. **La logística sale con el signo contrario al esperado y no es robusta.** Con el requisito definido como «menos log valor/peso» (más voluminoso = necesita más logística), se esperaba signo positivo. Sale −0,085. Pero depende de las ventanas con el LPI arrastrado hacia atrás (D14): en 2000 y 2005 da −0,132 (p = 0,001) y con solo 2010 y 2015 (datos reales) da −0,048 (p = 0,15). **No se cambió el signo del requisito para que coincida**: sería elegir la definición mirando el resultado. Una lectura posible es que el LPI favorezca más a los productos livianos y valiosos (el tiempo y la trazabilidad importan más ahí). Hay que decidirlo antes de repetir.

## Limitaciones de esta versión
- **No marca reexportaciones (D6):** hace falta el comercio bilateral (`baci_global`, no disponible en la foto). Afecta a Paraguay y a pocos centros comerciales.
- **Base de Ever desactualizada** (foto de lectura): usa su `rca_matrix` sin depurar. Se recalculó el RCA sin la energía, pero sin las reexportaciones de Paraguay.
- **Agricultura, minería y servicios quedan fuera** (143 de 1.242 productos HS4 sin requisitos, D4).
- **Casos con capas faltantes** reducen la muestra de 2000 a 61 países; decidir cómo tratarlos (tarea 1.7).
- **Sin fuera de muestra** (D2 a): esto es solo la parte de los coeficientes. El backtest de la 1.11 va aparte.

## Cómo repetirlo
```bash
uv run python -m src.modelos.logit_nacional --db RUTA_O_URL_DE_LA_BASE.duckdb
```
Escribe `data/model/exportaciones_hs4.parquet` (se reusa) y `data/model/logit_coeficientes.csv`.
