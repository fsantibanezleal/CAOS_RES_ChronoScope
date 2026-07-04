"""Auto-tuned statistical SOTA methods via Nixtla statsforecast (AutoARIMA, AutoETS, AutoTheta).

Offline-only: statsforecast pulls numba and is not Pyodide-safe, so it is imported lazily and never by
the live lane. Each method fits per forecast origin and produces analytic prediction intervals, which
we map to the requested quantile levels. AutoARIMA is the expensive one (it searches orders), so it
gets a small backtest-window budget and a context cap; ETS/Theta are cheap.
"""
from __future__ import annotations

import numpy as np

from ..model.forecasters import Forecaster, _clean


def _statsforecast_available() -> bool:
    try:
        import statsforecast  # noqa: F401
        return True
    except Exception:
        return False


class StatsforecastForecaster(Forecaster):
    def __init__(self, name: str, kind: str, max_windows: int, ctx_cap: int | None = None) -> None:
        self.name = name
        self.family = "statistical"
        self.kind = kind
        self.max_windows = max_windows
        self.ctx_cap = ctx_cap

    def _make_model(self, m: int):
        from statsforecast.models import AutoARIMA, AutoETS, AutoTheta

        season = m if m >= 2 else 1
        if self.kind == "arima":
            return AutoARIMA(season_length=season, stepwise=True, approximation=True)
        if self.kind == "ets":
            return AutoETS(season_length=season)
        if self.kind == "theta":
            return AutoTheta(season_length=season)
        raise ValueError(f"unknown statsforecast kind: {self.kind!r}")

    def quantiles(self, y: np.ndarray, m: int, h: int, levels: tuple[float, ...]) -> np.ndarray:
        yy = _clean(np.asarray(y, dtype=float))
        if self.ctx_cap and yy.shape[0] > self.ctx_cap:
            yy = yy[-self.ctx_cap:]
        model = self._make_model(m)
        model.fit(yy)

        # Analytic PIs are symmetric coverage bands; map each quantile level p to a coverage percent.
        cov = sorted({int(round(abs(1 - 2 * p) * 100)) for p in levels if abs(p - 0.5) > 1e-9})
        cov = [min(99, max(1, c)) for c in cov]
        f = model.predict(h, level=cov) if cov else model.predict(h)

        cols = []
        for p in levels:
            if abs(p - 0.5) <= 1e-9:
                cols.append(np.asarray(f["mean"], dtype=float))
            else:
                c = min(99, max(1, int(round(abs(1 - 2 * p) * 100))))
                key = f"lo-{c}" if p < 0.5 else f"hi-{c}"
                cols.append(np.asarray(f[key], dtype=float))
        out = np.column_stack(cols)
        return np.maximum.accumulate(out, axis=1)  # keep quantiles monotone across levels


def statsforecast_forecasters() -> list[StatsforecastForecaster]:
    """AutoETS + AutoTheta (cheap) and AutoARIMA (bounded), or [] if statsforecast is not installed."""
    if not _statsforecast_available():
        return []
    return [
        StatsforecastForecaster("AutoETS", "ets", max_windows=12),
        StatsforecastForecaster("AutoTheta", "theta", max_windows=12),
        StatsforecastForecaster("AutoARIMA", "arima", max_windows=3, ctx_cap=360),
    ]
