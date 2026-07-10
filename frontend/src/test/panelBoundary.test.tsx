// @vitest-environment jsdom
// The per-panel error boundary contract: a panel that throws renders an identifiable fallback and
// the sibling panels keep rendering (one bad panel must never blank the app).
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PanelBoundary } from '../render/PanelBoundary';

function Bomb(): never {
  throw new Error('NaN geometry');
}

describe('PanelBoundary', () => {
  it('renders the fallback with the panel label and the error detail', () => {
    render(
      <PanelBoundary label="Structure">
        <Bomb />
      </PanelBoundary>,
    );
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByText(/Structure/)).toBeTruthy();
    expect(screen.getByText(/NaN geometry/)).toBeTruthy();
  });

  it('keeps sibling panels alive when one throws', () => {
    render(
      <div>
        <PanelBoundary label="broken">
          <Bomb />
        </PanelBoundary>
        <PanelBoundary label="healthy">
          <div>still here</div>
        </PanelBoundary>
      </div>,
    );
    expect(screen.getByText('still here')).toBeTruthy();
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('renders children untouched when nothing throws', () => {
    render(
      <PanelBoundary label="fine">
        <div>content</div>
      </PanelBoundary>,
    );
    expect(screen.getByText('content')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
