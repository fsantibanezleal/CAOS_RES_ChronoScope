# Live learned-model adversaries

| requirement | adversarial check | gate |
|---|---|---|
| LM-1 | Reverse a history while retaining its length and sum; require another inference and the corresponding changed forecast. | `frontend/src/test/live-model.test.tsx::adversarial: equal length and equal sum cannot retain an old forecast` |
| LM-2 | Complete a superseded inference after the current one; require the newer result to remain selected. | `frontend/src/test/live-model.test.tsx::adversarial: a late old inference cannot overwrite the current input` |
| LM-3 | Supply invalid observations, a constant prefix, an unsupported horizon or a malformed output and require explicit unavailability or error. | `frontend/src/test/live-model.test.tsx::adversarial: unsupported horizons do not run the model` |
