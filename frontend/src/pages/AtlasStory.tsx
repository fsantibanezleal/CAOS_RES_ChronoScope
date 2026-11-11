import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router';
import { Scene3DFrame, SceneCallouts, Stage, StoryFrame, formatNumber, useLinkedCursor, useLinkedItem, useLinkedView, useShellLang, type SceneCalloutDef, type StoryStep } from '@fasl-work/caos-app-shell';
import { useAtlasSource } from '../state/AtlasSource';
import { completedMemory, delayCoordinates, EXPERTS, projectDelay, SHOWCASE_KINDS, type ShowcaseKind } from '../lib/showcase';
import { UPlotChart } from '../render/UPlotChart';
const bi = (en: string, es: string) => ({ en, es });
const methodLabel = (name: string) => name.replace('TimesFM-2.5', 'TimesFM v2.5');
function LinkedButton({ id, side, children }: { id: string; side: 'scene' | 'panel'; children: ReactNode }) {
  const linked = useLinkedItem(id, side), { scrub } = useLinkedCursor();
  return <button type="button" {...linked} onClick={() => { linked.onClick(); if (id.startsWith('observation:')) scrub(Number(id.split(':')[1])); }}>{children}</button>;
}
function Glyph({ id, children, label }: { id: string; children: ReactNode; label: string }) {
  const linked = useLinkedItem(id, 'scene'), { scrub } = useLinkedCursor();
  const activate = () => { linked.onClick(); if (id.startsWith('observation:')) scrub(Number(id.split(':')[1])); };
  return <g {...linked} onClick={activate} role="button" tabIndex={0} aria-label={label} onKeyDown={event => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activate(); }
  }}>{children}</g>;
}
/** Anchor annotations to the measured subject, including SVG and chart controls. */
function AnnotatedScene({ items, children, onBand }: { items: SceneCalloutDef[]; children: ReactNode; onBand: (band: number) => void }) {
  const [band, setBand] = useState(0);
  const host = useRef<HTMLDivElement>(null);
  const [anchors, setAnchors] = useState<Record<string, { x: number; y: number }>>({});
  const measure = useCallback(() => {
    const root = host.current; if (!root) return;
    const box = root.getBoundingClientRect(); if (!box.width || !box.height) return;
    const next: Record<string, { x: number; y: number }> = {};
    const normalized = (value: number) => Math.round(Math.max(0, Math.min(1, value)) * 1e6) / 1e6;
    for (const element of root.querySelectorAll('[data-subject]')) {
      const rect = element.getBoundingClientRect();
      const anchor = { x: normalized((rect.left + rect.width / 2 - box.left) / box.width), y: normalized((rect.top + rect.height / 2 - box.top) / box.height) };
      for (const id of element.getAttribute('data-subject')!.split(' ')) next[id] = anchor;
    }
    setAnchors(previous => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
  }, []);
  useLayoutEffect(measure);
  useLayoutEffect(() => {
    if (!host.current) return;
    const observer = new ResizeObserver(measure); observer.observe(host.current);
    return () => observer.disconnect();
  }, [measure]);
  return <div ref={host} className="cs-annotated-scene">
    <div className="cs-story-drawing" style={{ paddingTop: band }}>{children}</div>
    <SceneCallouts placement="header" items={items.map(item => ({ ...item, anchor: anchors[item.id] ?? item.anchor }))}
      onLayout={({ bandHeight }) => { setBand(bandHeight); onBand(bandHeight); }} />
  </div>;
}
function ResponsiveSvg({ label, children }: { label: string; children: ReactNode }) {
  return <Stage label={bi(label, label)}>{size => <svg viewBox="0 0 1000 650" className="cs-story-svg" role="img" aria-label={label} style={{ fontSize: Math.max(17, 12 / Math.min(size.width / 1000, size.height / 650)) }}>{children}</svg>}</Stage>;
}
function FlowScene() {
  const { activeData: data, allMethods } = useAtlasSource();
  const { cursor, markerProps } = useLinkedCursor();
  const es = useShellLang() === 'es';
  const boxes = [{ id: 'prefix', x: 65, value: data?.history.length ?? 0, label: es ? 'Historia observada' : 'Observed history' },
    { id: 'experts', x: 390, value: allMethods.length, label: es ? 'Pronósticos' : 'Forecasts' },
    { id: 'target', x: 715, value: data?.horizon ?? 0, label: es ? 'Objetivos reservados' : 'Reserved targets' }];
  return <div className="cs-story-flow" role="group" aria-label={es ? 'Orden causal de evaluación' : 'Causal evaluation order'}>
    {boxes.map(box => <div key={box.id} data-subject={box.id}><LinkedButton id={box.id} side="scene"><strong>{box.value}</strong><span>{box.label}</span>{box.id === 'prefix' && <output {...markerProps}>t={Math.max(0, Math.min((data?.history.length ?? 1) - 1, cursor ?? 0))} · {formatNumber(data?.history[Math.max(0, Math.min((data?.history.length ?? 1) - 1, cursor ?? 0))], es ? 'es' : 'en', { digits: 2 })}</output>}</LinkedButton></div>)}
  </div>;
}
function DelayScene({ onBand }: { onBand: (band: number) => void }) {
  const { activeData } = useAtlasSource();
  const es = useShellLang() === 'es';
  const [angle, setAngle] = useState(.65);
  const { cursor, markerProps } = useLinkedCursor();
  const points = useMemo(() => delayCoordinates(activeData?.history ?? []), [activeData?.history]);
  if (!activeData || !points.length) return <p>{es ? 'Faltan tres observaciones finitas.' : 'Three finite observations are required.'}</p>;
  const low = Math.min(...activeData.history), high = Math.max(...activeData.history), center = (low + high) / 2, span = high - low || 1;
  const project = (value: number[]) => projectDelay(value, center, span, angle);
  const coordinates = points.map(point => project(point.value));
  const currentIndex = Math.max(0, Math.min(activeData.history.length - 3, cursor ?? 0));
  const current = { index: currentIndex, value: activeData.history.slice(currentIndex, currentIndex + 3) };
  const anchor = project(current.value);
  const callouts: SceneCalloutDef[] = current.value.map((value, i) => ({ id: `coordinate-${i}`, eyebrow: bi(`y[${current.index + i}]`, `y[${current.index + i}]`), value: formatNumber(value, es ? 'es' : 'en', { digits: 2 }), unit: bi('source units', 'unidades de origen'), state: 'selected', anchor: { x: anchor[0] / 1000, y: anchor[1] / 650 }, source: bi(`Observed prefix; delay ${i}`, `Historia observada; retardo ${i}`) }));
  return <Scene3DFrame label={es ? 'Trayectoria en tres coordenadas retardadas' : 'Trajectory in three delayed coordinates'}
    controls={<label>{es ? 'Rotar vista' : 'Rotate view'} <input aria-label={es ? 'Ángulo de la vista' : 'View angle'} type="range" min="-3.14" max="3.14" step="0.02" value={angle} onChange={event => setAngle(Number(event.target.value))} /></label>}
    status={es ? 'Sólo historia observada. Una trayectoria no demuestra caos.' : 'Observed history only. A trajectory does not establish chaos.'}>
    <AnnotatedScene items={callouts} onBand={onBand}><ResponsiveSvg label={es ? 'Retardos de la historia observada' : 'Observed-prefix delay coordinates'}>
      <title>{es ? 'Cada punto es (y[t], y[t+1], y[t+2])' : 'Each point is (y[t], y[t+1], y[t+2])'}</title>
      {[0, 1, 2].map(axis => { const end = [center, center, center]; end[axis] = center + span * .57; const [x, y] = project(end); const start = project([center, center, center]);
        return <g key={axis}><line x1={start[0]} y1={start[1]} x2={x} y2={y} className="cs-flow-line" /><text x={x} y={y - 12}>{`y[t+${axis}]`}</text></g>; })}
      <polyline points={coordinates.map(v => v.join(',')).join(' ')} fill="none" stroke="var(--color-accent)" strokeWidth="2" opacity=".6" />
      {points.map((point, i) => <circle key={point.index} cx={coordinates[i][0]} cy={coordinates[i][1]} r="3" fill="var(--color-accent)" pointerEvents="none" aria-hidden="true" />)}
      <Glyph id={`observation:${current.index}`} label={`${es ? 'Observación' : 'Observation'} ${current.index}`}>
        <circle cx={anchor[0]} cy={anchor[1]} r="14" fill="transparent" />
        <circle cx={anchor[0]} cy={anchor[1]} r="7" />
      </Glyph>
      <circle data-subject="coordinate-0 coordinate-1 coordinate-2" {...markerProps} cx={anchor[0]} cy={anchor[1]} r="11" fill="none" stroke="var(--color-warn)" strokeWidth="2" pointerEvents="none" />
    </ResponsiveSvg></AnnotatedScene>
  </Scene3DFrame>;
}
function MemoryScene({ query }: { query: number }) {
  const { combinationOrigin, activeData } = useAtlasSource(); const es = useShellLang() === 'es';
  const selected = useLinkedView(state => state.selectedId);
  const origins = combinationOrigin?.methods.find(v => v.name === 'ValidationMix')?.memory_origins ?? [];
  const n = activeData?.history.length ?? 1, h = activeData?.horizon ?? 1, complete = completedMemory(origins, h, query);
  const x = (value: number) => 75 + 840 * value / n;
  const selectedOrigin = origins.find(origin => `origin:${origin}` === selected) ?? origins[0];
  const rowY = (i: number) => 110 + i * Math.min(32, 350 / Math.max(1, origins.length));
  return <ResponsiveSvg label={es ? 'Disponibilidad de objetivos históricos' : 'Historical target availability'}>
    <title>{es ? 'Sólo objetivos completos antes de la consulta' : 'Only complete targets before the query'}</title>
    <line x1="75" y1="540" x2="915" y2="540" className="cs-flow-line" /><text x="75" y="575">0</text><text x="915" y="575" textAnchor="end">{n} {es ? 'observaciones' : 'observations'}</text>
    <line data-subject="query completed horizon" x1={x(query)} y1="90" x2={x(query)} y2="540" stroke="var(--color-warn)" strokeDasharray="6 5" />
    {origins.map((origin, i) => <g key={origin} pointerEvents="none" aria-hidden="true">
      <rect x={x(origin)} y={rowY(i)} width={Math.max(3, x(origin + h) - x(origin))} height="18" className={complete.includes(origin) ? 'cs-memory-complete' : 'cs-memory-pending'} />
    </g>)}
    {selectedOrigin != null && <Glyph id={`origin:${selectedOrigin}`} label={`${es ? 'Origen' : 'Origin'} ${selectedOrigin}`}>
      <circle cx={x(selectedOrigin + h / 2)} cy={rowY(origins.indexOf(selectedOrigin)) + 9} r="30" fill="transparent" />
      <circle data-subject={`origin:${selectedOrigin}`} cx={x(selectedOrigin + h / 2)} cy={rowY(origins.indexOf(selectedOrigin)) + 9} r="7" />
    </Glyph>}
    {selectedOrigin != null && <text x="500" y="510" textAnchor="middle">{es ? 'Origen seleccionado' : 'Selected origin'} {selectedOrigin} → {selectedOrigin + h}</text>}
    {!origins.length && <text x="500" y="300" textAnchor="middle">{es ? 'Sin memoria validada para este origen' : 'No verified memory for this origin'}</text>}
    <text x="500" y="620" textAnchor="middle">{es ? 'Verde: observable · gris: pendiente' : 'Green: observable · grey: pending'}</text>
  </ResponsiveSvg>;
}
export default function AtlasStory() {
  const source = useAtlasSource();
  const [stageBand, setStageBand] = useState(0);
  const { activeData: data, allMethods, allRows, mode, setMode, caseId, setCaseId, index, err, combinationOrigin } = source;
  const es = useShellLang() === 'es'; const [params, setParams] = useSearchParams();
  const navigate = useNavigate(), pathStep = useParams().step;
  const requested = pathStep ?? params.get('story'), active: ShowcaseKind = SHOWCASE_KINDS.includes(requested as ShowcaseKind) ? requested as ShowcaseKind : 'system';
  const selected = useLinkedView(state => state.selectedId), select = useLinkedView(state => state.select);
  const { cursor, scrub, inputProps, markerProps } = useLinkedCursor();
  const n = data?.history.length ?? 0, h = data?.horizon ?? 0;
  const namedQuery = Number(params.get('q') ?? n), query = Number.isInteger(namedQuery) ? Math.max(0, Math.min(n, namedQuery)) : n;
  useEffect(() => {
    if (!n || !h || active === 'method') return;
    const min = active === 'system' || active === 'domain' ? 0 : n;
    const max = active === 'domain' ? Math.max(0, n - 3) : active === 'system' ? n - 1 : n + h - 1;
    const next = Math.max(min, Math.min(max, cursor ?? min));
    if (cursor !== next) scrub(next);
  }, [active, n, h, cursor, scrub]);
  const selectedMethod = allMethods.find(v => v.name === selected) ?? allMethods[0], selectedRow = allRows.find(v => v.name === selectedMethod?.name);
  const experts = allMethods.filter(v => EXPERTS.includes(v.name)), mix = combinationOrigin?.methods.find(v => v.name === 'ValidationMix');
  const memory = mix?.memory_origins ?? [], complete = completedMemory(memory, h, query);
  const fmt = (value: number | null | undefined, digits = 3) => formatNumber(value, es ? 'es' : 'en', { digits });
  const units = mode === 'synthetic' ? (es ? 'unidades generadas' : 'generated units') : (es ? 'unidades de origen (no especificadas)' : 'source units (unspecified)');
  function move(id: string) { navigate(href(id), { replace: true }); }
  function href(id: string) { const next = new URLSearchParams(params); next.delete('story'); next.delete('view'); return `/story/${id}?${next}`; }
  const sourceControls = <div className="cs-story-source"><label>{es ? 'Fuente' : 'Source'} <select aria-label={es ? 'Fuente de la historia' : 'Story source'} value={mode} onChange={event => setMode(event.target.value as 'baked' | 'synthetic')}>
    <option value="baked">{es ? 'Caso registrado' : 'Baked case'}</option><option value="synthetic">{es ? 'Generador determinista' : 'Deterministic generator'}</option></select></label>
    {mode === 'baked' && <label>{es ? 'Caso' : 'Case'} <select aria-label={es ? 'Caso de la historia' : 'Story case'} value={caseId} onChange={event => setCaseId(event.target.value)}>{index?.cases.map(item => <option key={item.case_id} value={item.case_id}>{item.case_id}</option>)}</select></label>}
    <small>{mode === 'synthetic' ? (es ? `Datos generados; semilla ${source.knobs.seed}. Modifica parámetros en Explorar.` : `Generated data; seed ${source.knobs.seed}. Edit parameters in Explore.`) : `${source.manifest?.real_or_synthetic ?? ''} · ${caseId}`}</small></div>;
  function methodRows(names = allMethods.map(v => v.name)) {
    return <div className="cs-story-methods">{names.map(name => { const row = allRows.find(v => v.name === name), weight = mix?.weights?.[EXPERTS.indexOf(name)];
      return <LinkedButton key={name} id={name} side="panel"><span>{methodLabel(name)}</span><span>{active === 'component' && weight != null ? `${fmt(100 * weight, 1)}%` : `MASE ${fmt(row?.mase)}`}</span></LinkedButton>; })}</div>;
  }
  function panel(kind: ShowcaseKind) {
    return <div className="cs-story-evidence">{sourceControls}<p className="cs-story-provenance">{mode === 'synthetic' ? (es ? 'Cálculo local con historia generada; no es evidencia de precisión en datos reales.' : 'Local computation on generated history; not authentic-data accuracy evidence.') : (es ? 'Reproducción de resultados admitidos; selección descriptiva, no decisión operativa automática.' : 'Replay of admitted results; descriptive selection, not an automatic operational decision.')}</p>
      {kind === 'system' && <>{['prefix', 'experts', 'target'].map((id, i) => <LinkedButton key={id} id={id} side="panel">{[`${n} ${es ? 'observaciones de ajuste' : 'fitting observations'}`, `${allMethods.length} ${es ? 'pronósticos' : 'forecasts'}`, `${h} ${es ? 'objetivos reservados' : 'reserved targets'}`][i]}</LinkedButton>)}<label>{es ? 'Índice observado' : 'Observed index'} <input aria-label={es ? 'Índice observado' : 'Observed index'} type="range" min="0" max={Math.max(0, n - 1)} {...inputProps} value={Math.max(0, Math.min(n - 1, cursor ?? 0))} /></label><output {...markerProps}>{fmt(data?.history[Math.max(0, Math.min(n - 1, cursor ?? 0))])} {units}</output><p>{es ? 'Los diagnósticos de Explorar pueden describir la serie completa; el pronóstico sólo utiliza su prefijo observado.' : 'Explore diagnostics may describe the complete series; forecasts use only its observed prefix.'}</p></>}
      {kind === 'component' && <><p>{mix?.weights ? (es ? 'Pesos ValidationMix de un estudio independiente; prefijo completo verificado por SHA-256.' : 'ValidationMix weights from a separate study; full prefix verified by SHA-256.') : (es ? 'Extrapolaciones locales. No se inventan pesos sin un origen verificado.' : 'Local extrapolations. No weights without a verified origin.')}</p>{methodRows(experts.map(v => v.name))}</>}
      {kind === 'domain' && <><p>{es ? 'Tres valores consecutivos por punto, todos anteriores al origen. La rotación cambia la cámara, no los datos.' : 'Three consecutive values per point, all before the origin. Rotation changes the camera, not the data.'}</p><label>{es ? 'Observación inicial' : 'Starting observation'} <input aria-label={es ? 'Observación inicial' : 'Starting observation'} type="range" min="0" max={Math.max(0, n - 3)} {...inputProps} value={Math.max(0, Math.min(n - 3, cursor ?? 0))} /></label>
        {[0, Math.max(0, Math.min(n - 3, cursor ?? 0)), Math.max(0, n - 3)].filter((v, i, a) => a.indexOf(v) === i).map(i => <LinkedButton key={i} id={`observation:${i}`} side="panel">{es ? 'Observación' : 'Observation'} {i}</LinkedButton>)}<p>{units}. {es ? 'Escala gráfica común para los tres ejes.' : 'Common graphical scale for all three axes.'}</p></>}
      {(kind === 'dynamics' || kind === 'decision') && <><p>{es ? 'MASE requiere una escala estacional positiva. Las métricas no definidas se muestran como no disponibles.' : 'MASE requires a positive seasonal scale. Undefined scores are shown as unavailable.'}</p><label>{es ? 'Índice del objetivo' : 'Target index'} <input aria-label={es ? 'Índice del objetivo' : 'Target index'} type="range" min={n} max={Math.max(n, n + h - 1)} {...inputProps} value={Math.max(n, Math.min(n + h - 1, cursor ?? n))} /></label>
        <output {...markerProps}>{es ? 'Objetivo' : 'Target'} {Math.max(n, Math.min(n + h - 1, cursor ?? n))}: {fmt(data?.actual[Math.max(0, Math.min(h - 1, (cursor ?? n) - n))])} {units}</output>{methodRows()}<p>{es ? 'Este bloque no establece una clasificación general.' : 'This block does not establish a general ranking.'}</p></>}
      {kind === 'method' && <><label>{es ? 'Consulta histórica' : 'Historical query'} <input aria-label={es ? 'Consulta histórica' : 'Historical query'} type="range" min="0" max={n} step="1" value={query} onChange={event => { const value = event.target.value; setParams(previous => { const next = new URLSearchParams(previous); next.set('q', value); return next; }, { replace: true }); }} /></label><p>{complete.length}/{memory.length} {es ? 'bloques completos en' : 'complete blocks at'} q={query}. {es ? 'Disponibilidad retrospectiva; no se recalculan pesos en cada posición.' : 'Retrospective availability; weights are not refitted at each position.'}</p>
        {memory.map(origin => <LinkedButton key={origin} id={`origin:${origin}`} side="panel">o={origin}, o+H={origin + h} · {complete.includes(origin) ? (es ? 'observable' : 'observable') : (es ? 'pendiente' : 'pending')}</LinkedButton>)}{!memory.length && <p>{es ? 'Sin memoria con enlace de prefijo verificado.' : 'No memory with a verified prefix binding.'}</p>}</>}
      <small>{es ? 'Origen' : 'Source'}: {mode === 'synthetic' ? `seed=${source.knobs.seed}` : caseId} · {n} → {h}. {mode === 'baked' && <a href={`${import.meta.env.BASE_URL}data/fresh-reevaluation.json`}>{es ? 'Comparación completa' : 'Full comparison'}</a>}</small>{err && <p role="alert">{err}</p>}
    </div>;
  }
  function plot(kind: 'component' | 'dynamics' | 'decision') {
    if (!data) return <p role="status">{err || (es ? 'Cargando fuente admitida…' : 'Loading admitted source…')}</p>;
    const methods = kind === 'component' ? experts : selectedMethod ? [selectedMethod] : [], xs = Array.from({ length: h }, (_, i) => n + i);
    const series = kind === 'dynamics' ? methods.map(v => ({ label: v.name, values: v.point.map((p, i) => p - data.actual[i]), color: v.color }))
      : [...methods.map(v => ({ label: v.name, values: v.point, color: v.color, width: v.name === selectedMethod?.name ? 3 : 1.2 })), ...(kind === 'decision' && selectedMethod ? [{ label: 'q0.1', values: selectedMethod.lower, color: selectedMethod.color, dash: [4, 3] }, { label: 'q0.9', values: selectedMethod.upper, color: selectedMethod.color, dash: [4, 3] }] : []), { label: es ? 'Objetivo reservado' : 'Reserved target', values: data.actual, color: 'var(--color-fg)' }];
    const lead = Math.max(0, Math.min(h - 1, (cursor ?? n) - n));
    const quantities = kind === 'component' ? experts.slice(0, 3).map(v => ({ label: v.name, value: v.point[lead] }))
      : kind === 'dynamics' ? [{ label: es ? 'Pronóstico' : 'Forecast', value: selectedMethod?.point[lead] }, { label: es ? 'Objetivo' : 'Target', value: data.actual[lead] }, { label: es ? 'Error firmado' : 'Signed error', value: selectedMethod ? selectedMethod.point[lead] - data.actual[lead] : NaN }]
      : [{ label: 'q0.1', value: selectedMethod?.lower[lead] }, { label: 'q0.5', value: selectedMethod?.point[lead] }, { label: 'q0.9', value: selectedMethod?.upper[lead] }];
    const annotationItems: SceneCalloutDef[] = quantities.map((quantity, i) => ({ id: `snapshot-${i}`, eyebrow: bi(methodLabel(quantity.label), methodLabel(quantity.label)), value: fmt(quantity.value), unit: bi(mode === 'synthetic' ? 'generated units' : 'source units', mode === 'synthetic' ? 'unidades generadas' : 'unidades de origen'), state: 'normal', anchor: { x: .5, y: .9 }, source: bi(`${kind === 'component' ? quantity.label : methodLabel(selectedMethod?.name ?? '')} · lead ${lead + 1}`, `${kind === 'component' ? quantity.label : methodLabel(selectedMethod?.name ?? '')} · paso ${lead + 1}`) }));
    return <AnnotatedScene items={annotationItems} onBand={setStageBand}><div className="cs-story-chart"><div className="cs-story-scene-choices">{(kind === 'component' ? experts : selectedMethod ? [selectedMethod] : []).map(v => <LinkedButton key={v.name} id={v.name} side="scene">{methodLabel(v.name)}</LinkedButton>)}</div>
      <Stage label={bi('Forecast paths on reserved targets', 'Pronósticos sobre objetivos reservados')}>{() => <UPlotChart xs={xs} series={series} height="fill" xPrecision={0} yLabel={`${kind === 'dynamics' ? (es ? 'Error firmado' : 'Signed error') : (es ? 'Valor' : 'Value')} · ${units}`} xLabel={es ? 'Índice de observación' : 'Observation index'} ariaSummary={kind === 'dynamics' ? (es ? 'Pronóstico menos objetivo; cero como referencia' : 'Forecast minus target; zero reference') : (es ? 'Trayectorias sobre el mismo bloque reservado' : 'Forecast paths on the same reserved block')}
        refLines={[...(kind === 'dynamics' ? [{ y: 0, label: '0' }] : []), ...(cursor != null && cursor >= n && cursor < n + h ? [{ x: cursor, label: es ? 'Objetivo seleccionado' : 'Selected target' }] : [])]} onPick={i => scrub(n + i)} />}</Stage>
      <p className="cs-story-chart-caption">{kind === 'decision' ? `${methodLabel(selectedMethod?.name ?? '')} · MASE ${fmt(selectedRow?.mase)} · ${es ? 'cobertura del bloque' : 'block coverage'} ${fmt((selectedRow?.coverage ?? NaN) * 100, 1)}%` : kind === 'dynamics' ? (es ? 'Cada error conserva signo y posición temporal.' : 'Each error retains its sign and temporal position.') : (es ? 'Mismo prefijo; objetivos visibles sólo para evaluar.' : 'Same prefix; targets visible only for evaluation.')}</p><div className="cs-story-leads">{quantities.map((quantity, i) => <output data-subject={`snapshot-${i}`} key={i}>{methodLabel(quantity.label)}: {fmt(quantity.value)}</output>)}</div></div></AnnotatedScene>;
  }
  const definitions: { id: ShowcaseKind; verb: ReturnType<typeof bi>; headline: ReturnType<typeof bi>; summary: ReturnType<typeof bi>; stage: ReactNode }[] = [
    { id: 'system', verb: bi('Trace the system', 'Seguir el sistema'), headline: bi(`${n} observations precede ${h} reserved targets`, `${n} observaciones preceden ${h} objetivos reservados`), summary: bi('Follow the same observed prefix into every forecast.', 'Sigue el mismo prefijo observado hasta cada pronóstico.'), stage: <AnnotatedScene onBand={setStageBand} items={[
      { id: 'prefix', eyebrow: bi('Observed prefix', 'Historia observada'), value: String(n), unit: bi('observations', 'observaciones'), state: 'normal', anchor: { x: .175, y: .44 }, source: bi('Before forecast origin', 'Antes del pronóstico') },
      { id: 'experts', eyebrow: bi('Compared methods', 'Métodos comparados'), value: String(allMethods.length), unit: bi('forecasts', 'pronósticos'), state: 'normal', anchor: { x: .5, y: .44 }, source: bi('Admitted paths', 'Trayectorias admitidas') },
      { id: 'target', eyebrow: bi('Reserved block', 'Bloque reservado'), value: String(h), unit: bi('observations', 'observaciones'), state: 'warning', anchor: { x: .825, y: .44 }, source: bi('Excluded from fit', 'Fuera del ajuste') },
    ]}><FlowScene /></AnnotatedScene> },
    { id: 'component', verb: bi('Inspect the experts', 'Inspeccionar expertos'), headline: bi(`${experts.length} experts expose different extrapolations`, `${experts.length} expertos muestran extrapolaciones diferentes`), summary: bi('Inspect paths and verified combination weights.', 'Inspecciona trayectorias y pesos verificados.'), stage: plot('component') },
    { id: 'domain', verb: bi('Rotate the history', 'Rotar la historia'), headline: bi('3 delayed coordinates use observed history only', '3 coordenadas retardadas usan sólo historia observada'), summary: bi('Explore sequence geometry without claiming an attractor.', 'Explora geometría sin afirmar un atractor.'), stage: <DelayScene onBand={setStageBand} /> },
    { id: 'dynamics', verb: bi('Follow the errors', 'Seguir los errores'), headline: bi(`${h} leads expose signed forecast errors`, `${h} pasos muestran errores con signo`), summary: bi('Scrub held-out errors; not native state-update timing.', 'Recorre errores reservados; no mide actualizaciones nativas.'), stage: plot('dynamics') },
    { id: 'method', verb: bi('Check information timing', 'Verificar disponibilidad'), headline: bi(`${complete.length} of ${memory.length} memory blocks are observable`, `${complete.length} de ${memory.length} bloques son observables`), summary: bi('Inspect which historical target blocks have completed.', 'Inspecciona qué bloques históricos terminaron.'), stage: <AnnotatedScene onBand={setStageBand} items={[
      { id: 'query', eyebrow: bi('Historical query', 'Consulta histórica'), value: String(query), unit: bi('index', 'índice'), state: 'selected', anchor: { x: .5, y: .5 }, source: bi('Chosen cutoff q', 'Corte elegido q') },
      { id: 'completed', eyebrow: bi('Completed blocks', 'Bloques completos'), value: String(complete.length), unit: bi('target blocks', 'bloques objetivo'), state: memory.length ? 'normal' : 'inactive', anchor: { x: .3, y: .5 }, source: bi('origin + horizon ≤ query', 'origen + horizonte ≤ consulta') },
      { id: 'horizon', eyebrow: bi('Reserved horizon', 'Horizonte reservado'), value: String(h), unit: bi('obs. / block', 'obs. / bloque'), state: 'warning', anchor: { x: .7, y: .5 }, source: bi('Case horizon', 'Horizonte del caso') },
    ]}><MemoryScene query={query} /></AnnotatedScene> },
    { id: 'decision', verb: bi('Compare the evidence', 'Comparar evidencia'), headline: bi(`${allRows.length} forecasts share 1 reserved block`, `${allRows.length} pronósticos comparten 1 bloque reservado`), summary: bi('Compare a selected path, interval and held-out score.', 'Compara trayectoria, intervalo y puntuación reservada.'), stage: plot('decision') },
  ];
  const steps: StoryStep[] = definitions.map((definition, i) => ({ ...definition, number: i + 1, href: href(definition.id), accent: (i % 5 + 1) as StoryStep['accent'], panel: panel(definition.id) }));
  return <StoryFrame steps={steps} activeId={active} mobileStageMinHeight={Math.min(900, Math.max(620, Math.round(stageBand + 440)))} onStepChange={id => { move(id); select(id === 'system' ? 'prefix' : id === 'method' ? (memory.length ? `origin:${memory[0]}` : null) : selectedMethod?.name ?? null, 'external'); }} onExit={() => { const next = new URLSearchParams(params); next.delete('story'); next.delete('focus'); next.set('view', 'explore'); navigate(`/app?${next}`); }} />;
}
