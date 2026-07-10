"""Pipeline smoke + determinism: a case regenerates deterministically (same seed -> identical artifact), the
control case runs, the real case ingests, and run_all writes the flat index. Also checks that the trace shape
matches CONTRACT 2 and that ChronoScope's evaluate stage produced backtest metrics via preqts.

Pipeline writes are sandboxed suite-wide by the conftest autouse fixture (the committed data/derived is
the canonical GPU bake; see conftest for the incident record)."""
import json

from chronoscopelab import pipeline, registry


def _trace(manifest):
    return json.loads((pipeline.DERIVED / manifest["artifact"]["path"]).read_text(encoding="utf-8"))


def test_case_deterministic_same_seed():
    a = pipeline.precompute("SEAS_hourly", seed=7)
    b = pipeline.precompute("SEAS_hourly", seed=7)
    assert a["artifact"]["bytes"] == b["artifact"]["bytes"]


def test_trace_shape_and_methods():
    m = pipeline.precompute("SEAS_hourly", seed=42)
    tr = _trace(m)
    assert tr["schema"].startswith("chronoscope.trace/")
    assert len(tr["actual"]) == tr["horizon"]
    assert len(tr["methods"]) >= 5  # classical ladder (5) + any available heavy engines
    for meth in tr["methods"]:
        assert len(meth["point"]) == tr["horizon"]
        assert len(meth["lower"]) == tr["horizon"]
        assert "mase" in meth["backtest"]
    assert tr["summary"]["best_method"] in {meth["name"] for meth in tr["methods"]}


def test_real_case_ingests_and_scores():
    m = pipeline.precompute("REAL_electricity", seed=1)
    assert m["real_or_synthetic"] == "real"
    assert m["series"]["n_obs"] > 100
    assert m["best_method"] is not None


def test_control_case_runs():
    m = pipeline.precompute("CTRL_white_noise", seed=1)
    assert m["lane"] in ("live", "precompute")


def test_run_all_writes_index():
    entries = pipeline.run_all(seed=42)
    assert len(entries) == len(registry.list_cases()) >= 6
    idx = json.loads((pipeline.MANIFESTS / "index.json").read_text(encoding="utf-8"))
    assert idx["n_cases"] == len(entries)
    assert idx["schema"].startswith("chronoscope.index/")
