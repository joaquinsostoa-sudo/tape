# Correspondencias HS-CPC-CIIU Rev.4

- **Institución:** ONU (UNSD) / WITS
- **Registro:** fila `concordancias` de `data/fuentes.csv`
- **Acceso:** Descarga directa
- **Cobertura:** Revisiones HS92-HS2022

## Qué esperamos aquí

Archivos esperados (UNSD, sección Correspondence Tables):
- `HS{rev}_to_CPC21.csv` y `CPC21_to_ISIC4.csv` (o `HS_ISIC4` directo de WITS)
- cualquier correlación HS92<->HS2002/2007/2012/2017 necesaria para homogeneizar revisiones

Descarga: `src/descargas/concordancias.py`; si no, bajar a mano de la URL y dejar aquí.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
