# Registro de supuestos y decisiones

Formato: fecha · decisión · alternativa descartada · motivo · quién decidió.

| Fecha | Decisión | Alternativa descartada | Motivo | Quién |
|---|---|---|---|---|
| 2026-10-08 | Gestión del entorno con `uv`, Python 3.12 | venv + requirements.txt | Reproducibilidad con `uv.lock` | Claude (propuesto) |

| 2026-10-08 | Carreras del MEC se vinculan a CIIU/sector TAPE, no a HS (D11) | Vincular carreras a listas de HS | CIIU es la lengua común; HS solo para comercio | Joaquín |
| 2026-10-08 | CIIU Rev.4 es la lengua común; átomo = división de 2 dígitos (01 partida en 014 y 01x) | Mapear cada clasificación directo a sector TAPE | Auditable; el crédito y las cuentas regionales parten la sección A | Claude (propuesto), pendiente de confirmar D12 |
| 2026-10-08 | Se excluyen CONSUMO, VIVIENDA (crédito) e Impuestos (regionales): no son actividades económicas | Mantenerlas como categorías sin CIIU | Decisión de Joaquín | Joaquín |
| 2026-10-08 | Mapa MIC: se leyó la tabla F4 del visor Zoho con el navegador (17.080 industrias, 73 subsectores, 1.744 sectores específicos) y se guardó el resumen sector-subsector en data/raw/mic_mapa/ | Pedir descarga al MIC | El visor no ofrece descarga; solo se registra lo visible públicamente | Claude (propuesto) |
| 2026-10-08 | D9: la taxonomía de sectores TAPE parte de CIIU Rev.4, con manufactura y agroindustria desagregadas | Partir de subsectores MIC | Internacional y auditable; el MIC ya se mapea a CIIU | Joaquín |
| 2026-10-08 | D5: HS92 a 4 dígitos para estimar; 6 dígitos para el puente a CIIU y robustez | HS6 en todo | Más entradas por producto, menos ruido; sigue el documento técnico | Joaquín |
| 2026-10-08 | D12: unidad común CIIU Rev.4 a 2 dígitos (bajando a 3-4 donde haga falta) y sector TAPE encima | Mapear cada clasificación directo a sector TAPE | Permite auditar cada salto | Joaquín |
| 2026-10-08 | PWT no se pudo bajar por script: el servidor devolvió una página anti-bots. Se baja a mano; el script ahora rechaza respuestas HTML | Sortear la protección | No se evaden protecciones del sitio | Claude |
| 2026-10-08 | PWT 10.01 (no la 11.0) como fuente de capital humano y stock de capital; hasta 2019 | Esperar la 11.0 | La bajó el usuario a mano; las dotaciones se miden al inicio de ventana (t ≤ 2015), no se necesita 2020 | Joaquín |
| 2026-10-08 | Se mantiene la taxonomía de sectores TAPE (66) y se añade 1 sector forzado por el BCP: confitería y pastas separada de panificados (67 en total) | Reducir a 40-60 | Aprobado por Joaquín; el sector extra lo exige la herencia de grupos con las 33 actividades | Joaquín |
| 2026-10-08 | Biocombustibles se identifican por producto HS en el puente, no por sector CIIU | Asignarlos por clase CIIU | La CIIU no tiene clase propia | Joaquín (acepta la recomendación) |
| 2026-10-08 | Arneses de maquila se asignan a Autopartes y vehículos, por producto HS | Electrónica y equipo eléctrico (CIIU 27) | Es el caso central del documento técnico | Joaquín (acepta la recomendación) |
| 2026-10-08 | Mapeo de las 33 actividades del BCP a CIIU es supuesto por nombre; educación y salud se reparten entre privado (hogares) y público (gubernamentales) | Esperar la nota metodológica del BCP | Permite avanzar; se revisa cuando llegue la nota | Claude (propuesto) |
| 2026-10-08 | Tabla oficial CNAEP 1.0 <-> CIIU Rev.4 (BCP 2016) extraida del PDF: 604 codigos de 5 digitos; 14% (85 codigos) con alineado aproximado, 7 filas corregidas a mano contra el texto | Digitar la tabla a mano | La extraccion reproduce la tabla; las filas aproximadas quedan con confianza media | Claude (propuesto) |
| 2026-10-08 | Biocombustibles: la CNAEP los trae como grupo propio (2020x) que corresponde a CIIU 2011; en TAPE quedan en Quimicos basicos y se identifican por producto HS | Sector propio | Se mantiene la decision previa; la CNAEP permite identificarlos en datos nacionales | Joaquin (acepta la recomendacion) |
| 2026-10-08 | Las 33 actividades del BCP se mapean a CIIU con la definicion oficial del SCN base 2014 (reemplaza mis supuestos). Cambios: almidon (1062) con otros alimentos; ganaderia incluye apoyo pecuario (0162) y caza (017); telecomunicaciones = divisiones 58 a 63; agencias de viaje en servicios a empresas | Mapeo por nombre | Documento oficial entregado por el usuario | Claude, con documentos del BCP |
| 2026-10-08 | Molineria (1061) se separa de almidones; los almidones pasan al sector de otros alimentos (siguen siendo 67 sectores) | Mantenerlos juntos | Si no, el sector cruzaria dos actividades del BCP | Claude (propuesto) |
| 2026-10-08 | Cuentas regionales: la serie disponible es 2021-2024 (el documento tecnico decia 2021-2023); 18 departamentos incluyendo Asuncion; el MEC se incorporara mas adelante y la equivalencia carrera-actividad se decidira con el clasificador (CINE-F de UNESCO u otro) | Esperar | Decision de Joaquin | Joaquin |
