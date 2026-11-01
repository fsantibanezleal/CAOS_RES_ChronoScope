"""Structural validators for the repository's published pipeline and model contracts.

These intentionally validate the stable boundary and required fields. Detailed semantic parity is
covered by the producer and browser consumer tests named in docs/contracts/catalog.md.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any


def _object(doc: Any, required: tuple[str, ...], schema: str) -> list[str]:
    if not isinstance(doc, dict):
        return [f"expected an object for {schema}"]
    missing = [key for key in required if key not in doc]
    return [f"missing required field {key!r}" for key in missing]


def _trace(doc: Any) -> list[str]:
    out = _object(doc, ("schema", "case_id", "seasonality", "horizon", "quantile_levels", "redacted",
                        "history_len", "history_index", "history", "actual", "methods", "summary"), "trace")
    if isinstance(doc, dict):
        if not str(doc.get("schema", "")).startswith("chronoscope.trace/"):
            out.append("schema must identify a chronoscope.trace version")
        if not isinstance(doc.get("methods"), list):
            out.append("methods must be an array")
    return out


def _manifest(doc: Any) -> list[str]:
    if isinstance(doc, dict) and str(doc.get("schema", "")).startswith("chronoscope.index/"):
        out = _object(doc, ("schema", "engine_version", "n_cases", "cases"), "index")
        if isinstance(doc.get("cases"), list):
            for i, case in enumerate(doc["cases"]):
                out.extend(f"cases[{i}]: {e}" for e in _object(case, ("case_id", "category", "manifest_path"), "index entry"))
        return out
    out = _object(doc, ("schema", "case_id", "category", "real_or_synthetic", "expected_band", "engine",
                        "provenance", "series", "seed", "artifact", "lane", "gate", "flags", "best_method", "metrics"), "manifest")
    if isinstance(doc, dict) and not str(doc.get("schema", "")).startswith("chronoscope.manifest/"):
        out.append("schema must identify a chronoscope.manifest version")
    return out


def _streaming(doc: Any) -> list[str]:
    out = _object(doc, ("nominal_coverage", "horizon", "warmup", "methods", "covariate", "references"), "streaming")
    if isinstance(doc, dict) and not isinstance(doc.get("methods"), dict):
        out.append("methods must be an object keyed by method name")
    return out


def _nlinear(doc: Any) -> list[str]:
    out = _object(doc, ("name", "lookback", "horizon", "normalization", "sigma_norm", "trained_windows"), "NLinear metadata")
    if isinstance(doc, dict):
        if doc.get("name") != "NLinear":
            out.append("name must be NLinear")
        for key in ("lookback", "horizon", "trained_windows"):
            if not isinstance(doc.get(key), int) or doc[key] <= 0:
                out.append(f"{key} must be a positive integer")
    return out


_VALIDATORS: dict[str, Callable[[Any], list[str]]] = {
    "trace.py": _trace,
    "manifest.py": _manifest,
    "streaming.py": _streaming,
    "nlinear.json": _nlinear,
    "analyze.py": lambda doc: _object(doc, ("n", "seasonality_period", "stationarity", "autocorrelation",
                                             "seasonality", "filters", "changepoints", "volatility",
                                             "distribution", "fractal", "nonlinear", "causality"), "analysis"),
}


def errors(schema: str, doc: Any) -> list[str]:
    if schema == "reevaluation":
        import json
        from pathlib import Path
        from jsonschema import Draft202012Validator

        path = Path(__file__).resolve().parents[2] / "docs/contracts/schemas/reevaluation.schema.json"
        validator = Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
        return [f"{list(e.path)}: {e.message}" for e in validator.iter_errors(doc)]
    validator = _VALIDATORS.get(schema)
    if validator is None:
        raise OSError(f"no validator registered for {schema!r}")
    return validator(doc)


def component_errors(schema: str, doc: Any) -> list[str]:
    return errors(schema, doc)
