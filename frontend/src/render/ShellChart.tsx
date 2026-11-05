import { BarChart, formatNumber, useShellLang, type ShellColorToken } from '@fasl-work/caos-app-shell';
import { UPlotChart as SharedChart } from '@fasl-work/caos-app-shell/chart';

export interface USeries {
  label: string; values: (number | null)[]; color: string;
  width?: number; dash?: number[]; bars?: boolean; scatter?: boolean;
  /** Paired interval boundaries are drawn as separately readable quantile paths. */
  fillToLabel?: string; fillAlpha?: number;
}
export interface RefLine { x?: number; y?: number; color?: string; label?: string; dash?: number[]; }
export interface UPlotChartProps {
  xs: number[]; series: USeries[]; height?: number | 'fill'; yLabel?: string; xLabel?: string;
  refLines?: RefLine[]; precision?: number; xPrecision?: number; ariaSummary?: string;
  readout?: (index: number) => string;
  onPick?: (index: number) => void;
}
const palette: ShellColorToken[] = ['--color-accent', '--color-accent-2', '--color-magenta', '--color-good', '--color-warn', '--color-bad'];
function colorToken(color: string, index: number): ShellColorToken {
  const token = color.match(/^var\((--color-[a-z0-9-]+)\)$/)?.[1];
  if (token) return token as ShellColorToken;
  if (['#3fb950', '#56d364', '#7ee787'].includes(color)) return '--color-good';
  if (['#d29922', '#e3b341'].includes(color)) return '--color-warn';
  return palette[index % palette.length];
}

/** Product data adapter only; interaction, accessibility, text fitting and themes belong to the shell. */
export function UPlotChart({ xs, series, height = 340, yLabel, xLabel, refLines = [], precision = 3, xPrecision, ariaSummary, readout, onPick }: UPlotChartProps) {
  const lang = useShellLang();
  const es = lang === 'es';
  const title = ariaSummary ?? yLabel ?? (es ? 'Valores de la serie' : 'Series values');
  if (height !== 'fill' && series.length === 1 && series[0].bars && refLines.length === 0) {
    return <BarChart title={title} orientation="horizontal" height={height} values={false}
      axis={{ label: yLabel ?? (es ? 'Cantidad' : 'Count'), format: { decimals: precision } }}
      data={xs.map((x, i) => ({ id: String(i), label: formatNumber(x, lang, { digits: 4 }), value: series[0].values[i] }))} />;
  }
  return <SharedChart title={title} height={height} solo={series.length <= 6} readout={readout} onPick={onPick}
    x={{ values: xs, label: xLabel ?? (es ? 'Índice de observación' : 'Observation index'), time: false, format: { decimals: xPrecision ?? precision } }}
    y={{ label: yLabel ?? (es ? 'Valor' : 'Value'), format: { decimals: precision } }}
    series={series.map((s, i) => ({ id: s.label, label: s.label.replace('TimesFM-2.5', 'TimesFM v2.5'), values: s.values,
      color: colorToken(s.color, i), width: s.width,
      dash: s.dash ?? (s.fillToLabel ? [4, 3] : undefined),
      mode: s.scatter ? 'points' as const : 'line' as const, dots: s.bars,
    }))}
    marks={refLines.filter(r => r.x != null).map(r => ({ x: r.x!, label: r.label ?? (es ? 'Origen' : 'Origin') }))}
    yMarks={refLines.filter(r => r.y != null).map(r => ({ y: r.y!, label: r.label, tone: 'neutral' as const }))}
  />;
}
