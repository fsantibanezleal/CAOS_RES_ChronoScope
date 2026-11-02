"""Author the three bilingual sequence/corpus lessons; execution is a separate gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOPIC = "02-sequence-evidence"
NAMES = ("01-shape-patterns", "02-complexity", "03-corpus-confirmation")
SETUP = """from pathlib import Path
import sys
import json
import warnings
import numpy as np
import matplotlib.pyplot as plt
root = next(p for p in Path.cwd().parents if (p / "VERSION").is_file())
sys.path.insert(0, str(root / "data-pipeline"))
from chronoscopelab.analysis.sequence import matrix_profile, sequence_report
from chronoscopelab.analysis.sequence import multiscale_entropy, time_reversal
from chronoscopelab.analysis.atlas import prefix_features, associations, by_adjust
plt.rcParams.update({"figure.figsize": (8, 3), "figure.dpi": 95, "font.size": 10})
plt.rcParams["svg.hashsalt"] = "chronoscope-sequence-lessons"
warnings.filterwarnings("ignore", message="A large number of values in.*", category=UserWarning)
import importlib.metadata
packages = ("numpy", "scipy", "matplotlib", "stumpy", "antropy", "nolds", "pycatch22", "scikit-learn",
            "statsforecast", "lightgbm", "mlforecast", "nbformat", "nbclient", "ipykernel")
for package in packages:
    print(package, importlib.metadata.version(package))
"""
DATA = """analysis = json.loads((root / "data/derived/BRKV_level_shift/analysis.json").read_text(encoding="utf-8"))
values = np.array(analysis["sequence"]["values"], dtype=float)
print("Original observations:", len(values))
"""
CODES = {
    "setup": SETUP,
    "data": DATA,
    "profile": """profile = matrix_profile(values, window=24)
print("Window:", profile["window"])
print("Profile starts:", len(profile["profile"]))
print("Motif pairs:", profile["motifs"])
print("Discord windows:", profile["discords"])
""",
    "profile_reference": """import stumpy
reference = stumpy.stump(values, m=24)
difference = np.max(np.abs(np.asarray(profile["profile"])-reference.P_))
print("Maximum distance from reference:", f"{difference:.8f}")
""",
    "sequence": """diagnostics = sequence_report(values, seasonality=12)
print("Original index count:", len(diagnostics["observation_indices"]))
print("FLUSS candidates:", diagnostics["matrix_profile"]["regime_boundaries"])
""",
    "pattern_plot": """fig, axes = plt.subplots(2, 1, figsize=(8, 5))
axes[0].plot(values, label="original observations")
for boundary in profile["regime_boundaries"]:
    axes[0].axvline(boundary, color="tab:red", linestyle="--")
for motif in profile["motifs"]:
    for start in (motif["start"], motif["match"]):
        axes[0].axvspan(start, start+23, color="tab:green", alpha=.2)
axes[0].set(xlabel="Original observation index", ylabel="Value")
axes[1].plot(profile["profile"], label="nearest-shape distance")
axes[1].set(xlabel="Window start", ylabel="Z-normalized distance")
fig.tight_layout()
plt.show()
""",
    "entropy": """entropy = multiscale_entropy(values, scales=(1, 2, 4, 8))
print("Original tolerance:", round(entropy["scales"][0]["tolerance"], 4))
for row in entropy["scales"]:
    print("Scale", row["scale"], "n", row["n"], "SampEn", row["entropy"])
""",
    "constant": """constant = multiscale_entropy(np.ones(100), scales=(1, 2, 4, 8))
print("Constant-series scale-one entropy:", constant["scales"][0]["entropy"])
print("Short coarse estimate:", constant["scales"][-1]["entropy"])
""",
    "reversal": """forward = time_reversal(values, lag=2)
backward = time_reversal(values[::-1], lag=2)
print("Forward standardized statistic:", round(forward["standardized"], 6))
print("Reversed standardized statistic:", round(backward["standardized"], 6))
""",
    "symbols": """symbolic = sequence_report(values, seasonality=12)
print("Binary phrase count:", symbolic["lempel_ziv"]["raw"])
print("Normalized phrase count:", round(symbolic["lempel_ziv"]["normalized"], 4))
""",
    "units": """converted = sequence_report(values*10+100, seasonality=12)
print("Phrase count after unit conversion:", converted["lempel_ziv"]["raw"])
print("Scale-one converted entropy:", converted["multiscale_entropy"]["scales"][0]["entropy"])
""",
    "entropy_plot": """fig, ax = plt.subplots()
ax.plot([r["scale"] for r in entropy["scales"]],
        [r["entropy"] for r in entropy["scales"]], marker="o", label="original sequence")
ax.plot([r["scale"] for r in constant["scales"]],
        [r["entropy"] for r in constant["scales"]], marker="s", label="constant control")
ax.set(xlabel="Coarse-graining scale", ylabel="Sample entropy")
ax.legend()
fig.tight_layout()
plt.show()
""",
    "reversal_plot": """fig, ax = plt.subplots()
ax.bar(["forward", "reversed"], [forward["standardized"], backward["standardized"]])
ax.axhline(0, color="grey", linewidth=.8)
ax.set(ylabel="Standardized third-order lag statistic")
fig.tight_layout()
plt.show()
""",
    "corpus": DATA
    + """study = json.loads((root / "data/derived/forecastability.json").read_text())
discovery = [r for r in study["series"] if r["partition"] == "discovery"]
confirmation = [r for r in study["series"] if r["partition"] == "confirmation"]
print("Source series:", study["source_n"])
print("Admitted series:", study["included_n"])
print("Origins per series:", study["protocol"]["origins"])
print("Discovery/confirmation:", len(discovery), len(confirmation))
""",
    "prefix": """features = prefix_features(values[:-42])
print("Features available before the three final blocks:", len(features))
print("Earliest prefix observations:", features["history_length"])
""",
    "associations": """discovery_tests = associations(discovery)
confirmation_tests = associations(confirmation)
print("Hypotheses per partition:", len(discovery_tests))
print("Rejected in discovery:", sum(r["rejected"] for r in discovery_tests))
print("Rejected in confirmation:", sum(r["rejected"] for r in confirmation_tests))
""",
    "kendall_reference": """from scipy import stats
chosen = "linear_trend_r"
pairs = [(r["features"][chosen], np.log1p(min(r["mase"].values())))
         for r in confirmation if r["features"][chosen] is not None]
x, y = zip(*pairs)
tau, probability = stats.kendalltau(x, y)
print("Reference feature:", chosen)
print("Kendall tau:", round(float(tau), 6))
print("Reference probability:", float(probability))
""",
    "correction": """probabilities = [r["p"] for r in confirmation_tests]
corrected = by_adjust(probabilities)
library = stats.false_discovery_control(probabilities, method="by")
print("Maximum BY reference difference:", f"{np.max(np.abs(corrected-library)):.8f}")
print("Confirmation threshold:", study["protocol"]["q"])
""",
    "reference_join": """same_prefix = values[:-42]
product_profile = matrix_profile(same_prefix, window=24)
import stumpy
library_profile = stumpy.stump(same_prefix, m=24)
print("Prefix-only profile difference:",
      f"{np.max(np.abs(np.asarray(product_profile['profile'])-library_profile.P_)):.8f}")
""",
    "association_plot": """chosen_tests = study["summary"]["associations"][:12]
fig, ax = plt.subplots(figsize=(8, 5))
locations = np.arange(len(chosen_tests))
ax.barh(locations-.18, [r["discovery"]["tau"] for r in chosen_tests], height=.35, label="discovery")
ax.barh(locations+.18, [r["confirmation"]["tau"] for r in chosen_tests], height=.35, label="confirmation")
ax.set_yticks(locations, [r["feature"] for r in chosen_tests])
ax.set(xlabel="Kendall association with log(1 + oracle MASE)")
ax.legend()
fig.tight_layout()
plt.show()
""",
    "selection_plot": """scores = study["summary"]["selection_mean_mase"]
fig, ax = plt.subplots()
ax.bar(list(scores), list(scores.values()))
ax.set(ylabel="Confirmation mean MASE")
fig.tight_layout()
plt.show()
for name, score in scores.items():
    print(name, round(score, 4))
""",
    "checks": """assert len(set(r["sequence_sha256"] for r in study["series"])) == study["included_n"]
assert not set(r["id"] for r in discovery) & set(r["id"] for r in confirmation)
assert np.allclose(corrected, library)
print("Duplicate, partition and corrected-probability checks passed")
""",
}
CODES["seeded"] = """from chronoscopelab.analysis.nonlinear import chaos_measures
first_fit = chaos_measures(values, seed=42)
second_fit = chaos_measures(values, seed=42)
print("Repeated robust estimates identical:", first_fit == second_fit)
print("Correlation dimension:", round(first_fit.corr_dim, 6))
"""
CODES["refit_selector"] = """from chronoscopelab.analysis.atlas import study_summary
reproduced, trained_selector = study_summary(study["series"])
differences = [abs(reproduced["selection_mean_mase"][n]-study["summary"]["selection_mean_mase"][n])
               for n in reproduced["selection_mean_mase"]]
print("Maximum reproduced selection-score difference:", f"{max(differences):.8f}")
"""
CODES["selection_plot"] = CODES["selection_plot"].replace(
    'study["summary"]["selection_mean_mase"]', 'reproduced["selection_mean_mase"]'
)


COMMENTS = {
    "setup": "Configure a portable session and suppress only the known repeated-shape control warning.",
    "data": "Read every original observation from the admitted structural-break case.",
    "profile": "Calculate the exact normalized self-join and retain original window positions.",
    "profile_reference": "Compare the product adapter with the pinned STUMPY reference.",
    "sequence": "Run the complete sequence diagnostic with an explicit candidate period.",
    "pattern_plot": "Connect motif intervals and retrospective boundaries to original observations.",
    "entropy": "Keep the original tolerance fixed while coarse-graining at four scales.",
    "constant": "Separate a legitimate zero entropy from insufficient coarse observations.",
    "reversal": "Compute the same lag statistic on forward and reversed observations.",
    "symbols": "Inspect median-thresholded binary phrase counts and their normalization.",
    "units": "Repeat the calculations after a positive affine unit conversion.",
    "entropy_plot": "Compare the observed case with the constant control under the same scale policy.",
    "reversal_plot": "Display the signed standardized lag statistic in both directions.",
    "corpus": "Read the complete admitted feature and error table with its series partitions.",
    "prefix": "Extract features before all three held-out target blocks in the worked case.",
    "associations": "Repeat all preregistered feature tests in each disjoint series partition.",
    "kendall_reference": "Check the chosen confirmation association against SciPy Kendall tau.",
    "correction": "Compare dependent-test BY adjustment with the reference implementation.",
    "reference_join": "Verify a prefix-only profile without admitting future observations.",
    "association_plot": "Show the first twelve features in schema order rather than significance order.",
    "selection_plot": "Plot confirmation scores from the reproduced selection calculation.",
    "checks": "Check exact deduplication, partition separation and corrected probabilities.",
    "seeded": "Repeat robust nonlinear estimates with an explicit local seed.",
    "refit_selector": "Train the fixed selector again using discovery rows and discovery-only imputation.",
}


LESSON_SOURCES = {
    1: ["https://doi.org/10.1109/ICDM.2016.0179", "https://doi.org/10.1109/ICDM.2017.21"],
    2: [
        "https://doi.org/10.1103/PhysRevLett.89.068102",
        "https://doi.org/10.1109/TIT.1976.1055501",
        "https://cschoel.github.io/nolds/nolds.html",
    ],
    3: [
        "https://doi.org/10.5281/zenodo.4656548",
        "https://tsfresh.readthedocs.io/en/v0.21.0/text/feature_filtering.html",
        "https://doi.org/10.1016/j.ijforecast.2006.03.001",
        "https://doi.org/10.1109/ICDM.2016.0179",
    ],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=NAMES)
    args = parser.parse_args()
    pins = [
        s
        for s in (ROOT / "notebooks/requirements.txt").read_text().splitlines()
        if s and not s.startswith("#")
    ]
    analysis = json.loads((ROOT / "data/derived/BRKV_level_shift/analysis.json").read_text(encoding="utf-8"))
    study = (
        json.loads((ROOT / "data/derived/forecastability.json").read_text(encoding="utf-8"))
        if args.only in (None, NAMES[2])
        else None
    )
    scores = (
        study["summary"]["selection_mean_mase"] if study else {"selected": 0.0, "discovery_constant": 0.0}
    )
    substitutions = {
        "{{PINS}}": "\n".join("pip install " + p for p in pins),
        "{{TOLERANCE}}": f"{analysis['sequence']['multiscale_entropy']['scales'][0]['tolerance']:.4f}",
        "{{SELECTED}}": f"{scores['selected']:.4f}",
        "{{CONSTANT}}": f"{scores['discovery_constant']:.4f}",
        "{{CONFIRMED}}": str(sum(r["confirmed"] for r in study["summary"]["associations"])) if study else "",
    }
    for lang in ("en", "es"):
        index = []
        for level, name in enumerate(NAMES, 1):
            if args.only and args.only != name:
                continue
            text = (ROOT / f"docs/lessons/{lang}/research/{name}.md").read_text(encoding="utf-8")
            for key, value in substitutions.items():
                text = text.replace(key, value)
            cells = []
            for i, piece in enumerate(re.split(r"<!-- code: ([a-z_]+) -->", text)):
                kind = "markdown" if i % 2 == 0 else "code"
                source = (
                    piece.strip()
                    if kind == "markdown"
                    else "# " + COMMENTS[piece] + "\n" + CODES[piece].strip()
                )
                if not source:
                    continue
                cell = {
                    "cell_type": kind,
                    "id": hashlib.sha256(f"{TOPIC}/{name}/{len(cells)}".encode()).hexdigest()[:12],
                    "metadata": {},
                    "source": source + "\n",
                }
                if kind == "code":
                    cell.update(execution_count=None, outputs=[])
                cells.append(cell)
            title = text.splitlines()[0].lstrip("# ")
            document = {
                "nbformat": 4,
                "nbformat_minor": 5,
                "metadata": {
                    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                    "language_info": {"name": "python"},
                    "caos": {
                        "language": lang,
                        "topic": TOPIC,
                        "level": level,
                        "title": title,
                        "packages": pins,
                        "data": [
                            "data/derived/BRKV_level_shift/analysis.json",
                            *(["data/derived/forecastability.json"] if level == 3 else []),
                        ],
                        "sources": LESSON_SOURCES[level],
                        "beyond": [],
                    },
                },
                "cells": cells,
            }
            dest = ROOT / f"notebooks/{lang}/{TOPIC}/{name}.ipynb"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(
                json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
            )
            index.append(f"| {level} | [{title}]({TOPIC}/{name}.ipynb) |")
        index = []
        for existing in sorted((ROOT / f"notebooks/{lang}/{TOPIC}").glob("*.ipynb")):
            meta = json.loads(existing.read_text(encoding="utf-8"))["metadata"]["caos"]
            index.append(f"| {meta['level']} | [{meta['title']}]({TOPIC}/{existing.name}) |")
        path = ROOT / f"notebooks/{lang}/README.md"
        text = path.read_text(encoding="utf-8").split("<!-- sequence-lessons:start -->")[0].rstrip()
        text += (
            "\n\n<!-- sequence-lessons:start -->\n\n| Level | Lesson |\n|---|---|\n"
            + "\n".join(index)
            + "\n<!-- sequence-lessons:end -->\n"
        )
        path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
