# Held-out linear forecasts and interval calibration

The first study follows the committed
[protocol](../../guides/browser-linear-protocol.md). Its complete generated
series, predictions, candidate matrix, calibration metadata and runtime/source
receipt are preserved in `v1/`. Two independent process runs reproduced every
output byte. The old 2,413-byte deployed matrix is unchanged.

The selected ridge penalty was 0.1, based only on 200 validation series.
Training used 52,144 windows from 400 series; calibration used 400 independent
series and testing another 400. The generator includes noise, trend, seasonal
and trend-plus-seasonal sequences. It is synthetic, not authentic field data.

| Metric on held-out series | Frozen browser model | Selected ridge with calibrated intervals |
|---|---:|---:|
| Normalized mean squared error | 0.548742 | 0.550561 |
| Normalized mean absolute error | 0.514146 | 0.517982 |
| Marginal coverage, nominal 80% | 96.60% | 79.46% |
| Normalized mean interval width | 4.593046 | 1.659786 |
| Normalized interval score | 4.764406 | 2.781262 |

The paired series bootstrap difference in squared error, candidate minus
frozen, is +0.001819 with exploratory 95% interval [0.000145,0.003465]. The
candidate does not improve point error. Its interval-score difference is
-1.983145 [-2.112696,-1.848951]; 358 of 400 series have lower interval score.
These are normalized losses, not MASE or MSIS. The unadjusted intervals are
conditional on this independent-series synthetic sampling design.

The overall coverage hides a material limitation: coverage is 53.06% for the
noise family, 76.60% for trend, 93.85% for seasonal and 94.21% for trend plus
seasonal. Global marginal calibration does not imply family-conditional
validity. A single overall coverage percentage would conceal this behavior.
The maximum normalized ONNX-versus-NumPy error was 0.000000507. Execution
parity establishes numerical agreement, not forecasting accuracy.

The [separate confirmation protocol](../../guides/browser-calibration-confirmation-protocol.md)
therefore retains the deployed point matrix and compares global and
prefix-stratified calibration on fresh series. The earlier test is not reused
as confirmation. No new matrix, interval metadata or empirical generalization
claim is admitted to the browser by the first experiment alone.
