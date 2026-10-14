import numpy as np
import pandas as pd

from src.modelos import oportunidades as op


def test_cuadrantes_por_cuartil_de_densidad_y_pci_positivo():
    df = pd.DataFrame({"densidad": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], "pci": [1, -1, 1, -1, 1, -1, 1, -1]})
    c = op.cuadrantes(df)
    # cuartil superior = densidad >= 0,625 (percentil 75): los dos últimos (0,7 con PCI 1 y 0,8 con PCI -1)
    assert c.tolist() == ["lejano y complejo", "lejano y simple", "lejano y complejo", "lejano y simple", "lejano y complejo", "lejano y simple", "cercano y complejo", "cercano y simple"]


def test_escalera_solo_vecinos_mas_complejos_en_orden_de_proximidad():
    productos = ["A", "B", "C", "D"]
    phi = np.array([[0, 0.5, 0.9, 0.1], [0.5, 0, 0.2, 0.3], [0.9, 0.2, 0, 0.4], [0.1, 0.3, 0.4, 0]])
    pci = pd.Series({"A": 0.0, "B": 1.0, "C": -1.0, "D": 2.0})
    e = op.escalera(phi, productos, ["A"], pci, k=5)
    assert e.destino.tolist() == ["B", "D"]  # C (más cercano) es menos complejo y no entra; B antes que D por φ
    assert e.phi.tolist() == [0.5, 0.1] and (e.pci_destino > e.pci_origen).all()
    assert len(op.escalera(phi, productos, ["A"], pci, k=1)) == 1


def test_escalera_ignora_origenes_sin_pci_o_fuera_de_la_matriz():
    phi = np.zeros((2, 2))
    assert op.escalera(phi, ["A", "B"], ["Z", "A"], pd.Series({"A": np.nan, "B": 1.0})).empty


def test_habilitadores_son_los_presentes_mas_proximos_al_candidato():
    productos = ["A", "B", "C", "X"]
    phi = np.array([[0, 0, 0, 0.2], [0, 0, 0, 0.7], [0, 0, 0, 0.0], [0.2, 0.7, 0.0, 0]])
    h = op.habilitadores(phi, productos, ["A", "B", "C"], ["X"], k=2)
    assert h.habilitador.tolist() == ["B", "A"] and h.phi.tolist() == [0.7, 0.2]  # C tiene φ = 0: no habilita
