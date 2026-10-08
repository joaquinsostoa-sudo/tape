import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import Point, box

from src.puentes.geoprocesar_industrias import ADM2, PUNTOS, SALIDA, asignar


def _poligonos() -> gpd.GeoDataFrame:
    # dos cuadrados de ~0,1 grado (~10 km) cerca de Asunción
    return gpd.GeoDataFrame(
        {"shapeName": ["A", "B"], "shapeID": ["a", "b"]},
        geometry=[box(-57.7, -25.4, -57.6, -25.3), box(-57.6, -25.4, -57.5, -25.3)], crs="EPSG:4326")


def test_punto_dentro_cercano_y_lejano():
    pts = gpd.GeoDataFrame(geometry=[Point(-57.65, -25.35), Point(-57.7005, -25.35), Point(-55.0, -25.35)],
                           crs="EPSG:4326")
    r = asignar(pts, _poligonos(), "distrito", max_m=2_000)
    assert r.distrito.tolist()[0] == "A" and r.distrito_asignacion.tolist()[0] == "dentro"
    assert r.distrito.tolist()[1] == "A" and r.distrito_asignacion.tolist()[1] == "cercano"
    assert pd.isna(r.distrito.tolist()[2]) and r.distrito_asignacion.tolist()[2] == "sin_asignar"


@pytest.mark.skipif(not SALIDA.exists(), reason="faltan datos locales")
def test_los_departamentos_reproducen_los_totales_por_zona_del_visor():
    # Totales por zona que muestra el visor del MIC (pestaña F, 2026-10-08)
    zonas = {
        "CENTRO": (7958, ["CENTRAL", "CORDILLERA", "ASUNCION", "PARAGUARI"]),
        "ESTE": (4466, ["ALTO PARANA", "CAAGUAZU", "CANINDEYU", "GUAIRA"]),
        "SUR": (2365, ["ITAPUA", "MISIONES", "ÑEEMBUCU", "CAAZAPA"]),
        "NORTE Y CHACO": (2291, ["SAN PEDRO", "CONCEPCION", "AMAMBAY", "PRESIDENTE HAYES", "BOQUERON",
                                 "ALTO PARAGUAY"]),
    }
    n = pd.read_parquet(SALIDA).groupby("departamento").size()
    for zona, (total, deptos) in zonas.items():
        assert n[deptos].sum() == total, zona


@pytest.mark.skipif(not (ADM2.exists() and PUNTOS.exists() and SALIDA.exists()), reason="faltan datos locales")
def test_casi_todas_las_industrias_quedan_localizadas():
    df = pd.read_parquet(SALIDA)
    assert len(df) == 17080
    assert df.departamento.notna().mean() > 0.99 and df.distrito.notna().mean() > 0.99
