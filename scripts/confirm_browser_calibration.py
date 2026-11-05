"""Confirm prefix-stratified intervals around the frozen browser point model."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import numpy as np

from evaluate_browser_linear import (
    ALPHA, FROZEN_SHA, HORIZON, LOOKBACK, ROOT, calibration_radii, digest,
    final_windows, json_bytes, losses, paired_summary, runtime_predictions,
)

BINS = (.5, 1.25)
SPLITS = {"calibration": (400, 20261109), "test": (800, 20261110)}
PRIOR = ROOT / "docs/research/browser-linear/v1/results.json"


def roughness_bin(x: np.ndarray) -> np.ndarray:
    """x is normalized using the observed window's finite positive scale."""
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] != LOOKBACK or not np.isfinite(x).all():
        raise ValueError("Invalid normalized prefix")
    variance = np.var(x, axis=1)
    if np.any(variance <= 0):
        raise ValueError("Unavailable prefix variance")
    roughness = np.mean(np.diff(x, axis=1) ** 2, axis=1) / variance
    return np.searchsorted(BINS, roughness, side="right")


def group_radii(x: np.ndarray, residual: np.ndarray) -> tuple[np.ndarray, list[int]]:
    groups = roughness_bin(x)
    if residual.shape != (len(x), HORIZON):
        raise ValueError("Calibration alignment differs")
    counts = [int(np.sum(groups == group)) for group in range(3)]
    if min(counts) < 20:
        raise ValueError("A roughness bin has fewer than 20 independent calibration series")
    return np.asarray([calibration_radii(residual[groups == group]) for group in range(3)]), counts


def generate_confirmation() -> dict[str, list[dict]]:
    from train_nlinear_onnx import _series

    prior_series = json.loads(gzip.decompress((PRIOR.parent / "series.json.gz").read_bytes()))
    seen = {r["sha256"] for records in prior_series.values() for r in records}
    result = {}
    for split, (count, seed) in SPLITS.items():
        rng, records = np.random.default_rng(seed), []
        for index in range(count):
            family = str(rng.choice(["seasonal", "trend_seasonal", "trend", "noise"]))
            values = _series(rng, family, n=rng.integers(120, 260)).tolist()
            series_hash = hashlib.sha256(json_bytes(values)).hexdigest()
            if series_hash in seen:
                raise ValueError("Confirmation overlaps an earlier partition")
            seen.add(series_hash)
            records.append({"id": f"confirmation-{split}-{index:04d}", "family": family,
                            "sha256": series_hash, "values": values})
        result[split] = records
    return result


def admission(scores: dict, counts: list[int], parity: float, points_identical: bool) -> dict[str, bool]:
    overall = scores["all"]
    return {
        "points_identical": points_identical,
        "minimum_calibration_count": min(counts) >= 20,
        "lower_interval_score": overall["stratified"]["normalized_interval_score"] < overall["gaussian"]["normalized_interval_score"],
        "overall_coverage": .75 <= overall["stratified"]["coverage"] <= .85,
        "bin_coverage": all(.70 <= scores[f"prefix_bin_{g}"]["stratified"]["coverage"] <= .90 for g in range(3)),
        "runtime_parity": parity < .0001,
    }


def run(output: Path) -> dict:
    import onnx
    from onnx import numpy_helper

    output = output.resolve()
    if output == ROOT or ROOT in output.parents or (output.exists() and any(output.iterdir())):
        raise ValueError("Output must be an empty external directory")
    frozen = ROOT / "frontend/public/models/nlinear.onnx"
    if digest(frozen) != FROZEN_SHA:
        raise ValueError("Frozen point model changed")
    output.mkdir(parents=True, exist_ok=True)
    records = generate_confirmation()
    cx, cy, _, _ = final_windows(records["calibration"])
    calibration_point = runtime_predictions(frozen, cx)
    residual = cy - calibration_point
    radii, counts = group_radii(cx, residual)
    global_radius = calibration_radii(residual)
    tx, ty, scales, lasts = final_windows(records["test"])
    point = runtime_predictions(frozen, tx)
    weights = next(numpy_helper.to_array(w) for w in onnx.load(frozen).graph.initializer if w.name == "W")
    parity = float(np.max(np.abs(point - tx.astype(np.float32) @ weights)))
    if parity >= .0001:
        raise ValueError(f"ONNX parity failed: {parity}")
    test_bins = roughness_bin(tx)
    sigma = float(json.loads((ROOT / "frontend/src/lib/nlinearMeta.json").read_text())["sigma_norm"])
    gaussian_radius = 1.2815515655446004 * sigma * np.sqrt(np.arange(1, HORIZON + 1))
    methods = {"gaussian": (point, point - gaussian_radius, point + gaussian_radius),
               "global": (point, point - global_radius, point + global_radius),
               "stratified": (point, point - radii[test_bins], point + radii[test_bins])}
    metrics = {name: losses(ty, *values) for name, values in methods.items()}
    groups = {"all": np.ones(len(tx), dtype=bool),
              **{f"prefix_bin_{g}": test_bins == g for g in range(3)}, **{
                  f"family_{family}": np.asarray([r["family"] == family for r in records["test"]])
                  for family in ("seasonal", "trend_seasonal", "trend", "noise")}}
    scores = {group: {name: {metric: float(np.mean(values[mask])) for metric, values in result.items()}
                      for name, result in metrics.items()} for group, mask in groups.items()}
    paired = {control: paired_summary(metrics["stratified"]["normalized_interval_score"] -
                                      metrics[control]["normalized_interval_score"])
              for control in ("gaussian", "global")}
    forecasts = [{"id": r["id"], "family": r["family"], "prefix_bin": int(test_bins[i]),
                  "actual": r["values"][-HORIZON:], "scale": float(scales[i]),
                  "methods": {name: {key: (array[i] * scales[i] + lasts[i]).tolist()
                                    for key, array in zip(("point", "lower", "upper"), values)}
                              for name, values in methods.items()}}
                 for i, r in enumerate(records["test"])]
    (output / "series.json.gz").write_bytes(gzip.compress(json_bytes(records), mtime=0))
    (output / "forecasts.json.gz").write_bytes(gzip.compress(json_bytes(forecasts), mtime=0))
    model = {"schema": "chronoscope.browser-calibration/v1", "point_model_sha256": FROZEN_SHA,
             "lookback": LOOKBACK, "horizon": HORIZON, "alpha": ALPHA,
             "normalization": "subtract_last_then_divide_population_std",
             "roughness_boundaries": list(BINS), "calibration_bin_counts": counts,
             "absolute_residual_radii": radii.tolist(), "global_radii": global_radius.tolist()}
    (output / "calibration.json").write_bytes(json_bytes(model))
    sources = {p: digest(ROOT / p) for p in (
        "docs/guides/browser-calibration-confirmation-protocol.md", "scripts/confirm_browser_calibration.py",
        "scripts/evaluate_browser_linear.py", "scripts/train_nlinear_onnx.py", "requirements-browser-model.txt",
        "docs/research/browser-linear/v1/results.json", "frontend/public/models/nlinear.onnx", "frontend/src/lib/nlinearMeta.json")}
    checks = admission(scores, counts, parity, all(np.array_equal(point, values[0]) for values in methods.values()))
    result = {"schema": "chronoscope.browser-calibration-confirmation/v1", "population": "synthetic generator only",
              "splits": {k: {"series": n, "seed": seed} for k, (n, seed) in SPLITS.items()},
              "scores": scores, "group_counts": {name: int(np.sum(mask)) for name, mask in groups.items()},
              "per_lead_coverage": {name: np.mean((ty >= values[1]) & (ty <= values[2]), axis=0).tolist()
                                    for name, values in methods.items()},
              "paired_exploratory": paired, "max_normalized_runtime_error": parity,
              "engineering_admission": checks, "engineering_admitted": all(checks.values()), "sources": sources,
              "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                          **{name: importlib.metadata.version(name) for name in ("numpy", "onnx", "onnxruntime")}},
              "artifacts": {p.name: digest(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output / "results.json").write_bytes(json_bytes(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    result = run(parser.parse_args().output)
    print(json.dumps({"scores": result["scores"], "admission": result["engineering_admission"],
                      "paired": result["paired_exploratory"]}, indent=2))
