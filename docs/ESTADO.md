# Estado del proyecto TAPE

Actualizado: 2026-10-16. Para ponerse al día: leer este archivo, luego `CLAUDE.md` (resumen técnico y reglas), `docs/PLAN_fase0_fase1.md` (plan, decisiones y estado por tarea) y `docs/COLABORACION.md` (cómo trabajar de a dos). Un resumen para repartir el trabajo está en `docs/TAPE_pasos_siguientes.pdf` (y `.docx`).

## Hasta dónde llegamos
**Fase 0 (fundamentos) cerrada. La Fase 1 (módulo nacional) está cerrada preliminarmente (2026-10-14); sigue la Fase 2 (territorial).** Hay 303 pruebas automáticas que pasan (`uv run pytest`). Resumen de resultados, decisiones y pendientes: `docs/informe_fase1.md`. Las secciones siguientes de este archivo son el diario de trabajo en orden cronológico (lo más viejo arriba).

**Estado de la Fase 2 (2026-10-16), para retomar:**
1. Leer `docs/informe_fase1.md`, `CLAUDE.md`, `docs/supuestos_fase2.md` (declaración previa de Ever, decisiones D19-D26, renumeradas) y las últimas filas de `docs/supuestos.md` (D17, D18, Vallemí, D27 final, D28).
2. **Hecho:** registro de títulos del MEC guardado (`data/raw/mec_titulos/`, sin versionar) y sus instituciones ubicadas por distrito (D17-D18, `docs/titulos_instituciones.md`: 90,0 % de los títulos, con una validación preliminar de 26 instituciones); cruce carrera → sector (D27 final, `docs/carrera_sector.md`: 99,9 % de los títulos clasificados) y exigencia de formación por NBER (D28). También: Censo Económico 2011 por distrito (`docs/censo_2011.md`), equivalencia de distritos (`docs/distritos.md`, con la nota de Vallemí), tabla Censo → sector (`docs/censo_sector.md`) y 17.080 industrias del MIC por distrito y sector (`docs/mic_especifico.md`).
3. **Decisión de Joaquín sobre el backtest territorial:** se prueba igual, restringido a manufactura (cruzando CIIU y sectores TAPE de 2010 y 2026), primero con la densidad sola y luego con capas si hay series con dos cortes; si no funciona, se pasa a diagnóstico (emparejar las capacidades de los productores con las del territorio). **Pendiente antes de correr:** actualizar `docs/supuestos_fase2.md` con esa decisión y commitearlo; declarar que el MIC 2026 es un stock y que el Censo 2011 y el MIC no miden igual.
4. **Ejemplo de aplicación (2026-10-16):** `docs/ejemplo_aplicacion_ch.md` y `docs/figuras/ejemplo_ch_S40_S09.png` muestran cómo se usa el capital humano con una industria que exige formación específica (S40) y una que no (S09); es una ilustración con una regla simple, sin validar. **Hecho (D30):** proximidad geográfica del pool de capital humano (`docs/proximidad.md`, escalas de 15, 30 y 60 km; dos índices v1 y v2). **Hecho (D29):** base de capital humano por distrito (`docs/base_capital_humano.md`: escolaridad estimada, distancia a salud, graduados transversales e índice). **Pendiente de decisión de Joaquín:** si se cambia la medida de la tercera parte (casi todos los distritos tienen cero graduados transversales ubicados).
5. **Pendientes de validación del equipo:** `data/clean/validacion_instituciones.csv` (26 validadas preliminarmente, 61 candidatas sin validar), `data/clean/puente_carrera_sector.csv`, los 4 distritos nuevos sin ley (Ybyrarobana, Karapa'í, Itacuá, Boquerón) y María Antonia, la carpintería del MIC y la cola de 802 actividades, las filas de baja confianza del puente del censo (109, 10, 23, 239), la lista de reexportaciones con la aduana, y la referencia oficial de exportaciones (BCP o DNA).
6. **Datos por conseguir:** Registro Nacional de Carreras del MEC (ubicaría las universidades sin acreditación y daría la oferta actual por sede), nivel educativo del Censo 2022 por distrito (INE; reemplazaría la estimación de escolaridad) y un listado completo de establecimientos de salud (hoy 212).
7. **Decisiones abiertas heredadas:** categorías residuales en los candidatos; D10 (ε, Fase 3); consolidar los borradores de Ever; replicar la diferencia de AUC-PR de +0,0006 a HS6; versión dinámica y régimen fiscal como mejoras.
8. Herramienta de Paraguay 2019 (artefacto privado, v4): https://claude.ai/artifact/LgLsQUrZ9gAMS4JHnSg4qV; se regenera con `src.herramienta.exportar_pry` y `construir_pagina`.
9. **Git:** rama `develop` (producción es `main`, los cambios entran por PR). Para correr lo nuevo: `uv run python -m src.puentes.titulos_instituciones`, luego `src.puentes.exigencia_sector` y `src.puentes.carrera_sector`.

**Decisión D2 (2026-10-13):** coeficientes con la especificación del documento (efectos país-año y producto-año, errores agrupados por país); backtest con efectos de país y producto constantes más indicador de ventana, prediciendo la ventana siguiente; Mundlak solo para países excluidos y Paraguay. Los errores estándar agrupados ya están en `logit_disperso.py` (`errores_agrupados`); falta repetir el baseline fuera de muestra.

**Decisión D14 (2026-10-13):** la primera edición del LPI (2007) se arrastra hacia atrás para tener logística en 2000 y 2005 (marca `lpi_hacia_atras`); robustez con las ventanas de datos reales.

**Decisión D13 (2026-10-13):** presencia para φ y densidad = RCA ≥ 1 en 2 de los 3 años de calendario que terminan en t.

**Decisiones tomadas el 2026-10-12** (detalle en `docs/supuestos.md`): D3 (proximidad con ventana de 5 años que termina en t; la distancia del Atlas solo como control), D4 (intensidades con NBER-CES, puente NAICS → HS de Pierce y Schott, energía con el **precio de la electricidad** de Doing Business) D6 (reexportaciones marcadas por regla automática, a revisar después con la aduana), **D7** (entrada de un solo año como principal y «2 de 3 años» como robustez; el promedio móvil de 3 años se descartó) y **D8** (población ≥ 1 millón y exportaciones ≥ USD 1.000 millones: 112 a 144 países, ≈ 97 % del comercio). Siguen abiertas D1, D2 y D10.

**Tareas de la Fase 1:**
| Tarea | Estado |
|---|---|
| 1.5 Dotaciones por país | **Hecha** (`docs/dotaciones.md`): capital humano, crédito, energía (precio) y logística, 235 países × 1990-2024 |
| 1.6 Requisitos por producto | **Hecha** (`docs/puente_requisitos.md`): energía, capital, habilidades y valor/peso para 1.242 productos HS4 |
| 1.2, 1.3, 1.4, 1.7, 1.8 | **Borradores de Ever en `src/modelos/`**; baseline de densidad sola subido el 2026-10-12 (dentro de la muestra, sin D2). Revisión y cambios pedidos: `docs/NOTA_revision_modelos_Ever.md`. Van a pasar a las versiones livianas `densidad_np.py` y `logit_disperso.py` (ver `docs/optimizacion_modelos.md`) |
| 1.9 Logit con capas | **Primera versión provisoria** (`src/modelos/logit_nacional.py`, `docs/resultado_logit_provisorio.md`): la densidad predice las entradas; capital humano es significativo pero pierde fuerza al controlar por PIB per cápita (no se separa del desarrollo general); energía y crédito no se distinguen de cero; logística sale con signo contrario al esperado, no se explica por desarrollo y no es robusta (depende de D14); se decide con el backtest. Capa nueva `capital_fisico` (PWT): no aporta señal propia pero amplía la muestra (97 países en 2000 contra 59); D15 decidida (capital físico en lugar del crédito; el crédito queda como robustez) |
| 1.11 Backtest | **Primera versión** (`src/modelos/backtest_nacional.py`, `docs/resultado_backtest.md`): fuera de muestra, **el modelo con capas no supera a la densidad sola** (diferencias de ±0,004 en precision@20 por país, intervalos que incluyen el cero); la condición de paso a la Fase 2 no se cumple todavía. Controles hechos (`docs/resultado_backtest.md`): **XGBoost con SHAP (1.10) y la variante sin efectos fijos tipo Mundlak no cambian la conclusión**: las capas no mejoran la predicción; las interacciones r·a no aportan. **Prueba de corte transversal (¿las dotaciones explican lo que se produce hoy?, `presente.py`, `docs/resultado_presente.md`, declarada antes de correrla): en parte. Capital humano (0,19) y tierra cultivable (0,22) sí, estables en los cuatro años; capital físico débil; energía no; la logística da signo contrario (−0,09) también aquí. Criterio no cumplido en el bloque de manufactura (2 de 4), cumplido en el de tierra.** **Extensión con todos los recursos naturales (`recursos.py`, declarada antes de correrla): criterio no cumplido (3 de 6 términos nuevos): petróleo, gas y carbón sí (reservas por persona), minerales solo si los países ausentes del USGS cuentan como cero; agua dulce e hidro no.** **Paso 3 del plan (entrada por sector TAPE, `backtest_sector.py`, declarado antes de correrlo): criterio no cumplido; dirección positiva en 2 de 3 ventanas (+0,011 y +0,009 en precision@5) con el intervalo tocando el cero y solo 67 a 96 entradas por ventana: indicio débil.** **Requisito revelado probado (paso 2 del plan, `backtest_revelado.py`): tampoco supera a la densidad sola** (criterio declarado no cumplido en 6 de 6 combinaciones), ni con efectos fijos ni sin ellos (`backtest_revelado_mundlak.py`, declarado antes de correrlo). **Robustez de la definición de la entrada hecha** (h = 10, 2 de 3 años y tres umbrales de RCA): el resultado no cambia. Falta: casos de Paraguay, países excluidos, HS6 y D1 para el informe |
| 1.1, 1.10 | Pendientes |

**Régimen fiscal, v0 (2026-10-14):** capa «impuesto bajo a las utilidades» = menos la tasa del impuesto sobre las utilidades de Doing Business (`PAY.TAX.PRFT.CP.ZS`, 2005-2019, 186 países; después de 2019 se arrastra el último dato y se marca). Paraguay: 9,6 %. **Solo es la tasa general**: no incluye la maquila (1 %) ni los regímenes exportadores de los países de referencia (v1, por codificar con las leyes); y la medida de Doing Business es para una empresa tipo y tiene rarezas (Argentina aparece con 0 a 4 % con una tasa legal del 35 %), a contrastar con una tabla de tasas legales.

**PWT 11.0 y salario (2026-10-14):** `data/raw/pwt/pwt110.xlsx` reemplaza a 10.01 para capital humano, capital por trabajador y salario, que ahora llegan hasta 2023 (`data/raw/pwt/README.md`). Nueva capa: **mano de obra barata** = menos el logaritmo de la remuneración media por trabajador en USD corrientes (promedio de toda la economía, 139 países; Paraguay 2019: USD 6.090, más que Marruecos y Nicaragua). **Los resultados de los modelos anteriores (backtest, regresiones, cuadro de bloques) se hicieron con PWT 10.01 y se verificaron con 11.0 (`docs/verificacion_pwt110.md`): las conclusiones no cambian.**

**Ficha de brechas, prototipo (2026-10-13):** `docs/ficha_brechas_prototipo.md` (arneses HS 8544 y etanol HS 2207): percentil de Paraguay en cada dotación frente a los productores, a los de ingreso parecido y a los productos vecinos; arneses entró con brechas de capital humano y capital por trabajador (la entrada vino por maquila), etanol casi sin brechas. Descriptivo, no predictivo.

**Mapa de brechas de compatibilidad (2026-10-14):** `docs/mapa_brechas.md`. Índice de brechas de todos los productos contra todos los productores y los de ingreso similar, con ámbito alternativo de cercanos no exportados. No agrega a la densidad (AUC) y la regla de tolerancia estricta con reservas rechaza el 95 % de lo que Paraguay ya exporta; pendiente decidir cómo tratar las reservas. Segunda versión con relevancia revelada y límite duro (`mapa_limites.py`): control de sensatez ok (78 %), 18 límites duros entre los 277 cercanos; la hipótesis del exceso como costo de oportunidad NO se cumple (signo contrario).

**Cuadro de bloques × dotaciones (2026-10-13):** `docs/resultado_bloques.md` y `docs/figuras/bloques_dotaciones_2015.png`: los recursos se asocian con sus bloques (tierra y agua con primarios agropecuarios; petróleo y gas con minerales y energía), capital humano, capital por trabajador y logística con manufactura pesada y media tecnología (pero también el ingreso); Paraguay: ventaja enorme en primarios agropecuarios, tercil alto en tierra, agua y electricidad barata.

**Clasificación de productos (2026-10-13):** `src/puentes/clasificacion_lall.py` lleva la clasificación tecnológica de Lall (2000) a HS4 con confianza por fila (`docs/clasificacion_lall.md`): seis bloques para cruzar con las dotaciones.

**Recursos naturales (2026-10-13):** WDI suma tierra cultivable por persona y agua dulce renovable por persona; `src/descargas/reservas.py` baja las reservas probadas de petróleo, gas y carbón (Energy Institute vía Our World in Data, 0,5 MB; el carbón solo desde 2008). **Minerales (USGS, Mineral Commodity Summaries 2026): descargados a mano el 2026-10-13** (ScienceBase bloquea el acceso automático); `data/raw/usgs_mcs/` (3,2 MB, Windows-1252): reservas de 53 minerales en 105 países, solo 2023-2025, y los países ausentes no son necesariamente cero (Paraguay no aparece); ver su README. Entra en el zip de datos manuales.

**Fuentes internacionales descargadas** (`uv run python -m src.descargas.todas`): BACI (HS92, 1995-2024), Atlas de Complejidad, WDI (15 indicadores, incluidos el precio de la electricidad y la proporción hidroeléctrica), Penn World Table 10.01 (a mano), LPI, correspondencias de la ONU y WITS, límites administrativos, 10 tablas de SIMEL, **NBER-CES** (intensidades por industria de EE. UU.) y la **concordancia HS → NAICS** de Pierce y Schott. Ver `docs/verificacion_fuentes.md`.

**Taxonomía y puentes:** 67 sectores TAPE sobre CIIU Rev.4 (`docs/taxonomia.md`); puente HS92 → CPC → CIIU → sector con confianza por fila (`docs/puente_hs_sector.md`); tabla CNAEP → sector y subsectores MIC → sector; puente de requisitos por producto.

**Datos nacionales ya incorporados** (a mano, en `TAPE_datos_manuales.zip`; detalle en `docs/COLABORACION.md` y en el README de cada carpeta `data/raw/<fuente>/`):
- **BCP:** PIB por 33 actividades (1991-2024) y regional por 6 ramas y 18 departamentos (2021-2024); crédito por 13 sectores y banco (mensual 2020-2026/08); cuentas nacionales base 2014.
- **MIP:** simulador con la matriz de 21 sectores (autoría y año por confirmar).
- **INE:** EPHC anual 2022-2025 (rama de actividad en 8 categorías, sin CIIU más fino).
- **MAG:** Censo Agropecuario 2022: Volumen I (78 cuadros por departamento) y fincas y superficie por distrito (259 distritos; los totales cuadran con el Volumen I).
- **MTESS (SIMEL):** establecimientos y puestos inscritos (por actividad y por departamento, pero no el cruce), formación SINAFOCAL/SNPP e informalidad por departamento.
- **Educación:** carreras y programas de la ANEAES con la marca acreditada o no (792); establecimientos 2012 e instituciones 2018 del MEC (incompletos).
- **Mapa logístico del MIC** (visor sin licencia declarada; provisorio): 263 distritos con población del Censo 2022, PEA y distancias; 17.080 industrias por distrito y sector; red eléctrica; 22 rutas nacionales y fronteras; AFI y centros del SNPP; comercio por aduana (sin año declarado); 212 establecimientos de salud. La capa de combustibles no se extrajo.
- **Maquila:** informe agregado de agosto 2026.

## Qué falta
**Decisiones abiertas:** D1 (producto → sector) para el informe; D10 (umbral ε) para la Fase 3.

**Hallazgos a resolver en la Fase 1:**
- **Las capas de dotaciones están correlacionadas:** capital humano, crédito y logística entre sí (0,65 a 0,76); la energía (precio) es independiente. Decidir en la tarea 1.9 cómo tratarlo (capa por capa, control por PIB per cápita o componentes).
- **Agricultura, minería y servicios no tienen requisitos** (NBER-CES es solo manufactura; 13 % del valor mundial, incluida la soja): decidir cómo tratarlos en el modelo (tarea 1.7) y en el módulo territorial (Fase 2).
- **Código de `src/modelos/`** (ver `docs/optimizacion_modelos.md`): `depurar.py` quita la energía y las reexportaciones pero no recalcula el RCA, y la depuración no llega a la densidad; las constantes de D8 de `panel.py` no se aplican (y D7 fija la entrada de un solo año como definición principal); hay rutas fijas de Windows (`C:\ever\...`) y dos copias de la base DuckDB.
- **Precio de la electricidad:** solo existe para 2014-2019 y se aplica a todos los años; en la robustez, repetir el modelo con las ventanas desde 2015.

**Datos nacionales por conseguir:**
- Registro de títulos del MEC: **solicitud formal enviada el 2026-10-12** (títulos expedidos agregados por año, carrera, institución, nivel, campo CINE, departamento y distrito, sin datos personales). **El MEC tiene plazo hasta el 2026-11-02 para responder.** Al llegar: guardar en `data/raw/mec_titulos/`, anotar en `data/fuentes.csv` y regenerar el zip.
- Registro Nacional de Carreras del MEC (descarga manual; el sitio rechaza scripts; no se incluyó en la solicitud).
- Pedidos formales: Censo Económico 2011 por distrito (INE), régimen de materia prima (MIC) y cuadros de oferta y utilización detallados (BCP).
- Comercio exterior de Paraguay por NCM (aduana o BCP): opcional, BACI ya trae a Paraguay.
- Cultivos y ganadería del censo agropecuario por distrito, si existe otro tomo.
- Informes de maquila y de la Ley de Inversiones: última capa, complementos.
- Leyes y normas (BACN y Gaceta), ILOSTAT, licencias de SIMEL, del visor del MIC y de BACI/Atlas.
- **Para la próxima versión de la ficha de brechas (acordado el 2026-10-13, para más adelante):** (1) **salario** como capa explícita (costo de la mano de obra, por ejemplo de la manufactura, de ILOSTAT u otra fuente): es el equivalente del precio de la electricidad y probablemente decida arneses y manufactura liviana; (2) **régimen de inversión y fiscal** (maquila, zonas francas, Ley de Inversiones, incentivos) como una variable institucional, no como dotación: indicador por país y año de qué regímenes existen y para qué actividades. El régimen de maquila se trata como un instrumento de política (saltos largos, IED), no como una capacidad del territorio.

**Trabajo de datos pendiente:** reconciliar los 247 distritos de los límites de 2012 con los 263 del Censo 2022; definir carrera → CINE-F → sector cuando lleguen los títulos.

## Quién hace qué
| Persona | Tarea en curso | Rama |
|---|---|---|
| Joaquín | Datos nacionales pendientes | — |
| Ever | Modelos de `src/modelos/`: pasar a `densidad_np.py` y `logit_disperso.py`, recalcular el RCA después de depurar, aplicar la depuración a la presencia y la densidad, aplicar D7 y D8 en el panel (entrada de un solo año y variante «2 de 3 años»; filtro de países), contar la presencia D13 en años de calendario y sacar las rutas fijas | — |
| Claude Code | Hechas: 1.5, 1.6 y las versiones livianas. Siguiente: revisar los borradores de Ever contra D3, D5 y D6 cuando él los suba | — |

Una tarea por rama (`fase1/1-1-limpieza-baci`), con pruebas y lint en verde antes de cada commit. Los archivos de `src/modelos/` existentes los modifica solo quien trabaja ese módulo.

## Cómo reproducir todo
```bash
uv sync
uv run python -m src.descargas.todas     # fuentes automáticas (≈ 4 GB)
# descomprimir TAPE_datos_manuales.zip (Drive) en la raíz del repositorio
uv run python -m src.reconstruir_todo    # tablas limpias, puentes, requisitos y dotaciones
uv run pytest
```
Para regenerar el zip: `uv run python -m src.empaquetar_datos_manuales`.

**Prototipo de la herramienta, Paraguay 2019 (2026-10-14, rama `develop`):** `src/herramienta/` (`exportar_pry.py` arma el JSON con coordenadas del espacio producto, estado, capacidades y productores por producto; `plantilla.html` y `construir_pagina.py` generan la página). Mapa de 1.239 productos coloreado por estado, lista filtrable y ficha por producto. Publicada como artefacto privado: https://claude.ai/artifact/LgLsQUrZ9gAMS4JHnSg4qV. Descriptivo: la ficha dice «brecha respecto de los productores», no probabilidad. Pendiente: nombres en español, otros países y años, comparación contra Costa Rica.

**Censo Económico 2011 por distrito (2026-10-14):** el Cuadro 1 sirve (224.242 unidades, 799.153 ocupados, 234 distritos, sumas exactas); limpio en `data/clean/censo2011_*.csv` (`docs/censo_2011.md`). Falta la equivalencia de distritos (solo nombres) y una tabla Censo → sector TAPE porque los códigos de 3 dígitos de alimentos, bebidas y químicos no son la CIIU Rev.4 internacional.

**Equivalencia de distritos (2026-10-14):** `docs/distritos.md`. Los 234 distritos del Censo 2011 tienen un polígono de 2012; las 17.080 industrias del MIC y las 263 ciudades de 2022 quedan en la unidad del censo (correlación 0,81 entre industrias MIC 2026 y manufactura del censo). 20 de los 24 distritos nuevos con padre confirmado por ley (9 correcciones, 11 confirmaciones; varios padres = partes iguales); 4 siguen con padre inferido (`baja`) y María Antonia sin unidad; el censo tiene 238 distritos, no 234 (cuatro vienen solo con su total) para validar con las leyes de creación. Falta la tabla Censo 2011 → sector TAPE.

**Tabla Censo 2011 → sector TAPE (2026-10-14):** `docs/censo_sector.md`. 228 códigos con pesos y confianza; las 224.242 unidades quedan asignadas. 78 % de la manufactura con confianza alta; el 21 % baja se concentra en 109, 10, 23 y 239. Seis códigos del censo no son la CIIU internacional (107, 109, 111, 112, 202, 209) y se resolvieron por nombre. Corrección de la limpieza: 238 distritos (no 234) y 24 distritos nuevos (no 28). Pendiente: elegir el nivel del backtest (sector o grupo).

**Limpieza de BACI (2026-10-14):** `docs/baci_limpieza.md`. El zip de CEPII se procesa con `src.limpieza.baci` (exportaciones e importaciones HS6 1995-2024); la tabla HS4 de los modelos coincide con la anterior, ya no depende de la base de Ever. Pendiente: referencia oficial de exportaciones de Paraguay. Siguen para cerrar la Fase 1: depuración D6 (reexportaciones), HS6, países excluidos, casos de Paraguay, D1, consolidar el código de Ever e informe.

**Depuración D6 (2026-10-14):** `docs/depuracion_d6.md`. La regla M ≥ 0,5·X marca 38 % del comercio mundial (también EE. UU. y Alemania por comercio intraindustrial) y 3 a 7 % de lo que exporta Paraguay sin energía; el backtest con la tabla depurada mantiene la conclusión sobre las capas. Decisión pendiente: alcance de la marca (recomendado: Paraguay y centros de reexportación).

**Alcance de la depuración D6 decidido (2026-10-14):** la marca se aplica solo a Paraguay, Hong Kong, Singapur, Países Bajos y Bélgica (`PAISES_DEPURADOS`); el backtest con esa tabla cumple el criterio de robustez (capas sin mejora, densidad sin cambio mayor a 0,01). Falta la revisión de la lista de productos marcados con la aduana.

**Pruebas del punto 3 de 1.11 (2026-10-14):** `docs/resultado_punto3.md`. HS6: la densidad ordena 3,5 a 4,1 veces mejor que el azar y las capas no mejoran la lista corta (AUC-PR +0,0006 en 2005 y 2010, a replicar); países excluidos comparables: lift 2,10 de la densidad, capas sin mejora detectable; casos de Paraguay: solo el etanol (puesto 8 de 1.019) se anticipaba; arneses no. Falta para cerrar la 1.11: D1 (producto → sector) y el informe de la Fase 1.

**D1 decidida y primera lista de sectores candidatos (2026-10-14):** `docs/candidatos_sector.md` (media ponderada por comercio mundial, máximo y conteo en el top 100; corte 2024; las puntuaciones ordenan, no son probabilidades). Para cerrar la Fase 1 falta el informe (`docs/informe_fase1.md`), con la sección explicativa de la densidad (Hidalgo y Hausmann) que pidió el equipo, y dos pendientes externos: la revisión de la aduana y la referencia oficial de exportaciones de Paraguay.

**Informe de la Fase 1 (2026-10-14):** `docs/informe_fase1.md`. Resume resultados, decisiones D1 a D16, limitaciones, pendientes y cómo reproducir; incluye la explicación de la densidad. La Fase 1 queda lista para cerrar en lo analítico, a confirmación del equipo.

**Herramienta v3 (2026-10-14):** mapa con tres modos (estado, cercanos y complejos, cercanos que suben), vecinos del producto elegido con su cercanía y complejidad relativa, glosario sin tecnicismos y resumen «en palabras simples» en cada ficha. Año 2019.
