import { H, Lead, P, Ref, UL } from '../components/doc';

export function Implementation() {
  return (
    <div>
      <H>Implementation</H>
      <Lead>
        ChronoScope is an offline-pipeline-heavy, static, deterministic-replay product: the heavy processing
        happens offline and bakes compact artifacts, and the web app replays them or recomputes the light tier
        live. No server.
      </Lead>

      <H>The two data contracts</H>
      <UL items={[
        'Ingestion contract (raw to pipeline): a long-format schema (series id, timestamp, value, optional covariates) with a missing/outlier policy. A series is accepted only if it passes; this is what lets the tool be pointed at new data, not just the built-in cases.',
        'Artifact contract (pipeline to web): every run writes a compact trace and a manifest (series descriptors, seed, engine, byte size, the lane/gate verdict, the per-method backtest). A TypeScript type mirrors the schema, so any drift fails the build.',
      ]} />

      <H>The staged pipeline</H>
      <P>
        A named, seeded, tested pipeline runs per case: preprocess (apply the ingestion contract), feature
        extraction (a series fingerprint), train (learn a global method selector), infer (fit every method and
        forecast), evaluate (the leakage-safe backtest), export (the artifact + manifest). The engines are the
        real libraries, pinned and documented, not toy substitutes.
      </P>

      <H>The three lanes</H>
      <UL items={[
        'Live (in-browser): the classical ladder is reimplemented in TypeScript and recomputes instantly as you turn the knobs. It is parity-checked against the offline Python engine, so "live" computes the same thing the pipeline does.',
        'Replay (baked): the statistical, ML, and foundation tiers are too heavy for the browser, so their forecasts and metrics are baked offline and replayed.',
        'Offline (hard processing): the pipeline runs statsforecast, LightGBM, and torch + Chronos on local checkpoints, then bakes the artifacts. A measured gate decides which cases can run live versus replay.',
      ]} />

      <H>Evaluation library</H>
      <P>
        The backtest is scored by <Ref href="https://github.com/fsantibanezleal/CAOS_PreqTS">preqts</Ref>, a
        prequential (test-then-update) evaluation library extracted from this product. It fills a real gap: no
        public harness evaluates a stateful, constant-cost forecaster over a stream, which is exactly what the
        streaming-native foundation models need. The streaming tab (a later slice) surfaces its curves.
      </P>

      <H>The learned tier, live (planned)</H>
      <P>
        A small deep model (DLinear or an N-HiTS-style network) is trained offline and exported to ONNX, then
        run in the browser with onnxruntime-web, so the app can test a learned method live, not only replay it.
        The heavy foundation models stay replay-only.
      </P>

      <H>Deploy</H>
      <P>
        Static build (Vite) deployed to GitHub Pages at chronoscope.fasl-work.com. CI builds the SPA over the
        committed, foundation-baked artifacts rather than regenerating them (CI has no GPU or checkpoints), so
        the deployed site shows the full ladder.
      </P>
    </div>
  );
}
