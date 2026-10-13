# Logit nacional con capas: primera corrida provisoria (2026-10-13)

**Provisorio.** Es la primera versión de la tarea 1.9 (`src/modelos/logit_nacional.py`). Los coeficientes son **asociaciones dentro de la muestra**, no causalidad ni predicción. No se usan para decidir qué capas entran al modelo final.

## Cómo se hizo
- **Datos:** `rca_matrix` de la base de Ever (foto de lectura, HS6, con todas las exportaciones de BACI), agregada a HS4 y recalculada sin la energía de Itaipú/Yacyretá (HS4 2716). Se usaron exportaciones de 1995 a 2020.
- **Modelo (D2 c):** `Pr(E=1) = Λ(α_ct + γ_pt + β d + Σ_k θ_k r_k a_k + Σ_k λ_k d r_k a_k)`. Efectos fijos de país-ventana y producto-ventana. Errores agrupados por país (`LogitEfectosFijos.errores_agrupados`).
- **Entrada (D7):** `RCA_t0 < 0,5` y `RCA_t0+5 ≥ 1`, un solo año. Ventanas 2000, 2005, 2010 y 2015. **El panel incluye los productos que el país no exportaba (RCA = 0)**: son el 22 % de las filas, con una tasa de entrada de 1,2 % (contra 2,6 % en los que ya exportaban algo).
- **Muestra (D8):** 112, 128, 141 y 144 países por ventana. **Se pierden países al exigir las cuatro capas** (cada especificación descarta los países que no tienen las capas que usa): con las capas vigentes (D15) quedan 97, 110, 122 y 123; con el crédito en lugar del capital físico, 59, 91, 112 y 119 (falta crédito en 46 de los 112 países de 2000, y capital humano en 12 a 18). Paraguay está en las cuatro ventanas.
- **Presencia (D13)** y densidad (D3): con la muestra D8 de cada ventana.
- **Capas:** energía (intensidad energética × precio de la electricidad), capital humano (habilidades × `hc`), **capital físico (intensidad de capital × log del stock de capital por trabajador de PWT; D15)** y logística (**menos** log valor/peso × LPI). r en logaritmo (salvo habilidades) y estandarizado; a re-estandarizado entre los países de la muestra.
- **Se descartaron** las filas de países-ventana y productos-ventana sin ninguna entrada (28 % de las filas): no aportan a las pendientes y causan separación perfecta. Con las capas vigentes quedan 296.435 filas y 9.315 entradas, 128 países y 1.095 productos.

## Resultados vigentes (D15, todas las ventanas)
| Variable | Coeficiente | Error agrupado | p |
|---|---|---|---|
| Densidad (d) | 1,09 | 0,06 | <0,001 |
| Energía (r·a) | 0,003 | 0,030 | 0,91 |
| **Capital humano (r·a)** | **0,088** | 0,016 | <0,001 |
| Capital físico (r·a) | 0,004 | 0,019 | 0,83 |
| **Logística (r·a)** | **−0,063** | 0,025 | 0,013 |

296.435 filas, 9.315 entradas, 128 países. Con la densidad sola (363.333 filas), el coeficiente de densidad es 1,13 (0,05). **Exploratorio:** con las interacciones de la densidad (λ) aparecen la de capital físico (−0,047, p = 0,008) y la de logística (+0,030, p = 0,023); hay ocho términos más y ninguno se había anticipado, así que no se interpretan hasta el backtest.

Las secciones siguientes se hicieron en orden y las primeras usan el **crédito** como par del requisito de capital (versión inicial, 230.643 filas); la comparación y la decisión D15 están en la sección de capital físico. En las submuestras con las capas vigentes: con solo 2010 y 2015 (datos reales de LPI), capital humano 0,091 (p < 0,001) y logística −0,043 (p = 0,14); con solo 2000 y 2005, capital humano 0,089 y logística −0,087 (p = 0,010). Con el control por PIB per cápita (todas las ventanas): capital humano 0,054 (p = 0,044), logística −0,080 (p = 0,030), capital físico −0,006 (p = 0,91).

## Lo que se ve
1. **La densidad predice las entradas** en las cuatro ventanas (coeficiente 0,98 a 1,31), como se esperaba.
2. **Capital humano: significativo, pero no se distingue del desarrollo general.** La interacción habilidades × capital humano da 0,087 a 0,091 en todas las submuestras, siempre significativa. **Al controlar por el PIB per cápita pierde fuerza** (0,042, p = 0,18; ver la prueba más abajo): los productos que exigen más habilidades entran más en los países más ricos, y el capital humano (correlación 0,79 con el PIB per cápita) no se separa bien de eso.
3. **Energía y crédito no se distinguen de cero.** El precio de la electricidad solo existe para 2014-2019 (anacrónico antes). Crédito y capital humano están correlacionados con la logística (0,65 a 0,72 entre las dotaciones).
4. **La logística sale con el signo contrario al esperado y no es robusta.** Con el requisito definido como «menos log valor/peso» (más voluminoso = necesita más logística), se esperaba signo positivo. Sale −0,085. Pero depende de las ventanas con el LPI arrastrado hacia atrás (D14): en 2000 y 2005 da −0,132 (p = 0,001) y con solo 2010 y 2015 (datos reales) da −0,048 (p = 0,15). **No se cambió el signo del requisito para que coincida**: sería elegir la definición mirando el resultado. Una lectura posible es que el LPI favorezca más a los productos livianos y valiosos (el tiempo y la trazabilidad importan más ahí). Hay que decidirlo antes de repetir.

## Prueba del control por PIB per cápita (2026-10-13)
Se agregó, para cada capa, el requisito multiplicado por el log del PIB per cápita (`rpib_k`), sobre la misma muestra (124 países; se pierden 6.237 filas de 2 países sin PIB). Pregunta: ¿la interacción de logística es solo «desarrollo»?

| Variable | Sin control | Con control | Con control, solo 2010 y 2015 |
|---|---|---|---|
| Capital humano (r·a) | 0,091 (p < 0,001) | 0,042 (p = 0,18) | 0,062 (p = 0,09) |
| Crédito (r·a) | 0,014 (p = 0,44) | 0,009 (p = 0,79) | −0,021 (p = 0,67) |
| Energía (r·a) | 0,028 (p = 0,43) | 0,024 (p = 0,47) | −0,005 (p = 0,89) |
| **Logística (r·a)** | **−0,085 (p = 0,005)** | **−0,091 (p = 0,023)** | −0,051 (p = 0,27) |
| Habilidades × PIB per cápita | | 0,081 (p = 0,005) | 0,055 (p = 0,10) |

- **La logística no es un efecto del desarrollo.** El coeficiente casi no cambia con el control (−0,085 a −0,091), y su interacción con el PIB per cápita es cero (0,003). El signo contrario al esperado sigue ahí, con las mismas dudas: con datos reales de LPI (2010 y 2015) no se distingue de cero (p = 0,27).
- **El capital humano sí pierde fuerza** (de 0,091 a 0,042), y en 2000-2005 casi desaparece (0,003), mientras que habilidades × PIB per cápita pasa a ser significativa (0,122). Los datos no separan «capital humano» de «ser un país rico»: el error estándar casi se duplica.
- **Energía:** la interacción con el PIB per cápita es positiva (0,054 a 0,077): los productos intensivos en energía entran más en países ricos; el precio de la electricidad no aporta aparte.
- **Conclusión para la decisión (a) de la logística:** no se explica por desarrollo; sigue sin interpretación clara y no es robusta. Se decide con el backtest fuera de muestra (tarea 1.11), eligiendo el signo solo con las ventanas de entrenamiento.

## Capital físico por trabajador en lugar del crédito (2026-10-13)
Se agregó la capa `capital_fisico` (log del stock de capital real por trabajador de PWT, `rnna / emp`), el par natural del requisito de capital (stock de capital real por trabajador de NBER-CES), y se comparó con el crédito.

| | Crédito (base) | Capital físico en lugar del crédito | Los dos |
|---|---|---|---|
| Países en 2000 / 2005 / 2010 / 2015 | 59 / 91 / 112 / 119 | **97 / 110 / 122 / 123** | 59 / 91 / 112 / 119 |
| Filas / entradas | 230.643 / 7.411 | **296.435 / 9.315** | 230.643 / 7.411 |
| Coeficiente de la capa de capital | 0,011 (p = 0,54) | 0,004 (p = 0,83) | crédito 0,004; capital físico 0,009 (p > 0,75) |
| Capital humano (r·a) | 0,089 (p < 0,001) | 0,088 (p < 0,001) | 0,089 |
| Logística (r·a) | −0,085 (p = 0,005) | −0,063 (p = 0,013) | −0,085 |
| Capital humano con control por PIB per cápita | 0,042 (p = 0,18) | 0,054 (p = 0,044) | 0,042 |

- **En la misma muestra no cambia nada:** con los 124 países que tienen todas las capas, la interacción de capital físico da 0,011 (p = 0,57), y las demás quedan igual. Ni el crédito ni el capital físico predicen entradas.
- **La ganancia es de muestra:** 26 % más filas y 38 países más en 2000 (97 contra 59). Con esa muestra mayor, capital humano da lo mismo y la logística se debilita (−0,063).
- **El capital físico es casi el PIB per cápita:** correlación 0,94 con el log del PIB per cápita (capital humano 0,81, logística 0,75, crédito 0,72). Con el control por PIB per cápita su error estándar se duplica (0,06).
- **Conclusión:** la capa de capital, con cualquiera de las dos medidas, no aporta una señal propia. Elegir una u otra es sobre todo una decisión sobre el tamaño de la muestra. **D15 decidida el 2026-10-13: (a), capital físico en lugar del crédito**, que queda como robustez (`capas_con_credito`) y como indicador separado de brechas en la Fase 3.

## Limitaciones de esta versión
- **No marca reexportaciones (D6):** hace falta el comercio bilateral (`baci_global`, no disponible en la foto). Afecta a Paraguay y a pocos centros comerciales.
- **Base de Ever desactualizada** (foto de lectura): usa su `rca_matrix` sin depurar. Se recalculó el RCA sin la energía, pero sin las reexportaciones de Paraguay.
- **Agricultura, minería y servicios quedan fuera** (143 de 1.242 productos HS4 sin requisitos, D4).
- **Casos con capas faltantes** reducen la muestra de 2000 a 97 países (con el crédito serían 59); decidir cómo tratarlos (tarea 1.7).
- **Sin fuera de muestra** (D2 a): esto es solo la parte de los coeficientes. El backtest de la 1.11 va aparte.

## Cómo repetirlo
```bash
uv run python -m src.modelos.logit_nacional --db RUTA_O_URL_DE_LA_BASE.duckdb
```
Escribe `data/model/exportaciones_hs4.parquet` (se reusa) y `data/model/logit_coeficientes.csv`.
