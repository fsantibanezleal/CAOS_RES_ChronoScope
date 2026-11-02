# Reproduce sequence and corpus research

The [fixed design](../design/features/research-extensions/requirements.md) precedes the executed
study. The [method record](../research/2026-11-02-sequence-evidence.md) explains interpretation,
statistical assumptions and retained negative outcomes. The separate
[fresh forecasting guide](fresh-reevaluation.md) covers the twenty-two-variant experiment.

## Environments and external inputs

Use the pinned precompute dependencies for the Python producer and the pinned
`notebooks/requirements.txt` environment for lessons. Record actual package versions; the
study cache includes them in its identity. The corpus needs NumPy, SciPy, STUMPY, antropy,
pycatch22, StatsForecast, scikit-learn and joblib. No GPU or pretrained checkpoint is used
in this corpus study. Bound numerical worker threads before starting child processes.

Acquire `m4_daily_dataset.zip` from the official [Monash record](https://zenodo.org/records/4656548).
The input is CC BY 4.0. Verify the record MD5 `a92adb385fe0aec3728e60bd6de29875` and ZIP SHA-256
`0f07fc3b67a93be1865de7853e06d8ad212f1a8cb8436ba859920cfe5625d889`.
The extracted `m4_daily_dataset.tsf` SHA-256 is
`d4d70b66ab4685a493f201bfff311c5495bf34972c206a1add0027d6d2a57d38`.
Keep source, receipt, caches and candidate output in the configured external data/scratch roots.
The source receipt contains record 4656548, DOI, licence, filename, byte count, MD5 and ZIP SHA-256.

## Sequence diagnostics

Run `python scripts/bake_research_diagnostics.py --help` for the candidate output arguments.
The producer analyzes each canonical case twice, requires identical serialized diagnostics,
and writes a reproduction receipt. Verify the candidate against the analysis schema and
original observation count before replacing canonical analysis artifacts and their manifest
byte counts. Do not replace forecast traces or infer ground-truth breaks from FLUSS.

The diagnostic tests use exhaustive window-distance and entropy pair-count oracles, planted
shape and frequency controls, unavailable/constant inputs, independent estimator processes
and caller-RNG preservation. These checks establish implementation properties under the
declared windows and fit choices, not general forecasting skill.

## Complete corpus execution and admission

Set `NUMBA_NUM_THREADS=1` and run the following with external paths substituted:

```text
python scripts/run_forecastability_study.py --source <external-tsf> --source-receipt <source-json> --cache <external-cache> --output <candidate-json> --workers 4
python scripts/check_research_extensions.py --statistics --study <candidate-json>
```

`--limit` is for a trial only and cannot pass complete-study admission. Resuming the same
protocol reuses source/code/package-bound per-series caches. Changing a bound implementation
during execution refuses the final candidate. The evaluator retains predictions and targets
externally and independently recomputes every MASE before compact export. It fits the selector
only after the series inventory is complete. Do not tune a configuration after inspecting
confirmation outcomes or promote a partial result as the full study.

Admit the compact document against `docs/contracts/schemas/forecastability.schema.json` and
the independent statistical checker before copying it to `data/derived/forecastability.json`.
Run `python -m pytest tests/adversarial/test_research_corpus.py -q` against the canonical
document; each planted corruption must be rejected. The local workflow carries the admitted
corpus unchanged and verifies its bindings; it does not rerun thousands of forecasts.

## Lessons, report and browser

`python scripts/build_research_lessons.py` authors all six new notebook files and clears
their outputs. Execute with the notebook environment using `scripts/run_notebooks.py`,
then rerun with `--check --tmp <external-scratch>` in fresh kernels. The corpus lesson
repeats statistical inference and retrains the selector from admitted rows; it does not
claim to rerun the external corpus forecasts.

`python scripts/build_research_report.py` generates the report's new scientific figures,
complete association table, corpus summary and current fresh comparison table. Compile the
report LaTeX, render every page and review layout before freezing its versioned publication.

After a production build, run `frontend/scripts/check-research-ui.mjs` with `GATE_URL` set
to the preview or canonical origin. It measures real case selection, all annotation filters,
corpus partitions, feature/method controls, pagination and series selection in both languages,
themes and phone/desktop sizes. The full installed-shell browser matrix remains a separate
required gate. Retain reports and representative captures with the versioned validation record.
