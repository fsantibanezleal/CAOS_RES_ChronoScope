// Dependency-free SVG chart: the history, the held-out actual, and one method's forecast with its prediction
// interval. Value read-out is provided by the surrounding App (method selector + metrics); this renders the shapes.
import type { MethodForecast, Trace } from '../lib/contract.types';

const W = 720;
const H = 300;
const PAD = 36;

export function ForecastChart({ trace, method }: { trace: Trace; method: MethodForecast }) {
  const h = trace.horizon;
  const fcastX = Array.from({ length: h }, (_, k) => trace.history_len + k);

  const allY = [
    ...trace.history,
    ...trace.actual,
    ...method.point,
    ...method.lower,
    ...method.upper,
  ].filter((v) => Number.isFinite(v));
  const yMin = Math.min(...allY);
  const yMax = Math.max(...allY);
  const xMin = trace.history_index[0] ?? 0;
  const xMax = trace.history_len + h - 1;

  const sx = (x: number) => PAD + ((x - xMin) / Math.max(1, xMax - xMin)) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - yMin) / Math.max(1e-9, yMax - yMin)) * (H - 2 * PAD);

  const line = (xs: number[], ys: number[]) =>
    xs.map((x, i) => `${i ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(ys[i]).toFixed(1)}`).join(' ');

  const band =
    fcastX.map((x, i) => `${i ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(method.upper[i]).toFixed(1)}`).join(' ') +
    ' ' +
    [...fcastX].reverse().map((x, i) => {
      const j = h - 1 - i;
      return `L${sx(x).toFixed(1)},${sy(method.lower[j]).toFixed(1)}`;
    }).join(' ') +
    ' Z';

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label={`${method.name} forecast`} style={{ maxWidth: 760 }}>
      <line x1={sx(trace.history_len)} y1={PAD} x2={sx(trace.history_len)} y2={H - PAD} stroke="#8b949e" strokeDasharray="4 4" strokeWidth={1} />
      <path d={band} fill="#1f6feb" fillOpacity={0.15} stroke="none" />
      <path d={line(trace.history_index, trace.history)} fill="none" stroke="#8b949e" strokeWidth={1.5} />
      <path d={line(fcastX, method.point)} fill="none" stroke="#1f6feb" strokeWidth={2} />
      <path d={line(fcastX, trace.actual)} fill="none" stroke="#3fb950" strokeWidth={2} strokeDasharray="5 3" />
    </svg>
  );
}
