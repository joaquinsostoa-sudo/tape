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
