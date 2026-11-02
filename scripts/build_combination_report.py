"""Generate complete comparison tables and figures from the admitted study index."""

from pathlib import Path
import json
import hashlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "data/derived/validated-combinations.json"
    index = json.loads(path.read_text(encoding="utf-8"))
    cohorts = {c["id"]: c for c in index["cohorts"]}
    summaries = {key: {r["name"]: r for r in c["summary"]} for key, c in cohorts.items()}
    names = list(summaries["m4_weekly"])
    table = [
        r"\begin{table}[htbp]\centering\small",
        r"\caption{Complete external comparison. W denotes 294 eligible M4 Weekly series; M denotes 1,422 unique M3 Monthly series. MASE and MSIS average origins within series and then series equally; Cov is empirical interval coverage. These are descriptive summaries, not confidence intervals.}",
        r"\begin{tabular}{lrrrrrr}\toprule Method & W MASE & W MSIS & W Cov & M MASE & M MSIS & M Cov\\\midrule",
    ]
    for name in names:
        values = [
            summaries[d][name][k] for d in ("m4_weekly", "m3_monthly") for k in ("mase", "msis", "coverage")
        ]
        table.append(name + " & " + " & ".join(f"{v:.4f}" for v in values) + r"\\")
    table += [r"\bottomrule\end{tabular}\end{table}", ""]
    for target in [
        ROOT / "manuscripts/context-memory/tables/external.tex",
        ROOT / "manuscripts/product-report/tables/validated-combinations.tex",
    ]:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(table), encoding="utf-8", newline="\n")
    selected = ["ContextMemory", "RecencyMean", "EqualMean", "ContextMemoryCV", "ValidationMix", "AutoTheta"]
    plt.rcParams.update({"font.size": 12, "pdf.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.5), layout="constrained")
    for ax, dataset, title in zip(
        axes, ["m4_weekly", "m3_monthly"], ["M4 Weekly (294 series)", "M3 Monthly (1,422 series)"]
    ):
        values = [summaries[dataset][n]["mase"] for n in selected]
        ax.barh(selected, values, color=["#818995", "#526b3f", "#b6a088", "#24648c", "#874b83", "#be6b27"])
        ax.invert_yaxis()
        ax.set(xlabel="Mean series MASE", title=title, xlim=(0, max(values) * 1.23))
        ax.spines[["top", "right"]].set_visible(False)
        for i, v in enumerate(values):
            ax.text(v + max(values) * 0.025, i, f"{v:.4f}", va="center", fontsize=10)
    output = ROOT / "manuscripts/product-report/figures/validated-combinations.pdf"
    fig.savefig(output, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    evidence = {
        "index_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "cohorts": cohorts,
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ROOT / "manuscripts/context-memory/combination-evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        "Generated all-method tables and a fixed-combination/statistical comparison figure for both external collections."
    )


if __name__ == "__main__":
    main()
