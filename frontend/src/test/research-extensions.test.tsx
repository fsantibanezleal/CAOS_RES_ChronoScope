// @vitest-environment jsdom
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { SequenceDiagnostics, type SequenceData } from '../render/SequenceDiagnostics';
import { admitForecastability } from '../lib/forecastability';

vi.mock('../render/UPlotChart', () => ({ UPlotChart: (p: { ariaSummary: string; xs: number[]; onPick?: (index:number)=>void; refLines?: { x?: number }[]; series: { values: (number | null)[] }[] }) =>
  <><output data-testid={p.ariaSummary}>{JSON.stringify({ count: p.xs.length, marks: p.refLines,
    visibleCounts:p.series.map(s => s.values.filter(v => v != null).length) })}</output>
    {p.onPick && <button onClick={()=>p.onPick!(p.xs.length-1)}>Pick from {p.ariaSummary}</button>}</> }));

afterEach(cleanup);
const analysis = JSON.parse(readFileSync(resolve('../data/derived/REAL_electricity/analysis.json'), 'utf8'));

describe('Original-sequence diagnostic consumer', () => {
  it('adversarial: uses the full original axis, exposes candidates and changes the annotation filter', () => {
    render(<SequenceDiagnostics data={analysis.sequence as SequenceData} />);
    expect(analysis.n).toBeGreaterThan(300);
    const chart = screen.getByTestId('Original sequence with detected pattern windows');
    expect(JSON.parse(chart.textContent!).count).toBe(analysis.n);
    expect(screen.getByText('Detected candidate windows on the original axis')).toBeTruthy();
    fireEvent.change(screen.getByRole('combobox', { name: 'Sequence annotations' }), { target: { value: 'motif' } });
    const marks = JSON.parse(chart.textContent!).marks;
    expect(marks).toEqual([]);
    expect(JSON.parse(chart.textContent!).visibleCounts[1]).toBe(analysis.sequence.matrix_profile.window*2);
    expect(screen.getByText(/Binary Lempel/)).toBeTruthy();
  });
  it('makes absent and restricted source diagnostics explicit', () => {
    render(<SequenceDiagnostics data={{ available: false, reason: 'source terms' }} />);
    expect(screen.getByText(/diagnostics are unavailable/)).toBeTruthy();
    expect(screen.queryByTestId('Exact Matrix Profile')).toBeNull();
  });
  it('adversarial: clears a picked profile window when the source changes to a shorter case', () => {
    const shorter = JSON.parse(readFileSync(resolve('../data/derived/BRKV_level_shift/analysis.json'),'utf8'));
    const { rerender } = render(<SequenceDiagnostics data={analysis.sequence as SequenceData} />);
    fireEvent.click(screen.getByRole('button',{name:'Pick from Exact Matrix Profile'}));
    const selectedIndex = analysis.sequence.matrix_profile.profile.length-1;
    expect(selectedIndex).toBeGreaterThan(shorter.n);
    const marks = () => JSON.parse(screen.getByTestId('Original sequence with detected pattern windows').textContent!).marks;
    expect(marks().some((m:{x:number})=>m.x===selectedIndex)).toBe(true);
    rerender(<SequenceDiagnostics data={shorter.sequence as SequenceData} />);
    expect(marks().some((m:{x:number})=>m.x===selectedIndex)).toBe(false);
    expect(marks().every((m:{x:number})=>m.x<shorter.n)).toBe(true);
  });
});

describe('Corpus admission boundary', () => {
  it('adversarial: rejects trials, missing inventories and the unrelated fifteen-case experiment', () => {
    for (const planted of [{}, { complete:false }, { schema:'chronoscope.forecastability/v1',complete:true,source_n:15 },
      { schema:'chronoscope.forecastability/v1',complete:true,source_n:4227,series:[],included_n:4227 }]) {
      expect(() => admitForecastability(planted)).toThrow();
    }
  });
});
