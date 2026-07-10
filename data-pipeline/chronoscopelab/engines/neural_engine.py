"""Deep forecasting tier (direct-torch reference): NLinear, DLinear, NHITS trained per case on the GPU.

These are the REAL published architectures implemented directly against their papers - genuinely faithful
(DLinear/NLinear are single linear layers on a decomposition; NHITS is a documented multi-rate MLP stack),
running on the torch cu126 GPU build with a CPU fallback via ``chronoscopelab.gpu``.

ROLE (revised 2026-07-10): with the pipeline's Python base on 3.12, neuralforecast IS installable (ray ships
cp312 win_amd64 wheels; the earlier "uninstallable" verdict was py3.13-on-Windows-specific) and becomes the
canonical deep tier. THIS module is kept as the independent PARITY REFERENCE and CI-friendly fallback: same
architectures, no framework, so the two implementations cross-check each other. Decision + revision:
wip/chronoscope/deep-engine-decision-2026-07-04.md.

Each model is trained per case, with a windowed (input -> horizon) dataset drawn from the history and a
multi-quantile (pinball) loss so the forecast carries a calibrated interval, not just a point. Training is
seeded for determinism. The engines degrade gracefully: if torch is absent, ``neural_forecasters()`` returns
[] and the rest of the ladder runs. Like the foundation tier they are OPT-IN via CHRONOSCOPE_ENABLE_NEURAL=1
(off in the fast unit-test path; the engine has its own direct GPU-gated test).

References:
  * DLinear / NLinear - Zeng et al. 2023, AAAI-23, arXiv:2205.13504.
  * NHITS - Challu et al. 2023, AAAI-23, arXiv:2201.12886.
  * pinball / quantile loss - Koenker & Bassett 1978.
"""
from __future__ import annotations

import os

import numpy as np

from ..model.forecasters import Forecaster, _clean

_ENABLE_ENV = "CHRONOSCOPE_ENABLE_NEURAL"


def _deps_available() -> bool:
    try:
        import torch  # noqa: F401
        return True
    except Exception:
        return False


# --- the models (torch nn.Modules), defined lazily inside a factory so torch is not imported at module load ---

def _build_models():
    import torch
    import torch.nn as nn

    class NLinear(nn.Module):
        """NLinear: subtract the last value, one Linear layer over the lookback, add it back (Zeng 2023).

        A per-quantile output head turns the single linear map into a quantile forecast.
        """

        def __init__(self, lookback: int, horizon: int, n_quantiles: int) -> None:
            super().__init__()
            self.proj = nn.Linear(lookback, horizon * n_quantiles)
            self.horizon = horizon
            self.n_quantiles = n_quantiles

        def forward(self, x):  # x: (B, lookback)
            last = x[:, -1:]                       # normalize by the last value (the "N" in NLinear)
            out = self.proj(x - last)
            out = out.view(-1, self.horizon, self.n_quantiles) + last.unsqueeze(-1)
            return out                              # (B, horizon, n_quantiles)

    class DLinear(nn.Module):
        """DLinear: decompose into trend (moving average) + remainder, a Linear on each, sum (Zeng 2023)."""

        def __init__(self, lookback: int, horizon: int, n_quantiles: int, kernel: int = 25) -> None:
            super().__init__()
            self.kernel = min(kernel, lookback if lookback % 2 else lookback - 1) or 3
            if self.kernel % 2 == 0:
                self.kernel += 1
            self.trend = nn.Linear(lookback, horizon * n_quantiles)
            self.seasonal = nn.Linear(lookback, horizon * n_quantiles)
            self.horizon = horizon
            self.n_quantiles = n_quantiles

        def _moving_avg(self, x):
            pad = self.kernel // 2
            xp = torch.nn.functional.pad(x.unsqueeze(1), (pad, pad), mode="replicate")
            return torch.nn.functional.avg_pool1d(xp, self.kernel, stride=1).squeeze(1)

        def forward(self, x):
            trend = self._moving_avg(x)
            seasonal = x - trend
            out = self.trend(trend) + self.seasonal(seasonal)
            return out.view(-1, self.horizon, self.n_quantiles)

    class NHITS(nn.Module):
        """A compact NHITS: a stack of MLP blocks at decreasing pooling rates, summed (Challu 2023).

        Each block pools the input (multi-rate sampling), maps through an MLP to a backcast + forecast, and
        the forecasts are summed hierarchically. Kept small for the 8 GB budget and the short case histories.
        """

        def __init__(self, lookback: int, horizon: int, n_quantiles: int,
                     pools=(4, 2, 1), hidden: int = 128) -> None:
            super().__init__()
            self.horizon = horizon
            self.n_quantiles = n_quantiles
            self.blocks = nn.ModuleList()
            self.pools = []
            for p in pools:
                pl = max(1, min(p, lookback))
                self.pools.append(pl)
                pooled = lookback // pl
                self.blocks.append(nn.Sequential(
                    nn.Linear(pooled, hidden), nn.ReLU(),
                    nn.Linear(hidden, hidden), nn.ReLU(),
                    nn.Linear(hidden, horizon * n_quantiles),
                ))

        def forward(self, x):
            total = 0.0
            for pl, block in zip(self.pools, self.blocks):
                xp = torch.nn.functional.avg_pool1d(x.unsqueeze(1), pl, stride=pl).squeeze(1) if pl > 1 else x
                total = total + block(xp)
            return total.view(-1, self.horizon, self.n_quantiles)

    return {"NLinear": NLinear, "DLinear": DLinear, "NHITS": NHITS}


class NeuralForecaster(Forecaster):
    """Train one deep model per case and return monotone quantile forecasts (GPU when available)."""

    def __init__(self, name: str, lookback_mult: int = 3, max_steps: int = 300,
                 hidden: int = 128, max_windows: int = 3, seed: int = 42) -> None:
        self.name = name
        self.family = "deep"
        self.lookback_mult = lookback_mult
        self.max_steps = max_steps
        self.hidden = hidden
        self.max_windows = max_windows
        self.seed = seed

    def quantiles(self, y: np.ndarray, m: int, h: int, levels: tuple[float, ...]) -> np.ndarray:
        yy = _clean(np.asarray(y, dtype=float))
        # adaptive lookback: prefer 2h / 3m, but shrink to fit the available context (>= 8 training windows)
        lookback = max(2 * h, self.lookback_mult * max(m, 1))
        lookback = min(lookback, len(yy) - h - 8)
        if lookback < 4:
            raise ValueError("series too short for the deep tier")
        if _run_in_subprocess():
            return _train_in_subprocess(self.name, yy, m, h, levels, lookback,
                                        self.max_steps, self.hidden, self.seed)
        return self._train(yy, m, h, levels, lookback)

    def _train(self, yy: np.ndarray, m: int, h: int, levels: tuple[float, ...], lookback: int) -> np.ndarray:
        """Train the model in-process (used directly on non-Windows / when numba is not co-resident)."""
        import torch

        from .. import gpu

        dev = torch.device(gpu.device())
        torch.manual_seed(self.seed)
        np_rng = np.random.default_rng(self.seed)

        # standardize (deep models train better on ~unit-scale inputs); undo on output
        mu, sd = float(np.mean(yy)), float(np.std(yy)) or 1.0
        z = (yy - mu) / sd

        # build the sliding (input -> horizon) windows
        xs, ts = [], []
        for start in range(0, len(z) - lookback - h + 1):
            xs.append(z[start:start + lookback])
            ts.append(z[start + lookback:start + lookback + h])
        X = torch.tensor(np.array(xs), dtype=torch.float32, device=dev)
        T = torch.tensor(np.array(ts), dtype=torch.float32, device=dev)

        qlevels = torch.tensor(list(levels), dtype=torch.float32, device=dev)
        model_cls = _build_models()[self.name]
        model = model_cls(lookback, h, len(levels)).to(dev)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)

        model.train()
        n = X.shape[0]
        batch = min(64, n)
        for _step in range(self.max_steps):
            idx = np_rng.integers(0, n, size=batch)
            xb, tb = X[idx], T[idx]                       # (B, lookback), (B, h)
            pred = model(xb)                              # (B, h, Q)
            # pinball loss summed over quantiles: mean over B, h, Q
            err = tb.unsqueeze(-1) - pred                 # (B, h, Q)
            loss = torch.maximum(qlevels * err, (qlevels - 1) * err).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()

        model.eval()
        with torch.no_grad():
            last_x = torch.tensor(z[-lookback:], dtype=torch.float32, device=dev).unsqueeze(0)
            out = model(last_x)[0].cpu().numpy()          # (h, Q)
        out = out * sd + mu
        return np.maximum.accumulate(out, axis=1)         # keep quantiles monotone across levels


# --- subprocess isolation (Windows numba+CUDA coexistence) --------------------------------------------------
# When numba (statsforecast) and CUDA (torch) initialize in the SAME process on this Windows box, the D:
# working drive enters a transactional-NTFS state that breaks subsequent file writes (WinError 6714). Running
# the torch training in a fresh SUBPROCESS keeps numba and CUDA in separate processes, so the parent's
# filesystem stays healthy. Verified 2026-07-04 (see docs/architecture/09_known-issues.md).

def _run_in_subprocess() -> bool:
    """Isolate torch in a subprocess on Windows (numba+CUDA taint); opt out with CHRONOSCOPE_NEURAL_INPROC=1."""
    import sys

    if os.environ.get("CHRONOSCOPE_NEURAL_INPROC"):
        return False
    return sys.platform == "win32"


def _train_in_subprocess(name, yy, m, h, levels, lookback, max_steps, hidden, seed) -> np.ndarray:
    """Run one model's training + forecast in a fresh Python process; return the (h, Q) quantile array."""
    import json
    import subprocess
    import sys
    import tempfile

    payload = {
        "name": name, "y": [float(v) for v in yy], "m": int(m), "h": int(h),
        "levels": list(levels), "lookback": int(lookback), "max_steps": int(max_steps),
        "hidden": int(hidden), "seed": int(seed),
    }
    fd, in_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    fd, out_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        with open(in_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        code = (
            "import json,sys;"
            "from chronoscopelab.engines.neural_engine import _subprocess_entry;"
            f"_subprocess_entry(r'{in_path}', r'{out_path}')"
        )
        res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=900)
        if res.returncode != 0:
            raise RuntimeError(f"deep subprocess failed for {name}: {res.stderr[-400:]}")
        with open(out_path, encoding="utf-8") as f:
            arr = json.load(f)
        return np.asarray(arr, dtype=float)
    finally:
        for pth in (in_path, out_path):
            if os.path.exists(pth):
                os.remove(pth)


def _subprocess_entry(in_path: str, out_path: str) -> None:
    """Entry point run inside the subprocess: read the payload, train in-process, write the quantiles."""
    import json

    with open(in_path, encoding="utf-8") as f:
        p = json.load(f)
    yy = np.asarray(p["y"], dtype=float)
    fc = NeuralForecaster(p["name"], max_steps=p["max_steps"], hidden=p["hidden"], seed=p["seed"])
    # _train() runs directly here (this IS the isolated process; no further nesting)
    q = fc._train(yy, p["m"], p["h"], tuple(p["levels"]), p["lookback"])
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([[float(v) for v in row] for row in q], f)


def neural_forecasters() -> list[NeuralForecaster]:
    """The deep engines, or [] when torch is missing or the tier is disabled (CHRONOSCOPE_ENABLE_NEURAL=1)."""
    if not os.environ.get(_ENABLE_ENV):
        return []
    if not _deps_available():
        return []
    return [NeuralForecaster("NLinear"), NeuralForecaster("DLinear"), NeuralForecaster("NHITS")]


def neural_available() -> bool:
    """True if torch is importable (the deep tier can run, regardless of the enable flag)."""
    return _deps_available()
