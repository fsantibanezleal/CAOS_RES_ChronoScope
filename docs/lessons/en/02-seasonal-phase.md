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

## References

- Seasonal continuation: https://otexts.com/fpp3/holt-winters.html
- Theta correction: https://robjhyndman.com/papers/Theta.pdf
- Error scaling: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Feature-dependent combinations: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Dynamic ensembles: https://doi.org/10.1007/s10994-018-05774-y
