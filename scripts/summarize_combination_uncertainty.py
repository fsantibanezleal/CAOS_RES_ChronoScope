"""Paired, series-level resampling of the frozen external combination study.

This is exploratory uncertainty analysis of recorded scores, never refitting,
hyperparameter selection or a population-performance guarantee. Observations
within one series stay together. Related series may still violate exchangeability.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("ContextMemoryCV", "ValidationMix")
CONTROLS = ("RecencyMean", "AutoTheta", "AutoETS")
METRICS = ("mase", "msis", "coverage")


def series_scores(rows):
    """Origins average inside each identity; identities receive equal weight."""
    result = {}
    for row in sorted(rows, key=lambda r: (r["dataset"], r["id"])):
        if row.get("excluded"):
            continue
        key = (row["dataset"], row["id"])
        if key in result or not row["origins"]:
            raise ValueError("Each admitted series must occur once and contain scored origins")
        origins = []
        for origin in row["origins"]:
            scores = {model["name"]: model["metrics"] for model in origin["methods"]}
            if len(scores) != len(origin["methods"]) or not set(METHODS + CONTROLS) <= scores.keys():
                raise ValueError("Missing or duplicate method in a scored origin")
            origins.append(scores)
        result[key] = {name: {metric: float(np.mean([o[name][metric] for o in origins]))
                             for metric in METRICS} for name in METHODS + CONTROLS}
    return result


def paired_interval(differences, *, seed, resamples=10000, batch=64):
    """Percentile interval for the empirical mean; memory bounded by batch size."""
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Paired differences must be a nonempty finite vector")
    if resamples < 100 or batch < 1:
        raise ValueError("At least 100 resamples and a positive batch size are required")
    rng = np.random.Generator(np.random.PCG64(seed))
    means = np.empty(resamples)
    for start in range(0, resamples, batch):
        size = min(batch, resamples - start)
        indices = rng.integers(0, len(values), size=(size, len(values)))
        means[start:start + size] = values[indices].mean(axis=1)
    low, high = np.quantile(means, (.025, .975), method="linear")
    return {"difference": float(values.mean()), "percentile_95": [float(low), float(high)],
            "series": len(values), "negative": int(np.sum(values < 0)),
            "zero": int(np.sum(values == 0)), "positive": int(np.sum(values > 0)),
            "median_difference": float(np.median(values))}


def summarize(document, *, resamples=10000, seed=20261105):
    scores = series_scores(document["series"])
    comparisons = []
    for dataset in sorted({key[0] for key in scores}):
        sample = [value for key, value in scores.items() if key[0] == dataset]
        # The same stream indexes series identically for every comparison in a dataset.
        stream = seed + int.from_bytes(hashlib.sha256(dataset.encode()).digest()[:4], "little")
        for method in METHODS:
            for control in CONTROLS:
                for metric in METRICS:
                    delta = [s[method][metric] - s[control][metric] for s in sample]
                    row = paired_interval(delta, seed=stream, resamples=resamples)
                    row.update(dataset=dataset, method=method, control=control, metric=metric,
                               method_mean=float(np.mean([s[method][metric] for s in sample])),
                               control_mean=float(np.mean([s[control][metric] for s in sample])))
                    comparisons.append(row)
    return {"schema": "chronoscope-paired-series-uncertainty-v1", "analysis": "exploratory",
            "protocol": {"seed": seed, "resamples": resamples, "generator": "numpy.PCG64",
                         "unit": "series after averaging its available origins",
                         "interval": "paired empirical percentile 0.025/0.975, linear quantiles",
                         "direction": "method minus control; lower favors method for MASE and MSIS",
                         "coverage": "signed coverage difference, not an improvement score",
                         "multiplicity": "unadjusted exploratory intervals; no familywise claim",
                         "scope": "conditional on admitted collections and exchangeable series; related series may violate this",
                         "selection": "no refit, no tuning, no new external data; analysis specified after original outcomes"},
            "comparisons": comparisons,
            "sources": ["https://doi.org/10.1214/aos/1176344552",
                        "https://www.jmlr.org/papers/v7/demsar06a.html"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resamples", type=int, default=10000)
    args = parser.parse_args()
    index = json.loads((ROOT / "data/derived/validated-combinations.json").read_text(encoding="utf-8"))
    raw = (ROOT / index["audit"]["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != index["audit"]["sha256"]:
        raise ValueError("Full audit archive differs from its frozen index binding")
    content = gzip.decompress(raw)
    if hashlib.sha256(content).hexdigest() != index["audit"]["uncompressed_sha256"]:
        raise ValueError("Decompressed full audit differs from its frozen binding")
    result = summarize(json.loads(content), resamples=args.resamples)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    result["code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["numpy"] = np.__version__
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(f"Recorded {len(result['comparisons'])} paired comparisons; no models refitted")


if __name__ == "__main__":
    main()
