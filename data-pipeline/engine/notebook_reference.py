"""History-only reference fits for the forecasting comparison lesson.

Windows delegates to the declared Linux runtime because TiRex-2 requires its
native CUDA kernels. No cached prediction or unavailable-engine fallback exists.
Checkpoint and package identities come from the retained common-holdout protocol;
new predictions are computed from the caller's history without evaluation truth.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
_CURRENT_METHOD = "runtime"
METHODS = ("NLinear", "DLinear", "NHITS", "Chronos-Bolt", "Chronos-2", "TimesFM-2.5", "TiRex-2")
PROVIDERS = {**dict.fromkeys(METHODS[:3], "neuralforecast"),
             **dict.fromkeys(METHODS[3:5], "chronos-forecasting"),
             "TimesFM-2.5": "timesfm", "TiRex-2": "tirex-2"}
CHECKPOINTS = dict(zip(METHODS[3:], ("amazon/chronos-bolt-small", "amazon/chronos-2",
                                    "google/timesfm-2.5-200m-pytorch", "NX-AI/TiRex-2"), strict=True))


def _request(history, seasonality, horizon, methods):
    history = [float(value) for value in history]
    if len(history) < 80 or not all(math.isfinite(value) for value in history):
        raise ValueError("Reference inference requires at least 80 finite observed values")
    if not isinstance(horizon, int) or isinstance(horizon, bool) or not 1 <= horizon <= 64:
        raise ValueError("Reference horizon must be an integer from 1 through 64")
    if not isinstance(seasonality, int) or isinstance(seasonality, bool) or not 1 <= seasonality <= len(history) // 2:
        raise ValueError("Reference seasonality must be a positive observed-cycle length")
    methods = list(METHODS if methods is None else methods)
    if not methods or len(methods) != len(set(methods)) or any(name not in METHODS for name in methods):
        raise ValueError("Unknown, empty or duplicate reference methods")
    return {"history": history, "seasonality": seasonality, "horizon": horizon, "methods": methods}


def _digest(request):
    return hashlib.sha256(json.dumps(request, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _wsl_path(path):
    value = str(path).replace("\\", "/")
    if len(value) > 2 and value[1] == ":":
        return "/mnt/" + value[0].lower() + value[2:]
    return value


def reference_forecasts(history, seasonality, horizon, methods=None):
    """Fit/infer the named references on one shared prefix, returning H x 3 paths.

    CAOS_TEMP_ROOT is required on Windows. The configured WSL interpreter must
    contain the exact retained protocol pins and the four local checkpoints.
    The result contains no wall-clock measurements or volatile machine paths.
    """
    request = _request(history, seasonality, horizon, methods)
    if os.name != "nt":
        return _native(request)
    temporary = os.environ.get("CAOS_TEMP_ROOT", "")
    if not temporary or not Path(temporary).is_absolute():
        raise ValueError("Configure an absolute external CAOS_TEMP_ROOT for reference inference")
    temporary = Path(temporary).resolve()
    if temporary.is_relative_to(ROOT):
        raise ValueError("Reference temporary files must be outside the product checkout")
    temporary.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chronoscope-reference-", dir=temporary) as folder:
        source, output = Path(folder) / "input.json", Path(folder) / "output.json"
        source.write_text(json.dumps(request, allow_nan=False), encoding="utf-8")
        interpreter = os.environ.get("CHRONOSCOPE_REFERENCE_PYTHON", "")
        if not interpreter.startswith("/"):
            raise ValueError("Configure CHRONOSCOPE_REFERENCE_PYTHON as the pinned Linux interpreter's absolute path")
        distribution = os.environ.get("CHRONOSCOPE_REFERENCE_DISTRO", "Ubuntu-24.04")
        cache = os.environ.get("CHRONOSCOPE_REFERENCE_CACHE", "")
        command = ["wsl.exe", "-d", distribution, "-u", "root", "--cd", "/root", "--", "env", "CUDA_HOME=/usr",
                   f"PATH={interpreter.rsplit('/', 1)[0]}:/usr/bin:/bin",
                   "TORCH_EXTENSIONS_DIR=/root/.cache/torch_extensions", "TORCHINDUCTOR_COMPILE_THREADS=1",
                   "HF_HUB_OFFLINE=1", "TRANSFORMERS_OFFLINE=1", f"CHRONOSCOPE_REFERENCE_CACHE={cache}",
                   interpreter, _wsl_path(__file__),
                   "--input", _wsl_path(source), "--output", _wsl_path(output)]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=1800)
        if run.returncode:
            # Model loaders can include authentication details in their errors;
            # expose the diagnostic class rather than forwarding their output.
            error = json.loads(output.read_text(encoding="utf-8")) if output.is_file() else {}
            detail = error.get("error_type", "runtime startup") + ": " + error.get("reference_error", "")
            raise RuntimeError(f"Pinned reference runtime failed (exit {run.returncode}, {detail}); no result substituted")
        result = json.loads(output.read_text(encoding="utf-8"))
    _validate_result(request, result)
    return result


def _validate_result(request, result):
    if result["input_sha256"] != _digest(request) or set(result["methods"]) != set(request["methods"]):
        raise ValueError("Reference result belongs to another prefix or method set")
    for record in result["methods"].values():
        values = record["quantiles"]
        if len(values) != request["horizon"] or any(
                len(row) != 3 or not all(math.isfinite(v) for v in row) or row != sorted(row) for row in values):
            raise ValueError("Invalid reference quantile paths")


def _native(request):
    global _CURRENT_METHOD
    import numpy as np
    import torch
    from huggingface_hub import snapshot_download

    sys.path.insert(0, str(ROOT / "data-pipeline"))
    protocol = json.loads((ROOT / "data/derived/fresh-reevaluation.json").read_text(encoding="utf-8"))["runtime"]
    packages = {PROVIDERS[name] for name in request["methods"]} | {"torch"}
    versions = {name: importlib.metadata.version(name) for name in sorted(packages)}
    for name, version in versions.items():
        if version != protocol["packages"][name]:
            raise ValueError(f"Reference package pin differs: {name}")
    torch.set_num_threads(4)
    torch.manual_seed(42)
    paths, hashes = {}, {}
    for name in request["methods"]:
        if name not in CHECKPOINTS:
            continue
        repository = CHECKPOINTS[name]
        _CURRENT_METHOD = "checkpoint " + name
        revision = protocol["checkpoint_revisions"][repository]
        cache = os.environ.get("CHRONOSCOPE_REFERENCE_CACHE") if name != "TiRex-2" else None
        path = Path(snapshot_download(repository, revision=revision, cache_dir=cache, local_files_only=True))
        actual = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(path.iterdir())
                  if p.suffix in (".json", ".safetensors")}
        for filename, expected in protocol["checkpoint_sha256"].get(repository, {}).items():
            if actual.get(filename) != expected:
                raise ValueError(f"Reference checkpoint bytes differ: {repository}/{filename}")
        paths[name], hashes[repository] = path, actual
    levels = (0.1, 0.5, 0.9)
    history = np.asarray(request["history"], dtype=float)
    seasonality, horizon = request["seasonality"], request["horizon"]
    result = {"input_sha256": _digest(request), "methods": {}, "runtime": {
        "platform": platform.system(), "packages": versions, "seed": 42,
        "checkpoint_revisions": {CHECKPOINTS[name]: protocol["checkpoint_revisions"][CHECKPOINTS[name]]
                                 for name in request["methods"] if name in CHECKPOINTS},
        "checkpoint_sha256": hashes}}
    for name in request["methods"]:
        _CURRENT_METHOD = name
        if name in METHODS[:3]:
            from engine.engines.neuralforecast_engine import NeuralForecastForecaster
            model = NeuralForecastForecaster(name, max_steps=300, seed=42)
            quantiles = model.quantiles(history, seasonality, horizon, levels)
        elif name in METHODS[3:5]:
            from engine.engines.chronos_engine import ChronosForecaster
            model = ChronosForecaster(name, str(paths[name]))
            quantiles = model.quantiles(history, seasonality, horizon, levels)
        elif name == "TimesFM-2.5":
            from engine.engines.timesfm_engine import _load_model
            model = _load_model(str(paths[name]))
            _, distribution = model.forecast(horizon=horizon, inputs=[history[-512:]])
            quantiles = np.asarray(distribution, dtype=float)[0][:, [1, 5, 9]]
            quantiles = np.maximum.accumulate(quantiles, axis=1)
        else:
            from engine.engines.tirex2_engine import Tirex2Forecaster
            os.environ["CHRONOSCOPE_TIREX_REVISION"] = protocol["checkpoint_revisions"][CHECKPOINTS[name]]
            model = Tirex2Forecaster()
            quantiles = model.quantiles(history, seasonality, horizon, levels)
        record = {"quantiles": np.asarray(quantiles, dtype=float).tolist(),
                  "package": PROVIDERS[name], "package_version": versions[PROVIDERS[name]],
                  "postprocessing": "quantile rearrangement; no forecast clipping"}
        if name in CHECKPOINTS:
            record["checkpoint_revision"] = protocol["checkpoint_revisions"][CHECKPOINTS[name]]
        result["methods"][name] = record
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    _validate_result(request, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if set(payload) != {"history", "seasonality", "horizon", "methods"}:
        raise ValueError("Only history, seasonality, horizon and methods may cross the inference boundary")
    request = _request(**payload)
    previous = Path.cwd()
    try:
        with tempfile.TemporaryDirectory(prefix="fit-", dir=args.input.parent) as working:
            try:
                os.chdir(working)
                result = _native(request)
            finally:
                os.chdir(previous)
    except Exception as error:
        detail = str(error)
        for name, value in os.environ.items():
            if value and len(value) > 6 and any(word in name.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "API_KEY")):
                detail = detail.replace(value, "[redacted]")
        detail = re.sub(r"\bhf_[A-Za-z0-9]+|Bearer\s+\S+", "[redacted]", detail)
        detail = (_CURRENT_METHOD + ": " + detail)[:1200]
        args.output.write_text(json.dumps({"error_type": type(error).__name__, "reference_error": detail}), encoding="utf-8")
        raise SystemExit(1) from None
    args.output.write_text(json.dumps(result, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
