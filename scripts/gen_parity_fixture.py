"""Generate the TS<->Python parity fixture for the live classical engine.

Runs the Python classical forecasters on a fixed synthetic series and dumps their point + interval
output to frontend/src/lib/__fixtures__/parity.json. A vitest asserts the TypeScript live engine
reproduces this within tolerance, so the browser's "live" classical forecasts are the same computation
the offline pipeline does, not a decorative approximation.

Run (from the repo root, with the pipeline venv):
    .venv-pipeline/Scripts/python.exe scripts/gen_parity_fixture.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-pipeline"))

from chronoscopelab.model.forecasters import METHODS, normal_ppf  # noqa: E402

OUT = ROOT / "frontend" / "src" / "lib" / "__fixtures__" / "parity.json"
LEVELS = (0.1, 0.5, 0.9)


def make_series(kind: str, n: int, m: int) -> list[float]:
    """Deterministic series (no RNG) so the fixture is stable and TS can reproduce the input exactly."""
    t = np.arange(n, dtype=float)
    if kind == "seasonal":
        y = 50 + 10 * np.sin(2 * np.pi * t / m)
    elif kind == "trend_seasonal":
        y = 50 + 0.3 * t + 8 * np.sin(2 * np.pi * t / m)
    elif kind == "noisy_seasonal":
        # a fixed pseudo-noise via a deterministic function (reproducible in TS)
        noise = 2.0 * np.sin(t * 12.9898) * np.cos(t * 78.233)
        y = 40 + 6 * np.sin(2 * np.pi * t / m) + noise
    else:
        raise ValueError(kind)
    return [round(float(v), 6) for v in y]


def main() -> int:
    cases = [
        {"kind": "seasonal", "n": 96, "m": 12, "h": 12},
        {"kind": "trend_seasonal", "n": 120, "m": 12, "h": 12},
        {"kind": "noisy_seasonal", "n": 144, "m": 24, "h": 24},
    ]
    fixture = {"levels": list(LEVELS), "cases": []}
    for c in cases:
        y = make_series(c["kind"], c["n"], c["m"])
        methods = []
        for name, family, fn in METHODS:
            point, sigma = fn(np.asarray(y, dtype=float), c["m"], c["h"])
            methods.append({
                "name": name,
                "point": [round(float(v), 5) for v in point],
                "sigma": round(float(sigma), 6),
            })
        fixture["cases"].append({**c, "y": y, "methods": methods})

    # A few normal_ppf reference values for the TS quantile function.
    fixture["normal_ppf"] = {str(p): round(normal_ppf(p), 6) for p in (0.1, 0.25, 0.5, 0.75, 0.9, 0.975)}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({len(fixture['cases'])} cases, {len(METHODS)} methods each)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
