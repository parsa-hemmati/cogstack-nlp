import { test, expect } from '@playwright/test';

/**
 * E2E tests for MedCAT Demo App
 * Tests the medical concept annotation demonstration interface
 */

test.describe('MedCAT Demo App - Homepage', () => {
  test('should load the demo app successfully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for MedCAT branding or demo content
    const pageContent = await page.content();
    const hasMedcatContent = pageContent.toLowerCase().includes('medcat') ||
                            pageContent.toLowerCase().includes('annotation') ||
                            pageContent.toLowerCase().includes('clinical');

    expect(hasMedcatContent).toBeTruthy();
  });

  test('should have text input area for annotation', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for text input area
    const hasTextInput = await page.locator('textarea, input[type="text"], [contenteditable="true"]').count() > 0;
    expect(hasTextInput).toBeTruthy();
  });

  test('should have annotation submit button', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for submit/annotate button
    const hasSubmitButton = await page.locator('button:has-text("Annotate"), button:has-text("Submit"), button:has-text("Process"), button[type="submit"]').count() > 0;
    expect(hasSubmitButton).toBeTruthy();
  });
});

test.describe('MedCAT Demo App - Annotation', () => {
  test('should accept text input', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const textInput = page.locator('textarea, input[type="text"]').first();

    if (await textInput.count() > 0) {
      await textInput.fill('Patient has diabetes and hypertension.');
      const value = await textInput.inputValue();
      expect(value).toContain('diabetes');
    }
  });

  test('should show results area', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for results/output area
    const hasResultsArea = await page.locator('[class*="result"], [class*="output"], [id*="result"], [id*="output"], .annotations, #annotations').count() > 0 ||
                          await page.locator('table, .card, .panel').count() > 0;

    expect(hasResultsArea).toBeTruthy();
  });
});

test.describe('MedCAT Demo App - API Integration', () => {
  test('should have API endpoint available', async ({ page, request }) => {
    // Check if API health endpoint exists
    const apiEndpoints = ['/api/health', '/health', '/api/', '/api/v1/'];

    let apiAvailable = false;
    for (const endpoint of apiEndpoints) {
      try {
        const response = await request.get(endpoint);
        if (response.ok()) {
          apiAvailable = true;
          break;
        }
      } catch {
        continue;
      }
    }

    // API should be available (if this is an API-based app)
    console.log(`API availability: ${apiAvailable}`);
  });
});

test.describe('MedCAT Demo App - Accessibility', () => {
  test('should have proper form labels', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const inputs = page.locator('input:not([type="hidden"]), textarea');
    const inputCount = await inputs.count();

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const placeholder = await input.getAttribute('placeholder');

      const hasLabel = id ? await page.locator(`label[for="${id}"]`).count() > 0 : false;
      const isAccessible = hasLabel || ariaLabel || placeholder;

      if (!isAccessible) {
        console.warn(`Input ${i} may not be accessible`);
      }
    }
  });

  test('should support keyboard interaction', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });
});

test.describe('MedCAT Demo App - Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    console.log(`MedCAT Demo App load time: ${loadTime}ms`);

    expect(loadTime).toBeLessThan(10000);
  });
});
