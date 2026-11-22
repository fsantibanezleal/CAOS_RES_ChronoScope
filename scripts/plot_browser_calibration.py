"""Computed manuscript figures from complete admitted confirmation predictions."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    evidence = ROOT / "docs/research/browser-linear/confirmation-v1"
    results = json.loads((evidence / "results.json").read_text())
    forecasts = json.loads(gzip.decompress((evidence / "forecasts.json.gz").read_bytes()))
    methods = ["gaussian", "global", "stratified"]
    labels = ["Training-residual Gaussian", "Global calibration", "Prefix-stratified calibration"]
    colors = ["#78716c", "#c27803", "#146a8a"]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "savefig.bbox": "tight"})
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.3))
    for ax, metric, title in zip(axes, ["normalized_interval_score", "normalized_width"],
                                ["Mean interval score (lower is better)", "Mean interval width"]):
        values = [results["scores"]["all"][method][metric] for method in methods]
        ax.bar(range(3), values, color=colors)
        ax.set_xticks(range(3), ["Gaussian", "Global", "Stratified"])
        ax.set(ylabel="Normalized observable units", title=title, ylim=(0, max(values) * 1.17))
        for i, value in enumerate(values):
            ax.text(i, value + .05, f"{value:.3f}", ha="center")
    fig.tight_layout()
    fig.savefig(output / "browser-interval-efficiency.pdf")
    plt.close(fig)
    families = ["noise", "trend", "seasonal", "trend_seasonal"]
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    for i, (method, label, color) in enumerate(zip(methods, labels, colors)):
        values = [results["scores"][f"family_{family}"][method]["coverage"] for family in families]
        ax.bar(np.arange(4) + (i - 1) * .24, values, .24, label=label, color=color)
    ax.axhline(.8, color="black", linestyle="--", linewidth=1, label="Nominal 80%")
    ax.set_xticks(range(4), ["White noise", "Trend", "Seasonal", "Trend + seasonal"])
    ax.set(ylabel="Empirical marginal coverage", ylim=(0, 1.05))
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "browser-family-coverage.pdf")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    for method, label, color in zip(methods, labels, colors):
        ax.plot(range(1, 13), results["per_lead_coverage"][method], marker="o", markersize=3, label=label, color=color)
    ax.axhline(.8, color="black", linestyle="--", linewidth=1, label="Nominal 80%")
    ax.set(xlabel="Forecast lead", ylabel="Empirical marginal coverage", xticks=range(1, 13), ylim=(.7, 1.01))
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "browser-lead-coverage.pdf")
    plt.close(fig)
    scores = {name: [] for name in methods}
    for record in forecasts:
        actual, scale = np.asarray(record["actual"]), record["scale"]
        for name in methods:
            prediction = record["methods"][name]
            lo, hi = np.asarray(prediction["lower"]), np.asarray(prediction["upper"])
            scores[name].append(float(np.mean((hi - lo + 10 * np.maximum(lo - actual, 0)
                                              + 10 * np.maximum(actual - hi, 0)) / scale)))
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    for control, label, color in [("gaussian", "Stratified minus Gaussian", colors[0]),
                                  ("global", "Stratified minus global", colors[1])]:
        delta = np.sort(np.asarray(scores["stratified"]) - scores[control])
        ax.step(delta, np.arange(1, len(delta) + 1) / len(delta), where="post", label=label, color=color)
    ax.axvline(0, color="black", linewidth=1, linestyle="--")
    ax.set(xlabel="Paired series difference in normalized interval score", ylabel="Empirical cumulative fraction", ylim=(0, 1.01))
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output / "browser-paired-scores.pdf")
    plt.close(fig)
    print("Four source-computed browser calibration figures written")


if __name__ == "__main__":
    main()
