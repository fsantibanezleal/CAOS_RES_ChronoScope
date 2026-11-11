# Manuscripts and revisions

The two preprints and the technical report passed independent review. Each final DOI-bearing PDF matches a fresh anonymous download. The technical report documents the forecast and diagnostic procedures, contract fields, and validation of the retained numerical evidence.

| Document | Published version | Canonical PDF | Source |
|---|---|---|---|
| Prequential Evaluation of Adaptive Prediction Intervals: A Fifteen-Series Replay Study | [v2.6, DOI 24123073](https://doi.org/10.5281/zenodo.24123073) | [22-page preprint](prequential-streaming-conformal/main.pdf) | [LaTeX](prequential-streaming-conformal/tex/main.tex) |
| Temporally Validated Forecast Combinations on Two Benchmark Collections | [v0.3, DOI 24123068](https://doi.org/10.5281/zenodo.24123068) | [26-page preprint](context-memory/main.pdf) | [LaTeX](context-memory/tex/main.tex) |
| ChronoScope: Time-Series Diagnostics and Forecast Evaluation | [v0.26.000, DOI 24124790](https://doi.org/10.5281/zenodo.24124790) | [85-page technical report](product-report/main.pdf) | [LaTeX](product-report/tex/main.tex) |

The combination paper and report cover ContextMemoryCV, ValidationMix and the complete external M4 Weekly/M3 Monthly evaluation. Both new methods lower point error relative to RecencyMean on each admitted collection; AutoTheta remains stronger on monthly point error and both collections' interval scores. All 53,148 external forecasts are independently rescored. The original ContextMemory and M4 Daily selection outcomes remain unchanged.

The streaming revision corrects the overbroad stateful-evaluation title, historical algorithm identities, coverage statistics and figures. It supplies complete numerical replay, sensitivity settings and additional generated seeds while retaining limits on runtime and generalization.

The [report reproduction guide](product-report/REPRODUCING.md) identifies the numerical checks, tables and figure builders. The complete set of current generators and experiment bindings is available in the [reviewed source snapshot](https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/tree/2f7e0447cff0db2b4903a63cc034738d2f3510f0).

The report retains concept DOI [23874816](https://doi.org/10.5281/zenodo.23874816), the combination study [23874820](https://doi.org/10.5281/zenodo.23874820), and the streaming study [21508920](https://doi.org/10.5281/zenodo.21508920). Earlier publication receipts remain under each folder's history and in immutable Git history. Each manuscript record contains exactly one PDF; software and numerical evidence are separate. These documents are not peer-reviewed articles.
