import { H, Lead, P, UL } from '../components/doc';

export function Experiments() {
  return (
    <div>
      <H>Experiments</H>
      <Lead>
        Every method is scored on the same leakage-safe, rolling-origin backtest, so the comparison is fair and
        no method sees its own test point.
      </Lead>

      <H>The backtest protocol</H>
      <UL items={[
        'Rolling origin: the forecast origin moves forward over the history; at each origin a method forecasts the horizon and is scored against the truth that follows. Every window is out-of-sample.',
        'Fixed scale: MASE and the scaled quantile loss use the in-sample seasonal-naive error computed once from the warmup window, so every window and every method share one denominator.',
        'Held-out display block: the final horizon of each series is held out as the truth shown next to the forecast in the App, so the displayed forecast is genuinely out-of-sample too.',
        'Bounded cost per tier: cheap methods get many windows; expensive ones (AutoARIMA, LightGBM, the foundation model) get a smaller window budget and a context cap, so the offline bake stays practical.',
      ]} />

      <H>The case coverage matrix</H>
      <P>
        The built-in cases are chosen to span the axes where methods differ, plus deliberate honesty controls:
      </P>
      <UL items={[
        'Seasonal (strong daily cycle): seasonal and foundation methods should win.',
        'Trend + seasonal: the auto-tuned statistical models tend to lead.',
        'Intermittent demand: mostly zeros; smooth methods struggle.',
        'Near-random-walk: an honesty case where beating the naive is essentially noise.',
        'Real electricity load (a UCI series, hourly): real data is harder and messier.',
        'White noise: a control where nothing should beat the baseline by much.',
      ]} />

      <H>Metrics</H>
      <UL items={[
        'MASE for point accuracy (below 1 beats the seasonal-naive baseline).',
        'Weighted quantile loss (WQL) for the full quantile forecast.',
        'Empirical interval coverage against the nominal level (the calibration honesty check).',
      ]} />

      <H>Honesty</H>
      <P>
        The near-random-walk and white-noise controls exist so that a suspiciously large skill gap would flag a
        leak. Numbers come from the committed artifacts, never hand-typed. Public long-horizon benchmarks are
        known to be fragile (the drop-last batch trick, tiny test sets), so ChronoScope reports its own backtest
        and links the live public leaderboards rather than freezing ranks.
      </P>
    </div>
  );
}
