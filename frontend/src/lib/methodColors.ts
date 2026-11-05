const tokens = ['--color-accent', '--color-accent-2', '--color-magenta', '--color-good', '--color-warn', '--color-bad'];
const order = ['SeasonalNaive', 'SES', 'Holt', 'HoltWinters', 'Theta', 'AutoETS', 'AutoTheta', 'AutoARIMA',
  'LightGBM', 'NLinear', 'DLinear', 'NHITS', 'NLinear (nf)', 'DLinear (nf)', 'NHITS (nf)',
  'Chronos-Bolt', 'Chronos-2', 'TimesFM-2.5', 'TiRex-2', 'ContextMemory', 'RecencyMean', 'EqualMean', 'Normalized linear (ONNX)'];
export function methodColor(name: string): string {
  const index = order.indexOf(name);
  return `var(${tokens[(index >= 0 ? index : 0) % tokens.length]})`;
}
