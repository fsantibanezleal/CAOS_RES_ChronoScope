"""CONTRACT 2 - artifact (pipeline -> web). The manifest is the authoritative, versioned record of a baked
case: its series descriptors, seed, engine + version, the artifact pointer + byte size, the lane/gate
verdict, CONTRACT-1 flags, and the evaluation metrics. The web loads ONLY manifests + artifacts;
frontend/src/lib/contract.types.ts mirrors this schema so a drift fails the build. A flat index.json
inventories every case (ADR-0057 default)."""
from __future__ import annotations

from typing import Any

from .. import __version__
from ..data.provenance import SOURCES
from .trace import TRACE_SCHEMA

MANIFEST_SCHEMA = "chronoscope.manifest/v1"
INDEX_SCHEMA = "chronoscope.index/v1"

ENGINE_MODEL = (
    "forecasting method ladder: classical numpy (seasonal-naive, SES, Holt, Holt-Winters, Theta; live-capable) "
    "+ statistical (AutoARIMA, AutoETS, AutoTheta via statsforecast; offline, when installed)"
)


STREAMING_SCHEMA = "chronoscope-streaming-v1"
ANALYSIS_SCHEMA = "chronoscope.analysis/v1"


def build_case_manifest(
    *,
    case: Any,
    feature: Any,
    seed: int,
    artifact_rel: str,
    trace_bytes: int,
    gate: dict,
    flags: list[dict],
    eval_metrics: dict,
    analysis_rel: str | None = None,
    analysis_bytes: int | None = None,
    streaming_rel: str | None = None,
    streaming_bytes: int | None = None,
) -> dict:
    # Deterministic: a pure function of (case, seed). No wall-clock (would dirty git on re-run).
    best = eval_metrics.get("best_method")
    # The analysis artifact (the "understand the series" half of CONTRACT 2) is optional so older cases
    # without a baked analysis still validate; when present the web Understand workbench reads it.
    analysis_block = (
        {"path": analysis_rel, "format": "json", "analysis_schema": ANALYSIS_SCHEMA, "bytes": analysis_bytes}
        if analysis_rel is not None else None
    )
    # The streaming bench artifact (preqts prequential trajectories): aggregate metrics only (license-safe).
    streaming_block = (
        {"path": streaming_rel, "format": "json", "streaming_schema": STREAMING_SCHEMA, "bytes": streaming_bytes}
        if streaming_rel is not None else None
    )
    # Provenance block: the source's license + the public-redistribution verdict (the export guard uses it).
    source_id = getattr(case, "source", "synthetic")
    src = SOURCES.get(source_id)
    provenance_block = {
        "source": source_id,
        "license": src.license if src else "unknown",
        "citation": src.citation if src else "",
        "public_artifact_ok": bool(src.public_artifact_ok) if src else False,
    }
    return {
        "schema": MANIFEST_SCHEMA,
        "case_id": case.id,
        "category": case.category,
        "real_or_synthetic": case.real_or_synthetic,
        "expected_band": case.expected_band,
        "engine": {"package": "chronoscopelab", "version": __version__, "model": ENGINE_MODEL},
        "provenance": provenance_block,
        "analysis_artifact": analysis_block,
        "streaming_artifact": streaming_block,
        "series": {
            "n_obs": feature.n_obs,
            "seasonality": feature.seasonality,
            "horizon": case.horizon,
            "source": case.real_or_synthetic,
            "mean": round(feature.mean, 4),
            "std": round(feature.std, 4),
            "trend_slope": round(feature.trend_slope, 6),
            "seasonal_strength": round(feature.seasonal_strength, 4),
            "acf1": round(feature.acf1, 4),
            "pct_zeros": round(feature.pct_zeros, 4),
        },
        "seed": seed,
        "artifact": {"path": artifact_rel, "format": "json", "trace_schema": TRACE_SCHEMA, "bytes": trace_bytes},
        "lane": gate["lane"],
        "gate": gate,
        "flags": flags,
        "best_method": best,
        "metrics": {
            "best_mase": eval_metrics.get("best_mase"),
            "n_methods": len(eval_metrics.get("methods", {})),
            "nominal_coverage": eval_metrics.get("nominal_coverage"),
        },
    }


def build_index(entries: list[dict]) -> dict:
    """entries: [{case_id, category, manifest_path}] -> the flat authoritative inventory."""
    return {
        "schema": INDEX_SCHEMA,
        "engine_version": __version__,
        "n_cases": len(entries),
        "cases": sorted(entries, key=lambda e: e["case_id"]),
    }
