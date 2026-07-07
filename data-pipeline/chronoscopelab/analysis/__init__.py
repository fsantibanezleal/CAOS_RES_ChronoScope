"""Time-series ANALYSIS toolkit: the "understand the series" half of ChronoScope.

Real, verified diagnostics (each delegated to its authoritative implementation and wrapped in one stable,
NaN-safe API that carries the primary reference), computed offline and baked per case so the web shows the
same numbers the pipeline computed. Built unit by unit; each module ships with its own tests and a deep
docs page (theory + equations + DOIs + SVG) authored in the same commit.

Modules:
  * stationarity    - ADF/KPSS/PP/DF-GLS/Zivot-Andrews + FPP3 differencing-order selection.
  * autocorrelation - ACF/PACF (Durbin-Levinson), Ljung-Box/Box-Pierce, Durbin-Watson, lag plot.
  * seasonality     - periodogram/Welch dominant period, seasonal strength, STL/MSTL, seasonal subseries.
  * filters         - HP/Baxter-King/Christiano-Fitzgerald band-pass, EMD/CEEMDAN IMFs, CWT scalogram.
  * changepoints    - PELT/BinSeg segmentation, OLS-CUSUM stability, Markov-switching regimes.
  * volatility      - ARCH-LM, GARCH conditional volatility, Box-Cox/Guerrero variance-stabilizing transform.
  * distribution    - moments/KDE/Q-Q + Jarque-Bera/Shapiro normality; sample/perm/spectral entropy, BDS, catch22.
  * fractal         - Hurst (R/S + DFA), MF-DFA singularity spectrum, Higuchi/Katz/Petrosian dimension, DCCA.
  * nonlinear       - Takens embedding, correlation dimension, Lyapunov, RQA, 0-1 test, surrogate gate.
"""
from __future__ import annotations

from . import autocorrelation
from . import changepoints
from . import distribution
from . import filters
from . import fractal
from . import nonlinear
from . import seasonality
from . import stationarity
from . import volatility
from .nonlinear import (
    ChaosMeasures,
    RQA,
    chaos_measures,
    iaaft_surrogate,
    nonlinear_report,
    recurrence_quantification,
    time_delay_embed,
    zero_one_test,
)
from .fractal import (
    FractalDimension,
    HurstResult,
    MultifractalSpectrum,
    dcca_coefficient,
    fractal_dimension,
    fractal_report,
    hurst,
    mfdfa,
)
from .distribution import (
    ComplexitySummary,
    DistributionSummary,
    catch22_features,
    complexity,
    distribution_report,
    kde_curve,
    qq_points,
    summary,
)
from .changepoints import (
    ChangePoints,
    CusumResult,
    RegimeFit,
    binseg,
    changepoints_report,
    cusum_stability,
    markov_regimes,
    pelt,
)
from .filters import (
    EMDResult,
    FilterResult,
    Scalogram,
    baxter_king,
    ceemdan,
    christiano_fitzgerald,
    cwt_scalogram,
    emd,
    filters_report,
    hodrick_prescott,
)
from .autocorrelation import (
    Correlogram,
    PortmanteauTest,
    acf,
    autocorrelation_report,
    bartlett_band,
    box_pierce,
    durbin_watson,
    lag_plot_pairs,
    ljung_box,
    pacf,
)
from .seasonality import (
    Decomp,
    SeasonalSubseries,
    Spectrum,
    mstl_decompose,
    periodogram,
    seasonal_strength,
    seasonal_subseries,
    seasonality_report,
    stl_decompose,
    welch,
)
from .volatility import (
    ArchTest,
    BoxCoxResult,
    GarchFit,
    arch_lm,
    box_cox,
    garch,
    rolling_volatility,
    volatility_report,
)
from .stationarity import (
    TestResult,
    adf,
    combined_verdict,
    dfgls,
    kpss,
    ndiffs,
    nsdiffs,
    phillips_perron,
    stationarity_report,
    zivot_andrews,
)

__all__ = [
    "stationarity",
    "autocorrelation",
    "seasonality",
    "filters",
    "changepoints",
    "volatility",
    "distribution",
    "fractal",
    "nonlinear",
    # stationarity
    "TestResult",
    "adf",
    "kpss",
    "phillips_perron",
    "dfgls",
    "zivot_andrews",
    "ndiffs",
    "nsdiffs",
    "combined_verdict",
    "stationarity_report",
    # autocorrelation
    "Correlogram",
    "PortmanteauTest",
    "acf",
    "pacf",
    "bartlett_band",
    "ljung_box",
    "box_pierce",
    "durbin_watson",
    "lag_plot_pairs",
    "autocorrelation_report",
    # seasonality (seasonal_strength lives here as the canonical home)
    "Spectrum",
    "Decomp",
    "SeasonalSubseries",
    "periodogram",
    "welch",
    "seasonal_strength",
    "stl_decompose",
    "mstl_decompose",
    "seasonal_subseries",
    "seasonality_report",
    # filters
    "FilterResult",
    "EMDResult",
    "Scalogram",
    "hodrick_prescott",
    "baxter_king",
    "christiano_fitzgerald",
    "emd",
    "ceemdan",
    "cwt_scalogram",
    "filters_report",
    # changepoints
    "ChangePoints",
    "CusumResult",
    "RegimeFit",
    "pelt",
    "binseg",
    "cusum_stability",
    "markov_regimes",
    "changepoints_report",
    # volatility
    "ArchTest",
    "GarchFit",
    "BoxCoxResult",
    "arch_lm",
    "garch",
    "box_cox",
    "rolling_volatility",
    "volatility_report",
    # distribution
    "DistributionSummary",
    "ComplexitySummary",
    "summary",
    "kde_curve",
    "qq_points",
    "complexity",
    "catch22_features",
    "distribution_report",
    # fractal
    "HurstResult",
    "MultifractalSpectrum",
    "FractalDimension",
    "hurst",
    "mfdfa",
    "fractal_dimension",
    "dcca_coefficient",
    "fractal_report",
    # nonlinear
    "ChaosMeasures",
    "RQA",
    "time_delay_embed",
    "chaos_measures",
    "recurrence_quantification",
    "iaaft_surrogate",
    "zero_one_test",
    "nonlinear_report",
]
