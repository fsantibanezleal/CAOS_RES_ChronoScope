// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { loadNLinearMeta, runNLinear } from '../lib/onnxRunner';
import { useNLinearForecast } from '../lib/useNLinearForecast';

vi.mock('../lib/onnxRunner', () => ({ loadNLinearMeta: vi.fn(), runNLinear: vi.fn() }));
afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(loadNLinearMeta).mockResolvedValue({ name: 'NLinear', lookback: 4, horizon: 2,
    normalization: 'subtract_last_then_divide_std', sigma_norm: .5, trained_windows: 20 });
  vi.mocked(runNLinear).mockImplementation(async history => ({ point: [history[0], history.at(-1)!], scale: 1 }));
});

describe('live learned input ownership', () => {
  it('adversarial: equal length and equal sum cannot retain an old forecast', async () => {
    const first = [0, 1, 2, 3], second = [3, 2, 1, 0];
    const { result, rerender } = renderHook(({ history }) => useNLinearForecast({ history, horizon: 2 }),
      { initialProps: { history: first } });
    await waitFor(() => expect(result.current.status).toBe('ready'));
    rerender({ history: second });
    await waitFor(() => expect(runNLinear).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.status).toBe('ready'));
    if (result.current.status !== 'ready') throw new Error('No current forecast');
    expect(result.current.forecast.point).toEqual([3, 0]);
    expect(result.current.history).toBe(second);
  });

  it('adversarial: a late old inference cannot overwrite the current input', async () => {
    let completeOld!: (value: { point: number[]; scale: number }) => void;
    vi.mocked(runNLinear).mockImplementationOnce(() => new Promise(resolve => { completeOld = resolve; }));
    const { result, rerender } = renderHook(({ history }) => useNLinearForecast({ history, horizon: 2 }),
      { initialProps: { history: [1, 2, 3, 4] } });
    await waitFor(() => expect(runNLinear).toHaveBeenCalledTimes(1));
    rerender({ history: [8, 7, 6, 5] });
    await waitFor(() => expect(result.current.status).toBe('ready'));
    await act(async () => { completeOld({ point: [100, 100], scale: 1 }); });
    if (result.current.status !== 'ready') throw new Error('No current forecast');
    expect(result.current.forecast.point).toEqual([8, 5]);
  });

  it('adversarial: unsupported horizons do not run the model', async () => {
    const history = [1, 2, 3, 4];
    const { result } = renderHook(() => useNLinearForecast({ history, horizon: 3 }));
    await waitFor(() => expect(result.current.status).toBe('unavailable'));
    expect(runNLinear).not.toHaveBeenCalled();
  });

  it.each([[1, 2, NaN, 4], [5, 5, 5, 5]])('adversarial: unusable lookbacks do not fabricate a scale: %j', async (...values) => {
    const history = values as number[];
    const { result } = renderHook(() => useNLinearForecast({ history, horizon: 2 }));
    await waitFor(() => expect(result.current.status).toBe('unavailable'));
    expect(runNLinear).not.toHaveBeenCalled();
  });

  it('adversarial: malformed inference output cannot become ready', async () => {
    vi.mocked(runNLinear).mockResolvedValue({ point: [NaN, 1], scale: 1 });
    const history = [1, 2, 3, 4];
    const { result } = renderHook(() => useNLinearForecast({ history, horizon: 2 }));
    await waitFor(() => expect(result.current.status).toBe('error'));
  });
});
