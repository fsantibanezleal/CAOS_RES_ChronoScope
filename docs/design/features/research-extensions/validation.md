# Research extension validation

| requirement | adversarial check | gate |
|---|---|---|
| RX-1 | Exhaustive normalized distances, original-index motif/discord plants and a frequency transition without a supplied break location. | `tests/test_sequence_diagnostics.py::test_adversarial_profile_matches_exhaustive_z_normalized_distance_oracle` |
| RX-2 | Change annotation families; reject absent source diagnostics and walk real cases at both sizes/languages/themes. | `frontend/src/test/research-extensions.test.tsx::adversarial: uses the full original axis, exposes candidates and changes the annotation filter` |
| RX-3 | Independent Chebyshev pair counts, constant/short controls, known binary phrase count and exact reversal sign. | `tests/test_sequence_diagnostics.py::test_adversarial_multiscale_entropy_uses_original_tolerance_and_independent_pair_counts` |
| RX-4 | Advance unrelated global randomness and compare independent processes; repeat every complete analyzer twice. | `tests/test_seeded_nonlinear.py::test_adversarial_independent_processes_reproduce_identical_robust_estimates` |
| RX-5 | Plant future changes, split changes and corrupted metrics, probabilities, confirmation flags, imputation and source identity. | `tests/test_forecastability.py::test_adversarial_future_changes_do_not_change_origin_features` |
| RX-6 | Reject partial corpus inventories and traverse actual corpus controls. | `frontend/src/test/research-extensions.test.tsx::adversarial: rejects trials, missing inventories and the unrelated fifteen-case experiment` |
| RX-7 | Reject stale notebook outputs, manuscript registrations and deployed source identities. | `tests/test_fresh_reevaluation.py::test_adversarial_fresh_admission_refutes_corrupted_candidate` |

The release receipts under `docs/validation/0.24.000/` distinguish local computation, manuscript
publication, remote CI and canonical deployment. Partial corpus caches and incomplete runtime trials
are not admitted as a complete study. All negative results remain visible.
