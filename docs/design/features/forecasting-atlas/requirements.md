# Forecasting atlas alignment

Status: live

| ID | statement | gate |
|---|---|---|
| FC-001 | The Python and browser HoltWinters forecasts SHALL preserve seasonal phase when the supplied history ends partway through a season. | `tests/test_forecasters.py::test_adversarial_holt_winters_preserves_an_incomplete_seasons_phase`, `frontend/src/test/parity.test.ts` |
| FC-002 | The nonseasonal Theta point equation SHALL match the two-line construction for its specified finite-grid SES fit. | `tests/test_forecasters.py::test_adversarial_theta_matches_the_two_theta_lines_with_finite_history` |
| FC-003 | ContextMemory SHALL fit its weights only from historical origins whose complete targets are observed before the query forecast. | `tests/test_reevaluation.py::test_adversarial_context_memory_uses_only_completed_training_targets` |
| FC-004 | The common-holdout comparison SHALL retain the actual final block and bind stored scores to source traces and computation code. | `frontend/src/test/reevaluation.test.ts` |
| FC-005 | The executive view SHALL carry valid bilingual sourced content and explicitly identify estimated cause weights. | `frontend/src/test/executive.test.ts` |
