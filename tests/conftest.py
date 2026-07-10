"""Make chronoscopelab importable whether or not `pip install -e .` has run (belt-and-suspenders for CI/local).

Also sandbox EVERY pipeline write for the whole suite: the committed data/derived is the canonical GPU bake
(all 18 methods), and any test regenerating a case on the test environment's lighter engine set would silently
downgrade the artifacts the site deploys (this shipped once, v0.14.000-v0.15.000: a smoke test's run_all()
clobbered the bake to the 9-method CPU lane). The autouse fixture makes the class of bug impossible here;
scripts/check_artifacts.py's ladder guard catches any other writer in CI.
"""
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "data-pipeline"))


@pytest.fixture(autouse=True)
def _sandbox_pipeline_writes(tmp_path, monkeypatch):
    from chronoscopelab import pipeline

    monkeypatch.setattr(pipeline, "DERIVED", tmp_path / "derived")
    monkeypatch.setattr(pipeline, "MANIFESTS", tmp_path / "derived" / "manifests")
