import { useEffect, useState } from 'react';
import { formatNumber, useShellLang } from '@fasl-work/caos-app-shell';
import type { components } from '../lib/contract.gen';
import { UPlotChart, type RefLine } from './UPlotChart';

export type SequenceData = NonNullable<components['schemas']['Analysis']['sequence']>;

export function SequenceDiagnostics({ data }: { data?: SequenceData }) {
  const lang = useShellLang(); const es = lang === 'es';
  const t = (en: string, translated: string) => es ? translated : en;
  const [marks, setMarks] = useState<'all' | 'motif' | 'discord' | 'regime'>('regime');
  const [picked, setPicked] = useState<number | null>(null);
  useEffect(() => setPicked(null), [data]);
  const fmt = (v: number | null) => formatNumber(v, lang, { digits: 4 });
  if (!data || !('values' in data)) return <p>{t('Original-sequence diagnostics are unavailable for this source.', 'Los diagnósticos de la secuencia original no están disponibles para esta fuente.')}</p>;
  const p = data.matrix_profile;
  const refs: RefLine[] = [];
  if (p.available) {
    // Colored intervals and their table retain both edges without overlapping inline labels.
    if (marks === 'all' || marks === 'regime') p.regime_boundaries.forEach(b => refs.push({ x: b, label: 'FLUSS' }));
  }
  if (picked != null && p.available && picked < p.profile.length) refs.push({ x: picked, label: t('Selected profile window', 'Ventana del perfil seleccionada') });
  const entropy = data.multiscale_entropy.scales;
  return <div className="cs-main" data-sequence-diagnostics="ready" data-observation-count={data.n}>
    <label className="cs-ctl">{t('Sequence annotations', 'Anotaciones de la secuencia')}<select className="cs-sel" value={marks} onChange={e => setMarks(e.target.value as typeof marks)}>
      <option value="all">{t('All candidates', 'Todos los candidatos')}</option><option value="motif">{t('Motif pair', 'Par de motivos')}</option>
      <option value="discord">{t('Discord windows', 'Ventanas discordantes')}</option><option value="regime">{t('FLUSS boundaries', 'Límites FLUSS')}</option>
    </select></label>
    <p>{t('Computed on every original observation. Marks are retrospective candidates, not real-time alarms or confirmed change points. Profile-window edges use the original observation index.', 'Se calcula sobre cada observación original. Las marcas son candidatos retrospectivos, no alarmas en tiempo real ni cambios confirmados. Los bordes de ventana usan el índice original.')}</p>
    <UPlotChart xs={data.observation_indices} series={[
      { label: t('Original sequence', 'Secuencia original'), values: data.values, color: 'var(--color-accent)' },
      ...(p.available && (marks === 'all' || marks === 'motif') ? [{ label: t('Motif windows', 'Ventanas de motivos'),
        values: data.values.map((v, i) => p.motifs.some(m => [m.start,m.match].some(start => i >= start && i < start+p.window)) ? v : null), color: 'var(--color-good)', width: 4 }] : []),
      ...(p.available && (marks === 'all' || marks === 'discord') ? [{ label: t('Discord windows', 'Ventanas discordantes'),
        values: data.values.map((v, i) => p.discords.some(d => i >= d.start && i < d.start+p.window) ? v : null), color: 'var(--color-warn)', width: 4 }] : []),
    ]}
      refLines={refs} xPrecision={0} ariaSummary={t('Original sequence with detected pattern windows', 'Secuencia original con ventanas de patrones detectados')} />
    {p.available ? <>
      <p>{t('Window', 'Ventana')}: {p.window}; {t('excluded trivial-match radius', 'radio de exclusión de coincidencias triviales')}: {p.exclusion_zone}.</p>
      <UPlotChart xs={p.profile.map((_, i) => i)} series={[{ label: t('Nearest-shape distance', 'Distancia a la forma más cercana'), values: p.profile, color: 'var(--color-accent-2)' }]}
        ariaSummary={t('Exact Matrix Profile', 'Perfil matricial exacto')} yLabel={t('Z-normalized distance', 'Distancia normalizada Z')}
        xLabel={t('Window start', 'Inicio de ventana')} xPrecision={0}
        onPick={i => setPicked(i)} readout={i => `${t('Window start', 'Inicio de ventana')} ${i}: ${fmt(p.profile[i])}`} />
      <UPlotChart xs={p.corrected_arc_curve.map((_, i) => i)} series={[{ label: 'FLUSS', values: p.corrected_arc_curve, color: 'var(--color-magenta)' }]}
        xLabel={t('Window start', 'Inicio de ventana')} xPrecision={0} yLabel={t('Corrected arc fraction', 'Fracción de arcos corregida')}
        ariaSummary={t('Corrected arc curve', 'Curva de arcos corregida')} refLines={p.regime_boundaries.map(x => ({ x, label: 'FLUSS' }))} />
      <div className="cs-table-scroll"><table className="cs-table"><caption>{t('Detected candidate windows on the original axis', 'Ventanas candidatas sobre el eje original')}</caption><thead><tr><th>{t('Kind', 'Tipo')}</th><th>{t('Start', 'Inicio')}</th><th>{t('End', 'Fin')}</th><th>{t('Distance', 'Distancia')}</th></tr></thead><tbody>
        {p.motifs.flatMap((m, i) => [m.start,m.match].map((start, j) => <tr key={`m${i}-${j}`}><td>{t('Motif pair', 'Par de motivos')}</td><td>{start}</td><td>{start+p.window-1}</td><td>{fmt(m.distance)}</td></tr>))}
        {p.discords.map((d, i) => <tr key={`d${i}`}><td>{t('Discord', 'Discordancia')}</td><td>{d.start}</td><td>{d.start+p.window-1}</td><td>{fmt(d.distance)}</td></tr>)}
        {p.regime_boundaries.map(b => <tr key={`b${b}`}><td>FLUSS</td><td>{b}</td><td>{t("n/a", "n/d")}</td><td>{t("n/a", "n/d")}</td></tr>)}
      </tbody></table></div>
    </> : <p>{p.reason}</p>}
    <UPlotChart xs={entropy.map(s => s.scale)} series={[{ label: t('Sample entropy', 'Entropía muestral'), values: entropy.map(s => s.entropy), color: 'var(--color-good)' }]}
      xPrecision={0} yLabel={t('Entropy (nats)', 'Entropía (nats)')}
      xLabel={t('Coarse-graining scale', 'Escala de grano grueso')} ariaSummary={t('Multiscale entropy with fixed original tolerance', 'Entropía multiescala con tolerancia original fija')} />
    <p>{t('Tolerance remains', 'La tolerancia se mantiene en')} {fmt(entropy[0]?.tolerance ?? null)}; m={data.multiscale_entropy.order}. {t('Missing values mean insufficient observations or no matching templates. Compare curves only under the same length and tolerance protocol.', 'Los valores ausentes indican pocas observaciones o falta de plantillas coincidentes. Compare curvas solo con el mismo protocolo de longitud y tolerancia.')}</p>
    <p>{t('Binary Lempel–Ziv complexity', 'Complejidad binaria Lempel–Ziv')}: {data.lempel_ziv.raw}; {t('normalized', 'normalizada')}: {fmt(data.lempel_ziv.normalized)}. {t('Threshold: median. Finite-sample normalization can exceed one.', 'Umbral: mediana. La normalización de muestras finitas puede superar uno.')}</p>
    <div className="cs-table-scroll"><table className="cs-table"><caption>{t('Time-reversal asymmetry: descriptive, without a significance verdict', 'Asimetría temporal: descriptiva, sin dictamen de significancia')}</caption><thead><tr><th>Lag</th><th>{t('Raw', 'Sin normalizar')}</th><th>{t('Standardized', 'Estandarizada')}</th></tr></thead><tbody>
      {data.time_reversal.map(r => <tr key={r.lag}><td>{r.lag}</td><td>{fmt(r.raw)}</td><td>{fmt(r.standardized)}</td></tr>)}
    </tbody></table></div>
  </div>;
}
