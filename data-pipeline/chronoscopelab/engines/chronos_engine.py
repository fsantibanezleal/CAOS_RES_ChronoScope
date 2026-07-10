"""Zero-shot foundation-model tier (SOTA): Amazon Chronos, run on local checkpoints.

This is the offline hard-processing tier of the ladder: a pretrained transformer forecasts each case
zero-shot (no fitting). It is offline-only (torch is heavy and not Pyodide-safe) and runs on the
checkpoints in the model vault (`E:\\_Models\\chronoscope` by default, override with the
`CHRONOSCOPE_MODEL_ROOT` env var). The loaded pipeline is cached at module level so a checkpoint is read
from disk once per process and reused across every backtest window and case.

Graceful degradation: if torch / chronos-forecasting are not installed, or a checkpoint folder is
absent, the corresponding engine is simply omitted and the rest of the ladder runs. The heavy deps live
in `data-pipeline/requirements-foundation.txt` (opt-in), so the core precompute stays light.

Because these models are zero-shot, they are the definition of the "beyond the classical/statistical
baselines" tier the atlas compares against. In the web app they are replay-only (baked artifacts);
the live lane runs the classical core (and, in a later slice, small ONNX-exported deep models).
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from ..model.forecasters import Forecaster, _clean

DEFAULT_MODEL_ROOT = r"E:\_Models\chronoscope"

# (display name, checkpoint folder under the model root). Apache-2.0. TimesFM 2.5 and TiRex-2 need their
# own loaders (different packages) and are tracked separately; the chronos-forecasting package serves both
# Chronos-Bolt (CPU-fast T5 patching) and Chronos-2 (120M, the strongest all-rounder; GPU).
_CHECKPOINTS = [
    ("Chronos-Bolt", "chronos-bolt-small"),
    ("Chronos-2", "chronos-2"),
]

# The foundation tier is heavy (loads a transformer + CPU inference per backtest window), so it is OPT-IN:
# set CHRONOSCOPE_ENABLE_FOUNDATION=1 to include it (canonical artifact baking does this). The test suite
# leaves it off so pytest runs fast on the classical + statistical + ML ladder; the foundation engine has
# its own direct test.
_ENABLE_ENV = "CHRONOSCOPE_ENABLE_FOUNDATION"

_PIPE_CACHE: dict[str, object] = {}


def _deps_available() -> bool:
    try:
        import chronos  # noqa: F401
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def _model_root() -> Path:
    return Path(os.environ.get("CHRONOSCOPE_MODEL_ROOT", DEFAULT_MODEL_ROOT))


def _load_pipeline(path: str):
    if path not in _PIPE_CACHE:
        from chronos import BaseChronosPipeline

        _PIPE_CACHE[path] = BaseChronosPipeline.from_pretrained(path, device_map="cpu")
    return _PIPE_CACHE[path]


class ChronosForecaster(Forecaster):
    def __init__(self, name: str, path: str, max_windows: int = 2, ctx_cap: int | None = 512) -> None:
        self.name = name
        self.family = "foundation"
        self.path = path
        self.max_windows = max_windows
        self.ctx_cap = ctx_cap

    def quantiles(self, y: np.ndarray, m: int, h: int, levels: tuple[float, ...]) -> np.ndarray:
        import torch

        yy = _clean(np.asarray(y, dtype=float))
        if self.ctx_cap and yy.shape[0] > self.ctx_cap:
            yy = yy[-self.ctx_cap:]
        pipe = _load_pipeline(self.path)
        x = torch.tensor(yy, dtype=torch.float32)
        try:
            # Chronos / Chronos-Bolt API: 1-D context -> (1, h, Q) tensor
            q, _mean = pipe.predict_quantiles(x, prediction_length=h, quantile_levels=list(levels))
            out = np.asarray(q, dtype=float)[0]
        except (ValueError, TypeError):
            # Chronos-2 API: (n_series, n_variates, T) -> list of (n_variates, h, Q) tensors
            q, _mean = pipe.predict_quantiles(x.reshape(1, 1, -1), prediction_length=h,
                                              quantile_levels=list(levels))
            out = np.asarray(q[0], dtype=float)[0]
        return np.maximum.accumulate(out, axis=1)  # keep quantiles monotone across levels


def chronos_forecasters() -> list[ChronosForecaster]:
    """The Chronos engines whose checkpoints are present, or [] if the tier is disabled, the deps are
    missing, or the checkpoints are absent. Enable with CHRONOSCOPE_ENABLE_FOUNDATION=1."""
    if not os.environ.get(_ENABLE_ENV):
        return []
    if not _deps_available():
        return []
    root = _model_root()
    out: list[ChronosForecaster] = []
    for name, folder in _CHECKPOINTS:
        path = root / folder
        if (path / "config.json").exists():
            out.append(ChronosForecaster(name, str(path)))
    return out


def foundation_available() -> bool:
    """True if the foundation deps and at least one checkpoint are present (regardless of the enable flag)."""
    if not _deps_available():
        return False
    root = _model_root()
    return any((root / folder / "config.json").exists() for _n, folder in _CHECKPOINTS)
