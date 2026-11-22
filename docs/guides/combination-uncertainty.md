# Uncertainty of the external combination comparison

The original external experiment scores 1,716 admitted series at 4,429 forecast
origins. Those origins are not 4,429 independent replications: several belong to
one series and share most of their fitting history. The paired analysis keeps
each series together and measures how the reported aggregate changes when the
empirical collection is reweighted by resampling its identities.

This is an exploratory analysis specified after the original outcomes were
available. It changes no forecast, candidate family, validation schedule, model
weight or exclusion. It is not a new external confirmation, a new training run
or a correction of an unfavorable outcome. The frozen full-precision audit is
the input; rounded browser paths are not used to calculate these intervals.

## Estimand and unit of resampling

Let `s` identify an admitted series and `o` one of its available origins. For
metric `L`, compute the within-series mean `L_s(A)` for method `A`. A series with
three origins then has the same final weight as a series with one origin. For a
comparison with control `B`, the paired observation is

$$d_s=L_s(A)-L_s(B),\qquad \bar d=\frac{1}{N}\sum_{s=1}^{N}d_s.$$

MASE and MSIS are losses, so a negative difference favors `A`. Coverage is a
frequency, so its signed difference has no universal preferred direction. In
particular, higher coverage can accompany wider and less useful intervals.
The analysis preserves coverage differences but does not label them gains.

One bootstrap sample draws `N` series indices with replacement and averages the
corresponding paired differences. It never samples the two methods separately,
never pools the weekly and monthly collections, and never samples individual
forecast leads as independent evidence. The reported interval is

$$[q_{0.025}(\bar d^*),q_{0.975}(\bar d^*)],$$

using 10,000 samples and linear empirical quantiles. The local PCG64 generator
uses seed 20261105 plus a stable dataset-specific offset. Each comparison in a
collection uses the same resampled identities, preserving the paired design.
Batch size bounds memory use and does not change the generated samples.

## Measured comparisons

The table reports ValidationMix minus each named control. The complete JSON
also contains ContextMemoryCV, AutoETS and signed coverage differences: 36
comparisons in total. Values below are rounded for reading; the evidence file
retains full precision.

| Collection | Control | Metric | Mean difference | Exploratory 95% percentile interval | Series with lower loss |
|---|---|---|---:|---|---:|
| M4 Weekly | RecencyMean | MASE | -0.025337 | [-0.033914, -0.017227] | 190 / 294 |
| M3 Monthly | RecencyMean | MASE | -0.009154 | [-0.013176, -0.005173] | 589 / 1,422 |
| M4 Weekly | AutoTheta | MASE | -0.022065 | [-0.037521, -0.008272] | 155 / 294 |
| M3 Monthly | AutoTheta | MASE | 0.052154 | [0.032437, 0.073112] | 689 / 1,422 |
| M4 Weekly | RecencyMean | MSIS | -0.383808 | [-0.431160, -0.334374] | 252 / 294 |
| M3 Monthly | RecencyMean | MSIS | -0.063788 | [-0.088692, -0.040255] | 589 / 1,422 |
| M4 Weekly | AutoTheta | MSIS | 0.835230 | [0.650853, 1.038115] | 49 / 294 |
| M3 Monthly | AutoTheta | MSIS | 2.521379 | [2.364504, 2.673453] | 267 / 1,422 |

The mean and the win count answer different questions. On M3 Monthly,
ValidationMix has a lower mean MASE than RecencyMean, while fewer than half of
the series have a strictly lower loss. Unequal magnitudes of improvements and
regressions can produce that combination. It would be incorrect to translate
an aggregate gain into a claim that most series improve.

Against AutoTheta the point-error comparison depends on the collection.
ValidationMix has the favorable weekly difference, while AutoTheta retains
the favorable monthly difference. AutoTheta has the lower MSIS on both
collections. The uncertainty analysis therefore supports a bounded reading of
the measured differences, not a single unconditional winner across metrics.

## Assumptions and limits

The entire admitted collection has already been enumerated; its observed mean
is not uncertain merely because a bootstrap interval is drawn. The interval
describes sensitivity to empirical series resampling. A confidence statement
about a larger population additionally requires a defensible sampling model,
exchangeability and sufficient independence between series. Exact duplicate
removal does not establish those assumptions: series can share industries,
sources, seasonal drivers and acquisition procedures without being identical.

These are unadjusted exploratory intervals for multiple comparisons. Their
nominal level does not establish simultaneous familywise coverage, and they
are not a basis for declaring all compared hypotheses significant. The script
does not calculate a collection of post hoc p-values or choose a method from
the intervals. No interval is interpreted as a forecast prediction interval.

The intervals also omit uncertainty from alternative source populations,
unobserved future regimes, changed expert implementations, different tuning
families and pretrained model exposure. They do not estimate operational value
or calibrated predictive coverage. A new method-selection claim would need a
separately fixed protocol and genuinely held-out evidence.

## Regeneration and checks

From the repository root, using the pinned scientific environment:

```powershell
python scripts/summarize_combination_uncertainty.py --output manuscripts/context-memory/evidence/paired-series-uncertainty.json
python -m pytest tests/test_combination_uncertainty.py
```

The script verifies both compressed and decompressed audit checksums against
the public combination index before reading any score. It records the audit
hash, its own source hash, NumPy version, exact resampling protocol and all
comparisons. It has no target-dependent tuning or model-fitting call. A repeated
run under the pinned environment produces the same JSON bytes.

The tests cover an exactly known constant paired effect, equal series weighting
with unequal origin counts, deterministic batching, preservation of caller RNG
state, duplicate identities and refusal of nonfinite observations. The separate
local admission tests ensure that an altered or incomplete study cannot enter
the release merely because an older comparison remains valid.

## Sources

Efron introduced empirical bootstrap resampling in
[Bootstrap Methods: Another Look at the Jackknife](https://doi.org/10.1214/aos/1176344552).
The method here is the simple paired percentile construction, with its empirical
unit and assumptions stated explicitly rather than a dependence correction.

Demšar's [Statistical Comparisons of Classifiers over Multiple Data Sets](https://www.jmlr.org/papers/v7/demsar06a.html)
concerns comparisons across datasets and motivates preserving the experimental
unit. Its classification testing recommendations do not, by themselves, justify
independent-series inference for these forecasting collections.
