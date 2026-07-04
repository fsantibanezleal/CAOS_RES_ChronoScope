"""Time-series ANALYSIS toolkit: the "understand the series" half of ChronoScope.

Real, verified diagnostics (each delegated to its authoritative implementation and wrapped in one stable,
NaN-safe API that carries the primary reference), computed offline and baked per case so the web shows the
same numbers the pipeline computed. Built unit by unit; each module ships with its own tests and a deep
docs page (theory + equations + DOIs + SVG) authored in the same commit.

Modules:
  * stationarity - ADF/KPSS/PP/DF-GLS/Zivot-Andrews + FPP3 differencing-order selection.
"""
from __future__ import annotations

from . import stationarity
from .stationarity import (
    TestResult,
    adf,
    combined_verdict,
    dfgls,
    kpss,
    ndiffs,
    nsdiffs,
    phillips_perron,
    seasonal_strength,
    stationarity_report,
    zivot_andrews,
)

__all__ = [
    "stationarity",
    "TestResult",
    "adf",
    "kpss",
    "phillips_perron",
    "dfgls",
    "zivot_andrews",
    "ndiffs",
    "nsdiffs",
    "seasonal_strength",
    "combined_verdict",
    "stationarity_report",
]
