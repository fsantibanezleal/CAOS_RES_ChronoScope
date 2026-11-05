# Held-out browser linear reference

| ID | Requirement | Verification |
|---|---|---|
| BR-1 | The evaluation SHALL normalize using observed data only; require finite positive scales and preserve predictions and scores under positive affine changes of units. | `tests/test_browser_linear.py` |
| BR-2 | The evaluation SHALL fit only training series and choose a float32 matrix by the fixed validation grid, retaining the unpenalized control and deterministic tie rule. | `tests/test_browser_linear.py` |
| BR-3 | The evaluation SHALL calibrate each lead on independent series using the finite-sample absolute-residual rank; compute interval scores with explicit tail penalties and resample paired series. | `tests/test_browser_linear.py` |
| BR-4 | Prefix-stratified confirmation SHALL use only observed-prefix roughness, preserve unit invariance and fixed point forecasts, refuse undersized calibration groups, and enforce every prospectively specified admission criterion. | `tests/test_browser_calibration.py` |

The prospectively committed procedure is in
`docs/guides/browser-linear-protocol.md`. Synthetic validation is not authentic
data acceptance or evidence of an unconditional model advantage.
