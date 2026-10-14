# Censo Económico Nacional 2011 (datos del año 2010): Cuadro 1 por distrito

Fuente: INE; archivo `49d4bCEN2011_DIST_CUADRO_1.xlsx` en `data/raw/censo_2011/` (descargado a mano el 2026-10-14). Limpieza: `src/limpieza/censo_2011.py` → `data/clean/censo2011_distrito_rama.csv` (nivel distrito) y `censo2011_departamento_rama.csv`.

## Veredicto: sirve para el backtest territorial
Trae lo que pedimos: **unidades económicas y personal ocupado (por sexo) por distrito y rama CIIU**, además de remuneraciones, gastos por compras e ingresos por suministro (miles de guaraníes). Totales nacionales: **224.242 unidades económicas y 799.153 ocupados**; 234 distritos.

Las sumas cuadran exactamente en todos los niveles (ramas = sector, ramas = distrito, distritos = departamento, departamentos = total nacional); está verificado en `verificar` y en un test.

## Cómo viene
- Bloques anidados: departamento (con sus propios totales y ramas) → distrito → sector (Industria, Comercio, Servicios) → rama. «Industria» incluye minería de apoyo (08, 09), manufactura (10-33), electricidad y construcción (41-43). No hay agropecuario ni administración pública.
- Las ramas chicas se agrupan en «Otras actividades de <sector>» (reserva estadística); son el 5,6 % de las unidades industriales. Los sectores sin ningún detalle se completan con una fila «(implícito)» para que los totales cuadren.
- Granularidad mezclada: hay códigos de 3 dígitos (grupos) y, donde el detalle se agrupó, de 2 dígitos (división). 73 grupos de 3 dígitos distintos en manufactura.
- Los distritos chicos no traen encabezado de sector; el sector se infiere de la división (`sector_inferido`).
- Asunción es departamento y distrito a la vez; en la salida por distrito figura como «ASUNCIÓN».

## Manufactura (lo comparable con el mapa MIC 2026)
21.134 unidades y 119.314 ocupados en las divisiones 10-33, en 160 de los 234 distritos; 147 distritos con al menos 5 unidades y 102 con al menos 20. Asunción (3.008), Ciudad del Este (1.315), San Lorenzo (1.220), Luque (1.219) y Capiatá (903) encabezan. Mayores ramas: confección (141, 2.324), muebles (310, 2.082), productos metálicos (251, 1.597), otros alimenticios (109, 1.375).

## Problemas a resolver antes de usarlo en el modelo
1. **Sin código de distrito: solo nombres.** Hay que cruzarlos con los 247 distritos de los límites DGEEC 2012 y los 263 del Censo 2022 (ya había un pendiente de reconciliación). Los distritos creados después de 2010 no existen aquí.
2. **Los códigos de 3 dígitos no coinciden del todo con la CIIU Rev.4 internacional.** En alimentos, el 109 se llama «otros productos alimenticios» y es el grupo grande (probablemente panadería y similares), mientras que el 107 se llama «alimentos preparados para animales» (en la Rev.4 internacional, 107 es «otros alimentos» y 108 «piensos»). Lo mismo con 111 y 112 (bebidas) y 209. Es una adaptación nacional; **inconsistencia señalada, no corregida**. Resultado: de las 22.940 unidades industriales con código, el 79,8 % cae en un único sector TAPE por prefijo; el 13 % es ambiguo (el grupo reparte entre varios sectores: 10, 20, 23, 239, 106...) y unas 1.600 (códigos 109, 209, 111, 112) no coinciden con ningún sector. Hace falta una **tabla Censo 2011 → sector TAPE** con confianza por fila, igual que la del mapa MIC.
3. **Año de referencia 2010** (el censo se llama 2011), 15 años antes del mapa MIC 2026.
4. **No distingue formal de informal** y excluye lo agropecuario. Es una unidad económica, no una industria del mapa MIC: las dos fuentes no cuentan lo mismo (17.080 industrias del MIC contra 21.134 unidades manufactureras del censo). Se presenta como validación débil, como se decidió el 2026-10-08.

## Qué viene
(1) Tabla de equivalencia de distritos (nombres → distrito actual). (2) Tabla Censo 2011 → sector TAPE (con la equivalencia de los códigos nacionales). (3) Matrices de presencia 2010 y 2026 por sector × distrito y la prueba hacia atrás: densidad 2010 contra las apariciones hasta 2026.
