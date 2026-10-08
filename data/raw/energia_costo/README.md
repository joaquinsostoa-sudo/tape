# Costo/precio de energía por país

- **Institución:** Por decidir (IEA, GlobalPetrolPrices, BM Doing Business/B-READY)
- **Registro:** fila `energia_costo` de `data/fuentes.csv`
- **Acceso:** Por decidir
- **Cobertura:** Por decidir

## Qué esperamos aquí

Pendiente de decisión (decisión D4 del plan). Candidatas: precio de electricidad industrial (IEA, GlobalPetrolPrices) o proxy WDI de acceso/consumo eléctrico.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
