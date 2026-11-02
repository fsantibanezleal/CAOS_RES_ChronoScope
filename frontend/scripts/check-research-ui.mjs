// Exercise the real sequence and corpus consumers, in both languages/themes at phone/desktop sizes.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { chromium } from 'playwright';
import { LANG_STORAGE_KEY, THEME_STORAGE_KEY } from '@fasl-work/caos-app-shell/keys';

const base = process.env.GATE_URL || 'http://127.0.0.1:4187';
const output = resolve(process.argv[2] || 'gate-output/research-ui');
const patternsOnly = process.argv.includes('--patterns-only');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const errors = [];
const states = [];
const started = new Date().toISOString();
await writeFile(resolve(output,'report.json'),JSON.stringify({ok:false,status:'running',started,base,patterns_only:patternsOnly},null,2)+'\n');
try {
  for (const lang of ['en','es']) for (const theme of ['light','dark']) for (const width of [390,1280]) {
    console.log(`Research UI start ${lang}/${theme}/${width}`);
    const context = await browser.newContext({ viewport: { width, height: 844 } });
    await context.addInitScript(({ lang, theme, languageKey, themeKey }) => {
      localStorage.setItem(languageKey,lang); localStorage.setItem(themeKey,theme);
    }, { lang, theme, languageKey: LANG_STORAGE_KEY, themeKey: THEME_STORAGE_KEY });
    const page = await context.newPage();
    page.setDefaultTimeout(60000);
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${base}/app`, {waitUntil:'domcontentloaded',timeout:60000});
    await page.getByRole('tab', { name: lang === 'es' ? 'Patrones' : 'Patterns', exact: true }).click();
    const choose = page.getByRole('combobox', { name: lang === 'es' ? 'Caso' : 'Case', exact: true });
    await choose.waitFor();
    for (const caseId of ['BRKV_level_shift','REAL_electricity','SEAS_hourly']) {
      const expected = await (await page.request.get(`${base}/data/${caseId}/analysis.json`)).json();
      await choose.selectOption(caseId);
      await page.waitForFunction(n => document.querySelector('[data-sequence-diagnostics="ready"]')?.getAttribute('data-observation-count') === String(n), expected.n);
      const annotation = page.getByRole('combobox', { name: lang === 'es' ? 'Anotaciones de la secuencia' : 'Sequence annotations' });
      for (const filter of ['motif','discord','regime','all']) {
        await annotation.selectOption(filter);
        assert.equal(await annotation.inputValue(),filter);
      }
      assert.equal(await page.locator('html').getAttribute('lang'),lang);
      assert.equal(await page.locator('html').getAttribute('data-theme'),theme);
      assert.ok(await page.locator('[data-sequence-diagnostics] canvas').count() >= 4);
      assert.ok(await page.locator('[data-sequence-diagnostics] table tbody tr').count() >= 3);
      assert.doesNotMatch(await page.locator('body').innerText(), /\u00c3[\u00a0-\u00bf]|\u00c2[\u0080-\u00bf]|\u00e2\u20ac/);
      if (caseId === 'BRKV_level_shift') await page.screenshot({ path: resolve(output,`patterns-${lang}-${theme}-${width}.png`),fullPage:true });
      states.push({ lang,theme,width,view:'patterns',case_id:caseId,original_observations:expected.n,filters:4 });
    }
    if (!patternsOnly) {
      await page.goto(`${base}/benchmark`, {waitUntil:'domcontentloaded',timeout:60000});
      await page.getByRole('tab', { name: lang === 'es' ? 'Estudio de corpus' : 'Corpus study', exact: true }).click();
      await page.locator('[data-forecastability-study="ready"]').waitFor({ timeout:60000 });
      const source = await (await page.request.get(`${base}/data/forecastability.json`)).json();
      assert.equal(source.complete,true); assert.equal(source.source_n,4227);
      assert.doesNotMatch(await page.locator('body').innerText(), /\u00c3[\u00a0-\u00bf]|\u00c2[\u0080-\u00bf]|\u00e2\u20ac/);
      const partition = page.getByRole('combobox', { name: lang === 'es' ? 'Partición del corpus' : 'Corpus partition' });
      for (const value of ['discovery','confirmation','all']) {
        await partition.selectOption(value); assert.equal(await partition.inputValue(),value);
      }
      await page.getByRole('combobox',{name:lang === 'es'?'Característica del prefijo':'Prefix feature'}).selectOption('history_length');
      await page.getByRole('combobox',{name:lang === 'es'?'Método del corpus':'Corpus method'}).selectOption('AutoETS');
      await page.getByRole('button',{name:lang === 'es'?'Página siguiente':'Next page',exact:true}).click();
      await page.getByRole('button',{name:lang === 'es'?'Página anterior':'Previous page',exact:true}).click();
      const firstId = source.series[0].id;
      await page.getByRole('textbox',{name:lang === 'es'?'Buscar serie':'Find series'}).fill(firstId);
      await page.locator('[data-forecastability-study] table').nth(1).getByRole('button',{name:firstId,exact:true}).click();
      assert.ok((await page.locator('[data-forecastability-study] [aria-live]').innerText()).includes(firstId));
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1),'Corpus overflows the viewport');
      await page.screenshot({path:resolve(output,`corpus-${lang}-${theme}-${width}.png`),fullPage:true});
      states.push({lang,theme,width,view:'corpus',series:source.included_n,partition_filters:3,method:'AutoETS'});
    }
    await context.close();
  }
  assert.deepEqual(errors,[]);
  await writeFile(resolve(output,'report.json'),JSON.stringify({ok:true,started,completed:new Date().toISOString(),base,patterns_only:patternsOnly,states,page_errors:errors},null,2)+'\n');
  console.log(`Research UI: ${states.length} real browser states passed`);
} catch (error) {
  await writeFile(resolve(output,'report.json'),JSON.stringify({ok:false,started,failed:new Date().toISOString(),base,patterns_only:patternsOnly,states,page_errors:errors,error:String(error)},null,2)+'\n');
  throw error;
} finally {
  await browser.close();
}
