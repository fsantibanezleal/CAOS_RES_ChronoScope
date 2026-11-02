# Sequence patterns, complexity and corpus forecastability

This extension answers four different questions. A Matrix Profile asks which local shapes repeat or
lack close matches. FLUSS proposes a partition of those shapes into a requested number of regimes.
Complexity diagnostics summarize ordering across scales and under symbolic encodings. A separate
M4 study tests whether prefix diagnostics associate with subsequent error and whether a learned method
selector improves on a discovery-selected constant. None of these questions licenses a causal story
about the data generator or a claim of universal forecast superiority.

## Exact shape comparison and original indices

For a length-m window starting at i, let z_i be its population-standardized observations. The profile
P_i is the minimum Euclidean distance between z_i and another eligible window z_j. The self-join
excludes |i-j| <= ceil(m/4), following the pinned STUMPY convention. This prevents a window from
declaring itself, or a nearly identical overlapping copy, its own nearest neighbor. Constant windows
use STUMPY's explicit constant-subsequence convention; an entirely constant sequence is reported as
unavailable because it contains no discriminating shape profile.

The motif pair is the smallest profile entry whose reported nearest-neighbor window does not overlap
the query window. It is one admitted pair, not an exhaustive motif set. Discords are the three largest
finite profile entries with non-overlapping query windows. Their distances are shape differences,
not calibrated anomaly scores. In particular, a large amplitude change alone need not be discordant:
per-window normalization deliberately removes a window's mean and amplitude.

The profile and corrected arc curve are computed with STUMPY 1.14.1. FLUSS consumes nearest-neighbor
indices and asks for three candidate regimes on the case diagnostics. Its number of regimes is a
declared parameter, not a measured count of true changes. The corrected arc curve discounts expected
arc traffic; its minima nominate candidate boundaries under the exclusion rule. A frequency-transition
plant checks localization without supplying its true transition to the algorithm. No ground-truth
generator boundaries enter the producer.

The exported sequence retains every original observation and its original integer index. Profile
positions identify window starts, not resampled display positions. The app plots these observations,
colors selected motif/discord intervals and marks FLUSS candidates on this axis. Its filter lets a
reader isolate a candidate family; tables retain window starts, inclusive ends and distances. These
are retrospective descriptions of the complete sequence. A mark near an earlier forecast origin does
not establish that an online system could have detected it then.

Primary references: [STUMPY Matrix Profile](https://stumpy.readthedocs.io/en/latest/Tutorial_The_Matrix_Profile.html),
[STUMPY FLUSS](https://stumpy.readthedocs.io/en/latest/Tutorial_Semantic_Segmentation.html),
[Yeh et al.](https://doi.org/10.1109/ICDM.2016.0179),
[Gharghabi et al.](https://doi.org/10.1109/ICDM.2017.21).

## Complexity across scale and ordering

Costa multiscale entropy first replaces each non-overlapping block of tau observations by its mean.
The sample-entropy calculation uses embedding order two and a Chebyshev tolerance of 0.15 times the
original sequence's population standard deviation. That tolerance stays fixed at every scale. Scaling
it separately to each coarse sequence would define a different statistic and can erase the contrast
the multiscale construction is intended to examine.

At a scale with N observations, both two- and three-component templates use the same N-2 start
positions. B counts distinct unordered matching two-component pairs; A counts their matching
three-component extensions. Self matches are excluded, equality at the tolerance is included, and
SampEn is -log(A/B). The producer exports A, B, tolerance and available observation count. Fewer than
twenty coarse observations, or no matching extensions, yield a null estimate and a stated reason.
Null does not mean zero complexity. A constant sequence legitimately gives zero entropy because all
eligible templates and extensions match.

Lempel-Ziv complexity uses the binary sequence 1[x > median(x)], with ties assigned to zero. It reports
both the phrase count and c(n) log2(n)/n. This asymptotic normalization is not clipped to one: short
samples can exceed it. The median threshold is part of the method; changing to ordinal patterns or
another alphabet would produce another experiment. The statistic is an ordering description, not a
physical entropy rate established by a short record.

Time-reversal asymmetry is the mean of x[t+l] times (x[t+2l]^2 - x[t]^2), at lags one, two and seven
when enough observations exist. Raw values have cubed source units. A second result standardizes the
input before computing the same expression, allowing a more meaningful cross-series comparison.
Reversing the observations changes its sign. Finite nonzero values alone do not reject a reversible
process; no significance threshold or irreversibility verdict is invented.

Sources: [Costa's implementation and explanation](https://physionet.org/content/mse/1.0/),
[Costa et al.](https://doi.org/10.1103/PhysRevLett.89.068102),
[Lempel and Ziv](https://doi.org/10.1109/TIT.1976.1055501), and
[tsfresh's statistic definition](https://tsfresh.readthedocs.io/en/stable/text/list_of_features.html).

## Reproducible nonlinear slopes

The former nolds defaults used RANSAC without an explicit random_state. Unrelated random draws could
therefore move correlation-dimension and Lyapunov estimates between otherwise identical bakes. The
new adapter obtains the library's log-distance data with deterministic least-squares debug output,
then fits the same polynomial-feature robust linear model using an explicit local seed. It falls
back to least squares if consensus cannot be fitted. It never seeds or restores the process-global
random generator because doing so can interfere with an unrelated caller or thread.

The case seed is SHA-256 of case identity and the supplied pipeline seed, truncated to 32 bits.
Surrogates and the 0-1 statistic receive derived local seeds. The existing surrogate gate remains
necessary for a chaos verdict; the extension does not turn a positive Lyapunov estimate into proof.
DFA and the fallback R/S slope now explicitly request least squares instead of an unseeded robust
default. This declared fit change can move old diagnostics even when the input series is unchanged.
Two complete analyzer calls per case must serialize identically before promotion. Independent-process
tests additionally check estimator repeatability and preservation of the caller's RNG state.

Reference: [nolds algorithm and fitting documentation](https://cschoel.github.io/nolds/nolds.html).

## Fixed M4 study and statistical boundary

The complete [Monash M4 Daily corpus](https://zenodo.org/records/4656548) contains 4,227 daily series,
licensed CC BY 4.0. The source ZIP and extracted TSF receive separate SHA-256 identities. Every source
series is processed or assigned an explicit exclusion; no favorable subset is selected after scoring.
Exact whole-sequence duplicates keep their lexicographically first identity for inference. The full
sequence hash is used only for identity grouping and deterministic partition allocation, never as a
predictor. Nonfinite histories, insufficient prefixes and zero scaled-error denominators are listed.

Each admitted series contributes three adjacent, non-overlapping 14-step future blocks. Fitting uses
at most the preceding 1,024 contiguous observations at each origin. Features come only from the
earliest fitting prefix. Daily forecasting seasonality is one, consistent with M4; weekly phase
strength is a separately named diagnostic, not an altered forecast period. The roster is Naive,
SeasonalNaive, SES, Holt, HoltWinters, Theta, AutoETS and AutoTheta. Some choices coincide when m=1;
they remain explicit identities rather than being silently assigned a seasonal advantage.

Within each series, MASE is averaged over its three origins before testing. The target is log1p of
the smallest mean MASE among the declared methods. It is an optimistic within-roster oracle, not
inherent predictability. Forty prefix diagnostics include catch24, scale/order summaries,
multiscale entropy, binary complexity, reversal asymmetry and profile distances. A feature may relate
to the construction of the MASE denominator rather than to lower operational error.

Exact-sequence identities allocate approximately 70 percent of series to discovery and the rest to
confirmation. Kendall tests handle monotonic relationships and ties. BY q=0.05 corrects the complete
feature family separately in each partition; a confirmation requires rejection in both and matching
effect direction. All p values, q values, sample counts, effects and negative findings remain public.
The procedure follows the dependent-test principle documented by
[tsfresh](https://tsfresh.readthedocs.io/en/v0.21.0/text/feature_filtering.html).

A fixed 200-tree random forest, depth at most eight and minimum leaf size ten, predicts the best
method identity from discovery features. Missing-value medians are fitted on discovery only. It is
evaluated once on confirmation series against the method with smallest discovery mean MASE and
against the future-informed per-series oracle. No confirmation outcomes choose hyperparameters,
feature thresholds, imputation values or the constant comparator. A worse selector remains a result.
Related industries or hidden source groups can violate observation-independence assumptions even
after exact deduplication; this limits inferential claims. No deep or pretrained model participates
in this separate corpus experiment. The original 22-variant case comparison remains independently
accessible and is not relabeled as a thousands-series foundation-model benchmark.

## Reproduce and inspect

`scripts/run_forecastability_study.py` consumes an external TSF, its source receipt and an external
cache/output directory. Cache identities bind protocol, source bytes, implementation and package
versions. The producer independently scores every retained forecast path before compact export.
`scripts/check_research_extensions.py --statistics` checks inventory, source bindings, split rules,
summary scores, discovery-only imputation, BY corrections and independently recomputed Kendall tests.
Schemas and generated browser types define the same boundary. Raw observations, forecast-path audits
and selector checkpoints remain external; the compact study retains features, mean scores, origins,
partition membership, selection results and public source identities.
