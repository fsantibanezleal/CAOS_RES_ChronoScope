# Do prefix associations survive a separate series partition?

**Question:** Which diagnostic associations survive a discovery/confirmation split, and does a feature-based method selector reduce error on the confirmation series? We examine the complete M4 Daily study under its fixed protocol. This lesson distinguishes three pieces of evidence: association tests, a learned selection rule and a future-informed oracle. A strong answer to one does not automatically answer the others, and a negative selection result must remain visible even when several feature tests reject their null hypotheses.

## Objectives

Trace prefix-only features through disjoint series partitions, repeat dependent-test correction and retrain the fixed selector. Separate an association result from the held-out error of a usable selection rule.

## Setup

Install the pinned environment below and read the compact executed corpus artifact. It contains per-series features, model scores, origin indices and partition identities, rather than the full downloaded observations. The producer's external forecast-path audit independently rescored every method at every origin before exporting these rows. Here we can repeat the statistical analysis and selector training from the same admitted feature/score table without downloading the raw benchmark or representing cached predictions as fresh model fits.

{{PINS}}

<!-- code: setup -->

## Data

The admitted artifact preserves the source identity and the observations used below.

<!-- code: corpus -->

## Method

The source contains 4,227 daily series. Each admitted sequence contributes three non-overlapping fourteen-step blocks, and each fit uses at most 1,024 preceding contiguous observations. Features are calculated once at the earliest origin, so none of those three future blocks enters their calculation. Daily forecast seasonality is one. A separately named weekly diagnostic does not change that forecast setting. Exact whole-sequence duplicates retain one identity for inference; excluded series remain listed with their reasons.

<!-- code: prefix -->

The displayed prefix call illustrates the same feature boundary on a committed case whose original observations are available locally. Its forty features combine compact statistical summaries with sequence ordering diagnostics. This example is not a replacement M4 row and does not claim to reconstruct the raw corpus from its compact output. In the actual study, each M4 feature vector came from that source series' own earliest fitting prefix, and its identity is bound to the external source file.

The analysis target is log(1 + the best mean MASE among the fixed eight-method roster). Each model's error is averaged across a series' three origins before choosing that within-roster minimum. This is an optimistic target, because future outcomes identify the winner. It describes achievable error among those specific configured methods, rather than inherent predictability. A feature can also associate with how the MASE denominator is constructed, without revealing a useful physical forecasting mechanism.

<!-- code: associations -->

Discovery and confirmation series are disjoint by exact sequence identity. Their allocation is deterministic and independent of the error labels. We test every preregistered feature in each partition, retaining sample counts, signed Kendall effects and probabilities. The unit is a series, not each origin treated as an independent replication. Aggregating origins addresses that immediate pseudoreplication risk; it does not prove that different benchmark series are independent in their underlying industries or sources.

## Comparison

<!-- code: kendall_reference -->

The direct SciPy calculation checks one explicitly selected feature against the reference Kendall implementation. It uses the confirmation rows with available feature values and the same log-transformed target. The coefficient measures a monotonic association, not a fitted causal response. Ties are handled by the library. A small probability must still be interpreted within the complete feature family, rather than reported alone because that feature happened to look interesting.

<!-- code: correction -->

BY correction uses the number of tests and its harmonic factor to account for dependent feature hypotheses. We compare the product's adjusted probabilities with the reference calculation over the entire confirmation family. A confirmation requires corrected rejection in both partitions and the same direction of effect. Selecting only the small probabilities before correcting would define a different and misleading procedure. Neither correction removes unmeasured dependence between related benchmark sources.

<!-- code: reference_join -->

The exact profile reference call uses a prefix that stops before the three final blocks in the worked case. It verifies that the diagnostic adapter can operate inside the temporal boundary rather than needing the complete future sequence. The app's retrospective case profile and this prefix-only calculation therefore serve different purposes. Their window coordinates retain original observation units, but their eligible neighboring windows and resulting distances can differ because their available observations differ.

<!-- code: association_plot -->

The figure shows the first twelve features in the fixed schema order, not a selection made by their smallest probabilities. All forty tests remain in the artifact and in the app's corrected-results table. Compare direction and magnitude across partitions before reading a rejection flag. Similar coefficients across groups are useful conditional evidence, while opposite signs or disappearing effects should remain findings rather than be removed from the presentation.

<!-- code: refit_selector -->

The selector is now fitted again from the compact discovery rows. It uses the fixed forest configuration and discovery-only missing-value medians. Confirmation labels do not choose hyperparameters, feature thresholds or the constant comparator. We compare the reproduced confirmation scores with the exported scores, so the following figure is based on an executed public-data-table training path. Repeating the selection calculation is distinct from refitting the eight forecasting methods on the full external corpus.

## Results

**Answer:** <!-- code: selection_plot -->

The oracle bar uses future scores to choose a different winner for every confirmation series. It is therefore a lower reference within this roster, not a deployable rule. The constant method was chosen from discovery only, and the forest makes its choices from available prefix features. Read both deployable rules against the same confirmation rows and units. A low oracle error can coexist with an unsuccessful learned selector because the features may not reliably identify the individual winners.

Answer: the reproduced selector has confirmation mean MASE {{SELECTED}}, compared with {{CONSTANT}} for the discovery-selected constant. {{CONFIRMED}} features satisfy the declared two-partition confirmation rule. These are different conclusions: feature association does not guarantee an improvement in discrete method selection, and an observed selection difference does not establish population superiority. The source count is 4,227 and the origin count is three, while the statistical sample consists of the admitted distinct series.

### Limitations

The corpus is one benchmark frequency with anonymized source identities. Exact deduplication cannot identify every related industry or common latent driver. The roster excludes deep and pretrained models and cannot rank them by implication. Context truncation, fixed fitting configurations and the use of a scaled-error oracle limit the target's meaning. No result is used to revise this study's feature set or forest settings. The separate twenty-two-variant case experiment remains available with its own package identities and provenance.

## Summary

The confirmation partition evaluates rules and hypotheses fixed elsewhere. Keep the complete corrected family, exclusions and negative selection outcomes beside any favorable coefficient.

### Reproduce

<!-- code: checks -->

Run all cells and compare the reference corrections, reproduced selector scores and partition checks. Full forecasting reproduction additionally requires the licensed TSF and the external evaluator; the repository documents its source checksum, cache identity and independent path scoring. The compact notebook reproduces the inferential and selection layer and states that boundary explicitly.

## References

Monash M4 Daily, DOI 10.5281/zenodo.4656548. The tsfresh feature-filtering documentation explains dependent-test BY correction. Hyndman and Koehler, DOI 10.1016/j.ijforecast.2006.03.001, discuss the scaled-error interpretation. STUMPY documents the exact prefix profile used in the numerical comparison.

[Dependent-test feature filtering](https://tsfresh.readthedocs.io/en/v0.21.0/text/feature_filtering.html); [Matrix Profile reference](https://doi.org/10.1109/ICDM.2016.0179).
