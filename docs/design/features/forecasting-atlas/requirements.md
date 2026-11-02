# Forecasting atlas alignment

Status: live

| ID | statement | gate |
|---|---|---|
| FC-001 | The Python and browser HoltWinters forecasts SHALL preserve seasonal phase when the supplied history ends partway through a season. | `tests/test_forecasters.py::test_adversarial_holt_winters_preserves_an_incomplete_seasons_phase`, `frontend/src/test/parity.test.ts` |
| FC-002 | The nonseasonal Theta point equation SHALL match the two-line construction for its specified finite-grid SES fit. | `tests/test_forecasters.py::test_adversarial_theta_matches_the_two_theta_lines_with_finite_history` |
| FC-003 | ContextMemory SHALL fit its weights only from historical origins whose complete targets are observed before the query forecast. | `tests/test_reevaluation.py::test_adversarial_context_memory_uses_only_completed_training_targets` |
| FC-004 | The common-holdout comparison SHALL retain the actual final block and bind stored scores to source traces and computation code. | `frontend/src/test/reevaluation.test.ts` |
| FC-005 | The executive view SHALL carry valid bilingual sourced content and explicitly identify estimated cause weights. | `frontend/src/test/executive.test.ts` |
| FC-006 | Replay histories with display decimation SHALL be rejected as consecutive fitting observations. | `tests/test_reevaluation.py::test_adversarial_display_decimation_cannot_become_a_fitting_series` |
| FC-007 | Fresh experiment admission SHALL reject a trial, partial inventory, archived path, altered metric or target, stale binding, absent checkpoint identity or invalid duration. | `tests/test_fresh_reevaluation.py::test_adversarial_fresh_admission_refutes_corrupted_candidate` |
| FC-008 | The native TiRex adapter SHALL reject unsupported probability levels instead of silently mapping them to deciles. | `tests/test_fresh_reevaluation.py::test_adversarial_native_tirex_cannot_map_arbitrary_levels_to_deciles` |
