// ChronoScope shell: the six-page nav (hash-routed, so deep links work on GitHub Pages without 404 tricks),
// a header with the product mark + external links, and the footer. The App page is the interactive workbench;
// the other five are the documentation pages filled to depth.
import { useEffect, useState } from 'react';
import { AppPage } from './pages/AppPage';
import { Benchmark } from './pages/Benchmark';
import { Experiments } from './pages/Experiments';
import { Implementation } from './pages/Implementation';
import { Introduction } from './pages/Introduction';
import { Methodology } from './pages/Methodology';

const VERSION = '0.07.000';
const REPO = 'https://github.com/fsantibanezleal/CAOS_RES_ChronoScope';

const PAGES = [
  { id: 'app', label: 'App', Comp: AppPage },
  { id: 'introduction', label: 'Introduction', Comp: Introduction },
  { id: 'methodology', label: 'Methodology', Comp: Methodology },
  { id: 'implementation', label: 'Implementation', Comp: Implementation },
  { id: 'experiments', label: 'Experiments', Comp: Experiments },
  { id: 'benchmark', label: 'Benchmark', Comp: Benchmark },
] as const;

function currentId(): string {
  const h = (typeof window !== 'undefined' ? window.location.hash : '').replace(/^#\/?/, '');
  return PAGES.some((p) => p.id === h) ? h : 'app';
}

export default function App() {
  const [id, setId] = useState<string>(currentId());
  useEffect(() => {
    const on = () => setId(currentId());
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  const page = PAGES.find((p) => p.id === id) ?? PAGES[0];
  const Comp = page.Comp;

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 1080, margin: '0 auto', padding: '0 1rem 3rem' }}>
      <header style={{ display: 'flex', alignItems: 'baseline', gap: 16, flexWrap: 'wrap', padding: '1.1rem 0', borderBottom: '1px solid #30363d', marginBottom: 18 }}>
        <a href="#/app" style={{ fontWeight: 800, fontSize: 20, textDecoration: 'none', color: 'inherit' }}>ChronoScope</a>
        <nav style={{ display: 'flex', gap: 4, flexWrap: 'wrap', flex: 1 }}>
          {PAGES.map((p) => (
            <a key={p.id} href={`#/${p.id}`} style={navLink(p.id === id)}>{p.label}</a>
          ))}
        </nav>
        <a href={REPO} target="_blank" rel="noreferrer" style={{ color: '#58a6ff', fontSize: 14 }}>GitHub</a>
      </header>

      <Comp />

      <footer style={{ marginTop: 40, paddingTop: 12, borderTop: '1px solid #30363d', fontSize: 12.5, color: '#8b949e', lineHeight: 1.6 }}>
        <div><b>ChronoScope</b>, a CAOS research project, v{VERSION}. Developed by Felipe Santibanez-Leal.</div>
        <div>
          Method ladder: classical (own numpy/TS), statistical (<a href="https://github.com/Nixtla/statsforecast" style={fl}>statsforecast</a>),
          ML (<a href="https://github.com/microsoft/LightGBM" style={fl}>LightGBM</a>), foundation
          (<a href="https://github.com/amazon-science/chronos-forecasting" style={fl}>Chronos</a>, Apache-2.0),
          scored by <a href="https://github.com/fsantibanezleal/CAOS_PreqTS" style={fl}>preqts</a>. Real sample:
          UCI ElectricityLoadDiagrams (CC BY 4.0). MIT license.
        </div>
        <div>Numbers come from committed backtest artifacts, never hand-typed. No method wins everywhere.</div>
      </footer>
    </main>
  );
}

function navLink(active: boolean): React.CSSProperties {
  return { padding: '4px 9px', borderRadius: 6, textDecoration: 'none', fontSize: 14, color: active ? '#fff' : '#8b949e', background: active ? '#1f6feb' : 'transparent' };
}
const fl: React.CSSProperties = { color: '#58a6ff' };
