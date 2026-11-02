# Does coarse-graining change the ordering evidence?

**Question:** How do entropy, symbolic complexity and time reversal describe different aspects of the same observed sequence? We use the structural-break case rather than replacing it with an idealized process, and keep a constant sequence as a control with a known answer. The aim is to understand each calculation's information and units. None of these summaries, by itself, identifies a forecasting winner or demonstrates a deterministic physical mechanism.

## Objectives

Calculate coarse-grained entropy with fixed original tolerance, inspect binary phrase counts, compare time reversal and repeat a locally seeded robust fit. Identify missing estimates before interpreting a curve.

## Setup

The environment includes the sequence implementation, its numerical libraries and the seeded robust estimator. All inputs for the worked case are committed. An observation index means the same original interval throughout the lesson. This matters when a coarse-grained block represents several observations: its scale is an operation on the original data, not a label attached to a resampled plotting coordinate.

{{PINS}}

<!-- code: setup -->

## Data

The admitted artifact preserves the source identity and the observations used below.

<!-- code: data -->

## Method

Costa multiscale entropy forms one reduced sequence per scale by averaging non-overlapping blocks. A scale of four retains the mean of each successive four-observation block and discards only an incomplete terminal block. Sample entropy then compares short patterns in that reduced sequence. The order is two: we ask whether similar two-observation patterns remain similar when extended to a third observation, excluding self matches from both counts.

<!-- code: entropy -->

Tolerance is fixed to a fraction of the original standard deviation. It does not shrink or expand independently with each reduced sequence. Re-estimating tolerance at every scale could make some curves appear artificially similar and would answer a different question. The output includes matching pair counts and observation counts, making a missing estimate inspectable. An absent value can arise because there are too few reduced observations or because no template extensions match; neither situation means zero complexity.

<!-- code: constant -->

The constant control separates unavailable estimation from a legitimate zero. When enough observations remain, every eligible pair and extension matches, so the entropy is zero. At a coarse scale with fewer than twenty observations, the product intentionally reports no estimate. The sample-size boundary is a declared reporting rule, not a theorem that all longer estimates are reliable. Short finite sequences can still produce unstable counts near the tolerance threshold.

Time-reversal asymmetry examines a third-order lagged moment. We use lag two and compute the same statistic after reversing the observations. The raw result has cubed source units; standardization before calculation removes location and scale. Reversing the complete ordering exchanges the two terms and changes the sign, which provides an exact structural check. It does not supply a p value or establish that a finite departure is statistically significant.

<!-- code: reversal -->

Lempel-Ziv complexity takes another route. Values above the median become one, and all other values become zero. The resulting binary sequence is parsed into new phrases. We retain the phrase count as well as its asymptotic normalization, c(n) log2(n)/n. A normalized value above one is possible for a finite sequence and is not clipped. This symbolic encoding discards amplitude information and assigns tied observations consistently; changing the threshold or alphabet changes the method.

<!-- code: symbols -->

A change of positive units and an additive offset should preserve the median ordering and the standardized statistics, apart from numerical precision. It also multiplies the original entropy tolerance by the same scale factor as the observations. We run the implementation again after that transformation instead of assuming that all quantities are dimensionless. The raw third-order statistic must not be compared numerically across units without acknowledging its cubic scaling.

<!-- code: units -->

## Results

**Answer:** <!-- code: entropy_plot -->

The two curves share a declared tolerance convention, but they describe different sequences. The case curve can change as local ordering is averaged away, whereas the constant control remains at zero wherever the sample-size rule admits an estimate. Missing endpoints should remain visible as missing values. A falling curve alone does not prove randomness, and a sustained curve does not prove useful long-range forecast information in this finite, nonstationary record.

<!-- code: reversal_plot -->

The bars visualize a sign reversal under a known ordering transformation. Their magnitudes refer to standardized observations, so their labels do not inherit the raw source's cubic units. The symmetric appearance is a property of the statistic under reversal, not independent evidence for a physical direction of time. A surrogate experiment or another properly specified test would be needed to interpret statistical departures under a particular null model.

Answer: the case tolerance is {{TOLERANCE}} and stays fixed across the entropy scales. The constant control has scale-one entropy zero, while its short coarse endpoint is unavailable. These outputs distinguish a measured zero from an estimation boundary. The symbolic phrase count survives the positive unit conversion; the reversed standardized statistic changes sign. Together they illustrate why several diagnostics can be useful without treating them as interchangeable estimates of a single hidden quantity called complexity.

The seeded nonlinear slope calculation addresses a different reproducibility issue. Its robust fit uses a local random_state over the library's exposed log-distance data. Repeating that fit should not depend on random draws made by another caller. The pipeline derives a seed from case identity and its supplied seed, and retains the surrogate gate before any chaos verdict. Deterministic numerical output is a necessary implementation property, not evidence that the observed process itself is deterministic.

<!-- code: seeded -->

### Limitations

The structural-break case contains changing levels and a finite observation budget. Global entropy and asymmetry summaries can combine several regimes rather than identify one stable mechanism. Binary symbolization hides amplitude distinctions and can be sensitive to ties. Matching counts depend on order, tolerance and length. The M4 study therefore treats these values as prefix features with a declared protocol, tests their association with subsequent error, and keeps negative findings rather than interpreting every irregular curve as predictive structure.

## Summary

Entropy, phrase counts and lagged moments discard different information. Their units, unavailable values and reproducibility conditions are part of the result rather than optional annotations.

### Reproduce

Execute each method call and both figures in order. Confirm the reported tolerance, the constant control's zero and missing endpoint, the phrase-count comparison and the repeated robust estimates. The repository's independent pair-count and RNG-state tests cover numerical properties beyond these worked outputs; this lesson provides an interpretable example rather than replacing those tests with a graph.

## References

Costa, Goldberger and Peng, DOI 10.1103/PhysRevLett.89.068102. Lempel and Ziv, DOI 10.1109/TIT.1976.1055501. The tsfresh feature definition specifies the lagged third-order reversal statistic, and nolds documents the correlation-dimension and Lyapunov fitting data used by the seeded adapter.

[Nolds fitting documentation](https://cschoel.github.io/nolds/nolds.html).
