"""Logit con efectos fijos de país y de producto en matrices dispersas (sin armar una matriz densa de dummies).

`smf.logit("E ~ densidad + C(country) + C(product)")` arma una matriz densa de filas × ~5.000 dummies: unos 14 a 16 GB
(float64) por ventana, más las copias que hace statsmodels al ajustar. Acá cada fila tiene solo 3 valores distintos de
cero (la densidad y una dummy de país y una de producto), así que la matriz dispersa ocupa unos 10 MB.

Para predecir y ordenar (precision@k, AUC-PR) basta con las probabilidades. Con `C=None` el ajuste no penaliza (máxima
verosimilitud, igual que statsmodels); si hay países o productos sin ninguna entrada (separación perfecta) el óptimo está
en el infinito y conviene una penalización suave (por ejemplo `C=10`).

`errores_agrupados` calcula los errores estándar agrupados (sandwich) de los coeficientes numéricos sin armar la matriz
de información completa: usa el complemento de Schur sobre los efectos fijos, con una solución dispersa por columna
numérica (D2: coeficientes de la tarea 1.9, agrupados por país). Se calcula como máxima verosimilitud sin penalización
(con `C=10` la diferencia en las pendientes es despreciable).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import sparse, stats
from scipy.sparse.linalg import splu
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

    def errores_agrupados(self, df: pd.DataFrame, y: str, grupo: str, correccion: bool = True) -> pd.DataFrame:
        """Errores estándar agrupados por `grupo` (sandwich) de los coeficientes de `columnas`.

        `df` debe ser la misma tabla del ajuste. Con `correccion` la varianza se multiplica por G/(G-1). Devuelve coef,
        ee, z y p (t con G-1 grados de libertad). Los efectos fijos omiten una categoría del último efecto para que
        la matriz sea de rango completo."""
        k, n = len(self.columnas), len(df)
        x = df[self.columnas].to_numpy(dtype=float)
        dummies = self.codificador.transform(df[self.efectos]).tocsc()
        omitida = sum(len(c) for c in self.codificador.categories_[:-1])
        z = dummies[:, [j for j in range(dummies.shape[1]) if j != omitida]]
        p = self.modelo.predict_proba(self._x(df))[:, 1]
        w, resid = p * (1 - p), df[y].to_numpy(dtype=float) - p

        h_gg = (z.T @ sparse.diags(w) @ z).tocsc()
        h_gg = h_gg + sparse.identity(h_gg.shape[0], format="csc") * (1e-8 * h_gg.diagonal().mean())  # separación
        h_gb = np.asarray(z.T @ (x * w[:, None]))  # (efectos × k)
        m = splu(h_gg).solve(h_gb)  # H_gg^-1 H_gb
        s = (x * w[:, None]).T @ x - h_gb.T @ m  # complemento de Schur: información de las pendientes
        x_res = x - z @ m  # pendientes sin la parte explicada por los efectos fijos
        codigos, _ = pd.factorize(df[grupo])
        g = int(codigos.max()) + 1
        suma = sparse.csr_matrix((np.ones(n), (codigos, np.arange(n))), shape=(g, n))
        u = suma @ (resid[:, None] * x_res)  # puntajes por grupo (G × k)
        s_inv = np.linalg.inv(s)
        var = s_inv @ (u.T @ u) @ s_inv * (g / (g - 1) if correccion else 1.0)
        coef = np.asarray(self.modelo.coef_[0][:k])
        error = np.sqrt(np.diag(var))
        est = coef / error
        return pd.DataFrame({"coef": coef, "ee": error, "z": est, "p": 2 * stats.t.sf(np.abs(est), df=g - 1)},
                            index=self.columnas)
