# Puente HS92 → CPC 2.1 → CIIU Rev.4 → sector TAPE (tarea 0.5)

Archivo: `data/clean/puente_hs92_sector.csv`. Código: `src/puentes/hs_sector.py`. Pruebas: `tests/test_hs_sector.py`.
Una fila por (código HS92 de 6 dígitos, sector TAPE) con su peso (suman 1 por código), las clases CIIU, la confianza, la vía y las marcas.

## Cómo se construye
1. **HS92 → HS12** encadenando las tablas ponderadas por comercio del Atlas (HS92 → HS96 → HS02 → HS07 → HS12). Esas tablas solo listan los códigos que cambian; los demás pasan sin cambio (si no, se perdían 349 códigos, entre ellos la carne bovina deshuesada).
2. **HS12 → CPC 2.1** (tabla de la ONU). Si un código tiene varias CPC, pesa 3 veces más la CPC contenida entera en el código (marca `CPC21partial = 0`) que una parcial. Ejemplo: 0805.10 es naranja fresca (agricultura) y, en parte, fruta seca (procesamiento).
3. **CPC 2.1 → CIIU Rev.4** (tabla de la ONU). Si una CPC tiene varias clases, reparto en partes iguales.
4. **Clase CIIU → sector TAPE** con la partición de la taxonomía (cada clase cae en un solo sector).

## Vías y confianza
| Vía | Qué es | Códigos |
|---|---|---|
| `cadena` | Todo oficial | la gran mayoría |
| `cadena_prefijo` | Un código HS12 que la ONU no lista (p. ej. 0405.00, que HS dividió en 0405.10/20/90) se reparte entre sus hermanos de 4 dígitos | 19 |
| `regla_residuos` | La ONU deja sin clase CIIU a los residuos y la chatarra (CPC 39); van a la clase 3830 de recuperación de materiales | 80 |
| `regla_especial` | Arneses (HS 854430) → Autopartes, por decisión del equipo | 1 |
| `fallback_hs4` | Código sin cadena: se reparte como sus hermanos de partida HS4, ponderado por valor mundial | 0 en esta corrida |

Confianza por código: **alta** (un sector tiene ≥ 95 % del peso, casi toda la masa llegó a una clase y la vía es `cadena`), **media** (sector principal ≥ 60 %, o vía de regla), **baja** (más repartido). `sin_mapeo`: solo los 2 códigos de "mercancías no especificadas" (999999 y 9999AA).

## Resultados de control (valor mundial 2022-2024)
- **5.022 códigos** HS92 de BACI; usan **50 de los 67 sectores** (los demás son servicios, construcción y energía, sin productos).
- Por valor exportado mundial: **alta 86,1 %**, media 8,9 %, baja 2,0 %, sin mapeo 3,1 % (todo "mercancías no especificadas").
- Por número de códigos: alta 4.614, media 244, baja 162, sin mapeo 2.
- **Contraste independiente con WITS (HS92 → CIIU Rev.3)** a nivel de gran grupo (agro, minería, manufactura): coincide el **98,1 % de los códigos y el 99,4 % del valor**. Las diferencias son sobre todo cambios entre revisiones (la edición de libros y los medios pasaron de manufactura a información) o casos ambiguos que la propia tabla de la ONU reparte (leche cruda; nueces y maníes, que van a procesamiento).
- **Principales exportaciones de Paraguay 2024:** soja → cultivos anuales; carne bovina deshuesada → frigoríficos; harina y aceite de soja → aceites; maíz → cultivos anuales; arroz semielaborado → molinería; arneses → autopartes (335 M USD); electricidad → marcada para excluir.

## Marcas
- `excluir_energia_binacional`: HS 271600 (energía eléctrica de Itaipú y Yacyretá).
- `arnes`: HS 854430. El caso central del documento técnico; sin la regla caería en cables eléctricos.
- `biocombustible_posible`: HS 2207.10, 2207.20 (etanol), 1518.00 y 3823.90 (partidas donde puede ir el biodiésel en HS92). La CIIU no tiene clase propia para biocombustibles: se identifican por producto, no por sector.
- `no_clasificable`: HS 999999.
- La marca de **reexportaciones** se agrega en la tarea 1.2 (depuración del comercio).

## Limitaciones
- Los **repartos en partes iguales** (HS → CPC y CPC → CIIU) son una convención, no un dato. Donde no hay una salida dominante la confianza baja a media o baja. Con las estadísticas de comercio por producto de las otras revisiones HS se podrían reemplazar por pesos de valor.
- **Fallos conocidos:** las nueces y los maníes se asignan a "frutas, hortalizas y pescado procesados" porque así lo hace la tabla de la ONU; la leche fresca va a ganadería. Están con confianza media o baja.
- Esta tabla es para **HS92**. Para usar BACI con otra revisión (HS12, HS17) hay que repetir el puente, partiendo directamente de las tablas HS12/HS17 de la ONU.
