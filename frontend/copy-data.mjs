// Prebuild: copy the committed CONTRACT-2 artifacts (../data/derived) into the SPA's public/ so the static site
// replays them. Live methods execute TypeScript and the self-hosted ONNX graph.
// Canonical copies stay in data/derived; public/ is a generated overlay.
import { cpSync, existsSync, mkdirSync, realpathSync, rmSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const PUB = join(HERE, 'public');

// Resolve the generated directory before letting the shared overlay rebuild it.
mkdirSync(PUB, { recursive: true });
const dataOverlay = join(PUB, 'data');
if (relative(realpathSync(HERE), realpathSync(PUB)) !== 'public' ||
    (existsSync(dataOverlay) && relative(realpathSync(PUB), realpathSync(dataOverlay)) !== 'data')) {
  throw new Error('Generated data cleanup must stay inside frontend/public/data');
}

// This release serves its admitted corpus. A machine's global raw-data setting
// must not redirect the public research overlay to another tree.
const canonical = join(HERE, '..', 'data', 'derived');
if (!existsSync(canonical)) throw new Error('Canonical data/derived is missing');
const previousDataRoot = process.env.CAOS_DATA_ROOT;
process.env.CAOS_DATA_ROOT = canonical;
try {
  // The base owns declared-file copying; the product hook adds admitted research.
  await import('./scripts/copy-data.mjs');
} finally {
  if (previousDataRoot === undefined) delete process.env.CAOS_DATA_ROOT;
  else process.env.CAOS_DATA_ROOT = previousDataRoot;
}

// The generated ONNX metadata is imported by the browser and also published beside the ONNX weights.
const modelMeta = join(HERE, 'src', 'lib', 'nlinearMeta.json');
if (existsSync(modelMeta)) {
  mkdirSync(join(PUB, 'models'), { recursive: true });
  cpSync(modelMeta, join(PUB, 'models', 'nlinear.json'));
  console.log('[copy-data] embedded NLinear metadata -> public/models/nlinear.json');
}
mkdirSync(join(PUB, 'models'), { recursive: true });
cpSync(join(HERE, 'src', 'lib', 'browserCalibration.json'), join(PUB, 'models', 'browser-calibration.json'));

// Copy onnxruntime-web WASM/loader assets -> public/ort for self-hosted inference.
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
