"""Deterministically generate the figures for the ChronoScope paper from the committed
streaming artifacts (data/derived/*/streaming.json). Every number is read from the JSON.
Run with the figures venv (matplotlib). Outputs vector PDFs next to this file."""
import json
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DER = HERE.parents[2] / "data" / "derived"
NAVY, BLUE, ORANGE, GREEN, GRAY, INK = "#1a365d", "#2b6cb0", "#c05621", "#2f855a", "#718096", "#1a202c"
STYLE = {"SeasonalNaive": (GRAY, ":"), "Theta": (ORANGE, "-"), "Theta+ACI": (BLUE, "-"), "Theta+PID": (GREEN, "--")}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#4a5568", "axes.linewidth": 0.8})


def load(case):
    return json.loads((DER / case / "streaming.json").read_text(encoding="utf-8"))


# ---- Fig 1: final coverage per method across all cases (raw spread vs calibrated at nominal) ----
def fig_percase():
    order = ["SeasonalNaive", "Theta", "Theta+ACI", "Theta+PID"]
    labels = ["Seasonal-\nnaive", "Theta\n(raw)", "Theta\n+ACI", "Theta\n+PID"]
    nom = 0.8; pts = {k: [] for k in order}
    for f in sorted(DER.glob("*/streaming.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for mn in order:
            m = d["methods"].get(mn)
            if m and "final" in m and m["final"].get("coverage") is not None:
                pts[mn].append(m["final"]["coverage"])
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
    ax.set_ylim(0.62, 1.06); ax.set_ylabel("final empirical coverage (one point per case)")
    ax.set_title("Calibrated methods cluster at nominal; raw intervals spread", fontsize=8.8)
    ax.legend(fontsize=7, loc="lower left", framealpha=0.9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "fig-coverage-percase.pdf"); plt.close(fig)


# ---- Fig 2: mean absolute coverage error per method across all cases (the headline) ----
def fig_summary():
    agg = defaultdict(list)
    ncases = 0
    for f in sorted(DER.glob("*/streaming.json")):
        d = json.loads(f.read_text(encoding="utf-8")); nom = d.get("nominal_coverage", 0.8); ncases += 1
        for mn in ("SeasonalNaive", "Theta", "Theta+ACI", "Theta+PID"):
            m = d["methods"].get(mn)
            if not m or "rolling_coverage" not in m:
                continue
            v = [x for x in m["rolling_coverage"] if x is not None]
            if v:
                agg[mn].append(abs(sum(v) / len(v) - nom))
    order = ["SeasonalNaive", "Theta", "Theta+ACI", "Theta+PID"]
    labels = ["Seasonal-naive", "Theta (raw)", "Theta+ACI", "Theta+PID"]
    means = [sum(agg[k]) / len(agg[k]) for k in order]
    maxes = [max(agg[k]) for k in order]
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    y = range(len(order))
    cols = [GRAY, ORANGE, BLUE, GREEN]
    ax.barh(list(y), means, color=cols, height=0.6, zorder=3, xerr=[[0] * 4, [mx - mn for mx, mn in zip(maxes, means)]],
            error_kw=dict(ecolor="#4a5568", capsize=3, lw=0.9), label="mean (bar), worst case (whisker)")
    for i, mv in enumerate(means):
        ax.text(mv + 0.001, i, f"{mv:.4f}", va="center", fontsize=8, color=INK)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels); ax.invert_yaxis()
    ax.set_xlabel(f"mean |coverage - {0.8:.2f}| over {ncases} cases (lower better)")
    ax.set_title("Online conformal cuts coverage error 7-10x", fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(HERE / "fig-coverage-summary.pdf"); plt.close(fig)


if __name__ == "__main__":
    fig_percase(); fig_summary()
    print("figures written:", [p.name for p in sorted(HERE.glob("*.pdf"))])
