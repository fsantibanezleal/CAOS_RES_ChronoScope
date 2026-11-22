"""Scientific candidates cannot overwrite the admitted corpus or selector."""
from pathlib import Path
import subprocess
import sys

import pytest

from engine import pipeline

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("arguments", [[], ["--output-root", "relative-candidate"],
                                        ["--output-root", str(ROOT / "candidate")]])
def test_adversarial_cli_refuses_unsafe_outputs_before_training(arguments):
    result = subprocess.run([sys.executable, "data-pipeline/run.py", *arguments], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert "output-root" in result.stderr or "outside the source checkout" in result.stderr
    assert "precomputed" not in result.stdout


@pytest.mark.parametrize("name", ["DERIVED", "MANIFESTS", "MODELS"])
def test_adversarial_programmatic_bake_refuses_each_in_checkout_output(name, monkeypatch, tmp_path):
    for destination in ("DERIVED", "MANIFESTS", "MODELS"):
        monkeypatch.setattr(pipeline, destination, tmp_path / "candidate" / destination.lower())
    monkeypatch.setattr(pipeline, name, ROOT / "forbidden-output")

    def forbidden(*args, **kwargs):
        raise AssertionError("Training must not start before output admission")

    monkeypatch.setattr(pipeline.train, "run", forbidden)
    with pytest.raises(ValueError, match=f"Scientific {name.lower()} output.*outside the source checkout"):
        pipeline.precompute("CTRL_white_noise")


def test_complete_external_layout_is_admitted_without_touching_the_checkout(tmp_path, monkeypatch):
    for destination in ("DERIVED", "MANIFESTS", "MODELS"):
        monkeypatch.setattr(pipeline, destination, tmp_path / "before" / destination.lower())
    candidate = tmp_path / "candidate with spaces"
    pipeline._configure_outputs(candidate)
    pipeline._require_external_outputs()
    assert all(path.is_relative_to(candidate) for path in (pipeline.DERIVED, pipeline.MANIFESTS, pipeline.MODELS))
    assert not candidate.exists()
