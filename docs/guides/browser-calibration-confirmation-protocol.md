# Prefix-stratified interval confirmation protocol

Version 1, specified on 2026-11-05 after the first browser-linear experiment
and before evaluating the new partitions below. This is a new experiment, not
a reinterpretation of its predecessor's test set. The previous test showed
79.46% overall coverage but only 53.06% for its white-noise family. Its selected
ridge point error was slightly worse. Both outcomes remain part of the record.

## Fixed point forecasts and prefix-only strata

Keep the deployed linear point map byte-identical (SHA-256
`621265165211f756cff537adee364b9790c34ced567bc2a5087513360e1f69f6`).
There is no training, penalty grid or point-model selection in this follow-up.
Compare its current Gaussian bands, global split-conformal bands and
prefix-stratified split-conformal bands around those identical points.

For the 48-value observed window x, compute roughness as the mean squared
first difference divided by population variance of x. The denominator must be
finite and positive. Roughness is invariant to translation and positive unit
changes; it does not use a future observation or a generator-family label.
Use the fixed bins [0, 0.5), [0.5, 1.25), [1.25, infinity). White noise has
population roughness near two; a well-sampled sinusoid has first-difference
energy ratio about 2(1-cos(2*pi/period)). The bins separate smooth sequences,
short-period oscillations and rough prefixes without fitting labels. They are
engineering choices, not parameters selected by searching the new test set.

For each bin and lead, calibrate the absolute normalized prediction residual
using order statistic ceil((n_bin+1)*0.8). Require at least 20 calibration
series in every bin, otherwise fail the experiment. A global calibration arm
uses the same calibration series without binning. The stratified construction
has marginal per-lead validity within its fixed bins under exchangeable series;
it does not promise simultaneous path coverage, conditional validity for every
prefix, or coverage within the unobserved generator-family labels. See the
group-conditional discussion in
[Angelopoulos and Bates](https://arxiv.org/abs/2107.07511).

## Independent confirmation population

Retain the same four-family synthetic generator, equal family sampling,
periods 6/12/24 and length sampling [120,260). Use PCG64 seed 20261109 for
400 calibration series and seed 20261110 for 800 test series. Each series
contributes its final 48-to-12 window only. Verify no identity overlaps the
previous study. Preserve every generated series and raw-scale prediction.
Run the actual frozen ONNX matrix for both calibration and testing.

The primary comparison is stratified minus current-Gaussian normalized interval
score at alpha=.2. Also report stratified minus global-calibration score,
coverage and width overall, by prefix bin, by generator family and by lead.
Retain the normalization and explicit scoring equations of
`browser-linear-protocol.md`. Calculate 10,000 paired series bootstrap means
with PCG64 seed 20261108 and unadjusted 95% percentile intervals. No test
outcome may modify the bins, seeds, sample sizes or acceptance criteria.

Admission for possible browser use requires: identical point predictions in
all three arms; no old model/source artifact changed; all bin counts at least
20; mean interval score below the current Gaussian arm; overall test coverage
in [0.75,0.85]; coverage in every roughness bin in [0.70,0.90]; actual ONNX
versus float32 NumPy normalized error below 0.0001; and independent rescoring
of every stored forecast. These are engineering admission criteria for this
fixture, not a claim of application-wide scientific acceptance. Report all
family and lead deviations even if these criteria pass. Browser state,
metadata, bilingual explanations and unavailable-input handling require their
own tests before adoption. Authentic series require separate evaluation.

Write only to an empty external directory; keep this protocol, source hashes,
runtime identity, full-precision predictions, calibration radii and the prior
study digest in the receipt. A failure remains a result and must not be hidden
by selecting a different confirmation seed.
