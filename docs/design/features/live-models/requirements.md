# Live learned-model correctness

| ID | Requirement | Verification |
|---|---|---|
| LM-1 | When the observed history changes, the learned forecast SHALL use that complete new history even when its length and sum are unchanged. | `frontend/src/test/live-model.test.tsx` |
| LM-2 | Completion of an earlier asynchronous inference SHALL NOT replace the result for a newer history. A previous forecast SHALL NOT be presented as belonging to a different current input. | `frontend/src/test/live-model.test.tsx` |
| LM-3 | The learned model SHALL refuse unsupported horizons, nonfinite data, constant lookbacks and malformed inference outputs instead of fabricating a forecast or an uncertainty scale. | `frontend/src/test/live-model.test.tsx` |
| LM-4 | Live metrics SHALL refuse zero or nonfinite seasonal scales and incomplete, nonfinite or inverted prediction paths instead of inventing a denominator or dropping observations. Valid scaled loss and coverage SHALL be invariant under positive affine unit changes. | `frontend/src/test/live-metrics.test.ts` |
