# Prequential streaming evaluation

Stage: [`chronoscopelab/stages/streaming.py`](../../data-pipeline/chronoscopelab/stages/streaming.py)
Tests: [`tests/test_stage_streaming.py`](../../tests/test_stage_streaming.py)
Evaluator: [`preqts` on PyPI](https://pypi.org/project/preqts/), version 0.3.0
Detailed study protocol: [`main.tex`](../../manuscripts/prequential-streaming-conformal/tex/main.tex)

## Protocol

The stage passes each case's target and covariates to `preqts.Stream`. With horizon one and step one, it initializes each method from a prefix of length

\[
w=\min\bigl(\max(2m,20),\max(1,\lfloor T/3\rfloor)\bigr),
\]

where \(m\) is the case seasonality and \(T\) is its series length. At cutoff \(t\), the method predicts from the context observed through \(t-1\). The harness scores that forecast against \(y_t\), then ingests \(y_t\) and advances one position. This ordering prevents the target from entering the forecast that is scored against it.

The stage requests quantiles at 0.1, 0.5 and 0.9, so the outer interval has nominal coverage 0.8. Its four stored trajectories are trailing-25 means of MASE, empirical coverage and weighted quantile loss, plus cumulative measured prediction and ingestion time. The artifact does not store interval width. Runtime is a timing observation and varies by machine and run; it is not a complexity proof.

## Methods in the current bake

The roster is SeasonalNaive, raw Theta, Theta+ACI and Theta+PID. Theta uses a batch forecaster through `ReplayAdapter`; at every prediction it recomputes from the accumulated target history. The current experiment therefore does not compare replay cost with a streaming-native model's constant-cost update.

Theta's base quantiles are centered on its point path and widened by the in-sample residual standard deviation times the standard-normal quantile and square root of lead. The conformal wrappers use a rolling buffer of at most 200 normalized scores,

\[
z_t=\frac{|y_t-\hat y_t|}{\max((q_{0.9,t}-q_{0.1,t})/2,10^{-8})}.
\]

Their interval endpoints are the forecast median plus or minus the empirical score quantile times the base half-width. The buffer begins empty and its multiplier begins at one. ACI uses target coverage 0.8 and \(\gamma=0.02\). PID uses \(k_p=0.05\), \(k_i=0.02\), and \(k_d=0.02\). The implementation, initialization, clipping and update equations are specified in the manuscript's methods sections.

These are finite-stream implementations. The results do not establish a distribution-free guarantee for this buffer and base interval, nor do the two controls rule out every form of leakage.

## Stored evidence and limits

There are 15 committed case artifacts. The summary figure averages each case's mean trailing-25 coverage error with equal case weight; the point plot uses each case's final full-run coverage. The cases are selected examples, not a sample from a defined forecasting-task population. Four cases use redistributed real datasets; the remaining cases are generated. Some source series are not included in the public repository, so their online updates cannot be replayed from the streaming artifact alone.

The gain values are constants in the bake code. A parameter-selection rationale, sensitivity analysis, repeated-seed study, and complete source-data revision identifiers are not stored with these artifacts. Results and evidence boundaries are reported in [`prequential-streaming-conformal`](../../manuscripts/prequential-streaming-conformal/tex/main.tex).

## References

- Dawid, A. P. (1984). The prequential approach. *Journal of the Royal Statistical Society: Series A*, 147(2), 278–292. [doi:10.2307/2981683](https://doi.org/10.2307/2981683).
- Gibbs, I. and Candès, E. (2021). Adaptive conformal inference under distribution shift. [arXiv:2106.00170](https://arxiv.org/abs/2106.00170).
- Angelopoulos, A. N., Candès, E. and Tibshirani, R. J. (2023). Conformal PID control for time series prediction. [arXiv:2307.16895](https://arxiv.org/abs/2307.16895).
