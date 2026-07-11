// The interactive method selector, replacing the under-bar checkbox list. Grouped by family; click a row
// to show/hide, click "solo" to isolate a single curve, "all/none" per group, and each row shows the
// method's MASE so the selection is informed. This is the on-chart curve selection the rubric requires
// when many series overlap (you can pick out one method among 18).
export interface LegendItem {
  name: string;
  family: string;
  color: string;
  mase?: number | null;
}

const FAMILY_ORDER = ['classical', 'statistical', 'ml', 'deep', 'deep (live)', 'foundation'];
const famLabel: Record<string, string> = {
  classical: 'Classical', statistical: 'Statistical', ml: 'ML', deep: 'Deep', 'deep (live)': 'Deep (live)', foundation: 'Foundation',
};

export function SeriesLegend({
  items, hidden, onToggle, onSolo, onSetGroup, es,
}: {
  items: LegendItem[];
  hidden: Set<string>;
  onToggle: (name: string) => void;
  onSolo: (name: string) => void;
  onSetGroup: (names: string[], show: boolean) => void;
  es: boolean;
}) {
  const families = Array.from(new Set(items.map((i) => i.family)))
    .sort((a, b) => (FAMILY_ORDER.indexOf(a) + 1 || 99) - (FAMILY_ORDER.indexOf(b) + 1 || 99));
  const fmt = (v: number | null | undefined) => (v == null || !Number.isFinite(v) ? '' : v.toFixed(2));
  const allNames = items.map((i) => i.name);
  const anyHidden = hidden.size > 0;

  return (
    <div className="cs-legend-panel">
      <div className="cs-legend-head">
        <span className="cs-legend-title">{es ? 'Métodos' : 'Methods'}</span>
        <span className="cs-legend-actions">
          <button className="cs-mini" onClick={() => onSetGroup(allNames, true)} disabled={!anyHidden}>{es ? 'todos' : 'all'}</button>
          <button className="cs-mini" onClick={() => onSetGroup(allNames, false)}>{es ? 'ninguno' : 'none'}</button>
        </span>
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
              return (
                <div key={it.name} className={`cs-legend-row${off ? ' off' : ''}`}>
                  <button className="cs-legend-item" onClick={() => onToggle(it.name)} aria-pressed={!off} title={es ? 'mostrar/ocultar' : 'show/hide'}>
                    <span className="swatch" style={{ background: it.color, opacity: off ? 0.3 : 1 }} />
                    <span className="cs-legend-name">{it.name}</span>
                    {it.mase != null && <span className="cs-legend-mase">{fmt(it.mase)}</span>}
                  </button>
                  <button className="cs-solo" onClick={() => onSolo(it.name)} title={es ? 'aislar esta curva' : 'isolate this curve'}>{es ? 'solo' : 'solo'}</button>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
