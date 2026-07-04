"""Offline-only forecasting engines (heavy, never imported by the Pyodide live lane).

These wrap research-chosen libraries (statsforecast now; mlforecast/LightGBM and the zero-shot
foundation models in later slices) into the same `Forecaster` contract as the pure-numpy classical
ladder. Imports are lazy, so a base install without the heavy deps still runs the classical lane and
passes the tests (graceful degradation): `heavy_forecasters()` returns only the engines available.
"""
from __future__ import annotations

from ..model.forecasters import Forecaster
from .statsforecast_engine import statsforecast_forecasters


def heavy_forecasters() -> list[Forecaster]:
    """Every heavy offline engine that is importable in this environment (may be empty)."""
    out: list[Forecaster] = []
    out.extend(statsforecast_forecasters())
    return out
