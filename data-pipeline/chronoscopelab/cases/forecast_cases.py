"""Cases spanning CATEGORIES (the forecasting problem-type taxonomy).

Each case is a deterministic series generator (synthetic) or a small committed real series, carrying
its seasonality, horizon, expected behaviour, and a real/synthetic flag. Categories mirror
wip/chronoscope/plan.md: seasonal, trend + seasonal, intermittent demand, near-random-walk (an honesty
case where beating the naive is noise), a real series, and a white-noise control. Later slices expand
toward the target of 12+ cases across more categories and more real datasets from E:\\_Datos\\chronoscope.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..io.schema import Covariate, SeriesSpec

# data-pipeline/chronoscopelab/cases/forecast_cases.py -> parents[3] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EXAMPLES = _REPO_ROOT / "data" / "examples"


@dataclass(frozen=True)
class Case:
    id: str
    category: str
    seasonality: int
    horizon: int
    expected_band: str
    real_or_synthetic: str
    spec: dict  # {"kind": ...} for synthetic, or {"file": "<name>.csv"} for real
    source: str = "synthetic"  # a provenance.SOURCES id; drives the public_artifact_ok export guard


CASES: list[Case] = [
    Case("SEAS_hourly", "seasonal (m=24)", 24, 24,
         "strong daily cycle; seasonal methods should beat naive", "synthetic",
         {"kind": "seasonal", "n": 480, "level": 100.0, "amp": 25.0, "noise": 4.0}),
    Case("TRND_seasonal", "trend + seasonal (m=12)", 12, 12,
         "upward trend with a yearly cycle; Holt-Winters should lead", "synthetic",
         {"kind": "trend_seasonal", "n": 180, "level": 50.0, "slope": 0.4, "amp": 12.0, "noise": 2.5}),
    Case("INTM_demand", "intermittent demand", 1, 12,
         "mostly zeros with sparse demand; hard for smooth methods", "synthetic",
         {"kind": "intermittent", "n": 200, "p": 0.25, "scale": 8.0}),
    Case("RWLK_noise", "near-random-walk (honesty)", 1, 12,
         "random walk; beating the naive is essentially noise", "synthetic",
         {"kind": "random_walk", "n": 200, "step": 1.0}),
    Case("REAL_electricity", "real: electricity load (hourly)", 24, 24,
         "real hourly load; strong daily seasonality with weekday effects", "real",
         {"file": "electricity_sample.csv"}, source="uci_electricity"),
    Case("REAL_pm25", "real: Beijing PM2.5 (hourly)", 24, 24,
         "real hourly air quality; daily cycle + heavy-tailed pollution spikes", "real",
         {"file": "beijing_pm25_sample.csv"}, source="uci_beijing_pm25"),
    Case("REAL_m4_hourly", "real: M4 hourly (m=24)", 24, 24,
         "real M4-competition hourly series; strong daily cycle on genuine benchmark data", "real",
         {"file": "m4_hourly_sample.csv"}, source="monash"),
    Case("REAL_m4_daily", "real: M4 daily (m=7)", 7, 14,
         "real M4-competition daily series; weekly cycle, the real counterpart to the synthetic seasonals",
         "real", {"file": "m4_daily_sample.csv"}, source="monash"),
    Case("CTRL_white_noise", "control: white noise", 1, 12,
         "iid noise: nothing should beat the naive/mean by much", "synthetic",
         {"kind": "white_noise", "n": 160, "noise": 5.0}),
    # --- the deep-context scenarios: each exercises one analysis family the toolkit diagnoses ---
    Case("BRKV_level_shift", "structural break", 12, 12,
         "two clean level shifts; models averaging across regimes should lag the naive after each break",
         "synthetic", {"kind": "level_shift", "n": 300, "noise": 2.0}),
    Case("MSEA_daily_weekly", "multi-seasonal (m=24 + 168)", 24, 24,
         "daily AND weekly cycles superposed; single-m seasonal methods miss the weekly component",
         "synthetic", {"kind": "multi_seasonal", "n": 672, "amp1": 12.0, "amp2": 8.0, "noise": 2.0}),
    Case("HETV_garch", "heteroscedastic (GARCH)", 1, 12,
         "GARCH(1,1) volatility clustering; point forecasts are near-naive but fixed-width intervals fail",
         "synthetic", {"kind": "garch", "n": 500, "omega": 0.2, "alpha": 0.15, "beta": 0.80}),
    Case("LMEM_fractional", "long memory (ARFIMA d=0.35)", 1, 12,
         "fractionally-integrated noise (H~0.85): slow hyperbolic autocorrelation decay, exploitable memory",
         "synthetic", {"kind": "arfima", "n": 500, "d": 0.35, "noise": 1.0}),
    Case("CHAO_mackey", "deterministic chaos (Mackey-Glass)", 1, 12,
         "chaotic but deterministic; short-horizon forecastable, error grows with the Lyapunov horizon",
         "synthetic", {"kind": "mackey_glass", "n": 500, "tau": 17}),
    Case("EXOG_promo", "exogenous driver (known-future covariate)", 7, 14,
         "a weekly cycle plus scheduled promotions known ahead; univariate methods lag every promo, a "
         "covariate-aware forecaster anticipates them (the streaming bench's covariate-policy demonstration)",
         "synthetic", {"kind": "exog_promo", "n": 240, "level": 40.0, "amp": 6.0, "gain": 14.0, "noise": 1.6}),
]


def _rng(seed: int, case_id: str) -> np.random.Generator:
    # Distinct, reproducible stream per case. hashlib (not builtin hash(), which is salted per process).
    digest = hashlib.sha1(case_id.encode("utf-8")).digest()[:4]
    return np.random.default_rng(seed + int.from_bytes(digest, "big") % 100_000)


def _synth(spec: dict, seed: int, case_id: str) -> list[float]:
    rng = _rng(seed, case_id)
    kind = spec["kind"]
    n = int(spec["n"])
    t = np.arange(n, dtype=float)
    if kind == "seasonal":
        m = 24
        y = spec["level"] + spec["amp"] * np.sin(2 * math.pi * t / m) + rng.normal(0, spec["noise"], n)
    elif kind == "trend_seasonal":
        m = 12
        y = (spec["level"] + spec["slope"] * t + spec["amp"] * np.sin(2 * math.pi * t / m)
             + rng.normal(0, spec["noise"], n))
    elif kind == "intermittent":
        occur = rng.random(n) < spec["p"]
        y = np.where(occur, rng.gamma(2.0, spec["scale"] / 2.0, n), 0.0)
    elif kind == "random_walk":
        y = 100.0 + np.cumsum(rng.normal(0, spec["step"], n))
    elif kind == "white_noise":
        y = 50.0 + rng.normal(0, spec["noise"], n)
    elif kind == "level_shift":
        # piecewise-constant mean with two clean breaks at 1/3 and 2/3 (the change-point scenario)
        y = np.full(n, 50.0)
        y[n // 3:] += 15.0
        y[2 * n // 3:] -= 25.0
        y = y + 6.0 * np.sin(2 * math.pi * t / 12) + rng.normal(0, spec["noise"], n)
    elif kind == "multi_seasonal":
        # daily (24) + weekly (168) cycles superposed (the MSTL / multi-seasonality scenario)
        y = (80.0 + spec["amp1"] * np.sin(2 * math.pi * t / 24)
             + spec["amp2"] * np.sin(2 * math.pi * t / 168) + rng.normal(0, spec["noise"], n))
    elif kind == "garch":
        # GARCH(1,1) returns accumulated onto a level: volatility clusters, point path near-random
        omega, a1, b1 = spec["omega"], spec["alpha"], spec["beta"]
        eps = np.empty(n)
        sig2 = omega / max(1e-9, (1 - a1 - b1))
        for i in range(n):
            z = rng.normal()
            eps[i] = math.sqrt(sig2) * z
            sig2 = omega + a1 * eps[i] ** 2 + b1 * sig2
        y = 100.0 + np.cumsum(eps * 0.25)
    elif kind == "arfima":
        # fractionally-integrated noise via the truncated MA(inf) expansion of (1-B)^{-d} eps_t
        # (Granger-Joyeux 1980; Hosking 1981): psi_k = Gamma(k+d) / (Gamma(k+1) Gamma(d))
        d = float(spec["d"])
        k = np.arange(1, n, dtype=float)
        psi = np.empty(n)
        psi[0] = 1.0
        psi[1:] = np.cumprod((k - 1 + d) / k)          # recursive form of the Gamma ratio
        eps = rng.normal(0, spec["noise"], n)
        y = 50.0 + np.convolve(eps, psi)[:n]
    elif kind == "mackey_glass":
        # Mackey-Glass delay differential (tau=17 -> chaotic), Euler-integrated then decimated.
        # Sampled every 6 time units: the 0-1 chaos test misreads OVERSAMPLED chaos as regular (a
        # documented caveat), and this stride gives K ~ 0.9 with a positive Lyapunov (verified sweep).
        tau = int(spec["tau"])
        dt = 0.1
        sample_every = 6.0
        steps = int(n * sample_every / dt) + tau * 10 + 2000   # generous transient discard
        hist = np.full(steps, 1.2)
        hist[: int(tau / dt)] += 0.01 * rng.normal(size=int(tau / dt))  # seed-dependent initial history
        delay = int(tau / dt)
        for i in range(delay, steps - 1):
            x_tau = hist[i - delay]
            hist[i + 1] = hist[i] + dt * (0.2 * x_tau / (1 + x_tau ** 10) - 0.1 * hist[i])
        stride = int(sample_every / dt)
        y = 50.0 + 20.0 * hist[-n * stride::stride][:n]
    else:
        raise ValueError(f"unknown synthetic kind: {kind!r}")
    return [float(v) for v in y]


def _load_real(spec: dict) -> list[float]:
    path = _EXAMPLES / spec["file"]
    import csv

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [float(r["y"]) for r in rows]


def _synth_exog(spec: dict, seed: int, case_id: str) -> tuple[list[float], list[float]]:
    """Target driven by a KNOWN-FUTURE exogenous regressor (scheduled promotions) + a weekly cycle.

    The driver is a pulse train of scheduled promotions at seeded-irregular positions: planned ahead, so
    its future values are known, but NOT predictable from the target's own history (the jumps land at
    irregular times). A univariate method must lag every promo; a covariate-aware method that sees the
    driver ahead can anticipate them. That gap is exactly what the streaming bench's covariate policy shows.
    """
    rng = _rng(seed, case_id)
    n = int(spec["n"])
    m = 7
    t = np.arange(n, dtype=float)
    driver = np.zeros(n)
    pos = int(rng.integers(6, 12))
    while pos < n:
        dur = int(rng.integers(2, 5))
        mag = float(rng.uniform(0.6, 1.4))
        driver[pos:min(n, pos + dur)] = mag
        pos += int(rng.integers(10, 22))
    base = spec["level"] + spec["amp"] * np.sin(2 * math.pi * t / m)
    y = base + spec["gain"] * driver + rng.normal(0, spec["noise"], n)
    return [float(v) for v in y], [float(v) for v in driver]


def build_series(case: Case, seed: int = 42) -> SeriesSpec:
    """Produce the (deterministic) SeriesSpec for a case (with optional exogenous covariates)."""
    covariates: tuple[Covariate, ...] = ()
    if case.real_or_synthetic == "real":
        y = _load_real(case.spec)
    elif case.spec.get("kind") == "exog_promo":
        ylist, driver = _synth_exog(case.spec, seed, case.id)
        y = ylist
        covariates = (Covariate(name="promo", values=tuple(driver), kind="known_future", lag=0),)
    else:
        y = _synth(case.spec, seed, case.id)
    return SeriesSpec(
        case_id=case.id, y=tuple(y), seasonality=case.seasonality,
        horizon=case.horizon, freq="", source=case.real_or_synthetic, covariates=covariates,
    )
