// The ONNX live deep tier: run the NLinear model (a one-layer LTSF-linear, trained offline by least squares
// and exported to a 2 KB ONNX) in the browser with onnxruntime-web. This is a genuinely LEARNED method
// running LIVE client-side, next to the classical live tier and the replayed heavy tiers.
//
// Single-threaded WASM (numThreads=1) so no COOP/COEP cross-origin-isolation headers are needed on GitHub
// Pages; assets are self-hosted under <base>/ort (copied by copy-data.mjs). Everything degrades gracefully:
// if the model or runtime fails to load, the method simply does not appear.
import * as ort from 'onnxruntime-web';

const BASE = import.meta.env.BASE_URL;

ort.env.wasm.wasmPaths = `${BASE}ort/`;
ort.env.wasm.numThreads = 1;

export interface NLinearMeta {
  name: string;
  lookback: number;
  horizon: number;
  sigma_norm: number;
}

let metaPromise: Promise<NLinearMeta> | null = null;
let sessionPromise: Promise<ort.InferenceSession> | null = null;

export function loadNLinearMeta(): Promise<NLinearMeta> {
  if (!metaPromise) {
    metaPromise = fetch(`${BASE}models/nlinear.json`).then((r) => {
      if (!r.ok) throw new Error(`nlinear.json ${r.status}`);
      return r.json() as Promise<NLinearMeta>;
    });
  }
  return metaPromise;
}

function getSession(): Promise<ort.InferenceSession> {
  if (!sessionPromise) {
    sessionPromise = ort.InferenceSession.create(`${BASE}models/nlinear.onnx`);
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
  if (series.length < meta.lookback) throw new Error('series shorter than the model lookback');
  const window = series.slice(series.length - meta.lookback);
  const last = window[window.length - 1];
  const s = std(window) || 1;
  const xn = Float32Array.from(window.map((v) => (v - last) / s));

  const sess = await getSession();
  const input = new ort.Tensor('float32', xn, [1, meta.lookback]);
  const out = await sess.run({ x: input });
  const yn = Array.from(out.y.data as Float32Array);
  return { point: yn.map((v) => v * s + last), scale: s };
}
