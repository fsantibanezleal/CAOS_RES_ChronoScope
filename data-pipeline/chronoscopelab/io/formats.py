"""Standard-format readers/writers. EXAMPLE: CSV in (params), JSON out (compact committed artifact). A real product
adds the formats its domain demands here (parquet/npz/.vtk/.vtu/.h5/GeoTIFF) — never a bespoke ad-hoc format."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _sanitize(obj: Any) -> Any:
    """Replace NaN/Inf floats with None so the artifact is STRICT JSON (JSON.parse-safe in the browser)."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def write_json(path: str | Path, obj: Any) -> int:
    """Write compact, strict JSON (no NaN/Inf); return the byte size (used by the gate + manifest)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(_sanitize(obj), separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    encoded = data.encode("utf-8")
    p.write_bytes(encoded)
    return len(encoded)


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
