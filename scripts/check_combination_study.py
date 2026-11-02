"""Independently admit complete combination outcomes, paths and temporal schedules."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPERTS = ("SeasonalNaive", "SES", "Holt", "HoltWinters", "Theta")


def validate(document, source_root):
    from run_forecastability_study import series_from_tsf

    assert len(document["series"]) == 1787, "Incomplete source inventory"
    for path, digest in document["code_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    methods_checked, origins_checked = 0, 0
    summary = {}
    for dataset, config in document["datasets"].items():
        path = source_root / config["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == document["input_sha256"][dataset]
        source = {name: y for name, _, y in series_from_tsf(path)}
        rows = [r for r in document["series"] if r["dataset"] == dataset]
        assert len(source) == len(rows) == config["count"]
        assert {r["id"] for r in rows} == set(source)
        aggregated = {}
        h, m = config["horizon"], config["seasonality"]
        for row in rows:
            y = source[row["id"]]
            assert hashlib.sha256(y.astype("<f8").tobytes()).hexdigest() == row["sequence_sha256"]
            if row.get("excluded"):
                assert row["excluded"] in {
                    "exact duplicate",
                    "nonfinite observations or no eligible origin",
                    "unavailable seasonal MASE scale at an outer origin",
                }
                if row["excluded"] == "exact duplicate":
                    other = next(
                        r for r in document["series"] if r["dataset"] + "/" + r["id"] == row["representative"]
                    )
                    assert other["sequence_sha256"] == row["sequence_sha256"]
                continue
            expected = [
                o for o in (len(y) - 3 * h, len(y) - 2 * h, len(y) - h) if o >= max(2 * m, 2 * h + 8, 24)
            ]
            assert [o["origin"] for o in row["origins"]] == expected
            per_series = {}
            for origin in row["origins"]:
                origins_checked += 1
                t = origin["origin"]
                prefix = y[max(0, t - 512) : t]
                actual = y[t : t + h]
                np.testing.assert_array_equal(origin["actual"], actual)
                assert origin["prefix_length"] == len(prefix)
                assert origin["prefix_start"] == t - len(prefix)
                assert origin["prefix_sha256"] == hashlib.sha256(prefix.astype("<f8").tobytes()).hexdigest()
                scale = float(np.mean(abs(prefix[m:] - prefix[:-m])))
                np.testing.assert_allclose(scale, origin["scale"], rtol=1e-12)
                forecasts = {model["name"]: np.asarray(model["quantiles"]) for model in origin["methods"]}
                assert len(forecasts) == 12
                for model in origin["methods"]:
                    q = forecasts[model["name"]]
                    assert q.shape == (h, 3) and np.isfinite(q).all() and np.all(np.diff(q, axis=1) >= 0)
                    error = abs(actual - q[:, 1])
                    iscore = (
                        q[:, 2]
                        - q[:, 0]
                        + 10 * np.maximum(q[:, 0] - actual, 0)
                        + 10 * np.maximum(actual - q[:, 2], 0)
                    )
                    score = {
                        "mase": float(np.mean(error) / scale),
                        "mae": float(np.mean(error)),
                        "coverage": float(np.mean((actual >= q[:, 0]) & (actual <= q[:, 2]))),
                        "mean_width": float(np.mean(q[:, 2] - q[:, 0])),
                        "msis": float(np.mean(iscore) / scale),
                    }
                    for key, value in score.items():
                        np.testing.assert_allclose(value, model["metrics"][key], rtol=1e-10, atol=1e-10)
                    per_series.setdefault(model["name"], []).append(score)
                    if "weights" in model:
                        weights = np.asarray(model["weights"])
                        assert len(weights) == 5 and np.min(weights) >= 0.01 - 1e-10
                        np.testing.assert_allclose(np.sum(weights), 1, rtol=0, atol=1e-10)
                        mixture = np.tensordot(
                            weights, np.array([forecasts[e] for e in EXPERTS]), axes=(0, 0)
                        )
                        np.testing.assert_allclose(mixture, q, rtol=1e-10, atol=1e-8)
                        assert all(o + h <= len(prefix) for o in model["memory_origins"])
                    if "validation_splits" in model:
                        for split in model["validation_splits"]:
                            assert len(split["train"]) >= 3
                            assert all(
                                model["memory_origins"][j] + h <= split["query"] for j in split["train"]
                            )
                        scored = [
                            c for c in model["validation"] if c["mean_validation_mae_scaled"] is not None
                        ]
                        selected = (
                            min(scored, key=lambda c: c["mean_validation_mae_scaled"])["configuration"]
                            if scored
                            else ["recency", 1.0, 1.0]
                        )
                        assert model["selected"] == list(selected)
                    methods_checked += 1
            for name, values in per_series.items():
                aggregated.setdefault(name, []).append(
                    {k: float(np.mean([v[k] for v in values])) for k in values[0]}
                )
        for name, values in aggregated.items():
            expected = document["summaries"][dataset][name]
            assert expected["series"] == len(values)
            for key in values[0]:
                np.testing.assert_allclose(
                    np.mean([v[key] for v in values]), expected[key], rtol=1e-10, atol=1e-10
                )
        summary[dataset] = {
            "inventory": len(rows),
            "admitted": len(next(iter(aggregated.values()))),
            "exclusions": dict(Counter(r["excluded"] for r in rows if r.get("excluded"))),
        }
    return {
        "ok": True,
        "origins_checked": origins_checked,
        "method_forecasts_checked": methods_checked,
        "datasets": summary,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.document.read_text(encoding="utf-8")), args.source_root), indent=2))


if __name__ == "__main__":
    main()
