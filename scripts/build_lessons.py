"""Author the bilingual worked lessons from reviewed prose and real method calls.

Execution and outputs belong to run_notebooks.py, never this authoring step.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "01-forecast-decisions"
NAMES = ("01-baseline", "02-seasonal-phase", "03-model-comparison", "04-context-memory")
SOURCES = ["https://doi.org/10.1016/j.ijforecast.2006.03.001",
           "https://robjhyndman.com/papers/Theta.pdf",
           "https://otexts.com/fpp3/holt-winters.html",
           "https://doi.org/10.1016/j.ijforecast.2019.02.011",
           "https://doi.org/10.1007/s10994-018-05774-y"]
SETUP = '''# Configure a portable lesson session; no data are downloaded.
from pathlib import Path
import sys
import json
import warnings
import numpy as np
import matplotlib.pyplot as plt
root = next(p for p in Path.cwd().parents if (p / "product.json").is_file())
sys.path.insert(0, str(root / "data-pipeline"))
from chronoscopelab.model.forecasters import seasonal_naive, ses, holt, holt_winters, theta
from chronoscopelab.model.forecasters import gaussian_quantiles
from chronoscopelab.model.context_memory import fit_context_memory
from chronoscopelab.reevaluation import metrics
from chronoscopelab.engines.statsforecast_engine import StatsforecastForecaster
from chronoscopelab.engines.lightgbm_engine import LightGBMForecaster
plt.rcParams.update({"figure.figsize": (8, 3), "figure.dpi": 95, "font.size": 10})
plt.rcParams["svg.hashsalt"] = "chronoscope-lessons"
import importlib.metadata
packages = ("numpy", "scipy", "matplotlib", "statsforecast", "lightgbm", "mlforecast",
            "nbformat", "nbclient", "ipykernel")
for package in packages:
    print(package, importlib.metadata.version(package))
'''
DATA = '''# The committed trace separates available history from the unseen final block.
trace = json.loads((root / "data/derived/TRND_seasonal/trace.json").read_text())
history = np.array(trace["history"], dtype=float)
actual = np.array(trace["actual"], dtype=float)
m, h = trace["seasonality"], trace["horizon"]
comparison = json.loads((root / "data/derived/reevaluation.json").read_text())
print("History:", len(history), "Season:", m, "Holdout:", h)
'''
CODES = {
    "setup": SETUP, "data": DATA,
    "naive": '''# Repeat the final observed season without using actual in fitting.
naive, naive_sigma = seasonal_naive(history, m, h)
naive_q = gaussian_quantiles(naive, naive_sigma, (0.1, 0.5, 0.9))
print("SeasonalNaive first prediction:", round(float(naive[0]), 4))
''',
    "theta": '''# Fit the finite-history Theta implementation on the same prefix.
theta_point, theta_sigma = theta(history, m, h)
theta_q = gaussian_quantiles(theta_point, theta_sigma, (0.1, 0.5, 0.9))
print("Theta first prediction:", round(float(theta_point[0]), 4))
''',
    "holt": '''# A trend-only forecast is a useful deliberately mismatched comparator.
holt_point, holt_sigma = holt(history, m, h)
print("Holt first prediction:", round(float(holt_point[0]), 4))
''',
    "baseline_scores": '''# Score the same future block with one historical seasonal scale.
scores_naive = metrics(history, actual, naive, naive_q[:, 0], naive_q[:, 2], m)
scores_theta = metrics(history, actual, theta_point, theta_q[:, 0], theta_q[:, 2], m)
print("SeasonalNaive MASE:", round(scores_naive["mase"], 4))
print("Theta MASE:", round(scores_theta["mase"], 4))
''',
    "baseline_plot": '''# Plot the observed cut and both competing paths on a shared vertical scale.
fig, ax = plt.subplots()
x = np.arange(len(history), len(history) + h)
ax.plot(np.arange(len(history))[-60:], history[-60:], label="history")
ax.plot(x, actual, label="actual", color="black")
ax.plot(x, naive, label="SeasonalNaive")
ax.plot(x, theta_point, label="Theta")
ax.axvline(len(history) - 1, color="grey", linestyle="--")
ax.set(xlabel="Observation index", ylabel="Series value")
ax.legend(ncol=4, fontsize=8)
fig.tight_layout()
plt.show()
''',
    "partial": '''# Remove five known observations to create an incomplete terminal season.
short = history[:-5]
short_actual = np.concatenate((history[-5:], actual))[:h]
hw_point, hw_sigma = holt_winters(short, m, h)
full_hw, full_sigma = holt_winters(history, m, h)
print("Removed observations:", len(history) - len(short))
print("Partial history remainder:", len(short) % m)
print("Forecast horizon:", h)
''',
    "phase_baseline": '''# Refit the seasonal reference and Theta at the earlier origin as well.
short_naive, short_sigma = seasonal_naive(short, m, h)
short_theta, short_theta_sigma = theta(short, m, h)
short_q = gaussian_quantiles(hw_point, hw_sigma, (0.1, 0.5, 0.9))
print("HoltWinters first prediction:", round(float(hw_point[0]), 4))
''',
    "phase_scores": '''# The earlier-origin target is different, so its scores form a separate experiment.
short_score = metrics(short, short_actual, hw_point, short_q[:, 0], short_q[:, 2], m)
print("Earlier-origin MASE:", round(short_score["mase"], 4))
print("Earlier-origin coverage:", round(short_score["coverage"], 4))
''',
    "phase_plot": '''# Display phase alignment around the deliberately shifted origin.
fig, ax = plt.subplots()
x = np.arange(len(short), len(short) + h)
ax.plot(np.arange(len(short))[-36:], short[-36:], label="history")
ax.plot(x, short_actual, color="black", label="actual")
ax.plot(x, hw_point, label="HoltWinters")
ax.plot(x, short_naive, label="SeasonalNaive")
ax.set(xlabel="Observation index", ylabel="Series value")
ax.legend(ncol=4, fontsize=8)
fig.tight_layout()
plt.show()
''',
    "phase_errors": '''# Inspect errors by lead; an average can hide phase-specific failures.
short_naive_q = gaussian_quantiles(short_naive, short_sigma, (0.1, 0.5, 0.9))
short_naive_score = metrics(short, short_actual, short_naive, short_naive_q[:, 0], short_naive_q[:, 2], m)
fig, ax = plt.subplots()
ax.plot(np.arange(1, h + 1), np.abs(short_actual - hw_point), label="HoltWinters")
ax.plot(np.arange(1, h + 1), np.abs(short_actual - short_naive), label="SeasonalNaive")
ax.set(xlabel="Forecast lead", ylabel="Absolute error")
ax.legend()
fig.tight_layout()
plt.show()
print("Seasonal reference MASE:", round(short_naive_score["mase"], 4))
''',
    "ets": '''# Run the actual installed reference adapter, with the released ETS settings.
ets = StatsforecastForecaster("AutoETS", "ets", max_windows=12)
with warnings.catch_warnings(record=True) as notices:
    warnings.filterwarnings("ignore", message="IProgress not found.*")
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    ets_q = ets.quantiles(history, m, h, (0.1, 0.5, 0.9))
print("AutoETS runtime notices:", [str(w.message) for w in notices])
print("AutoETS MASE:", round(metrics(history, actual, ets_q[:, 1], ets_q[:, 0], ets_q[:, 2], m)["mase"], 4))
''',
    "auto_theta": '''# AutoTheta is a reference implementation distinct from the local Theta equation.
auto_theta = StatsforecastForecaster("AutoTheta", "theta", max_windows=12)
auto_theta_q = auto_theta.quantiles(history, m, h, (0.1, 0.5, 0.9))
print("AutoTheta first prediction:", round(float(auto_theta_q[0, 1]), 4))
''',
    "arima": '''# Fit the bounded stepwise, approximate AutoARIMA configuration.
arima = StatsforecastForecaster("AutoARIMA", "arima", max_windows=3, ctx_cap=360)
with warnings.catch_warnings(record=True) as notices:
    warnings.simplefilter("always")
    arima_q = arima.quantiles(history, m, h, (0.1, 0.5, 0.9))
print("AutoARIMA runtime notices:", sorted(set(str(w.message) for w in notices)))
print("AutoARIMA first prediction:", round(float(arima_q[0, 1]), 4))
''',
    "tree": '''# Run the point-regression lag-tree adapter, not a quantile-regression substitute.
tree = LightGBMForecaster()
tree_q = tree.quantiles(history, m, h, (0.1, 0.5, 0.9))
print("LightGBM MASE:", round(metrics(history, actual, tree_q[:, 1], tree_q[:, 0], tree_q[:, 2], m)["mase"], 4))
''',
    "reference_plot": '''# Compare freshly executed adapters and the historical seasonal reference.
naive, naive_sigma = seasonal_naive(history, m, h)
fig, ax = plt.subplots()
ax.plot(actual, color="black", label="actual")
for label, q in (("AutoETS", ets_q), ("AutoTheta", auto_theta_q), ("AutoARIMA", arima_q), ("LightGBM", tree_q)):
    ax.plot(q[:, 1], label=label)
ax.plot(naive, label="SeasonalNaive", linestyle="--")
ax.set(xlabel="Zero-based lead", ylabel="Series value")
ax.legend(ncol=3, fontsize=8)
fig.tight_layout()
plt.show()
''',
    "frozen_scores": '''# Recompute scores of released neural and pretrained paths without claiming refits.
frozen = [row for row in trace["methods"] if row["name"] in
          ("NLinear", "DLinear", "NHITS", "NLinear (nf)", "DLinear (nf)", "NHITS (nf)",
           "Chronos-Bolt", "Chronos-2", "TimesFM-2.5", "TiRex-2")]
frozen_scores = [(row["name"], metrics(history, actual, row["point"], row["lower"], row["upper"], m))
                 for row in frozen]
for name, score in frozen_scores:
    print(name, "MASE", round(score["mase"], 4), "coverage", round(score["coverage"], 4))
''',
    "frozen_plot": '''# A score-width view preserves the point/interval tradeoff on this one case.
fig, ax = plt.subplots()
for name, score in frozen_scores:
    ax.scatter(score["mase"], score["mean_width"])
    ax.annotate(name, (score["mase"], score["mean_width"]), fontsize=7)
ax.set(xlabel="Final-block MASE", ylabel="Mean interval width")
fig.tight_layout()
plt.show()
''',
    "context": '''# Fit the fixed context kernel using only completed targets within the history.
context_fit = fit_context_memory(history, m, h, mode="context")
print("Completed training origins:", len(context_fit.origins))
print("Latest training target ends:", max(context_fit.origins) + h)
print("Available history ends:", len(history))
''',
    "recency": '''# Remove context similarity while retaining the expert set and recency rule.
recency_fit = fit_context_memory(history, m, h, mode="recency")
print("Recency weights:", np.round(recency_fit.weights, 4))
''',
    "uniform": '''# The equal-weight ablation removes estimated loss preferences as well.
uniform_fit = fit_context_memory(history, m, h, mode="uniform")
print("Equal weights:", np.round(uniform_fit.weights, 4))
''',
    "weight_plot": '''# Associate weights with expert identities rather than an unlabeled vector.
from chronoscopelab.model.context_memory import EXPERT_NAMES
fig, ax = plt.subplots()
x = np.arange(len(EXPERT_NAMES))
ax.bar(x - 0.2, context_fit.weights, width=0.2, label="ContextMemory")
ax.bar(x, recency_fit.weights, width=0.2, label="RecencyMean")
ax.bar(x + 0.2, uniform_fit.weights, width=0.2, label="EqualMean")
ax.set_xticks(x, EXPERT_NAMES)
ax.set(ylabel="Convex expert weight")
ax.legend(fontsize=8)
fig.tight_layout()
plt.show()
''',
    "context_scores": '''# Evaluate the ablations against the same target and the same history scale.
for name, fit in (("ContextMemory", context_fit), ("RecencyMean", recency_fit), ("EqualMean", uniform_fit)):
    q = fit.quantiles
    score = metrics(history, actual, q[:, 1], q[:, 0], q[:, 2], m)
    print(name, "case MASE", round(score["mase"], 4))
''',
    "affine": '''# Changing units should preserve the context rule's convex weights.
converted = fit_context_memory(history * 10 + 100, m, h, mode="context")
print("Maximum weight change after unit conversion:", f"{np.max(np.abs(converted.weights - context_fit.weights)):.8f}")
''',
    "proposal_plot": '''# Read the already fixed fifteen-case experiment, without tuning to its outcomes.
names = ["ContextMemory", "RecencyMean", "EqualMean"]
means = [next(row["mean_mase"] for row in comparison["summary"] if row["name"] == name) for name in names]
fig, ax = plt.subplots()
ax.bar(names, means)
ax.set(ylabel="Mean MASE across fifteen final blocks")
fig.tight_layout()
plt.show()
for name, value in zip(names, means, strict=True):
    print(name, "mean MASE", f"{value:.4f}")
''',
}


def main():
    pins = [s for s in (ROOT / "notebooks/requirements.txt").read_text().splitlines() if s and not s.startswith("#")]
    for lang in ("en", "es"):
        index = []
        for level, name in enumerate(NAMES, 1):
            text = (ROOT / f"docs/lessons/{lang}/{name}.md").read_text(encoding="utf-8")
            text = text.replace("{{PINS}}", "\n".join(f"pip install {pin}" for pin in pins))
            cells = []
            pieces = re.split(r"<!-- code: ([a-z_]+) -->", text)
            for i, piece in enumerate(pieces):
                cell_type = "markdown" if i % 2 == 0 else "code"
                source = piece.strip() if cell_type == "markdown" else CODES[piece].strip()
                if not source:
                    continue
                cell = {"cell_type": cell_type, "id": hashlib.sha256(f"{name}/{len(cells)}".encode()).hexdigest()[:12],
                        "metadata": {}, "source": source + "\n"}
                if cell_type == "code":
                    cell.update(execution_count=None, outputs=[])
                cells.append(cell)
            title = text.splitlines()[0].lstrip("# ")
            meta = {"language": lang, "topic": TOPIC, "level": level, "title": title,
                    "packages": pins, "data": ["data/derived/TRND_seasonal/trace.json", "data/derived/reevaluation.json"],
                    "sources": SOURCES, "beyond": ["BS-1"] if level == 4 else []}
            if level == 3:
                meta["methods"] = ["ST-1", "ST-2", "ST-3", "ST-4"]
            doc = {"nbformat": 4, "nbformat_minor": 5, "metadata": {"caos": meta,
                   "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python"}}, "cells": cells}
            path = ROOT / f"notebooks/{lang}/{TOPIC}/{name}.ipynb"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            index.append(f"| {level} | [{title}]({TOPIC}/{name}.ipynb) |")
        heading = "Forecast decisions" if lang == "en" else "Decisiones de pronóstico"
        (ROOT / f"notebooks/{lang}/README.md").write_text(
            f"# {heading}\n\n| Level | Lesson |\n|---|---|\n" + "\n".join(index) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
