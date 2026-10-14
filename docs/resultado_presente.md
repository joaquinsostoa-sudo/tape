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

## Pendiente
- **Reservas** de minerales, petróleo y gas (USGS y Energy Institute), a descargar con tu confirmación; **hidro** (proporción hidroeléctrica × intensidad energética) y **agua dulce** (WDI, ya descargada). Se declarará aparte como extensión antes de correrla.
- **Definición del requisito de logística:** con dos salidas independientes (entrada y presencia) en el mismo sentido, hay evidencia para plantear una definición alternativa («valor/peso» con signo positivo). Cambiarla ahora sería post hoc; habría que declararla como tal y validarla en datos nuevos.
