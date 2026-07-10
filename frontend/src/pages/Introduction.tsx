import { Callout, Cite, Equation, Refs, useShellLang } from '@fasl-work/caos-app-shell';

// Introduction: what ChronoScope is (a forecasting + analysis atlas), the no-free-lunch thesis, the two
// pillars (understand + forecast), the streaming story, and the honest scope. Content transcribed from the
// persisted research dossiers (docs/research + wip/chronoscope), never improvised.
export default function Introduction() {
  const es = useShellLang() === 'es';
  return (
    <section className="page-body prose">
      <h2>{es ? 'Introducción' : 'Introduction'}</h2>
      <p className="cs-lead">{es
        ? 'ChronoScope es un atlas interactivo del pronóstico de series de tiempo: toma una serie (sintética con perillas, un caso real, o la tuya), la ENTIENDE con el kit clásico de diagnóstico (estacionariedad, autocorrelación, estacionalidad, quiebres, volatilidad, memoria larga, caos), corre la escalera completa de métodos (clásicos, estadísticos, ML, profundos, fundacionales) sobre ella, y muestra honestamente dónde gana y dónde falla cada familia.'
        : 'ChronoScope is an interactive atlas of time-series forecasting: it takes a series (synthetic with knobs, a real case, or your own), UNDERSTANDS it with the classical diagnostic toolkit (stationarity, autocorrelation, seasonality, breaks, volatility, long memory, chaos), runs the full method ladder (classical, statistical, ML, deep, foundation) across it, and shows honestly where each family wins and where it fails.'}</p>

      <svg viewBox="0 0 680 120" width="100%" style={{ maxWidth: 680, display: 'block', margin: '0.8rem auto', font: '11px var(--font-sans, sans-serif)' }} role="img" aria-label="the two pillars: understand then forecast">
        <rect x="6" y="42" width="92" height="36" rx="6" fill="var(--color-surface)" stroke="var(--color-border)" /><text x="52" y="64" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="10">{es ? 'serie' : 'series'}</text>
        <line x1="98" y1="60" x2="126" y2="60" stroke="var(--color-fg-subtle)" />
        <rect x="126" y="14" width="180" height="40" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" /><text x="216" y="32" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'ENTENDER: 10 familias' : 'UNDERSTAND: 10 families'}</text><text x="216" y="46" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">ADF·ACF·STL·PELT·GARCH·DFA·RQA</text>
        <rect x="126" y="66" width="180" height="40" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" /><text x="216" y="84" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'PRONOSTICAR: 18 métodos' : 'FORECAST: 18 methods'}</text><text x="216" y="98" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">naive · ARIMA · LightGBM · NHITS · TimesFM</text>
        <line x1="306" y1="60" x2="334" y2="60" stroke="var(--color-fg-subtle)" />
        <rect x="334" y="30" width="150" height="60" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" /><text x="409" y="52" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'backtest honesto' : 'honest backtest'}</text><text x="409" y="68" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? 'origen móvil + prequential' : 'rolling origin + prequential'}</text>
        <line x1="484" y1="60" x2="512" y2="60" stroke="var(--color-fg-subtle)" />
        <rect x="512" y="14" width="160" height="40" rx="6" fill="var(--color-surface)" stroke="#3fb950" /><text x="592" y="32" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'dónde gana cada familia' : 'where each family wins'}</text><text x="592" y="46" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? '(y por qué: el diagnóstico)' : '(and why: the diagnosis)'}</text>
        <rect x="512" y="66" width="160" height="40" rx="6" fill="var(--color-surface)" stroke="#3fb950" /><text x="592" y="84" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'intervalos calibrados' : 'calibrated intervals'}</text><text x="592" y="98" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">ACI · Conformal-PID (preqts)</text>
      </svg>

      <h3>{es ? 'El problema' : 'The problem'}</h3>
      <p>{es
        ? 'El pronóstico de series de tiempo vive una explosión: en tres años el estado del arte pasó de modelos estadísticos ajustados por serie (ARIMA, ETS) a transformers fundacionales pre-entrenados que pronostican zero-shot cualquier serie. Pero la literatura también documenta dos verdades incómodas. Primero, no hay almuerzo gratis: los rankings cambian según el benchmark, un modelo lineal de una capa rivaliza con transformers profundos en horizontes largos, y en una caminata aleatoria nadie le gana al naive.'
        : 'Time-series forecasting is mid-explosion: in three years the state of the art went from per-series fitted statistical models (ARIMA, ETS) to pretrained foundation transformers that forecast any series zero-shot. But the literature also documents two uncomfortable truths. First, there is no free lunch: rankings flip across benchmarks, a one-layer linear model rivals deep transformers on long horizons, and on a random walk nobody beats the naive.'}
        {' '}<Cite id="dlinear" /> <Cite id="tfb" /></p>
      <p>{es
        ? 'Segundo, la evaluación misma está en disputa: fuga de datos de pre-entrenamiento en los benchmarks, el bug del drop-last en la suite LTSF, y protocolos que evalúan a los modelos SIN estado (re-pronosticando ventanas independientes) cuando el pronóstico real es un STREAM: las observaciones llegan una a una, el modelo se actualiza, y sus intervalos deben mantenerse calibrados bajo deriva.'
        : 'Second, evaluation itself is contested: pretraining leakage into the benchmarks, the drop-last bug in the LTSF suite, and protocols that evaluate models STATELESSLY (re-forecasting independent windows) when real forecasting is a STREAM: observations arrive one by one, the model updates, and its intervals must stay calibrated under drift.'}
        {' '}<Cite id="gifteval" /> <Cite id="fevbench" /></p>

      <h3>{es ? 'Qué hace ChronoScope' : 'What ChronoScope does'}</h3>
      <p>{es
        ? 'Dos pilares con el mismo peso. ENTENDER: diez familias de diagnóstico (estacionariedad y raíces unitarias; autocorrelación e identificación Box-Jenkins; estacionalidad y espectro; filtros y descomposición adaptativa; puntos de quiebre y regímenes; volatilidad y transformaciones; distribución y complejidad; fractales y multifractales; dinámica no lineal y caos; causalidad y cointegración), cada una delegada a su implementación de referencia y horneada por caso. PRONOSTICAR: una escalera de 18 métodos, del naive estacional a TimesFM 2.5 y Chronos-2, evaluada con un backtest de origen móvil sin fuga y un banco prequential de streaming.'
        : 'Two pillars, equal weight. UNDERSTAND: ten diagnostic families (stationarity and unit roots; autocorrelation and Box-Jenkins identification; seasonality and spectrum; filters and adaptive decomposition; change points and regimes; volatility and transforms; distribution and complexity; fractals and multifractals; nonlinear dynamics and chaos; causality and cointegration), each delegated to its reference implementation and baked per case. FORECAST: an 18-method ladder, from the seasonal naive to TimesFM 2.5 and Chronos-2, scored by a leakage-safe rolling-origin backtest and a prequential streaming bench.'}</p>
      <p>{es
        ? 'La tesis del atlas es que ambos pilares se explican mutuamente: el caso con quiebres estructurales lo diagnostica el panel de change-points Y hace tropezar a los modelos que promedian regímenes; el caso GARCH dispara el test ARCH-LM Y demuestra por qué los intervalos de ancho fijo fallan; el caso de memoria larga muestra el decaimiento hiperbólico de la ACF Y el borde que los modelos de contexto largo explotan. El diagnóstico no es decoración: es la explicación de la tabla de posiciones.'
        : 'The atlas thesis is that the pillars explain each other: the structural-break case is diagnosed by the change-point panel AND trips the models that average across regimes; the GARCH case fires the ARCH-LM test AND demonstrates why fixed-width intervals fail; the long-memory case shows the hyperbolic ACF decay AND the edge long-context models exploit. The diagnosis is not decoration: it is the explanation of the leaderboard.'}</p>

      <h3>{es ? 'La historia de streaming (lo nuevo)' : 'The streaming story (the novel piece)'}</h3>
      <p>{es
        ? 'Ningún harness público evalúa pronosticadores CON estado de forma prequential (predecir, observar, actualizar) con una política explícita de llegada de covariables; fev, GIFT-Eval y los backtests de GluonTS/Darts evalúan ventanas sin estado. ChronoScope extrajo esa capacidad como preqts, nuestro paquete publicado en PyPI, y la demuestra por caso: trayectorias de habilidad, cobertura y costo, con los intervalos re-calibrados en línea por Adaptive Conformal Inference y Conformal PID.'
        : 'No public harness evaluates STATEFUL forecasters prequentially (predict, observe, update) with an explicit covariate-arrival policy; fev, GIFT-Eval and the GluonTS/Darts backtests evaluate stateless windows. ChronoScope extracted that capability as preqts, our published PyPI package, and demonstrates it per case: skill, coverage and cost trajectories, with intervals re-calibrated online by Adaptive Conformal Inference and Conformal PID.'}
        {' '}<Cite id="prequential" /></p>
      <Equation tex={String.raw`\alpha_{t+1} \;=\; \alpha_t + \gamma\,\big(\alpha_{\text{target}} - \text{miss}_t\big)`} caption={es ? 'ACI: la mis-cobertura efectiva se corrige en línea; la cobertura de largo plazo converge al objetivo bajo deriva arbitraria (Gibbs y Candès 2021).' : 'ACI: the effective miscoverage self-corrects online; long-run coverage converges to the target under arbitrary drift (Gibbs & Candès 2021).'} />

      <h3>{es ? 'Alcance honesto' : 'Honest scope'}</h3>
      <Callout variant="honest" title={es ? 'Qué es y qué NO es' : 'What it is and is NOT'}>
        {es
          ? 'Un atlas de investigación reproducible, no un servicio de pronóstico de producción. Los casos sintéticos están etiquetados y generados con semilla; los datos reales se publican solo bajo sus términos de licencia (las fuentes solo-local publican métricas agregadas, nunca sus valores). Los métodos pesados se hornean OFFLINE y se reproducen aquí; el nivel clásico y un modelo profundo pequeño corren EN VIVO en tu navegador. En los casos de control (ruido blanco, caminata aleatoria) ningún método debería ganar por mucho: si algo gana, sospecha del harness, no celebres el modelo.'
          : 'A reproducible research atlas, not a production forecasting service. Synthetic cases are labelled and seed-generated; real data ships only under its license terms (local-only sources publish aggregate metrics, never their values). Heavy methods are baked OFFLINE and replayed here; the classical tier and a small deep model run LIVE in your browser. On the control cases (white noise, random walk) no method should win by much: if something does, suspect the harness, do not celebrate the model.'}
      </Callout>

      <Refs ids={['fm-survey', 'dlinear', 'gifteval', 'fevbench', 'prequential', 'mase']} label={es ? 'Referencias' : 'References'} />
    </section>
  );
}
