"""Logit con efectos fijos de país y de producto en matrices dispersas (sin armar una matriz densa de dummies).

`smf.logit("E ~ densidad + C(country) + C(product)")` arma una matriz densa de filas × ~5.000 dummies: unos 14 a 16 GB
(float64) por ventana, más las copias que hace statsmodels al ajustar. Acá cada fila tiene solo 3 valores distintos de
cero (la densidad y una dummy de país y una de producto), así que la matriz dispersa ocupa unos 10 MB.

Para predecir y ordenar (precision@k, AUC-PR) basta con las probabilidades. Con `C=None` el ajuste no penaliza (máxima
verosimilitud, igual que statsmodels); si hay países o productos sin ninguna entrada (separación perfecta) el óptimo está
en el infinito y conviene una penalización suave (por ejemplo `C=10`). No calcula errores estándar: para los coeficientes
de la tarea 1.9 hará falta otra herramienta (errores agrupados por país).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder


class LogitEfectosFijos:
    def __init__(self, columnas: list[str], efectos: list[str], C: float | None = None, max_iter: int = 3000,
                 tol: float = 1e-7):
        self.columnas, self.efectos = columnas, efectos
        self.codificador = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
        self.modelo = LogisticRegression(C=np.inf if C is None else C, solver="lbfgs", max_iter=max_iter, tol=tol)

    def _x(self, df: pd.DataFrame, ajustar: bool = False) -> sparse.csr_matrix:
        dummies = (self.codificador.fit_transform(df[self.efectos]) if ajustar
                   else self.codificador.transform(df[self.efectos]))
        return sparse.hstack([sparse.csr_matrix(df[self.columnas].to_numpy(dtype=float)), dummies], format="csr")

    def ajustar(self, df: pd.DataFrame, y: str) -> LogitEfectosFijos:
        self.modelo.fit(self._x(df, ajustar=True), df[y].to_numpy())
        return self

    def predecir(self, df: pd.DataFrame) -> np.ndarray:
        """Probabilidad de y = 1. Países o productos no vistos al ajustar quedan sin efecto fijo (solo constante)."""
        return self.modelo.predict_proba(self._x(df))[:, 1]

    @property
    def coeficientes(self) -> dict[str, float]:
        """Coeficientes de las columnas numéricas (los efectos fijos no se reportan)."""
        return dict(zip(self.columnas, self.modelo.coef_[0][: len(self.columnas)].tolist(), strict=True))
