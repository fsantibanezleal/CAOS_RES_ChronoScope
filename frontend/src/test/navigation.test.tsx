// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router';
import App from '../App';

vi.hoisted(() => {
  vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener() {}, removeEventListener() {} }));
  vi.stubGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
});

function Location() {
  const loc = useLocation();
  return <output data-testid="location">{loc.pathname}{loc.search}{loc.hash}</output>;
}
function mount(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><App /><Location /></MemoryRouter>);
}
beforeEach(() => {
  vi.stubGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
  vi.stubGlobal('matchMedia', () => ({ matches: false, addEventListener() {}, removeEventListener() {} }));
  vi.stubGlobal('fetch', () => Promise.reject(new Error('No data service in navigation test')));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe('Actual product routing and document shell', () => {
  it('adversarial: root and unknown links resolve to the executive introduction', async () => {
    for (const path of ['/', '/a-route-that-does-not-exist']) {
      mount(path);
      await waitFor(() => expect(screen.getByTestId('location').textContent).toBe('/introduction'));
      expect(screen.getByRole('tab', { name: /^Executive$/ }).getAttribute('aria-selected')).toBe('true');
      expect(screen.getByRole('tab', { name: /^Technical$/ })).toBeTruthy();
      cleanup();
    }
  });
  it('adversarial: an old root app link preserves its case query and fragment', async () => {
    mount('/?case=REAL_m4_daily#forecast');
    await waitFor(() => expect(screen.getByTestId('location').textContent).toBe('/app?case=REAL_m4_daily#forecast'));
    expect(screen.getByRole('heading', { name: /^Forecasting atlas$/ })).toBeTruthy();
  });
  it('adversarial: landing choice does not change the six header destinations or their order', () => {
    const view = mount('/introduction');
    const routes = [...view.container.querySelectorAll('header a')].map(a => a.getAttribute('href'));
    expect(routes.filter(h => ['/app', '/introduction', '/methodology', '/implementation', '/experiments', '/benchmark'].includes(h ?? '')))
      .toEqual(['/app', '/introduction', '/methodology', '/implementation', '/experiments', '/benchmark']);
  });
  it('adversarial: all documentation routes retain the shared full width document boundary', () => {
    for (const path of ['/introduction', '/methodology', '/implementation', '/experiments', '/benchmark']) {
      const view = mount(path);
      const doc = view.container.querySelector('[data-doc-page]');
      expect(doc?.classList.contains('wide'), path).toBe(true);
      cleanup();
    }
  });
  it('adversarial: story keyboard navigation preserves the selected generator and exits to the actual atlas', async () => {
    const view = mount('/story/system?source=synthetic');
    const story = view.container.querySelector('[data-story]')!;
    expect(story.getAttribute('data-story-step')).toBe('system');
    fireEvent.keyDown(story, { key: 'End' });
    await waitFor(() => expect(screen.getByTestId('location').textContent).toBe('/story/decision?source=synthetic'));
    fireEvent.keyDown(view.container.querySelector('[data-story]')!, { key: 'Home' });
    await waitFor(() => expect(screen.getByTestId('location').textContent).toBe('/story/system?source=synthetic'));
    fireEvent.click(screen.getByRole('button', { name: 'Return to exploration' }));
    await waitFor(() => expect(screen.getByTestId('location').textContent).toBe('/app?source=synthetic&view=explore'));
    expect(screen.getByRole('tab', { name: 'Explore' }).getAttribute('aria-selected')).toBe('true');
  });
  it('adversarial: linked scene selection and panel selection use the same source object', () => {
    const view = mount('/story/system?source=synthetic');
    const scene = view.container.querySelector('[data-linked-view="scene"][data-linked-id="prefix"]')!;
    const panel = view.container.querySelector('[data-linked-view="panel"][data-linked-id="prefix"]')!;
    fireEvent.click(scene);
    expect(panel.getAttribute('data-linked-selected')).toBe('true');
    fireEvent.click(view.container.querySelector('[data-linked-view="panel"][data-linked-id="target"]')!);
    expect(view.container.querySelector('[data-linked-view="scene"][data-linked-id="target"]')!.getAttribute('data-linked-selected')).toBe('true');
    fireEvent.click(panel);
    expect(scene.getAttribute('data-linked-selected')).toBe('true');
  });

});
