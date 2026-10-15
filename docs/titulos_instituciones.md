# Registro de títulos del MEC: ubicación de las instituciones

Fecha: 2026-10-15. Código: `src/puentes/titulos_instituciones.py` (14 pruebas en `tests/test_titulos_instituciones.py`). Reglas declaradas antes de construir: D17 en `docs/supuestos.md`.
Salidas (en `data/clean/`, sin datos personales): `titulos_conteos.parquet`, `puente_titulos_institucion.csv`, `titulos_institucion_distrito.csv`, `titulos_sensibilidad_departamento.csv`, `titulos_ajustes_distritos.csv`.

## En palabras simples
El registro de títulos dice **qué institución** dio el título, pero no **en qué distrito**. Para ubicarla usamos el listado de instituciones del MEC (2018), que sí trae el distrito de cada campus. Cada institución del registro se busca por nombre en ese listado.
- Si la institución tiene **una sola sede**, el título va a ese distrito.
- Si tiene **varias** y el nombre no dice cuál, no sabemos dónde se estudió: se asigna a la sede principal y se marca con confianza **baja**.
- Si el nombre dice el lugar («– Caacupé», «Sede Encarnación»), se usa ese lugar.

**Resultado: se pudo ubicar el 72 % de los títulos 2013-2025, pero solo el 23 % con confianza alta.** La meta de ubicar el 90 % no se cumple todavía.

## Fuentes y ventana
- Registro de títulos (`data/raw/mec_titulos/`): 688.161 títulos de 2013 a 2025, 1.579 nombres de institución una vez normalizados (573 códigos).
- Listado de instituciones del MEC de 2018, educación superior (`data/raw/mec_escuelas/instituciones_20261015.csv`): 819 filas, 430 instituciones, 133 distritos.
- Tabla de distritos de TAPE (`puente_distritos_2022.csv`) para llevar cada campus a su departamento y distrito.

## Resultado (control)
| Cómo se ubicó | Confianza | Instituciones | Títulos | % de los títulos |
|---|---|---|---|---|
| Nombre exacto, institución con **varias sedes** (sede principal) | baja | 32 | 258.495 | 37,6 |
| Sin cruce con el listado del MEC | — | 1.273 | 163.449 | 23,8 |
| Nombre exacto, **una sola sede** | alta | 62 | 150.188 | 21,8 |
| Por similitud, una sola sede | media | 100 | 75.996 | 11,0 |
| Candidato a revisar (similitud entre 0,60 y 0,80, no asignado) | — | 86 | 26.456 | 3,8 |
| Lugar o campus en el nombre | alta | 15 | 8.708 | 1,3 |
| Por similitud, varias sedes | baja | 9 | 4.273 | 0,6 |
| Solo el departamento en el nombre | media | 2 | 596 | 0,1 |

Lectura: **del 72 % ubicado, más de la mitad (38 puntos) tiene confianza baja**, porque son las grandes universidades con varias sedes (Católica, UTCD, del Norte, UTIC, entre otras). Ahí el título no dice dónde se estudió.

## Sensibilidad declarada: ¿y si en vez de la sede principal se reparte parejo entre los campus?
El **23,6 % de los títulos ubicados cambia de lugar** entre los dos escenarios. Participación por departamento:

| Departamento | Sede principal | Reparto parejo |
|---|---|---|
| Central | 25,9 % | 17,5 % |
| Asunción | 25,3 % | 15,3 % |
| Alto Paraná | 16,5 % | 11,4 % |
| Caaguazú | 8,1 % | 10,2 % |
| Itapúa | 6,2 % | 9,2 % |
| Concepción | 2,4 % | 4,9 % |

Lectura: con la sede principal, Asunción y Central juntos concentran el 51 % de los títulos; con el reparto parejo, el 33 %. **El resultado por distrito depende de este supuesto**; cualquier indicador que use estos títulos debe correrse en los dos escenarios.

## Qué se encontró en el camino (no estaba previsto)
1. **El listado del MEC no incluye muchas universidades privadas grandes** (Universidad Privada del Guairá, San Lorenzo, Metropolitana, del Sol, San Carlos, Autónoma San Sebastián, Sudamericana, Central del Paraguay, entre otras). No es un problema de nombres: no están en ningún año del archivo. Son la mayor parte del 23,8 % sin cruce. Se necesita otra fuente de ubicación.
2. **Falsos positivos en la similitud de 0,80 exacto.** Unos 6 cruces con 4 de 5 palabras en común son dudosos (por ejemplo «Instituto Técnico Superior TESA Paraguay» quedó con «Inst. Téc. Superior del Paraguay»). Pesan cerca de 1.300 títulos (0,2 %). Las reglas declaradas los aceptan y no se cambiaron; **todos los cruces por similitud menores a 0,90 quedan marcados para revisión** (3,9 % de los títulos). Subir el umbral sería una decisión metodológica.
3. **La sede principal por «más filas» es una pista débil:** para varias universidades las filas empatan y decide el desempate (Asunción primero, luego la capital departamental). Aun así quedan marcadas «revisar».
4. **Inconsistencia en la tabla de distritos:** **Vallemí (Concepción)** figura en el listado del MEC y no existe en nuestras tablas (ni en el Censo 2011, ni en los límites de 2012, ni en las ciudades del Censo 2022). Quedó sin emparejar y marcado; hay que revisar `puente_distritos_2022.csv`. El nombre «1º de Marzo» se emparejó con «Primero de Marzo» por alias y «Fernheim» (colonia) con Filadelfia; los demás nombres se emparejaron por similitud dentro del departamento (`titulos_ajustes_distritos.csv`).
5. Refinamientos de las reglas, sin cambiar los umbrales: se amplió la lista de abreviaturas (EDUC., GRAL., MCAL., DR., REG., ESC.); los nombres del MEC con las mismas palabras cuentan como una sola institución; en un empate de sedes, Asunción tiene prioridad sobre la capital departamental.

## Limitaciones
- El listado de campus es de 2018: no incluye instituciones ni sedes posteriores.
- Un título dice dónde se formó la persona, no dónde vive o trabaja hoy.
- El registro de títulos solo es completo desde 2013.
- Resultados como asociación, no causalidad.

## Qué falta para llegar a la meta del 90 %
1. **Revisar los 86 candidatos** de similitud entre 0,60 y 0,80 (3,8 % de los títulos): `puente_titulos_institucion.csv`, filas con `metodo_ubicacion = candidato_a_revisar`.
2. **Ubicar las universidades que el MEC no lista**: paso (d) de D17 (búsqueda en la web de las instituciones que concentran el 80 % de los títulos), y/o la tabla de ANEAES (792 programas acreditados con su sede), que es una fuente nueva no declarada en D17.
3. Que el equipo valide las filas con `revisar = True`.
