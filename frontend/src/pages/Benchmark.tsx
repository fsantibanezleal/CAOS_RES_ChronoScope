import { useEffect, useState } from 'react';
import { Callout, Refs, SubTabs, useShellLang } from '@fasl-work/caos-app-shell';
import { loadIndex, loadManifest, loadTrace } from '../api/artifacts';
import type { Trace } from '../lib/contract.types';

// Benchmark: the cross-case results built LIVE from the committed artifacts (never hand-typed).
// Tabbed: leaderboard (MASE per method x case) · per-family view · coverage · honesty notes.
interface CaseTrace { caseId: string; category: string; trace: Trace; }
const fmt = (v: number | null | undefined, nd = 3) => (v == null || Number.isNaN(v) ? '-' : v.toFixed(nd));

const FAMILY_ORDER = ['classical', 'statistical', 'ml', 'deep', 'foundation'];

export default function Benchmark() {
  const es = useShellLang() === 'es';
  const [rows, setRows] = useState<CaseTrace[]>([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    loadIndex()
      .then(async (ix) => {
        const out: CaseTrace[] = [];
        for (const c of ix.cases) {
          const m = await loadManifest(c.case_id);
          const t = await loadTrace(m.artifact.path);
          out.push({ caseId: c.case_id, category: c.category, trace: t });
        }
        setRows(out);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const methods = Array.from(new Set(rows.flatMap((r) => r.trace.methods.map((m) => m.name))));
  const familyOf = (name: string) => rows.flatMap((r) => r.trace.methods).find((m) => m.name === name)?.family ?? '';
  methods.sort((a, b) => FAMILY_ORDER.indexOf(familyOf(a)) - FAMILY_ORDER.indexOf(familyOf(b)) || a.localeCompare(b));
  const maseOf = (ct: CaseTrace, name: string) => ct.trace.methods.find((m) => m.name === name)?.backtest.mase ?? null;
  const covOf = (ct: CaseTrace, name: string) => ct.trace.methods.find((m) => m.name === name)?.backtest.coverage ?? null;
  const msisOf = (ct: CaseTrace, name: string) => ct.trace.methods.find((m) => m.name === name)?.backtest.msis ?? null;
  const winnerOf = (ct: CaseTrace) => ct.trace.summary.best_method;

  const leaderboard = (
    <div className="cs-chart">
      <table className="cs-table">
        <thead>
          <tr>
            <th>{es ? 'método (familia)' : 'method (family)'}</th>
            {rows.map((r) => <th key={r.caseId} title={r.category}>{r.caseId.replace(/_/g, ' ')}</th>)}
          </tr>
        </thead>
        <tbody>
          {methods.map((name) => (
            <tr key={name}>
              <td>{name} <span className="cs-badge replay">{familyOf(name)}</span></td>
              {rows.map((r) => (
                <td key={r.caseId} style={winnerOf(r) === name ? { fontWeight: 700, color: 'var(--color-accent)' } : undefined}>
                  {fmt(maseOf(r, name))}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="cs-panel-sub">{es
        ? 'MASE por método x caso, del backtest de origen móvil sin fuga (menor es mejor; < 1 le gana al naive estacional). El ganador por caso en color. Construido en vivo desde los artefactos comprometidos.'
        : 'MASE per method x case, from the leakage-safe rolling-origin backtest (lower is better; < 1 beats the seasonal naive). The per-case winner is highlighted. Built live from the committed artifacts.'}</p>
    </div>
  );

  const families = (
    <div className="prose">
      <p>{es
        ? 'La lectura por familia confirma la tesis de no-hay-almuerzo-gratis del atlas:'
        : 'The per-family read confirms the atlas\'s no-free-lunch thesis:'}</p>
      <ul>
        <li>{es
          ? 'Los CLÁSICOS ganan o empatan en los casos de estacionalidad limpia y en los controles (donde ganar por mucho sería una bandera roja).'
          : 'CLASSICAL methods win or tie on the clean-seasonality cases and the controls (where winning big would be a red flag).'}</li>
        <li>{es
          ? 'Los ESTADÍSTICOS (AutoARIMA/ETS/Theta) son el punto de referencia robusto del nivel medio: rara vez los mejores, rara vez malos.'
          : 'STATISTICAL methods (AutoARIMA/ETS/Theta) are the robust mid-tier reference: rarely best, rarely bad.'}</li>
        <li>{es
          ? 'Los PROFUNDOS (NHITS en particular) lideran donde hay estructura no lineal o multi-escala que aprender (estacional + tendencia, multi-estacional, caos de corto plazo). Cada modelo profundo aparece dos veces (framework "(nf)" y implementación directa): su acuerdo es una auditoría integrada.'
          : 'DEEP methods (NHITS in particular) lead where there is nonlinear or multi-scale structure to learn (seasonal + trend, multi-seasonal, short-horizon chaos). Every deep model appears twice (framework "(nf)" and direct implementation): their agreement is a built-in audit.'}</li>
        <li>{es
          ? 'Los FUNDACIONALES (TimesFM-2.5, Chronos-2) son los generalistas: zero-shot, sin ajuste, competitivos en casi todo, y ganadores donde el contexto largo importa (intermitencia, memoria larga). Que un modelo sin entrenar en estos datos compita con modelos entrenados EN ellos es el resultado SOTA central.'
          : 'FOUNDATION models (TimesFM-2.5, Chronos-2) are the generalists: zero-shot, no fitting, competitive almost everywhere, and winners where long context matters (intermittency, long memory). That a model never trained on this data competes with models trained ON it is the central SOTA result.'}</li>
      </ul>
    </div>
  );

  const coverage = (
    <div className="cs-chart">
      <table className="cs-table">
        <thead>
          <tr>
            <th>{es ? 'método' : 'method'}</th>
            {rows.map((r) => <th key={r.caseId}>{r.caseId.replace(/_/g, ' ')}</th>)}
          </tr>
        </thead>
        <tbody>
          {methods.map((name) => (
            <tr key={name}>
              <td>{name}</td>
              {rows.map((r) => {
                const c = covOf(r, name);
                const off = c == null ? 0 : Math.abs(c - 0.8);
                const cls = c == null ? '' : off <= 0.07 ? 'ok' : off <= 0.15 ? 'warn' : 'bad';
                return <td key={r.caseId}><span className={`cs-badge ${cls}`}>{fmt(c)}</span></td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="cs-panel-sub">{es
        ? 'Cobertura empírica del intervalo 10/90 (nominal 0.80). Verde: dentro de ±0.07; ámbar: ±0.15; rojo: peor. Un punto excelente con cobertura rota sigue siendo un pronóstico defectuoso; la vista de streaming del App muestra cómo ACI/PID la reparan en línea.'
        : 'Empirical coverage of the 10/90 interval (nominal 0.80). Green: within ±0.07; amber: ±0.15; red: worse. An excellent point with broken coverage is still a defective forecast; the App\'s streaming view shows ACI/PID repairing it online.'}</p>
    </div>
  );

  const interval = (
    <div className="cs-chart">
      <table className="cs-table">
        <thead>
          <tr>
            <th>{es ? 'método' : 'method'}</th>
            {rows.map((r) => <th key={r.caseId}>{r.caseId.replace(/_/g, ' ')}</th>)}
          </tr>
        </thead>
        <tbody>
          {methods.map((name) => {
            const cells = rows.map((r) => msisOf(r, name));
            if (cells.every((v) => v == null)) return null; // pre-v2 traces carry no MSIS
            return (
              <tr key={name}>
                <td>{name}</td>
                {rows.map((r, i) => {
                  const v = cells[i];
                  const bestHere = Math.min(...methods.map((n) => msisOf(r, n) ?? Infinity));
                  const isBest = v != null && Number.isFinite(bestHere) && v <= bestHere + 1e-9;
                  return <td key={r.caseId} style={isBest ? { fontWeight: 700, color: 'var(--color-accent)' } : undefined}>{fmt(v, 2)}</td>;
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="cs-panel-sub">{es
        ? 'MSIS por método x caso (Gneiting y Raftery 2007; la métrica de intervalo de M4): ancho del intervalo 10/90 más 2/α por unidad de falla, escalado por el naive estacional. Menor es mejor; el mejor por caso en color. Complementa la vista de cobertura: cobertura perfecta con intervalos inflados paga aquí.'
        : 'MSIS per method x case (Gneiting & Raftery 2007; the M4 interval metric): the 10/90 interval width plus 2/α per unit of miss, scaled by the seasonal naive. Lower is better; the per-case best is highlighted. It complements the coverage view: perfect coverage with bloated intervals pays here.'}</p>
    </div>
  );

  const honesty = (
    <div className="prose">
      <Callout variant="honest" title={es ? 'Cómo leer esta tabla sin engañarse' : 'How to read this table without fooling yourself'}>
        <ul>
          <li>{es
            ? 'Controles primero: en RWLK y ruido blanco nadie debería ganar por mucho. Si un método muestra MASE mucho menor que 1 ahí, sospecha del harness (fuga), no celebres el método.'
            : 'Controls first: on RWLK and white noise nobody should win by much. If a method shows MASE far below 1 there, suspect the harness (leakage), do not celebrate the method.'}</li>
          <li>{es
            ? 'Presupuestos de ventanas: los métodos pesados se backtestean con menos ventanas (n_windows está en el manifiesto); sus MASE tienen más varianza.'
            : 'Window budgets: heavy methods are backtested on fewer windows (n_windows is in the manifest); their MASE has more variance.'}</li>
          <li>{es
            ? 'Fuga de pre-entrenamiento: los fundacionales pudieron ver series públicas parecidas a los casos reales. Los casos sintéticos (sembrados, imposibles de haber visto) son el contrapeso; que los fundacionales también compitan AHÍ es la señal fuerte.'
            : 'Pretraining leakage: foundation models may have seen public series resembling the real cases. The synthetic cases (seeded, impossible to have seen) are the counterweight; that foundation models also compete THERE is the strong signal.'}</li>
          <li>{es
            ? 'GARCH es a propósito: su tabla de puntos es aburrida; su valor está en la vista de cobertura y en el banco de streaming.'
            : 'GARCH is on purpose: its point table is boring; its value lives in the coverage view and the streaming bench.'}</li>
        </ul>
      </Callout>
    </div>
  );

  return (
    <section className="page-body prose">
      <h2>Benchmark</h2>
      <p className="cs-lead">{es
        ? 'Los resultados cruzados sobre los 12 casos, construidos EN VIVO desde los artefactos comprometidos (nunca tipeados a mano): 18 métodos, backtest de origen móvil, punto + cobertura.'
        : 'The cross-case results over the 12 cases, built LIVE from the committed artifacts (never hand-typed): 18 methods, rolling-origin backtest, point + coverage.'}</p>
      {err && <p style={{ color: 'var(--color-danger, #f85149)' }}>error: {err}</p>}
      {rows.length === 0 && !err && <p className="cs-panel-sub">{es ? 'cargando artefactos...' : 'loading artifacts...'}</p>}
      {rows.length > 0 && (
        <SubTabs
          ariaLabel="benchmark views"
          tabs={[
            { id: 'leaderboard', label: es ? 'Tabla (MASE)' : 'Leaderboard (MASE)', content: leaderboard },
            { id: 'families', label: es ? 'Por familia' : 'By family', content: families },
            { id: 'coverage', label: es ? 'Cobertura' : 'Coverage', content: coverage },
            { id: 'interval', label: es ? 'Intervalo (MSIS)' : 'Interval (MSIS)', content: interval },
            { id: 'honesty', label: es ? 'Notas de honestidad' : 'Honesty notes', content: honesty },
          ]}
        />
      )}
      <Refs ids={['mase', 'tfb', 'gifteval', 'fevbench']} label={es ? 'Referencias' : 'References'} />
    </section>
  );
}
