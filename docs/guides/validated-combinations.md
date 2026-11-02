# Reproduce temporally validated combinations

The [fixed protocol](../design/features/validated-combinations/requirements.md) was
committed before the new external outcomes. ContextMemoryCV chooses context shrinkage
and temperature; ValidationMix also considers regularized convex stacking. Both use
only completed historical targets for selection. The original ContextMemory result
remains a separate, unchanged experiment.

## Source and environment identities

Use Python 3.13 and the exact CPU dependencies in `requirements-combinations.txt`.
The admitted run used Python 3.13.14, NumPy 2.4.6, SciPy 1.15.3, StatsForecast 2.0.3
and Numba 0.68.1. No GPU, neural training or pretrained inference is used in this study.
Recursive reference loops are compiled without fast-math transformations; independent
expert parity tests protect their equations, grids and initialization.

Acquire the CC BY 4.0 ZIPs from the official Monash records:

| Collection | Record | Source identities | Horizon | Seasonal lag |
|---|---|---|---|---|
| M4 Weekly | [4656522](https://zenodo.org/records/4656522) | 359 | 13 | 52 |
| M3 Monthly | [4656298](https://zenodo.org/records/4656298) | 1,428 | 18 | 12 |

The [study index](../../data/derived/validated-combinations.json) retains the exact
ZIP/TSF SHA-256 values and source provenance. Verify the downloaded and extracted
bytes before running. Keep raw inputs, per-series caches and full candidate output
outside the repository. The runner binds TSF bytes, scientific source hashes,
protocol and package versions into its cache identity.

## Execute and independently admit

Substitute external paths in these commands, from the repository root:

```text
python -m pip install -r requirements-combinations.txt
python scripts/run_combination_study.py --source-root <external-tsf-folder> --cache <external-cache> --output <external-result.json> --workers 4
python scripts/check_combination_study.py <external-result.json> --source-root <external-tsf-folder>
```

Completion requires the explicit `COMBINATION_STUDY_COMPLETE` marker and a successful
checker exit. A method failure stops the run. Every source identity remains admitted
or excluded with a reason; no difficult method or series is silently removed.
All 65 weekly exclusions are finite 93-observation series without an eligible origin.
Six exact monthly duplicates retain their representatives. The final inventory has
1,716 admitted series, 4,429 origins and 53,148 twelve-method forecasts.

The full numerical audit is also retained at
`manuscripts/context-memory/evidence/external-evaluation.json.gz`. Decompress it into
external scratch and run the same checker with the checksum-identified TSF sources.
It reconstructs prefixes, targets, scales, exclusions and temporal schedules, recomputes
every score, reconstructs mixtures from expert paths/weights, checks historical candidate
selection and aggregates origins within series before weighting series equally.

## Browser, lessons and interpretation

The app loads a compact index and only the selected per-series document. Browser paths
retain eight decimal places; the compressed audit retains full floating-point output.
`frontend/scripts/check-combinations-ui.mjs`, with `GATE_URL` set to the preview or
canonical origin, exercises each collection, first/last admitted series, every available
origin and every method in both languages/themes at phone and desktop widths. It compares
displayed MASE values with the served numerical records and checks excluded inventories.
The complete shell browser matrix is a separate release check.

The new English and Spanish temporal-validation lessons fit the algorithms on all
fifteen development prefixes. All sixteen lessons are executed and independently
reproduced with `scripts/run_notebooks.py --check --tmp <external-scratch>`. The lessons
distinguish these reused development cases from the external weekly/monthly study.

Both variants improve point error against RecencyMean in each external collection.
AutoTheta remains better on monthly point error and both collections' interval scores.
Changing context shrinkage, temperature and validation together does not isolate a
benefit of context similarity. These finite-collection results establish neither
population superiority, calibrated uncertainty, operational benefit nor priority for
established forecast-combination principles. The [published manuscript set](../../manuscripts/README.md)
reports the complete comparisons and limitations.
