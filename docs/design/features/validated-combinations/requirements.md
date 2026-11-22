# Forecast combination with temporal validation

The fixed ContextMemory configuration has an unfavorable mean-error difference on the
fifteen selected cases. The user requests continued implementation and improvement.
That outcome is retained; new configurations receive their own identities and evaluation.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| VC-1 | A combination SHALL fit and validate only on complete target blocks already available inside its supplied prefix. At an inner query origin v, a training origin o is eligible only if o+H <= v. | `tests/test_validated_combination.py` |
| VC-2 | ContextMemoryCV SHALL select context shrinkage and temperature from a fixed finite family using temporal validation. ValidationMix SHALL additionally consider regularized convex stacking and the original equal/recency combinations. | `tests/test_validated_combination.py` |
| VC-3 | Every outer forecast SHALL retain its method, expert paths, weights, selected configuration, validation origins and scores. No outer target may select a candidate or change its settings. | `scripts/check_combination_study.py` |
| VC-4 | The evaluation SHALL account for every M4 Weekly and M3 Monthly source identity, explicitly retaining exclusions, duplicates and all model failures. | `scripts/check_combination_study.py`, `tests/test_combination_contract.py` |
| VC-5 | The app, notebooks, report and method manuscript SHALL expose the new methods and measured results without rewriting earlier negative results or assigning novelty by implementation alone. | `scripts/run_notebooks.py`, `scripts/check_manuscripts.py`, `frontend/scripts/gate.mjs` |
| VC-6 | Exploratory uncertainty summaries SHALL resample paired series after averaging their origins, keep collections separate, retain every admitted identity, use a local seeded generator and identify the analysis as post hoc with unadjusted intervals. No model may be refitted or selected by this analysis. | `tests/test_combination_uncertainty.py`, `scripts/summarize_combination_uncertainty.py` |

VC-6 is an exploratory analysis added on 5 November after the original outcomes.
It is not part of the pre-outcome design below and does not retroactively alter
its hypotheses, candidates, exclusions or acceptance criteria.

## Fixed protocol before new external outcomes

Sources are Monash M4 Weekly, record 4656522 (359 identities, horizon 13, period 52),
and M3 Monthly, record 4656298 (1,428 identities, horizon 18, period 12). Source ZIP,
extracted TSF and exact sequence hashes identify the data. Every identity is retained
or excluded with a reason. Whole-sequence exact duplicates share one representative.

Each series supplies up to three nonoverlapping final origins, subject to an available
prefix of at least max(2m, 2H+8, 24). All methods receive the same last 512 contiguous
prefix observations. Scoring divides error by the seasonal-difference scale of that
same supplied prefix, never a future block; unavailable scales are explicit exclusions.
Origins are averaged within series, then series are equally weighted within each dataset.
The two datasets are reported separately and are not pooled to conceal an unfavorable result.

The fixed experts are SeasonalNaive, SES, Holt, HoltWinters and finite-history Theta.
Matching controls are ContextMemory, RecencyMean and EqualMean; additional comparators
are the individual experts, AutoETS and AutoTheta from the installed StatsForecast version.
The primary comparison is ValidationMix versus RecencyMean mean MASE on each dataset.
Other comparisons, coverage, interval scores and per-series differences are retained.

The existing maximum twelve evenly spaced completed origins are the memory. Temporal
validation uses each origin having at least three fully completed earlier memory blocks.
Context candidates use recency half-life six, the existing distance kernel, shrinkages
0, 0.5 and 1, and temperatures 0.15, 0.5 and 1. Their final uniform floor is 0.05.
The original RecencyMean and EqualMean are explicit candidates. Stacking candidates
minimize normalized squared forecast error plus lambda times squared distance from
uniform weights, subject to nonnegative weights summing to one; lambda is 0.01, 0.1,
1 or 10. Their final uniform floor is also 0.05. Validation ranks candidates by mean
scaled absolute error on causally held-out historical blocks, with stable configured
tie-breaking and no outer-target access. Without eligible validation, use RecencyMean.

ContextMemoryCV selects only among context candidates and the original controls.
ValidationMix selects from that family plus convex stacking. Selected settings are
refit on all completed memory blocks before the final query. A favorable historical
validation score is not a guarantee of a favorable outer result. Both negative and
positive external outcomes remain publishable and visible.
