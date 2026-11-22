"""Render the same validated Timestral summaries for the browser and LaTeX."""

from __future__ import annotations

import argparse
import json

from check_timestral_study import FOLDER, ROOT, digest, load, validate


def outputs() -> dict:
    source = FOLDER / "results.json"
    result = load(source)
    validate(result)
    primary = next(row for row in result["paired_comparisons"]
                   if row["model"] == "mistralai/Timestral-209M" and row["control"] == "AutoTheta"
                   and row["metric"] == "mase")
    summary = {
        "source_sha256": digest(source),
        "checkpoints": result["summaries"],
        "primary": primary,
    }
    lines = [
        r"\begin{table}[htbp]\centering\small",
        r"\caption{Case-weighted scores for four official Timestral checkpoints on the same fifteen reserved blocks, with a nominal 80 percent interval.}\label{tab:timestral-scores}",
        r"\begin{tabular}{lrrr}\toprule Checkpoint & MASE & MSIS & Coverage\\\midrule",
    ]
    for row in result["summaries"]:
        if row["group"] != "all15":
            continue
        name = row["model"].split("/")[-1]
        metrics = row["mean_metrics"]
        lines.append(f"{name} & {metrics['mase']:.5f} & {metrics['msis']:.5f} & {100*metrics['coverage']:.2f}\\% " + r"\\")
    lines.extend([r"\bottomrule\end{tabular}", r"\end{table}", ""])
    return {
        ROOT / "frontend/src/data/timestral-study.json": json.dumps(summary, indent=2) + "\n",
        ROOT / "manuscripts/product-report/next/tables/timestral.tex": "\n".join(lines),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, content in outputs().items():
        if args.check:
            if path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale Timestral presentation: {path.relative_to(ROOT)}")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    print("Timestral presentation matches the validated study")


if __name__ == "__main__":
    main()
