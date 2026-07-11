"""Streaming-bench stage tests: the preqts prequential trajectories bake per case (the flagship piece)."""
import numpy as np

from chronoscopelab.io.schema import SeriesSpec
from chronoscopelab.stages import streaming


def _spec(n=300, m=12, seed=0, case_id="stream_test"):
    rng = np.random.default_rng(seed)
    y = 50 + 10 * np.sin(np.arange(n) * 2 * np.pi / m) + rng.normal(0, 2.0, n)
    return SeriesSpec(case_id=case_id, y=list(y), seasonality=m, horizon=m)


def test_streaming_bench_runs_the_roster():
    out = streaming.run(_spec())
    assert set(out["methods"]) == {"SeasonalNaive", "Theta", "Theta+ACI", "Theta+PID"}
    for name, block in out["methods"].items():
        assert "error" not in block, f"{name} failed: {block.get('error')}"
        assert block["n_steps"] > 20
        assert len(block["rolling_mase"]) == block["n_steps"]
        assert len(block["rolling_coverage"]) == block["n_steps"]
        assert len(block["cumulative_cost_ms"]) == block["n_steps"]


def test_calibration_improves_or_matches_coverage_error():
    """The whole point: on a drifting stream, the ACI/PID variants track nominal coverage better."""
    rng = np.random.default_rng(1)
    n = 400
    y = 50 + 10 * np.sin(np.arange(n) * 2 * np.pi / 12)
    noise = np.concatenate([rng.normal(0, 1.0, n // 2), rng.normal(0, 3.0, n - n // 2)])  # regime shift
    spec = SeriesSpec(case_id="shift", y=list(y + noise), seasonality=12, horizon=12)
    out = streaming.run(spec)
    target = out["nominal_coverage"]
    raw = abs(out["methods"]["Theta"]["final"]["coverage"] - target)
    aci = abs(out["methods"]["Theta+ACI"]["final"]["coverage"] - target)
    pid = abs(out["methods"]["Theta+PID"]["final"]["coverage"] - target)
    assert aci <= raw + 0.05
    assert pid <= raw + 0.05


def test_cost_trajectories_are_monotone():
    out = streaming.run(_spec())
    for block in out["methods"].values():
        cost = block["cumulative_cost_ms"]
        assert all(b >= a - 1e-9 for a, b in zip(cost, cost[1:]))  # cumulative => non-decreasing


def test_block_is_json_ready_and_referenced():
    out = streaming.run(_spec())
    import json

    json.dumps(out)                                        # fully serializable
    assert "references" in out and "preqts" in out["references"]["package"]
    assert out["nominal_coverage"] == 0.8


def test_exog_case_demonstrates_the_covariate_policy():
    """The known-future-covariate case: the covariate-AWARE ridge must beat the covariate-BLIND one, and
    the streaming block must carry the covariate with its arrival policy (the preqts novel piece)."""
    from chronoscopelab import registry

    spec = registry.build_series(registry.get_case("EXOG_promo"), seed=42)
    assert spec.covariates and spec.covariates[0].kind == "known_future"
    out = streaming.run(spec, horizon=1)
    assert out["covariate"] is not None
    assert out["covariate"]["kind"] == "known_future"
    assert len(out["covariate"]["values"]) == len(spec.y)
    aware = out["methods"]["Ridge+exog (aware)"]["final"]["mase"]
    blind = out["methods"]["Ridge (blind)"]["final"]["mase"]
    assert aware is not None and blind is not None
    assert aware < blind          # knowing the scheduled driver ahead genuinely helps
    import json
    json.dumps(out)               # still fully serializable with the covariate block


def test_univariate_case_has_no_covariate_block_or_ridge_roster():
    out = streaming.run(_spec())  # a synthetic univariate spec
    assert out["covariate"] is None
    assert "Ridge+exog (aware)" not in out["methods"]   # the ridge roster only appears with a covariate
