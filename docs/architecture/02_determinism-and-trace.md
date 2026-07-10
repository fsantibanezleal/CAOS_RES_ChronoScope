# Determinism + the trace

**A run is a pure function of `(params, seed)`.** Use `core/rng.py :: make_rng(seed)` — never a global/implicit
RNG. Same inputs ⇒ byte-identical artifact (asserted in `tests/test_pipeline_smoke.py`). This is what makes the
committed artifact a trustworthy source-of-truth the SPA merely animates (ADR-0052 / ADR-0054).

**The trace** (`core/trace.py`, schema `chronoscope.trace/v2`) is the compact, decimated replay artifact — not the raw
solver state. `build_trace()` down-samples long histories to `MAX_HISTORY` so the committed JSON stays small; since v2 every method's backtest block carries the full metric family (MASE/WQL/coverage plus MAE/RMSE/sMAPE/MSIS) and the per-lead scaled error curve (`per_horizon_scaled`, preqts 0.3).
For a heavy product the offline run also emits the full raw output (kept local/LFS, git-ignored); only the compact
trace is committed and shipped. Its shape is mirrored by `frontend/src/lib/contract.types.ts` (CONTRACT 2).
