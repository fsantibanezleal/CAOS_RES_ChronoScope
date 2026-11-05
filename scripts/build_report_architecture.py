"""Render the documented offline-to-browser data flow for the working report."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    fig, ax = plt.subplots(figsize=(10, 4.6), layout="constrained")
    ax.set(xlim=(0, 10), ylim=(0, 4.6))
    ax.axis("off")
    boxes = [
        (0.1, 2.9, "Admitted source", "CSV or seeded generator\nmanifest and original indices"),
        (3.55, 2.9, "Offline calculation", "prefix-only fit; reserved targets\nmethod and runtime identity"),
        (6.9, 2.9, "Candidate admission", "schemas; reconstruction\nindependent numerical checks"),
        (6.9, 0.55, "Explicit promotion", "complete inventory\nsource and payload bindings"),
        (3.55, 0.55, "Static delivery", "indexes and per-series JSON\nONNX graph and calibration"),
        (0.1, 0.55, "Shared browser source", "case/configuration ownership\nExplore and six guided views"),
    ]
    for x, y, title, detail in boxes:
        ax.add_patch(FancyBboxPatch((x, y), 2.95, 1.25, boxstyle="round,pad=0.06", facecolor="#f2f6fa", edgecolor="#32536b"))
        ax.text(x + 1.475, y + 0.92, title, ha="center", va="center", fontsize=11, weight="bold", color="#183247")
        ax.text(x + 1.475, y + 0.43, detail, ha="center", va="center", fontsize=9, linespacing=1.5, color="#183247")
    for start, end in [((3.08, 3.53), (3.47, 3.53)), ((6.53, 3.53), (6.82, 3.53)), ((8.38, 2.82), (8.38, 1.88)), ((6.82, 1.18), (6.53, 1.18)), ((3.47, 1.18), (3.08, 1.18))]:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=14, linewidth=1.4, color="#32536b"))
    ax.text(0.1, 0.06, "Schematic of responsibilities; no active request-time Python prediction service.", fontsize=9, color="#32536b")
    out = ROOT / "manuscripts/product-report/next/figures/architecture.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
