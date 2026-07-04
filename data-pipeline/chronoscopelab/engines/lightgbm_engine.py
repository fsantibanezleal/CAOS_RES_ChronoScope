"""Machine-learning tier: gradient boosting on lag features (LightGBM via Nixtla mlforecast).

Gradient boosting on lagged/date features is the approach that won the M5 competition and is the standard
ML baseline for a forecasting atlas. Offline-only: LightGBM and mlforecast are not Pyodide-safe, so they are
imported lazily and never by the live lane. The pipeline degrades gracefully to the classical + statistical
tiers if these deps are absent.

Design choice: one LightGBM point model on recursive lag features, with prediction intervals derived from the
in-sample one-step residual sigma (the same Gaussian widening the classical ladder uses). This is faster than
three quantile models and avoids the drift of recursively feeding each quantile model its own prediction. A
future refinement can add native quantile-objective LightGBM models.
"""
from __future__ import annotations

import numpy as np

from ..model.forecasters import Forecaster, _clean, gaussian_quantiles


def _lightgbm_available() -> bool:
    try:
        import lightgbm  # noqa: F401
        import mlforecast  # noqa: F401
        import pandas  # noqa: F401
        return True
    except Exception:
        return False


class LightGBMForecaster(Forecaster):
    def __init__(self, name: str = "LightGBM", max_windows: int = 6, ctx_cap: int | None = 500) -> None:
        self.name = name
        self.family = "ml"
        self.max_windows = max_windows
        self.ctx_cap = ctx_cap

    def _lags(self, m: int, n: int) -> list[int]:
        cand = [1, 2, 3]
        if m >= 2:
            cand += [m, m + 1, 2 * m]
        # A lag L needs more than L training rows; keep lags comfortably inside the context.
        usable = max(4, n - 4)
        return sorted({L for L in cand if L < usable})

    def quantiles(self, y: np.ndarray, m: int, h: int, levels: tuple[float, ...]) -> np.ndarray:
        import pandas as pd
        from lightgbm import LGBMRegressor
        from mlforecast import MLForecast

        yy = _clean(np.asarray(y, dtype=float))
        if self.ctx_cap and yy.shape[0] > self.ctx_cap:
            yy = yy[-self.ctx_cap:]
        lags = self._lags(m, yy.shape[0])

        df = pd.DataFrame({"unique_id": "s", "ds": np.arange(yy.shape[0]), "y": yy})
        model = LGBMRegressor(n_estimators=100, num_leaves=31, min_child_samples=5,
                              learning_rate=0.05, verbosity=-1)
        mlf = MLForecast(models={"lgb": model}, freq=1, lags=lags)
        mlf.fit(df, fitted=True, static_features=[])

        fitted = mlf.forecast_fitted_values()
        resid = fitted["y"].to_numpy() - fitted["lgb"].to_numpy()
        sigma = float(np.std(resid)) if resid.size else 0.0

        point = mlf.predict(h)["lgb"].to_numpy()
        return gaussian_quantiles(point, sigma, levels)


def lightgbm_forecasters() -> list[LightGBMForecaster]:
    """The LightGBM ML method, or [] if lightgbm/mlforecast/pandas are not installed."""
    if not _lightgbm_available():
        return []
    return [LightGBMForecaster()]
