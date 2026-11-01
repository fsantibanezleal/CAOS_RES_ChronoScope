import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router';
import { Activity } from 'lucide-react';
import { AppShell, CitationsProvider, Landing, STANDARD_ROUTES, SurfacePage, useShellLang, type ShellConfig } from '@fasl-work/caos-app-shell';
import '@fasl-work/caos-app-shell/styles.css';
import '@fasl-work/caos-app-shell/chart.css';
import 'katex/dist/katex.min.css';
import './chronoscope.css';
import { CITATIONS } from './data/citations';
import { architecture } from './architecture';
import { EXTERNAL_LINKS } from './lib/links';
import product from '../../product.json';
import AppPage from './pages/AppPage';
import Introduction from './pages/Introduction';
import Methodology from './pages/Methodology';
import Implementation from './pages/Implementation';
import Experiments from './pages/Experiments';
import Benchmark from './pages/Benchmark';

// Restore a deep link captured by the Pages 404 shim (public/404.html) before the router mounts.
const redirect = sessionStorage.getItem('cs-redirect');
if (redirect && redirect !== location.pathname + location.search) {
  sessionStorage.removeItem('cs-redirect');
  history.replaceState(null, '', redirect);
}

const config: ShellConfig = {
  product: { name: product.name, mark: <Activity size={18} aria-hidden="true" /> },
  routes: STANDARD_ROUTES,
  links: {
    github: EXTERNAL_LINKS.github,
    personal: EXTERNAL_LINKS.personal,
    portfolio: EXTERNAL_LINKS.portfolio,
  },
  version: __APP_VERSION__,
  build: __BUILD_ID__,
  license: { en: `${product.license} licence`, es: `Licencia ${product.license}` },
  visibility: product.visibility as ShellConfig['visibility'],
  architecture,
  contain: true,
  footer: {
    provenance: {
      en: 'Data: UCI Electricity + Beijing PM2.5 and M4/Monash excerpts (CC-BY 4.0, attributed); synthetic cases seed-generated (MIT). Engines: Nixtla statsforecast/mlforecast/neuralforecast + local Chronos-2, TimesFM 2.5 and TiRex-2 checkpoints (Apache-2.0); streaming eval: preqts (PyPI).',
      es: 'Datos: extractos UCI Electricity + PM2.5 de Beijing y M4/Monash (CC-BY 4.0, con atribución); casos sintéticos generados por semilla (MIT). Motores: Nixtla statsforecast/mlforecast/neuralforecast + checkpoints locales Chronos-2, TimesFM 2.5 y TiRex-2 (Apache-2.0); evaluación streaming: preqts (PyPI).',
    },
    disclaimer: {
      en: 'A research atlas, not a production forecasting service: every number is baked offline by the open seed-deterministic pipeline (or computed live in the browser) and is reproducible from the repo; methods are compared honestly (no free lunch) and synthetic cases are labelled.',
      es: 'Un atlas de investigación, no un servicio de pronóstico de producción: cada número se precalcula offline con el pipeline abierto determinista por semilla (o se calcula en vivo en el navegador) y es reproducible desde el repo; los métodos se comparan honestamente (no hay almuerzo gratis) y los casos sintéticos están etiquetados.',
    },
  },
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <CitationsProvider items={CITATIONS}>
        <AppShell config={config}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/app" element={<AtlasSurface />} />
            <Route path="/introduction" element={<Introduction />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/implementation" element={<Implementation />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/benchmark" element={<Benchmark />} />
            <Route path="*" element={<Landing />} />
          </Routes>
        </AppShell>
      </CitationsProvider>
    </BrowserRouter>
  </StrictMode>,
);

function AtlasSurface() {
  const lang = useShellLang();
  return (
    <SurfacePage
      title={{ en: 'Forecasting atlas', es: 'Atlas de pronósticos' }}
      lede={lang === 'es'
        ? 'Inspecciona una serie, compara pronósticos y sigue sus errores y sus intervalos.'
        : 'Inspect a series, compare forecasts, and follow their error and interval behavior.'}
      tabs={[
        {
          id: 'explore',
          label: lang === 'es' ? 'Explorar' : 'Explore',
          focus: {
            title: { en: 'Forecasting atlas', es: 'Atlas de pronósticos' },
            description: { en: 'Series diagnostics and forecast comparisons', es: 'Diagnósticos de series y comparación de pronósticos' },
          },
          content: <AppPage />,
        },
      ]}
      instrument
      focus
    />
  );
}
