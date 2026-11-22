"""Generate horizon-aware manuscript counts and paired tables from admitted evidence."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEXT = ROOT / "manuscripts/context-memory/next"
COLLECTIONS = (("m4_weekly", "M4 Weekly", "Weekly"), ("m3_monthly", "M3 Monthly", "Monthly"))


def outputs() -> dict[Path, str]:
    index = json.loads((ROOT / "data/derived/validated-combinations.json").read_text(encoding="utf-8"))
    raw = (ROOT / index["audit"]["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == index["audit"]["sha256"], "Audit archive changed"
    content = gzip.decompress(raw)
    assert hashlib.sha256(content).hexdigest() == index["audit"]["uncompressed_sha256"], "Decoded audit changed"
    document = json.loads(content)
    paired_path = ROOT / "manuscripts/context-memory/evidence/paired-series-uncertainty.json"
    paired = json.loads(paired_path.read_text(encoding="utf-8"))
    assert paired["input_sha256"] == hashlib.sha256(raw).hexdigest(), "Paired source binding differs"
    counts, rows = {}, []
    for key, label, _ in COLLECTIONS:
        series = [s for s in document["series"] if s["dataset"] == key]
        admitted = [s for s in series if not s.get("excluded")]
        origins = [origin for s in admitted for origin in s["origins"]]
        horizon = document["datasets"][key]["horizon"]
        methods = {len(origin["methods"]) for origin in origins}
        assert len(methods) == 1 and all(len(o["actual"]) == horizon for o in origins)
        paths = sum(len(o["methods"]) for o in origins)
        points = sum(len(m["quantiles"]) for o in origins for m in o["methods"])
        assert all(len(m["quantiles"]) == horizon for o in origins for m in o["methods"])
        counts[key] = {"source": len(series), "admitted": len(admitted), "excluded": len(series)-len(admitted),
                       "origins": len(origins), "horizon": horizon, "methods": next(iter(methods)),
                       "method_paths": paths, "point_values": points}
        worker_seconds = [s["seconds"] for s in admitted]
        counts[key].update({
            "worker_median_seconds": statistics.median(worker_seconds),
            "worker_p90_seconds": statistics.quantiles(worker_seconds, n=10, method="inclusive")[8],
            "validation_mix_stack_origins": sum(
                m["selected"][0] == "stack" for o in origins for m in o["methods"] if m["name"] == "ValidationMix"
            ),
        })
        rows.append(f"{label} & {horizon} & {len(series)} & {len(admitted)} & {len(series)-len(admitted)} & "
                    f"{len(origins)} & {points:,}" + r"\\")
    total = {name: sum(c[name] for c in counts.values()) for name in
             ("source", "admitted", "excluded", "origins", "method_paths", "point_values")}
    inventory = "\n".join([
        r"\begin{table}[htbp]\centering\small",
        r"\caption{Source inventories and admitted external evaluation units. Each origin has twelve methods; "
        r"the weekly and monthly horizons differ. Point values count one scalar per method and lead, not all three quantiles.}",
        r"\label{tab:collection-inventory}", r"\begin{tabular}{lrrrrrr}\toprule",
        r"Collection & $H$ & Source & Admitted & Excluded & Origins & Point values\\\midrule", *rows,
        f"Total & -- & {total['source']} & {total['admitted']} & {total['excluded']} & {total['origins']} & "
        f"{total['point_values']:,}" + r"\\\bottomrule", r"\end{tabular}\end{table}", ""])
    lookup = {(r["dataset"], r["control"], r["metric"]): r for r in paired["comparisons"] if r["method"] == "ValidationMix"}
    rows = []
    for metric in ("mase", "msis"):
        for control in ("RecencyMean", "AutoTheta"):
            for key, _, label in COLLECTIONS:
                row = lookup[key, control, metric]
                low, high = row["percentile_95"]
                rows.append(f"{label} & {control} & {metric.upper()} & ${row['difference']:.6f}$ & "
                            f"$[{low:.6f},{high:.6f}]$ & {row['negative']}/{row['series']}" + r"\\")
    table = "\n".join([r"\begin{table}[htbp]\centering\small",
                       r"\caption{ValidationMix minus each control after averaging available origins within each series. "
                       r"Unadjusted exploratory 95\% paired-series intervals describe the admitted collection, "
                       r"not population-wide superiority.}", r"\label{tab:paired-main}",
                       r"\begin{tabular}{lllrrr}\toprule",
                       r"Collection & Control & Loss & Difference & 95\% interval & Lower loss\\\midrule",
                       *rows, r"\bottomrule\end{tabular}\end{table}", ""])
    macros = "\n".join(["% Generated from exact admitted method-path lengths.",
                        rf"\newcommand{{\externalpointcount}}{{{total['point_values']:,}}}",
                        rf"\newcommand{{\externalpathcount}}{{{total['method_paths']:,}}}", ""])
    for key, prefix in (("m4_weekly", "weekly"), ("m3_monthly", "monthly")):
        row = counts[key]
        macros += "\n".join([
            rf"\newcommand{{\{prefix}MedianSeconds}}{{{row['worker_median_seconds']:.3f}}}",
            rf"\newcommand{{\{prefix}PninetySeconds}}{{{row['worker_p90_seconds']:.3f}}}",
            rf"\newcommand{{\{prefix}StackOrigins}}{{{row['validation_mix_stack_origins']:,}}}",
            rf"\newcommand{{\{prefix}AllOrigins}}{{{row['origins']:,}}}",
            "",
        ])
    receipt = {"archive_sha256": hashlib.sha256(raw).hexdigest(), "paired_sha256": hashlib.sha256(paired_path.read_bytes()).hexdigest(),
               "collections": counts, "total": total, "unit": "one scalar point prediction per method-origin-lead"}
    return {NEXT / "tables/collection-inventory.tex": inventory, NEXT / "tables/paired-main.tex": table,
            NEXT / "tex/protocol-counts.tex": macros,
            NEXT / "evidence/protocol-counts.json": json.dumps(receipt, indent=2) + "\n"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    check = parser.parse_args().check
    for path, payload in outputs().items():
        if check:
            assert path.read_text(encoding="utf-8") == payload, f"Stale generated manuscript input: {path}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8", newline="\n")
    print("Combination tables: horizon-aware archive counts and eight paired comparisons match evidence")


if __name__ == "__main__":
    main()
