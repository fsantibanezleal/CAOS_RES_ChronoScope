// Instance-normalized global least-squares map, exported to ONNX for browser inference.
// This is distinct from the per-prefix NLinear neural fits in the offline study.
//
// Single-threaded WASM (numThreads=1) so no COOP/COEP cross-origin-isolation headers are needed on GitHub
// Pages; assets are self-hosted under <base>/ort (copied by copy-data.mjs). Everything degrades gracefully:
// if the model or runtime fails to load, the method simply does not appear.
// The /wasm subpath pins the plain wasm backend (the default bundle asks for the JSEP/webgpu loader,
// which copy-data.mjs deliberately does not ship).
import * as ort from 'onnxruntime-web/wasm';
import modelMeta from './nlinearMeta.json';
import { BROWSER_CALIBRATION } from './calibratedLinearIntervals';

const BASE = import.meta.env.BASE_URL;

// Must be a fully qualified URL: ort resolves bare/relative prefixes against its own bundled chunk
// (/assets/...), not the site root.
ort.env.wasm.wasmPaths = new URL(`${BASE}ort/`, globalThis.location?.href ?? 'http://localhost/').href;
ort.env.wasm.numThreads = 1;

export type NLinearMeta = import('./contract.gen').components['schemas']['NLinearMetadata'];

let sessionPromise: Promise<ort.InferenceSession> | null = null;

// The metadata is tiny and changes only with a model bake. Import the canonical generated
// JSON into the bundle so the first inference does not depend on an extra request racing page teardown.
const NLINEAR_META = modelMeta as NLinearMeta;
export const loadNLinearMeta = (): Promise<NLinearMeta> => Promise.resolve(NLINEAR_META);

function getSession(): Promise<ort.InferenceSession> {
  if (!sessionPromise) {
    sessionPromise = (async () => {
      const response = await fetch(`${BASE}models/nlinear.onnx`);
      if (!response.ok) throw new Error(`Browser model request failed: ${response.status}`);
      const bytes = await response.arrayBuffer();
      const digest = await crypto.subtle.digest('SHA-256', bytes);
      const actual = Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, '0')).join('');
      if (actual !== BROWSER_CALIBRATION.point_model_sha256) throw new Error('Browser model differs from its calibration');
      return ort.InferenceSession.create(new Uint8Array(bytes));
    })().catch(error => { sessionPromise = null; throw error; });
  }
  return sessionPromise;
}

function std(a: number[]): number {
  const m = a.reduce((s, v) => s + v, 0) / a.length;
  return Math.sqrt(a.reduce((s, v) => s + (v - m) * (v - m), 0) / a.length);
}

/** Point forecast (length = meta.horizon) for the given series, or throws if the series is too short. */
export async function runNLinear(series: number[]): Promise<{ point: number[]; scale: number }> {
  const meta = await loadNLinearMeta();
  if (series.length < meta.lookback || !series.every(Number.isFinite)) throw new Error('Invalid finite model lookback');
  const window = series.slice(series.length - meta.lookback);
  const last = window[window.length - 1];
  const s = std(window);
  if (!Number.isFinite(s) || s <= 0) throw new Error('Unavailable observed model scale');
  const xn = Float32Array.from(window.map((v) => (v - last) / s));

  const sess = await getSession();
  const input = new ort.Tensor('float32', xn, [1, meta.lookback]);
  const out = await sess.run({ x: input });
  if (!out.y || out.y.type !== 'float32' || out.y.dims.length !== 2 || out.y.dims[0] !== 1 || out.y.dims[1] !== meta.horizon) {
    throw new Error('Unexpected browser model output shape or type');
  }
  const yn = Array.from(out.y.data as Float32Array);
  const point = yn.map((v) => v * s + last);
  if (yn.length !== meta.horizon || !point.every(Number.isFinite)) throw new Error('Invalid browser model output');
  return { point, scale: s };
}
