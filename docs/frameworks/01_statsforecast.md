# StatsForecast adapters

The [StatsForecast](https://github.com/Nixtla/statsforecast) adapters in `data-pipeline/engine/engines/statsforecast_engine.py` instantiate AutoARIMA, AutoETS and AutoTheta. Their exact package version belongs to each recorded experiment; the current requirements and retained fresh-runtime record identify separate environments.

AutoARIMA searches ARIMA/SARIMA orders with `stepwise=True` and `approximation=True`. AutoETS selects an exponential-smoothing state-space specification. AutoTheta implements automatic Theta-family selection. Their statistical assumptions and tuning differ from the five finite-prefix ForecastScope kernels; a matching family name does not imply the same forecast.

At a forecast origin the adapter cleans the supplied prefix, applies any context cap, fits the requested package model and requests its prediction bands. Requested probabilities are mapped to integer percentage coverages. The package's mean occupies the central output column; it is not proven to be a conditional median. Endpoints are rearranged to retain ordering. These model-based bands have no distribution-free coverage guarantee.

The historical rolling adapter gives AutoARIMA at most three origins and a 360-observation context, while AutoETS/AutoTheta permit twelve origins. That unequal schedule cannot be treated as a matched leaderboard. The separate common-final-block experiment aligns targets while recording each configuration and warning. A MASE below one compares its error with a historical seasonal scale; it does not by itself prove a win over a SeasonalNaive forecast on the same targets.

These native package models execute offline. The actual browser runs TypeScript rules and a separate ONNX map, with no Python worker. Optional package discovery can omit unavailable methods in an exploratory local runtime, but full-roster study admission refuses incomplete candidates and the canonical delivered evidence must remain intact.

Numba may compile on first use. Fit and convergence warnings remain part of an experiment's evidence and should be read before interpreting a finite forecast. Current results are available in the workbench's explicitly selected study and in the [source-bound fresh execution guide](../guides/fresh-reevaluation.md); this page makes no universal ranking claim.
