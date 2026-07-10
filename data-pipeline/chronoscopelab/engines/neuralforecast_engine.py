"""Deep forecasting tier (canonical): neuralforecast NHITS / DLinear / NLinear, GPU-trained per case.

With the pipeline's Python base on 3.12 (decision revised 2026-07-10: ray ships cp312 win_amd64 wheels, so
neuralforecast installs; the earlier blocker was py3.13-on-Windows-specific), the REAL Nixtla framework is
the canonical deep tier: ``neuralforecast`` trains NHITS, DLinear and NLinear per case with a multi-quantile
``MQLoss`` so each forecast carries a calibrated interval. The direct-torch implementations in
``neural_engine.py`` are kept as the independent parity reference (same architectures, no framework).

Engineering notes:
  * OPT-IN via CHRONOSCOPE_ENABLE_NEURALFORECAST=1 (heavy: Lightning + per-case training). Graceful skip when
    the framework or torch is absent (CI, the py3.13 venv).
  * GPU when available (``accelerator='gpu'`` through Lightning), CPU fallback otherwise.
  * Deterministic: seeded per fit; ``enable_progress_bar=False, logger=False`` keeps the bake logs clean.
  * The frequency passed to NeuralForecast is synthetic ("h"): the pipeline's series are index-based, and the
    model only uses the index spacing, not calendar semantics.

References:
  * neuralforecast (Nixtla), Apache-2.0: https://github.com/Nixtla/neuralforecast
  * NHITS - Challu et al. 2023, AAAI-23, arXiv:2201.12886 (the official implementation lives in this package).
  * DLinear / NLinear - Zeng et al. 2023, AAAI-23, arXiv:2205.13504.
"""
from __future__ import annotations

import os

import numpy as np

from ..model.forecasters import Forecaster, _clean

_ENABLE_ENV = "CHRONOSCOPE_ENABLE_NEURALFORECAST"


def _deps_available() -> bool:
    try:
        import neuralforecast  # noqa: F401
        import torch  # noqa: F401
        return True
    except Exception:
        return False


class NeuralForecastForecaster(Forecaster):
    """Train one neuralforecast model per case; return monotone quantile forecasts (GPU when available)."""

    def __init__(self, name: str, max_steps: int = 300, max_windows: int = 3, seed: int = 42) -> None:
        self.name = f"{name} (nf)"
        self.model_name = name
        self.family = "deep"
        self.max_steps = max_steps
        self.max_windows = max_windows
        self.seed = seed

    def quantiles(self, y: np.ndarray, m: int, h: int, levels: tuple[float, ...]) -> np.ndarray:
        import warnings

        import pandas as pd

        from .. import gpu

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from neuralforecast import NeuralForecast
            from neuralforecast.losses.pytorch import MQLoss
            from neuralforecast.models import NHITS, DLinear, NLinear

            yy = _clean(np.asarray(y, dtype=float))
            # adaptive lookback: prefer 2h / 3m, but shrink to fit the available context
            lookback = max(2 * h, 3 * max(m, 1))
            lookback = min(lookback, len(yy) - h - 8)
            if lookback < 4:
                raise ValueError("series too short for the deep tier")

            classes = {"NHITS": NHITS, "DLinear": DLinear, "NLinear": NLinear}
            cls = classes[self.model_name]
            kwargs = dict(h=h, input_size=lookback, max_steps=self.max_steps,
                          loss=MQLoss(quantiles=list(levels)), random_seed=self.seed,
                          enable_progress_bar=False, logger=False,
                          accelerator="gpu" if gpu.cuda_available() else "cpu", devices=1)
            model = cls(**kwargs)
            nf = NeuralForecast(models=[model], freq="h")
            df = pd.DataFrame({
                "unique_id": "series",
                "ds": pd.date_range("2000-01-01", periods=len(yy), freq="h"),
                "y": yy,
            })
            nf.fit(df)
            fc = nf.predict()

            # MQLoss emits one column per quantile: "<Model>-lo-80", "<Model>-median", "<Model>-hi-80" style
            # OR "<Model>-ql0.1"; resolve by matching each requested level to its column.
            cols = [c for c in fc.columns if c not in ("unique_id", "ds")]
            out = np.empty((h, len(levels)), dtype=float)
            for j, lv in enumerate(levels):
                col = _match_quantile_column(cols, self.model_name, float(lv))
                out[:, j] = np.asarray(fc[col], dtype=float)[:h]
            return np.maximum.accumulate(out, axis=1)


def _match_quantile_column(cols: list[str], model: str, level: float) -> str:
    """Resolve the forecast column for a quantile level across neuralforecast's naming schemes."""
    # exact ql-style: "NHITS-ql0.1"
    for c in cols:
        if c.endswith(f"ql{level}") or c.endswith(f"ql-{level}"):
            return c
    if abs(level - 0.5) < 1e-9:
        for c in cols:
            if c.endswith("-median") or c == model:
                return c
    # lo/hi-style with a central band percentage: level 0.1 -> "lo-80" / "lo-80.0" (int or float form)
    band = abs(1.0 - 2.0 * level) * 100
    side = "lo" if level < 0.5 else "hi"
    for suffix in (f"{side}-{band:g}", f"{side}-{int(round(band))}", f"{side}-{band:.1f}"):
        for c in cols:
            if c.endswith(suffix):
                return c
    raise KeyError(f"no forecast column for quantile {level} among {cols}")


def neuralforecast_forecasters() -> list[NeuralForecastForecaster]:
    """The canonical deep engines, or [] when disabled (CHRONOSCOPE_ENABLE_NEURALFORECAST=1) or deps absent."""
    if not os.environ.get(_ENABLE_ENV):
        return []
    if not _deps_available():
        return []
    return [NeuralForecastForecaster("NHITS"), NeuralForecastForecaster("DLinear"),
            NeuralForecastForecaster("NLinear")]


def neuralforecast_available() -> bool:
    """True if neuralforecast + torch are importable (regardless of the enable flag)."""
    return _deps_available()
