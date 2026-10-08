import pandas as pd
import pytest

from src.limpieza.industrias_mic import JSON_PUNTOS, RESUMEN, cargar

pytestmark = pytest.mark.skipif(not JSON_PUNTOS.exists(), reason="falta el JSON de puntos del mapa MIC (no versionado)")


def test_17080_industrias_con_coordenadas_validas():
    df = cargar()
    assert len(df) == 17080 and df.industria_id.is_unique
    assert df[["lat", "lon"]].notna().all().all()


def test_los_puntos_coinciden_con_el_resumen_sector_subsector():
    df = cargar()
    puntos = df.groupby(["sector", "subsector"]).size()
    resumen = pd.read_csv(RESUMEN).set_index(["sector", "subsector"]).n_industrias
    # los nombres del mapa traen "--C--" donde el resumen trae coma (codificación del visor)
    puntos.index = pd.MultiIndex.from_tuples(
        [(s.replace("--C--", ","), b.replace("--C--", ",")) for s, b in puntos.index])
    assert (puntos.sort_index() == resumen.sort_index()).all() and len(puntos) == len(resumen)
