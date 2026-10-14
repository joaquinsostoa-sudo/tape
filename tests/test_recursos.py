import numpy as np
import pandas as pd
import pytest

from src.modelos import recursos as rc


def test_limpiar_valor_del_usgs():
    assert rc.limpiar_valor("1,200,000") == 1_200_000
    assert rc.limpiar_valor(">9,100,000") == 9_100_000
    assert all(np.isnan(rc.limpiar_valor(x)) for x in ["—", "Small", "s", "W", np.nan, "NA"])


def test_familia_de_reservas_quita_la_marca_de_redondeo():
    assert rc._familia("Reserves: rounded") == "Reserves"
    assert rc._familia("Reserves (million metric tons): Crude ore, rounded") == "Reserves (million metric tons): Crude ore"
    assert rc._familia("Reserves, Recoverable ore: rounded") == "Reserves, Recoverable ore"
    assert rc._familia("Reserves: K2O equivalent") == "Reserves: K2O equivalent"


def _usgs():
    f = [("Copper", "Chile", "Reserves", "180,000"), ("Copper", "Russia", "Reserves", "80,000"), ("Copper", "Peru", "Reserves", "—"),
         ("Copper", "Other countries", "Reserves", "210,000"), ("Copper", "World total", "Reserves: rounded", "980,000"),
         ("Gold", "Chile", "Reserves", "1,000"), ("Gold", "Russia", "Reserves", "2,000"), ("Gold", "Chile", "Reserves: other", "5")]
    return pd.DataFrame([{"Commodity": c, "Country": p, "Statistics": "Reserves", "Statistics_detail": d, "Value": v} for c, p, d, v in f])


def test_participacion_usa_el_total_mundial_y_la_suma_cuando_no_existe_y_los_alias_de_pais():
    puente = pd.DataFrame({"nombre": ["Chile", "Russian Federation", "Peru"], "iso3": ["CHL", "RUS", "PER"]})
    s = rc.participacion_reservas(_usgs(), puente).set_index(["commodity", "iso3"]).share
    assert s["Copper", "CHL"] == pytest.approx(180_000 / 980_000) and s["Copper", "RUS"] == pytest.approx(80_000 / 980_000)  # Russia → RUS por alias
    assert ("Copper", "PER") not in s.index  # sin dato («—»): ausente, no cero
    assert s["Gold", "CHL"] == pytest.approx(1_000 / 3_000) and s["Gold", "RUS"] == pytest.approx(2_000 / 3_000)  # sin total: suma de países
