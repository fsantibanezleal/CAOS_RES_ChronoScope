import { Callout, Cite, DocPage, Equation, ExecutiveView, Refs, Tabs, useShellLang } from '@fasl-work/caos-app-shell';
import executive from '../../../content/executive.json';

// Introduction: what ChronoScope is (a forecasting + analysis atlas), the no-free-lunch thesis, the two
// pillars (understand + forecast), the streaming story, and the honest scope. Content transcribed from the
// persisted research dossiers (docs/research + wip/chronoscope), never improvised.
export default function Introduction() {
  const es = useShellLang() === 'es';
  return <DocPage
    title={{ en: 'Introduction', es: 'Introducción' }}
    lede={es ? 'La decisión de planificación y la evidencia que permite evaluar sus pronósticos.' : 'The planning decision and the evidence used to evaluate its forecasts.'}
  >
    <Tabs ariaLabel={es ? 'Vistas de la introducción' : 'Introduction views'} tabs={[
      { id: 'executive', label: es ? 'Ejecutiva' : 'Executive', content: <ExecutiveView data={executive} base={import.meta.env.BASE_URL} /> },
      { id: 'technical', label: es ? 'Técnica' : 'Technical', content: <TechnicalView /> },
    ]} />
  </DocPage>;
}

function TechnicalView() {
  const es = useShellLang() === 'es';
  return (
    <div>
      <p className="cs-lead">{es
        ? 'ChronoScope es un atlas interactivo del pronóstico de series de tiempo: toma una serie (sintética con perillas, un caso real, o una propia), la entiende con el kit clásico de diagnóstico (estacionariedad, autocorrelación, estacionalidad, quiebres, volatilidad, memoria larga, caos), ejecuta la escalera completa de métodos (clásicos, estadísticos, ML, profundos, fundacionales) sobre ella, y muestra honestamente dónde gana y dónde falla cada familia.'
        : 'ChronoScope is an interactive atlas of time-series forecasting: it takes a series (synthetic with knobs, a real case, or a user-supplied one), understands it with the classical diagnostic toolkit (stationarity, autocorrelation, seasonality, breaks, volatility, long memory, chaos), runs the full method ladder (classical, statistical, ML, deep, foundation) across it, and shows honestly where each family wins and where it fails.'}</p>

      <svg viewBox="0 0 680 120" width="100%" style={{ maxWidth: 680, display: 'block', margin: '0.8rem auto', font: '11px var(--font-sans, sans-serif)' }} role="img" aria-label="the two pillars: understand then forecast">
        <rect x="6" y="42" width="92" height="36" rx="6" fill="var(--color-surface)" stroke="var(--color-border)" /><text x="52" y="64" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="10">{es ? 'serie' : 'series'}</text>
        <line x1="98" y1="60" x2="126" y2="60" stroke="var(--color-fg-subtle)" />
        <rect x="126" y="14" width="180" height="40" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" /><text x="216" y="32" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'ENTENDER: 10 familias' : 'UNDERSTAND: 10 families'}</text><text x="216" y="46" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">ADF·ACF·STL·PELT·GARCH·DFA·RQA</text>
        <rect x="126" y="66" width="180" height="40" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" /><text x="216" y="84" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'PRONOSTICAR: 19 métodos' : 'FORECAST: 19 methods'}</text><text x="216" y="98" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">naive · ARIMA · LightGBM · NHITS · TimesFM</text>
        <line x1="306" y1="60" x2="334" y2="60" stroke="var(--color-fg-subtle)" />
        <rect x="334" y="30" width="150" height="60" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" /><text x="409" y="52" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'backtest honesto' : 'honest backtest'}</text><text x="409" y="68" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? 'origen móvil + prequential' : 'rolling origin + prequential'}</text>
        <line x1="484" y1="60" x2="512" y2="60" stroke="var(--color-fg-subtle)" />
        <rect x="512" y="14" width="160" height="40" rx="6" fill="var(--color-surface)" stroke="#3fb950" /><text x="592" y="32" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'dónde gana cada familia' : 'where each family wins'}</text><text x="592" y="46" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? '(y por qué: el diagnóstico)' : '(and why: the diagnosis)'}</text>
        <rect x="512" y="66" width="160" height="40" rx="6" fill="var(--color-surface)" stroke="#3fb950" /><text x="592" y="84" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'intervalos calibrados' : 'calibrated intervals'}</text><text x="592" y="98" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">ACI · Conformal-PID (preqts)</text>
      </svg>

      <h3>{es ? 'El problema' : 'The problem'}</h3>
      <p>{es
        ? 'La investigación reciente en pronóstico de series de tiempo abarca desde modelos estadísticos ajustados por serie (ARIMA, ETS) hasta modelos preentrenados que pronostican sin ajuste por serie. Las comparaciones publicadas muestran que los rankings varían entre benchmarks y que los controles de caminata aleatoria son difíciles de superar.'
        : 'Recent time-series forecasting research spans per-series statistical models (ARIMA, ETS) and pretrained models that forecast without per-series fitting. Published comparisons show that rankings vary across benchmarks and random-walk controls are difficult to beat.'}
        {' '}<Cite id="dlinear" /> <Cite id="tfb" /></p>
      <p>{es
        ? 'Segundo, la evaluación misma está en disputa: fuga de datos de pre-entrenamiento en los benchmarks, el bug del drop-last en la suite LTSF, y protocolos que evalúan a los modelos sin estado (re-pronosticando ventanas independientes) cuando el pronóstico real es un stream: las observaciones llegan una a una, el modelo se actualiza, y sus intervalos deben mantenerse calibrados bajo deriva.'
        : 'Second, evaluation itself is contested: pretraining leakage into the benchmarks, the drop-last bug in the LTSF suite, and protocols that evaluate models statelessly (re-forecasting independent windows) when real forecasting is a stream: observations arrive one by one, the model updates, and its intervals must stay calibrated under drift.'}
        {' '}<Cite id="gifteval" /> <Cite id="fevbench" /></p>

      <h3>{es ? 'Qué hace ChronoScope' : 'What ChronoScope does'}</h3>
      <p>{es
        ? 'Dos pilares con el mismo peso. Entender: diez familias de diagnóstico (estacionariedad y raíces unitarias; autocorrelación e identificación Box-Jenkins; estacionalidad y espectro; filtros y descomposición adaptativa; puntos de quiebre y regímenes; volatilidad y transformaciones; distribución y complejidad; fractales y multifractales; dinámica no lineal y caos; causalidad y cointegración), cada una delegada a su implementación de referencia y precalculada por caso. Pronosticar: una escalera de 19 métodos, del naive estacional a TimesFM 2.5, Chronos-2 y TiRex-2 (por el carril WSL2), evaluada con un backtest de origen móvil sin fuga y un banco prequential de streaming.'
        : 'Two pillars, equal weight. Understand: ten diagnostic families (stationarity and unit roots; autocorrelation and Box-Jenkins identification; seasonality and spectrum; filters and adaptive decomposition; change points and regimes; volatility and transforms; distribution and complexity; fractals and multifractals; nonlinear dynamics and chaos; causality and cointegration), each delegated to its reference implementation and baked per case. Forecast: a 19-method ladder, from the seasonal naive to TimesFM 2.5, Chronos-2 and TiRex-2 (via the WSL2 lane), scored by a leakage-safe rolling-origin backtest and a prequential streaming bench.'}</p>
      <p>{es
        ? 'Los paneles describen propiedades de cada caso junto a las comparaciones de pronóstico. Estas relaciones aportan contexto, pero los casos seleccionados no establecen causalmente por qué un método supera a otro.'
        : 'Diagnostic panels describe properties of each case alongside forecast comparisons. These relationships add context, but the selected cases do not establish why one method outperforms another.'}</p>

      <h3>{es ? 'Evaluación prequential en streaming' : 'Prequential streaming evaluation'}</h3>
      <p>{es
        ? 'El protocolo prequential predice, observa y luego actualiza el estado. Este atlas lo ejecuta mediante preqts y presenta trayectorias por caso para MASE, cobertura y tiempo medido. ACI y Conformal-PID recalibran los intervalos en línea.'
        : 'The prequential protocol predicts, observes, then updates state. This atlas runs it through preqts and reports per-case trajectories for MASE, coverage, and measured time. ACI and Conformal-PID recalibrate intervals online.'}
        {' '}<Cite id="prequential" /></p>
      <Equation tex={String.raw`\alpha_{t+1} \;=\; \alpha_t + \gamma\,\big(\alpha_{\text{target}} - \text{miss}_t\big)`} caption={es ? 'ACI actualiza la mis-cobertura objetivo después de cada observación; esta regla no garantiza por sí sola cobertura finita para los artefactos mostrados.' : 'ACI updates its target miscoverage after each observation; this update alone does not guarantee finite-sample coverage for the displayed artifacts.'} />

      <h3>{es ? 'Cómo leer el atlas' : 'How to read the atlas'}</h3>
      <p>{es
        ? 'El flujo de trabajo es el mismo que el de un pronóstico real. (1) Seleccionar un caso en la App (o generar uno sintético con las perillas): la barra muestra su huella (m, fuerza estacional, DFA α, persistencia GARCH, K de caos, mejor MASE), el resumen de una línea de lo que la serie es. (2) Leer el diagnóstico: Serie (media/desviación móviles, distribución), Estructura (ACF/PACF, periodograma), Descomponer (tendencia/estación/residuo) y Veredictos (los tests precalculados: raíces unitarias, ARCH, caos, catch22). (3) Recién entonces observar el pronóstico: la pestaña Pronóstico con sus vistas Completo/Zoom/Horizonte/Errores, la Tabla con MASE/WQL/MSIS/cobertura, y Streaming para la calibración en línea. El orden importa: el diagnóstico primero convierte la tabla de posiciones de un ranking opaco en una consecuencia explicable.'
        : 'The workflow is the same as a real forecasting job. (1) Pick a case in the App (or generate a synthetic one with the knobs): the bar shows its fingerprint (m, seasonal strength, DFA α, GARCH persistence, chaos K, best MASE), the one-line summary of what the series is. (2) Read the diagnosis: Series (rolling mean/std, distribution), Structure (ACF/PACF, periodogram), Decompose (trend/seasonal/remainder) and Verdicts (the baked tests: unit roots, ARCH, chaos, catch22). (3) Only then look at the forecast: the Forecast tab with its Full/Zoom/Horizon/Errors views, the Leaderboard with MASE/WQL/MSIS/coverage, and Streaming for online calibration. The order matters: diagnosis-first turns the leaderboard from an opaque ranking into an explainable consequence.'}</p>
      <p>{es
        ? 'Cada número es trazable: los métodos pesados llevan la insignia "replay" (precalculados por el pipeline abierto, con semilla), los ligeros se ejecutan en vivo en el navegador, y el pie de página declara la procedencia de datos y motores con sus licencias.'
        : 'Every number is traceable: heavy methods carry the "replay" badge (baked by the open, seeded pipeline), light ones run live in the browser, and the footer declares the data and engine provenance with their licenses.'}</p>

      <h3>{es ? 'Alcance honesto' : 'Honest scope'}</h3>
      <Callout variant="honest" title={es ? 'Qué es y qué no es' : 'What it is and is not'}>
        {es
          ? 'Un atlas de investigación reproducible, no un servicio de pronóstico de producción. Los casos sintéticos están etiquetados y generados con semilla; los datos reales se publican solo bajo sus términos de licencia (las fuentes solo-local publican métricas agregadas, nunca sus valores). Los métodos pesados se precalculan offline y se reproducen aquí; el nivel clásico y un modelo profundo pequeño se ejecutan en vivo en el navegador. En los casos de control (ruido blanco, caminata aleatoria) ningún método debería ganar por mucho: si algo gana, la sospecha recae en el harness, no es motivo para celebrar el modelo.'
          : 'A reproducible research atlas, not a production forecasting service. Synthetic cases are labelled and seed-generated; real data ships only under its license terms (local-only sources publish aggregate metrics, never their values). Heavy methods are baked offline and replayed here; seasonal-naive and smoothing methods plus a small deep model run live in the browser. Unexpectedly strong control-case results warrant harness review.'}
      </Callout>

      <Refs ids={['fm-survey', 'dlinear', 'gifteval', 'fevbench', 'prequential', 'mase']} label={es ? 'Referencias' : 'References'} />
    </div>
  );
}
