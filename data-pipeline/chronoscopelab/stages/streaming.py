"""Stage 5b - streaming: the prequential streaming bench (the product's flagship novel piece).

Real forecasting is streaming: observations arrive one by one, the model updates, and its INTERVALS must
stay calibrated as the series drifts. No public harness evaluates stateful forecasters this way with an
explicit covariate-arrival policy - that is the gap `preqts` (our published package, PyPI `preqts>=0.2`)
fills, and this stage bakes the demonstration per case:

For each streaming method (the classical live methods wrapped as replay + the ACI / Conformal-PID
calibrated variants of the best one), it runs a prequential test-then-update pass over the case history
and records the CUMULATIVE trajectories the web's streaming bench renders:

  * rolling MASE (skill as the stream lengthens),
  * rolling empirical coverage vs the nominal target (the calibration story: raw vs ACI vs PID),
  * per-step interval width (the price of coverage),
  * cumulative compute cost (ms) - the constant-cost-per-step story.

References (verified dossiers): prequential evaluation Dawid 1984 (DOI 10.2307/2981683); ACI Gibbs &
Candes 2021 (arXiv:2106.00170); Conformal PID Angelopoulos, Candes & Tibshirani 2023 (arXiv:2307.16895).
"""
from __future__ import annotations

import math

import numpy as np

from preqts import AdaptiveConformal, ConformalPID, ReplayAdapter, Stream, run_prequential
from preqts import Covariate as PqCovariate

from ..io.schema import SeriesSpec
from ..model.forecasters import classical_forecasters

_LEVELS = (0.1, 0.5, 0.9)
_TARGET = 0.8  # nominal outer coverage of the 10/90 band


def _batch_fn(fc, m: int):
    def batch(context, horizon, past_cov, future_cov, levels):
        return fc.quantiles(np.asarray(context, dtype=float), m, horizon, tuple(levels))

    return batch


def _norm_ppf(p: float) -> float:
    """Acklam's rational approximation of the standard-normal inverse CDF (|err| < 1.15e-9)."""
    if not 0.0 < p < 1.0:
        return 0.0
    a = (-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2,
         1.383577518672690e2, -3.066479806614716e1, 2.506628277459239)
    b = (-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2,
         6.680131188771972e1, -1.328068155288572e1)
    c = (-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783)
    d = (7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416)
    pl = 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= 1 - pl:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
        ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def _ridge_batch(m: int, use_cov: bool, alpha: float = 1.0):
    """A small online-ridge forecaster (as a ReplayAdapter batch fn): regress y[t] on an intercept, the
    lag-1 and lag-m values, and (when ``use_cov``) the exogenous covariate. The covariate-aware variant
    reads the KNOWN-FUTURE covariate for the horizon from ``future_cov``; the blind variant ignores it, so
    the gap between the two isolates exactly what the covariate buys.
    """
    def batch(context, horizon, past_cov, future_cov, levels):
        y = np.asarray(context, dtype=float)
        n = y.shape[0]
        lo = max(1, m)
        if n <= lo + 3:
            last = float(y[-1]) if n else 0.0
            return np.full((horizon, len(levels)), last)
        rows_x, rows_y = [], []
        for t in range(lo, n):
            feat = [1.0, y[t - 1], y[t - m]]
            if use_cov and past_cov is not None:
                feat.append(float(past_cov[t, 0]))
            rows_x.append(feat)
            rows_y.append(y[t])
        X = np.asarray(rows_x)
        yy = np.asarray(rows_y)
        k = X.shape[1]
        reg = alpha * np.eye(k)
        reg[0, 0] = 0.0  # do not penalise the intercept
        coef = np.linalg.solve(X.T @ X + reg, X.T @ yy)
        sd = float(np.std(yy - X @ coef)) or 1e-6
        hist = list(y)
        preds = []
        for h in range(horizon):
            feat = [1.0, hist[-1], hist[-m]]
            if use_cov:
                cov_val = float(future_cov[h, 0]) if future_cov is not None else 0.0
                feat.append(cov_val)
            p = float(np.dot(coef, feat))
            preds.append(p)
            hist.append(p)
        preds = np.asarray(preds)
        out = np.zeros((horizon, len(levels)))
        for j, q in enumerate(levels):
            out[:, j] = preds + _norm_ppf(q) * sd * np.sqrt(np.arange(1, horizon + 1))
        return out

    return batch


def _rolling_mean(x: np.ndarray, w: int = 25) -> list:
    out = []
    for i in range(len(x)):
        seg = x[max(0, i - w + 1):i + 1]
        seg = seg[np.isfinite(seg)]
        out.append(round(float(seg.mean()), 5) if seg.size else None)
    return out


def _trajectories(res) -> dict:
    """Extract the per-cutoff trajectories the web renders from a preqts PrequentialResult."""
    cost_ms = (np.nan_to_num(res.predict_latency) + np.nan_to_num(res.ingest_latency)) * 1e3
    return {
        "cutoffs": [int(c) for c in res.cutoffs],
        "rolling_mase": _rolling_mean(np.asarray(res.mase, dtype=float)),
        "rolling_coverage": _rolling_mean(np.asarray(res.coverage, dtype=float)),
        "rolling_wql": _rolling_mean(np.asarray(res.wql, dtype=float)),
        "cumulative_cost_ms": np.cumsum(cost_ms).round(3).tolist(),
        "n_steps": int(res.n_windows),
    }


def run(spec: SeriesSpec, horizon: int = 1) -> dict:
    """Run the streaming bench on the case history; return the JSON-ready streaming artifact block.

    A case with a known-future covariate additionally gets the covariate-policy demonstration: a
    covariate-aware ridge vs a covariate-blind ridge, run through a preqts Stream that carries the
    covariate with its arrival policy. The aware one anticipates the scheduled driver; the blind one lags.
    """
    y = np.asarray(spec.y, dtype=float)
    m = spec.seasonality
    pq_covs = [PqCovariate(name=c.name, values=np.asarray(c.values, dtype=float), kind=c.kind, lag=c.lag)
               for c in spec.covariates]
    has_known_future = any(c.kind == "known_future" for c in spec.covariates)
    stream = Stream(y, covariates=pq_covs, seasonality=m, name=spec.case_id)
    warmup = min(max(2 * m, 20), max(1, len(y) // 3))

    # the streaming roster: the best cheap classical live method raw, + its calibrated variants
    base_fc = next(f for f in classical_forecasters() if f.name == "Theta")
    naive_fc = next(f for f in classical_forecasters() if f.name == "SeasonalNaive")

    def _theta():
        return ReplayAdapter(_batch_fn(base_fc, m), name="Theta")

    roster = {
        "SeasonalNaive": ReplayAdapter(_batch_fn(naive_fc, m), name="SeasonalNaive"),
        "Theta": _theta(),
        "Theta+ACI": AdaptiveConformal(_theta(), target_coverage=_TARGET, gamma=0.02),
        "Theta+PID": ConformalPID(_theta(), target_coverage=_TARGET, kp=0.05, ki=0.02, kd=0.02),
    }
    # covariate-policy demonstration (only when a known-future covariate is present)
    if has_known_future:
        roster["Ridge (blind)"] = ReplayAdapter(_ridge_batch(m, use_cov=False), name="Ridge (blind)")
        roster["Ridge+exog (aware)"] = ReplayAdapter(_ridge_batch(m, use_cov=True), name="Ridge+exog (aware)")

    methods: dict[str, dict] = {}
    for name, fc in roster.items():
        try:
            res = run_prequential(fc, stream, horizon=horizon, quantile_levels=list(_LEVELS),
                                  warmup=warmup)
            block = _trajectories(res)
            s = res.summary()
            block["final"] = {"mase": round(float(s["mase"]), 5) if s["mase"] == s["mase"] else None,
                              "coverage": round(float(s["coverage"]), 4),
                              "wql": round(float(s["wql"]), 5) if s["wql"] == s["wql"] else None}
            methods[name] = block
        except Exception as exc:  # noqa: BLE001 - record, never crash the bake
            methods[name] = {"error": f"{type(exc).__name__}: {exc}"}

    covariate_block = None
    if spec.covariates:
        c0 = spec.covariates[0]
        covariate_block = {
            "name": c0.name,
            "kind": c0.kind,
            "lag": int(c0.lag),
            "values": [round(float(v), 4) for v in c0.values],
        }

    return {
        "nominal_coverage": _TARGET,
        "horizon": int(horizon),
        "warmup": int(warmup),
        "methods": methods,
        "covariate": covariate_block,
        "references": {
            "prequential": "Dawid 1984, JRSS-A 147(2):278-292, DOI 10.2307/2981683",
            "aci": "Gibbs & Candes 2021, NeurIPS, arXiv:2106.00170",
            "conformal_pid": "Angelopoulos, Candes & Tibshirani 2023, NeurIPS, arXiv:2307.16895",
            "package": "preqts (PyPI), the extracted prequential harness",
        },
    }
