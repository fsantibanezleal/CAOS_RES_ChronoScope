# Change points and regimes

Code: [`chronoscopelab/analysis/changepoints.py`](../../data-pipeline/chronoscopelab/analysis/changepoints.py)
· Tests: [`tests/test_analysis_changepoints.py`](../../tests/test_analysis_changepoints.py)

## Why breaks matter for forecasting

Every fitted model assumes one process generated the whole training window. A **structural break** (a shift
in mean, variance, or dynamics) violates that: the model averages two regimes and forecasts neither. Breaks
and regime changes are among the structures that most reliably degrade both classical models and zero-shot
foundation models, so ChronoScope's case narratives lean on this panel. Three complementary questions:

![Breaks, stability, regimes](assets/changepoints-regimes.svg)

1. **Where are the breaks?** - offline change-point detection (PELT / Binary Segmentation).
2. **Are the parameters stable at all?** - the CUSUM test.
3. **Which regime is each point in?** - Markov switching (recurring states, not one-off breaks).

## PELT: exact penalized segmentation in (expected) linear time

Change-point detection minimizes, over the number of breaks $m$ and their locations $t_1 < \cdots < t_m$,

$$\sum_{j=0}^{m} \, \mathcal{C}\big(y_{t_j : t_{j+1}}\big) \;+\; \beta\, m ,$$

a per-segment cost $\mathcal{C}$ (here the $\ell_2$ cost = within-segment variance, for mean shifts; the
`normal` cost adds variance shifts; `rbf` is model-agnostic) plus a penalty $\beta$ per break. **PELT**
solves this *exactly* by dynamic programming with a pruning rule whose expected cost is linear in $n$
(Killick, Fearnhead & Eckley 2012, DOI
[10.1080/01621459.2012.737745](https://doi.org/10.1080/01621459.2012.737745)). ChronoScope's default
penalty is BIC-style, $\beta = 2\hat\sigma^2 \log n$, with $\hat\sigma^2$ estimated robustly from first
differences; too small a penalty over-segments noise, too large misses real breaks - the report records the
penalty used so the read-out is auditable.

**Binary segmentation** (`binseg`) is the greedy alternative: find the single best break, recurse on the two
halves. It is $O(n \log n)$ and approximate; ChronoScope uses it when the number of breaks is known a
priori. Library: `ruptures` (Truong, Oudre & Vayatis 2020, DOI
[10.1016/j.sigpro.2019.107299](https://doi.org/10.1016/j.sigpro.2019.107299)).

## CUSUM: is anything drifting at all?

The OLS-CUSUM test cumulates scaled OLS residuals; under the null of parameter stability that path behaves
like a Brownian bridge, so its supremum has known bounds:

$$\sup_t \left| \frac{1}{\hat\sigma \sqrt{n}} \sum_{s \le t} \hat e_s \right| \;\gtrless\; c_\alpha .$$

Crossing the bound rejects stability (Brown, Durbin & Evans 1975 lineage; the Ploberger-Kramer OLS variant
implemented by statsmodels' `breaks_cusumolsresid`). It answers "is there drift?" without locating it - the
cheap first gate before segmenting.

## Markov switching: recurring regimes, not one-off breaks

Where PELT models breaks as permanent, many series *alternate* between recurring states (calm/volatile,
high/low demand). Hamilton's Markov-switching model (Econometrica 1989, JSTOR
[1912559](https://www.jstor.org/stable/1912559)) posits a latent K-state first-order Markov chain $S_t$ with
per-regime mean (and optionally variance):

$$y_t = \mu_{S_t} + \varepsilon_t, \qquad \varepsilon_t \sim N(0, \sigma^2_{S_t}), \qquad
P(S_t = j \mid S_{t-1} = i) = p_{ij} .$$

The Hamilton filter + smoother yield $P(S_t = j \mid y_{1:n})$ per point - the regime-probability ribbon the
web renders. The fitted transition matrix tells regime persistence (diagonal near 1 = long-lived states).
Implementation: `statsmodels` `MarkovRegression` (regime means read from the named `const[j]` parameters).

## What this is, and is NOT

- PELT/Binseg locate breaks in *retrospect* (offline, whole-sample). They are not real-time detectors: the
  online counterpart (BOCPD, Adams & MacKay 2007) belongs to the streaming lane and is planned with `preqts`,
  not duplicated here.
- The Chow test (single *known* break date) is deliberately not wrapped: it is not first-class in
  statsmodels' public API (verified), and the unknown-date problem is covered by PELT + the break-aware
  Zivot-Andrews unit-root test (stationarity page).
- A detected break is a statistical statement about the cost model used (mean shift under `l2`), not a causal
  event; corroborate against the volatility and regime views before narrating a cause.
- Markov switching assumes the regime process is Markov and the regime count K is chosen by the analyst; the
  report records a fit failure honestly (`markov.error`) rather than forcing a degenerate fit.

## Implementation notes

- `ruptures.Pelt` / `ruptures.Binseg` (cost models `l2`/`normal`/`rbf`, `min_size` guard); `statsmodels`
  `breaks_cusumolsresid` and `MarkovRegression` (smoothed marginal probabilities). Inputs coerced to finite
  1-D; ruptures' segment-end convention converted to first-index-of-new-segment breakpoints.
- `changepoints_report(x)` bakes: PELT breakpoints + per-segment mean/std + the penalty used, the CUSUM
  stat/p-value/verdict, and the Markov fit (means, most-likely path, transition matrix) or its recorded
  error. This is what the pipeline writes per case.

## References

- Killick, R., Fearnhead, P. & Eckley, I.A. (2012). Optimal Detection of Changepoints With a Linear Computational Cost. *JASA* 107(500):1590-1598. DOI [10.1080/01621459.2012.737745](https://doi.org/10.1080/01621459.2012.737745).
- Truong, C., Oudre, L. & Vayatis, N. (2020). Selective review of offline change point detection methods. *Signal Processing* 167:107299. DOI [10.1016/j.sigpro.2019.107299](https://doi.org/10.1016/j.sigpro.2019.107299).
- Brown, R.L., Durbin, J. & Evans, J.M. (1975). Techniques for Testing the Constancy of Regression Relationships over Time. *JRSS-B* 37(2):149-192. DOI [10.1111/j.2517-6161.1975.tb01532.x](https://doi.org/10.1111/j.2517-6161.1975.tb01532.x).
- Hamilton, J.D. (1989). A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle. *Econometrica* 57(2):357-384. JSTOR [1912559](https://www.jstor.org/stable/1912559).
- Adams, R.P. & MacKay, D.J.C. (2007). Bayesian Online Changepoint Detection. arXiv:[0710.3742](https://arxiv.org/abs/0710.3742) (the online counterpart; streaming lane).
