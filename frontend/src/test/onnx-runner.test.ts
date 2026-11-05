import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { BROWSER_CALIBRATION } from '../lib/calibratedLinearIntervals';

const mocks = vi.hoisted(() => ({ create: vi.fn(), run: vi.fn() }));
vi.mock('onnxruntime-web/wasm', () => ({
  env: { wasm: {} },
  InferenceSession: { create: mocks.create },
  Tensor: class { data: Float32Array; constructor(_type: string, data: Float32Array) { this.data = data; } },
}));
beforeEach(() => {
  vi.resetModules(); vi.resetAllMocks();
  const digest = Uint8Array.from(BROWSER_CALIBRATION.point_model_sha256.match(/../g)!, value => parseInt(value, 16));
  vi.stubGlobal('crypto', { subtle: { digest: vi.fn().mockResolvedValue(digest.buffer) } });
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, arrayBuffer: async () => new ArrayBuffer(1) }));
  mocks.create.mockResolvedValue({ run: mocks.run });
  mocks.run.mockImplementation(async ({ x }) => ({ y: { type: 'float32', dims: [1, 12], data: new Float32Array(12).fill(x.data[0]) } }));
});
afterEach(() => vi.unstubAllGlobals());

it('adversarial: constant and nonfinite prefixes refuse inference without a raw-unit scale fallback', async () => {
  const { runNLinear } = await import('../lib/onnxRunner');
  await expect(runNLinear(Array(48).fill(5))).rejects.toThrow('scale');
  await expect(runNLinear([...Array(47).fill(5), NaN])).rejects.toThrow('finite');
  expect(mocks.create).not.toHaveBeenCalled();
});

it('adversarial: an ONNX graph with the wrong digest cannot use this calibration', async () => {
  vi.stubGlobal('crypto', { subtle: { digest: vi.fn().mockResolvedValue(new ArrayBuffer(32)) } });
  const { runNLinear } = await import('../lib/onnxRunner');
  await expect(runNLinear(Array.from({ length: 48 }, (_, i) => i))).rejects.toThrow('differs from its calibration');
  expect(mocks.create).not.toHaveBeenCalled();
});

it('adversarial: observed-unit transformation preserves the normalized model computation', async () => {
  const { runNLinear } = await import('../lib/onnxRunner');
  const history = Array.from({ length: 48 }, (_, i) => Math.sin(i) + i);
  const first = await runNLinear(history);
  const converted = await runNLinear(history.map(value => value * 1000 + 273.15));
  for (let i = 0; i < 12; i++) expect(converted.point[i]).toBeCloseTo(first.point[i] * 1000 + 273.15, 7);
  expect(converted.scale).toBeCloseTo(first.scale * 1000, 8);
});

it('adversarial: an incorrectly shaped model output cannot appear as a forecast', async () => {
  mocks.run.mockResolvedValue({ y: { type: 'float32', dims: [1, 11], data: new Float32Array(11) } });
  const { runNLinear } = await import('../lib/onnxRunner');
  await expect(runNLinear(Array.from({ length: 48 }, (_, i) => i))).rejects.toThrow('shape');
});
