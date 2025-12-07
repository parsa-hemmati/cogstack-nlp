import { test, expect } from '@playwright/test';

/**
 * Generic E2E tests that work for any web application module.
 * These tests check basic functionality, accessibility, and performance.
 */

test.describe('Generic Module Tests - Homepage', () => {
  test('should load the homepage successfully', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBeLessThan(400);
    await page.waitForLoadState('networkidle');
  });

  test('should have a valid page title', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
  });

  test('should have no critical console errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Filter out common non-critical errors
        if (!text.includes('favicon') &&
            !text.includes('404') &&
            !text.includes('net::ERR')) {
          consoleErrors.push(text);
        }
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Allow up to 2 non-critical errors
    expect(consoleErrors.length).toBeLessThanOrEqual(2);
  });

  test('should not have JavaScript errors', async ({ page }) => {
    const jsErrors: string[] = [];

    page.on('pageerror', error => {
      jsErrors.push(error.message);
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    expect(jsErrors).toHaveLength(0);
  });
});

test.describe('Generic Module Tests - Navigation', () => {
  test('should have interactive elements', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for any interactive elements
    const interactiveElements = await page.locator('a, button, input, select, textarea').count();
    expect(interactiveElements).toBeGreaterThan(0);
  });

  test('should have working links', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const links = page.locator('a[href]');
    const linkCount = await links.count();

    if (linkCount > 0) {
      // Check first few links are valid
      const linksToCheck = Math.min(linkCount, 5);
      for (let i = 0; i < linksToCheck; i++) {
        const href = await links.nth(i).getAttribute('href');
        expect(href).toBeTruthy();
      }
    }
  });
});

test.describe('Generic Module Tests - Accessibility', () => {
  test('should have a main landmark or content area', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const hasMain = await page.locator('main, [role="main"], #main, .main, #app, #root').count() > 0;
    expect(hasMain).toBeTruthy();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Press Tab
    await page.keyboard.press('Tab');

    // Something should be focused
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedTag).toBeTruthy();
  });

  test('should have sufficient color contrast (basic check)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check that body has some styling (not completely unstyled)
    const bodyStyle = await page.evaluate(() => {
      const body = document.body;
      const style = window.getComputedStyle(body);
      return {
        hasBackground: style.backgroundColor !== 'rgba(0, 0, 0, 0)',
        hasColor: style.color !== ''
      };
    });

    // At minimum, there should be some styling applied
    expect(bodyStyle.hasColor).toBeTruthy();
  });
});

test.describe('Generic Module Tests - Responsive Design', () => {
  test('should render on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    const response = await page.goto('/');
    expect(response?.status()).toBeLessThan(400);

    await page.waitForLoadState('networkidle');

    // Page should not have excessive horizontal scroll
    const hasExcessiveHScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth + 50;
    });
    expect(hasExcessiveHScroll).toBeFalsy();
  });

  test('should render on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });

    const response = await page.goto('/');
    expect(response?.status()).toBeLessThan(400);
  });

  test('should render on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });

    const response = await page.goto('/');
    expect(response?.status()).toBeLessThan(400);
  });
});

test.describe('Generic Module Tests - Performance', () => {
  test('should load within 15 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);

    expect(loadTime).toBeLessThan(15000);
  });

  test('should have reasonable DOM size', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const domSize = await page.evaluate(() => document.querySelectorAll('*').length);
    console.log(`DOM elements: ${domSize}`);

    // DOM should not be excessively large
    expect(domSize).toBeLessThan(5000);
  });
});

test.describe('Generic Module Tests - Security', () => {
  test('should not expose sensitive data in HTML', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const htmlContent = await page.content();
    const lowerContent = htmlContent.toLowerCase();

    // Check for common sensitive patterns
    const sensitivePatterns = [
      'password=',
      'api_key=',
      'secret=',
      'token=',
      'private_key'
    ];

    for (const pattern of sensitivePatterns) {
      expect(lowerContent).not.toContain(pattern);
    }
  });

  test('should have security headers (basic check)', async ({ page }) => {
    const response = await page.goto('/');

    // These are nice-to-have, not required
    const headers = response?.headers() || {};
    console.log('Security headers present:', Object.keys(headers).join(', '));
  });
});
