import { H, Lead, P, Ref, UL } from '../components/doc';
import { M } from '../components/Math';

export function Methodology() {
  return (
    <div>
      <H>Methodology</H>
      <Lead>
        The method ladder, from a transparent baseline upward. Every method emits a point path and a prediction
        interval, and is scored on the same rolling-origin backtest. Notation: history <M tex="y_1,\dots,y_T" />,
        horizon <M tex="h" />, seasonal period <M tex="m" />, forecast <M tex="\hat y_{T+k}" /> for
        <M tex="\,k=1,\dots,h" />.
      </Lead>

      <H>Baselines and scaling</H>
      <P>
        The <b>seasonal-naive</b> forecast repeats the last season, <M tex="\hat y_{T+k}=y_{T+k-m}" />. It is
        also the denominator for the mean absolute scaled error, so a method beats the baseline exactly when its
        MASE is below 1:
      </P>
      <M block tex="\mathrm{MASE}=\frac{\frac{1}{h}\sum_{k=1}^{h}\lvert y_{T+k}-\hat y_{T+k}\rvert}{\frac{1}{T-m}\sum_{t=m+1}^{T}\lvert y_t-y_{t-m}\rvert}" />

      <H>Exponential smoothing</H>
      <P>
        <b>Simple exponential smoothing</b> (SES) tracks a level that is an exponentially weighted average of
        the past, with smoothing parameter <M tex="\alpha\in(0,1)" /> chosen to minimise the in-sample one-step
        error:
      </P>
      <M block tex="\ell_t=\alpha\,y_t+(1-\alpha)\,\ell_{t-1},\qquad \hat y_{T+k}=\ell_T" />
      <P>
        <b>Holt</b> adds a trend component <M tex="b_t" /> (double exponential smoothing), and <b>Holt-Winters</b>
        adds an additive seasonal component <M tex="s_t" /> with period <M tex="m" />:
      </P>
      <M block tex="\ell_t=\alpha\,(y_t-s_{t-m})+(1-\alpha)(\ell_{t-1}+b_{t-1}),\quad b_t=\beta\,(\ell_t-\ell_{t-1})+(1-\beta)b_{t-1}" />
      <M block tex="s_t=\gamma\,(y_t-\ell_t)+(1-\gamma)s_{t-m},\qquad \hat y_{T+k}=\ell_T+k\,b_T+s_{T+k-m}" />

      <H>Theta</H>
      <P>
        The <b>Theta</b> method (Assimakopoulos and Nikolopoulos, 2000) is equivalent to SES with half the OLS
        drift (Hyndman and Billah, 2003): fit a line with slope <M tex="b" /> by least squares, and forecast
        <M tex="\;\hat y_{T+k}=\ell_T+\tfrac{1}{2}b\,k" />. It is a strong, cheap benchmark that won M3.
      </P>

      <H>Statistical (auto-tuned)</H>
      <UL items={[
        <><b>AutoARIMA</b>: automatic ARIMA/SARIMA order selection (Hyndman-Khandakar) over <M tex="(p,d,q)(P,D,Q)_m" />, with analytic prediction intervals.</>,
        <><b>AutoETS</b>: automatic error/trend/seasonal state-space model selection (the state-space generalisation of Holt-Winters).</>,
        <><b>AutoTheta</b>: the automatic Theta method.</>,
      ]} />
      <P>Implemented via <Ref href="https://github.com/Nixtla/statsforecast">Nixtla statsforecast</Ref>; offline-only (numba), replayed in the browser.</P>

      <H>Machine learning</H>
      <P>
        Gradient boosting on lagged features (the approach that won M5): a LightGBM regressor learns a nonlinear
        map from recent lags <M tex="(y_{t-1},y_{t-2},\dots,y_{t-m})" /> to the next value, forecast recursively.
        Intervals come from the in-sample residual spread. Implemented via
        {' '}<Ref href="https://github.com/Nixtla/mlforecast">mlforecast</Ref> + <Ref href="https://github.com/microsoft/LightGBM">LightGBM</Ref>.
      </P>

      <H>Foundation models (zero-shot)</H>
      <P>
        Pretrained transformers forecast a series with no fitting. ChronoScope runs
        {' '}<Ref href="https://github.com/amazon-science/chronos-forecasting">Amazon Chronos</Ref> offline on
        local checkpoints and bakes its forecasts. This is the tier that, on the seasonal cases, already beats
        the auto-tuned statistical models. The wider landscape (Chronos-2, TimesFM 2.5, Moirai 2.0, TiRex-2,
        Granite TTM, FlowState) is surveyed in the research library; see also the anchor survey
        {' '}<Ref href="https://arxiv.org/abs/2504.04011">arXiv 2504.04011</Ref>.
      </P>

      <H>Probabilistic scoring</H>
      <P>
        Beyond MASE, the interval is scored by the weighted quantile loss (WQL) and by empirical coverage (the
        fraction of truths inside the interval, compared to the nominal level). The pinball loss at level
        <M tex="\,q" /> is <M tex="\rho_q(e)=\max(q\,e,\,(q-1)e)" /> with <M tex="e=y-\hat y_q" />; WQL sums it
        over levels, normalised by <M tex="\sum\lvert y\rvert" />.
      </P>
    </div>
  );
}
