import { test } from 'vitest';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

function calibrationFixture(front: string) {
  mkdirSync(join(front, 'src/lib'), { recursive: true });
  mkdirSync(join(front, 'public/models'), { recursive: true });
  copyFileSync(join(dirname(fileURLToPath(import.meta.url)), '../lib/browserCalibration.json'), join(front, 'src/lib/browserCalibration.json'));
}

test('adversarial: prebuild removes orphaned public cases and copies the canonical corpus', () => {
  const tempBase = resolve(tmpdir());
  const root = mkdtempSync(join(tempBase, 'chronoscope-copy-data-'));
  try {
    const front = join(root, 'frontend');
    const source = join(root, 'data/derived/current');
    const obsolete = join(front, 'public/data/obsolete');
    mkdirSync(source, { recursive: true });
    mkdirSync(obsolete, { recursive: true });
    calibrationFixture(front);
    writeFileSync(join(source, 'trace.json'), '{"current":true}\n');
    writeFileSync(join(obsolete, 'trace.json'), '{"obsolete":true}\n');
    copyFileSync(join(dirname(fileURLToPath(import.meta.url)), '../../copy-data.mjs'), join(front, 'copy-data.mjs'));
    execFileSync(process.execPath, [join(front, 'copy-data.mjs')], { cwd: front });
    assert.equal(existsSync(obsolete), false);
    assert.equal(readFileSync(join(front, 'public/data/current/trace.json'), 'utf8'), '{"current":true}\n');
    assert.equal(readFileSync(join(front, 'public/models/browser-calibration.json'), 'utf8'),
      readFileSync(join(front, 'src/lib/browserCalibration.json'), 'utf8'));
  } finally {
    const rel = relative(tempBase, resolve(root));
    assert.ok(rel && !isAbsolute(rel) && rel !== '..' && !rel.startsWith(`..${sep}`));
    rmSync(root, { recursive: true, force: true });
  }
});

test('adversarial: prebuild refuses missing canonical inputs instead of publishing a cached corpus', () => {
  const tempBase = resolve(tmpdir());
  const root = mkdtempSync(join(tempBase, 'chronoscope-copy-data-'));
  try {
    const front = join(root, 'frontend');
    const cached = join(front, 'public/data/cached.json');
    mkdirSync(dirname(cached), { recursive: true });
    calibrationFixture(front);
    writeFileSync(cached, '{"old":true}');
    copyFileSync(join(dirname(fileURLToPath(import.meta.url)), '../../copy-data.mjs'), join(front, 'copy-data.mjs'));
    assert.throws(() => execFileSync(process.execPath, [join(front, 'copy-data.mjs')], { cwd: front, stdio: 'pipe' }),
      error => typeof error === 'object' && error !== null && 'status' in error && error.status !== 0
        && 'stderr' in error && String(error.stderr).includes('Canonical data/derived is missing'));
    assert.equal(readFileSync(cached, 'utf8'), '{"old":true}');
  } finally {
    const rel = relative(tempBase, resolve(root));
    assert.ok(rel && !isAbsolute(rel) && rel !== '..' && !rel.startsWith(`..${sep}`));
    rmSync(root, { recursive: true, force: true });
  }
});
