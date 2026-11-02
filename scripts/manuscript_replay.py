"""Reconstruct the historical one-step study and export every online update.

This is a reproduction of the archived smoothing-plus-drift adaptation, not the
current finite-history Theta method. Additional settings are sensitivity analyses,
not independent confirmations of the historical experiment. Run in the product venv.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))
from chronoscopelab.cases.forecast_cases import CASES, build_series  # noqa: E402
from chronoscopelab.model.forecasters import normal_ppf, _opt_alpha, _ses_run  # noqa: E402
import preqts.conformal as conformal  # noqa: E402

OUTPUT = ROOT / "manuscripts/prequential-streaming-conformal/evidence/replay.json"
METHODS = ("SeasonalNaive", "Theta", "Theta+ACI", "Theta+PID")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def legacy_point(y):
    """All 19 SES candidates in parallel; same SSE selection as the archived code."""
    grid = np.linspace(.05, .95, 19)
    level = np.full(19, y[0])
    sse = np.zeros(19)
    residuals = []
    for value in y[1:]:
        residuals.append(value - level)
        sse += (value - level) ** 2
        level = grid * value + (1 - grid) * level
    best = int(np.argmin(sse))
    slope = float(np.polyfit(np.arange(len(y)), y, 1)[0])
    return float(level[best] + .5 * slope), float(np.std(np.asarray(residuals)[:, best]))


def base_paths(y, lag, warmup):
    paths = {"Theta": [], "SeasonalNaive": []}
    for t in range(warmup, len(y)):
        prefix = y[:t]
        point, sigma = legacy_point(prefix)
        # Independently check the vectorized calculation against the scalar
        # archived equation at first, middle and last cutoffs of every series.
        if t in {warmup, (warmup + len(y)) // 2, len(y) - 1}:
            fitted, level = _ses_run(prefix, _opt_alpha(prefix))
            expected = float(level + .5 * np.polyfit(np.arange(t), prefix, 1)[0])
            np.testing.assert_allclose([point, sigma], [expected, np.std(prefix[1:] - fitted[1:])], rtol=1e-12, atol=1e-10)
        paths["Theta"].append([point, sigma])
        paths["SeasonalNaive"].append([float(prefix[-lag]), float(np.std(prefix[lag:] - prefix[:-lag]))])
    return paths


def evaluate(y, paths, warmup, coverage=.8, gain=1., controller="raw", keep_rows=False):
    scores = deque(maxlen=200)
    target = 1 - coverage
    alpha = target
    integral, last = 0., None
    levels = np.array([target / 2, .5, 1 - target / 2])
    z = normal_ppf(float(levels[-1]))
    rows, covered, widths, wql, interval_scores = [], [], [], [], []
    for t, (point, sigma) in enumerate(paths, warmup):
        half = max(z * sigma, 1e-8) if controller != "raw" else z * sigma
        before = alpha
        qhat = float(np.quantile(scores, 1 - alpha)) if scores and controller != "raw" else 1.
        lower, upper = point - qhat * half, point + qhat * half
        value = float(y[t])  # revealed only after the interval is fixed
        hit = lower <= value <= upper
        miss = float(not hit)
        score = abs(value - point) / max(half, 1e-8)
        derivative = 0. if last is None else target - miss - last
        if controller != "raw":
            scores.append(score)
            error = target - miss
            if controller == "ACI":
                alpha = float(np.clip(alpha + .02 * gain * error, 1e-4, 1 - 1e-4))
            elif controller == "PID":
                integral += error
                alpha = float(np.clip(target + gain * (.05 * error + .02 * integral + .02 * derivative), 1e-4, 1 - 1e-4))
            else:
                raise ValueError(controller)
            last = error
        q = np.array([lower, point, upper])
        residual = value - q
        loss = float(2 * np.sum(np.maximum(levels * residual, (levels - 1) * residual)) / abs(value)) if value else None
        interval_score = upper - lower + 2 / target * ((lower - value) if value < lower else (value - upper) if value > upper else 0.)
        covered.append(float(hit))
        widths.append(upper - lower)
        interval_scores.append(interval_score)
        wql.append(loss)
        if keep_rows:
            rows.append([t, value, lower, point, upper, score, qhat, before, alpha, integral, derivative, len(scores), float(hit), loss])
    rolling = [round(float(np.mean(covered[max(0, i - 24):i + 1])), 5) for i in range(len(covered))]
    valid_wql = [v for v in wql if v is not None]
    result = {"final_coverage": float(np.mean(covered)), "rolling_summary_error": abs(float(np.mean(rolling)) - coverage),
              "mean_rolling_absolute_error": float(np.mean(np.abs(np.asarray(rolling) - coverage))),
              "final_absolute_coverage_error": abs(float(np.mean(covered)) - coverage),
              "mean_width": float(np.mean(widths)), "mean_interval_score": float(np.mean(interval_scores)),
              "mean_wql": float(np.mean(valid_wql)) if valid_wql else None,
              "wql_available_steps": len(valid_wql), "steps": len(covered), "rolling_coverage": rolling}
    if keep_rows:
        result["rows"] = rows
    return result


def build():
    sources = ["data-pipeline/chronoscopelab/cases/forecast_cases.py", "data-pipeline/chronoscopelab/model/forecasters.py", "scripts/manuscript_replay.py"]
    source_hashes = {p: sha((ROOT / p).read_bytes()) for p in sources}
    input_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p.read_bytes()) for p in sorted((ROOT / "data/examples").glob("*.csv"))}
    cases, sensitivity, repeats = [], [], []
    for definition in sorted(CASES, key=lambda c: c.id):
        cid = definition.id
        mp = ROOT / f"data/derived/manifests/{cid}.json"
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        archive_path = ROOT / f"data/derived/{cid}/streaming.json"
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
        seed = manifest["seed"]
        spec = build_series(definition, seed, ROOT / "data/examples")
        y = np.asarray(spec.y, dtype=float)
        trace_path = ROOT / f"data/derived/{cid}/trace.json"
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        prefix = y[:-trace["horizon"]]
        assert len(prefix) == trace["history_len"]
        np.testing.assert_allclose(prefix[trace["history_index"]], trace["history"], rtol=0, atol=.000051)
        np.testing.assert_allclose(y[-trace["horizon"]:], trace["actual"], rtol=0, atol=.000051)
        warmup = min(max(2 * definition.seasonality, 20), max(1, len(y) // 3))
        paths = base_paths(y, definition.seasonality, warmup)
        methods = {}
        for name in METHODS:
            base = "SeasonalNaive" if name == "SeasonalNaive" else "Theta"
            control = name.split("+")[-1] if "+" in name else "raw"
            result = evaluate(y, paths[base], warmup, controller=control, keep_rows=True)
            original = archive["methods"][name]
            np.testing.assert_allclose(result["rolling_coverage"], original["rolling_coverage"], rtol=0, atol=1e-5)
            assert round(result["final_coverage"], 4) == original["final"]["coverage"], (cid, name)
            if result["mean_wql"] is not None:
                np.testing.assert_allclose(result["mean_wql"], original["final"]["wql"], atol=.000011, rtol=0)
            methods[name] = result
        cases.append({"case_id": cid, "seed": seed, "seasonality": definition.seasonality, "warmup": warmup,
                      "source_values": y.tolist(), "source_values_sha256": sha(y.astype('<f8').tobytes()),
                      "historical_artifact_sha256": sha(archive_path.read_bytes()), "case_manifest_sha256": sha(mp.read_bytes()),
                      "trace_sha256": sha(trace_path.read_bytes()), "source_id": definition.source,
                      "methods": methods})
        for base in paths:
            for coverage in (.7, .8, .9):
                for controller in ("raw", "ACI", "PID"):
                    for gain in ((1.,) if controller == "raw" else (.5, 1., 2.)):
                        r = evaluate(y, paths[base], warmup, coverage, gain, controller)
                        sensitivity.append({"case_id": cid, "base": base, "coverage": coverage, "controller": controller, "gain": gain,
                                            **{k: v for k, v in r.items() if k != "rolling_coverage"}})
        if definition.real_or_synthetic == "synthetic":
            for repeat_seed in (43, 44):
                yr = np.asarray(build_series(definition, repeat_seed, ROOT / "data/examples").y, dtype=float)
                rp = base_paths(yr, definition.seasonality, warmup)
                for controller in ("raw", "ACI", "PID"):
                    r = evaluate(yr, rp["Theta"], warmup, controller=controller)
                    repeats.append({"case_id": cid, "seed": repeat_seed, "source_values_sha256": sha(yr.astype('<f8').tobytes()),
                                    "controller": controller, **{k: v for k, v in r.items() if k != "rolling_coverage"}})
        print(f"reproduced {cid}: {len(y)-warmup} cutoffs, archived coverage and WQL matched", flush=True)
    summary = {name: {key: float(np.mean([c["methods"][name][key] for c in cases]))
                     for key in ("rolling_summary_error", "mean_rolling_absolute_error", "final_absolute_coverage_error", "final_coverage")} for name in METHODS}
    return {"schema": "chronoscope.manuscript-replay/v1", "protocol": {"horizon": 1, "score_buffer": 200,
            "historical_levels": [.1, .5, .9], "historical_coverage": .8, "gains": {"ACI": .02, "PID": [.05, .02, .02]},
            "sensitivity_coverage": [.7, .8, .9], "gain_multipliers": [.5, 1., 2.], "additional_generated_seeds": [43, 44],
            "row_columns": ["cutoff", "actual", "lower", "point", "upper", "normalized_score", "multiplier", "alpha_before", "alpha_after", "integral_after", "derivative", "buffer_size_after", "covered", "wql"]},
            "source_sha256": source_hashes, "input_sha256": input_hashes,
            "package": {"preqts": importlib.metadata.version("preqts"), "numpy": np.__version__, "conformal_source_sha256": sha(inspect.getsource(conformal).encode())},
            "cases": cases, "summary": summary, "sensitivity": sensitivity, "generated_repeats": repeats,
            "timing_scope": "Numerical reconstruction only; original per-call hardware and latencies cannot be recovered."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true", help="Recompute numerical evidence and compare to the committed payload")
    args = parser.parse_args()
    started = time.perf_counter()
    result = build()
    payload = json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    if args.check:
        assert payload == args.output.read_bytes(), "Numerical replay payload changed"
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(payload)
    print(json.dumps({"ok": True, "cases": len(result['cases']), "sensitivity_rows": len(result['sensitivity']),
                      "repeat_rows": len(result['generated_repeats']), "sha256": sha(payload),
                      "environment": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform()},
                      "reconstruction_seconds": time.perf_counter() - started}, indent=2))


if __name__ == "__main__":
    main()
