// Prebuild: copy the committed CONTRACT-2 artifacts (../data/derived) into the SPA's public/ so the static site
// replays them, and inline the chronoscopelab sources for the live (Pyodide) lane. Canonical copies live in ../data
// and ../data-pipeline — public/ is a build-time overlay (git-ignored).
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const PUB = join(HERE, 'public');

// 1) data/derived -> public/data (traces under <case>/trace.json + manifests/ subdir incl. index.json)
const derived = join(ROOT, 'data', 'derived');
if (existsSync(derived)) {
  mkdirSync(join(PUB, 'data'), { recursive: true });
  cpSync(derived, join(PUB, 'data'), { recursive: true });
  console.log('[copy-data] data/derived -> public/data');
} else {
  console.warn('[copy-data] no data/derived — run scripts/precompute first');
}

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
