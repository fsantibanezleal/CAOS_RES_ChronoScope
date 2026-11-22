"""CONTRACT 2 (artifact) tests: the manifest points to a real artifact with the recorded byte size, and the
lane verdict is consistent with the gate."""
from engine import pipeline


def test_manifest_matches_artifact_and_gate():
    m = pipeline.precompute("SEAS_hourly", seed=7)
    artifact = pipeline.DERIVED / m["artifact"]["path"]
    assert artifact.exists(), "manifest points to a non-existent artifact"
    assert artifact.stat().st_size == m["artifact"]["bytes"], "manifest byte size drifted from the artifact"
    assert m["schema"].startswith("chronoscope.manifest/")
    assert m["lane"] in ("live", "precompute")
    assert m["gate"]["lane"] == m["lane"], "manifest lane disagrees with the gate verdict"
    # Fast offline execution is not evidence of an implemented browser runtime.
    assert m["lane"] == "precompute"
    assert m["gate"]["pure_python"] is False
    assert "forecastscope" in m["gate"]["wheels"]
