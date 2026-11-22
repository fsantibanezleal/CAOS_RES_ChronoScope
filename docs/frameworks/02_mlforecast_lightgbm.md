# MLForecast and LightGBM adapter

`data-pipeline/engine/engines/lightgbm_engine.py` fits one recursive LightGBM point model using [MLForecast](https://github.com/Nixtla/mlforecast). [LightGBM](https://github.com/microsoft/LightGBM) supplies the gradient-boosted regression trees. This per-prefix configuration is distinct from a global model trained across a competition collection; a result from another implementation or task is not transferred to this adapter.

The candidate lags are 1, 2 and 3, plus the seasonal lag, one beyond it and twice it where the supplied history permits. The adapter filters unusable lags and caps its retained context at 500 observations. Its historical rolling schedule permits six origins. These are configuration choices, not evidence that a particular lag set or fitting budget is optimal.

Prediction proceeds recursively, using earlier predicted point values as later lag inputs. Gaussian endpoints use the in-prefix one-step residual standard deviation and square-root lead widening through the shared provider helper. This is a lightweight uncertainty approximation. It does not fit independent conditional quantile models or establish calibrated coverage on authentic future data.

The maintained experiment records its exact MLForecast, LightGBM and numerical dependencies. Native LightGBM/pandas computation remains offline; the deployed browser's TypeScript and ONNX paths do not import these libraries. Unavailable optional dependencies can reduce an exploratory local roster, but they cannot silently replace a method or overwrite the admitted complete study.

Inspect the matched final-block or external-collection results under their own protocols. Historical rolling rows, common final targets and cross-series model-selection experiments have different sampling units and fitting budgets. Their errors and warnings are retained separately. More training data, covariates or cross-series fitting are hypotheses for another specified experiment rather than demonstrated gains of this implementation.
