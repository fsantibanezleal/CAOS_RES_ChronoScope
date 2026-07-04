# Guide — bring your own data

The product is applicable to NEW data, not just the baked cases: that is what makes it a tool. The door is
CONTRACT 1 (`data-pipeline/chronoscopelab/io/contract.py`).

1. Put your series in the long format (see [`data/README.md`](../../data/README.md)): a CSV with columns
   `unique_id,ds,y` (plus optional covariate columns). Drop the file under `data/raw/` (git-ignored).
2. Point `preprocess` at it and run `scripts/precompute.{sh,ps1}`. CONTRACT 1 validates each series: rejected with
   a reason if it violates the schema/policy (fewer than 8 observations, more than 30% missing, non-numeric `y`),
   flagged if plausible-but-suspicious (missing values, outliers, unsorted timestamps), accepted otherwise.
   Nothing is silently coerced.
3. The pipeline produces a compact artifact + manifest you can replay in the SPA, exactly like the built-in cases.
4. Live (optional): the classical method core also runs in the browser via
   `chronoscopelab.live.run_forecast_json({...your series...})`, rendering the forecast in-browser with no server.

If your data legitimately doesn't fit, extend CONTRACT 1 (and its tests) deliberately; never loosen it just to
make bad data pass.
