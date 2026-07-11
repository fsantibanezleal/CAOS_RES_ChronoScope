// Render smoke: the workbench page mounts and renders inside a router (synthetic/live mode needs no fetch),
// the live classical engine runs, and the workbench controls + tabs appear. The shell (header/footer/i18n/
// theme) is the shared @fasl-work/caos-app-shell and is exercised by its own package tests; here we assert
// OUR page renders end to end. Full light/dark screenshot verification runs before deploy.
import { renderToStaticMarkup } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import AppPage from '../pages/AppPage';

describe('App workbench renders (baked-first with synthetic live mode available)', () => {
  const html = renderToStaticMarkup(<MemoryRouter><AppPage /></MemoryRouter>);

  it('shows the source control bar and the workbench tabs', () => {
    expect(html).toContain('Baked case');
    expect(html).toContain('Synthetic (live)');
    expect(html).toContain('Source'); // the full-width control bar label
    for (const label of ['Series', 'Structure', 'Decompose', 'Verdicts', 'Forecast', 'Zoom', 'Horizon', 'Residuals', 'Leaderboard', 'Streaming']) {
      expect(html).toContain(label);
    }
  });
});

describe('App workbench synthetic mode (live engine, no fetch)', () => {
  it('runs the live classical engine when synthetic knobs render', async () => {
    // The synthetic path computes forecasts synchronously in useMemo on first render when mode=synthetic;
    // here we assert the module-level engine produces finite forecasts for the default knobs.
    const { forecastAllLive } = await import('../lib/liveEngine');
    const { DEFAULT_KNOBS, generateSeries } = await import('../lib/synthetic');
    const y = generateSeries(DEFAULT_KNOBS);
    const fc = forecastAllLive(y.slice(0, -DEFAULT_KNOBS.horizon), DEFAULT_KNOBS.seasonality, DEFAULT_KNOBS.horizon, [0.1, 0.5, 0.9]);
    expect(fc.length).toBeGreaterThanOrEqual(5);
    for (const f of fc) {
      expect(f.point.length).toBe(DEFAULT_KNOBS.horizon);
      expect(f.point.every(Number.isFinite)).toBe(true);
    }
  });
});
