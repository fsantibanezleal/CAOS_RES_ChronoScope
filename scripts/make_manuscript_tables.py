"""Generate manuscript tables from the full numerical replay, retaining all settings."""
from collections import defaultdict
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "manuscripts/prequential-streaming-conformal"
LABELS = {"SeasonalNaive": "Seasonal naive", "Theta": "S+D", "Theta+ACI": "S+D + ACI-style", "Theta+PID": "S+D + PID-style"}


def table(caption, headings, rows):
    return "\n".join([r"\begin{table}[htbp]\centering\footnotesize", "\\caption{" + caption + "}",
                      r"\begin{tabular}{l" + "r" * (len(headings) - 1) + "}", r"\toprule",
                      " & ".join(headings) + r"\\\midrule", *[" & ".join(row) + r"\\" for row in rows],
                      r"\bottomrule\end{tabular}\end{table}", ""])


def main():
    x = json.loads((HERE / "evidence/replay.json").read_text(encoding="utf-8"))
    dest = HERE / "tables"
    dest.mkdir(exist_ok=True)
    rows = [[LABELS[n], *[f"{x['summary'][n][k]:.4f}" for k in ("rolling_summary_error", "mean_rolling_absolute_error", "final_absolute_coverage_error")]] for n in LABELS]
    (dest / "coverage.tex").write_text(table("Coverage errors on the same fifteen cases at nominal 80\\%. The three columns are distinct statistics defined in the text; none is a confidence interval.", ["Method", "$E_{\\rm avg}$", "$E_{\\rm roll}$", "$E_{\\rm final}$"], rows), encoding="utf-8")
    rows = []
    for n in LABELS:
        scaled = []
        for c in x["cases"]:
            y = np.array(c["source_values"][:c["warmup"]])
            m = c["seasonality"]
            scale = np.mean(abs(y[m:] - y[:-m]))
            scaled.append([c["methods"][n][k] / scale for k in ("mean_width", "mean_interval_score")])
        rows.append([LABELS[n], *[f"{v:.4f}" for v in np.mean(scaled, axis=0)]])
    (dest / "efficiency.tex").write_text(table("Interval width and interval score divided by each case's warmup seasonal-difference scale, then averaged equally over cases. Lower interval score is better; smaller width alone is not.", ["Method", "Scaled width", "Scaled score"], rows), encoding="utf-8")
    groups = defaultdict(list)
    for row in x["sensitivity"]:
        groups[row["base"], row["coverage"], row["controller"], row["gain"]].append(row["mean_rolling_absolute_error"])
    rows = []
    for base in ("SeasonalNaive", "Theta"):
        for coverage in (.7, .8, .9):
            cells = [LABELS[base], f"{coverage:.1f}", f"{np.mean(groups[base,coverage,'raw',1.]):.4f}"]
            for controller in ("ACI", "PID"):
                values = [np.mean(groups[base, coverage, controller, gain]) for gain in (.5, 1., 2.)]
                cells.append(f"{min(values):.4f}--{max(values):.4f}")
            rows.append(cells)
    (dest / "sensitivity.tex").write_text(table("Mean rolling absolute error across fifteen cases. Controller cells give the range of the three fixed gain multipliers (0.5, 1, 2), not sampling uncertainty or a selected optimum.", ["Base", "$c$", "Raw", "ACI-style", "PID-style"], rows), encoding="utf-8")
    rows = []
    for seed in (42, 43, 44):
        cells = [str(seed)]
        for controller in ("raw", "ACI", "PID"):
            if seed == 42:
                name = "Theta" if controller == "raw" else "Theta+" + controller
                values = [c["methods"][name]["mean_rolling_absolute_error"] for c in x["cases"] if not c["case_id"].startswith("REAL_")]
            else:
                values = [r["mean_rolling_absolute_error"] for r in x["generated_repeats"] if r["seed"] == seed and r["controller"] == controller]
            assert len(values) == 11
            cells.append(f"{np.mean(values):.4f}")
        rows.append(cells)
    (dest / "seeds.tex").write_text(table("S+D base at nominal 80\\%, default gains: mean rolling absolute error on eleven generated mechanisms for each seed. Seeds share generator definitions; real series are excluded from this table.", ["Seed", "Raw", "ACI-style", "PID-style"], rows), encoding="utf-8")
    print("Generated four tables from 15 reproduced cases, 630 sensitivity rows and 66 additional-seed rows.")


if __name__ == "__main__":
    main()
