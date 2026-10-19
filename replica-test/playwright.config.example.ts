// Ins Projekt kopieren. Den lokalen Dev-Server separat starten.
import { defineConfig } from '@playwright/test';

const baseURL = process.env.REPLICA_TEST_URL || 'http://127.0.0.1:3000';
const target = new URL(baseURL);
if (!['http:', 'https:'].includes(target.protocol) ||
    !['127.0.0.1', 'localhost', '[::1]'].includes(target.hostname) ||
    target.username || target.password) {
  throw new Error('Die Beispieltests dürfen nur einen lokalen Testserver ansprechen.');
}

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  use: { baseURL, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
});
