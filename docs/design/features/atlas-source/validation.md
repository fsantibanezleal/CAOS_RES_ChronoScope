# Shared atlas source adversaries

| requirement | adversarial check | gate |
|---|---|---|
| AS-1 | Navigate between story steps and require the same history object and seed. | `frontend/src/test/atlas-source.test.tsx::adversarial: story navigation retains the exact history object and generator URL controls` |
| AS-2 | Delay an old case, switch subjects, complete it late and inject a wrong-subject trace. | `frontend/src/test/atlas-source.test.tsx::adversarial: a late old case cannot overwrite the current subject` |
| AS-3 | Request an unknown case and malformed synthetic links; refuse forecasts while preserving optional-artifact failure separately. | `frontend/src/test/atlas-source.test.tsx::adversarial: malformed generator links never produce substitute forecasts` |
| AS-4 | Supply matching lengths and targets with a missing or wrong full-prefix digest; refuse the join. | `frontend/src/test/atlas-source.test.tsx::adversarial: combination weights require the entire prefix digest, not just matching lengths and targets` |
