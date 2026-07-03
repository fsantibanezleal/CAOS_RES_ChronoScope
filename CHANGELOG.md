# Changelog

All notable changes to this product. Format: `X.XX.XXX` (display) — see `chronoscopelab.__version__`. Keep `0.x`
while on mock/synthetic data. Tag every release.

## [0.01.000] — 2026-07-03

### Added
- ChronoScope: initial instantiation from the CAOS product-repo template (ADR-0057); package
  `chronoscopelab`. Kickoff plan + binding research dossiers: `_CAOS_MANAGE/wip/chronoscope/`.
- Offline `data-pipeline/` (`chronoscopelab`): the two data contracts (ingestion + artifact), the named staged
  pipeline (preprocess → feature_extraction → train → infer → evaluate → export), the seeded RNG, the compact
  trace, the manifest, and the measured live-vs-precompute gate.
- EXAMPLE engine: a deterministic SIR epidemic (numpy-only, Pyodide-safe) — **replace with the product's
  research-chosen SOTA engine**.
- Cases-by-category registry (4 regimes + 1 degenerate control); a live-lane entrypoint (`live.py`); tests for
  both contracts + pipeline determinism.
