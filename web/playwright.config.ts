import {defineConfig} from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  /** One baseline for all OSes; generate updates with `npm run e2e -- --update-snapshots` (prefer CI/Linux when possible). */
  snapshotPathTemplate: '{testDir}/{testFilePath}-snapshots/{arg}{ext}',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 800,
      animations: 'disabled',
    },
  },
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run build && npx vite preview --host 127.0.0.1 --port 4173 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: !process.env.CI,
    /** Production build can exceed 2 minutes on a cold cache; preview must bind before tests run. */
    timeout: 300_000,
  },
});
