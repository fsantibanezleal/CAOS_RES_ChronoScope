"""Export license-guard tests: a local-only source ships aggregate metrics only, never a raw series excerpt."""
import json
import tempfile
from pathlib import Path

from chronoscopelab import registry
from chronoscopelab.stages import analyze, evaluate, export, feature_extraction, infer

QLEVELS = (0.1, 0.5, 0.9)


def _bake(case, tmp):
    """Bake one case into a temp dir and return (manifest, trace, analysis)."""
    spec = registry.build_series(case, seed=42)
    feature = feature_extraction.run(spec)
    result = infer.run(spec, QLEVELS)
    _, actual = infer.split(spec)
    eval_metrics = evaluate.run(spec, QLEVELS)
    analysis = analyze.run(spec)
    derived = Path(tmp) / "derived"
    manifests = derived / "manifests"
    manifest = export.run(
        case=case, feature=feature, result=result, actual=[float(v) for v in actual],
        eval_metrics=eval_metrics, seed=42, run_ms=1.0, flags=[],
        derived_dir=str(derived), manifests_dir=str(manifests), analysis=analysis,
    )
    trace = json.loads((derived / f"{case.id}/trace.json").read_text())
    art = json.loads((derived / f"{case.id}/analysis.json").read_text())
    return manifest, trace, art


def _local_only_case():
    """A case cloned from a public one but pointed at a LOCAL-only source (Kaggle M5 rules)."""
    base = registry.get_case("SEAS_hourly")
    return type(base)(
        id="LOCALONLY_probe", category=base.category, seasonality=base.seasonality, horizon=base.horizon,
        expected_band=base.expected_band, real_or_synthetic="synthetic", spec=base.spec, source="m5",
    )


def test_public_case_ships_the_full_trace():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, trace, art = _bake(registry.get_case("SEAS_hourly"), tmp)
        assert manifest["provenance"]["public_artifact_ok"] is True
        assert trace["redacted"] is False
        assert len(trace["history"]) > 0                        # the raw excerpt ships
        assert "point" in trace["methods"][0]                   # the per-step forecast paths ship
        assert "_redacted" not in art                           # the analysis arrays ship


def test_local_only_case_redacts_the_raw_series():
    with tempfile.TemporaryDirectory() as tmp:
        manifest, trace, art = _bake(_local_only_case(), tmp)
        # the manifest is honest about the license
        assert manifest["provenance"]["source"] == "m5"
        assert manifest["provenance"]["public_artifact_ok"] is False
        assert "no redistribution" in manifest["provenance"]["license"].lower()
        # the raw series excerpt and per-step paths are GONE
        assert trace["redacted"] is True
        assert trace["history"] == [] and trace["actual"] == []
        assert "point" not in trace["methods"][0]
        # but the aggregate backtest metrics STILL ship (so it contributes to the public Benchmark)
        assert trace["methods"][0]["backtest"]["mase"] is not None
        # the analysis artifact keeps scalar verdicts but drops the series-derived arrays
        assert art["_redacted"].startswith("raw series-derived arrays omitted")
        assert "acf" not in art.get("autocorrelation", {})


def test_redaction_keeps_scalar_verdicts_for_the_benchmark():
    with tempfile.TemporaryDirectory() as tmp:
        _manifest, _trace, art = _bake(_local_only_case(), tmp)
        # a scalar stationarity verdict is license-safe and still present
        st = art.get("stationarity", {})
        assert "combined_verdict" in st or "error" in st
