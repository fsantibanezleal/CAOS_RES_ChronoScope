import { useEffect, useMemo, useState } from 'react';
import { formatNumber, useShellLang } from '@fasl-work/caos-app-shell';
import { loadCombinationCase, loadCombinationIndex } from '../api/artifacts';
import type { CombinationCase, CombinationIndex } from '../lib/contract.types';
import { UPlotChart } from './UPlotChart';

export function CombinationStudy() {
  const lang = useShellLang(); const es = lang === 'es';
  const t = (en: string, translated: string) => es ? translated : en;
  const fmt = (v: number | null | undefined) => formatNumber(v, lang, { digits: 4 });
  const [index, setIndex] = useState<CombinationIndex | null>(null);
  const [dataset, setDataset] = useState('m4_weekly');
  const [caseId, setCaseId] = useState('');
  const [originIndex, setOriginIndex] = useState(0);
  const [method, setMethod] = useState('ValidationMix');
  const [detail, setDetail] = useState<CombinationCase | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { let cancelled = false; loadCombinationIndex().then(x => { if (!cancelled) setIndex(x); }).catch(e => { if (!cancelled) setError(String(e)); }); return () => { cancelled = true; }; }, []);
  const entries = useMemo(() => index?.cases.filter(c => c.dataset === dataset && !c.excluded) ?? [], [index, dataset]);
  const entry = entries.find(c => c.id === caseId) ?? entries[0];
  useEffect(() => {
    if (!entry) return;
    let cancelled = false; setDetail(null); setError('');
    loadCombinationCase(entry.path).then(x => { if (!cancelled) setDetail(x); }).catch(e => { if (!cancelled) setError(String(e)); });
    return () => { cancelled = true; };
  }, [entry?.path]);
  const cohort = index?.cohorts.find(c => c.id === dataset);
  const activeDetail = detail?.dataset === dataset && detail.id === entry?.id ? detail : null;
  const origin = activeDetail?.origins[Math.min(originIndex, activeDetail.origins.length - 1)];
  const chosen = origin?.methods.find(m => m.name === method) ?? origin?.methods.find(m => m.name === 'ValidationMix');
  const recency = origin?.methods.find(m => m.name === 'RecencyMean');
  if (error) return <p role="alert">{t('The combination study could not be loaded.', 'No se pudo cargar el estudio de combinaciones.')} {error}</p>;
  if (!index || !cohort) return <p role="status">{t('Loading the measured combination study…', 'Cargando el estudio medido de combinaciones…')}</p>;
  const experts = ['SeasonalNaive', 'SES', 'Holt', 'HoltWinters', 'Theta'];
  return <div data-state={activeDetail ? 'ready' : 'loading'}>
    <p>{t('Temporal validation selects parameters using completed historical blocks. ValidationMix improves on RecencyMean in both external collections; AutoTheta remains better on M3 Monthly. The fifteen selected development cases are displayed separately.', 'La validación temporal selecciona parámetros con bloques históricos completos. ValidationMix mejora a RecencyMean en ambas colecciones externas; AutoTheta conserva menor error en M3 Monthly. Los quince casos de desarrollo se muestran separadamente.')}</p>
    <div className="cs-bar">
      <label className="cs-bar-group">{t('Collection', 'Colección')}
        <select className="cs-sel" aria-label={t('Combination collection', 'Colección de combinaciones')} value={dataset} onChange={e => { setDataset(e.target.value); setCaseId(''); setOriginIndex(0); }}>
          {index.cohorts.map(c => <option key={c.id} value={c.id}>{c.id === 'selected_cases' ? t('Selected development cases', 'Casos seleccionados de desarrollo') : c.name}</option>)}
        </select>
      </label>
      <label className="cs-bar-group">{t('Series', 'Serie')}
        <select className="cs-sel" aria-label={t('Combination series', 'Serie de combinaciones')} value={entry?.id ?? ''} onChange={e => { setCaseId(e.target.value); setOriginIndex(0); }}>
          {entries.map(c => <option key={c.id} value={c.id}>{c.id.replaceAll('_', ' ')}</option>)}
        </select>
      </label>
      {activeDetail && <label className="cs-bar-group">{t('Origin', 'Origen')}
        <select className="cs-sel" aria-label={t('Combination origin', 'Origen de combinaciones')} value={Math.min(originIndex, activeDetail.origins.length - 1)} onChange={e => setOriginIndex(Number(e.target.value))}>
          {activeDetail.origins.map((o, i) => <option key={o.origin} value={i}>{o.origin}</option>)}
        </select>
      </label>}
    </div>
    <p>{t('Source identities', 'Identidades de origen')}: {cohort.inventory}. {t('Admitted', 'Admitidas')}: {cohort.admitted}. {t('Excluded', 'Excluidas')}: {cohort.excluded}. {t('Scored origins', 'Orígenes evaluados')}: {cohort.origins}.</p>
    <p>{dataset === 'selected_cases'
      ? t('One original final block per development case. These outcomes are not fresh external confirmation.', 'Un bloque final original por caso de desarrollo. Estos resultados no constituyen una confirmación externa nueva.')
      : t('Up to three nonoverlapping target blocks per series; each fit uses at most 512 contiguous observations. Scores average origins within series, then weight series equally. M4 competition rankings use a different protocol and cannot be inferred from this table.', 'Hasta tres bloques objetivo sin solapamiento por serie; cada ajuste usa como máximo 512 observaciones contiguas. Se promedian orígenes por serie y luego series con igual peso. La competición M4 usa otro protocolo: esta tabla no establece posiciones en ella.')}</p>
    <div className="cs-table-scroll"><table className="cs-table">
      <caption>{t('Complete comparison on the same admitted series; select a method to inspect its paths.', 'Comparación completa sobre las mismas series admitidas; seleccione un método para inspeccionar sus trayectorias.')}</caption>
      <thead><tr><th>{t('Method', 'Método')}</th><th>{t('Mean MASE', 'MASE medio')}</th><th>{t('Mean MSIS', 'MSIS medio')}</th><th>{t('Coverage', 'Cobertura')}</th></tr></thead>
      <tbody>{[...cohort.summary].sort((a, b) => a.mase - b.mase).map(row => <tr key={row.name}>
        <td><button className={`cs-filter-chip${chosen?.name === row.name ? ' is-active' : ''}`} type="button" onClick={() => setMethod(row.name)} aria-pressed={chosen?.name === row.name}>{row.name}</button></td><td>{fmt(row.mase)}</td><td>{fmt(row.msis)}</td><td>{fmt(row.coverage)}</td>
      </tr>)}</tbody>
    </table></div>
    {origin && chosen && <>
      <UPlotChart xs={origin.actual.map((_, i) => origin.origin + i)} height={340}
        ariaSummary={t(`Held-out forecasts: ${chosen.name}, ${detail?.id}`, `Pronósticos reservados: ${chosen.name}, ${detail?.id}`)}
        series={[
          { label: t('Observed target', 'Objetivo observado'), values: origin.actual, color: 'var(--color-fg)' },
          { label: chosen.name, values: chosen.quantiles.map(q => q[1]), color: 'var(--color-accent)' },
          { label: `${chosen.name} 10%`, values: chosen.quantiles.map(q => q[0]), color: 'var(--color-accent-2)', dash: [4, 3] },
          { label: `${chosen.name} 90%`, values: chosen.quantiles.map(q => q[2]), color: 'var(--color-accent-2)', dash: [4, 3] },
          ...(recency && chosen.name !== 'RecencyMean' ? [{ label: 'RecencyMean', values: recency.quantiles.map(q => q[1]), color: 'var(--color-warn)' }] : []),
        ]} />
      <p>{chosen.name}: MASE {fmt(chosen.metrics.mase)}; MSIS {fmt(chosen.metrics.msis)}; {t('coverage', 'cobertura')} {fmt(chosen.metrics.coverage)}.</p>
      {chosen.weights && <div className="cs-table-scroll"><table className="cs-table"><caption>{t('Expert weights fitted before this target block', 'Pesos de expertos ajustados antes de este bloque objetivo')}</caption><thead><tr>{experts.map(e => <th key={e}>{e}</th>)}</tr></thead><tbody><tr>{chosen.weights.map((w, i) => <td key={experts[i]}>{fmt(w)}</td>)}</tr></tbody></table></div>}
      {chosen.selected && <p>{t('Selected rule', 'Regla seleccionada')}: {chosen.selected.map(value => typeof value === 'number' ? fmt(value) : value).join('; ')}. {t('Eligible historical validation blocks', 'Bloques históricos elegibles de validación')}: {chosen.validation_blocks ?? 0}.</p>}
    </>}
    <p>{t('The interval endpoints are weighted Gaussian approximations. Lower point error does not establish calibrated uncertainty; coverage and interval score must be checked separately. The original fixed ContextMemory negative result remains available.', 'Los extremos de los intervalos son aproximaciones gaussianas ponderadas. Un menor error puntual no establece incertidumbre calibrada; la cobertura y la puntuación de intervalos se revisan por separado. El resultado negativo original de ContextMemory sigue disponible.')}</p>
    {cohort.excluded > 0 && <details><summary>{t('Excluded source identities', 'Identidades de origen excluidas')}</summary><ul>{index.cases.filter(c => c.dataset === dataset && c.excluded).map(c => <li key={c.id}>{c.id}: {c.excluded === 'exact duplicate' ? t('exact duplicate', 'duplicado exacto') : t('insufficient history for the fixed seasonal/origin protocol', 'historia insuficiente para el protocolo estacional y de orígenes fijado')}</li>)}</ul></details>}
  </div>;
}
