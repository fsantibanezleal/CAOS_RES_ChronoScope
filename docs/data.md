# Data

How ChronoScope sources, licenses, and ingests time series.

## Pages

- [Provenance and licensing](data/provenance.md) - the per-source license registry, the two-tier
  public-safe / local-only policy, and how the export stage enforces it (a source whose license forbids
  redistribution ships aggregate metrics only, never a raw excerpt).

## Contract 1 (ingestion)

Every series - a built-in case or bring-your-own data - enters through Contract 1
([`io/contract.py`](../data-pipeline/chronoscopelab/io/contract.py)): a long-format `unique_id, ds, y` table
with an explicit missing/outlier policy (accept / reject / flag). See
[architecture/08_data-contracts.md](architecture/08_data-contracts.md).

## The vault

Raw data lives in a private local vault (`E:\_Datos\chronoscope`); only license-cleared derived excerpts and
aggregate metrics are committed to this public repo, per the [provenance policy](data/provenance.md).
