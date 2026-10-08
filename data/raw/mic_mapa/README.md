# Mapa Logístico MIC (capas)

- **Institución:** MIC
- **Registro:** fila `mic_mapa` de `data/fuentes.csv`
- **Acceso:** Visor (verificar si permite descarga) / solicitud de acceso a la información
- **Cobertura:** Foto 2026

## Qué esperamos aquí

Una subcarpeta por capa (`habitantes_pea/`, `rutas/`, `red_electrica/`, `combustibles/`, `salud/`, `industrias/`, `polos_ifcl/`, `aduanas/`), cada una con shapefile/GeoJSON/CSV tal como salió del visor o de la solicitud. Anotar en un `LEEME_fecha.txt` la fecha de descarga o de entrega.

## Reglas

- No modificar, renombrar columnas ni resguardar versiones editadas: `data/raw` es solo lectura.
- Al copiar archivos, completar `fecha de descarga` y `versión` en `data/fuentes.csv`.
- Los archivos pesados están ignorados por git (solo se versionan los README).
