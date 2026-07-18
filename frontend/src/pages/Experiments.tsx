import { Callout, Cite, Equation, Refs, useShellLang } from '@fasl-work/caos-app-shell';

// Experiments: the evaluation design (rolling-origin + prequential protocols, the metric suite with its
// math, the 15-case scenario matrix and what each teaches). Transcribed from the metrics/protocols dossiers.
export default function Experiments() {
  const es = useShellLang() === 'es';
  return (
    <section className="page-body prose">
      <h2>{es ? 'Experimentos' : 'Experiments'}</h2>
      <p className="cs-lead">{es
        ? 'El diseño experimental: cómo se evalúa cada método (para que la comparación sea justa y sin fuga), con qué métricas, y sobre qué matriz de escenarios, cada escenario elegido para ejercitar una familia del kit de análisis.'
        : 'The experimental design: how every method is scored (so the comparison is fair and leakage-free), with which metrics, and over which scenario matrix, each scenario chosen to exercise one family of the analysis toolkit.'}</p>

      <h3>{es ? 'El protocolo: origen móvil + prequential' : 'The protocol: rolling origin + prequential'}</h3>
      <p>{es
        ? 'Cada método se evalúa con un backtest de origen móvil sin fuga: en cada corte, el modelo ajusta/condiciona solo sobre la historia hasta el corte y predice el horizonte completo fuera de muestra; el corte avanza y se repite. Los métodos baratos reciben muchas ventanas; los pesados un presupuesto acotado (honesto: se registra n_windows por método). Encima, el banco de streaming evalúa de forma prequential (Dawid 1984): predecir, observar, actualizar, con el estado del modelo acarreado paso a paso, que es como opera el pronóstico real.'
        : 'Every method is scored by a leakage-safe rolling-origin backtest: at each cutoff the model fits/conditions only on the history up to the cutoff and predicts the full horizon out-of-sample; the cutoff advances and repeats. Cheap methods get many windows; heavy ones a bounded budget (honest: n_windows is recorded per method). On top, the streaming bench evaluates prequentially (Dawid 1984): predict, observe, update, with model state carried step to step, which is how real forecasting operates.'}
        {' '}<Cite id="prequential" /></p>

      <svg viewBox="0 0 680 170" width="100%" style={{ maxWidth: 680, display: 'block', margin: '0.8rem auto', font: '11px var(--font-sans, sans-serif)' }} role="img" aria-label={es ? 'backtest de origen móvil: el corte avanza, el modelo nunca ve el futuro' : 'rolling-origin backtest: the cutoff advances, the model never sees the future'}>
        <text x="8" y="16" fill="var(--color-fg)" fontSize="10">{es ? 'origen móvil: en cada corte, ajustar solo con la historia y predecir h pasos fuera de muestra' : 'rolling origin: at each cutoff, fit only on history and predict h steps out-of-sample'}</text>
        {[0, 1, 2].map((k) => {
          const y0 = 30 + k * 36;
          const trainW = 240 + k * 60;
          return (
            <g key={k}>
              <text x="8" y={y0 + 14} fill="var(--color-fg-subtle)" fontSize="9">{es ? `corte ${k + 1}` : `cutoff ${k + 1}`}</text>
              <rect x="58" y={y0} width={trainW} height="20" rx="3" fill="var(--color-surface)" stroke="var(--color-accent)" />
              <text x={58 + trainW / 2} y={y0 + 14} textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? 'historia (train)' : 'history (train)'}</text>
              <rect x={58 + trainW + 2} y={y0} width="70" height="20" rx="3" fill="var(--color-surface)" stroke="#3fb950" strokeDasharray="4 2" />
              <text x={58 + trainW + 37} y={y0 + 14} textAnchor="middle" fill="#3fb950" fontSize="9">h</text>
              <line x1={58 + trainW + 1} y1={y0 - 3} x2={58 + trainW + 1} y2={y0 + 23} stroke="var(--color-fg-subtle)" strokeDasharray="3 2" />
            </g>
          );
        })}
        <text x="58" y="158" fill="var(--color-fg-faint)" fontSize="9">{es ? 'el corte solo avanza: ninguna observación del horizonte entra al ajuste (sin fuga); las métricas promedian sobre todos los cortes' : 'the cutoff only advances: no horizon observation enters the fit (leakage-safe); metrics average over all cutoffs'}</text>
      </svg>

      <h3>{es ? 'Las métricas (y su matemática)' : 'The metrics (and their math)'}</h3>
      <Equation tex={String.raw`\text{MASE} = \frac{\frac{1}{h}\sum_{i=1}^{h} |y_{t+i} - \hat y_{t+i}|}{\frac{1}{T-m}\sum_{t=m+1}^{T} |y_t - y_{t-m}|}`} caption={es ? 'MASE: error absoluto escalado por el MAE in-sample del naive estacional. Menor que 1 le gana al naive; libre de escala y comparable entre casos (Hyndman y Koehler 2006).' : 'MASE: absolute error scaled by the in-sample MAE of the seasonal naive. Below 1 beats the naive; scale-free and comparable across cases (Hyndman & Koehler 2006).'} />
      <Equation tex={String.raw`\text{WQL} = \frac{\sum_{q \in Q} \sum_{i} 2\,\rho_q\big(y_{t+i} - \hat y^{(q)}_{t+i}\big)}{\sum_i |y_{t+i}|}, \qquad \rho_q(u) = u\,(q - \mathbf{1}\{u < 0\})`} caption={es ? 'WQL: pérdida pinball agregada sobre la grilla de cuantiles, normalizada. Es la aproximación discreta del CRPS: mide la distribución pronosticada, no solo el punto.' : 'WQL: pinball loss aggregated over the quantile grid, normalized. It is the discretized approximation of CRPS: it scores the forecast distribution, not just the point.'} />
      <Equation tex={String.raw`\text{MSIS} = \frac{\frac{1}{h}\sum_{i=1}^{h}\Big[(u_i - l_i) + \tfrac{2}{\alpha}(l_i - y_i)\,\mathbf{1}\{y_i < l_i\} + \tfrac{2}{\alpha}(y_i - u_i)\,\mathbf{1}\{y_i > u_i\}\Big]}{\frac{1}{T-m}\sum_{t=m+1}^{T} |y_t - y_{t-m}|}`} caption={es ? 'MSIS (Gneiting y Raftery 2007; la métrica de intervalo de M4, con α = 0.2 para la banda del 80%): ancho del intervalo más una multa de 2/α por unidad de falla, escalado como MASE. Pone el trade-off ancho-vs-cobertura en un solo número: un intervalo angosto que falla no puede verse bien.' : 'MSIS (Gneiting & Raftery 2007; the M4 interval metric, with α = 0.2 for the 80% band): interval width plus a 2/α penalty per unit of miss, scaled like MASE. It prices the width-vs-coverage trade-off in a single number: a narrow interval that misses cannot look good.'} />
      <p>{es
        ? 'Cada método reporta además su cobertura empírica del intervalo 10/90 (nominal 80%): un intervalo que no cubre lo que promete es un defecto aunque el punto sea bueno. En el banco de streaming, la cobertura es una trayectoria rodante, que es donde los calibradores ACI/PID muestran su valor. Se reportan también MAE/RMSE (en unidades de la serie) y sMAPE (la convención de las competencias M), y desde preqts 0.3 la curva de error por horizonte: la media de |error| en el paso h sobre todos los cortes, escalada por el naive (una MASE por paso; la pestaña Horizonte del workbench). La forma de esa curva es un diagnóstico en sí misma: meseta = reversión a la media, crecimiento tipo raíz = caminata aleatoria, crecimiento exponencial que satura = caos determinista.'
        : 'Each method also reports its empirical coverage of the 10/90 interval (nominal 80%): an interval that does not cover what it promises is a defect even when the point is good. In the streaming bench, coverage is a rolling trajectory, which is where the ACI/PID calibrators show their value. MAE/RMSE (in series units) and sMAPE (the M-competition convention) are reported too, and since preqts 0.3 the per-horizon error curve: mean |error| at lead h over all backtest cutoffs, scaled by the naive (a per-lead MASE; the workbench Horizon tab). The shape of that curve is a diagnosis in itself: a plateau = mean reversion, square-root growth = a random walk, exponential growth that saturates = deterministic chaos.'}
        {' '}<Cite id="mase" /> <Cite id="msis" /></p>

      <h3>{es ? 'La matriz de escenarios (15 casos)' : 'The scenario matrix (15 cases)'}</h3>
      <p>{es
        ? 'Cada caso ejercita una familia del análisis, de modo que el diagnóstico explica la tabla de posiciones:'
        : 'Each case exercises one analysis family, so the diagnosis explains the leaderboard:'}</p>
      <ul>
        <li><b>SEAS_hourly / TRND_seasonal</b>: {es ? 'estacionalidad limpia y tendencia+estación; los métodos estacionales deben ganar (periodograma + Fs los diagnostican).' : 'clean seasonality and trend+season; seasonal methods must win (periodogram + Fs diagnose them).'}</li>
        <li><b>MSEA_daily_weekly</b>: {es ? 'ciclos diario + semanal superpuestos; dos picos espectrales, MSTL los separa; los métodos de un solo m pierden el componente semanal.' : 'superposed daily + weekly cycles; two spectral peaks, MSTL splits them; single-m methods miss the weekly component.'}</li>
        <li><b>INTM_demand</b>: {es ? 'demanda intermitente (mayormente ceros); difícil para los suavizadores.' : 'intermittent demand (mostly zeros); hard for smoothers.'}</li>
        <li><b>BRKV_level_shift</b>: {es ? 'dos quiebres de nivel; PELT los localiza, CUSUM rechaza estabilidad, y los modelos que promedian regímenes tropiezan justo después de cada quiebre.' : 'two level breaks; PELT localizes them, CUSUM rejects stability, and regime-averaging models stumble right after each break.'}</li>
        <li><b>HETV_garch</b>: {es ? 'volatilidad GARCH(1,1) (persistencia 0.95): el punto es aburrido a propósito; la historia es la cobertura (ancho fijo falla, ACI/PID la sostienen).' : 'GARCH(1,1) volatility (persistence 0.95): the point is boring on purpose; the story is coverage (fixed width fails, ACI/PID hold it).'}</li>
        <li><b>LMEM_fractional</b>: {es ? 'ARFIMA d=0.35 (H~0.85, verificado con DFA al generar): decaimiento hiperbólico de la ACF; el borde de los modelos de contexto largo.' : 'ARFIMA d=0.35 (H~0.85, DFA-verified at generation): hyperbolic ACF decay; the long-context models\' edge.'}</li>
        <li><b>CHAO_mackey</b>: {es ? 'caos Mackey-Glass (test 0-1 K=0.87, Lyapunov positivo, verificados): pronosticable a corto plazo, el error crece a la tasa de Lyapunov; la curva por horizonte es la lectura estrella.' : 'Mackey-Glass chaos (0-1 test K=0.87, positive Lyapunov, verified): short-horizon forecastable, error grows at the Lyapunov rate; the per-horizon curve is the star read-out.'}</li>
        <li><b>REAL_electricity / REAL_pm25</b>: {es ? 'datos reales CC-BY (carga eléctrica UCI; PM2.5 de Beijing con colas pesadas, curtosis ~5).' : 'CC-BY real data (UCI electricity load; heavy-tailed Beijing PM2.5, kurtosis ~5).'}</li>
        <li><b>REAL_m4_hourly / REAL_m4_daily</b>: {es ? 'series reales de la competencia M4 (Monash CC-BY) a dos frecuencias (horaria m=24, diaria m=7): estacionalidad real, medida y no diseñada; la prueba zero-shot de los modelos fundacionales sobre datos de benchmark genuinos.' : 'real M4-competition series (Monash CC-BY) at two frequencies (hourly m=24, daily m=7): real seasonality, measured not designed; the zero-shot test of the foundation models on genuine benchmark data.'}</li>
        <li><b>EXOG_promo</b>: {es ? 'un driver exógeno conocido-a-futuro (promociones programadas); el banco de streaming muestra la política de covariables (ridge aware vs blind), la pieza que ningún harness público evalúa.' : 'a known-future exogenous driver (scheduled promotions); the streaming bench shows the covariate policy (ridge aware vs blind), the piece no public harness evaluates.'}</li>
        <li><b>RWLK_noise / CTRL_white_noise</b>: {es ? 'los controles de honestidad: nadie debería ganar por mucho; una brecha grande delata fuga en el harness.' : 'the honesty controls: nobody should win by much; a big gap betrays harness leakage.'}</li>
      </ul>

      <h3>{es ? 'Los generadores, con sus ecuaciones reales' : 'The generators, with their actual equations'}</h3>
      <p>{es
        ? 'Cada caso sintético profundo es un proceso canónico de la literatura, generado con semilla fija (hashlib por caso, no el hash() salteado de Python). Las ecuaciones de abajo son las que ejecuta el código (chronoscopelab/cases/forecast_cases.py), no una aproximación:'
        : 'Each deep synthetic case is a canonical process from the literature, generated under a fixed seed (per-case hashlib, not Python\'s salted hash()). The equations below are what the code executes (chronoscopelab/cases/forecast_cases.py), not an approximation:'}</p>
      <Equation tex={String.raw`\sigma^2_t = \omega + \alpha_1\,\varepsilon^2_{t-1} + \beta_1\,\sigma^2_{t-1}, \qquad \varepsilon_t = \sigma_t z_t, \qquad y_t = 100 + 0.25\textstyle\sum_{s\le t}\varepsilon_s`} caption={es
        ? 'HETV_garch: GARCH(1,1) de Bollerslev (1986) con ω=0.2, α₁=0.15, β₁=0.80 (persistencia α₁+β₁=0.95): la varianza se agrupa en rachas; el punto es casi caminata, la historia es el intervalo.'
        : 'HETV_garch: Bollerslev\'s (1986) GARCH(1,1) with ω=0.2, α₁=0.15, β₁=0.80 (persistence α₁+β₁=0.95): variance clusters in bursts; the point path is near-walk, the story is the interval.'} />
      <Equation tex={String.raw`y_t = 50 + (1-B)^{-d}\varepsilon_t, \quad \psi_k = \frac{\Gamma(k+d)}{\Gamma(k+1)\,\Gamma(d)}, \quad d = 0.35`} caption={es
        ? 'LMEM_fractional: ruido fraccionalmente integrado (Granger-Joyeux 1980; Hosking 1981) vía la expansión MA(∞) truncada: ACF de decaimiento hiperbólico, H ≈ d + 0.5 ≈ 0.85 (verificado con DFA al generar).'
        : 'LMEM_fractional: fractionally-integrated noise (Granger-Joyeux 1980; Hosking 1981) via the truncated MA(∞) expansion: hyperbolic ACF decay, H ≈ d + 0.5 ≈ 0.85 (DFA-verified at generation).'} />
      <Equation tex={String.raw`\frac{dx}{dt} = \frac{0.2\,x(t-\tau)}{1 + x(t-\tau)^{10}} - 0.1\,x(t), \qquad \tau = 17`} caption={es
        ? 'CHAO_mackey: la ecuación diferencial con retardo de Mackey-Glass (1977), caótica en τ=17; integrada por Euler (dt=0.1) y muestreada cada 6 unidades (el test 0-1 malinterpreta el caos sobremuestreado como regular, una caveat documentada; este paso da K≈0.9 con Lyapunov positivo).'
        : 'CHAO_mackey: the Mackey-Glass (1977) delay differential equation, chaotic at τ=17; Euler-integrated (dt=0.1) and sampled every 6 time units (the 0-1 test misreads oversampled chaos as regular, a documented caveat; this stride gives K≈0.9 with a positive Lyapunov exponent).'} />
      <Equation tex={String.raw`y_t = 50 + 15\,\mathbf{1}\{t \ge n/3\} - 25\,\mathbf{1}\{t \ge 2n/3\} + 6\sin\!\tfrac{2\pi t}{12} + \varepsilon_t`} caption={es
        ? 'BRKV_level_shift (n=300): dos quiebres limpios de nivel en t=100 y t=200 sobre un ciclo estacional; PELT debe localizarlos y los modelos que promedian regímenes tropiezan justo después de cada quiebre.'
        : 'BRKV_level_shift (n=300): two clean level breaks at t=100 and t=200 over a seasonal cycle; PELT must localize them, and regime-averaging models stumble right after each break.'} />
      <p>{es
        ? 'Los demás siguen el mismo estándar: MSEA superpone ciclos de 24 y 168 pasos (dos picos espectrales); INTM es Bernoulli(0.25) × Gamma(2, 4) (demanda intermitente, mayormente ceros); los controles son ruido blanco N(0,25) y una caminata aleatoria con paso N(0,1). Los parámetros exactos viven en el registro de casos y cada caso tiene su página en docs/cases/.'
        : 'The rest follow the same standard: MSEA superposes 24- and 168-step cycles (two spectral peaks); INTM is Bernoulli(0.25) × Gamma(2, 4) (intermittent demand, mostly zeros); the controls are N(0,25) white noise and a random walk with N(0,1) steps. The exact parameters live in the case registry, and every case has its page in docs/cases/.'}</p>

      <Callout variant="honest" title={es ? 'Los controles negativos son parte del diseño' : 'The negative controls are part of the design'}>
        {es
          ? 'Un atlas que solo muestra casos donde los modelos sofisticados ganan está sobre-vendiendo. Los controles (ruido blanco, caminata aleatoria) y el caso GARCH (punto deliberadamente aburrido) existen para que el "no" sea tan visible como el "sí".'
          : 'An atlas showing only cases where sophisticated models win is overselling. The controls (white noise, random walk) and the GARCH case (deliberately boring point forecast) exist so the "no" is as visible as the "yes".'}
      </Callout>

      <Refs ids={['prequential', 'mase', 'msis', 'tfb', 'fevbench', 'uci-electricity', 'garch', 'granger-joyeux', 'hosking', 'mackey-glass']} label={es ? 'Referencias' : 'References'} />
    </section>
  );
}
