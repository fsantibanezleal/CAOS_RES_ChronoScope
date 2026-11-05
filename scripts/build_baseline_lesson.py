"""Author the bilingual seasonal-reference lesson; execution is a separate step."""
from __future__ import annotations

import hashlib
import json
import re
from pprint import pformat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "01-forecast-decisions"
NAME = "01-baseline"
PINS = ["numpy==2.4.6", "matplotlib==3.10.8", "preqts==0.3.0"]
SOURCES = [
    "https://doi.org/10.24432/C58C86",
    "https://otexts.com/fpp3/toolbox.html",
    "https://doi.org/10.1016/j.ijforecast.2006.03.001",
    "https://pypi.org/project/preqts/0.3.0/",
]
CODES = {
    "setup": '''# Import the released API; the lesson does not install or redefine a method.
from pathlib import Path
import csv
from datetime import datetime
import importlib.metadata
import numpy as np
import matplotlib.pyplot as plt
from preqts import SeasonalNaive, Stream, run_prequential
from preqts.metrics import seasonal_naive_mae
root = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "VERSION").is_file())
plt.rcParams.update({"figure.figsize": (9, 3), "figure.dpi": 95, "font.size": 10})
for package in ("numpy", "matplotlib", "preqts"):
    print(package, importlib.metadata.version(package))
''',
    "data": '''# Read the authentic hourly excerpt and inspect its time axis before forecasting.
with (root / "data/examples/electricity_sample.csv").open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))
times = [datetime.fromisoformat(r["ds"]) for r in rows]
y = np.array([float(r["y"]) for r in rows])
assert {r["unique_id"] for r in rows} == {"MT_010"}
assert np.isfinite(y).all()
assert all((b-a).total_seconds() == 3600 for a, b in zip(times, times[1:]))
m, warmup, horizon = 24, 96, 48
cut = len(y) - horizon
history, actual = y[:cut], y[cut:]
print("rows / prefix / held out:", len(y), len(history), len(actual))
print("first / last:", times[0].isoformat(), times[-1].isoformat())
''',
    "raw_plot": '''# Keep the reserved final block visible without passing it into the fit.
fig, ax = plt.subplots()
ax.plot(times, y, color="0.3")
ax.axvline(times[cut], color="tab:red", linestyle="--", label=words["cut"])
ax.set(xlabel=words["time"], ylabel=words["value"])
ax.legend()
fig.autofmt_xdate()
fig.tight_layout()
plt.show()
''',
    "fit": '''# Start from the prefix, then request all three quantile columns together.
model = SeasonalNaive(seasonality=m, widen=True)
model.start(history)
q = model.predict(horizon, [0.1, 0.5, 0.9])
assert q.shape == (horizon, 3) and np.isfinite(q).all()
assert (np.diff(q, axis=1) >= 0).all()
print("first predicted row:", np.round(q[0], 4))
print("manual first point / package median:", history[-m], q[0, 1])
assert q[0, 1] == history[-m]
''',
    "score": '''# Fix the historical scale once; the target is used only after prediction.
scale = seasonal_naive_mae(y[:warmup], m)
if scale <= 0:
    raise ValueError("The warmup seasonal error scale must be positive")
mae = float(np.mean(np.abs(actual - q[:, 1])))
coverage = float(np.mean((actual >= q[:, 0]) & (actual <= q[:, 2])))
print("fixed warmup scale:", f"{scale:.6f}")
print("48-step MAE / MASE / interval coverage:", f"{mae:.6f}", f"{mae/scale:.6f}", f"{coverage:.6f}")
fig, ax = plt.subplots()
ax.plot(times[cut-72:cut], history[-72:], label=words["history"])
ax.plot(times[cut:], actual, color="black", label=words["actual"])
ax.plot(times[cut:], q[:, 1], label=words["forecast"])
ax.fill_between(times[cut:], q[:, 0], q[:, 2], alpha=.2, label=words["interval"])
ax.set(xlabel=words["time"], ylabel=words["value"])
ax.legend(ncol=2, fontsize=8)
fig.autofmt_xdate()
fig.tight_layout()
plt.show()
''',
    "sensitivity": '''# Change only the model period, keeping the stream and metric period fixed.
periods = (1, 12, 24, 48)
stream = Stream(y, seasonality=m, name="MT_010-hourly-sum")
results = [run_prequential(SeasonalNaive(p), stream, horizon=1, warmup=warmup) for p in periods]
print("scales for all model periods:", [round(r.scale, 6) for r in results])
for p, r in zip(periods, results, strict=True):
    print("period / forecasts / MASE / coverage:", p, len(r.cutoffs),
          f"{np.mean(r.mase):.6f}", f"{np.mean(r.coverage):.6f}")
fig, ax = plt.subplots()
ax.bar([str(p) for p in periods], [np.mean(r.mase) for r in results])
ax.set(xlabel=words["period"], ylabel="MASE")
fig.tight_layout()
plt.show()
''',
    "failure": '''# A declared synthetic intervention isolates the lag after a level change.
shift = 2 * scale
changed = y.copy()
changed[cut:] += shift
original_model, changed_model = SeasonalNaive(m), SeasonalNaive(m)
original_model.start(history)
changed_model.start(history)
original_errors, changed_errors = [], []
for t in range(cut, len(y)):
    original_errors.append(abs(y[t] - original_model.predict(1, [0.5])[0, 0]))
    changed_errors.append(abs(changed[t] - changed_model.predict(1, [0.5])[0, 0]))
    original_model.ingest(y[t:t+1])
    changed_model.ingest(changed[t:t+1])
fig, ax = plt.subplots()
ax.plot(np.arange(1, horizon+1), original_errors, label=words["original"])
ax.plot(np.arange(1, horizon+1), changed_errors, label=words["shift"])
ax.axvline(m, color="0.5", linestyle="--")
ax.set(xlabel=words["arrival"], ylabel=words["absolute"])
ax.legend()
fig.tight_layout()
plt.show()
print("added level:", f"{shift:.6f}")
print("mean absolute errors, first cycle:",
      f"{np.mean(original_errors[:m]):.6f}", f"{np.mean(changed_errors[:m]):.6f}")
print("post-cycle error-path difference:",
      f"{np.max(np.abs(np.array(original_errors[m:])-np.array(changed_errors[m:]))):.8f}")
''',
}
WORDS = {
    "en": {"cut": "Forecast origin", "time": "Recorded local time", "value": "Hourly sum (source readings in kW)",
           "history": "Available history", "actual": "Later observations", "forecast": "Repeated daily cycle",
           "interval": "Empirical 10–90% band", "period": "Model period (hours)", "original": "Original excerpt",
           "shift": "Synthetic level shift", "arrival": "Arrivals after intervention", "absolute": "Absolute one-step error"},
    "es": {"cut": "Origen del pronóstico", "time": "Hora local registrada", "value": "Suma horaria (lecturas originales en kW)",
           "history": "Historia disponible", "actual": "Observaciones posteriores", "forecast": "Ciclo diario repetido",
           "interval": "Banda empírica de 10–90%", "period": "Período del modelo (horas)", "original": "Extracto original",
           "shift": "Cambio de nivel sintético", "arrival": "Llegadas desde la intervención", "absolute": "Error absoluto a un paso"},
}


def build(lang: str) -> str:
    text = (ROOT / f"docs/lessons/{lang}/{NAME}.md").read_text(encoding="utf-8")
    text = text.replace("{{PINS}}", "\n".join(f"pip install {pin}" for pin in PINS))
    cells = []
    for i, piece in enumerate(re.split(r"<!-- code: ([a-z_]+) -->", text)):
        kind = "markdown" if i % 2 == 0 else "code"
        source = piece.strip() if kind == "markdown" else CODES[piece].strip()
        if not source:
            continue
        if kind == "code" and piece == "setup":
            source += "\nwords = " + pformat(WORDS[lang], width=100, sort_dicts=False)
        cell = {"cell_type": kind, "id": hashlib.sha256(f"{NAME}/{len(cells)}".encode()).hexdigest()[:12],
                "metadata": {}, "source": source + "\n"}
        if kind == "code":
            cell.update(execution_count=None, outputs=[])
        if kind == "markdown":
            for section in re.split(r"(?m)(?=^## )", source):
                if section.strip():
                    cells.append({**cell, "id": hashlib.sha256(f"{NAME}/{len(cells)}".encode()).hexdigest()[:12],
                                  "source": section.strip() + "\n"})
        else:
            cells.append(cell)
    title = text.splitlines()[0].lstrip("# ")
    doc = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "caos": {"language": lang, "topic": TOPIC, "level": 1, "title": title, "packages": PINS,
                 "data": ["data/examples/electricity_sample.csv"], "sources": SOURCES, "beyond": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}, "cells": cells}
    (ROOT / f"notebooks/{lang}/{TOPIC}/{NAME}.ipynb").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return title


if __name__ == "__main__":
    for language in WORDS:
        build(language)
