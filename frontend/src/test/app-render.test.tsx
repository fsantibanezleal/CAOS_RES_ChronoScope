// Render smoke: the App workbench mounts and renders (default = synthetic/live mode, no fetch needed), the
// live classical engine runs, and a chart + method leaderboard appear. This verifies the interactive app
// actually renders end to end (types are checked by tsc; logic by parity.test). Full light/dark screenshot
// verification is a later polish slice.
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import App from '../App';

describe('App workbench renders (synthetic live mode)', () => {
  const html = renderToStaticMarkup(<App />);

  it('shows the product heading and the source modes', () => {
    expect(html).toContain('ChronoScope');
    expect(html).toContain('Synthetic (live)');
    expect(html).toContain('Baked case');
  });

  it('renders the interactive chart (svg) and the knobs', () => {
    expect(html).toContain('<svg');
    expect(html).toContain('seasonality m');
    expect(html).toContain('horizon');
  });

  it('runs the live engine and renders a method leaderboard', () => {
    expect(html).toContain('MASE');
    expect(html).toContain('SeasonalNaive');
    expect(html).toContain('HoltWinters');
    // a live MASE number is rendered (contains a decimal in the table region)
    expect(html).toMatch(/\d\.\d\d\d/);
  });
});
