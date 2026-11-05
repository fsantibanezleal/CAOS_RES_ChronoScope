# Temporal combination validation

| requirement | adversarial check | gate |
|---|---|---|
| VC-1 | Plant overlapping historical target blocks and reject them until their entire horizon has arrived. | `tests/test_validated_combination.py::test_adversarial_temporal_validation_excludes_incomplete_target_blocks` |
| VC-2 | Plant one perfect expert among conflicting experts; require the independently known optimum and reject unavailable training values. | `tests/test_validated_combination.py::test_adversarial_convex_stacking_finds_perfect_expert_and_obeys_simplex` |
| VC-3 | Remove a quantile column and require rejection while retaining selected configuration and expert weights. | `tests/test_combination_contract.py::test_adversarial_case_rejects_missing_quantile_columns_and_retains_parameters` |
| VC-4 | Mark an eligible series as short or unscaled; independently reconstruct its history and reject the false exclusion. | `tests/test_combination_admission.py::test_adversarial_eligible_series_cannot_be_excluded_as_short_or_unscaled` |
| VC-5 | Return another series from the artifact endpoint and reject the mismatched identity before displaying its result. | `frontend/src/test/combinations.test.ts::adversarial: rejects a response from a different series` |
| VC-6 | Plant unequal origin counts and duplicate identities; require equal series weighting and refuse duplicate pairs. Independent controls cover a known constant effect, deterministic batching and preservation of caller RNG state. | `tests/test_combination_uncertainty.py::test_adversarial_equal_series_weighting_refuses_duplicate_identities` |

The independent full-study check reconstructs every admitted prefix and all 53,148
external forecasts. Release receipts in `docs/validation/0.25.000/` distinguish that
numerical evidence from notebook execution, manuscript publication and live delivery.
