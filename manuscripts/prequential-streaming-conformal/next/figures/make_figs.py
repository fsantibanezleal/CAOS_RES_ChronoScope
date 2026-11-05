"""Deterministically generate figures from the complete numerical replay.
Run with the figures venv (matplotlib). Outputs vector PDFs next to this file."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DER = HERE.parents[2] / "data" / "derived"
EVIDENCE = json.loads((HERE.parent / "evidence/replay.json").read_text(encoding="utf-8"))
NAVY, BLUE, ORANGE, GREEN, GRAY, INK = "#1a365d", "#2b6cb0", "#c05621", "#2f855a", "#718096", "#1a202c"
STYLE = {"SeasonalNaive": (GRAY, ":"), "Theta": (ORANGE, "-"), "Theta+ACI": (BLUE, "-"), "Theta+PID": (GREEN, "--")}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#4a5568", "axes.linewidth": 0.8})


def load(case):
    return json.loads((DER / case / "streaming.json").read_text(encoding="utf-8"))


# ---- Fig 1: final coverage per method across all cases (raw spread vs calibrated at nominal) ----
def fig_percase():
    order = ["SeasonalNaive", "Theta", "Theta+ACI", "Theta+PID"]
    labels = ["Seasonal\nnaive", "S+D\n(raw)", "S+D\nACI-style", "S+D\nPID-style"]
    nom = 0.8; pts = {k: [] for k in order}
    for d in EVIDENCE["cases"]:
        for mn in order:
            m = d["methods"].get(mn)
            if m:
                pts[mn].append(m["final_coverage"])
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    ax.axhline(nom, color=INK, lw=1.2, ls="--", zorder=2, label="nominal 80%")
    for i, mn in enumerate(order):
        v = pts[mn]; c = STYLE[mn][0]
        jit = [(-1) ** j * 0.06 * (j % 3) for j in range(len(v))]
        ax.scatter([i + jx for jx in jit], v, s=34, color=c, edgecolor="w", lw=0.5, zorder=3, alpha=0.9)
        band = max(v) - min(v)
        ax.plot([i - 0.28, i + 0.28], [sum(v) / len(v)] * 2, color=c, lw=2.2, zorder=4)
        ax.text(i, 1.02, f"span {band:.2f}", ha="center", fontsize=7, color=c)
    ax.set_xticks(range(len(order))); ax.set_xticklabels(labels, fontsize=8)
    # Two-line axis label: on one line it is taller than the axes and is clipped.
    ax.set_ylim(0, 1.08); ax.set_ylabel("Final empirical coverage\n(one point per case)")
    ax.set_title("All fifteen cases, including the lowest-coverage case", fontsize=8.8)
    ax.legend(fontsize=7, loc="lower left", framealpha=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "fig-coverage-percase.pdf", metadata={"CreationDate": None, "ModDate": None}); plt.close(fig)


# ---- Fig 2: mean absolute coverage error per method across all cases (the headline) ----
def fig_summary():
    order = ["SeasonalNaive", "Theta", "Theta+ACI", "Theta+PID"]
    labels = ["Seasonal naive", "S+D (raw)", "S+D + ACI-style", "S+D + PID-style"]
    fig, ax = plt.subplots(figsize=(5.3, 3.4))
    for offset, key, label, color in [(-.18, "rolling_summary_error", "Absolute error after time averaging", BLUE),
                                      (.18, "mean_rolling_absolute_error", "Time average of rolling absolute error", ORANGE)]:
        values = [EVIDENCE["summary"][k][key] for k in order]
        positions = [i + offset for i in range(4)]
        ax.barh(positions, values, height=.31, color=color, label=label)
        for y, value in zip(positions, values):
            ax.text(value + .002, y, f"{value:.4f}", va="center", fontsize=8)
    ax.set_yticks(range(4)); ax.set_yticklabels(labels); ax.invert_yaxis()
    ax.set_xlim(0, .16)
    ax.set_xlabel("Coverage error at nominal 80% (15 equal-weight cases)")
    ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(.45, 1.2), frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "fig-coverage-summary.pdf", metadata={"CreationDate": None, "ModDate": None}); plt.close(fig)


if __name__ == "__main__":
    fig_percase(); fig_summary()
    print("figures written:", [p.name for p in sorted(HERE.glob("*.pdf"))])
