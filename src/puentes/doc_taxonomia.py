"""Genera docs/taxonomia.md a partir de data/clean/taxonomia_sectores_tape.csv."""
from __future__ import annotations

import pandas as pd

from .taxonomia_tape import RAIZ

PLANTILLA = """# Taxonomía de sectores TAPE (tarea 0.4)

Archivo: `data/clean/taxonomia_sectores_tape.csv`. Código y validaciones: `src/puentes/taxonomia_tape.py`, `tests/test_taxonomia_tape.py`. Este documento se genera con `src/puentes/doc_taxonomia.py`.

**{n} sectores** ({con} de bienes con código HS y {sin} de servicios, construcción y energía), sobre CIIU Rev.4 (decisión D9). Los ids se asignan por orden y cambian si se inserta un sector.

## Criterios de corte
1. **Base CIIU Rev.4.** Cada sector es una lista de prefijos (división, grupo o clase). Se desagrega más donde Paraguay tiene espacio producto (alimentos, textil y cuero, metales, químicos). Los servicios quedan agrupados porque no entran al espacio producto.
2. **Partición exacta.** Cada clase CIIU de las secciones A-S cae en un solo sector (prueba automática contra la tabla oficial de la ONU). Se excluye la división 99.
3. **Herencia de grupos.** Ningún sector cruza los grupos de EPHC, crédito BCP, cuentas regionales, MIP ni las 33 actividades del BCP, así cada sector hereda un solo grupo de cada clasificación. Esto obligó a separar comercio mayorista de minorista, agencias de viaje de alojamiento, ganadería de cultivos y panificados de confitería y pastas (el BCP los pone en actividades distintas). Única excepción: educación y salud, que las 33 actividades reparten entre servicios a los hogares (privado) y gubernamentales (público); la CIIU no distingue la titularidad.
4. **Detalle según los datos disponibles.** Dentro de un grupo se puede dividir; nunca juntar grupos distintos.

## Tabla
Columna "grupos": EPHC / crédito / cuentas regionales / MIP / 33 actividades BCP. Las 33 actividades y las 6 ramas regionales siguen las definiciones **oficiales** del BCP (SCN año base 2014 y Metodología de Cuentas Regionales); EPHC, crédito y MIP son supuestos por nombre (ver `clasificaciones_locales.py`).

| ID | Sector | CIIU Rev.4 | Comercio | Grupos | Confianza | Notas |
|---|---|---|---|---|---|---|
{filas}

## Decisiones tomadas (2026-10-08)
- Se mantiene la taxonomía de 66 sectores propuesta, más uno forzado por el BCP: **confitería y pastas** se separa de panificados.
- **Biocombustibles:** no tienen clase CIIU propia; se identifican **por producto HS** en el puente (tarea 0.5), no por sector.
- **Arneses de maquila:** se asignan a **Autopartes y vehículos** por producto HS.
- **Las 33 actividades del BCP se mapean con la definición oficial** (SCN año base 2014). Frente a mi primer supuesto cambió: el almidón (CIIU 1062) va con otros alimentos y no con la molinería; ganadería incluye el apoyo pecuario (0162) y la caza (017); "telecomunicaciones" incluye edición, audiovisual, informática y servicios de información (58 a 63); y las agencias de viaje (79) van en servicios a las empresas. Por eso molinería se separa de almidones, y los servicios pecuarios y la caza pasan al sector de ganadería.
- Excepción conocida: el hielo (CNAEP 10991) lo cuenta el BCP en otros alimentos, pero su clase CIIU (3530) cae en electricidad, gas y vapor. Solo afecta a datos codificados en CNAEP.

## Puntos pendientes de revisión
1. **Mapeos supuestos de EPHC, crédito y MIP.** Se hicieron por el nombre de cada categoría. Con los clasificadores oficiales (INE, BCP, CEPAL-OIT) se pueden confirmar; si alguno cambia, la prueba indica qué sector pasa a cruzar grupos.
2. **"Productos metálicos" vale cero de 1991 a 2007** en la serie del BCP: corte de serie, hay que saber dentro de qué actividad estaba antes.
3. **Educación y salud** (público y privado) se reparten entre dos actividades del BCP; el dato público/privado no se puede asignar por CIIU.
4. **Minería.** La EPHC no muestra una rama de minería: queda `SIN_GRUPO` hasta tener el clasificador del INE.
5. **Cantidad.** Son {n}, por encima del rango 40-60 del documento técnico. Si querés reducir, se pueden juntar los tres sectores de transporte y logística, educación con salud, o lácteos con molinería. Juntar pierde detalle.
6. **Servicios y construcción** quedan fuera del espacio producto; se usan en el módulo territorial y en las cuentas nacionales.
"""


def main() -> None:
    d = pd.read_csv(RAIZ / "data" / "clean" / "taxonomia_sectores_tape.csv", dtype=str).fillna("")
    filas = "\n".join(
        f"| {r.sector_id} | {r.nombre} | {r.ciiu4} | {'sí' if r.entra_en_comercio == 'True' else 'no'} "
        f"| {r.grupo_ephc} / {r.grupo_credito} / {r.grupo_regional} / {r.grupo_mip} / {r.grupo_cnaep33} "
        f"| {r.confianza} | {r.notas} |" for r in d.itertuples(index=False))
    con = int((d.entra_en_comercio == "True").sum())
    texto = PLANTILLA.format(n=len(d), con=con, sin=len(d) - con, filas=filas)
    (RAIZ / "docs" / "taxonomia.md").write_text(texto, encoding="utf-8")
    print(f"docs/taxonomia.md: {len(d)} sectores")


if __name__ == "__main__":
    main()
