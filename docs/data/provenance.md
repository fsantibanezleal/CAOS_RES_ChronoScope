# Data provenance and licensing

Code: [`chronoscopelab/data/provenance.py`](../../data-pipeline/chronoscopelab/data/provenance.py)
· Tests: [`tests/test_data_provenance.py`](../../tests/test_data_provenance.py),
[`tests/test_data_export_guard.py`](../../tests/test_data_export_guard.py)

ChronoScope is a public MIT repository. The offline pipeline reads raw data from a **private local
vault** (`E:\_Datos\chronoscope`) and bakes compact **derived artifacts** (series excerpts, forecasts,
metrics, analysis) into the public repo. The legal question for every dataset is: *may those small derived
excerpts be redistributed publicly, with attribution?* This page is the honest answer, and the pipeline
**enforces** it.

## The two-tier policy

Each source carries a verified `public_artifact_ok` verdict:

- **PUBLIC-safe** (`public_artifact_ok = true`): derived excerpts ship in the public repo **with
  attribution**. These are CC-BY-4.0 (or ChronoScope-owned synthetic) sources.
- **LOCAL-only** (`public_artifact_ok = false`): the pipeline may run on the data locally, but **no raw
  excerpt ships**. Only the **aggregate backtest metrics** (per-method MASE/WQL/coverage) and the **scalar
  analysis verdicts** are published, so the dataset still contributes to the public Benchmark without leaking
  its values. This covers Kaggle-competition data (redistribution forbidden), no-derivatives licenses, and
  any source whose license is unverified (the safe default).

## The registry

| Source | License | Public artifacts? | Citation |
|---|---|---|---|
| synthetic | ChronoScope-own (MIT) | **yes** | ChronoScope seeded generators |
| UCI Electricity | CC-BY-4.0 | **yes** | Trindade 2015, DOI 10.24432/C58C86 |
| UCI Beijing PM2.5 | CC-BY-4.0 | **yes** | Liang et al. 2015 |
| OPSD time_series | CC-BY-4.0 | **yes** | Open Power System Data 2020 |
| Monash (incl. M3/M4) | CC-BY-4.0 | **yes** | Godahewa et al. 2021, arXiv:2105.06643 |
| M5 (Kaggle) | competition rules | no (metrics only) | Makridakis et al. 2022, DOI 10.1016/j.ijforecast.2021.07.007 |
| Favorita (Kaggle) | competition rules | no (metrics only) | Favorita Kaggle 2017-18 |
| ETT / LTSF bundle | CC-BY-NC-ND / murky | no (metrics only) | Zhou et al. 2021 (Informer) |
| Mining flotation (Kaggle) | uploader-stated (UNVERIFIED) | no (metrics only) | Kaggle, edumagalhaes |
| Stooq finance | Stooq terms (UNVERIFIED) | no (metrics only) | Stooq |

The verdicts are transcribed from the verified license dossier (`wip/chronoscope/deep-research-datasets-licenses-2026-07-04.md`).

## How the enforcement works

1. Each `Case` carries a `source` id into `chronoscopelab.data.provenance.SOURCES`.
2. The **manifest** records a `provenance` block: `{source, license, citation, public_artifact_ok}`.
3. The **export stage** computes `redact_raw = not public_artifact_ok(source)`. When true:
   - the **trace** omits `history`, `actual`, and every method's `point`/`lower`/`upper` (the raw excerpt and
     the per-step forecast paths), keeping only each method's aggregate `backtest` block, and sets
     `redacted: true`;
   - the **analysis artifact** drops the point-wise series-derived arrays (ACF, PSD, KDE grid, decomposition
     components, MF-DFA spectrum, ...) and keeps only the scalar verdicts (test statistics, exponents,
     change-point counts), tagged `_redacted`.
4. The frontend contract types mirror this: `point/lower/upper` are optional and `trace.redacted` is a boolean,
   so a redacted trace typechecks and the App shows it in the leaderboard but not the forecast chart.

The guard is symmetric and honest: a public-safe source ships the full trace; a local-only source ships only
what its license permits, and says so in the manifest. New sources default to LOCAL-only until their license
is verified.

## Adding a source

1. Add a `DataSource` to `SOURCES` in `provenance.py` with its verified license + `public_artifact_ok` verdict
   (default `False` until the license is confirmed).
2. Point the case's `source` field at the new id.
3. The manifest, the export guard, and the docs table follow automatically; add the source's row here.

## References

- Verified license dossier: `wip/chronoscope/deep-research-datasets-licenses-2026-07-04.md` (CAOS_MANAGE vault).
- Creative Commons BY 4.0: <https://creativecommons.org/licenses/by/4.0/>.
