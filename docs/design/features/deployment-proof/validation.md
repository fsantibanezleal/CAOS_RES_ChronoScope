# Canonical transport adversaries

| requirement | adversarial check | gate |
|---|---|---|
| DP-1 | Return persistent 503, 404, 403 or a rate-limit wait beyond budget and require refusal. A separate control records one transient 503 before returning the exact subsequent bytes without a TLS override. | `tests/test_deployment_transport.py::test_adversarial_persistent_or_nonretryable_failure_is_never_admitted` |
