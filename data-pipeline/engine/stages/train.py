"""Stage 3 - train (OFFLINE): learn a global method selector from a backtest across the TRAINING cases.

Ranks each CLASSICAL method by its mean MASE over the training cases (each scored out-of-sample by the
evaluate stage) and records a default recommendation. Uses the classical ladder only, so training stays
fast and the ranking is independent of which heavy engines happen to be installed. Leakage-safe: the
ranking is computed on training cases only; each case's own manifest still reports that case's held-out
metrics. Saved to models/selector.json.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..io.formats import write_json
from ..io.schema import SeriesSpec
from ..model.forecasters import classical_forecasters
from . import evaluate


def run(train_specs: list[SeriesSpec], models_dir: str, quantile_levels: tuple[float, ...]) -> dict:
    fcs = classical_forecasters()
    per_method: dict[str, list[float]] = {fc.name: [] for fc in fcs}
    for spec in train_specs:
        ev = evaluate.run(spec, quantile_levels, forecasters=fcs)
        for name, v in ev["methods"].items():
            if v["mase"] == v["mase"]:  # skip NaN
                per_method[name].append(v["mase"])

    ranking = sorted(
        ((name, float(np.mean(vals)) if vals else float("inf")) for name, vals in per_method.items()),
        key=lambda kv: kv[1],
    )
    default = ranking[0][0] if ranking else "SeasonalNaive"
    model = {
        "kind": "method-selector",
        "metric": "mean_mase_over_training_cases",
        "scope": "classical",
        "ranking": [[name, round(mase, 5)] for name, mase in ranking],
        "default_method": default,
        "n_train_cases": len(train_specs),
    }
    Path(models_dir).mkdir(parents=True, exist_ok=True)
    write_json(Path(models_dir) / "selector.json", model)
    return model
