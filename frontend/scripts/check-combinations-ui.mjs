// Verify real collection/series/origin/method controls against the served numerical artifacts.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import { formatNumber } from '@fasl-work/caos-app-shell';
import { LANG_STORAGE_KEY, THEME_STORAGE_KEY } from '@fasl-work/caos-app-shell/keys';

const base = process.env.GATE_URL || 'http://127.0.0.1:4188';
const output = resolve(process.argv[2] || 'gate-output/combinations-ui');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const errors = [], states = [];
const started = new Date().toISOString();
const report = async extra => writeFile(resolve(output, 'report.json'), JSON.stringify({
  ok: false, base, started, states, page_errors: errors, ...extra,
}, null, 2) + '\n');
await report({ status: 'running' });
try {
  for (const lang of ['en', 'es']) for (const theme of ['light', 'dark']) for (const width of [390, 1280]) {
    const context = await browser.newContext({ viewport: { width, height: 844 } });
    await context.addInitScript(({ lang, theme, languageKey, themeKey }) => {
      localStorage.setItem(languageKey, lang); localStorage.setItem(themeKey, theme);
    }, { lang, theme, languageKey: LANG_STORAGE_KEY, themeKey: THEME_STORAGE_KEY });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);
    page.on('pageerror', error => errors.push(error.message));
    const index = await (await page.request.get(`${base}/data/validated-combinations.json`)).json();
    assert.equal(index.complete, true);
    assert.equal(index.cases.length, 1802);
    await page.goto(`${base}/experiments`, { waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: lang === 'es' ? 'Combinaciones validadas' : 'Validated combinations', exact: true }).click();
    const study = page.locator('[data-combination-study="ready"]');
    const collection = page.getByRole('combobox', { name: lang === 'es' ? 'Colección de combinaciones' : 'Combination collection' });
    for (const cohort of index.cohorts) {
      await collection.selectOption(cohort.id);
      const entries = index.cases.filter(c => c.dataset === cohort.id && !c.excluded);
      const series = page.getByRole('combobox', { name: lang === 'es' ? 'Serie de combinaciones' : 'Combination series' });
      assert.equal(await series.locator('option').count(), cohort.admitted);
      for (const entry of [entries[0], entries.at(-1)]) {
        await series.selectOption(entry.id);
        await page.waitForFunction(({ dataset, id }) => !!document.querySelector(
          `[data-combination-study="ready"][data-dataset="${dataset}"][data-series="${id}"]`
        ), { dataset: cohort.id, id: entry.id });
        const expected = await (await page.request.get(`${base}/data/${entry.path}`)).json();
        const originControl = page.getByRole('combobox', { name: lang === 'es' ? 'Origen de combinaciones' : 'Combination origin' });
        assert.equal(await originControl.locator('option').count(), expected.origins.length);
        for (let i = 0; i < expected.origins.length; i++) {
          await originControl.selectOption(String(i));
          // Every method is clicked on the first series; the last series protects identity changes.
          const methods = entry === entries[0] ? expected.origins[i].methods : expected.origins[i].methods.filter(m => m.name === 'ValidationMix');
          for (const method of methods) {
            const button = study.locator('table').first().getByRole('button', { name: method.name, exact: true });
            await button.click();
            assert.equal(await button.getAttribute('aria-pressed'), 'true');
            const score = study.locator('p').filter({ hasText: new RegExp(`^${method.name}: MASE`) });
            const displayed = await score.innerText();
            assert.ok(displayed.includes(formatNumber(method.metrics.mase, lang, { digits: 4 })), displayed);
            assert.ok(await study.locator('canvas').count() >= 1);
            states.push({ lang, theme, width, dataset: cohort.id, series: entry.id, origin: expected.origins[i].origin, method: method.name });
          }
        }
      }
      if (cohort.excluded) {
        await study.getByText(lang === 'es' ? 'Identidades de origen excluidas' : 'Excluded source identities', { exact: true }).click();
        assert.equal(await study.locator('details li').count(), cohort.excluded);
      }
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Viewport overflow');
      assert.doesNotMatch(await study.innerText(), /\u00c3[\u00a0-\u00bf]|\u00c2[\u0080-\u00bf]|\u00e2\u20ac/);
      await page.screenshot({ path: resolve(output, `${cohort.id}-${lang}-${theme}-${width}.png`), fullPage: true });
    }
    assert.equal(await page.locator('html').getAttribute('lang'), lang);
    assert.equal(await page.locator('html').getAttribute('data-theme'), theme);
    await context.close();
    console.log(`Combination controls passed: ${lang}/${theme}/${width}`);
  }
  assert.deepEqual(errors, []);
  await report({ ok: true, completed: new Date().toISOString() });
  console.log(`Combination UI: ${states.length} measured controls passed`);
} catch (error) {
  await report({ failed: new Date().toISOString(), error: String(error) });
  throw error;
} finally {
  await browser.close();
}
