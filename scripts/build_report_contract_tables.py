"""Generate the working report's root-field tables from the normative contract catalog and schemas."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tex(value: object) -> str:
    text = str(value)
    escaped = {"\\": r"\textbackslash{}", "_": r"\_\allowbreak{}", "%": r"\%", "&": r"\&", "#": r"\#", "{": r"\{", "}": r"\}", "$": r"\$", "^": r"\textasciicircum{}", "~": r"\textasciitilde{}"}
    parts = []
    for token in text.split(" "):
        if len(token) > 24 and "_" not in token:
            parts.append(r"\allowbreak{}".join("".join(escaped.get(c, c) for c in token[i:i+16]) for i in range(0, len(token), 16)))
        else:
            parts.append("".join(escaped.get(c, c) for c in token))
    return " ".join(parts)


def field_type(field: dict) -> str:
    if "type" in field:
        value = field["type"]
        return "/".join(value) if isinstance(value, list) else value
    if "$ref" in field:
        return "object reference"
    if "anyOf" in field or "oneOf" in field:
        return "declared union"
    if "const" in field or "enum" in field:
        return "fixed value"
    return "schema-defined"


def unit(identifier: str, name: str) -> str:
    if identifier == "forecastability" and name == "source_n":
        return "series"
    if name in {"history", "actual"}:
        return "source U"
    if name in {"n", "source_n", "history_len", "horizon", "lookback", "seasonality", "seasonality_period"}:
        return "observations"
    if name == "history_index":
        return "indices"
    if name in {"n_cases", "n_train_cases", "included_n", "trained_windows", "calibration_bin_counts", "browser_forecast_decimals"}:
        return "counts"
    if name in {"alpha", "nominal_coverage", "quantile_levels"}:
        return "probabilities"
    if name in {"sigma_norm", "roughness_boundaries", "absolute_residual_radii", "global_radii"}:
        return "dimensionless"
    if name in {"methods", "series", "summary", "metrics", "covariate", "ranking"}:
        return "mixed; see text"
    return "metadata"


def constraints(field: dict) -> str:
    values = []
    for key in ("const", "enum", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minItems", "maxItems", "pattern"):
        if key in field:
            values.append(f"{key}={json.dumps(field[key], ensure_ascii=True, separators=(',', ':'))}")
    if not values:
        values.append("Nested content follows the normative schema" if field.get("type") in ("object", "array") else "No additional root-field range")
    return "; ".join(values)


def generate() -> dict[str, str]:
    rows = []
    for line in (ROOT / "docs/contracts/catalog.md").read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 13 and cells[-1] == "real":
            rows.append(cells)
    if len({row[0] for row in rows}) != len(rows) or not rows:
        raise ValueError("The contract catalog is empty or has duplicate ids")
    result = {}
    for row in rows:
        identifier, version, _, schema_path = row[:4]
        schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
        lines = [r"\begingroup\small", r"\begin{longtable}{@{}p{.22\textwidth}p{.14\textwidth}p{.14\textwidth}p{.29\textwidth}p{.09\textwidth}@{}}",
                 r"\caption{Root fields of the " + tex(identifier) + " contract, catalog version " + tex(version) + r". Types, units and structural constraints distinguish required members from optional metadata; nested records follow the cited schema.}\label{tab:contract-" + identifier + r"}\\",
                 r"\toprule Field & JSON type & Unit & Root constraint & Required\\\midrule\endfirsthead",
                 r"\toprule Field & JSON type & Unit & Root constraint & Required\\\midrule\endhead"]
        required = set(schema.get("required", []))
        for name, field in schema.get("properties", {}).items():
            lines.append(r"\texttt{" + tex(name) + "} & " + tex(field_type(field)) + " & " + tex(unit(identifier, name)) + " & " + tex(constraints(field)) + " & " + ("yes" if name in required else "no") + r"\\")
        lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", ""])
        result[identifier + ".tex"] = "\n".join(lines)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "manuscripts/product-report/next/tables/contracts")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    tables = generate()
    if args.check:
        bad = [name for name, content in tables.items() if not (args.output / name).is_file() or (args.output / name).read_text(encoding="utf-8") != content]
        if bad:
            print("Stale contract tables: " + ", ".join(bad))
            return 1
    else:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, content in tables.items():
            (args.output / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"Report contract tables: {len(tables)} current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
