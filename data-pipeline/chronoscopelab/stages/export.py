"""Stage 6 - export (CONTRACT 2): write the compact trace artifact + the case manifest. The manifest records
the measured lane/gate verdict, the artifact byte size, the CONTRACT-1 flags, and the evaluation metrics."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.gate import classify_lane
from ..core.manifest import build_case_manifest
from ..core.trace import build_trace
from ..io.formats import write_json
from ..io.schema import ForecastResult


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
    trace = build_trace(result, actual, eval_metrics)
    artifact_rel = f"{case.id}/trace.json"
    trace_bytes = write_json(Path(derived_dir) / artifact_rel, trace)
    gate = classify_lane(pure_python=True, wheels={"numpy"}, run_ms=run_ms, trace_bytes=trace_bytes)

    # The "understand the series" half of CONTRACT 2: the baked analysis panel the web Understand workbench
    # reads. Written as a separate artifact (it is large and only the App's Understand half needs it).
    analysis_rel = analysis_bytes = None
    if analysis is not None:
        analysis_rel = f"{case.id}/analysis.json"
        analysis_bytes = write_json(Path(derived_dir) / analysis_rel, analysis)

    manifest = build_case_manifest(
        case=case, feature=feature, seed=seed,
        artifact_rel=artifact_rel, trace_bytes=trace_bytes, gate=gate, flags=flags, eval_metrics=eval_metrics,
        analysis_rel=analysis_rel, analysis_bytes=analysis_bytes,
    )
    write_json(Path(manifests_dir) / f"{case.id}.json", manifest)
    return manifest
