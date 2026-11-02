import { useState } from 'react';
import { Callout, formatNumber, useShellLang } from '@fasl-work/caos-app-shell';
import type { Reevaluation } from '../lib/reevaluation.types';

export function CommonHoldout({ data }: { data: Reevaluation }) {
  const lang = useShellLang();
  const es = lang === 'es';
  const fresh = data.protocol.name === 'fresh common final holdout';
  const [caseId, setCaseId] = useState(data.cases[0]?.case_id ?? '');
  const selected = data.cases.find(c => c.case_id === caseId) ?? data.cases[0];
  const fmt = (v: number | null) => formatNumber(v, lang, { digits: 3 });
  const rows = [...data.summary].sort((a, b) => a.mean_mase - b.mean_mase);
  return <div className="cs-main">
    <p>{fresh ? (es
      ? 'Las veintidós variantes se ejecutaron de nuevo sobre historias originales contiguas y los mismos objetivos reservados. Las versiones de paquetes y revisiones de los cuatro modelos preentrenados quedan registradas. Los tiempos incluyen ajuste, inferencia y carga inicial; no miden latencia en caliente.'
      : 'All twenty-two variants were freshly executed on contiguous original histories and identical held-out targets. Package versions and revisions of all four pretrained models are recorded. Timings include fitting, inference and first-use loading; they do not measure warm inference latency.') : es
      ? 'Cada método se puntúa sobre el mismo bloque final de cada caso. Los pronósticos pesados provienen de la versión archivada; los métodos ligeros y las combinaciones se recalcularon con la historia comprometida.'
      : 'Every method is scored on the same final block of each case. Heavy forecasts come from the archived release; light methods and combinations were recomputed on the committed history.'}</p>
    {fresh && data.runtime && <p>{es ? 'Ejecución registrada' : 'Recorded execution'}: Python <code>{data.runtime.python}</code>, PyTorch <code>{data.runtime.packages.torch}</code>, <code>{data.runtime.gpu ?? 'CPU'}</code>. {es ? 'El solapamiento con datos de preentrenamiento sigue sin verificar.' : 'Pretraining-data overlap remains unverified.'}</p>}
    <Callout variant="honest" title={es ? 'Resultado de la propuesta' : 'Proposal result'}>
      {es
        ? 'ContextMemory no mejoró el MASE medio de la combinación que usa solo recencia. Se conservan la propuesta, ambas ablaciones y todos los casos; los parámetros no se ajustaron usando el bloque final.'
        : 'ContextMemory did not improve mean MASE over the recency-only combination. The proposal, both ablations and every case are retained; parameters were not tuned on the final block.'}
    </Callout>
    <div className="cs-chart"><div className="cs-table-scroll"><table className="cs-table">
      <caption>{es ? 'Promedio no ponderado entre los 15 casos seleccionados; un origen por caso.' : 'Unweighted average across 15 selected cases; one origin per case.'}</caption>
      <thead><tr><th>{es ? 'Método' : 'Method'}</th><th>MASE</th><th>{es ? 'Cobertura' : 'Coverage'}</th><th>{es ? 'Casos' : 'Cases'}</th></tr></thead>
      <tbody>{rows.map(r => <tr key={r.name}><td><code>{r.name}</code></td><td>{fmt(r.mean_mase)}</td><td>{fmt(r.mean_coverage)}</td><td>{r.cases}</td></tr>)}</tbody>
    </table></div></div>
    <label className="cs-ctl">{es ? 'Examinar un caso' : 'Inspect a case'}
      <select className="cs-sel" value={caseId} onChange={e => setCaseId(e.target.value)}>
        {data.cases.map(c => <option key={c.case_id} value={c.case_id}>{c.case_id}</option>)}
      </select>
    </label>
    {selected && <div className="cs-chart"><div className="cs-table-scroll"><table className="cs-table">
      <caption>{selected.case_id}: {selected.horizon} {es ? 'observaciones reservadas' : 'held-out observations'}</caption>
      <thead><tr><th>{es ? 'Método' : 'Method'}</th><th>MASE</th><th>{es ? 'Cobertura' : 'Coverage'}</th><th>{es ? 'Amplitud' : 'Width'}</th><th>{es ? 'Procedencia' : 'Provenance'}</th></tr></thead>
      <tbody>{[...selected.methods].sort((a, b) => (a.metrics.mase ?? Infinity) - (b.metrics.mase ?? Infinity)).map(r => <tr key={r.name}>
        <td><code>{r.name}</code></td><td>{fmt(r.metrics.mase)}</td><td>{fmt(r.metrics.coverage)}</td><td>{fmt(r.metrics.mean_width)}</td>
        <td>{es ? (r.source.startsWith('frozen') ? 'Pronóstico archivado' : 'Recalculado') : r.source}</td>
      </tr>)}</tbody>
    </table></div></div>}
    <p>{es
      ? 'Una comparación finita no establece superioridad general ni significancia estadística. MASE divide el error absoluto por la diferencia estacional media de la historia; un valor inferior a uno no compara directamente dos pronósticos del bloque final.'
      : 'A finite comparison does not establish general superiority or statistical significance. MASE scales absolute error by the mean historical seasonal difference; a value below one does not directly compare two final-block forecasts.'}</p>
  </div>;
}
