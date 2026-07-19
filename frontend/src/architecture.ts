// In-app Architecture / "How it works" modal (ADR-0058). Five hand-authored, theme-aware SVG diagrams
// meeting the ADR FLOOR: a <style> class vocabulary (not per-element inline attrs), type-coded boxes with
// real code/module paths in monospace, labeled flows, bands/lanes with nested boxes, ~880 wide. Every
// colour is a CSS-variable token (the shell --color-* + ChronoScope's --cs-* diagram tokens), so the
// diagrams follow light/dark. Content is the CURRENT system (10-tab workbench, 19-method ladder, preqts
// streaming, the real pipeline stages + two data contracts). Inlined via dangerouslySetInnerHTML by the
// shell's ArchitectureModal, so SVG var() colours resolve.
import type { ArchitectureConfig } from '@fasl-work/caos-app-shell';

// Shared class vocabulary (FLOOR item 1). Prepended to each standalone SVG.
const STYLE = `
  .arch-svg text { font-family: Inter, "Segoe UI", system-ui, sans-serif; }
  .arch-svg .mono { font-family: ui-monospace, Consolas, monospace; }
  .arch-svg .bx { fill: var(--color-surface-2); stroke: var(--color-border); stroke-width: 1.2; }
  .arch-svg .bx-hi { stroke: var(--color-accent); stroke-width: 1.7; }
  .arch-svg .bx-web { stroke: var(--cs-web); stroke-width: 1.7; }
  .arch-svg .bx-compute { stroke: var(--cs-compute); stroke-width: 1.7; }
  .arch-svg .bx-store { stroke: var(--cs-store); stroke-width: 1.7; }
  .arch-svg .bx-pkg { stroke: var(--cs-pkg); stroke-width: 1.7; }
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
  <text class="hd" x="20" y="30">ChronoScope &#8212; understand a series, then forecast it, honestly</text>
  <rect class="grp" x="14" y="46" width="852" height="196" rx="10"/>
  <text class="sub" x="28" y="66" style="font-weight:600;">WHAT IT IS &#183; the two pillars, per case</text>
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
  <text class="mu" x="198" y="183" style="font-size:9px;">19 methods: naive &#8594; ARIMA &#8594; NHITS &#8594; Chronos</text>
  <path class="flow" d="M384,138 L418,138" marker-end="url(#cs-a1)"/>
  <text class="lbl" x="388" y="130">score</text>
  <rect class="bx bx-store" x="420" y="86" width="196" height="106" rx="9"/>
  <text class="ttl" x="432" y="106">honest evaluation</text>
  <text class="cd mono" x="432" y="124">stages/evaluate.py &#183; preqts</text>
  <text class="it" x="432" y="144">rolling-origin backtest,</text>
  <text class="it" x="432" y="160">leakage-safe; + prequential</text>
  <text class="mu" x="432" y="178">MASE/WQL/coverage/MSIS + per-horizon</text>
  <path class="flow" d="M616,138 L650,138" marker-end="url(#cs-a1)"/>
  <rect class="bx" x="652" y="86" width="200" height="106" rx="9"/>
  <text class="ttl" x="664" y="106">where each family wins</text>
  <text class="mu" x="664" y="126">and why: the diagnosis</text>
  <text class="mu" x="664" y="142">explains the leaderboard</text>
  <text class="mu" x="664" y="162">(forecastability atlas);</text>
  <text class="mu" x="664" y="178">calibrated intervals (ACI/PID)</text>

  <rect class="grp" x="14" y="256" width="852" height="196" rx="10"/>
  <text class="sub" x="28" y="276" style="font-weight:600;">DESIGN-BUILD LIFECYCLE &#183; how it was built (deep-research first, no shortcuts)</text>
  ${[
    ['1 research', 'wip/*.md dossiers', 'SOTA, papers,', 'datasets, licenses'],
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
  <text class="hd" x="20" y="30">Three lanes &#8212; what runs WHERE (the core split)</text>

  <rect class="grp" x="14" y="46" width="852" height="120" rx="10"/>
  <rect x="24" y="52" width="9" height="9" rx="2" fill="var(--cs-web)"/>
  <text class="sub" x="40" y="61" style="fill:var(--cs-web);font-weight:600;">WEB &#183; live in your browser (no server)</text>
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
  <text class="mu" x="664" y="146">solo a curve, forecast&#8596;errors</text>

  <rect class="grp" x="14" y="180" width="852" height="86" rx="10"/>
  <rect x="24" y="186" width="9" height="9" rx="2" fill="var(--cs-store)"/>
  <text class="sub" x="40" y="195" style="fill:var(--cs-store);font-weight:600;">REPLAY &#183; committed artifacts the SPA animates (too heavy for the browser)</text>
  <rect class="bx bx-store" x="28" y="208" width="266" height="48" rx="9"/>
  <text class="it" x="40" y="228">trace <tspan class="cd mono">data/derived/&lt;case&gt;/trace.json</tspan></text>
  <text class="mu" x="40" y="246">history + every method's forecast + backtest metrics</text>
  <rect class="bx bx-store" x="304" y="208" width="266" height="48" rx="9"/>
  <text class="it" x="316" y="228">analysis <tspan class="cd mono">analysis.json</tspan></text>
  <text class="mu" x="316" y="246">the 10-family baked verdicts (ADF/KPSS/GARCH/chaos)</text>
  <rect class="bx bx-store" x="580" y="208" width="272" height="48" rx="9"/>
  <text class="it" x="592" y="228">streaming <tspan class="cd mono">streaming.json</tspan></text>
  <text class="mu" x="592" y="246">preqts prequential trajectories (raw vs ACI vs PID)</text>

  <rect class="grp" x="14" y="280" width="852" height="150" rx="10"/>
  <rect x="24" y="286" width="9" height="9" rx="2" fill="var(--cs-compute)"/>
  <text class="sub" x="40" y="295" style="fill:var(--cs-compute);font-weight:600;">OFFLINE / COMPUTE &#183; the .venv pipeline (never deployed) bakes the artifacts</text>
  <rect class="bx bx-compute" x="28" y="308" width="180" height="106" rx="9"/>
  <text class="ttl" x="40" y="328">statistical + ML</text>
  <text class="cd mono" x="40" y="346">engines/statsforecast_*</text>
  <text class="mu" x="40" y="366">AutoARIMA/ETS/Theta,</text>
  <text class="mu" x="40" y="382">LightGBM (mlforecast)</text>
  <text class="mu" x="40" y="404">CPU, numba</text>
  <rect class="bx bx-compute" x="220" y="308" width="180" height="106" rx="9"/>
  <text class="ttl" x="232" y="328">deep (GPU)</text>
  <text class="cd mono" x="232" y="346">engines/neuralforecast_*</text>
  <text class="mu" x="232" y="366">NHITS/DLinear/NLinear,</text>
  <text class="mu" x="232" y="382">MQLoss; + direct-torch</text>
  <text class="mu" x="232" y="404">parity reference</text>
  <rect class="bx bx-compute" x="412" y="308" width="180" height="106" rx="9"/>
  <text class="ttl" x="424" y="328">foundation (GPU)</text>
  <text class="cd mono" x="424" y="346">engines/chronos_*, timesfm_*</text>
  <text class="mu" x="424" y="366">Chronos-Bolt + Chronos-2</text>
  <text class="mu" x="424" y="382">+ TimesFM-2.5, zero-shot</text>
  <text class="mu" x="424" y="404">from local checkpoints</text>
  <rect class="bx bx-pkg" x="604" y="308" width="248" height="106" rx="9"/>
  <text class="ttl" x="616" y="328" style="fill:var(--cs-pkg);">preqts (our PyPI package)</text>
  <text class="cd mono" x="616" y="346">preqts 0.3 &#183; ADR-0061 extraction</text>
  <text class="mu" x="616" y="366">prequential eval + ACI/Conformal-PID;</text>
  <text class="mu" x="616" y="382">MSIS + per-horizon curves; the</text>
  <text class="mu" x="616" y="404">streaming bench's spine</text>
  <path class="flow" d="M300,266 L300,306" marker-end="url(#cs-a2)"/>
  <text class="lbl" x="306" y="290">bake &#8593; commit</text>
`);

// ---- Tab 3: the web-app flow ----
const FLOW = svg('cs-a3', 430, `
  <text class="hd" x="20" y="30">Web-app flow &#8212; source &#8594; engines &#8594; the 10-tab workbench</text>
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
  <text class="ttl" x="424" y="72" style="fill:var(--color-accent);">the workbench &#183; 10 interactive tabs (uPlot)</text>
  <text class="sub" x="424" y="92">UNDERSTAND</text>
  <text class="mu" x="424" y="110">Series &#183; Structure (ACF/PACF/spectrum) &#183; Decompose &#183; Verdicts</text>
  <text class="sub" x="424" y="134">FORECAST</text>
  <text class="mu" x="424" y="152">Forecast (&#8596; Errors) &#183; Zoom &#183; Horizon &#183; Residuals &#183; Leaderboard &#183; Streaming</text>
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
  <text class="hd" x="20" y="30">The science &#8212; the 19-method ladder, scored by one honest protocol</text>
  <rect class="grp" x="14" y="46" width="852" height="150" rx="10"/>
  <text class="sub" x="28" y="66" style="font-weight:600;">THE LADDER &#183; transparent baseline &#8594; SOTA, each emitting a point path + a prediction interval</text>
  ${[
    ['classical', 'baselines', 'SeasonalNaive (MASE=1),', 'SES/Holt/HoltWinters, Theta'],
    ['statistical', 'auto-tuned', 'AutoARIMA / AutoETS /', 'AutoTheta (statsforecast)'],
    ['ml', 'boosting', 'LightGBM on lag/date', 'features (mlforecast)'],
    ['deep', 'neural', 'NHITS/DLinear/NLinear', '(neuralforecast, GPU)'],
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
  <text class="sub" x="28" y="230" style="font-weight:600;">DIAGNOSIS &#183; the 10-family toolkit (analysis/*.py)</text>
  <text class="it" x="28" y="252">stationarity &#183; autocorrelation &#183; seasonality</text>
  <text class="it" x="28" y="270">filters/decomposition &#183; change-points</text>
  <text class="it" x="28" y="288">volatility (GARCH) &#183; distribution</text>
  <text class="it" x="28" y="306">fractal/memory (Hurst, DFA, MF-DFA)</text>
  <text class="it" x="28" y="324">nonlinear/chaos (Lyapunov, 0-1, RQA) &#183; causality</text>
  <text class="mu" x="28" y="350" style="fill:var(--color-accent);">each honesty-gated:</text>
  <text class="mu" x="28" y="368">surrogate test before claiming chaos;</text>
  <text class="mu" x="28" y="386">length gate for nonlinear stats;</text>
  <text class="mu" x="28" y="404">I(1) gate before cointegration.</text>
  <text class="mu" x="28" y="430">The diagnosis explains which family wins.</text>

  <rect class="grp" x="446" y="210" width="420" height="242" rx="10"/>
  <text class="sub" x="460" y="230" style="font-weight:600;">EVALUATION &#183; leakage-safe, and the novel piece</text>
  <rect class="bx" x="460" y="242" width="392" height="74" rx="9"/>
  <text class="ttl" x="472" y="262">rolling-origin backtest</text>
  <text class="mu" x="472" y="282">each cutoff fits only on history up to it, predicts</text>
  <text class="mu" x="472" y="298">the full horizon out-of-sample; the cutoff advances</text>
  <rect class="bx bx-pkg" x="460" y="326" width="392" height="60" rx="9"/>
  <text class="ttl" x="472" y="346" style="fill:var(--cs-pkg);">streaming (prequential) &#183; preqts</text>
  <text class="mu" x="472" y="366">predict &#8594; observe &#8594; update, state carried; ACI + Conformal-PID</text>
  <text class="mu" x="472" y="380" style="font-size:9px;">recalibrate the interval online, per horizon (the atlas's novel piece)</text>
  <text class="mu" x="460" y="408" style="fill:var(--color-accent);">metrics:</text>
  <text class="mu" x="502" y="408">MASE &#183; WQL &#183; coverage &#183; MSIS &#183; per-horizon curve</text>
  <text class="mu" x="460" y="428">a control that beats the naive by a lot is a red flag,</text>
  <text class="mu" x="460" y="444">not a triumph &#8212; the negative controls stay visible.</text>
`);

// ---- Tab 5: the data contracts / design ----
const CONTRACTS = svg('cs-a5', 430, `
  <text class="hd" x="20" y="30">Data contracts &#8212; two validated boundaries bracket a seeded pipeline</text>

  <rect class="bx bx-store" x="20" y="56" width="200" height="120" rx="9"/>
  <text class="ttl" x="32" y="76" style="fill:var(--cs-store);">CONTRACT 1 &#183; ingestion</text>
  <text class="cd mono" x="32" y="94">io/contract.py &#183; io/schema.py</text>
  <text class="mu" x="32" y="114">a valid series: long-format</text>
  <text class="mu" x="32" y="130">id/timestamp/value + an explicit</text>
  <text class="mu" x="32" y="146">missing/outlier policy, so the tool</text>
  <text class="mu" x="32" y="162">accepts external data, not just cases</text>
  <path class="flow" d="M220,116 L256,116" marker-end="url(#cs-a5)"/>
  <text class="lbl" x="224" y="108">valid obs</text>

  <rect class="bx bx-hi" x="258" y="56" width="340" height="120" rx="10"/>
  <text class="ttl" x="270" y="76" style="fill:var(--color-accent);">the staged pipeline &#183; pure function of (case, seed)</text>
  <text class="cd mono" x="270" y="94">chronoscopelab/pipeline.py</text>
  <text class="mu" x="270" y="116">preprocess &#8594; feature_extraction &#8594; train &#8594; infer</text>
  <text class="mu" x="270" y="134">&#8594; evaluate &#8594; export &#8212; deterministic, seeded (42)</text>
  <text class="mu" x="270" y="158">same (case, seed) &#8594; byte-identical artifacts; no network,</text>
  <text class="mu" x="270" y="172" style="font-size:9px;">no wall-clock branching. CHRONOSCOPE_DERIVED_DIR sandboxes test writes.</text>
  <path class="flow" d="M598,116 L634,116" marker-end="url(#cs-a5)"/>
  <text class="lbl" x="602" y="108">baked</text>

  <rect class="bx bx-store" x="636" y="56" width="220" height="120" rx="9"/>
  <text class="ttl" x="648" y="76" style="fill:var(--cs-store);">CONTRACT 2 &#183; artifact</text>
  <text class="it" x="648" y="98">trace <tspan class="cd mono">chronoscope.trace/v2</tspan></text>
  <text class="it" x="648" y="116">manifest <tspan class="cd mono">.manifest/v1</tspan></text>
  <text class="it" x="648" y="134">analysis, streaming, index</text>
  <text class="cd mono" x="648" y="154">core/trace.py &#183; core/manifest.py</text>
  <text class="mu" x="648" y="170">mirrored in TS &#8594; tsc gate</text>

  <rect class="grp" x="20" y="200" width="411" height="206" rx="10"/>
  <text class="sub" x="34" y="220" style="font-weight:600;">THE LANE GATE &#183; core/gate.py</text>
  <rect class="bx bx-web" x="34" y="234" width="180" height="72" rx="9"/>
  <text class="ttl" x="46" y="254" style="fill:var(--cs-web);">LIVE</text>
  <text class="mu" x="46" y="274">cheap + pure-numpy/ONNX:</text>
  <text class="mu" x="46" y="290">safe to recompute in the browser</text>
  <rect class="bx bx-compute" x="228" y="234" width="188" height="72" rx="9"/>
  <text class="ttl" x="240" y="254" style="fill:var(--cs-compute);">PRECOMPUTE</text>
  <text class="mu" x="240" y="274">heavy (GPU/foundation/AutoARIMA):</text>
  <text class="mu" x="240" y="290">baked offline, replayed as artifact</text>
  <text class="mu" x="34" y="332">a measured verdict per method, recorded in the manifest;</text>
  <text class="mu" x="34" y="350">the manifest lane must match the gate lane (checked in CI).</text>
  <text class="mu" x="34" y="376" style="fill:var(--cs-store);">license guard:</text>
  <text class="mu" x="112" y="376">a local-only-licensed source ships</text>
  <text class="mu" x="34" y="394">aggregate metrics only (the raw excerpt is redacted).</text>

  <rect class="grp" x="443" y="200" width="413" height="206" rx="10"/>
  <text class="sub" x="457" y="220" style="font-weight:600;">DRIFT GATE (CI) &#183; scripts/check_artifacts.py</text>
  <text class="it" x="457" y="244">the index references every case;</text>
  <text class="it" x="457" y="262">each manifest &#8596; artifact byte-size matches;</text>
  <text class="it" x="457" y="280">the lane matches the gate verdict;</text>
  <text class="it" x="457" y="298">the ladder is complete (&#8805; 15 methods/trace).</text>
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
      body_en: 'ChronoScope is an interactive atlas of time-series forecasting. For each case it runs two pillars: Understand (a 10-family analysis toolkit that diagnoses the series) and Forecast (a 19-method ladder from the seasonal-naive baseline up to zero-shot foundation models). Every method is scored by a leakage-safe rolling-origin backtest and the prequential streaming bench, so the diagnosis explains which family wins and the intervals are honestly calibrated. The lower band is the design-build lifecycle: deep research persisted to dossiers, then implement, train + validate on GPU, bake the deterministic artifact, build the SPA over it, and deploy.',
      body_es: 'ChronoScope es un atlas interactivo del pronóstico de series de tiempo. Por cada caso ejecuta dos pilares: Entender (un kit de 10 familias de análisis que diagnostica la serie) y Pronosticar (una escalera de 19 métodos (18 nativos + TiRex-2 por el carril WSL2), del naive-estacional hasta modelos fundacionales zero-shot). Cada método se evalúa con un backtest de origen móvil sin fuga y el banco de streaming prequential, de modo que el diagnóstico explica qué familia gana y los intervalos quedan calibrados honestamente. La banda inferior es el ciclo diseño-construcción: investigación profunda persistida en dossiers, luego implementar, entrenar + validar en GPU, precalcular el artefacto determinista, construir la SPA sobre él y desplegar.',
    },
    {
      id: 'lanes', en: 'Lanes', es: 'Carriles', svg: LANES,
      body_en: 'The split is the point. Web (live, in the browser): the classical ladder recomputes on every control via a TypeScript engine parity-checked against the Python core, a small NLinear model runs client-side via onnxruntime-web, the light analysis recomputes instantly, and every chart is an interactive uPlot view. Replay: the statistical, ML, deep and foundation tiers are too heavy for the browser, so their baked backtest (trace + analysis + streaming) is shown. Offline / compute: the .venv pipeline runs the real engines (statsforecast, LightGBM, neuralforecast on GPU, Chronos/TimesFM from local checkpoints) and preqts, and bakes the committed artifacts.',
      body_es: 'La división es lo central. Web (en vivo, en el navegador): la escalera clásica recalcula con cada control vía un motor TypeScript verificado por paridad contra el núcleo Python, un pequeño modelo NLinear se ejecuta en el cliente vía onnxruntime-web, el análisis ligero recalcula al instante, y cada gráfico es una vista interactiva uPlot. Replay: los niveles estadístico, ML, profundo y fundacional son demasiado pesados para el navegador, así que se muestra su backtest precalculado (trace + análisis + streaming). Offline / cómputo: el pipeline en .venv ejecuta los motores reales (statsforecast, LightGBM, neuralforecast en GPU, Chronos/TimesFM desde checkpoints locales) y preqts, y precalcula los artefactos versionados.',
    },
    {
      id: 'flow', en: 'Web flow', es: 'Flujo web', svg: FLOW,
      body_en: 'The App page is a per-case workbench. A source selector chooses a baked case (replay) or a synthetic pattern with live knobs; the engines produce forecasts (live for classical + ONNX, replay for the heavy tiers); and the case is presented across 10 interactive tabs, split Understand (Series, Structure, Decompose, Verdicts) and Forecast (Forecast with a Forecast/Errors toggle, Zoom, Horizon, Residuals, Leaderboard, Streaming). Two mechanisms keep it honest: copy-data.mjs overlays the committed artifacts (never hand-typed), and the TypeScript contract mirror fails the build on any schema drift; a CI drift-gate runs before deploy.',
      body_es: 'La página App es un entorno de trabajo por caso. Un selector de fuente elige un caso precalculado (replay) o un patrón sintético con perillas en vivo; los motores producen pronósticos (en vivo para clásicos + ONNX, replay para los niveles pesados); y el caso se presenta en 10 pestañas interactivas, divididas en Entender (Serie, Estructura, Descomponer, Veredictos) y Pronosticar (Pronóstico con un toggle Pronóstico/Errores, Zoom, Horizonte, Residuos, Tabla, Streaming). Dos mecanismos lo mantienen honesto: copy-data.mjs superpone los artefactos versionados (nunca tipeados a mano) y el espejo de contrato en TypeScript rompe el build ante cualquier divergencia de esquema; un drift-gate de CI se ejecuta antes de desplegar.',
    },
    {
      id: 'science', en: 'The science', es: 'La ciencia', svg: SCIENCE,
      body_en: 'The ladder runs from a transparent baseline upward: seasonal-naive (the MASE denominator), exponential smoothing (SES, Holt, Holt-Winters), Theta, auto-tuned statistical models (AutoARIMA/AutoETS/AutoTheta), LightGBM on lag features, deep nets (NHITS/DLinear/NLinear), and zero-shot foundation transformers (Chronos-Bolt, Chronos-2, TimesFM-2.5). The 10-family analysis toolkit diagnoses the series (each family honesty-gated). Evaluation is a leakage-safe rolling-origin backtest plus the novel prequential streaming bench (preqts: predict, observe, update, with ACI + Conformal-PID recalibrating the interval online). Metrics: MASE, WQL, coverage, MSIS, and the per-horizon error curve; the negative controls stay visible so a "no" is as clear as a "yes".',
      body_es: 'La escalera va de un baseline transparente hacia arriba: naive-estacional (el denominador de MASE), suavizamiento exponencial (SES, Holt, Holt-Winters), Theta, modelos estadísticos auto-ajustados (AutoARIMA/AutoETS/AutoTheta), LightGBM sobre rezagos, redes profundas (NHITS/DLinear/NLinear) y transformers fundacionales zero-shot (Chronos-Bolt, Chronos-2, TimesFM-2.5). El kit de 10 familias diagnostica la serie (cada familia con su compuerta de honestidad). La evaluación es un backtest de origen móvil sin fuga más el novedoso banco de streaming prequential (preqts: predecir, observar, actualizar, con ACI + Conformal-PID recalibrando el intervalo en línea). Métricas: MASE, WQL, cobertura, MSIS y la curva de error por horizonte; los controles negativos quedan visibles para que un "no" sea tan claro como un "sí".',
    },
    {
      id: 'contracts', en: 'Data contracts', es: 'Contratos de datos', svg: CONTRACTS,
      body_en: 'Two validated contracts bracket the pipeline. Contract 1 (ingestion) defines a valid series (long-format id/timestamp/value + a missing/outlier policy), so the tool accepts external data, not just the built-in cases. Between them a staged, seeded pipeline (preprocess to export) is a pure function of (case, seed): same inputs give byte-identical artifacts. Contract 2 (artifact) defines the compact trace v2 + manifest + analysis + streaming the web reads, mirrored by a TypeScript type so drift fails the build. A measured live/replay lane gate is recorded per method (the manifest lane must match it), a license guard ships aggregate-only metrics for local-only sources, and a CI drift-gate enforces artifact consistency and ladder completeness (>= 15 methods/trace) so a lighter-lane regeneration can never silently ship a downgraded bake.',
      body_es: 'Dos contratos validados encierran el pipeline. El Contrato 1 (ingesta) define una serie válida (formato largo id/marca-de-tiempo/valor + una política de faltantes/atípicos), para que la herramienta acepte datos externos, no solo los casos incluidos. Entre ambos, un pipeline por etapas y con semilla (de preprocess a export) es una función pura de (caso, semilla): las mismas entradas dan artefactos byte-idénticos. El Contrato 2 (artefacto) define el trace v2 compacto + manifiesto + análisis + streaming que lee la web, espejado por un tipo TypeScript para que la divergencia rompa el build. Un gate de carril live/replay medido se registra por método (el carril del manifiesto debe coincidir), una compuerta de licencia publica solo métricas agregadas para fuentes solo-locales, y un drift-gate de CI exige consistencia de artefactos y completitud de la escalera (>= 15 métodos/trace) para que una regeneración en un carril liviano nunca publique en silencio un precálculo degradado.',
    },
  ],
};
