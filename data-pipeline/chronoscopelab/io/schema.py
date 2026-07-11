"""Typed objects passed between pipeline stages: the inter-stage contract. Plain dataclasses (Pyodide-safe)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Covariate:
    """An exogenous regressor accompanying a series, with its ARRIVAL POLICY (the preqts distinction).

    ``kind='known_future'`` (calendar, scheduled promotions, planned interventions): the value is known for
    every time, including the forecast horizon, so a covariate-aware forecaster may use it ahead. ``kind=
    'past'`` with ``lag>=0``: the value for time s is only available at time s+lag. The univariate ladder
    ignores covariates; the streaming bench uses them to show what the covariate BUYS.
    """

    name: str
    values: tuple[float, ...]
    kind: str = "known_future"   # "known_future" | "past"
    lag: int = 0


@dataclass(frozen=True)
class SeriesSpec:
    """One validated series to forecast (the unit of work); univariate target + optional covariates.

    ``y`` is the observed history; ``seasonality`` is the seasonal period m (1 = non-seasonal);
    ``horizon`` is how many steps ahead to forecast; ``freq`` is a human label (e.g. "H", "D", "M").
    ``covariates`` are optional exogenous regressors (empty for the univariate cases).
    """

    case_id: str
    y: tuple[float, ...]
    seasonality: int
    horizon: int
    freq: str = ""
    source: str = "synthetic"
    covariates: tuple[Covariate, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FeatureRow:
    """A compact fingerprint of a series (feature_extraction stage), used to describe the case."""

    case_id: str
    n_obs: int
    seasonality: int
    mean: float
    std: float
    trend_slope: float        # OLS slope per step
    seasonal_strength: float  # 0..1, share of variance explained by the seasonal means
    acf1: float               # lag-1 autocorrelation
    pct_zeros: float          # fraction of exact zeros (intermittency signal)


@dataclass(frozen=True)
class MethodForecast:
    """One method's forecast for a case: point path plus an outer prediction interval."""

    name: str
    family: str               # "classical" | "ml" | "deep" | "foundation"
    point: tuple[float, ...]
    lower: tuple[float, ...]
    upper: tuple[float, ...]


@dataclass(frozen=True)
class ForecastResult:
    """The infer-stage output for one case: history + every method's forecast."""

    case_id: str
    horizon: int
    seasonality: int
    quantile_levels: tuple[float, ...]
    history: tuple[float, ...]
    methods: tuple[MethodForecast, ...] = field(default_factory=tuple)
    covariates: tuple[Covariate, ...] = field(default_factory=tuple)
