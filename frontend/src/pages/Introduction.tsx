import { H, Lead, P, UL } from '../components/doc';

export function Introduction() {
  return (
    <div>
      <H>Introduction</H>
      <Lead>
        ChronoScope is an interactive atlas of time-series forecasting: it puts the whole method ladder, from
        transparent classical baselines through statistical and machine-learning methods to zero-shot
        foundation models, side by side on the same series and the same leakage-safe backtest, so you can see
        what each family is good at and where it breaks.
      </Lead>

      <H>The problem</H>
      <P>
        A forecast turns a history of observations into a distribution over future values. Two facts make it
        harder than a single accuracy number suggests. First, real forecasting is streaming: new observations
        arrive continuously, covariates interact, some are known into the future, and a model should update its
        prediction efficiently rather than re-reading everything. Second, there is no free lunch: no single
        method dominates across seasonal, trending, intermittent, noisy, and regime-changing series. A useful
        tool has to make both facts visible.
      </P>

      <H>What ChronoScope is</H>
      <UL items={[
        'A workbench: adjust a synthetic series (or pick a real one) and watch the classical methods recompute live in your browser, then compare them against the heavier tiers replayed from an offline backtest.',
        'A guide: each method family is documented with its equations, its assumptions, and when it works or fails.',
        'A benchmark: every method is scored on the same rolling-origin, leakage-safe protocol, with honest numbers taken from committed artifacts, never hand-typed.',
      ]} />

      <H>What it is not</H>
      <UL items={[
        'Not a leaderboard clone: it links the live public leaderboards (GIFT-Eval, fev-bench) rather than freezing ranks that move monthly.',
        'Not a black box: every result is measured against a transparent baseline, and the classical tier computed in your browser is parity-checked against the offline engine.',
        'Not a claim of universal accuracy: the honest story is that different series call for different methods.',
      ]} />

      <H>Who it is for</H>
      <P>
        Practitioners choosing a forecasting method, students learning the landscape from baselines to
        foundation models, and researchers who want a reproducible harness to compare methods, including the
        streaming regime that public batch benchmarks do not cover.
      </P>
    </div>
  );
}
