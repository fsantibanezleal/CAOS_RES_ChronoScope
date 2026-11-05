# Shared atlas source

| ID | Requirement | Verification |
|---|---|---|
| AS-1 | The URL SHALL select the baked case or deterministic synthetic configuration across atlas views. Unrelated view navigation SHALL retain the input history identity. | `frontend/src/test/atlas-source.test.tsx` |
| AS-2 | A selected-case change SHALL hide superseded artifacts immediately; late requests and wrong-subject artifacts SHALL NOT acquire the new case identity. | `frontend/src/test/atlas-source.test.tsx` |
| AS-3 | Unknown cases and invalid generator configurations SHALL produce explicit errors without substitute forecasts. Optional combination failure SHALL remain separate from the admitted core comparison. | `frontend/src/test/atlas-source.test.tsx` |
| AS-4 | A combination origin SHALL match the complete little-endian float64 prefix digest, horizon, seasonal lag, origin and reserved targets before its weights are joined to the active comparison. | `frontend/src/test/atlas-source.test.tsx` |
