# Canonical deployment evidence

| ID | Requirement | Verification |
|---|---|---|
| DP-1 | Canonical verification SHALL retain default TLS validation, exact build identity and every artifact hash. A transient HTTP server response MAY be retried at most twice with recorded backoff. Persistent failures, absent files, access refusal and server-requested waits beyond the retry budget SHALL remain failures. | `scripts/check_deployment.py`, `tests/test_deployment_transport.py` |
