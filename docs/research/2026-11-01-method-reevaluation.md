# Forecasting implementation reassessment

Reviewed 2026-11-01 against current source, the released traces, the current template and primary sources. The product checkpoint is `2706742`; follow-up source changes and the comparison artifact are separately committed.

The sections below record the initial archived-path reassessment. The subsequent full
fresh execution is documented in the [fresh evaluation guide](../guides/fresh-reevaluation.md)
and its separately admitted artifact; the browser retains both experiments explicitly.

## Established forecasts

SeasonalNaive repeats the last observed seasonal block. SES and Holt use explicit finite grids, first-observation initialisation and residual Gaussian intervals. They are transparent implementations with narrower fitting choices than a fully optimised state-space package. Their intervals are approximations; fitting a quantile loss or applying square-root-horizon widening does not establish calibration.

Two defects were identified by re-reading the equations rather than only checking finite output. HoltWinters indexed the next season at zero, losing phase when the history length was not a seasonal multiple. It now uses the actual next phase in Python and TypeScript. The nonseasonal Theta forecast omitted the finite-history SES correction from [Hyndman and Billah's equation 5](https://robjhyndman.com/papers/Theta.pdf). It now matches the mean of the two Theta lines for the chosen grid alpha. Automatic seasonal adjustment remains the separate AutoTheta engine. The [Holt-Winters equations](https://otexts.com/fpp3/holt-winters.html) and the two independent regression plants define the checks. The parity fixture now includes a partial final season.

## Library and pretrained implementations

| Implementations | Audit finding and admitted evidence |
|---|---|
| AutoETS, AutoTheta, AutoARIMA | Actual statsforecast adapters exist; AutoARIMA uses stepwise/approximate search and a 360-point context cap. Those choices belong to the method configuration. |
| LightGBM | A real lag-feature adapter exists; its frozen paths can be scored on the same final block as other methods. |
| NLinear, DLinear, NHITS via neuralforecast | These consume the maintained reference library, with a fixed training budget and multiple quantile loss. The training budget is part of the experiment, not the complete capacity of the architecture. |
| Direct-torch NLinear, DLinear, NHITS | These are adaptations, including quantile heads and the project's documented NHITS design. Their names and provenance stay distinct from neuralforecast. They are not automatically faithful independent replications or parity oracles. |
| Chronos-Bolt and Chronos-2 | Local-checkpoint wrappers exist. [The official releases](https://github.com/amazon-science/chronos-forecasting/releases) now include 2.3.2, while the original environment used 2.3.1; the refresh does not relabel a frozen result as a new package run. |
| TimesFM 2.5 | The official model supports a separate point/quantile output layout; [the primary API](https://github.com/google-research/timesfm/blob/master/timesfm-forecasting/references/api_reference.md) identifies the median and nine quantile columns. The committed path remains tied to its historical adapter configuration. |
| TiRex-2 | A real WSL/CUDA bridge and frozen forecast paths exist; [the primary paper](https://arxiv.org/abs/2607.01204) supports multivariate/covariate capability. The current refresh rescored its committed path and did not rerun that checkpoint. |

The original rolling backtests used different origin budgets, ranging from three to over twenty-five windows per case. A cross-method ranking of those scores confounds the model with its evaluated origins. They are kept as historical measurements, labeled accordingly. The new comparison instead scores every method against exactly the same committed final block. Fourteen heavy-model paths are frozen, five light methods are recomputed after the fixes, and three combinations are freshly evaluated. Each source trace and each current computation module has a SHA-256 binding in the new artifact.

## Proposed forecasting rule

ContextMemory is specified in the companion proposal, implemented as engine code, and evaluated with two ablations. Its context component did not beat its recency-only ablation on average. The negative result is retained. Adaptive conformal wrappers, the prequential protocol and property visualisations are useful components, but none is relabeled as this forecasting method.

## Evidence limits

The common final-holdout experiment has one origin per selected case. Heavy forecasts are archived outputs, not a fresh replication using every newly released package. Pretraining overlap and source-corpus revisions remain unverified. The in-history seasonal scale in MASE is not the error of an independently scored naive forecast on the final holdout. The direct-torch quantile heads and the Gaussian intervals are not calibrated merely because a loss function or an interval was implemented. These distinctions are carried into the app and technical report.

## Contiguous-history correction

Replay histories are display-decimated for nine cases and cannot be treated as consecutive observations. The corrected comparison reconstructs the complete original histories, verifies every displayed sample and target, binds the original CSV inputs and uses one contiguous historical scale per case. See `docs/research/2026-11-01-history-decimation-correction.md` for the invalidation record.
