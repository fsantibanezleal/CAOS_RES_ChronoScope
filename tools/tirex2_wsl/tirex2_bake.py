"""TiRex-2 WSL2-lane baker: run TiRex-2 (NX-AI xLSTM foundation model) for one case and emit the same
backtest block + display forecast the Windows pipeline produces for every other method.

TiRex-2's `flashrnn` dependency needs `triton` + fused CUDA kernels compiled by nvcc, which have no Windows
wheels; so TiRex-2 runs here, in a WSL2 (Linux) venv with CUDA-in-WSL, and the Windows bake merges the
result as the 19th ("foundation") method. This script LOADS THE MODEL ONCE and does the whole case
in-process, so the Windows side makes ONE WSL call per case (not one per backtest window).

It reuses the EXACT metric machinery of the Windows evaluate stage: a `preqts.ReplayAdapter` wrapping the
TiRex-2 forecast + `preqts.run_prequential`, with the same warmup/step/max_windows formula as
`stages/evaluate.py`, so TiRex-2's MASE/WQL/coverage/MSIS/per-horizon are computed identically to the rest
of the ladder. Read `in.json`, write `out.json`.

Usage (in the WSL venv):  python tirex2_bake.py in.json out.json
in.json  = {"case_id","y":[...],"seasonality","horizon","quantile_levels":[...],"max_windows":2}
out.json = {"name":"TiRex-2","family":"foundation","point":[...],"lower":[...],"upper":[...],
            "backtest":{mase,wql,coverage,mae,rmse,smape,msis,per_horizon_scaled,n_windows}}
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import torch

_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        tok_path = "/root/.hf_token"
        if os.path.exists(tok_path):
            os.environ.setdefault("HF_TOKEN", open(tok_path).read().strip())
        os.environ.setdefault("CUDA_HOME", "/usr")
        from tirex2 import load_model
        _MODEL = load_model("NX-AI/TiRex-2", device="cuda")
    return _MODEL


def _decile_index(level: float) -> int:
    # TiRex-2 emits the 9 deciles q0.1..q0.9 at indices 0..8; map a requested level to the nearest decile.
    return int(min(8, max(0, round(level * 10) - 1)))


def _forecast(context: np.ndarray, horizon: int, levels) -> np.ndarray:
    """(horizon, len(levels)) quantile forecast from TiRex-2 for a 1-D context."""
    from tirex2 import TimeseriesType
    ts = TimeseriesType(torch.tensor(np.asarray(context, dtype=np.float32)), None, None)
    out = _model().forecast(timeseries=[ts], prediction_length=horizon, output_type="numpy")
    arr = np.asarray(out[0] if isinstance(out, (list, tuple)) else out)  # (9, horizon) or (1,9,horizon)
    if arr.ndim == 3:
        arr = arr[0]
    idx = [_decile_index(q) for q in levels]
    return arr[idx, :].T  # (horizon, len(levels))


def _batch_fn(horizon_default):
    def batch(context, horizon, past_cov, future_cov, levels):
        return _forecast(np.asarray(context, dtype=float), horizon, list(levels))
    return batch


def run(spec: dict) -> dict:
    from preqts import ReplayAdapter, Stream, run_prequential

    y = np.asarray(spec["y"], dtype=float)
    m = int(spec["seasonality"])
    h = int(spec["horizon"])
    levels = list(spec.get("quantile_levels", [0.1, 0.5, 0.9]))
    max_windows = int(spec.get("max_windows", 2))

    # mirror stages/evaluate.py exactly
    train_end = max(2 * m + h, len(y) - h)
    hist = y[:train_end]
    warmup = min(max(2 * m, 2 * h + 20, 10), max(1, len(hist) - h - 1))
    usable = len(hist) - warmup - h
    step = max(1, usable // max(1, max_windows))

    stream = Stream(hist, seasonality=m, name=spec["case_id"])
    adapter = ReplayAdapter(_batch_fn(h), name="TiRex-2")
    res = run_prequential(adapter, stream, horizon=h, quantile_levels=levels, step=step, warmup=warmup)
    s = res.summary()
    ph = res.per_horizon()

    def num(x):
        x = float(x)
        return round(x, 5) if x == x else None

    backtest = {
        "mase": num(s["mase"]), "wql": num(s["wql"]), "coverage": num(s["coverage"]),
        "mae": num(s["mae"]), "rmse": num(s["rmse"]), "smape": num(s["smape"]), "msis": num(s["msis"]),
        "per_horizon_scaled": [num(v) for v in ph["scaled"]], "n_windows": int(res.n_windows),
    }

    # display forecast: TiRex-2 on the full observed history (what the trace draws over the holdout)
    disp = _forecast(y[: max(2 * m + h, len(y) - h)], h, levels)
    lo_i, mid_i, hi_i = 0, len(levels) // 2, len(levels) - 1
    return {
        "name": "TiRex-2", "family": "foundation",
        "point": [round(float(v), 4) for v in disp[:, mid_i]],
        "lower": [round(float(v), 4) for v in disp[:, lo_i]],
        "upper": [round(float(v), 4) for v in disp[:, hi_i]],
        "backtest": backtest,
    }


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = run(spec)
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"))
    print("TiRex-2 baked:", spec["case_id"], "mase=", out["backtest"]["mase"], "n_windows=", out["backtest"]["n_windows"])
