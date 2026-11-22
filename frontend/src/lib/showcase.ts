
export const SHOWCASE_KINDS = ['system', 'component', 'domain', 'dynamics', 'method', 'decision'] as const;
export type ShowcaseKind = typeof SHOWCASE_KINDS[number];
export const EXPERTS = ['SeasonalNaive', 'SES', 'Holt', 'HoltWinters', 'Theta'];
export interface DelayPoint { index: number; value: [number, number, number]; }
/** Display geometry only: all three coordinates precede the forecast origin. */
export function delayCoordinates(history: number[], lag = 1): DelayPoint[] {
  if (!Number.isInteger(lag) || lag < 1 || !history.every(Number.isFinite)) return [];
  const count = history.length - 2 * lag;
  if (count <= 0) return [];
  const stride = Math.max(1, Math.ceil(count / 500));
  return Array.from({ length: Math.ceil(count / stride) }, (_, j) => {
    const index = j * stride;
    return { index, value: [history[index], history[index + lag], history[index + 2 * lag]] };
  });
}
export function projectDelay(value: number[], center: number, span: number, angle: number): [number, number] {
  const [x, y, z] = value.map(v => (v - center) / span);
  const horizontal = Math.cos(angle) * x + Math.sin(angle) * z;
  const depth = -Math.sin(angle) * x + Math.cos(angle) * z;
  return [500 + 510 * horizontal, 330 - 370 * (.8 * y - .35 * depth)];
}
export function completedMemory(origins: number[], horizon: number, query: number): number[] {
  if (!Number.isInteger(horizon) || horizon < 1 || !Number.isInteger(query)) return [];
  return origins.filter(origin => Number.isInteger(origin) && origin >= 0 && origin + horizon <= query);
}
