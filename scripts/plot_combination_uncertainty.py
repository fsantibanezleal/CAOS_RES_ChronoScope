"""Visualize paired series uncertainty and information order for the revision."""
from __future__ import annotations

import argparse
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
    rows = json.loads((ROOT / "manuscripts/context-memory/evidence/paired-series-uncertainty.json").read_text())["comparisons"]
    lookup = {(r["dataset"], r["metric"], r["method"], r["control"]): r for r in rows}
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 5.4))
    for i, (dataset, title) in enumerate([("m4_weekly", "M4 Weekly"), ("m3_monthly", "M3 Monthly")]):
        for j, metric in enumerate(["mase", "msis"]):
            ax = axes[i, j]
            for method, offset, color in [("ContextMemoryCV", -.09, "#c27803"), ("ValidationMix", .09, "#146a8a")]:
                for y, control in enumerate(["RecencyMean", "AutoTheta"]):
                    row = lookup[dataset, metric, method, control]
                    mean, (lo, hi) = row["difference"], row["percentile_95"]
                    ax.errorbar(mean, y + offset, xerr=[[mean - lo], [hi - mean]], fmt="o", capsize=3,
                                color=color, label=method if y == 0 else None)
            ax.axvline(0, linestyle="--", color="black", linewidth=.8)
            ax.set(yticks=[0, 1], yticklabels=["RecencyMean", "AutoTheta"], title=f"{title}: {metric.upper()}",
                   xlabel="Method minus control; negative favors method", ylim=(-.4, 1.4))
            ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output / "paired-series-intervals.pdf", bbox_inches="tight")
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
    for ax, metric in zip(axes, ["mase", "msis"]):
        labels, fractions = [], []
        for dataset, name in [("m4_weekly", "Weekly"), ("m3_monthly", "Monthly")]:
            for control in ["RecencyMean", "AutoTheta"]:
                row = lookup[dataset, metric, "ValidationMix", control]
                labels.append(f"{name}\n{control}")
                fractions.append([row[k] / row["series"] for k in ("negative", "zero", "positive")])
        values = np.asarray(fractions)
        bottom = np.zeros(4)
        for k, label, color in [(0, "Lower loss", "#146a8a"), (1, "Equal loss", "#b8b0a7"), (2, "Higher loss", "#c27803")]:
            ax.bar(range(4), values[:, k], bottom=bottom, label=label, color=color)
            bottom += values[:, k]
        ax.set(xticks=range(4), xticklabels=labels, ylabel="Fraction of complete series", title=f"ValidationMix: {metric.upper()}", ylim=(0, 1))
        ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(.5, -.23), ncol=3)
    fig.tight_layout()
    fig.savefig(output / "paired-series-directions.pdf", bbox_inches="tight")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9.2, 2.7))
    ax.broken_barh([(0, 5)], (2.8, .5), facecolors="#146a8a")
    ax.broken_barh([(5, 2)], (2.8, .5), facecolors="#c27803")
    ax.broken_barh([(0, 8)], (1.6, .5), facecolors="#146a8a")
    ax.broken_barh([(8, 2)], (1.6, .5), facecolors="#b8b0a7")
    ax.annotate("Historical target fully observed: o + H <= q", xy=(7, 3.1), xytext=(4.3, 4),
                ha="center", arrowprops={"arrowstyle": "->"})
    ax.axvline(8, linestyle="--", color="black", linewidth=.8)
    ax.set(yticks=[3.05, 1.85], yticklabels=["Historical validation origin o", "Current query origin q"],
           xticks=[0, 5, 7, 8, 10], xticklabels=["start", "o", "o + H", "q", "q + H"],
           ylim=(1, 4.5), xlim=(0, 10.2), xlabel="Illustrative information order, not a measured timeline")
    ax.spines[["left", "bottom"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output / "causal-validation-order.pdf", bbox_inches="tight")
    plt.close(fig)
    print("Two computed uncertainty figures and an explicitly illustrative information-order diagram written")


if __name__ == "__main__":
    main()
