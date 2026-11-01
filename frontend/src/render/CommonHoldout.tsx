import { useState } from 'react';
import { Callout, formatNumber, useShellLang } from '@fasl-work/caos-app-shell';
import type { Reevaluation } from '../lib/reevaluation.types';

export function CommonHoldout({ data }: { data: Reevaluation }) {
  const lang = useShellLang();
  const es = lang === 'es';
  const [caseId, setCaseId] = useState(data.cases[0]?.case_id ?? '');
  const selected = data.cases.find(c => c.case_id === caseId) ?? data.cases[0];
  const fmt = (v: number | null) => formatNumber(v, lang, { digits: 3 });
  const rows = [...data.summary].sort((a, b) => a.mean_mase - b.mean_mase);
  return <div className="cs-main">
    <p>{es
      ? 'Cada método se puntúa sobre el mismo bloque final de cada caso. Los pronósticos pesados provienen de la versión archivada; los métodos ligeros y las combinaciones se recalcularon con la historia comprometida.'
      : 'Every method is scored on the same final block of each case. Heavy forecasts come from the archived release; light methods and combinations were recomputed on the committed history.'}</p>
    <Callout variant="honest" title={es ? 'Resultado de la propuesta' : 'Proposal result'}>
      {es
        ? 'ContextMemory no mejoró el MASE medio de la combinación que usa solo recencia. Se conservan la propuesta, ambas ablaciones y todos los casos; los parámetros no se ajustaron usando el bloque final.'
        : 'ContextMemory did not improve mean MASE over the recency-only combination. The proposal, both ablations and every case are retained; parameters were not tuned on the final block.'}
    </Callout>
    <div className="cs-chart"><table className="cs-table">
      <caption>{es ? 'Promedio no ponderado entre los 15 casos seleccionados; un origen por caso.' : 'Unweighted average across 15 selected cases; one origin per case.'}</caption>
      <thead><tr><th>{es ? 'Método' : 'Method'}</th><th>MASE</th><th>{es ? 'Cobertura' : 'Coverage'}</th><th>{es ? 'Casos' : 'Cases'}</th></tr></thead>
      <tbody>{rows.map(r => <tr key={r.name}><td>{r.name}</td><td>{fmt(r.mean_mase)}</td><td>{fmt(r.mean_coverage)}</td><td>{r.cases}</td></tr>)}</tbody>
    </table></div>
    <label className="cs-ctl">{es ? 'Examinar un caso' : 'Inspect a case'}
      <select className="cs-sel" value={caseId} onChange={e => setCaseId(e.target.value)}>
        {data.cases.map(c => <option key={c.case_id} value={c.case_id}>{c.case_id}</option>)}
      </select>
    </label>
    {selected && <div className="cs-chart"><table className="cs-table">
      <caption>{selected.case_id}: {selected.horizon} {es ? 'observaciones reservadas' : 'held-out observations'}</caption>
      <thead><tr><th>{es ? 'Método' : 'Method'}</th><th>MASE</th><th>{es ? 'Cobertura' : 'Coverage'}</th><th>{es ? 'Amplitud' : 'Width'}</th><th>{es ? 'Procedencia' : 'Provenance'}</th></tr></thead>
      <tbody>{[...selected.methods].sort((a, b) => (a.metrics.mase ?? Infinity) - (b.metrics.mase ?? Infinity)).map(r => <tr key={r.name}>
        <td>{r.name}</td><td>{fmt(r.metrics.mase)}</td><td>{fmt(r.metrics.coverage)}</td><td>{fmt(r.metrics.mean_width)}</td>
        <td>{es ? (r.source.startsWith('frozen') ? 'Pronóstico archivado' : 'Recalculado') : r.source}</td>
      </tr>)}</tbody>
    </table></div>}
    <p>{es
      ? 'Una comparación finita no establece superioridad general ni significancia estadística. MASE divide el error absoluto por la diferencia estacional media de la historia; un valor inferior a uno no compara directamente dos pronósticos del bloque final.'
      : 'A finite comparison does not establish general superiority or statistical significance. MASE scales absolute error by the mean historical seasonal difference; a value below one does not directly compare two final-block forecasts.'}</p>
  </div>;
}
