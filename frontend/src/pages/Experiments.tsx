import { Callout, Cite, Equation, Refs, useShellLang } from '@fasl-work/caos-app-shell';

// Experiments: the evaluation design (rolling-origin + prequential protocols, the metric suite with its
// math, the 12-case scenario matrix and what each teaches). Transcribed from the metrics/protocols dossiers.
export default function Experiments() {
  const es = useShellLang() === 'es';
  return (
    <section className="page-body prose">
      <h2>{es ? 'Experimentos' : 'Experiments'}</h2>
      <p className="cs-lead">{es
        ? 'El diseño experimental: cómo se evalúa cada método (para que la comparación sea justa y sin fuga), con qué métricas, y sobre qué matriz de escenarios, cada escenario elegido para ejercitar UNA familia del kit de análisis.'
        : 'The experimental design: how every method is scored (so the comparison is fair and leakage-free), with which metrics, and over which scenario matrix, each scenario chosen to exercise ONE family of the analysis toolkit.'}</p>

      <h3>{es ? 'El protocolo: origen móvil + prequential' : 'The protocol: rolling origin + prequential'}</h3>
      <p>{es
        ? 'Cada método se evalúa con un backtest de ORIGEN MÓVIL sin fuga: en cada corte, el modelo ajusta/condiciona SOLO sobre la historia hasta el corte y predice el horizonte completo fuera de muestra; el corte avanza y se repite. Los métodos baratos reciben muchas ventanas; los pesados un presupuesto acotado (honesto: se registra n_windows por método). Encima, el banco de STREAMING evalúa de forma prequential (Dawid 1984): predecir, observar, actualizar, con el estado del modelo acarreado paso a paso, que es como opera el pronóstico real.'
        : 'Every method is scored by a leakage-safe ROLLING-ORIGIN backtest: at each cutoff the model fits/conditions ONLY on the history up to the cutoff and predicts the full horizon out-of-sample; the cutoff advances and repeats. Cheap methods get many windows; heavy ones a bounded budget (honest: n_windows is recorded per method). On top, the STREAMING bench evaluates prequentially (Dawid 1984): predict, observe, update, with model state carried step to step, which is how real forecasting operates.'}
        {' '}<Cite id="prequential" /></p>

      <h3>{es ? 'Las métricas (y su matemática)' : 'The metrics (and their math)'}</h3>
      <Equation tex={String.raw`\text{MASE} = \frac{\frac{1}{h}\sum_{i=1}^{h} |y_{t+i} - \hat y_{t+i}|}{\frac{1}{T-m}\sum_{t=m+1}^{T} |y_t - y_{t-m}|}`} caption={es ? 'MASE: error absoluto escalado por el MAE in-sample del naive estacional. Menor que 1 = le ganas al naive; libre de escala y comparable entre casos (Hyndman y Koehler 2006).' : 'MASE: absolute error scaled by the in-sample MAE of the seasonal naive. Below 1 = you beat the naive; scale-free and comparable across cases (Hyndman & Koehler 2006).'} />
      <Equation tex={String.raw`\text{WQL} = \frac{\sum_{q \in Q} \sum_{i} 2\,\rho_q\big(y_{t+i} - \hat y^{(q)}_{t+i}\big)}{\sum_i |y_{t+i}|}, \qquad \rho_q(u) = u\,(q - \mathbf{1}\{u < 0\})`} caption={es ? 'WQL: pérdida pinball agregada sobre la grilla de cuantiles, normalizada. Es la aproximación discreta del CRPS: mide la DISTRIBUCIÓN pronosticada, no solo el punto.' : 'WQL: pinball loss aggregated over the quantile grid, normalized. It is the discretized approximation of CRPS: it scores the forecast DISTRIBUTION, not just the point.'} />
      <p>{es
        ? 'Cada método reporta además su cobertura empírica del intervalo 10/90 (nominal 80%): un intervalo que no cubre lo que promete es un defecto aunque el punto sea bueno. En el banco de streaming, la cobertura es una TRAYECTORIA rodante, que es donde los calibradores ACI/PID muestran su valor.'
        : 'Each method also reports its empirical coverage of the 10/90 interval (nominal 80%): an interval that does not cover what it promises is a defect even when the point is good. In the streaming bench, coverage is a rolling TRAJECTORY, which is where the ACI/PID calibrators show their value.'}
        {' '}<Cite id="mase" /></p>

      <h3>{es ? 'La matriz de escenarios (12 casos)' : 'The scenario matrix (12 cases)'}</h3>
      <p>{es
        ? 'Cada caso ejercita una familia del análisis, de modo que el diagnóstico EXPLICA la tabla de posiciones:'
        : 'Each case exercises one analysis family, so the diagnosis EXPLAINS the leaderboard:'}</p>
      <ul>
        <li><b>SEAS_hourly / TRND_seasonal</b>: {es ? 'estacionalidad limpia y tendencia+estación; los métodos estacionales deben ganar (periodograma + Fs los diagnostican).' : 'clean seasonality and trend+season; seasonal methods must win (periodogram + Fs diagnose them).'}</li>
        <li><b>MSEA_daily_weekly</b>: {es ? 'ciclos diario + semanal superpuestos; dos picos espectrales, MSTL los separa; los métodos de un solo m pierden el componente semanal.' : 'superposed daily + weekly cycles; two spectral peaks, MSTL splits them; single-m methods miss the weekly component.'}</li>
        <li><b>INTM_demand</b>: {es ? 'demanda intermitente (mayormente ceros); difícil para los suavizadores.' : 'intermittent demand (mostly zeros); hard for smoothers.'}</li>
        <li><b>BRKV_level_shift</b>: {es ? 'dos quiebres de nivel; PELT los localiza, CUSUM rechaza estabilidad, y los modelos que promedian regímenes tropiezan justo después de cada quiebre.' : 'two level breaks; PELT localizes them, CUSUM rejects stability, and regime-averaging models stumble right after each break.'}</li>
        <li><b>HETV_garch</b>: {es ? 'volatilidad GARCH(1,1) (persistencia 0.95): el punto es aburrido a propósito; la historia es la COBERTURA (ancho fijo falla, ACI/PID la sostienen).' : 'GARCH(1,1) volatility (persistence 0.95): the point is boring on purpose; the story is COVERAGE (fixed width fails, ACI/PID hold it).'}</li>
        <li><b>LMEM_fractional</b>: {es ? 'ARFIMA d=0.35 (H~0.85, verificado con DFA al generar): decaimiento hiperbólico de la ACF; el borde de los modelos de contexto largo.' : 'ARFIMA d=0.35 (H~0.85, DFA-verified at generation): hyperbolic ACF decay; the long-context models\' edge.'}</li>
        <li><b>CHAO_mackey</b>: {es ? 'caos Mackey-Glass (test 0-1 K=0.87, Lyapunov positivo, verificados): pronosticable a corto plazo, el error crece a la tasa de Lyapunov; la curva por horizonte es la lectura estrella.' : 'Mackey-Glass chaos (0-1 test K=0.87, positive Lyapunov, verified): short-horizon forecastable, error grows at the Lyapunov rate; the per-horizon curve is the star read-out.'}</li>
        <li><b>REAL_electricity / REAL_pm25</b>: {es ? 'datos reales CC-BY (carga eléctrica UCI; PM2.5 de Beijing con colas pesadas, curtosis ~5).' : 'CC-BY real data (UCI electricity load; heavy-tailed Beijing PM2.5, kurtosis ~5).'}</li>
        <li><b>RWLK_noise / CTRL_white_noise</b>: {es ? 'los controles de honestidad: nadie debería ganar por mucho; una brecha grande delata fuga en el harness.' : 'the honesty controls: nobody should win by much; a big gap betrays harness leakage.'}</li>
      </ul>

      <Callout variant="honest" title={es ? 'Los controles negativos son parte del diseño' : 'The negative controls are part of the design'}>
        {es
          ? 'Un atlas que solo muestra casos donde los modelos sofisticados ganan está sobre-vendiendo. Los controles (ruido blanco, caminata aleatoria) y el caso GARCH (punto deliberadamente aburrido) existen para que el "no" sea tan visible como el "sí".'
          : 'An atlas showing only cases where sophisticated models win is overselling. The controls (white noise, random walk) and the GARCH case (deliberately boring point forecast) exist so the "no" is as visible as the "yes".'}
      </Callout>

      <Refs ids={['prequential', 'mase', 'tfb', 'fevbench', 'uci-electricity']} label={es ? 'Referencias' : 'References'} />
    </section>
  );
}
