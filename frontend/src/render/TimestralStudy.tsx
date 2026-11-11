import { DocSection, formatNumber, useShellLang } from '@fasl-work/caos-app-shell';
import study from '../data/timestral-study.json';

export function TimestralStudy() {
  const lang = useShellLang();
  const es = lang === 'es';
  const fmt = (value: number, digits = 4) => formatNumber(value, lang, { digits });
  const primary = study.primary;
  const [low, high] = primary.case_reweighting_percentile_95;
  const rows = study.checkpoints.filter(row => row.group === 'all15');
  return <DocSection area="comparison" noRefsReason={{ en: "The paired study links to its numerical evidence below.", es: "El estudio emparejado enlaza su evidencia numérica." }} title={{ en: 'Timestral on the common final blocks', es: 'Timestral en los bloques finales comunes' }}>
    <p>{es
      ? 'Se ejecutaron cuatro tamaños en CPU con el prefijo contiguo de cada caso. Los quince bloques reservados incluyen cuatro extractos reales y once casos generados.'
      : 'Four checkpoint sizes ran on CPU using each case’s contiguous prefix. The fifteen reserved blocks include four authentic excerpts and eleven generated cases.'}</p>
    <div className="cs-table-scroll">
      <table className="cs-table">
        <caption>{es ? 'Promedios por caso, cobertura nominal del 80 %' : 'Case-weighted means, nominal coverage 80%'}</caption>
        <thead><tr><th scope="col">{es ? 'Modelo' : 'Checkpoint'}</th><th scope="col">MASE</th><th scope="col">MSIS</th><th scope="col">{es ? 'Cobertura' : 'Coverage'}</th></tr></thead>
        <tbody>{rows.map(row => <tr key={row.model}>
          <th scope="row">{row.model.split('/')[1]}</th>
          <td>{fmt(row.mean_metrics.mase)}</td><td>{fmt(row.mean_metrics.msis)}</td>
          <td>{fmt(100 * row.mean_metrics.coverage, 2)}%</td>
        </tr>)}</tbody>
      </table>
    </div>
    <p>{es ? 'Diferencia media de MASE, Timestral-209M menos AutoTheta' : 'Mean MASE difference, Timestral-209M minus AutoTheta'}: {fmt(primary.mean_difference)}.
      {' '}{es ? 'Intervalo exploratorio del 95 % al remuestrear los casos emparejados' : 'Exploratory 95% interval from reweighting the paired cases'}: [{fmt(low)}, {fmt(high)}].
      {' '}{es ? 'Timestral tuvo menor error en' : 'Timestral had lower error on'} {primary.negative}/{primary.cases} {es ? 'casos.' : 'cases.'}</p>
    <p>{es
      ? 'El estudio usó pronósticos univariantes sin covariables. La cobertura resume estos casos seleccionados. La calibración en nuevas poblaciones y los efectos de covariables quedan por medir.'
      : 'The study used univariate forecasts without covariates. Coverage summarizes these selected cases. Calibration on new populations and covariate effects remain unmeasured.'}</p>
    <a href="https://github.com/fsantibanezleal/CAOS_RES_ChronoScope/tree/a9b83ea/docs/research/timestral-v1">
      {es ? 'Protocolo, pronósticos y verificación' : 'Protocol, forecasts and validation'}
    </a>
  </DocSection>;
}
