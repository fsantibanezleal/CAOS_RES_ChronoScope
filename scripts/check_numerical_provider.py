"""Compare published methods with verified frozen reference kernels on every shipped history.

The reference is executed only by this independent verification command under a
separate namespace. Product execution and admission never import the old kernels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import types

import numpy as np
from forecastscope import combine, forecast

from method_inventory import numerical_providers
from source_bindings import verified_archive

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path("docs/validation/base-adoption-2026-11-22/forecastscope-parity.json")


def reference(root):
    receipt, sources = verified_archive(root)
    name = "chronoscope_frozen_reference"
    for suffix in ("", ".io", ".model"):
        module = types.ModuleType(name + suffix)
        module.__path__ = []
        sys.modules[module.__name__] = module
    for suffix in ("io.schema", "model.forecasters", "model.context_memory", "model.validated_combination"):
        path = "data-pipeline/chronoscopelab/" + suffix.replace(".", "/") + ".py"
        module = types.ModuleType(name + "." + suffix)
        module.__package__ = module.__name__.rpartition(".")[0]
        module.__file__ = "verified-frozen-reference/" + path
        sys.modules[module.__name__] = module
        exec(compile(sources[path], module.__file__, "exec"), module.__dict__)
    return receipt, tuple(sys.modules[name + ".model." + suffix]
                          for suffix in ("forecasters", "context_memory", "validated_combination"))


def validate(root=ROOT):
    providers = numerical_providers(root)
    archive, (old, contextual, validated) = reference(root)
    source = root / "data/derived/fresh-reevaluation.json"
    cases = json.loads(source.read_text(encoding="utf-8"))["cases"]
    assert len(cases) == 15
    rows = []
    for case in cases:
        y, m, h = np.asarray(case["history"]), case["seasonality"], case["horizon"]
        names = []
        for name, _, fn in old.METHODS:
            expected = old.gaussian_quantiles(*fn(y, m, h), (.1, .5, .9))
            actual = forecast(name, y, seasonality=m, horizon=h)
            np.testing.assert_array_equal(actual, expected)
            names.append(name)
        for name, mode in [("ContextMemory", "context"), ("RecencyMean", "recency"),
                           ("EqualMean", "uniform"), ("ContextMemoryCV", None), ("ValidationMix", None)]:
            expected = (contextual.fit_context_memory(y, m, h, mode=mode) if mode else
                        validated.fit_validated(y, m, h, stacking=name == "ValidationMix"))
            actual = combine(name, y, seasonality=m, horizon=h)
            np.testing.assert_array_equal(actual.quantiles, expected.quantiles)
            np.testing.assert_array_equal(actual.weights, expected.weights)
            assert actual.origins == expected.origins
            names.append(name)
        rows.append({"case_id": case["case_id"],
                     "history_sha256": hashlib.sha256(y.astype("<f8").tobytes()).hexdigest(),
                     "history_length": len(y), "horizon": h, "seasonality": m,
                     "exact_methods": names})
        print(case["case_id"], len(names), "exact forecast and combination comparisons", flush=True)
    receipt = json.loads((root / "docs/validation/base-adoption-2026-11-22/forecastscope-provider.json").read_text())
    return {"schema": "chronoscope-numerical-provider-parity-v1",
            "distribution": receipt["distribution"], "version": receipt["version"],
            "source_artifact_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_archive_sha256": archive["archive_sha256"], "provider_module_count": len(providers),
            "cases": rows, "exact_comparisons": sum(len(row["exact_methods"]) for row in rows),
            "scope": "Full-precision forecast quantiles, allocation weights and historical origins on the fifteen shipped histories; diagnostic unit changes have separate controls. No new accuracy experiment.",
            "runtime": {"python": platform.python_version(), "numpy": np.__version__}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = validate()
    path = ROOT / REPORT
    if args.write:
        path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    else:
        expected = json.loads(path.read_text(encoding="utf-8"))
        for field in ("distribution", "version", "source_artifact_sha256", "source_archive_sha256",
                      "provider_module_count", "cases", "exact_comparisons"):
            assert result[field] == expected[field], "Provider parity receipt differs: " + field
    print("Published numerical provider:", result["exact_comparisons"], "exact comparisons")


if __name__ == "__main__":
    main()
