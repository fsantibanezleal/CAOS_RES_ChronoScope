"""chronoscopelab: the offline + live forecasting engine for ChronoScope (ADR-0057 product).

The engine is the time-series forecasting method ladder: a real pure-numpy classical core (seasonal-naive,
SES, Holt, Holt-Winters, Theta) that runs both the offline pipeline and the browser live lane, scored by the
preqts prequential library. Heavier engines (Nixtla, LightGBM, zero-shot foundation models) plug in behind the
same MethodForecast contract in later slices. The base (two data contracts, staged pipeline, lane gate,
manifest/trace, cases-by-category registry) is the FROZEN template.
"""

__version__ = "0.18.000"  # display X.XX.XXX; PEP 440 form in pyproject.toml (0.18.0)
