"""Observable-range checks shared by export and the independent artifact sweep.

The widened range is an output diagnostic, never a clipping or fitting rule.
Only a wholly disjoint point path blocks; interval width and a flat point path
are not accuracy failures. Constants below are dimensionless ratios.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping


def check_forecast_units(observed: Iterable[float], methods: Iterable[Mapping]) -> list[dict]:
    """Check finite paths and their observable, preserving poor but in-range fits.

    Call after predicting. ``observed`` may contain evaluation truths because
    this diagnostic only accepts/refuses output; it never alters a fitted model.
    The caller retains units and source provenance, including unknown units.
    """
    values = [float(v) for v in observed]
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError("The observed reference must be nonempty and finite")
    lo, hi = min(values), max(values)
    span = hi - lo
    if not math.isfinite(span):
        raise ValueError("The observed reference range overflows")
    bounds = (lo - span, hi + span)  # one full observed range of slack per side
    problems = []
    for method in methods:
        name = str(method.get("name", "unnamed"))
        paths = {k: [float(v) for v in method.get(k, ())] for k in ("point", "lower", "upper")}
        if not paths["point"] or len({len(p) for p in paths.values()}) != 1:
            problems.append({"method": name, "violation": "empty_or_mismatched_paths", "blocking": True})
            continue
        if not all(math.isfinite(v) for p in paths.values() for v in p):
            problems.append({"method": name, "violation": "non_finite_prediction", "blocking": True})
            continue
        if any(a > b or b > c for a, b, c in zip(paths["lower"], paths["point"], paths["upper"], strict=True)):
            problems.append({"method": name, "violation": "unordered_prediction_interval", "blocking": True})
            continue
        low, high = min(paths["point"]), max(paths["point"])
        if high < bounds[0] or low > bounds[1]:
            problems.append({"method": name, "violation": "prediction_outside_observable", "blocking": True,
                             "observed_range": [lo, hi], "point_range": [low, high]})
        elif span > 0 and high - low <= 1e-6 * span:
            problems.append({"method": name, "violation": "constant_prediction", "blocking": False,
                             "detail": "A flat point path can be a legitimate level forecast; retained as advisory"})
    return problems


def require_forecast_units(observed: Iterable[float], methods: Iterable[Mapping]) -> list[dict]:
    """Refuse blocking output before any export; return only advisory findings."""
    problems = check_forecast_units(observed, methods)
    blocking = [p for p in problems if p["blocking"]]
    if blocking:
        raise ValueError(f"Forecast observable gate refused output: {blocking}")
    return problems
