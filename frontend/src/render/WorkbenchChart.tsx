// Interactive forecast chart: history + held-out actual + one or more methods (point line + prediction
// interval band), with a hover cursor that reads out the value of every visible series at the cursor. Pure
// inline SVG, no chart lib. Shared by the App workbench's synthetic (live) and baked (replay) modes.
import { useRef, useState } from 'react';

export interface ChartSeries {
  name: string;
  color: string;
  point: number[];
  lower: number[];
  upper: number[];
}

export interface ChartData {
  history: number[];
  actual: number[]; // held-out truth over the horizon (may be empty)
  horizon: number;
  methods: ChartSeries[];
}

const W = 820;
const H = 340;
const PAD = 40;

export function WorkbenchChart({ data }: { data: ChartData }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverX, setHoverX] = useState<number | null>(null);

  const nHist = data.history.length;
  const h = data.horizon;
  const total = nHist + h;
  const histX = Array.from({ length: nHist }, (_, i) => i);
  const fcastX = Array.from({ length: h }, (_, k) => nHist + k);

  const allY = [
    ...data.history,
    ...data.actual,
    ...data.methods.flatMap((m) => [...m.point, ...m.lower, ...m.upper]),
  ].filter((v) => Number.isFinite(v));
  const yMin = Math.min(...allY);
  const yMax = Math.max(...allY);

  const sx = (x: number) => PAD + (x / Math.max(1, total - 1)) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - yMin) / Math.max(1e-9, yMax - yMin)) * (H - 2 * PAD);

  const line = (xs: number[], ys: number[]) =>
    xs.map((x, i) => `${i ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(ys[i]).toFixed(1)}`).join(' ');

  const band = (m: ChartSeries) => {
    const top = fcastX.map((x, i) => `${i ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(m.upper[i]).toFixed(1)}`).join(' ');
    const bot = [...fcastX].reverse().map((x, i) => {
      const j = h - 1 - i;
      return `L${sx(x).toFixed(1)},${sy(m.lower[j]).toFixed(1)}`;
    }).join(' ');
    return `${top} ${bot} Z`;
  };

  const onMove = (e: React.MouseEvent) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const px = ((e.clientX - rect.left) / rect.width) * W;
    const xIdx = Math.round(((px - PAD) / (W - 2 * PAD)) * (total - 1));
    setHoverX(xIdx >= 0 && xIdx < total ? xIdx : null);
  };

  const readout = () => {
    if (hoverX == null) return null;
    const rows: { label: string; value: number; color: string }[] = [];
    if (hoverX < nHist) rows.push({ label: 'history', value: data.history[hoverX], color: '#8b949e' });
    else {
      const k = hoverX - nHist;
      if (k < data.actual.length) rows.push({ label: 'actual', value: data.actual[k], color: '#3fb950' });
      for (const m of data.methods) rows.push({ label: m.name, value: m.point[k], color: m.color });
    }
    return rows;
  };

  const rows = readout();

  return (
    <div style={{ position: 'relative' }}>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        style={{ maxWidth: W, cursor: 'crosshair' }}
        onMouseMove={onMove}
        onMouseLeave={() => setHoverX(null)}
        role="img"
        aria-label="forecast chart"
      >
        <line x1={sx(nHist)} y1={PAD} x2={sx(nHist)} y2={H - PAD} stroke="#8b949e" strokeDasharray="4 4" strokeWidth={1} />
        {data.methods.map((m) => (
          <path key={`band-${m.name}`} d={band(m)} fill={m.color} fillOpacity={0.12} stroke="none" />
        ))}
        <path d={line(histX, data.history)} fill="none" stroke="#8b949e" strokeWidth={1.4} />
        {data.actual.length > 0 && (
          <path d={line(fcastX.slice(0, data.actual.length), data.actual)} fill="none" stroke="#3fb950" strokeWidth={2} strokeDasharray="5 3" />
        )}
        {data.methods.map((m) => (
          <path key={`pt-${m.name}`} d={line(fcastX, m.point)} fill="none" stroke={m.color} strokeWidth={2} />
        ))}
        {hoverX != null && <line x1={sx(hoverX)} y1={PAD} x2={sx(hoverX)} y2={H - PAD} stroke="#f0883e" strokeWidth={1} />}
      </svg>
      {rows && rows.length > 0 && (
        <div style={{ fontSize: 13, marginTop: 4 }}>
          <b>t={hoverX}</b>{' '}
          {rows.map((r) => (
            <span key={r.label} style={{ marginRight: 12, color: r.color }}>
              {r.label}: {Number.isFinite(r.value) ? r.value.toFixed(2) : '-'}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
