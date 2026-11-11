"""Author the bilingual lesson on training, forecast origin and replay boundaries."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "02-sequence-evidence"
LESSON = "04-information-boundaries"
SOURCES = [
    "https://doi.org/10.24432/C58C86",
    "https://doi.org/10.2307/2981683",
    "https://arxiv.org/abs/2106.00170",
    "https://pypi.org/project/preqts/0.3.0/",
]
DATA = [
    "data/examples/electricity_sample.csv",
    "data/derived/manifests/index.json",
    "data/derived/readiness.json",
    "data/derived/fresh-reevaluation.json",
    "data/derived/validated-combinations.json",
    "data/derived/combinations/m4_weekly/T1.json",
    "docs/contracts/catalog.md",
    "docs/research/browser-linear/v1/results.json",
    "docs/research/browser-linear/confirmation-v1/results.json",
    "frontend/public/models/nlinear.json",
]
CODES = {
    "setup": '''# Initialize the pinned numerical environment without downloading input data.
from pathlib import Path
import importlib.metadata
import json
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
import warnings
import numpy as np
import matplotlib.pyplot as plt
from preqts import SeasonalNaive
root = next(path for path in Path.cwd().parents if (path / "VERSION").is_file())
sys.path.insert(0, str(root / "data-pipeline"))
from chronoscopelab import registry
from chronoscopelab.core.manifest import build_index
from chronoscopelab.io.formats import write_json
from chronoscopelab.io.schema import SeriesSpec
from chronoscopelab.model.forecasters import classical_forecasters, forecast_all
from chronoscopelab.reevaluation import metrics
from chronoscopelab.stages import analyze, evaluate, export, feature_extraction, infer, preprocess, streaming, train
plt.rcParams.update({"figure.figsize": (8, 3.2), "figure.dpi": 95, "font.size": 10})
print("PreqTS", importlib.metadata.version("preqts"))
''',
    "data": '''# Admit the long-format source and take a contiguous chronological excerpt.
table = preprocess.run(str(root / "data/examples/electricity_sample.csv"))
case = registry.get_case("REAL_electricity")
record = table.accepted[0]
spec = SeriesSpec(case.id, tuple(record.y[:120]), 24, case.horizon, "H", case.source)
levels = (0.1, 0.5, 0.9)
prefix, target = infer.split(spec)
fitting = SeriesSpec(case.id, tuple(prefix), spec.seasonality, spec.horizon, "H", case.source)
print("Ingestion", table.summary())
print("Series, fitting rows, reserved rows:", record.unique_id, len(prefix), len(target))
''',
    "diagnostics": '''# Pass only the fitting prefix into the diagnostic and feature stages.
with warnings.catch_warnings(record=True):
    warnings.simplefilter("always")
    features = feature_extraction.run(fitting)
    analysis = analyze.run(fitting, seed=42)
print("Mean and lag-one correlation:", round(features.mean, 4), round(features.acf1, 4))
print("Analyzed panels:", ", ".join(sorted(analysis)))
''',
    "inference": '''# Issue final-block predictions, then call a package reference at the same origin.
with warnings.catch_warnings(record=True) as notices:
    warnings.simplefilter("always")
    forecast = infer.run(spec, levels)
print("Available adapters:", ", ".join(row.name for row in forecast.methods))
print("Numerical warning types:", sorted({type(w.message).__name__ for w in notices}))
theta = next(method for method in forecast.methods if method.name == "Theta")
reference = SeasonalNaive(seasonality=spec.seasonality)
reference.start(np.asarray(prefix))
ref = np.asarray(reference.predict(spec.horizon, list(levels)))
assert np.array_equal(ref[:, 1], prefix[-spec.seasonality:][:spec.horizon])
fig, ax = plt.subplots()
indices = np.arange(len(prefix), len(spec.y))
ax.plot(np.arange(len(prefix))[-36:], prefix[-36:], label="Fitting history")
ax.plot(indices, target, color="black", label="Reserved observations")
ax.plot(indices, theta.point, label="Theta")
ax.plot(indices, ref[:, 1], label="PreqTS seasonal reference")
ax.fill_between(indices, theta.lower, theta.upper, alpha=0.16)
ax.set(xlabel="Original observation index", ylabel="Hourly source sum")
ax.legend(ncol=2)
fig.tight_layout()
plt.show()
''',
    "scores": '''# Keep rolling prefix scores distinct from errors on the common final block.
historical = evaluate.run(spec, levels, classical_forecasters())
eligible = [row for row in forecast.methods if row.name in historical["methods"]]
final = [metrics(prefix, target, row.point, row.lower, row.upper, spec.seasonality)["mase"]
         for row in eligible]
fig, ax = plt.subplots()
positions = np.arange(len(eligible))
ax.bar(positions - 0.18, [historical["methods"][row.name]["mase"] for row in eligible],
       width=0.35, label="Rolling prefix")
ax.bar(positions + 0.18, final, width=0.35, label="Reserved final block")
ax.set_xticks(positions, [row.name for row in eligible], rotation=22)
ax.set(ylabel="MASE")
ax.legend()
fig.tight_layout()
plt.show()
print("Rolling selection:", historical["best_method"])
''',
    "stream": '''# Run an independent one-step replay inside the fitting history.
replay = streaming.run(fitting)
fig, ax = plt.subplots()
for name in ("Theta", "Theta+ACI", "Theta+PID"):
    row = replay["methods"][name]
    ax.plot(row["rolling_coverage"], label=name)
ax.axhline(replay["nominal_coverage"], linestyle="--", color="black", linewidth=0.8)
ax.set(xlabel="Completed replay update", ylabel="Rolling coverage")
ax.legend()
fig.tight_layout()
plt.show()
''',
    "export": '''# Train on distinct generated histories and write a disposable artifact and index.
training = [registry.build_series(registry.get_case(name), seed=42)
            for name in ("TRND_seasonal", "SEAS_hourly")]
start = perf_counter()
forecast_all(prefix, spec.seasonality, spec.horizon, levels)
elapsed_ms = (perf_counter() - start) * 1000
with TemporaryDirectory() as directory:
    output = Path(directory)
    selector = train.run(training, str(output / "models"), levels)
    manifest = export.run(case=case, feature=features, result=forecast, actual=target.tolist(),
                          eval_metrics=historical, seed=42, run_ms=elapsed_ms, flags=table.flagged,
                          derived_dir=directory, manifests_dir=str(output / "manifests"),
                          analysis=analysis, streaming_bench=replay)
    path = output / manifest["artifact"]["path"]
    assert path.stat().st_size == manifest["artifact"]["bytes"]
    trace = json.loads(path.read_text(encoding="utf-8"))
    assert trace["history_len"] == len(prefix) and trace["horizon"] == len(target)
    index = build_index([{"case_id": case.id, "category": case.category,
                          "manifest_path": f"manifests/{case.id}.json"}])
    write_json(output / "manifests/index.json", index)
print("Disposable index size:", index["n_cases"],
      "training default:", selector["default_method"])
''',
    "readiness": '''# Read the case and contract counts in the complete release inventory.
current = json.loads((root / "data/derived/readiness.json").read_text(encoding="utf-8"))
admitted = json.loads((root / "data/derived/manifests/index.json").read_text(encoding="utf-8"))
print("Committed index size:", admitted["n_cases"], "readiness entries:", len(current["contracts"]))
print("Catalog checksum:", current["catalog_sha256"],
      "product version:", current["product_version"])
''',
    "comparison_records": '''# Identify the different evaluation origins before comparing recorded scores.
derived = root / "data/derived"
fresh = json.loads((derived / "fresh-reevaluation.json").read_text(encoding="utf-8"))
released = next(row for row in fresh["cases"] if row["case_id"] == case.id)
combination_index = json.loads((derived / "validated-combinations.json").read_text(encoding="utf-8"))
entry = next(row for row in combination_index["cases"]
             if (row["dataset"], row["id"]) == ("m4_weekly", "T1"))
combination_case = json.loads((derived / entry["path"]).read_text(encoding="utf-8"))
first = combination_case["origins"][0]
mix = next(method for method in first["methods"] if method["name"] == "ValidationMix")
print("Released electricity fitting length:", released["history_length"])
print("Electricity teaching and published first targets:", target[0], released["actual"][0])
print("External series, first cutoff, reserved length:", entry["id"], first["origin"], len(first["actual"]))
print("ValidationMix path shape:", np.asarray(mix["quantiles"]).shape)
''',
    "browser_calibration": '''# Rescore two admitted studies before interpreting browser interval changes.
sys.path.insert(0, str(root / "scripts"))
from check_browser_linear_evidence import validate
validated = validate(root)
print("Independently rescored studies:", [study["study"] for study in validated])
browser = root / "docs/research/browser-linear"
ridge = json.loads((browser / "v1/results.json").read_text(encoding="utf-8"))["scores"]["all"]
confirmed = json.loads((browser / "confirmation-v1/results.json").read_text(encoding="utf-8"))["scores"]["all"]
metadata = json.loads((root / "frontend/public/models/nlinear.json").read_text(encoding="utf-8"))
print("Frozen graph lookback and horizon:", metadata["lookback"], metadata["horizon"])
print("Point MAE, frozen and ridge:", [round(row["normalized_mae"], 4) for row in ridge.values()])
print("Confirmation interval scores:", {name: round(row["normalized_interval_score"], 4)
                                         for name, row in confirmed.items()})
''',
}

SPANISH_TEXT = {
    "Ingestion": "Ingestión",
    "Series, fitting rows, reserved rows:": "Serie, filas de ajuste, filas reservadas:",
    "Mean and lag-one correlation:": "Media y correlación de rezago uno:",
    "Analyzed panels:": "Paneles analizados:",
    "Available adapters:": "Adaptadores disponibles:",
    "Numerical warning types:": "Tipos de avisos numéricos:",
    "Fitting history": "Historia de ajuste",
    "Reserved observations": "Observaciones reservadas",
    "PreqTS seasonal reference": "Referencia estacional de PreqTS",
    "Original observation index": "Índice de observación original",
    "Hourly source sum": "Suma horaria de la fuente",
    "Rolling prefix": "Orígenes móviles en el prefijo",
    "Reserved final block": "Bloque final reservado",
    "Rolling selection:": "Selección con orígenes móviles:",
    "Completed replay update": "Actualización de reproducción completada",
    "Rolling coverage": "Cobertura móvil",
    "Disposable index size:": "Tamaño del índice temporal:",
    "training default:": "método por defecto del entrenamiento:",
    "Committed index size:": "Tamaño del índice admitido:",
    "readiness entries:": "entradas de disponibilidad:",
    "Catalog checksum:": "Resumen criptográfico del catálogo:",
    "product version:": "versión del producto:",
    "Released electricity fitting length:": "Longitud de ajuste eléctrico publicado:",
    "Electricity teaching and published first targets:": "Primer objetivo eléctrico didáctico y publicado:",
    "External series, first cutoff, reserved length:": "Serie externa, primer corte, longitud reservada:",
    "ValidationMix path shape:": "Dimensiones de la trayectoria ValidationMix:",
    "Independently rescored studies:": "Estudios recalculados de forma independiente:",
    "Frozen graph lookback and horizon:": "Historia y horizonte del grafo congelado:",
    "Point MAE, frozen and ridge:": "MAE puntual, congelado y cresta:",
    "Confirmation interval scores:": "Puntuaciones de intervalos en confirmación:",
}

SPANISH_COMMENTS = {
    "setup": "Inicializa el entorno fijado sin descargar datos de entrada.",
    "data": "Admite la tabla larga y conserva un extracto cronológico contiguo.",
    "diagnostics": "Entrega solo el prefijo de ajuste a las etapas descriptivas.",
    "inference": "Pronostica el bloque final y ejecuta la referencia del mismo origen.",
    "scores": "Distingue puntajes históricos de errores del bloque final.",
    "stream": "Reproduce pronósticos de un paso dentro de la historia de ajuste.",
    "export": "Entrena sobre historias distintas y crea un índice temporal.",
    "readiness": "Lee los totales de casos y contratos del inventario completo.",
    "comparison_records": "Identifica los orígenes antes de comparar puntajes publicados.",
    "browser_calibration": "Recalcula dos estudios antes de interpretar cambios de intervalos.",
}


def main() -> None:
    pins = [line for line in (ROOT / "notebooks/requirements.txt").read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]
    for lang in ("en", "es"):
        source = ROOT / "docs/lessons" / lang / "01-information-boundaries.md"
        text = source.read_text(encoding="utf-8").replace("{{PINS}}", "\n".join(f"pip install {pin}" for pin in pins))
        title = text.splitlines()[0].removeprefix("# ")
        cells = []
        for i, item in enumerate(re.split(r"<!-- code: ([a-z_]+) -->", text)):
            kind = "code" if i % 2 else "markdown"
            value = (CODES[item] if kind == "code" else item).strip()
            if not value:
                continue
            if lang == "es" and kind == "code":
                _, _, body = value.partition("\n")
                value = f"# {SPANISH_COMMENTS[item]}\n{body}"
                for en, es in SPANISH_TEXT.items():
                    value = value.replace(f'"{en}"', f'"{es}"')
            cell = {"cell_type": kind, "id": hashlib.sha256(f"{LESSON}/{i}".encode()).hexdigest()[:12],
                    "metadata": {}, "source": value + "\n"}
            if kind == "code":
                cell.update(execution_count=None, outputs=[])
            cells.append(cell)
        metadata = {
            "caos": {"language": lang, "title": title, "topic": TOPIC, "level": 3,
                     "packages": pins, "sources": SOURCES, "data": DATA, "methods": ["ST-1", "ST-2"], "beyond": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        }
        target = ROOT / "notebooks" / lang / TOPIC / f"{LESSON}.ipynb"
        target.parent.mkdir(parents=True, exist_ok=True)
        value = {"cells": cells, "metadata": metadata, "nbformat": 4, "nbformat_minor": 5}
        target.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        index = ROOT / "notebooks" / lang / "README.md"
        heading = "Forecast workflow" if lang == "en" else "Flujo de pronóstico"
        labels = "| Level | Lesson |" if lang == "en" else "| Nivel | Lección |"
        block = (f"<!-- workflow-lesson:start -->\n\n## {heading}\n\n"
                 f"{labels}\n|---|---|\n| 3 | [{title}]({TOPIC}/{LESSON}.ipynb) |\n"
                 "<!-- workflow-lesson:end -->")
        previous = index.read_text(encoding="utf-8")
        pattern = r"<!-- workflow-lesson:start -->.*?<!-- workflow-lesson:end -->"
        updated = re.sub(pattern, block, previous, flags=re.S) if re.search(pattern, previous, re.S) else (
            previous.rstrip() + "\n\n" + block + "\n")
        index.write_text(updated, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
