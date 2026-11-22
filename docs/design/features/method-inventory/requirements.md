# Numerical method inventory

The software exposes more numerical procedures than the seven grouped rows of
the original method ladder describe. The inventory names each implemented
procedure and execution identity so documentation can account for the complete
surface. An inventory entry establishes implementation location, not teaching
depth, novelty or scientific acceptance.

| ID | Requirement | Verification |
|---|---|---|
| MI-1 | The inventory SHALL retain every named forecast in the fresh comparison and external combination study, with distinct direct and package implementations. | `tests/test_method_inventory.py` |
| MI-2 | Every inventory implementation and validation path SHALL resolve to actual source and tests; each numerical component in a combined diagnostic API SHALL retain its own identity. | `tests/test_method_inventory.py`, `scripts/method_inventory.py` |
| MI-3 | The reconstructed historical smoothing-plus-drift predictor SHALL remain distinct from the current finite-history Theta implementation and from native stateful execution. | `tests/test_method_inventory.py` |
