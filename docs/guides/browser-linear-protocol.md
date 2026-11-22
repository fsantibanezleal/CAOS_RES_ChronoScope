# Held-out browser linear model protocol

Protocol version 1, specified on 2026-11-05 before new validation, calibration
or test results were generated. The integer seeds below are random-generator
identifiers. They do not denote dates of data collection.

## Question and fixed comparator

Can selection of a regularized global linear predictor and calibration on
independent synthetic series improve the browser reference's point errors or
interval scores? This is an engineering comparison of ordinary linear methods,
not a new forecasting architecture or a state-of-the-art claim. The deployed
`nlinear.onnx` is an instance-normalized least-squares map, distinct from the
per-prefix PyTorch and NeuralForecast fits. Preserve its bytes, metadata and
published results. Its SHA-256 is
`621265165211f756cff537adee364b9790c34ced567bc2a5087513360e1f69f6`.

The comparator uses that frozen matrix, the last 48 observations, subtraction
of their last value and division by their population standard deviation. Its
80% Gaussian bands use the existing training-residual `sigma_norm` and
`sqrt(lead)` multiplier. These are evaluated as implemented, without calling
them calibrated. A repeat-last point forecast supplies a second simple control.

## Population, partitions and selection

Use exactly the generator and four equiprobable families in
`scripts/train_nlinear_onnx.py`: seasonal, trend plus seasonal, trend and noise.
Retain its period choices 6, 12 and 24 and length sampling [120, 260). This
generator is a synthetic fixture; none of its series are observations of a
plant, economy or patient. Each partition has its own local PCG64 generator.

| Partition | Series | Seed | Permitted use |
|---|---:|---:|---|
| Training | 400 | 20260704 | Fit all overlapping 48-to-12 windows; same population and draw sequence as the old training recipe. |
| Validation | 200 | 20261105 | Choose one ridge penalty by mean normalized squared error. |
| Calibration | 400 | 20261106 | Compute separate absolute-error quantiles for each of 12 leads after selection. |
| Test | 400 | 20261107 | Evaluate the frozen selected point map and intervals once. |

Validation, calibration and test each contribute only the final complete
48-to-12 window of each independent series. Never split overlapping windows
of one series between partitions. Persist series identities, family, length,
source hashes and every test forecast, interval and observed target.

Fit the global matrix W by minimizing mean squared normalized training error
plus lambda times its squared Frobenius norm. Select lambda from the fixed
ordered grid [0, 0.000001, 0.0001, 0.01, 0.1, 1, 10]; exact ties choose the
earlier grid entry. The unpenalized entry uses least squares, not an unstable
inverse of a singular Gram matrix. Cast each candidate matrix to float32
before validation to match export precision. Do not refit after validation.
No calibration or test observation may enter selection or fitting.

## Intervals and decision metrics

For each lead, sort the 400 absolute normalized calibration errors and take
order statistic ceil((400 + 1) * 0.8), with one-based indexing. Use that fixed
radius around the selected point forecast and transform back using the
observed lookback's scale. This is a marginal interval for each lead; it is
not simultaneous coverage of the whole path and not a conditional guarantee
within any family. Finite-sample split-conformal reasoning requires independent
exchangeable series from this same generator. It does not establish coverage
on the app's arbitrary user inputs or the four existing real case histories.
The construction follows the absolute-residual split procedure described by
[Angelopoulos and Bates](https://arxiv.org/abs/2107.07511).

Primary point metric: series-mean squared error after dividing errors by the
observed lookback's population standard deviation. Primary interval metric:
series-mean interval score at alpha=0.2 on that same normalized scale. Also
report normalized absolute error, marginal coverage and normalized width,
overall and by generator family. The interval score is width plus ten times
each lower or upper exceedance. Each test series has equal weight. These
normalized errors are not MASE, and interval score is not MSIS.

Report the selected candidate minus the frozen comparator for both primary
losses, together with 10,000 paired series bootstrap means (PCG64 seed
20261108; 2.5% and 97.5% linear percentiles). These two unadjusted exploratory
intervals characterize this test sample, not a multiplicity-controlled
discovery. Preserve a zero or negative improvement. Do not change the grid,
generator, seeds, split sizes or metrics after viewing test outcomes.

## Numerical admission and artifacts

Refuse nonfinite data, unsupported horizons, zero or nonfinite lookback scales
and malformed matrices. No arbitrary raw-unit scale of one is permitted for
a constant prefix. Positive changes of measurement units and translations
must preserve normalized predictions, intervals and scores within tolerance.
Verify float32 ONNX Runtime output against NumPy for all test inputs, retain
the maximum error, and require absolute normalized error below 0.0001.

Training writes only to an explicit empty external output directory. The run
receipt binds this protocol, trainer, original generator, comparator, metadata,
runtime versions and all generated files. The final result file is written
after numerical parity succeeds. The old canonical model is not replaced.
Browser adoption, authentic-data evaluation, repeat-seed robustness and a new
published release require their own validation and evidence.
