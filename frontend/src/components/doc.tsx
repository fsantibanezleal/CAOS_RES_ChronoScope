// Shared prose primitives for the documentation pages (deep text, not card grids).
import type { ReactNode } from 'react';

export const H = ({ children }: { children: ReactNode }) => (
  <h2 style={{ marginTop: 26, marginBottom: 8, fontSize: 20 }}>{children}</h2>
);

export const H3 = ({ children }: { children: ReactNode }) => (
  <h3 style={{ marginTop: 18, marginBottom: 6, fontSize: 16 }}>{children}</h3>
);

export const P = ({ children }: { children: ReactNode }) => (
  <p style={{ lineHeight: 1.6, maxWidth: 780 }}>{children}</p>
);

export const UL = ({ items }: { items: ReactNode[] }) => (
  <ul style={{ lineHeight: 1.55, maxWidth: 780 }}>
    {items.map((it, i) => (
      <li key={i} style={{ marginBottom: 3 }}>{it}</li>
    ))}
  </ul>
);

export const Ref = ({ href, children }: { href: string; children: ReactNode }) => (
  <a href={href} target="_blank" rel="noreferrer" style={{ color: '#58a6ff' }}>{children}</a>
);

export const Lead = ({ children }: { children: ReactNode }) => (
  <p style={{ lineHeight: 1.6, maxWidth: 780, color: '#8b949e' }}>{children}</p>
);
