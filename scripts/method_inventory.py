"""Authoritative numerical-procedure catalog and source-bound documentation index.

Generate with --write; otherwise verify the committed index and every source
reference. This inventory does not certify a method's teaching or publication.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = Path("docs/design/method-inventory.json")
ENGINE = "data-pipeline/chronoscopelab/"
NON_METHOD_APIS = {
    "stationarity.stationarity_report": "Assembles the stationarity tests, differencing recommendations and combined verdict.",
    "autocorrelation.autocorrelation_report": "Assembles correlograms, portmanteau statistics and lag pairs.",
    "causality.causality_report": "Assembles cross-correlation, Granger and cointegration outputs.",
    "changepoints.changepoints_report": "Assembles segmentation, stability and regime-fit outputs.",
    "distribution.distribution_report": "Assembles distributional summaries, density, quantile and complexity outputs.",
    "filters.filters_report": "Assembles trend-cycle, empirical-mode and wavelet outputs.",
    "fractal.fractal_report": "Assembles scaling, multifractal and graph-dimension outputs.",
    "nonlinear.nonlinear_report": "Assembles embedded-state, recurrence, chaos and surrogate diagnostics.",
    "seasonality.seasonality_report": "Assembles spectral, decomposition and seasonal-subseries outputs.",
    "sequence.finite_sequence": "Enforces the finite contiguous input contract; it estimates no numerical property.",
    "volatility.volatility_report": "Assembles conditional-variance, transformation and rolling-dispersion outputs.",
}


def entry(key, name, module, symbol, test, *, scope="analysis", artifact=None, relation="numerical procedure"):
    source = module if module.startswith("scripts/") else ENGINE + module
    return {"id": key, "name": name, "scope": scope,
            "implementation": source + "::" + symbol,
            "validation": test if test.startswith("frontend/") else "tests/" + test,
            "artifact_name": artifact, "implementation_relation": relation}


def catalog():
    rows = []
    for name, symbol in [("SeasonalNaive", "seasonal_naive"), ("SES", "ses"), ("Holt", "holt"),
                         ("HoltWinters", "holt_winters"), ("Theta", "theta")]:
        rows.append(entry("forecast/" + name, name, "model/forecasters.py", symbol,
                          "test_forecasters.py", scope="forecast", artifact=name,
                          relation="local finite-history forecast"))
    for name, mode in [("ContextMemory", "context"), ("RecencyMean", "recency"), ("EqualMean", "uniform")]:
        row = entry("forecast/" + name, name, "model/context_memory.py", "fit_context_memory",
                    "test_reevaluation.py", scope="forecast", artifact=name,
                    relation="fixed combination" if mode == "context" else "matching combination control")
        row["configuration"] = {"mode": mode}
        rows.append(row)
    for name in ("ContextMemoryCV", "ValidationMix"):
        row = entry("forecast/" + name, name, "model/validated_combination.py", "fit_validated",
                    "test_validated_combination.py", scope="forecast", artifact=name,
                    relation="temporally selected combination")
        row["configuration"] = {"stacking": name == "ValidationMix"}
        rows.append(row)
    for name in ("AutoETS", "AutoTheta", "AutoARIMA"):
        rows.append(entry("forecast/" + name, name, "engines/statsforecast_engine.py", "StatsforecastForecaster",
                          "test_engines.py", scope="forecast", artifact=name, relation="StatsForecast model"))
    rows.append(entry("forecast/LightGBM", "LightGBM", "engines/lightgbm_engine.py", "LightGBMForecaster",
                      "test_engines.py", scope="forecast", artifact="LightGBM", relation="lag-feature regression"))
    for name in ("NLinear", "DLinear", "NHITS"):
        rows.append(entry("forecast/" + name, name + " with a local quantile head", "engines/neural_engine.py",
                          "NeuralForecaster", "test_engine_neural.py", scope="forecast", artifact=name,
                          relation="direct local adaptation, distinct from the package implementation"))
        rows.append(entry("forecast/" + name + "-nf", name + " from NeuralForecast",
                          "engines/neuralforecast_engine.py", "NeuralForecastForecaster",
                          "test_engine_neuralforecast.py", scope="forecast", artifact=name + " (nf)",
                          relation="NeuralForecast package model"))
    for name, module, symbol, test in [
        ("Chronos-Bolt", "chronos_engine", "ChronosForecaster", "test_engine_foundation.py"),
        ("Chronos-2", "chronos_engine", "ChronosForecaster", "test_engine_foundation.py"),
        ("TimesFM-2.5", "timesfm_engine", "TimesFmForecaster", "test_engine_foundation.py"),
        ("TiRex-2", "tirex2_engine", "Tirex2Forecaster", "test_engine_tirex2_wsl.py"),
    ]:
        rows.append(entry("forecast/" + name, name, "engines/" + module + ".py", symbol, test,
                          scope="forecast", artifact=name, relation="pretrained checkpoint inference"))
    rows.extend([
        entry("browser/normalized-linear-least-squares", "Instance-normalized linear least-squares browser model",
              "scripts/train_nlinear_onnx.py", "main", "frontend/scripts/check-live-real.mjs",
              scope="browser-export", artifact="NLinear",
              relation="global synthetic-window least-squares fit exported to ONNX; distinct from per-prefix neural fits"),
        entry("experimental-browser/normalized-ridge", "Held-out instance-normalized ridge reference",
              "scripts/evaluate_browser_linear.py", "fit_ridge", "test_browser_linear.py",
              scope="experimental-browser", relation="synthetic held-out reference; not the deployed point model"),
        entry("experimental-browser/split-calibration", "Per-lead absolute-residual split calibration",
              "scripts/evaluate_browser_linear.py", "calibration_radii", "test_browser_linear.py",
              scope="experimental-interval", relation="finite-sample marginal calibration under exchangeable series"),
        entry("experimental-browser/roughness-stratification", "Prefix-roughness stratified residual calibration",
              "scripts/confirm_browser_calibration.py", "group_radii", "test_browser_calibration.py",
              scope="experimental-interval", relation="fixed prefix-only strata; independent synthetic confirmation"),
        entry("selection/training-case-ranking", "Training-case mean-MASE method ranking", "stages/train.py", "run",
              "test_pipeline_smoke.py", scope="selection", relation="legacy global ranking; separate from corpus selector"),
        entry("forecast/Naive", "Last-observation forecast", "scripts/run_forecastability_study.py", "evaluate",
              "test_forecastability.py", scope="forecast", artifact="Naive", relation="corpus control"),
        entry("interval/gaussian", "Gaussian marginal quantiles", "model/forecasters.py", "gaussian_quantiles",
              "test_forecasters.py", scope="interval"),
        entry("historical/streaming-smoothing-drift", "Archived smoothing-plus-drift predictor",
              "scripts/manuscript_replay.py", "legacy_point", "test_manuscript_replay.py",
              scope="historical-reconstruction", artifact="Theta",
              relation="reconstructs the archived streaming predictor; separate from current finite-history Theta"),
        entry("interval/aci-style", "Adaptive miscoverage-level feedback", "stages/streaming.py", "run",
              "test_stage_streaming.py", scope="interval", artifact="Theta+ACI",
              relation="preqts AdaptiveConformal wrapper; replay base"),
        entry("interval/pid-style", "Proportional-integral-derivative miscoverage feedback", "stages/streaming.py", "run",
              "test_stage_streaming.py", scope="interval", artifact="Theta+PID",
              relation="preqts ConformalPID wrapper; no published Conformal PID theorem is claimed"),
        entry("forecast/ridge-blind", "Ridge with observed target lags", "stages/streaming.py", "_ridge_batch",
              "test_stage_streaming.py", scope="covariate-protocol", artifact="Ridge (blind)"),
        entry("forecast/ridge-aware", "Ridge with admissible known-future covariates", "stages/streaming.py", "_ridge_batch",
              "test_stage_streaming.py", scope="covariate-protocol", artifact="Ridge+exog (aware)"),
    ])
    groups = {
        "stationarity": [
            ("adf", "adf", "Augmented Dickey-Fuller unit-root test"),
            ("kpss", "kpss", "KPSS stationarity test"),
            ("pp", "phillips_perron", "Phillips-Perron unit-root test"),
            ("dfgls", "dfgls", "GLS-detrended unit-root test"),
            ("zivot-andrews", "zivot_andrews", "Unit-root test with an endogenous structural break"),
            ("differencing", "ndiffs", "Sequential KPSS differencing-order selection"),
            ("seasonal-differencing", "nsdiffs", "STL-strength seasonal differencing selection"),
            ("joint-verdict", "combined_verdict", "Joint ADF and KPSS interpretation"),
        ],
        "autocorrelation": [
            ("bartlett", "bartlett_band", "Bartlett lag-dependent autocorrelation uncertainty band"),
            ("acf", "acf", "Autocorrelation function with lag uncertainty"),
            ("pacf", "pacf", "Partial autocorrelation by Durbin-Levinson recursion"),
            ("ljung-box", "ljung_box", "Ljung-Box portmanteau statistic"),
            ("box-pierce", "box_pierce", "Box-Pierce portmanteau statistic"),
            ("durbin-watson", "durbin_watson", "Durbin-Watson serial-correlation statistic"),
            ("lag-pairs", "lag_plot_pairs", "Lagged state-pair representation"),
        ],
        "seasonality": [
            ("periodogram", "periodogram", "Fourier periodogram"),
            ("welch", "welch", "Welch spectral-density estimate"),
            ("strength", "seasonal_strength", "Seasonal variance strength"),
            ("stl", "stl_decompose", "STL decomposition"),
            ("mstl", "mstl_decompose", "Multiple-seasonal STL decomposition"),
            ("subseries", "seasonal_subseries", "Seasonal subseries comparison"),
        ],
        "filters": [
            ("hp", "hodrick_prescott", "Hodrick-Prescott trend-cycle filter"),
            ("bk", "baxter_king", "Baxter-King band-pass filter"),
            ("cf", "christiano_fitzgerald", "Christiano-Fitzgerald band-pass filter"),
            ("emd", "emd", "Empirical mode decomposition"),
            ("ceemdan", "ceemdan", "Complete ensemble empirical mode decomposition"),
            ("cwt", "cwt_scalogram", "Continuous-wavelet scalogram"),
        ],
        "changepoints": [
            ("pelt", "pelt", "PELT segmentation"), ("binseg", "binseg", "Binary segmentation"),
            ("cusum", "cusum_stability", "OLS residual cumulative-sum stability test"),
            ("markov", "markov_regimes", "Markov-switching regime model"),
        ],
        "volatility": [
            ("arch", "arch_lm", "ARCH Lagrange-multiplier test"),
            ("garch", "garch", "GARCH conditional-variance model"),
            ("box-cox-mle", "box_cox", "Box-Cox profile-likelihood transform selection"),
            ("box-cox-guerrero", "box_cox", "Guerrero seasonal variance stabilization"),
            ("rolling", "rolling_volatility", "Rolling dispersion estimate"),
        ],
        "distribution": [
            ("moments", "summary", "Empirical moments"),
            ("jarque-bera", "summary", "Jarque-Bera normality test"),
            ("shapiro-wilk", "summary", "Shapiro-Wilk normality test"),
            ("kde", "kde_curve", "Kernel density estimate"),
            ("qq", "qq_points", "Normal quantile-quantile representation"),
            ("sample-entropy", "complexity", "Sample entropy"),
            ("permutation-entropy", "complexity", "Normalized permutation entropy"),
            ("spectral-entropy", "complexity", "Normalized spectral entropy"),
            ("bds", "complexity", "BDS independence statistic"),
            ("catch22", "catch22_features", "Canonical catch22 feature vector"),
        ],
        "fractal": [
            ("hurst-rs", "hurst", "Rescaled-range Hurst estimate"),
            ("dfa", "hurst", "Detrended fluctuation scaling estimate"),
            ("mfdfa", "mfdfa", "Multifractal detrended fluctuation analysis"),
            ("higuchi", "fractal_dimension", "Higuchi graph-dimension estimate"),
            ("katz", "fractal_dimension", "Katz graph-dimension estimate"),
            ("petrosian", "fractal_dimension", "Petrosian graph-dimension estimate"),
            ("dcca", "dcca_coefficient", "Detrended cross-correlation coefficient"),
        ],
        "nonlinear": [
            ("embedding", "time_delay_embed", "Time-delay state-space embedding"),
            ("correlation-dimension", "chaos_measures", "Grassberger-Procaccia correlation dimension"),
            ("lyapunov", "chaos_measures", "Rosenstein largest Lyapunov estimate"),
            ("rqa", "recurrence_quantification", "Recurrence quantification analysis"),
            ("iaaft", "iaaft_surrogate", "Iterative amplitude-adjusted Fourier surrogate"),
            ("zero-one", "zero_one_test", "Zero-one chaos diagnostic"),
        ],
        "causality": [
            ("cross-correlation", "cross_correlation", "Cross-correlation lead-lag estimate"),
            ("granger", "granger_causality", "Granger predictive-causality test"),
            ("engle-granger", "cointegration", "Engle-Granger residual cointegration test"),
            ("johansen", "cointegration", "Johansen trace-rank cointegration test"),
        ],
        "sequence": [
            ("matrix-profile", "matrix_profile", "Exact z-normalized Matrix Profile self-join"),
            ("fluss", "matrix_profile", "FLUSS candidate regime boundaries"),
            ("multiscale-entropy", "multiscale_entropy", "Fixed-tolerance multiscale sample entropy"),
            ("lempel-ziv", "sequence_report", "Binary Lempel-Ziv complexity with an explicit finite-length reference"),
            ("time-reversal-raw", "time_reversal", "Raw third-order lag-reversal statistic"),
            ("time-reversal-standardized", "time_reversal", "Standardized third-order lag-reversal statistic"),
        ],
        "atlas": [
            ("partition", "partition", "Deterministic disjoint-series partition assignment"),
            ("prefix-features", "prefix_features", "Prefix-only forecastability feature extraction"),
            ("by", "by_adjust", "Benjamini-Yekutieli dependent-test adjustment"),
            ("kendall", "associations", "Kendall rank association with disjoint-series confirmation"),
            ("selector", "study_summary", "Discovery-trained random-forest method selector"),
        ],
    }
    for module, methods in groups.items():
        test = {"sequence": "test_sequence_diagnostics.py", "atlas": "test_forecastability.py"}.get(
            module, "test_analysis_" + module + ".py")
        for key, symbol, name in methods:
            rows.append(entry("analysis/" + module + "/" + key, name, "analysis/" + module + ".py", symbol, test))
    strength = next(row for row in rows if row["id"] == "analysis/seasonality/strength")
    strength["implementation_aliases"] = [ENGINE + "analysis/stationarity.py::seasonal_strength"]
    return rows


def validate_analysis_api(rows, root=ROOT):
    covered = {row["implementation"] for row in rows}
    covered.update(alias for row in rows for alias in row.get("implementation_aliases", []))
    excluded = {ENGINE + "analysis/" + name.split(".")[0] + ".py::" + name.split(".")[1]
                for name in NON_METHOD_APIS}
    actual = set()
    for source in sorted((root / ENGINE / "analysis").glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        actual.update(source.relative_to(root).as_posix() + "::" + node.name for node in tree.body
                      if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"))
    if actual - covered - excluded:
        raise ValueError("Uninventoried analysis API: " + ", ".join(sorted(actual - covered - excluded)))


def validate(rows, root=ROOT):
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate numerical method identity")
    expected = {row["id"] for row in catalog()}
    if set(ids) != expected:
        raise ValueError("Numerical procedure inventory is incomplete or contains undeclared entries")
    for row in rows:
        source, symbol = row["implementation"].split("::", 1)
        path = root / source
        validation = root / row["validation"]
        if (not path.resolve().is_relative_to(root.resolve())
                or not validation.resolve().is_relative_to(root.resolve())
                or not path.is_file() or not validation.is_file()):
            raise ValueError(f"Missing source or validation: {row['id']}")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if not any(isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == symbol for node in tree.body):
            raise ValueError(f"Unimplemented callable: {row['implementation']}")
    covered = {row["artifact_name"] for row in rows if row["scope"] == "forecast"}
    fresh = json.loads((root / "data/derived/fresh-reevaluation.json").read_text(encoding="utf-8"))
    index = json.loads((root / "data/derived/validated-combinations.json").read_text(encoding="utf-8"))
    measured = {method["name"] for case in fresh["cases"] for method in case["methods"]}
    measured.update(method["name"] for cohort in index["cohorts"] for method in cohort["summary"])
    if measured - covered:
        raise ValueError("Measured forecasts missing from inventory: " + ", ".join(sorted(measured - covered)))
    validate_analysis_api(rows, root)


def document(root=ROOT):
    rows = catalog()
    validate(rows, root)
    paths = {row["implementation"].split("::", 1)[0] for row in rows}
    return {"schema": "chronoscope-method-inventory-v1",
            "scope": "Numerical procedures and execution identities; inventory counts do not establish novelty or teaching depth",
            "methods": rows,
            "non_method_analysis_apis": NON_METHOD_APIS,
            "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sorted(paths)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = document()
    serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    destination = ROOT / DESTINATION
    if args.write:
        destination.write_text(serialized, encoding="utf-8", newline="\n")
    elif not destination.is_file() or destination.read_text(encoding="utf-8") != serialized:
        raise SystemExit("Method inventory is stale; run scripts/method_inventory.py --write and review the change")
    print(f"Method inventory: {len(result['methods'])} procedures and execution identities, all source-bound")


if __name__ == "__main__":
    main()
