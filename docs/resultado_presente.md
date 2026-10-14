# ¿Las dotaciones explican lo que se produce hoy? Prueba de corte transversal (2026-10-13)

**Provisorio.** Especificación, hipótesis y criterio registrados antes de correr (`docs/supuestos.md`, commit `293c2bd`). Código: `src/modelos/presente.py`. Base de Ever en lectura, sin marca de reexportaciones. Resultados como asociación, no causalidad.

## Cómo se hizo
- **Resultado:** presencia en t = 1[RCA_t ≥ 1], todos los pares país × producto HS4 (incluidos los de RCA = 0), sin energía binacional; países D8; años 2000, 2005, 2010 y 2015 (651.000 filas, 97.260 presencias, 147 países, 1.240 productos).
- **Modelo:** logit con efectos fijos de país-año y producto-año, errores agrupados por país (D2 c). Los efectos fijos absorben el nivel de cada país y cada producto; solo cuenta el **cruce** entre lo que el producto exige y lo que el país tiene.
- **Bloque M (manufactura):** 1.099 productos con requisitos de NBER-CES; términos r × a de energía, capital humano, capital físico y logística.
- **Bloque R (recursos):** todos los productos; «producto de tierra» (161 de los 1.240; capítulos HS de animales, carne, lácteos, plantas, cereales, oleaginosas, azúcar, cacao, forraje, tabaco y algodón) × tierra cultivable por persona (WDI, log, estandarizada).
- **Hipótesis:** los cuatro coeficientes de M y el de R son positivos. **Criterio de éxito:** en la estimación agrupada, al menos 3 de los 4 de M positivos con p < 0,05 y el de R positivo con p < 0,05.

## Resultados (estimación agrupada de los cuatro años)
| Bloque | Término | Coeficiente | Error agrupado | p | ¿Positivo y p < 0,05? |
|---|---|---|---|---|---|
| M | Energía (r·a) | 0,041 | 0,057 | 0,48 | no |
| M | **Capital humano (r·a)** | **0,193** | 0,030 | < 0,001 | **sí** |
| M | Capital físico (r·a) | 0,072 | 0,031 | 0,021 | sí |
| M | **Logística (r·a)** | **−0,093** | 0,038 | 0,016 | **no (signo contrario)** |
| R | **Tierra × tierra cultivable** | **0,218** | 0,067 | 0,0015 | **sí** |

- **El criterio no se cumple:** M da 2 de 4 (capital humano y capital físico), y se pedían 3; **R sí se cumple**.
- **Capital humano es muy estable:** 0,19 a 0,20 en cada uno de los cuatro años, siempre p < 0,001. Los productos que usan más habilidades están presentes en los países con más capital humano, como se esperaba.
- **Tierra cultivable también:** positivo y creciente (0,15 en 2000 a 0,27 en 2015, siempre p < 0,05). Paraguay (0,59 a 0,68 ha por persona) es de los países de mayor dotación.
- **Energía no se distingue de cero** (la medida usa el precio de 2014-2019 y el LPI/precios son proxies débiles).
- **La logística tiene signo contrario al esperado, en los cuatro años** (−0,08 a −0,10, p < 0,03 en cada uno). Es el mismo signo que en el modelo de entrada. Con el requisito definido como «menos log valor/peso», los productos voluminosos están **menos** presentes en países con mejor LPI; es decir, los productos livianos y valiosos son los que se concentran donde el LPI es alto. Es una segunda salida, independiente de la entrada, que apunta al mismo lado.
- **Poder explicativo:** M mejora la log-verosimilitud sobre el modelo de solo efectos fijos en 2,4 por mil observaciones (LR = 2.406); R, en 0,30 por mil (diluido: la tierra solo afecta a 161 productos).

## Sensibilidades (no cuentan para el criterio)
- **Control por PIB per cápita (r × ingreso):** el capital humano baja a 0,114 (p = 0,057) y el capital físico se anula (−0,03); la energía pasa a +0,096 (p = 0,020); la logística sigue negativa y más fuerte (−0,157, p = 0,007). En R, la tierra se mantiene (0,184, p = 0,016) y el término de ingreso es muy negativo (−0,49): los países ricos tienen menos productos de tierra. Es decir, parte de lo que parecía «capital humano» o «capital físico» es desarrollo general, pero la tierra y la logística (contraria) no.
- **Faltantes del requisito revelado:** los cinco son negativos y muy significativos en cada año (p < 0,05 siempre), y la mejora de log-verosimilitud es mucho mayor (19,1 por mil). **Cuidado:** es parcialmente circular, porque la referencia se arma con la presencia del mismo año de otros países: mide cuánto se parece el país al resto de los productores. No debe leerse como un resultado independiente.

## Qué responde a la pregunta
**Sí, en parte.** Las dotaciones, bien alineadas con las intensidades, explican lo que se produce hoy en capital humano (fuerte y estable) y en recursos de tierra (fuerte y creciente). No lo hacen en energía, y la logística, tal como está definida, va en sentido contrario. Que algunas capas expliquen el stock y no predigan la entrada es coherente con la idea de que la entrada la gobiernan sobre todo la cercanía y la propensión de país y producto, no las dotaciones.

## Extensión: todos los recursos naturales (2026-10-13)
Declarada antes de correr (commit `cbf086b`); código `src/modelos/recursos.py`. Mismo diseño que arriba (presencia 1[RCA_t ≥ 1], efectos fijos de país-año y producto-año, errores agrupados por país). Términos nuevos: **agua dulce** (productos de tierra × recursos hídricos por persona), **hidro** (intensidad energética × proporción hidroeléctrica), **petróleo**, **gas** y **carbón** (HS4 de cada uno × reservas probadas por persona; el carbón solo para 2010 y 2015) y **minerales** (18 productos × participación del país en las reservas mundiales del USGS; países ausentes = sin dato).

| Término (estimación agrupada) | Coeficiente | Error agrupado | p | ¿Positivo y p < 0,05? |
|---|---|---|---|---|
| Tierra (en el modelo conjunto con agua) | +0,239 | 0,090 | 0,009 | (ya contado) |
| Agua dulce × productos de tierra | −0,100 | 0,087 | 0,25 | no |
| Hidro × intensidad energética | −0,013 | 0,033 | 0,70 | no |
| **Petróleo** (HS4 2709 y 2710) | **+1,954** | 0,206 | < 0,001 | **sí** |
| **Gas** (HS4 2711) | **+5,009** | 1,298 | 0,0002 | **sí** |
| **Carbón** (HS4 2701 y 2704) | **+1,392** | 0,257 | < 0,001 | **sí** |
| Minerales (USGS, ausente = sin dato) | +0,463 | 0,389 | 0,24 | no |

- **El criterio declarado no se cumple:** exigía al menos 4 de los 6 términos nuevos positivos con p < 0,05, y son **3 de 6** (petróleo, gas y carbón).
- **Reservas de energía:** muy claras y estables año por año (petróleo 1,8 a 2,1; gas 3,5 a 7,9; carbón 1,4). Es una validación de que el cruce recurso-producto funciona, pero es casi mecánica: los países con reservas exportan petróleo, gas y carbón.
- **Minerales:** positivo pero impreciso con la muestra principal (solo los 82 países que el USGS informa; 404 pares mineral-país). **Sensibilidad (no cuenta para el criterio): con los países ausentes como cero reservas, el coeficiente es +0,684 (p = 0,0001).** La diferencia viene de comparar productores informados con no productores; hay que recordar que el USGS solo informa a los principales productores y que ausente no es necesariamente cero.
- **Agua dulce:** sin efecto, y con signo negativo creciente (−0,05 en 2000 a −0,18 en 2015, p = 0,056 en 2015) una vez que la tierra está en el modelo; no hay evidencia a favor.
- **Hidro:** sin efecto en ninguna ventana (−0,046 a +0,016, p ≥ 0,19).
- **Controlando por ingreso** (término tipo × PIB per cápita), la tierra se mantiene (+0,204, p = 0,036) y el petróleo, el gas y el carbón también; el término de ingreso es negativo y fuerte para la tierra (−0,49) y el petróleo (−0,95): los países ricos tienen menos productos basados en recursos.
- **Fallas técnicas corregidas durante la corrida (no cambian la especificación declarada):** (a) el control de ingreso del bloque R1 repetía dos columnas idénticas (`rpib_agua` = `rpib_tierra`, mismos productos) y daba una matriz singular; se dejó una; (b) en las estimaciones año por año de 2000 y 2005 la columna del carbón es toda cero (la serie empieza en 2008) y se excluyó.

**Qué responde.** Para los bienes primarios, la dotación física del recurso sí explica la presencia actual: tierra, petróleo, gas y carbón, y los minerales cuando se compara con los no productores. Para la manufactura, capital humano. Energía eléctrica barata, hidro, agua dulce, capital físico y logística no.

## Pendiente
- **Reservas** de minerales, petróleo y gas (USGS y Energy Institute), a descargar con tu confirmación; **hidro** (proporción hidroeléctrica × intensidad energética) y **agua dulce** (WDI, ya descargada). Se declarará aparte como extensión antes de correrla.
- **Definición del requisito de logística:** con dos salidas independientes (entrada y presencia) en el mismo sentido, hay evidencia para plantear una definición alternativa («valor/peso» con signo positivo). Cambiarla ahora sería post hoc; habría que declararla como tal y validarla en datos nuevos.
