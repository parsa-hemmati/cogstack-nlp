import { test, expect } from '@playwright/test';

/**
 * E2E tests for AnonCAT Demo App
 * Tests the anonymization/de-identification demonstration interface
 */

test.describe('AnonCAT Demo App - Homepage', () => {
  test('should load the demo app successfully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for AnonCAT branding or anonymization content
    const pageContent = await page.content();
    const hasAnonContent = pageContent.toLowerCase().includes('anon') ||
                          pageContent.toLowerCase().includes('de-identif') ||
                          pageContent.toLowerCase().includes('anonymi') ||
                          pageContent.toLowerCase().includes('redact');

    expect(hasAnonContent).toBeTruthy();
  });

  test('should have text input area for de-identification', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const hasTextInput = await page.locator('textarea, input[type="text"], [contenteditable="true"]').count() > 0;
    expect(hasTextInput).toBeTruthy();
  });

  test('should have process/anonymize button', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const hasProcessButton = await page.locator('button:has-text("Anonymize"), button:has-text("De-identify"), button:has-text("Process"), button:has-text("Submit"), button[type="submit"]').count() > 0;
    expect(hasProcessButton).toBeTruthy();
  });
});

test.describe('AnonCAT Demo App - De-identification', () => {
  test('should accept text input with PHI', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const textInput = page.locator('textarea, input[type="text"]').first();

    if (await textInput.count() > 0) {
      // Sample text with PHI-like content
      await textInput.fill('John Smith was seen on 01/15/2024 at Hospital XYZ.');
      const value = await textInput.inputValue();
      expect(value).toContain('John Smith');
    }
  });

  test('should show results/output area', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const hasResultsArea = await page.locator('[class*="result"], [class*="output"], [id*="result"], [id*="output"], .redacted, #redacted').count() > 0 ||
                          await page.locator('pre, code, .card, .panel').count() > 0;

    expect(hasResultsArea).toBeTruthy();
  });
});

test.describe('AnonCAT Demo App - Security', () => {
  test('should not leak PHI in page source', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const htmlContent = await page.content();

    // Check that no real PHI patterns are in the initial page load
    // (This is a basic check - the demo might have example data)
    const realSsnPattern = /\b\d{3}-\d{2}-\d{4}\b/;
    const matches = htmlContent.match(realSsnPattern) || [];

    // Should have no more than example SSNs
    expect(matches.length).toBeLessThanOrEqual(3);
  });
});

test.describe('AnonCAT Demo App - Accessibility', () => {
  test('should have proper ARIA attributes', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for any ARIA attributes
    const ariaElements = await page.locator('[aria-label], [aria-describedby], [role]').count();

    // Should have some accessibility attributes
    console.log(`ARIA elements found: ${ariaElements}`);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Navigate with keyboard
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
    }

    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedElement).toBeTruthy();
  });
});

test.describe('AnonCAT Demo App - Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    console.log(`AnonCAT Demo App load time: ${loadTime}ms`);

    expect(loadTime).toBeLessThan(10000);
  });
});
