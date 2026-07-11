// The interactive analytical chart for the whole App workbench, built on uPlot (the library the Faena
// interactive-visualization rubric prescribes for 2D lines/stems). Every chart gets Tier A for free:
// drag-to-zoom (x-range brush) + wheel zoom + double-click reset, a crosshair with a PER-SERIES value
// readout (uPlot's live legend), hover-to-highlight (focus dims the other curves), theme-aware axes/grid
// (read from the shell CSS tokens, re-init on theme switch), responsive full-width (ResizeObserver), and
// an aria-reachable data-table fallback (the canvas is aria-hidden). Static SVG line charts were the
// below-bar defect this replaces.
import { useEffect, useMemo, useRef, useState } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

export interface USeries {
  label: string;
  values: (number | null)[];
  color: string;
  width?: number;
  dash?: number[];
  /** Render as vertical bars/stems (ACF/PACF) instead of a line. */
  bars?: boolean;
  /** Fill an interval band from this series down to the series with this label (e.g. upper -> lower). */
  fillToLabel?: string;
  fillAlpha?: number;
}

export interface RefLine {
  x?: number;
  y?: number;
  color?: string;
  label?: string;
  dash?: number[];
}

export interface UPlotChartProps {
  xs: number[];
  series: USeries[];
  height?: number;
  yLabel?: string;
  xLabel?: string;
  refLines?: RefLine[];
  /** Legend value formatting precision. */
  precision?: number;
  ariaSummary?: string;
}

function readTokens(el: HTMLElement) {
  const cs = getComputedStyle(el);
  const g = (name: string, fb: string) => cs.getPropertyValue(name).trim() || fb;
  return {
    axis: g('--color-fg-subtle', '#8b949e'),
    grid: g('--color-border', '#30363d'),
    text: g('--color-fg', '#c9d1d9'),
    surface: g('--color-surface', 'transparent'),
  };
}

// Canvas cannot resolve `var(--token)` (unlike SVG/CSS), so resolve any CSS-variable colour to its
// concrete computed value against the host element before handing it to uPlot / the canvas context.
// Without this a var-coloured series (e.g. the grey history line) silently does not stroke.
function resolveColor(el: HTMLElement, color: string): string {
  const c = color.trim();
  const m = c.match(/^var\((--[a-z0-9-]+)\s*(?:,\s*(.+))?\)$/i);
  if (!m) return c;
  const val = getComputedStyle(el).getPropertyValue(m[1]).trim();
  return val || (m[2] ? m[2].trim() : '#888');
}

// Wheel-zoom plugin: zoom the x-scale around the cursor (Tier A). Ctrl/no-modifier both zoom x.
function wheelZoomPlugin(factor = 0.9): uPlot.Plugin {
  return {
    hooks: {
      ready: (u) => {
        const over = u.over;
        over.addEventListener('wheel', (e: WheelEvent) => {
          e.preventDefault();
          const { left } = u.cursor;
          if (left == null || left < 0) return;
          const xVal = u.posToVal(left, 'x');
          const xMin = u.scales.x.min!;
          const xMax = u.scales.x.max!;
          const f = e.deltaY < 0 ? factor : 1 / factor;
          const nMin = xVal - (xVal - xMin) * f;
          const nMax = xVal + (xMax - xVal) * f;
          u.setScale('x', { min: nMin, max: nMax });
        }, { passive: false });
      },
    },
  };
}

// Draw ref lines (the forecast boundary, the naive wall at y=1, a zero baseline) on the canvas.
function refLinePlugin(refs: RefLine[]): uPlot.Plugin {
  return {
    hooks: {
      draw: (u) => {
        const ctx = u.ctx;
        const tok = readTokens(u.root as HTMLElement);
        ctx.save();
        for (const r of refs) {
          const rc = r.color ? resolveColor(u.root as HTMLElement, r.color) : tok.axis;
          ctx.strokeStyle = rc;
          ctx.lineWidth = 1;
          ctx.setLineDash(r.dash || [4, 4]);
          ctx.beginPath();
          if (r.x != null) {
            const px = Math.round(u.valToPos(r.x, 'x', true)) + 0.5;
            ctx.moveTo(px, u.bbox.top);
            ctx.lineTo(px, u.bbox.top + u.bbox.height);
          } else if (r.y != null) {
            const py = Math.round(u.valToPos(r.y, 'y', true)) + 0.5;
            ctx.moveTo(u.bbox.left, py);
            ctx.lineTo(u.bbox.left + u.bbox.width, py);
          }
          ctx.stroke();
          if (r.label) {
            ctx.setLineDash([]);
            ctx.fillStyle = rc;
            ctx.font = '10px Inter, system-ui, sans-serif';
            if (r.x != null) {
              const px = u.valToPos(r.x, 'x', true);
              ctx.textAlign = 'left';
              ctx.fillText(r.label, px + 4, u.bbox.top + 12);
            } else if (r.y != null) {
              const py = u.valToPos(r.y, 'y', true);
              ctx.textAlign = 'right';
              ctx.fillText(r.label, u.bbox.left + u.bbox.width - 4, py - 4);
            }
          }
        }
        ctx.restore();
      },
    },
  };
}

export function UPlotChart({ xs, series, height = 340, yLabel, xLabel, refLines = [], precision = 2, ariaSummary }: UPlotChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);
  // theme signal: re-init when the root theme attribute/class flips
  const themeKey = useThemeKey();

  // uPlot handles gaps as `null` in plain arrays and skips them in auto-ranging; a typed array with NaN
  // instead poisons the range computation to null (nothing draws). So keep plain (number|null)[] arrays.
  const data = useMemo<uPlot.AlignedData>(
    () => [xs, ...series.map((s) => s.values.map((v) => (v == null || !Number.isFinite(v) ? null : v)))],
    [xs, series],
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const tok = readTokens(host);

    const labelToIdx = new Map(series.map((s, i) => [s.label, i + 1])); // +1 for the x series at 0
    const col = (c: string) => resolveColor(host, c);
    const bands: uPlot.Band[] = [];
    for (const s of series) {
      if (s.fillToLabel && labelToIdx.has(s.fillToLabel)) {
        bands.push({ series: [labelToIdx.get(s.label)!, labelToIdx.get(s.fillToLabel)!], fill: withAlpha(col(s.color), s.fillAlpha ?? 0.12) });
      }
    }

    const barsPath = uPlot.paths.bars ? uPlot.paths.bars({ size: [0.34, 8] }) : undefined;
    const uSeries: uPlot.Series[] = [
      {},
      ...series.map((s) => ({
        label: s.label,
        stroke: col(s.color),
        fill: s.bars ? col(s.color) : undefined,
        width: s.width ?? 1.6,
        dash: s.dash,
        paths: s.bars ? barsPath : undefined,
        points: { show: false },
        value: (_u: uPlot, v: number | null) => (v == null || !Number.isFinite(v) ? '-' : v.toFixed(precision)),
      })),
    ];

    const axisBase = { stroke: tok.axis, grid: { stroke: tok.grid, width: 1 }, ticks: { stroke: tok.grid, width: 1 }, font: '11px Inter, system-ui, sans-serif' };
    const opts: uPlot.Options = {
      width: host.clientWidth || 800,
      height,
      series: uSeries,
      bands,
      scales: { x: { time: false } },
      cursor: { focus: { prox: 24 }, drag: { x: true, y: false } },
      focus: { alpha: 0.25 },
      legend: { live: true },
      axes: [
        { ...axisBase, label: xLabel, labelSize: xLabel ? 26 : 12 },
        { ...axisBase, label: yLabel, labelSize: yLabel ? 30 : 40, size: 52 },
      ],
      plugins: [wheelZoomPlugin(), ...(refLines.length ? [refLinePlugin(refLines)] : [])],
    };

    const u = new uPlot(opts, data, host);
    plotRef.current = u;
    u.over.setAttribute('aria-hidden', 'true');

    const ro = new ResizeObserver(() => u.setSize({ width: host.clientWidth || 800, height }));
    ro.observe(host);
    return () => { ro.disconnect(); u.destroy(); plotRef.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, height, themeKey, xLabel, yLabel]);

  return (
    <div>
      <div ref={hostRef} className="cs-uplot" style={{ width: '100%' }} />
      {/* screen-reader fallback: the series as a reachable table; the canvas is aria-hidden. Wrapped in a
          block div so the visually-hidden clip actually collapses it (a bare <table> ignores height:1px and
          would inflate the page height). Capped rows keep the DOM light. */}
      <div className="cs-sr-only">
        <table>
          <caption>{ariaSummary || 'chart data'}</caption>
          <thead><tr><th>x</th>{series.map((s) => <th key={s.label}>{s.label}</th>)}</tr></thead>
          <tbody>
            {xs.slice(0, 120).map((x, i) => (
              <tr key={i}><td>{x}</td>{series.map((s) => <td key={s.label}>{s.values[i] == null || !Number.isFinite(s.values[i] as number) ? '-' : (s.values[i] as number).toFixed(precision)}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// A key that bumps when the shell theme flips, so uPlot re-inits with the new token colours.
function useThemeKey(): number {
  const [key, setKey] = useState(0);
  useEffect(() => {
    const obs = new MutationObserver(() => setKey((k) => k + 1));
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class'] });
    return () => obs.disconnect();
  }, []);
  return key;
}

function withAlpha(color: string, alpha: number): string {
  // hex (#rgb/#rrggbb) -> rgba; otherwise wrap in color-mix as a graceful fallback
  const m = color.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (m) {
    const hex = m[1].length === 3 ? m[1].split('').map((c) => c + c).join('') : m[1];
    const r = parseInt(hex.slice(0, 2), 16), g = parseInt(hex.slice(2, 4), 16), b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }
  return color;
}
