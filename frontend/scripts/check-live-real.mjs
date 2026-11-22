// Exercise actual browser ONNX inference on each admitted real history.
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';

const base = process.env.GATE_URL || 'http://127.0.0.1:4173';
const output = resolve(process.argv[2] || 'gate-output/live-real');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const errors = [];
const results = [];
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`${base}/benchmark?theme=dark&lang=en`);
  await page.getByRole('tab', { name: 'Live real inference', exact: true }).click();
  const choose = page.getByRole('combobox', { name: /^Case/ });
  const run = page.getByRole('button', { name: 'Run linear model on this real case', exact: true });
  await choose.waitFor({ state: 'visible' });
  const caseIds = await choose.locator('option').evaluateAll(options => options.map(option => option.value));
  if (caseIds.length !== 4 || caseIds.some(id => !id.startsWith('REAL_'))) throw new Error('Incomplete real-case inventory');
  for (const id of caseIds) {
    if (await choose.inputValue() !== id) {
      await Promise.all([
        page.waitForResponse(response => response.url().endsWith(`/data/${id}/trace.json`) && response.ok()),
        choose.selectOption(id),
      ]);
    }
    await run.waitFor({ state: 'visible' });
    await page.waitForFunction(() => !document.querySelector('[data-control="run-real-nlinear"]')?.disabled);
    await run.click();
    const score = page.locator('p').filter({ hasText: /^Mean absolute error:/ });
    await score.waitFor({ state: 'visible', timeout: 60000 });
    const text = await score.innerText();
    if (!/^Mean absolute error:\s*[\d,.]+$/.test(text)) throw new Error(`Invalid live score: ${text}`);
    results.push({ case_id: id, displayed_score: text });
    await page.screenshot({ path: resolve(output, `${id}.png`), fullPage: true });
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await writeFile(resolve(output, 'report.json'), `${JSON.stringify({ ok: true, results, page_errors: errors }, null, 2)}\n`);
  console.log(`Live ONNX inference: ${results.length} real cases passed`);
} finally {
  await browser.close();
}
