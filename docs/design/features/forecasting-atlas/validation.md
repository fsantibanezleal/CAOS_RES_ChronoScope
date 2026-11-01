# Forecasting atlas adversarial validation

| requirement | adversarial check | gate |
|---|---|---|
| FC-001 | A history stops at phase three of a four-period pattern; the next path must continue at that phase rather than restarting the first seasonal index. | `tests/test_forecasters.py::test_adversarial_holt_winters_preserves_an_incomplete_seasons_phase` |
| FC-002 | A short trending history exposes the omitted finite-history correction; the forecast is compared to the independently constructed two Theta lines. | `tests/test_forecasters.py::test_adversarial_theta_matches_the_two_theta_lines_with_finite_history` |
| FC-003 | A short history and long forecast horizon force the training-origin boundary; every admitted target must end within the observed prefix. | `tests/test_reevaluation.py::test_adversarial_context_memory_uses_only_completed_training_targets` |
| FC-004 | Changed source bytes or a changed historical trace invalidate the exact hashes before the comparison is admitted. | `frontend/src/test/reevaluation.test.ts::adversarial: detects changed traces or source before admitting stored scores` |
| FC-005 | Cause weights are planted above the whole; the real shell validator must reject the brief. | `frontend/src/test/executive.test.ts::adversarial: rejects cause weights that exceed the whole` |
