"""Zero-shot foundation tier: Google TimesFM 2.5 (200M, decoder-only), run on the local checkpoint.

TimesFM 2.5 (Das et al. 2024, ICML, arXiv:2310.10688; the 2.5 checkpoint is the 200M PyTorch release with a
16k context and a continuous quantile head) forecasts zero-shot from the vault checkpoint
(``E:\\_Models\\chronoscope\\timesfm-2.5``, Apache-2.0). Same contract and gating pattern as the Chronos
engine: OPT-IN via CHRONOSCOPE_ENABLE_FOUNDATION=1, graceful skip when the package or checkpoint is absent,
module-level pipeline cache, context cap for backtest speed.

Quantile mapping: ``forecast()`` returns (point, quantile_forecast) where the quantile tensor's 10 columns
are [mean, q0.1, q0.2, ..., q0.9] (the continuous quantile head). We map each requested level to its decile
column (levels are rounded to the nearest decile; ChronoScope's canonical levels 0.1/0.5/0.9 map exactly).

Windows roster note (verified 2026-07-10): TiRex-2 is NOT installable on native Windows (its ``flashrnn``
dependency requires ``triton``, which has no Windows wheels) - it stays a WSL2/Linux lane engine. And
``granite-tsfm`` 0.3.6 pins ``torch<2.11`` (conflicts with the cu126 2.12.1 build), so TTM is deferred to a
dedicated venv. The native-Windows foundation roster is therefore Chronos-Bolt + Chronos-2 + TimesFM 2.5.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from ..model.forecasters import Forecaster, _clean

DEFAULT_MODEL_ROOT = r"E:\_Models\chronoscope"
_ENABLE_ENV = "CHRONOSCOPE_ENABLE_FOUNDATION"
_CHECKPOINT_DIR = "timesfm-2.5"

_MODEL_CACHE: dict[str, object] = {}


def _deps_available() -> bool:
    try:
        import timesfm  # noqa: F401
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def _model_root() -> Path:
    return Path(os.environ.get("CHRONOSCOPE_MODEL_ROOT", DEFAULT_MODEL_ROOT))


def _load_model(path: str):
    if path not in _MODEL_CACHE:
        import timesfm

        model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(path)
        # compile once with a generous envelope; the continuous quantile head gives the deciles
        model.compile(timesfm.ForecastConfig(
            max_context=512, max_horizon=64, normalize_inputs=True,
            use_continuous_quantile_head=True,
        ))
        _MODEL_CACHE[path] = model
    return _MODEL_CACHE[path]


class TimesFmForecaster(Forecaster):
    def __init__(self, name: str = "TimesFM-2.5", max_windows: int = 2, ctx_cap: int = 512) -> None:
        self.name = name
        self.family = "foundation"
        self.max_windows = max_windows
        self.ctx_cap = ctx_cap

    def quantiles(self, y: np.ndarray, m: int, h: int, levels: tuple[float, ...]) -> np.ndarray:
        yy = _clean(np.asarray(y, dtype=float))
        if self.ctx_cap and yy.shape[0] > self.ctx_cap:
            yy = yy[-self.ctx_cap:]
        model = _load_model(str(_model_root() / _CHECKPOINT_DIR))
        _point, quant = model.forecast(horizon=h, inputs=[yy])
        q = np.asarray(quant, dtype=float)[0]           # (h, 10): [mean, q0.1 .. q0.9]
        out = np.empty((h, len(levels)), dtype=float)
        for j, lv in enumerate(levels):
            col = int(round(float(lv) * 10))            # 0.1 -> 1, 0.5 -> 5, 0.9 -> 9
            col = min(max(col, 1), 9)
            out[:, j] = q[:, col]
        return np.maximum.accumulate(out, axis=1)       # keep quantiles monotone across levels


def timesfm_forecasters() -> list[TimesFmForecaster]:
    """The TimesFM engine when enabled + installed + checkpoint present, else [] (graceful skip)."""
    if not os.environ.get(_ENABLE_ENV):
        return []
    if not _deps_available():
        return []
    ckpt = _model_root() / _CHECKPOINT_DIR
    if not (ckpt / "model.safetensors").exists():
        return []
    return [TimesFmForecaster()]


def timesfm_available() -> bool:
    """True if the package and the vault checkpoint are present (regardless of the enable flag)."""
    return _deps_available() and (_model_root() / _CHECKPOINT_DIR / "model.safetensors").exists()
