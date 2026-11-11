# Which information belongs to a forecast at issuance?

**Question:** How can the same electricity excerpt yield a different historical method choice, final-block ranking, and interval coverage trajectory?

## Objectives

A dashboard can show a preferred method, a path for a particular forecast origin and a recent coverage estimate on one screen. They use different observations and answer different questions. We will reproduce these quantities while tracking the information available to each calculation. The same experiment also shows how a small teaching export differs from a complete product release.

The test case is a chronological excerpt of meter MT_010 in the UCI electricity collection. Its hourly values are sums of the retained quarter-hour measurements. We reserve the final 24 observations of a five-day excerpt for one forecast and use earlier observations for the historical scores. The rolling backtest, the later reserved forecast and the one-step replay use the same source but use different origins. None represents a new customer planning result. We will keep their numerical outputs separate even when they have the same method name.

## Setup

Use the declared notebook runtime. The stage registry discovers optional adapters from the installed libraries, so the roster can differ from the full published offline roster. The notebook prints the roster it actually executes. There is no checkpoint download in this environment. Exact pins make both the local methods and their reference packages identifiable.

```text
{{PINS}}
```

<!-- code: setup -->

## Data

The ingestion stage reads a long table whose keys are series identity and timestamp. It returns accepted records, rejected records and warnings. The warning mechanism distinguishes a suspicious observation from an unreadable or inadmissible series. An accepted record can still have missing values under the ingestion rule. Additional conditions are needed before a model consumes a contiguous finite prefix. In this example the slice is contiguous and finite. We cut the slice in timestamp order and keep the original positions, so a seasonal lag of 24 refers to one day.

<!-- code: data -->

The code starts with a single source record and defines the horizon before calling any scoring function. The inference stage reserves the last block, fits on the preceding prefix and returns predictions. The targets are passed only to the scoring and export steps. The same separation also applies to diagnostics when they inform a decision. A retrospective graph may use the whole series to explain what happened. A diagnostic used to choose a forecast must be calculated using the information already available at issuance.

## Method

Call the feature stage and diagnostic stage on the fitting prefix. The feature row records familiar quantities such as lag-one correlation in a compact form. It describes the data supplied to it and does not predict the next observation. The larger analysis record adds separate panels whose applicability can vary. Some diagnostics remove nonfinite observations or require optional dependencies. A panel with an error or skip record needs to be read as unavailable. The code prints panel identities to make the boundary visible without interpreting every statistic as a conclusion about this meter.

<!-- code: diagnostics -->

A point prediction from the final origin can be compared with a reserved value at the same lead. Let $n$ be the prefix length, $h$ the horizon and $m$ the seasonal lag. Compute the historical scale once using only the prefix.

$$
s_m=\frac{1}{n-m}\sum_{i=m+1}^{n}|y_i-y_{i-m}|.
$$

The final-block MASE for a point path $\widehat y$ is

$$
\operatorname{MASE}=\frac{1}{h s_m}\sum_{j=1}^{h}|y_{n+j}-\widehat y_{n+j}|.
$$

The denominator measures past variation relative to seasonal recurrence. A small value can amplify errors even when their absolute size is modest. The code uses the same prefix scale for all final paths, which makes their scores directly comparable on this origin. The historical evaluator constructs its own prequential scale for a different set of earlier origins. Comparing the rankings is meaningful as a diagnostic of sensitivity to evaluation design; a difference between the scores is not an estimate of degradation measured on repeated independent blocks.

## Comparison

The package reference repeats the last daily phase and returns three quantile columns. Its median equals the recorded value at the corresponding phase for these 24 leads. The Theta path comes from the installed ChronoScope inference stage. The ribbon belongs to that path's lower and upper quantiles, and the actual line is drawn only after fitting. Compare the lines during the rising and falling portions of the day. An average error can hide a peak shift or a failure to respond to a downward ramp.

<!-- code: inference -->

The next figure pairs rolling and final-block scores for SeasonalNaive, SES, Holt, HoltWinters and Theta. The rolling evaluator fits earlier forecast origins in the prefix and scores the corresponding later blocks there. Candidate adapters may have different historical window budgets, so the figure compares only these five implementations. For each of them the single final block has one particular pattern of targets. A method with low error over earlier origins may encounter a different daily level or phase in the reserved block. Check which method has the smallest bar within each evaluation and report the origin design with that ranking.

<!-- code: scores -->

### Sensitivity to the evaluation window

A separate one-step replay now stays inside the same fitting history. On each replay step the forecaster predicts before seeing the next outcome. The controller can change its next interval after learning whether the current one covered the realized value. This information order gives an adaptive interval a well-defined meaning. It does not make predictions at neighboring times statistically independent. The historical score table and the coverage trajectory also have different horizons, so no coverage claim for the 24-step band follows from this calculation.

<!-- code: stream -->

The dashed line is the declared marginal target. When a curve approaches it, inspect how long the nearby values persist and what happened earlier. A high coverage level alone can be obtained with a wide interval. A low score under a proper interval metric requires balancing width and missed observations. The plotted trajectories do not supply uncertainty on a future coverage fraction. They let a reader see, on this particular prefix, when a controller responds to a sequence of misses. The one-step wrapper refits its base forecast on available history; the elapsed time of that wrapper is different from the time to update an estimator with persistent native state.

## Results

**Answer:** The rolling ranking summarizes earlier forecast origins inside the 96 available observations. The final ranking uses the 24 reserved observations, and the coverage graph uses one-step updates inside the prefix. These quantities differ when the sampled origins, horizons, and available observations differ. Read each evaluation with its own denominator and target window.

The training selector in the next cell uses two generated histories. It averages the rolling MASE for each of the same five forecasters across those histories and records a default. The choice is neither derived from the electricity targets nor used to select the electricity winner. The export stage writes a trace, manifest, analysis and replay to a temporary directory. It records the measured cost of the five-adapter forecast call for this run, but no machine-specific timing is printed as a reproducible result. The manifest supplies an artifact path and byte count, and the index names which manifest belongs to each case. The code checks this relation before the directory is removed.

<!-- code: export -->

The release inventory uses the same general file relationships across the entire product. A single well-formed trace does not show that an application has every case or evidence file it declares. The readiness record names the current catalog digest and version, and the admitted index records the full case count. Schema checks, exact numerical bindings and complete cohort checks accompany readiness. Read the recorded inventory and identities separately from the small training exercise.

<!-- code: readiness -->

### Identify the origin behind a published score

The full fresh comparison has an electricity row with the same case label and horizon. It uses the final block of the complete admitted history. The local teaching cut uses an earlier day, so equal case labels and horizons cannot establish equal targets. Compare the lengths and targets before transferring a score. The independent combination study has a second level of identity. Its index points to a specific source series, and its case record contains the eligible origins with fitting-prefix digests, scales, targets and all forecast paths. Follow one index entry below and interpret the shape of its first ValidationMix path as reserved observations by quantile levels. The compact index serves navigation. The case record supplies the information needed to inspect a numerical claim about that series.

<!-- code: comparison_records -->

The browser experiment uses a different boundary again. Its frozen linear graph accepts a fixed-length normalized prefix and produces twelve point values. The original ridge study changed the point estimator, while the confirmation study keeps the graph and points fixed and changes only the prediction intervals. Rescore the retained studies before comparing the normalized errors. The independent checker verifies the graph digest, configuration identities, split separation and arithmetic on retained forecast paths. This calculation uses their retained outputs; it does not refit the graph or measure new browser runtime.

<!-- code: browser_calibration -->

In the ridge comparison, first compare point MAE against the frozen model. A narrower interval can improve an interval score even if the center becomes worse. In the confirmation, compare interval scores for the same point path. The calibration group depends on roughness within the observed prefix. Its empirical residual radii come from separate calibration series, and the score is measured on untouched generated test series. A normalized score is expressed relative to the prefix scale. It cannot be read as an electricity-unit error, and the synthetic test cannot establish real-data coverage for the teaching meter.

### Repeat the comparison with your own data

Choose a horizon that corresponds to an action such as staffing the next shift. Preserve timestamps and sampling frequency, including daylight-saving transitions. Record the policy for gaps and repeated times before ingesting the table. Use separate histories for training a default where available. Pick final evaluation blocks before scoring, keep the fitting prefix contiguous, and decide whether a controller can see outcomes immediately or only after a delay. Make the same assumption for each compared method.

Inspect the two scoring designs with several consecutive reserved days if enough history is available. Keep each day's entire path, its method revision and its units. If an adapter cannot forecast an origin, report the failure and analyze the common-support results explicitly. Retain available long-format records and versioned hashes so a reader can recover which observations supported every result. Before publishing an export, verify redistribution rights for the original series and inspect whether the per-step forecast or diagnostic arrays reveal restricted values.

## Summary

Identify the origins and information sets first. Choose a score appropriate to the decision horizon, preserve all forecasts and targets, and document the training histories and available methods. A trace and manifest let a reader inspect these choices, while completeness and evidence checks determine whether a whole research release is ready.

## References

- [UCI electricity source](https://doi.org/10.24432/C58C86).
- [Dawid's prequential framework](https://doi.org/10.2307/2981683).
- [Adaptive conformal inference](https://arxiv.org/abs/2106.00170).
- [PreqTS 0.3.0](https://pypi.org/project/preqts/0.3.0/).
