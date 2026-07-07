"""Stage 6 - export (CONTRACT 2): write the compact trace artifact + the case manifest. The manifest records
the measured lane/gate verdict, the artifact byte size, the CONTRACT-1 flags, and the evaluation metrics."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.gate import classify_lane
from ..core.manifest import build_case_manifest
from ..core.trace import build_trace
from ..data.provenance import public_artifact_ok
from ..io.formats import write_json
from ..io.schema import ForecastResult

# Keys inside an analysis panel that are point-wise ARRAYS reconstructing (a transform of) the source series.
# For a local-only-licensed source these are dropped; scalar verdicts (test stats, exponents) still ship.
_ARRAY_KEYS = frozenset({
    "acf", "pacf", "freqs", "power", "grid", "density", "theoretical", "sample", "energy_by_period",
    "periods", "trend", "cycle", "imfs", "residual", "seasonal", "hq", "alpha", "f_alpha", "q",
    "rolling_mean", "rolling_std", "smoothed_probabilities", "most_likely", "segments",
})


def _redact_analysis(analysis: dict) -> dict:
    """Recursively drop the point-wise array fields, keeping the scalar verdicts (license-safe aggregate)."""
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items() if k not in _ARRAY_KEYS}
        if isinstance(obj, list):
            # keep short scalar lists (e.g. break indices); drop long series-length arrays
            return obj if len(obj) <= 16 else f"<redacted array, len={len(obj)}>"
        return obj

    out = _clean(analysis)
    out["_redacted"] = "raw series-derived arrays omitted (source license forbids public redistribution)"
    return out


def run(
    *,
    case: Any,
    feature: Any,
    result: ForecastResult,
    actual: list[float],
    eval_metrics: dict,
    seed: int,
    run_ms: float,
    flags: list[dict],
    derived_dir: str,
    manifests_dir: str,
    analysis: dict | None = None,
) -> dict:
    # License guard: for a source whose license forbids public redistribution, the raw series excerpt and the
    # per-step forecast/analysis paths are omitted from the committed artifacts - only aggregate metrics ship.
    source_id = getattr(case, "source", "synthetic")
    redact_raw = not public_artifact_ok(source_id)

    trace = build_trace(result, actual, eval_metrics, redact_raw=redact_raw)
    artifact_rel = f"{case.id}/trace.json"
    trace_bytes = write_json(Path(derived_dir) / artifact_rel, trace)
    gate = classify_lane(pure_python=True, wheels={"numpy"}, run_ms=run_ms, trace_bytes=trace_bytes)

    # The "understand the series" half of CONTRACT 2: the baked analysis panel the web Understand workbench
    # reads. Written as a separate artifact (it is large and only the App's Understand half needs it). For a
    # local-only source we ship only the license-safe scalar verdicts, not the full series-derived arrays.
    analysis_rel = analysis_bytes = None
    if analysis is not None:
        payload = _redact_analysis(analysis) if redact_raw else analysis
        analysis_rel = f"{case.id}/analysis.json"
        analysis_bytes = write_json(Path(derived_dir) / analysis_rel, payload)

    manifest = build_case_manifest(
        case=case, feature=feature, seed=seed,
        artifact_rel=artifact_rel, trace_bytes=trace_bytes, gate=gate, flags=flags, eval_metrics=eval_metrics,
        analysis_rel=analysis_rel, analysis_bytes=analysis_bytes,
    )
    write_json(Path(manifests_dir) / f"{case.id}.json", manifest)
    return manifest
