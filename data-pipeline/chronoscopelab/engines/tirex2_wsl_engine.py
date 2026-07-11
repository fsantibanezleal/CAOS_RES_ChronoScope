"""TiRex-2 via the WSL2 lane (the Windows side of a cross-OS foundation method).

TiRex-2 (NX-AI, xLSTM) cannot run on native Windows: its ``flashrnn`` dependency needs ``triton`` + fused
CUDA kernels compiled by nvcc, and neither ships Windows wheels. So TiRex-2 runs in a WSL2 (Linux) venv with
CUDA-in-WSL, and this engine is the bridge: for one case it writes the SeriesSpec to a temp JSON, invokes
``tools/tirex2_wsl/tirex2_bake.py`` inside WSL (which loads the model once and produces the same backtest
block + display forecast as every other method), and reads the result back to merge as the 19th method.

OPT-IN and graceful: enabled only with ``CHRONOSCOPE_ENABLE_TIREX_WSL=1`` and only when the WSL distro +
venv are reachable. When off or unavailable it returns None, so CI and the default bake are unaffected and
the committed artifact stays valid. This mirrors the other heavy-tier env gates (CHRONOSCOPE_ENABLE_*).

Setup (once, in the distro): a WSL2 Ubuntu with the NVIDIA Windows driver (CUDA-in-WSL), a venv at
``/root/tirex-venv`` with torch(cuda) + tirex-2 + flashrnn + preqts + the CUDA toolkit (nvcc), and the
gated HF token at ``/root/.hf_token``. See ``docs/guides/tirex2-wsl-lane.md``.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from ..io.schema import ForecastResult, MethodForecast, SeriesSpec

_ENABLE_ENV = "CHRONOSCOPE_ENABLE_TIREX_WSL"
_DISTRO = os.environ.get("CHRONOSCOPE_TIREX_WSL_DISTRO", "Ubuntu-24.04")
_WSL_PYTHON = os.environ.get("CHRONOSCOPE_TIREX_WSL_PYTHON", "/root/tirex-venv/bin/python")
_MAX_WINDOWS = 2  # the foundation-tier backtest-window budget (matches chronos/timesfm)

# repo root -> the WSL path of the baker (D:\...  ->  /mnt/d/...)
_REPO = Path(__file__).resolve().parents[3]


def _to_wsl_path(win_path: str) -> str:
    p = str(win_path).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        return "/mnt/" + p[0].lower() + p[2:]
    return p


def _baker_wsl_path() -> str:
    return _to_wsl_path(str(_REPO / "tools" / "tirex2_wsl" / "tirex2_bake.py"))


def tirex2_enabled() -> bool:
    return os.environ.get(_ENABLE_ENV, "") == "1"


def tirex2_available() -> bool:
    """Enabled AND the WSL distro + venv python are reachable (a cheap probe; never raises)."""
    if not tirex2_enabled():
        return False
    try:
        # a probe with no shell metacharacters (parens get mangled through wsl.exe arg parsing)
        r = subprocess.run(["wsl.exe", "-d", _DISTRO, "-u", "root", "--", _WSL_PYTHON, "--version"],
                           capture_output=True, timeout=60, text=True)
        return r.returncode == 0 and "Python" in (r.stdout + r.stderr)
    except Exception:  # noqa: BLE001 - a missing distro/venv just means the lane is unavailable
        return False


def bake_tirex2(spec: SeriesSpec, quantile_levels: tuple[float, ...]) -> dict | None:
    """Run TiRex-2 in WSL for one case; return the method dict (name/family/point/lower/upper/backtest) or
    None if the lane is unavailable or the WSL run fails (graceful: the bake proceeds without TiRex-2)."""
    if not tirex2_available():
        return None
    payload = {
        "case_id": spec.case_id, "y": [float(v) for v in spec.y], "seasonality": int(spec.seasonality),
        "horizon": int(spec.horizon), "quantile_levels": list(quantile_levels), "max_windows": _MAX_WINDOWS,
    }
    with tempfile.TemporaryDirectory() as td:
        in_path = Path(td) / "in.json"
        out_path = Path(td) / "out.json"
        in_path.write_text(json.dumps(payload), encoding="utf-8")
        # set CUDA_HOME (nvcc) + a PATH that includes the venv bin (ninja lives there; torch's JIT extension
        # loader needs it) and /usr/bin (nvcc); a stable TORCH_EXTENSIONS_DIR so the compiled sLSTM kernel is
        # cached across bakes instead of rebuilt each call.
        venv_bin = _WSL_PYTHON.rsplit("/", 1)[0]
        cmd = ["wsl.exe", "-d", _DISTRO, "-u", "root", "--", "env", "CUDA_HOME=/usr",
               f"PATH=/usr/bin:/bin:{venv_bin}", "TORCH_EXTENSIONS_DIR=/root/.cache/torch_extensions",
               _WSL_PYTHON, _baker_wsl_path(), _to_wsl_path(str(in_path)), _to_wsl_path(str(out_path))]
        try:
            subprocess.run(cmd, capture_output=True, timeout=1800, text=True, check=True)
            return json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - never crash the bake on a WSL hiccup
            return None


def merge_into(result: ForecastResult, eval_metrics: dict, spec: SeriesSpec,
               quantile_levels: tuple[float, ...]) -> tuple[ForecastResult, dict]:
    """Merge the TiRex-2 method into an existing ForecastResult + evaluate metrics (as the foundation-tier
    19th method), if the WSL lane produced a result. Idempotent-safe and graceful."""
    baked = bake_tirex2(spec, quantile_levels)
    if baked is None:
        return result, eval_metrics
    mf = MethodForecast(
        name=baked["name"], family=baked["family"],
        point=tuple(baked["point"]), lower=tuple(baked["lower"]), upper=tuple(baked["upper"]),
    )
    result = ForecastResult(
        case_id=result.case_id, horizon=result.horizon, seasonality=result.seasonality,
        quantile_levels=result.quantile_levels, history=result.history,
        methods=result.methods + (mf,), covariates=result.covariates,
    )
    methods = dict(eval_metrics.get("methods", {}))
    methods[baked["name"]] = baked["backtest"]
    eval_metrics = {**eval_metrics, "methods": methods}
    # keep best_method / best_mase honest across the enlarged roster
    scored = [(n, v.get("mase")) for n, v in methods.items() if isinstance(v.get("mase"), (int, float))]
    if scored:
        best_name, best_mase = min(scored, key=lambda kv: kv[1])
        eval_metrics["best_method"], eval_metrics["best_mase"] = best_name, round(float(best_mase), 5)
    return result, eval_metrics
