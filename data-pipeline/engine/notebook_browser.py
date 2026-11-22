"""Worked browser-model operations using the product's canonical study producers.

These helpers compute fits, graph inference and calibration. They do not load
retained forecast paths or invoke an evidence checker as a scientific method.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_browser_linear import (  # noqa: E402
    calibration_radii, digest, final_windows, FROZEN_SHA, generate_splits,
    export_model, losses, normalize_window, runtime_predictions, select_weights,
)
from train_nlinear_onnx import _windows  # noqa: E402
from confirm_browser_calibration import (  # noqa: E402
    generate_confirmation, group_radii, roughness_bin,
)


def _graph() -> Path:
    path = ROOT / "frontend/public/models/nlinear.onnx"
    if digest(path) != FROZEN_SHA:
        raise ValueError("The browser point graph differs from the frozen study identity")
    return path


def release_context() -> dict:
    """Load declared study identities once, separately from scientific operations."""
    derived = ROOT / "data/derived"
    combination = json.loads((derived / "validated-combinations.json").read_text(encoding="utf-8"))
    entry = next(row for row in combination["cases"]
                 if (row["dataset"], row["id"]) == ("m4_weekly", "T1"))
    return {
        "readiness": json.loads((derived / "readiness.json").read_text(encoding="utf-8")),
        "admitted": json.loads((derived / "manifests/index.json").read_text(encoding="utf-8")),
        "fresh": json.loads((derived / "fresh-reevaluation.json").read_text(encoding="utf-8")),
        "combination_index": combination, "combination_entry": entry,
        "combination_case": json.loads((derived / entry["path"]).read_text(encoding="utf-8")),
    }


def exported_pair(directory: Path, case_id: str) -> tuple[dict, dict]:
    """Read the trace and manifest produced by the worked export call."""
    directory = Path(directory)
    trace = json.loads((directory / case_id / "trace.json").read_text(encoding="utf-8"))
    manifest = json.loads((directory / "manifests" / (case_id + ".json")).read_text(encoding="utf-8"))
    return trace, manifest


def observed_graph(history) -> dict:
    """Infer twelve points using only the final48 available source observations."""
    history = np.asarray(history, dtype=float)
    if history.ndim != 1 or len(history) < 48 or not np.isfinite(history).all():
        raise ValueError("Observed graph input must be a finite chronological history of at least48 rows")
    # The normalizer's target output is unused; no observed future is provided.
    normalized, _, scale, last = normalize_window(history[-48:], np.zeros(12))
    point = runtime_predictions(_graph(), normalized[None, :])[0]
    return {"point": point * scale + last, "normalized_point": point,
            "scale": scale, "last": last, "lookback": 48, "horizon": 12}


def ridge_experiment() -> dict:
    """Fit, select, calibrate and score on the original disjoint generated splits."""
    records = generate_splits()
    training = [_windows(np.asarray(row["values"])) for row in records["training"]]
    train_x = np.concatenate([pair[0] for pair in training])
    train_y = np.concatenate([pair[1] for pair in training])
    validation, calibration, test = [final_windows(records[name])
                                    for name in ("validation", "calibration", "test")]
    weights, candidates = select_weights(train_x, train_y, validation[0], validation[1])
    cx, cy, _, _ = calibration
    tx, ty, _, _ = test
    temporary = os.environ.get("CAOS_TEMP_ROOT")
    if not temporary:
        raise ValueError("Ridge graph execution needs the configured external CAOS_TEMP_ROOT")
    temporary = Path(temporary).expanduser().resolve()
    if temporary == ROOT or temporary.is_relative_to(ROOT):
        raise ValueError("Notebook graph scratch must be outside the product repository")
    temporary.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="lesson-browser-", dir=temporary) as directory:
        ridge_graph = Path(directory) / "ridge.onnx"
        export_model(weights, ridge_graph)
        point_ridge = runtime_predictions(ridge_graph, tx)
        calibration_point = runtime_predictions(ridge_graph, cx)
    point_frozen = runtime_predictions(_graph(), tx)
    radius_ridge = calibration_radii(cy - calibration_point)
    meta = json.loads((ROOT / "frontend/src/lib/nlinearMeta.json").read_text(encoding="utf-8"))
    frozen_radius = 1.2815515655446004 * float(meta["sigma_norm"]) * np.sqrt(np.arange(1, 13))
    values = {
        "frozen": losses(ty, point_frozen, point_frozen - frozen_radius, point_frozen + frozen_radius),
        "ridge": losses(ty, point_ridge, point_ridge - radius_ridge, point_ridge + radius_ridge),
    }
    return {"validation": candidates, "counts": {name: len(rows) for name, rows in records.items()},
            "weights": weights, "scores": {name: {key: float(np.mean(value)) for key, value in row.items()}
                                            for name, row in values.items()},
            "test": {"actual": ty, "frozen": point_frozen, "ridge": point_ridge}}


def calibration_experiment() -> dict:
    """Keep the actual graph points fixed while learning radii from separate series."""
    records = generate_confirmation()
    cx, cy, _, _ = final_windows(records["calibration"])
    tx, ty, _, _ = final_windows(records["test"])
    residual = cy - runtime_predictions(_graph(), cx)
    radii, counts = group_radii(cx, residual)
    global_radius = calibration_radii(residual)
    point = runtime_predictions(_graph(), tx)
    groups = roughness_bin(tx)
    sigma = float(json.loads((ROOT / "frontend/src/lib/nlinearMeta.json").read_text(encoding="utf-8"))["sigma_norm"])
    gaussian_radius = 1.2815515655446004 * sigma * np.sqrt(np.arange(1, 13))
    half_widths = {"gaussian": gaussian_radius, "global": global_radius, "stratified": radii[groups]}
    scores = {name: losses(ty, point, point - width, point + width) for name, width in half_widths.items()}
    return {"counts": counts, "radii": radii, "global_radii": global_radius,
            "scores": {name: {key: float(np.mean(value)) for key, value in row.items()}
                       for name, row in scores.items()},
            "test": {"actual": ty, "point": point, "groups": groups}, "test_series": len(tx)}
