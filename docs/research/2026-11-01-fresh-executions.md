# Fresh forecasting executions

All 22 variants were freshly fitted or inferred on the same 15 original contiguous prefixes and final targets. Source, input, checkpoint and runtime identities are recorded in `data/derived/fresh-reevaluation.json`. The independent admission checker recomputes every metric.

The archived-path comparison remains in `data/derived/reevaluation.json`; repeated executions on these targets are not independent statistical replications. Settings were not tuned after the negative ContextMemory result.

| Method | Archived MASE | Fresh MASE | Fresh coverage |
|---|---|---|---|
| Chronos-Bolt | 1.036306 | 1.036307 | 0.756349 |
| TimesFM-2.5 | 1.063329 | 1.063327 | 0.807143 |
| TiRex-2 | 1.080935 | 1.080932 | 0.769444 |
| Chronos-2 | 1.155534 | 1.155536 | 0.690476 |
| DLinear | 1.160029 | 1.160028 | 0.559524 |
| AutoARIMA | 1.210400 | 1.210398 | 0.781349 |
| NLinear | 1.229783 | 1.229776 | 0.452381 |
| LightGBM | 1.298326 | 1.298326 | 0.578571 |
| NHITS (nf) | 1.254627 | 1.299264 | 0.496825 |
| NHITS | 1.289821 | 1.303106 | 0.474603 |
| SeasonalNaive | 1.413663 | 1.413663 | 0.870238 |
| RecencyMean | 1.448883 | 1.448883 | 0.888889 |
| ContextMemory | 1.450435 | 1.450435 | 0.894444 |
| AutoTheta | 1.496432 | 1.496434 | 0.732937 |
| HoltWinters | 1.677762 | 1.677762 | 0.863889 |
| AutoETS | 1.694031 | 1.694037 | 0.763889 |
| NLinear (nf) | 1.754699 | 1.754700 | 0.182143 |
| EqualMean | 1.896958 | 1.896958 | 0.861111 |
| SES | 1.916657 | 1.916657 | 0.827381 |
| Theta | 1.922377 | 1.922377 | 0.827381 |
| Holt | 3.984587 | 3.984587 | 0.730159 |
| DLinear (nf) | 10.738474 | 10.738476 | 0.499603 |

Timings include fitting, inference and first-use loading/imports. They are not a warm-inference or hardware-normalized ranking. Warning categories are retained; finite output does not establish optimizer convergence or calibration. Pretraining overlap remains unverified. TimesFM 3.0 is documented separately because its newer weights have noncommercial, nonproduction terms; 2.5 remains the admitted checkpoint.

The bounded LightGBM worker and compiler settings are documented in the [execution guide](../guides/fresh-reevaluation.md). The stopped unbounded candidate and the earlier line-ending candidate were never admitted. Text sources and generated comparison JSON use LF, matching the repository attributes and Linux CI.
