"""Build audit tables for the technical report from committed numerical inputs."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "manuscripts/product-report/next/tables"
DERIVED = ROOT / "data/derived"
ANALYSIS_SECTIONS = {
    "stationarity": "diagnostic-stationarity",
    "autocorrelation": "diagnostic-autocorrelation",
    "seasonality": "diagnostic-autocorrelation",
    "filters": "diagnostic-filters",
    "changepoints": "diagnostic-breaks",
    "volatility": "diagnostic-breaks",
    "distribution": "diagnostic-complexity",
    "fractal": "diagnostic-complexity",
    "nonlinear": "diagnostic-complexity",
    "causality": "diagnostic-relations",
    "sequence": "method-sequence",
    "atlas": "forecastability",
}
FORECAST_SECTIONS = {
    "method-local-experts": ("Naive", "SeasonalNaive", "SES", "Holt", "HoltWinters", "Theta"),
    "method-combinations": ("ContextMemory", "RecencyMean", "EqualMean", "ContextMemoryCV", "ValidationMix"),
    "method-automatic-statistical": ("AutoARIMA", "AutoETS", "AutoTheta"),
    "method-lag-trees": ("LightGBM",),
    "method-neural": ("NLinear", "DLinear", "NHITS", "NLinear-nf", "DLinear-nf", "NHITS-nf"),
    "method-pretrained": ("Chronos-Bolt", "Chronos-2", "TimesFM-2.5", "TiRex-2"),
    "diagnostic-relations": ("ridge-blind", "ridge-aware"),
}
OTHER_SECTIONS = {
    "browser/normalized-linear-least-squares": "browser-normalization",
    "experimental-browser/normalized-ridge": "browser-ridge",
    "experimental-browser/split-calibration": "browser-split",
    "experimental-browser/roughness-stratification": "browser-strata",
    "selection/training-case-ranking": "forecastability",
    "interval/gaussian": "method-local-experts",
    "historical/streaming-smoothing-drift": "streaming-evidence",
    "interval/aci-style": "streaming-evidence",
    "interval/pid-style": "streaming-evidence",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def csv_text(rows) -> str:
    stream = io.StringIO()
    csv.writer(stream, lineterminator="\n").writerows(rows)
    return stream.getvalue()


def report_section(method_id: str) -> str:
    group, _, name = method_id.partition("/")
    if group == "analysis":
        return ANALYSIS_SECTIONS[name.split("/")[0]]
    if group == "forecast":
        return next(section for section, names in FORECAST_SECTIONS.items() if name in names)
    return OTHER_SECTIONS[method_id]


def observed_fields():
    """Record observed paths and shapes for open legacy analysis objects."""
    fields = defaultdict(lambda: {"cases": set(), "types": set(), "lengths": set()})
    types = {dict: "object", list: "array", bool: "boolean", int: "integer",
             float: "number", str: "string", type(None): "null"}

    def visit(case, path, value):
        field = fields[path]
        field["cases"].add(case)
        field["types"].add(types[type(value)])
        if isinstance(value, dict):
            for key, child in value.items():
                visit(case, f"{path}.{key}", child)
        elif isinstance(value, list):
            field["lengths"].add(len(value))
            for child in value:
                visit(case, f"{path}[]", child)

    for file in sorted(DERIVED.glob("*/analysis.json")):
        data = load(file)
        for group in ANALYSIS_SECTIONS.keys() - {"sequence", "atlas"}:
            if group in data:
                visit(file.parent.name, group, data[group])
    rows = [("field_path", "observed_json_types", "observed_min_array_length", "observed_max_array_length",
             "case_count_with_field", "method_section")]
    for path, field in sorted(fields.items()):
        lengths = field["lengths"]
        group = path.split(".")[0].split("[")[0]
        rows.append((path, "|".join(sorted(field["types"])), min(lengths) if lengths else "",
                     max(lengths) if lengths else "", len(field["cases"]), "sec:" + ANALYSIS_SECTIONS[group]))
    return rows


def outputs() -> dict[Path, str]:
    fresh = load(DERIVED / "fresh-reevaluation.json")
    metrics = ("mae", "rmse", "mase", "coverage", "mean_width", "msis", "wql")
    by_case = [("case", "method", "history_length", "horizon", "seasonal_lag", *metrics)]
    for case in fresh["cases"]:
        for method in case["methods"]:
            by_case.append((case["case_id"], method["name"], case["history_length"], case["horizon"],
                            case["seasonality"], *(method["metrics"][name] for name in metrics)))
    if len(by_case) - 1 != 15 * 22:
        raise ValueError("The admitted fresh roster is incomplete")
    inventory = load(ROOT / "docs/design/method-inventory.json")
    crosswalk = [("procedure", "source", "section_label")]
    source = "\n".join(path.read_text(encoding="utf-8") for path in (TABLES.parent / "tex").glob("*.tex"))
    for row in inventory["methods"]:
        label = "sec:" + report_section(row["id"])
        if r"\label{" + label + "}" not in source:
            raise ValueError(f"Missing report section for {row['id']}: {label}")
        crosswalk.append((row["name"], row["implementation"], label))
    return {
        TABLES / "fresh-by-case.csv": csv_text(by_case),
        TABLES / "procedure-crosswalk.csv": csv_text(crosswalk),
        TABLES / "observed-analysis-fields.csv": csv_text(observed_fields()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, content in outputs().items():
        if args.check:
            if path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Stale report evidence: {path.relative_to(ROOT)}")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    print("Technical report: 330 case-method rows, procedure crosswalk and observed diagnostic fields")


if __name__ == "__main__":
    main()
