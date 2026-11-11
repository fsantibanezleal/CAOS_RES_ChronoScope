# Teach a sequence method in a notebook

The English and Spanish trees in [the lesson index](../../notebooks/README.md)
share paths and experimental structure. Use one question that can be answered
by running an implemented method. The electricity baseline distinguishes the
committed source readings from the observed prefix and held-out block. A
different origin changes both the fitted data and the comparison targets.

Use the actual product or published package entry point. Define the observation
axis, units and cutoffs before the first fit. A plot of a committed output alone
does not explain how to choose a lag, fit an estimator or interpret a score.
Compute an intermediate numerical value with the reader, then compare a method
against an independent calculation or a named reference on the same data.
Higher-level lessons also need a sensitivity experiment and instructions for
using the method on a new series. Keep scale failures and negative results.

The adopted static guards measure both language trees. Generate and inspect
fresh kernel outputs in the declared external notebook environment. The execution
check uses an external temporary directory and preserves the committed files.

```text
python scripts/check_notebooks.py
python scripts/check_notebook_depth.py --report
python scripts/run_notebooks.py --check --tmp <external-scratch>
```

The whole-tool coverage file records the lessons that teach each declared method,
data contract, pipeline stage and package. Add an entry only after both language
versions teach the named subject. A missing entry identifies curriculum work.
