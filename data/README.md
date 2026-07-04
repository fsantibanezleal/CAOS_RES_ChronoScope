# data/ : the data contract + layout

This folder is governed by the two data contracts of ADR-0057.

## Layout

| Path | What | Git |
|---|---|---|
| `raw/` | private/large source inputs | git-ignored (never committed; staged via `scripts/fetch-data`) |
| `examples/` | small real sample series that PASS Contract 1 (clone-verify) | committed |
| `derived/<case>/` | the compact artifacts the web replays | committed |
| `derived/manifests/` | per-case `<case>.json` (Contract 2) + the flat `index.json` inventory | committed |

`examples/electricity_sample.csv` is a real series: one UCI ElectricityLoadDiagrams client (MT_010)
aggregated from 15-minute to hourly, 720 points (CC BY 4.0). The heavier datasets (GIFT-Eval, M-competition,
LTSF, more UCI/Kaggle series) live in the vault at `E:\_Datos\chronoscope` and are staged, never committed.

## CONTRACT 1: ingestion (raw to pipeline), the bring-your-own-data gate

Defined in `data-pipeline/chronoscopelab/io/contract.py`. Long-format schema, one row per (series, timestamp):

| Column | Type | Notes |
|---|---|---|
| `unique_id` | str | series identifier |
| `ds` | str | timestamp (sortable); strictly increasing per series (else flagged and sorted) |
| `y` | float | target value; finite (NaN allowed up to 30%, then rejected) |

Optional extra columns are treated as covariates and passed through.

A series is accepted iff it passes; rejected with a reason otherwise (never silently coerced);
suspicious-but-plausible series are flagged (the flag is recorded in the manifest).

Policy: fewer than 8 observations, reject. More than 30% missing target, reject. Non-numeric `y`, reject.
Any missing value, flag. Robust MAD z-score above 8, flag. Unsorted timestamps, flag (and sort on ingest).

## CONTRACT 2: artifact (pipeline to web)

Each pipeline run writes a compact trace (`derived/<case>/trace.json`, schema `chronoscope.trace/v1`) and a
manifest (`derived/manifests/<case>.json`, schema `chronoscope.manifest/v1`) recording the series descriptors,
seed, engine + version, the artifact byte size, the measured lane/gate verdict, Contract-1 flags, the best
method, and the evaluation metrics. `frontend/src/lib/contract.types.ts` mirrors these schemas so any drift
fails the web build. The web loads ONLY these committed artifacts; it never recomputes (except the optional
live lane, which uses the same method core).

## Provenance / license

Synthetic cases are generated deterministically (documented in `cases/forecast_cases.py`). The real sample is
UCI ElectricityLoadDiagrams20112014 (CC BY 4.0). Only compact derived artifacts are committed; raw/large sources
stay in the vault per ADR-0055.
