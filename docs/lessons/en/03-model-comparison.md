# Comparing executed adapters with archived model paths

**Level:** 3. **Prerequisites:** Earlier lessons in this topic; NumPy arrays and temporal evaluation. **Reading time:** 50 minutes.

**Question:** How do four fitted statistical/tree adapters, seven newly executed neural/pretrained references and separately archived paths compare on the same synthetic 12-step target block?

## Objectives

Compare methods without erasing how their predictions were obtained. This lesson executes three distinct evidence sources on the same synthetic history and 12 reserved targets. First it fits the installed AutoETS, AutoTheta, bounded AutoARIMA and LightGBM adapters. Then the pinned reference runtime actually fits NeuralForecast NLinear, DLinear and NHITS and runs the pinned Chronos-Bolt, Chronos-2, TimesFM-2.5 and TiRex-2 checkpoints. Separately it rescores previously retained forecast paths, including direct-torch adaptations. Rescoring an archived prediction is a new calculation, not a new fit or checkpoint inference.

We will examine point error and uncertainty width separately, retain the original forecast names, and identify limitations that a leaderboard cannot resolve. The experiment does not establish performance on a new population, independence from pretraining data or the accuracy of a production planning policy. Its narrower purpose is useful: competitors share their available series, forecast horizon, final targets and scaling rule, so an error difference cannot be attributed to a different scoring block.

## Setup

The exact direct pins below identify the notebook environment and its statistical/tree providers. The separately declared Linux reference runtime supplies the seven neural/pretrained implementations; its checked package versions and checkpoint revisions are printed with the newly returned paths. Prepare that runtime and its weights through the documented setup before execution. No cell installs packages or substitutes smaller models.

```text
{{PINS}}
```

<!-- code: setup -->

## Data

This shared adapter experiment takes the synthetic trend-plus-season fixture TRND_seasonal from `data/derived/TRND_seasonal/trace.json`. Its owner is the ChronoScope project, licence MIT; the seed-42 generator is `data-pipeline/engine/cases/forecast_cases.py`. The history is the available fitting prefix, actual is its consecutive reserved final block, seasonality is 12 observations and horizon is 12 predictions. Values have generated source units. Retained paths are identified separately from calls executed here. The reference package and checkpoint sources are listed in References; a model's prior pretraining exposure is not ruled out by this example.

<!-- code: data -->

## Method

AutoETS selects an exponential-smoothing specification within the installed statsforecast implementation. The adapter receives the seasonal period from the trace and maps the library's analytical interval columns to the requested quantiles. Running the actual adapter matters: a hand-coded smoothing curve with the same display name would not reproduce the library's model selection or parameter fitting. The resulting score applies to this installed version and this history, rather than an unspecified ideal implementation of the ETS family.

<!-- code: ets -->

AutoTheta is similarly delegated to the reference library. It is distinct from the local finite-history Theta function introduced earlier. Automatic seasonal treatment and selection can change its forecast, so combining the two under one identity would conceal an implementation choice. The code prints its first prediction to expose an executed result while keeping the same origin and horizon as ETS. Parameter settings are not chosen after looking at the reserved future block.

<!-- code: auto_theta -->

AutoARIMA uses the released bounded configuration: stepwise search, approximate fitting and a maximum context of three hundred sixty observations. These choices keep computation practical and are part of the tested method. They do not represent an exhaustive search of all seasonal orders. A stronger or slower alternative would be another experiment with its own runtime and provenance. Numerical runtime notices, including convergence problems, are captured and printed without machine paths. A returned forecast with a convergence notice is not evidence of a successful optimum. Any exception or non-finite output still prevents clean execution.

<!-- code: arima -->

LightGBM converts past values into lag features and predicts recursively through MLForecast. The configured model uses one hundred trees, thirty-one leaves and a learning rate of five hundredths. Its point objective is not quantile regression. The adapter estimates a residual standard deviation and constructs Gaussian intervals around its point path, so uncertainty is an additional assumption rather than a learned conditional distribution. Recursive reuse of predictions can amplify errors at later leads even when the first-step fit looks convincing.

<!-- code: tree -->

## Comparison

The first figure compares newly executed paths with the same observed final block and a freshly computed SeasonalNaive reference. Every line uses the same value scale. Identify whether the models disagree mainly about trend, recurring shape or amplitude. A model can improve the average while missing the particular peak that matters to a planner. This plot therefore supports diagnosis; the printed scores provide an explicitly defined whole-block comparison without inventing an operational cost function.

<!-- code: reference_plot -->

The figure makes model disagreement visible but does not attribute its cause uniquely. A difference between a tree and a statistical model can reflect lag features, recursion, context length, fitting objectives or parameter selection. It cannot automatically be called a benefit of model capacity. The common temporal cut removes one confounder while leaving these genuine method differences in place. Controlled ablations would be needed to isolate each proposed explanation.

The next cell uses the frozen neural and pretrained paths stored in the released trace. Direct-torch NLinear, DLinear and NHITS adaptations retain separate names from the neuralforecast variants. Chronos-Bolt, Chronos-2, TimesFM and TiRex paths likewise retain their checkpoint-era provenance. The metric function is executed again on their stored predictions, using the same prefix scale and final targets as the newly executed adapters. No neural training, checkpoint download or foundation-model inference occurs in this cell.

<!-- code: frozen_scores -->

Point accuracy and interval width answer different questions. The second figure plots MASE against mean width for the archived methods. Coverage remains in the printed table so narrow intervals cannot be praised without checking their misses. Width is expressed in the series' units and should not be pooled directly across unrelated datasets. A low point on this plot is evidence about this block only; it does not prove that a method dominates across repeated origins or costs.

<!-- code: frozen_plot -->

The scatter can expose tradeoffs that disappear in a single ranking. Two models with similar point error can express very different uncertainty, while a broad interval can produce high coverage without useful precision. Three available quantiles also provide a limited view of the predictive distribution. The artifact's weighted quantile loss averages those three quantile scores; it is not an integral over an entire distribution or a claim that every tail probability is reliable.

### Sensitivity to forecast lead

Let $y_1,\ldots,y_n$ be the fitting history and $m$ the declared seasonal lag. The seasonal reference scale uses differences entirely within that prefix.

$$
s_m=\frac{1}{n-m}\sum_{i=m+1}^{n}|y_i-y_{i-m}|.
$$

With the same scale for every method, a group $G$ of forecast leads has scaled absolute error

$$
E_G(f)=\frac{1}{|G|s_m}\sum_{j\in G}|y_{n+j}-\widehat y_{n+j}^{(f)}|.
$$

The full group gives MASE for the reserved block. Split the leads into two equal groups after producing the original fixed-horizon forecasts. The cell below applies the same operation to each newly executed point path and the seasonal reference. It holds the fit, forecast origin, horizon and scale constant. Any change in the relative ordering reflects which outcomes and forecast positions enter the score. A refit at a later origin would expose new information and answer a different question. A change of horizon could also change how an adapter fits or constructs its predictions.

<!-- code: lead_sensitivity -->

Read each pair of bars together. Differences in the later leads can reflect recursion, accumulating trend mismatch, or the position of a difficult peak. The plot alone cannot identify which explanation applies. Compare the exact leads in the earlier path plot before making an attribution. The early and late scores are dependent because the forecasts were issued together and the targets come from one series. Repeating the exercise across origins with nonoverlapping target blocks would support stronger evidence. Keep all models' early and late results, including cases where the preferred method changes. A decision that only acts on the next six steps may reasonably emphasize the first group. State that priority before checking the scores.

### Try this with your own data

Choose one regularly sampled series and retain the original timestamps, units and missing-value flags. Decide the forecasting horizon from the action that needs the predictions. Use the actual data frequency to specify a seasonal lag, or declare a one-step scale where seasonality is unsupported. Pick the last training timestamp before reading the reserved values. Save the complete contiguous history, the targets in chronological order and the forecast origin. Check that every method receives that history, that all paths have the same number of leads and that every reported point or quantile uses the original target units.

Inspect the denominator before computing MASE. A constant seasonal recurrence can give zero scale. In that case report the absolute error in source units and declare scaled error undefined. Dropping these cases only for one candidate can produce an apparent advantage by changing the sample. Log exceptions, convergence notices and checkpoint revisions next to the paths. If a pretrained model has an uncertain training-data overlap, retain that uncertainty alongside its scores. Use the same decisions on the next independently reserved blocks before changing the roster. These records let another reader determine whether an apparent improvement belongs to the model, the evaluation design or the data available at the time.

If the target represents energy per interval, sum forecasts across a decision block only after checking the aggregation rule. A sum of marginal lower quantiles generally differs from the lower quantile of the total. For a procurement total, validate the forecast distribution of that total on its own historical decision blocks.

## Results

**Answer:** On the same synthetic 12-step target block, freshly fitted AutoARIMA has MASE 0.526274 and freshly executed Chronos-2 has 0.532694. AutoARIMA reports a convergence notice, so its returned score does not establish a successful optimum. Fresh TimesFM-2.5 coverage is 0.833333 on this block, which does not establish calibrated population coverage. The retained direct-torch DLinear path has MASE 0.378737, whereas the newly fitted NeuralForecast DLinear reference has 2.951097. These distinct implementations must retain separate identities. Four installed adapters, seven actual reference fits/inferences and separately rescored archived paths share targets and scale, but provide different provenance. This one generated case supports no general superiority claim.

The number of methods is not the number of independent experimental replications. Their errors share a target series and often share modelling assumptions. General comparisons require declared datasets, multiple temporal origins, appropriate dependence-aware uncertainty and resource budgets. For real excerpts, potential overlap with model pretraining must also be investigated. Those obligations remain visible instead of being replaced by a favorable mean from a selected collection.

## Summary

Specify what ran, what was read, which implementation and settings produced each path, and what observations define every score. Keep direct adaptations distinct from reference-library implementations. Compare point quality with interval width and coverage, and preserve negative outcomes. The next lesson tests a fixed context-dependent combination against two matching-expert ablations, using a criterion declared before examining the final holdouts.

## References

- Forecast scaling: https://doi.org/10.1016/j.ijforecast.2006.03.001
- Local Theta identity: https://robjhyndman.com/papers/Theta.pdf
- Smoothing and seasonal continuation: https://otexts.com/fpp3/holt-winters.html
- Feature-dependent combinations: https://doi.org/10.1016/j.ijforecast.2019.02.011
- Dynamic ensembles: https://doi.org/10.1007/s10994-018-05774-y
