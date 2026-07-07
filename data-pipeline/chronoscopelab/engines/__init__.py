"""Offline-only forecasting engines (heavy, never imported by the Pyodide live lane).

These wrap research-chosen libraries (statsforecast now; mlforecast/LightGBM and the zero-shot
foundation models in later slices) into the same `Forecaster` contract as the pure-numpy classical
ladder. Imports are lazy, so a base install without the heavy deps still runs the classical lane and
passes the tests (graceful degradation): `heavy_forecasters()` returns only the engines available.
"""
from __future__ import annotations

from ..model.forecasters import Forecaster
from .chronos_engine import chronos_forecasters
from .lightgbm_engine import lightgbm_forecasters
from .neural_engine import neural_forecasters
from .statsforecast_engine import statsforecast_forecasters


def heavy_forecasters() -> list[Forecaster]:
    """Every heavy offline engine available in this environment (may be empty): statistical, ML, deep, and the
    zero-shot foundation tier. Each degrades gracefully when its deps or checkpoints are absent."""
    out: list[Forecaster] = []
    out.extend(statsforecast_forecasters())
    out.extend(lightgbm_forecasters())
    out.extend(neural_forecasters())
    out.extend(chronos_forecasters())
    return out
