import { DocPage, ExecutiveView, Tabs, useShellLang } from '@fasl-work/caos-app-shell';
import executive from '../../../content/executive.json';
import TechnicalIntroduction from './TechnicalIntroduction';

// Introduction: what ChronoScope is (a forecasting + analysis atlas), the no-free-lunch thesis, the two
// pillars (understand + forecast), the streaming story, and the honest scope. Content transcribed from the
// persisted research dossiers (docs/research + wip/chronoscope), never improvised.
export default function Introduction() {
  const es = useShellLang() === 'es';
  return <DocPage
    title={{ en: 'Introduction', es: 'Introducción' }}
    lede={es
      ? 'Las decisiones de inventario, capacidad y personal dependen de pronósticos realizados antes de observar la demanda. Esta introducción presenta el problema de planificación y explica cómo se comparan modelos, información disponible e incertidumbre mediante casos delimitados y resultados reproducibles.'
      : 'Inventory, capacity and staffing decisions depend on forecasts made before demand is observed. This introduction frames the planning problem and explains how models, available information and uncertainty are compared through bounded cases, explicit forecast origins and reproducible computational results.'}
  >
    <Tabs ariaLabel={es ? 'Vistas de la introducción' : 'Introduction views'} tabs={[
      { id: 'executive', label: es ? 'Ejecutiva' : 'Executive', content: <ExecutiveView data={executive} base={import.meta.env.BASE_URL} /> },
      { id: 'technical', label: es ? 'Técnica' : 'Technical', content: <TechnicalIntroduction /> },
    ]} />
  </DocPage>;
}
