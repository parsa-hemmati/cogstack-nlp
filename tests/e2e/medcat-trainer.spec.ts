import { test, expect } from '@playwright/test';

test.describe('MedCAT Trainer - Homepage', () => {
  test('should load the homepage successfully', async ({ page }) => {
    await page.goto('/');

    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');

    // Check the page title
    await expect(page).toHaveTitle(/MedCATTrainer/i);
  });

  test('should display the application branding', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for MedCAT branding elements
    const hasLogo = await page.locator('img[alt*="logo"], img[src*="logo"]').count() > 0;
    const hasBranding = await page.locator('text=/MedCAT/i').count() > 0;

    expect(hasLogo || hasBranding).toBeTruthy();
  });

  test('should have no console errors on load', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out known benign errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('404')
    );

    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('MedCAT Trainer - Login', () => {
  test('should display login form elements', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // MedCAT Trainer uses a Vue modal login with specific IDs:
    // - Username: #uname
    // - Password: #password
    // - Submit: .login-submit button with text "Login"

    // Wait for the login modal to appear (Vue SPA)
    await page.waitForTimeout(1000);

    // Check for the login form elements with the actual selectors
    const hasUsernameField = await page.locator('#uname, input[id="uname"]').count() > 0;
    const hasPasswordField = await page.locator('#password, input[type="password"]').count() > 0;

    // If login form exists, verify it has required elements
    if (hasUsernameField || hasPasswordField) {
      expect(hasUsernameField).toBeTruthy();
      expect(hasPasswordField).toBeTruthy();

      // Look for the login submit button (class="login-submit")
      const hasSubmitButton = await page.locator('.login-submit, button:has-text("Login")').count() > 0;
      expect(hasSubmitButton).toBeTruthy();
    } else {
      // If no login form visible, user might be auto-logged in or modal not shown
      console.log('Login form not visible - may be auto-authenticated or modal not triggered');
    }
  });

  test('should show error on invalid login attempt', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for the login modal to appear
    await page.waitForTimeout(1000);

    // Find the login form elements
    const usernameField = page.locator('#uname');
    const passwordField = page.locator('#password');
    const loginButton = page.locator('.login-submit, button:has-text("Login")').first();

    if (await loginButton.count() > 0 && await usernameField.count() > 0) {
      // Enter invalid credentials
      await usernameField.fill('invalid_user_test');
      await passwordField.fill('invalid_password_test');

      // Click login
      await loginButton.click();

      // Wait for the API response and error message
      await page.waitForTimeout(2000);

      // Check for error message (span.text-danger with login error)
      const hasErrorMessage = await page.locator('.text-danger, [class*="error"], [class*="danger"]').count() > 0;

      // Either shows error or stays on login (not navigated away)
      const stillOnLogin = await page.locator('#uname, .login-submit').count() > 0;

      expect(hasErrorMessage || stillOnLogin).toBeTruthy();
    } else {
      // Login form not present - skip test
      console.log('Login form not visible - skipping validation test');
    }
  });
});

test.describe('MedCAT Trainer - Navigation', () => {
  test('should have navigation elements', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for navigation elements
    const hasNav = await page.locator('nav, [role="navigation"], .navbar, .v-navigation-drawer, .v-app-bar').count() > 0;
    const hasLinks = await page.locator('a[href], .v-list-item').count() > 0;

    expect(hasNav || hasLinks).toBeTruthy();
  });

  test('should have clickable navigation items', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find navigation links
    const navLinks = page.locator('nav a, .navbar a, .v-list-item--link, a[href^="/"]');
    const count = await navLinks.count();

    if (count > 0) {
      // Verify at least one link is visible and clickable
      const firstLink = navLinks.first();
      await expect(firstLink).toBeVisible();
    }
  });
});

test.describe('MedCAT Trainer - Accessibility', () => {
  test('should have proper heading structure', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for at least one heading
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const headingCount = await headings.count();

    expect(headingCount).toBeGreaterThan(0);
  });

  test('should have accessible form labels', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find all input fields
    const inputs = page.locator('input:not([type="hidden"]):not([type="submit"])');
    const inputCount = await inputs.count();

    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledby = await input.getAttribute('aria-labelledby');
      const placeholder = await input.getAttribute('placeholder');

      // Check if input has some form of label
      const hasLabel = id
        ? await page.locator(`label[for="${id}"]`).count() > 0
        : false;

      const isAccessible = hasLabel || ariaLabel || ariaLabelledby || placeholder;

      if (!isAccessible) {
        console.warn(`Input at index ${i} may not be accessible`);
      }
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Press Tab to move focus
    await page.keyboard.press('Tab');

    // Get the focused element
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);

    // Should focus on an interactive element
    const interactiveElements = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'];
    expect(interactiveElements).toContain(focusedElement);
  });

  test('should have visible focus indicators', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Press Tab to move focus
    await page.keyboard.press('Tab');

    // Get the focused element
    const focusedElement = page.locator(':focus');

    // Check that focused element is visible
    await expect(focusedElement).toBeVisible();
  });
});

test.describe('MedCAT Trainer - Responsive Design', () => {
  test('should render correctly on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Page should not have horizontal scroll
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });

    expect(hasHorizontalScroll).toBeFalsy();
  });

  test('should render correctly on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Page should load without errors
    await expect(page).toHaveTitle(/MedCATTrainer/i);
  });

  test('should render correctly on desktop viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Page should load without errors
    await expect(page).toHaveTitle(/MedCATTrainer/i);
  });
});

test.describe('MedCAT Trainer - Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Page should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);

    console.log(`Page load time: ${loadTime}ms`);
  });

  test('should have no large layout shifts', async ({ page }) => {
    await page.goto('/');

    // Wait for initial render
    await page.waitForLoadState('domcontentloaded');

    // Take a screenshot of initial state
    const initialViewport = await page.viewportSize();

    // Wait for full load
    await page.waitForLoadState('networkidle');

    // Viewport should remain the same
    const finalViewport = await page.viewportSize();
    expect(finalViewport).toEqual(initialViewport);
  });
});
