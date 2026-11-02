// In-app Architecture / "How it works" modal (ADR-0058). Five hand-authored, theme-aware SVG diagrams
// meeting the ADR floor: a <style> class vocabulary (not per-element inline attrs), type-coded boxes with
// real code/module paths in monospace, labeled flows, bands/lanes with nested boxes, ~880 wide. Every
// colour is a CSS-variable token from the shell, so the
// diagrams follow light/dark. Content is the current system (grouped workbench views, model roster, preqts
// streaming, the real pipeline stages + two data contracts). Inlined via dangerouslySetInnerHTML by the
// shell's ArchitectureModal, so SVG var() colours resolve.
import type { ArchitectureConfig } from '@fasl-work/caos-app-shell';

// Shared class vocabulary (FLOOR item 1). Prepended to each standalone SVG.
const STYLE = `
  .arch-svg text { font-family: Inter, "Segoe UI", system-ui, sans-serif; }
  .arch-svg .mono { font-family: ui-monospace, Consolas, monospace; }
  .arch-svg .bx { fill: var(--color-surface-2); stroke: var(--color-border); stroke-width: 1.2; }
  .arch-svg .bx-hi { stroke: var(--color-accent); stroke-width: 1.7; }
  .arch-svg .bx-web { stroke: var(--color-accent); stroke-width: 1.7; }
  .arch-svg .bx-compute { stroke: var(--color-warn); stroke-width: 1.7; }
  .arch-svg .bx-store { stroke: var(--color-good); stroke-width: 1.7; }
  .arch-svg .bx-pkg { stroke: var(--color-accent); stroke-width: 1.7; }
  .arch-svg .bx-warn { stroke: var(--color-warn); stroke-width: 1.7; }
  .arch-svg .grp { fill: none; stroke: var(--color-border); stroke-dasharray: 5 4; }
  .arch-svg .ttl { fill: var(--color-fg); font-size: 12.5px; font-weight: 600; }
  .arch-svg .hd { fill: var(--color-fg); font-size: 15px; font-weight: 600; }
  .arch-svg .sub { fill: var(--color-fg-subtle); font-size: 10px; }
  .arch-svg .it { fill: var(--color-fg); font-size: 10.5px; }
  .arch-svg .cd { fill: var(--color-accent); font-size: 9.3px; }
  .arch-svg .mu { fill: var(--color-fg-subtle); font-size: 9.8px; }
  .arch-svg .flow { fill: none; stroke: var(--color-fg-subtle); stroke-width: 1.5; }
  .arch-svg .lbl { fill: var(--color-fg-subtle); font-size: 9.3px; }
`;

// wrap inner markup in a themed <svg> with an arrowhead marker (unique id per diagram)
const svg = (id: string, h: number, inner: string) =>
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 ${h}" width="880" class="arch-svg" role="img">` +
  `<style>${STYLE}</style>` +
  `<defs><marker id="${id}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">` +
  `<path d="M0,0 L8,4 L0,8 z" fill="var(--color-fg-subtle)"/></marker></defs>${inner}</svg>`;

// ---- Tab 1: what the app IS + the design-build lifecycle ----
const APP = svg('cs-a1', 470, `
  <text class="hd" x="20" y="30">ChronoScope · understand a series, then forecast it, honestly</text>
  <rect class="grp" x="14" y="46" width="852" height="196" rx="10"/>
  <text class="sub" x="28" y="66" style="font-weight:600;">WHAT IT IS · the two pillars, per case</text>
  <rect class="bx" x="28" y="78" width="120" height="120" rx="9"/>
  <text class="ttl" x="40" y="100">series in</text>
  <text class="cd mono" x="40" y="118">cases/forecast_cases.py</text>
  <text class="it" x="40" y="140">15 cases:</text>
  <text class="mu" x="40" y="156">synthetic (labelled),</text>
  <text class="mu" x="40" y="170">real (UCI, M4/Monash),</text>
  <text class="mu" x="40" y="184">controls (noise, walk)</text>
  <path class="flow" d="M150,138 L184,138" marker-end="url(#cs-a1)"/>
  <rect class="bx bx-hi" x="186" y="86" width="196" height="46" rx="8"/>
  <text class="ttl" x="198" y="105" style="fill:var(--color-accent);">UNDERSTAND</text>
  <text class="mu" x="198" y="123" style="font-size:9px;">10 families: ADF/STL/PELT/GARCH/DFA</text>
  <rect class="bx bx-hi" x="186" y="146" width="196" height="46" rx="8"/>
  <text class="ttl" x="198" y="165" style="fill:var(--color-accent);">FORECAST</text>
  <text class="mu" x="198" y="183" style="font-size:9px;">22 variants: baselines, models, combinations</text>
  <path class="flow" d="M384,138 L418,138" marker-end="url(#cs-a1)"/>
  <text class="lbl" x="388" y="130">score</text>
  <rect class="bx bx-store" x="420" y="86" width="196" height="106" rx="9"/>
  <text class="ttl" x="432" y="106">honest evaluation</text>
  <text class="cd mono" x="432" y="124">stages/evaluate.py · preqts</text>
  <text class="it" x="432" y="144">rolling-origin backtest,</text>
  <text class="it" x="432" y="160">leakage-safe; + prequential</text>
  <text class="mu" x="432" y="178">MASE/WQL/coverage/MSIS + per-horizon</text>
  <path class="flow" d="M616,138 L650,138" marker-end="url(#cs-a1)"/>
  <rect class="bx" x="652" y="86" width="200" height="106" rx="9"/>
  <text class="ttl" x="664" y="106">compare forecast errors</text>
  <text class="mu" x="664" y="126">inspect diagnostics</text>
  <text class="mu" x="664" y="142">describes each case</text>
  <text class="mu" x="664" y="162">(forecastability atlas);</text>
  <text class="mu" x="664" y="178">adaptive replay intervals</text>

  <rect class="grp" x="14" y="256" width="852" height="196" rx="10"/>
  <text class="sub" x="28" y="276" style="font-weight:600;">RESEARCH AND BUILD WORKFLOW</text>
  ${[
    ['1 research', 'research notes', 'papers, methods,', 'datasets, licenses'],
    ['2 implement', 'chronoscopelab/', 'engines + the', '10-family toolkit'],
    ['3 train + validate', 'stages/train.py', 'GPU deep + foundation;', 'ONNX export + parity'],
    ['4 bake artifact', 'stages/export.py', 'trace v2 + manifest', '+ streaming, seeded'],
    ['5 build SPA', 'copy-data.mjs + vite', 'overlay artifacts;', 'tsc contract gate'],
    ['6 deploy', 'Deploy Pages (Actions)', 'static over the', 'committed artifacts'],
  ].map((b, i) => {
    const x = 28 + i * 138;
    return `<rect class="bx${i === 2 ? ' bx-compute' : i === 3 ? ' bx-store' : ''}" x="${x}" y="292" width="122" height="140" rx="9"/>` +
      `<text class="ttl" x="${x + 12}" y="312" style="font-size:11px;">${b[0]}</text>` +
      `<text class="cd mono" x="${x + 12}" y="330" style="font-size:8.4px;">${b[1]}</text>` +
      `<text class="mu" x="${x + 12}" y="352">${b[2]}</text>` +
      `<text class="mu" x="${x + 12}" y="368">${b[3]}</text>` +
      (i < 5 ? `<path class="flow" d="M${x + 122},362 L${x + 138},362" marker-end="url(#cs-a1)"/>` : '');
  }).join('')}
`);

// ---- Tab 2: the lanes (web / offline / compute) ----
const LANES = svg('cs-a2', 450, `
  <text class="hd" x="20" y="30">Three lanes · what runs WHERE (the core split)</text>

  <rect class="grp" x="14" y="46" width="852" height="120" rx="10"/>
  <rect x="24" y="52" width="9" height="9" rx="2" fill="var(--color-accent)"/>
  <text class="sub" x="40" y="61" style="fill:var(--color-accent);font-weight:600;">WEB · live in your browser (no server)</text>
  <rect class="bx bx-web" x="28" y="74" width="196" height="80" rx="9"/>
  <text class="ttl" x="40" y="94">classical engine</text>
  <text class="cd mono" x="40" y="112">lib/liveEngine.ts</text>
  <text class="mu" x="40" y="130">SES/Holt/HW/Theta, recomputed</text>
  <text class="mu" x="40" y="146">on every knob; parity vs Python</text>
  <rect class="bx bx-web" x="236" y="74" width="196" height="80" rx="9"/>
  <text class="ttl" x="248" y="94">NLinear ONNX</text>
  <text class="cd mono" x="248" y="112">lib/onnxRunner.ts</text>
  <text class="mu" x="248" y="130">a learned model, client-side via</text>
  <text class="mu" x="248" y="146">onnxruntime-web (wasm, 1 thread)</text>
  <rect class="bx bx-web" x="444" y="74" width="196" height="80" rx="9"/>
  <text class="ttl" x="456" y="94">live analysis</text>
  <text class="cd mono" x="456" y="112">lib/tsAnalysis.ts</text>
  <text class="mu" x="456" y="130">ACF/PACF/periodogram/DFA/</text>
  <text class="mu" x="456" y="146">decompose, instant on the knobs</text>
  <rect class="bx bx-web" x="652" y="74" width="200" height="80" rx="9"/>
  <text class="ttl" x="664" y="94">uPlot workbench</text>
  <text class="cd mono" x="664" y="112">render/UPlotChart.tsx</text>
  <text class="mu" x="664" y="130">interactive charts: zoom, crosshair,</text>
  <text class="mu" x="664" y="146">solo a curve, forecast↔errors</text>

  <rect class="grp" x="14" y="180" width="852" height="86" rx="10"/>
  <rect x="24" y="186" width="9" height="9" rx="2" fill="var(--color-good)"/>
  <text class="sub" x="40" y="195" style="fill:var(--color-good);font-weight:600;">REPLAY · committed artifacts the SPA animates (too heavy for the browser)</text>
  <rect class="bx bx-store" x="28" y="208" width="266" height="48" rx="9"/>
  <text class="it" x="40" y="228">trace <tspan class="cd mono">data/derived/<case>/trace.json</tspan></text>
  <text class="mu" x="40" y="246">history + every method's forecast + backtest metrics</text>
  <rect class="bx bx-store" x="304" y="208" width="266" height="48" rx="9"/>
  <text class="it" x="316" y="228">analysis <tspan class="cd mono">analysis.json</tspan></text>
  <text class="mu" x="316" y="246">the 10-family baked verdicts (ADF/KPSS/GARCH/chaos)</text>
  <rect class="bx bx-store" x="580" y="208" width="272" height="48" rx="9"/>
  <text class="it" x="592" y="228">streaming <tspan class="cd mono">streaming.json</tspan></text>
  <text class="mu" x="592" y="246">preqts prequential trajectories (raw vs ACI vs PID)</text>

  <rect class="grp" x="14" y="280" width="852" height="150" rx="10"/>
  <rect x="24" y="286" width="9" height="9" rx="2" fill="var(--color-warn)"/>
  <text class="sub" x="40" y="295" style="fill:var(--color-warn);font-weight:600;">OFFLINE / COMPUTE · the .venv pipeline (never deployed) bakes the artifacts</text>
  <rect class="bx bx-compute" x="28" y="308" width="180" height="106" rx="9"/>
  <text class="ttl" x="40" y="328">statistical + ML</text>
  <text class="cd mono" x="40" y="346">engines/statsforecast_*</text>
  <text class="mu" x="40" y="366">AutoARIMA/ETS/Theta,</text>
  <text class="mu" x="40" y="382">LightGBM (mlforecast)</text>
  <text class="mu" x="40" y="404">CPU, numba</text>
  <rect class="bx bx-compute" x="220" y="308" width="180" height="106" rx="9"/>
  <text class="ttl" x="232" y="328">deep (offline)</text>
  <text class="cd mono" x="232" y="346">engines/neuralforecast_*</text>
  <text class="mu" x="232" y="366">NHITS/DLinear/NLinear,</text>
  <text class="mu" x="232" y="382">MQLoss; + direct-torch</text>
  <text class="mu" x="232" y="404">parity reference</text>
  <rect class="bx bx-compute" x="412" y="308" width="180" height="106" rx="9"/>
  <text class="ttl" x="424" y="328">foundation (offline)</text>
  <text class="cd mono" x="424" y="346">engines/chronos_*, timesfm_*</text>
  <text class="mu" x="424" y="366">Chronos-Bolt + Chronos-2</text>
  <text class="mu" x="424" y="382">+ TimesFM-2.5, zero-shot</text>
  <text class="mu" x="424" y="404">from local checkpoints</text>
  <rect class="bx bx-pkg" x="604" y="308" width="248" height="106" rx="9"/>
  <text class="ttl" x="616" y="328" style="fill:var(--color-accent);">preqts (our PyPI package)</text>
  <text class="cd mono" x="616" y="346">preqts 0.3 · ADR-0061 extraction</text>
  <text class="mu" x="616" y="366">replay + adaptive intervals;</text>
  <text class="mu" x="616" y="382">MSIS + per-horizon curves; the</text>
  <text class="mu" x="616" y="404">streaming bench's spine</text>
  <path class="flow" d="M300,266 L300,306" marker-end="url(#cs-a2)"/>
  <text class="lbl" x="306" y="290">bake ↑ commit</text>
`);

// ---- Tab 3: the web-app flow ----
const FLOW = svg('cs-a3', 430, `
  <text class="hd" x="20" y="30">Web-app flow · source → engines → the grouped eight-view workbench</text>
  <rect class="bx" x="20" y="58" width="150" height="92" rx="9"/>
  <text class="ttl" x="32" y="78">source selector</text>
  <text class="cd mono" x="32" y="96">pages/AppPage.tsx</text>
  <text class="it" x="32" y="116">Baked case (replay)</text>
  <text class="it" x="32" y="132">Synthetic (live knobs)</text>
  <path class="flow" d="M170,104 L206,104" marker-end="url(#cs-a3)"/>
  <text class="lbl" x="174" y="96">case / knobs</text>
  <rect class="bx bx-web" x="208" y="58" width="164" height="92" rx="9"/>
  <text class="ttl" x="220" y="78">engines</text>
  <text class="cd mono" x="220" y="96">liveEngine + onnxRunner</text>
  <text class="mu" x="220" y="116">live: classical + ONNX</text>
  <text class="mu" x="220" y="132">replay: fetch the trace</text>
  <path class="flow" d="M372,104 L408,104" marker-end="url(#cs-a3)"/>
  <rect class="bx bx-hi" x="410" y="52" width="442" height="150" rx="10"/>
  <text class="ttl" x="424" y="72" style="fill:var(--color-accent);">the workbench · grouped interactive views (uPlot)</text>
  <text class="sub" x="424" y="92">UNDERSTAND</text>
  <text class="mu" x="424" y="110">Series · Patterns · Structure · Decompose · Verdicts</text>
  <text class="sub" x="424" y="134">FORECAST</text>
  <text class="mu" x="424" y="152">Forecast (Full/Zoom/Horizon/Errors) · Residuals · Leaderboard · Streaming</text>
  <text class="mu" x="424" y="180">every chart: zoom/pan/crosshair/brush; the legend rail solos a curve; theme-aware</text>

  <rect class="grp" x="20" y="222" width="832" height="184" rx="10"/>
  <text class="sub" x="34" y="242" style="font-weight:600;">HOW THE BUILD STAYS HONEST</text>
  <rect class="bx bx-store" x="34" y="256" width="250" height="130" rx="9"/>
  <text class="ttl" x="46" y="276">artifact overlay</text>
  <text class="cd mono" x="46" y="294">frontend/copy-data.mjs</text>
  <text class="mu" x="46" y="314">prebuild copies data/derived +</text>
  <text class="mu" x="46" y="330">manifests into public/; the SPA</text>
  <text class="mu" x="46" y="346">fetches them (never hand-typed)</text>
  <text class="mu" x="46" y="370">+ inlines the pyodide sources</text>
  <rect class="bx bx-warn" x="300" y="256" width="250" height="130" rx="9"/>
  <text class="ttl" x="312" y="276" style="fill:var(--color-warn);">contract-type gate</text>
  <text class="cd mono" x="312" y="294">lib/contract.types.ts</text>
  <text class="mu" x="312" y="314">the Python trace/manifest shapes,</text>
  <text class="mu" x="312" y="330">mirrored in TS; a drift fails</text>
  <text class="mu" x="312" y="346">tsc, so the build cannot ship an</text>
  <text class="mu" x="312" y="370">artifact the UI would misread</text>
  <rect class="bx" x="566" y="256" width="286" height="130" rx="9"/>
  <text class="ttl" x="578" y="276">deploy</text>
  <text class="cd mono" x="578" y="294">.github/workflows/deploy-pages.yml</text>
  <text class="mu" x="578" y="314">Actions builds the SPA over the</text>
  <text class="mu" x="578" y="330">committed artifacts and publishes</text>
  <text class="mu" x="578" y="346">to Pages; CI drift-gate first</text>
  <text class="cd mono" x="578" y="370">scripts/check_artifacts.py</text>
  <path class="flow" d="M284,321 L298,321" marker-end="url(#cs-a3)"/>
  <path class="flow" d="M550,321 L564,321" marker-end="url(#cs-a3)"/>
`);

// ---- Tab 4: the science ----
const SCIENCE = svg('cs-a4', 470, `
  <text class="hd" x="20" y="30">Forecast methods and their evaluation protocols</text>
  <rect class="grp" x="14" y="46" width="852" height="150" rx="10"/>
  <text class="sub" x="28" y="66" style="font-weight:600;">THE LADDER · transparent baselines through pretrained models, each emitting a point path + a prediction interval</text>
  ${[
    ['smoothing', 'references', 'SeasonalNaive reference,', 'SES/Holt/HoltWinters, Theta'],
    ['statistical', 'auto-tuned', 'AutoARIMA / AutoETS /', 'AutoTheta (statsforecast)'],
    ['ml', 'boosting', 'LightGBM on lag/date', 'features (mlforecast)'],
    ['deep', 'neural', 'NHITS/DLinear/NLinear', '(neuralforecast)'],
    ['foundation', 'zero-shot', 'Chronos-Bolt, Chronos-2,', 'TimesFM-2.5 (pretrained)'],
  ].map((b, i) => {
    const x = 28 + i * 167;
    const cls = i >= 3 ? ' bx-compute' : '';
    return `<rect class="bx${cls}" x="${x}" y="78" width="151" height="108" rx="9"/>` +
      `<text class="ttl" x="${x + 12}" y="98" style="font-size:11px;">${b[0]}</text>` +
      `<text class="sub" x="${x + 12}" y="114">${b[1]}</text>` +
      `<text class="mu" x="${x + 12}" y="140">${b[2]}</text>` +
      `<text class="mu" x="${x + 12}" y="156">${b[3]}</text>` +
      (i < 4 ? `<path class="flow" d="M${x + 151},132 L${x + 167},132" marker-end="url(#cs-a4)"/>` : '');
  }).join('')}

  <rect class="grp" x="14" y="210" width="418" height="242" rx="10"/>
  <text class="sub" x="28" y="230" style="font-weight:600;">DIAGNOSIS · the 10-family toolkit (analysis/*.py)</text>
  <text class="it" x="28" y="252">stationarity · autocorrelation · seasonality</text>
  <text class="it" x="28" y="270">filters/decomposition · change-points</text>
  <text class="it" x="28" y="288">volatility (GARCH) · distribution</text>
  <text class="it" x="28" y="306">fractal/memory (Hurst, DFA, MF-DFA)</text>
  <text class="it" x="28" y="324">nonlinear/chaos (Lyapunov, 0-1, RQA) · causality</text>
  <text class="mu" x="28" y="350" style="fill:var(--color-accent);">each honesty-gated:</text>
  <text class="mu" x="28" y="368">surrogate test before claiming chaos;</text>
  <text class="mu" x="28" y="386">length gate for nonlinear stats;</text>
  <text class="mu" x="28" y="404">I(1) gate before cointegration.</text>
  <text class="mu" x="28" y="430">Diagnostics describe case structure.</text>

  <rect class="grp" x="446" y="210" width="420" height="242" rx="10"/>
  <text class="sub" x="460" y="230" style="font-weight:600;">EVALUATION · separate target-block and replay studies</text>
  <rect class="bx" x="460" y="242" width="392" height="74" rx="9"/>
  <text class="ttl" x="472" y="262">declared common or rolling target blocks</text>
  <text class="mu" x="472" y="282">each fit uses its available prefix; future targets</text>
  <text class="mu" x="472" y="298">are scored under that study's declared protocol</text>
  <rect class="bx bx-pkg" x="460" y="326" width="392" height="60" rx="9"/>
  <text class="ttl" x="472" y="346" style="fill:var(--color-accent);">separate prequential prefix replay</text>
  <text class="mu" x="472" y="366">predict, score, ingest; interval state persists</text>
  <text class="mu" x="472" y="380" style="font-size:9px;">one-step intervals; controller state persists across cutoffs</text>
  <text class="mu" x="460" y="408" style="fill:var(--color-accent);">metrics:</text>
  <text class="mu" x="502" y="408">MASE · WQL · coverage · MSIS · per-horizon curve</text>
  <text class="mu" x="460" y="428">a control that beats the naive by a lot is a red flag,</text>
  <text class="mu" x="460" y="444">not a triumph; the negative controls stay visible.</text>
`);

// ---- Tab 5: the data contracts / design ----
const CONTRACTS = svg('cs-a5', 430, `
  <text class="hd" x="20" y="30">Data contracts · two validated boundaries bracket a seeded pipeline</text>

  <rect class="bx bx-store" x="20" y="56" width="200" height="120" rx="9"/>
  <text class="ttl" x="32" y="76" style="fill:var(--color-good);">CONTRACT 1 · ingestion</text>
  <text class="cd mono" x="32" y="94">io/contract.py · io/schema.py</text>
  <text class="mu" x="32" y="114">a valid series: long-format</text>
  <text class="mu" x="32" y="130">id/timestamp/value + an explicit</text>
  <text class="mu" x="32" y="146">missing/outlier policy, so the tool</text>
  <text class="mu" x="32" y="162">accepts external data, not just cases</text>
  <path class="flow" d="M220,116 L256,116" marker-end="url(#cs-a5)"/>
  <text class="lbl" x="224" y="108">valid obs</text>

  <rect class="bx bx-hi" x="258" y="56" width="340" height="120" rx="10"/>
  <text class="ttl" x="270" y="76" style="fill:var(--color-accent);">staged computation with source identities</text>
  <text class="cd mono" x="270" y="94">chronoscopelab/pipeline.py</text>
  <text class="mu" x="270" y="116">preprocess → feature_extraction → train → infer</text>
  <text class="mu" x="270" y="134">→ evaluate → export · seeded numerical fits</text>
  <text class="mu" x="270" y="158">source, package and checkpoint hashes retained;</text>
  <text class="mu" x="270" y="172" style="font-size:9px;">timings remain separate. Tests redirect generated artifacts.</text>
  <path class="flow" d="M598,116 L634,116" marker-end="url(#cs-a5)"/>
  <text class="lbl" x="602" y="108">baked</text>

  <rect class="bx bx-store" x="636" y="56" width="220" height="120" rx="9"/>
  <text class="ttl" x="648" y="76" style="fill:var(--color-good);">CONTRACT 2 · artifact</text>
  <text class="it" x="648" y="98">trace <tspan class="cd mono">chronoscope.trace/v2</tspan></text>
  <text class="it" x="648" y="116">manifest <tspan class="cd mono">.manifest/v1</tspan></text>
  <text class="it" x="648" y="134">analysis, streaming, index</text>
  <text class="cd mono" x="648" y="154">core/trace.py · core/manifest.py</text>
  <text class="mu" x="648" y="170">mirrored in TS → tsc gate</text>

  <rect class="grp" x="20" y="200" width="411" height="206" rx="10"/>
  <text class="sub" x="34" y="220" style="font-weight:600;">THE LANE GATE · core/gate.py</text>
  <rect class="bx bx-web" x="34" y="234" width="180" height="72" rx="9"/>
  <text class="ttl" x="46" y="254" style="fill:var(--color-accent);">LIVE</text>
  <text class="mu" x="46" y="274">cheap + pure-numpy/ONNX:</text>
  <text class="mu" x="46" y="290">safe to recompute in the browser</text>
  <rect class="bx bx-compute" x="228" y="234" width="188" height="72" rx="9"/>
  <text class="ttl" x="240" y="254" style="fill:var(--color-warn);">PRECOMPUTE</text>
  <text class="mu" x="240" y="274">heavy offline (models/AutoARIMA):</text>
  <text class="mu" x="240" y="290">baked offline, replayed as artifact</text>
  <text class="mu" x="34" y="332">a measured verdict per method, recorded in the manifest;</text>
  <text class="mu" x="34" y="350">the manifest lane must match the gate lane (checked in CI).</text>
  <text class="mu" x="34" y="376" style="fill:var(--color-good);">license guard:</text>
  <text class="mu" x="112" y="376">a local-only-licensed source ships</text>
  <text class="mu" x="34" y="394">aggregate metrics only (the raw excerpt is redacted).</text>

  <rect class="grp" x="443" y="200" width="413" height="206" rx="10"/>
  <text class="sub" x="457" y="220" style="font-weight:600;">DRIFT GATE (CI) · scripts/check_artifacts.py</text>
  <text class="it" x="457" y="244">the index references every case;</text>
  <text class="it" x="457" y="262">each manifest ↔ artifact byte-size matches;</text>
  <text class="it" x="457" y="280">the lane matches the gate verdict;</text>
  <text class="it" x="457" y="298">the ladder is complete (≥ 15 methods/trace).</text>
  <text class="mu" x="457" y="324" style="fill:var(--color-warn);">why the last one:</text>
  <text class="mu" x="457" y="342">a test that regenerated artifacts on a lighter engine</text>
  <text class="mu" x="457" y="358">set once downgraded the committed bake to 9 methods</text>
  <text class="mu" x="457" y="374">and it shipped; the completeness floor makes a</text>
  <text class="mu" x="457" y="390">CPU-lane clobber fail CI instead of reaching prod.</text>
`);

export const architecture: ArchitectureConfig = {
  title_en: 'Architecture / How it works',
  title_es: 'Arquitectura / Cómo funciona',
  tabs: [
    {
      id: 'app', en: 'The app', es: 'La app', svg: APP,
      body_en: "ChronoScope combines ten diagnostic families with a freshly executed common final-holdout comparison of 22 forecast variants. The earlier archived-path comparison remains separately available. Fixed ContextMemory retains its unfavorable recency-ablation result. A further twelve-method study evaluates ContextMemoryCV and ValidationMix on complete M4 Weekly and M3 Monthly inventories; both improve point error against RecencyMean on the admitted collections, while AutoTheta remains stronger on monthly point error and interval scores. The streaming study separately replays adaptive intervals. These are bounded research outcomes.",
      body_es: "ChronoScope combina diez familias diagnósticas y una comparación de 22 variantes recién ejecutadas sobre los mismos bloques finales. La comparación anterior de trayectorias archivadas se conserva separadamente. ContextMemory fijo mantiene su resultado desfavorable frente a la ablación por recencia. Otro estudio de doce métodos evalúa ContextMemoryCV y ValidationMix en los inventarios completos de M4 Weekly y M3 Monthly: ambas variantes mejoran el error puntual de RecencyMean en las colecciones admitidas; AutoTheta conserva menor error mensual y mejores puntuaciones de intervalos. El estudio de streaming reproduce intervalos adaptativos como evidencia separada. Son resultados acotados de investigación.",
    },
    {
      id: 'lanes', en: 'Lanes', es: 'Carriles', svg: LANES,
      body_en: "The browser computes lightweight classical forecasts, small ONNX NLinear inference and lightweight diagnostics. Heavy engine fitting runs offline. The default fifteen-case comparison stores fresh execution of all 22 configurations with package, checkpoint and source identities; the earlier archived-path experiment remains separate. The twelve-method weekly/monthly combination study also runs offline and serves a compact index plus the selected series document, exposing expert weights, validation choices, targets and scores. The adaptive-interval experiment is a separate prefix replay; native stateful updates and normalized runtime advantages are outside its evidence.",
      body_es: "El navegador calcula pronósticos clásicos ligeros, inferencia ONNX de un pequeño NLinear y diagnósticos ligeros. Los ajustes pesados se ejecutan offline. La comparación predeterminada de quince casos conserva la ejecución nueva de las 22 configuraciones con identidades de paquetes, pesos y fuentes; el experimento anterior con trayectorias archivadas permanece separado. El estudio semanal y mensual de doce métodos también se ejecuta offline y sirve un índice compacto y el documento de la serie elegida, mostrando pesos de expertos, decisiones de validación, objetivos y puntuaciones. Los intervalos adaptativos se evalúan en una reproducción separada de prefijos; su evidencia no incluye actualizaciones nativas con estado ni ventajas de tiempo normalizadas.",
    },
    {
      id: 'flow', en: 'Web flow', es: 'Flujo web', svg: FLOW,
      body_en: "The App workbench groups series observations, original-axis patterns, structure, decomposition and verdicts separately from forecast paths, residuals, leaderboards and streaming results. The forecast chart offers Full, Zoom, Horizon and Errors modes. Users choose committed cases or interactive synthetic controls. A separate experiment view explores combination studies by collection, series, origin and method. Builds replace public data from canonical artifacts; normative schemas generate TypeScript types, and independent numerical tests check displayed paths.",
      body_es: "El entorno App agrupa observaciones, patrones en el eje original, estructura, descomposición y veredictos, separados de trayectorias de pronóstico, residuos, tablas y streaming. El gráfico de pronósticos ofrece vistas Completa, Zoom, Horizonte y Errores. Se eligen casos comprometidos o controles sintéticos interactivos. Otra vista experimental explora combinaciones por colección, serie, origen y método. El build reemplaza datos públicos desde artefactos canónicos; los esquemas normativos generan tipos TypeScript y pruebas numéricas independientes verifican las trayectorias.",
    },
    {
      id: 'science', en: 'The science', es: 'La ciencia', svg: SCIENCE,
      body_en: "The fifteen-case roster includes SeasonalNaive, SES, Holt, HoltWinters, Theta, automatic statistical, tree, neural and pretrained methods. Separate experiments evaluate fixed ContextMemory ablations, temporally validated combinations on weekly/monthly collections, prefix-feature associations and held-out method selection on M4 Daily, and one-step adaptive intervals through prefix replay. ContextMemoryCV and ValidationMix improve the recency control on both external collections, while stronger automatic-statistical and interval-score outcomes remain visible. Original-axis patterns, multiscale complexity and seeded nonlinear estimates describe case structure. Scores and associations do not establish population superiority, calibrated uncertainty or a causal forecasting mechanism.",
      body_es: "El conjunto de quince casos incluye SeasonalNaive, SES, Holt, HoltWinters, Theta, modelos estadísticos automáticos, árboles, redes y modelos preentrenados. Experimentos separados evalúan ablaciones de ContextMemory fijo, combinaciones con validación temporal en colecciones semanales y mensuales, asociaciones y selección fuera de muestra en M4 Daily, e intervalos adaptativos de un paso mediante reproducción de prefijos. ContextMemoryCV y ValidationMix mejoran el control de recencia en ambas colecciones externas; se conservan los mejores resultados estadísticos automáticos y de intervalos. Los patrones en el eje original, la complejidad multiescala y las estimaciones no lineales con semilla describen los casos. Estos resultados no prueban superioridad poblacional, incertidumbre calibrada ni un mecanismo causal.",
    },
    {
      id: 'contracts', en: 'Data contracts', es: 'Contratos de datos', svg: CONTRACTS,
      body_en: "Ingestion and artifact interfaces bracket the pipeline. Twelve catalog boundaries cover cases, forecasts, diagnostics, streaming, model metadata, corpus studies and combination records. Normative JSON Schemas generate browser TypeScript types; admission independently checks source identities, temporal eligibility, expert mixtures and scores. Seeded numerical diagnostics are tested for repeatability, while timing records and runtime-dependent model fitting retain separate limits. Tests redirect generated output away from canonical data. License checks govern redistribution, and completeness checks reject partial inventories or degraded model rosters before publication.",
      body_es: "Las interfaces de ingesta y artefactos delimitan el pipeline. Doce límites del catálogo cubren casos, pronósticos, diagnósticos, streaming, metadatos de modelos, estudios de corpus y combinaciones. Los esquemas JSON normativos generan tipos TypeScript; la admisión verifica independientemente fuentes, elegibilidad temporal, mezclas y puntuaciones. Se prueba la repetibilidad de diagnósticos numéricos con semilla; los tiempos y ajustes dependientes del entorno mantienen límites separados. Las pruebas redirigen salidas fuera de los datos canónicos. Las licencias gobiernan la redistribución y las comprobaciones de completitud rechazan inventarios parciales o conjuntos de modelos degradados antes de publicar.",
    },
  ],
};
