import { Callout, Cite, Equation, InlineMath, Refs, SubTabs, useShellLang } from '@fasl-work/caos-app-shell';

// Methodology: the 19-method ladder with the actual math, per family (SubTabs), each method with its
// equations, when-it-wins/when-it-fails, and inline citations. Transcribed from the persisted research
// dossiers (research-classical-statistical-ml, research-dl-forecasters, research-cluster-A/B/C).
export default function Methodology() {
  const es = useShellLang() === 'es';

  const classical = (
    <div className="prose">
      <p>{es
        ? 'La base transparente de la escalera: métodos de suavizamiento exponencial en forma de espacio de estados, cada uno computable en microsegundos y sorprendentemente difíciles de vencer. Todos corren EN VIVO en tu navegador (portados a TypeScript y verificados por paridad contra el núcleo Python).'
        : 'The transparent base of the ladder: exponential-smoothing methods in state-space form, each computable in microseconds and surprisingly hard to beat. All run LIVE in your browser (ported to TypeScript, parity-checked against the Python core).'}</p>
      <h4>Seasonal naive</h4>
      <p>{es ? 'Repite la última temporada observada: ' : 'Repeats the last observed season: '}
        <InlineMath tex={String.raw`\hat y_{t+h} = y_{t+h-m}`} />.{' '}
        {es
          ? 'Es el denominador del MASE: todo método se mide contra él, y en una caminata aleatoria o ruido blanco NADIE debería ganarle por mucho.'
          : 'It is the MASE denominator: every method is measured against it, and on a random walk or white noise NOBODY should beat it by much.'}
        {' '}<Cite id="mase" /></p>
      <h4>SES / Holt / Holt-Winters</h4>
      <Equation tex={String.raw`\ell_t = \alpha y_t + (1-\alpha)\,\ell_{t-1}, \qquad \hat y_{t+h} = \ell_t`} caption={es ? 'SES: un nivel exponencialmente suavizado; el pronóstico es plano.' : 'SES: an exponentially-smoothed level; the forecast is flat.'} />
      <Equation tex={String.raw`\ell_t = \alpha y_t + (1-\alpha)(\ell_{t-1} + b_{t-1}), \quad b_t = \beta(\ell_t - \ell_{t-1}) + (1-\beta) b_{t-1}`} caption={es ? 'Holt añade una tendencia local; Holt-Winters añade un componente estacional aditivo actualizado por temporada.' : 'Holt adds a local trend; Holt-Winters adds an additive seasonal component updated per season.'} />
      <h4>Theta</h4>
      <p>{es
        ? 'El método que ganó la competencia M3, luego desenmascarado como SES con la mitad de la pendiente OLS: '
        : 'The method that won the M3 competition, later unmasked as SES with half the OLS drift: '}
        <InlineMath tex={String.raw`\hat y_{t+h} = \ell_t + \tfrac{1}{2}\, b_{\text{OLS}}\, h`} />.{' '}
        <Cite id="theta" /> <Cite id="theta-ses" /></p>
      <Callout variant="note" title={es ? 'Cuándo ganan' : 'When they win'}>
        {es
          ? 'Series cortas, estacionalidad estable, poco presupuesto de cómputo. Cuándo fallan: múltiples estacionalidades, quiebres de régimen (promedian a través de ellos), memoria larga.'
          : 'Short series, stable seasonality, tiny compute budgets. When they fail: multiple seasonalities, regime breaks (they average across them), long memory.'}
      </Callout>
    </div>
  );

  const statistical = (
    <div className="prose">
      <p>{es
        ? 'Los modelos estadísticos auto-ajustados (statsforecast): búsqueda por AICc sobre el espacio del modelo, intervalos analíticos. Se hornean OFFLINE (numba no corre en el navegador).'
        : 'The auto-tuned statistical models (statsforecast): AICc search over the model space, analytic intervals. Baked OFFLINE (numba does not run in a browser).'}</p>
      <h4>AutoARIMA</h4>
      <Equation tex={String.raw`\phi_p(B)\,(1-B)^d\, y_t \;=\; c + \theta_q(B)\,\varepsilon_t`} caption={es ? 'ARIMA(p,d,q): polinomios AR y MA sobre la serie d-diferenciada; la búsqueda elige (p,d,q) por AICc con tests de raíz unitaria para d.' : 'ARIMA(p,d,q): AR and MA polynomials on the d-differenced series; the search picks (p,d,q) by AICc with unit-root tests for d.'} />
      <h4>AutoETS</h4>
      <p>{es
        ? 'La taxonomía completa de espacio de estados (Error, Trend, Seasonal, cada uno ausente/aditivo/multiplicativo, con amortiguamiento), seleccionada por AICc. La contraparte probabilística exacta del suavizamiento exponencial.'
        : 'The full state-space taxonomy (Error, Trend, Seasonal, each none/additive/multiplicative, with damping), selected by AICc. The exact probabilistic counterpart of exponential smoothing.'}</p>
      <h4>AutoTheta</h4>
      <p>{es ? 'La familia Theta con selección automática de la variante y descomposición estacional previa.' : 'The Theta family with automatic variant selection and prior seasonal decomposition.'}</p>
      <Callout variant="note" title={es ? 'Cuándo ganan' : 'When they win'}>
        {es
          ? 'Series univariadas con estructura ARMA genuina; son el punto de referencia honesto del nivel medio. La lección M3/M4: combinaciones simples de estos métodos vencieron a casi todo lo complejo durante dos décadas.'
          : 'Univariate series with genuine ARMA structure; the honest mid-tier reference. The M3/M4 lesson: simple combinations of these beat almost everything complex for two decades.'}
        {' '}<Cite id="m5" />
      </Callout>
    </div>
  );

  const ml = (
    <div className="prose">
      <h4>LightGBM {es ? 'sobre rezagos' : 'on lags'}</h4>
      <p>{es
        ? 'Gradient boosting sobre features de rezago y calendario (mlforecast). La lección de la competencia M5: el primer certamen M donde el ML puro venció a todos los benchmarks estadísticos, con LightGBM como caballo de batalla de las soluciones ganadoras.'
        : 'Gradient boosting on lag and calendar features (mlforecast). The M5 lesson: the first M competition where pure ML beat every statistical benchmark, with LightGBM the workhorse of the winning solutions.'}
        {' '}<Cite id="lightgbm" /> <Cite id="m5" /></p>
      <Equation tex={String.raw`\hat y_{t+h} \;=\; F\big(y_{t-1}, y_{t-2}, \ldots, y_{t-k},\; \text{cal}_t\big), \qquad F = \textstyle\sum_{j} f_j`} caption={es ? 'El pronóstico como regresión tabular: los rezagos son las features, F es un ensamble de árboles; los cuantiles vienen de la pérdida pinball por nivel.' : 'Forecasting as tabular regression: the lags are the features, F is a tree ensemble; quantiles come from a per-level pinball loss.'} />
      <Callout variant="note" title={es ? 'Cuándo gana' : 'When it wins'}>
        {es
          ? 'Muchas series relacionadas, covariables ricas, no-linealidades tabulares. Cuándo falla: extrapolación de tendencia (los árboles no extrapolan fuera del rango visto) y series únicas cortas.'
          : 'Many related series, rich covariates, tabular nonlinearities. When it fails: trend extrapolation (trees cannot extrapolate beyond the seen range) and short single series.'}
      </Callout>
    </div>
  );

  const deep = (
    <div className="prose">
      <p>{es
        ? 'El nivel profundo cuenta el debate 2022-2026 completo: Zeng et al. mostraron que UNA capa lineal (DLinear/NLinear) vencía a los transformers de la época en horizontes largos; PatchTST e iTransformer respondieron cambiando QUÉ es un token (parches temporales; series como tokens), no la atención; y el consenso actual es que ambas familias compiten, con la frontera desplazada a los modelos fundacionales.'
        : 'The deep tier tells the full 2022-2026 debate: Zeng et al. showed ONE linear layer (DLinear/NLinear) beat the era\'s transformers on long horizons; PatchTST and iTransformer answered by changing WHAT a token is (temporal patches; series as tokens), not the attention; and the current consensus is both families compete, with the frontier moved to foundation models.'}
        {' '}<Cite id="dlinear" /> <Cite id="patchtst" /> <Cite id="itransformer" /></p>
      <h4>NLinear / DLinear</h4>
      <Equation tex={String.raw`\hat{\mathbf y} = W(\mathbf x - x_L) + x_L \;\;\text{(NLinear)}; \qquad \hat{\mathbf y} = W_T\,\text{MA}(\mathbf x) + W_S(\mathbf x - \text{MA}(\mathbf x)) \;\;\text{(DLinear)}`} caption={es ? 'NLinear: normaliza por el último valor, una capa lineal, des-normaliza. DLinear: una capa para la tendencia (media móvil) + una para el resto.' : 'NLinear: normalize by the last value, one linear map, de-normalize. DLinear: one layer for the trend (moving average) + one for the remainder.'} />
      <h4>NHITS</h4>
      <p>{es
        ? 'Una pila de bloques MLP a tasas de muestreo decrecientes (interpolación jerárquica): los bloques gruesos capturan la estructura de largo alcance, los finos el detalle.'
        : 'A stack of MLP blocks at decreasing sampling rates (hierarchical interpolation): coarse blocks capture long-range structure, fine ones the detail.'}
        {' '}<Cite id="nhits" /></p>
      <Callout variant="strong" title={es ? 'Dos implementaciones que se auditan mutuamente' : 'Two implementations auditing each other'}>
        {es
          ? 'ChronoScope hornea CADA modelo profundo dos veces: la implementación canónica del framework neuralforecast ("NHITS (nf)") y una implementación directa en PyTorch contra el paper ("NHITS"). Ambas entrenan por caso en la GPU con pérdida pinball multi-cuantil y semilla fija. Una discrepancia grande entre ambas es una bandera roja que el Benchmark expone, no esconde.'
          : 'ChronoScope bakes EVERY deep model twice: the canonical neuralforecast framework implementation ("NHITS (nf)") and a direct-PyTorch implementation against the paper ("NHITS"). Both train per case on the GPU with a multi-quantile pinball loss and a fixed seed. A large disagreement between the two is a red flag the Benchmark surfaces, not hides.'}
      </Callout>
    </div>
  );

  const foundation = (
    <div className="prose">
      <p>{es
        ? 'El nivel SOTA: transformers pre-entrenados sobre miles de millones de observaciones que pronostican CUALQUIER serie zero-shot, sin ajuste. Todos los pesos horneados son Apache-2.0; corren desde checkpoints locales en la GPU.'
        : 'The SOTA tier: transformers pretrained on billions of observations that forecast ANY series zero-shot, no fitting. All baked weights are Apache-2.0; they run from local checkpoints on the GPU.'}
        {' '}<Cite id="fm-survey" /></p>
      <h4>Chronos-Bolt · Chronos-2</h4>
      <p>{es
        ? 'La línea Chronos de Amazon: Bolt (parches + T5, rápido en CPU, el candidato ONNX del navegador) y Chronos-2 (120M, atención de grupo; el único del roster con univariado + multivariado + covariables pasadas/futuras nativos en un solo modelo).'
        : 'Amazon\'s Chronos line: Bolt (patching + T5, CPU-fast, the browser ONNX candidate) and Chronos-2 (120M, group attention; the only roster model with native univariate + multivariate + past/future covariates in one model).'}
        {' '}<Cite id="chronos" /> <Cite id="chronos2" /></p>
      <h4>TimesFM 2.5</h4>
      <p>{es
        ? 'El decoder-only de Google (200M, contexto 16k, cabeza cuantílica continua): el punto de referencia inter-proveedor.'
        : 'Google\'s decoder-only (200M, 16k context, continuous quantile head): the cross-vendor reference point.'}
        {' '}<Cite id="timesfm" /></p>
      <h4>TiRex-2 {es ? '(carril WSL2)' : '(WSL2 lane)'}</h4>
      <p>{es
        ? 'El xLSTM streaming-nativo de NX-AI (el primer TSFM con estado). Sus kernels sLSTM (flashrnn -> triton, compilados por nvcc) no tienen wheels de Windows, así que corre en un carril WSL2 (Linux) con CUDA-in-WSL y se fusiona como el método 19 (fundacional): el pipeline de Windows escribe la serie, invoca TiRex-2 en WSL vía preqts con el MISMO backtest que el resto de la escalera, y lee el resultado. Es opt-in (CHRONOSCOPE_ENABLE_TIREX_WSL) y se salta con elegancia cuando WSL no está.'
        : 'NX-AI\'s streaming-native xLSTM (the first stateful TSFM). Its sLSTM kernels (flashrnn -> triton, nvcc-compiled) have no Windows wheels, so it runs in a WSL2 (Linux) lane with CUDA-in-WSL and merges as the 19th method (foundation): the Windows pipeline writes the series, invokes TiRex-2 in WSL via preqts with the SAME backtest as the rest of the ladder, and reads the result back. Opt-in (CHRONOSCOPE_ENABLE_TIREX_WSL) and it degrades gracefully when WSL is absent.'}
        {' '}<Cite id="tirex2" /></p>
      <h4>{es ? 'Los límites honestos del roster' : 'The honest roster limits'}</h4>
      <p>{es
        ? 'Con TiRex-2 en el carril WSL2, el único límite que queda es de licencia: Moirai-2 lidera GIFT-Eval pero sus pesos son CC-BY-NC (no comerciales): material de guía, nunca horneado.'
        : 'With TiRex-2 in the WSL2 lane, the only remaining limit is a license one: Moirai-2 tops GIFT-Eval but its weights are CC-BY-NC (non-commercial): guide material, never baked.'}
        {' '}<Cite id="moirai" /></p>
      <Callout variant="honest" title={es ? 'La caveat de fuga' : 'The leakage caveat'}>
        {es
          ? 'Los benchmarks públicos solo garantizan una evaluación limpia para modelos entrenados en SUS splits de pre-entrenamiento; un fundacional entrenado en otro corpus puede haber visto los datos de test. Por eso los casos sintéticos de ChronoScope (generados por semilla, imposibles de haber visto) son una señal de honestidad complementaria a los casos reales.'
          : 'Public benchmarks only guarantee clean evaluation for models trained on THEIR pretraining splits; a foundation model trained on another corpus may have seen the test data. That is why ChronoScope\'s synthetic cases (seed-generated, impossible to have seen) are an honesty signal complementary to the real cases.'}
        {' '}<Cite id="gifteval" />
      </Callout>
    </div>
  );

  const calibrated = (
    <div className="prose">
      <p>{es
        ? 'Más allá del punto: TODA salida de la escalera es cuantílica, y el banco de streaming añade la capa "más allá del SOTA en la práctica": el mismo pronosticador puntual con intervalos que se auto-corrigen en línea.'
        : 'Beyond the point: EVERY ladder output is quantile-based, and the streaming bench adds the beyond-SOTA-in-practice layer: the same point forecaster with intervals that self-correct online.'}</p>
      <h4>Adaptive Conformal Inference (ACI)</h4>
      <Equation tex={String.raw`\alpha_{t+1} = \alpha_t + \gamma\,(\alpha^{*} - \text{miss}_t), \qquad \hat q_t = \text{Quantile}_{1-\alpha_t}\{s_1, \ldots, s_t\}`} caption={es ? 'La mis-cobertura efectiva se ajusta con cada verdad revelada; la cobertura de largo plazo converge al objetivo bajo deriva arbitraria (sin intercambiabilidad).' : 'The effective miscoverage adjusts with each revealed truth; long-run coverage converges to the target under arbitrary drift (no exchangeability).'} />
      <h4>Conformal PID</h4>
      <p>{es
        ? 'La calibración como problema de control: términos Proporcional + Integral + Derivativo sobre el error de cobertura (ACI es el caso especial solo-integral, kp = kd = 0, verificado por test). P y D compran mejores transientes: recuperación más rápida tras un cambio de régimen.'
        : 'Calibration as a control problem: Proportional + Integral + Derivative terms on the coverage error (ACI is the integral-only special case, kp = kd = 0, asserted by test). P and D buy better transients: faster recovery after a regime change.'}</p>
      <p>{es
        ? 'Implementado en preqts (nuestro paquete PyPI), calibrando POR HORIZONTE: cada lead time mantiene su propio buffer y controlador, porque la mis-calibración crece con el lead.'
        : 'Implemented in preqts (our PyPI package), calibrating PER HORIZON: each lead time keeps its own buffer and controller, because miscalibration grows with lead.'}</p>
    </div>
  );

  return (
    <section className="page-body prose">
      <h2>{es ? 'Metodología' : 'Methodology'}</h2>
      <p className="cs-lead">{es
        ? 'La escalera completa de 19 métodos, familia por familia, con la matemática real de cada una: qué computa, cuándo gana y cuándo falla. El Benchmark muestra estos métodos medidos; esta página explica qué son.'
        : 'The full 19-method ladder, family by family, with each one\'s real math: what it computes, when it wins, and when it fails. The Benchmark shows these methods measured; this page explains what they are.'}</p>

      <svg viewBox="0 0 680 150" width="100%" style={{ maxWidth: 680, display: 'block', margin: '0.8rem auto', font: '10px var(--font-sans, sans-serif)' }} role="img" aria-label={es ? 'la escalera de 19 métodos por familia, del naive a los fundacionales' : 'the 19-method ladder by family, from the naive to the foundation models'}>
        {(es
          ? [['Clásicos', '5 · en vivo (TS)', 'naive, SES, Holt, HW, Theta', 20, 108], ['Estadísticos', '3 · horneados', 'AutoARIMA, ETS, Theta', 150, 84], ['ML', '1 · horneado', 'LightGBM en rezagos', 280, 60], ['Profundos', '6 · GPU ×2 impl.', 'NLinear, DLinear, NHITS', 410, 36], ['Fundacionales', '4 · zero-shot', 'Bolt, Chronos-2, TimesFM, TiRex-2', 540, 12]]
          : [['Classical', '5 · live (TS)', 'naive, SES, Holt, HW, Theta', 20, 108], ['Statistical', '3 · baked', 'AutoARIMA, ETS, Theta', 150, 84], ['ML', '1 · baked', 'LightGBM on lags', 280, 60], ['Deep', '6 · GPU ×2 impl.', 'NLinear, DLinear, NHITS', 410, 36], ['Foundation', '4 · zero-shot', 'Bolt, Chronos-2, TimesFM, TiRex-2', 540, 12]]
        ).map(([fam, count, names, x, y]) => (
          <g key={fam as string}>
            <rect x={x as number} y={y as number} width={126} height={40} rx={6} fill="var(--color-surface)" stroke="var(--color-accent)" />
            <text x={(x as number) + 63} y={(y as number) + 15} textAnchor="middle" fill="var(--color-fg)" fontSize="9.5" fontWeight="600">{fam} <tspan fill="var(--color-fg-subtle)" fontWeight="400">{count}</tspan></text>
            <text x={(x as number) + 63} y={(y as number) + 30} textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="8">{names}</text>
          </g>
        ))}
        <line x1="20" y1="146" x2="672" y2="146" stroke="var(--color-border)" />
        <text x="20" y="140" fill="var(--color-fg-faint)" fontSize="8.5">{es ? 'costo por serie: microsegundos' : 'per-series cost: microseconds'}</text>
        <text x="672" y="10" textAnchor="end" fill="var(--color-fg-faint)" fontSize="8.5">{es ? 'pre-entrenado en miles de millones de obs.' : 'pretrained on billions of observations'}</text>
      </svg>
      <SubTabs
        ariaLabel="method families"
        tabs={[
          { id: 'classical', label: es ? 'Clásicos (5, en vivo)' : 'Classical (5, live)', content: classical },
          { id: 'statistical', label: es ? 'Estadísticos (3)' : 'Statistical (3)', content: statistical },
          { id: 'ml', label: 'ML (LightGBM)', content: ml },
          { id: 'deep', label: es ? 'Profundos (6, GPU)' : 'Deep (6, GPU)', content: deep },
          { id: 'foundation', label: es ? 'Fundacionales (4, zero-shot)' : 'Foundation (4, zero-shot)', content: foundation },
          { id: 'calibrated', label: es ? 'Calibrados (ACI/PID)' : 'Calibrated (ACI/PID)', content: calibrated },
        ]}
      />
      <Refs ids={['mase', 'theta', 'theta-ses', 'm5', 'lightgbm', 'dlinear', 'patchtst', 'itransformer', 'nhits', 'chronos', 'chronos2', 'timesfm', 'tirex2', 'moirai', 'fm-survey', 'gifteval']} label={es ? 'Referencias' : 'References'} />
    </section>
  );
}
