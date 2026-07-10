# The two data contracts

A product is only real if data flows through two **enforced** contracts. Both are CI-checked.

## CONTRACT 1: ingestion (`raw` to `pipeline`), the bring-your-own-data gate
`data-pipeline/chronoscopelab/io/contract.py`. Declares the required long-format schema (`unique_id`, `ds`, `y`
plus optional covariates) and an explicit missing/outlier policy (reject / flag). A series is accepted iff it
passes; bad series are rejected with a reason, never silently coerced; suspicious-but-plausible series are
flagged (the flag is recorded in the manifest). This is what lets a third party point the tool at THEIR series
instead of only replaying baked cases.

Policy: fewer than 8 observations or more than 30% missing target or non-numeric `y`, reject; any missing value,
robust MAD z-score above 8, or unsorted timestamps, flag (and sort). Full table: [`data/README.md`](../../data/README.md).

## CONTRACT 2: artifact (`pipeline` to `web`)
`data-pipeline/chronoscopelab/core/{trace.py, manifest.py}`. Every run writes a compact trace (`chronoscope.trace/v2`; v2 added the extended metric block: MAE/RMSE/sMAPE/MSIS + `per_horizon_scaled` per method, all aggregates and therefore redaction-safe)
plus a manifest (`chronoscope.manifest/v1`) recording the series descriptors, seed, engine + version, the artifact
byte size, the measured [lane/gate](03_the-gate.md) verdict, the Contract-1 flags, the best method, and the
evaluation metrics. A flat `data/derived/manifests/index.json` inventories every case.

**Enforcement:** `frontend/src/lib/contract.types.ts` mirrors this schema — a drift fails `tsc`. `scripts/check_artifacts.py`
(run in CI) verifies index→manifests→artifacts exist, byte sizes match, and lane==gate. The web loads **only** these
artifacts; it never recomputes (except the optional live lane, which emits the same trace schema).

## Why this matters
Without Contract 1 the app can't be applied to new data (it's a demo). Without Contract 2 the web can silently
drift from what the pipeline produced. The contracts are the seam that makes the product a tool, not a slideshow.
