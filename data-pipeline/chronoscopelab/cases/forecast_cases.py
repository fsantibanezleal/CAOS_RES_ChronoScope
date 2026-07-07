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

from ..io.schema import SeriesSpec

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
    Case("CTRL_white_noise", "control: white noise", 1, 12,
         "iid noise: nothing should beat the naive/mean by much", "synthetic",
         {"kind": "white_noise", "n": 160, "noise": 5.0}),
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
    else:
        raise ValueError(f"unknown synthetic kind: {kind!r}")
    return [float(v) for v in y]


def _load_real(spec: dict) -> list[float]:
    path = _EXAMPLES / spec["file"]
    import csv

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [float(r["y"]) for r in rows]


def build_series(case: Case, seed: int = 42) -> SeriesSpec:
    """Produce the (deterministic) SeriesSpec for a case."""
    if case.real_or_synthetic == "real":
        y = _load_real(case.spec)
    else:
        y = _synth(case.spec, seed, case.id)
    return SeriesSpec(
        case_id=case.id, y=tuple(y), seasonality=case.seasonality,
        horizon=case.horizon, freq="", source=case.real_or_synthetic,
    )
