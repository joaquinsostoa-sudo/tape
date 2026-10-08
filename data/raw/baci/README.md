# BACI comercio bilateral

- **Institución:** CEPII
- **Registro:** fila `baci` de `data/fuentes.csv`
- **Acceso:** Descarga directa (zip por revisión HS)
- **Cobertura:** 1995-último año de la versión (verificar)

## Qué esperamos aquí

Archivos esperados (zip oficial de CEPII, descomprimido aquí):
- `BACI_HS92_Y{año}_V{versión}.csv`  columnas: `t,i,j,k,v,q` (año, exportador, importador, producto HS6, valor miles USD, cantidad toneladas)
- `country_codes_V{versión}.csv`
- `product_codes_HS92_V{versión}.csv`
- `Readme*.txt` y documentación de la versión

Descarga: `src/descargas/baci.py` intenta bajar el zip; si CEPII lo bloquea, bajar a mano desde la URL de fuentes.csv (sección "BACI" > HS92) y descomprimir en esta carpeta.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
