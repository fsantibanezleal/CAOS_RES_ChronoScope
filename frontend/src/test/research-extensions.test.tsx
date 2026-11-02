// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { SequenceDiagnostics, type SequenceData } from '../render/SequenceDiagnostics';
import { admitForecastability } from '../lib/forecastability';

vi.mock('../render/UPlotChart', () => ({ UPlotChart: (p: { ariaSummary: string; xs: number[]; refLines?: { x?: number }[] }) =>
  <output data-testid={p.ariaSummary}>{JSON.stringify({ count: p.xs.length, marks: p.refLines })}</output> }));

afterEach(cleanup);
const analysis = JSON.parse(readFileSync(resolve('../data/derived/BRKV_level_shift/analysis.json'), 'utf8'));

describe('Original-sequence diagnostic consumer', () => {
  it('uses the full original axis, exposes candidates and changes the annotation filter', () => {
    render(<SequenceDiagnostics data={analysis.sequence as SequenceData} />);
    const chart = screen.getByTestId('Original sequence with detected pattern windows');
    expect(JSON.parse(chart.textContent!).count).toBe(analysis.n);
    expect(screen.getByText('Detected candidate windows on the original axis')).toBeTruthy();
    fireEvent.change(screen.getByRole('combobox', { name: 'Sequence annotations' }), { target: { value: 'motif' } });
    const marks = JSON.parse(chart.textContent!).marks;
    expect(marks.map((m: { x: number }) => m.x)).toEqual(analysis.sequence.matrix_profile.motifs.flatMap((m: { start: number; match: number }) => [m.start,m.match]));
    expect(screen.getByText(/Binary Lempel/)).toBeTruthy();
  });
  it('makes absent and restricted source diagnostics explicit', () => {
    render(<SequenceDiagnostics data={{ available: false, reason: 'source terms' }} />);
    expect(screen.getByText(/diagnostics are unavailable/)).toBeTruthy();
    expect(screen.queryByTestId('Exact Matrix Profile')).toBeNull();
  });
});

describe('Corpus admission boundary', () => {
  it('rejects trials, missing inventories and the unrelated fifteen-case experiment', () => {
    for (const planted of [{}, { complete:false }, { schema:'chronoscope.forecastability/v1',complete:true,source_n:15 },
      { schema:'chronoscope.forecastability/v1',complete:true,source_n:4227,series:[],included_n:4227 }]) {
      expect(() => admitForecastability(planted)).toThrow();
    }
  });
});
