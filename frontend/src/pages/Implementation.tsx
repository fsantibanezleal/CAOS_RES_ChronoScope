import { Callout, Equation, Refs, useShellLang } from '@fasl-work/caos-app-shell';

// Implementation: the ADR-0057 architecture (three lanes, two contracts, determinism, the GPU lane, the
// license guard, the parity discipline), with the stage map and the license-guard flow as themed SVGs.
// Transcribed from docs/architecture + the persisted decisions; equations validated against the code.
export default function Implementation() {
  const es = useShellLang() === 'es';
  return (
    <section className="page-body prose">
      <h2>{es ? 'Implementación' : 'Implementation'}</h2>
      <p className="cs-lead">{es
        ? 'ChronoScope es un producto de pipeline-offline-pesado con replay determinista y estático: el procesamiento duro (entrenar la escalera profunda en GPU, correr los fundacionales, las diez familias de análisis, el banco de streaming) ocurre offline y se hornea en artefactos compactos versionados; esta web los reproduce, y el nivel clásico + un modelo profundo pequeño corren EN VIVO en tu navegador.'
        : 'ChronoScope is an offline-pipeline-heavy, static, deterministic-replay product: the hard processing (training the deep ladder on GPU, running the foundation models, the ten analysis families, the streaming bench) happens offline and is baked into compact versioned artifacts; this web replays them, and the classical tier + a small deep model run LIVE in your browser.'}</p>

      <svg viewBox="0 0 680 150" width="100%" style={{ maxWidth: 680, display: 'block', margin: '0.8rem auto', font: '11px var(--font-sans, sans-serif)' }} role="img" aria-label="the three lanes">
        <rect x="6" y="10" width="200" height="60" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" /><text x="106" y="30" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'OFFLINE (GPU, py3.12)' : 'OFFLINE (GPU, py3.12)'}</text><text x="106" y="44" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">statsforecast · LightGBM · torch</text><text x="106" y="57" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">neuralforecast · Chronos · TimesFM</text>
        <rect x="6" y="80" width="200" height="60" rx="6" fill="var(--color-surface)" stroke="var(--color-border)" /><text x="106" y="100" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'contratos de datos' : 'data contracts'}</text><text x="106" y="114" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? 'C1: ingesta + licencia' : 'C1: ingestion + license'}</text><text x="106" y="127" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? 'C2: artefacto (espejo TS)' : 'C2: artifact (TS mirror)'}</text>
        <line x1="206" y1="75" x2="250" y2="75" stroke="var(--color-fg-subtle)" />
        <rect x="250" y="45" width="180" height="60" rx="6" fill="var(--color-surface)" stroke="var(--color-border)" /><text x="340" y="66" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'artefactos precalculados' : 'baked artifacts'}</text><text x="340" y="80" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">trace · analysis · streaming</text><text x="340" y="93" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? '(por caso, semilla 42)' : '(per case, seed 42)'}</text>
        <line x1="430" y1="75" x2="474" y2="75" stroke="var(--color-fg-subtle)" />
        <rect x="474" y="10" width="200" height="60" rx="6" fill="var(--color-surface)" stroke="#3fb950" /><text x="574" y="30" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'WEB: REPLAY' : 'WEB: REPLAY'}</text><text x="574" y="44" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? 'escalera completa + análisis' : 'full ladder + analysis'}</text><text x="574" y="57" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? '+ banco de streaming' : '+ streaming bench'}</text>
        <rect x="474" y="80" width="200" height="60" rx="6" fill="var(--color-surface)" stroke="#3fb950" /><text x="574" y="100" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'WEB: EN VIVO' : 'WEB: LIVE'}</text><text x="574" y="114" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">{es ? 'clásicos en TS (paridad)' : 'classical in TS (parity)'}</text><text x="574" y="127" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">NLinear ONNX (onnxruntime-web)</text>
      </svg>

      <h3>{es ? 'Los tres carriles' : 'The three lanes'}</h3>
      <p>{es
        ? 'OFFLINE: el pipeline por etapas (preprocess, analyze, feature_extraction, train, infer, evaluate + streaming, export) corre en Python 3.12 con la GPU (torch cu126) y hornea, por caso: la traza de pronósticos (19 métodos con backtest), el panel de análisis (10 familias) y el banco de streaming (trayectorias prequential). REPLAY: la web lee esos artefactos; nada pesado corre aquí. EN VIVO: la escalera clásica está portada a TypeScript y verificada por PARIDAD contra el núcleo Python sobre un fixture comprometido (el navegador computa lo mismo que el pipeline, no una aproximación decorativa), y un NLinear exportado a ONNX corre con onnxruntime-web.'
        : 'OFFLINE: the staged pipeline (preprocess, analyze, feature_extraction, train, infer, evaluate + streaming, export) runs on Python 3.12 with the GPU (torch cu126) and bakes, per case: the forecast trace (19 backtested methods), the analysis panel (10 families) and the streaming bench (prequential trajectories). REPLAY: the web reads those artifacts; nothing heavy runs here. LIVE: the classical ladder is ported to TypeScript and PARITY-checked against the Python core on a committed fixture (the browser computes the same thing the pipeline does, not a decorative approximation), and an ONNX-exported NLinear runs via onnxruntime-web.'}</p>

      <svg viewBox="0 0 680 130" width="100%" style={{ maxWidth: 680, display: 'block', margin: '0.8rem auto', font: '10px var(--font-sans, sans-serif)' }} role="img" aria-label={es ? 'las etapas del pipeline y los artefactos que emite' : 'the pipeline stages and the artifacts they emit'}>
        {(es
          ? [['preprocess', 'contrato 1'], ['analyze', '10 familias'], ['features', 'rezagos+cal'], ['train', 'GPU, semilla'], ['infer', 'escalera'], ['evaluate', 'preqts'], ['streaming', 'ACI/PID'], ['export', 'guardián lic.']]
          : [['preprocess', 'contract 1'], ['analyze', '10 families'], ['features', 'lags+cal'], ['train', 'GPU, seeded'], ['infer', 'ladder'], ['evaluate', 'preqts'], ['streaming', 'ACI/PID'], ['export', 'license guard']]
        ).map(([name, sub], i) => (
          <g key={name}>
            <rect x={6 + i * 84} y={26} width={76} height={40} rx={6} fill="var(--color-surface)" stroke={i === 7 ? '#3fb950' : 'var(--color-accent)'} />
            <text x={44 + i * 84} y={43} textAnchor="middle" fill="var(--color-fg)" fontSize="9.5">{name}</text>
            <text x={44 + i * 84} y={57} textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="8.5">{sub}</text>
            {i < 7 && <line x1={82 + i * 84} y1={46} x2={90 + i * 84} y2={46} stroke="var(--color-fg-subtle)" />}
          </g>
        ))}
        <text x="6" y="14" fill="var(--color-fg)" fontSize="10">{es ? 'una corrida = una función pura de (caso, semilla); cada etapa es tipada, sembrada y testeada' : 'one run = a pure function of (case, seed); every stage is typed, seeded, and tested'}</text>
        <text x="6" y="90" fill="var(--color-fg-faint)" fontSize="9">{es ? 'emite por caso: trace.json (19 métodos + backtest) · analysis.json (veredictos + catch22) · streaming.json (trayectorias) · manifest (bytes + gate + procedencia)' : 'emits per case: trace.json (19 methods + backtest) · analysis.json (verdicts + catch22) · streaming.json (trajectories) · manifest (bytes + gate + provenance)'}</text>
        <text x="6" y="106" fill="var(--color-fg-faint)" fontSize="9">{es ? 'los carriles pesados son opt-in por bandera: CHRONOSCOPE_ENABLE_NEURAL / _FOUNDATION / _NEURALFORECAST / _TIREX_WSL' : 'heavy lanes are opt-in by flag: CHRONOSCOPE_ENABLE_NEURAL / _FOUNDATION / _NEURALFORECAST / _TIREX_WSL'}</text>
      </svg>

      <h3>{es ? 'Determinismo y procedencia' : 'Determinism and provenance'}</h3>
      <p>{es
        ? 'Cada precalculado es una función pura de (caso, semilla): generadores sembrados vía hashlib (no el hash() salteado de Python), entrenamiento profundo sembrado, sin timestamps en los artefactos (re-hornear no ensucia git). El manifiesto por caso registra el veredicto del gate en-vivo/replay (medido sobre el camino clásico del navegador, no sobre los motores pesados), los bytes del artefacto y el bloque de procedencia de la fuente.'
        : 'Every bake is a pure function of (case, seed): generators seeded via hashlib (not Python\'s salted hash()), seeded deep training, no timestamps in artifacts (re-baking does not dirty git). The per-case manifest records the live/replay gate verdict (measured on the browser classical path, not the heavy engines), the artifact bytes, and the source provenance block.'}</p>
      <Equation tex={String.raw`\text{artifact}(c) \;=\; \text{Pipeline}\big(c,\ s\big), \qquad \text{rng}_c = \text{PCG64}\big(\text{SHA-1}(c)[{:}4] \oplus s\big)`} caption={es
        ? 'El contrato de determinismo: mismo caso c y semilla s (42 canónica) = mismos bytes. Cada caso deriva su stream aleatorio propio del SHA-1 de su id, de modo que los casos son independientes y reproducibles proceso a proceso.'
        : 'The determinism contract: same case c and seed s (canonical 42) = the same bytes. Each case derives its own random stream from the SHA-1 of its id, so cases are independent and reproducible process to process.'} />
      <p>{es
        ? 'La paridad TS-Python no es una frase: el fixture comprometido (generado por el pipeline) se re-computa en el navegador y los tests exigen coincidencia del punto a 0.01, de sigma a 0.001 y de la ppf normal a 0.0001. Si el motor vivo diverge del núcleo Python, el build falla.'
        : 'TS-Python parity is not a phrase: the committed fixture (generated by the pipeline) is recomputed in the browser and the tests demand the point match to 0.01, sigma to 0.001, and the normal ppf to 0.0001. If the live engine diverges from the Python core, the build fails.'}</p>

      <h3>{es ? 'El guardián de licencias' : 'The license guard'}</h3>
      <p>{es
        ? 'El Contrato 1 registra la fuente y su licencia por caso; el export APLICA el veredicto: una fuente cuya licencia prohíbe redistribución pública publica SOLO métricas agregadas (la traza omite la serie y los caminos por paso; el panel de análisis descarta los arreglos derivados de la serie y conserva los veredictos escalares). Los casos UCI (CC-BY) publican todo con atribución.'
        : 'Contract 1 records each case\'s source and license; the export ENFORCES the verdict: a source whose license forbids public redistribution ships ONLY aggregate metrics (the trace omits the series and per-step paths; the analysis panel drops series-derived arrays, keeps scalar verdicts). The UCI cases (CC-BY) ship everything with attribution.'}</p>

      <svg viewBox="0 0 680 150" width="100%" style={{ maxWidth: 680, display: 'block', margin: '0.8rem auto', font: '10px var(--font-sans, sans-serif)' }} role="img" aria-label={es ? 'el flujo del guardián de licencias' : 'the license-guard flow'}>
        <rect x="6" y="52" width="150" height="46" rx="6" fill="var(--color-surface)" stroke="var(--color-border)" />
        <text x="81" y="71" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'fuente del caso' : 'case source'}</text>
        <text x="81" y="86" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">DataSource(license, ...)</text>
        <line x1="156" y1="75" x2="200" y2="75" stroke="var(--color-fg-subtle)" />
        <rect x="200" y="42" width="190" height="66" rx="6" fill="var(--color-surface)" stroke="var(--color-accent)" />
        <text x="295" y="64" textAnchor="middle" fill="var(--color-fg)" fontSize="10">{es ? 'veredicto verificado' : 'verified verdict'}</text>
        <text x="295" y="80" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="9">public_artifact_ok?</text>
        <text x="295" y="94" textAnchor="middle" fill="var(--color-fg-faint)" fontSize="8.5">{es ? '(dossier de licencias; jamás inventado)' : '(license dossier; never invented)'}</text>
        <line x1="390" y1="60" x2="450" y2="34" stroke="#3fb950" />
        <rect x="450" y="10" width="224" height="46" rx="6" fill="var(--color-surface)" stroke="#3fb950" />
        <text x="562" y="29" textAnchor="middle" fill="var(--color-fg)" fontSize="9.5">{es ? 'CC-BY / propio: TODO se publica' : 'CC-BY / own: EVERYTHING ships'}</text>
        <text x="562" y="44" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="8.5">{es ? 'serie + caminos + análisis, con atribución' : 'series + paths + analysis, attributed'}</text>
        <line x1="390" y1="92" x2="450" y2="116" stroke="#d29922" />
        <rect x="450" y="94" width="224" height="46" rx="6" fill="var(--color-surface)" stroke="#d29922" />
        <text x="562" y="113" textAnchor="middle" fill="var(--color-fg)" fontSize="9.5">{es ? 'solo-local: SOLO agregados' : 'local-only: aggregates ONLY'}</text>
        <text x="562" y="128" textAnchor="middle" fill="var(--color-fg-subtle)" fontSize="8.5">{es ? 'sin serie, sin caminos por paso; veredictos escalares' : 'no series, no per-step paths; scalar verdicts'}</text>
      </svg>

      <h3>{es ? 'El carril GPU y las decisiones de entorno' : 'The GPU lane and the environment decisions'}</h3>
      <p>{es
        ? 'La caja de precalculado es una RTX 4070 Laptop (8.5 GB, torch 2.12.1+cu126). Dos decisiones de ingeniería quedaron registradas con su evidencia: (1) la base Python se migró a 3.12 porque ray (dependencia dura de neuralforecast) publica wheels de Windows solo hasta cp312, lo que hace instalable el framework real; (2) cada modelo profundo se hornea DOS veces, el framework canónico y una implementación directa contra el paper, de modo que ambas se auditan mutuamente.'
        : 'The bake box is an RTX 4070 Laptop (8.5 GB, torch 2.12.1+cu126). Two engineering decisions are on record with their evidence: (1) the Python base moved to 3.12 because ray (neuralforecast\'s hard dependency) ships Windows wheels only up to cp312, which makes the real framework installable; (2) every deep model is baked TWICE, the canonical framework and a direct-against-the-paper implementation, so the two audit each other.'}</p>

      <Callout variant="note" title={es ? 'Reproducibilidad' : 'Reproducibility'}>
        {es
          ? 'Todo es reproducible desde el repo: requirements fijados por carril (vivo = solo numpy; precompute = el stack completo), el pipeline se invoca con una semilla, y los artefactos comprometidos coinciden byte a byte al re-hornear. preqts, el paquete de evaluación streaming extraído de este trabajo, está publicado en PyPI (pip install preqts).'
          : 'Everything is reproducible from the repo: per-lane pinned requirements (live = numpy only; precompute = the full stack), the pipeline is invoked with a seed, and the committed artifacts match byte-for-byte on re-bake. preqts, the streaming-evaluation package extracted from this work, is published on PyPI (pip install preqts).'}
      </Callout>

      <Refs ids={['prequential', 'mase', 'uci-electricity']} label={es ? 'Referencias' : 'References'} />
    </section>
  );
}
