import { useEffect, useState } from 'react';
import { calibratedLinearIntervals } from './calibratedLinearIntervals';
import { loadNLinearMeta, runNLinear } from './onnxRunner';

export interface LiveModelInput { history: number[]; horizon: number; }
interface Forecast { point: number[]; lower: number[]; upper: number[]; }
type State = { status: 'idle' | 'loading' | 'unavailable' | 'error'; reason?: string }
  | { status: 'ready'; forecast: Forecast; history: number[]; horizon: number };

/** Histories are immutable inputs; changing the observations supplies a new array. */
export function useNLinearForecast(input: LiveModelInput | null): State {
  const history = input?.history;
  const horizon = input?.horizon;
  const [state, setState] = useState<State>({ status: 'idle' });
  useEffect(() => {
    let cancelled = false;
    if (!history?.length) { setState({ status: 'idle' }); return; }
    if (!Number.isInteger(horizon) || !horizon || horizon < 1 || !history.every(Number.isFinite)) {
      setState({ status: 'unavailable', reason: 'Invalid finite history or horizon' }); return;
    }
    setState({ status: 'loading' });
    (async () => {
      try {
        const meta = await loadNLinearMeta();
        if (cancelled) return;
        if (horizon !== meta.horizon || history.length < meta.lookback) {
          setState({ status: 'unavailable', reason: 'Unsupported model horizon or lookback' }); return;
        }
        const window = history.slice(-meta.lookback);
        if (window.every(value => value === window[0])) {
          setState({ status: 'unavailable', reason: 'Uncertainty scale is unavailable for a constant lookback' }); return;
        }
        const { point, scale } = await runNLinear(history);
        if (cancelled) return;
        if (point.length !== horizon || !point.every(Number.isFinite) || !Number.isFinite(scale) || scale <= 0) {
          throw new Error('Invalid model output or scale');
        }
        const { lower, upper } = calibratedLinearIntervals(history, point, scale);
        if (!lower.every(Number.isFinite) || !upper.every(Number.isFinite)) throw new Error('Nonfinite model interval');
        setState({ status: 'ready', forecast: { point, lower, upper }, history, horizon });
      } catch (error) {
        if (!cancelled) setState({ status: 'error', reason: String(error) });
      }
    })();
    return () => { cancelled = true; };
  }, [history, horizon]);
  if (state.status === 'ready' && (state.history !== history || state.horizon !== horizon)) {
    return { status: history?.length ? 'loading' : 'idle' };
  }
  return state;
}
