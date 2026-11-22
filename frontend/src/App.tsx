import { Link, Route, Routes, useParams, useSearchParams } from 'react-router';
import { Activity } from 'lucide-react';
import { AppShell, CitationsProvider, Landing, LinkedViewProvider, STANDARD_ROUTES, SurfacePage, useShellLang, type ShellConfig } from '@fasl-work/caos-app-shell';
import { CITATIONS } from './data/citations';
import { architecture } from './architecture';
import { EXTERNAL_LINKS } from './lib/links';
import product from '../../product.json';
import AppPage from './pages/AppPage';
import AtlasStory from './pages/AtlasStory';
import { AtlasSourceProvider } from './state/AtlasSource';
import Introduction from './pages/Introduction';
import Methodology from './pages/Methodology';
import Implementation from './pages/Implementation';
import Experiments from './pages/Experiments';
import Benchmark from './pages/Benchmark';

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
  immersiveRoutes: product.showcase.story_routes,
  footer: {
    provenance: {
      en: 'Four real data excerpts and eleven generated cases. Source licences, method versions and frozen-versus-recomputed provenance are listed in Benchmark. Streaming experiments use preqts.',
      es: 'Cuatro extractos reales y once casos generados. Banco de pruebas detalla licencias, versiones y procedencia congelada o recalculada. Los experimentos de streaming utilizan preqts.',
    },
    disclaimer: {
      en: 'Research examples with explicit sources, seeds and evaluation protocols. Forecast quality, uncertainty and runtime are bounded by the reported experiment; generated cases are labelled.',
      es: 'Ejemplos de investigación con fuentes, semillas y protocolos explícitos. La calidad, incertidumbre y tiempo de cálculo dependen del experimento declarado; los casos generados están identificados.',
    },
  },
};

export default function App() {
  return <CitationsProvider items={CITATIONS}><AppShell config={config}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/app" element={<AtlasSurface />} />
            <Route path="/story/:step" element={<AtlasSurface />} />
            <Route path="/introduction" element={<Introduction />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/implementation" element={<Implementation />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/benchmark" element={<Benchmark />} />
            <Route path="*" element={<Landing />} />
          </Routes>
  </AppShell></CitationsProvider>;
}

function AtlasSurface() {
  return <AtlasSourceProvider><LinkedViewProvider><AtlasSurfaceBody /></LinkedViewProvider></AtlasSourceProvider>;
}

function AtlasSurfaceBody() {
  const lang = useShellLang();
  const { step } = useParams();
  const [params] = useSearchParams();
  const storyParams = new URLSearchParams(params); storyParams.delete('view'); storyParams.delete('focus');
  if (step) return <AtlasStory />;
  return (
    <SurfacePage
      title={{ en: 'Forecasting atlas', es: 'Atlas de pronósticos' }}
      lede={lang === 'es'
        ? 'Inspecciona una serie, compara pronósticos y sigue sus errores y sus intervalos.'
        : 'Inspect a series, compare forecasts, and follow their error and interval behavior.'}
      actions={<Link to={`/story/system?${storyParams}`}>{lang === 'es' ? 'Recorrido de evidencia' : 'Guided evidence walkthrough'}</Link>}
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
