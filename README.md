# TAPE — Territorio, Actividades y Potencial Económico

Herramienta del Laboratorio de Desarrollo Económico (LabDE) que predice a qué actividades puede diversificarse Paraguay, dónde, qué brechas lo frenan y qué política corresponde. Primero herramienta interna para producir servicios; después web pública.

Ver `CLAUDE.md` (resumen técnico y reglas), `docs/` (documentos originales) y `docs/PLAN_fase0_fase1.md` (plan de trabajo).

## Estructura

| Carpeta | Contenido |
|---|---|
| `data/raw/` | Datos tal como se descargaron. **Nunca se modifica.** Una carpeta por fuente con su README. |
| `data/clean/` | Datos estandarizados (parquet). |
| `data/model/` | Tablas derivadas: densidad, panel, probabilidades. |
| `data/fuentes.csv` | Registro de fuentes (URL, fecha, versión, licencia). |
| `src/` | `descargas/`, `limpieza/`, `puentes/`, `modelos/`. |
| `notebooks/`, `tests/`, `web/`, `docs/` | Exploración, pruebas, interfaz futura, documentación. |

## Entorno

Requiere [uv](https://docs.astral.sh/uv/) y Python 3.12.

```bash
uv sync
uv run pytest
```

## Estado

Fase 0 (fundamentos). Ver la hoja de ruta en `CLAUDE.md`.
