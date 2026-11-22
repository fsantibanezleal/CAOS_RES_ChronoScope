# Numerical quantities and their source assumptions

ChronoScope accepts observables in source-specific units. Electricity examples
contain sums of four quarter-hour power readings in kW, without a conversion to
energy. Public forecasting collections can leave the original observable unit
undisclosed. A method may be inaccurate; it must still predict the declared
observable. The runtime range/advisory boundary and the author-time constant
inventory address complementary parts of that requirement.

The author-time gate inventories actual Python/TypeScript AST numeric nodes,
including signed floats, integer precision/count values and complex Fourier
coefficients. It binds every active engine file, the complete installed
ForecastScope provider, all active library TS/TSX files, and scientific browser
producers. Numeric-free files are bound too. Generated case parameters are
included with their synthetic-population interpretation; they are not silently
excluded from source review.

The reviewed occurrence baseline is
[`scripts/unit_constants.json`](../../scripts/unit_constants.json). Each entry
retains the exact literal, function/class scope, source expression and its hash,
quantity, unit, rationale and review state. Source hashes canonicalize CRLF to LF
so Windows and Linux audit the same Git text; no other source bytes are ignored.
The enclosing file hash prevents a
meaning-changing rewrite from inheriting approval just because the number itself
is unchanged. Provider version/source inventory and TypeScript compiler version
are part of the same acceptance boundary.

| Quantity | Unit and interpretation |
|---|---|
| Forecast level, residual and conditional sigma | Original input unit U; source-array transport retains numerical precision. |
| Conditional variance, squared error and l2 segmentation penalty | U squared, with penalty derived from observed variation; non-l2 PELT costs need explicit penalties. |
| Context/kernel distance, scaled loss and convex weights | Declared normalized coordinates; the RMS context bandwidth floor is not an amplitude floor in U. |
| Probability, coverage, p-value and quantile level | Dimensionless probabilities, with explicit statistical/finite-sample assumptions. |
| Entropy matching tolerance | Dimensionless tolerance ratio times the original observed standard deviation in U. |
| Lyapunov interpretation cutoff | Inverse sample steps under the estimator's default sample index; no universal physical chaos threshold. |
| Wavelet periods, lags, horizons and memory age | Sample steps or completed origins; physical durations require stated cadence. |
| HP lambda1600 | Discrete-index smoothing penalty using the declared quarterly convention, not a cadence-independent filter. |
| Synthetic levels/noise/slopes | Generated U or U per sample; generator probability/shape/phase factors are separately dimensionless. |
| Time and payload budgets | Milliseconds/seconds or bytes; they do not restrict observable amplitude. |
| Legacy reconstruction allowance | The specific frozen trace's declared four-decimal storage resolution in U; never a generic fitting floor. |
| Figure geometry | Inches, viewport coordinates or plotted normalized-score/coverage coordinates; not a model parameter. |

Exact zero can be a neutral element with the same unit as the surrounding
quantity, or a zero-based coordinate. This does not justify replacing an unknown
positive scale with1 or1e-12 U. The active methods normalize with representable
observed scales and declare constant/zero-variance behavior explicitly. Raw point
comparisons in the browser evidence validator are divided by their common
observed fitting scale; equality of positive scales uses a relative comparison.

Run the gate in the declared product runtime after installing the frontend's
locked dependencies:

```text
python scripts/check_unit_constants.py
python -m pytest tests/test_unit_constants.py
```

To author a change, run `python scripts/check_unit_constants.py --update` and
inspect the diff. Changed sources receive pending annotations, even if their
previous numbers had an explanation. Write the specific quantity, unit and
rationale; test the claimed unit transformation and exact-degenerate behavior;
then obtain a reader's dimensional review before accepting the baseline. The
update command deliberately exits unsuccessfully while entries remain pending.

An inventory pass establishes an exact source/annotation match, not a proof that
every formula is dimensionally correct. Hidden constants inside third-party
algorithms, cadence assumptions, runtime backend behavior and scientific accuracy
still require source-specific review and validation. The runtime observable
diagnostic remains loose and must not become an accuracy filter or change the
forecast to make a check pass.
