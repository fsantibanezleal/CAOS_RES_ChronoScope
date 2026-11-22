# Executing the seven model references

The bilingual model-comparison lesson executes NLinear, DLinear, NHITS, Chronos-Bolt, Chronos-2, TimesFM 2.5 and the retained TiRex-2 reference. These are actual fits or checkpoint inferences. `data-pipeline/engine/notebook_reference.py` accepts only the observed prefix, seasonal lag and forecast horizon. Future outcomes are scored after the helper returns.

The helper validates pinned package versions and checkpoint revisions/hashes against retained runtime declarations. Its result records package, Python, seed, checkpoint, CPU-thread, CUDA and build-tool identities. Missing packages, unavailable weights and invalid output shapes fail explicitly; there is no replacement forecast.

On Windows, configure the Linux reference interpreter and a native Linux checkpoint cache before executing the curriculum:

```powershell
$env:CAOS_VENVS_ROOT = '<absolute-environments-root>'
$env:CAOS_TEMP_ROOT = '<absolute-temporary-root>'
$env:CHRONOSCOPE_REFERENCE_PYTHON = '<absolute-Linux-reference-interpreter>'
$env:CHRONOSCOPE_REFERENCE_CACHE = '<absolute-native-Linux-checkpoint-cache>'
python scripts/run_notebooks.py
python scripts/run_notebooks.py --check --tmp $env:CAOS_TEMP_ROOT
```

The interpreter path is explicit machine configuration. Initialize product and lesson environments with the repository setup workflow. Provision the Linux interpreter using exact versions in the retained fresh-reference runtime and current ForecastScope pin in `notebooks/requirements.txt`. The TiRex lane requires its declared CUDA/compiler toolchain and Ninja 1.13.0; the helper locates the executable installed by the Ninja wheel. It bounds compiler and CPU workers and releases memory between methods.

`scripts/prepare_reference_models.py --cache <external-directory> --receipt <external-json>` prepares and verifies three public checkpoints at retained revisions. The gated TiRex checkpoint must already be available under authorized access terms. Native Linux storage avoids unnecessary cross-filesystem weight loading. Do not copy credentials into a notebook or repository.

New upstream releases, including TimesFM 3.0 and TiRex 0.5, require a separate protocol and license/runtime assessment; they are not silently substituted. The [dated model review](../research/2026-11-22-foundation-update.md) records that distinction.
