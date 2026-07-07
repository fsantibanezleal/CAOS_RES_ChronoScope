// In-app Architecture / "How it works" modal (ADR-0058). >=5 tabs, each a theme-aware schematic SVG
// (strokes/text via currentColor + the shell's --accent token, so they follow light/dark) + bilingual body.
import type { ArchitectureConfig } from '@fasl-work/caos-app-shell';

const box = (x: number, y: number, w: number, h: number, label: string, accent = false) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="6" fill="none" stroke="${accent ? 'var(--accent,#1f6feb)' : 'currentColor'}" stroke-width="1.5"/>` +
  `<text x="${x + w / 2}" y="${y + h / 2 + 4}" text-anchor="middle" font-size="11" fill="currentColor">${label}</text>`;
const arrow = (x1: number, y1: number, x2: number, y2: number) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="var(--accent,#1f6feb)" stroke-width="1.5" marker-end="url(#a)"/>`;
const svg = (inner: string, w = 640, h = 220) =>
  `<svg viewBox="0 0 ${w} ${h}" width="100%" role="img" style="max-width:${w}px;color:currentColor">` +
  `<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="var(--accent,#1f6feb)"/></marker></defs>${inner}</svg>`;

export const architecture: ArchitectureConfig = {
  title_en: 'Architecture / How it works',
  title_es: 'Arquitectura / Cómo funciona',
  tabs: [
    {
      id: 'app', en: 'The app', es: 'La app',
      svg: svg(box(30, 80, 150, 60, 'series in') + arrow(180, 110, 250, 110) + box(250, 60, 150, 100, 'method ladder') + arrow(400, 110, 470, 110) + box(470, 80, 150, 60, 'forecast + interval')),
      body_en: 'ChronoScope is an interactive atlas of time-series forecasting. You give it a series (a synthetic one you shape with knobs, or a baked real case); it runs the whole method ladder (classical, statistical, ML, foundation) and shows each forecast against the held-out truth with an honest, leakage-safe backtest. The classical tier recomputes live in your browser; the heavier tiers are replayed from an offline bake.',
      body_es: 'ChronoScope es un atlas interactivo del pronóstico de series de tiempo. Le das una serie (sintética, moldeada con perillas, o un caso real horneado); corre toda la escalera de métodos (clásicos, estadísticos, ML, fundacionales) y muestra cada pronóstico contra la verdad reservada con un backtest honesto y sin fuga. El nivel clásico recalcula en vivo en tu navegador; los niveles pesados se reproducen desde un horneado offline.',
    },
    {
      id: 'lanes', en: 'Lanes', es: 'Carriles',
      svg: svg(box(20, 40, 180, 50, 'WEB: TS classical + ONNX', true) + box(20, 100, 180, 50, 'REPLAY: baked artifacts') + box(230, 70, 180, 60, 'contract types (tsc gate)') + arrow(200, 65, 230, 90) + arrow(200, 125, 230, 110) + box(440, 40, 180, 110, 'OFFLINE: statsforecast /\\nLightGBM / torch+Chronos') + arrow(530, 150, 320, 150) + arrow(320, 150, 110, 150)),
      body_en: 'Three lanes, and the split is the point. WEB (live, in the browser): the classical ladder recomputes on every control via a TypeScript engine parity-checked against the Python core, and a small NLinear model runs client-side via onnxruntime-web. REPLAY: the statistical, ML and foundation tiers are too heavy for the browser, so their baked backtest is shown. OFFLINE: the pipeline runs the real engines and bakes the committed artifacts; a typed contract fails the build on any drift.',
      body_es: 'Tres carriles, y la división es lo central. WEB (en vivo, en el navegador): la escalera clásica recalcula con cada control vía un motor TypeScript verificado por paridad contra el núcleo Python, y un pequeño modelo NLinear corre en el cliente vía onnxruntime-web. REPLAY: los niveles estadístico, ML y fundacional son demasiado pesados para el navegador, así que se muestra su backtest horneado. OFFLINE: el pipeline corre los motores reales y hornea los artefactos versionados; un contrato tipado rompe el build ante cualquier divergencia.',
    },
    {
      id: 'flow', en: 'Web flow', es: 'Flujo web',
      svg: svg(box(20, 80, 130, 60, 'source selector') + arrow(150, 110, 210, 110) + box(210, 80, 130, 60, 'engines (live/replay)') + arrow(340, 110, 400, 110) + box(400, 40, 220, 140, 'workbench:\\nField / Live / Charts / Context', true)),
      body_en: 'The App page is a per-case workbench. A source selector chooses a synthetic pattern (with live knobs) or a baked case; the engines produce forecasts (live for classical + ONNX, replay for the heavy tiers); and the case is presented as a variant bar plus four sub-tabs: Field (the interactive chart, value read-out at the cursor), Live (re-run the browser engines as knobs move), Charts (per-method leaderboard), and Context (the deep write-up).',
      body_es: 'La página App es un banco de trabajo por caso. Un selector de fuente elige un patrón sintético (con perillas en vivo) o un caso horneado; los motores producen pronósticos (en vivo para clásicos + ONNX, replay para los niveles pesados); y el caso se presenta como una barra de variantes más cuatro sub-tabs: Field (el gráfico interactivo, lectura de valor en el cursor), Live (re-corre los motores del navegador al mover las perillas), Charts (tabla de posiciones por método) y Context (la explicación profunda).',
    },
    {
      id: 'science', en: 'The science', es: 'La ciencia',
      svg: svg(box(15, 90, 110, 40, 'baselines') + arrow(125, 110, 155, 110) + box(155, 90, 110, 40, 'smoothing/Theta') + arrow(265, 110, 295, 110) + box(295, 90, 110, 40, 'statistical') + arrow(405, 110, 435, 110) + box(435, 90, 90, 40, 'ML') + arrow(525, 110, 555, 110) + box(555, 90, 80, 40, 'foundation', true), 650),
      body_en: 'The ladder runs from a transparent baseline upward: seasonal-naive (the MASE denominator), simple/double exponential smoothing (SES, Holt), Holt-Winters seasonality, the Theta method (SES with half the OLS drift), auto-tuned statistical models (AutoARIMA/AutoETS/AutoTheta), gradient boosting on lags (LightGBM), and zero-shot foundation transformers (Chronos). Every method emits a point path and a prediction interval, and is scored by the same rolling-origin backtest.',
      body_es: 'La escalera va de un baseline transparente hacia arriba: naive-estacional (el denominador de MASE), suavizamiento exponencial simple/doble (SES, Holt), estacionalidad Holt-Winters, el método Theta (SES con la mitad de la pendiente OLS), modelos estadísticos auto-ajustados (AutoARIMA/AutoETS/AutoTheta), boosting de gradiente sobre rezagos (LightGBM), y transformers fundacionales zero-shot (Chronos). Cada método emite una trayectoria puntual y un intervalo de predicción, y se evalúa con el mismo backtest de origen móvil.',
    },
    {
      id: 'contracts', en: 'Data contracts', es: 'Contratos de datos',
      svg: svg(box(30, 80, 150, 60, 'raw series') + arrow(180, 110, 240, 110) + box(240, 80, 170, 60, 'Contract 1: ingest', true) + arrow(410, 110, 470, 110) + box(470, 80, 150, 60, 'Contract 2: artifact', true)),
      body_en: 'Two validated data contracts bracket the pipeline. Contract 1 (ingestion) defines a valid series (long-format id/timestamp/value + a missing/outlier policy), so the tool accepts your data, not just the built-in cases. Contract 2 (artifact) defines the compact trace + manifest the web reads, mirrored by a TypeScript type so any drift fails the build. Between them the staged, seeded pipeline runs a measured live/replay gate and writes a provenance manifest.',
      body_es: 'Dos contratos de datos validados encierran el pipeline. El Contrato 1 (ingesta) define una serie válida (formato largo id/marca-de-tiempo/valor + una política de faltantes/atípicos), para que la herramienta acepte tus datos, no solo los casos incluidos. El Contrato 2 (artefacto) define la traza compacta + el manifiesto que lee la web, espejado por un tipo TypeScript de modo que cualquier divergencia rompe el build. Entre ambos, el pipeline por etapas y con semilla corre un gate medido live/replay y escribe un manifiesto de procedencia.',
    },
  ],
};
