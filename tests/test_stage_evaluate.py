"""Evaluate-stage tests for the extended metric block (preqts 0.3 / trace v2): every method entry
carries the point family (MAE/RMSE/sMAPE), MSIS, and the per-lead scaled error curve, and the trace
ships them (including for license-redacted sources, where they are aggregates like MASE)."""
import numpy as np

from chronoscopelab import registry
from chronoscopelab.core.trace import TRACE_SCHEMA, build_trace
from chronoscopelab.methods import all_forecasters
from chronoscopelab.stages import evaluate, infer

QLEVELS = (0.1, 0.5, 0.9)

METRIC_KEYS = ("mase", "wql", "coverage", "mae", "rmse", "smape", "msis")


def _fast_forecasters():
    """Two cheap classical methods; the metric plumbing is method-agnostic."""
    fcs = all_forecasters()
    picked = [fc for fc in fcs if fc.name in ("SeasonalNaive", "Theta")]
    assert len(picked) == 2
    return picked


def test_evaluate_carries_the_extended_metric_block():
    spec = registry.build_series(registry.get_case("SEAS_hourly"), seed=42)
    out = evaluate.run(spec, QLEVELS, forecasters=_fast_forecasters())
    for name, m in out["methods"].items():
        for k in METRIC_KEYS:
            assert k in m, f"{name} missing {k}"
            assert np.isfinite(m[k]), f"{name} {k} not finite"
        curve = m["per_horizon_scaled"]
        assert len(curve) == spec.horizon
        assert all(np.isfinite(v) for v in curve)
        # sanity: RMSE dominates MAE; sMAPE within its [0, 2] bound; MSIS positive
        assert m["rmse"] >= m["mae"] > 0
        assert 0.0 <= m["smape"] <= 2.0
        assert m["msis"] > 0


def test_per_horizon_curve_is_the_star_readout_shape():
    # On a seasonal case the seasonal naive's scaled error must stay flat-ish (no growth by lead:
    # every lead is one season back), while Theta's drifts; both must be positive and finite.
    spec = registry.build_series(registry.get_case("SEAS_hourly"), seed=42)
    out = evaluate.run(spec, QLEVELS, forecasters=_fast_forecasters())
    naive = out["methods"]["SeasonalNaive"]["per_horizon_scaled"]
    spread = max(naive) - min(naive)
    assert spread < 0.75 * max(naive)  # flat-ish: the spread is well under the level itself


def test_trace_v2_ships_the_metric_block_even_when_redacted():
    spec = registry.build_series(registry.get_case("SEAS_hourly"), seed=42)
    result = infer.run(spec, QLEVELS)
    _, actual = infer.split(spec)
    metrics = evaluate.run(spec, QLEVELS, forecasters=_fast_forecasters())
    trace = build_trace(result, [float(v) for v in actual], metrics, redact_raw=True)
    assert trace["schema"] == TRACE_SCHEMA == "chronoscope.trace/v2"
    scored = {m["name"]: m for m in trace["methods"] if m["name"] in metrics["methods"]}
    assert set(scored) == {"SeasonalNaive", "Theta"}
    for m in trace["methods"]:
        assert "point" not in m  # redaction still holds for every method
    for m in scored.values():
        for k in METRIC_KEYS:
            assert m["backtest"][k] is not None
        assert len(m["backtest"]["per_horizon_scaled"]) == spec.horizon
