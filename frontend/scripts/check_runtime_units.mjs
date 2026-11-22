// Real Chromium/Vite/WASM observable-unit audit. No mocked forecasts or exported UI test hooks.
// Usage: node scripts/check_runtime_units.mjs --out <external receipt.json> [--temp-root <external directory>]
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { chromium } from 'playwright';

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.dirname(frontend);
const args = process.argv.slice(2);
const option = name => {
  const index = args.indexOf(name);
  return index < 0 ? undefined : args[index + 1];
};
const namedOutput = option('--out');
const namedTemp = option('--temp-root') || process.env.CAOS_TEMP_ROOT;
assert.ok(namedOutput && namedTemp, '--out and --temp-root (or CAOS_TEMP_ROOT) must identify external destinations');
const output = path.resolve(namedOutput);
const tempRoot = path.resolve(namedTemp);
const outsideProduct = target => {
  const relative = path.relative(root, target);
  return relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative);
};
assert.ok(outsideProduct(output) && outsideProduct(tempRoot), 'Audit scratch and output must remain outside the product repository');
await fs.mkdir(tempRoot, { recursive: true });
await fs.mkdir(path.dirname(output), { recursive: true });
const scratch = await fs.mkdtemp(path.join(tempRoot, 'browser-runtime-units-'));
// Keep this process's own Chromium/Vite temporary data in the declared external root.
process.env.TEMP = scratch;
process.env.TMP = scratch;
process.env.TMPDIR = scratch;
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const canonicalHash = (name, bytes) => hash(/\.(?:ts|mjs|json)$/.test(name)
  ? Buffer.from(bytes.toString('utf8').replace(/\r\n/g, '\n')) : bytes);
const sourceNames = [
  'frontend/src/lib/liveEngine.ts', 'frontend/src/lib/onnxRunner.ts',
  'frontend/src/lib/calibratedLinearIntervals.ts', 'frontend/src/lib/nlinearMeta.json',
  'frontend/src/lib/browserCalibration.json', 'frontend/public/models/nlinear.onnx',
  'frontend/public/ort/ort-wasm-simd-threaded.mjs', 'frontend/public/ort/ort-wasm-simd-threaded.wasm',
  'frontend/scripts/check_runtime_units.mjs', 'frontend/package-lock.json',
  'data/derived/reevaluation.json',
];
const sourceBytes = Object.fromEntries(await Promise.all(sourceNames.map(async name => [name, await fs.readFile(path.join(root, name))])));
const sourceHashes = Object.fromEntries(sourceNames.map(name => [name, canonicalHash(name, sourceBytes[name])]));
const observedHashes = Object.fromEntries(sourceNames.map(name => [name, hash(sourceBytes[name])]));
const runtimePackages = Object.fromEntries(await Promise.all(['vite', 'playwright', 'onnxruntime-web'].map(async name =>
  [name, JSON.parse(await fs.readFile(path.join(frontend, 'node_modules', name, 'package.json'), 'utf8')).version])));
const source = JSON.parse(await fs.readFile(path.join(root, 'data/derived/reevaluation.json'), 'utf8'));
assert.equal(source.cases.length, 15, 'The complete selected-case source must have fifteen cases');
const cases = source.cases.map(row => {
  assert.ok(row.history.length >= 48 && row.actual.length >= 12 && row.history.every(Number.isFinite));
  return { id: row.case_id, history: row.history, target: row.actual.slice(0, 12), seasonality: row.seasonality,
    originalHorizon: row.horizon, input_sha256: hash(JSON.stringify([row.history, row.actual.slice(0, 12)])) };
});
const receipt = {
  schema: 'chronoscope.browser-runtime-units/v1', checked_utc: new Date().toISOString(), state: 'running',
  runtime_packages: runtimePackages,
  source_sha256: sourceHashes, source_observed_bytes_sha256: observedHashes,
  source_hash_policy: 'UTF-8 ts/mjs/json source canonicalized CRLF to LF for Git portability; ONNX/WASM binary hashes remain exact. Observed-byte hashes separately bind the actual execution files.',
  input_digest_encoding: 'ECMAScript JSON of [full contiguous history, first twelve reserved targets]',
  protocol: {
    horizon: 12, levels: [0.1, 0.5, 0.9], unit_factors: [1, 1e-9, 1e9],
    offsets: 'zero and two observed-prefix ranges multiplied by the same unit factor; no held-out target chooses the offset',
    original_history: 'Full contiguous reevaluation prefixes; never display-decimated trace arrays',
    observable_check: 'Point path must overlap [observed min-range, observed max+range]; interval endpoints may extend outside it',
    classic_normalized_tolerance: 5e-10, onnx_normalized_tolerance: 128 * 2 ** -23,
    tolerance_basis: 'Binary64 classical arithmetic budget;128 binary32 epsilon for the actual normalized ONNX path. Errors are divided by observed prefix standard deviation, never an absolute U tolerance.',
    flat_path_advisory: 'Path spread at most1e-6 of observed range; valid SES/flat predictions are not blockers',
  },
  scientific_boundary: [
    'This checks observable consistency and positive-affine transformation behavior, not forecast accuracy or ranking.',
    'Held-out targets enter only the post-prediction loose observable-range diagnostic, never fitting or normalization.',
    'Classical Gaussian intervals retain their residual-sigma times sqrt(lead) assumption; this audit does not establish its probabilistic validity.',
    'ONNX intervals are per-lead marginal residual bands calibrated on a declared synthetic population; real-series unit consistency does not establish real-data coverage.',
  ],
  blockers: [], advisories: [], cases: [], constant_inputs: [], model_hash_rejection: null,
};
const servers = [];
const contexts = [];

async function serve(publicDir, label) {
  const server = await createServer({
    configFile: false, root: frontend, base: '/', publicDir,
    cacheDir: path.join(scratch, `vite-${label}`),
    server: { host: '127.0.0.1', port: 0, strictPort: true },
    logLevel: 'error',
    plugins: [{ name: 'private-runtime-audit-document', configureServer(vite) {
      vite.middlewares.use((request, response, next) => {
        if (request.url !== '/__runtime_units__') return next();
        response.setHeader('Content-Type', 'text/html; charset=utf-8');
        response.end('<!doctype html><html><head><meta charset="utf-8"></head><body>Private numerical audit document</body></html>');
      });
    } }],
  });
  servers.push(server);
  await server.listen();
  const address = server.httpServer.address();
  assert.ok(address && typeof address !== 'string');
  return `http://127.0.0.1:${address.port}`;
}

async function pageAt(origin, label) {
  const context = await chromium.launchPersistentContext(path.join(scratch, `chromium-${label}`), {
    headless: true, args: ['--no-proxy-server'], viewport: { width: 1280, height: 800 },
    downloadsPath: path.join(scratch, `downloads-${label}`), tracesDir: path.join(scratch, `traces-${label}`),
  });
  contexts.push(context);
  receipt.browser = { name: 'Chromium', version: context.browser().version(), headless: true, backend: 'actual onnxruntime-web single-thread WASM' };
  const page = await context.newPage();
  await page.goto(`${origin}/__runtime_units__`, { waitUntil: 'domcontentloaded' });
  return page;
}

try {
  const origin = await serve(path.join(frontend, 'public'), 'actual');
  const page = await pageAt(origin, 'actual');
  const requests = [];
  page.on('request', request => { if (/\/models\/nlinear\.onnx|\.wasm(?:\?|$)/.test(request.url())) requests.push(new URL(request.url()).pathname); });
  receipt.constant_inputs = await page.evaluate(async () => {
    const { runNLinear } = await import('/src/lib/onnxRunner.ts');
    const rows = [];
    for (const level of [0.1, 1e-14, 1e12]) {
      let error = null;
      try { await runNLinear(Array(48).fill(level)); } catch (failure) { error = failure.message; }
      rows.push({ level, rejected: error?.includes('scale') === true, reason: error });
    }
    return rows;
  });
  assert.ok(receipt.constant_inputs.every(row => row.rejected), 'Every exact constant must be refused');
  assert.deepEqual(requests, [], 'Exact constants must be refused before requesting a model or WASM graph');
  const result = await page.evaluate(async inputCases => {
    const { forecastAllLive } = await import('/src/lib/liveEngine.ts');
    const { runNLinear } = await import('/src/lib/onnxRunner.ts');
    const { calibratedLinearIntervals, BROWSER_LINEAR_NAME } = await import('/src/lib/calibratedLinearIntervals.ts');
    const results = [], blockers = [], advisories = [];
    const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length;
    const span = values => Math.max(...values) - Math.min(...values);
    for (const item of inputCases) {
      const center = mean(item.history);
      const scale = Math.sqrt(mean(item.history.map(value => (value - center) ** 2)));
      if (!(scale > 0 && Number.isFinite(scale))) throw new Error(`Unavailable source scale: ${item.id}`);
      const prefixRange = span(item.history);
      let reference = null, referenceGroup = null;
      const contexts = [];
      for (const factor of [1, 1e-9, 1e9]) {
        for (const shifted of [false, true]) {
          const offset = shifted ? 2 * prefixRange * factor : 0;
          const history = item.history.map(value => value * factor + offset);
          const before = JSON.stringify(history);
          const methods = forecastAllLive(history, item.seasonality, 12, [0.1, 0.5, 0.9]);
          const graph = await runNLinear(history);
          const calibrated = calibratedLinearIntervals(history, graph.point, graph.scale);
          methods.push({ name: BROWSER_LINEAR_NAME, family: 'actual WASM graph', point: graph.point,
            lower: calibrated.lower, upper: calibrated.upper });
          if (before !== JSON.stringify(history)) blockers.push({ case: item.id, factor, offset, reason: 'Input history mutated' });
          if (!reference) { reference = methods; referenceGroup = calibrated.group; }
          if (calibrated.group !== referenceGroup) blockers.push({ case: item.id, factor, offset, reason: 'Prefix calibration group changed under unit conversion' });
          const target = item.target.map(value => value * factor + offset);
          const observed = [...history, ...target], range = span(observed);
          const lowerBound = Math.min(...observed) - range, upperBound = Math.max(...observed) + range;
          const rows = [];
          for (const method of methods) {
            const all = [...method.point, ...method.lower, ...method.upper];
            const valid = ['point', 'lower', 'upper'].every(key => method[key].length === 12) && all.every(Number.isFinite)
              && method.point.every((point, index) => method.lower[index] <= point && point <= method.upper[index]);
            if (!valid) blockers.push({ case: item.id, method: method.name, factor, offset, reason: 'Nonfinite, unordered or wrong-length path' });
            const pointMin = Math.min(...method.point), pointMax = Math.max(...method.point);
            if (pointMax < lowerBound || pointMin > upperBound) blockers.push({ case: item.id, method: method.name, factor, offset, reason: 'Point path wholly outside widened observable' });
            const flat = range > 0 && pointMax - pointMin <= 1e-6 * range;
            if (flat) advisories.push({ case: item.id, method: method.name, factor, shifted, reason: 'Valid constant/near-constant point path' });
            const base = reference.find(row => row.name === method.name);
            const error = Math.max(...['point', 'lower', 'upper'].flatMap(key => method[key].map((value, index) =>
              Math.abs((value - offset) / factor - base[key][index]) / scale)));
            const tolerance = method.family === 'actual WASM graph' ? 128 * 2 ** -23 : 5e-10;
            if (!Number.isFinite(error) || error > tolerance) blockers.push({ case: item.id, method: method.name, factor, offset,
              reason: 'Positive-affine equivariance failed', normalized_error: error, tolerance });
            rows.push({ method: method.name, finite_ordered: valid, point_min: pointMin, point_max: pointMax,
              flat_advisory: flat, max_normalized_affine_error: error, normalized_budget: tolerance });
          }
          contexts.push({ factor, offset, shifted, observed_bounds: [lowerBound, upperBound],
            calibration_group: calibrated.group, methods: rows });
        }
      }
      results.push({ id: item.id, history_length: item.history.length, reserved_target_length: 12,
        original_horizon: item.originalHorizon, seasonality: item.seasonality, input_sha256: item.input_sha256, contexts });
    }
    return { cases: results, blockers, advisories };
  }, cases);
  Object.assign(receipt, result);
  receipt.actual_network = { model_requests: requests.filter(value => value.endsWith('/nlinear.onnx')).length,
    wasm_requests: requests.filter(value => value.endsWith('.wasm')).length };
  assert.ok(receipt.actual_network.model_requests > 0 && receipt.actual_network.wasm_requests > 0, 'The real model and WASM runtime must be fetched');
  // Exercise the real SHA guard using a genuinely corrupted file on a second disposable server.
  const badPublic = path.join(scratch, 'corrupted-model-fixture');
  await fs.mkdir(path.join(badPublic, 'models'), { recursive: true });
  const corrupted = Buffer.from(await fs.readFile(path.join(frontend, 'public/models/nlinear.onnx')));
  corrupted[corrupted.length - 1] ^= 1;
  await fs.writeFile(path.join(badPublic, 'models/nlinear.onnx'), corrupted);
  const badOrigin = await serve(badPublic, 'corrupted');
  const badPage = await pageAt(badOrigin, 'corrupted');
  const badWasm = [];
  badPage.on('request', request => { if (/\.wasm(?:\?|$)/.test(request.url())) badWasm.push(request.url()); });
  const rejection = await badPage.evaluate(async history => {
    const { runNLinear } = await import('/src/lib/onnxRunner.ts');
    try { await runNLinear(history); return null; } catch (error) { return error.message; }
  }, cases[0].history);
  receipt.model_hash_rejection = { fixture: 'One changed byte in an actual external ONNX file, served by private Vite; no intercepted requests or fabricated predictions',
    corrupt_sha256: hash(corrupted), rejected: rejection?.includes('differs from its calibration') === true,
    reason: rejection, wasm_requests_before_rejection: badWasm.length };
  if (!receipt.model_hash_rejection.rejected || badWasm.length) receipt.blockers.push({ reason: 'The actual model SHA guard did not reject corruption before WASM' });
  for (const [name, expected] of Object.entries(observedHashes)) assert.equal(hash(await fs.readFile(path.join(root, name))), expected, `Source changed during audit: ${name}`);
  receipt.coverage = { cases: receipt.cases.length, methods_per_context: 6, contexts_per_case: 6,
    method_paths: receipt.cases.reduce((sum, item) => sum + item.contexts.reduce((count, context) => count + context.methods.length, 0), 0),
    values_per_path: 36, exact_constant_refusals: receipt.constant_inputs.filter(item => item.rejected).length };
  receipt.state = receipt.blockers.length ? 'failed' : 'passed';
} catch (error) {
  receipt.state = 'failed';
  receipt.blockers.push({ reason: error.message });
} finally {
  for (const context of contexts.reverse()) await context.close().catch(error => receipt.blockers.push({ reason: `Own browser cleanup: ${error.message}` }));
  for (const server of servers.reverse()) await server.close().catch(error => receipt.blockers.push({ reason: `Own server cleanup: ${error.message}` }));
  if (receipt.blockers.length) receipt.state = 'failed';
  await fs.writeFile(output, `${JSON.stringify(receipt, null, 2)}\n`);
  const resolvedTemp = await fs.realpath(tempRoot), resolvedScratch = await fs.realpath(scratch);
  const relative = path.relative(resolvedTemp, resolvedScratch);
  assert.ok(relative && !relative.startsWith('..') && !path.isAbsolute(relative) && path.basename(scratch).startsWith('browser-runtime-units-'));
  await fs.rm(resolvedScratch, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
}
console.log(`Browser runtime units ${receipt.state.toUpperCase()}: ${receipt.coverage?.method_paths ?? 0} actual paths; ${receipt.blockers.length} blockers; ${receipt.advisories.length} flat-path advisories`);
if (receipt.state !== 'passed') process.exitCode = 1;
