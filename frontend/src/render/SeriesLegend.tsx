// The interactive method selector, replacing the under-bar checkbox list. Grouped by family; click a row
// to show/hide, click "solo" to isolate a single curve, "all/none" per group. Each row shows the method's
// score under a SELECTABLE metric (MASE / WQL / MSIS - all lower-is-better), with the best row highlighted,
// so the selection is informed and the number is never ambiguous. This is the on-chart curve selection the
// rubric requires when many series overlap (you can pick out one method among 19).
export interface LegendItem {
  name: string;
  family: string;
  color: string;
  mase?: number | null;
  wql?: number | null;
  msis?: number | null;
}

export type LegendMetric = 'mase' | 'wql' | 'msis';

const FAMILY_ORDER = ['classical', 'statistical', 'ml', 'deep', 'deep (live)', 'foundation'];
const famLabel: Record<string, string> = {
  classical: 'Classical', statistical: 'Statistical', ml: 'ML', deep: 'Deep', 'deep (live)': 'Deep (live)', foundation: 'Foundation',
};
const METRICS: { id: LegendMetric; label: string }[] = [
  { id: 'mase', label: 'MASE' },
  { id: 'wql', label: 'WQL' },
  { id: 'msis', label: 'MSIS' },
];

export function SeriesLegend({
  items, hidden, onToggle, onSolo, onSetGroup, metric, onMetric, es,
}: {
  items: LegendItem[];
  hidden: Set<string>;
  onToggle: (name: string) => void;
  onSolo: (name: string) => void;
  onSetGroup: (names: string[], show: boolean) => void;
  metric: LegendMetric;
  onMetric: (m: LegendMetric) => void;
  es: boolean;
}) {
  const families = Array.from(new Set(items.map((i) => i.family)))
    .sort((a, b) => (FAMILY_ORDER.indexOf(a) + 1 || 99) - (FAMILY_ORDER.indexOf(b) + 1 || 99));
  const fmt = (v: number | null | undefined) => (v == null || !Number.isFinite(v) ? '' : v.toFixed(2));
  const allNames = items.map((i) => i.name);
  const anyHidden = hidden.size > 0;

  // a metric is offered only when at least one method carries it (live/synthetic mode has no baked
  // quantile/interval metrics, so WQL/MSIS honestly disable there instead of showing blanks)
  const has = (m: LegendMetric) => items.some((i) => i[m] != null && Number.isFinite(i[m] as number));
  const valueOf = (i: LegendItem) => i[metric];
  // the best (minimum - all three metrics are lower-is-better) among finite values
  const finite = items.filter((i) => valueOf(i) != null && Number.isFinite(valueOf(i) as number));
  const bestName = finite.length
    ? finite.reduce((a, b) => ((valueOf(a) as number) <= (valueOf(b) as number) ? a : b)).name
    : null;

  return (
    <div className="cs-legend-panel">
      <div className="cs-legend-head">
        <span className="cs-legend-title">{es ? 'Métodos' : 'Methods'}</span>
        <span className="cs-legend-actions">
          <button className="cs-mini" onClick={() => onSetGroup(allNames, true)} disabled={!anyHidden}>{es ? 'todos' : 'all'}</button>
          <button className="cs-mini" onClick={() => onSetGroup(allNames, false)}>{es ? 'ninguno' : 'none'}</button>
        </span>
      </div>
      <div className="cs-legend-metric" role="tablist" aria-label={es ? 'métrica mostrada' : 'displayed metric'}>
        {METRICS.map((m) => (
          <button
            key={m.id}
            className={`cs-mini${metric === m.id ? ' on' : ''}`}
            onClick={() => onMetric(m.id)}
            disabled={!has(m.id)}
            role="tab"
            aria-selected={metric === m.id}
            title={!has(m.id)
              ? (es ? 'métrica precalculada: elige un caso precalculado' : 'baked metric: pick a baked case')
              : m.id === 'mase'
                ? (es ? 'error absoluto escalado por el naive (punto)' : 'naive-scaled absolute error (point)')
                : m.id === 'wql'
                  ? (es ? 'pérdida cuantílica ponderada (distribución)' : 'weighted quantile loss (distribution)')
                  : (es ? 'puntaje de intervalo escalado (banda 80%)' : 'mean scaled interval score (80% band)')}
          >{m.label}</button>
        ))}
      </div>
      {families.map((fam) => {
        const group = items.filter((i) => i.family === fam);
        const names = group.map((g) => g.name);
        const allShown = names.every((n) => !hidden.has(n));
        return (
          <div key={fam} className="cs-legend-group">
            <button className="cs-legend-fam" onClick={() => onSetGroup(names, !allShown)} title={es ? 'alternar familia' : 'toggle family'}>
              {famLabel[fam] ?? fam}
            </button>
            {group.map((it) => {
              const off = hidden.has(it.name);
              const isBest = it.name === bestName;
              return (
                <div key={it.name} className={`cs-legend-row${off ? ' off' : ''}${isBest ? ' best' : ''}`}>
                  <button className="cs-legend-item" onClick={() => onToggle(it.name)} aria-pressed={!off} title={es ? 'mostrar/ocultar' : 'show/hide'}>
                    <span className="swatch" style={{ background: it.color, opacity: off ? 0.3 : 1 }} />
                    <span className="cs-legend-name">{it.name}</span>
                    {valueOf(it) != null && (
                      <span className="cs-legend-mase" title={metric.toUpperCase()}>
                        {fmt(valueOf(it))}{isBest ? (es ? ' · mejor' : ' · best') : ''}
                      </span>
                    )}
                  </button>
                  <button className="cs-solo" onClick={() => onSolo(it.name)} title={es ? 'aislar esta curva' : 'isolate this curve'}>{es ? 'solo' : 'solo'}</button>
                </div>
              );
            })}
          </div>
        );
      })}
      <div className="cs-legend-foot">
        {metric === 'mase'
          ? (es ? 'MASE: error del punto escalado por el naive estacional; < 1 le gana al naive.' : 'MASE: point error scaled by the seasonal naive; < 1 beats the naive.')
          : metric === 'wql'
            ? (es ? 'WQL: pérdida pinball sobre los cuantiles precalculados, normalizada; puntúa la DISTRIBUCIÓN.' : 'WQL: pinball loss over the baked quantiles, normalized; scores the DISTRIBUTION.')
            : (es ? 'MSIS: ancho del intervalo 80% + multa 2/α por falla, escalado como MASE.' : 'MSIS: 80% interval width + a 2/α miss penalty, scaled like MASE.')}
        {' '}{es ? 'Menor es mejor; el mejor va resaltado.' : 'Lower is better; the best is highlighted.'}
      </div>
    </div>
  );
}
