import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for MedCAT Trainer E2E tests.
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8001',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chrome',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome', // Use system Chrome instead of downloading
      },
    },
  ],

  /* Run local dev server before starting the tests */
  // webServer: {
  //   command: 'docker-compose up -d',
  //   url: 'http://localhost:8001',
  //   reuseExistingServer: !process.env.CI,
  // },
});
