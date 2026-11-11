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

**Answer:** The binary phrase count is 13 and its normalization is 0.3566. The entropy curve varies with scale under one fixed original tolerance, while the binary phrase count describes a different representation. Reversal changes the signed lag statistic. None of these descriptive values alone certifies chaos, significance or forecast accuracy.

<!-- code: entropy_plot -->

The two curves share a declared tolerance convention, but they describe different sequences. The case curve can change as local ordering is averaged away, whereas the constant control remains at zero wherever the sample-size rule admits an estimate. Missing endpoints should remain visible as missing values. A falling curve alone does not prove randomness, and a sustained curve does not prove useful long-range forecast information in this finite, nonstationary record.

<!-- code: reversal_plot -->

The bars visualize a sign reversal under a known ordering transformation. Their magnitudes refer to standardized observations, so their labels do not inherit the raw source's cubic units. The symmetric appearance is a property of the statistic under reversal, not independent evidence for a physical direction of time. A surrogate experiment or another properly specified test would be needed to interpret statistical departures under a particular null model.

Answer: the case tolerance is {{TOLERANCE}} and stays fixed across the entropy scales. The constant control has scale-one entropy zero, while its short coarse endpoint is unavailable. These outputs distinguish a measured zero from an estimation boundary. The symbolic phrase count survives the positive unit conversion; the reversed standardized statistic changes sign. Together they illustrate why several diagnostics can be useful without treating them as interchangeable estimates of a single hidden quantity called complexity.

The seeded nonlinear slope calculation addresses a different reproducibility issue. Its robust fit uses a local random_state over the library's exposed log-distance data. Repeating that fit should not depend on random draws made by another caller. The pipeline derives a seed from case identity and its supplied seed, and retains the surrogate gate before any chaos verdict. Deterministic numerical output is a necessary implementation property, not evidence that the observed process itself is deterministic.

<!-- code: seeded -->

### Limitations

The structural-break case contains changing levels and a finite observation budget. Global entropy and asymmetry summaries can combine several regimes rather than identify one stable mechanism. Binary symbolization hides amplitude distinctions and can be sensitive to ties. Matching counts depend on order, tolerance and length. The M4 study therefore treats these values as prefix features with a declared protocol, tests their association with subsequent error, and keeps negative findings rather than interpreting every irregular curve as predictive structure.

### Sensitivity to the matching tolerance

For scale $s$ the algorithm forms disjoint means, discarding any incomplete last group.

$$
x^{(s)}_j=\frac{1}{s}\sum_{k=0}^{s-1}x_{js+k},
\qquad 0\le j<\lfloor n/s\rfloor .
$$

Let $B_m$ count unordered distinct pairs of length-$m$ templates whose maximum coordinatewise difference is at most $r$. Let $A_{m+1}$ count the same type of matches after extension by one observation. The implementation restricts both counts to start positions admitting the extension.

$$
\operatorname{SampEn}(m,r)=-\log\!\left(\frac{A_{m+1}}{B_m}\right),
\qquad A_{m+1},B_m>0.
$$

The ratio is the fraction of matched templates that remain matched at the next observation. A positive threshold can admit equal values and nearby values. Increasing it cannot reduce either matching count for a fixed sequence and scale. The ratio can nevertheless rise or fall because the two counts need not grow proportionally. A larger threshold therefore does not necessarily move entropy in one direction.

<!-- code: tolerance_plot -->

The left panel shows how the reported entropy changes across the three declared thresholds. The right panel reveals how much evidence supports each estimate by counting extended matches. Compare the panels at the same coarse scale. A threshold with few extended matches makes the ratio sensitive to individual pairs and can yield an unavailable estimate when the count reaches zero. At higher coarse scales the available sequence is shorter. This reduces the number of possible pairs even though averaging can make values more similar. A plot of entropy alone would hide those countervailing changes.

This sweep varies only a fraction of the original standard deviation. Each line still uses the same absolute tolerance throughout its four scales. If you instead recalibrate the threshold on each coarse sequence, label that as a different estimator and document its purpose. Examining these settings after observing a case can diagnose fragility. It cannot justify selecting whichever curve most resembles an anticipated mechanism.

### Extend the experiment with your own data

Choose a regularly sampled segment whose time span, frequency and measurement units are known. State whether missing readings break the sequence or receive an imputation, and record the locations and method before calculating lagged statistics. Define coarse scales in physical durations and ensure every displayed duration retains enough blocks. Do not count adjacent overlapping segments as independent data simply because they have different start times. Use a separate reserved period for comparison if the diagnostic will influence a decision.

Include two controls. A constant segment exercises the boundary between zero and unavailable estimates. A positive unit conversion tests whether the tolerance and values scale together. If your question involves temporal ordering, reverse the original segment and compare the sign of the standardized lag moment while keeping every other setting fixed. Quantization and ties can change binary phrase counts even when two sensor calibrations appear nearly identical. Preserve the original values and record the threshold so this effect can be checked later.

Compare the pair counts before comparing published entropy values from two studies. Differences in template order, the norm, or whether a template can match itself change the denominator. Report those settings alongside the tolerance ratio and sample count at each scale.

## Summary

Entropy, phrase counts and lagged moments discard different information. Their units, unavailable values and reproducibility conditions are part of the result rather than optional annotations.

### Reproduce

Execute each method call and both figures in order. Confirm the reported tolerance, the constant control's zero and missing endpoint, the phrase-count comparison and the repeated robust estimates. The repository's independent pair-count and RNG-state tests cover numerical properties beyond these worked outputs; this lesson provides an interpretable example rather than replacing those tests with a graph.

## References

Costa, Goldberger and Peng, DOI 10.1103/PhysRevLett.89.068102. Lempel and Ziv, DOI 10.1109/TIT.1976.1055501. The tsfresh feature definition specifies the lagged third-order reversal statistic, and nolds documents the correlation-dimension and Lyapunov fitting data used by the seeded adapter.

[Nolds fitting documentation](https://cschoel.github.io/nolds/nolds.html).

[Richman and Moorman on sample entropy](https://doi.org/10.1152/ajpheart.2000.278.6.H2039).
