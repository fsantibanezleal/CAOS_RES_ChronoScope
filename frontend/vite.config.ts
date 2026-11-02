import react from '@vitejs/plugin-react';
import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { defineConfig } from 'vitest/config';
import { THEME_BOOT_SCRIPT } from '@fasl-work/caos-app-shell/keys';

const root = new URL('..', import.meta.url);
const VERSION = readFileSync(new URL('VERSION', root), 'utf8').trim();
const product = JSON.parse(readFileSync(new URL('product.json', root), 'utf8')) as {
  name: string;
  tagline: { en: string };
};

function commit(): string {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    return execSync('git rev-parse HEAD', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
  } catch {
    return 'unknown';
  }
}

const SHA = commit();

export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [
    react(),
    {
      name: 'chronoscope-html',
      transformIndexHtml: (html) => html
        .replaceAll('%PRODUCT_NAME%', product.name)
        .replaceAll('%PRODUCT_TAGLINE%', product.tagline.en)
        .replace('<!--caos-boot-->', `<script>${THEME_BOOT_SCRIPT}</script>`),
    },
    {
      name: 'chronoscope-build-json',
      apply: 'build',
      writeBundle() {
        writeFileSync(
          new URL('frontend/dist/build.json', root),
          `${JSON.stringify({ version: VERSION, sha: SHA, built: new Date().toISOString() }, null, 2)}\n`,
        );
      },
    },
  ],
  define: {
    __APP_VERSION__: JSON.stringify(VERSION),
    __BUILD_ID__: JSON.stringify(SHA.slice(0, 7)),
  },
  resolve: { dedupe: ['react', 'react-dom', 'react-router'] },
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'react-vendor', test: /node_modules[\\/](react|react-dom|scheduler)[\\/]/, priority: 20, includeDependenciesRecursively: false },
            { name: 'math-vendor', test: /node_modules[\\/]katex[\\/]/, priority: 10, includeDependenciesRecursively: false },
          ],
        },
      },
    },
  },
  test: { environment: 'node', globals: true, include: ['src/**/*.test.ts', 'src/**/*.test.tsx'] },
});
