# Forecast observable boundaries

| ID | Requirement | Verification |
|---|---|---|
| OU-1 | Export SHALL refuse non-finite, empty, mismatched or unordered paths and point paths wholly outside the observed range widened by one full range on either side, before writing public or redacted outputs. | `tests/test_forecast_units.py` |
| OU-2 | A flat forecast inside the observable SHALL remain admissible and be recorded as a manifest advisory without modifying the forecast or the caller's flags. | `tests/test_forecast_units.py::test_adversarial_flat_forecast_is_exported_and_recorded_without_altering_callers_flags` |
| OU-3 | Artifact validation SHALL reapply the observable check to every canonical trace and both common-holdout reevaluations, including artifacts created before the gate. | `tests/test_forecast_units.py::test_adversarial_artifact_sweep_refuses_a_tampered_existing_forecast` |
| OU-4 | A runtime boundary change SHALL preserve original experiment source bytes under their existing hashes; a source archive SHALL refuse changed members, inventories, artifact bytes and redirected paths. | `tests/test_fresh_reevaluation.py::test_adversarial_frozen_sources_refuse_tampering` |
