# Registro de títulos del MEC: ubicación de las instituciones

Fecha: 2026-10-15. Código: `src/puentes/titulos_instituciones.py` (18 pruebas en `tests/test_titulos_instituciones.py`). Reglas declaradas antes de construir: D17 y D18 en `docs/supuestos.md`.
Salidas (en `data/clean/`, sin datos personales): `titulos_conteos.parquet`, `puente_titulos_institucion.csv` (una fila por institución), `titulos_institucion_distrito.csv` (pesos por distrito en los dos escenarios), `titulos_sensibilidad_departamento.csv`, `titulos_ajustes_distritos.csv`, `titulos_aneaes_sedes_sin_distrito.csv`, `validacion_instituciones.csv` (planilla para el equipo) y `ubicaciones_web_instituciones.csv` (intentos de búsqueda en la web).

## En palabras simples
El registro de títulos dice **qué institución** dio el título, pero no **en qué distrito**. Para ubicarla se cruza el nombre de la institución con dos listados que sí traen la sede: el del MEC (2018) y el de ANEAES (programas acreditados).
- Si la institución tiene **una sola sede**, el título va a ese distrito.
- Si tiene **varias** y el nombre no dice cuál, no sabemos dónde se estudió: se asigna a la sede principal con confianza **baja**, y se calcula también un escenario que reparte parejo.
- Si el nombre dice el lugar («– Caacupé», «Sede Encarnación»), se usa ese lugar.

**Resultado: se ubicó el 88 % de los títulos 2013-2025, pero solo el 18 % con confianza alta y la mitad (50 %) con confianza baja.** La meta de 90 % no se cumple todavía; con la validación del equipo de los candidatos pendientes el techo es 91,8 %.

## Fuentes y ventana
- Registro de títulos (`data/raw/mec_titulos/`): 688.161 títulos de 2013 a 2025, 1.579 nombres de institución una vez normalizados.
- Listado de instituciones del MEC de 2018, educación superior: 819 filas, 430 instituciones, 133 distritos.
- ANEAES (`aneaes_programas.parquet`): 792 programas acreditados; 140 sedes ubicadas en un distrito (20 no: departamentos solos, «No aplica» y hospitales; `titulos_aneaes_sedes_sin_distrito.csv`).
- Tabla de distritos de TAPE (`puente_distritos_2022.csv`) para llevar cada campus a su departamento y distrito.

## Resultado (control)
| Cómo se ubicó | Confianza | Instituciones | Títulos | % de los títulos |
|---|---|---|---|---|
| Nombre exacto, institución con **varias sedes** (sede principal) | baja | 46 | 325.297 | 47,3 |
| Nombre exacto, **una sola sede** | alta | 55 | 117.661 | 17,1 |
| Nombre exacto, una sola sede **solo según ANEAES** | media | 22 | 79.916 | 11,6 |
| Por similitud (≥ 0,80), una sola sede | media | 95 | 55.934 | 8,1 |
| Por similitud, varias sedes | baja | 12 | 17.808 | 2,6 |
| Lugar o campus en el nombre | alta | 15 | 8.708 | 1,3 |
| Solo el departamento en el nombre | media | 2 | 596 | 0,1 |
| **Total ubicado** | | | | **88,0** |
| Candidato a revisar (similitud entre 0,60 y 0,80, no asignado) | — | 87 | 25.677 | 3,7 |
| Sin cruce | — | 1.245 | 56.564 | 8,2 |

Confianza sobre el total de títulos: alta 18,4 %, media 19,8 %, baja 49,9 %. Un 25 % de los títulos ubicados queda marcado `revisar` (cruces por similitud menores a 0,90, institución solo en ANEAES, empates de sedes).

Lectura: las grandes universidades con varias sedes (Católica, UTCD, del Norte, UTIC, la UNA y otras) concentran la mayor parte, y de ellas no se sabe en qué sede se estudió.

## Qué aportó cada fuente
- **ANEAES** subió lo ubicado de 72 % a 88 % (bajó el sin cruce de 24 % a 8 %): las universidades privadas grandes que el listado del MEC no incluye (Privada del Guairá, San Lorenzo, Metropolitana, del Sol, San Carlos, Autónoma San Sebastián y otras) figuran en ANEAES. **Límite:** ANEAES solo lista programas acreditados. Una universidad con una sola sede acreditada puede tener otras sedes sin acreditar; por eso esas 22 instituciones (11,6 % de los títulos) quedan con confianza media y marcadas `revisar`. Por ejemplo, la Universidad Privada del Guairá aparece con una sola sede (Villarrica), pero el registro mismo menciona sedes en Encarnación y San Juan Nepomuceno.
- **Búsqueda en la web (paso (d) de D17, ampliado en D18):** se buscaron las 6 instituciones más grandes sin ubicar (Ateneo de Lengua y Cultura Guaraní, Universidad Hispano Guaraní, Universidad de Desarrollo Sustentable, Instituto Superior Interregional en Ciencias de la Salud, Universidad Interamericana, Instituto de Lingüística Guaraní). **Ninguna tiene una fuente oficial que dé la sede**: las leyes que las crean no fijan domicilio, las páginas oficiales no la muestran y los directorios y notas de prensa se contradicen. Como D18 acepta solo fuentes oficiales, **no se asignó ninguna** y los intentos quedaron registrados en `ubicaciones_web_instituciones.csv`.

## Sensibilidad declarada: sede principal contra reparto parejo
El **18,6 % de los títulos ubicados cambia de lugar** entre los dos escenarios.

| Departamento | Sede principal | Reparto parejo |
|---|---|---|
| Asunción | 29,2 % | 21,2 % |
| Central | 25,0 % | 17,5 % |
| Alto Paraná | 13,6 % | 10,7 % |
| Caaguazú | 7,2 % | 8,0 % |
| Itapúa | 5,1 % | 7,7 % |
| Guairá | 5,1 % | 6,8 % |
| Amambay | 2,6 % | 4,8 % |

Lectura: con la sede principal, Asunción y Central juntos concentran el 54 % de los títulos; con el reparto parejo, el 39 %. **El resultado por distrito depende de este supuesto**; cualquier indicador que use estos títulos debe correrse en los dos escenarios.

## Hallazgos que conviene tener presentes
1. **Los cruces por similitud de 0,80 exacto incluyen unos 6 falsos** (≈ 0,2 % de los títulos), por ejemplo «Instituto Técnico Superior TESA Paraguay» con «Inst. Téc. Superior del Paraguay». El umbral se mantuvo en 0,80 por decisión de Joaquín (D18); los cruces menores a 0,90 quedan marcados `revisar`.
2. **La sede principal por «más filas» es una pista débil:** para varias universidades las filas empatan y decide el desempate (Asunción primero, luego la capital departamental).
3. **Vallemí no es un distrito aparte: es la localidad principal del distrito de San Lázaro (Concepción).** El listado del MEC de 2012 y 2018 lo trae como una fila suelta, pero los datos oficiales (Censo Económico 2011, ciudades del Censo 2022, los 14 distritos de Concepción del MEC 2023 y los límites de 2012) no lo listan, y Puerto Vallemí (el hospital del IPS y la subestación de 220 kV) cae dentro del polígono de San Lázaro. Una acordada de la Corte Suprema y una nota de Última Hora confirman que Vallemí pertenece al distrito de San Lázaro. Por eso el campus «Vallemí» del MEC se asigna a **San Lázaro** (alias en el código) y **las 55 industrias del mapa MIC y los demás datos de «San Lázaro» son, en lo esencial, de Vallemí**. Si existiera una ley reciente que lo cree como distrito, haría falta su límite, que no tenemos.
   «1º de Marzo» se emparejó con «Primero de Marzo» y «Fernheim» con Filadelfia por alias; los demás nombres, por similitud dentro del departamento (`titulos_ajustes_distritos.csv`).
4. Refinamientos de las reglas, sin cambiar los umbrales: más abreviaturas (EDUC., GRAL., MCAL., DR., REG., ESC.); los nombres del MEC con las mismas palabras cuentan como una institución; en un empate de sedes, Asunción tiene prioridad.

## Limitaciones
- El listado de campus es de 2018 (más ANEAES, que no tiene fecha de sedes): no incluye instituciones ni sedes posteriores.
- Un título dice dónde se formó la persona, no dónde vive o trabaja hoy.
- El registro de títulos solo es completo desde 2013.
- Resultados como asociación, no causalidad.

## Qué falta para llegar a la meta del 90 %
1. **Validación del equipo de los 87 candidatos** (3,7 % de los títulos): `validacion_instituciones.csv`, ya con el candidato propuesto, sus distritos, la similitud y una **sugerencia de Claude** (26 «probable_si», 11 «dudoso», 50 «probable_no»; es una lectura de los nombres, no una verificación). Se marca `validado = si` en las que sean la misma institución y se vuelve a correr el módulo (`uv run python -m src.puentes.titulos_instituciones`); las validadas se ubican con confianza media. Si se validan todas, el techo es 91,8 %; si solo se validan las 26 «probable_si» (13.218 títulos), se llega a 90,0 %.
2. Para las instituciones sin cruce que más pesan, una fuente oficial con la sede: pedirla al MEC (la solicitud ya enviada pedía distrito) o al CONES, que regula las universidades.
3. Revisar las filas con `revisar = True` de las universidades grandes (UPG y otras con sedes no acreditadas).
