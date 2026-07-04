"""CONTRACT 1 - ingestion (raw -> pipeline). The *bring-your-own-data* gate.

Declares the required schema of a long-format time-series table and an EXPLICIT missing/outlier policy.
A series is ACCEPTED iff it passes; bad series are REJECTED with a reason (never silently coerced);
plausible-but-suspicious series are FLAGGED (accepted, but the manifest records the flag). This is what
lets ChronoScope be pointed at NEW data instead of only replaying baked cases. Documented in
data/README.md.

Schema (long format, one row per (series, timestamp)):
    unique_id : str   series identifier
    ds        : str   timestamp (ISO-8601 or any sortable label); must be strictly increasing per series
    y         : float target value (finite; NaN allowed up to MAX_NAN_FRAC, then flagged)
Optional extra columns are treated as covariates and passed through.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

REQUIRED_COLUMNS: tuple[str, ...] = ("unique_id", "ds", "y")

MIN_OBS = 8                 # a series shorter than this cannot be backtested meaningfully -> REJECT
MAX_NAN_FRAC = 0.30         # more than 30% missing target -> REJECT; any missing -> FLAG
OUTLIER_Z = 8.0             # |z-score| above this on the target -> FLAG (not reject); robust MAD-based


@dataclass
class SeriesRecord:
    """A validated series: identifier, timestamps, target, and any covariate columns."""

    unique_id: str
    ds: list[str]
    y: list[float]
    covariates: dict[str, list[float]] = field(default_factory=dict)


@dataclass
class ContractReport:
    accepted: list[SeriesRecord]
    rejected: list[dict[str, Any]]
    flagged: list[dict[str, Any]]

    @property
    def ok(self) -> bool:
        return len(self.accepted) > 0

    def summary(self) -> str:
        return f"{len(self.accepted)} accepted, {len(self.rejected)} rejected, {len(self.flagged)} flagged"


def _mad_zscores(y: list[float]) -> list[float]:
    """Robust z-scores using the median and MAD (finite values only; NaN -> 0 contribution)."""
    finite = [v for v in y if not (math.isnan(v) or math.isinf(v))]
    if len(finite) < 3:
        return [0.0] * len(y)
    med = sorted(finite)[len(finite) // 2]
    abs_dev = sorted(abs(v - med) for v in finite)
    mad = abs_dev[len(abs_dev) // 2] or 1e-9
    return [0.0 if (math.isnan(v) or math.isinf(v)) else abs(v - med) / (1.4826 * mad) for v in y]


def validate_series(unique_id: str, ds: list[str], y_raw: list[Any],
                    covariates: dict[str, list[float]] | None = None) -> tuple[SeriesRecord | None, dict | None, dict | None]:
    """Validate a single series. Returns (record|None, rejection|None, flag|None)."""
    try:
        y = [float(v) for v in y_raw]
    except (TypeError, ValueError):
        return None, {"unique_id": unique_id, "reason": "non-numeric value in y"}, None
    if len(y) < MIN_OBS:
        return None, {"unique_id": unique_id, "reason": f"only {len(y)} obs (< MIN_OBS={MIN_OBS})"}, None
    n_nan = sum(1 for v in y if math.isnan(v) or math.isinf(v))
    if n_nan / len(y) > MAX_NAN_FRAC:
        return None, {"unique_id": unique_id, "reason": f"{n_nan}/{len(y)} missing (> {MAX_NAN_FRAC:.0%})"}, None

    flag: dict | None = None
    reasons: list[str] = []
    if n_nan > 0:
        reasons.append(f"{n_nan} missing target value(s)")

    ds = list(ds)
    covariates = covariates or {}
    if ds != sorted(ds):
        reasons.append("timestamps not strictly increasing (sorted on ingest)")
        order = sorted(range(len(ds)), key=lambda i: ds[i])
        ds = [ds[i] for i in order]
        y = [y[i] for i in order]
        covariates = {c: [vals[i] for i in order] for c, vals in covariates.items()}

    n_out = sum(1 for z in _mad_zscores(y) if z > OUTLIER_Z)
    if n_out > 0:
        reasons.append(f"{n_out} value(s) with robust |z| > {OUTLIER_Z:g}")
    if reasons:
        flag = {"unique_id": unique_id, "flag": "; ".join(reasons)}

    record = SeriesRecord(unique_id=unique_id, ds=ds, y=y, covariates=covariates)
    return record, None, flag


def validate_rows(raw_rows: list[dict[str, Any]]) -> ContractReport:
    """Apply CONTRACT 1 to long-format rows (e.g. from a CSV). Pure; deterministic; no I/O."""
    accepted: list[SeriesRecord] = []
    rejected: list[dict[str, Any]] = []
    flagged: list[dict[str, Any]] = []

    if raw_rows:
        missing = [c for c in REQUIRED_COLUMNS if c not in raw_rows[0]]
        if missing:
            return ContractReport([], [{"reason": f"missing required columns: {missing}"}], [])

    grouped: dict[str, dict[str, list]] = {}
    cov_cols = [c for c in (raw_rows[0].keys() if raw_rows else []) if c not in REQUIRED_COLUMNS]
    for row in raw_rows:
        uid = str(row.get("unique_id", "series"))
        g = grouped.setdefault(uid, {"ds": [], "y": [], **{c: [] for c in cov_cols}})
        g["ds"].append(str(row.get("ds", "")))
        g["y"].append(row.get("y"))
        for c in cov_cols:
            try:
                g[c].append(float(row.get(c)))
            except (TypeError, ValueError):
                g[c].append(math.nan)

    for uid, g in grouped.items():
        # Pass original order so validate_series can detect + flag unsorted timestamps (and sort them).
        covs = {c: g[c] for c in cov_cols}
        rec, rej, flag = validate_series(uid, g["ds"], g["y"], covs)
        if rec is not None:
            accepted.append(rec)
        if rej is not None:
            rejected.append(rej)
        if flag is not None:
            flagged.append(flag)
    return ContractReport(accepted=accepted, rejected=rejected, flagged=flagged)
