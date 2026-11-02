import { useEffect, useRef, useState } from 'react';
import { Callout, DocPage, DocSection, Figure, SubTabs, formatNumber, useShellLang } from '@fasl-work/caos-app-shell';
import { loadManifest, loadReevaluation, loadTrace } from '../api/artifacts';
import type { CaseManifest, Trace } from '../lib/contract.types';
import type { Reevaluation, ReevaluatedCase } from '../lib/reevaluation.types';
import { loadNLinearMeta, runNLinear } from '../lib/onnxRunner';
import { CommonHoldout } from '../render/CommonHoldout';
import { UPlotChart } from '../render/UPlotChart';
import { methodColor } from '../lib/methodColors';
import { ForecastabilityStudy } from '../render/ForecastabilityStudy';

function CaseSelect({ cases, value, onChange }: { cases: ReevaluatedCase[]; value: string; onChange: (value: string) => void }) {
  const es = useShellLang() === 'es';
  return <label className="cs-ctl">{es ? 'Caso' : 'Case'}<select className="cs-sel" value={value} onChange={e => onChange(e.target.value)}>
    {cases.map(c => <option key={c.case_id} value={c.case_id}>{c.case_id}</option>)}
  </select></label>;
}

function LiveRealInference({ cases }: { cases: ReevaluatedCase[] }) {
  const lang = useShellLang(); const es = lang === 'es';
  const real = cases.filter(c => c.case_id.startsWith('REAL_'));
  const [caseId, setCaseId] = useState(real[0].case_id);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [point, setPoint] = useState<number[] | null>(null);
  const [busy, setBusy] = useState(false); const [err, setErr] = useState('');
  const runId = useRef(0);
  useEffect(() => {
    let cancelled = false; runId.current += 1; setTrace(null); setPoint(null); setErr(''); setBusy(false);
    loadTrace(`${caseId}/trace.json`).then(v => { if (!cancelled) setTrace(v); }).catch(e => { if (!cancelled) setErr(String(e)); });
    return () => { cancelled = true; runId.current += 1; };
  }, [caseId]);
  const execute = async () => {
    if (!trace) return;
    const generation = ++runId.current;
    setBusy(true); setErr('');
    try {
      const meta = await loadNLinearMeta();
      if (trace.actual.length < meta.horizon) throw new Error('The reserved block is shorter than the model horizon');
      const result = await runNLinear(real.find(c => c.case_id === caseId)!.history);
      if (generation === runId.current) setPoint(result.point);
    } catch (e) { if (generation === runId.current) setErr(String(e)); }
    finally { if (generation === runId.current) setBusy(false); }
  };
  return <div className="cs-main" data-state={busy || (!trace && !err) ? 'loading' : 'ready'}>
    <CaseSelect cases={real} value={caseId} onChange={setCaseId} />
    <p>{es ? 'Este panel ejecuta el pequeÃ±o modelo NLinear en el navegador sobre una historia real reservada. El modelo fue entrenado con ventanas sintÃ©ticas; aquÃ­ se comparan doce predicciones nuevas con las primeras doce observaciones del bloque final, sin actualizar el ajuste con ellas.' : 'This panel executes the small NLinear model in the browser on a real held-out history. The model was trained on synthetic windows; twelve new predictions are compared with the first twelve observations of the final block, without updating the fit from those outcomes.'}</p>
    <button type="button" data-control="run-real-nlinear" className="cs-mini" disabled={!trace || busy} onClick={execute}>{es ? 'Ejecutar NLinear en este caso real' : 'Run NLinear on this real case'}</button>
    {err && <p role="alert">{err}</p>}
    {point && trace && <>
      <UPlotChart xs={point.map((_, i) => i + 1)} series={[
        { label: es ? 'Observado' : 'Observed', values: trace.actual.slice(0, point.length), color: 'var(--color-good)' },
        { label: 'NLinear (ONNX)', values: point, color: 'var(--color-accent)' },
      ]} height={320} xLabel={es ? 'Paso reservado' : 'Held-out lead'} yLabel={es ? 'Unidades del caso' : 'Case value units'} ariaSummary={es ? 'Inferencia real en el navegador' : 'Live browser inference on real data'} />
      <p>{es ? 'Error absoluto medio' : 'Mean absolute error'}: {formatNumber(point.reduce((s, p, i) => s + Math.abs(p - trace.actual[i]), 0) / point.length, lang, { digits: 4 })}</p>
    </>}
  </div>;
}

export default function BenchmarkCurrent() {
  const lang = useShellLang(); const es = lang === 'es';
  const t = (en: string, translated: string) => es ? translated : en;
  const [data, setData] = useState<Reevaluation | null>(null);
  const [manifests, setManifests] = useState<CaseManifest[]>([]);
  const [err, setErr] = useState('');
  const [caseId, setCaseId] = useState('REAL_electricity');
  const [method, setMethod] = useState('ContextMemory');
  const [feature, setFeature] = useState<'seasonal_strength' | 'acf1' | 'pct_zeros'>('seasonal_strength');
  const [study, setStudy] = useState<'fresh' | 'archived'>('fresh');
  useEffect(() => {
    let cancelled = false;
    setData(null); setErr('');
    (async () => {
      try {
        const comparison = await loadReevaluation(study);
        const sources = await Promise.all(comparison.cases.map(c => loadManifest(c.case_id)));
        if (!cancelled) { setData(comparison); setManifests(sources); }
      } catch (e) { if (!cancelled) setErr(String(e)); }
    })();
    return () => { cancelled = true; };
  }, [study]);
  const own = { en: 'Reports computations and provenance from the committed case artifacts.', es: 'Informa cÃ³mputos y procedencia de los artefactos comprometidos.' };
  const c = data?.cases.find(v => v.case_id === caseId) ?? data?.cases[0];
  const fmt = (v: number | null) => formatNumber(v, lang, { digits: 3 });
  const selected = c?.methods.find(v => v.name === method);
  const naive = c?.methods.find(v => v.name === 'SeasonalNaive');
  const real = data?.cases.filter(v => v.case_id.startsWith('REAL_')) ?? [];
  const realCase = real.find(v => v.case_id === caseId) ?? real[0];
  const points = manifests.flatMap(m => {
    const result = data?.cases.find(v => v.case_id === m.case_id)?.methods.find(v => v.name === method);
    const x = m.series[feature];
    return result?.metrics.mase != null && Number.isFinite(x) ? [{ id: m.case_id, x, y: result.metrics.mase }] : [];
  });
  return <DocPage title={{ en: 'Benchmark', es: 'ComparaciÃ³n' }} lede={t('The common comparison scores twenty-two forecasting variants on identical final blocks from fifteen selected cases. Inspect fresh executions, archived comparisons, real-series forecasts, lead-time errors, executable browser inference and source provenance. Exact packages and checkpoint revisions identify the new numerical experiment.', 'La comparaciÃ³n comÃºn puntÃºa veintidÃ³s variantes sobre bloques finales idÃ©nticos de quince casos. Examine ejecuciones nuevas, comparaciones archivadas, pronÃ³sticos reales, errores por horizonte, inferencia ejecutable y procedencia. Las versiones de paquetes y revisiones de modelos identifican el nuevo experimento numÃ©rico.')}>
    <label className="cs-ctl">{t('Experiment', 'Experimento')}<select className="cs-sel" value={study} onChange={e => setStudy(e.target.value as typeof study)}>
      <option value="fresh">{t('Fresh executions', 'Ejecuciones nuevas')}</option>
      <option value="archived">{t('Archived predictions rescored', 'PronÃ³sticos archivados repuntuados')}</option>
    </select></label>
    {err ? <p role="alert">{err}</p> : !data ? <p data-state="loading">{t('Loading admitted results', 'Cargando resultados admitidos')}</p> : <SubTabs ariaLabel={t('Benchmark topics', 'Temas de comparaciÃ³n')} tabs={[
      { id:'results',label:t('Common results','Resultados comunes'),content:<DocSection title={{en:'Common final holdout',es:'Bloque final comÃºn'}} area="results" refs={['chronoscope-report','mase','msis']}><CommonHoldout data={data} /></DocSection> },
      { id:'real',label:t('Real series','Series reales'),content:<DocSection title={{en:'Models on the same real outcomes',es:'Modelos sobre los mismos resultados reales'}} area="comparison" refs={['uci-electricity','mase']}>
        <CaseSelect cases={real} value={realCase?.case_id ?? ''} onChange={setCaseId} />
        {realCase && <Figure caption={t('These model paths share one real historical cutoff and the same final observations.', 'Estas trayectorias comparten un corte histÃ³rico real y las mismas observaciones finales.')}><UPlotChart xs={realCase.actual.map((_,i)=>i+1)} series={[
          {label:t('Observed','Observado'),values:realCase.actual,color:'var(--color-fg)'},
          ...realCase.methods.filter(m=>['SeasonalNaive','Chronos-Bolt','ContextMemory'].includes(m.name)).map(m=>({label:m.name,values:m.point,color:methodColor(m.name)})),
        ]} ariaSummary={t('Forecasts on a real held-out block','PronÃ³sticos sobre un bloque real reservado')} xLabel={t('Lead','Paso')} yLabel={t('Case value units','Unidades del caso')} /></Figure>}
        <p>{study === 'fresh' ? t('Every displayed method was executed again on the original contiguous history. The pretrained checkpoint is identified by its revision; independence from its pretraining corpus remains unverified.', 'Cada mÃ©todo mostrado se ejecutÃ³ de nuevo sobre la historia original contigua. La revisiÃ³n identifica el modelo preentrenado; la independencia de su corpus sigue sin verificar.') : t('The pretrained path is frozen evidence; the smoothing reference and combination were recomputed. The comparison concerns these outcomes and does not establish independence from a pretraining corpus.', 'La trayectoria preentrenada es evidencia congelada; la referencia y combinaciÃ³n fueron recalculadas. La comparaciÃ³n corresponde a estos resultados y no establece independencia del corpus de preentrenamiento.')}</p>
      </DocSection> },
      { id:'lead',label:t('Lead-time errors','Errores por paso'),content:<DocSection title={{en:'Observed error by forecast lead',es:'Error observado por paso'}} area="robustness" noRefsReason={own}>
        <CaseSelect cases={data.cases} value={c?.case_id ?? ''} onChange={setCaseId} />
        <label className="cs-ctl" data-control>{t('Method','MÃ©todo')}<select className="cs-sel" value={method} onChange={e=>setMethod(e.target.value)}>{data.summary.map(m=><option key={m.name}>{m.name}</option>)}</select></label>
        {c && selected && naive && <UPlotChart xs={c.actual.map((_,i)=>i+1)} series={[
          {label:method,values:c.actual.map((a,i)=>Math.abs(a-selected.point[i])),color:methodColor(method)},
          ...(method==='SeasonalNaive'?[]:[{label:'SeasonalNaive',values:c.actual.map((a,i)=>Math.abs(a-naive.point[i])),color:methodColor('SeasonalNaive')}]),
        ]} ariaSummary={t('Absolute error by lead on one reserved block','Error absoluto por paso en un bloque reservado')} xLabel={t('Forecast lead','Paso de pronÃ³stico')} yLabel={t('Absolute error in case units','Error absoluto en unidades del caso')} />}
        <p>{t('This is an observed degradation diagnostic from one final block, not a confidence band or a repeated-noise robustness experiment. Compare local spikes with the aggregate score before drawing a conclusion.', 'Este es un diagnÃ³stico observado de un bloque final, no una banda de confianza ni un experimento repetido con perturbaciones. Compare los errores locales con la medida agregada antes de concluir.')}</p>
      </DocSection> },
      { id:'live',label:t('Live real inference','Inferencia real viva'),content:<DocSection title={{en:'NLinear in the browser',es:'NLinear en el navegador'}} area="live" refs={['dlinear']}><LiveRealInference cases={data.cases} /></DocSection> },
      { id:'sources',label:t('Cases and sources','Casos y fuentes'),content:<DocSection title={{en:'Case provenance and diagnostic context',es:'Procedencia y contexto diagnÃ³stico'}} area="provenance" noRefsReason={own}>
        <div className="cs-table-scroll"><table className="cs-table"><thead><tr><th>{t('Case','Caso')}</th><th>{t('Difficulty','Dificultad')}</th><th>{t('Source','Fuente')}</th><th>{t('Redistribution','RedistribuciÃ³n')}</th></tr></thead><tbody>{manifests.map(m=><tr key={m.case_id}><td>{m.case_id}</td><td>{es ? m.category.replace(/(\d)\.(\d)/g, '$1,$2') : m.category}</td><td>{m.provenance.source}</td><td><code>{m.provenance.license}</code>: {m.provenance.public_artifact_ok?t('admitted','admitida'):t('restricted','restringida')}</td></tr>)}</tbody></table></div>
        <label className="cs-ctl" data-control>{t('Diagnostic coordinate','Coordenada diagnÃ³stica')}<select className="cs-sel" value={feature} onChange={e=>setFeature(e.target.value as typeof feature)}><option value="seasonal_strength">{t('Seasonal strength','Fuerza estacional')}</option><option value="acf1">{t('Lag-one correlation','CorrelaciÃ³n de rezago uno')}</option><option value="pct_zeros">{t('Zero observations','Observaciones nulas')}</option></select></label>
        <UPlotChart xs={points.map(p=>p.x)} series={[{label:method,values:points.map(p=>p.y),color:'var(--color-accent)',scatter:true}]} xLabel={feature} yLabel="MASE" ariaSummary={t('Diagnostic coordinate and held-out error','Coordenada diagnÃ³stica y error reservado')} readout={i=>`${points[i].id}: ${fmt(points[i].y)} MASE`} onPick={i=>setCaseId(points[i].id)} />
        <p>{t('The diagnostic coordinate describes the case; its association with error does not establish a causal explanation. Select a point to carry that case into the other comparison views.', 'La coordenada describe el caso; su relaciÃ³n con el error no establece una explicaciÃ³n causal. Seleccione un punto para llevar el caso a las otras vistas comparativas.')}</p>
      </DocSection> },
      { id:'corpus',label:t('Corpus study','Estudio de corpus'),content:<DocSection title={{en:'Forecastability over the M4 Daily corpus',es:'Pronosticabilidad en el corpus M4 Daily'}} area="robustness" refs={['chronoscope-report','mase']}><ForecastabilityStudy /></DocSection> },
      { id:'limits',label:t('Limits','LÃ­mites'),content:<DocSection title={{en:'What the experiment establishes',es:'QuÃ© establece el experimento'}} area="caveat" noRefsReason={own}>
        <Callout variant="honest" title={t('Finite evidence','Evidencia finita')}>{t('One origin per selected case does not establish population superiority or significance. The fresh experiment executes all methods; the archived experiment rescores older heavy-model paths. Pretraining overlap remains unverified. ContextMemory failed its mean comparison against its recency-only ablation; the negative result and all cases are retained.', 'Un origen por caso no establece superioridad poblacional ni significancia. El experimento nuevo ejecuta todos los mÃ©todos; el archivado repuntÃºa trayectorias pesadas anteriores. El solapamiento de preentrenamiento sigue sin verificar. ContextMemory no mejorÃ³ su ablaciÃ³n de recencia; se conservan el resultado negativo y todos los casos.')}</Callout>
        <p>{t('Historical rolling results used different origin schedules and remain in the source artifacts. The common comparison uses the same final targets and explicitly distinguishes forecast provenance. MASE below one compares error to an in-history scale, not directly to a separately scored naive path.', 'Los resultados mÃ³viles histÃ³ricos usaron otros calendarios y permanecen en los artefactos de origen. La comparaciÃ³n comÃºn utiliza los mismos objetivos finales y distingue procedencia. MASE inferior a uno compara el error con una escala histÃ³rica y no directamente con otra trayectoria naive puntuada.')}</p>
      </DocSection> },
    ]} />}
  </DocPage>;
}
