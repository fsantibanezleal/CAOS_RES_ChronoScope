// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router';
import type { ReactNode } from 'react';
import * as api from '../api/artifacts';
import { AtlasSourceProvider, matchingCombinationOrigin, parseSyntheticKnobs, useAtlasSource, type AtlasData } from '../state/AtlasSource';
import { DEFAULT_KNOBS } from '../lib/synthetic';
import type { CaseIndex, CaseManifest, CombinationCase, Trace } from '../lib/contract.types';
import type { Reevaluation } from '../lib/reevaluation.types';

vi.mock('../api/artifacts', () => ({ loadIndex: vi.fn(), loadReevaluation: vi.fn(), loadManifest: vi.fn(),
  loadTrace: vi.fn(), loadAnalysis: vi.fn(), loadStreaming: vi.fn(), loadCombinationCase: vi.fn() }));
vi.mock('../lib/useNLinearForecast', () => ({ useNLinearForecast: () => ({ status: 'unavailable' }) }));
const manifest = (id: string) => ({ case_id: id, artifact: { path: id } }) as CaseManifest;
const trace = (id: string) => ({ case_id: id, horizon: 2, seasonality: 1, actual: [5, 6] }) as Trace;
function mount(path = '/app?case=A') {
  return renderHook(() => ({ source: useAtlasSource(), navigate: useNavigate() }), {
    wrapper: ({ children }: { children: ReactNode }) => <MemoryRouter initialEntries={[path]}><AtlasSourceProvider>{children}</AtlasSourceProvider></MemoryRouter>,
  });
}
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.loadIndex).mockResolvedValue({ cases: ['A', 'B'].map(case_id => ({ case_id })) } as CaseIndex);
  vi.mocked(api.loadReevaluation).mockResolvedValue({ cases: ['A', 'B'].map(case_id => ({ case_id, history: [1, 2, 3, 4], methods: [] })) } as unknown as Reevaluation);
  vi.mocked(api.loadManifest).mockImplementation(async id => manifest(id));
  vi.mocked(api.loadTrace).mockImplementation(async id => trace(id));
  vi.mocked(api.loadCombinationCase).mockRejectedValue(new Error('No combination evidence'));
});
afterEach(cleanup);

describe('Shared atlas source ownership', () => {
  it('deep links load the requested subject and preserve optional-artifact failure separately', async () => {
    const { result } = mount('/app?case=B&story=system');
    await waitFor(() => expect(result.current.source.activeData).not.toBeNull());
    expect(result.current.source.trace?.case_id).toBe('B');
    expect(api.loadManifest).toHaveBeenCalledWith('B');
    expect(result.current.source.err).toBe('');
    expect(result.current.source.combinationError).toContain('No combination evidence');
  });
  it('adversarial: a case change hides old data before the new load resolves', async () => {
    const { result } = mount();
    await waitFor(() => expect(result.current.source.trace?.case_id).toBe('A'));
    vi.mocked(api.loadManifest).mockReturnValue(new Promise(() => {}));
    act(() => result.current.source.setCaseId('B'));
    expect(result.current.source.trace).toBeNull();
    expect(result.current.source.activeData).toBeNull();
    expect(result.current.source.artifactsLoading).toBe(true);
  });
  it('adversarial: a late old case cannot overwrite the current subject', async () => {
    let finish!: (value: CaseManifest) => void;
    vi.mocked(api.loadManifest).mockImplementation(id => id === 'A' ? new Promise(resolve => { finish = resolve; }) : Promise.resolve(manifest(id)));
    const { result } = mount();
    await waitFor(() => expect(api.loadManifest).toHaveBeenCalledWith('A'));
    act(() => result.current.source.setCaseId('B'));
    await waitFor(() => expect(result.current.source.trace?.case_id).toBe('B'));
    await act(async () => finish(manifest('A')));
    expect(result.current.source.trace?.case_id).toBe('B');
  });
  it('adversarial: an unadmitted case never reaches a manifest fetch', async () => {
    const { result } = mount('/app?case=unknown');
    await waitFor(() => expect(result.current.source.err).toContain('not in the admitted inventory'));
    expect(api.loadManifest).not.toHaveBeenCalled();
    expect(result.current.source.activeData).toBeNull();
  });
  it('adversarial: wrong-subject trace cannot become visible', async () => {
    vi.mocked(api.loadTrace).mockResolvedValue(trace('B'));
    const { result } = mount();
    await waitFor(() => expect(result.current.source.err).toContain('Artifact subject differs'));
    expect(result.current.source.trace).toBeNull();
  });
  it('adversarial: story navigation retains the exact history object and generator URL controls', async () => {
    const knobs = { ...DEFAULT_KNOBS, seed: 42 };
    const query = `source=synthetic&knobs=${encodeURIComponent(JSON.stringify(knobs))}`;
    const { result } = mount(`/app?${query}&story=system`);
    const history = result.current.source.activeData!.history;
    act(() => result.current.navigate(`/app?${query}&story=domain`));
    expect(result.current.source.activeData!.history).toBe(history);
    expect(result.current.source.knobs.seed).toBe(42);
  });
  it('adversarial: malformed generator links never produce substitute forecasts', () => {
    const { result } = mount('/app?source=synthetic&knobs=%7B%7D');
    expect(result.current.source.err).toContain('Invalid synthetic configuration');
    expect(result.current.source.activeData).toBeNull();
    for (const invalid of [null, [], { ...DEFAULT_KNOBS, n: 2 }, { ...DEFAULT_KNOBS, level: null }, { ...DEFAULT_KNOBS, seed: -1 }]) {
      expect(parseSyntheticKnobs(JSON.stringify(invalid)).error).not.toBe('');
    }
  });
  it('adversarial: combination weights require the entire prefix digest, not just matching lengths and targets', () => {
    const data = { history: [1, 2, 3], actual: [4, 5], horizon: 2, m: 1 } as AtlasData;
    const origin = { origin: 3, prefix_start: 0, prefix_length: 3, prefix_sha256: 'correct', actual: [4, 5] };
    const document = { horizon: 2, seasonality: 1, origins: [origin] } as CombinationCase;
    expect(matchingCombinationOrigin(document, data, null)).toBeNull();
    expect(matchingCombinationOrigin(document, data, 'wrong')).toBeNull();
    expect(matchingCombinationOrigin(document, data, 'correct')).toBe(origin);
    expect(matchingCombinationOrigin(document, { ...data, actual: [4, 9] }, 'correct')).toBeNull();
  });
});
