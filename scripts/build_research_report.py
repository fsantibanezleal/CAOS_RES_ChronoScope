"""Generate report tables and scientific figures from admitted research artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "manuscripts/product-report"


def load(name):
    return json.loads((ROOT / "data/derived" / name).read_text(encoding="utf-8"))


def text(name, content):
    (REPORT / "tables" / name).write_text(content + "\n", encoding="utf-8", newline="\n")


def save(name, fig):
    fig.tight_layout()
    fig.savefig(REPORT / "figures" / name, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def main():
    from check_research_extensions import validate_diagnostics, validate_study

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study",type=Path,default=ROOT/"data/derived/forecastability.json")
    args = parser.parse_args()
    study = json.loads(args.study.read_text(encoding="utf-8"))
    validate_diagnostics()
    validate_study(study, statistics_check=True)
    summary = study["summary"]
    scores = summary["selection_mean_mase"]
    plt.rcParams.update({"font.size": 10, "figure.figsize": (8, 3.6), "pdf.fonttype": 42})

    original = load("BRKV_level_shift/analysis.json")["sequence"]
    profile = original["matrix_profile"]
    fig, axes = plt.subplots(3, 1, figsize=(8, 7))
    axes[0].plot(original["values"], color="#1264a3", linewidth=1)
    for motif in profile["motifs"]:
        for start in (motif["start"], motif["match"]):
            axes[0].axvspan(start, start + profile["window"] - 1, color="#16813d", alpha=0.3)
    for discord in profile["discords"]:
        axes[0].axvspan(
            discord["start"], discord["start"] + profile["window"] - 1, color="#aa6a00", alpha=0.3
        )
    axes[0].set(xlabel="Original observation index", ylabel="Value")
    axes[1].plot(profile["profile"], color="#06778b")
    axes[1].set(xlabel="Window start", ylabel="Normalized distance")
    axes[2].plot(profile["corrected_arc_curve"], color="#aa2678")
    axes[2].set(xlabel="Window start", ylabel="Corrected arc fraction")
    for axis in (axes[0], axes[2]):
        for boundary in profile["regime_boundaries"]:
            axis.axvline(boundary, linestyle="--", color="#855100", linewidth=1)
    save("sequence-patterns.pdf", fig)

    entropy = original["multiscale_entropy"]["scales"]
    fig, axis = plt.subplots()
    axis.plot([r["scale"] for r in entropy], [r["entropy"] for r in entropy], "o-", color="#16813d")
    axis.set(xlabel="Coarse-graining scale", ylabel="Sample entropy (nats)")
    save("sequence-entropy.pdf", fig)

    fig, axis = plt.subplots()
    axis.bar(
        ["Fixed selector", summary["constant_method"] + " constant", "Future-informed oracle"],
        [scores["selected"], scores["discovery_constant"], scores["oracle"]],
        color=["#1264a3", "#aa6a00", "#16813d"],
    )
    axis.set(ylabel="Confirmation mean MASE")
    save("corpus-selection.pdf", fig)

    n_confirmed = sum(r["confirmed"] for r in summary["associations"])
    difference = scores["selected"] - scores["discovery_constant"]
    direction = "higher" if difference > 0 else "lower"
    body = (
        f"The complete source contains {study['source_n']:,} identities; {study['included_n']:,} are admitted "
        f"and {len(study['excluded']):,} {'is' if len(study['excluded']) == 1 else 'are'} explicitly excluded. The deterministic partitions contain "
        f"{summary['discovery_n']:,} discovery and {summary['confirmation_n']:,} confirmation series. "
        f"Of forty tested features, {n_confirmed} meet the fixed two-partition confirmation rule. "
        f"The discovery-selected constant is {summary['constant_method']}. On confirmation series, the fixed "
        f"selector has mean MASE {scores['selected']:.4f}, the constant {scores['discovery_constant']:.4f}, "
        f"and the future-informed oracle {scores['oracle']:.4f}. The selector's error is {abs(difference):.4f} "
        f"{direction} than the constant on this fixed split. This descriptive outcome is not a significance "
        "test of selection benefit. The oracle uses future outcomes and cannot be deployed as a selection policy.\n\n"
    )
    if study["excluded"]:
        reasons = {}
        for row in study["excluded"]:
            reason = row["excluded"].split(" of ")[0]
            reasons[reason] = reasons.get(reason, 0) + 1
        body += (
            "Exclusions by reason: " + "; ".join(f"{k}: {v}" for k, v in sorted(reasons.items())) + ".\n\n"
        )
    body += "\\begin{center}\\begin{tabular}{lr}\n\\toprule Confirmation method & Mean MASE\\\\\\midrule\n"
    body += "\n".join(
        f"{name} & {value:.4f} \\\\"
        for name, value in sorted(summary["model_mean_mase"].items(), key=lambda r: r[1])
    )
    body += "\n\\bottomrule\\end{tabular}\\end{center}"
    text("corpus-summary.tex", body)

    lines = [
        r"\begingroup\footnotesize\setlength{\tabcolsep}{3pt}",
        r"\begin{longtable}{p{.35\textwidth}rrrrrr}",
        r"\caption{All forty preregistered features. D/C denote discovery/confirmation. Signed Kendall effects, BY-adjusted probabilities and the fixed confirmation decision are retained, including negative outcomes. Available counts and raw probabilities are in the public artifact.}\\",
        r"\toprule Feature & $n_D$ & $\tau_D$ & $q_D$ & $n_C$ & $\tau_C$ & $q_C$\\\midrule\endhead",
    ]
    for row in summary["associations"]:
        d, c = row["discovery"], row["confirmation"]
        name = r"\nolinkurl{" + row["feature"] + "}"
        marker = r"\textsuperscript{*}" if row["confirmed"] else ""
        lines.append(
            f"\\raggedright {name}{marker} & {d['n']} & {d['tau']:.3f} & {d['q']:.2g} & {c['n']} & {c['tau']:.3f} & {c['q']:.2g} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule\end{longtable}",
            r"* Rejected at BY $q\leq0.05$ in both partitions with the same effect direction.\endgroup",
        ]
    )
    text("corpus-associations.tex", "\n".join(lines))

    fresh, archive = load("fresh-reevaluation.json"), load("reevaluation.json")
    archived = {r["name"]: r for r in archive["summary"]}
    rows = [
        r"\begin{longtable}{lrrr}",
        r"\caption{Fresh execution alongside the archived-path comparison. The same fifteen final blocks are used in both; these are not independent replications.}\\",
        r"\toprule Method & Archived MASE & Fresh MASE & Fresh coverage\\\midrule\endhead",
    ]
    for row in sorted(fresh["summary"], key=lambda r: r["mean_mase"]):
        rows.append(
            f"{row['name']} & {archived[row['name']]['mean_mase']:.4f} & {row['mean_mase']:.4f} & {row['mean_coverage']:.4f} \\\\"
        )
    text("fresh.tex", "\n".join([*rows, r"\bottomrule\end{longtable}"]))

    inputs = (
        "forecastability.json",
        "fresh-reevaluation.json",
        "reevaluation.json",
        "BRKV_level_shift/analysis.json",
    )
    receipt = {
        "inputs": {
            "data/derived/" + p: hashlib.sha256((args.study if p == "forecastability.json" else ROOT / "data/derived" / p).read_bytes()).hexdigest()
            for p in inputs
        },
        "generator": "scripts/build_research_report.py",
        "confirmed_features": n_confirmed,
    }
    (REPORT / "research-tables.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
