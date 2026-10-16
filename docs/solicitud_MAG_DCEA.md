# Borrador: pedido de información al MAG (Dirección de Censos y Estadísticas Agropecuarias)

Estado: **borrador sin enviar**. Lo envía una persona del equipo (es una comunicación hacia afuera); ajustar el nombre del solicitante y el medio de entrada (acceso a la información pública, Ley 5282/14).

## Para qué lo necesitamos
El módulo territorial de TAPE mide la dotación de recursos agropecuarios de cada distrito. Hoy tenemos la cantidad de fincas y la superficie por distrito (Censo Agropecuario 2022) y el uso del suelo por satélite (MapBiomas), pero **no sabemos qué se cultiva ni cuánto rinde** en cada distrito. El rendimiento oficial que encontramos está solo por departamento.

## Texto sugerido
> Solicitamos, en formato de planilla (xlsx o csv) y a nivel de **distrito**, la siguiente información de la Dirección de Censos y Estadísticas Agropecuarias:
>
> 1. **Censo Agropecuario Nacional 2022:** superficie sembrada (hectáreas), superficie cosechada, producción (toneladas) y número de fincas, por cultivo y por distrito, para al menos soja, maíz, trigo, arroz, caña de azúcar, algodón, mandioca, yerba mate, sésamo, chía, girasol, canola, frutas y hortalizas principales; y la existencia de ganado (bovinos, porcinos, aves, ovinos y equinos) por distrito.
> 2. **Estimaciones de zafra (soja, maíz, trigo y otros cultivos de renta):** superficie sembrada, producción y rendimiento (kg por hectárea) por distrito, de las últimas cinco zafras disponibles.
> 3. La **metodología** de cada serie y las notas sobre secreto estadístico (por qué algunos distritos aparecen agregados o vacíos).
>
> Los datos se usarán para un estudio de diversificación productiva territorial del Laboratorio de Desarrollo Económico. Solicitamos que se indique la licencia o las condiciones de uso y la forma de citarlos.

## Qué haríamos al recibirlo
- Guardar el archivo tal como llegue en `data/raw/mag_cultivos_distrito/` y registrarlo en `data/fuentes.csv`.
- Calcular el rendimiento por cultivo y distrito (producción sobre superficie cosechada) y reemplazar la medida de recursos, hoy preliminar, por una que distinga cultivos y ganadería.

## Mientras tanto
Con lo que ya tenemos se puede calcular el **rendimiento departamental** por cultivo (producción sobre superficie, Censo Agropecuario Volumen I, 78 cuadros) y estimar la producción del distrito como la tierra agrícola de MapBiomas por el rendimiento de su departamento. Es una estimación (supone igual rendimiento dentro del departamento), con el mismo criterio que usamos para la escolaridad.
