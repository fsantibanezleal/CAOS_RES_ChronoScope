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
    "method-combinations": ("ContextMemory", "RecencyMean", "EqualMean"),
    "temporal-validation": ("ContextMemoryCV", "ValidationMix"),
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
    "selection/training-case-ranking": "training-case-ranking",
    "interval/gaussian": "method-local-experts",
    "historical/streaming-smoothing-drift": "streaming-evidence",
    "interval/aci-style": "streaming-evidence",
    "interval/pid-style": "streaming-evidence",
}
DIAGNOSTIC_FIELDS = {
    "stationarity": {
        "adf": "tests[ADF]", "kpss": "tests[KPSS]", "pp": "tests[PhillipsPerron]",
        "dfgls": "tests[DFGLS]", "zivot-andrews": "tests[ZivotAndrews]", "differencing": "recommended_d",
        "seasonal-differencing": "recommended_D", "joint-verdict": "combined_verdict",
    },
    "autocorrelation": {
        "bartlett": "bartlett_band", "acf": "acf", "pacf": "pacf", "ljung-box": "ljung_box",
        "box-pierce": "box_pierce", "durbin-watson": "durbin_watson",
    },
    "seasonality": {
        "periodogram": "periodogram", "welch": "welch.dominant_power",
        "strength": "seasonal_strength_by_candidate_period", "stl": "stl_at_dominant",
    },
    "filters": {"hp": "hp", "cf": "cf", "emd": "emd", "cwt": "scalogram"},
    "changepoints": {"pelt": "pelt", "cusum": "cusum", "markov": "markov.most_likely"},
    "volatility": {
        "arch": "arch_lm", "garch": "garch", "rolling": "rolling",
        "box-cox-mle": "boxcox", "box-cox-guerrero": "boxcox",
    },
    "distribution": {
        "moments": "summary.mean", "jarque-bera": "summary.jarque_bera_pvalue",
        "shapiro-wilk": "summary.shapiro_pvalue", "kde": "kde", "qq": "qq",
        "sample-entropy": "complexity.sample_entropy", "permutation-entropy": "complexity.permutation_entropy",
        "spectral-entropy": "complexity.spectral_entropy", "bds": "complexity.bds_pvalue",
        "catch22": "catch22.features",
    },
    "fractal": {
        "hurst-rs": "hurst.rs", "dfa": "hurst.dfa_alpha", "mfdfa": "multifractal.q",
        "higuchi": "fractal_dimension.higuchi", "katz": "fractal_dimension.katz",
        "petrosian": "fractal_dimension.petrosian",
    },
    "nonlinear": {
        "correlation-dimension": "correlation_dimension", "lyapunov": "largest_lyapunov",
        "rqa": "rqa.recurrence_rate", "iaaft": "surrogate_test.n_surrogates", "zero-one": "zero_one_K",
    },
    "sequence": {
        "matrix-profile": "matrix_profile.profile", "fluss": "matrix_profile.corrected_arc_curve",
        "multiscale-entropy": "multiscale_entropy.scales", "lempel-ziv": "lempel_ziv",
        "time-reversal-raw": "time_reversal[].raw", "time-reversal-standardized": "time_reversal[].standardized",
    },
}
STUDY_EVIDENCE = {
    "analysis/atlas/partition": "data/derived/forecastability.json#series[].partition",
    "analysis/atlas/prefix-features": "data/derived/forecastability.json#series[].features",
    "analysis/atlas/by": "data/derived/forecastability.json#summary.associations",
    "analysis/atlas/kendall": "data/derived/forecastability.json#summary.associations",
    "analysis/atlas/selector": "data/derived/forecastability.json#summary.selection_mean_mase",
    "forecast/Naive": "data/derived/forecastability.json#series[].mase.Naive",
    "forecast/ContextMemoryCV": "data/derived/combinations/m4_weekly/T1.json#origins",
    "forecast/ValidationMix": "data/derived/combinations/m4_weekly/T1.json#origins",
    "browser/normalized-linear-least-squares": "frontend/public/models/nlinear.json",
    "experimental-browser/normalized-ridge": "docs/research/browser-linear/v1/results.json#selection",
    "experimental-browser/split-calibration": "docs/research/browser-linear/v1/results.json#scores",
    "experimental-browser/roughness-stratification": "docs/research/browser-linear/confirmation-v1/results.json#scores",
    "selection/training-case-ranking": "models/selector.json#ranking",
    "interval/gaussian": "data/derived/TRND_seasonal/trace.json",
    "historical/streaming-smoothing-drift": "manuscripts/prequential-streaming-conformal/evidence/replay.json",
    "interval/aci-style": "data/derived/TRND_seasonal/streaming.json#methods.Theta+ACI",
    "interval/pid-style": "data/derived/TRND_seasonal/streaming.json#methods.Theta+PID",
    "forecast/ridge-blind": "data/derived/EXOG_promo/streaming.json#methods.Ridge (blind)",
    "forecast/ridge-aware": "data/derived/EXOG_promo/streaming.json#methods.Ridge+exog (aware)",
}
CATCH24_FIELDS = {
    "DN_HistogramMode_5": ("Mode of a five-bin histogram of standardized values", "dimensionless"),
    "DN_HistogramMode_10": ("Mode of a ten-bin histogram of standardized values", "dimensionless"),
    "CO_f1ecac": ("First 1/e autocorrelation crossing", "observation steps"),
    "CO_FirstMin_ac": ("First local autocorrelation minimum lag", "observation steps"),
    "CO_HistogramAMI_even_2_5": ("Histogram auto-mutual information at lag two, using five bins", "dimensionless"),
    "CO_trev_1_num": ("Mean cube of one-step increments of the standardized series", "dimensionless"),
    "MD_hrv_classic_pnn40": ("Fraction of absolute increments exceeding the backend threshold", "fraction"),
    "SB_BinaryStats_mean_longstretch1": ("Length of the longest run above the sample mean", "observations"),
    "SB_TransitionMatrix_3ac_sumdiagcov": ("Sum of the transition-column covariance diagonal", "dimensionless"),
    "PD_PeriodicityWang_th0_01": ("Period lag selected from the detrended autocovariance", "observation steps"),
    "CO_Embed2_Dist_tau_d_expfit_meandiff": ("Mean histogram discrepancy from an exponential fit to embedding distances",
                                         "dimensionless"),
    "IN_AutoMutualInfoStats_40_gaussian_fmmi": ("First minimum of Gaussian auto-mutual information", "observation steps"),
    "FC_LocalSimple_mean1_tauresrat": ("Ratio of correlation time after one-step differencing to original time",
                                     "dimensionless"),
    "DN_OutlierInclude_p_001_mdrmd": ("Relative timing statistic for large positive deviations", "dimensionless"),
    "DN_OutlierInclude_n_001_mdrmd": ("Relative timing statistic for large negative deviations", "dimensionless"),
    "SP_Summaries_welch_rect_area_5_1": ("Spectral area in the lowest fifth of frequencies", "standardized variance"),
    "SB_BinaryStats_diff_longstretch0": ("Length of the longest decreasing stretch", "observation steps"),
    "SB_MotifThree_quantile_hh": ("Entropy of adjacent symbol pairs after three-level quantile encoding", "nats"),
    "SC_FluctAnal_2_rsrangefit_50_1_logi_prop_r1": ("Fraction of scales on the smaller-scale side of the R/S fit",
                                                "fraction"),
    "SC_FluctAnal_2_dfa_50_1_2_logi_prop_r1": ("Fraction of scales on the smaller-scale side of the DFA fit",
                                             "fraction"),
    "SP_Summaries_welch_rect_centroid": ("Angular frequency at the halfway point of cumulative spectral power",
                                        "radians per observation step"),
    "FC_LocalSimple_mean3_stderr": ("Spread of three-point rolling-mean forecast errors on standardized values",
                                   "dimensionless"),
    "DN_Mean": ("Arithmetic mean of the original values", "source unit"),
    "DN_Spread_Std": ("Standard deviation of the original values", "source unit"),
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


def observed_value(value, field: str):
    for key in field.split("."):
        name, _, selector = key.partition("[")
        if not isinstance(value, dict) or name not in value:
            return None
        value = value[name]
        if selector == "]":
            value = value[0] if value else None
        elif selector:
            value = next((row for row in value if row["name"] == selector.removesuffix("]")), None)
    return value


def diagnostic_evidence(method_id: str, analyses: dict[Path, dict]) -> tuple[str, str]:
    _, group, method = method_id.split("/")
    if group == "causality":
        return "Runtime test; retained cases skipped", "data/derived/REAL_electricity/analysis.json#causality.skipped"
    field = DIAGNOSTIC_FIELDS.get(group, {}).get(method)
    if field is None:
        return "Callable procedure", ""
    path = f"{group}.{field}"
    for file, data in analyses.items():
        if method.startswith("box-cox-"):
            boxcox = observed_value(data, path)
            mode = "guerrero" if method.endswith("-guerrero") else "mle"
            if not boxcox or boxcox.get("method", "").lower() != mode:
                continue
        value = observed_value(data, path)
        if value is not None and not (isinstance(value, dict) and "error" in value):
            return "Retained output or summary", f"{file.relative_to(ROOT).as_posix()}#{path}"
    raise ValueError(f"No retained diagnostic output for {method_id}: {path}")


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
    crosswalk = [("procedure", "source", "section_label", "validation_reference",
                  "retained_evidence_scope", "retained_evidence_reference")]
    source = "\n".join(path.read_text(encoding="utf-8") for path in (TABLES.parent / "tex").glob("*.tex"))
    analyses = {file: load(file) for file in sorted(DERIVED.glob("*/analysis.json"))}
    feature_paths = set().union(*(row.get("distribution", {}).get("catch22", {}).get("features", {})
                                 for row in analyses.values()))
    if feature_paths != CATCH24_FIELDS.keys():
        raise ValueError("The Catch24 field dictionary differs from the retained feature keys")
    catch_fields = [("key", "meaning", "unit"), *((key, *value) for key, value in CATCH24_FIELDS.items())]
    fresh_methods = {method["name"] for case in fresh["cases"] for method in case["methods"]}
    for row in inventory["methods"]:
        label = "sec:" + report_section(row["id"])
        if r"\label{" + label + "}" not in source:
            raise ValueError(f"Missing report section for {row['id']}: {label}")
        validation = row["validation"]
        if not (ROOT / validation.partition("::")[0]).is_file():
            raise ValueError(f"Missing validation reference for {row['id']}: {validation}")
        if row["id"].startswith("analysis/") and not row["id"].startswith("analysis/atlas/"):
            scope, evidence = diagnostic_evidence(row["id"], analyses)
        elif row["id"] in STUDY_EVIDENCE:
            scope, evidence = "Retained study artifact", STUDY_EVIDENCE[row["id"]]
        elif row["artifact_name"] in fresh_methods:
            scope = "Retained fresh holdout paths"
            evidence = f"data/derived/fresh-reevaluation.json#cases[].methods[{row['artifact_name']}]"
        else:
            raise ValueError(f"Missing evidence classification for {row['id']}")
        if evidence and not (ROOT / evidence.partition("#")[0]).is_file():
            raise ValueError(f"Missing retained evidence file for {row['id']}: {evidence}")
        crosswalk.append((row["name"], row["implementation"], label, validation, scope, evidence))
    return {
        TABLES / "fresh-by-case.csv": csv_text(by_case),
        TABLES / "procedure-crosswalk.csv": csv_text(crosswalk),
        TABLES / "observed-analysis-fields.csv": csv_text(observed_fields()),
        TABLES / "catch24-fields.csv": csv_text(catch_fields),
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
