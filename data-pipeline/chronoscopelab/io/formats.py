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
    """Write compact, strict JSON (no NaN/Inf); return the byte size (used by the gate + manifest).

    The ``mkdir`` is retried against a transient Windows transactional-NTFS glitch (WinError 6714) that can
    appear when numba (statsforecast) and CUDA (torch) run in the same process; see
    docs/architecture/09_known-issues.md for the deep-tier baking caveat and its subprocess workaround.
    """
    import os
    import time

    p = Path(path)
    for attempt in range(5):
        try:
            os.makedirs(p.parent, exist_ok=True)
            break
        except OSError as exc:
            if getattr(exc, "winerror", None) == 6714 and attempt < 4:
                time.sleep(0.1)
                continue
            if p.parent.is_dir():
                break
            raise
    data = json.dumps(_sanitize(obj), separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    encoded = data.encode("utf-8")
    p.write_bytes(encoded)
    return len(encoded)


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
