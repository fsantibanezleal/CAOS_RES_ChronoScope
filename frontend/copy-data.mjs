// Prebuild: copy the committed CONTRACT-2 artifacts (../data/derived) into the SPA's public/ so the static site
// replays them, and inline the chronoscopelab sources for the live (Pyodide) lane. Canonical copies live in ../data
// and ../data-pipeline, public/ is a build-time overlay (git-ignored).
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const PUB = join(HERE, 'public');

// Resolve the generated directory before letting the shared overlay rebuild it.
mkdirSync(PUB, { recursive: true });
const dataOverlay = join(PUB, 'data');
if (relative(realpathSync(HERE), realpathSync(PUB)) !== 'public' ||
    (existsSync(dataOverlay) && relative(realpathSync(PUB), realpathSync(dataOverlay)) !== 'data')) {
  throw new Error('Generated data cleanup must stay inside frontend/public/data');
}

// The base owns the data overlay. The product adds admitted research documents through its hook.
await import('./scripts/copy-data.mjs');

// The generated ONNX metadata is imported by the browser and also published beside the ONNX weights.
const modelMeta = join(HERE, 'src', 'lib', 'nlinearMeta.json');
if (existsSync(modelMeta)) {
  mkdirSync(join(PUB, 'models'), { recursive: true });
  cpSync(modelMeta, join(PUB, 'models', 'nlinear.json'));
  console.log('[copy-data] embedded NLinear metadata -> public/models/nlinear.json');
}
mkdirSync(join(PUB, 'models'), { recursive: true });
cpSync(join(HERE, 'src', 'lib', 'browserCalibration.json'), join(PUB, 'models', 'browser-calibration.json'));

// 2) inline the chronoscopelab Python sources for the optional Pyodide live lane -> public/pyodide/sources.json
const pkg = join(ROOT, 'data-pipeline', 'chronoscopelab');
if (existsSync(pkg)) {
  const sources = {};
  const walk = (dir, rel = '') => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.name === '__pycache__') continue;
      const abs = join(dir, e.name);
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) walk(abs, r);
      else if (e.name.endsWith('.py')) sources[`chronoscopelab/${r}`] = readFileSync(abs, 'utf-8');
    }
  };
  walk(pkg);
  mkdirSync(join(PUB, 'pyodide'), { recursive: true });
  writeFileSync(join(PUB, 'pyodide', 'sources.json'), JSON.stringify(sources));
  console.log(`[copy-data] inlined ${Object.keys(sources).length} chronoscopelab sources -> public/pyodide/sources.json`);
}

// 3) copy the onnxruntime-web WASM/loader assets -> public/ort so the ONNX live deep tier is self-hosted
//    (ort.env.wasm.wasmPaths points here; single-threaded so no COOP/COEP headers are needed on Pages).
//    Only the plain wasm backend files are fetched at runtime (the .jsep/.asyncify/.jspi variants are for
//    webgpu/alternative binding modes; the ort*.mjs bundles are the library itself, which vite bundles).
const ortDist = join(HERE, 'node_modules', 'onnxruntime-web', 'dist');
if (existsSync(ortDist)) {
  const outDir = join(PUB, 'ort');
  rmSync(outDir, { recursive: true, force: true });
  mkdirSync(outDir, { recursive: true });
  let n = 0;
  for (const f of ['ort-wasm-simd-threaded.wasm', 'ort-wasm-simd-threaded.mjs']) {
    if (existsSync(join(ortDist, f))) {
      cpSync(join(ortDist, f), join(outDir, f));
      n++;
    }
  }
  console.log(`[copy-data] copied ${n} onnxruntime-web assets -> public/ort`);
}
