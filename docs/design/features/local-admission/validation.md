# Local admission validation

| requirement | adversarial check | gate |
|---|---|---|
| LA-1 | Reject undeclared, in-checkout, redirected and reserved-name environment destinations before any write. | `tests/test_bootstrap_admission.py::test_adversarial_initializer_enforces_external_location_before_writes` |
| LA-2 | Forward the same flags and native failure code through each real PowerShell and Bash entrypoint. | `tests/test_local_bootstrap.py::test_adversarial_shell_entrypoints_propagate_failure` |
| LA-3 | Mutate the payload after the custom validator returns; require refusal. Prove receipt binding and rollback through the generic path independently. | `tests/test_product_bootstrap_admission.py::test_adversarial_custom_validator_cannot_mutate_payload_after_checking` |
| LA-4 | Remove, alter, add or redirect a study document; require admission failure. Exercise the actual full external candidate without changing canonical inputs. | `tests/test_combination_release_admission.py::test_adversarial_missing_or_changed_release_payload_is_refused` |
| LA-5 | Compare every frozen stage input and canonical payload before/after real generation. Corrupt the published PDF/source and require independent binding checks to refuse it. | `tests/test_publication_bindings.py::test_adversarial_publication_rejects_changed_or_noncanonical_source` |

The bootstrap fixtures deliberately distinguish generic template readiness from
the custom immutable-study provider. Template-only controls retain explicit
skips on this product. The real full-corpus generation/admission test replaces
those engine-specific integrations; it does not replace any mutation refusal.
