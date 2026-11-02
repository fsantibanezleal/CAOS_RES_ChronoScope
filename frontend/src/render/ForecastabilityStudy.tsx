import { useEffect, useMemo, useState } from 'react';
import { formatNumber, useShellLang } from '@fasl-work/caos-app-shell';
import { admitForecastability, type ForecastabilityStudy as Study } from '../lib/forecastability';
import { UPlotChart } from './UPlotChart';

export function ForecastabilityStudy() {
  const lang = useShellLang(); const es = lang === 'es'; const t = (en: string, translated: string) => es ? translated : en;
  const [data, setData] = useState<Study | null>(null); const [error, setError] = useState('');
  const [feature, setFeature] = useState('linear_trend_r'); const [method, setMethod] = useState('AutoTheta');
  const [partition, setPartition] = useState('confirmation'); const [query, setQuery] = useState('');
  const [page, setPage] = useState(0); const [picked, setPicked] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch(`${import.meta.env.BASE_URL}data/forecastability.json`).then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json();
    }).then(admitForecastability).then(d => { if (!cancelled) setData(d); }).catch(e => { if (!cancelled) setError(String(e)); });
    return () => { cancelled = true; };
  }, []);
  const rows = useMemo(() => data?.series.filter(r => (partition === 'all' || r.partition === partition) &&
    (!query || r.id.toLowerCase().includes(query.toLowerCase()))) ?? [], [data, partition, query]);
  const points = useMemo(() => rows.filter(r => r.features[feature] != null).sort((a,b) => a.features[feature]!-b.features[feature]!), [rows, feature]);
  const fmt = (v: number | null) => formatNumber(v, lang, { digits: 4 });
  const probability = (v: number) => v === 0 ? '<1e-308' : new Intl.NumberFormat(lang, { notation: 'scientific', maximumSignificantDigits: 3 }).format(v);
  const selected = data?.series.find(r => r.id === picked);
  if (error) return <p role="alert">{t('Corpus study unavailable', 'Estudio de corpus no disponible')}: {error}</p>;
  if (!data) return <p data-state="loading">{t('Loading the complete corpus study', 'Cargando el estudio completo del corpus')}</p>;
  const summary = data.summary;
  return <div className="cs-main" data-forecastability-study="ready">
    <p>{t('All 4,227 M4 Daily source series were processed. Exact duplicates, nonfinite histories and unavailable error scales are listed as exclusions. Each admitted series contributes three non-overlapping 14-step origins; features use only the earliest fitting prefix, with at most 1,024 contiguous observations. Forecast seasonality is one; weekly phase strength is a separate diagnostic.', 'Se procesaron las 4.227 series originales M4 Daily. Los duplicados exactos, historias no finitas y escalas no disponibles se registran como exclusiones. Cada serie admitida aporta tres orÃ­genes de 14 pasos sin superposiciÃ³n; las caracterÃ­sticas usan solo el prefijo del primer ajuste, con un mÃ¡ximo de 1.024 observaciones contiguas. La estacionalidad del pronÃ³stico es uno; la fuerza semanal es otro diagnÃ³stico.')}</p>
    <p>{t('Admitted', 'Admitidas')}: {data.included_n}; {t('excluded', 'excluidas')}: {data.excluded.length}; {t('discovery', 'descubrimiento')}: {summary.discovery_n}; {t('confirmation', 'confirmaciÃ³n')}: {summary.confirmation_n}.</p>
    <div className="cs-table-scroll"><table className="cs-table"><caption>{t('Mean MASE on confirmation series only', 'MASE medio solo en series de confirmaciÃ³n')}</caption><thead><tr><th>{t('Selection rule', 'Regla de selecciÃ³n')}</th><th>MASE</th></tr></thead><tbody>
      <tr><td>{t('Discovery-trained feature selector', 'Selector por caracterÃ­sticas entrenado en descubrimiento')}</td><td>{fmt(summary.selection_mean_mase.selected)}</td></tr>
      <tr><td>{t('Discovery-selected constant', 'MÃ©todo constante elegido en descubrimiento')}: {summary.constant_method}</td><td>{fmt(summary.selection_mean_mase.discovery_constant)}</td></tr>
      <tr><td>{t('Per-series oracle within this roster', 'OrÃ¡culo por serie dentro de este conjunto')}</td><td>{fmt(summary.selection_mean_mase.oracle)}</td></tr>
    </tbody></table></div>
    <p>{t('The oracle uses future outcomes to identify the best method and is not an executable selection rule. The selector and imputation were fitted on discovery series only. These are descriptive held-out results; a worse selector result is retained.', 'El orÃ¡culo usa resultados futuros para identificar el mejor mÃ©todo y no es una regla de selecciÃ³n ejecutable. El selector y la imputaciÃ³n se ajustaron solo con series de descubrimiento. Son resultados descriptivos reservados; se conserva un resultado peor del selector.')}</p>
    <div className="cs-bar">
      <label className="cs-ctl">{t('Corpus partition', 'ParticiÃ³n del corpus')}<select className="cs-sel" value={partition} onChange={e => { setPartition(e.target.value); setPage(0); }}>
        <option value="confirmation">{t('Confirmation', 'ConfirmaciÃ³n')}</option><option value="discovery">{t('Discovery', 'Descubrimiento')}</option><option value="all">{t('Both partitions', 'Ambas particiones')}</option>
      </select></label>
      <label className="cs-ctl">{t('Prefix feature', 'CaracterÃ­stica del prefijo')}<select className="cs-sel" value={feature} onChange={e => setFeature(e.target.value)}>
        {summary.selector_features.map(f => <option key={f} value={f}>{f}</option>)}
      </select></label>
      <label className="cs-ctl">{t('Corpus method', 'MÃ©todo del corpus')}<select className="cs-sel" value={method} onChange={e => setMethod(e.target.value)}>
        {data.model_names.map(n => <option key={n}>{n}</option>)}
      </select></label>
      <label className="cs-ctl">{t('Find series', 'Buscar serie')}<input value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} /></label>
    </div>
    <p>{rows.length} {t('series in the current view; plot excludes unavailable feature values.', 'series en la vista actual; el grÃ¡fico omite valores de caracterÃ­sticas no disponibles.')}</p>
    {points.length > 0 ? <UPlotChart xs={points.map(r => r.features[feature]!)} series={[{ label: method, values: points.map(r => r.mase[method]), color: 'var(--color-accent)', scatter: true }]}
      xLabel={feature} yLabel="MASE" ariaSummary={t('Corpus feature and future error', 'CaracterÃ­stica del corpus y error futuro')}
      onPick={i => setPicked(points[i].id)} readout={i => `${points[i].id}: ${fmt(points[i].mase[method])} MASE`} /> : <p>{t('No matching feature values', 'No hay valores coincidentes')}</p>}
    {selected && <p aria-live="polite">{selected.id}: {selected.partition}; {feature}={fmt(selected.features[feature])}; {method} MASE={fmt(selected.mase[method])}.</p>}
    <div className="cs-table-scroll"><table className="cs-table"><caption>{t('Series-level audit, 25 rows per page', 'AuditorÃ­a por serie, 25 filas por pÃ¡gina')}</caption><thead><tr><th>ID</th><th>{t('Partition', 'ParticiÃ³n')}</th><th>{feature}</th><th>{method} MASE</th></tr></thead><tbody>
      {rows.slice(page*25,(page+1)*25).map(r => <tr key={r.id}><td><button onClick={() => setPicked(r.id)}>{r.id}</button></td><td>{r.partition === 'discovery' ? t('Discovery','Descubrimiento') : t('Confirmation','ConfirmaciÃ³n')}</td><td>{fmt(r.features[feature])}</td><td>{fmt(r.mase[method])}</td></tr>)}
    </tbody></table></div>
    <div className="cs-bar"><button disabled={page === 0} onClick={() => setPage(page-1)}>{t('Previous page','PÃ¡gina anterior')}</button><span>{page+1}/{Math.max(1,Math.ceil(rows.length/25))}</span><button disabled={(page+1)*25 >= rows.length} onClick={() => setPage(page+1)}>{t('Next page','PÃ¡gina siguiente')}</button></div>
    <p>{t('Kendall associations target log(1 + best mean MASE) within this fixed eight-method roster. BY q=0.05 corrects all feature tests separately in each partition. Confirmation requires rejection in both partitions and the same effect direction. An association is not a causal explanation or a guarantee of future skill.', 'Las asociaciones Kendall usan log(1 + mejor MASE medio) dentro de este conjunto fijo de ocho mÃ©todos. BY q=0,05 corrige todas las pruebas por separado en cada particiÃ³n. La confirmaciÃ³n exige rechazo en ambas y la misma direcciÃ³n. Una asociaciÃ³n no explica causalidad ni garantiza habilidad futura.')}</p>
    <div className="cs-table-scroll"><table className="cs-table"><caption>{t('Dependent-test correction and disjoint-series confirmation', 'CorrecciÃ³n de pruebas dependientes y confirmaciÃ³n en series separadas')}</caption><thead><tr><th>{t('Feature','CaracterÃ­stica')}</th><th>Ï„ D</th><th>q D</th><th>Ï„ C</th><th>q C</th><th>{t('Confirmed','Confirmada')}</th></tr></thead><tbody>
      {summary.associations.map(a => <tr key={a.feature}><td>{a.feature}</td><td>{fmt(a.discovery.tau)}</td><td>{probability(a.discovery.q)}</td><td>{fmt(a.confirmation.tau)}</td><td>{probability(a.confirmation.q)}</td><td>{a.confirmed ? t('Yes','SÃ­') : t('No','No')}</td></tr>)}
    </tbody></table></div>
    <p>{t('Related industries or latent source groups may remain dependent even after exact deduplication. This study includes neither deep nor pretrained models, and its diagnostic associations do not replace the separately executed 22-variant case experiment.', 'Sectores relacionados o grupos de origen latentes pueden seguir siendo dependientes despuÃ©s de deduplicar. Este estudio no incluye modelos profundos ni preentrenados; sus asociaciones no sustituyen el experimento separado de 22 variantes.')}</p>
    <details><summary>{t('Exclusions and source identity','Exclusiones e identidad de la fuente')}</summary><p><a href="https://zenodo.org/records/4656548">Monash M4 Daily, CC BY 4.0</a>; SHA-256 {data.source_sha256}</p><ul>{data.excluded.map(r => <li key={r.id}>{r.id}: {r.excluded}</li>)}</ul></details>
  </div>;
}
