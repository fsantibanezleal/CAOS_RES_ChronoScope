# Forecasting after an unfinished season

**Question:** When the forecast origin moves five observations earlier, does HoltWinters continue the correct seasonal phase, and how do its lead-specific errors compare with a repeated season?

## Objectives

Investigate a concrete implementation risk rather than assuming that a familiar method name guarantees a correct forecast. We will shorten a committed history, construct the corresponding target from observations that follow the new origin, and call the actual additive HoltWinters implementation. We then compare the path with two simpler methods and inspect both aggregate and lead-specific errors. The experiment deliberately changes the temporal cut while keeping the underlying observed sequence fixed.

A seasonal model stores components indexed by position in a cycle. If a history ends halfway through that cycle, forecasting must continue from that position. Restarting the seasonal component at its first slot can generate a plausible looking oscillation with the wrong phase. This defect is particularly easy to miss when every demonstration history happens to contain an integer number of seasons. The example therefore removes a fixed, predeclared number of observations before fitting.

## Setup

Use the isolated notebook environment with these direct pins. The code imports the product functions instead of defining another HoltWinters implementation whose behaviour might differ from the app.

```text
{{PINS}}
```

<!-- code: setup -->

## Data

The original generated trend-plus-seasonal trace provides a historical prefix and a reserved final block. For the earlier origin, the final five historical observations become the first five future targets. The remaining targets come from the original holdout. This concatenation preserves chronological order. Neither the newly reserved observations nor the original holdout enters fitting. Scores at the earlier origin must not be compared as if they used the original target block: the question, available information and target have all changed.

<!-- code: data -->

## Method

The first fit uses the shortened prefix. The second fit uses the complete original history and is retained only to distinguish the two forecast origins. In additive HoltWinters, level, trend and seasonal components are updated together using finite parameter grids. The forecast must use the seasonal slot corresponding to the full length of the fitting prefix plus the requested lead. The printed remainder identifies whether the shortened history ends on a cycle boundary. That value is a direct check of the experimental condition, rather than a forecast accuracy measure.

<!-- code: partial -->

SeasonalNaive provides a phase-aware reference because it copies the final observed cycle relative to the new origin. Theta supplies a second comparison with drift but without the same automatically fitted seasonal structure. Both must be refitted on the shortened history. Keeping a forecast trained on the original longer history would give that competitor access to observations that the earlier-origin method could not have seen. This is a small example of temporal leakage that a shared target alone would not prevent.

<!-- code: phase_baseline -->

The corrected local Theta equation remains useful as a contrasting mechanism even when its score is not the main outcome. Its finite-history correction depends on the number of observations available at fitting, so moving the origin also changes that correction. A test that compares only forecast shapes can overlook such dependencies. We call the implementation again with the original prefix to make its information set explicit, while leaving the earlier-origin scores tied exclusively to earlier-origin predictions.

<!-- code: theta -->

Scoring uses the shortened prefix to compute the historical seasonal scale and the newly assembled target block to compute future errors. Coverage is the fraction of those targets falling between the lower and upper Gaussian quantiles. It is a sample fraction from one block, not a probability guarantee for the next individual observation. Width and coverage should be considered together: a method can cover more targets by producing intervals too wide to guide a useful action. This lesson prints coverage but does not optimize interval settings against the reserved target.

<!-- code: phase_scores -->

In the first figure, compare the timing of the predicted peaks with the corresponding observed peaks. A correct implementation can still make large errors because its trend or estimated seasonal amplitude is imperfect. Conversely, a low aggregate error on a nearly flat series would be weak evidence that seasonal indexing was correct. This generated case has visible structure specifically so that phase can be inspected. The independent regression tests in the repository additionally exercise histories whose lengths are not divisible by the seasonal period.

<!-- code: phase_plot -->

The displayed paths distinguish alignment from accuracy. Following the correct slots is necessary for the stated HoltWinters algorithm, but it does not ensure that the resulting seasonal estimate is appropriate for a future regime. Check the origin and the oscillation together rather than attributing every discrepancy to phase. A changed level or imperfect drift can shift the whole forecast while leaving its seasonal positions intact. That interpretation motivates looking at individual leads in the next figure.

Lead-specific absolute errors preserve the units of the series and expose which future observations dominate the average. Each point is one error at one lead, not an estimate averaged over many origins. A peak in this curve can therefore reflect one unusual target rather than a general weakness at that horizon. We show the seasonal reference on the same axes so that any relative improvement is visible directly. No confidence interval or significance test is attached to this small deterministic comparison.

<!-- code: phase_errors -->

The error plot reveals whether the two methods fail on the same positions or trade errors across the block. Their curves can cross, so a lower average does not imply improvement at every lead. That matters when a planning process values near-term service more than a distant forecast. Such costs would need to be declared before choosing a weighted criterion. The present lesson keeps every lead equally weighted and retains the seasonal reference's independently printed MASE.

## Results

**Answer:** Earlier-origin HoltWinters has MASE 0.4948, versus 1.0136 for SeasonalNaive. Removing five observations creates an unfinished season that the corrected implementation continues from its actual terminal position. The paths and printed earlier-origin scores quantify this case. The error curve compares every future lead with SeasonalNaive on the same new target block; it does not justify ranking the methods against scores from the original, later origin.

Implementation correctness and empirical quality are separate conclusions. The independent partial-season test can falsify the indexing rule without claiming population superiority. The observed error can falsify an accuracy expectation on this case without proving the indexing rule wrong. Keep both forms of evidence when diagnosing a forecast, and retain an unfavorable result instead of changing the origin until a preferred method wins.

## Summary

Record the exact information set whenever the temporal cut moves. Build the corresponding future target in chronological order, refit all competitors, and recalculate the historical scale from that prefix. Use adversarial histories with incomplete seasons to test a seasonal algorithm. Then examine both whole-block scores and individual errors, while keeping clear that one forecast origin supplies neither a population estimate nor a deployment acceptance test.


### Sensitivity to the position inside a day

Number the prefix observations from zero. If its length is $n$, the next
seasonal slot is $n\bmod m$. An additive HoltWinters fit retains a level
$\ell$ and trend $b$ in source units and source units per step, plus $m$
seasonal offsets $s$ in source units. For a lead $j$ counted from one, the
released forecast is

$$
\widehat y_{n+j-1} = \ell + jb + s_{(n+j-1)\bmod m}.
$$

For $m=12$, a prefix of length 125 advances to slot 5. Starting the forecast
at slot zero would reuse the seasonal position of the first observation,
although the predicted day has already advanced five slots. Refit before
changing the cutoff, because moving it also changes the estimated level and
trend. The search in this implementation tries four level coefficients,
two trend coefficients and three seasonal coefficients. It minimizes squared
one-step residuals after the initial seasonal cycle. Below two complete
cycles, the public method falls back to Holt, since it cannot estimate this
seasonal initialization from the available observations.

The synthetic control above isolates phase with a known period. The following
experiment moves to the committed MT_010 electricity excerpt (Trindade,
UCI, CC BY 4.0, [DOI 10.24432/C58C86](https://doi.org/10.24432/C58C86)).
Each hourly-labelled value sums four successive quarter-hour power readings
in kW. These sums have not been converted to energy. The first retained
timestamp is 00:15 and later timestamps advance by one hour. The data contain
480 rows. A daily reference has $m=24$ and a weekly reference $m=168$. We
compare both seasonal-naive forecasts and daily HoltWinters at cutoffs
312 through 368, stepping by seven observations to move across different
daily phases. At each cutoff all three forecast the same 24 reserved
observations. We score them with one common daily lag scale so that the
weekly method does not get a different denominator.

$$
s_{24}(y_{0:n})=\frac{1}{n-24}\sum_{i=24}^{n-1}|y_i-y_{i-24}|,
\qquad
\operatorname{MASE}_{24}=\frac{\sum_{j=1}^{24}|a_j-\widehat y_{n+j-1}|}{24s_{24}(y_{0:n})}.
$$

The daily seasonal reference must copy the 24 values immediately preceding
the cutoff. The cell calculates the maximum difference from direct indexing, which should be zero.

<!-- code: electricity_phase -->

The plot gives a conditional comparison at each cutoff. A curve crossing
changes the local ordering. Read the printed phase beside the observation
index: the same phase can recur after a different calendar history, so the
phase by itself does not explain every score difference. The target windows
overlap because seven observations separate cutoffs and each block has
24 observations. The nine points therefore do not constitute nine
independent replications. Also, the weekly reference accesses a specific
earlier weekday rather than fitting a weekly effect. A poor weekly score at
one cutoff does not disprove weekly structure.

### Using this method on your own data

Supply one timestamp-sorted, equally spaced finite series and identify which
values were available at the forecast origin. For hourly observations, try
period 24 when a daily cycle is scientifically relevant. Confirm the sampling
cadence before comparing period 168. Distinguish a missing hour from an
observed zero, and do not quietly compress the timestamp index when there are
gaps. Split off the next contiguous block before calling
`holt_winters(prefix, m, horizon)`. The method returns the forecast vector
and a residual dispersion in the input's measurement unit. Check that the
vector has the requested length and compare its phase with the independently
indexed seasonal reference. Calculate the common scale only from the prefix.
A constant or exactly periodic prefix can have zero lagged error and thus
an unavailable scaled score. Keep absolute errors in that case. When the
residual dispersion is used to form a Gaussian interval, assess its observed
coverage and width separately from point error. A forecast may have a correct
phase and still miss a shift in level or amplitude.

## References

- Seasonal continuation: https://otexts.com/fpp3/holt-winters.html
- Theta correction: https://robjhyndman.com/papers/Theta.pdf
- Error scaling: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Feature-dependent combinations: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Dynamic ensembles: https://doi.org/10.1007/s10994-018-05774-y
- A. Trindade, ElectricityLoadDiagrams20112014, UCI. [Dataset](https://doi.org/10.24432/C58C86).
