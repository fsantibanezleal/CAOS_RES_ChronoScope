# Forecastability and sequence diagnostics

Approved scope: the four remaining research extensions, 2 November 2026. The existing executive
brief, shared shell and forecasting experiment remain the problem context and comparison baseline.

## Requirements and validation

| ID | Requirement | Validation |
|---|---|---|
| RX-1 | For an admitted finite sequence, the producer SHALL compute its exact z-normalized self-join Matrix Profile with an explicit window and exclusion zone, identify non-overlapping motif/discord windows, and compute FLUSS candidate regime boundaries without supplying known generator breaks. | `tests/test_sequence_diagnostics.py`: exhaustive distance oracle, planted repeated motifs, discord and regime tests; `tests/test_research_extensions.py`: every committed case |
| RX-2 | The app SHALL show the profile, motif/discord intervals and candidate boundaries on the original observation axis, with accessible labels, selection controls and explicit retrospective/noncausal interpretation. Display decimation SHALL not change diagnostic input or index locations. | `frontend/src/test/research-extensions.test.tsx`, `frontend/scripts/check-research-ui.mjs` |
| RX-3 | For each admitted sequence, the producer SHALL compute Costa multiscale sample entropy using coarse-grained means and a tolerance fixed to the original series standard deviation; binary Lempel-Ziv complexity; and lagged time-reversal asymmetry. Undefined or insufficient-data cases SHALL be explicit. | `tests/test_sequence_diagnostics.py` |
| RX-4 | Nonlinear correlation-dimension and Lyapunov fits SHALL use an explicit seed, repeat identically across independent processes, and leave the caller's random generator unchanged. The robust estimator and surrogate gates SHALL be retained. | `tests/test_seeded_nonlinear.py`, `scripts/bake_research_diagnostics.py` |
| RX-5 | A corpus study SHALL evaluate thousands of licensed M4 series under a fixed, recorded protocol, compute features exclusively from pre-origin observations, apply dependent-test Benjamini-Yekutieli correction, and confirm discoveries on disjoint series. | `tests/test_forecastability.py`, `scripts/check_research_extensions.py` |
| RX-6 | The corpus app SHALL expose sample counts, exclusions, model roster, origins, corrected significance and held-out selection performance with all negative results. The original 15-case experiment SHALL remain a separate study. | `frontend/src/test/research-extensions.test.tsx`, `frontend/scripts/check-research-ui.mjs` |
| RX-7 | Code, schemas, generated types, notebooks, methodological documentation and the versioned technical report SHALL describe the executed protocol and its limits; the completed release SHALL pass CI and canonical production verification. | `scripts/check_sdd.py`, `scripts/run_notebooks.py`, `scripts/check_manuscripts.py`, `scripts/check_deployment.py` |

## Scientific protocol fixed before execution

Use the complete Monash M4 Daily corpus (4,227 series, CC BY 4.0, record 4656548), retaining its
source checksum and series identities. Three non-overlapping 14-step final-origin blocks per series;
at most 1,024 original contiguous observations at each fit; no display resampling. Features use
only the earliest origin's fitting prefix. Daily forecasting seasonality is one, matching M4;
weekly diagnostic strength is a separately named feature. Exclude only nonfinite/insufficient
histories or unavailable scaled-error denominators, with a complete exclusion inventory.

Compare Naive, the five implemented lightweight experts, AutoETS and AutoTheta. Model settings
are fixed before scoring. This bounded roster is not a foundation-model comparison. The earlier
22-variant experiment remains available separately. Aggregate origins within each series before
statistical testing. Use series-level deterministic discovery/confirmation splits; exact duplicate
sequences share a partition; retain the lexicographically first exact duplicate for inference and
list the rest as exclusions. Test continuous features against log1p of the best mean MASE within
this roster with Kendall's tau. Apply BY at q=0.05 jointly across the preregistered features in each
partition. Confirmation requires rejection in both partitions and matching effect direction.

Train a deterministic feature-based method selector on discovery series only, evaluate once on
confirmation series, and compare it with the discovery-selected constant method and the per-series
oracle. Selection metrics are descriptive held-out results, not a guarantee of future performance.
Dependent or related M4 sources can limit inferential interpretations even after exact deduplication.
No feature, model, threshold or split is changed after observing the study result.

## Boundaries and ownership

`analysis/sequence.py` owns Matrix Profile and complexity calculations; `analysis/nonlinear.py`
owns seeded robust fits; `analysis/atlas.py` owns prefix features, multiple-testing and selection;
the staged analyzer owns per-case export. `scripts/run_forecastability_study.py` owns external
source acquisition, resumable execution and final export. A normative study JSON schema defines
the browser boundary. Raw corpus files and computation caches stay outside Git. The browser
consumes compact diagnostic and study artifacts; it does not fabricate absent outputs.

The analysis contract gains additive optional diagnostic fields. A separate study contract records
the corpus protocol, source identity, split membership, features, scores, corrections and summaries.
Producer and consumer validation reject stale or incomplete artifacts. Existing forecast, source
history and quantile contracts remain unchanged.

## Review

Reviewed before implementation against the four backlog definitions and the primary references:
STUMPY's exact Matrix Profile/FLUSS documentation, Costa's MSE algorithm, nolds' robust-fit source,
the Monash M4 Daily record, and tsfresh's dependent-hypothesis filtering procedure. Particular risks
are index mapping, trivial matches, changing entropy tolerance by scale, future leakage, duplicate
series, multiple comparisons, random-state leakage and overstating out-of-sample evidence.
