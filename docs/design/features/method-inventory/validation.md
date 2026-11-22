# Method inventory adversaries

| requirement | adversarial check | gate |
|---|---|---|
| MI-1 | Remove a measured method and require refusal; retain separate direct and package model identities. | `tests/test_method_inventory.py::test_adversarial_measured_method_cannot_disappear` |
| MI-2 | Point an entry at an absent callable or remove one bundled diagnostic component and require refusal. | `tests/test_method_inventory.py::test_adversarial_unimplemented_callable_is_refused`, `tests/test_method_inventory.py::test_adversarial_bundled_components_have_independent_identities` |
| MI-3 | Collapse the historical predictor into the current Theta entry and require refusal of the incomplete inventory. | `tests/test_method_inventory.py::test_adversarial_historical_predictor_identity_is_not_collapsed` |
