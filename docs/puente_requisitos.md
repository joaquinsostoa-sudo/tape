# Puente de requisitos por producto (tarea 1.6, decisión D4)

Fecha: 2026-10-12. Código: `src/puentes/requisitos.py`. Salidas: `data/clean/requisitos_producto.parquet` y `requisitos_producto_hs4.csv` (1.242 productos HS de 4 dígitos, la unidad de estimación de D5) y `requisitos_producto_hs6.parquet` (5.022 productos HS92 de 6 dígitos). Pruebas: `tests/test_requisitos.py`.

## Qué mide cada requisito
| Columna | Definición | Fuente | Unidad |
|---|---|---|---|
| `energia` | costo de energía / valor de envíos de la industria, 2012-2018 (razón de sumas) | NBER-CES | fracción |
| `capital` | stock de capital real / empleo, 2012-2016 (el capital llega a 2016) | NBER-CES | miles de USD por trabajador |
| `habilidades` | proporción de trabajadores que no son de producción, 2012-2018 | NBER-CES | 0 a 1 (sustituto: la base no mide habilidades) |
| `valor_peso_usd_kg` | valor / peso del comercio mundial, 2018-2019 | BACI | USD por kg |

Además cada fila trae `cobertura` (parte del peso del producto que llega a una industria con dato), `peso_top` (qué tan ambiguo es el reparto entre industrias), `valor_mundial` (ponderador) y `confianza`.

## Cadena
NBER-CES (364 industrias NAICS 2012) → productos HS 2012 con la concordancia de Pierce y Schott (años 2014-2016) → productos HS92 con la cadena de conversión de `hs_sector.py` → HS de 4 dígitos, ponderando por el valor mundial exportado de 2018-2019 (Atlas). El peso de cada camino es el producto de los pesos de sus tramos.

## Confianza por fila
- **alta:** cobertura ≥ 0,8 y reparto no ambiguo (`peso_top` ≥ 0,8).
- **media:** cobertura ≥ 0,4, o cobertura alta con reparto ambiguo.
- **baja:** cobertura menor a 0,4.
- **sin_dato:** ningún camino llega a una industria de NBER-CES (agricultura, minería, energía y servicios).

Los umbrales son supuestos del equipo, por revisar. Por valor mundial exportado (2018-2019): **alta 58,7 %, media 21,9 %, baja 6,2 %, sin dato 13,1 %**. De los 4.552 productos HS6 con dato, 79 tienen un reparto ambiguo (`peso_top` < 0,5). 203 HS6 no traen peso en BACI.

## Control: sentido económico (HS4 con valor mundial de más de USD 100 millones)
| | Más intensivos | Menos intensivos |
|---|---|---|
| **Energía** | cal viva, aluminio, papel prensa, dolomita, clínker de cemento, alúmina, vidrio | vehículos de transporte público, cigarros, tabaco, camiones fuera de ruta |
| **Capital** | derivados del petróleo, papel prensa, hidrocarburos, cintas magnéticas, elementos dopados para electrónica | peletería, bolsas de yute, placas metálicas, toldos |
| **Habilidades** | instrumentos de navegación, radar, rayos X, reactivos, microscopios, computadoras | lavarropas, carne de pollo, hilados |

## Productos clave de Paraguay (HS4)
| Producto | Energía | Capital | Habilidades | Valor/peso | Confianza |
|---|---|---|---|---|---|
| 0201 y 0202 Carne bovina | 0,006 | 110 | 0,12 | 4,4 a 6,0 | alta |
| 1507 Aceite de soja | 0,012 | 542 | 0,26 | 0,73 | alta |
| 2304 Harina de soja | 0,013 | 574 | 0,26 | 0,38 | alta |
| 1006 Arroz con cáscara | 0,020 | 248 | 0,23 | 0,57 | alta |
| 2207 Etanol | 0,044 | 440 | 0,28 | 0,75 | media |
| 8544 Conductores eléctricos (arneses) | 0,008 | 162 | 0,30 | 12,0 | alta |
| 2523 Clínker de cemento | 0,171 | 998 | 0,22 | 0,06 | alta |
| **1201 Soja en grano** | — | — | — | 0,39 | **sin dato** |
| **5201 Algodón** | — | — | — | 1,84 | **sin dato** |

## Límites
1. **La tecnología es la de la manufactura de EE. UU.**: se supone que producir un bien exige lo mismo en todos los países.
2. **Agricultura y minería quedan sin dato** (13 % del valor mundial; incluye la soja en grano, el principal producto de exportación de Paraguay). Hay que decidir cómo tratarlos en el modelo (excluirlos de las interacciones, o imputar por el sector). Se deja a la tarea 1.7.
3. **Las 364 industrias son pocas** frente a miles de productos: productos distintos heredan el mismo valor (por ejemplo, 8548 y 3818 comparten el de la industria de semiconductores).
4. **Los HS6 que caen en varias industrias** se reparten en partes iguales por línea HS10. La concordancia no trae valores de comercio de EE. UU. por HS10, así que no se pudo ponderar por valor exportado.
5. **El capital llega a 2016** y la concordancia a 2017; las intensidades se suponen estructurales.
6. **La energía mide el costo de energía de la industria, no el de un país**: el costo por país va aparte (proxies de WDI, tarea 1.5).
7. Resultados como asociación, no como causalidad.

## Estándares pendientes para el modelo
Estas son intensidades en bruto: la tarea 1.7 las estandariza (r_pk y a_ckt estandarizados, según el modelo M1).
