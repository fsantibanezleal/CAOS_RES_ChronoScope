"""Volatility, heteroscedasticity, and variance-stabilizing transforms.

Two related questions: (1) is the series' variance constant, or does it cluster in bursts (conditional
heteroscedasticity)? and (2) can a power transform stabilize a growing variance so an additive model fits a
multiplicative series? The first is answered by Engle's ARCH-LM test and a fitted GARCH conditional-variance
model; the second by the Box-Cox family with an MLE or Guerrero (seasonal) lambda. Each is delegated to its
authoritative implementation and wrapped in one NaN-safe API carrying the primary reference.

IMPORTANT scope note: GARCH here characterises VOLATILITY (the second moment). It is an ANALYSIS tool, not a
point-forecast method; the forecasting ladder's point methods live in ``model/``. Volatility structure is a
property the analysis pillar surfaces (e.g. finance/energy series with variance clustering), and it explains
why a point forecast's intervals should widen in turbulent regimes.

Methods / references (verified 2026-07-04, see wip/chronoscope/research-volatility-transforms-2026-07-04.md):
  * ARCH-LM - Engle 1982, Econometrica 50(4):987-1007, DOI 10.2307/1912773. ``statsmodels.stats.diagnostic.het_arch``.
  * GARCH / EGARCH - Bollerslev 1986, J. Econometrics 31(3):307-327, DOI 10.1016/0304-4076(86)90063-1.
    ``arch.arch_model`` (Sheppard). EGARCH captures leverage asymmetry; FIGARCH captures long-memory volatility.
  * Box-Cox - Box & Cox 1964, JRSS-B 26(2):211-252, JSTOR 2984418. ``scipy.stats.boxcox`` / ``boxcox_normmax``.
  * Guerrero lambda - Guerrero 1993, J. Forecasting 12(1):37-48, DOI 10.1002/for.3980120104.
    ``coreforecast.scalers.boxcox_lambda(method='guerrero', season_length=...)`` (an installed dependency).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


@dataclass(frozen=True)
class ArchTest:
    """Engle ARCH-LM test for conditional heteroscedasticity (variance clustering)."""

    lm_stat: float
    lm_pvalue: float
    f_stat: float
    f_pvalue: float
    nlags: int
    has_arch: bool
    alpha: float
    reference: str


def arch_lm(x, nlags: int = 12, alpha: float = 0.05, demean: bool = True) -> ArchTest:
    """ARCH-LM on the series (demeaned by default). Small p => variance clusters (ARCH effects present)."""
    from statsmodels.stats.diagnostic import het_arch

    a = _clean(x)
    resid = a - a.mean() if demean else a
    lm_stat, lm_p, f_stat, f_p = het_arch(resid, nlags=nlags)
    return ArchTest(
        lm_stat=float(lm_stat), lm_pvalue=float(lm_p), f_stat=float(f_stat), f_pvalue=float(f_p),
        nlags=int(nlags), has_arch=bool(lm_p < alpha), alpha=alpha,
        reference="Engle 1982, Econometrica 50(4):987-1007, DOI 10.2307/1912773",
    )


@dataclass(frozen=True)
class GarchFit:
    """A fitted GARCH-family conditional-variance model: per-point conditional volatility + parameters."""

    vol: str
    p: int
    q: int
    params: dict[str, float]
    conditional_volatility: np.ndarray   # sigma_t per point (std, not variance)
    persistence: float                   # sum(alpha)+sum(beta): near 1 => shocks persist (IGARCH-like)
    loglikelihood: float
    reference: str


def garch(x, p: int = 1, q: int = 1, vol: str = "GARCH", dist: str = "normal",
          rescale: bool = True) -> GarchFit:
    """Fit a GARCH(p,q) (or EGARCH/FIGARCH) conditional-variance model to the series' mean residuals."""
    from arch import arch_model

    a = _clean(x)
    # arch prefers series scaled to roughly unit range; rescale=True lets it handle that internally.
    model = arch_model(a, mean="Constant", vol=vol, p=p, q=q, dist=dist, rescale=rescale)
    res = model.fit(disp="off")
    params = {k: float(v) for k, v in res.params.items()}
    # persistence: sum of the alpha[*] and beta[*] parameters (standard GARCH stationarity read-out)
    persistence = float(sum(v for k, v in params.items() if k.startswith(("alpha", "beta"))))
    return GarchFit(
        vol=vol, p=p, q=q, params=params,
        conditional_volatility=np.asarray(res.conditional_volatility, dtype=float),
        persistence=persistence, loglikelihood=float(res.loglikelihood),
        reference="Bollerslev 1986, J. Econometrics 31(3):307-327, DOI 10.1016/0304-4076(86)90063-1",
    )


@dataclass(frozen=True)
class BoxCoxResult:
    """A Box-Cox variance-stabilizing transform: the fitted lambda, the transformed series, and the shift."""

    lam: float
    method: str                  # "mle", "guerrero", or "log"
    transformed: np.ndarray
    shift: float                 # amount added to make the series strictly positive (0 if already >0)
    reference: str


def _positive_shift(a: np.ndarray) -> tuple[np.ndarray, float]:
    """Box-Cox needs y > 0; shift by (1 - min) when non-positive values are present. Record the shift."""
    m = float(np.min(a))
    if m <= 0:
        shift = 1.0 - m
        return a + shift, shift
    return a, 0.0


def box_cox(x, method: str = "mle", season_length: int | None = None) -> BoxCoxResult:
    """Box-Cox transform with lambda by MLE (scipy) or Guerrero (coreforecast, seasonal-aware).

    ``method='mle'`` maximizes the profile likelihood; ``method='guerrero'`` minimizes the coefficient of
    variation across seasonal subseries (needs ``season_length``); ``method='log'`` forces lambda=0.
    """
    a = _clean(x)
    shifted, shift = _positive_shift(a)
    if method == "log":
        return BoxCoxResult(lam=0.0, method="log", transformed=np.log(shifted), shift=shift,
                            reference="Box & Cox 1964, JRSS-B 26(2):211-252, JSTOR 2984418 (log special case)")
    if method == "guerrero":
        from coreforecast.scalers import boxcox_lambda
        from scipy.special import boxcox as _bc

        if not season_length or season_length < 2:
            raise ValueError("Guerrero lambda needs season_length >= 2")
        lam = float(boxcox_lambda(shifted.astype(np.float64), method="guerrero", season_length=season_length))
        transformed = np.asarray(_bc(shifted, lam), dtype=float)
        return BoxCoxResult(lam=lam, method="guerrero", transformed=transformed, shift=shift,
                            reference="Guerrero 1993, J. Forecasting 12(1):37-48, DOI 10.1002/for.3980120104")
    # default: MLE via scipy
    from scipy.stats import boxcox as _scipy_boxcox

    transformed, lam = _scipy_boxcox(shifted)
    return BoxCoxResult(lam=float(lam), method="mle", transformed=np.asarray(transformed, dtype=float),
                        shift=shift, reference="Box & Cox 1964, JRSS-B 26(2):211-252, JSTOR 2984418")


def rolling_volatility(x, window: int = 20) -> dict:
    """Rolling mean and std (the visual heteroscedasticity check); returns JSON-ready arrays."""
    import pandas as pd

    a = _clean(x)
    s = pd.Series(a)
    return {
        "window": int(window),
        "rolling_mean": s.rolling(window).mean().to_numpy().tolist(),
        "rolling_std": s.rolling(window).std().to_numpy().tolist(),
    }


def volatility_report(x, arch_lags: int = 12, season_length: int | None = None,
                      garch_pq: tuple[int, int] = (1, 1)) -> dict:
    """Run the volatility panel (ARCH-LM + rolling vol + Box-Cox lambda; GARCH only if ARCH is present)."""
    a = _clean(x)
    at = arch_lm(a, nlags=arch_lags)
    out = {
        "n": int(len(a)),
        "arch_lm": {"lm_stat": at.lm_stat, "lm_pvalue": at.lm_pvalue, "nlags": at.nlags,
                    "has_arch": at.has_arch, "reference": at.reference},
        "rolling": rolling_volatility(a, window=min(20, max(3, len(a) // 10))),
    }
    # Box-Cox lambda: Guerrero when a season is given, else MLE. Records the shift if non-positive.
    try:
        method = "guerrero" if (season_length and season_length >= 2) else "mle"
        bc = box_cox(a, method=method, season_length=season_length)
        out["boxcox"] = {"lambda": bc.lam, "method": bc.method, "shift": bc.shift, "reference": bc.reference}
    except Exception as exc:  # noqa: BLE001 - record, do not crash the bake
        out["boxcox"] = {"error": f"{type(exc).__name__}: {exc}"}
    # Fit GARCH only when ARCH effects are actually present (else the model is not warranted).
    if at.has_arch:
        try:
            g = garch(a, p=garch_pq[0], q=garch_pq[1])
            out["garch"] = {"vol": g.vol, "p": g.p, "q": g.q, "params": g.params,
                            "persistence": g.persistence, "loglikelihood": g.loglikelihood,
                            "reference": g.reference}
        except Exception as exc:  # noqa: BLE001
            out["garch"] = {"error": f"{type(exc).__name__}: {exc}"}
    else:
        out["garch"] = {"skipped": "no significant ARCH effects (het_arch p >= alpha); GARCH not warranted"}
    return out
