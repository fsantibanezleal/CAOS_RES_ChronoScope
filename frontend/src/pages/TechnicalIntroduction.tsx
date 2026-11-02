import { Callout, Cite, DocSection, Equation, Figure, Glossary, useShellLang } from '@fasl-work/caos-app-shell';

export default function TechnicalIntroduction() {
  const es = useShellLang() === 'es';
  const t = (en: string, translated: string) => es ? translated : en;
  return <>
    <DocSection title={{ en: 'The forecasting decision', es: 'La decisión de pronóstico' }} area="problem" refs={['tfb', 'mase']}>
      <p>{t('A demand planner requests stock before customer orders arrive, while an operations manager allocates equipment and staff against that request. The useful forecast depends on its deadline, lead time and available information. The same prediction error can have different consequences when capacity is expensive to revise or a shortage causes a long delay.',
        'Un planificador solicita inventario antes de recibir pedidos y operaciones asigna equipos y personal según esa solicitud. El pronóstico útil depende del plazo, la anticipación y la información disponible. Un mismo error tiene consecuencias distintas cuando modificar capacidad resulta costoso o un faltante genera una demora prolongada para atender la demanda.')}</p>
      <p>{t('Model selection needs evidence from the intended task. The atlas places seasonal, trending, intermittent, changing-variance and control series beside real data excerpts, so readers can inspect failures as well as successes. Fifteen selected cases provide a bounded comparison; their aggregate ranking does not identify a universally preferable model for every organisation or operating decision.',
        'Seleccionar modelos requiere evidencia de la tarea prevista. El atlas reúne series estacionales, tendenciales, intermitentes, de varianza cambiante y de control junto a extractos reales. Esto permite examinar fallas y aciertos. Quince casos seleccionados constituyen una comparación delimitada; su ranking agregado no identifica un modelo universalmente preferible para cada organización o decisión operativa.')} <Cite id="tfb" /></p>
    </DocSection>
    <DocSection title={{ en: 'Information and temporal order', es: 'Información y orden temporal' }} area="principles" refs={['prequential', 'mase']}>
      <p>{t('A prediction uses a historical prefix and covariates genuinely known at its origin. A later observation can update the next forecast but cannot be supplied to an earlier one. This distinction matters for promotions and revised measurements: a value present in a historical file is not automatically information that was operationally available before the commitment.',
        'Una predicción utiliza un prefijo histórico y las covariables conocidas en su origen. Una observación posterior puede actualizar el siguiente pronóstico, pero no el anterior. Esta distinción importa para promociones y mediciones revisadas: que un valor figure en un archivo histórico no demuestra que estuviera disponible antes de comprometer los recursos operativos.')}</p>
      <p>{t('Comparisons also need common targets. The archived rolling experiments allocated different origin budgets to different methods, mixing performance with origin selection. The current final-holdout comparison scores every admitted path on the same block within each case. It records whether a forecast was frozen from the earlier release or recomputed from the corrected light engine.',
        'Las comparaciones también necesitan objetivos comunes. Los experimentos móviles archivados asignaron distintos presupuestos de orígenes por método, mezclando desempeño y selección temporal. La comparación final actual puntúa cada trayectoria sobre el mismo bloque por caso. Además, registra si un pronóstico proviene del archivo anterior o fue recalculado con el motor ligero corregido.')} <Cite id="prequential" /></p>
    </DocSection>
    <DocSection title={{ en: 'Forecasts and scores', es: 'Pronósticos y medidas' }} area="math" refs={['mase', 'prequential']}>
      <Equation tex={String.raw`\widehat y_{t+h\mid t}=f_\theta(y_{1:t},x^{\mathrm{available}}_{1:t+h})`} caption={t('The forecast at lead h uses only the history and covariates available at origin t.', 'El pronóstico al paso h usa la historia y las covariables disponibles en el origen t.')} />
      <Equation tex={String.raw`\operatorname{MASE}=\frac{H^{-1}\sum_{h=1}^{H}|y_{t+h}-\widehat y_{t+h\mid t}|}{(t-m)^{-1}\sum_{i=m+1}^{t}|y_i-y_{i-m}|}`} caption={t('MASE scales holdout absolute error by the mean seasonal difference in the training history.', 'MASE divide el error absoluto reservado por la diferencia estacional media de la historia.')} />
      <Equation tex={String.raw`\rho_\tau(e)=\max\{\tau e,(\tau-1)e\},\qquad \widehat C=\frac1H\sum_{h=1}^{H}\mathbf1\{q_{0.1,h}\le y_{t+h}\le q_{0.9,h}\}`} caption={t('Pinball loss scores quantiles; empirical coverage counts outcomes inside the stated interval.', 'La pérdida pinball puntúa cuantiles; la cobertura cuenta observaciones dentro del intervalo.')} />
      <Glossary entries={[
        { term: 't', definition: { en: 'forecast origin, the final observed index', es: 'origen, último índice observado' } },
        { term: 'h', definition: { en: 'lead time from the origin', es: 'anticipación desde el origen' } },
        { term: 'H', definition: { en: 'number of reserved observations', es: 'cantidad de observaciones reservadas' } },
        { term: 'm', definition: { en: 'declared seasonal period', es: 'período estacional declarado' } },
        { term: 'y', definition: { en: 'target value in the series units', es: 'valor objetivo en sus unidades' } },
        { term: 'x', definition: { en: 'covariates admitted by the arrival policy', es: 'covariables admitidas según su llegada' } },
        { term: 'θ', definition: { en: 'parameters fitted before forecasting', es: 'parámetros ajustados antes de pronosticar' } },
        { term: 'τ', definition: { en: 'quantile probability level', es: 'nivel de probabilidad del cuantil' } },
        { term: 'e', definition: { en: 'observation minus forecast quantile', es: 'observación menos cuantil pronosticado' } },
        { term: 'q', definition: { en: 'quantile at the stated level and lead', es: 'cuantil al nivel y paso indicados' } },
        { term: 'Ĉ', definition: { en: 'empirical coverage over the reserved block', es: 'cobertura sobre el bloque reservado' } },
      ]} />
    </DocSection>
    <DocSection title={{ en: 'From series to comparison', es: 'De la serie a la comparación' }} area="pipeline" noRefsReason={{ en: 'Describes the source and artifact flow implemented in this repository.', es: 'Describe el flujo de código y artefactos implementado en este repositorio.' }}>
      <ol>
        <li>{t('Validate the series, source licence, seasonal period and information-arrival policy.', 'Validar serie, licencia, período y política de información.')}</li>
        <li>{t('Reserve the final block and fit current light methods using the historical prefix.', 'Reservar el bloque final y ajustar los métodos ligeros con la historia.')}</li>
        <li>{t('Admit frozen heavy-model paths with their source hashes and recorded configuration.', 'Admitir trayectorias pesadas archivadas con hashes y configuración.')}</li>
        <li>{t('Score every path on the same targets and retain the proposal and its ablations.', 'Puntuar las trayectorias sobre los mismos objetivos y conservar propuesta y ablaciones.')}</li>
        <li>{t('Validate the contract and display forecasts, scores, provenance and uncertainty.', 'Validar el contrato y mostrar pronósticos, medidas, procedencia e incertidumbre.')}</li>
      </ol>
      <Figure caption={t('A fixed cutoff separates forecast inputs from the outcomes used to score each path.', 'Un corte fijo separa las entradas de los resultados usados para puntuar cada trayectoria.')}>
        <svg viewBox="0 0 800 145" role="img" aria-label={t('The shared forecast cutoff', 'El corte común del pronóstico')}>
          {[t('History', 'Historia'), t('Origin', 'Origen'), t('Forecast', 'Pronóstico'), t('Outcomes', 'Resultados')].map((s, i) => <g key={s}>
            <rect x={10 + i * 200} y="36" width="180" height="70" rx="10" fill="var(--color-surface-2)" stroke="var(--color-border)" />
            <text x={100 + i * 200} y="78" textAnchor="middle" fontSize="20" fill="var(--color-fg)">{s}</text>
            {i < 3 && <path d={`M${192 + i * 200} 71h15`} stroke="var(--color-accent)" strokeWidth="3" />}
          </g>)}
        </svg>
      </Figure>
    </DocSection>
    <DocSection title={{ en: 'Evidence boundaries', es: 'Límites de la evidencia' }} area="honesty" noRefsReason={{ en: 'States the scope and limitations of the implemented experiment.', es: 'Declara el alcance y las limitaciones del experimento implementado.' }}>
      <p>{t('The common comparison has one final origin per selected case. Heavy forecasts are archived outputs, while corrected smoothing equations and ContextMemory combinations were recomputed. Their scores on these targets do not establish superiority over fresh checkpoint fits, independence from pretraining data, or performance in a particular organisation with different constraints and decision deadlines.',
        'La comparación común tiene un origen final por caso seleccionado. Los pronósticos pesados son resultados archivados; las ecuaciones corregidas y ContextMemory fueron recalculadas. Sus medidas no demuestran superioridad sobre nuevos ajustes, independencia del preentrenamiento ni desempeño en una organización particular que tenga otras restricciones, costos y plazos para decidir sus recursos.')}</p>
      <Callout variant="honest" title={t('What the proposal showed', 'Qué mostró la propuesta')}>
        {t('ContextMemory failed its aggregate comparison against the recency-only ablation. The negative result is retained. Gaussian intervals, combined quantiles and finite coverage trajectories require inspection of width and local errors; their implementation alone supplies no coverage guarantee.', 'ContextMemory no mejoró el resultado agregado de la ablación que usa solo recencia. Se conserva el resultado negativo. Los intervalos gaussianos, cuantiles combinados y trayectorias finitas requieren revisar amplitud y errores locales; implementarlos no proporciona por sí mismo una garantía de cobertura.')}
      </Callout>
    </DocSection>
  </>;
}
