"""Generate the working report's field tables from the normative catalog and schemas."""
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
    if identifier == "analysis" and name in {
        "stationarity", "autocorrelation", "seasonality", "filters", "changepoints",
        "volatility", "distribution", "fractal", "nonlinear", "causality", "sequence",
    }:
        return "mixed; see text"
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
        if field.get("additionalProperties") is True:
            values.append("Open object")
        elif field.get("type") not in ("object", "array"):
            values.append("No explicit range")
    return "; ".join(values)


def nested_fields(schema: dict) -> list[tuple[str, dict, str]]:
    """Enumerate explicit nested members, retaining branch and required distinctions."""
    rows = []

    def visit(node, path, required, references=()):
        if not isinstance(node, dict):
            return
        if "$ref" in node and node["$ref"].startswith("#/"):
            ref = node["$ref"]
            if ref in references:
                return
            target = schema
            for component in ref[2:].split("/"):
                target = target[component.replace("~1", "/").replace("~0", "~")]
            visit(target, path, required, (*references, ref))
        elif path and any(marker in path for marker in (".", "[", "{")):
            rows.append((path, node, required))
        for name, child in node.get("properties", {}).items():
            child_path = f"{path}.{name}" if path else name
            visit(child, child_path, "yes" if name in node.get("required", ()) else "no", references)
        for i, child in enumerate(node.get("prefixItems", ())):
            visit(child, f"{path}[{i}]", "tuple", references)
        if isinstance(node.get("items"), dict):
            visit(node["items"], f"{path}[]", "item", references)
        if isinstance(node.get("additionalProperties"), dict):
            visit(node["additionalProperties"], f"{path}{{key}}", "keyed", references)
        for key in ("allOf", "oneOf", "anyOf"):
            for i, child in enumerate(node.get(key, ()), start=1):
                visit(child, f"{path}[{key} {i}]", "branch", references)

    visit(schema, "", "")
    return rows


def generate() -> dict[str, str]:
    rows = []
    for line in (ROOT / "docs/contracts/catalog.md").read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 13 and cells[-1] == "real":
            rows.append(cells)
    if len({row[0] for row in rows}) != len(rows) or not rows:
        raise ValueError("The contract catalog is empty or has duplicate ids")
    result = {}
    nested = [r"\begingroup\small",
              r"\begin{longtable}{@{}p{.38\textwidth}p{.15\textwidth}p{.29\textwidth}p{.08\textwidth}@{}}",
              r"\caption{Explicit nested JSON fields and schema constraints across the ChronoScope data interfaces. Requirement markers apply within the immediate parent record or branch.}\label{tab:nested-schema}\\",
              r"\toprule Field path & JSON type & Explicit constraint & Req.\\\midrule\endfirsthead",
              r"\toprule Field path & JSON type & Explicit constraint & Req.\\\midrule\endhead"]
    for row in rows:
        identifier, version, _, schema_path = row[:4]
        schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
        lines = [r"\begingroup\small", r"\begin{longtable}{@{}p{.22\textwidth}p{.14\textwidth}p{.14\textwidth}p{.29\textwidth}p{.09\textwidth}@{}}",
                 r"\caption{Root fields of the " + tex(identifier) + r" contract, interface revision \texttt{" + tex(version) + r"}. Types, units and structural constraints distinguish required members from optional metadata; nested records are listed separately.}\label{tab:contract-" + identifier + r"}\\",
                 r"\toprule Field & JSON type & Unit & Root constraint & Required\\\midrule\endfirsthead",
                 r"\toprule Field & JSON type & Unit & Root constraint & Required\\\midrule\endhead"]
        required = set(schema.get("required", []))
        for name, field in schema.get("properties", {}).items():
            lines.append(r"\texttt{" + tex(name) + "} & " + tex(field_type(field)) + " & " + tex(unit(identifier, name)) + " & " + tex(constraints(field)) + " & " + ("yes" if name in required else "no") + r"\\")
        lines.extend([r"\bottomrule", r"\end{longtable}", r"\endgroup", ""])
        result[identifier + ".tex"] = "\n".join(lines)
        fields = nested_fields(schema)
        if fields:
            nested.append(r"\midrule\multicolumn{4}{@{}l}{\textbf{" + tex(identifier) + r"}}\\")
            for path, field, required in fields:
                # Line breaks at field boundaries keep long array paths legible.
                field_path = r".\allowbreak{}".join(map(tex, path.split(".")))
                nested.append(r"\texttt{" + field_path + "} & " + tex(field_type(field))
                              + " & " + tex(constraints(field)) + " & " + required + r"\\")
    nested.extend([r"\bottomrule\end{longtable}", r"\endgroup", ""])
    result["nested.tex"] = "\n".join(nested)
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
