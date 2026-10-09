# EPHC microdatos

- **Institución:** INE
- **Registro:** fila `ephc` de `data/fuentes.csv`
- **Acceso:** Web del INE
- **Cobertura:** 2022-2025

## Qué esperamos aquí

Archivos esperados: microdatos EPHC por año o trimestre (SAV/DTA/CSV), diccionarios de variables y el clasificador de actividad. Una subcarpeta por año.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).

## Archivos presentes (2026-10-09)
Entregados a mano por el usuario (la página del INE responde 503 a ratos). `2022/` a `2025/` con REG01 (hogares), REG02 (personas) e INGREFAM (ingresos del hogar), en CSV con `;` y latin-1; diccionario solo para 2025 (`2025/diccionario_EPHC_ANUAL_2025.xls`).

- **Rama de actividad:** `A14REC` (establecimiento), `B02REC` (ocupación principal) y `RAMA_PEA`: 8 ramas, 99 = no responde, blanco = no corresponde. No hay código CIIU más fino. `DPTO` va de 0 (Asunción) a 15; no hay distrito.
- **2022 en dos versiones:** `2022/` es la entregada por el usuario (columna `FACTOR`, igual que 2023-2025; se toma como la versión revisada) y `2022_sitio_previo/` es la que bajó un intento automático desde la ruta `.../documento/microdato/EPHC-ANUAL/2022/` (columna `FEX.2022`). Difieren en ponderadores, ingresos y pobreza; la rama de actividad es idéntica. Usar `2022/`.
- La página del INE dice 2022-2025 pero solo enlaza 2022-2024.
