# Observable units in computation and source

The runtime boundary inspects finite forecasts in the original observable. Its
loose range diagnostic remains separate from forecast accuracy and keeps valid
constant methods as advisories. The author-time boundary catches a different
failure: a newly introduced numeric assumption that has not declared a quantity.

`scripts/check_unit_constants.py` parses every active `data-pipeline/engine`
Python module, including the case fixture generator, the installed ForecastScope
provider, active `frontend/src/lib` TypeScript/TSX modules, and the named browser
training/evaluation/calibration/evidence/figure producers. Test modules are
excluded from this method inventory. Numeric-free modules remain inventoried so
a new method cannot enter silently. Python uses `ast`; TypeScript uses the actual
installed TypeScript compiler through `scripts/unit_constants_ts.mjs`. A parser
failure is a failed gate, never an empty accepted result.

Each signed integer, float or complex Python constant and each TypeScript numeric
literal is recorded with source location, enclosing scope, expression, expression
hash and source-file SHA-256 after CRLF-to-LF canonicalization. This matches Git's
portable text identity without ignoring a token or expression change.
`scripts/unit_constants.json` gives every occurrence
its quantity, unit, rationale and review state. Provider distribution version,
provider source members and compiler version are bound as well. A source edit
requires review even when it leaves the number of literals unchanged.

`--update` creates pending review entries for changed sources; it does not infer
units or grant approval. In particular, assigning the word "dimensionless" alone
does not justify a literal. Neutral zero is recorded as an identity in its
surrounding quantity, rather than an arbitrary positive amplitude floor.
Synthetic levels and slopes have generated units, probability/shape parameters
have their stated ratios, and durations/byte budgets are operational quantities.
The distinctions and remaining limits are detailed in
[numerical-units.md](../../numerical-units.md).

This source inventory is not a symbolic units solver. A reviewer must establish
that the annotation matches the expression, and metamorphic/degeneracy tests must
test the claimed behavior. The gate prevents an accepted annotation from being
silently carried onto a different source expression or provider revision.
