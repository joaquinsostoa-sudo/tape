"""
Métricas de evaluación: precision@k, AUC-PR, calibración.

Uso:
    from src.modelos.evaluacion import precision_at_k, auc_pr, calibracion
"""

from typing import Sequence
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def precision_at_k(y_true: Sequence[int], y_score: Sequence[float], k: int = 20) -> float:
    """Fracción de positivos en los k con mayor score."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    if k > len(y_score):
        k = len(y_score)
    idx = np.argsort(y_score)[::-1][:k]
    return float(y_true[idx].mean())


def auc_pr(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """Área bajo la curva precision-recall."""
    return float(average_precision_score(y_true, y_score))


def auc_roc(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """Área bajo la curva ROC (para comparar)."""
    return float(roc_auc_score(y_true, y_score))


def calibracion(y_true: Sequence[int], y_score: Sequence[float], n_bins: int = 10) -> list[dict]:
    """Devuelve, por bin, la probabilidad predicha media y la frecuencia real."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    bins = np.linspace(0, 1, n_bins + 1)
    resultado = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        mask = (y_score >= lo) & (y_score < hi)
        if mask.sum() == 0:
            continue
        resultado.append({
            "bin_lo": float(lo),
            "bin_hi": float(hi),
            "n": int(mask.sum()),
            "predicho": float(y_score[mask].mean()),
            "real": float(y_true[mask].mean()),
        })
    return resultado


if __name__ == "__main__":
    # Test mínimo con datos sintéticos
    y = [0, 0, 1, 1, 1, 0, 1, 0, 1, 0]
    s = [0.1, 0.2, 0.8, 0.9, 0.7, 0.3, 0.6, 0.4, 0.5, 0.15]
    print(f"precision@3 = {precision_at_k(y, s, 3):.3f}")
    print(f"AUC-PR = {auc_pr(y, s):.3f}")
    print(f"AUC-ROC = {auc_roc(y, s):.3f}")
    print("Calibración:")
    for b in calibracion(y, s, 5):
        print(f"  [{b['bin_lo']:.1f}, {b['bin_hi']:.1f}]: "
              f"n={b['n']}, pred={b['predicho']:.2f}, real={b['real']:.2f}")