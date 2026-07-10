import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  base: './', // relative base -> works on a GitHub Pages project site
  plugins: [react()],
  // node env for pure-computation tests; DOM tests (the panel boundary) opt in per file
  // via the `// @vitest-environment jsdom` pragma.
  test: { environment: 'node', globals: true },
});
