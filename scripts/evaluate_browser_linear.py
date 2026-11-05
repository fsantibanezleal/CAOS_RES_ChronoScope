"""Execute the prospectively recorded synthetic browser-linear protocol.

Optional dependencies: requirements-browser-model.txt. Never writes to the
canonical model or data tree; --output must name an empty external directory.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import platform
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
LOOKBACK, HORIZON, ALPHA = 48, 12, .2
GRID = (0., .000001, .0001, .01, .1, 1., 10.)
SPLITS = {"training": (400, 20260704), "validation": (200, 20261105),
          "calibration": (400, 20261106), "test": (400, 20261107)}
FROZEN_SHA = "621265165211f756cff537adee364b9790c34ced567bc2a5087513360e1f69f6"


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_window(history: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, float]:
    history, target = np.asarray(history, dtype=float), np.asarray(target, dtype=float)
    if history.shape != (LOOKBACK,) or target.shape != (HORIZON,):
        raise ValueError("Unsupported lookback or horizon")
    if not np.isfinite(history).all() or not np.isfinite(target).all():
        raise ValueError("Nonfinite observations")
    scale, last = float(np.std(history)), float(history[-1])
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("Unavailable lookback scale")
    return (history - last) / scale, (target - last) / scale, scale, last


def fit_ridge(x: np.ndarray, y: np.ndarray, penalty: float) -> np.ndarray:
    if (x.ndim != 2 or x.shape[1] != LOOKBACK or y.shape != (len(x), HORIZON)
            or not len(x) or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not math.isfinite(penalty) or penalty < 0):
        raise ValueError("Invalid ridge training inputs")
    if penalty == 0:
        weights = np.linalg.lstsq(x, y, rcond=None)[0]
    else:
        weights = np.linalg.solve(x.T @ x / len(x) + penalty * np.eye(LOOKBACK), x.T @ y / len(x))
    return weights.astype(np.float32)


def select_weights(x: np.ndarray, y: np.ndarray, vx: np.ndarray, vy: np.ndarray) -> tuple[np.ndarray, list[dict]]:
    rows, candidates = [], []
    for penalty in GRID:
        weights = fit_ridge(x, y, penalty)
        # Both inputs and weights have the browser tensor precision.
        loss = float(np.mean((vy - vx.astype(np.float32) @ weights) ** 2))
        rows.append({"penalty": penalty, "normalized_mse": loss})
        candidates.append(weights)
    index = int(np.argmin([row["normalized_mse"] for row in rows]))
    rows[index]["selected"] = True
    return candidates[index], rows


def calibration_radii(residual: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    residual = np.asarray(residual, dtype=float)
    if (residual.ndim != 2 or residual.shape[1] != HORIZON or not len(residual)
            or not np.isfinite(residual).all() or not 0 < alpha < 1):
        raise ValueError("Invalid calibration residuals")
    order = math.ceil((len(residual) + 1) * (1 - alpha))
    if order > len(residual):
        raise ValueError("Too few calibration series for a finite radius")
    return np.sort(np.abs(residual), axis=0)[order - 1]


def losses(target: np.ndarray, point: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> dict[str, np.ndarray]:
    arrays = [np.asarray(a, dtype=float) for a in (target, point, lower, upper)]
    target, point, lower, upper = arrays
    if (target.ndim != 2 or target.shape[1] != HORIZON or not len(target)
            or any(a.shape != target.shape or not np.isfinite(a).all() for a in arrays)
            or np.any(lower > upper)):
        raise ValueError("Invalid scoring arrays")
    error = target - point
    return {"normalized_mse": np.mean(error ** 2, axis=1),
            "normalized_mae": np.mean(np.abs(error), axis=1),
            "coverage": np.mean((target >= lower) & (target <= upper), axis=1),
            "normalized_width": np.mean(upper - lower, axis=1),
            "normalized_interval_score": np.mean(upper - lower + 2 / ALPHA * (
                np.maximum(lower - target, 0) + np.maximum(target - upper, 0)), axis=1)}


def paired_summary(difference: np.ndarray) -> dict:
    difference = np.asarray(difference, dtype=float)
    if difference.ndim != 1 or not len(difference) or not np.isfinite(difference).all():
        raise ValueError("Invalid paired losses")
    rng = np.random.default_rng(20261108)
    boot = np.empty(10000)
    for start in range(0, len(boot), 100):
        indices = rng.integers(0, len(difference), size=(100, len(difference)))
        boot[start:start + 100] = np.mean(difference[indices], axis=1)
    return {"mean_difference": float(np.mean(difference)),
            "percentile_95": np.quantile(boot, [.025, .975]).tolist(),
            "strictly_lower_loss_series": int(np.sum(difference < 0)), "series": len(difference)}


def generate_splits() -> dict[str, list[dict]]:
    # Keep the original draw sequence and training distribution unchanged.
    from train_nlinear_onnx import _series

    result, seen = {}, set()
    for split, (count, seed) in SPLITS.items():
        rng, records = np.random.default_rng(seed), []
        for index in range(count):
            family = str(rng.choice(["seasonal", "trend_seasonal", "trend", "noise"]))
            values = _series(rng, family, n=rng.integers(120, 260)).tolist()
            series_hash = hashlib.sha256(json_bytes(values)).hexdigest()
            if series_hash in seen:
                raise ValueError("Series overlap between partitions")
            seen.add(series_hash)
            records.append({"id": f"{split}-{index:04d}", "family": family,
                            "sha256": series_hash, "values": values})
        result[split] = records
    return result


def final_windows(records: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    values = [np.asarray(record["values"][-LOOKBACK - HORIZON:]) for record in records]
    normalized = [normalize_window(y[:LOOKBACK], y[LOOKBACK:]) for y in values]
    x, y, scale, last = zip(*normalized)
    return np.asarray(x), np.asarray(y), np.asarray(scale), np.asarray(last)


def export_model(weights: np.ndarray, path: Path) -> None:
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    graph = helper.make_graph([helper.make_node("MatMul", ["x", "W"], ["y"])], "normalized_ridge",
                              [helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, LOOKBACK])],
                              [helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, HORIZON])],
                              [numpy_helper.from_array(weights, name="W")])
    model = helper.make_model(graph, opset_imports=[helper.make_operatorsetid("", 13)],
                              producer_name="chronoscope-held-out-linear")
    model.ir_version = 9
    onnx.checker.check_model(model)
    onnx.save(model, path)


def runtime_predictions(path: Path, x: np.ndarray) -> np.ndarray:
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(path), sess_options=options, providers=["CPUExecutionProvider"])
    return np.vstack([session.run(["y"], {"x": row[None].astype(np.float32)})[0] for row in x])


def run(output: Path) -> dict:
    import onnx
    from onnx import numpy_helper

    output = output.resolve()
    if output == ROOT or ROOT in output.parents or (output.exists() and any(output.iterdir())):
        raise ValueError("Output must be an empty directory outside the source checkout")
    frozen = ROOT / "frontend/public/models/nlinear.onnx"
    metadata = ROOT / "frontend/src/lib/nlinearMeta.json"
    if digest(frozen) != FROZEN_SHA:
        raise ValueError("Frozen comparator changed")
    meta = json.loads(metadata.read_text())
    if (meta["lookback"], meta["horizon"]) != (LOOKBACK, HORIZON):
        raise ValueError("Frozen comparator dimensions changed")
    output.mkdir(parents=True, exist_ok=True)
    partitions = generate_splits()
    x_rows, y_rows = [], []
    for record in partitions["training"]:
        values = np.asarray(record["values"])
        for start in range(len(values) - LOOKBACK - HORIZON + 1):
            x, y, _, _ = normalize_window(values[start:start + LOOKBACK],
                                           values[start + LOOKBACK:start + LOOKBACK + HORIZON])
            x_rows.append(x)
            y_rows.append(y)
    train_x, train_y = np.asarray(x_rows), np.asarray(y_rows)
    vx, vy, _, _ = final_windows(partitions["validation"])
    weights, selection = select_weights(train_x, train_y, vx, vy)
    export_model(weights, output / "normalized-ridge.onnx")
    cx, cy, _, _ = final_windows(partitions["calibration"])
    radii = calibration_radii(cy - runtime_predictions(output / "normalized-ridge.onnx", cx))
    # The test split is not consulted by either fit, selection or calibration.
    tx, ty, scales, lasts = final_windows(partitions["test"])
    point = runtime_predictions(output / "normalized-ridge.onnx", tx)
    old_point = runtime_predictions(frozen, tx)
    frozen_weights = next(numpy_helper.to_array(w) for w in onnx.load(frozen).graph.initializer if w.name == "W")
    parity = max(float(np.max(np.abs(point - tx.astype(np.float32) @ weights))),
                 float(np.max(np.abs(old_point - tx.astype(np.float32) @ frozen_weights))))
    if parity >= .0001:
        raise ValueError(f"ONNX numerical parity failed: {parity}")
    old_radius = 1.2815515655446004 * float(meta["sigma_norm"]) * np.sqrt(np.arange(1, HORIZON + 1))
    methods = {"held_out_ridge": (point, point - radii, point + radii),
               "frozen_browser_linear": (old_point, old_point - old_radius, old_point + old_radius)}
    metrics = {name: losses(ty, *forecast) for name, forecast in methods.items()}
    groups = {"all": np.ones(len(tx), dtype=bool), **{
        family: np.asarray([r["family"] == family for r in partitions["test"]])
        for family in ("seasonal", "trend_seasonal", "trend", "noise")}}
    scores = {group: {name: {metric: float(np.mean(values[mask])) for metric, values in result.items()}
                      for name, result in metrics.items()} for group, mask in groups.items()}
    for group, mask in groups.items():
        scores[group]["repeat_last"] = {"normalized_mse": float(np.mean(ty[mask] ** 2)),
                                        "normalized_mae": float(np.mean(np.abs(ty[mask])))}
    paired = {metric: paired_summary(metrics["held_out_ridge"][metric] - metrics["frozen_browser_linear"][metric])
              for metric in ("normalized_mse", "normalized_interval_score")}
    forecasts = []
    for i, record in enumerate(partitions["test"]):
        forecasts.append({"id": record["id"], "family": record["family"], "scale": float(scales[i]),
                          "actual": record["values"][-HORIZON:], "methods": {
                              name: {key: (array[i] * scales[i] + lasts[i]).tolist()
                                     for key, array in zip(("point", "lower", "upper"), forecast)}
                              for name, forecast in methods.items()}})
    (output / "series.json.gz").write_bytes(gzip.compress(json_bytes(partitions), mtime=0))
    (output / "forecasts.json.gz").write_bytes(gzip.compress(json_bytes(forecasts), mtime=0))
    (output / "model.json").write_bytes(json_bytes({"name": "Held-out normalized ridge", "lookback": LOOKBACK,
        "horizon": HORIZON, "alpha": ALPHA, "normalization": "subtract_last_then_divide_population_std",
        "absolute_residual_radii": radii.tolist(), "selection": selection}))
    sources = {p: digest(ROOT / p) for p in ("docs/guides/browser-linear-protocol.md",
        "scripts/evaluate_browser_linear.py", "scripts/train_nlinear_onnx.py", "requirements-browser-model.txt",
        "frontend/public/models/nlinear.onnx", "frontend/src/lib/nlinearMeta.json")}
    result = {"schema": "chronoscope.browser-linear-evaluation/v1", "population": "synthetic generator only",
              "protocol_version": 1, "splits": {k: {"series": n, "seed": seed} for k, (n, seed) in SPLITS.items()},
              "training_windows": len(train_x), "selection": selection, "scores": scores,
              "paired_exploratory": paired, "per_lead_coverage": {name: np.mean(
                  (ty >= forecast[1]) & (ty <= forecast[2]), axis=0).tolist() for name, forecast in methods.items()},
              "max_normalized_runtime_error": parity, "sources": sources,
              "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                          **{name: importlib.metadata.version(name) for name in ("numpy", "onnx", "onnxruntime")}},
              "artifacts": {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "results.json").write_bytes(json_bytes(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"selection": result["selection"], "scores": result["scores"]["all"],
                      "paired": result["paired_exploratory"], "max_runtime_error": result["max_normalized_runtime_error"]}, indent=2))
