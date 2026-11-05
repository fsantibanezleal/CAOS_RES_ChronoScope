"""Post-hoc paired case reweighting of the frozen replay; never a new trial."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "manuscripts/prequential-streaming-conformal"
NEXT = HERE / "next"
METHODS = ("Theta", "Theta+ACI", "Theta+PID")
LABELS = ("S+D", "ACI-style", "PID-style")


def summarize_rows(rows: list, scale: float, coverage: float = .8) -> np.ndarray:
    """Independently derive rolling coverage error and scaled interval score."""
    x = np.asarray(rows, dtype=float)
    if x.ndim != 2 or x.shape[1] != 14 or not len(x):
        raise ValueError("Expected complete fourteen-column forecast rows")
    if not np.isfinite(x[:, :13]).all() or not np.isfinite(scale) or scale <= 0:
        raise ValueError("Finite forecast rows and a positive historical scale required")
    if not 0 < coverage < 1 or np.any(x[:, 2] > x[:, 4]):
        raise ValueError("Invalid coverage or reversed endpoints")
    actual, lower, upper = x[:, 1], x[:, 2], x[:, 4]
    hit = (lower <= actual) & (actual <= upper)
    if not np.array_equal(hit.astype(float), x[:, 12]):
        raise ValueError("Retained hit column disagrees with endpoints")
    # Prefix sums provide an independent route to the archived trailing means.
    cumulative = np.r_[0., np.cumsum(hit)]
    end = np.arange(1, len(hit) + 1)
    start = np.maximum(0, end - 25)
    rolling = np.round((cumulative[end] - cumulative[start]) / (end - start), 5)
    score = upper - lower + 2 / (1 - coverage) * (np.maximum(lower - actual, 0) + np.maximum(actual - upper, 0))
    return np.array([np.mean(abs(rolling - coverage)), np.mean(score) / scale])


def paired_resample(values: np.ndarray, count: int, seed: int) -> np.ndarray:
    """One joint draw of whole-case identities, shared by methods and metrics."""
    if values.ndim != 3 or values.shape[1:] != (3, 2) or not np.isfinite(values).all() or not len(values):
        raise ValueError("Expected finite case by three-method by two-metric array")
    indices = np.random.Generator(np.random.PCG64(seed)).integers(0, len(values), (count, len(values)))
    means = values[indices].mean(axis=1)
    return means[:, 1:] - means[:, :1]


def analyze(source: dict, plan: dict) -> dict:
    cases, values = [], []
    for case in source["cases"]:
        prefix = np.asarray(case["source_values"][:case["warmup"]])
        m = case["seasonality"]
        if not 0 < m < len(prefix):
            raise ValueError("Invalid warmup seasonal lag")
        scale = float(np.mean(abs(prefix[m:] - prefix[:-m])))
        metrics = []
        point = np.asarray(case["methods"]["Theta"]["rows"], dtype=float)[:, 3]
        for method in METHODS:
            record = case["methods"][method]
            if not np.array_equal(point, np.asarray(record["rows"], dtype=float)[:, 3]):
                raise ValueError("An interval controller changed the point forecast")
            metric = summarize_rows(record["rows"], scale)
            np.testing.assert_allclose(metric, [record["mean_rolling_absolute_error"], record["mean_interval_score"] / scale], atol=1e-12, rtol=1e-12)
            metrics.append(metric)
        cases.append(case["case_id"])
        values.append(metrics)
    a = np.asarray(values)
    draws = paired_resample(a, plan["resamples"], plan["seed"])
    rows = []
    for method in range(1, 3):
        for metric, name in enumerate(plan["metrics"]):
            delta = a[:, method, metric] - a[:, 0, metric]
            endpoints = np.quantile(draws[:, method - 1, metric], [.025, .975])
            rows.append({"method": METHODS[method], "metric": name, "reference_mean": float(a[:, 0, metric].mean()), "method_mean": float(a[:, method, metric].mean()), "paired_difference": float(delta.mean()), "case_reweighting_interval": endpoints.tolist(), "strict_improvements": int((delta < 0).sum()), "ties": int((delta == 0).sum())})
    return {"schema": "chronoscope-replay-case-analysis-v1", "plan": plan, "case_ids": cases, "case_metrics": a.tolist(), "comparisons": rows, "interpretation": "Retrospective case-weight sensitivity; selected cases are not a random population sample; no multiplicity adjustment or new confirmation."}


def render(source: dict, result: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = NEXT / "figures"
    colors = ["#c05621", "#2b6cb0", "#2f855a"]
    meta = {"CreationDate": None, "ModDate": None}
    plt.rcParams.update({"font.size": 9})
    groups = defaultdict(list)
    for row in source["sensitivity"]:
        groups[row["base"], row["coverage"], row["controller"], row["gain"]].append(row["mean_rolling_absolute_error"])
    fig, axes = plt.subplots(2, 3, figsize=(9.3, 5.2), sharex=True, sharey=True, layout="constrained")
    for i, base in enumerate(("SeasonalNaive", "Theta")):
        for j, coverage in enumerate((.7, .8, .9)):
            ax = axes[i, j]
            ax.axhline(np.mean(groups[base, coverage, "raw", 1.]), color=colors[0], ls=":", label="Raw")
            for k, control in enumerate(("ACI", "PID"), 1):
                ax.plot([.5, 1, 2], [np.mean(groups[base, coverage, control, g]) for g in (.5, 1., 2.)], marker="o", color=colors[k], label=control + "-style")
            ax.set_title(f"{'Seasonal naive' if i == 0 else 'S+D'}; nominal {coverage:.0%}")
            ax.set_xticks([.5, 1, 2])
            if j == 0:
                ax.set_ylabel("Mean rolling absolute\ncoverage error")
            if i == 1:
                ax.set_xlabel("Fixed gain multiplier")
    axes[0, 0].legend(fontsize=8)
    fig.savefig(out / "fig-gain-sensitivity.pdf", metadata=meta)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.2), layout="constrained")
    for metric, ax in enumerate(axes):
        for j, control in enumerate(METHODS[1:]):
            row = next(r for r in result["comparisons"] if r["method"] == control and r["metric"] == result["plan"]["metrics"][metric])
            lo, hi = row["case_reweighting_interval"]
            ax.plot([lo, hi], [j, j], color=colors[j + 1], lw=2)
            ax.scatter([row["paired_difference"]], [j], color=colors[j + 1])
        ax.axvline(0, color="black", lw=.8, ls=":")
        ax.set_yticks([0, 1], LABELS[1:])
        ax.set_ylim(-.7, 1.7)
        ax.set_xlabel("Controller minus raw S+D")
        ax.set_title(["Rolling absolute coverage error", "Warmup-scaled interval score"][metric])
    fig.savefig(out / "fig-case-reweighting.pdf", metadata=meta)
    plt.close(fig)

    generated = [c for c in source["cases"] if not c["case_id"].startswith("REAL_")]
    fig, axes = plt.subplots(1, 3, figsize=(10, 5), sharey=True, sharex=True, layout="constrained")
    for k, method in enumerate(METHODS):
        ax = axes[k]
        for i, case in enumerate(generated):
            values = [case["methods"][method]["final_coverage"]]
            for seed in (43, 44):
                control = "raw" if k == 0 else method.split("+")[1]
                row = next(r for r in source["generated_repeats"] if r["case_id"] == case["case_id"] and r["seed"] == seed and r["controller"] == control)
                values.append(row["final_coverage"])
            for j, marker in enumerate(("o", "x", "+")):
                ax.scatter([values[j]], [i + (j - 1) * .12], marker=marker, s=28, color=colors[k], label=f"seed {42 + j}" if i == 0 else None)
        ax.axvline(.8, color="black", ls=":", lw=.8)
        ax.set_title(LABELS[k])
        ax.set_xlabel("Final empirical coverage")
        ax.set_xlim(0, 1.03)
        ax.legend(fontsize=7, loc="lower left")
    axes[0].set_yticks(range(len(generated)), [c["case_id"] for c in generated], fontsize=8)
    fig.savefig(out / "fig-generated-seeds.pdf", metadata=meta)
    plt.close(fig)

    rows = []
    for row in result["comparisons"]:
        lo, hi = row["case_reweighting_interval"]
        rows.append(f"{row['method'].replace('Theta+', '')}-style & {'Rolling error' if row['metric'].startswith('mean_') else 'Scaled score'} & {row['paired_difference']:.5f} & [{lo:.5f}, {hi:.5f}] & {row['strict_improvements']}/15" + r"\\")
    text = "\n".join([r"\begin{table}[htbp]\centering\small", r"\caption{Paired differences from raw smoothing plus drift and exploratory ninety-five-percent case-reweighting intervals; entire selected cases, not individual arrivals, are resampled jointly.}\label{tab:case-reweighting}", r"\begin{tabular}{llrrr}\toprule", r"Controller & Quantity & Difference & Reweighting interval & Improved cases\\\midrule", *rows, r"\bottomrule\end{tabular}\end{table}", ""])
    (NEXT / "tables/case-reweighting.tex").write_text(text, encoding="utf-8", newline="\n")
    case_rows = []
    for case in source["cases"]:
        identifier = case["case_id"].replace("_", r"\_")
        provenance = "Generated" if case["source_id"] == "synthetic" else "Monash" if case["source_id"] == "monash" else "UCI"
        n = len(case["source_values"])
        case_rows.append(f"\\texttt{{{identifier}}} & {n} & {case['warmup']} & {case['seasonality']} & {n - case['warmup']} & {provenance}" + r"\\")
    text = "\n".join([r"\begin{table}[htbp]\centering\small", r"\caption{Complete replay inventory with original sequence length, initial prefix, configured seasonal lag and scored arrivals; generated cases and authentic excerpts remain distinct provenance classes.}\label{tab:replay-cases}", r"\begin{tabular}{lrrrrl}\toprule", r"Case & $T$ & $w$ & $m$ & Arrivals & Provenance\\\midrule", *case_rows, r"\bottomrule\end{tabular}\end{table}", ""])
    (NEXT / "tables/cases.tex").write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    raw = (HERE / "evidence/replay.json").read_bytes()
    plan = json.loads((NEXT / "evidence/analysis-plan.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != plan["source_sha256"]:
        raise ValueError("Frozen numerical replay differs from the analysis plan")
    source = json.loads(raw)
    result = analyze(source, plan)
    payload = json.dumps(result, indent=2, allow_nan=False) + "\n"
    dest = NEXT / "evidence/case-reweighting.json"
    if args.check:
        assert dest.read_text(encoding="utf-8") == payload, "Case analysis changed"
    else:
        dest.write_text(payload, encoding="utf-8", newline="\n")
    if args.render:
        render(source, result)
    print(json.dumps(result["comparisons"], indent=2))


if __name__ == "__main__":
    main()
