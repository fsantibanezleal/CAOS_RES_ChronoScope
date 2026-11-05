"""Independently rescore stored browser-linear forecasts, using only stdlib.

This does not import the fitting, calibration or scoring producer. Actual ONNX
parity is a separate execution gate, recorded by the source-bound experiments.
"""
from __future__ import annotations

import gzip
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/research/browser-linear"
METRICS = ("normalized_mse", "normalized_mae", "coverage", "normalized_width", "normalized_interval_score")


def close(actual, expected, context):
    if not math.isfinite(actual) or not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-10):
        raise ValueError(f"Evidence mismatch: {context}: {actual} != {expected}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def roughness_group(history):
    variance = statistics.pvariance(history)
    roughness = statistics.mean((b - a) ** 2 for a, b in zip(history, history[1:])) / variance
    return 0 if roughness < .5 else 1 if roughness < 1.25 else 2


def validate_directory(directory: Path, seen: set[str], source_root=ROOT) -> dict:
    result = json.loads((directory / "results.json").read_text(encoding="utf-8"))
    confirmation = directory.name == "confirmation-v1"
    expected_schema = ("chronoscope.browser-calibration-confirmation/v1" if confirmation else
                       "chronoscope.browser-linear-evaluation/v1")
    expected_sources = {"scripts/evaluate_browser_linear.py", "scripts/train_nlinear_onnx.py",
                        "requirements-browser-model.txt", "frontend/public/models/nlinear.onnx",
                        "frontend/src/lib/nlinearMeta.json"}
    expected_sources.update({"docs/guides/browser-calibration-confirmation-protocol.md",
                             "scripts/confirm_browser_calibration.py", "docs/research/browser-linear/v1/results.json"}
                            if confirmation else {"docs/guides/browser-linear-protocol.md"})
    if result["schema"] != expected_schema or set(result["sources"]) != expected_sources:
        raise ValueError("Evidence schema or source inventory differs")
    expected_files = ({"series.json.gz", "forecasts.json.gz", "calibration.json"} if confirmation else
                      {"series.json.gz", "forecasts.json.gz", "model.json", "normalized-ridge.onnx"})
    if set(result["artifacts"]) != expected_files or {p.name for p in directory.iterdir()} != expected_files | {"results.json"}:
        raise ValueError("Incomplete or unexpected evidence payload")
    for name, expected in result["artifacts"].items():
        if sha(directory / name) != expected:
            raise ValueError(f"Artifact hash differs: {name}")
    for name, expected in result["sources"].items():
        path = (source_root / name).resolve()
        if not path.is_relative_to(source_root.resolve()) or sha(path) != expected:
            raise ValueError(f"Source hash differs: {name}")
    partitions = json.loads(gzip.decompress((directory / "series.json.gz").read_bytes()))
    expected_splits = ({"calibration": (400, 20261109), "test": (800, 20261110)} if confirmation else
                       {"training": (400, 20260704), "validation": (200, 20261105),
                        "calibration": (400, 20261106), "test": (400, 20261107)})
    if set(partitions) != set(expected_splits) or result["splits"] != {
            key: {"series": n, "seed": seed} for key, (n, seed) in expected_splits.items()}:
        raise ValueError("Protocol partition changed")
    for name, records in partitions.items():
        if len(records) != expected_splits[name][0] or len({r["id"] for r in records}) != len(records):
            raise ValueError("Incomplete or duplicate series identities")
        for record in records:
            values = record["values"]
            series_hash = hashlib.sha256((json.dumps(values, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()).hexdigest()
            if series_hash != record["sha256"] or series_hash in seen:
                raise ValueError("Changed series or overlapping partitions")
            if not 120 <= len(values) < 260 or not all(math.isfinite(v) for v in values):
                raise ValueError("Invalid generated series")
            seen.add(series_hash)
    test = {r["id"]: r for r in partitions["test"]}
    forecasts = json.loads(gzip.decompress((directory / "forecasts.json.gz").read_bytes()))
    if len(forecasts) != len(test) or {r["id"] for r in forecasts} != set(test):
        raise ValueError("Forecast inventory differs from test population")
    methods = {"gaussian", "global", "stratified"} if confirmation else {"frozen_browser_linear", "held_out_ridge"}
    rows = []
    for forecast in forecasts:
        record = test[forecast["id"]]
        history, actual = record["values"][-60:-12], record["values"][-12:]
        scale = statistics.pstdev(history)
        close(forecast["scale"], scale, "observed scale")
        if forecast["actual"] != actual or forecast["family"] != record["family"] or set(forecast["methods"]) != methods:
            raise ValueError("Forecast input or methods differ")
        group = roughness_group(history)
        if confirmation and forecast["prefix_bin"] != group:
            raise ValueError("Future data or an incorrect prefix group used")
        scored = {}
        points = []
        for name, prediction in forecast["methods"].items():
            point, lower, upper = [prediction[k] for k in ("point", "lower", "upper")]
            if (any(len(a) != 12 or not all(math.isfinite(v) for v in a) for a in (point, lower, upper))
                    or any(lo > hi for lo, hi in zip(lower, upper))):
                raise ValueError("Invalid forecast path")
            points.append(point)
            error = [(a - p) / scale for a, p in zip(actual, point)]
            scored[name] = {
                "normalized_mse": statistics.mean(e * e for e in error),
                "normalized_mae": statistics.mean(abs(e) for e in error),
                "coverage": statistics.mean(lo <= a <= hi for a, lo, hi in zip(actual, lower, upper)),
                "normalized_width": statistics.mean((hi - lo) / scale for lo, hi in zip(lower, upper)),
                "normalized_interval_score": statistics.mean((hi - lo + 10 * max(lo - a, 0) +
                                                              10 * max(a - hi, 0)) / scale
                                                             for a, lo, hi in zip(actual, lower, upper))}
        if confirmation and any(p != points[0] for p in points[1:]):
            raise ValueError("Confirmation changed a point forecast")
        if not confirmation:
            naive_error = [(a - history[-1]) / scale for a in actual]
            scored["repeat_last"] = {"normalized_mse": statistics.mean(e * e for e in naive_error),
                                     "normalized_mae": statistics.mean(abs(e) for e in naive_error)}
        rows.append((record["family"], group, scored))
    groups = {"all": rows}
    for family in ("seasonal", "trend_seasonal", "trend", "noise"):
        groups[("family_" if confirmation else "") + family] = [r for r in rows if r[0] == family]
    if confirmation:
        groups.update({f"prefix_bin_{g}": [r for r in rows if r[1] == g] for g in range(3)})
        if result["group_counts"] != {key: len(values) for key, values in groups.items()}:
            raise ValueError("Group counts differ")
    for group, observations in groups.items():
        for name in methods | (set() if confirmation else {"repeat_last"}):
            for metric in (METRICS[:2] if name == "repeat_last" else METRICS):
                value = statistics.mean(row[2][name][metric] for row in observations)
                close(value, result["scores"][group][name][metric], f"{group}/{name}/{metric}")
    for name in methods:
        for lead in range(12):
            value = statistics.mean(r["methods"][name]["lower"][lead] <= r["actual"][lead] <=
                                    r["methods"][name]["upper"][lead] for r in forecasts)
            close(value, result["per_lead_coverage"][name][lead], f"coverage lead {lead}")
    if confirmation:
        counts = [sum(roughness_group(r["values"][-60:-12]) == g for r in partitions["calibration"]) for g in range(3)]
        calibration = json.loads((directory / "calibration.json").read_text())
        if counts != calibration["calibration_bin_counts"] or min(counts) < 20:
            raise ValueError("Invalid calibration bin counts")
        for control in ("gaussian", "global"):
            delta = statistics.mean(row[2]["stratified"]["normalized_interval_score"] -
                                    row[2][control]["normalized_interval_score"] for row in rows)
            close(delta, result["paired_exploratory"][control]["mean_difference"], "paired score")
        checks = {"points_identical": True, "minimum_calibration_count": min(counts) >= 20,
                  "lower_interval_score": result["scores"]["all"]["stratified"]["normalized_interval_score"] <
                  result["scores"]["all"]["gaussian"]["normalized_interval_score"],
                  "overall_coverage": .75 <= result["scores"]["all"]["stratified"]["coverage"] <= .85,
                  "bin_coverage": all(.70 <= result["scores"][f"prefix_bin_{g}"]["stratified"]["coverage"] <= .90 for g in range(3)),
                  "runtime_parity": result["max_normalized_runtime_error"] < .0001}
        if result["engineering_admitted"] != all(checks.values()) or result["engineering_admission"] != checks:
            raise ValueError("Recorded engineering admission differs")
    else:
        for metric in ("normalized_mse", "normalized_interval_score"):
            delta = statistics.mean(row[2]["held_out_ridge"][metric] - row[2]["frozen_browser_linear"][metric] for row in rows)
            close(delta, result["paired_exploratory"][metric]["mean_difference"], "paired loss")
    return {"study": directory.name, "series": sum(len(r) for r in partitions.values()),
            "test_series": len(test), "forecast_values": len(test) * 12 * len(methods),
            "result_sha256": sha(directory / "results.json")}


def validate_runtime(directory: Path):
    """Reconstruct predictions and calibration independently from graph weights."""
    import numpy as np
    import onnx
    import onnxruntime as ort
    from onnx import numpy_helper

    confirmation = directory.name == "confirmation-v1"
    data = json.loads(gzip.decompress((directory / "series.json.gz").read_bytes()))
    stored = {r["id"]: r for r in json.loads(gzip.decompress((directory / "forecasts.json.gz").read_bytes()))}
    frozen = ROOT / "frontend/public/models/nlinear.onnx"
    models = ({"gaussian": frozen, "global": frozen, "stratified": frozen} if confirmation else
              {"frozen_browser_linear": frozen, "held_out_ridge": directory / "normalized-ridge.onnx"})
    calibration = json.loads((directory / ("calibration.json" if confirmation else "model.json")).read_text())
    gaussian_sigma = json.loads((ROOT / "frontend/src/lib/nlinearMeta.json").read_text())["sigma_norm"]
    maximum = 0.
    for method, path in models.items():
        weights = next(numpy_helper.to_array(w) for w in onnx.load(path).graph.initializer if w.name == "W")
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(path), sess_options=options, providers=["CPUExecutionProvider"])
        calibration_errors = []
        for record in data["calibration"]:
            history, actual = record["values"][-60:-12], record["values"][-12:]
            scale, last = float(np.std(history)), history[-1]
            xn = ((np.asarray(history) - last) / scale).astype(np.float32)[None]
            predicted = session.run(["y"], {"x": xn})[0][0]
            calibration_errors.append((roughness_group(history), np.abs((np.asarray(actual) - last) / scale - predicted)))
        def radius(group=None):
            errors = np.array([error for g, error in calibration_errors if group is None or g == group])
            k = math.ceil((len(errors) + 1) * .8)
            return np.sort(errors, axis=0)[k - 1]
        if confirmation and method == "stratified":
            radii = np.array([radius(g) for g in range(3)])
            np.testing.assert_allclose(radii, calibration["absolute_residual_radii"], rtol=1e-10, atol=1e-10)
        elif confirmation and method == "global":
            radii = radius()
            np.testing.assert_allclose(radii, calibration["global_radii"], rtol=1e-10, atol=1e-10)
        elif not confirmation and method == "held_out_ridge":
            radii = radius()
            np.testing.assert_allclose(radii, calibration["absolute_residual_radii"], rtol=1e-10, atol=1e-10)
        else:
            radii = np.sqrt(np.arange(1, 13)) * 1.2815515655446004 * gaussian_sigma
        for record in data["test"]:
            history = record["values"][-60:-12]
            scale, last = float(np.std(history)), history[-1]
            xn = ((np.asarray(history) - last) / scale).astype(np.float32)[None]
            predicted = session.run(["y"], {"x": xn})[0][0]
            maximum = max(maximum, float(np.max(np.abs(predicted - (xn @ weights)[0]))))
            half_width = radii[roughness_group(history)] if confirmation and method == "stratified" else radii
            expected = {"point": predicted * scale + last,
                        "lower": (predicted - half_width) * scale + last,
                        "upper": (predicted + half_width) * scale + last}
            # The producer promotes its point arrays to float64 for raw-unit mapping.
            expected["point"] = predicted.astype(float) * scale + last
            for key, values in expected.items():
                np.testing.assert_allclose(values, stored[record["id"]]["methods"][method][key], rtol=1e-10, atol=1e-10)
        if maximum >= .0001:
            raise ValueError("Independent ONNX/NumPy parity failed")
    return {"study": directory.name, "independent_max_runtime_error": maximum, "calibration_radii_reconstructed": True}


def validate(root=ROOT):
    seen = set()
    evidence = root / "docs/research/browser-linear"
    calibration = evidence / "confirmation-v1/calibration.json"
    if (root / "frontend/src/lib/browserCalibration.json").read_bytes() != calibration.read_bytes():
        raise ValueError("Browser calibration differs from admitted evidence")
    return [validate_directory(evidence / name, seen, root) for name in ("v1", "confirmation-v1")]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", action="store_true", help="Also reconstruct every prediction and radius with ONNX Runtime")
    args = parser.parse_args()
    result = {"ok": True, "studies": validate()}
    if args.runtime:
        result["runtime"] = [validate_runtime(EVIDENCE / name) for name in ("v1", "confirmation-v1")]
    print(json.dumps(result, indent=2))
