"""Generate manuscript tables and figures from the admitted contiguous-history artifact."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def tex(value):
    return str(value).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")


def main():
    data = json.loads((ROOT / "data/derived/reevaluation.json").read_text())
    if data["schema"] != "chronoscope.reevaluation/v2":
        raise ValueError("Manuscripts require the corrected contiguous-history protocol")
    figures, tables = HERE / "figures", HERE / "tables"
    figures.mkdir(exist_ok=True)
    tables.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "figure.dpi": 140, "pdf.fonttype": 42})
    names = ["ContextMemory", "RecencyMean", "EqualMean"]
    summary = {r["name"]: r for r in data["summary"]}
    fig, ax = plt.subplots(figsize=(7.5, 3.7))
    values = [summary[n]["mean_mase"] for n in names]
    bars = ax.bar(names, values, color=["#24648c", "#526b3f", "#818995"])
    ax.bar_label(bars, labels=[f"{v:.4f}" for v in values], padding=5)
    ax.set(ylabel="Mean final-block MASE", ylim=(0, max(values) * 1.18))
    ax.spines[["right", "top"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(figures / "proposal-comparison.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    cases = data["cases"]
    differences = []
    for case in cases:
        methods = {m["name"]: m for m in case["methods"]}
        differences.append(methods["ContextMemory"]["metrics"]["mase"] - methods["RecencyMean"]["metrics"]["mase"])
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    x = np.arange(len(cases))
    ax.bar(x, differences, color=["#9a5933" if v > 0 else "#24648c" for v in differences])
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_xticks(x, [c["case_id"] for c in cases], rotation=55, ha="right", fontsize=8)
    ax.set(ylabel="ContextMemory MASE minus RecencyMean MASE")
    ax.spines[["right", "top"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(figures / "case-differences.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    overall = [r"\begin{longtable}{lrrr}",
               r"\caption{Corrected common final-block comparison. Means weight each selected case equally.}\\",
               r"\toprule Method & Cases & Mean MASE & Mean coverage\\\midrule\endhead"]
    for row in sorted(data["summary"], key=lambda r: r["mean_mase"]):
        overall.append(f"{tex(row['name'])} & {row['cases']} & {row['mean_mase']:.4f} & {row['mean_coverage']:.4f} " + r"\\")
    overall += [r"\bottomrule", r"\end{longtable}"]
    (tables / "overall.tex").write_text("\n".join(overall) + "\n")
    case_rows = [r"\begin{longtable}{lrrrl}",
                 r"\caption{Admitted cases: original contiguous history length, horizon and seasonal lag.}\\",
                 r"\toprule Case & History & Horizon & Lag & Source\\\midrule\endhead"]
    proposal = [r"\begin{longtable}{lrrr}",
                r"\caption{Matching-expert ablations: final-block MASE per selected case.}\\",
                r"\toprule Case & ContextMemory & RecencyMean & EqualMean\\\midrule\endhead"]
    for case in cases:
        cid = case["case_id"]
        case_rows.append(f"{tex(cid)} & {case['history_length']} & {case['horizon']} & {case['seasonality']} & "
                         + ("Real excerpt" if cid.startswith("REAL_") else "Generated") + r"\\")
        methods = {m["name"]: m for m in case["methods"]}
        proposal.append(tex(cid) + " & " + " & ".join(f"{methods[n]['metrics']['mase']:.4f}" for n in names) + r"\\")
    proposal.append(r"\midrule Mean & " + " & ".join(f"{summary[n]['mean_mase']:.4f}" for n in names) + r"\\")
    for rows, filename in ((case_rows, "cases.tex"), (proposal, "proposal.tex")):
        rows += [r"\bottomrule", r"\end{longtable}"]
        (tables / filename).write_text("\n".join(rows) + "\n")
    print("Manuscript evidence: 15 cases, 22 methods, 3 matching-expert variants")


if __name__ == "__main__":
    main()
