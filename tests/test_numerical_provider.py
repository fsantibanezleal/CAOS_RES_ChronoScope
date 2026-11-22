"""The live product consumes published numerical modules rather than a local distribution."""
import importlib
import json
from pathlib import Path
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = json.loads((ROOT / "docs/validation/base-adoption-2026-11-22/forecastscope-provider.json").read_text())


def test_product_has_only_path_tooling_and_no_private_distribution():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "project" not in config and "build-system" not in config
    assert not (ROOT / "data-pipeline/chronoscopelab").exists()
    assert (ROOT / "data-pipeline/run.py").is_file()
    metadata = json.loads((ROOT / "product.json").read_text())
    assert "forecastscope" in metadata["method_packages"]
    assert all(path.startswith("data-pipeline/engine/") for path in metadata["pipeline_stage_sources"].values())


@pytest.mark.parametrize("adapter,provider", sorted(PROVIDER["adapters"].items()))
def test_current_entrypoint_resolves_to_the_installed_published_numerical_module(adapter, provider):
    module = adapter.removeprefix("data-pipeline/").removesuffix(".py").replace("/", ".")
    assert importlib.import_module(module) is importlib.import_module(provider)
