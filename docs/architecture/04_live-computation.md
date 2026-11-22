# Live browser computation

The browser recomputes five classical rules in `frontend/src/lib/liveEngine.ts` and the fixed normalized linear graph in `onnxRunner.ts`. These are separate from heavier package models whose retained paths the application displays. The live panel does not run Chronos, TimesFM, TiRex or Timestral.

The ONNX map consumes a standardized 48-observation lookback and returns twelve steps. Location and scale come only from that observed lookback; predictions are transformed back to response units. The browser verifies the graph SHA-256 before executing it through self-hosted ONNX Runtime WASM. Constant lookbacks, unsupported horizons, nonfinite values and malformed outputs are refused. Changing history invalidates earlier asynchronous results.

Prefix-stratified residual bands use the admitted calibration record bound to the graph digest. Their confirmation experiment uses generated series. Its marginal coverage and interval-score results do not establish calibration for arbitrary authentic series. A live path changes with browser inputs; a retained benchmark result does not become a new trial when inspected.

`node frontend/scripts/check_runtime_units.mjs --out <external-json>` executes actual TypeScript and WASM paths against complete admitted histories and positive affine changes of units. Its receipt records input, source, graph and dependency hashes, numerical errors, refusals and runtime. This is distinct from the shared shell's layout, accessibility and motion gate.

There is no Python source inlining or active Pyodide worker. Offline Python methods and actual seven-model notebook references retain their own [explicit environments](../guides/notebook-references.md).
