"""The combined method set the OFFLINE pipeline evaluates: the pure-numpy classical ladder plus every
heavy engine available in this environment. The live lane uses only the classical ladder
(`model.forecasters.forecast_all`); this module is imported by the offline stages, never by live.py."""
from __future__ import annotations

from .engines import heavy_forecasters
from .model.forecasters import Forecaster, classical_forecasters


def all_forecasters() -> list[Forecaster]:
    return [*classical_forecasters(), *heavy_forecasters()]
