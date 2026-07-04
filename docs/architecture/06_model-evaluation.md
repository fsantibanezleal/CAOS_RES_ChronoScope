# Model evaluation (the TEST stage)

`stages/evaluate.py` reports leakage-safe metrics via the `preqts` prequential library: a rolling-origin
backtest over the case history where every window predicts out-of-sample, so no method ever sees its own test
point. Each method (seasonal-naive, SES, Holt, Holt-Winters, Theta) is wrapped into the preqts
StatefulForecaster protocol and scored on:

- MASE (point accuracy, scaled by the in-sample seasonal-naive error; below 1 beats the baseline),
- WQL (the weighted quantile loss over the full quantile forecast),
- empirical interval coverage against the nominal level.

The per-method metrics are written into each case's manifest and the trace, and surfaced on the App and the
Benchmark/Experiments views. The final `horizon` observations of each series are held out as the display truth
shown next to each forecast, so the displayed forecast is genuinely out-of-sample too.

This is where the honesty lives: the near-random-walk and white-noise control cases exist precisely so that a
suspiciously large skill gap would flag a leak. The `train` stage learns the global method ranking on the
synthetic training cases only; each case still reports its own held-out metrics. Later slices add the streaming
(constant-cost, stateful) evaluation lane that preqts is built for.
